# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QmsInspectionRoll(models.Model):
    _inherit = "qms.inspection.roll"

    # Roll acceptance, the 100/0 pattern of qms_defect_free. An unscored roll
    # passes its points and carries 100; Roll Analysis's domain keeps scored
    # rolls only, so it never reaches the average.
    qms_accepted = fields.Float(
        string="Accepted (%)",
        compute="_compute_qms_accepted",
        store=True,
        aggregator="avg",
        help="100 when the roll passes its points, 0 otherwise; averaged over "
        "scored rolls, roll acceptance.",
    )
    # Re-declared for the aggregator only: a field declared again merges onto
    # the earlier definitions' attributes (odoo/fields.py:409-425), so compute,
    # storage and label stay qms_fabric_inspection's. Summed, an average score
    # or colour difference means nothing.
    score = fields.Float(aggregator="avg")
    delta_e = fields.Float(aggregator="avg")
    delta_e_length = fields.Float(aggregator="avg")
    delta_e_width = fields.Float(aggregator="avg")

    # Dimensions for grouping, not stored: each ends on a stored field through
    # Many2one hops (odoo/models.py:2932-2954).
    qms_partner_id = fields.Many2one(
        string="Partner",
        related="inspection_id.picking_id.partner_id",
        help="The receipt's supplier.",
    )
    qms_product_id = fields.Many2one(
        string="Fabric",
        related="inspection_id.product_id",
    )
    qms_inspection_date = fields.Datetime(
        string="Inspection Date",
        related="inspection_id.date",
    )

    @api.depends("points_pass")
    def _compute_qms_accepted(self):
        for roll in self:
            roll.qms_accepted = 100.0 if roll.points_pass else 0.0
