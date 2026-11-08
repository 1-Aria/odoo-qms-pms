# Attendance Daily Time — Design Note

v0.1 (draft) · Nov 8, 2026 · @Peter · **for decision**

**Purpose:** settle how a new attendance module classifies each employee's day (normal hours, overtime by category, night hours, late arrivals, absences) before its module doc is written, and what payroll then reads instead of computing time itself. The rules come from the Attendance Specification v0.4; this note decides which of them v1 builds, how they sit on Odoo's own attendance, and what moves out of `l10n_vn_payroll`.

**Based on:**
- Attendance Specification v0.4 (the business rules), Payroll Technical Design v0.4 §10 and §14, `docs/modules/l10n_vn_payroll.md` D20–D25;
- the Odoo code the instance runs, read 2026-11-08: `hr_attendance`, `hr`, `hr_contract`, `resource`;
- the test copy's attendance for May 2026 (§9).

**Status labels:** **Proposed** (designed here, Peter decides), **Agreed** (confirmed by Peter, with date).

---

## 0. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| AD-01 | **A separate module, `hr_attendance_day`, classifies time; payroll prices it.** Each employee-day becomes one stored record of facts about time. Payroll reads those records and keeps every rule about who pays and how much (§2). | Direction agreed 2026-11-08; the details here Proposed |
| AD-02 | **Odoo decides how much time; the module decides what kind.** Expected hours, worked hours, the day's overtime, its approval and both tolerances come from `hr_attendance` as it computes them. The module adds what Odoo lacks: day type, night hours, the split of overtime by category, late arrivals, early leaves, absences (§3, §5). | Proposed |
| AD-03 | **The grace period and the 0.8 h OT minimum become Odoo's two tolerance settings.** The grace period is *Tolerance Time In Favor Of Employee*: 5 minutes, a placeholder (Attendance Spec OPEN-04). The 0.8 h minimum is *Tolerance Time In Favor Of Company*: 48 minutes. Payroll's `vn.policy.ot_min_hours_day` is retired (§6). | Proposed |
| AD-04 | **Late minutes and overtime net out within a day, as Odoo computes it.** A worker 10 minutes late who stays an hour has 50 minutes of overtime and a full normal day. Today's payroll pays the same way (§5.3). | Proposed |
| AD-05 | **No OT time frame in v1.** Early check-ins are trimmed to the shift start before they reach Odoo (§9), and a frame inside Odoo would give a second overtime figure that disagrees with Odoo's own (§7). | Proposed |
| AD-06 | **One setting of its own: the night window** (22:00–06:00 by default), on the company (§6). | Proposed |
| AD-07 | **Computed on demand, never by patching Odoo:** a nightly job for recent days, a *Recompute* action, and payroll's summary build. Day records are read-only; corrections are made on the attendance records (§4.3). | Proposed |
| AD-08 | **`l10n_vn_payroll` depends on `hr_attendance_day`.** This reverses Payroll Technical Design §1 ("no dependency on the attendance module") and divergence 7. Payroll reads `hr.attendance` today without declaring `hr_attendance`, so the dependency also closes that gap (§8). | Proposed |
| AD-09 | **The attendance mode moves to the attendance module.** *Present unless on leave* is a rule about time. Payroll's `l10n_vn_attendance_mode` exists but nothing reads it today (§8.3). | Proposed |
| AD-10 | **Legal limits stay in payroll.** The daily OT limit, the night-OT factor after daytime OT, and the monthly and yearly counters are law and pay. Payroll derives them from the day records (§8.2). | Proposed |

---

## 1. Scope of v1

v1 is the daily classification. The Specification's other parts wait until they are needed, or stay with Odoo:

| Specification | v1 | Where it lives |
| --- | --- | --- |
| §5.1 normal minutes, lateness, rest day and holiday work, night flag | Yes | `hr_attendance_day` |
| §5.2 exception-driven mode (office, management) | Yes | `hr_attendance_day` (AD-09) |
| §5.3 paid breaks for women | No change | Payroll, as built (D25): monthly credits over the month's short days |
| §5.4 off-site work registration | No | An attendance record entered by hand covers it today |
| §3 shift templates and rosters | No | Odoo's working calendars on contracts; see the quilting finding (§9) |
| §4 scan capture and pairing | No | The fingerprint → pandas → `hr.attendance` pipeline, outside Odoo |
| §7.1–7.2 OT requests with approved windows | No | Odoo's overtime approval (*Validated Extra Hours*); both companies use *no validation* today |
| §7.3 counters and limits | Facts only | Day records carry the hours; payroll applies the limits (AD-10) |
| §8 exception queue, day status codes, corrections workflow | No | Lists and filters on the day records show the exceptions; corrections are made on the attendance record |

