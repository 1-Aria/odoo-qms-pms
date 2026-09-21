# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNonconformityDepartment(TransactionCase):
    """post_install: the fixtures create users and employees."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["mgmtsystem.nonconformity"]
        cls.department = cls.env["hr.department"].create({"name": "Sewing"})

    def test_default_department_from_employee(self):
        user = self.env["res.users"].create(
            {"name": "Sewing Operator", "login": "qms_sewing_operator"}
        )
        self.env["hr.employee"].create(
            {
                "name": "Sewing Operator",
                "user_id": user.id,
                "department_id": self.department.id,
            }
        )
        defaults = self.model.with_user(user).default_get(["department_id"])
        self.assertEqual(defaults.get("department_id"), self.department.id)

    def test_default_department_without_employee(self):
        user = self.env["res.users"].create(
            {"name": "No Employee", "login": "qms_hr_no_employee"}
        )
        defaults = self.model.with_user(user).default_get(["department_id"])
        self.assertFalse(defaults.get("department_id"))
