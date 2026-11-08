# Attendance Daily Time — Design Note

v0.2 (draft) · Nov 8, 2026 · @Peter · **Route A agreed**

**Supersedes:** v0.1, kept as history. v0.1 designed a full attendance module: a time engine of its own, stored daily records with screens, a scheduled job and per-calendar counting rules. Peter chose the lean route instead (Route A, 2026-11-08): Odoo decides how much time there is, a small module derives what payroll needs from it, and the counting window stays an Odoo automation rule.

**Purpose:** settle how each employee's day is classified before the module doc of `hr_attendance_day` is written:
- normal hours, overtime and its night part, days worked;
- late arrivals and absences;
- what payroll then reads instead of computing time itself.

**Based on:**
- Attendance Specification v0.4 (the business rules), Payroll Technical Design v0.4 §10 and §14, `docs/modules/l10n_vn_payroll.md` D20–D25;
- the Odoo code the instance runs, read 2026-11-08: `hr_attendance`, `hr`, `hr_contract`, `resource`;
- the test copy's attendance for May 2026, its *Normalize Attendance* server action and the salary rule `MINW` (§8).

---

## 0. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| AD-01 | **A small module, `hr_attendance_day`, derives each day's figures; payroll prices them.** It has one method that returns the figures per employee and date, plus three fields on the working calendar. No stored records, no screens, no scheduled job (§2, §4). | Agreed 2026-11-08 |
| AD-02 | **Odoo decides how much time there is.** Expected hours, worked hours, the day's overtime, its approval and both tolerances are taken from `hr_attendance` as it computes them. The module derives the rest from them: normal hours, the night part, days worked, late arrivals, absences (§3, §5). | Agreed 2026-11-08 |
| AD-03 | **The grace period and the 0.8 h OT minimum are Odoo's two tolerance settings:** *Tolerance Time In Favor Of Employee* 5 minutes and *Tolerance Time In Favor Of Company* 48 minutes. Payroll's `vn.policy.ot_min_hours_day` is retired (§6). | Agreed 2026-11-08 |
| AD-04 | **Late minutes are made up by staying later**, as payroll paid before. A worker 10 minutes late who stays an hour has a full normal day and 50 minutes of overtime. A worker 7 minutes late who stays 32 minutes has a full normal day and no overtime: Odoo's company tolerance ignores the stay as overtime, and the module counts it as making up the lateness (§5.2; amended 2026-11-08 after the May comparison). | Agreed 2026-11-08 |
| AD-05 | **The counting window is an Odoo automation rule, not module code.** The *Normalize Attendance* code runs on every new attendance, so an early check-in is moved to its shift start before Odoo computes overtime (§6). | Agreed 2026-11-08 |
| AD-06 | **Hours per paid day, on the calendar.** A calendar may say how many hours make one paid day; days worked are then normal hours ÷ that number. Quilting's 16-hour calendar uses 8, which makes `MINW`'s hidden rule ("over 12 hours means 8") explicit (§5.3). | Agreed 2026-11-08 |
| AD-07 | **Night hours with a window on the calendar** (22:00–06:00 by default). Night overtime is the overtime that falls at the end of the day, inside the window (§5.4). | Agreed 2026-11-08 |
| AD-08 | **Late arrival:** the first check-in after the first expected start, beyond the grace period. On a calendar with hours per paid day, it is measured from the nearest shift start instead. Early leave is the same at the end of the day (§5.5). | Agreed 2026-11-08 |
| AD-09 | **`l10n_vn_payroll` depends on `hr_attendance_day` and reads its method.** This reverses Payroll Technical Design §1 and divergence 7, and declares the attendance dependency payroll already needs. The attendance mode stays a payroll field (§7). | Agreed 2026-11-08 |
| AD-10 | **Legal limits stay in payroll.** It adds the daily OT limit, reported by the `ot_limit` check, and the check `long_days` for days over 12 hours. The check reports and enforces nothing; its level is configuration (§7.3). | Agreed 2026-11-08 |

---

## 1. Scope

