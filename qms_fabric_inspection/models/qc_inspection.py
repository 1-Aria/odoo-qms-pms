# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.qms_quality_control.models.qc_test_question import (
    CHECKLIST_DEFECT_CODE_DOMAIN,
)


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    # The test's settings, frozen: these depend on `test` alone and read the
    # test's fields without depending on them, so a later edit of the test
    # never reaches this inspection. `test` is read-only on the form and both
    # OCA paths write it -- set_test with the header, the Set test wizard by
    # assignment -- and write() calls modified() whether or not the value
    # changed, so writing the same test again still recomputes.
    qms_roll_inspection = fields.Boolean(
        string="Roll Inspection",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_points_limit = fields.Float(
        string="Points Limit (per 100 m²)",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_points_cap = fields.Integer(
        string="Points Cap per Metre",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_delta_e_max = fields.Float(
        string="Max ΔE vs Standard",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_delta_e_length_max = fields.Float(
        string="Max ΔE Head–Tail",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_delta_e_width_max = fields.Float(
        string="Max ΔE Side–Centre–Side",
        compute="_compute_qms_test_settings",
        store=True,
    )
    qms_roll_ids = fields.One2many(
        comodel_name="qms.inspection.roll",
        inverse_name="inspection_id",
        string="Rolls",
    )
    qms_show_all_codes = fields.Boolean(
        string="Show all catalog codes",
        default=False,
        help="Offer every quality defect code on the point entries, instead of "
        "only those in the catalog profiles assigned to this product.",
    )
    # Computed once here and handed down: the roll relates it and the point
    # list reads `parent.defect_code_domain or []`, one level up, which is what
    # the client's `parent` supports in a dialog whose records are still new.
    # The `or []` is for the view validator, which accepts a bare field name
    # or a domain expression but not an attribute access
    # (odoo/tools/view_validation.py:76-126); it never takes effect, since
    # the domain always carries the quality-leaf terms.
    qms_defect_code_domain = fields.Binary(
        string="Defect Code Domain",
        compute="_compute_qms_defect_code_domain",
    )

    @api.depends("test")
    def _compute_qms_test_settings(self):
        for inspection in self:
            test = inspection.test
            inspection.qms_roll_inspection = test.qms_roll_inspection
            inspection.qms_points_limit = test.qms_points_limit
            inspection.qms_points_cap = test.qms_points_cap
            inspection.qms_delta_e_max = test.qms_delta_e_max
            inspection.qms_delta_e_length_max = test.qms_delta_e_length_max
            inspection.qms_delta_e_width_max = test.qms_delta_e_width_max

    @api.depends("qms_roll_inspection", "qms_roll_ids.passed")
    def _compute_success(self):
        """OCA's verdict, and on a roll inspection every roll passing too.

        Odoo merges the @api.depends of every override along the MRO, so OCA's
        own dependencies on the lines need not be restated here.

        Rolls count only on a roll inspection: set_test and the Set test wizard
        rebuild the question lines alone, so rolls survive a change of test.
        After a switch to a plain test they are hidden, and must not decide.
        """
        res = super()._compute_success()
        for inspection in self:
            if inspection.qms_roll_inspection:
                inspection.success = inspection.success and all(
                    inspection.qms_roll_ids.mapped("passed")
                )
        return res

    @api.depends("product_id.qms_effective_profile_ids", "qms_show_all_codes")
    def _compute_qms_defect_code_domain(self):
        """Quality leaf codes, narrowed to the product's profiles when that helps.

        The quality half holds in every branch, as on the checklists; the
        profile term only narrows, and the switch or a product with no profile
        widens back, so the filter stays advisory (plan D7).
        """
        for inspection in self:
            domain = list(CHECKLIST_DEFECT_CODE_DOMAIN)
            profiles = inspection.product_id.qms_effective_profile_ids
            if profiles and not inspection.qms_show_all_codes:
                domain.append(("parent_id.profile_ids", "in", profiles.ids))
            inspection.qms_defect_code_domain = domain

    def action_confirm(self):
        # Before OCA's checks, so an incomplete roll fails on the roll, the
        # thing the inspector is looking at.
        self._qms_check_rolls()
        return super().action_confirm()

    def _qms_check_rolls(self):
        """A roll that was started must be measured both ways to be scored."""
        for inspection in self.filtered("qms_roll_inspection"):
            for roll in inspection.qms_roll_ids:
                started = roll.point_ids or roll.length or roll.width
                if started and not (roll.length and roll.width):
                    raise UserError(
                        self.env._(
                            "Roll %(roll)s: enter both its length and width to "
                            "score it, or remove its point entries.",
                            roll=roll.lot_id.name,
                        )
                    )
