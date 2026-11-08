# hr_attendance_day

Each employee's attendance per day, derived from Odoo's own attendance: day type, scheduled and expected hours, normal hours, days worked, overtime and its night part, late arrival, early leave and absence. One method for server code (payroll, later IE) and three fields on the working calendar; no stored records, screens or scheduled job.
Design: `docs/HR-Contract-Payroll/Attendance Daily Time — Design Note v0.2.md` (AD-xx), on the Attendance Specification v0.4.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The whole module: the calendar fields and their form, `hr.employee._attendance_days()`, tests, readme | done | 2026-11-08, two runs. First: `-i`, 17 tests, 3 failures (`test_overtime`, `test_unapproved`, `test_batch`): the tests expected 1 h of overtime from a 07:30–18:30 scan, which is 1 h 30 after the 17:00 end, as Odoo and the module computed; the scans changed to 07:30–18:00, the code unchanged. Second: `-u`, `exit=0`, 17 tests, 0 failures. UI checked by Peter: the three fields on the calendar form |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | Note §4: depends on `hr_attendance` only | also `hr_contract` | Calendars come from contracts on the instance, and with `hr_contract` installed an employee's calendar periods are their contracts (`hr_contract/models/hr_employee.py:149`). Depending on it makes the result the same in every database and in the tests. Payroll installs it anyway |
| 2 | Note §3: expected hours from `hr.employee._get_expected_attendances()`, lunch from `_employee_attendance_intervals(lunch=True)` | scheduled, expected and lunch intervals from the calendar methods of each calendar period (D3) | One source of periods for all three. `hr_contract` builds expected hours the same way, per contract (`hr_contract/models/hr_employee.py:247-264`), so the result matches Odoo's overtime |
| 3 | Note §4: the method returns `{date: figures}` | `{employee id: {date: figures}}` | It is batched over employees |
| 4 | Note §4: a calendar line starting at 00:00 that continues one ending at 24:00 belongs to the day before | calendars whose shifts cross midnight are not supported (D4) | Odoo's overtime reads the expected intervals only up to midnight after the last attendance date (`hr_attendance/models/hr_attendance.py:394-395`), so a 22:00–06:00 shift is planned as 2 hours and its overtime is wrong. Route A takes Odoo's overtime as it is; no calendar on the instance crosses midnight. A shift ending at 24:00 and presence running past midnight are handled |

## Decisions

| # | Decision |
|---|---|
| D1 | **One reader, no storage:** `hr.employee._attendance_days(date_from, date_to)` computes from Odoo's data at each call and returns plain dictionaries. It writes nothing (AD-01) |
| D2 | **As superuser:** the method reads as superuser for the employees it is given. It is a private method (leading underscore), so it cannot be called through RPC; its callers decide who sees the figures |
| D3 | **Intervals per calendar period:** for each period of `_get_calendar_periods()` and its calendar, scheduled intervals from `_attendance_intervals_batch()`, lunch from `_attendance_intervals_batch(lunch=True)`, expected intervals from `_work_intervals_batch()` (leave and public holidays removed), with `tz` the employee's `tz` when set, else none (the calendar's), as `hr_contract` does. Dates outside every period have no scheduled hours |
| D4 | **The work day:** an attendance belongs to the local date of its check-in in `employee._get_tz()`, as in Odoo's overtime (`hr_attendance.py:296-304`); an interval belongs to the local date of its start. Odoo merges touching intervals (`resource/models/utils.py:117-131`), so quilting's two shifts are one interval 06:00–22:00. The intervals are read from one day before `date_from` to two days after `date_to`, so presence running past midnight meets the next day's schedule and night window. Calendars whose shifts cross midnight are not supported (divergence 4) |
| D5 | **How much time is Odoo's** (AD-02): *D* = the sum of `hr.attendance.overtime.duration` for the employee and date with `adjustment` False; *V* = the sum over the day's attendances of max(0, `validated_overtime_hours`) |
| D6 | **The figures** (note §5): `normal_hours` = 0 without attendance, else max(0, `expected_hours` + min(0, *D*)); `overtime_hours` = min(max(0, *D*), *V*); `unapproved_hours` = max(0, *D*) − `overtime_hours`; `day_hours` = the calendar's `paid_day_hours`, else `scheduled_hours`; `days_worked` = `normal_hours` ÷ `day_hours`, 0 when `day_hours` is 0 |
| D7 | **Night** (AD-07): the window from `night_start` to `night_end` of the date's calendar, crossing midnight when the start is later than the end, taken for the date and the days before and after. `normal_night_hours` = \|*P* ∩ *S* ∩ *N*\|; `overtime_night_hours` = min(`overtime_hours`, \|(*P* − *S*ₐₗₗ − *L*ₐₗₗ) ∩ *N*\|), where *S*ₐₗₗ and *L*ₐₗₗ are the expected and lunch intervals of the whole range, so presence running into the next day's schedule is not taken as overtime |
| D8 | **Late arrival and early leave** (AD-08): references are the first expected interval's start and the last one's end on the date. On a calendar with `paid_day_hours`, the references are instead the start and end of the calendar line nearest to the first check-in and last check-out. The lines are the records of the date's scheduled intervals, placed on the date or the next day by their `dayofweek`, with `hour_to` 24 as midnight. Minutes are whole, from 0; `late` and `early_leave` are minutes above the company's `overtime_employee_threshold` |
| D9 | **Absent and incomplete:** `absent` when `expected_hours` > 0 and the date has no attendance at all; `incomplete` when one of the date's attendances has no check-out. Open attendances count for neither presence nor overtime (Odoo computes no overtime for that day) |
| D10 | **Day type:** `holiday` when a public holiday covers the date: a `resource.calendar.leaves` with no resource, calendar the date's or none, company the employee's or none, whose local dates span it. Else `rest` when `scheduled_hours` is 0, else `workday` |
| D11 | **Which dates:** every date in the range with scheduled hours or an attendance. Hours are rounded to 4 decimals |