| Specification | Route A | Where |
| --- | --- | --- |
| §5.1 normal minutes, lateness, rest day and holiday work, night flag | Yes | `hr_attendance_day` |
| §5.2 exception-driven mode | Yes | Payroll, from the method's expected hours (§7.2) |
| §5.3 paid breaks for women | Unchanged | Payroll (D25) |
| §3 shift templates and rosters | No | Odoo's working calendars on contracts, with hours per paid day where shifts combine |
| Early check-ins, a cut-off time | Yes | An Odoo automation rule (AD-05) |
| §5.4 off-site work, §7.1 OT requests, §8 exception queue and day status codes | No | An attendance record entered or corrected by hand; Odoo's overtime approval |
| §7.3 counters and limits | Facts only | Payroll applies the limits (AD-10) |
| Daily lists for HR | No | Payroll's monthly summary carries the counts. Stored daily records can be added later without changing the method |

---

## 2. The split

| `hr_attendance_day`: what time it was, per employee and date | `l10n_vn_payroll`: who pays and how much, per month |
| --- | --- |
| Day type: workday, rest day, public holiday | The month's pieces and segments |
| Scheduled and expected hours | Leave classified by who pays |
| Normal hours, normal night hours, days worked | Paid breaks for women; exception-driven mode |
| Overtime hours and their night part | OT categories and factors; the daily, monthly and yearly limits |
| Late and early-leave minutes; absence | The attendance bonus condition; unexcused absences counted |
| Worked hours | Days over 12 hours (`long_days`) |

IE can call the same method for its attended minutes (normal + overtime).

---

## 3. What Odoo provides, and how it is used

| Odoo (CE 18) | Source | Used as |
| --- | --- | --- |
| Expected work intervals from each contract's calendar, less approved leave and public holidays, lunch excluded | `hr.employee._get_expected_attendances()` (`hr_contract/models/hr_employee.py:247`) | Expected hours *S*, and the starts and ends for lateness |
| Calendar periods per contract | `hr.employee._get_calendar_periods()` (`hr/models/hr_employee_base.py:297`, overridden by `hr_contract`) | The calendar in force; scheduled hours before leave through `resource.calendar._attendance_intervals_batch()` |
| Lunch intervals | `hr.employee._employee_attendance_intervals(lunch=True)` | Time outside both normal and overtime |
| Worked hours, lunch excluded | `hr.attendance.worked_hours` | Worked hours |
| The day's overtime *D*: worked − expected, with both tolerances, negative when short beyond the employee tolerance | `hr.attendance.overtime.duration` (non-adjustment), written by `_update_overtime` (`hr_attendance.py:320`) | Normal hours and overtime |
| Overtime approval | `hr.attendance.validated_overtime_hours` | Cap on overtime |
| Public holidays | `resource.calendar.leaves` without an employee | Day type |
| Calendar lines | `resource.calendar.attendance`: `dayofweek`, `day_period`, `hour_from`, `hour_to` | Shift starts and ends on a calendar with hours per paid day (§5.5) |

The module reads these stored fields and calls these methods. It overrides no method and writes no Odoo record.

---

## 4. The module: `hr_attendance_day`

