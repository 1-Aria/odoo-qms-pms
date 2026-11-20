# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_vn_payroll_post = fields.Boolean(related="company_id.l10n_vn_payroll_post", readonly=False)
    l10n_vn_payroll_journal_id = fields.Many2one(
        related="company_id.l10n_vn_payroll_journal_id", readonly=False
    )
    l10n_vn_payroll_payable_account_id = fields.Many2one(
        related="company_id.l10n_vn_payroll_payable_account_id", readonly=False
    )
    l10n_vn_payroll_bank_journal_id = fields.Many2one(
        related="company_id.l10n_vn_payroll_bank_journal_id", readonly=False
    )
    l10n_vn_payroll_cash_journal_id = fields.Many2one(
        related="company_id.l10n_vn_payroll_cash_journal_id", readonly=False
    )
