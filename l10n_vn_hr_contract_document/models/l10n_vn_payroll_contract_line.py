# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .hr_contract import UNLOCK

# fields of a line that are not terms of the contract (D30, D41)
FREE_FIELDS = {"note", "granted_by", "review_date"}
# print modes whose lines the lock and an amendment govern
GOVERNED = ("amount", "reference")


class L10nVnPayrollContractLine(models.Model):
    _inherit = "l10n_vn.payroll.contract.line"

    def _l10n_vn_refuse(self, contract, component):
        raise ValidationError(
            self.env._(
                "Contract %(contract)s is approved: its pay line %(component)s cannot change. "
                "Use an amendment.",
                contract=contract.name,
                component=component.code,
            )
        )

    def _l10n_vn_refuse_amendment(self, contract, rule):
        raise ValidationError(
            self.env._(
                "Contract %(contract)s is being amended from %(date)s: %(rule)s",
                contract=contract.name,
                date=contract.l10n_vn_amendment_date,
                rule=rule,
            )
        )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(UNLOCK):
            Contract = self.env["hr.contract"].sudo()
            Component = self.env["l10n_vn.payroll.component"].sudo()
            for vals in vals_list:
                contract = Contract.browse(vals.get("contract_id"))
                if not contract.l10n_vn_approved:
                    continue
                component = Component.browse(vals.get("component_id"))
                mode = component.l10n_vn_contract_print
                if contract.l10n_vn_amendment_id:
                    # D41: a new line starts on or after the effective date
                    date_from = fields.Date.to_date(vals.get("date_from"))
                    if mode in GOVERNED and (
                        not date_from or date_from < contract.l10n_vn_amendment_date
                    ):
                        self._l10n_vn_refuse_amendment(
                            contract, self.env._("a new pay line starts on or after that date.")
                        )
                    continue
                if mode == "amount" or (
                    mode == "reference" and component not in contract.l10n_vn_line_ids.component_id
                ):
                    self._l10n_vn_refuse(contract, component)
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(UNLOCK):
            for line in self.sudo().filtered("contract_id.l10n_vn_approved"):
                contract = line.contract_id
                mode = line.component_id.l10n_vn_contract_print
                if contract.l10n_vn_amendment_id:
                    if mode not in GOVERNED:
                        continue
                    # D41: an existing line may only be ended
                    if set(vals) - FREE_FIELDS - {"date_to"}:
                        self._l10n_vn_refuse_amendment(
                            contract, self.env._("an existing pay line can only be ended.")
                        )
                    if "date_to" in vals:
                        date_to = fields.Date.to_date(vals["date_to"])
                        earliest = contract.l10n_vn_amendment_date - datetime.timedelta(days=1)
                        if not date_to or date_to < earliest:
                            self._l10n_vn_refuse_amendment(
                                contract,
                                self.env._("a pay line ends on or after the day before it."),
                            )
                    continue
                if (mode == "amount" and set(vals) - FREE_FIELDS) or (
                    mode == "reference" and {"component_id", "contract_id"} & set(vals)
                ):
                    self._l10n_vn_refuse(contract, line.component_id)
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get(UNLOCK):
            for line in self.sudo().filtered("contract_id.l10n_vn_approved"):
                contract = line.contract_id
                mode = line.component_id.l10n_vn_contract_print
                if contract.l10n_vn_amendment_id:
                    if mode in GOVERNED:
                        self._l10n_vn_refuse_amendment(
                            contract, self.env._("pay lines are ended, not deleted.")
                        )
                    continue
                if mode == "amount":
                    self._l10n_vn_refuse(contract, line.component_id)
                if mode == "reference":
                    others = contract.l10n_vn_line_ids.filtered(
                        lambda other: other.component_id == line.component_id
                    ) - self.sudo()
                    if not others:
                        self._l10n_vn_refuse(contract, line.component_id)
        return super().unlink()
