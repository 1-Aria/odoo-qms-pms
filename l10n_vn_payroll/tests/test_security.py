# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestSecurity(PayrollCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salary = cls._component("SALARY")
        cls.officer = cls._user("test.l10n_vn_payroll.officer", ["payroll.group_payroll_user"])

    def test_new_user_template(self):
        template = self.env.ref("base.default_user")
        self.assertNotIn(self.env.ref("payroll.group_payroll_user"), template.groups_id)
        self.assertNotIn(self.env.ref("payroll.group_payroll_manager"), template.groups_id)

    def test_manager_manages_parameters(self):
        manager = self.env.ref("payroll.group_payroll_manager")
        self.assertIn(
            self.env.ref("base_time_parameter.group_time_parameter"),
            manager.trans_implied_ids,
        )

    def test_officer_sees_all_payslips(self):
        manager_user = self._user("test.l10n_vn_payroll.dept_manager", [])
        manager_employee = self.env["hr.employee"].create(
            {
                "name": "Payroll Test Department Manager",
                "company_id": self.company.id,
                "user_id": manager_user.id,
            }
        )
        self.department.manager_id = manager_employee
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "company_id": self.company.id,
                "date_from": D(2026, 10, 1),
                "date_to": D(2026, 10, 31),
            }
        )
        found = self._as(self.officer)["hr.payslip"].search([("id", "=", payslip.id)])
        self.assertEqual(found, payslip)

    def test_hr_user_cannot_read_pay_lines(self):
        self.env["l10n_vn.payroll.contract.line"].create(
            {
                "contract_id": self.contract.id,
                "component_id": self.salary.id,
                "amount": 1000,
                "date_from": D(2026, 1, 1),
            }
        )
        hr_user = self._user(
            "test.l10n_vn_payroll.hr_user", ["hr_contract.group_hr_contract_manager"]
        )
        contract = self.contract.with_env(self._as(hr_user))
        self.assertEqual(contract.name, "Payroll Test Contract")
        with self.assertRaises(AccessError):
            self._as(hr_user)["l10n_vn.payroll.contract.line"].search([])

    def test_officer_writes_pay_lines(self):
        Line = self._as(self.officer)["l10n_vn.payroll.contract.line"]
        line = Line.create(
            {
                "contract_id": self.contract.id,
                "component_id": self.salary.id,
                "amount": 1000,
                "date_from": D(2026, 1, 1),
            }
        )
        line.amount = 2000
        self.assertEqual(line.amount, 2000)
        with self.assertRaises(AccessError):
            self._as(self.officer)["l10n_vn.payroll.component"].create(
                {
                    "code": "TEST_OFFICER",
                    "name": "Officer",
                    "company_id": self.company.id,
                    "kind": "earning",
                    "legal_nature": "bonus",
                    "pit_treatment": "taxable",
                    "amount_source": "entered",
                }
            )
