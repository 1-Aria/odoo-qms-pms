# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The monthly summary on the day figures of hr_attendance_day (step 10)."""

import datetime

from odoo.tests import tagged

from .common import D
from .input_common import InputCase


@tagged("post_install", "-at_install")
class TestInputTime(InputCase):
    def test_grace_paid(self):
        self._attend_month(start="07:04")
        inp = self._build()
        self.assertAlmostEqual(inp.days_worked, 26)
        self.assertEqual(inp.late_arrivals, 0)

    def test_late_arrivals(self):
        late = (D(2026, 10, 5), D(2026, 10, 6))
        self._attend_month(skip=late)
        for day in late:
            self._attend(day, "07:20", "16:00")
        inp = self._build()
        self.assertEqual(inp.late_arrivals, 2)
        self.assertAlmostEqual(inp.days_worked, 26 - 2 * 20 / 480, places=4)

    def test_exception_mode(self):
        self.employee.l10n_vn_pay_group = "office"
        self.assertEqual(self.employee.l10n_vn_attendance_mode, "exception")
        day = D(2026, 10, 12)
        self._leave(self._leave_type("Payroll Test Annual"), day, day)
        inp = self._build()
        self.assertAlmostEqual(inp.days_worked, 25)
        self.assertAlmostEqual(inp.company_leave_days, 2)
        self.assertEqual(inp.unexcused_absences, 0)
        self.assertEqual(inp.late_arrivals, 0)

    def test_night_categories(self):
        monday, tuesday, sunday = D(2026, 10, 5), D(2026, 10, 6), D(2026, 10, 11)
        self._attend_month(skip=(monday, tuesday))
        self._attend(monday, "07:00", "23:00")
        self._attend(tuesday, "07:00", "16:00")
        self._attend(tuesday, "22:00", "23:30")
        self._attend(sunday, "18:00", "23:00")
        inp = self._build()
        self.assertEqual(
            inp.ot_hours_json,
            {"WD": 6.0, "NWD_AFTER": 1.0, "NWD": 1.5, "RD": 4.0, "NRD": 1.0},
        )
        self.assertAlmostEqual(inp.ot_hours, 13.5)
        self.assertAlmostEqual(inp.ot_night_hours, 3.5)
        self.assertEqual(inp.night_hours, 0)

    def test_normal_night(self):
        calendar = self._calendar("Payroll Test Late Shift", [("afternoon", 15, 23)])
        employee = self._hire_on(calendar)
        day = D(2026, 10, 1)
        while day.month == 10:
            if day.weekday() != 6:  # Monday to Saturday: 27 days, no holiday on this calendar
                self._attend(day, "15:00", "23:00", employee=employee)
            day += datetime.timedelta(days=1)
        inp = self._build(employee)
        self.assertAlmostEqual(inp.night_hours, 27)
        self.assertEqual(inp.ot_hours, 0)
        self.assertAlmostEqual(inp.days_worked, 27)

    def test_paid_day_hours(self):
        calendar = self._calendar(
            "Payroll Test Two Shifts",
            [("morning", 6, 14), ("afternoon", 14, 22)],
            paid_day_hours=8,
        )
        employee = self._hire_on(calendar)
        self._attend(D(2026, 10, 5), "06:00", "14:00", employee=employee)
        self._attend(D(2026, 10, 6), "06:00", "22:00", employee=employee)
        leave_day = D(2026, 10, 7)
        self._leave(self._leave_type("Payroll Test Annual"), leave_day, leave_day, employee)
        inp = self._build(employee)
        self.assertAlmostEqual(inp.days_worked, 3)
        self.assertAlmostEqual(inp.company_leave_days, 1)
        # the 16-hour day is a long day, but no overtime is over the daily limit
        self.assertEqual(inp.long_days, 1)
        self.assertEqual(inp.ot_over_daily_hours, 0)

    def test_daily_limit_and_long_days(self):
        workday, sunday = D(2026, 10, 7), D(2026, 10, 18)
        self._attend_month(skip=(workday,))
        self._attend(workday, "07:00", "21:00")
        self._attend(sunday, "07:00", "20:00")
        inp = self._build()
        self.assertAlmostEqual(inp.ot_over_daily_hours, 2)
        self.assertEqual(inp.long_days, 2)

    def test_corrections_counted(self):
        day = D(2026, 10, 5)
        self._attend_month(skip=(day,))
        self._attend(day, "07:00", "16:00").correction_reason = "Forgot check-out"
        inp = self._build()
        self.assertEqual(inp.corrected_days, 1)
        self.assertEqual(inp.corrections_json, {"2026-10-05": ["Forgot check-out"]})

    def test_incomplete_day(self):
        last = D(2026, 10, 31)
        self._attend_month(skip=(last,))
        # Odoo refuses an attendance after an open one: the open one comes last
        self.env["hr.attendance"].create(
            {"employee_id": self.employee.id, "check_in": self._utc(last, "07:00")}
        )
        inp = self._build()
        self.assertEqual(inp.incomplete_days, 1)
        self.assertAlmostEqual(inp.days_worked, 25)
        self.assertEqual(inp.unexcused_absences, 0)
