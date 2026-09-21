# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNonconformityHeader(TransactionCase):
    """Header defaults, the relaxed partner and the disposition.

    post_install for the same reason as the item tests: the fixtures create
    records of models that modules loading after this one extend.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["mgmtsystem.nonconformity"]
        cls.origin = cls.env.ref("mgmtsystem_nonconformity.nc_origin_qc")

    def _values(self, **extra):
        values = {
            "description": "Raised without a partner",
            "origin_ids": [(6, 0, self.origin.ids)],
            "responsible_user_id": self.env.user.id,
            "manager_user_id": self.env.user.id,
            "user_id": self.env.user.id,
        }
        values.update(extra)
        return values

    def test_partner_optional(self):
        nonconformity = self.model.create(self._values())
        self.assertFalse(nonconformity.partner_id)

    def test_default_responsible_is_current_user(self):
        defaults = self.model.default_get(["responsible_user_id"])
        self.assertEqual(defaults.get("responsible_user_id"), self.env.user.id)

    def test_default_manager_from_employee(self):
        manager_user = self.env["res.users"].create(
            {"name": "Line Manager", "login": "qms_line_manager"}
        )
        employee = self.env["hr.employee"]
        manager_employee = employee.create(
            {"name": "Line Manager", "user_id": manager_user.id}
        )
        reporter_user = self.env["res.users"].create(
            {"name": "Reporter", "login": "qms_reporter"}
        )
        employee.create(
            {
                "name": "Reporter",
                "user_id": reporter_user.id,
                "parent_id": manager_employee.id,
            }
        )
        defaults = self.model.with_user(reporter_user).default_get(
            ["responsible_user_id", "manager_user_id"]
        )
        self.assertEqual(defaults.get("responsible_user_id"), reporter_user.id)
        self.assertEqual(defaults.get("manager_user_id"), manager_user.id)

    def test_default_manager_without_employee(self):
        user = self.env["res.users"].create(
            {"name": "No Employee", "login": "qms_no_employee"}
        )
        defaults = self.model.with_user(user).default_get(["manager_user_id"])
        self.assertFalse(defaults.get("manager_user_id"))

    def test_disposition_tracked(self):
        nonconformity = self.model.create(self._values())
        self.assertFalse(nonconformity.disposition)
        # create() calls _track_discard (mail/models/mail_thread.py:335),
        # which parks None against this record in the precommit data and
        # suppresses tracking for the rest of the transaction. Running the
        # queue pops it, so the write below is tracked as it would be in a
        # later request.
        self.env.cr.precommit.run()
        before = len(nonconformity.message_ids)

        nonconformity.disposition = "scrap"
        self.assertEqual(nonconformity.disposition, "scrap")
        # Tracking messages are written from the same precommit queue
        # (mail_thread.py:513), which a test transaction never reaches.
        self.env.cr.precommit.run()
        nonconformity.invalidate_recordset(["message_ids"])
        self.assertGreater(len(nonconformity.message_ids), before)
