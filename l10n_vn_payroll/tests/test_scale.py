# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestScale(PayrollCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.scale = cls._scale(
            "PROD",
            "level",
            {D(2026, 1, 1): {"S4": 2800000}, D(2027, 1, 1): {"S4": 3000000}},
        )

    def test_cell_by_date(self):
        self.assertEqual(self.scale._cell_amount("S4", D(2026, 12, 31)), 2800000)
        self.assertEqual(self.scale._cell_amount("S4", D(2027, 1, 1)), 3000000)

    def test_missing_cell_raises(self):
        with self.assertRaises(UserError):
            self.scale._cell_amount("S9", D(2026, 6, 1))
        with self.assertRaises(UserError):
            self.scale._cell_amount("S4", D(2025, 12, 31))

    def test_has_key(self):
        self.assertTrue(self.scale._has_key("S4"))
        self.assertFalse(self.scale._has_key("S9"))

    def test_unique_version_date(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["l10n_vn.payroll.scale.version"].create(
                {"scale_id": self.scale.id, "date_from": D(2026, 1, 1)}
            )
