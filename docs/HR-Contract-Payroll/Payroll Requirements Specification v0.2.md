# Payroll Requirements Specification

v0.2 · Oct 30, 2026 · @Peter

This spec states what the payroll module for Odoo CE 18 must do: hold pay data, calculate monthly pay from closed attendance and IE figures, and produce payslips, payments, accounting entries and statutory data. It says *what*, not *how*; models and code belong to the technical design.

v0.2 adds the principle that the module enforces no pay policy (§0), per-person contribution profiles, configurable validation levels, component proration, the OT supplement, conditional components, daily-paid workers, go-live opening data and the starting point in the instance (§11). Existing FR numbers are kept; new ones start at FR-59. Change log at the end.

**Document set**

| Document | Holds | Role here |
| --- | --- | --- |
| Vietnam Payroll Regulation Reference v0.2 | Laws, rates, caps | Legal limits and the checks that report on them |
| Pay Policy v0.2 | Current scheme (options A and B) and target policy | What the go-live configuration calculates |
| Attendance Specification v0.2 | Paid time | The time input |
| IE Business Logic Spec v0.6; IE Technical Design v0.4 §14 | Efficiency incentive | The incentive input (units U) |
| Payroll Acceptance Test Cases v0.2 | Expected payslips | Acceptance |

*Payslip Profiles 2026 v0.1* (HTML) is superseded by the test cases.

**Conventions**

- `FR-nn`: a numbered requirement, so development and tests can trace to it.
- `[P]`: effective-dated parameter. `[OPEN-n]` and `FLAG-TECH-n`: listed in §10.
- Rules refer to the pay policy and regulation sections; no amount or rate is fixed in this spec.

## 0. Principles

1. **The module enforces no pay policy.** How each component counts for SI, OT and PIT, how it is prorated and when it is paid is configuration on the component. The engine calculates whatever the configuration says. Legal checks report; whether a check blocks is also configuration (FR-59). The company decides how it applies the law and answers for it.
2. **Actual pay first.** The go-live configuration reproduces the current scheme (Pay Policy §3–§11), checked against the accountant's payslips for a parallel month. The target policy (Pay Policy §12) is reachable by changing configuration, not code.
3. **Contribution bases are per person.** Which funds apply, where each base comes from and its floor are on the person's contribution profile, so an owner, a worker and a probationer differ in data, not in rules (FR-60).

## 1. Scope, users and access

Payroll owns money; it takes time from attendance and incentive units from IE, and calculates neither.

**In scope:** employee pay profiles and contracts, salary scale, pay components, contribution profiles, the monthly run, payslips, the bank transfer file, accounting entries, data for SI and PIT declarations, payroll reports.

**Out of scope:** computing attended time and leave (attendance module), computing incentive units (IE module), recruitment, performance appraisal, the trading company's payroll in v1.

| Role | Can do |
| --- | --- |
| Payroll officer (HR) | Maintain pay profiles and inputs, run and correct payroll, produce outputs |
| HR manager | Review the run; certify skill levels; approve contract pay changes |
| Director | Approve the run before payment |
| Accountant | Post accounting entries; read payroll totals |
| Employee | See their own payslips `[OPEN-01]` |

- **FR-01** Salary data is visible only to the roles above. Supervisors and line leaders see attendance, not pay.
- **FR-02** The person who prepares a run cannot approve it.
- **FR-67** Payroll data is company-scoped. v1 is configured for the garment company only; nothing in the design assumes one company.

## 2. Master data and configuration

Every amount the calculation uses comes from configured, effective-dated data; nothing is typed into a salary rule.