---

## 2. The split

| `hr_attendance_day`: what time it was, per employee per day | `l10n_vn_payroll`: who pays and how much, per month |
| --- | --- |
| Scheduled hours (the calendar) and expected hours (less leave and public holidays) | The month's pieces and segments, cut at contract and pay-line dates |
| Day type: workday, rest day, public holiday | Leave classified by who pays: company, SI fund, unpaid |
| Normal hours, normal night hours | Paid breaks for women |
| Overtime hours, and the part of them at night | OT categories and their factors: `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL` |
| Unapproved extra time | The daily, monthly and yearly OT limits; PIT on hours above them |
| Late and early-leave minutes, beyond-grace flags | The attendance bonus condition; discipline is HR's |
| Absence: scheduled, not on leave, no attendance | Unexcused absences counted in the month |
| Exception-driven mode | Pay groups, which default the mode |

Payroll stops reading `hr.attendance` and public holidays itself; it reads day records and keeps reading leave to classify it by payer.

The IE module reads the same day records: its attended minutes (A) are normal plus overtime hours. This replaces the IE proposal P-01, which is already obsolete.

---

## 3. What Odoo already does, and how the module uses it

| Odoo (CE 18) | Source | Used as |
| --- | --- | --- |
| Expected work intervals per day, from **each contract's calendar**, less approved leave and public holidays, lunch excluded | `hr.employee._get_expected_attendances()` (`hr_contract/models/hr_employee.py:247`) | Expected hours, and the scheduled time a day's presence is measured against |
| Calendar periods per contract | `hr.employee._get_calendar_periods()` (`hr/models/hr_employee_base.py:297`, overridden by `hr_contract`) | Scheduled hours before leave |
| Lunch intervals | `hr.employee._employee_attendance_intervals(lunch=True)` | Time that is neither normal nor overtime |
| Worked hours per attendance, lunch excluded | `hr.attendance.worked_hours` (`hr_attendance/models/hr_attendance.py:210`) | Worked hours |
| The day's overtime: worked − expected, with both tolerances, negative when short beyond the employee tolerance | `hr.attendance.overtime.duration`, written by `_update_overtime` (`hr_attendance.py:320`) | How much overtime, and how much normal time is missing |
| Overtime approval | `hr.attendance.validated_overtime_hours`; company setting `attendance_overtime_validation` | Approved overtime |
| Tolerance in favour of employee | `res.company.overtime_employee_threshold`: a short day within it counts as complete (`hr_attendance.py:470`, `:532-546`) | The grace period (AD-03) |
| Tolerance in favour of company | `res.company.overtime_company_threshold`: the day's overtime counts only above it, then in full (`hr_attendance.py:465`) | The OT minimum (AD-03) |

The module reads these values, calls the four methods above, and reads the stored fields. It overrides nothing.

---

## 4. The daily record: `hr.attendance.day`

