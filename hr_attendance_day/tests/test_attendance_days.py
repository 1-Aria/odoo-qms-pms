# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.tests import tagged

from .common import FRI, MON, SAT, SUN, THU, TUE, WED, AttendanceDayCase, utc


@tagged("post_install", "-at_install")
class TestAttendanceDays(AttendanceDayCase):
    def _check(self, figures, **expected):
        for key, value in expected.items():
            self.assertEqual(figures[key], value, key)

    # ------------------------------------------------------------------ day calendar
    def test_on_time_short_stay(self):
        self._scan(self.employee, MON, 7.5, 17.5)
        self._check(
            self._day(self.employee, MON),
            day_type="workday",
            scheduled_hours=8,
            expected_hours=8,
            normal_hours=8,
            days_worked=1,
            overtime_hours=0,
            late=False,
            early_leave=False,
        )

    def test_overtime(self):
        self._scan(self.employee, MON, 7.5, 18)
        self._check(
            self._day(self.employee, MON),
            normal_hours=8,
            overtime_hours=1,
            overtime_night_hours=0,
            unapproved_hours=0,
        )

    def test_late_within_grace(self):
        self._scan(self.employee, MON, 7.5 + 4 / 60, 17)
        self._check(self._day(self.employee, MON), normal_hours=8, late_minutes=4, late=False)

    def test_late_beyond_grace(self):
        self._scan(self.employee, MON, 7.75, 17)
        self._check(
            self._day(self.employee, MON),
            normal_hours=7.75,
            days_worked=0.9688,
            late_minutes=15,
            late=True,
        )

    def test_late_made_up(self):
        self._scan(self.employee, MON, 7.75, 18.25)
        self._check(
            self._day(self.employee, MON), normal_hours=8, overtime_hours=1, late=True
        )

    def test_afternoon_only(self):
        self._scan(self.employee, MON, 13, 17)
        self._check(
            self._day(self.employee, MON),
            normal_hours=4,
            days_worked=0.5,
            late_minutes=330,
            late=True,
        )

    def test_early_leave(self):
        self._scan(self.employee, MON, 7.5, 16)
        self._check(
            self._day(self.employee, MON),
            normal_hours=7,
            early_leave_minutes=60,
            early_leave=True,
        )

    def test_rest_day(self):
        self._scan(self.employee, SUN, 7.5, 11.5)
        self._check(
            self._day(self.employee, SUN),
            day_type="rest",
            scheduled_hours=0,
            normal_hours=0,
            overtime_hours=4,
        )

    def test_public_holiday(self):
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Attendance Day Test Holiday",
                "company_id": self.company.id,
                "date_from": utc(WED, 0),
                "date_to": utc(WED, 24) - datetime.timedelta(seconds=1),
                "time_type": "leave",
            }
        )
        self._scan(self.employee, WED, 7.5, 11.5)
        self._check(
            self._day(self.employee, WED),
            day_type="holiday",
            scheduled_hours=8,
            expected_hours=0,
            normal_hours=0,
            overtime_hours=4,
        )

    def test_half_day_leave(self):
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Attendance Day Test Leave",
                "company_id": self.company.id,
                "calendar_id": self.day_calendar.id,
                "resource_id": self.employee.resource_id.id,
                "date_from": utc(THU, 7.5),
                "date_to": utc(THU, 11.5),
                "time_type": "leave",
            }
        )
        self._scan(self.employee, THU, 13, 17)
        self._check(
            self._day(self.employee, THU),
            expected_hours=4,
            normal_hours=4,
            days_worked=0.5,
            late_minutes=0,
            absent=False,
        )

    def test_absent(self):
        self._check(
            self._day(self.employee, FRI), absent=True, normal_hours=0, days_worked=0
        )

    def test_incomplete(self):
        self._scan(self.employee, SAT, 7.5)
        self._check(
            self._day(self.employee, SAT),
            incomplete=True,
            overtime_hours=0,
            normal_hours=0,
            absent=False,
        )

    def test_unapproved(self):
        self.company.attendance_overtime_validation = "by_manager"
        attendance = self._scan(self.employee, MON, 7.5, 18)
        attendance.validated_overtime_hours = 0.5
        self._check(self._day(self.employee, MON), overtime_hours=0.5, unapproved_hours=0.5)

    # ------------------------------------------------------------------ shift calendar
    def test_shift_calendar(self):
        employee = self._hire(self.shift_calendar)
        for day, start, end in (
            (MON, 6, 14),
            (TUE, 14, 22),
            (WED, 6, 22),
            (THU, 6, 22.5),
            (FRI, 6, 23.5),
        ):
            self._scan(employee, day, start, end)
        days = self._days(employee, MON, FRI)
        self.assertEqual([days[d]["scheduled_hours"] for d in (MON, TUE, WED, THU, FRI)], [16] * 5)
        self.assertEqual(
            [days[d]["days_worked"] for d in (MON, TUE, WED, THU, FRI)], [1, 1, 2, 2, 2]
        )
        self.assertEqual(
            [days[d]["overtime_hours"] for d in (MON, TUE, WED, THU, FRI)], [0, 0, 0, 0, 1.5]
        )
        self._check(days[TUE], late_minutes=0, late=False)
        self._check(days[FRI], overtime_night_hours=1.5, normal_night_hours=0)

    def test_night_shift(self):
        employee = self._hire(self.night_calendar)
        self._scan(employee, MON, 16, 24)
        self._scan(employee, TUE, 16, 25.5)
        days = self._days(employee, MON, WED)
        self._check(
            days[MON],
            scheduled_hours=8,
            normal_hours=8,
            normal_night_hours=2,
            overtime_hours=0,
        )
        self._check(
            days[TUE],
            normal_hours=8,
            normal_night_hours=2,
            overtime_hours=1.5,
            overtime_night_hours=1.5,
        )
        self._check(days[WED], worked_hours=0, absent=True)

    def test_two_contracts(self):
        employee = self._hire(self.day_calendar, date_end=WED)
        self._contract(employee, self.shift_calendar, THU)
        days = self._days(employee, MON, SAT)
        self.assertEqual(
            [days[d]["scheduled_hours"] for d in (MON, TUE, WED, THU, FRI, SAT)],
            [8, 8, 8, 16, 16, 16],
        )
        self.assertEqual(
            {days[d]["day_hours"] for d in (MON, TUE, WED, THU, FRI, SAT)}, {8}
        )

    def test_batch(self):
        other = self._hire(self.day_calendar)
        self._scan(self.employee, MON, 7.5, 17)
        self._scan(other, MON, 7.5, 18)
        result = (self.employee | other)._attendance_days(MON, MON)
        self.assertEqual(set(result), {self.employee.id, other.id})
        self.assertEqual(result[self.employee.id][MON]["overtime_hours"], 0)
        self.assertEqual(result[other.id][MON]["overtime_hours"], 1)
