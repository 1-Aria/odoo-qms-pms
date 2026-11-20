# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.l10n_vn_payroll_payment.tests.common import AdvanceCase

# the accounts the tests use: code -> (type, reconcile)
ACCOUNTS = {
    "3341": ("liability_payable", True),
    "33831": ("liability_payable", True),
    "33841": ("liability_payable", True),
    "33861": ("liability_payable", True),
    "338811": ("liability_payable", True),
    "33821": ("liability_payable", True),
    "33351": ("liability_current", False),
    "7110": ("income_other", False),
    "6220": ("expense_direct_cost", False),
    "6421": ("expense", False),
    "1132": ("asset_current", True),
}
COMPONENT_ACCOUNTS = {
    "EE_SI": "33831",
    "ER_PENSION": "33831",
    "ER_SICKNESS": "33831",
    "ER_ACCIDENT": "33831",
    "EE_HI": "33841",
    "ER_HI": "33841",
    "EE_UI": "33861",
    "ER_UI": "33861",
    "DUES": "338811",
    "UNION_FEE": "33821",
    "PIT": "33351",
    "DAMAGE": "7110",
}


class AccountCase(AdvanceCase):
    """Runs of October posted on the Vietnamese chart; holds no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["account.chart.template"].try_loading("vn", cls.company, install_demo=False)
        Journal = cls.env["account.journal"]
        # loading a chart in a company without accounting deletes its journals
        # (account/models/chart_template.py:205-217), the run journal RunCase made included
        cls.journal = Journal.create(
            {"name": "Test Salaries", "code": "TSAL", "type": "general",
             "company_id": cls.company.id}
        )
        cls.acc = {code: cls._account(code, *spec) for code, spec in ACCOUNTS.items()}
        cls.bank = Journal.search(
            [("company_id", "=", cls.company.id), ("type", "=", "bank")], limit=1
        )
        cls.cash = Journal.search(
            [("company_id", "=", cls.company.id), ("type", "=", "cash")], limit=1
        )
        (cls.bank | cls.cash).outbound_payment_method_line_ids.write(
            {"payment_account_id": cls.acc["1132"].id}
        )
        cls.company.write(
            {
                "l10n_vn_payroll_post": True,
                "l10n_vn_payroll_journal_id": cls.journal.id,
                "l10n_vn_payroll_payable_account_id": cls.acc["3341"].id,
                "l10n_vn_payroll_bank_journal_id": cls.bank.id,
                "l10n_vn_payroll_cash_journal_id": cls.cash.id,
            }
        )
        Group = cls.env["l10n_vn.payroll.cost.group"]
        cls.direct = Group.create(
            {"code": "DIRECT", "name": "Direct labour", "company_id": cls.company.id,
             "expense_account_id": cls.acc["6220"].id}
        )
        cls.admin_group = Group.create(
            {"code": "ADMIN", "name": "Administration", "company_id": cls.company.id,
             "expense_account_id": cls.acc["6421"].id}
        )
        Department = cls.env["hr.department"]
        cls.production = Department.create(
            {"name": "Test Production", "company_id": cls.company.id,
             "l10n_vn_cost_group_id": cls.direct.id}
        )
        cls.sewing = Department.create(
            {"name": "Test Sewing", "company_id": cls.company.id, "parent_id": cls.production.id}
        )
        cls.administration = Department.create(
            {"name": "Test Administration", "company_id": cls.company.id,
             "l10n_vn_cost_group_id": cls.admin_group.id}
        )
        for code, account in COMPONENT_ACCOUNTS.items():
            cls.engine[code].l10n_vn_account_id = cls.acc[account]

    @classmethod
    def _account(cls, code, account_type, reconcile=False):
        """The company's account with this code, created when the chart has none."""
        Account = cls.env["account.account"].with_company(cls.company)
        account = Account.search(
            [*Account._check_company_domain(cls.company), ("code", "=", code)], limit=1
        )
        if not account:
            account = Account.create(
                {
                    "code": code,
                    "name": f"Test {code}",
                    "account_type": account_type,
                    "reconcile": reconcile,
                    "company_ids": [Command.link(cls.company.id)],
                }
            )
        elif reconcile and not account.reconcile:
            account.reconcile = True
        return account

    def setUp(self):
        super().setUp()
        self.alice_contract.department_id = self.sewing
        self.bao_contract.department_id = self.administration

    # ------------------------------------------------------------------ helpers
    def _approved_run_noted(self):
        """Calculated, warnings noted, reviewed and approved."""
        run = self._new_run()
        self._calculate(run)
        run.l10n_vn_check_result_ids.filtered(
            lambda r: r.level == "warning" and not r.note
        ).write({"note": "Seen"})
        self._review(run)
        self._approve(run)
        return run

    def _lines(self, move, code, partner=None):
        lines = move.line_ids.filtered(lambda l: l.account_id == self.acc[code])
        if partner is not None:
            lines = lines.filtered(lambda l: l.partner_id == partner)
        return lines

    def _residual(self, employee):
        """The sum of the employee's open 3341 residuals: negative is owed to them."""
        lines = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.acc["3341"].id),
                ("partner_id", "=", employee.work_contact_id.id),
                ("parent_state", "=", "posted"),
            ]
        )
        return sum(lines.mapped("amount_residual"))

    def _component_total(self, payslip, code):
        component = self.engine[code]
        return sum(
            payslip.line_ids.filtered(lambda l: l.l10n_vn_component_id == component).mapped("total")
        )
