# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

PLAIN_TEXT = [("Content-Type", "text/plain; charset=utf-8")]


class ZaloController(http.Controller):
    """Thin routes: the logic lives on zalo.token and zalo.message."""

    @http.route("/zalo/authorize", type="http", auth="user", methods=["GET"])
    def zalo_authorize(self, **kwargs):
        """Send a system administrator to Zalo to grant the app permission."""
        env = request.env
        if not env.user._is_system():
            return request.make_response(
                env._("Only a system administrator can authorize the Zalo app."),
                headers=PLAIN_TEXT,
                status=403,
            )
        tokens = env["zalo.token"]
        try:
            url = tokens._authorize_start(f"{tokens.get_base_url()}/zalo/callback")
        except UserError as error:
            return request.make_response(error.args[0], headers=PLAIN_TEXT)
        # Not local: the default strips scheme and host (http.py:1942-1947).
        return request.redirect(url, local=False)

    @http.route(
        "/zalo/callback",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def zalo_callback(self, state=None, code=None, **kwargs):
        """Zalo's redirect after the OA administrator's approval.

        Plain text: a refusal may carry Zalo's own error text.
        """
        env = request.env
        ok, message = env["zalo.token"].sudo()._authorize_finish(state, code)
        if not ok:
            message = env._("The Zalo app was not authorized: %s", message)
        return request.make_response(message, headers=PLAIN_TEXT)

    @http.route(
        "/zalo/send",
        type="http",
        auth="bearer",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def zalo_send(self, **kwargs):
        """Queue a message to a raw recipient, for the Apps Script.

        Odoo's bearer authentication answers a missing or invalid key with 401
        before this runs (base/models/ir_http.py:204-243); the rest is
        zalo.message._queue_from_request, as the key's user.
        """
        try:
            payload = request.get_json_data()
        except ValueError:
            payload = None
        status, result = request.env["zalo.message"]._queue_from_request(payload)
        return request.make_json_response(result, status=status)
