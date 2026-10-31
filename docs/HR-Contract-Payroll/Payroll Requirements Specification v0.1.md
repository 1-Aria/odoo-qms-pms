# Payroll Requirements Specification

Oct 29, 2026 · @Peter

This spec states what the payroll module for Odoo CE 18 must do: hold pay data, calculate monthly pay from closed attendance and IE figures, and produce payslips, payments, accounting entries and statutory data. It says *what*, not *how*; models and code belong to the technical design.

**Document set**

| Document | Holds | Role here |
| --- | --- | --- |
| Vietnam Payroll Regulation Reference | Laws, rates, caps | Legal limits the rules must respect |
| Pay Policy Draft | Company pay rules | What each rule calculates |
| Attendance Specification | Paid time | The time input |
| IE Business Logic Spec v0.6 | Efficiency incentive | The incentive input (units U) |
| Payroll test cases (next) | Expected payslips | Acceptance |

**Conventions**

- `FR-nn`: a numbered requirement, so development and tests can trace to it.
- `[P]`: effective-dated parameter. `[OPEN-n]` and `FLAG-TECH-n`: listed in §10.
- Rules refer to the pay policy and regulation sections; no amount or rate is fixed in this spec.

## 1. Scope, users and access

Payroll owns money; it takes time from attendance and incentive units from IE, and calculates neither.

**In scope:** employee pay profiles and contracts, salary scale, pay components, the monthly run, payslips, the bank transfer file, accounting entries, data for SI and PIT declarations, payroll reports.

**Out of scope:** computing attended time and leave (attendance module), computing incentive units (IE module), recruitment, performance appraisal.

| Role | Can do |
| --- | --- |
| Payroll officer (HR) | Maintain pay profiles and inputs, run and correct payroll, produce outputs |
| HR manager | Review the run; grant skill allowances; approve contract pay changes |
| Director | Approve the run before payment |
| Accountant | Post accounting entries; read payroll totals |
| Employee | See their own payslips `[OPEN-01]` |

- **FR-01** Salary data is visible only to the roles above. Supervisors and line leaders see attendance, not pay.
- **FR-02** The person who prepares a run cannot approve it.

## 2. Master data and configuration

Every amount the calculation uses comes from configured, effective-dated data; nothing is typed into a salary rule.

| Data | Content | Changed by |
| --- | --- | --- |
| Pay component | Code, name, legal nature, flags: in SI base, in OT base, PIT treatment (taxable, exempt, exempt up to a cap, excluded), cap parameter, payslip section, accounting account | Payroll officer, HR manager approval |
| Parameters | Minimum wage by region, reference level, rates per insurance fund, caps, PIT brackets, family deductions, meal cap, OT rates and hour limits, standard days, incentive unit rate | Payroll officer, with effective date |
| Salary scale | Grade × step → amount; worker base salary | HR manager, new version per change |
| Allowance tables | Skill allowance levels S1–S3; duty allowances per duty | HR manager |
| Employee pay profile | Group (worker, support, office), attendance mode, workplace region, SI number, tax code, residency, dependents, union member, bank account | Payroll officer |
| Contract pay | Grade and step (or worker base), allowance lines with start and end dates, probation dates and rate | HR manager |

- **FR-03** Every parameter, scale and allowance table is stored with an effective date. A calculation uses the values effective in the period being calculated, so past periods can be reproduced.
- **FR-04** Contract salary is looked up from the scale by grade and step, not entered by hand. G6 (senior management) salaries are the exception, entered on the contract.
- **FR-05** A skill allowance line records the level, the review date and who granted it. IE skill data can be shown beside it as a suggestion.
- **FR-06** Dependents are registered with start and end months and a reference to the registration document.
- **FR-07** Adding a new pay component (for example a role bonus) needs configuration only.

## 3. The monthly run

One run per month covers all employees; it moves through fixed states, and only an approved run produces payments and entries.

