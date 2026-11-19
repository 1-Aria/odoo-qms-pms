# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nVnPayrollAdvancePay(models.TransientModel):
    _name = "l10n_vn.payroll.advance.pay"
    _description = "Mark Salary Advances as Paid"

    advance_ids = fields.Many2many(
        "l10n_vn.payroll.advance", "l10n_vn_advance_pay_rel", required=True
    )
    paid_date = fields.Date(
        string="Payment Date", required=True, default=fields.Date.context_today
    )
    currency_id = fields.Many2one("res.currency", compute="_compute_totals")
    advance_count = fields.Integer(string="Advances", compute="_compute_totals")
    amount_total = fields.Monetary(string="Total", compute="_compute_totals")

    @api.depends("advance_ids")
    def _compute_totals(self):
        for wizard in self:
            wizard.currency_id = wizard.advance_ids[:1].currency_id
            wizard.advance_count = len(wizard.advance_ids)
            wizard.amount_total = sum(wizard.advance_ids.mapped("amount"))

    def action_confirm(self):
        self.ensure_one()
        self.advance_ids._l10n_vn_mark_paid(self.paid_date)
        return {"type": "ir.actions.act_window_close"}
