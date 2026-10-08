# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import hashlib
import string
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from psycopg2.errors import SerializationFailure

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons.zalo_oa.tools import zalo_client

# Patched where the model imported it: the client's own test covers HTTP.
EXCHANGE = "odoo.addons.zalo_oa.models.zalo_token.exchange_code"
CONFIG = {"zalo_app_id": "T", "zalo_app_secret": "S3CRET"}
REDIRECT_URI = "https://odoo.example.com/zalo/callback"
OK = {
    "ok": True,
    "access_token": "A-NEW",
    "refresh_token": "R-NEW",
    "expires_in": 90000,
}
FAILED = {"ok": False, "error": "Zalo error -14019: invalid code verifier"}


def challenge_of(code_verifier):
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class TestZaloAuthorize(TransactionCase):
    """The initial authorization, without HTTP. No core records."""

    def setUp(self):
        super().setUp()
        # Per test, never as a class patcher (addons/CLAUDE.md, Tests).
        self.startPatcher(patch.dict(config.options, CONFIG))
        self.tokens = self.env["zalo.token"]

    def _pending(self, minutes_ago=1, **vals):
        """T's row with a pending authorization, state STATE."""
        token = self.tokens._get_current() or self.tokens.create({"app_id": "T"})
        token.write(
            dict(
                {
                    "auth_state": "STATE",
                    "auth_code_verifier": "VERIFIER",
                    "auth_requested_at": fields.Datetime.now()
                    - timedelta(minutes=minutes_ago),
                },
                **vals,
            )
        )
        return token

    def _finish(self, state="STATE", code="CODE", response=OK):
        with patch(EXCHANGE, return_value=response) as exchange:
            result = self.tokens._authorize_finish(state, code)
        return result, exchange

    def assertPending(self, token, pending=True):
        if pending:
            self.assertEqual(token.auth_state, "STATE")
            self.assertEqual(token.auth_code_verifier, "VERIFIER")
            self.assertTrue(token.auth_requested_at)
        else:
            self.assertFalse(token.auth_state)
            self.assertFalse(token.auth_code_verifier)
            self.assertFalse(token.auth_requested_at)

    # -- the client's helpers -------------------------------------------------

    def test_pkce_pair(self):
        code_verifier, code_challenge = zalo_client.pkce_pair()
        self.assertEqual(len(code_verifier), 64)
        self.assertLessEqual(
            set(code_verifier), set(string.ascii_letters + string.digits + "-_")
        )
        self.assertEqual(code_challenge, challenge_of(code_verifier))
        self.assertNotIn("=", code_challenge)

    def test_permission_url(self):
        url = zalo_client.permission_url("T", REDIRECT_URI, "CHALLENGE", "STATE")
        self.assertTrue(url.startswith(zalo_client.OA_PERMISSION_URL + "?"))
        self.assertEqual(
            parse_qs(urlsplit(url).query),
            {
                "app_id": ["T"],
                "redirect_uri": [REDIRECT_URI],
                "code_challenge": ["CHALLENGE"],
                "state": ["STATE"],
            },
        )

    # -- start ----------------------------------------------------------------

    def test_start_creates_the_row(self):
        self.assertFalse(self.tokens._get_current())
        url = self.tokens._authorize_start(REDIRECT_URI)
        token = self.tokens._get_current()
        self.assertTrue(token)
        self.assertTrue(token.auth_state)
        self.assertTrue(token.auth_code_verifier)
        self.assertTrue(token.auth_requested_at)
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query["app_id"], ["T"])
        self.assertEqual(query["redirect_uri"], [REDIRECT_URI])
        self.assertEqual(query["state"], [token.auth_state])
        self.assertEqual(
            query["code_challenge"], [challenge_of(token.auth_code_verifier)]
        )

    def test_start_without_app(self):
        with (
            patch.dict(config.options, {"zalo_app_id": ""}),
            self.assertRaises(UserError),
        ):
            self.tokens._authorize_start(REDIRECT_URI)

    # -- finish ---------------------------------------------------------------

    def test_finish_saves_the_pair(self):
        token = self._pending()
        (ok, __), exchange = self._finish()
        self.assertTrue(ok)
        exchange.assert_called_once_with("T", "S3CRET", "CODE", "VERIFIER")
        self.assertEqual(token.access_token, "A-NEW")
        self.assertEqual(token.refresh_token, "R-NEW")
        expected = fields.Datetime.now() + timedelta(seconds=90000)
        self.assertLess(abs(token.expires_at - expected), timedelta(minutes=1))
        self.assertTrue(token.last_refresh_at)
        self.assertFalse(token.last_error)
        self.assertPending(token, False)

    def test_finish_wrong_state(self):
        token = self._pending()
        (ok, __), exchange = self._finish(state="OTHER")
        self.assertFalse(ok)
        exchange.assert_not_called()
        self.assertFalse(token.access_token)
        self.assertPending(token)

    def test_finish_non_ascii_state(self):
        token = self._pending()
        (ok, __), exchange = self._finish(state="é")
        self.assertFalse(ok)
        exchange.assert_not_called()
        self.assertPending(token)

    def test_finish_expired(self):
        token = self._pending(minutes_ago=11)
        (ok, __), exchange = self._finish()
        self.assertFalse(ok)
        exchange.assert_not_called()
        self.assertPending(token, False)

    def test_finish_without_code(self):
        token = self._pending()
        (ok, __), exchange = self._finish(code="")
        self.assertFalse(ok)
        exchange.assert_not_called()
        self.assertPending(token, False)

    def test_finish_without_app(self):
        self._pending()
        with patch.dict(config.options, {"zalo_app_id": ""}):
            (ok, __), exchange = self._finish()
        self.assertFalse(ok)
        exchange.assert_not_called()

    def test_finish_locks_before_exchange(self):
        self._pending()
        model = type(self.tokens)
        failure = SerializationFailure("concurrent update")
        with (
            patch.object(model, "_lock_row", side_effect=failure),
            patch(EXCHANGE, return_value=OK) as exchange,
            self.assertRaises(SerializationFailure),
        ):
            self.tokens._authorize_finish("STATE", "CODE")
        exchange.assert_not_called()

    def test_finish_failed_exchange(self):
        token = self._pending(access_token="A-OLD", refresh_token="R-OLD")
        (ok, message), __ = self._finish(response=FAILED)
        self.assertFalse(ok)
        self.assertEqual(message, FAILED["error"])
        self.assertEqual(token.last_error, FAILED["error"])
        self.assertEqual(token.access_token, "A-OLD")
        self.assertEqual(token.refresh_token, "R-OLD")
        self.assertPending(token, False)

    def test_state_used_once(self):
        self._pending()
        (ok, __), __ = self._finish()
        self.assertTrue(ok)
        (ok, __), exchange = self._finish()
        self.assertFalse(ok)
        exchange.assert_not_called()
