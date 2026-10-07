# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import config, mute_logger

MODULE = "odoo.addons.zalo_oa.models.zalo_message"
SEND = f"{MODULE}.send_text"
REFRESH = "odoo.addons.zalo_oa.models.zalo_token.refresh_tokens"
CONFIG = {
    "zalo_app_id": "T",
    "zalo_app_secret": "S3CRET",
    "zalo_redirect_recipient": "",
}

SENT = {"status": "sent", "error": False, "response": '{"error": 0}'}
EXPIRED = {"status": "expired", "error": "access token expired", "response": False}
RETRY = {
    "status": "retry",
    "error": "network error: ConnectionError",
    "response": False,
}
FAILED = {"status": "failed", "error": "Zalo error -224: package", "response": "{}"}
REFRESHED = {
    "ok": True,
    "access_token": "A-NEW",
    "refresh_token": "R-NEW",
    "expires_in": 90000,
}


@tagged("post_install", "-at_install")
class TestZaloMessage(TransactionCase):
    """The queue, the send cron, the redirect and the log.

    post_install: the access test creates a user, a core record later
    modules extend.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.token = cls.env["zalo.token"].create(
            {
                "app_id": "T",
                "access_token": "A-OLD",
                "refresh_token": "R-OLD",
                "expires_at": fields.Datetime.now() + timedelta(hours=20),
            }
        )
        cls.destination = cls.env["zalo.destination"].create(
            {
                "name": "Maintenance group",
                "recipient_type": "group",
                "zalo_id": "G-MAINT",
            }
        )
        cls.messages = cls.env["zalo.message"]
        cls.send_cron = cls.env.ref("zalo_oa.ir_cron_zalo_send")

    def setUp(self):
        super().setUp()
        # Per test, never as a class patcher (addons/CLAUDE.md, Tests).
        self.startPatcher(patch.dict(config.options, CONFIG))

    def _queue(self, text="Hello", **kwargs):
        kwargs.setdefault("destination", self.destination)
        return self.messages._queue(text, **kwargs)

    def _cron(self, *results, refresh=REFRESHED):
        """Run the send cron once, send_text answering `results` in turn."""
        with (
            patch(SEND, side_effect=list(results)) as send,
            patch(REFRESH, return_value=refresh) as refresh_call,
        ):
            self.messages._cron_send()
        return send, refresh_call

    def _make_due(self, message):
        message.next_attempt_at = fields.Datetime.now() - timedelta(minutes=1)

    # -- queueing -------------------------------------------------------------

    def test_queue_wakes_the_cron(self):
        before = self.env["ir.cron.trigger"].search_count(
            [("cron_id", "=", self.send_cron.id)]
        )
        message = self._queue()
        self.assertEqual(message.state, "queued")
        after = self.env["ir.cron.trigger"].search_count(
            [("cron_id", "=", self.send_cron.id)]
        )
        self.assertGreater(after, before)

    def test_queue_from_destination(self):
        message = self._queue(record=self.token)
        self.assertEqual(message.recipient_type, "group")
        self.assertEqual(message.recipient_id, "G-MAINT")
        self.assertEqual(message.destination_id, self.destination)
        self.assertEqual(message.res_model, "zalo.token")
        self.assertEqual(message.res_id, self.token.id)

    @mute_logger(MODULE)
    def test_queue_never_raises(self):
        no_recipient = self.messages._queue("Hello")
        self.assertEqual(no_recipient.state, "failed")
        self.assertIn("No recipient", no_recipient.last_error)

        no_text = self._queue(text="")
        self.assertEqual(no_text.state, "failed")
        self.assertIn("No text", no_text.last_error)

        archived = self.env["zalo.destination"].create(
            {"name": "Old group", "zalo_id": "G-OLD", "active": False}
        )
        self.assertEqual(self._queue(destination=archived).state, "failed")

        model = type(self.messages)
        with patch.object(model, "create", side_effect=RuntimeError("boom")):
            self.assertFalse(self._queue())

    def test_queue_flushes_the_callers_writes_first(self):
        """The caller's own error is the caller's, not swallowed.

        Patched inside assertRaises: Odoo's assertRaises opens a flushing
        savepoint on entry (odoo/tests/common.py:489), which would otherwise
        meet the patched flush first.
        """
        with self.assertRaises(RuntimeError):
            with patch.object(
                type(self.env), "flush_all", side_effect=RuntimeError("caller")
            ):
                self._queue()

    # -- sending --------------------------------------------------------------

    def test_cron_sends(self):
        message = self._queue()
        send, __ = self._cron(SENT)
        send.assert_called_once_with("A-OLD", "group", "G-MAINT", "Hello")
        self.assertEqual(message.state, "sent")
        self.assertTrue(message.sent_at)
        self.assertEqual(message.sent_to, "group:G-MAINT")
        self.assertEqual(message.zalo_response, SENT["response"])

    def test_cron_without_app(self):
        message = self._queue()
        with patch.dict(config.options, {"zalo_app_id": ""}):
            send, __ = self._cron(SENT)
        send.assert_not_called()
        self.assertEqual(message.state, "queued")

    def test_cron_ignores_other_apps_token(self):
        message = self._queue()
        self.token.app_id = "P"
        send, __ = self._cron(SENT)
        send.assert_not_called()
        self.assertEqual(message.state, "queued")

    def test_expired_refreshes_and_retries(self):
        message = self._queue()
        send, refresh = self._cron(EXPIRED, SENT)
        refresh.assert_called_once_with("T", "S3CRET", "R-OLD")
        self.assertEqual(send.call_args_list[1][0][0], "A-NEW")
        self.assertEqual(message.state, "sent")

    def test_expired_after_refresh_stays_queued(self):
        message = self._queue()
        self._cron(EXPIRED, EXPIRED)
        self.assertEqual(message.state, "queued")
        self.assertEqual(message.attempts, 1)
        self.assertGreater(message.next_attempt_at, fields.Datetime.now())

    def test_failed_refresh_stays_queued(self):
        message = self._queue()
        failed = {"ok": False, "error": "Zalo error -201: refresh refused"}
        self._cron(EXPIRED, refresh=failed)
        self.assertEqual(message.state, "queued")
        self.assertEqual(message.attempts, 1)
        self.assertIn("refresh refused", message.last_error)

    def test_retry_waits_for_its_turn(self):
        """A retried message is not due again within the same run."""
        message = self._queue()
        send, __ = self._cron(RETRY, SENT)
        send.assert_called_once()
        self.assertEqual(message.state, "queued")
        send, __ = self._cron(SENT)
        send.assert_not_called()

    def test_retry_until_max_attempts(self):
        message = self._queue()
        for attempt in range(1, 6):
            self._make_due(message)
            self._cron(RETRY)
            self.assertEqual(message.attempts, attempt)
        self.assertEqual(message.state, "failed")

    def test_permanent_error_fails_at_once(self):
        message = self._queue()
        self._cron(FAILED)
        self.assertEqual(message.state, "failed")
        self.assertEqual(message.zalo_response, FAILED["response"])

    def test_redirect(self):
        message = self._queue()
        with patch.dict(config.options, {"zalo_redirect_recipient": "group:G-TEST"}):
            send, __ = self._cron(SENT)
        args = send.call_args[0]
        self.assertEqual(args[1:3], ("group", "G-TEST"))
        self.assertTrue(args[3].startswith("[→ Maintenance group] "))
        self.assertEqual(message.sent_to, "group:G-TEST")
        self.assertEqual(message.destination_id, self.destination)

    def test_malformed_redirect_fails(self):
        message = self._queue()
        with patch.dict(config.options, {"zalo_redirect_recipient": "bogus"}):
            send, __ = self._cron(SENT)
        send.assert_not_called()
        self.assertEqual(message.state, "failed")
        self.assertIn("zalo_redirect_recipient", message.last_error)

    @mute_logger(MODULE)
    def test_cron_never_raises(self):
        message = self._queue()
        with patch(SEND, side_effect=RuntimeError("boom")):
            self.messages._cron_send()
        self.assertEqual(message.state, "queued")
        self.assertEqual(message.attempts, 1)
        self.assertIn("RuntimeError", message.last_error)

    def test_batch_progress(self):
        for __ in range(3):
            self._queue()
        notify = patch.object(type(self.env["ir.cron"]), "_notify_progress")
        with patch(f"{MODULE}.BATCH_SIZE", 2), notify as progress:
            send, __ = self._cron(SENT, SENT)
        self.assertEqual(send.call_count, 2)
        progress.assert_called_once_with(done=2, remaining=1)

    def test_retry_action(self):
        message = self._queue()
        self._cron(FAILED)
        message.action_retry()
        self.assertEqual(message.state, "queued")
        self.assertEqual(message.attempts, 0)
        self.assertFalse(message.last_error)

    # -- housekeeping and access ----------------------------------------------

    def test_old_messages_vacuumed(self):
        old_sent, old_failed, old_queued, recent_sent = (
            self._queue() for __ in range(4)
        )
        (old_sent | recent_sent).state = "sent"
        old_failed.state = "failed"
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE zalo_message SET create_date = now() - interval '31 days' "
            "WHERE id IN %s",
            [tuple((old_sent | old_failed | old_queued).ids)],
        )
        self.env.cr.execute(
            "UPDATE zalo_message SET create_date = now() - interval '1 day' "
            "WHERE id = %s",
            [recent_sent.id],
        )
        self.messages.invalidate_model()
        self.messages._gc_old_messages()
        self.assertFalse(old_sent.exists())
        self.assertFalse(old_failed.exists())
        self.assertTrue(old_queued.exists())
        self.assertTrue(recent_sent.exists())

    def test_log_for_administrators_only(self):
        user = self.env["res.users"].create(
            {
                "name": "Zalo outsider",
                "login": "zalo-message-outsider@example.com",
                "groups_id": [(6, 0, self.env.ref("base.group_user").ids)],
            }
        )
        # The positive control: an ordinary read succeeds.
        self.env["res.partner"].with_user(user).search([], limit=1)
        message = self._queue()
        with self.assertRaises(AccessError):
            message.with_user(user).read(["text"])
        queued = self.messages.with_user(user)._queue(
            "From a user", recipient_type="group", recipient_id="G-MAINT"
        )
        self.assertEqual(queued.sudo().state, "queued")
