# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QcInspectionLine(models.Model):
    _inherit = "qc.inspection.line"

    # A failed check is at least one defect: an inspector who fails a line
    # without typing a quantity must not make the defect vanish from DHU and
    # the Pareto. A quantity left on a passing line is ignored, as Populate
    # Defect ignores it.
    qms_qty_defects = fields.Float(
        string="Defects",
        compute="_compute_qms_qty_defects",
        store=True,
        help="On a failed line its quantity failed, or 1 when none was entered; "
        "0 on a passing line.",
    )

    # Dimensions borrowed from the inspection, not stored: Odoo 18 groups by a
    # non-stored related field by joining along its path, which must be
    # Many2one hops ending on a stored field (odoo/models.py:2932-2954). So the
    # partner goes straight to the picking's, not through the inspection's own
    # related field.
    qms_inspection_date = fields.Datetime(
        string="Inspection Date",
        related="inspection_id.date",
    )
    qms_workcenter_id = fields.Many2one(
        string="Work Centre",
        related="inspection_id.qms_workcenter_id",
    )
    qms_partner_id = fields.Many2one(
        string="Partner",
        related="inspection_id.picking_id.partner_id",
        help="The receipt's supplier, or the delivery's customer.",
    )
    qms_test_id = fields.Many2one(
        string="Checkpoint",
        related="inspection_id.test",
    )
    qms_test_category_id = fields.Many2one(
        string="Checkpoint Category",
        related="inspection_id.test.category",
    )
    qms_reinspection = fields.Boolean(
        string="Re-inspection",
        related="inspection_id.qms_reinspection",
    )
    qms_inspection_state = fields.Selection(
        string="Inspection Status",
        related="inspection_id.state",
    )
    qms_roll_inspection = fields.Boolean(
        string="Roll Inspection",
        related="inspection_id.qms_roll_inspection",
    )

    @api.depends("success", "qms_qty_failed")
    def _compute_qms_qty_defects(self):
        for line in self:
            if line.success:
                line.qms_qty_defects = 0.0
            else:
                line.qms_qty_defects = (
                    line.qms_qty_failed if line.qms_qty_failed > 0 else 1.0
                )