1. **Open** the period. Attendance and IE must both be closed for that month (Attendance §8.4).
2. **Import inputs:** attendance totals per employee, IE incentive units, entered bonuses (KPI bonus, the current efficiency bonus during IE shadow mode), adjustments for earlier periods, damage deductions.
3. **Calculate** every payslip (§4).
4. **Validate:** run the checks in §7; errors block, warnings need a note.
5. **Review** by the HR manager. Corrections reopen individual payslips, which are recalculated.
6. **Approve** by the director. The run is locked.
7. **Produce outputs:** payslips, bank file, accounting entries, statutory data (§6).
8. **Mark paid** once the bank confirms payment.

- **FR-08** Run states: Draft → Calculated → Reviewed → Approved → Paid. A locked run cannot be edited; changes go into the next run as adjustments (§4.9).
- **FR-09** Recalculating a draft run is repeatable: same inputs give the same results.
- **FR-10** Each payslip keeps a snapshot of the inputs and parameter values it used.
- **FR-11** Off-cycle payslips are possible for leavers paid before the run date.

## 4. Calculation

Each payslip is calculated in this order, and every line takes its SI, OT and PIT treatment from its component (§2), never from the rule.

### 4.1 Salary and fixed allowances

```latex
\text{Salary pay} = (\text{salary} + \text{skill allowance} + \text{duty allowance}) \times \frac{\text{paid days}}{\text{standard days}}
```

- **FR-12** Paid days and standard days come from attendance (Attendance §9). Each allowance is prorated over the days it was active.
- **FR-13** During probation, salary pay uses the probation rate (Pay Policy §9).

### 4.2 Overtime and night pay

```latex
\text{Hourly rate} = \frac{\text{monthly salary} + \text{skill allowance} + \text{duty allowance}}{\text{standard days} \times 8}
```

- **FR-14** OT pay = hourly rate × factor × hours, per category from attendance.

| Category | Factor `[P]` |
| --- | --- |
| OT workday | 150% |
| OT rest day | 200% |
| OT holiday | 300% |
| Night, normal hours | +30% |
| Night OT, workday | 200%, or 210% if the employee also worked daytime OT that day |
| Night OT, rest day | 270% |
| Night OT, holiday | 390% |

- **FR-15** The hourly rate uses only components flagged *in OT base*. The incentive, KPI bonus and attendance bonus are excluded.

### 4.3 Bonuses

- **FR-16** Efficiency incentive = IE units U × unit rate `[P]`. Until IE leaves shadow mode, an entered amount under the same component.
- **FR-17** Attendance bonus: paid in full when attendance reports no unexcused absence and late arrivals within the allowed number (Pay Policy §3.5); otherwise zero.
- **FR-18** KPI bonus, annual bonus and future bonus types are entered or imported amounts per employee.

### 4.4 Other earnings

- **FR-19** Travel allowance, phone lump-sum and any cash meal allowance as configured on the profile, prorated by paid days `[OPEN-02]`.

### 4.5 Gross pay

- **FR-20** Gross = sum of all earning lines, including adjustments (§4.9).

### 4.6 Insurance

```latex
\text{SI base} = \max(\text{salary} + \text{skill allowance} + \text{duty allowance},\ \text{regional minimum wage})
```

- **FR-21** The SI base uses contract amounts, not prorated pay. SI and HI apply to the base capped at 20 × reference level; UI to the base capped at 20 × regional minimum wage.
- **FR-22** Employee: SI 8%, HI 1.5%, UI 1%. Employer: SI 17.5% (14% pension, 3% sickness and maternity, 0.5% accident), HI 3%, UI 1%, union fee 2%. All rates are parameters.
- **FR-23** No compulsory SI, HI or UI for a month in which the employee neither works nor is paid for 14 working days or more (unpaid leave, sick leave, maternity) `[OPEN-03]`. Probation contracts are excluded.
- **FR-24** A change of SI base takes effect from `[OPEN-04]`.

### 4.7 Union dues

- **FR-25** Members only: 0.5% of the SI base, capped at 10% of the base salary `[P]`.

### 4.8 Personal income tax

```latex
\text{Taxable income} = \text{gross} - \text{exempt and excluded amounts} - \text{employee insurance} - \text{family deductions}
```

