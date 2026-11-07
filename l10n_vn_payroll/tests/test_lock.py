# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import D
from .run_common import RunCase


@tagged("post_install", "-at_install")
class TestLock(RunCase):
    def _alice_input(self):
        return self.period.input_ids.filtered(lambda i: i.employee_id == self.alice)

    def test_payslip_locked(self):
        run = self._approved_run()
        slip = self._as(self.officer)["hr.payslip"].browse(self._slip(run, self.alice).id)
        with self.assertRaises(UserError):
            slip.line_ids[:1].amount = 1
        with self.assertRaises(UserError):
            slip.note = "Changed after approval"
        with self.assertRaises(UserError):
            slip.action_payslip_draft()
        with self.assertRaises(UserError):
            self._runs(self.officer).browse(run.id).unlink()

    def test_check_result_locked(self):
        self._parameter_text("vn.check.nature", "note")
        self.travel.in_ot_base = True
        self._line(self.travel, contract=self.alice_contract, amount=200000)
        run = self._approved_run()
        result = self._slip(run, self.alice).l10n_vn_check_result_ids[:1]
        self.assertTrue(result)
        with self.assertRaises(UserError):
            self._as(self.reviewer)["l10n_vn.payroll.check.result"].browse(result.id).note = "Late"

    def test_input_locked(self):
        self._approved_run()
        inp = self._as(self.officer)["l10n_vn.payroll.input"].browse(self._alice_input().id)
        with self.assertRaises(UserError):
            inp.attainment = 1
        with self.assertRaises(UserError):
            self._as(self.officer)["l10n_vn.payroll.input.line"].create(
                {"input_id": inp.id, "component_id": self.one.id, "amount": 1000}
            )
        with self.assertRaises(UserError):
            self._as(self.manager)["l10n_vn.payroll.period"].browse(
                self.period.id
            ).action_reopen_attendance()

    def test_input_open_before_approval(self):
        run = self._new_run()
        self._calculate(run)
        self._review(run)
        inp = self._as(self.officer)["l10n_vn.payroll.input"].browse(self._alice_input().id)
        inp.attainment = 1
        self._as(self.officer)["l10n_vn.payroll.input.line"].create(
            {"input_id": inp.id, "component_id": self.one.id, "amount": 1000}
        )
        self.assertEqual(inp.attainment, 1)

    def test_pay_line_locked(self):
        self._approved_run()
        line = self._as(self.officer)["l10n_vn.payroll.contract.line"].browse(
            self.alice_contract.sudo().l10n_vn_line_ids.ids
        )
        with self.assertRaises(UserError):
            line.amount = 5000000
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            line.date_to = D(2026, 10, 15)
        line.date_to = D(2026, 11, 30)
        self.assertEqual(line.date_to, D(2026, 11, 30))

    def test_unused_line_free(self):
        self._approved_run()
        skill = self._line(self.skill, contract=self.alice_contract, amount=1000000,
                           date_from=D(2026, 11, 1))
        line = self._as(self.officer)["l10n_vn.payroll.contract.line"].browse(skill.id)
        line.amount = 1500000
        self.assertEqual(line.amount, 1500000)

    def test_access_approver_reader(self):
        run = self._approved_run()
        self.assertTrue(self._runs(self.officer).browse(run.id).name)
        for user in (self.approver, self.reader):
            as_user = self._runs(user).browse(run.id)
            self.assertEqual(as_user.state, "approved")
            for slip in as_user.slip_ids:
                self.assertTrue(slip.line_ids.mapped("total"))
                self.assertTrue(slip.worked_days_line_ids.mapped("code"))
        # the run is not locked, so only access rules can refuse the reader
        with self.assertRaises(AccessError):
            self._runs(self.reader).browse(run.id).name = "Reader's name"
