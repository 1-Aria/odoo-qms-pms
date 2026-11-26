# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError

GROUP_LABELS = {
    "work": "work",
    "salary": "salary",
    "bonus": "bonus and welfare",
    "insurance": "insurance",
    "training": "training",
    "individual": "individual terms",
}


class L10nVnContractAnnexBatchWizard(models.TransientModel):
    """Annexes for the contracts whose printed terms change on a date (D48)."""

    _name = "l10n_vn.contract.annex.batch.wizard"
    _description = "Annexes for a Date"

    date = fields.Date(required=True)
    reason = fields.Char(required=True, default="Điều chỉnh tiền lương")
    contract_ids = fields.Many2many("hr.contract", string="Contracts")
    line_ids = fields.One2many(
        "l10n_vn.contract.annex.batch.line", "wizard_id", string="Contracts with Changes"
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "hr.contract" and "contract_ids" in fields_list:
            values["contract_ids"] = [Command.set(self.env.context.get("active_ids") or [])]
        return values

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_find_changes(self):
        self.ensure_one()
        self.env["hr.contract"]._l10n_vn_check_manager()
        lines = []
        for contract in self.contract_ids.sudo():
            kind = contract._l10n_vn_document_kind_value()
            if not kind or not contract.l10n_vn_approved or contract.l10n_vn_amendment_id:
                continue
            # only contracts in force on the date can take an annex from it (D54)
            if contract.date_start > self.date or (
                contract.date_end and contract.date_end < self.date
            ):
                continue
            current = (contract.l10n_vn_version_id.terms or {}).get("render") or {}
            changes = contract._l10n_vn_changes(
                current, contract._l10n_vn_document_terms(self.date), kind
            )
            if changes:
                groups = ", ".join(GROUP_LABELS[change["group"]] for change in changes)
                lines.append(Command.create({"contract_id": contract.id, "groups": groups}))
        if not lines:
            raise UserError(
                self.env._(
                    "No approved contract's printed terms change on %(date)s.", date=self.date
                )
            )
        self.line_ids = [Command.clear()] + lines
        return self._reopen()

    def action_confirm(self):
        self.ensure_one()
        Contract = self.env["hr.contract"]
        Contract._l10n_vn_check_manager()
        if not self.line_ids:
            raise UserError(self.env._("Find the contracts with changes first."))
        failures = []
        for line in self.line_ids:
            try:
                with self.env.cr.savepoint():
                    line.contract_id._l10n_vn_amend(self.date, self.reason)
                    line.contract_id._l10n_vn_approve_amendment_one()
            except (UserError, ValidationError) as error:
                failures.append(f"{line.contract_id.name}: {error.args[0]}")
        params = {"next": {"type": "ir.actions.act_window_close"}}
        if failures:
            params.update(
                type="warning",
                sticky=True,
                title=self.env._(
                    "%(failed)s of %(count)s annexes not made",
                    failed=len(failures),
                    count=len(self.line_ids),
                ),
                message="\n\n".join(failures),
            )
        else:
            params.update(
                type="success",
                message=self.env._("%(count)s annexes approved.", count=len(self.line_ids)),
            )
        return {"type": "ir.actions.client", "tag": "display_notification", "params": params}


class L10nVnContractAnnexBatchLine(models.TransientModel):
    _name = "l10n_vn.contract.annex.batch.line"
    _description = "Annexes for a Date: Contract"

    wizard_id = fields.Many2one(
        "l10n_vn.contract.annex.batch.wizard", required=True, ondelete="cascade"
    )
    contract_id = fields.Many2one("hr.contract", required=True, ondelete="cascade")
    groups = fields.Char(string="Changes")