| Data | Content | Changed by |
| --- | --- | --- |
| Pay component | Code, name, legal nature, flags: in SI base, in OT base, PIT treatment (taxable, exempt, exempt up to a cap, excluded), cap parameter, proration basis (FR-61), condition (FR-64), payslip section, accounting account | Payroll officer, HR manager approval |
| Parameters | Minimum wage by region, reference level, rates per insurance fund, caps, PIT brackets, family deductions, meal cap, OT factors, OT supplement per hour, hour limits, standard days, incentive unit rate, validation levels | Payroll officer, with effective date |
| Salary scale | Grade × step → amount; worker base salary | HR manager, new version per change |
| Allowance tables | Skill levels S1–S4; duty allowances per duty | HR manager |
| Employee pay profile | Group (worker, support, office, daily-paid, manager), attendance mode, workplace region, SI number, tax code, residency, dependents, union member, bank account | Payroll officer |
| Contribution profile | Participant type, funds that apply, base source and floor (FR-60) | Payroll officer |
| Contract pay | Grade and step (or worker base, or daily rate), component lines with start and end dates, probation dates, rate and form (separate contract or clause) | HR manager |

- **FR-03** Every parameter, scale and allowance table is stored with an effective date. A calculation uses the values effective in the period being calculated, so past periods can be reproduced.
- **FR-04** Contract salary is looked up from the scale by grade and step, or from the worker base parameter, not entered by hand. G6 salaries, daily rates and owners' salaries are entered on the contract or profile.
- **FR-05** A skill line records the level, the certification or review date and who granted it. IE skill data can be shown beside it as a suggestion. Under option A (Pay Policy §3.2), each month also records whether the level was met, the evidence, and any HR override with its reason.
- **FR-06** Dependents are registered with start and end months and a reference to the registration document.
- **FR-07** Adding a new pay component (for example a role bonus) needs configuration only.
- **FR-60** A **contribution profile** per person holds: participant type (labour-contract employee, probation contract, enterprise manager without a labour contract, other); the funds that apply (SI pension, sickness, accident; HI; UI; union fee; union dues); the base source (the sum of contract components flagged *in SI base*, or a declared amount); the floor (regional minimum wage or reference level `[P]`); and the PIT method. Defaults come from the participant type.
- **FR-61** Each component has a **proration basis**: paid days, days worked, none (paid in full), or per hour. Components prorate over standard days (FR-62) for the days they were active.
- **FR-62** **Standard days** come from a parameter: a fixed number `[P 26]` or the month's scheduled working days from attendance.

## 3. The monthly run

One run per month covers all employees; it moves through fixed states, and only an approved run produces payments and entries.

1. **Open** the period. Attendance and IE must both be closed for that month (Attendance §8.4).
2. **Import inputs:** attendance totals per employee, IE incentive units, entered amounts (KPI bonus, the efficiency bonus during IE shadow mode), skill-level results (option A), adjustments for earlier periods, damage deductions.
3. **Calculate** every payslip (§4).
4. **Validate:** run the checks in §7 at their configured levels.
5. **Review** by the HR manager. Corrections reopen individual payslips, which are recalculated.
6. **Approve** by the director. The run is locked.
7. **Produce outputs:** payslips, bank file, accounting entries, statutory data (§6).
8. **Mark paid** once the bank confirms payment.

- **FR-08** Run states: Draft → Calculated → Reviewed → Approved → Paid. A locked run cannot be edited; changes go into the next run as adjustments (§4.9).
- **FR-09** Recalculating a draft run is repeatable: same inputs give the same results.
- **FR-10** Each payslip keeps a snapshot of the inputs and parameter values it used.
- **FR-11** Off-cycle payslips are possible for leavers paid before the run date.
- **FR-66** **Go-live opening data:** for the first month calculated in the module, the year-to-date OT hours, taxable income, PIT withheld, leave balances and dependents are loaded per employee, so limits, the annual finalisation and leave pay are correct from the first run `[OPEN-07]`.

## 4. Calculation

Each payslip is calculated in this order, and every line takes its SI, OT, PIT, proration and condition from its component (§2), never from the rule.

### 4.1 Salary and fixed components

```latex
\text{Component pay} = \text{amount} \times \frac{\text{days on its basis}}{\text{standard days}}
```

- **FR-12** Paid days, days worked and scheduled days come from attendance (Attendance §9). Each component is prorated on its own basis (FR-61) over the days it was active.
- **FR-13** During probation, salary pay uses the probation rate (Pay Policy §11).
- **FR-65** **Daily-paid** contracts pay daily rate × paid days; their OT hourly base is the daily rate ÷ 8.

