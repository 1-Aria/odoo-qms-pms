# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from .common import AccountCase


@tagged("post_install", "-at_install")
class TestRunEntry(AccountCase):
    def test_entry_at_approval(self):
        # the approver has no accounting rights: posting runs as superuser
        run = self._approved_run()
        move = run.l10n_vn_move_id
        self.assertTrue(move)
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.journal_id, self.journal)
        self.assertEqual(move.date, D(2026, 10, 31))
        self.assertEqual(move.l10n_vn_payroll_run_id, run)
        self.assertAlmostEqual(sum(move.line_ids.mapped("debit")), sum(move.line_ids.mapped("credit")))

    def test_lines_by_kind(self):
        run = self._approved_run()
        move = run.l10n_vn_move_id
        alice, bao = self._slip(run, self.alice), self._slip(run, self.bao)
        self.assertEqual(
            sum(self._lines(move, "6220").mapped("debit")),
            alice.l10n_vn_gross + alice.l10n_vn_employer_cost,
        )
        self.assertEqual(
            sum(self._lines(move, "6421").mapped("debit")),
            bao.l10n_vn_gross + bao.l10n_vn_employer_cost,
        )
        alice_3341 = self._lines(move, "3341", self.alice.work_contact_id)
        self.assertEqual(sum(alice_3341.mapped("credit")), alice.l10n_vn_gross)
        deductions = alice.line_ids.filtered(
            lambda l: l.l10n_vn_component_id.kind == "deduction" and l.total
        )
        self.assertEqual(len(alice_3341.filtered("debit")), len(deductions.l10n_vn_component_id))
        self.assertEqual(sum(alice_3341.mapped("debit")), -sum(deductions.mapped("total")))
        si = sum(
            -self._component_total(slip, "EE_SI")
            + sum(self._component_total(slip, code)
                  for code in ("ER_PENSION", "ER_SICKNESS", "ER_ACCIDENT"))
            for slip in (alice, bao)
        )
        self.assertEqual(sum(self._lines(move, "33831").mapped("credit")), si)

    def test_residual_is_to_pay(self):
        run = self._approved_run()
        for employee in (self.alice, self.bao):
            self.assertEqual(self._residual(employee), -self._slip(run, employee).l10n_vn_to_pay)

    def test_cost_group_from_parent_and_contract(self):
        # Sewing has no group: Production's; then a contract override
        self.alice_contract.l10n_vn_cost_group_id = self.admin_group
        run = self._approved_run()
        alice, bao = self._slip(run, self.alice), self._slip(run, self.bao)
        self.assertFalse(self._lines(run.l10n_vn_move_id, "6220"))
        self.assertEqual(
            sum(self._lines(run.l10n_vn_move_id, "6421").mapped("debit")),
            alice.l10n_vn_gross + alice.l10n_vn_employer_cost
            + bao.l10n_vn_gross + bao.l10n_vn_employer_cost,
        )

    def test_damage_to_its_account(self):
        self._damage(self.alice, 300000)
        run = self._approved_run()
        damage = self._lines(run.l10n_vn_move_id, "7110")
        self.assertEqual(sum(damage.mapped("credit")), 300000)
        self.assertFalse(damage.partner_id)

    def test_casual_not_posted(self):
        self.bao_contract.l10n_vn_participant_type_id = self.env.ref(
            "l10n_vn_payroll.participant_casual"
        )
        run = self._approved_run_noted()
        move = run.l10n_vn_move_id
        self.assertFalse(move.line_ids.filtered(lambda l: l.partner_id == self.bao.work_contact_id))
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "cash")
        bao_line = payment.line_ids.filtered(lambda l: l.employee_id == self.bao)
        self.assertEqual(bao_line.state, "paid")
        self.assertFalse(bao_line.l10n_vn_move_id)

    def test_posting_check(self):
        self.alice_contract.department_id = self.env["hr.department"].create(
            {"name": "Test No Group", "company_id": self.company.id}
        )
        self.engine["EE_SI"].l10n_vn_account_id = False
        self.company.l10n_vn_payroll_journal_id = False
        rule = self.structure.rule_ids.filtered(lambda r: r.code == self.sal.code)
        rule.account_debit = self.acc["6220"]
        run = self._new_run()
        self._calculate(run)
        result = self._results(self._slip(run, self.alice), "posting")
        self.assertEqual(result.level, "error")
        for text in ("payroll journal", "Test No Group", self.engine["EE_SI"].code, rule.code):
            self.assertIn(text, result.message)
        with self.assertRaises(UserError):
            self._review(run)

    def test_posting_off(self):
        # a company that does not post: no check, no entry, payments without entries (D11)
        self.company.l10n_vn_payroll_post = False
        self.company.l10n_vn_payroll_journal_id = False
        run = self._approved_run()
        self.assertFalse(run.l10n_vn_move_id)
        self.assertFalse(run.l10n_vn_check_result_ids.filtered(lambda r: r.check_id.code == "posting"))
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "transfer")
        self.assertEqual(payment.state, "paid")
        self.assertFalse(payment.line_ids.l10n_vn_move_id)

    def test_run_journal_default(self):
        run = self.env["hr.payslip.run"].create(
            {"l10n_vn_period_id": self.period.id, "l10n_vn_kind": "off_cycle"}
        )
        self.assertEqual(run.journal_id, self.journal)
