# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import PayrollCase

FUNDS = (
    "fund_pension",
    "fund_sickness",
    "fund_accident",
    "fund_hi",
    "fund_ui",
    "fund_union_fee",
)


@tagged("post_install", "-at_install")
class TestParticipantType(PayrollCase):
    def _type(self, name):
        return self.env.ref(f"l10n_vn_payroll.participant_{name}")

    def test_data_records(self):
        codes = {name: self._type(name).code for name in ("labour", "probation", "manager", "short")}
        self.assertEqual(
            codes,
            {"labour": "LABOUR", "probation": "PROBATION", "manager": "MANAGER", "short": "SHORT"},
        )

    def test_labour(self):
        labour = self._type("labour")
        self.assertTrue(all(labour[fund] for fund in FUNDS))
        self.assertTrue(labour.dues_allowed)
        self.assertEqual(
            (labour.base_source, labour.floor, labour.pit_method),
            ("components", "min_wage", "progressive"),
        )

    def test_manager(self):
        manager = self._type("manager")
        self.assertFalse(manager.fund_ui)
        self.assertTrue(all(manager[fund] for fund in FUNDS if fund != "fund_ui"))
        self.assertEqual(
            (manager.base_source, manager.floor, manager.pit_method),
            ("declared", "reference_level", "progressive"),
        )

    def test_probation_and_short(self):
        for name in ("probation", "short"):
            with self.subTest(name=name):
                record = self._type(name)
                self.assertFalse(any(record[fund] for fund in FUNDS))
                self.assertFalse(record.dues_allowed)
                self.assertEqual(record.pit_method, "flat_short")
