# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from .common import D
from .payslip_common import PayslipCase

CONTRIBUTION_CODES = ("EE_SI", "EE_HI", "EE_UI", "ER_PENSION", "ER_SICKNESS", "ER_ACCIDENT",
                      "ER_HI", "ER_UI", "UNION_FEE")


@tagged("post_install", "-at_install")
class TestContributions(PayslipCase):
    def _salary(self, amount=4500000, **values):
        return self._hire(lines=[(self.sal, {"amount": amount})], **values)

    @staticmethod
    def _contributions(payslip):
        return payslip.l10n_vn_context["contributions"]

    def test_floor(self):
        employee, _contract = self._salary(3000000)
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._contributions(payslip)["base"], 3700000)
        self.assertEqual(self._totals(payslip, "EE_SI"), [-296000])

    def test_base_on_last_day(self):
        employee, _contract = self._salary(date_end=D(2026, 10, 24), state="close")
        self._input(employee, paid_days=20, days_worked=20)
        payslip = self._payslip(employee)
        self.assertEqual(self._contributions(payslip)["base"], 4500000)

    def test_leaver_not_liable(self):
        employee, _contract = self._salary(date_end=D(2026, 10, 10), state="close")
        self._input(employee, paid_days=8, days_worked=8)
        payslip = self._payslip(employee)
        for code in CONTRIBUTION_CODES:
            self.assertFalse(self._totals(payslip, code), code)
        contributions = self._contributions(payslip)
        self.assertFalse(contributions["liable"])
        self.assertEqual(contributions["days_without_si"], 18)

    def test_hire_liable(self):
        employee, _contract = self._salary(date_start=D(2026, 10, 13))
        self._input(employee, paid_days=14, days_worked=14)
        payslip = self._payslip(employee)
        contributions = self._contributions(payslip)
        self.assertTrue(contributions["liable"])
        self.assertEqual(contributions["days_without_si"], 12)
        self.assertEqual(self._totals(payslip, "EE_SI"), [-360000])

    def test_dues_cap(self):
        employee, _contract = self._salary(80000000)
        employee.l10n_vn_union_member = True
        self._input(employee)
        self.assertEqual(self._totals(self._payslip(employee), "DUES"), [-253000])

    def test_no_participant_type(self):
        employee, contract = self._salary()
        contract.l10n_vn_participant_type_id = False
        self._input(employee)
        self._stopped(self._payslip(employee), "calculation", "participant type")

    def test_no_region(self):
        employee, _contract = self._salary()
        employee.l10n_vn_region = False
        self._input(employee)
        self._stopped(self._payslip(employee), "calculation", "region")

    def test_month_days_missing(self):
        employee, _contract = self._salary()
        self._input(employee, month_scheduled_days=0)
        self._stopped(self._payslip(employee), "calculation", "rebuild")

    def test_month_scheduled_days_built(self):
        # a calendar of its own: a new company copies the current company's calendar
        monday_to_friday = self.env["resource.calendar"].create(
            {
                "name": "Payroll Test 5x8",
                "company_id": self.company.id,
                "tz": "Asia/Ho_Chi_Minh",
                "attendance_ids": [Command.clear()]
                + [
                    Command.create(
                        {
                            "name": f"{day} {period}",
                            "dayofweek": str(day),
                            "hour_from": hour_from,
                            "hour_to": hour_to,
                            "day_period": period,
                        }
                    )
                    for day in range(5)
                    for period, hour_from, hour_to in (("morning", 8, 12), ("afternoon", 13, 17))
                ],
            }
        )
        employee, _contract = self._salary(
            date_end=D(2026, 10, 10), state="close", resource_calendar_id=monday_to_friday.id
        )
        inp = self.env["l10n_vn.payroll.input"].create(
            {"period_id": self.period.id, "employee_id": employee.id}
        )
        inp._l10n_vn_build()
        self.assertEqual(inp.scheduled_days, 7)
        self.assertEqual(inp.month_scheduled_days, 22)

    def test_missing_engine_component(self):
        self.engine["NET"].active = False
        employee, _contract = self._salary()
        self._input(employee)
        self._stopped(self._payslip(employee), "calculation", "NET")
