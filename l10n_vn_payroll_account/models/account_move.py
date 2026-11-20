# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_vn_payroll_run_id = fields.Many2one(
        "hr.payslip.run", string="Payroll Run", readonly=True, index="btree_not_null", copy=False
    )
    l10n_vn_payroll_payment_id = fields.Many2one(
        "l10n_vn.payroll.payment",
        string="Payroll Payment List",
        readonly=True,
        index="btree_not_null",
        copy=False,
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _l10n_vn_payroll_reconcile(self, company, partners):
        """Reconciles each employee's open 3341 lines on payroll entries together (D7)."""
        account = company.l10n_vn_payroll_payable_account_id
        if not account or not partners:
            return
        lines = self.sudo().search(
            [
                ("company_id", "=", company.id),
                ("account_id", "=", account.id),
                ("partner_id", "in", partners.ids),
                ("reconciled", "=", False),
                ("parent_state", "=", "posted"),
                "|",
                ("move_id.l10n_vn_payroll_run_id", "!=", False),
                ("move_id.l10n_vn_payroll_payment_id", "!=", False),
            ]
        )
        for partner in partners:
            mine = lines.filtered(lambda line: line.partner_id == partner)
            if mine.filtered(lambda l: l.balance > 0) and mine.filtered(lambda l: l.balance < 0):
                mine.reconcile()
