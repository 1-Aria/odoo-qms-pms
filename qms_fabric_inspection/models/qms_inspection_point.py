# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsInspectionPoint(models.Model):
    _name = "qms.inspection.point"
    _description = "Point Entry"
    _order = "roll_id, position, id"

    roll_id = fields.Many2one(
        comodel_name="qms.inspection.roll",
        required=True,
        ondelete="cascade",
        index=True,
    )
    # Counted from 1 and required: an Integer left empty reads 0, so with
    # metre 0 allowed every unpositioned entry would be capped together. A
    # CHECK lets NULL through; NOT NULL is what refuses a missing position.
    position = fields.Integer(
        string="Position (m)",
        required=True,
        help="The metre of the roll the defect lies in, 1 for the first metre, "
        "as read on the inspection machine.",
    )
    defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect",
        required=True,
        ondelete="restrict",
    )
    # Judged by the inspector, not computed: the classes are guidance.
    points = fields.Integer(
        required=True,
        help="1 to 4, by the defect's size under the 4-point system: up to "
        "7.5 cm 1, to 15 cm 2, to 23 cm 3, longer 4; a hole up to 2.5 cm 2, "
        "larger 4.",
    )

    _sql_constraints = [
        (
            "points_range",
            "CHECK (points >= 1 AND points <= 4)",
            "Points must be between 1 and 4.",
        ),
        (
            "position_positive",
            "CHECK (position >= 1)",
            "A position must be 1 or more: the metre the defect lies in.",
        ),
    ]
