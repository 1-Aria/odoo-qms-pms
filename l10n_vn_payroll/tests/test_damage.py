# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import D
from .payslip_common import PayslipCase


@tagged("post_install", "-at_install")
class TestDamage(PayslipCase):
    def _salary(self, amount=4500000):
        return self._hire(lines=[(self.sal, {"amount": amount})])

    def test_carry_forward(self):
        employee, _contract = self._hire(lines=[
            (self.sal, {"amount": 4500000}),
            (self.skill, {"amount": 1500000}),
            (self.att, {"amount": 300000}),
            (self.travel, {"amount": 200000}),
        ])
        damage = self._damage(employee, 3000000)
        self._input(employee, ot_hours_json={"WD": 20}, ie_units=1000)
        first = self._payslip(employee)
        first.state = "done"
        self.assertEqual(damage.deducted, 2470616)
        self.assertEqual(damage.balance, 529384)
        self.assertEqual(damage.state, "open")
        second = self._payslip(employee)
        self.assertEqual(self._totals(second, "DAMAGE"), [-529384])
        second.state = "done"
        self.assertEqual(damage.state, "done")

    def test_oldest_first(self):
        employee, _contract = self._salary()
        older = self._damage(employee, 300000, D(2026, 9, 1))
        newer = self._damage(employee, 2000000, D(2026, 10, 1))
        self._input(employee)
        payslip = self._payslip(employee)
        # cap: 30% x (4,500,000 - 472,500 insurance - 0 PIT) = 1,208,250
        self.assertEqual(self._totals(payslip, "DAMAGE"), [-1208250])
        taken = {a.damage_id: a.amount for a in payslip.l10n_vn_damage_allocation_ids}
        self.assertEqual(taken, {older: 300000, newer: 908250})

    def test_later_decision_waits(self):
        employee, _contract = self._salary()
        self._damage(employee, 300000, D(2026, 11, 5))
        self._input(employee)
        self.assertFalse(self._totals(self._payslip(employee), "DAMAGE"))

    def test_recompute_replaces(self):
        employee, _contract = self._salary()
        self._damage(employee, 300000)
        self._input(employee)
        payslip = self._payslip(employee)
        payslip.compute_sheet()
        self.assertEqual(len(payslip.l10n_vn_damage_allocation_ids), 1)

    def test_cannot_delete_deducted(self):
        employee, _contract = self._salary()
        damage = self._damage(employee, 300000)
        self._input(employee)
        self._payslip(employee).state = "done"
        with self.assertRaises(UserError):
            damage.unlink()

    def test_access(self):
        employee, _contract = self._salary()
        officer = self._user("test.l10n_vn_payroll.damage_officer", ["payroll.group_payroll_user"])
        reader = self._user("test.l10n_vn_payroll.damage_reader", ["l10n_vn_payroll.group_payroll_reader"])
        vals = {
            "employee_id": employee.id,
            "company_id": self.company.id,
            "decision_ref": "TEST-ACCESS",
            "decision_date": D(2026, 10, 1),
            "reason": "Test",
            "amount": 100000,
        }
        self._as(officer)["l10n_vn.payroll.damage"].create(vals)
        with self.assertRaises(AccessError):
            self._as(reader)["l10n_vn.payroll.damage"].create(dict(vals, decision_ref="TEST-2"))
