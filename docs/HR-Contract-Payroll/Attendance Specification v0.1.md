# Attendance Specification

Oct 29, 2026 · @Peter

Attendance is the single source of time for the company: it turns biometric scans, shifts, leave and approved overtime into closed daily records that payroll pays from and the IE module measures against. This spec holds the business rules; device integration and data models are flagged for technical design.

**Consumers**

- **Payroll** (Pay Policy Draft): paid days, OT and night hours by category, leave, late arrivals and absences.
- **IE module** (IE Business Logic Spec v0.6, DEC-18): attended minutes (A) per day by time category, the master clock for NAM.

**Conventions** (same as the IE spec)

- `[P]`: configurable parameter with an effective date; values are placeholders.
- `[OPEN-n]`: undecided item (§10). `FLAG-TECH-n`: technical concern for implementation (§10).
- Minutes are the working unit. Time is never rounded in the employee's disfavour.

## 1. Principles and legal limits

One set of closed daily records serves both payroll and IE, so pay and efficiency can never disagree about who worked when.

1. **One clock.** Payroll and IE read the same attendance records; neither keeps its own time.
2. **Two modes, one record shape.** Workers and production support are *scan-driven*: scans decide time worked. Office and management are *exception-driven*: present unless leave is registered (Pay Policy §5).
3. **Scheduled time is paid; extra time needs approval.** Arriving early or leaving late earns nothing unless covered by an approved OT request.
4. **Corrections are recorded, never silent.** Every change to a scan or day status keeps who, when and why.
5. **Monthly close.** Payroll and IE use only closed periods; a closed period is corrected in the next one.

**Legal limits the rules must respect** (Labor Code 2019)

| Rule | Limit | Article |
| --- | --- | --- |
| Normal hours | 8 h a day, 48 h a week (10 h a day if hours are set by week) | 105 |
| Night work | 22:00 to 06:00 | 106 |
| Break during the shift | At least 30 continuous minutes for 6 h or more; 45 minutes at night | 109 |
| Weekly rest | At least 24 consecutive hours a week | 111 |
| Overtime | 50% of normal daily hours (12 h total a day), 40 h a month, 300 h a year for garment | 107; Decree 145 Art. 60–61 |

Where work runs as continuous shifts of 6 hours or more, the break counts as working time. The IE spec assumes an unpaid lunch on day shifts; any night or continuous shift needs this checked `[OPEN-01]`.

## 2. Core definitions

| Term | Definition |
| --- | --- |
| **Shift** | A template: start, end, unpaid break(s), and whether it crosses midnight. E.g. day shift 07:00–16:00 with an unpaid 11:00–12:00 lunch = 480 scheduled minutes. |
| **Roster** | The shift assigned to an employee for a given day. Rest days and holidays have no shift. |
| **Scan** | One check-in or check-out event: employee, device, server timestamp. |
| **Scan pair** | A check-in matched to the following check-out on the same work day. |
| **Scheduled minutes** | Shift length minus unpaid breaks. |
| **Attended minutes (A)** | Paid time present: scan pairs clipped to the scheduled shift plus approved OT, minus unpaid breaks. The IE module's A. |
| **Time category** | Normal · OT workday · OT rest day · OT holiday · Night (normal or OT). Every attended minute has exactly one category, plus the night flag. |
| **Late / early-out minutes** | Scheduled minutes not attended at the start or end of the shift. |
| **Day status** | One code per employee per day (§8.1): worked, partial, a leave type, unexcused absence, rest day, holiday. |
| **Work day** | The calendar date the shift starts on. A night shift crossing midnight belongs to its start date. |

## 3. Shifts, calendar and rosters

Every employee has a roster for every day, so the system always knows what was expected before it looks at scans.

**Shift templates** `[P]`

- Fields: code, start, end, unpaid breaks, crosses midnight, early check-in window, late check-out window.
- Starting set: Day shift 07:00–16:00 with lunch 11:00–12:00; Office 07:30–16:30 with lunch 11:30–12:30 `[OPEN-02]`.

**Work calendar**

- Weekly rest day `[P Sunday]`.
- Public holidays per year under Art. 112, including Tet days as announced. When a holiday falls on a rest day, the compensatory day off is entered as a holiday.
- Company days off and swapped working days (common around Tet), each recorded as a calendar exception.

**Rosters**

- Default roster from the employee's team or line: a line's workers share its shift.
- Changes per day or period by the supervisor, with the reason recorded.
- A roster cannot be changed for a closed period.

## 4. Scan capture and pairing

Scans come from biometric devices today; the rules here don't depend on the device, so a better capture method later only changes the import.

**Capture**

