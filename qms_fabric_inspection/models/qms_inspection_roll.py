# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models


class QmsInspectionRoll(models.Model):
    _name = "qms.inspection.roll"
    _description = "Inspected Roll"
    _order = "inspection_id, id"

    inspection_id = fields.Many2one(
        comodel_name="qc.inspection",
        required=True,
        ondelete="cascade",
        index=True,
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Roll",
        required=True,
        ondelete="restrict",
        index=True,
    )
    length = fields.Float(string="Length (m)")
    width = fields.Float(string="Width (cm)")
    point_ids = fields.One2many(
        comodel_name="qms.inspection.point",
        inverse_name="roll_id",
        string="Point Entries",
    )
    defect_code_domain = fields.Binary(
        related="inspection_id.qms_defect_code_domain",
    )
    # Everything reporting reads is stored. An unscored roll stores its score
    # as 0.0 -- a Float cannot hold "no score" through the ORM -- so anything
    # averaging scores filters on `scored`.
    total_points = fields.Integer(
        string="Points",
        compute="_compute_total_points",
        store=True,
    )
    scored = fields.Boolean(
        compute="_compute_scored",
        store=True,
    )
    # No digits: a Float with digits is rounded as it is assigned
    # (Float.convert_to_cache), so 28.02 would be stored as 28.0 and pass a
    # limit of 28. The views show one decimal, where it decides nothing.
    score = fields.Float(
        string="Score (per 100 m²)",
        compute="_compute_score",
        store=True,
    )
    points_pass = fields.Boolean(
        string="Points Pass",
        compute="_compute_points_pass",
        store=True,
    )
    passed = fields.Boolean(
        string="Pass",
        compute="_compute_passed",
        store=True,
    )

    _sql_constraints = [
        (
            "lot_unique_per_inspection",
            "UNIQUE (inspection_id, lot_id)",
            "A roll can appear only once in an inspection.",
        ),
        (
            "length_positive",
            "CHECK (length >= 0)",
            "A roll's length cannot be negative.",
        ),
        (
            "width_positive",
            "CHECK (width >= 0)",
            "A roll's width cannot be negative.",
        ),
    ]

    @api.depends("lot_id")
    def _compute_display_name(self):
        for roll in self:
            roll.display_name = roll.lot_id.display_name or ""

    @api.depends(
        "point_ids.points", "point_ids.position", "inspection_id.qms_points_cap"
    )
    def _compute_total_points(self):
        """The points per metre, each metre capped, summed.

        The cap counts metres, not entries: a running defect is entered once
        per metre it covers, and the cap keeps one metre at 4.
        """
        for roll in self:
            per_metre = defaultdict(int)
            for point in roll.point_ids:
                per_metre[point.position] += point.points
            cap = roll.inspection_id.qms_points_cap
            roll.total_points = sum(
                min(points, cap) if cap > 0 else points
                for points in per_metre.values()
            )

    @api.depends("length", "width")
    def _compute_scored(self):
        for roll in self:
            roll.scored = roll.length > 0 and roll.width > 0

    @api.depends("scored", "total_points", "length", "width")
    def _compute_score(self):
        """Points per 100 m².

        The area in m² is length x width / 100, so points per 100 m² is
        points x 100 / area = points x 10000 / (length m x width cm).
        """
        for roll in self:
            if roll.scored:
                roll.score = roll.total_points * 10000 / (roll.length * roll.width)
            else:
                roll.score = 0.0

    @api.depends("scored", "score", "inspection_id.qms_points_limit")
    def _compute_points_pass(self):
        """Not scored, or not judged (a limit of 0), or within the limit."""
        for roll in self:
            limit = roll.inspection_id.qms_points_limit
            roll.points_pass = not roll.scored or not limit or roll.score <= limit

    @api.depends("points_pass")
    def _compute_passed(self):
        for roll in self:
            roll.passed = roll.points_pass
