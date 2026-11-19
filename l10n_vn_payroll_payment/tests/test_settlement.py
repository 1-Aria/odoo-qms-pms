# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D
from odoo.addons.l10n_vn_payroll.tests.group_g import WORKER, GroupGCases
from odoo.addons.l10n_vn_payroll.tests.payslip_common import PayslipCase

from .common import AdvanceCase, AdvanceMixin


@tagged("post_install", "-at_install")
class TestSettlement(AdvanceCase):
    def _settled(self, payslip):
        return {s.advance_id: s.amount for s in payslip.l10n_vn_advance_settlement_ids}

    def test_oldest_first(self):
        newer = self._paid_advance(self.alice, 3000000, D(2026, 10, 10))
        older = self._paid_advance(self.alice, 3000000, D(2026, 10, 1))
        payslip = self._payslip(self.alice)
        net = payslip.l10n_vn_net
        self.assertGreater(net, 3000000)
        self.assertEqual(self._settled(payslip), {older: 3000000, newer: net - 3000000})
        ids = [a["id"] for a in payslip.l10n_vn_context["advances"]]
        self.assertEqual(ids, [older.id, newer.id])
        self.assertEqual(payslip.l10n_vn_advance, net)
        self.assertEqual(payslip.l10n_vn_to_pay, 0)

    def test_paid_after_month_end_waits(self):
        self._paid_advance(self.alice, 1000000, D(2026, 11, 5))
        payslip = self._payslip(self.alice)
        self.assertFalse(payslip.l10n_vn_advance_settlement_ids)
        self.assertEqual(payslip.l10n_vn_advance, 0)

    def test_approved_not_paid_waits(self):
        self._advance(self.alice, 1000000, state="approved")
        payslip = self._payslip(self.alice)
        self.assertFalse(payslip.l10n_vn_advance_settlement_ids)

    def test_recalculate_replaces(self):
        advance = self._paid_advance(self.alice, 1000000)
        payslip = self._payslip(self.alice)
        payslip.compute_sheet()
        self.assertEqual(self._settled(payslip), {advance: 1000000})
        self.assertEqual(len(payslip.l10n_vn_advance_settlement_ids), 1)

    def test_stop_clears(self):
        self._paid_advance(self.alice, 1000000)
        payslip = self._payslip(self.alice)
        self.assertTrue(payslip.l10n_vn_advance_settlement_ids)
        payslip.date_to = D(2026, 10, 30)
        payslip.compute_sheet()
        self.assertTrue(self._results(payslip, "calculation"))
        self.assertFalse(payslip.l10n_vn_advance_settlement_ids)

    def test_balance_moves_at_approval(self):
        advance = self._paid_advance(self.alice, 1000000)
        run = self._new_run()
        self._calculate(run)
        self.assertEqual(self._settled(self._slip(run, self.alice)), {advance: 1000000})
        self.assertEqual(advance.balance, 1000000)
        self._review(run)
        self._approve(run)
        self.assertEqual(advance.settled_amount, 1000000)
        self.assertEqual(advance.balance, 0)

    def test_carried_to_next_payslip(self):
        advance = self._paid_advance(self.alice, 5000000)
        first = self._payslip(self.alice)
        net = first.l10n_vn_net
        self.assertEqual(first.l10n_vn_advance, net)
        self.assertTrue(self._results(first, "advance_carried"))
        first.state = "done"
        self.assertEqual(advance.balance, 5000000 - net)
        second = self._payslip(self.alice)
        self.assertEqual(second.l10n_vn_advance, 5000000 - net)
        second.state = "done"
        self.assertEqual(advance.balance, 0)

    def test_run_approval_rereads_advances(self):
        run = self._new_run()
        self._calculate(run)
        self._review(run)
        self._paid_advance(self.alice, 1000000, D(2026, 10, 20))
        with self.assertRaises(UserError) as caught:
            self._approve(run)
        self.assertIn(self.alice.name, str(caught.exception))
        self.assertEqual(run.state, "reviewed")
        self._calculate(run)
        self._review(run)
        self._approve(run)
        self.assertEqual(self._slip(run, self.alice).l10n_vn_advance, 1000000)

    def test_cancel_refused_once_settled(self):
        advance = self._paid_advance(self.alice, 1000000)
        payslip = self._payslip(self.alice)
        payslip.state = "done"
        with self.assertRaises(UserError):
            self._advances(self.reviewer).browse(advance.id).action_cancel()
        self.assertEqual(advance.state, "paid")


@tagged("post_install", "-at_install")
class TestAdvanceAcceptance(AdvanceMixin, GroupGCases, PayslipCase):
    # only the tests below: group G itself runs in l10n_vn_payroll

    def test_g14_settled(self):
        employee, _contract = self._worker("Entry")
        self._paid_advance(employee, 1500000)
        payslip = self._run("G14", employee, WORKER, **self._supervised(
            ot_hours_json={"WD": 20}, lines=[(self.eff, {"amount": 300000})]))
        data = self._cases()["G14"]
        self.assertEqual(self._totals(payslip, "ADVANCE"), [-data["settled"]])
        self.assertEqual(payslip.l10n_vn_advance, data["settled"])
        self.assertEqual(payslip.l10n_vn_to_pay, data["to_pay"])

    def test_g15_carried(self):
        employee, _contract = self._worker("Entry")
        advance = self._paid_advance(employee, 2000000)
        payslip = self._run("G15", employee, ["BASE", "PROD"], **self._supervised(
            paid_days=10, days_worked=10, unpaid_days=16))
        data = self._cases()["G15"]
        self.assertEqual(payslip.l10n_vn_to_pay, 0)
        self.assertTrue(self._results(payslip, "advance_carried"))
        payslip.state = "done"
        self.assertEqual(advance.balance, 2000000 - data["settled"])
