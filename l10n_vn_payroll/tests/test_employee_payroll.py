# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestEmployeePayroll(PayrollCase):
    def _relative(self, employee=None, relation="child", env=None, **values):
        vals = {
            "employee_id": (employee or self.employee).id,
            "relation_id": self.env.ref(f"hr_employee_relative.relation_{relation}").id,
            "name": f"Payroll Test {relation}",
        }
        vals.update(values)
        return (env or self.env)["hr.employee.relative"].create(vals)

    def test_attendance_mode_follows_pay_group(self):
        employee = self.employee
        employee.l10n_vn_pay_group = "worker"
        self.assertEqual(employee.l10n_vn_attendance_mode, "scan")
        employee.l10n_vn_pay_group = "office"
        self.assertEqual(employee.l10n_vn_attendance_mode, "exception")
        employee.l10n_vn_attendance_mode = "scan"
        self.assertEqual(employee.l10n_vn_attendance_mode, "scan")

    def test_region_default(self):
        self.env["base.time.parameter"].create(
            {
                "name": "vn.policy.region",
                "code": "vn.policy.region",
                "type": "string",
                "company_id": self.company.id,
                "version_ids": [Command.create({"date_from": D(2026, 1, 1), "value": "IV"})],
            }
        )
        employee = self.env["hr.employee"].with_company(self.company).create(
            {"name": "Payroll Test Region IV", "company_id": self.company.id}
        )
        self.assertEqual(employee.l10n_vn_region, "IV")
        other = self.env["res.company"].create({"name": "Payroll Test No Region"})
        employee_other = self.env["hr.employee"].with_company(other).create(
            {"name": "Payroll Test No Region", "company_id": other.id}
        )
        self.assertFalse(employee_other.l10n_vn_region)

    def test_dependent_count(self):
        self._relative(l10n_vn_pit_dependent=True, l10n_vn_from=D(2026, 3, 1), l10n_vn_to=D(2026, 8, 1))
        self._relative(relation="parent")
        count = self.employee._l10n_vn_dependent_count
        self.assertEqual(count(D(2026, 2, 15)), 0)
        self.assertEqual(count(D(2026, 3, 31)), 1)
        self.assertEqual(count(D(2026, 8, 20)), 1)
        self.assertEqual(count(D(2026, 9, 1)), 0)

    def test_dependent_dates(self):
        with self.assertRaises(ValidationError):
            self._relative(l10n_vn_pit_dependent=True)
        with self.assertRaises(ValidationError):
            self._relative(l10n_vn_pit_dependent=True, l10n_vn_from=D(2026, 3, 15))
        with self.assertRaises(ValidationError):
            self._relative(
                l10n_vn_pit_dependent=True, l10n_vn_from=D(2026, 3, 1), l10n_vn_to=D(2026, 2, 1)
            )

    def test_hr_user_cannot_read_pay_fields(self):
        hr_user = self._user("test.l10n_vn_payroll.employee_hr_user", ["hr.group_hr_user"])
        employee = self.employee.with_env(self._as(hr_user))
        self.assertEqual(employee.name, "Payroll Test Employee")
        with self.assertRaises(AccessError):
            employee.read(["l10n_vn_pay_group"])

    def test_officer_registers_dependent(self):
        officer = self._user("test.l10n_vn_payroll.relative_officer", ["payroll.group_payroll_user"])
        relative = self._relative(
            env=self._as(officer),
            l10n_vn_pit_dependent=True,
            l10n_vn_tax_code="8000000000",
            l10n_vn_from=D(2026, 1, 1),
        )
        self.assertEqual(self.employee._l10n_vn_dependent_count(D(2026, 1, 1)), 1)
        self.assertEqual(relative.employee_id, self.employee)
