# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_FROM, OCT_TO
from .run_common import RunCase

SEP_FROM, SEP_TO = D(2026, 9, 1), D(2026, 9, 30)


@tagged("post_install", "-at_install")
class TestStatement(RunCase):
    def _statement(self, kind, date_from=OCT_FROM, date_to=OCT_TO):
        statement = self._as(self.officer)["l10n_vn.payroll.statement"].create(
            {"kind": kind, "date_from": date_from, "date_to": date_to, "company_id": self.company.id}
        )
        statement.action_generate()
        return self.env["l10n_vn.payroll.statement"].browse(statement.id)

    def _row(self, statement, employee):
        return statement.line_ids.filtered(lambda l: l.employee_id == employee)

    def _period_run(self, period):
        vals = {"l10n_vn_period_id": period.id}
        if self.journal:
            vals["journal_id"] = self.journal.id
        run = self.env["hr.payslip.run"].browse(self._runs(self.officer).create(vals).id)
        self._calculate(run)
        self._review(run)
        self._approve(run)
        return run

    def _september(self, employees):
        period = self.env["l10n_vn.payroll.period"].create(
            {"date_from": SEP_FROM, "company_id": self.company.id}
        )
        for employee in employees:
            self.env["l10n_vn.payroll.input"].create(
                {"period_id": period.id, "employee_id": employee.id, "figures_locked": True,
                 "scheduled_days": 26, "month_scheduled_days": 26, "paid_days": 26,
                 "days_worked": 26}
            )
        period.attendance_closed = True
        return self._period_run(period)

    def test_si_monthly(self):
        self._approved_run()
        line = self._row(self._statement("si_monthly"), self.alice)
        self.assertEqual(len(line), 1)
        self.assertEqual(
            (line.si_base, line.ee_si, line.er_pension, line.union_fee),
            (4500000, 360000, 630000, 90000),
        )
        self.assertEqual(line.personal_id, self.alice.l10n_vn_personal_id)

    def test_only_approved(self):
        run = self._new_run()
        self._calculate(run)
        self.assertFalse(self._statement("si_monthly").line_ids)

    def test_si_changes(self):
        self._september(self.alice | self.bao)
        old_line = self.alice_contract.l10n_vn_line_ids
        old_line.date_to = SEP_TO
        self._line(self.sal, contract=self.alice_contract, amount=5000000, date_from=OCT_FROM)
        self.bao_contract.write({"date_end": SEP_TO, "state": "close"})
        newcomer, _contract = self._hire(date_start=OCT_FROM, lines=[(self.sal, {"amount": 4500000})])
        self._identify(newcomer)
        self._input(newcomer)
        self._approved_run()
        statement = self._statement("si_changes")
        changes = {l.employee_id: (l.change_type, l.change_date) for l in statement.line_ids}
        self.assertEqual(changes[self.alice][0], "base")
        self.assertEqual(changes[self.bao], ("leave", SEP_TO))
        self.assertEqual(changes[newcomer], ("join", OCT_FROM))

    def test_pit_period(self):
        run = self._approved_run()
        context = self._slip(run, self.alice).l10n_vn_context
        line = self._row(self._statement("pit_period"), self.alice)
        self.assertEqual(line.income, context["gross"])
        self.assertEqual(line.income_exempt, context["pit"]["exempt"])
        self.assertEqual(line.insurance, context["employee_insurance"])
        self.assertEqual(line.taxable, max(context["pit"]["taxable"], 0))
        self.assertEqual(line.pit, context["pit"]["pit"])
        self.assertEqual(line.pit_method, "progressive")

    def test_pit_annual_with_opening(self):
        self.env["l10n_vn.payroll.opening"].create(
            {"company_id": self.company.id, "employee_id": self.alice.id, "year": 2026,
             "months": 9, "income": 40000000, "pit": 100000}
        )
        run = self._approved_run()
        context = self._slip(run, self.alice).l10n_vn_context
        line = self._row(self._statement("pit_annual", D(2026, 1, 1), D(2026, 12, 31)), self.alice)
        self.assertEqual(line.months, 10)
        self.assertEqual(line.income, 40000000 + context["gross"])
        self.assertEqual(line.pit, 100000 + context["pit"]["pit"])

    def test_ot_schedule(self):
        worker, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        self._identify(worker)
        self._input(worker, ot_hours_json={"WD": 10})
        run = self._approved_run()
        slip = self._slip(run, worker)
        line = self._row(self._statement("ot_schedule"), worker)
        self.assertEqual(line.ot_wd_hours, 10)
        self.assertEqual(line.ot_pay, sum(self._totals(slip, "OT_WD")))
        self.assertEqual(line.ot_exempt, slip.l10n_vn_context["pit"]["ot_exempt"])

    def test_union(self):
        self.alice.l10n_vn_union_member = True
        run = self._approved_run()
        slip = self._slip(run, self.alice)
        line = self._row(self._statement("union"), self.alice)
        self.assertEqual(line.dues, -self._totals(slip, "DUES")[0])
        self.assertEqual(line.union_fee, self._totals(slip, "UNION_FEE")[0])

    def test_regenerate_and_done(self):
        self._approved_run()
        statement = self._statement("si_monthly")
        count = len(statement.line_ids)
        statement.action_generate()
        self.assertEqual(len(statement.line_ids), count)
        as_officer = self._as(self.officer)["l10n_vn.payroll.statement"].browse(statement.id)
        as_officer.action_done()
        with self.assertRaises(UserError):
            as_officer.line_ids[:1].note = "Changed"
        with self.assertRaises(UserError):
            as_officer.unlink()
        self._as(self.manager)["l10n_vn.payroll.statement"].browse(statement.id).action_draft()
        as_officer.line_ids[:1].note = "Changed"
        self.assertEqual(statement.line_ids[:1].note, "Changed")

    def test_opening_feeds_ot_ytd(self):
        november = self.env["l10n_vn.payroll.period"].create(
            {"date_from": D(2026, 11, 1), "company_id": self.company.id}
        )
        self.env["l10n_vn.payroll.opening"].create(
            {"company_id": self.company.id, "employee_id": self.alice.id, "year": 2026,
             "ot_hours": 120}
        )
        inp = self.env["l10n_vn.payroll.input"].create(
            {"period_id": november.id, "employee_id": self.alice.id}
        )
        inp._l10n_vn_build()
        self.assertEqual(inp.ot_hours_ytd, 120)

    def test_access(self):
        self._approved_run()
        statement = self._statement("si_monthly")
        as_reader = self._as(self.reader)["l10n_vn.payroll.statement"].browse(statement.id)
        self.assertTrue(as_reader.line_ids.mapped("ee_si"))
        with self.assertRaises(AccessError):
            self._as(self.reader)["l10n_vn.payroll.statement"].create(
                {"kind": "union", "date_from": OCT_FROM, "date_to": OCT_TO,
                 "company_id": self.company.id, "line_ids": [Command.clear()]}
            )
