# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from psycopg2 import IntegrityError
from psycopg2.errors import SerializationFailure

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import config, mute_logger

# Patched where the model imported it: the client's own test covers HTTP.
REFRESH = "odoo.addons.zalo_oa.models.zalo_token.refresh_tokens"
CONFIG = {"zalo_app_id": "T", "zalo_app_secret": "S3CRET"}
OK = {
    "ok": True,
    "access_token": "A-NEW",
    "refresh_token": "R-NEW",
    "expires_in": 90000,
}
FAILED = {"ok": False, "error": "Zalo error -201: Bad request"}


@tagged("post_install", "-at_install")
class TestZaloToken(TransactionCase):
    """The token per app, the refresh and the refresh cron.

    post_install: the access test creates a user, a core record later
    modules extend. The configuration names app T; P is another instance's
    app, as a database restore leaves it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        soon = fields.Datetime.now() + timedelta(hours=2)
        token = cls.env["zalo.token"]
        cls.token = token.create(
            {
                "app_id": "T",
                "access_token": "A-OLD",
                "refresh_token": "R-OLD",
                "expires_at": soon,
            }
        )
        cls.other = token.create(
            {
                "app_id": "P",
                "access_token": "A-P",
                "refresh_token": "R-P",
                "expires_at": soon,
            }
        )

    def setUp(self):
        super().setUp()
        # Per test, never as a class patcher: after every test TransactionCase
        # reads .target from each active patch (odoo/tests/common.py:1117-1122),
        # and patch.dict has none. A test patch stops before that check runs.
        self.startPatcher(patch.dict(config.options, CONFIG))

    def _cron(self, response=OK, side_effect=None):
        with patch(REFRESH, return_value=response, side_effect=side_effect) as call:
            self.env["zalo.token"]._cron_refresh()
        return call

    # -- the configured app ---------------------------------------------------

    def test_current_is_the_configured_app(self):
        self.assertEqual(self.env["zalo.token"]._get_current(), self.token)
        with patch.dict(config.options, {"zalo_app_id": ""}):
            self.assertFalse(self.env["zalo.token"]._get_current())

    def test_one_row_per_app(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env["zalo.token"].create({"app_id": "T"})

    # -- the refresh ----------------------------------------------------------

    def test_refresh_saves_the_pair(self):
        self.token.refresh_requested = True
        with patch(REFRESH, return_value=OK) as call:
            self.assertTrue(self.token._refresh(stale_access_token="A-OLD"))
        call.assert_called_once_with("T", "S3CRET", "R-OLD")
        self.assertEqual(self.token.access_token, "A-NEW")
        self.assertEqual(self.token.refresh_token, "R-NEW")
        expected = fields.Datetime.now() + timedelta(seconds=90000)
        self.assertAlmostEqual(
            self.token.expires_at, expected, delta=timedelta(minutes=1)
        )
        self.assertTrue(self.token.last_refresh_at)
        self.assertFalse(self.token.last_error)
        self.assertFalse(self.token.refresh_requested)

    def test_refresh_failure_keeps_the_pair(self):
        with patch(REFRESH, return_value=FAILED):
            self.assertFalse(self.token._refresh(stale_access_token="A-OLD"))
        self.assertEqual(self.token.access_token, "A-OLD")
        self.assertEqual(self.token.refresh_token, "R-OLD")
        self.assertEqual(self.token.last_error, FAILED["error"])

    def test_refresh_skips_when_already_refreshed(self):
        with patch(REFRESH, return_value=OK) as call:
            self.assertTrue(self.token._refresh(stale_access_token="A-STALE"))
        call.assert_not_called()
        self.assertEqual(self.token.access_token, "A-OLD")

    # -- the cron -------------------------------------------------------------

    def test_cron_refreshes_when_expiring(self):
        call = self._cron()
        call.assert_called_once_with("T", "S3CRET", "R-OLD")
        self.assertEqual(self.token.access_token, "A-NEW")

    def test_cron_skips_fresh_token(self):
        self.token.expires_at = fields.Datetime.now() + timedelta(hours=20)
        self._cron().assert_not_called()

    def test_cron_refresh_requested(self):
        self.token.expires_at = fields.Datetime.now() + timedelta(hours=20)
        self.token.action_refresh_now()
        self.assertTrue(self.token.refresh_requested)
        self._cron().assert_called_once()
        self.assertFalse(self.token.refresh_requested)

    def test_cron_never_touches_other_apps(self):
        call = self._cron()
        for args in call.call_args_list:
            self.assertEqual(args[0][0], "T")
        self.assertEqual(self.other.access_token, "A-P")
        self.assertEqual(self.other.refresh_token, "R-P")

    def test_cron_without_app(self):
        with patch.dict(config.options, {"zalo_app_id": ""}):
            self._cron().assert_not_called()

    @mute_logger("odoo.addons.zalo_oa.models.zalo_token")
    def test_cron_never_raises(self):
        self._cron(side_effect=RuntimeError("boom"))
        self.assertIn("RuntimeError", self.token.last_error)
        self.assertEqual(self.token.refresh_token, "R-OLD")

    def test_cron_survives_serialization_failure(self):
        model = type(self.env["zalo.token"])
        with patch.object(
            model, "_lock_row", side_effect=SerializationFailure("concurrent update")
        ):
            call = self._cron()
        call.assert_not_called()
        self.assertEqual(self.token.access_token, "A-OLD")
        self.assertEqual(self.token.refresh_token, "R-OLD")
        self.assertFalse(self.token.last_error)

    def test_health_alert_once(self):
        admin = self.env.ref("base.user_admin")
        self.token.write(
            {
                "alert_user_id": admin.id,
                "last_refresh_at": fields.Datetime.now() - timedelta(days=3),
                "expires_at": fields.Datetime.now() + timedelta(hours=20),
            }
        )
        warning = self.env.ref("mail.mail_activity_data_warning")

        def alerts():
            return self.token.activity_ids.filtered(
                lambda activity: activity.activity_type_id == warning
                and activity.user_id == admin
            )

        self._cron()
        self.assertEqual(len(alerts()), 1)
        self._cron()
        self.assertEqual(len(alerts()), 1)

    # -- access ---------------------------------------------------------------

    def test_tokens_for_administrators_only(self):
        user = self.env["res.users"].create(
            {
                "name": "Zalo outsider",
                "login": "zalo-outsider@example.com",
                "groups_id": [(6, 0, self.env.ref("base.group_user").ids)],
            }
        )
        # The positive control: an ordinary read succeeds.
        self.env["res.partner"].with_user(user).search([], limit=1)
        with self.assertRaises(AccessError):
            self.token.with_user(user).read(["app_id"])
