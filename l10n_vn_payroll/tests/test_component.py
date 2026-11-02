# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestComponent(PayrollCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.level_scale = cls._scale("PROD", "level", {D(2026, 1, 1): {"S4": 2800000}})
        cls.grade_scale = cls._scale("GRADE", "grade_step", {D(2026, 1, 1): {"G2-2": 8000000}})

    def test_scale_source_needs_scale(self):
        with self.assertRaises(ValidationError):
            self._component("NOSCALE", amount_source="scale")

    def test_engine_needs_code(self):
        with self.assertRaises(ValidationError):
            self._component("NOCODE", kind="deduction", amount_source="engine")
        with self.assertRaises(ValidationError):
            self._component("LINECODE", engine_code="PIT")

    def test_ot_needs_category(self):
        with self.assertRaises(ValidationError):
            self._component("OTNOCAT", amount_source="ot", proration=False, pit_treatment="ot")
        with self.assertRaises(ValidationError):
            self._component(
                "SUPP",
                amount_source="ot",
                ot_category="all",
                proration=False,
                pit_treatment="ot",
            )

    def test_earning_needs_treatment(self):
        with self.assertRaises(ValidationError):
            self._component("NOPRO", proration=False)
        with self.assertRaises(ValidationError):
            self._component("NOPIT", pit_treatment=False)

    def test_variable_needs_source(self):
        with self.assertRaises(ValidationError):
            self._component("VARNOSRC", variable=True)
        with self.assertRaises(ValidationError):
            self._component(
                "VARDED",
                kind="deduction",
                legal_nature="statutory",
                amount_source="engine",
                engine_code="PIT",
                variable=True,
                attainment_source="manager",
            )

    def test_exempt_cap_needs_parameter(self):
        with self.assertRaises(ValidationError):
            self._component("CAP", legal_nature="welfare", pit_treatment="exempt_cap")

    def test_entered_needs_no_proration(self):
        self._component("ONE", legal_nature="bonus", amount_source="entered", proration=False)

    def test_code_unique_per_company(self):
        self._component("DUP")
        other = self.env["res.company"].create({"name": "Payroll Test Other Company"})
        self._component("DUP", company_id=other.id)
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._component("DUP")

    def test_valid_examples(self):
        self._component("BASE", amount_source="parameter", amount_parameter="TEST.base")
        self._component(
            "PROD",
            legal_nature="variable_salary",
            amount_source="scale",
            scale_id=self.level_scale.id,
            variable=True,
            attainment_source="supervisor",
        )
        self._component(
            "PERF",
            legal_nature="variable_salary",
            amount_source="scale_remainder",
            scale_id=self.grade_scale.id,
            variable=True,
            attainment_source="manager",
        )
        self._component(
            "OT_WD",
            legal_nature="overtime",
            amount_source="ot",
            ot_category="WD",
            proration=False,
            pit_treatment="ot",
            section="ot",
        )
        self._component(
            "PIT",
            kind="deduction",
            legal_nature="statutory",
            amount_source="engine",
            engine_code="PIT",
            proration=False,
            pit_treatment=False,
            section="deduction",
        )
