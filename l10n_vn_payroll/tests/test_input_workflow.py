# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import D
from .input_common import InputCase


@tagged("post_install", "-at_install")
class TestInputWorkflow(InputCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.inp = cls.env["l10n_vn.payroll.input"].create(
            {"period_id": cls.period.id, "employee_id": cls.employee.id}
        )
        cls.bonus = cls._component(
            "ONE", legal_nature="bonus", amount_source="entered", proration=False
        )
        cls.officer = cls._user("test.l10n_vn_payroll.input_officer", ["payroll.group_payroll_user"])

    def test_close_freezes_figures(self):
        self.period.action_close_attendance()
        with self.assertRaises(UserError):
            self.inp.paid_days = 10
        self.inp.attainment = 0.9
        self.assertEqual(self.inp.attainment, 0.9)
        with self.assertRaises(UserError):
            self.period.action_build()

    def test_reopen_managers_only(self):
        self.period.action_close_attendance()
        with self.assertRaises(AccessError):
            self.period.with_env(self._as(self.officer)).action_reopen_attendance()
        manager = self._user("test.l10n_vn_payroll.input_manager", ["payroll.group_payroll_manager"])
        self.period.with_env(self._as(manager)).action_reopen_attendance()
        self.assertFalse(self.period.attendance_closed)

    def test_override_needs_note(self):
        with self.assertRaises(ValidationError):
            self.inp.attainment_source = "override"
        self.inp.write({"attainment_source": "override", "attainment_note": "Machine stop"})

    def test_line_rules(self):
        salary = self._component("SALARY")
        Line = self.env["l10n_vn.payroll.input.line"]
        with self.assertRaises(ValidationError):
            Line.create({"input_id": self.inp.id, "component_id": salary.id, "amount": 1000})
        with self.assertRaises(ValidationError):
            Line.create(
                {
                    "input_id": self.inp.id,
                    "component_id": salary.id,
                    "amount": 1000,
                    "period_ref": D(2026, 11, 1),
                }
            )
        Line.create(
            {
                "input_id": self.inp.id,
                "component_id": salary.id,
                "amount": 1000,
                "period_ref": D(2026, 9, 1),
            }
        )

    def test_approval(self):
        line = self.env["l10n_vn.payroll.input.line"].create(
            {"input_id": self.inp.id, "component_id": self.bonus.id, "amount": 500000}
        )
        as_officer = line.with_env(self._as(self.officer))
        as_officer.amount = 600000
        self.assertEqual(line.amount, 600000)
        with self.assertRaises(AccessError):
            as_officer.action_approve()
        approver = self._user(
            "test.l10n_vn_payroll.input_approver", ["l10n_vn_payroll.group_payroll_approver"]
        )
        line.with_env(self._as(approver)).action_approve()
        self.assertEqual(line.approved_by, approver)
        line.amount = 700000
        self.assertFalse(line.approved_by)

    def test_one_input_per_employee(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["l10n_vn.payroll.input"].create(
                {"period_id": self.period.id, "employee_id": self.employee.id}
            )
