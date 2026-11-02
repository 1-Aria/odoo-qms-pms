# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import D, PayrollCase

PAY_DATE = D(2026, 2, 10)


@tagged("post_install", "-at_install")
class TestPitMethod(PayrollCase):
    def _method(self):
        return self.contract._l10n_vn_pit_method(PAY_DATE)

    def test_labour_open_ended(self):
        self.assertEqual(self._method(), "progressive")

    def test_non_resident(self):
        self.employee.l10n_vn_resident = False
        self.assertEqual(self._method(), "flat_nonresident")

    def test_short_contract(self):
        self.contract.date_end = D(2026, 2, 28)
        self.assertEqual(self._method(), "flat_short")
        self.employee.l10n_vn_pit_commitment_year = 2026
        self.assertEqual(self._method(), "progressive")
        self.employee.l10n_vn_pit_commitment_year = 2025
        self.assertEqual(self._method(), "flat_short")

    def test_three_months_is_not_short(self):
        self.contract.date_end = D(2026, 3, 31)
        self.assertEqual(self._method(), "progressive")

    def test_probation_type(self):
        self.contract.l10n_vn_participant_type_id = self.env.ref(
            "l10n_vn_payroll.participant_probation"
        )
        self.assertEqual(self._method(), "flat_short")
