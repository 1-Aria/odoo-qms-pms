# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from .common import FabricInspectionCase


@tagged("post_install", "-at_install")
class TestPopulateDefect(FabricInspectionCase):
    """Populate Defect: the checklist's items, then the rolls' point entries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        question = cls.roll_test.test_lines
        question.ql_values.filtered(lambda value: not value.ok).qms_defect_code_id = (
            cls.hole
        )

    def _nonconformity(self, inspection):
        user = self.env.user
        return self.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Fabric receipt",
                "origin_ids": [
                    (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
                "qc_inspection_id": inspection.id,
                "stage_id": self.env.ref("mgmtsystem_nonconformity.stage_analysis").id,
            }
        )

    def _point(self, roll, position, code):
        return self.env["qms.inspection.point"].create(
            {
                "roll_id": roll.id,
                "position": position,
                "defect_code_id": code.id,
                "points": 1,
            }
        )

    def _inspect_with_entries(self):
        """Slub at 1 and 2 and Hole at 3 on lot 1; Slub at 1 on lot 2."""
        inspection = self._inspect()
        first = self._roll(inspection, self.lot1, 100, 150)
        self._point(first, 1, self.slub)
        self._point(first, 2, self.slub)
        self._point(first, 3, self.hole)
        second = self._roll(inspection, self.lot2, 100, 150)
        self._point(second, 1, self.slub)
        return inspection

    def _answer_not_ok(self, inspection):
        line = inspection.inspection_lines
        line.qualitative_value = line.possible_ql_values.filtered(
            lambda value: not value.ok
        )

    def test_points_become_items(self):
        inspection = self._inspect_with_entries()
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)
        self.assertIs(nonconformity.action_populate_defect(), True)

        slub, hole = nonconformity.item_ids.sorted("sequence")
        self.assertEqual((slub.sequence, hole.sequence), (10, 20))
        self.assertEqual(slub.defect_code_id, self.slub)
        self.assertEqual(slub.qty_affected, 3)
        self.assertIn(self.lot1.name, slub.note)
        self.assertIn(self.lot2.name, slub.note)
        self.assertEqual(hole.defect_code_id, self.hole)
        self.assertEqual(hole.qty_affected, 1)
        self.assertIn(self.lot1.name, hole.note)
        self.assertNotIn(self.lot2.name, hole.note)

    def test_lines_come_first(self):
        inspection = self._inspect_with_entries()
        self._answer_not_ok(inspection)
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)
        nonconformity.action_populate_defect()

        line_item, slub, hole = nonconformity.item_ids.sorted("sequence")
        self.assertEqual(line_item.sequence, 10)
        self.assertEqual(line_item.defect_code_id, self.hole)
        self.assertEqual(line_item.note, "Hand feel")
        self.assertEqual((slub.sequence, hole.sequence), (20, 30))
        self.assertEqual(slub.defect_code_id, self.slub)

    def test_only_points_resolve(self):
        inspection = self._inspect_with_entries()
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)
        self.assertIs(nonconformity.action_populate_defect(), True)
        self.assertEqual(len(nonconformity.item_ids), 2)

    def test_entries_on_passing_rolls_count(self):
        inspection = self._inspect()
        roll = self._roll(inspection, self.lot1, 100, 150)
        self._point(roll, 1, self.slub)
        self.assertTrue(roll.passed)
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)
        nonconformity.action_populate_defect()
        self.assertEqual(nonconformity.item_ids.defect_code_id, self.slub)

    def test_plain_test_rolls_ignored(self):
        inspection = self._inspect_with_entries()
        inspection.test = self.plain_test
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)
        result = nonconformity.action_populate_defect()
        self.assertEqual(result["tag"], "display_notification")
        self.assertFalse(nonconformity.item_ids)

    def test_populate_by_user_without_inventory(self):
        user = self._user_without_inventory("mgmtsystem.group_mgmtsystem_user")
        inspection = self._inspect_with_entries()
        inspection.action_confirm()
        nonconformity = self._nonconformity(inspection)

        nonconformity.with_user(user).action_populate_defect()
        self.assertEqual(len(nonconformity.item_ids), 2)
        self.assertIn(self.lot1.name, nonconformity.item_ids[0].note)

        # The control: the user really cannot read the lot.
        with self.assertRaises(AccessError):
            self.lot1.with_user(user).read(["name"])

    def test_points_action_by_user_without_inventory(self):
        user = self._user_without_inventory()
        roll = self._roll(self._inspect(), self.lot1)
        action = roll.with_user(user).action_qms_open_points()
        self.assertIn(self.lot1.name, action["name"])