- **FR-26** Exempt amounts: OT and night pay for hours within the legal limits (pro rata above them), cash meal up to its cap, phone lump-sum within the company rule, untaken-leave pay.
- **FR-27** Tax method per employee: progressive (residents with a contract of 3 months or more), flat 10% on payments of 5,000,000 or more (contracts under 3 months, including separate probation contracts, unless the employee has filed the commitment form), flat 20% (non-residents).
- **FR-28** Progressive tax uses the monthly brackets effective for the payment month. Family deductions use dependents registered for that month.
- **FR-29** Income is taxed in the month it is paid; an adjustment for an earlier month is taxed in the month it is paid.

### 4.9 Adjustments, deductions and net pay

- **FR-30** Corrections to locked periods are separate lines naming the period they belong to; they carry their component's flags.
- **FR-31** Damage compensation deductions are capped at 30% of the month's pay after insurance and PIT; any excess carries to the next month.
- **FR-32** Net pay = gross − employee insurance − union dues − PIT − damage deductions. A negative net pay is an error (§7).
- **FR-33** Employer cost = gross + employer insurance + union fee.
- **FR-34** Calculations run at full precision; each payslip line is rounded to whole VND.

## 5. Mid-month events

Any change inside a month splits that month at the change date, and each part is calculated with the terms in force on its days.

| Event | Requirement |
| --- | --- |
| New hire | **FR-35** Paid days start on the first working day. Probation rate applies until the probation end date. |
| Probation ends | **FR-36** Days before the end date at the probation rate, days after at the full rate. SI starts with the labour contract. |
| Salary, grade, step or allowance change | **FR-37** Split by effective date; each part prorated. |
| Leaver | **FR-38** Paid days up to the last working day, untaken annual leave paid (PIT-exempt), incentive for the partial month from IE, any severance per the contract. Final pay within 14 working days, as an off-cycle payslip if needed. |
| Maternity, long sick leave | **FR-39** Days paid by the SI fund are unpaid days in payroll; the 14-day rule decides contributions (FR-23). |
| Transfer between groups (e.g. worker to line leader) | **FR-40** Split by date; the incentive stops from the transfer date (IE scope ends). |

## 6. Outputs

An approved run produces everything needed to pay people, book the cost and file the statutory returns, without re-keying.

### 6.1 Payslip

- **FR-41** One payslip per employee per run, in Vietnamese with English labels `[OPEN-05]`, showing: earnings by component, OT and night hours with amounts, each deduction, net pay, SI base, and paid and unpaid days (Labor Code Art. 95).
- **FR-42** Delivered as PDF; employees can see their own payslips if self-service is adopted (OPEN-01).

### 6.2 Payment

- **FR-43** Bank transfer file for net pay in the paying bank's format `[OPEN-06]`. Employees without a bank account are listed as an error before approval.

### 6.3 Accounting

- **FR-44** One journal entry per run, mapped from each component's account and the employee's department.

| Posting | Typical accounts |
| --- | --- |
| Salary cost | 622 production labour, 627 production overhead, 641 selling, 642 administration (by department) |
| Payable to employees | 334 |
| Employer and employee insurance, union fee | 3383 SI, 3384 HI, 3386 UI, 3382 union fee |
| PIT withheld | 3335 |

The mapping is configuration, so it follows the chart of accounts in use.

### 6.4 Statutory data

- **FR-45** SI: the monthly contribution list and the list of changes (joiners, leavers, base changes, long absences) in the form used for the SI agency's electronic filing `FLAG-TECH-03`.
- **FR-46** PIT: the data for the periodic withholding return, the annual finalisation for employees who authorise the company, and withholding certificates per employee.
- **FR-47** Union fee and union dues totals per month.

### 6.5 Reports

- **FR-48** Payroll register; cost by department and line; OT hours and cost against the legal limits; incentive cost; change against the previous month.
- **FR-49** Labour cost per period for the IE self-funding check (base wages, incentive paid, allowances).

## 7. Validations and controls

Checks run on every calculation; errors stop approval, warnings need a reviewer's note.