- Each scan stores employee, device, timestamp and the time it was received. `FLAG-TECH-01`
- Duplicate scans by the same employee within `[P 2 min]` are merged into one.
- A device that was offline uploads its stored scans with their original timestamps; late uploads are accepted until the period closes.

**Pairing**

1. Scans are assigned to the work day of the shift they fall in, including the early and late windows.
2. The first scan is check-in and the last is check-out. Scans in between are kept but ignored for time, unless the employee leaves and returns during the shift `[OPEN-03]`.
3. A day with exactly one scan, or with scans but no matching roster, becomes an **exception** (§8.2). Missing scans are never filled in automatically.

**What scans are not used for**

- IE bundle scans are production data, not attendance. They never create or correct attended time (IE DEC-18).

## 5. Computing attended time

Attended time is the overlap of the scan pair with the scheduled shift, plus its overlap with approved OT, minus unpaid breaks; each minute then takes one time category.

### 5.1 Scan-driven mode (workers, production support)

1. **Normal minutes** = scan pair ∩ scheduled shift − unpaid breaks.
2. **Lateness:** late minutes up to `[P 5]` are treated as on time and paid; beyond that, the late minutes are unpaid and counted as one late arrival `[OPEN-04]`. Early leaving works the same way.
3. **OT minutes** = scan pair ∩ approved OT windows (§7). Time outside the shift with no approval is not paid.
4. **On a rest day or holiday** every attended minute inside an approved window is OT rest day or OT holiday; there are no normal minutes.
5. **Night flag** on every minute between 22:00 and 06:00.
6. **A** = normal minutes + OT minutes.

**Example** · day shift 07:00–16:00, lunch 11:00–12:00, OT approved 16:00–18:30. Scans 07:04 and 18:35.

| Part | Calculation | Minutes | Category |
| --- | --- | --- | --- |
| Normal | 07:04–16:00 less lunch; 4 min late within grace | 480 | Normal |
| OT | 16:00–18:30 (approval ends 18:30; 18:30–18:35 unpaid) | 150 | OT workday |
| Attended minutes (A) |  | 630 |  |

### 5.2 Exception-driven mode (office, management)

- **Normal minutes** = scheduled minutes on every working day without registered leave. Scans don't change pay.
- Scans are still required. Late arrivals and missing scans are reported to the manager for discipline, not deducted `[OPEN-05]`.
- **OT** follows §5.1 step 3: approved and scanned, the same as workers.

Each employee's mode is a field on the employee, defaulted from their group (Pay Policy §1).

## 6. Leave and absence

Every absence is either a registered leave type or an unexcused absence; the type decides who pays and whether the day counts as paid.

| Day status | Basis | Paid by | Paid day | Attendance bonus |
| --- | --- | --- | --- | --- |
| Annual leave | `[P 12]` days a year, +1 day per 5 years of service (Art. 113–114) | Company | Yes | Kept |
| Public holiday | Calendar (Art. 112) | Company | Yes | Kept |
| Own marriage | 3 days (Art. 115) | Company | Yes | Kept |
| Child's marriage | 1 day | Company | Yes | Kept |
| Death of parent, spouse's parent, spouse or child | 3 days | Company | Yes | Kept |
| Sick leave | With medical certificate | SI fund | No | Kept |
| Maternity and related leave | Per SI Law | SI fund | No | Kept |
| Work accident treatment | Per OSH Law | Company | Yes | Kept |
| Unpaid leave | Approved request | – | No | `[OPEN-06]` |
| Unexcused absence | No approved request | – | No | Forfeited |

- **Registration:** the employee or supervisor files the request; the manager approves. Leave can be registered after the fact until the period closes.
- **Annual leave balance:** accrues monthly; employees with under 12 months' service get a proportional amount. Carry-over to the next year `[OPEN-07]`. Untaken days are paid on leaving (Pay Policy §9).
- **Half days** are allowed for annual and unpaid leave.
- **For IE:** a leave day has no attended minutes (A = 0), so it has no effect on efficiency.

## 7. Overtime

OT is paid only for time that was approved before it was worked and that the employee actually attended, and the system warns before any hour limit is reached.

### 7.1 OT request

- Fields: employees (one or a whole line), date, start and end, reason, requester, approver.
- Raised by the supervisor before the OT starts; approved by `[P production manager]`.
- **Employee agreement** is recorded per employee: listed employees confirm, or decline and are removed. The record is the written consent the law requires `[OPEN-08]`.
- Requests after the fact are allowed only for emergencies, with a reason, before the period closes.

### 7.2 Matching

- Paid OT minutes = attended time ∩ the approved window (§5.1).
- Approved but not attended: unpaid, and reported to the supervisor.
- Attended outside any window: unpaid, and reported as unapproved presence.

### 7.3 Hour counters and alerts

