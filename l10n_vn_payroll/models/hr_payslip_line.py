# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    l10n_vn_days = fields.Float(string="Days", digits=(16, 4))
    l10n_vn_hours = fields.Float(string="Hours", digits=(16, 4))
    l10n_vn_factor = fields.Float(string="Factor", digits=(16, 6))
    l10n_vn_unit_amount = fields.Float(string="Unit Amount", digits=(16, 4))
    l10n_vn_date_from = fields.Date(string="From")
    l10n_vn_date_to = fields.Date(string="To")
    l10n_vn_attainment = fields.Float(string="Attainment", digits=(16, 4))
    l10n_vn_period_ref = fields.Date(string="Belongs to month")