| Part | Content |
| --- | --- |
| Depends | `hr_attendance` (which brings `hr` and `resource`). Contract calendars come through the two `hr.employee` methods, which `hr_contract` overrides when it is installed |
| `hr.employee._attendance_days(date_from, date_to)` | Returns `{date: figures}` for every date with scheduled hours or an attendance (§5); batched over the employees in `self` |
| `resource.calendar` fields | `paid_day_hours` *Hours per paid day* (Float, empty = the day's scheduled hours); `night_start`, `night_end` (Float hours, default 22.0 and 6.0) |
| View | One inheritance of `resource.resource_calendar_form`: the three fields after `hours_per_day` |
| Access | None of its own: the method runs as superuser for the employees it is given; the fields follow the calendar's access |

**Figures per date:**

| Key | Meaning |
| --- | --- |
| `day_type` | `workday`, `rest` or `holiday` |
| `scheduled_hours`, `expected_hours` | Calendar hours before leave; expected hours after leave and holidays |
| `worked_hours` | Sum of the day's worked hours |
| `normal_hours`, `normal_night_hours` | §5.2, §5.4 |
| `day_hours` | The divisor of a paid day: `paid_day_hours`, else `scheduled_hours` |
| `days_worked` | `normal_hours` ÷ `day_hours` |
| `overtime_hours`, `overtime_night_hours`, `unapproved_hours` | §5.2, §5.4 |
| `late_minutes`, `late`, `early_leave_minutes`, `early_leave` | §5.5 |
| `absent` | Expected hours > 0 and no attendance |
| `incomplete` | An attendance without check-out (Odoo then computes no overtime for the day) |

An attendance belongs to the local date of its check-in, as in Odoo's overtime. Calendars whose shifts cross midnight are not supported: Odoo's overtime reads expected hours only up to midnight (`hr_attendance/models/hr_attendance.py:394-395`), so its figure for such a shift is wrong. No calendar on the instance crosses midnight; presence running past midnight is handled.

---

## 5. The rules

Notation for one employee and date:
- *S* — the expected intervals;
- *L* — the lunch intervals;
- *P* — the attendances;
- *D* — Odoo's overtime for the date (negative when short);
- *V* — the sum of the attendances' validated overtime, each counted from 0;
- *N* — the night window around the date.

### 5.1 Day type, scheduled and expected hours

- `holiday` when a public holiday covers the date; else `rest` when the calendar schedules no hours; else `workday`.
- `scheduled_hours` comes from the calendar in force; `expected_hours` = |*S*|.

### 5.2 Normal hours and overtime

| Figure | Rule |
| --- | --- |
| `normal_hours` | No attendance → 0. Otherwise max(0, min(`expected_hours`, max(`expected_hours` + min(0, *D*), `worked_hours` − max(0, *D*)))) |
| `overtime_hours` | min(max(0, *D*), *V*). With Odoo's *no validation*, *V* equals the overtime, so this is max(0, *D*) |
| `unapproved_hours` | max(0, *D*) − `overtime_hours` |

- A short day within the grace period is complete; a short day beyond it loses all its missing minutes (Attendance Spec §5.1 rule 2).
- Minutes made up by staying later count (AD-04): Odoo nets them when the stay is above its company tolerance; when it is within, the time present beyond the overtime (`worked_hours` − max(0, *D*)) makes them up.
- On a rest day or holiday *S* is empty, so all worked time is overtime.

### 5.3 Days worked

`days_worked` = `normal_hours` ÷ `day_hours`.
- On an ordinary calendar this is at most 1: normal hours never exceed expected hours.
- On quilting's calendar (16 scheduled hours, `paid_day_hours` 8) it is 1 for one shift and 2 for both.

### 5.4 Night hours

- `normal_night_hours` = |*P* ∩ *S* ∩ *N*|.
- `overtime_night_hours` = min(`overtime_hours`, |(*P* − *S* − *L*) ∩ *N*|).

Overtime is taken to be the end of the day: true for staying late, and for work on a rest day or holiday, where all time is overtime.

### 5.5 Late arrival and early leave

- `late_minutes` = the first check-in − the reference start, when positive. The reference start is the start of *S*'s first interval. On a calendar with `paid_day_hours`, it is the start of the calendar line (not lunch) for that weekday nearest to the check-in, as *Normalize Attendance* chooses it: Odoo merges touching intervals, so quilting's 06:00–14:00 and 14:00–22:00 come back from *S* as one 06:00–22:00 interval (`resource/models/utils.py:117-131`).
- `late` = `late_minutes` > the employee tolerance.
- `early_leave_minutes` and `early_leave` are the same with the last check-out and the matching end.
- A half day of leave in the morning moves the first expected start to the afternoon.

### 5.6 Worked examples

Calendar 1 (07:30–11:30, 13:00–17:00), grace 5 minutes, company tolerance 48 minutes:

| Scans | *D* | Normal | Days | Overtime | Night | Late |
| --- | --- | --- | --- | --- | --- | --- |
| 07:30–17:30 | 0 (30 min ≤ 48) | 8 h | 1 | 0 | 0 | no |
| 07:30–18:00 | +1 h | 8 h | 1 | 1 h | 0 | no |
| 07:34–17:00 | 0 (within grace) | 8 h | 1 | 0 | 0 | 4 min, not late |
| 07:45–17:00 | −15 min | 7 h 45 | 0.97 | 0 | 0 | 15 min, late |
| 07:45–18:15 | +1 h (1 h 15 − 15 min) | 8 h | 1 | 1 h | 0 | 15 min, late |
| 13:00–17:00, no leave | −4 h | 4 h | 0.5 | 0 | 0 | 5 h 30, late |
| Sunday 07:30–11:30 | +4 h | 0 | 0 | 4 h, rest day | 0 | – |

Quilting, calendar 13 (06:00–14:00, 14:00–22:00, 16 h), `paid_day_hours` 8:

| Scans | *D* | Normal | Days | Overtime | Night | Late |
| --- | --- | --- | --- | --- | --- | --- |
| 06:00–14:00 | −8 h | 8 h | 1 | 0 | 0 | no |
| 14:00–22:00 | −8 h | 8 h | 1 | 0 | 0 | no (nearest start 14:00) |
| 06:00–22:00 | 0 | 16 h | 2 | 0 | 0 | no |
| 06:00–22:30 | 0 (30 min ≤ 48) | 16 h | 2 | 0 | 0 | no |
| 06:00–23:30 | +1 h 30 | 16 h | 2 | 1 h 30 | 1 h 30 | no |

The same days under `MINW` give the same days worked: (worked − positive overtime) ÷ 8.

---

## 6. Odoo configuration (no module code)

| Setting | Where | Value |
| --- | --- | --- |
| Grace period | *Attendances → Configuration*: Tolerance Time In Favor Of Employee | 5 minutes |
| OT minimum | Tolerance Time In Favor Of Company | 48 minutes |
| OT approval | Extra Hours Validation | *no validation*, as today |
| Counting window | An automation rule on `hr.attendance`, trigger *On creation*, action *Execute Code* with the *Normalize Attendance* code | Early check-ins moved to the nearest shift start, as today |
| Quilting | Calendar 13: Hours per paid day 8 | 8 |

- Odoo counts overtime above its company tolerance, while payroll's old rule counted it from 0.8 h. They differ only on a day with exactly 48 minutes.
- **Changing either tolerance recomputes Odoo's overtime for every attendance of the company, past months included** (`hr_attendance/models/res_company.py:70-82`). Set them on the test copy first, and on production at go-live, once the last month paid by the old rules is closed. Approved payslips keep their figures: their summaries are frozen.
- The automation rule rewrites `check_in`, as the server action does today. Odoo tracks the field, so the original time stays in the record's history.
- A hard cut-off (for example nothing counted after 22:00) can be added to the same code later, by trimming check-outs. Quilting does not need it: up to 48 minutes past 22:00 is absorbed by the company tolerance.

---

## 7. Changes to `l10n_vn_payroll` (step 10)

### 7.1 What the summary reads

| Summary figure | Today (D20–D25) | From step 10 |
| --- | --- | --- |
| Days worked | min(1, (worked − overtime) ÷ scheduled) per day | `days_worked` per day |
| Scheduled hours, for leave fractions | the contract calendar's intervals | `scheduled_hours` |
| OT by category | validated overtime kept from 0.8 h, by holiday / no schedule / else | from `overtime_hours`, `overtime_night_hours` and `day_type` (§7.3); no minimum of its own |
| Night hours | not computed | `normal_night_hours` → `NIGHT` |
| Unexcused absences | days with no attendance and no leave | days with `absent` |
| Late arrivals | not computed | days with `late` |
| Days over 12 hours | – | days with `worked_hours` > `vn.ot.limit.day_total` |
| Leave by payer, paid breaks, pieces, `month_scheduled_days` | as built | unchanged |

Leave fractions keep dividing leave hours by `scheduled_hours`, so a day of annual leave on quilting's 16-hour calendar is one day.

### 7.2 Exception-driven mode

An employee whose `l10n_vn_attendance_mode` is `exception`: `days_worked` = `expected_hours` ÷ `day_hours` on every date, whatever the scans say. Late arrivals and absences are not counted. Overtime comes from scans as for everyone. This is the field's first reader; it stays on the employee as built (D16).

### 7.3 Categories and limits

| Per day | Category |
| --- | --- |
| Day OT (`overtime_hours` − `overtime_night_hours`) | `WD`, `RD` or `HOL` by `day_type` |
| Night OT on a workday | `NWD` when the day has no day OT, `NWD_AFTER` when it has |
| Night OT on a rest day / holiday | `NRD` / `NHOL` |
| `normal_night_hours` | `NIGHT` |

New statutory parameters, created per Vietnamese company like the others:

| Code | Value | Use |
| --- | --- | --- |
| `vn.ot.limit.day_share` | 0.5 | OT above this share of the day's scheduled hours on a workday is over the daily limit |
| `vn.ot.limit.day_total` | 12 | Hours of work above this in a day: over the daily limit on rest days and holidays, and the `long_days` check |

- **The daily limit is a labour rule only.** The summary gains `ot_over_daily_hours`, which the `ot_limit` check reports. The PIT exemption keeps the monthly and yearly limits (D54; Peter, 2026-11-08).
- **The `long_days` check** is a legal check, default *warning*. Its finding is the number of days over 12 hours, and the summary gains `long_days`. Its level is a parameter like every check's. For the garment company it is *note* (proposed for `l10n_vn_payroll_garment`), since quilting's double shifts are the agreed arrangement.
- The OT categories and factors are the engine's, as built.

### 7.4 Retired

- In `_l10n_vn_days`: the `hr.attendance` search, the public-holiday search and the OT minimum and category rule (D22, D23).
- The parameter `vn.policy.ot_min_hours_day`: no longer read. `l10n_vn_payroll_garment` stops creating it in a later version; an existing one stays, unused.

---

## 8. What the test copy shows (May 2026, garment company)

| Finding | Figures | Consequence |
| --- | --- | --- |
| Check-ins are normalized in Odoo, by hand | The server action *Normalize Attendance* (id 1045) moves a check-in earlier than the nearest shift start to that start. Of 4,685 first check-ins on calendar 1: 4,254 exactly 07:30; 83 late by up to 5 minutes; 97 by 5–30 minutes; 24 later in the morning; 121 start at the afternoon; 106 before 07:30 | AD-05: the same code as an automation rule, so it no longer depends on someone running it. About 200 late arrivals a month, so the grace period matters to pay |
| Most workers check out shortly after 17:00 | 3,149 of 4,685 days end between 17:00 and 17:48 | With both tolerances at 0, Odoo counts that time as overtime; payroll's 0.8 h rule drops it. A 48-minute company tolerance makes them agree (AD-03) |
| Approval | *No validation* in both companies; no manual overtime adjustments; no *Extra Hours* time off | *V* equals Odoo's overtime; nothing else reads Odoo's overtime figure |
| The quilting calendar is deliberate | Calendar 13: both shifts, 16 hours, 11 employees on rotating shifts, sometimes both. No overtime is paid up to 16 hours; output bonuses are paid instead (Peter, 2026-11-08). `MINW` treats a calendar over 12 hours as 8, so a 16-hour day is 2 days | AD-06: `paid_day_hours` 8 gives the same days worked |
| Presence after 22:00 | 63 quilting attendances end after 22:00, about 14 minutes past on average | Absorbed by the company tolerance; night overtime appears only beyond 48 minutes |

**Legal note.** The Labor Code allows 8 normal hours a day (10 when hours are set by week). Overtime is at most 50% of normal hours and 12 hours of work in the day in total, paid at 150% or more (Art. 98, 105, 107). A 16-hour day paid as two normal days, with bonuses instead of an overtime premium, sits outside those limits. The modules record the arrangement and report it through `long_days`; they do not enforce pay policy. This is an analysis of the rules for system design, not legal advice.

---

## 9. Footprint and upgrades

- **Adds:** one method on `hr.employee`, three fields on `resource.calendar`, and one view inheritance of the calendar form. No model, data, scheduled job, menu or security file.
- **Reads:**
  - `hr.attendance`: `check_in`, `check_out`, `worked_hours`, `validated_overtime_hours`;
  - `hr.attendance.overtime`: `employee_id`, `date`, `duration`, `adjustment`;
  - `res.company.overtime_employee_threshold`;
  - `resource.calendar.leaves` and `resource.calendar.attendance`;
  - the four calendar methods in §3.
- **Never:** overrides a method or writes to an Odoo record.
- **Within 18.0:** image updates and OCA pulls do not touch it.
- **At 19.0:** check the four methods and the fields above, `hr.attendance.overtime` first, as the part of Odoo's attendance most likely to change. The tests build attendances by hand for each case in §5.6, plus a public holiday, a half day of leave, an open attendance and two contracts in one month, so a change shows up as a failing test.
- **Later, if wanted:** stored daily records with list and pivot views for HR can be added on top of the method without changing it or payroll.

---

## 10. Open items

| ID | Item | Proposal |
| --- | --- | --- |
| AD-OPEN-01 | The grace period (Attendance Spec OPEN-04) | **Decided:** 5 minutes (Peter, 2026-11-08) |
| AD-OPEN-02 | The daily limit on rest days and public holidays | **Decided:** 12 hours of work in the day (Peter, 2026-11-08) |
| AD-OPEN-03 | Should the automation rule also run when a check-in is edited, not only on creation? | **Decided:** creation only; an edit is a deliberate correction (Peter, 2026-11-08) |
| AD-OPEN-04 | Lateness for exception-driven staff (Attendance Spec OPEN-05) | **Decided:** not counted (Peter, 2026-11-08) |

---

## 11. Proposals to other documents

| Document | Proposal |
| --- | --- |
| Attendance Specification | v0.5 status note: Route A (this note). §3 rosters, §5.4 off-site registration, §7 approval windows and §8 queue deferred. The grace period and OT minimum are Odoo's tolerances; early check-ins are moved by an automation rule; hours per paid day for combined shifts |
| Payroll Technical Design | §1: `l10n_vn_payroll` depends on `hr_attendance_day`. §10.4 and §14: the summary reads the method; the daily limit; `long_days`. Corrections to divergences 7, 10 and 11 |
| Vietnam Payroll Regulation Reference | The OT exemption covers the whole OT payment within the monthly and yearly limits; the daily limits (50% of normal hours, 12 hours of work) are labour rules only (Peter, 2026-11-07 and 2026-11-08); `vn.ot.limit.day_share` and `vn.ot.limit.day_total` |
| `docs/modules/l10n_vn_payroll.md` | Step 10: D20, D22, D23 replaced; D16 gets its reader |
| `docs/modules/l10n_vn_payroll_garment.md` | A later step: `vn.check.long_days` = *note*; `vn.policy.ot_min_hours_day` no longer created |
| IE Technical Design | Attended minutes from `_attendance_days()` (normal + overtime hours); P-01 marked obsolete |

---

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-11-08 | First draft: a full attendance module with stored daily records, decisions AD-01 to AD-10. |
| 0.2 | 2026-11-08 | Route A (Peter, 2026-11-08). The module is one method and three calendar fields, with no stored records. Odoo's overtime decides how much time there is. The counting window is an automation rule running the *Normalize Attendance* code. Hours per paid day for combined shifts (quilting), night window on the calendar, lateness from the nearest shift start on such calendars. The attendance mode stays in payroll. New: the daily OT limit and the `long_days` check. Quilting understood as deliberate (§8); the legal note added. |
