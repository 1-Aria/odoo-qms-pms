# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from .common import FabricInspectionCase


@tagged("post_install", "-at_install")
class TestLoadRolls(FabricInspectionCase):
    """Load rolls: one row per lot of the inspection's receipt line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        supplier = cls.env.ref("stock.stock_location_suppliers")
        stock = cls.env.ref("stock.stock_location_stock")
        line = {
            "product_id": cls.product.id,
            "product_uom_id": cls.product.uom_id.id,
            "location_id": supplier.id,
            "location_dest_id": stock.id,
            "quantity": 100.0,
        }
        # Lot 3 first, so line order and lot creation order differ; lot 2
        # twice; and one line with no lot at all.
        lots = (cls.lot3, cls.lot1, cls.lot2, cls.lot2)
        cls.move = cls.env["stock.move"].create(
            {
                "name": "Fabric receipt",
                "product_id": cls.product.id,
                "product_uom": cls.product.uom_id.id,
                "product_uom_qty": 500.0,
                "location_id": supplier.id,
                "location_dest_id": stock.id,
                "move_line_ids": [(0, 0, dict(line, lot_id=lot.id)) for lot in lots]
                + [(0, 0, line)],
            }
        )

    def _is_notification(self, result):
        return isinstance(result, dict) and result.get("tag") == "display_notification"

    def test_load_one_row_per_lot(self):
        inspection = self._inspect(target=self.move)
        self.assertIs(inspection.action_qms_load_rolls(), True)
        # Rolls are ordered by id, so this is the order they were created in.
        self.assertEqual(
            inspection.qms_roll_ids.mapped("lot_id").ids,
            [self.lot1.id, self.lot2.id, self.lot3.id],
        )

    def test_load_keeps_existing_rows(self):
        inspection = self._inspect(target=self.move)
        existing = self._roll(inspection, self.lot2, 100, 150, [(1, 2)])
        inspection.action_qms_load_rolls()
        self.assertEqual(len(inspection.qms_roll_ids), 3)
        self.assertEqual(
            inspection.qms_roll_ids.lot_id, self.lot1 | self.lot2 | self.lot3
        )
        self.assertEqual(existing.length, 100)
        self.assertEqual(len(existing.point_ids), 1)

    def test_load_twice_notifies(self):
        inspection = self._inspect(target=self.move)
        inspection.action_qms_load_rolls()
        self.assertTrue(self._is_notification(inspection.action_qms_load_rolls()))
        self.assertEqual(len(inspection.qms_roll_ids), 3)

    def test_load_without_move_notifies(self):
        inspection = self._inspect()
        self.assertTrue(self._is_notification(inspection.action_qms_load_rolls()))
        self.assertFalse(inspection.qms_roll_ids)

    def test_load_as_inspector_without_inventory(self):
        inspector = self._user_without_inventory()
        inspection = self._inspect(target=self.move)
        inspection.with_user(inspector).action_qms_load_rolls()
        self.assertEqual(len(inspection.qms_roll_ids), 3)

        # The control: the inspector really cannot read the move.
        with self.assertRaises(AccessError):
            self.move.with_user(inspector).read(["name"])
