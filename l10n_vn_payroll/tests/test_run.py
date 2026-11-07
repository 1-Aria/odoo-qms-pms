# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .payslip_common import OCT_FROM, OCT_TO
from .run_common import RunCase


@tagged("post_install", "-at_install")
class TestRun(RunCase):
    def test_create_from_period(self):
        run = self._new_run()
        self.assertEqual((run.date_start, run.date_end), (OCT_FROM, OCT_TO))
        self.assertEqual(run.company_id, self.company)
        self.assertIn(self.period.name, run.name)
        with self.assertRaises(ValidationError):
            self._new_run()
        self.assertTrue(self._new_run("off_cycle", self.alice))

    def test_calculate_needs_closed_period(self):
        self.period.attendance_closed = False
        run = self._new_run()
        with self.assertRaisesRegex(UserError, "2026-10"):
            self._calculate(run)

    def test_calculate_generates_payslips(self):
        other = self.env["hr.payroll.structure"].create(
            {"name": "TEST OTHER", "code": "TEST_OTHER", "company_id": self.company.id}
        )
        self._hire(struct_id=other.id)
        run = self._new_run()
        self._calculate(run)
        self.assertEqual(run.slip_ids.employee_id, self.alice | self.bao)
        self.assertEqual(set(run.slip_ids.mapped("state")), {"verify"})
        self.assertEqual(run.state, "calculated")
        self.assertEqual(run.l10n_vn_calculated_by, self.officer)

    def test_recalculate_repeatable(self):
        run = self._new_run()
        self._calculate(run)
        first = (run.slip_ids.ids, [self._totals(p, "NET") for p in run.slip_ids])
        self._calculate(run)
        self.assertEqual((run.slip_ids.ids, [self._totals(p, "NET") for p in run.slip_ids]), first)

    def test_employee_leaves_run(self):
        run = self._new_run()
        self._calculate(run)
        other = self.env["hr.payroll.structure"].create(
            {"name": "TEST OTHER", "code": "TEST_OTHER", "company_id": self.company.id}
        )
        self.bao_contract.struct_id = other
        self._calculate(run)
        self.assertEqual(run.slip_ids.employee_id, self.alice)

    def test_review_blocked(self):
        inp = self.period.input_ids.filtered(lambda i: i.employee_id == self.alice)
        line = self.env["l10n_vn.payroll.input.line"].create(
            {"input_id": inp.id, "component_id": self.one.id, "amount": 500000}
        )
        run = self._new_run()
        self._calculate(run)
        with self.assertRaisesRegex(UserError, self.alice.name):
            self._review(run)
        line.sudo().write({"approved_by": self.env.uid, "approved_at": fields.Datetime.now()})
        self.travel.in_ot_base = True
        self._line(self.travel, contract=self.bao_contract, amount=200000)
        self._calculate(run)
        with self.assertRaisesRegex(UserError, self.bao.name):
            self._review(run)
        warning = run.l10n_vn_check_result_ids.filtered(lambda r: r.level == "warning")
        self._as(self.reviewer)["l10n_vn.payroll.check.result"].browse(warning.ids).write(
            {"note": "Travel counts in the OT base by decision."}
        )
        self._review(run)
        self.assertEqual(run.state, "reviewed")
        self.assertEqual(run.l10n_vn_reviewed_by, self.reviewer)

    def test_review_reviewer_only(self):
        run = self._new_run()
        self._calculate(run)
        with self.assertRaises(AccessError):
            self._review(run, self.officer)

    def test_recalculate_sends_back(self):
        run = self._new_run()
        self._calculate(run)
        self._review(run)
        run.slip_ids[:1].compute_sheet()
        self.assertEqual(run.state, "calculated")
        self.assertFalse(run.l10n_vn_reviewed_by)

    def test_approve(self):
        run = self._approved_run()
        self.assertEqual(run.state, "approved")
        self.assertEqual(set(run.slip_ids.mapped("state")), {"done"})
        self.assertEqual(run.l10n_vn_approved_by, self.approver)
        if "move_id" in run.slip_ids._fields:
            self.assertFalse(run.slip_ids.move_id)

    def test_approve_needs_review(self):
        run = self._new_run()
        self._calculate(run)
        with self.assertRaisesRegex(UserError, "after review"):
            self._approve(run)

    def test_segregation(self):
        run = self._new_run()
        self._calculate(run, self.officer_approver)
        self._review(run)
        with self.assertRaisesRegex(UserError, "calculated"):
            self._approve(run, self.officer_approver)
        self._approve(run)
        self.assertEqual(run.state, "approved")

    def test_no_way_back(self):
        run = self._approved_run()
        with self.assertRaises(UserError):
            self._runs(self.reviewer).browse(run.id).action_l10n_vn_back_to_calculated()
        with self.assertRaises(UserError):
            self._calculate(run)
        with self.assertRaises(UserError):
            run.draft_payslip_run()

    def test_mark_paid(self):
        run = self._approved_run()
        with self.assertRaises(AccessError):
            self._runs(self.reader).browse(run.id).action_l10n_vn_mark_paid()
        self._runs(self.officer).browse(run.id).action_l10n_vn_mark_paid()
        self.assertEqual(run.state, "paid")

    def test_off_cycle(self):
        self._approved_run("off_cycle", self.alice)
        run = self._new_run()
        self._calculate(run)
        self.assertEqual(run.slip_ids.employee_id, self.bao)

    def test_one_payment(self):
        first = self._new_run("off_cycle", self.alice)
        second = self._new_run("off_cycle", self.alice)
        for run in (first, second):
            self._calculate(run)
            self._review(run)
        self._approve(first)
        with self.assertRaisesRegex(UserError, self.alice.name):
            self._approve(second)

    def test_other_runs_untouched(self):
        run = self.env["hr.payslip.run"].create(
            dict(
                {"name": "TEST OCA run", "date_start": OCT_FROM, "date_end": OCT_TO,
                 "company_id": self.company.id},
                **({"journal_id": self.journal.id} if self.journal else {}),
            )
        )
        run.close_payslip_run()
        self.assertEqual(run.state, "close")
        run.draft_payslip_run()
        self.assertEqual(run.state, "draft")
