Each employee's attendance per day, derived from Odoo's own attendance, for other modules to read
(payroll, later IE). It has no screens of its own.

**From Odoo:** the expected hours of the contract's calendar, less leave and public holidays;
worked hours; the day's overtime with its two tolerances; approved overtime.

**Derived per day:**

- day type: workday, rest day or public holiday;
- scheduled and expected hours;
- normal hours, and days worked: normal hours ÷ the hours of a paid day;
- overtime, its part inside the night window, and overtime not approved;
- normal hours inside the night window;
- late arrival and early leave, in minutes and beyond the grace period;
- absence: expected hours and no attendance;
- incomplete: an attendance without check-out.

Calendars whose shifts cross midnight are not supported: Odoo's overtime counts their expected
hours only up to midnight.
