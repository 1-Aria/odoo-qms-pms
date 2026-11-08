**Configuration** (payroll managers): *Payroll → Configuration*

- *Pay Components*: a component is saved only when its configuration is complete; the error names
  what is missing.
- *Pay Scales*: a scale holds versions; a version's date is when its amounts start. To change amounts,
  add a version rather than editing an old one.
- *Time Parameters*: the statutory parameters (`vn.*`) and the company's own. A new value is a new
  version from its date.

**Pay lines** (payroll officers): the *Pay Lines* page on a contract.

| The component's amount source | The line holds |
|---|---|
| Amount on the pay line | the amount |
| Parameter | nothing: the amount is the parameter's value on the date |
| Scale cell | the scale key, or an amount that overrides the cell |
| Remainder of a scale cell | the scale key (or a total amount); the amount is the cell minus the lines ticked *Part of the scale cell* |

Two lines of one component cannot overlap: to change one, end it the day before and add a new line.

**Roles:** *Settings → Users*, application *Payroll*: Officer, Reviewer, Approver, Reader, Manager.
New users receive no payroll role; give it on purpose.

**Pay profiles** (step 2):

- *Payroll → Configuration → Participant Types*: the four legal categories and the funds, base and tax
  method of each.
- A contract's *Pay Lines* page starts with its participant type (new contracts: labour contract), the
  declared SI base for a manager without a labour contract, and the probation form. A probation clause
  needs the end of the trial period.
- An employee's *Payroll* page: pay group, attendance mode (follows the pay group, can be changed),
  region, tax residency, union membership, the year of the commitment form for short contracts.
- Dependents: on the employee's *Relatives* page, tick *PIT Dependent* and give the months registered
  from and to (first day of the month) and the registration document.

**Monthly inputs** (step 3): *Payroll → Monthly Inputs → Payroll Periods*: create the month, *Build
Summaries* (as often as needed while attendance is open), check and correct (*Corrected by hand* keeps a
summary from being rebuilt), then *Close Attendance*. Enter attainment, IE units and menstruation days in
*Monthly Inputs*; bonuses and adjustments as entered lines, which an approver approves. Mark time off types
paid by social insurance on the type, and the nursing break on the employee's *Payroll* page.

**Calculation** (step 4): on the salary structure, tick *Vietnamese Pay Context* and give it one rule per
pay component, with *Pay Component* as both the condition and the amount type. Payslips of that structure
cover a calendar month; computing one takes the month's latest contract, reads its monthly input (which
must exist, with segments when the month is split, and with an attainment source when productivity or
performance pay is in force) and refreshes the worked days. The optional columns of the payslip lines
show each line's dates, days, hours, factor, hourly rate, attainment and the month an adjustment belongs to.

**Deductions and net pay** (step 5): the structure also needs one *Pay Component* rule for each
calculated component: employee insurance, union dues, PIT, damage, net pay, advance, remaining to pay,
and the employer's funds. Every contract of the month needs a participant type, and an employee on a
labour contract a minimum wage region. Monthly inputs built before step 5 need one rebuild, for the
month's scheduled days. *Monthly Inputs → Damage Decisions*: record each work-rules decision with its
amount; payslips deduct from the oldest first, and a decision is settled once approved payslips have
taken all of it. An entered deduction is typed as a positive amount.

**Checks** (step 6): *Payroll → Configuration → Payroll Checks* lists the checks and their default
levels. To change a level, add a time parameter of type text `vn.check.<code>` (or
`vn.check.<code>.<component code>` for one component) with the value `error`, `warning`, `note` or
`off`, from the date it applies. Each payslip's *Checks* page shows its results, and *Monthly Inputs →
Check Results* lists them all; reviewers write a note on each warning. A payslip with an integrity
error has no lines until the cause is put right and it is calculated again. For the probation limit,
fill in the contract's *Probation Job Category*.

**Runs** (step 7): *Payroll → Payslips Batches*, create a batch and choose its *Payroll Period* (and, for an
off-cycle run, its employees). Close the month's attendance first. *Calculate* (officer) makes and
calculates the payslips; correct inputs and calculate again as often as needed. *Review* (reviewer) needs
no error left and a note on each warning; the *Errors / Warnings* button lists them. *Approve* (an
approver who did not calculate the run) confirms the payslips; *Mark as Paid* once paid. After approval
nothing in the run changes: enter corrections on a later month's input, with the month they belong to.

**Reports** (step 8): *Print Payslips* on a run prints every employee's payslip; a single one prints
from the payslip's *Print* menu. *Monthly Inputs → Payroll Analysis* pivots the lines of every run by
employee, department, month or pay item, and downloads to Excel. The *Payroll Register* (on runs) and
*Attendance Sign-off* (on payroll periods) templates are in *Excel Import/Export → Templates*: edit
their layout there, and add their export button from the template's form.

**Statements** (step 9): *Monthly Inputs → Statements*, create one with its kind and months, *Generate*,
then open its *Lines* and export them (select all, *Action → Export*). *Done* freezes a statement; a
payroll manager can set it back to draft. Only approved runs count. *Opening Data*: one row per employee
and year for the months paid before go-live; fill it by hand or with *Import records* from a spreadsheet.


**Time from attendance** (step 10): the summary follows the attendance settings: *Attendances →
Configuration → Settings*, the two tolerances (the grace period and the overtime minimum; changing
either recomputes all past overtime), and on the working calendar *Hours per Paid Day* and the night
window. An employee's *Attendance Mode* (on the *Payroll* tab, defaulted from the pay group) decides
whether scans or the calendar give the days worked. A day with a check-in and no check-out blocks
review until the attendance is corrected.