### 4.2 Overtime and night pay

```latex
\text{Hourly rate} = \frac{\sum \text{components flagged in OT base}}{\text{standard days} \times 8}
```

- **FR-14** OT pay = hourly rate × factor × hours, per category from attendance (factors in Pay Policy §8).
- **FR-15** The hourly rate uses only components flagged *in OT base*, at their full contract amounts for the month, or the amount earned that month for a conditional component (option A skill pay).
- **FR-63** The **OT supplement** is a component paid per OT hour: supplement per hour `[P]` × the hour's factor. It has its own flags; by default it is PIT-treated as OT.

### 4.3 Bonuses and conditional components

- **FR-16** Efficiency incentive = IE units U × unit rate `[P]`, read from IE's closed period record (IE TD §14.3). Until IE leaves shadow mode, an entered amount under the same component.
- **FR-17** Attendance bonus: paid in full when attendance reports no unexcused absence and late arrivals within the allowed number (Pay Policy §3.1); otherwise zero.
- **FR-18** KPI bonus, annual bonus and future bonus types are entered or imported amounts per employee.
- **FR-64** A **conditional component** is paid for a month only when its condition holds: the attendance bonus on attendance counts; option A skill pay on the month's skill result (FR-05). The payslip shows the condition's result, and an override needs a reason.

### 4.4 Other earnings

- **FR-19** Travel and housing support, phone lump-sum and any other support as configured on the profile, each prorated on its basis (FR-61).

### 4.5 Gross pay

- **FR-20** Gross = sum of all earning lines, including adjustments (§4.9).

### 4.6 Insurance

```latex
\text{SI base} = \max(\text{base source},\ \text{floor}) \quad \text{base source} = \textstyle\sum \text{contract components flagged in SI base, or the declared amount}
```

- **FR-21** The SI base uses contract amounts, not prorated pay, from the contribution profile (FR-60). SI and HI apply to the base capped at 20 × reference level; UI to the base capped at 20 × regional minimum wage.
- **FR-22** Employee: SI 8%, HI 1.5%, UI 1%. Employer: SI 17.5% (14% pension, 3% sickness and maternity, 0.5% accident), HI 3%, UI 1%, union fee 2%. Rates are parameters per fund, and each applies only if the profile includes that fund.
- **FR-23** No compulsory SI, HI or UI for a month in which the employee neither works nor is paid for 14 working days or more (unpaid leave, sick leave, maternity) `[OPEN-03]`. Separate probation contracts are excluded; a probation clause inside a labour contract is not.
- **FR-24** A change of SI base takes effect from `[OPEN-04]`.

### 4.7 Union dues

- **FR-25** Members only: 0.5% of the SI base, capped `[P]`. With no member, no dues line appears. The 2% employer union fee (FR-22) applies regardless of membership.

### 4.8 Personal income tax

```latex
\text{Taxable income} = \text{gross} - \text{exempt and excluded amounts} - \text{employee insurance} - \text{family deductions}
```

- **FR-26** Exempt amounts: OT, night pay and the OT supplement for hours within the legal limits (pro rata above them), cash meal up to its cap, phone lump-sum within the company rule, untaken-leave pay.
- **FR-27** Tax method per employee, on the contribution profile: progressive (residents with a contract of 3 months or more, and managers paid without a labour contract), flat 10% on payments of 5,000,000 or more (contracts under 3 months, including separate probation contracts, unless the employee has filed the commitment form), flat 20% (non-residents).
- **FR-28** Progressive tax uses the monthly brackets effective for the payment month. Family deductions use dependents registered for that month.
- **FR-29** Income is taxed in the month it is paid; an adjustment for an earlier month is taxed in the month it is paid.

### 4.9 Adjustments, deductions and net pay

- **FR-30** Corrections to locked periods are separate lines naming the period they belong to; they carry their component's flags.
- **FR-31** Damage compensation deductions are capped at 30% of the month's pay after insurance and PIT; any excess carries to the next month.
- **FR-32** Net pay = gross − employee insurance − union dues − PIT − damage deductions. A negative net pay is an error (§7).
- **FR-33** Employer cost = gross + employer insurance + union fee.
- **FR-34** Calculations run at full precision; each payslip line is rounded to whole VND, half up.

