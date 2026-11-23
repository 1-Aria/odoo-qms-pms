# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import AccessError, UserError

from .hr_contract import ANNEX_TITLES, FORM_NAMES


class L10nVnContractVersion(models.Model):
    """An approved state of a contract: version 0 is the contract, later ones annexes (D20)."""

    _name = "l10n_vn.contract.version"
    _description = "Contract Version"
    _order = "contract_id, sequence"
    _rec_name = "number"

    contract_id = fields.Many2one("hr.contract", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="contract_id.company_id", store=True)
    employee_id = fields.Many2one(related="contract_id.employee_id", store=True)
    sequence = fields.Integer(default=0)
    kind = fields.Selection(
        [("contract", "Contract"), ("annex", "Annex")], required=True, default="contract"
    )
    number = fields.Char()
    effective_date = fields.Date(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("cancelled", "Cancelled")],
        required=True,
        default="draft",
    )
    reason = fields.Char()
    terms = fields.Json()
    approved_by = fields.Many2one("res.users")
    approved_at = fields.Datetime()

    _sql_constraints = [
        (
            "contract_sequence_unique",
            "unique(contract_id, sequence)",
            "A contract has one version per sequence.",
        ),
    ]

    def _l10n_vn_annex_values(self):
        """What an annex prints (D46): the contract's parties, this version's terms."""
        if not self.env.su and not self.env.user.has_group("payroll.group_payroll_user"):
            raise AccessError(
                self.env._("Only payroll users print contract documents, which show pay.")
            )
        self.ensure_one()
        version = self.sudo()
        if version.kind != "annex" or version.state != "approved":
            raise UserError(self.env._("Only an approved annex prints."))
        contract = version.contract_id.sudo()
        values = contract._l10n_vn_document_values(terms=version.terms["render"])
        doc = self.env["l10n_vn.contract.document"]
        kind = values["kind"]
        return dict(
            values,
            # the header prints the annex's own title and number (D46)
            title=ANNEX_TITLES[kind],
            number=version.number or "",
            annex_title=ANNEX_TITLES[kind],
            form_name=FORM_NAMES[kind],
            annex_number=version.number or "",
            contract_number=contract._l10n_vn_version_zero().number or "",
            contract_sign_date=doc._date(contract.l10n_vn_sign_date),
            effective_date=doc._date(version.effective_date),
            changes=version.terms.get("changes") or [],
            draft=False,
        )

    def action_l10n_vn_print(self):
        for version in self:
            if version.kind != "annex" or version.state != "approved":
                raise UserError(self.env._("Only an approved annex prints."))
        return self.env.ref(
            "l10n_vn_hr_contract_document.action_report_contract_annex"
        ).report_action(self, config=False)
