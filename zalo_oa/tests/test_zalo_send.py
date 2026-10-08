# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests.common import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

VALID = {"recipient_type": "user", "recipient": "U-1", "text": "Hello"}


@tagged("post_install", "-at_install")
class TestZaloSend(TransactionCase):
    """The body of /zalo/send, without HTTP: no HttpCase runs on this image.

    post_install: the fixtures create users, a core record later modules
    extend. Called as the technical user, as the route calls it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The technical user holds Zalo sender and nothing else (D27).
        cls.sender = new_test_user(
            cls.env, "zalo_send_sender", groups="zalo_oa.group_zalo_sender"
        )
        cls.employee = new_test_user(
            cls.env, "zalo_send_employee", groups="base.group_user"
        )

    def _call(self, payload, user=None):
        messages = self.env["zalo.message"].with_user(user or self.sender)
        return messages._queue_from_request(payload)

    def _count(self):
        return self.env["zalo.message"].search_count([])

    def test_send_queues(self):
        status, result = self._call(VALID)
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        message = self.env["zalo.message"].browse(result["id"])
        self.assertEqual(message.state, "queued")
        self.assertEqual(message.recipient_type, "user")
        self.assertEqual(message.recipient_id, "U-1")
        self.assertEqual(message.text, "Hello")

    def test_send_without_group(self):
        before = self._count()
        status, result = self._call(VALID, user=self.employee)
        self.assertEqual(status, 403)
        self.assertFalse(result["ok"])
        self.assertEqual(self._count(), before)

    def test_send_bad_payload(self):
        before = self._count()
        cases = {
            "not JSON": None,
            "a list": [VALID],
            "channel": dict(VALID, recipient_type="channel"),
            "numeric recipient": dict(VALID, recipient=12345),
            "empty text": dict(VALID, text=""),
            "missing text": {"recipient_type": "user", "recipient": "U-1"},
        }
        for name, payload in cases.items():
            with self.subTest(name):
                status, result = self._call(payload)
                self.assertEqual(status, 400)
                self.assertFalse(result["ok"])
                self.assertTrue(result["error"])
        self.assertEqual(self._count(), before)

    @mute_logger("odoo.addons.zalo_oa.models.zalo_message")
    def test_send_reports_a_failed_queue(self):
        model = type(self.env["zalo.message"])
        with patch.object(model, "_queue_values", side_effect=RuntimeError("boom")):
            status, result = self._call(VALID)
        self.assertEqual(status, 200)
        self.assertFalse(result["ok"])
        self.assertTrue(result["id"])
        self.assertIn("RuntimeError", result["error"])
