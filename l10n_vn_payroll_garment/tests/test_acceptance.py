# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Group G of the acceptance cases on the loaded garment configuration, night pay, and an option
switched on."""

from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.group_g import GroupGCases
from odoo.addons.l10n_vn_payroll.tests.payslip_common import PayslipCase

from ..models.garment_scheme import ENGINE_CODES


@tagged("post_install", "-at_install")
class TestGarmentAcceptance(GroupGCases, PayslipCase):
    # group G comes from GroupGCases
    allow_inherited_tests_method = True

    @classmethod
    def _l10n_vn_configure(cls):
        cls.company._l10n_vn_garment_load()
        components = (
            cls.env["l10n_vn.payroll.component"]
            .with_context(active_test=False)
            .search([("company_id", "=", cls.company.id)])
        )
        cls.components = {component.code: component for component in components}
        for attribute, code in (
            ("base", "BASE"),
            ("prod", "PROD"),
            ("perf", "PERF"),
            ("eff", "EFF"),
            ("one", "ONE"),
            ("ot_wd", "OT_WD"),
            ("ot_rd", "OT_RD"),
            ("ot_hol", "OT_HOL"),
            ("gross", "GROSS"),
        ):
            setattr(cls, attribute, cls.components[code])
        cls.engine = {code: cls.components[code] for code in ENGINE_CODES - {"GROSS"}}
        cls.structure = cls.env["hr.payroll.structure"].search(
            [("code", "=", "VN_GARMENT"), ("company_id", "=", cls.company.id)]
        )

    @staticmethod
    def _code(code):
        return code

    def test_night_components(self):
        employee, _c = self._worker("Entry")
        self._input(employee, **self._supervised(ot_hours_json={"NIGHT": 8, "NWD": 2}))
        payslip = self._payslip(employee)
        # OT base 3,700,000 + 800,000 = 4,500,000; hourly = 4,500,000 ÷ (26 × 8)
        self.assertEqual(self._totals(payslip, "OT_NIGHT"), [51923])  # × 0.3 × 8 h
        self.assertEqual(self._totals(payslip, "OT_NWD"), [86538])  # × 2.0 × 2 h

    def test_option_switched_on(self):
        duty = self.components["DUTY"]
        duty.active = True
        employee, _c = self._hire(
            lines=[
                (self.base, {"in_cell": True}),
                (self.prod, {"scale_key": "Entry"}),
                (duty, {"amount": 500000}),
            ]
        )
        self._input(employee, **self._supervised())
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "DUTY"), [500000])
        self.assertEqual(payslip.l10n_vn_context["contributions"]["base"], 4200000)
