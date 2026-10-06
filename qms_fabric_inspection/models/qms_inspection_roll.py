# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# One letter, grouping rolls within a dye lot, or a 555 code: lightness, chroma
# and hue against the approved standard, each 1-9 with 5 on standard.
SHADE_BAND_PATTERN = re.compile(r"^([A-Z]|[1-9]{3})$")


def _normalise_band(value):
    """Strip and upper-case a band, so "a" and "A" group together."""
    return (value or "").strip().upper() or False


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
    # Stored so rolls group by dye lot in reporting; related_sudo keeps it
    # readable by an inspector without Inventory rights.
    dye_lot = fields.Char(
        string="Dye Lot",
        related="lot_id.qms_dye_lot",
        store=True,
    )
    # As read on the spectrophotometer. No digits, for the reason given on
    # `score`: the views show two decimals.
    delta_e = fields.Float(string="ΔE vs Standard")
    delta_e_length = fields.Float(string="ΔE Head–Tail")
    delta_e_width = fields.Float(string="ΔE Side–Centre–Side")
    shade_pass = fields.Boolean(
        string="Shade Pass",
        compute="_compute_shade_pass",
        store=True,
    )
    shade_band = fields.Char(
        string="Shade Band",
        help="The roll's group from shade sorting: one letter, A closest to the "
        "standard, meaningful within the dye lot; or a 555 code of three digits "
        "1-9, lightness, chroma and hue against the standard.",
    )
    # Read by the Points form, which is read-only outside "ready".
    inspection_state = fields.Selection(
        related="inspection_id.state",
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "shade_band" in vals:
                vals["shade_band"] = _normalise_band(vals["shade_band"])
        return super().create(vals_list)

    def write(self, vals):
        if "shade_band" in vals:
            vals = dict(vals, shade_band=_normalise_band(vals["shade_band"]))
        return super().write(vals)

    @api.constrains("shade_band")
    def _check_shade_band(self):
        for roll in self:
            if roll.shade_band and not SHADE_BAND_PATTERN.match(roll.shade_band):
                raise ValidationError(
                    self.env._(
                        "Shade band %(band)s: use one letter (A, B, …) or a 555 "
                        "code of three digits 1–9.",
                        band=roll.shade_band,
                    )
                )

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

    @api.depends(
        "delta_e",
        "delta_e_length",
        "delta_e_width",
        "inspection_id.qms_delta_e_max",
        "inspection_id.qms_delta_e_length_max",
        "inspection_id.qms_delta_e_width_max",
    )
    def _compute_shade_pass(self):
        """Each value within its maximum; a maximum of 0 is not judged.

        An unmeasured value reads 0.0 and passes: "not measured" and "perfect"
        cannot be told apart in a Float.
        """
        for roll in self:
            inspection = roll.inspection_id
            checks = (
                (roll.delta_e, inspection.qms_delta_e_max),
                (roll.delta_e_length, inspection.qms_delta_e_length_max),
                (roll.delta_e_width, inspection.qms_delta_e_width_max),
            )
            roll.shade_pass = all(
                not maximum or value <= maximum for value, maximum in checks
            )

    @api.depends("points_pass", "shade_pass")
    def _compute_passed(self):
        for roll in self:
            roll.passed = roll.points_pass and roll.shade_pass

    def action_qms_open_points(self):
        """The roll's point entries in a dialog, from its row.

        The roll list is editable so shade can be typed for every roll, and an
        editable list cannot open a row's form; core's picking moves solve the
        same with a row button (stock.move.action_show_details).
        """
        self.ensure_one()
        view = self.env.ref("qms_fabric_inspection.qms_inspection_roll_points_form")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Points — %(roll)s", roll=self.lot_id.name),
            "res_model": "qms.inspection.roll",
            "view_mode": "form",
            "views": [(view.id, "form")],
            "target": "new",
            "res_id": self.id,
        }
