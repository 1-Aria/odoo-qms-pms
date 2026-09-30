# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .maintenance_priority_rule import CRITICALITY


class MaintenanceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    # The default for new equipment in this category. The module does not walk
    # the category tree that maintenance_equipment_category_hierarchy adds: a
    # default that changed silently when someone reparented a category would be
    # a different feature.
    criticality = fields.Selection(
        selection=CRITICALITY,
        string="Criticality",
        help="Criticality new equipment in this category starts with.",
    )
