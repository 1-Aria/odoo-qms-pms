# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import tagged

from .common import FabricInspectionCase

# The common roll test's maxima: 1.0 vs standard, 0.8 head-tail and
# side-centre-side.
DELTA_E_MAXIMA = (
    ("delta_e", 1.0),
    ("delta_e_length", 0.8),
    ("delta_e_width", 0.8),
)


@tagged("post_install", "-at_install")
class TestShade(FabricInspectionCase):
    """Shade on the roll, the band, and dye lot and band on the lot."""

    # -- shade verdict -------------------------------------------------------

    def test_delta_e_settings_copied(self):
        inspection = self._inspect()
        self.assertEqual(inspection.qms_delta_e_max, 1.0)
        self.assertEqual(inspection.qms_delta_e_length_max, 0.8)
        self.assertEqual(inspection.qms_delta_e_width_max, 0.8)

    def test_shade_pass_each_limit(self):
        """Each value is wired to its own maximum."""
        inspection = self._inspect()
        roll = self._roll(inspection, self.lot1)
        for field, maximum in DELTA_E_MAXIMA:
            with self.subTest(field=field):
                roll[field] = maximum
                self.assertTrue(roll.shade_pass)
                self.assertTrue(inspection.success)

                roll[field] = maximum + 0.01
                self.assertFalse(roll.shade_pass)
                self.assertFalse(roll.passed)
                self.assertFalse(inspection.success)
                roll[field] = 0.0

    def test_delta_e_max_zero_not_judged(self):
        self.roll_test.write(
            {
                "qms_delta_e_max": 0.0,
                "qms_delta_e_length_max": 0.0,
                "qms_delta_e_width_max": 0.0,
            }
        )
        roll = self._roll(
            self._inspect(),
            self.lot1,
            delta_e=5.0,
            delta_e_length=5.0,
            delta_e_width=5.0,
        )
        self.assertTrue(roll.shade_pass)

    def test_unmeasured_delta_e_passes(self):
        roll = self._roll(self._inspect(), self.lot1)
        self.assertTrue(roll.shade_pass)

    def test_passed_needs_points_and_shade(self):
        inspection = self._inspect()
        shade_fails = self._roll(inspection, self.lot1, 100, 100, delta_e=2.0)
        self.assertTrue(shade_fails.points_pass)
        self.assertFalse(shade_fails.passed)

        # 32 points on 100 m x 100 cm against a limit of 28.
        eight_full_metres = [(metre, 4) for metre in range(1, 9)]
        points_fail = self._roll(inspection, self.lot2, 100, 100, eight_full_metres)
        self.assertTrue(points_fail.shade_pass)
        self.assertFalse(points_fail.passed)

    # -- band ----------------------------------------------------------------

    def test_band_normalised(self):
        inspection = self._inspect()
        roll = self._roll(inspection, self.lot1, shade_band=" a ")
        self.assertEqual(roll.shade_band, "A")
        code = self._roll(inspection, self.lot2, shade_band="455")
        self.assertEqual(code.shade_band, "455")

        roll.shade_band = " b"
        self.assertEqual(roll.shade_band, "B")
        roll.shade_band = "  "
        self.assertFalse(roll.shade_band)

    def test_band_format_refused(self):
        inspection = self._inspect()
        for band in ("AB", "4 55", "055", "1234", "A1"):
            with (
                self.subTest(band=band),
                self.assertRaises(ValidationError),
                self.cr.savepoint(),
            ):
                self._roll(inspection, self.lot1, shade_band=band)

    # -- dye lot -------------------------------------------------------------

    def test_dye_lot_from_name(self):
        lot = self.env["stock.lot"]
        prefix = self.prefix

        def make(name):
            return lot.create({"name": prefix + name, "product_id": self.product.id})

        self.assertEqual(make("JJD1015-1").qms_dye_lot, f"{prefix}JJD1015")
        self.assertEqual(make("A-B-12").qms_dye_lot, f"{prefix}A-B")
        self.assertFalse(make("1111").qms_dye_lot)

        corrected = make("ODD1")
        corrected.qms_dye_lot = "ODD"
        corrected.invalidate_recordset()
        self.assertEqual(corrected.qms_dye_lot, "ODD")

        corrected.name = f"{prefix}NEW-1"
        self.assertEqual(corrected.qms_dye_lot, f"{prefix}NEW")

    def test_roll_dye_lot_follows_lot(self):
        roll = self._roll(self._inspect(), self.lot1)
        self.assertEqual(roll.dye_lot, f"{self.prefix}DL")
        self.lot1.qms_dye_lot = "OTHER"
        self.assertEqual(roll.dye_lot, "OTHER")

    # -- band on the lot -----------------------------------------------------

    def test_lot_band_from_confirmed_inspection(self):
        first = self._inspect()
        self._roll(first, self.lot1, shade_band="A")
        self.assertFalse(self.lot1.qms_shade_band)
        first.action_confirm()
        self.assertEqual(self.lot1.qms_shade_band, "A")

        second = self._inspect()
        self._roll(second, self.lot1, shade_band="B")
        second.action_confirm()
        self.assertEqual(self.lot1.qms_shade_band, "B")

        # Scored, not banded: the earlier band stays.
        third = self._inspect()
        self._roll(third, self.lot1)
        third.action_confirm()
        self.assertEqual(self.lot1.qms_shade_band, "B")

        cancelled = self._inspect()
        self._roll(cancelled, self.lot1, shade_band="C")
        cancelled.action_cancel()
        self.assertEqual(self.lot1.qms_shade_band, "B")

    def test_lot_band_ignores_plain_test(self):
        inspection = self._inspect()
        self._roll(inspection, self.lot1, shade_band="A")
        inspection.test = self.plain_test
        inspection.action_confirm()
        self.assertFalse(self.lot1.qms_shade_band)

    def test_lot_band_by_inspector_without_inventory(self):
        inspector = self.env["res.users"].create(
            {
                "name": "Fabric inspector",
                "login": f"{self.prefix}-inspector",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref(
                                "quality_control_oca.group_quality_control_user"
                            ).id,
                        ],
                    )
                ],
            }
        )
        inspection = self._inspect()
        roll = self._roll(inspection, self.lot1)

        roll.with_user(inspector).shade_band = "A"
        inspection.with_user(inspector).action_confirm()
        self.assertEqual(self.lot1.qms_shade_band, "A")

        # The control: the inspector really cannot read the lot.
        with self.assertRaises(AccessError):
            self.lot1.with_user(inspector).read(["name"])

    # -- points dialog -------------------------------------------------------

    def test_open_points_action(self):
        roll = self._roll(self._inspect(), self.lot1)
        action = roll.action_qms_open_points()
        view = self.env.ref("qms_fabric_inspection.qms_inspection_roll_points_form")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "qms.inspection.roll")
        self.assertEqual(action["res_id"], roll.id)
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["views"], [(view.id, "form")])
