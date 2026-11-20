# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from .common import AccountCase


@tagged("post_install", "-at_install")
class TestPaymentEntry(AccountCase):
    def _advance_paid(self, employee, amount, paid_date=D(2026, 10, 16)):
        """An approved advance paid through its own payment list."""
        advance = self._advance(employee, amount, state="approved")
        action = self._advances(self.officer).browse(advance.id).action_create_payment()
        payment = self.env["l10n_vn.payroll.payment"].browse(action["res_id"])
        self._pay(payment, "transfer", paid_date)
        return advance, payment

    def test_transfer_entry(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "transfer", D(2026, 11, 10))
        move = payment.line_ids.l10n_vn_move_id
        self.assertEqual(len(move), 1)
        self.assertEqual(move.journal_id, self.bank)
        self.assertEqual(move.date, D(2026, 11, 10))
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.l10n_vn_payroll_payment_id, payment)
        self.assertEqual(sum(self._lines(move, "1132").mapped("credit")), payment.amount_total)
        for employee in (self.alice, self.bao):
            line = payment.line_ids.filtered(lambda l: l.employee_id == employee)
            debit = self._lines(move, "3341", employee.work_contact_id)
            self.assertEqual(debit.debit, line.amount)
            self.assertEqual(self._residual(employee), 0)

    def test_cash_entry(self):
        cash_type = self.env.ref("l10n_vn_payroll.participant_labour").copy(
            {"code": "TEST_CASH_POSTED", "name": "Test posted, paid in cash",
             "paid_by_transfer": False}
        )
        self.bao_contract.l10n_vn_participant_type_id = cash_type
        run = self._approved_run_noted()
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "cash", D(2026, 11, 10))
        bao_line = payment.line_ids.filtered(lambda l: l.employee_id == self.bao)
        self.assertEqual(bao_line.l10n_vn_move_id.journal_id, self.cash)
        self.assertEqual(self._residual(self.bao), 0)

    def test_advance_before_run(self):
        _advance, advance_list = self._advance_paid(self.alice, 1000000)
        move = advance_list.line_ids.l10n_vn_move_id
        self.assertEqual(self._lines(move, "3341", self.alice.work_contact_id).debit, 1000000)
        self.assertEqual(self._residual(self.alice), 1000000)
        run = self._approved_run()
        alice = self._slip(run, self.alice)
        self.assertEqual(alice.l10n_vn_advance, 1000000)
        self.assertEqual(self._residual(self.alice), -alice.l10n_vn_to_pay)
        self._pay(run.l10n_vn_payment_ids, "transfer", D(2026, 11, 10))
        self.assertEqual(self._residual(self.alice), 0)

    def test_carried_advance_open(self):
        self._advance_paid(self.alice, 5000000)
        run = self._approved_run_noted()
        alice = self._slip(run, self.alice)
        self.assertEqual(alice.l10n_vn_to_pay, 0)
        self.assertEqual(self._residual(self.alice), 5000000 - alice.l10n_vn_net)

    def test_missing_journal(self):
        self.company.l10n_vn_payroll_bank_journal_id = False
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        with self.assertRaises(UserError):
            self._pay(payment, "transfer")
        self.assertEqual(set(payment.line_ids.mapped("state")), {"to_pay"})
