# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Group G of the acceptance cases on the loaded garment configuration, night pay, and an option
switched on."""

from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from odoo.addons.l10n_vn_payroll.tests.group_g import GroupGCases
from odoo.addons.l10n_vn_payroll.tests.payslip_common import PayslipCase

from .common import GarmentMixin


@tagged("post_install", "-at_install")
class TestGarmentAcceptance(GarmentMixin, GroupGCases, PayslipCase):
    # group G comes from GroupGCases
    allow_inherited_tests_method = True

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
                (self.base, {"in_cell": True, "scale_key": "WORKER"}),
                (self.prod, {"scale_key": "Entry"}),
                (duty, {"amount": 500000}),
            ]
        )
        self._input(employee, **self._supervised())
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "DUTY"), [500000])
        self.assertEqual(payslip.l10n_vn_context["contributions"]["base"], 4200000)

    def test_base_scale(self):
        _employee, contract = self._worker("S4")
        lines = contract.l10n_vn_line_ids
        base = lines.filtered(lambda line: line.component_id == self.base)
        prod = lines.filtered(lambda line: line.component_id == self.prod)
        october, november = D(2026, 10, 31), D(2026, 11, 30)
        self.assertEqual(base._l10n_vn_amount_on(october), 3700000)
        self.assertEqual(prod._l10n_vn_amount_on(october), 2800000)
        # the base rises, productivity pay falls, the total stays (D18)
        self.assertEqual(base._l10n_vn_amount_on(november), 4500000)
        self.assertEqual(prod._l10n_vn_amount_on(november), 2000000)

    def test_training_allowance(self):
        training = self.env.ref("l10n_vn_payroll.participant_training")
        employee, _c = self._hire(
            lines=[(self.components["TRAIN"], {"amount": 4500000})],
            l10n_vn_participant_type_id=training.id,
        )
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "TRAIN"), [4500000])
        self.assertFalse(self._totals(payslip, "EE_SI"))
        self.assertEqual(self._totals(payslip, "PIT"), [0])