| Check | Level |
| --- | --- |
| Attendance or IE period for the month not closed | Error |
| Contract salary for full normal hours below the regional minimum wage | Error |
| Negative net pay | Error |
| Missing bank account, tax code or SI number for a paid employee | Error |
| Component without SI, OT or PIT flags | Error |
| OT hours above 40 in the month or 300 in the year | Warning |
| Net pay changed by more than `[P 30%]` from the previous month | Warning |
| Incentive units imported for an employee outside IE scope | Warning |
| Skill allowance past its review date | Warning |
| Dependent registration missing its document | Warning |

- **FR-50** Every change to pay data, inputs and payslips keeps who, when, old value and new value.
- **FR-51** A locked run, its payslips and their snapshots can never be changed or deleted.

## 8. Non-functional requirements

- **FR-52 Volume.** A full run for `[P 3,000]` employees calculates in under `[P 10 minutes]`; recalculating one payslip takes seconds.
- **FR-53 Reproducibility.** Any past payslip can be regenerated from its snapshot with the same result (FR-03, FR-10).
- **FR-54 Security.** Salary fields hidden from users outside the payroll roles, including in exports and list views; access to payroll data is logged.
- **FR-55 Language.** Interface and outputs in Vietnamese and English.
- **FR-56 Parameter changes without code.** A new minimum wage, reference level, tax table or rate is entered as a dated record by the payroll officer.
- **FR-57 Retention.** Payroll records kept for at least `[P 10 years]`, in line with accounting record rules.

## 9. Interfaces

| Direction | Partner | Data | When |
| --- | --- | --- | --- |
| Attendance → Payroll | Attendance module | Per employee per month: standard, paid and unpaid days; leave by type; OT and night hours by category; late arrivals and unexcused absences; OT hours year to date | At attendance close |
| IE → Payroll | IE module | Per operator per month: incentive units U; skill metrics for the skill-allowance review | At IE close |
| HR → Payroll | Employees and contracts | Pay profile, contract pay, dependents | Continuous |
| Payroll → Accounting | Odoo Accounting | Journal entry per run | On approval |
| Payroll → Bank | Paying bank | Transfer file | On approval |
| Payroll → SI and tax filing | SI agency and tax portals, via the filing tool in use | Contribution lists, changes, PIT returns and certificates | Monthly, quarterly, yearly |
| Payroll → IE | IE module | Labour cost per period for the self-funding check | After approval |

- **FR-58** Payroll reads only closed attendance and IE periods; it never changes their data.

## 10. Acceptance, open items and technical flags

**Acceptance.** The module is accepted when it reproduces the expected payslips in the payroll test cases to the dong, and every FR is covered by at least one case. The nine payslip profiles are the starting set; mid-month events (§5), the 14-day rule, the PIT methods and the validations (§7) each need their own cases.

### Open items

| ID | Item |
| --- | --- |
| OPEN-01 | Employee self-service for payslips: Odoo portal, Zalo OA message, or printed only |
| OPEN-02 | Whether travel and phone allowances are prorated by paid days |
| OPEN-03 | Confirm the 14-day no-contribution rule and its leave types against the SI Law 2024 and Decree 158/2025 |
| OPEN-04 | Month from which a changed SI base applies (change date, or the following month) |
| OPEN-05 | Payslip layout and language |
| OPEN-06 | Paying bank and its transfer file format |

### Technical flags

| ID | Flag |
| --- | --- |
| FLAG-TECH-01 | **OCA payroll fit-gap.** Decide whether to build on the OCA `payroll` module (structures, rules, categories) with generic rules driven by component flags, or to write dedicated models. Either way, salary rules must not hold amounts or classifications. |
| FLAG-TECH-02 | **Contract pay.** Replace the single `wage` field on `hr.contract` with grade, step and dated pay lines; keep `wage` filled from them for compatibility. |
| FLAG-TECH-03 | **Statutory files.** SI electronic declarations go through a licensed filing service; PIT returns through the tax portal. Decide between export files in their formats and a direct integration. |
| FLAG-TECH-04 | **Batch performance** for thousands of payslips: compute in bulk, not line by line through the ORM. |
| FLAG-TECH-05 | **Field-level security** on salary fields across forms, lists, exports and reports. |
