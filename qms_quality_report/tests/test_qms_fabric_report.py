# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.qms_fabric_inspection.tests.common import FabricInspectionCase
from odoo.addons.qms_quality_control.models.mgmtsystem_nonconformity import (
    INSPECTION_DONE_STATES,
)

# Seven metres at the cap: 28 points, the roll test's limit.
SEVEN_FULL_METRES = [(metre, 4) for metre in range(1, 8)]


@tagged("post_install", "-at_install")
class TestFabricReport(FabricInspectionCase):
    """The fabric section: roll acceptance, the aggregators, the domains."""

    def _domain(self, xmlid):
        return safe_eval(self.env.ref(f"qms_quality_report.{xmlid}").domain)

    def _rolls(self):
        """A scored and an unscored roll on a confirmed roll inspection, a
        scored roll on a ready one, and one on an inspection switched to the
        plain test and confirmed."""
        confirmed = self._inspect()
        scored = self._roll(confirmed, self.lot1, 100, 150, [(1, 1)])
        unscored = self._roll(confirmed, self.lot2)
        confirmed.action_confirm()

        ready = self._inspect()
        ready_roll = self._roll(ready, self.lot1, 100, 150, [(1, 1)])

        switched = self._inspect()
        switched_roll = self._roll(switched, self.lot1, 100, 150, [(1, 1)])
        switched.test = self.plain_test
        switched.action_confirm()
        return scored, unscored, ready_roll, switched_roll

    def test_accepted_follows_points_pass(self):
        roll = self._roll(self._inspect(), self.lot1, 100, 100, SEVEN_FULL_METRES)
        self.assertEqual(roll.qms_accepted, 100.0)
        self.env["qms.inspection.point"].create(
            {
                "roll_id": roll.id,
                "position": 8,
                "defect_code_id": self.slub.id,
                "points": 1,
            }
        )
        self.assertFalse(roll.points_pass)
        self.assertEqual(roll.qms_accepted, 0.0)

    def test_aggregators(self):
        """Re-declared for the aggregator only, the rest merged in."""
        fields = self.env["qms.inspection.roll"]._fields
        averaged = (
            "qms_accepted",
            "score",
            "delta_e",
            "delta_e_length",
            "delta_e_width",
        )
        for name in averaged:
            with self.subTest(field=name):
                self.assertEqual(fields[name].aggregator, "avg")
        self.assertEqual(fields["score"].compute, "_compute_score")
        self.assertTrue(fields["score"].store)

    def test_roll_action_domain(self):
        domain = self._domain("qms_inspection_roll_report_action")
        self.assertIn(("inspection_id.state", "in", INSPECTION_DONE_STATES), domain)
        rolls = self._rolls()
        scored = rolls[0]
        candidates = self.env["qms.inspection.roll"].concat(*rolls)
        found = candidates.search(domain + [("id", "in", candidates.ids)])
        self.assertEqual(found, scored)

    def test_shade_action_domain(self):
        domain = self._domain("qms_inspection_shade_report_action")
        self.assertIn(("inspection_id.state", "in", INSPECTION_DONE_STATES), domain)
        scored, unscored, *__ = rolls = self._rolls()
        candidates = self.env["qms.inspection.roll"].concat(*rolls)
        found = candidates.search(domain + [("id", "in", candidates.ids)])
        self.assertEqual(found, scored | unscored)

    def test_point_action_domain(self):
        domain = self._domain("qms_inspection_point_report_action")
        self.assertIn(
            ("roll_id.inspection_id.state", "in", INSPECTION_DONE_STATES), domain
        )
        scored, __, ready_roll, __ = self._rolls()
        candidates = scored.point_ids | ready_roll.point_ids
        found = candidates.search(domain + [("id", "in", candidates.ids)])
        self.assertEqual(found, scored.point_ids)

    def test_related_dimensions_group(self):
        """Non-stored related fields group by joining along their path."""
        roll = self._roll(self._inspect(), self.lot1, 100, 150, [(1, 1)])
        cases = (
            (roll, ("qms_partner_id", "qms_product_id", "qms_inspection_date:month")),
            (
                roll.point_ids,
                (
                    "qms_partner_id",
                    "qms_product_id",
                    "qms_inspection_date:month",
                    "qms_dye_lot",
                ),
            ),
        )
        for records, groupbys in cases:
            for groupby in groupbys:
                with self.subTest(model=records._name, groupby=groupby):
                    groups = records._read_group(
                        [("id", "in", records.ids)], [groupby], ["__count"]
                    )
                    self.assertEqual(sum(count for __, count in groups), 1)

    def test_menus_under_reporting(self):
        reporting = self.env.ref("qms_quality_report.menu_qms_quality_report")
        for xmlid in (
            "menu_qms_inspection_roll_report",
            "menu_qms_inspection_shade_report",
            "menu_qms_inspection_point_report",
        ):
            with self.subTest(menu=xmlid):
                menu = self.env.ref(f"qms_quality_report.{xmlid}")
                self.assertEqual(menu.parent_id, reporting)
