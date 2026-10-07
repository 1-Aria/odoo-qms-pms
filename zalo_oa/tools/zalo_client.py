# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Zalo API, with no ORM: a port of docs/zalo_client.js.

Functions take the app's ID and secret and return a result dictionary; the
models persist and lock. Nothing here ever puts a token, a secret or a raw
response body into a returned text or a log line.
"""

import requests

from odoo.tools import config

OA_TOKEN_URL = "https://oauth.zaloapp.com/v4/oa/access_token"
REFRESH_TOKEN_INVALID = -14020
# When a response has no expires_in: 25 hours, as observed (the reference's
# Caveats; the original script's "1 hour" was wrong).
DEFAULT_EXPIRES_IN = 90000
TIMEOUT = 20

# The instance's Zalo app, named in its odoo.conf (on this instance through
# ADDITIONAL_ODOO_RC). Every [options] key is kept by Odoo's config
# (odoo/tools/config.py:703-709).
CONFIG_KEYS = {
    "app_id": "zalo_app_id",
    "app_secret": "zalo_app_secret",
    "oa_secret": "zalo_oa_secret",
    "redirect": "zalo_redirect_recipient",
}


def get_zalo_config():
    """The instance's Zalo configuration, read on every call.

    Nothing is cached, so a restart with a new .env takes effect without a
    database change. A missing or empty key is False; no app_id, no Zalo.
    """
    result = {}
    for key, option in CONFIG_KEYS.items():
        value = config.get(option)
        result[key] = (str(value).strip() if value else "") or False
    return result


def _error_code(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def request_tokens(app_id, app_secret, fields):
    """POST to the OA token endpoint: the code exchange and the refresh.

    Form-encoded, the app secret in a `secret_key` header (the reference,
    Refresh request). Zalo reports failures inside HTTP 200 bodies as well.
    """
    try:
        response = requests.post(
            OA_TOKEN_URL,
            data=dict(fields, app_id=app_id),
            headers={"secret_key": app_secret},
            timeout=TIMEOUT,
        )
    except requests.RequestException as error:
        return {"ok": False, "error": f"network error: {type(error).__name__}"}
    unexpected = {
        "ok": False,
        "error": f"unexpected response (HTTP {response.status_code})",
    }
    try:
        data = response.json()
    except ValueError:
        return unexpected
    if not isinstance(data, dict):
        return unexpected

    code = _error_code(data.get("error"))
    if code == REFRESH_TOKEN_INVALID:
        return {
            "ok": False,
            "error": "refresh token already used or expired; authorize the app again",
        }
    if code not in (None, 0, "") or data.get("error_name") or data.get(
        "error_description"
    ):
        detail = data.get("error_name") or data.get("error_description") or ""
        return {"ok": False, "error": f"Zalo error {code}: {detail}".strip()}
    if (
        response.status_code != 200
        or not data.get("access_token")
        or not data.get("refresh_token")
    ):
        return unexpected

    try:
        expires_in = int(data.get("expires_in") or DEFAULT_EXPIRES_IN)
    except (TypeError, ValueError):
        expires_in = DEFAULT_EXPIRES_IN
    return {
        "ok": True,
        "access_token": str(data["access_token"]),
        "refresh_token": str(data["refresh_token"]),
        "expires_in": expires_in,
    }


def refresh_tokens(app_id, app_secret, refresh_token):
    """Exchange a refresh token for a new pair. The old one is dead after."""
    return request_tokens(
        app_id,
        app_secret,
        {"refresh_token": refresh_token, "grant_type": "refresh_token"},
    )