### 4.1 Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `employee_id`, `date`, `company_id` | | One record per employee and date; unique |
| `attendance_mode` | Selection | `scan` or `exception`, the employee's on the date (AD-09) |
| `day_type` | Selection | `workday` (scheduled hours), `rest` (none), `holiday` (a public holiday covers the date) |
| `scheduled_hours` | Float | The calendar's hours that day, before leave |
| `expected_hours` | Float | Scheduled hours less leave and public holidays (Odoo's expected intervals) |
| `worked_hours` | Float | Sum of the day's attendances' worked hours |
| `normal_hours` | Float | Paid normal time (§5.3) |
| `normal_night_hours` | Float | The part of normal time inside the night window |
| `overtime_hours` | Float | Approved overtime (§5.4) |
| `overtime_night_hours` | Float | The part of overtime inside the night window |
| `unapproved_hours` | Float | Extra time Odoo counted but approval did not cover |
| `late_minutes`, `early_leave_minutes` | Integer | First check-in after the first expected start; last check-out before the last expected end |
| `late`, `early_leave` | Boolean | Beyond the grace period |
| `absent` | Boolean | Scan mode, expected hours > 0, no attendance |
| `incomplete` | Boolean | An attendance without check-out: overtime not computed yet (Odoo does the same) |
| `first_check_in`, `last_check_out` | Datetime | For lists and exports |
| `attendance_ids` | Many2many `hr.attendance` | The attendances the day was computed from |

A record exists for every date with scheduled hours or an attendance, for every employee computed.

### 4.2 The work day

An attendance belongs to the local date of its check-in, as in Odoo's own overtime (`_get_day_start_and_day`). A calendar shift that crosses midnight is two calendar lines (22:00–24:00 and 00:00–06:00 the next weekday); the line starting at 00:00 joins the day before when it continues a line ending at 24:00 (Attendance Spec §2, FLAG-TECH-04). No calendar on the instance crosses midnight today.

### 4.3 When it is computed

- `hr.attendance.day._recompute(employees, date_from, date_to)` is the only writer. It rebuilds the records in the range from Odoo's data.
- A nightly scheduled job recomputes the last 7 days for every employee with a contract.
- A *Recompute* action on the list recomputes the selected days.
- Payroll's *Build Summaries* recomputes the month before reading it, so a payslip never reads a stale day.
- Records are read-only. A forgotten scan or a wrong time is corrected on the attendance record, then the day is recomputed.
- A closed payroll month keeps its own figures (its summary is frozen at close). A later recompute of those days changes the day records, not the payslip.

---

## 5. The rules

Notation for one employee and day: *S* the expected intervals, *L* the lunch intervals, *P* the attendances, *D* Odoo's overtime duration for the day (negative when short), *V* the sum of the attendances' validated overtime, *N* the night window.

### 5.1 Day type, scheduled and expected hours

- `holiday` when a public holiday (a calendar leave with no employee) covers the date; else `rest` when the calendar schedules no hours; else `workday`.
- `scheduled_hours` from the calendar of the contract in force; `expected_hours` = the length of *S*.

### 5.2 Exception-driven mode

`normal_hours` = `expected_hours`, whatever the scans say; `late`, `early_leave` and `absent` are not set. Overtime follows §5.4, as for everyone (Attendance Spec §5.2).

### 5.3 Normal hours (scan mode)

- No attendance: `normal_hours` = 0; `absent` when `expected_hours` > 0.
- Otherwise `normal_hours` = max(0, `expected_hours` + min(0, *D*)).

So a short day within the grace period is complete, and a short day beyond it loses all its missing minutes (Attendance Spec §5.1 rule 2). Late minutes made up by staying later are not lost: Odoo nets them first (AD-04).

- `normal_night_hours` = the length of *P* ∩ *S* ∩ *N*.

### 5.4 Overtime and its night part

- `overtime_hours` = min(max(0, *D*), *V*). With *no validation*, *V* equals Odoo's overtime, so this is max(0, *D*).
- `unapproved_hours` = max(0, *D*) − `overtime_hours`.
- **Which hours are overtime.** The extra time *E* = *P* − *S* − *L* is laid out in time order:
  1. its first stretch makes up the missing normal time (length |*E*| − max(0, *D*));
  2. the next `overtime_hours` are overtime;
  3. the rest is unapproved.

  `overtime_night_hours` is the part of stretch 2 inside *N*.
- On a rest day or holiday *S* is empty: all presence is extra, and Odoo's *D* is all of it.

### 5.5 Late arrival and early leave (scan mode)

- `late_minutes` = the first check-in − the start of the first interval of *S*, when positive.
- `late` = `late_minutes` > the employee tolerance (the grace period).
- `early_leave_minutes` and `early_leave` are the same at the end of the day.
- A half day of leave in the morning moves the first expected start to the afternoon, so the employee is not late.

### 5.6 Worked examples (calendar 1: 07:30–11:30, 13:00–17:00; grace 5 min; company tolerance 48 min)

| Scans | *D* | Normal | Overtime | Night | Late |
| --- | --- | --- | --- | --- | --- |
| 07:30–17:30 | 0 (30 min ≤ 48) | 8 h | 0 | 0 | no |
| 07:30–18:30 | +1 h | 8 h | 1 h | 0 | no |
| 07:34–17:00 | 0 (4 min within grace) | 8 h | 0 | 0 | 4 min, not late |
| 07:45–17:00 | −15 min | 7 h 45 | 0 | 0 | 15 min, late |
| 07:45–18:15 | +1 h (1 h 15 extra − 15 min late) | 8 h | 1 h (17:15–18:15) | 0 | 15 min, late |
| Quilting on a one-shift calendar 14:00–22:00, scans 14:00–23:30 | +1 h 30 | 8 h | 1 h 30 | 1 h 30 | no |
| Sunday 07:30–11:30 | +4 h | 0 | 4 h (rest day) | 0 | – |

---

## 6. Settings

| Setting | Where | Value for the garment company |
| --- | --- | --- |
| Night window start and end | `res.company`, new: `attendance_night_start`, `attendance_night_end` (Float hours), in *Attendances → Configuration* | 22:00, 06:00 (the defaults) |
| Grace period | Odoo's *Tolerance Time In Favor Of Employee* | 5 minutes, placeholder (Attendance Spec OPEN-04) |
| OT minimum | Odoo's *Tolerance Time In Favor Of Company* | 48 minutes |
| OT approval | Odoo's *Extra Hours Validation* | *no validation*, as today |

- Odoo counts overtime above its company tolerance; payroll's rule counts it from 0.8 h. They differ only on a day with exactly 48 minutes.
- **Changing either tolerance recomputes Odoo's overtime for every attendance of the company, past months included** (`hr_attendance/models/res_company.py:70-82`). Set them at go-live, once the last month paid by the old rules is closed, and on the test copy first.
- Payslips already approved keep their figures: their summaries are frozen (§4.3).
- The day records follow at their next recompute: the job, the action or payroll's build.

---

## 7. Footprint and upgrades

- **Depends on** `hr_attendance` only, which brings `hr` and `resource`. Contract calendars are used through `_get_calendar_periods` and `_get_expected_attendances`, which `hr_contract` overrides when it is installed. No OCA module.
- **Reads:**
  - `hr.attendance`: `check_in`, `check_out`, `worked_hours`, `validated_overtime_hours`;
  - `hr.attendance.overtime`: `date`, `duration`, `adjustment`;
  - `res.company`: the two tolerances and the validation setting;
  - the four methods in §3, and `resource.calendar.leaves` for public holidays.
- **Never:** overrides an Odoo method, inherits an Odoo view, or writes to an Odoo record.
- **Adds:**
  - one model;
  - two company fields with their settings block;
  - a menu *Attendances → Reporting → Daily Time* with list, pivot and graph views;
  - one scheduled job;
  - access: attendance officers read, attendance managers recompute.
- **Within 18.0:** an image update or an OCA pull touches none of it.
- **At 19.0:**
  - check the four methods' signatures and the three models' fields;
  - check `hr.attendance.overtime` first, the part of Odoo's attendance most likely to change;
  - the module's tests build attendances by hand (late arrivals, early leaves, a night shift, a rest day, a holiday, a half day of leave, an open attendance, exception mode), so a change shows up as a failing test.
- **Why no OT frame (AD-05).** Odoo counts time before the shift as overtime. A frame that removed it would make the module's overtime differ from Odoo's. Odoo's figure is the one its screens show, and the one its *Extra Hours* time off would deduct. The pandas step already sets early check-ins to the shift start (4,254 of 4,685 first check-ins in May are exactly 07:30, §9). If scans ever reach Odoo untrimmed, the frame can be added then, as a documented departure from Odoo's figure.

---

## 8. Changes to `l10n_vn_payroll` (step 10)

### 8.1 What the summary reads

| Summary figure | Today (D20–D25) | From step 10 |
| --- | --- | --- |
| Scheduled hours per day | the contract calendar's intervals | `scheduled_hours` |
| Days worked | min(1, (worked − overtime) ÷ scheduled) | min(1, `normal_hours` ÷ `scheduled_hours`) |
| OT hours by category | validated overtime, kept from 0.8 h, by holiday / no schedule / else | from `overtime_hours`, `overtime_night_hours` and `day_type` (§8.2); no minimum of its own |
| Night hours | not computed | `normal_night_hours` → `NIGHT` |
| Unexcused absences | days with no attendance and no leave | days with `absent` |
| Late arrivals | not computed | days with `late` |
| Leave by payer, paid breaks, pieces, `month_scheduled_days` | as built | unchanged |

### 8.2 Categories and limits

Per day, with *O* = `overtime_hours`, *n* = `overtime_night_hours`, and day OT = *O* − *n*:
- **Day OT:** `WD`, `RD` or `HOL` by `day_type`.
- **Night OT:** on a workday, `NWD` when the day has no day OT and `NWD_AFTER` when it has. On a rest day `NRD`; on a holiday `NHOL`.
- **Normal night hours:** `NIGHT`.

The daily OT limit is new in payroll. Overtime above 50% of the day's scheduled hours on a workday, or beyond 12 hours of work in the day, is hours over the limit. Those hours are taxable (the PIT exemption already prorates the month's OT by hours within the limits) and raise the `ot_limit` warning. The limits become statutory parameters. The rest-day and holiday limit is to confirm (Regulation Reference).

