# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsDefectCode(models.Model):
    _name = "qms.defect.code"
    _inherit = "qms.catalog.mixin"
    _description = "Defect Code"

    parent_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Group",
        ondelete="restrict",
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name="qms.defect.code",
        inverse_name="parent_id",
        string="Codes",
    )
