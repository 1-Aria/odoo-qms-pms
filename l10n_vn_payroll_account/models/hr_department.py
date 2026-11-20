# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = "hr.department"

    l10n_vn_cost_group_id = fields.Many2one(
        "l10n_vn.payroll.cost.group", string="Payroll Cost Group", check_company=True
    )

    def _l10n_vn_cost_group(self):
        """Its cost group, else the nearest parent's (D4)."""
        self.ensure_one()
        department = self.sudo()
        while department:
            if department.l10n_vn_cost_group_id:
                return department.l10n_vn_cost_group_id
            department = department.parent_id
        return self.env["l10n_vn.payroll.cost.group"]
