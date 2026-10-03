# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MaintenancePlan(models.Model):
    _inherit = "maintenance.plan"

    action_template_ids = fields.Many2many(
        comodel_name="mgmtsystem.action.template",
        string="Action Templates",
        help="One action per template is created on every request this plan "
        "generates. A template without a response type is skipped.",
    )