## Folder structure

```
hr_attendance_day/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── hr_employee.py
│   └── resource_calendar.py
├── views/
│   └── resource_calendar_views.xml
├── readme/
│   ├── DESCRIPTION.md
│   └── USAGE.md
└── tests/
    ├── __init__.py
    ├── common.py
    └── test_attendance_days.py
```

No `security/` folder: the module adds no model.

## Manifest

| Key | Value |
|---|---|
| `name` | `Attendance Daily Figures` |
| `summary` | `Per-day normal hours, overtime with its night part, late arrivals and absences, derived from Odoo's attendance` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Human Resources/Attendances` |
| `depends` | `hr_attendance`, `hr_contract` |
| `data` | `views/resource_calendar_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import resource_calendar`, `from . import hr_employee` |
| `tests/__init__.py` | `from . import test_attendance_days` |

## Models

### `resource.calendar` — `models/resource_calendar.py`

`_inherit = "resource.calendar"`.

| Field | Type | Attributes |
|---|---|---|
| `paid_day_hours` | Float | string *Hours per Paid Day*, help *Hours that make one paid day. Empty: the day's scheduled hours. Set it on a calendar that combines shifts, so that each shift worked counts as a day.* |
| `night_start` | Float | string *Night From*, default 22.0 |
| `night_end` | Float | string *Night To*, default 6.0 |

**`_check_attendance_day_hours`** — `@api.constrains("paid_day_hours", "night_start", "night_end")`, `ValidationError`: `paid_day_hours` ≥ 0; `night_start` and `night_end` between 0 and 24.

### `hr.employee` — `models/hr_employee.py`

`_inherit = "hr.employee"`.

| Method | Behaviour |
|---|---|
| `_attendance_days(date_from, date_to)` | Dates (`datetime.date`), both included. Returns `{employee.id: {date: figures}}` for the employees in `self` (D1, D2, D11), the figures below |

Per employee, in order:

1. The range: local midnight of `date_from` − 1 day to local midnight of `date_to` + 2 days, in `_get_tz()`, as aware UTC datetimes (D4).
2. Periods from `_get_calendar_periods(start, stop)`; per period, the three interval sets (D3), joined over the periods, and the period calendar of each date.
3. Public holidays over the range (D10).
4. Attendances whose check-in falls in the local dates `date_from`…`date_to`, grouped by date (D4).
5. *D* per date from `hr.attendance.overtime` (D5).
6. Per date with scheduled hours or an attendance: the figures (D6–D10).

**Figures per date:**

| Key | Type | Rule |
|---|---|---|
| `day_type` | str | D10 |
| `scheduled_hours` | float | length of the date's scheduled intervals |
| `expected_hours` | float | length of the date's expected intervals (*S*) |
| `worked_hours` | float | sum of the closed attendances' `worked_hours` |
| `normal_hours`, `day_hours`, `days_worked` | float | D6 |
| `normal_night_hours` | float | D7 |
| `overtime_hours`, `unapproved_hours` | float | D6 |
| `overtime_night_hours` | float | D7 |
| `late_minutes`, `early_leave_minutes` | int | D8 |
| `late`, `early_leave` | bool | D8 |
| `absent`, `incomplete` | bool | D9 |

## Views — `views/resource_calendar_views.xml`

| XML id | Inherits | Change |
|---|---|---|
| `resource_calendar_form` | `resource.resource_calendar_form` | after `//field[@name='hours_per_day']`: `paid_day_hours`, `night_start`, `night_end`, each `widget="float_time"` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | What a day's figures are and where each comes from: Odoo's expected hours, worked hours, overtime and its approval; the module's day type, night part, days worked, late arrival, early leave and absence. No screens: other modules (payroll) read them |
| `readme/USAGE.md` | The settings that shape the figures: the two tolerances in *Attendances → Configuration* (the grace period and the overtime minimum) and their recompute of all past overtime when changed; *Hours per Paid Day* for a calendar that combines shifts; the night window on the calendar |

