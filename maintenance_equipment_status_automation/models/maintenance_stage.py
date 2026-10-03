# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MaintenanceStage(models.Model):
    _inherit = "maintenance.stage"

    # Configuration, not a fixed table: maintenance_equipment_status defines no
    # statuses of its own, and stages are a site's to arrange. Empty does
    # nothing.
    equipment_status_id = fields.Many2one(
        comodel_name="maintenance.equipment.status",
        string="Equipment Status",
        ondelete="set null",
        help="The status the equipment of a corrective request takes when the "
        "request reaches this stage. Empty leaves the equipment's status alone.",
    )
