# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

import requests

from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons.zalo_oa.tools import zalo_client

# Patched at the client's own requests.post: Odoo's tests refuse outbound
# requests at requests.Session.send (odoo/tests/common.py:295-333), and the
# client must never reach it.
POST = "odoo.addons.zalo_oa.tools.zalo_client.requests.post"
SECRET = "S3CRET"
OLD_REFRESH = "R-OLD"
SUCCESS = {"access_token": "A-NEW", "refresh_token": "R-NEW", "expires_in": "90000"}


class Response:
    """What the client reads of a requests response."""

    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("No JSON object could be decoded")
        return self._body


class TestZaloClient(TransactionCase):
    """The token half of the client. No records."""

    def _refresh(self, response=None, side_effect=None):
        with patch(POST, return_value=response, side_effect=side_effect) as post:
            result = zalo_client.refresh_tokens("A1", SECRET, OLD_REFRESH)
        return result, post

    def test_refresh_request_shape(self):
        __, post = self._refresh(Response(200, SUCCESS))
        args, kwargs = post.call_args
        self.assertEqual(args[0], zalo_client.OA_TOKEN_URL)
        self.assertEqual(
            kwargs["data"],
            {
                "refresh_token": OLD_REFRESH,
                "grant_type": "refresh_token",
                "app_id": "A1",
            },
        )
        self.assertEqual(kwargs["headers"], {"secret_key": SECRET})
        self.assertEqual(kwargs["timeout"], zalo_client.TIMEOUT)

    def test_success(self):
        result, __ = self._refresh(Response(200, SUCCESS))
        self.assertEqual(
            result,
            {
                "ok": True,
                "access_token": "A-NEW",
                "refresh_token": "R-NEW",
                "expires_in": 90000,
            },
        )

    def test_missing_expires_in(self):
        body = {"access_token": "A-NEW", "refresh_token": "R-NEW"}
        result, __ = self._refresh(Response(200, body))
        self.assertEqual(result["expires_in"], zalo_client.DEFAULT_EXPIRES_IN)

    def test_zalo_error_in_body(self):
        body = {"error": -14020, "error_name": "Invalid refresh token"}
        result, __ = self._refresh(Response(200, body))
        self.assertFalse(result["ok"])
        self.assertIn("authorize the app again", result["error"])

    def test_not_json(self):
        result, __ = self._refresh(Response(502, None))
        self.assertFalse(result["ok"])
        self.assertIn("502", result["error"])

    def test_network_error(self):
        result, __ = self._refresh(side_effect=requests.ConnectionError("down"))
        self.assertFalse(result["ok"])
        self.assertIn("network error", result["error"])

    def test_no_secret_in_error(self):
        failures = (
            {"response": Response(200, {"error": -14020})},
            {"response": Response(200, {"error": -201, "error_name": "Bad request"})},
            {"response": Response(200, {"access_token": "A-NEW"})},
            {"response": Response(500, None)},
            {"side_effect": requests.Timeout("slow")},
        )
        for failure in failures:
            with self.subTest(failure=failure):
                result, __ = self._refresh(**failure)
                self.assertFalse(result["ok"])
                for secret in (SECRET, OLD_REFRESH, "A-NEW"):
                    self.assertNotIn(secret, result["error"])

    def test_config_read(self):
        with patch.dict(config.options, {"zalo_app_id": " A1 "}):
            self.assertEqual(zalo_client.get_zalo_config()["app_id"], "A1")
        with patch.dict(config.options, {"zalo_app_id": ""}):
            self.assertFalse(zalo_client.get_zalo_config()["app_id"])
