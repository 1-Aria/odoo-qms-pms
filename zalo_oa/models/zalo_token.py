# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import threading
from datetime import timedelta

from psycopg2.errors import SerializationFailure

from odoo import api, fields, models

from ..tools.zalo_client import get_zalo_config, refresh_tokens

_logger = logging.getLogger(__name__)

# Refresh when fewer than this remain, hourly, so one failed run never lets
# the access token (about 25 hours) lapse.
REFRESH_MARGIN = timedelta(hours=6)
# Alert when the last successful refresh is older than this, while the
# refresh token (about three months) still has months left.
HEALTH_LIMIT = timedelta(days=2)


class ZaloToken(models.Model):
    """One Zalo app's token pair.

    One row per app: the instance's odoo.conf names its app, and only that
    app's row is ever used or refreshed, so a row copied in by a database
    restore -- another instance's app -- is left alone.
    """

    _name = "zalo.token"
    _description = "Zalo App Token"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "app_id"

    app_id = fields.Char(string="App ID", required=True, index=True)
    # Typed by hand on the form, masked: phase 2 copies the Apps Script's
    # refresh token in, phase 1 tests sends with a borrowed access token.
    access_token = fields.Char(groups="base.group_system", copy=False)
    refresh_token = fields.Char(groups="base.group_system", copy=False)
    expires_at = fields.Datetime(string="Access Token Expires", copy=False)
    last_refresh_at = fields.Datetime(string="Last Refresh", readonly=True, copy=False)
    last_error = fields.Text(readonly=True, copy=False)
    refresh_requested = fields.Boolean(
        copy=False,
        help="Set by Refresh now; the next run of the refresh cron refreshes "
        "whatever the expiry.",
    )
    alert_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Alert User",
        domain=lambda self: [
            ("groups_id", "in", self.env.ref("base.group_system").ids)
        ],
        help="A system administrator, told when the token has not been refreshed "
        "for two days. Only administrators can open the token the alert points at.",
    )
    is_configured_app = fields.Boolean(
        string="This Instance's App",
        compute="_compute_is_configured_app",
    )

    _sql_constraints = [
        (
            "app_id_unique",
            "UNIQUE (app_id)",
            "There is already a token for this Zalo app.",
        ),
    ]

    @api.depends("app_id")
    def _compute_is_configured_app(self):
        app_id = get_zalo_config()["app_id"]
        for token in self:
            token.is_configured_app = bool(app_id) and token.app_id == app_id

    @api.model
    def _get_current(self):
        """The configured app's row, or nothing. Never creates."""
        app_id = get_zalo_config()["app_id"]
        if not app_id:
            return self.browse()
        return self.search([("app_id", "=", app_id)], limit=1)

    @api.model
    def _zalo_auto_commit(self):
        """Commit outside tests only -- core's mail queue rule
        (mail/models/mail_mail.py:263)."""
        return not getattr(threading.current_thread(), "testing", False)

    def _lock_row(self):
        self.env.cr.execute(
            "SELECT id FROM zalo_token WHERE id = %s FOR UPDATE", [self.id]
        )

    def _refresh(self, stale_access_token):
        """Refresh the pair, unless another worker already did.

        Zalo rotates the refresh token the moment it answers, so the new pair
        is saved at once and committed before anything else can roll it back.

        Odoo's cursors run in REPEATABLE READ (odoo/sql_db.py:303): waiting on
        the lock for a row another transaction then updates and commits fails
        with a serialization error rather than returning the new row. So the
        locked work runs in a savepoint, and that error is read as "refreshed
        by another worker" -- this one never calls Zalo, and the next
        transaction sees the new pair. The commit comes after the savepoint
        closes: committing inside an open one breaks its release. So this must
        not be called inside a savepoint of the caller's either.

        :return: True when a new pair was saved or found already saved.
        """
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                result, saved = self._refresh_locked(stale_access_token)
        except SerializationFailure:
            self.invalidate_recordset()
            _logger.info(
                "Zalo: token of app %s refreshed by another worker", self.app_id
            )
            return True
        if saved and self._zalo_auto_commit():
            self.env.cr.commit()
        return result

    def _refresh_locked(self, stale_access_token):
        self._lock_row()
        self.invalidate_recordset()
        # Refreshed before this transaction began, after the caller read its
        # stale token: the send fallback's case (step 2).
        if self.access_token != stale_access_token:
            self.refresh_requested = False
            return True, False
        app_secret = get_zalo_config()["app_secret"]
        if not app_secret or not self.refresh_token:
            self.last_error = self.env._(
                "Cannot refresh: no app secret configured, or no refresh token stored."
            )
            return False, False
        response = refresh_tokens(self.app_id, app_secret, self.refresh_token)
        if not response["ok"]:
            # Both tokens stay: a failed refresh has rotated nothing.
            self.last_error = response["error"]
            return False, False
        now = fields.Datetime.now()
        self.write(
            {
                "access_token": response["access_token"],
                "refresh_token": response["refresh_token"],
                "expires_at": now + timedelta(seconds=response["expires_in"]),
                "last_refresh_at": now,
                "last_error": False,
                "refresh_requested": False,
            }
        )
        return True, True

    def action_refresh_now(self):
        """Ask the refresh cron to refresh at its next run, within seconds.

        Not a refresh in this request: Zalo is called from crons only.
        """
        self.ensure_one()
        self.refresh_requested = True
        self.env.ref("zalo_oa.ir_cron_zalo_token_refresh")._trigger()

    @api.model
    def _cron_refresh(self):
        """The refresh cron. It never raises.

        Odoo deactivates a cron that keeps failing (base/models/ir_cron.py:
        24-25, 457-494), and notifications would stop silently, so every error
        is caught and written to last_error -- except a serialization failure,
        which means the row changed under this transaction: writing to it would
        fail the same way, and the next run sees the new pair. _refresh keeps
        its own savepoint, and commits, so only the health check gets one here.
        """
        token = self._get_current()
        if not token:
            return
        try:
            due = (
                token.refresh_requested
                or not token.expires_at
                or token.expires_at - fields.Datetime.now() < REFRESH_MARGIN
            )
            if due:
                token._refresh(stale_access_token=token.access_token)
            with self.env.cr.savepoint():
                token._check_health()
        except SerializationFailure:
            token.invalidate_recordset()
        except Exception as error:
            _logger.exception("Zalo: token refresh failed for app %s", token.app_id)
            token.invalidate_recordset()
            token.last_error = f"{type(error).__name__}: {error}"

    def _check_health(self):
        """Tell the alert user, once, when the token has stopped refreshing."""
        self.ensure_one()
        if not self.alert_user_id:
            return
        now = fields.Datetime.now()
        if self.last_refresh_at and now - self.last_refresh_at < HEALTH_LIMIT:
            return
        warning = self.env.ref("mail.mail_activity_data_warning")
        if self.activity_ids.filtered(
            lambda activity: activity.activity_type_id == warning
            and activity.user_id == self.alert_user_id
        ):
            return
        self.activity_schedule(
            "mail.mail_activity_data_warning",
            user_id=self.alert_user_id.id,
            summary=self.env._("Zalo token not refreshed"),
            note=self.env._(
                "Last successful refresh: %(when)s. Last error: %(error)s",
                when=self.last_refresh_at or self.env._("never"),
                error=self.last_error or self.env._("none"),
            ),
        )
