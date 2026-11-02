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
