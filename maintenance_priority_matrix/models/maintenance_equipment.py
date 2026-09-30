# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .maintenance_priority_rule import CRITICALITY


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    criticality = fields.Selection(
        selection=CRITICALITY,
        string="Criticality",
        compute="_compute_criticality",
        store=True,
        readonly=False,
        help="How much this machine's failure costs production. Defaults from "
        "the equipment category.",
    )

    @api.depends("category_id")
    def _compute_criticality(self):
        """Take the category's criticality, when it has one.

        An editable stored compute, as qms_nonconformity uses for item severity:
        a value set by hand stands, and re-categorising a machine re-derives it,
        which is right because the machine is being reclassified. The guard
        matters: a category with no criticality assigns nothing rather than
        clearing a value someone set deliberately.
        """
        for equipment in self:
            if equipment.category_id.criticality:
                equipment.criticality = equipment.category_id.criticality
