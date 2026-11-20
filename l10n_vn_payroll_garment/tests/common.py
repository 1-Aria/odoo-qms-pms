# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from ..models.garment_scheme import ENGINE_CODES

# the chart accounts the account mapping looks for (step 4): code -> (type, reconcile)
MAPPED_ACCOUNTS = {
    "6220": ("expense_direct_cost", False),
    "6271": ("expense_direct_cost", False),
    "6411": ("expense", False),
    "6421": ("expense", False),
    "33831": ("liability_payable", True),
    "33841": ("liability_payable", True),
    "33861": ("liability_payable", True),
    "33821": ("liability_payable", True),
    "338811": ("liability_payable", True),
    "33351": ("liability_current", False),
    "7110": ("income_other", False),
    "3341": ("liability_payable", True),
}


def prepare_chart(env, company, skip=()):
    """Loads the Vietnamese chart in the company, then the accounts and journals the mapping
    looks for. Returns {code: account}.

    Loading a chart deletes the company's journals and accounts, so this runs first.
    """
    env["account.chart.template"].try_loading("vn", company, install_demo=False)
    Account = env["account.account"].with_company(company)
    accounts = {}
    for code, (account_type, reconcile) in MAPPED_ACCOUNTS.items():
        if code in skip:
            continue
        account = Account.search(
            [*Account._check_company_domain(company), ("code", "=", code)], limit=1
        )
        if not account:
            account = Account.create(
                {
                    "code": code,
                    "name": f"Test {code}",
                    "account_type": account_type,
                    "reconcile": reconcile,
                    "company_ids": [Command.link(company.id)],
                }
            )
        elif reconcile and not account.reconcile:
            account.reconcile = True
        accounts[code] = account
    Journal = env["account.journal"]
    Journal.create(
        {"name": "Test Payroll", "code": "PYRL", "type": "general", "company_id": company.id}
    )
    for code, kind in (("BNK1", "bank"), ("CSH1", "cash")):
        journal = Journal.search([("company_id", "=", company.id), ("type", "=", kind)], limit=1)
        if journal.code != code:
            journal.code = code
    return accounts


class GarmentMixin:
    """The loaded garment configuration for a PayslipCase; holds no test methods."""

    @classmethod
    def _l10n_vn_configure(cls):
        cls.company._l10n_vn_garment_load()
        components = (
            cls.env["l10n_vn.payroll.component"]
            .with_context(active_test=False)
            .search([("company_id", "=", cls.company.id)])
        )
        cls.components = {component.code: component for component in components}
        for attribute, code in (
            ("base", "BASE"),
            ("prod", "PROD"),
            ("perf", "PERF"),
            ("eff", "EFF"),
            ("one", "ONE"),
            ("ot_wd", "OT_WD"),
            ("ot_rd", "OT_RD"),
            ("ot_hol", "OT_HOL"),
            ("gross", "GROSS"),
        ):
            setattr(cls, attribute, cls.components[code])
        cls.engine = {code: cls.components[code] for code in ENGINE_CODES - {"GROSS"}}
        cls.structure = cls.env["hr.payroll.structure"].search(
            [("code", "=", "VN_GARMENT"), ("company_id", "=", cls.company.id)]
        )

    @staticmethod
    def _code(code):
        return code

    # BASE comes from the scale BASE by group (step 6): workers carry the key WORKER, staff
    # their amount until their grade's key exists
    def _worker(self, level, **values):
        return self._hire(
            lines=[(self.base, {"in_cell": True, "scale_key": "WORKER"}),
                   (self.prod, {"scale_key": level})],
            **values,
        )

    def _staff(self, perf_values, **values):
        return self._hire(
            lines=[(self.base, {"in_cell": True, "amount": 3700000}), (self.perf, perf_values)],
            **values,
        )