The system keeps each employee's OT hours for the day, month and calendar year, and checks every new request against them.

| Check | Limit `[P]` | Action |
| --- | --- | --- |
| Daily total | 12 h (normal + OT) | Request blocked |
| Monthly OT | 40 h | Warning at 32 h; request above 40 h needs director approval and is flagged |
| Yearly OT | 300 h | Warning at 250 h |
| Yearly OT above 200 h | First time in the year | Reminder to notify the provincial labour authority within 15 days |
| Weekly rest | 24 consecutive hours | Warning if a request removes the week's rest |

OT above the legal limits is still paid at the statutory rate; payroll taxes the excess (Pay Policy §6).

## 8. Exceptions, corrections and monthly close

Every employee-day ends with one confirmed status, and a period closes only when no exceptions are left open.

### 8.1 Day status codes

`WORK` worked · `PART` worked part of the shift · `AL` annual leave · `PH` public holiday · `PL` paid personal leave · `SICK` sick leave · `MAT` maternity · `ACC` work accident · `UL` unpaid leave · `ABS` unexcused absence · `REST` rest day · `OFF` company day off.

### 8.2 Exception queue

Raised automatically and cleared by the supervisor:

- one scan only, or scans with no roster;
- rostered day with no scans and no leave (proposed `ABS`, to be confirmed);
- attended OT without approval, or approved OT not attended;
- late arrival or early leave beyond the grace period;
- OT counter warnings (§7.3).

### 8.3 Corrections

- A supervisor can add a missing scan, change a day status or attach leave, with a reason and evidence where available.
- The original scan is never edited or deleted; corrections are separate records with who, when and why.
- Corrections by the same person to their own attendance are not allowed.

### 8.4 Monthly close `[P]`

1. Day 1–3 of the next month: supervisors clear exceptions; IE clears its own data-quality exceptions.
2. Day 3: HR closes attendance for the month.
3. Day 4: IE closes the period and publishes incentive units.
4. Day 4–7: payroll runs, is reviewed and approved.
5. Day 10: payday.

After close, a late correction goes into the next month as an adjustment for the period it belongs to.

## 9. Outputs

Both consumers read the same closed daily records; payroll takes monthly totals, IE takes minutes per day.

| Output | Payroll (per employee, per month) | IE (per operator, per day) |
| --- | --- | --- |
| Days | Standard days, paid days, unpaid days | – |
| Leave | Days by leave type | Leave days (A = 0) |
| Attended minutes | – | A by time category |
| OT | Hours by category: workday, rest day, holiday | Included in A by category |
| Night | Normal night hours and OT night hours | Night flag on A |
| Discipline | Late arrivals, early leaves, unexcused absences | – |
| Counters | OT hours month to date and year to date; hours over the legal limits | – |

- Provisional daily values are available to IE before close for real-time monitoring (IE §13.2); only closed values feed pay.
- Paid days for exception-driven employees come from the calendar and registered leave, not scans.

## 10. Open items and technical flags

### Open items

| ID | Item | Current proposal |
| --- | --- | --- |
| OPEN-01 | Night or continuous shifts: their breaks count as working time | Confirm whether any exist; day shifts keep the unpaid lunch |
| OPEN-02 | Actual shift times and early or late check-in windows | Take from current practice |
| OPEN-03 | Employees leaving and returning during a shift | Ignore middle scans in v1 unless a gate-out rule is needed |
| OPEN-04 | Grace period and whether late minutes beyond it are deducted | 5 minutes; beyond that, deducted and counted as late |
| OPEN-05 | Lateness for office staff: discipline only, or deducted | Discipline only |
| OPEN-06 | Does approved unpaid leave forfeit the attendance bonus? | Pay Policy OPEN-05 decides |
| OPEN-07 | Annual leave carry-over to the next year | To decide |
| OPEN-08 | How employees confirm OT agreement (signature, kiosk, list sign-off) | Line list signed by the employees, recorded on the request |

### Technical flags

| ID | Flag |
| --- | --- |
| FLAG-TECH-01 | **Device integration.** How scans reach Odoo from the current biometric devices (vendor SDK or API, file export, middleware), how often, and how offline uploads are handled. Store the server receipt time as well as the device time; device clocks drift. |
| FLAG-TECH-02 | **Odoo base.** Decide whether to extend `hr.attendance` and `hr.leave` (CE 18) or build dedicated models; `hr.attendance` holds check-in/check-out pairs only, with no shift, category or exception concept. |
| FLAG-TECH-03 | **Volume.** Thousands of employees × days: daily computation runs as a batch job, recomputing only days whose inputs changed. |
| FLAG-TECH-04 | **Shift-day assignment** for shifts crossing midnight and for scans in the early or late windows. |
