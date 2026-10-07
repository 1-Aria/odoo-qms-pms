# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsInspectionPoint(models.Model):
    _inherit = "qms.inspection.point"

    # Dimensions for grouping the fabric defect Pareto, not stored: each ends
    # on a stored field through Many2one hops (odoo/models.py:2932-2954).
    qms_partner_id = fields.Many2one(
        string="Partner",
        related="roll_id.inspection_id.picking_id.partner_id",
        help="The receipt's supplier.",
    )
    qms_product_id = fields.Many2one(
        string="Fabric",
        related="roll_id.inspection_id.product_id",
    )
    qms_inspection_date = fields.Datetime(
        string="Inspection Date",
        related="roll_id.inspection_id.date",
    )
    qms_dye_lot = fields.Char(
        string="Dye Lot",
        related="roll_id.dye_lot",
    )
