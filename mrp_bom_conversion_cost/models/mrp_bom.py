# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    conversion_minutes = fields.Float(
        string="Conversion Minutes",
        digits=(16, 4),
        default=0.0,
        tracking=True,
        help="Standard minutes of conversion work per unit of the product, in "
        "the product's unit of measure (for a garment, its SAM). "
        "Manufacturing orders are valued at these minutes × the conversion "
        "cost rate in force on the day they are done.",
    )

    _sql_constraints = [
        (
            "conversion_minutes_not_negative",
            "CHECK (conversion_minutes >= 0)",
            "Conversion minutes cannot be negative.",
        ),
    ]
