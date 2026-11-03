# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestContractLine(PayrollCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._parameter("TEST.base", [(D(2026, 1, 1), "3700000")])
        cls.level_scale = cls._scale("PROD", "level", {D(2026, 1, 1): {"S4": 2800000}})
        cls.grade_scale = cls._scale("GRADE", "grade_step", {D(2026, 1, 1): {"G2-2": 8000000}})
        cls.salary = cls._component("SALARY")
        cls.base = cls._component(
            "BASE", amount_source="parameter", amount_parameter="TEST.base", sets_wage=True
        )
        cls.prod = cls._component(
            "PROD",
            legal_nature="variable_salary",
            amount_source="scale",
            scale_id=cls.level_scale.id,
            variable=True,
            attainment_source="supervisor",
        )
        cls.perf = cls._component(
            "PERF",
            legal_nature="variable_salary",
            amount_source="scale_remainder",
            scale_id=cls.grade_scale.id,
            variable=True,
            attainment_source="manager",
        )

    def test_line_inside_contract(self):
        with self.assertRaises(ValidationError):
            self._line(self.salary, amount=1000, date_from=D(2025, 12, 31))
        self.contract.date_end = D(2026, 12, 31)
        with self.assertRaises(ValidationError):
            self._line(self.salary, amount=1000, date_to=D(2027, 1, 31))

    def test_line_amount_required(self):
        with self.assertRaises(ValidationError):
            self._line(self.salary)

    def test_scale_key_checked(self):
        with self.assertRaises(ValidationError):
            self._line(self.prod, scale_key="S9")

    def test_no_overlap(self):
        first = self._line(self.salary, amount=1000)
        with self.assertRaises(ValidationError):
            self._line(self.salary, amount=2000, date_from=D(2026, 6, 1))
        first.date_to = D(2026, 5, 31)
        self._line(self.salary, amount=2000, date_from=D(2026, 6, 1))

    def test_one_remainder_per_scale(self):
        perf_2 = self._component(
            "PERF2",
            legal_nature="variable_salary",
            amount_source="scale_remainder",
            scale_id=self.grade_scale.id,
            variable=True,
            attainment_source="manager",
        )
        self._line(self.perf, scale_key="G2-2")
        with self.assertRaises(ValidationError):
            self._line(perf_2, scale_key="G2-2", date_from=D(2026, 3, 1))

    def test_amounts_by_source(self):
        base = self._line(self.base)
        prod_s4 = self._line(self.prod, scale_key="S4", date_to=D(2026, 6, 30))
        prod_amount = self._line(self.prod, amount=3000000, date_from=D(2026, 7, 1))
        self.assertEqual(base._l10n_vn_amount_on(D(2026, 3, 1)), 3700000)
        self.assertEqual(prod_s4._l10n_vn_amount_on(D(2026, 3, 1)), 2800000)
        self.assertEqual(prod_amount._l10n_vn_amount_on(D(2026, 8, 1)), 3000000)

    def test_remainder(self):
        self._line(self.base, in_cell=True)
        perf = self._line(self.perf, scale_key="G2-2", date_to=D(2026, 6, 30))
        perf_g6 = self._line(self.perf, amount=45000000, date_from=D(2026, 7, 1))
        self.assertEqual(perf._l10n_vn_amount_on(D(2026, 3, 1)), 4300000)
        self.assertEqual(perf_g6._l10n_vn_amount_on(D(2026, 8, 1)), 41300000)

    def test_wage_follows_lines(self):
        today = fields.Date.context_today(self.contract)
        tomorrow = fields.Date.add(today, days=1)
        line = self._line(self.base)
        self.assertEqual(self.contract.wage, 3700000)
        line.date_to = today
        self._line(self.base, date_from=tomorrow)
        self.assertEqual(self.contract.wage, 3700000)
        self.contract.l10n_vn_line_ids.unlink()
        self.assertEqual(self.contract.wage, 3700000)

    def test_wage_safe_without_parameter(self):
        missing = self._component(
            "MISSING", amount_source="parameter", amount_parameter="TEST.missing", sets_wage=True
        )
        self._line(missing)
        self.assertEqual(self.contract.wage, 1)

    def test_contract_shortened_past_lines(self):
        self._line(self.salary, amount=1000, date_to=D(2026, 12, 31))
        with self.assertRaises(ValidationError):
            self.contract.date_end = D(2026, 6, 30)

    def test_open_line_on_ended_contract(self):
        # an open line runs until the contract ends, so a leaver's contract can end
        self._line(self.salary, amount=1000)
        self.contract.date_end = D(2026, 6, 30)
        self.assertEqual(self.contract.date_end, D(2026, 6, 30))
