# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # A Float, not a Monetary: a Monetary rounds to the currency, and VND
    # rounds to whole units, which would cut a rate such as 1,494.25.
    conversion_cost_rate = fields.Float(
        string="Conversion Cost per Minute",
        digits="Product Price",
        default=0.0,
        help="Cost of one standard minute of conversion work (labour and "
        "overhead), in the company's currency. Copied into new manufacturing "
        "orders as their BoM's minutes × this rate.",
    )

    _sql_constraints = [
        (
            "conversion_cost_rate_not_negative",
            "CHECK (conversion_cost_rate >= 0)",
            "The conversion cost per minute cannot be negative.",
        ),
    ]
