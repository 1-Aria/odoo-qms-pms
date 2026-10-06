# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import FabricInspectionCase

# Seven metres at the cap: 28 points.
SEVEN_FULL_METRES = [(metre, 4) for metre in range(1, 8)]
# 3 + 2 at metre 10, capped to 4, and 1 at metre 11: 5 points, 6 uncapped.
MIXED_METRES = [(10, 3), (10, 2), (11, 1)]


@tagged("post_install", "-at_install")
class TestFabricInspection(FabricInspectionCase):
    """Roll scoring, the verdict and the settings snapshot."""

    def _failing_roll(self, inspection, lot=None):
        """29 points on 100 m x 100 cm: a score of 29 against a limit of 28."""
        return self._roll(
            inspection, lot or self.lot1, 100, 100, SEVEN_FULL_METRES + [(8, 1)]
        )

    # -- settings snapshot ----------------------------------------------

    def test_settings_copied_from_test(self):
        inspection = self._inspect()
        self.assertTrue(inspection.qms_roll_inspection)
        self.assertEqual(inspection.qms_points_limit, 28.0)
        self.assertEqual(inspection.qms_points_cap, 4)

        # A plain test still has a cap: the field defaults to 4.
        plain = self._inspect(self.plain_test)
        self.assertFalse(plain.qms_roll_inspection)
        self.assertEqual(plain.qms_points_limit, 0.0)
        self.assertEqual(plain.qms_points_cap, 4)

        untested = self.env["qc.inspection"].create(
            {"object_id": f"product.product,{self.product.id}"}
        )
        self.assertFalse(untested.qms_roll_inspection)
        self.assertEqual(untested.qms_points_limit, 0.0)
        self.assertEqual(untested.qms_points_cap, 0)

    def test_settings_frozen_after_test_edit(self):
        inspection = self._inspect()
        # A stored compute runs at the next read or flush, not at the write of
        # `test`: read it before the edit, or it would copy the edited values.
        self.assertEqual(inspection.qms_points_limit, 28.0)
        self.assertEqual(inspection.qms_points_cap, 4)
        self.roll_test.write({"qms_points_limit": 40.0, "qms_points_cap": 5})
        # Read back from the database, not from a cache that never refreshed.
        inspection.invalidate_recordset()
        self.assertEqual(inspection.qms_points_limit, 28.0)
        self.assertEqual(inspection.qms_points_cap, 4)

        later = self._inspect()
        self.assertEqual(later.qms_points_limit, 40.0)
        self.assertEqual(later.qms_points_cap, 5)

    def test_settings_follow_test_change(self):
        self.plain_test.qms_points_cap = 0
        inspection = self._inspect()
        self.assertTrue(inspection.qms_roll_inspection)
        inspection.test = self.plain_test
        self.assertFalse(inspection.qms_roll_inspection)
        self.assertEqual(inspection.qms_points_limit, 0.0)
        self.assertEqual(inspection.qms_points_cap, 0)

    def test_rolls_ignored_after_test_change(self):
        inspection = self._inspect()
        roll = self._failing_roll(inspection)
        self.assertFalse(inspection.success)

        inspection.test = self.plain_test
        self.assertTrue(inspection.success)
        self.assertTrue(roll.exists())

        inspection.test = self.roll_test
        self.assertFalse(inspection.success)

    # -- scoring -----------------------------------------------------------

    def test_total_points_capped_per_metre(self):
        roll = self._roll(self._inspect(), self.lot1, points=MIXED_METRES)
        self.assertEqual(roll.total_points, 5)

    def test_no_cap(self):
        self.roll_test.qms_points_cap = 0
        roll = self._roll(self._inspect(), self.lot1, points=MIXED_METRES)
        self.assertEqual(roll.total_points, 6)

    def test_total_follows_position(self):
        roll = self._roll(self._inspect(), self.lot1, points=MIXED_METRES)
        self.assertEqual(roll.total_points, 5)
        roll.point_ids.filtered(lambda point: point.points == 2).position = 12
        self.assertEqual(roll.total_points, 6)

    def test_score_formula(self):
        nine_points = [(1, 4), (2, 4), (3, 1)]
        roll = self._roll(self._inspect(), self.lot1, 100, 150, nine_points)
        self.assertTrue(roll.scored)
        self.assertAlmostEqual(roll.score, 6.0)

    def test_unscored_roll(self):
        roll = self._roll(self._inspect(), self.lot1, 100, 0, [(1, 4)])
        self.assertFalse(roll.scored)
        self.assertEqual(roll.score, 0.0)
        self.assertTrue(roll.points_pass)

    def test_points_against_limit(self):
        inspection = self._inspect()
        at_limit = self._roll(inspection, self.lot1, 100, 100, SEVEN_FULL_METRES)
        self.assertAlmostEqual(at_limit.score, 28.0)
        self.assertTrue(at_limit.points_pass)

        # About 28.019: one-decimal rounding would have stored 28.0 and passed.
        over = self._roll(
            inspection, self.lot2, 100, 103.5, SEVEN_FULL_METRES + [(8, 1)]
        )
        self.assertGreater(over.score, 28.0)
        self.assertLess(over.score, 28.05)
        self.assertFalse(over.points_pass)

    def test_limit_zero_not_judged(self):
        self.roll_test.qms_points_limit = 0.0
        full_roll = [(metre, 4) for metre in range(1, 26)]
        roll = self._roll(self._inspect(), self.lot1, 100, 100, full_roll)
        self.assertAlmostEqual(roll.score, 100.0)
        self.assertTrue(roll.points_pass)

    # -- verdict -----------------------------------------------------------

    def test_success_includes_rolls(self):
        inspection = self._inspect()
        roll = self._failing_roll(inspection)
        self.assertFalse(roll.passed)
        self.assertFalse(inspection.success)

        roll.point_ids.filtered(lambda point: point.position == 8).unlink()
        self.assertTrue(roll.passed)
        self.assertTrue(inspection.success)

    def test_lines_still_decide(self):
        inspection = self._inspect()
        self._roll(inspection, self.lot1, 100, 100, [(1, 1)])
        self.assertTrue(inspection.success)
        line = inspection.inspection_lines
        line.qualitative_value = line.possible_ql_values.filtered(
            lambda value: not value.ok
        )
        self.assertFalse(inspection.success)

    def test_confirm_failing_roll_waits(self):
        inspection = self._inspect()
        self._failing_roll(inspection)
        inspection.action_confirm()
        self.assertEqual(inspection.state, "waiting")
        inspection.action_approve()
        self.assertEqual(inspection.state, "failed")

    def test_confirm_requires_length_and_width(self):
        no_length = self._inspect()
        self._roll(no_length, self.lot1, 0, 150, [(1, 1)])
        with self.assertRaises(UserError):
            no_length.action_confirm()

        no_width = self._inspect()
        self._roll(no_width, self.lot1, 100, 0)
        with self.assertRaises(UserError):
            no_width.action_confirm()

        # Neither measured nor scored: the rest of a sample.
        untouched = self._inspect()
        self._roll(untouched, self.lot1)
        untouched.action_confirm()
        self.assertEqual(untouched.state, "success")

    # -- database rules --------------------------------------------------

    @mute_logger("odoo.sql_db")
    def test_points_range(self):
        roll = self._roll(self._inspect(), self.lot1, 100, 150)
        point = self.env["qms.inspection.point"]
        for values in (
            {"position": 1, "points": 0},
            {"position": 1, "points": 5},
            {"position": 0, "points": 1},
            {"points": 1},
        ):
            with (
                self.subTest(values=values),
                self.assertRaises(IntegrityError),
                self.cr.savepoint(),
            ):
                point.create(dict(values, roll_id=roll.id, defect_code_id=self.slub.id))

    @mute_logger("odoo.sql_db")
    def test_roll_once_per_inspection(self):
        inspection = self._inspect()
        self._roll(inspection, self.lot1)
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._roll(inspection, self.lot1)
        other = self._roll(self._inspect(), self.lot1)
        self.assertTrue(other.exists())

    @mute_logger("odoo.sql_db")
    def test_defect_code_restrict(self):
        self._roll(self._inspect(), self.lot1, points=[(1, 1)])
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.slub.unlink()

    # -- defect-code filter ------------------------------------------------

    def test_code_domain_follows_profiles(self):
        codes = self.env["qms.defect.code"]
        groups = self.fabric_group | self.seam_group
        roll = self._roll(self._inspect(), self.lot1)

        found = codes.search(roll.defect_code_domain)
        self.assertIn(self.slub, found)
        self.assertNotIn(self.open_seam, found)
        self.assertFalse(found & groups)

        roll.inspection_id.qms_show_all_codes = True
        found = codes.search(roll.defect_code_domain)
        self.assertIn(self.slub, found)
        self.assertIn(self.open_seam, found)
        self.assertFalse(found & groups)

        plain = self._inspect(target=self.plain_product)
        found = codes.search(plain.qms_defect_code_domain)
        self.assertIn(self.slub, found)
        self.assertIn(self.open_seam, found)
        self.assertFalse(found & groups)
