The figures follow these settings:

- **Grace period:** *Attendances → Configuration → Settings → Extra Hours: Tolerance Time In Favor Of Employee*. A day short by
  no more than this is complete, and an arrival this late is not counted as late.
- **Overtime minimum:** *Tolerance Time In Favor Of Company*. A day's extra time counts as overtime
  only above this, then in full.
- Changing either tolerance makes Odoo recompute the overtime of every attendance of the company,
  past months included.
- **Overtime approval:** *Extra Hours Validation*. With validation by a manager, only the validated
  hours count as overtime; the rest is reported as not approved.
- **Hours per Paid Day**, on the working calendar: set it on a calendar that combines shifts, for
  example 8 on a 16-hour two-shift calendar, so that each shift worked counts as one day and an
  arrival is measured from the start of the nearest shift.
- **Night From / Night To**, on the working calendar: the night window, 22:00–06:00 by default.

Server code reads the figures with `employee._attendance_days(date_from, date_to)`.
