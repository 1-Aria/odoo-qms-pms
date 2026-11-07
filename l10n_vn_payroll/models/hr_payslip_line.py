# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    @api.model_create_multi
    def create(self, vals_list):
        self.env["hr.payslip"].browse(
            [v["slip_id"] for v in vals_list if v.get("slip_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.slip_id._l10n_vn_raise_if_locked()
        return super().write(vals)

    def unlink(self):
        self.slip_id._l10n_vn_raise_if_locked()
        return super().unlink()


class HrPayslipWorkedDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    @api.model_create_multi
    def create(self, vals_list):
        self.env["hr.payslip"].browse(
            [v["payslip_id"] for v in vals_list if v.get("payslip_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.payslip_id._l10n_vn_raise_if_locked()
        return super().write(vals)

    def unlink(self):
        self.payslip_id._l10n_vn_raise_if_locked()
        return super().unlink()


class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    @api.model_create_multi
    def create(self, vals_list):
        self.env["hr.payslip"].browse(
            [v["payslip_id"] for v in vals_list if v.get("payslip_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.payslip_id._l10n_vn_raise_if_locked()
        return super().write(vals)

    def unlink(self):
        self.payslip_id._l10n_vn_raise_if_locked()
        return super().unlink()

