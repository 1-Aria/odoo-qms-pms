# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import api, fields, models

from ..tools.zalo_client import get_zalo_config, send_text
from .zalo_destination import RECIPIENT_TYPES

_logger = logging.getLogger(__name__)

# A message still failing after this many attempts is failed for good.
MAX_ATTEMPTS = 5
# Messages per run; the cron runner calls the job again while due ones remain.
BATCH_SIZE = 50
# Sent and failed messages older than this are removed.
RETENTION_DAYS = 30
# A retried message waits attempts x this before it is due again, so the
# runner's repeated calls within one run (ir_cron.py:419-454) do not burn its
# attempts in seconds while Zalo is down.
RETRY_DELAY = timedelta(minutes=5)


def _payload_error(payload):
    """What is wrong with a /zalo/send body, or False."""
    if not isinstance(payload, dict):
        return "The body must be a JSON object."
    if payload.get("recipient_type") not in dict(RECIPIENT_TYPES):
        return "recipient_type must be 'user' or 'group'."
    for key in ("recipient", "text"):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            return f"{key} must be a non-empty string."
    return False


class ZaloMessage(models.Model):
    """The queue and log of every send.

    Every send becomes a record first and goes to Zalo only from the send
    cron, so a rolled-back record never produces a message and no user
    request waits on Zalo.
    """

    _name = "zalo.message"
    _description = "Zalo Message"
    _order = "id desc"

    # Not required: a failed message records whatever it had (_queue).
    recipient_type = fields.Selection(selection=RECIPIENT_TYPES, string="Type")
    recipient_id = fields.Char(string="Zalo ID")
    destination_id = fields.Many2one(
        comodel_name="zalo.destination",
        ondelete="set null",
        index=True,
    )
    text = fields.Text()
    state = fields.Selection(
        selection=[("queued", "Queued"), ("sent", "Sent"), ("failed", "Failed")],
        required=True,
        default="queued",
        index=True,
    )
    attempts = fields.Integer(readonly=True)
    next_attempt_at = fields.Datetime(
        string="Next Attempt",
        readonly=True,
        index=True,
        help="Set after a retryable failure; the message is not sent before it.",
    )
    last_error = fields.Text(readonly=True)
    zalo_response = fields.Text(string="Zalo Response", readonly=True)
    sent_at = fields.Datetime(readonly=True)
    sent_to = fields.Char(
        readonly=True,
        help="The recipient Zalo was given, as <type>:<id>: another than the "
        "intended one when a redirect is configured.",
    )
    res_model = fields.Char(string="Source Model", index=True)
    res_id = fields.Many2oneReference(
        model_field="res_model", string="Source Record"
    )
    template_id = fields.Many2one(
        comodel_name="zalo.template",
        ondelete="set null",
        readonly=True,
    )

    @api.depends("destination_id", "recipient_type", "recipient_id")
    def _compute_display_name(self):
        for message in self:
            message.display_name = message.destination_id.name or (
                f"{message.recipient_type}:{message.recipient_id}"
                if message.recipient_type
                else self.env._("No recipient")
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Every queued message wakes the send cron, however it was created."""
        messages = super().create(vals_list)
        if any(message.state == "queued" for message in messages):
            self.env.ref("zalo_oa.ir_cron_zalo_send").sudo()._trigger()
        return messages

    # -- queueing -------------------------------------------------------------

    @api.model
    def _queue(
        self,
        text,
        recipient_type=None,
        recipient_id=None,
        destination=None,
        record=None,
        template=None,
        error=None,
    ):
        """Queue a message. Never raises.

        Queueing runs inside the caller's transaction -- often an automation
        rule, which re-raises its actions' errors and would fail the user's
        save (base_automation.py:737-742). So the module's work runs in a
        savepoint, and any error becomes a failed message.

        The caller's pending writes are flushed first, outside the guard: a
        savepoint flushes them when it opens (sql_db.py:123-126), and a failure
        of the caller's own write caught here would leave an aborted
        transaction and hide the caller's error.

        :param error: given, the message is created failed with it -- a
            template that could not be rendered, for one.
        :return: the message, or an empty recordset.
        """
        self.env.flush_all()
        messages = self.sudo()
        failure = False
        try:
            vals = messages._queue_values(
                text, recipient_type, recipient_id, destination, record, template, error
            )
            with self.env.cr.savepoint():
                return messages.create(vals).sudo(False)
        except Exception as error:
            _logger.exception("Zalo: could not queue a message")
            failure = f"{type(error).__name__}: {error}"
        try:
            with self.env.cr.savepoint():
                return messages.create(
                    {
                        "state": "failed",
                        "last_error": failure,
                        "text": text if isinstance(text, str) else False,
                    }
                ).sudo(False)
        except Exception:
            _logger.exception("Zalo: could not record a failed message")
            return self.browse()

    @api.model
    def _queue_values(
        self, text, recipient_type, recipient_id, destination, record, template, error
    ):
        vals = {
            "text": text or False,
            "res_model": record._name if record else False,
            "res_id": record.id if record else False,
            "template_id": template.id if template else False,
        }
        if destination:
            destination = destination.sudo()
            vals.update(
                destination_id=destination.id,
                recipient_type=destination.recipient_type,
                recipient_id=destination.zalo_id,
            )
            if not destination.active and not error:
                error = self.env._("The destination %s is archived.", destination.name)
        else:
            vals.update(
                recipient_type=recipient_type or False,
                recipient_id=recipient_id or False,
            )
        if not error and (
            vals["recipient_type"] not in dict(RECIPIENT_TYPES)
            or not vals["recipient_id"]
        ):
            error = self.env._("No recipient.")
        if not error and not text:
            error = self.env._("No text.")
        if error:
            vals.update(state="failed", last_error=error)
        return vals

    @api.model
    def _queue_from_template(self, template, records, destinations):
        """Render a template for each record and queue it to each destination.

        Never raises (the design's Isolation from Odoo, rule 1): a rendering
        error -- a mistyped placeholder, a removed field -- becomes a failed
        message per record and destination, and the save that triggered the
        rule goes through.

        The caller's writes are flushed first, outside the guard, as in
        _queue.

        The template is read and rendered as superuser, so it renders the same
        whether an automation runs the action, through sudo, or a user does.
        """
        if not records or not destinations:
            return self.browse()
        self.env.flush_all()
        template = template.sudo()
        texts, failure = {}, False
        try:
            with self.env.cr.savepoint():
                texts = template._render_field("body", records.ids)
        except Exception as error:
            _logger.exception("Zalo: could not render template %s", template.id)
            failure = self.env._(
                "The template could not be rendered: %(error)s",
                error=f"{type(error).__name__}: {error}",
            )
        messages = self.browse()
        for record in records:
            for destination in destinations:
                messages |= self._queue(
                    texts.get(record.id) or False,
                    destination=destination,
                    record=record,
                    template=template,
                    error=failure,
                )
        return messages

    @api.model
    def _queue_from_request(self, payload):
        """The body of /zalo/send, as the key's user: (HTTP status, answer).

        A model method so that it is tested without HTTP: no HttpCase runs on
        this image. Bearer authentication (401) is Odoo's, before the route.

        The message is read back as superuser: the sender holds no access to
        the log, and reading its state as that user would raise.
        """
        if not self.env.user.has_group("zalo_oa.group_zalo_sender"):
            return 403, {
                "ok": False,
                "error": "This key's user may not send Zalo messages.",
            }
        error = _payload_error(payload)
        if error:
            return 400, {"ok": False, "error": error}
        message = self._queue(
            payload["text"],
            recipient_type=payload["recipient_type"],
            recipient_id=payload["recipient"],
        ).sudo()
        result = {"ok": message.state == "queued", "id": message.id or False}
        if not result["ok"]:
            result["error"] = message.last_error or "The message could not be queued."
        return 200, result

    # -- sending --------------------------------------------------------------

    @api.model
    def _redirect(self):
        """The configured redirect as (type, id), or False.

        :raises ValueError: when zalo_redirect_recipient is malformed -- the
            message then fails rather than reach its real recipient, which is
            what the redirect exists to prevent.
        """
        value = get_zalo_config()["redirect"]
        if not value:
            return False
        kind, separator, zalo_id = value.partition(":")
        kind, zalo_id = kind.strip(), zalo_id.strip()
        if not separator or kind not in dict(RECIPIENT_TYPES) or not zalo_id:
            raise ValueError("malformed zalo_redirect_recipient")
        return kind, zalo_id

    def _send(self, token):
        """Send one message with the token, refreshing once on expiry.

        The refresh runs outside any savepoint, since _refresh commits.
        """
        self.ensure_one()
        try:
            redirect = self._redirect()
        except ValueError:
            self._write_result(
                {
                    "status": "failed",
                    "error": self.env._(
                        "zalo_redirect_recipient is malformed: expected "
                        "group:<id> or user:<id>."
                    ),
                    "response": False,
                }
            )
            return
        if redirect:
            recipient_type, recipient_id = redirect
            text = f"[→ {self.display_name}] {self.text or ''}"
        else:
            recipient_type, recipient_id = self.recipient_type, self.recipient_id
            text = self.text
        if (
            recipient_type not in dict(RECIPIENT_TYPES)
            or not recipient_id
            or not self.text
        ):
            self._write_result(
                {
                    "status": "failed",
                    "error": self.env._("No recipient or no text."),
                    "response": False,
                }
            )
            return

        stale = token.access_token
        result = send_text(stale, recipient_type, recipient_id, text)
        if result["status"] == "expired":
            if token._refresh(stale_access_token=stale):
                token.invalidate_recordset(["access_token"])
                result = send_text(
                    token.access_token, recipient_type, recipient_id, text
                )
                if result["status"] == "expired":
                    # A concurrent refresh this transaction cannot see yet:
                    # one attempt, and the next run sends with the new pair.
                    result = dict(result, status="retry")
            else:
                result = {
                    "status": "retry",
                    "error": token.last_error or self.env._("Token refresh failed."),
                    "response": False,
                }
        self._write_result(result, sent_to=f"{recipient_type}:{recipient_id}")

    def _write_result(self, result, sent_to=False):
        """Record one send's outcome, in a savepoint of its own."""
        self.ensure_one()
        now = fields.Datetime.now()
        status = result["status"]
        if status == "sent":
            vals = {
                "state": "sent",
                "sent_at": now,
                "sent_to": sent_to,
                "zalo_response": result["response"],
                "last_error": False,
                "next_attempt_at": False,
            }
        elif status == "retry":
            attempts = self.attempts + 1
            vals = {
                "attempts": attempts,
                "last_error": result["error"],
                "next_attempt_at": now + RETRY_DELAY * attempts,
            }
            if attempts >= MAX_ATTEMPTS:
                vals.update(state="failed", next_attempt_at=False)
        else:
            vals = {
                "state": "failed",
                "attempts": self.attempts + 1,
                "last_error": result["error"],
                "zalo_response": result.get("response") or False,
                "next_attempt_at": False,
            }
        with self.env.cr.savepoint():
            self.write(vals)

    @api.model
    def _due_domain(self):
        return [
            ("state", "=", "queued"),
            "|",
            ("next_attempt_at", "=", False),
            ("next_attempt_at", "<=", fields.Datetime.now()),
        ]

    @api.model
    def _cron_send(self):
        """The send cron. It never raises, and commits after each message.

        A crash mid-batch must not resend a message Zalo accepted, so each
        result is committed before the next send -- as core's mail and SMS
        queues do (sms_sms.py:147-149). Odoo deactivates a cron that keeps
        failing, so every error is caught. Without a configured app, or its
        token, the messages simply stay queued.
        """
        try:
            if not get_zalo_config()["app_id"]:
                return
            tokens = self.env["zalo.token"]
            token = tokens._get_current()
            if not token or not token.access_token:
                return
            auto_commit = tokens._zalo_auto_commit()
            messages = self.search(self._due_domain(), order="id", limit=BATCH_SIZE)
            for message in messages:
                try:
                    message._send(token)
                except Exception as error:
                    _logger.exception("Zalo: sending message %s failed", message.id)
                    try:
                        message._write_result(
                            {
                                "status": "retry",
                                "error": f"{type(error).__name__}: {error}",
                                "response": False,
                            }
                        )
                    except Exception:
                        _logger.exception(
                            "Zalo: could not record message %s", message.id
                        )
                if auto_commit:
                    self.env.cr.commit()
            self.env["ir.cron"]._notify_progress(
                done=len(messages), remaining=self.search_count(self._due_domain())
            )
        except Exception:
            _logger.exception("Zalo: send cron failed")

    def action_retry(self):
        """Failed messages back into the queue, from the start."""
        self.filtered(lambda message: message.state == "failed").write(
            {
                "state": "queued",
                "attempts": 0,
                "last_error": False,
                "next_attempt_at": False,
            }
        )
        self.env.ref("zalo_oa.ir_cron_zalo_send").sudo()._trigger()

    @api.autovacuum
    def _gc_old_messages(self):
        """Remove sent and failed messages after the retention period."""
        limit = fields.Datetime.now() - timedelta(days=RETENTION_DAYS)
        self.sudo().search(
            [("state", "in", ("sent", "failed")), ("create_date", "<", limit)]
        ).unlink()