### 8.3 The attendance mode (AD-09)

`hr.employee.l10n_vn_attendance_mode` (step 2, D16) has no reader: the summary treats everyone as scan-driven. An office employee who does not scan would therefore have no days worked. Step 10 replaces it:
- `hr_attendance_day` adds `hr.employee.attendance_mode`, readable by attendance officers;
- payroll's pay-group default writes it;
- payroll's own field is removed, its values copied by a migration.

### 8.4 Retired

- In `_l10n_vn_days`: the attendance search, the public-holiday search, and the OT category and minimum rule (D22).
- The parameter `vn.policy.ot_min_hours_day`: the strict reader stops requiring it. `l10n_vn_payroll_garment` stops creating it in a later version, and an existing one is left in place, unused.

---

## 9. What the test copy shows (May 2026, garment company)

| Finding | Figures | Consequence |
| --- | --- | --- |
| Check-ins are trimmed | 4,901 attendances, 236 employees, none open. Of 4,685 first check-ins on calendar 1: 4,254 exactly 07:30; 83 late by up to 5 min; 97 by 5–30 min; 24 later in the morning; 121 start at the afternoon; 106 before 07:30 | AD-05: no frame needed. About 200 late arrivals a month, so the grace period matters to pay |
| Most workers check out shortly after 17:00 | 3,149 of 4,685 days end between 17:00 and 17:48; 260 later | With both tolerances at 0, Odoo counts all of that as overtime today; payroll's 0.8 h rule drops it. A 48-minute company tolerance makes them agree (AD-03) |
| Approval | Both companies on *no validation*; no manual overtime adjustments; no *Extra Hours* time off | *V* equals Odoo's overtime; nothing else depends on Odoo's overtime figure |
| **The quilting calendar holds both shifts** | Calendar 13 *8 Hours 2 Shifts*: 06:00–14:00 and 14:00–22:00 every day, 16 h expected; 11 employees (Quilting); most days 06:00–14:00, some 06:00–22:00 | Odoo shows −8 h on an ordinary 8-hour day, and the built engine pays half a day (D23 measures against the calendar's hours). **This must be corrected before go-live:** one calendar per shift, on each contract |
| Night presence exists | 63 quilting attendances end after 22:00 (about 14 minutes on average), from the afternoon shift and from 06:00–22:00 double shifts | Night OT hours appear as soon as overtime runs past 22:00. A 16-hour day is 8 h of overtime: over the daily limit (§8.2) |

---

## 10. Open items

| ID | Item | Proposal |
| --- | --- | --- |
| AD-OPEN-01 | Quilting shifts: do the employees rotate between morning and afternoon, and how often? | Fixed shifts: two calendars, one per contract. Rotating: OCA `hr_employee_calendar_planning` (available in `oca/hr`, not installed); whether contract calendars follow its planning needs reading `hr_contract_employee_calendar_planning` first |
| AD-OPEN-02 | The grace period (Attendance Spec OPEN-04) | 5 minutes |
| AD-OPEN-03 | The daily limit on rest days and public holidays | 12 hours of work in the day, to confirm |
| AD-OPEN-04 | Breaks in a continuous 8-hour shift (quilting has none on its calendar), which count as working time (Attendance Spec OPEN-01) | Keep the calendar without a lunch line, so the whole shift is expected time |
| AD-OPEN-05 | Lateness for exception-driven staff (Attendance Spec OPEN-05) | Not computed in v1 |

---

## 11. Proposals to other documents

| Document | Proposal |
| --- | --- |
| Attendance Specification | v0.5 status note: v1 is `hr_attendance_day` on Odoo's attendance (this note); §7 approval windows, §3 rosters, §8 queue and §5.4 off-site registration deferred; the grace period and OT minimum are Odoo's tolerances |
| Payroll Technical Design | §1: `l10n_vn_payroll` depends on `hr_attendance_day`; §10.4 and §14: the summary reads day records; the daily OT limit; corrections to divergences 7, 10 and 11 |
| `docs/modules/l10n_vn_payroll.md` | Step 10: D20–D23 replaced, D16 moved (§8) |
| IE Technical Design | Attended minutes A from `hr.attendance.day` (normal + overtime hours); P-01 marked obsolete |

---

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-11-08 | First draft: decisions AD-01 to AD-10, scope, split, Odoo reuse, the daily record and its rules, settings, footprint, payroll step 10, test-copy findings, open items. |
