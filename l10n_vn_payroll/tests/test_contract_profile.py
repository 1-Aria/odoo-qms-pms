# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestContractProfile(PayrollCase):
    def test_default_labour(self):
        employee = self.env["hr.employee"].create(
            {"name": "Payroll Test New Hire", "company_id": self.company.id}
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Payroll Test New Contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "date_start": D(2026, 1, 1),
                "wage": 1,
                "resource_calendar_id": self.calendar.id,
            }
        )
        self.assertEqual(
            contract.l10n_vn_participant_type_id,
            self.env.ref("l10n_vn_payroll.participant_labour"),
        )

    def test_manager_needs_declared_base(self):
        manager = self.env.ref("l10n_vn_payroll.participant_manager")
        with self.assertRaises(ValidationError):
            self.contract.l10n_vn_participant_type_id = manager
        self.contract.write(
            {"l10n_vn_participant_type_id": manager.id, "l10n_vn_declared_si_base": 10000000}
        )
        self.assertEqual(self.contract.l10n_vn_participant_type_id, manager)

    def test_clause_needs_trial_date(self):
        with self.assertRaises(ValidationError):
            self.contract.l10n_vn_probation_form = "clause"
        self.contract.write({"l10n_vn_probation_form": "clause", "trial_date_end": D(2026, 1, 8)})
        self.assertEqual(self.contract.l10n_vn_probation_form, "clause")

    def test_hr_user_edits_contract_dates(self):
        self.contract.write(
            {
                "l10n_vn_participant_type_id": self.env.ref(
                    "l10n_vn_payroll.participant_labour"
                ).id,
                "l10n_vn_probation_form": "none",
            }
        )
        hr_user = self._user(
            "test.l10n_vn_payroll.contract_hr_user", ["hr_contract.group_hr_contract_manager"]
        )
        contract = self.contract.with_env(self._as(hr_user))
        contract.write({"trial_date_end": D(2026, 1, 31), "date_end": D(2027, 12, 31)})
        self.assertEqual(contract.date_end, D(2027, 12, 31))