## 5. Mid-month events

Any change inside a month splits that month at the change date, and each part is calculated with the terms in force on its days.

| Event | Requirement |
| --- | --- |
| New hire | **FR-35** Paid days start on the first working day. Probation rate applies until the probation end date. |
| Probation ends | **FR-36** Days before the end date at the probation rate, days after at the full rate. After a separate probation contract, SI starts with the labour contract; with a probation clause, SI ran from the contract's first day. |
| Salary, grade, step, skill level or component change | **FR-37** Split by effective date; each part prorated. |
| Leaver | **FR-38** Paid days up to the last working day, untaken annual leave paid (PIT-exempt), the partial month's efficiency bonus, any severance per the contract. Final pay within 14 working days, as an off-cycle payslip if needed. |
| Maternity, long sick leave | **FR-39** Days paid by the SI fund are unpaid days in payroll; the 14-day rule decides contributions (FR-23). |
| Transfer between groups (e.g. worker to line leader) | **FR-40** Split by date; the incentive stops from the transfer date (IE scope ends). |

## 6. Outputs

An approved run produces everything needed to pay people, book the cost and file the statutory returns, without re-keying.

### 6.1 Payslip

- **FR-41** One payslip per employee per run, in Vietnamese with English labels `[OPEN-05]`, showing: earnings by component, OT and night hours with amounts, each deduction, net pay, SI base, paid and unpaid days, and the result of each conditional component (Labor Code Art. 95).
- **FR-42** Delivered as PDF; employees can see their own payslips if self-service is adopted (OPEN-01).

### 6.2 Payment

- **FR-43** Bank transfer file for net pay in the paying bank's format `[OPEN-06]`. Employees without a bank account are listed as an error before approval.

### 6.3 Accounting

- **FR-44** One journal entry per run, mapped from each component's account and the employee's department. Account codes are those of the company's chart (Circular 99/2025):

| Posting | Debit | Credit |
| --- | --- | --- |
| Gross pay | Cost by department `[P mapping]`: 6220 direct labour (sewing, cutting, finishing lines), 6271 factory staff (production support, factory management), 6411 selling, 6421 administration | 3341 |
| Employee SI, HI, UI | 3341 | 33831, 33841, 33861 |
| Union dues (members) | 3341 | 33881 `[to confirm with the accountant]` |
| PIT withheld | 3341 | 33351 |
| Employer SI, HI, UI, union fee | The same cost accounts as the employee's gross pay | 33831, 33841, 33861, 33821 |
| Payment of net pay | 3341 | Bank (at payment) |

The mapping is configuration, so it follows the chart of accounts in use.

### 6.4 Statutory data

- **FR-45** SI: the monthly contribution list and the list of changes (joiners, leavers, base changes, long absences) in the form used for the SI agency's electronic filing `FLAG-TECH-03`.
- **FR-46** PIT: the data for the periodic withholding return, the annual finalisation for employees who authorise the company, withholding certificates per employee, and the schedule of OT and night hours and amounts Decree 253 requires.
- **FR-47** Union fee and union dues totals per month.

### 6.5 Reports

- **FR-48** Payroll register; cost by department and line; OT hours and cost against the legal limits; incentive cost; change against the previous month.
- **FR-49** Labour cost per period for the IE self-funding check (base wages, incentive paid, allowances).

## 7. Validations and controls

