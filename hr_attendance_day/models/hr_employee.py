# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from collections import defaultdict

import pytz

from odoo import models

from odoo.addons.resource.models.utils import Intervals, sum_intervals

ONE_DAY = datetime.timedelta(days=1)
ONE_SECOND = datetime.timedelta(seconds=1)


def _local(tz, day, hours=0.0):
    """The aware datetime ``hours`` after local midnight of ``day``."""
    return tz.localize(
        datetime.datetime.combine(day, datetime.time.min) + datetime.timedelta(hours=hours)
    )


def _aware(tz, value):
    """A naive UTC datetime, as stored, expressed in ``tz``."""
    return pytz.utc.localize(value).astimezone(tz)


def _naive_utc(value):
    return value.astimezone(pytz.utc).replace(tzinfo=None)


def _by_start_date(intervals, tz):
    """Intervals grouped by the local date of their start (D4)."""
    grouped = defaultdict(list)
    for start, stop, records in intervals:
        grouped[start.astimezone(tz).date()].append((start, stop, records))
    return {day: Intervals(items) for day, items in grouped.items()}


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_days(self, date_from, date_to):
        """Each employee's attendance figures per date, from Odoo's attendance.

        ``date_from`` and ``date_to`` are dates, both included. Returns
        ``{employee id: {date: figures}}`` for every date with scheduled hours or an
        attendance. Reads as superuser and writes nothing.
        """
        return {
            employee.id: employee._attendance_days_one(date_from, date_to)
            for employee in self.sudo()
        }

    def _attendance_days_one(self, date_from, date_to):
        self.ensure_one()
        tz = pytz.timezone(self._get_tz())
        # the timezone hr_contract gives the calendar methods (expected attendances)
        interval_tz = pytz.timezone(self.tz) if self.tz else None
        start = _local(tz, date_from - ONE_DAY)
        stop = _local(tz, date_to + 2 * ONE_DAY)
        resource = self.resource_id
        Attendance = self.env["hr.attendance"]

        # intervals per calendar period (D3)
        periods = []
        scheduled, expected, lunch = [], [], []
        for p_start, p_stop, calendar in self._get_calendar_periods(start, stop).get(self, []):
            calendar = calendar or self.company_id.resource_calendar_id
            if not calendar or p_start >= p_stop:
                continue
            periods.append((p_start, p_stop, calendar))
            scheduled.extend(
                calendar._attendance_intervals_batch(
                    p_start, p_stop, resources=resource, tz=interval_tz
                )[resource.id]
            )
            lunch.extend(
                calendar._attendance_intervals_batch(
                    p_start, p_stop, resources=resource, tz=interval_tz, lunch=True
                )[resource.id]
            )
            expected.extend(
                calendar._work_intervals_batch(
                    p_start, p_stop, resources=resource, tz=interval_tz
                )[resource.id]
            )
        expected_all = Intervals(expected)
        lunch_all = Intervals(lunch)
        scheduled_by_day = _by_start_date(Intervals(scheduled), tz)
        expected_by_day = _by_start_date(expected_all, tz)

        def calendar_of(day):
            moment = _local(tz, day)
            for p_start, p_stop, calendar in periods:
                if p_start <= moment < p_stop:
                    return calendar
            return None

        # public holidays (D10)
        holidays = self.env["resource.calendar.leaves"].search(
            [
                ("resource_id", "=", False),
                ("time_type", "=", "leave"),
                ("company_id", "in", [False, self.company_id.id]),
                ("calendar_id", "in", [False] + [c.id for _s, _e, c in periods]),
                ("date_from", "<", _naive_utc(stop)),
                ("date_to", ">", _naive_utc(start)),
            ]
        )
        holiday_spans = [
            (
                leave.calendar_id,
                _aware(tz, leave.date_from).date(),
                _aware(tz, leave.date_to - ONE_SECOND).date(),
            )
            for leave in holidays
        ]

        def is_holiday(day, calendar):
            return any(
                (not leave_calendar or leave_calendar == calendar) and first <= day <= last
                for leave_calendar, first, last in holiday_spans
            )

        # attendances by the local date of their check-in (D4)
        attendances = Attendance.search(
            [
                ("employee_id", "=", self.id),
                ("check_in", ">=", _naive_utc(_local(tz, date_from))),
                ("check_in", "<", _naive_utc(_local(tz, date_to + ONE_DAY))),
            ],
            order="check_in",
        )
        attendances_by_day = defaultdict(lambda: Attendance)
        for attendance in attendances:
            attendances_by_day[_aware(tz, attendance.check_in).date()] |= attendance

        # Odoo's overtime per date (D5)
        overtime_by_day = defaultdict(float)
        for overtime in self.env["hr.attendance.overtime"].search(
            [
                ("employee_id", "=", self.id),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("adjustment", "=", False),
            ]
        ):
            overtime_by_day[overtime.date] += overtime.duration

        grace = self.company_id.overtime_employee_threshold
        result = {}
        day = date_from
        while day <= date_to:
            figures = self._attendance_day_figures(
                day,
                tz,
                calendar_of(day),
                scheduled_by_day.get(day, Intervals()),
                expected_by_day.get(day, Intervals()),
                expected_all,
                lunch_all,
                attendances_by_day.get(day, Attendance),
                overtime_by_day.get(day, 0.0),
                grace,
                is_holiday,
            )
            if figures:
                result[day] = figures
            day += ONE_DAY
        return result

    def _attendance_day_figures(
        self,
        day,
        tz,
        calendar,
        scheduled,
        expected,
        expected_all,
        lunch_all,
        attendances,
        overtime,
        grace,
        is_holiday,
    ):
        """The figures of one date (D6–D10), or None for a date without schedule or attendance."""
        scheduled_hours = sum_intervals(scheduled)
        if not scheduled_hours and not attendances:
            return None
        closed = attendances.filtered("check_out")
        presence = Intervals(
            [(_aware(tz, a.check_in), _aware(tz, a.check_out), a) for a in closed]
        )
        expected_hours = sum_intervals(expected)

        # normal hours and overtime (D6). Odoo's figure keeps the grace period; time present
        # beyond the overtime makes up lateness even when Odoo's company tolerance ignores it.
        worked_hours = sum(closed.mapped("worked_hours"))
        normal_hours = 0.0
        if closed:
            odoo_normal = expected_hours + min(0.0, overtime)
            present = worked_hours - max(0.0, overtime)
            normal_hours = max(0.0, min(expected_hours, max(odoo_normal, present)))
        approved = sum(max(0.0, a.validated_overtime_hours) for a in closed)
        overtime_hours = min(max(0.0, overtime), approved)
        unapproved_hours = max(0.0, overtime) - overtime_hours
        day_hours = (calendar.paid_day_hours if calendar else 0.0) or scheduled_hours

        # night (D7)
        night = self._attendance_night_window(tz, day, calendar)
        normal_night_hours = sum_intervals(presence & expected & night)
        extra = presence - expected_all - lunch_all
        overtime_night_hours = min(overtime_hours, sum_intervals(extra & night))

        # late arrival and early leave (D8)
        late_minutes = early_leave_minutes = 0
        incomplete = bool(attendances - closed)
        if attendances and expected:
            starts, ends = self._attendance_references(day, tz, calendar, scheduled, expected)
            first_in = _aware(tz, attendances[0].check_in)
            if starts:
                reference = min(starts, key=lambda moment: abs(moment - first_in))
                late_minutes = max(0, round((first_in - reference).total_seconds() / 60))
            if closed and not incomplete and ends:
                last_out = max(_aware(tz, a.check_out) for a in closed)
                reference = min(ends, key=lambda moment: abs(moment - last_out))
                early_leave_minutes = max(0, round((reference - last_out).total_seconds() / 60))

        reasons = []
        for attendance in attendances:
            if attendance.correction_reason and attendance.correction_reason not in reasons:
                reasons.append(attendance.correction_reason)
        if is_holiday(day, calendar):
            day_type = "holiday"
        elif not scheduled_hours:
            day_type = "rest"
        else:
            day_type = "workday"
        return {
            "day_type": day_type,
            "scheduled_hours": round(scheduled_hours, 4),
            "expected_hours": round(expected_hours, 4),
            "worked_hours": round(worked_hours, 4),
            "normal_hours": round(normal_hours, 4),
            "day_hours": round(day_hours, 4),
            "days_worked": round(normal_hours / day_hours, 4) if day_hours else 0.0,
            "normal_night_hours": round(normal_night_hours, 4),
            "overtime_hours": round(overtime_hours, 4),
            "unapproved_hours": round(unapproved_hours, 4),
            "overtime_night_hours": round(overtime_night_hours, 4),
            "late_minutes": late_minutes,
            "late": late_minutes > grace,
            "early_leave_minutes": early_leave_minutes,
            "early_leave": early_leave_minutes > grace,
            "absent": expected_hours > 0 and not attendances,
            "incomplete": incomplete,
            # attendances added or changed by hand (D12, D13)
            "corrected": bool(reasons),
            "correction_reasons": reasons,
        }

    def _attendance_night_window(self, tz, day, calendar):
        """The night window around ``day``: the date itself and the days on either side (D7)."""
        night_start = calendar.night_start if calendar else 22.0
        night_end = calendar.night_end if calendar else 6.0
        items = []
        if night_start != night_end:
            empty = self.env["hr.attendance"]
            for each in (day - ONE_DAY, day, day + ONE_DAY):
                end_day = each + ONE_DAY if night_end <= night_start else each
                items.append((_local(tz, each, night_start), _local(tz, end_day, night_end), empty))
        return Intervals(items)

    def _attendance_references(self, day, tz, calendar, scheduled, expected):
        """Starts and ends a check-in and a check-out are measured against (D8).

        On a calendar with hours per paid day, every line of the date is a shift of its own;
        Odoo merges touching lines into one interval, so the lines are read from the
        interval's records.
        """
        if calendar and calendar.paid_day_hours:
            lines = self.env["resource.calendar.attendance"].union(
                *[records for _start, _stop, records in scheduled]
            )
            starts, ends = [], []
            for line in lines:
                line_day = next(
                    (
                        each
                        for each in (day, day + ONE_DAY)
                        if each.weekday() == int(line.dayofweek)
                    ),
                    None,
                )
                if line_day:
                    starts.append(_local(tz, line_day, line.hour_from))
                    ends.append(_local(tz, line_day, line.hour_to))
            return starts, ends
        items = list(expected)
        return [items[0][0]], [items[-1][1]]
