# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import ROUND_HALF_UP, Decimal

from odoo import fields
from odoo.tests import tagged

from .common import D
from .payslip_common import PayslipCase


@tagged("post_install", "-at_install")
class TestPit(PayslipCase):
    def _salary(self, amount=4500000, extra=()):
        return self._hire(lines=[(self.sal, {"amount": amount}), *extra])

    @staticmethod
    def _pit(payslip):
        return payslip.l10n_vn_context["pit"]

    def _approve(self, lines):
        lines.sudo().write({"approved_by": self.env.uid, "approved_at": fields.Datetime.now()})

    def test_year_limit(self):
        employee, _contract = self._salary()
        self._input(employee, ot_hours_json={"WD": 20}, ot_hours_ytd=290)
        payslip = self._payslip(employee)
        ot_pay = self._totals(payslip, "OT_WD")[0]
        expected = (Decimal(str(ot_pay)) * 10 / 20).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        self.assertEqual(self._pit(payslip)["ot_exempt"], int(expected))

    def test_adjustment_own_month(self):
        september = self.env["l10n_vn.payroll.period"].create(
            {"date_from": D(2026, 9, 1), "company_id": self.company.id}
        )
        employee, _contract = self._salary()
        own = self.env["l10n_vn.payroll.input"].create(
            {"period_id": september.id, "employee_id": employee.id, "figures_locked": True,
             "ot_hours_json": {"WD": 38}}
        )
        inp = self._input(employee, lines=[(self.ot_wd, {
            "amount": 100000, "hours": 4, "period_ref": D(2026, 9, 1)})])
        payslip = self._payslip(employee)
        self.assertEqual(self._pit(payslip)["ot_exempt"], 50000)
        own.unlink()
        payslip.compute_sheet()
        self.assertEqual(self._pit(payslip)["ot_exempt"], 100000)
        inp.line_ids.hours = 0
        self._approve(inp.line_ids)
        payslip.compute_sheet()
        self.assertEqual(self._pit(payslip)["ot_exempt"], 0)

    def test_exempt_cap_shared(self):
        meal2 = self._component("MEAL2", legal_nature="welfare", pit_treatment="exempt_cap",
                                pit_cap_parameter="vn.pit.meal_cap", proration="none")
        self._rule(meal2)
        employee, _contract = self._salary(
            extra=[(self.meal, {"amount": 1000000}), (meal2, {"amount": 500000})]
        )
        self._input(employee)
        self.assertEqual(self._pit(self._payslip(employee))["exempt"], 1200000)

    def test_non_resident(self):
        employee, _contract = self._salary(10000000)
        employee.l10n_vn_resident = False
        self._dependents(employee, 1)
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._pit(payslip)["method"], "flat_nonresident")
        self.assertEqual(self._totals(payslip, "PIT"), [-2000000])

    def test_negative_taxable(self):
        employee, _contract = self._salary()
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "PIT"), [0])
        self.assertLess(self._pit(payslip)["taxable"], 0)

    def test_deduction_entered_positive(self):
        uniform = self._component("UNIFORM", kind="deduction", legal_nature="damage",
                                  amount_source="entered", pit_treatment=False, proration=False)
        self._rule(uniform)
        employee, _contract = self._salary()
        self._input(employee, lines=[(uniform, {"amount": 100000})])
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "UNIFORM"), [-100000])
        # 4,500,000 less 10.5% insurance, no PIT, less the 100,000
        self.assertEqual(self._totals(payslip, "NET"), [3927500])
