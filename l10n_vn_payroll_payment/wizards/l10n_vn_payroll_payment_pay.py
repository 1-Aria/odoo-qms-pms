# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..models.l10n_vn_payroll_payment import METHODS


class L10nVnPayrollPaymentPay(models.TransientModel):
    _name = "l10n_vn.payroll.payment.pay"
    _description = "Mark Payroll Payments as Paid"

    payment_id = fields.Many2one("l10n_vn.payroll.payment", required=True)
    method = fields.Selection(METHODS, required=True)
    line_ids = fields.Many2many(
        "l10n_vn.payroll.payment.line",
        "l10n_vn_payment_pay_line_rel",
        required=True,
        domain="[('payment_id', '=', payment_id), ('method', '=', method), ('state', '=', 'to_pay')]",
    )
    paid_date = fields.Date(
        string="Payment Date", required=True, default=fields.Date.context_today
    )
    currency_id = fields.Many2one(related="payment_id.currency_id")
    amount_total = fields.Monetary(string="Total", compute="_compute_amount_total")

    @api.depends("line_ids")
    def _compute_amount_total(self):
        for wizard in self:
            wizard.amount_total = sum(wizard.line_ids.mapped("amount"))

    def action_confirm(self):
        self.ensure_one()
        self.line_ids._l10n_vn_mark_paid(self.paid_date)
        return {"type": "ir.actions.act_window_close"}
