# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsObjectPart(models.Model):
    _name = "qms.object.part"
    _inherit = "qms.catalog.mixin"
    _description = "Object Part"

    parent_id = fields.Many2one(
        comodel_name="qms.object.part",
        string="Group",
        ondelete="restrict",
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name="qms.object.part",
        inverse_name="parent_id",
        string="Codes",
    )
    profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        relation="qms_profile_object_part_group_rel",
        column1="object_part_id",
        column2="profile_id",
        string="Profiles",
    )