Checks run on every calculation. Integrity checks are always errors. Policy and legal checks have a configured level: **error** (blocks approval), **warning** (needs a reviewer's note) or **off**.

| Check | Kind | Default level |
| --- | --- | --- |
| Attendance or IE period for the month not closed | Integrity | Error |
| Negative net pay | Integrity | Error |
| Missing bank account, tax code or SI number for a paid employee | Integrity | Error |
| Component without SI, OT, PIT or proration settings | Integrity | Error |
| Contract salary for full normal hours below the regional minimum wage | Legal | Error |
| Daily rate below the hourly minimum × the day's normal hours | Legal | Error |
| Component flags inconsistent with its legal nature (e.g. a welfare item in the OT base, a fixed allowance outside the SI base) | Legal | Warning |
| Probation longer than the legal limit for the job | Legal | Warning |
| OT hours above 40 in the month or 300 in the year | Legal | Warning |
| A conditional component paid in full every month for `[P 6]` months running | Policy | Warning |
| Net pay changed by more than `[P 30%]` from the previous month | Policy | Warning |
| Incentive units imported for an employee outside IE scope | Policy | Warning |
| Skill level past its review date | Policy | Warning |
| Dependent registration missing its document | Policy | Warning |

- **FR-50** Every change to pay data, inputs and payslips keeps who, when, old value and new value.
- **FR-51** A locked run, its payslips and their snapshots can never be changed or deleted.
- **FR-59** Each policy or legal check's level is a parameter with an effective date. A run that passes a lowered check records the check, its level and the approver.

## 8. Non-functional requirements

- **FR-52 Volume.** A full run for `[P 3,000]` employees (about 300 today) calculates in under `[P 10 minutes]`; recalculating one payslip takes seconds.
- **FR-53 Reproducibility.** Any past payslip can be regenerated from its snapshot with the same result (FR-03, FR-10).
- **FR-54 Security.** Salary fields hidden from users outside the payroll roles, including in exports and list views; access to payroll data is logged.
- **FR-55 Language.** Interface and outputs in Vietnamese and English.
- **FR-56 Parameter changes without code.** A new minimum wage, reference level, tax table, rate or check level is entered as a dated record by the payroll officer.
- **FR-57 Retention.** Payroll records kept for at least `[P 10 years]`, in line with accounting record rules.

## 9. Interfaces

| Direction | Partner | Data | When |
| --- | --- | --- | --- |
| Attendance → Payroll | Attendance module | Per employee per month: scheduled, paid and unpaid days; days worked; days counted for the SI 14-day rule; leave by type; paid break minutes; OT and night hours by category; late arrivals and unexcused absences; OT hours year to date | At attendance close |
| IE → Payroll | IE module | Per operator per month: incentive units U and the payable flag; skill metrics for the skill review and option A's monthly result | At IE close |
| HR → Payroll | Employees and contracts | Pay profile, contribution profile, contract pay, dependents | Continuous |
| Payroll → Accounting | Odoo Accounting | Journal entry per run | On approval |
| Payroll → Bank | Paying bank | Transfer file | On approval |
| Payroll → SI and tax filing | SI agency and tax portals, via the filing tool in use | Contribution lists, changes, PIT returns and certificates | Monthly, quarterly, yearly |
| Payroll → IE | IE module | Labour cost per period for the self-funding check | After approval |

- **FR-58** Payroll reads only closed attendance and IE periods; it never changes their data.

## 10. Acceptance, open items and technical flags

**Acceptance.** The module is accepted when it reproduces every unblocked case in the payroll test cases to the dong, and every FR is covered by at least one case. Go-live additionally needs one parallel month in which the current-scheme configuration reproduces the accountant's payslips (OPEN-07).

### Open items

| ID | Item |
| --- | --- |
| OPEN-01 | Employee self-service for payslips: Odoo portal, Zalo OA message, or printed only |
| OPEN-02 | Proration of the supports: per day worked or per paid day (Pay Policy OPEN-13) |
| OPEN-03 | Confirm the 14-day no-contribution rule and its leave types against the SI Law 2024 and Decree 158/2025 |
| OPEN-04 | Month from which a changed SI base applies (change date, or the following month) |
| OPEN-05 | Payslip layout and language |
| OPEN-06 | Paying bank and its transfer file format |
| OPEN-07 | Go-live month and the parallel run (Pay Policy OPEN-16); the accountant's payslips for that month are the expected results |
| OPEN-08 | Union dues account (33881 or another) and whether the union fee is paid while no grassroots union exists |

### Technical flags

| ID | Flag |
| --- | --- |
| FLAG-TECH-01 | **OCA payroll fit-gap. Proposal: build on OCA `payroll` and `payroll_account`.** They are installed and hold this year's payslips. Their engine exposes the hooks needed to inject component sums, bases and profiles into the rules (`get_payroll_dict`, `get_current_contract_dict`, `localdict_hook`, `oca/payroll/payroll/models/hr_payslip.py:428-614`), and IE's payroll pull is designed for it (IE TD-49). Rules become short generic sums over flagged components. OCA posts one entry per payslip (`payroll_account/models/hr_payslip.py:46`); FR-44's one entry per run is added in our module. To be confirmed in the fit-gap, with `payroll_rule_time_parameter` and `base_time_parameter` checked for FR-03. |
| FLAG-TECH-02 | **Contract pay.** Replace the single `wage` field on `hr.contract` with grade, step and dated component lines; keep `wage` filled from the base line for compatibility. OCA `payroll_contract_advantages` has no dates or flags, so it does not fit. |
| FLAG-TECH-03 | **Statutory files.** SI electronic declarations go through a licensed filing service; PIT returns through the tax portal. Decide between export files in their formats and a direct integration. |
| FLAG-TECH-04 | **Batch performance** for thousands of payslips: compute in bulk, not line by line through the ORM. |
| FLAG-TECH-05 | **Field-level security** on salary fields across forms, lists, exports and reports. In core, `wage` has no field-level group (`odoo/addons/hr_contract/models/hr_contract.py:42`), so everyone who can read a contract sees it, including the read-only group `hr_contract.group_hr_contract_employee_manager` (`security/ir.model.access.csv:8`). |

## 11. Starting point in the instance

What runs today (read from the test copy of production, 2026-10-30), so the build replaces it knowingly.

- **Modules:** OCA `payroll` 18.0.1.4.0 and `payroll_account` 18.0.1.0.6 are installed, on core `hr_contract`, `hr_attendance`, `hr_holidays`, `hr_work_entry` and `hr_skills`.
- **Structures:** *Salary Monthly* (MINW wage ÷ 26 × days from attendance, BNOT OT, PALV, BNPC pieces, COMD bonus hours, BONP bonus, NET) and *Salary Daily* (DAYW, BOTD, NET). BNSK (skill bonus) exists but is in no structure.
- **No deductions:** NET is the sum of the earnings; no SI, HI, UI, union or PIT is calculated, so net pay equals gross. SI and PIT have been handled outside Odoo.
- **Accounting:** one entry per payslip, Dr 6271 / Cr 3341 for the net amount, for every employee. No employer contribution cost, no 338x or 33351 postings. January 2026 was never posted.
- **PALV** is leftover debug code (edited 2026-07-04) that always raises an exception, so computing a monthly payslip fails.
- **Inputs:** the rules read `hr.attendance` and timesheet lines directly, filtered on task names ("Pieces Pay", "Bonus Hour", "Bonus Pay") and on the hand-made field `account.analytic.line.x_status`; the skill bonus reads the hand-made field `hr.skill.level.x_bonus_amount`. BOTD and MINW shift dates to the UTC+7 day differently.
- **History:** runs January to April 2026 done; May in *verify*; nothing since. 287 open contracts: 217 Temporary, 22 Seasonal, 41 Employee, 7 daily-paid; 26 with wage 0.
- **Migration:** old payslips stay as they are, read-only history. The old structures and rules are archived at go-live; the hand-made fields are retired once nothing reads them. Payslips from the go-live month are calculated only by the new module.

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-29 | First draft. |
| 0.2 | 2026-10-30 | Principles (§0). Contribution profiles (FR-60), proration bases (FR-61), standard days source (FR-62), OT supplement (FR-63), conditional components (FR-64), daily-paid pay (FR-65), go-live opening data (FR-66), company scope (FR-67), configurable check levels (FR-59). FR-04, -05, -15, -17, -19, -21 to -27, -36, -41, -46 updated; probation clause versus contract. Accounting table moved to the company's Circular 99 codes, with debits and credits. Validations split into integrity checks and configurable checks, with new legal and policy checks. Interfaces extended. OPEN-07 and OPEN-08 added; FLAG-TECH-01 proposes OCA payroll. §11 records the instance's starting point. Payslip Profiles superseded by the test cases. |
