# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .hr_payslip_run import LOCKED_STATES
from .l10n_vn_payroll_component import LINE_SOURCES

FROZEN = {"component_id", "amount", "scale_key", "in_cell", "contract_id", "date_from"}

FAR_FUTURE = datetime.date.max


class L10nVnPayrollContractLine(models.Model):
    _name = "l10n_vn.payroll.contract.line"
    _description = "Contract Pay Line"
    _order = "contract_id, date_from, component_id"
    _check_company_auto = True

    contract_id = fields.Many2one(
        "hr.contract", required=True, ondelete="cascade", index=True
    )
    employee_id = fields.Many2one(related="contract_id.employee_id", store=True)
    company_id = fields.Many2one(related="contract_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    component_id = fields.Many2one(
        "l10n_vn.payroll.component",
        required=True,
        ondelete="restrict",
        domain=[("amount_source", "in", list(LINE_SOURCES))],
        check_company=True,
    )
    amount_source = fields.Selection(related="component_id.amount_source")
    amount = fields.Monetary()
    scale_key = fields.Char()
    in_cell = fields.Boolean(string="Part of the scale cell")
    date_from = fields.Date(required=True, default=lambda self: self._default_date_from())
    date_to = fields.Date()
    granted_by = fields.Many2one("res.users")
    review_date = fields.Date()
    note = fields.Char()

    def _default_date_from(self):
        contract_id = self.env.context.get("default_contract_id")
        if contract_id:
            contract = self.env["hr.contract"].browse(contract_id)
            if contract.exists() and contract.date_start:
                return contract.date_start
        return fields.Date.context_today(self)

    @api.constrains("contract_id", "component_id", "date_from", "date_to", "amount", "scale_key")
    def _check_line(self):
        _ = self.env._
        for line in self:
            contract = line.contract_id
            name = line.component_id.code
            if line.date_from < contract.date_start:
                raise ValidationError(
                    _("Pay line %(name)s starts before its contract.", name=name)
                )
            if line.date_to and line.date_to < line.date_from:
                raise ValidationError(
                    _("Pay line %(name)s ends before it starts.", name=name)
                )
            if contract.date_end and (
                line.date_from > contract.date_end
                or (line.date_to and line.date_to > contract.date_end)
            ):
                raise ValidationError(
                    _("Pay line %(name)s runs past the end of its contract.", name=name)
                )
            source = line.component_id.amount_source
            if source not in LINE_SOURCES:
                raise ValidationError(
                    _("Component %(name)s does not sit on pay lines.", name=name)
                )
            if source == "line" and not line.amount:
                raise ValidationError(_("Pay line %(name)s needs an amount.", name=name))
            if source in ("scale", "scale_remainder"):
                if not line.scale_key and not line.amount:
                    raise ValidationError(
                        _("Pay line %(name)s needs a scale key or an amount.", name=name)
                    )
                scale = line.component_id.scale_id
                if line.scale_key and not scale._has_key(line.scale_key):
                    raise ValidationError(
                        _(
                            "Scale %(scale)s has no cell %(key)s.",
                            scale=scale.code,
                            key=line.scale_key,
                        )
                    )
            others = self.sudo().search(
                [("contract_id", "=", contract.id), ("id", "!=", line.id)]
            )
            same = others.filtered(lambda o: o.component_id == line.component_id)
            if any(line._overlaps(other) for other in same):
                raise ValidationError(
                    _(
                        "Two pay lines of %(name)s overlap on one contract; "
                        "end the first the day before the next starts.",
                        name=name,
                    )
                )
            if source == "scale_remainder":
                remainders = others.filtered(
                    lambda o: o.component_id.amount_source == "scale_remainder"
                    and o.component_id.scale_id == line.component_id.scale_id
                )
                if any(line._overlaps(other) for other in remainders):
                    raise ValidationError(
                        _(
                            "Two remainder lines of scale %(scale)s overlap on one contract.",
                            scale=line.component_id.scale_id.code,
                        )
                    )

    def _overlaps(self, other):
        self.ensure_one()
        return self.date_from <= (other.date_to or FAR_FUTURE) and other.date_from <= (
            self.date_to or FAR_FUTURE
        )

    def _l10n_vn_in_force(self, date):
        return self.filtered(
            lambda line: line.date_from <= date and (not line.date_to or line.date_to >= date)
        )

    def _l10n_vn_amount_on(self, date):
        self.ensure_one()
        component = self.component_id
        source = component.amount_source
        if source == "line":
            return self.amount
        if source == "parameter":
            return self.env["base.time.parameter"]._strict_get(
                component.amount_parameter, date, company=self.company_id
            )
        cell = self.amount or component.scale_id._cell_amount(self.scale_key, date)
        if source == "scale":
            return cell
        if source == "scale_remainder":
            parts = self.contract_id.l10n_vn_line_ids._l10n_vn_in_force(date).filtered(
                lambda line: line.in_cell
                and line != self
                and line.component_id.amount_source != "scale_remainder"
            )
            return cell - sum(part._l10n_vn_amount_on(date) for part in parts)
        raise ValidationError(
            self.env._("Component %(name)s does not sit on pay lines.", name=component.code)
        )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.contract_id._l10n_vn_sync_wage()
        return lines

    # ------------------------------------------------------------------ after approval (D77)
    def _l10n_vn_used_until(self):
        """{line id: the last day of the latest locked payslip that used it}"""
        used = {}
        if not self.ids:
            return used
        payslips = self.env["hr.payslip"].sudo().search(
            [
                ("employee_id", "in", self.sudo().contract_id.employee_id.ids),
                ("payslip_run_id.l10n_vn_period_id", "!=", False),
                ("payslip_run_id.state", "in", LOCKED_STATES),
            ]
        )
        for payslip in payslips:
            ids = {p["id"] for p in (payslip.l10n_vn_context or {}).get("pay_lines", [])}
            for line_id in ids & set(self.ids):
                used[line_id] = max(used.get(line_id, payslip.date_to), payslip.date_to)
        return used

    def _l10n_vn_refuse(self):
        raise UserError(
            self.env._(
                "This pay line was used by an approved payslip: end it and add a new line "
                "instead."
            )
        )

    def write(self, vals):
        if not self.env.su:
            used = self._l10n_vn_used_until()
            if used:
                if FROZEN.intersection(vals):
                    self._l10n_vn_refuse()
                new_end = fields.Date.to_date(vals.get("date_to")) if "date_to" in vals else None
                if new_end and any(new_end < until for until in used.values()):
                    raise UserError(
                        self.env._(
                            "This pay line was used by an approved payslip until %(date)s; it "
                            "cannot end before.",
                            date=max(used.values()),
                        )
                    )
        contracts = self.contract_id
        result = super().write(vals)
        (contracts | self.contract_id)._l10n_vn_sync_wage()
        return result

    def unlink(self):
        if not self.env.su and self._l10n_vn_used_until():
            self._l10n_vn_refuse()
        contracts = self.contract_id
        result = super().unlink()
        contracts.exists()._l10n_vn_sync_wage()
        return result
