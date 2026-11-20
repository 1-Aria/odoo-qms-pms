# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Step 4: the account mapping by code, only where empty, what is missing reported."""

from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import PayrollCase

from ..models.garment_scheme import ACCOUNT_MAPPING
from .common import prepare_chart


@tagged("post_install", "-at_install")
class TestLoadAccounts(PayrollCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the dues sub-account is left out, as on the instance today
        cls.accounts = prepare_chart(cls.env, cls.company, skip=("338811",))

    def _groups(self):
        return self.env["l10n_vn.payroll.cost.group"].search(
            [("company_id", "=", self.company.id)]
        )

    def _components(self):
        return {
            c.code: c
            for c in self.env["l10n_vn.payroll.component"].with_context(active_test=False).search(
                [("company_id", "=", self.company.id)]
            )
        }

    def test_load_accounts(self):
        result = self.company._l10n_vn_garment_load()
        self.assertEqual(
            {group.code: group.expense_account_id for group in self._groups()},
            {code: self.accounts[account] for code, _names, account in ACCOUNT_MAPPING["cost_groups"]},
        )
        components = self._components()
        for code, account in ACCOUNT_MAPPING["components"].items():
            if code == "DUES":
                self.assertFalse(components[code].l10n_vn_account_id)
            else:
                self.assertEqual(components[code].l10n_vn_account_id, self.accounts[account], code)
        company = self.company
        self.assertEqual(company.l10n_vn_payroll_journal_id.code, "PYRL")
        self.assertEqual(company.l10n_vn_payroll_payable_account_id, self.accounts["3341"])
        self.assertEqual(company.l10n_vn_payroll_bank_journal_id.code, "BNK1")
        self.assertEqual(company.l10n_vn_payroll_cash_journal_id.code, "CSH1")
        # switching posting on is the go-live act (D25)
        self.assertFalse(company.l10n_vn_payroll_post)
        self.assertEqual(result["missing"], ["account 338811 for DUES"])

    def test_load_keeps_accounts(self):
        self.company._l10n_vn_garment_load()
        components = self._components()
        direct = self._groups().filtered(lambda g: g.code == "DIRECT")
        components["PIT"].l10n_vn_account_id = self.accounts["7110"]
        direct.expense_account_id = self.accounts["6271"]
        self.company.l10n_vn_payroll_payable_account_id = self.accounts["33831"]
        result = self.company._l10n_vn_garment_load()
        self.assertEqual(result["created"], [])
        self.assertEqual(components["PIT"].l10n_vn_account_id, self.accounts["7110"])
        self.assertEqual(direct.expense_account_id, self.accounts["6271"])
        self.assertEqual(self.company.l10n_vn_payroll_payable_account_id, self.accounts["33831"])
        for label in ("cost group DIRECT", "account of component PIT",
                      "setting l10n_vn_payroll_payable_account_id"):
            self.assertIn(label, result["kept"])
