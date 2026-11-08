# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import itertools

import pytz

from odoo import Command
from odoo.tests import TransactionCase

D = datetime.date
TZ = "Asia/Ho_Chi_Minh"
LOCAL = pytz.timezone(TZ)
# the base week: Monday 5 to Sunday 11 October 2026
MON, TUE, WED, THU, FRI, SAT, SUN = (D(2026, 10, day) for day in range(5, 12))


def _lines(days, ranges):
    return [
        Command.create(
            {
                "name": f"{day} {hour_from}",
                "dayofweek": str(day),
                "hour_from": hour_from,
                "hour_to": hour_to,
                "day_period": period,
            }
        )
        for day in days
        for hour_from, hour_to, period in ranges
    ]


def utc(day, hours):
    """Naive UTC of ``hours`` after local midnight of ``day``; hours may pass 24."""
    moment = LOCAL.localize(
        datetime.datetime.combine(day, datetime.time.min) + datetime.timedelta(hours=hours)
    )
    return moment.astimezone(pytz.utc).replace(tzinfo=None)


class AttendanceDayCase(TransactionCase):
    """Fixtures for hr_attendance_day tests; holds no test methods."""

    _names = itertools.count(1)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Attendance Day Test Company",
                "overtime_employee_threshold": 5,
                "overtime_company_threshold": 48,
                "attendance_overtime_validation": "no_validation",
            }
        )
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=[cls.company.id, *cls.env.companies.ids],
            )
        )
        Calendar = cls.env["resource.calendar"]
        week = range(6)  # Monday to Saturday
        cls.day_calendar = Calendar.create(
            {
                "name": "Attendance Day Test Day Calendar",
                "tz": TZ,
                "company_id": cls.company.id,
                "attendance_ids": _lines(
                    week,
                    [(7.5, 11.5, "morning"), (11.5, 13.0, "lunch"), (13.0, 17.0, "afternoon")],
                ),
            }
        )
        cls.shift_calendar = Calendar.create(
            {
                "name": "Attendance Day Test Shift Calendar",
                "tz": TZ,
                "company_id": cls.company.id,
                "paid_day_hours": 8,
                "attendance_ids": _lines(week, [(6.0, 14.0, "morning"), (14.0, 22.0, "afternoon")]),
            }
        )
        cls.night_calendar = Calendar.create(
            {
                "name": "Attendance Day Test Night Calendar",
                "tz": TZ,
                "company_id": cls.company.id,
                "attendance_ids": _lines(week, [(16.0, 24.0, "afternoon")]),
            }
        )
        cls.employee = cls._hire(cls.day_calendar)

    @classmethod
    def _hire(cls, calendar, date_start=D(2026, 1, 1), date_end=None):
        employee = cls.env["hr.employee"].create(
            {
                "name": f"Attendance Day Test Employee {next(cls._names)}",
                "company_id": cls.company.id,
                "resource_calendar_id": calendar.id,
                "tz": TZ,
            }
        )
        cls._contract(employee, calendar, date_start, date_end)
        return employee

    @classmethod
    def _contract(cls, employee, calendar, date_start, date_end=None):
        return cls.env["hr.contract"].create(
            {
                "name": f"{employee.name} {date_start}",
                "employee_id": employee.id,
                "company_id": cls.company.id,
                "resource_calendar_id": calendar.id,
                "date_start": date_start,
                "date_end": date_end,
                "wage": 1,
                "state": "open",
            }
        )

    def _scan(self, employee, day, start, end=None):
        """An attendance from ``start`` to ``end`` hours after local midnight of ``day``."""
        return self.env["hr.attendance"].create(
            {
                "employee_id": employee.id,
                "check_in": utc(day, start),
                "check_out": utc(day, end) if end is not None else False,
            }
        )

    def _days(self, employee, date_from, date_to=None):
        return employee._attendance_days(date_from, date_to or date_from)[employee.id]

    def _day(self, employee, day):
        return self._days(employee, day)[day]
