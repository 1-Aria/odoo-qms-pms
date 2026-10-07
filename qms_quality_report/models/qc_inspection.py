# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    # DHU's numerator on the inspection row.
    qms_qty_defects = fields.Float(
        string="Defects",
        compute="_compute_qms_qty_defects",
        store=True,
        help="The defects of the inspection's lines.",
    )
    # Derived, never entered: the production order's work orders, when they all
    # use one work centre. A routing with several leaves it empty.
    qms_workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Centre",
        compute="_compute_qms_workcenter_id",
        store=True,
        index=True,
        help="The work centre of the production order's work orders, when they "
        "all use one.",
    )
    # A plain 100/0, not empty outside finished states: a computed Float cannot
    # store empty (odoo/fields.py:1685-1689), and the action's domain keeps
    # only finished inspections, so the average is always over the right rows.
    qms_defect_free = fields.Float(
        string="Defect-free (%)",
        compute="_compute_qms_defect_free",
        store=True,
        aggregator="avg",
        help="100 for an inspection with no failed line, 0 otherwise; averaged, "
        "the share of defect-free inspections.",
    )
    qms_partner_id = fields.Many2one(
        string="Partner",
        related="picking_id.partner_id",
        help="The receipt's supplier, or the delivery's customer.",
    )
    qms_test_category_id = fields.Many2one(
        string="Checkpoint Category",
        related="test.category",
    )

    @api.depends("inspection_lines.qms_qty_defects")
    def _compute_qms_qty_defects(self):
        for inspection in self:
            inspection.qms_qty_defects = sum(
                inspection.inspection_lines.mapped("qms_qty_defects")
            )

    @api.depends("production_id.workorder_ids.workcenter_id")
    def _compute_qms_workcenter_id(self):
        for inspection in self:
            workcenters = inspection.production_id.workorder_ids.workcenter_id
            inspection.qms_workcenter_id = (
                workcenters if len(workcenters) == 1 else False
            )

    @api.depends("success")
    def _compute_qms_defect_free(self):
        for inspection in self:
            inspection.qms_defect_free = 100.0 if inspection.success else 0.0
