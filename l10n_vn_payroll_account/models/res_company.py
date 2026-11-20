# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # off: payroll and payments work without posting (D11, FR-77)
    l10n_vn_payroll_post = fields.Boolean(string="Post Payroll in Accounting")
    l10n_vn_payroll_journal_id = fields.Many2one(
        "account.journal", string="Payroll Journal", domain="[('type', '=', 'general')]"
    )
    l10n_vn_payroll_payable_account_id = fields.Many2one(
        "account.account", string="Payroll Payable Account"
    )
    l10n_vn_payroll_bank_journal_id = fields.Many2one(
        "account.journal", string="Payroll Bank Journal", domain="[('type', '=', 'bank')]"
    )
    l10n_vn_payroll_cash_journal_id = fields.Many2one(
        "account.journal", string="Payroll Cash Journal", domain="[('type', '=', 'cash')]"
    )
