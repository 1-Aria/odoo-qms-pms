# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from .payslip_common import PayslipCase


class RunCase(PayslipCase):
    """Runs of the October period, with one user per payroll role; holds no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.period.attendance_closed = True
        # the base fixture's employee has no summary: keep it out of the runs
        cls.contract.struct_id = False
        cls.journal = None
        if "journal_id" in cls.env["hr.payslip.run"]._fields:
            cls.journal = cls.env["account.journal"].create(
                {"name": "Test Salaries", "code": "TSAL", "type": "general",
                 "company_id": cls.company.id}
            )
        cls.officer = cls._user("test.vn_run.officer", ["payroll.group_payroll_user"])
        cls.reviewer = cls._user("test.vn_run.reviewer", ["l10n_vn_payroll.group_payroll_reviewer"])
        cls.approver = cls._user("test.vn_run.approver", ["l10n_vn_payroll.group_payroll_approver"])
        cls.officer_approver = cls._user(
            "test.vn_run.officer_approver",
            ["payroll.group_payroll_user", "l10n_vn_payroll.group_payroll_approver"],
        )
        cls.reader = cls._user("test.vn_run.reader", ["l10n_vn_payroll.group_payroll_reader"])
        cls.manager = cls._user("test.vn_run.manager", ["payroll.group_payroll_manager"])

    def setUp(self):
        super().setUp()
        self.alice, self.alice_contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        self.bao, self.bao_contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        for employee in (self.alice, self.bao):
            self._identify(employee)
            self._input(employee)

    def _runs(self, user):
        return self._as(user)["hr.payslip.run"]

    def _new_run(self, kind="regular", employees=None):
        vals = {"l10n_vn_period_id": self.period.id, "l10n_vn_kind": kind}
        if employees:
            vals["l10n_vn_employee_ids"] = [Command.set(employees.ids)]
        if self.journal:
            vals["journal_id"] = self.journal.id
        return self.env["hr.payslip.run"].browse(self._runs(self.officer).create(vals).id)

    def _calculate(self, run, user=None):
        self._runs(user or self.officer).browse(run.id).action_l10n_vn_calculate()

    def _review(self, run, user=None):
        self._runs(user or self.reviewer).browse(run.id).action_l10n_vn_review()

    def _approve(self, run, user=None):
        self._runs(user or self.approver).browse(run.id).action_l10n_vn_approve()

    def _approved_run(self, kind="regular", employees=None):
        run = self._new_run(kind, employees)
        self._calculate(run)
        self._review(run)
        self._approve(run)
        return run

    def _slip(self, run, employee):
        return run.slip_ids.filtered(lambda p: p.employee_id == employee)
