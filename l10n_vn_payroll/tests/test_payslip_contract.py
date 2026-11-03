# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_FROM, OCT_TO, PayslipCase


@tagged("post_install", "-at_install")
class TestPayslipContract(PayslipCase):
    def test_main_contract_latest(self):
        employee, _first = self._hire(date_end=D(2026, 10, 14), state="close")
        _employee, second = self._hire(employee=employee, date_start=D(2026, 10, 15))
        self._input(employee, segments=self._halves())
        payslip = self._payslip(employee)
        self.assertEqual(payslip.contract_id, second)
        self.assertEqual(len(payslip.line_ids.filtered(lambda l: l.code == "TEST_GROSS")), 1)

    def test_leaver_closed_contract(self):
        employee, contract = self._hire(date_end=D(2026, 10, 20), state="close")
        vals = self.env["hr.payslip"].get_payslip_vals(OCT_FROM, OCT_TO, employee.id)["value"]
        self.assertEqual(vals["contract_id"], contract.id)
        self.assertFalse(employee._get_contracts(OCT_FROM, OCT_TO))

    def test_form_without_contract(self):
        employee, contract = self._hire()
        self._input(employee)
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "date_from": OCT_FROM,
                "date_to": OCT_TO,
                "struct_id": self.structure.id,
                "company_id": self.company.id,
            }
        )
        payslip.compute_sheet()
        self.assertEqual(payslip.contract_id, contract)

    def test_worked_days_from_input(self):
        employee, _contract = self._hire()
        self._input(
            employee,
            paid_days=24,
            days_worked=22,
            unpaid_days=2,
            leave_days_json={"Annual leave": 2},
        )
        payslip = self._payslip(employee)
        days = {(w.code, w.name): w.number_of_days for w in payslip.worked_days_line_ids}
        self.assertEqual(
            days,
            {
                ("PAID", "Paid days"): 24,
                ("WORKED", "Days worked"): 22,
                ("UNPAID", "Unpaid days"): 2,
                ("LEAVE", "Annual leave"): 2,
            },
        )

    def test_worked_days_refreshed(self):
        employee, _contract = self._hire()
        inp = self._input(employee)
        payslip = self._payslip(employee)
        inp.paid_days = 25
        payslip.compute_sheet()
        paid = payslip.worked_days_line_ids.filtered(lambda w: w.code == "PAID")
        self.assertEqual(paid.number_of_days, 25)

    def test_other_structure_untouched(self):
        other = self.env["hr.payroll.structure"].create(
            {"name": "TEST OTHER", "code": "TEST_OTHER", "company_id": self.company.id}
        )
        employee, _contract = self._hire(struct_id=other.id)
        Payslip = self.env["hr.payslip"]
        vals = Payslip.get_payslip_vals(OCT_FROM, OCT_TO, employee.id)["value"]
        self.assertEqual(vals["contract_id"], employee.contract_id.id)
        self.assertIn("WORK100", [w["code"] for w in vals["worked_days_line_ids"]])
        payslip = Payslip.create(
            {
                "employee_id": employee.id,
                "date_from": OCT_FROM,
                "date_to": OCT_TO,
                "contract_id": vals["contract_id"],
                "struct_id": vals["struct_id"],
                "company_id": self.company.id,
            }
        )
        payslip.compute_sheet()
        self.assertFalse(payslip.l10n_vn_context)

    def test_month_only(self):
        employee, contract = self._hire()
        self._input(employee)
        payslip = self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "date_from": D(2026, 10, 5),
                "date_to": OCT_TO,
                "contract_id": contract.id,
                "struct_id": self.structure.id,
                "company_id": self.company.id,
            }
        )
        payslip.compute_sheet()
        self._stopped(payslip, "calculation", "calendar month")
        self.assertEqual(payslip.state, "draft")

    def test_no_input(self):
        employee, _contract = self._hire()
        self._stopped(self._payslip(employee), "calculation", employee.name)