## Tests

`@tagged("post_install", "-at_install")`: the fixtures create employees, whose work contacts are `res.partner` records. No import from a core `tests` package.

### `tests/common.py` — `AttendanceDayCase(TransactionCase)`

Holds no test methods.

**Fixtures** (`setUpClass`):
- `company`: a new company, `overtime_employee_threshold` 5, `overtime_company_threshold` 48, `attendance_overtime_validation` `no_validation`.
- `day_calendar`, tz `Asia/Ho_Chi_Minh`: Monday–Saturday 07:30–11:30 and 13:00–17:00, with lunch 11:30–13:00.
- `shift_calendar`: Monday–Saturday 06:00–14:00 and 14:00–22:00, `paid_day_hours` 8.
- `night_calendar`: Monday–Saturday 16:00–24:00, no lunch.
- `employee` in `company`, tz `Asia/Ho_Chi_Minh`, with an open contract on `day_calendar` from 2026-01-01.

**Helpers:**
- `_hire(calendar, date_start, date_end=None)`: a new employee with an open contract on that calendar.
- `_scan(employee, day, start, end=None)`: an attendance with local times on that date; `end` the next day when earlier than `start`; no check-out when `end` is None.
- `_days(employee, date_from, date_to=None)` returns `_attendance_days(...)[employee.id]`.

The base week is 2026-10-05 (Monday) to 2026-10-11 (Sunday).

### `tests/test_attendance_days.py` — `TestAttendanceDays(AttendanceDayCase)`

| Test | Scans (local) | Asserts |
|---|---|---|
| `test_on_time_short_stay` | Mon 07:30–17:30 | `workday`; scheduled and expected 8; normal 8; days 1; overtime 0; not late |
| `test_overtime` | Mon 07:30–18:00 | overtime 1; normal 8; night 0 |
| `test_late_within_grace` | Mon 07:34–17:00 | normal 8; `late_minutes` 4; `late` False |
| `test_late_beyond_grace` | Mon 07:45–17:00 | normal 7.75; days 0.9688; `late_minutes` 15; `late` True |
| `test_late_made_up` | Mon 07:45–18:15 | normal 8; overtime 1; `late` True |
| `test_afternoon_only` | Mon 13:00–17:00 | normal 4; days 0.5; `late_minutes` 330 |
| `test_early_leave` | Mon 07:30–16:00 | normal 7; `early_leave_minutes` 60; `early_leave` True |
| `test_rest_day` | Sun 07:30–11:30 | `rest`; scheduled 0; normal 0; overtime 4 |
| `test_public_holiday` | a public holiday on Wed; Wed 07:30–11:30 | `holiday`; expected 0; overtime 4; normal 0 |
| `test_half_day_leave` | a leave for the employee's resource Thu 07:30–11:30; Thu 13:00–17:00 | expected 4; normal 4; days 0.5; not late; not absent |
| `test_absent` | none on Fri | `absent` True; normal 0; days 0 |
| `test_incomplete` | Sat 07:30, no check-out | `incomplete` True; overtime 0; not absent |
| `test_unapproved` | validation `by_manager`; Mon 07:30–18:00 with validated 0.5 | overtime 0.5; unapproved 0.5 |
| `test_shift_calendar` | employee on `shift_calendar`: Mon 06:00–14:00, Tue 14:00–22:00, Wed 06:00–22:00, Thu 06:00–22:30, Fri 06:00–23:30 | scheduled 16 each; days 1, 1, 2, 2, 2; Tue not late (nearest start 14:00); overtime 0, 0, 0, 0, 1.5; Fri night overtime 1.5 |
| `test_night_shift` | employee on `night_calendar`: Mon 16:00–24:00; Tue 16:00–Wed 01:30 | Mon: scheduled 8, normal 8, normal night 2 (22:00–24:00), overtime 0. Tue: normal 8, normal night 2, overtime 1.5, all at night; the attendance counts on Tuesday only |
| `test_two_contracts` | employee on `day_calendar` until 2026-10-07, then `shift_calendar` | scheduled 8 on Mon–Wed, 16 on Thu–Sat; `day_hours` 8 throughout |
| `test_batch` | two employees, one scan each | both employees in the result, each with its own figures |

**Expected count:** 17 tests.
