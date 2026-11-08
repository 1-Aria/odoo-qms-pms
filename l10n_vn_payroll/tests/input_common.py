# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import pytz

from odoo import Command

from .common import D, PayrollCase

TZ = "Asia/Ho_Chi_Minh"
HOLIDAY = D(2026, 10, 20)


class InputCase(PayrollCase):
    """October 2026 on a Monday–Saturday 8-hour calendar; holds no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the grace period and the OT minimum are Odoo's tolerances (step 10)
        cls.company.write({"overtime_employee_threshold": 5, "overtime_company_threshold": 48})
        cls.company._l10n_vn_payroll_ensure_parameters()
        cls.cal = cls.env["resource.calendar"].create(
            {
                "name": "Payroll Test 6x8",
                "company_id": cls.company.id,
                "tz": TZ,
                "hours_per_day": 8,
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
                    for day in range(6)
                    for period, hour_from, hour_to in (
                        ("morning", 7, 11),
                        ("lunch", 11, 12),
                        ("afternoon", 12, 16),
                    )
                ],
            }
        )
        cls.employee.write({"resource_calendar_id": cls.cal.id, "tz": TZ})
        cls.contract.write({"resource_calendar_id": cls.cal.id})
        cls.env["resource.calendar.leaves"].create(
            {
                "name": "Payroll Test Holiday",
                "company_id": cls.company.id,
                "calendar_id": cls.cal.id,
                "date_from": cls._utc(HOLIDAY, "00:00"),
                "date_to": cls._utc(HOLIDAY, "23:59"),
            }
        )
        cls.period = cls.env["l10n_vn.payroll.period"].create(
            {"date_from": D(2026, 10, 1), "company_id": cls.company.id}
        )

    @staticmethod
    def _utc(day, hhmm):
        hour, minute = (int(x) for x in hhmm.split(":"))
        local = pytz.timezone(TZ).localize(datetime.datetime.combine(day, datetime.time(hour, minute)))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    @staticmethod
    def _october_workdays():
        day, days = D(2026, 10, 1), []
        while day.month == 10:
            if day.weekday() != 6 and day != HOLIDAY:
                days.append(day)
            day += datetime.timedelta(days=1)
        return days

    def _attend(self, day, start="07:00", end="16:00", employee=None):
        return self.env["hr.attendance"].create(
            {
                "employee_id": (employee or self.employee).id,
                "check_in": self._utc(day, start),
                "check_out": self._utc(day, end),
            }
        )

    def _attend_month(self, skip=(), start="07:00", end="16:00"):
        for day in self._october_workdays():
            if day not in skip:
                self._attend(day, start, end)

    def _leave_type(self, name, **values):
        vals = {
            "name": name,
            "company_id": self.company.id,
            "requires_allocation": "no",
            "leave_validation_type": "no_validation",
        }
        vals.update(values)
        return self.env["hr.leave.type"].create(vals)

    def _leave(self, leave_type, first, last, employee=None):
        leave = self.env["hr.leave"].create(
            {
                "employee_id": (employee or self.employee).id,
                "holiday_status_id": leave_type.id,
                "request_date_from": first,
                "request_date_to": last,
            }
        )
        if leave.state != "validate":
            leave.action_validate()
        return leave

    def _build(self, employee=None):
        self.period.action_build()
        employee = employee or self.employee
        return self.period.input_ids.filtered(lambda i: i.employee_id == employee)

    def _calendar(self, name, ranges, **values):
        """A Monday–Saturday calendar from ``(period, hour_from, hour_to)`` ranges."""
        return self.env["resource.calendar"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "tz": TZ,
                "attendance_ids": [Command.clear()]
                + [
                    Command.create(
                        {
                            "name": f"{day} {period} {hour_from}",
                            "dayofweek": str(day),
                            "hour_from": hour_from,
                            "hour_to": hour_to,
                            "day_period": period,
                        }
                    )
                    for day in range(6)
                    for period, hour_from, hour_to in ranges
                ],
                **values,
            }
        )

    def _hire_on(self, calendar):
        """A second employee with an open contract on ``calendar`` from 2026-01-01."""
        employee = self.env["hr.employee"].create(
            {
                "name": f"Payroll Test Employee on {calendar.name}",
                "company_id": self.company.id,
                "resource_calendar_id": calendar.id,
                "tz": TZ,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": f"{employee.name} contract",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "date_start": D(2026, 1, 1),
                "wage": 1,
                "resource_calendar_id": calendar.id,
                "state": "open",
            }
        )
        return employee
