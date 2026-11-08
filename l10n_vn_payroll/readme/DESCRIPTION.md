Vietnamese payroll on OCA `payroll`.

This first step holds the configuration layer:

- **Pay components:** each earning, deduction, employer contribution and total, with its legal nature,
  whether it counts in the SI base and the OT base, its PIT treatment, where its amount comes from and
  how it is prorated.
- **Pay scales:** grade and step tables and productivity levels, with dated versions of their amounts.
- **Contract pay lines:** dated lines on each contract. A change is a new line from its date; the
  contract's wage follows the lines whose component sets it.
- **Payroll roles:** Officer, Reviewer, Approver, Reader and Manager. Officers see every payslip of their
  companies, and new users receive no payroll role.
- **Statutory parameters:** minimum wages, the SI reference level, contribution rates and caps, PIT
  brackets and deductions, OT factors and limits, created for every Vietnamese company and kept up to
  date at each upgrade, without overwriting values edited by hand.
- **Pay profiles** (step 2): participant types (labour contract, probation contract, manager without a
  labour contract, contract under 1 month) deciding the SI funds, the SI base and the PIT method; on the
  contract, the participant type, a declared SI base and the probation form; on the employee, the pay
  group, attendance mode, minimum-wage region, tax residency, union membership and commitment form year;
  PIT dependents registered on the employee's relatives.
- **Monthly inputs** (step 3): one summary per employee and month built from Odoo's attendance, approved
  time off and working schedules — days worked, paid and unpaid days, leave by who pays it, overtime by
  day type above a daily minimum, paid breaks for women — plus attainment, IE units and approved entered
  amounts. Closing attendance freezes the time figures.
- **Earnings calculation** (step 4): on a structure marked *Vietnamese Pay Context*, a payslip covers one
  month, takes the latest contract of the month (closed ones included) and the month's input, and computes
  every earning from the pay lines: proration by paid days, days worked or a daily rate, the probation
  rate, attainment, the attendance condition, approved entered amounts and adjustments, IE units, and OT
  on the OT base. A month split by a contract change, a pay line change or the end of a probation clause
  shows one line per part. Each line holds its exact amount through the *Pay Component* rule type, and
  the whole calculation is kept on the payslip as a snapshot.
- **Deductions and net pay** (step 5): social, health and unemployment insurance by fund, from the
  contract's participant type, on the SI base with its floor and caps, and none in a month with 14 or
  more working days neither worked nor paid; the union fee and members' dues; PIT, progressive with OT
  and capped exemptions and dependents, or flat for short contracts and non-residents; damage
  compensation decisions deducted oldest first within 30% of pay after insurance and PIT; net pay, and
  the amount to pay once salary advances are settled (the advances themselves come with
  `l10n_vn_payroll_account`). Deductions show as negative lines.
- **Checks** (step 6): 20 integrity, legal and policy checks run on every payslip — period not closed,
  missing attainment or identifiers, unapproved entries, negative net pay, the minimum wage, probation
  limits, unlawful deductions, OT limits, variable pay unchanged for months, sharp changes in net pay,
  and more. A check's level (error, warning, note or off) is a dated parameter, per check and per
  component. Results sit on the payslip, where reviewers write their notes. A payslip that cannot be
  calculated gets an error result instead of stopping the rest of the batch.
- **Runs** (step 7): a payslip batch of a payroll period, regular or off-cycle, moves Draft → Calculated →
  Reviewed → Approved → Paid. Calculating makes and calculates the period's payslips; review needs no
  errors and a note on every warning; approval is by someone other than the person who calculated, and
  an employee is paid by one approved run per month. Once approved, the payslips, their lines, the
  monthly inputs they read and the pay lines they used are locked; corrections go into a later month.
- **Reports** (step 8): each payslip keeps its totals (time and OT by category, pay by section,
  deductions, net, amount to pay, employer cost) for lists, exports and Excel templates; a payroll
  analysis view for pivots that download to Excel; the employee payslip in Vietnamese with English
  labels (Labor Code Art. 95); two editable Excel templates, the payroll register and the attendance
  sign-off sheet.
- **Statements and opening data** (step 9): SI contributions and changes, PIT for a period and for the
  year, the OT schedule and the union fee and dues, generated as lists from approved payslips and
  exported with Odoo's export; the year-to-date figures of months paid before go-live, which the annual
  PIT and the yearly OT count add.


**Time from attendance** (step 10): the monthly summary reads each day's figures from
`hr_attendance_day`. Odoo's attendance tolerances decide overtime (the grace period and the overtime
minimum), and overtime is split into workday, rest day and holiday hours and their night variants,
with normal hours at night under their own category. A calendar that combines shifts counts each
shift as a day. Late arrivals, absences and days without check-out are counted, office staff on
*present unless on leave* are paid their scheduled days, overtime above the daily limit is reported,
and the check *Days with more than 12 hours of work* reports long days.
