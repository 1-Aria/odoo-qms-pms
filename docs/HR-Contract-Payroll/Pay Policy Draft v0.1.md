# Pay Policy Draft

Oct 29, 2026 · @Peter

This policy sets the company's pay rules: what each employee group is paid, how each component is calculated, and how it is treated for social insurance (SI), overtime (OT) and personal income tax (PIT). It is the business input for the payroll module; the legal limits it works within are in the Vietnam Payroll Regulation Reference.

Once the open decisions (§10) are settled, this draft becomes three official documents: the **salary scale and pay table** (Labor Code Art. 93), the **pay regulation** (quy chế lương) and the **bonus regulation** (Art. 104). Before they apply, the scale and the bonus regulation must be discussed with the worker representative organisation and published at the workplace.

**Conventions** (same as the IE spec)

- `[P]`: configurable parameter. Values are illustrative placeholders, stored with an effective date.
- `[OPEN-n]`: undecided item, listed in §10.
- Amounts are VND per month unless stated.

## 1. Scope

The policy covers all employees on labour contracts, in three groups with different pay structures.

| Group | Who | Pay structure |
| --- | --- | --- |
| Workers | Sewing, cutting, finishing and helper roles on SAM-measured work | One base salary, optional skill allowance, efficiency incentive |
| Production support | Line leaders, line QC, feeders, mechanics (outside the IE incentive) | Grade salary; role bonus to be designed later `[OPEN-01]` |
| Office and management | QC staff and above, accounting, HR, planning, managers | Grade and step salary, KPI bonus |

- **Pay period:** calendar month.
- **Payday:** once a month, on a fixed day `[P day 10 of the following month]`. No mid-month advance.
- **Workplace region:** Region IV, regional minimum wage 3,700,000 from 1 Jan 2026.

## 2. Pay components

Every payment belongs to one component, and each component has one fixed treatment. The payroll module stores these flags on the component, so salary rules never decide classification themselves.

| Component | Groups | Legal nature | SI base | OT base | PIT |
| --- | --- | --- | --- | --- | --- |
| Base salary | Workers | Salary by job | Yes | Yes | Taxable |
| Grade salary | Support, office, management | Salary by job or title | Yes | Yes | Taxable |
| Skill allowance | Workers | Fixed allowance (job complexity) | Yes | Yes | Taxable |
| Duty allowance | Anyone holding a concurrent duty | Fixed allowance (responsibility) | Yes | Yes | Taxable |
| Efficiency incentive | Workers on SAM work | Bonus, Art. 104 | No | No | Taxable |
| KPI bonus | Office and management | Bonus, Art. 104 | No | No | Taxable |
| Attendance bonus | Workers | Bonus, conditional | No | No | Taxable |
| Annual (Tet) bonus | All | Bonus, Art. 104 | No | No | Taxable |
| Overtime and night pay | All | Statutory premium pay | No | – | Free within legal hour caps |
| Travel allowance | Workers | Welfare support | No | No | Taxable |
| Phone lump-sum | Office roles that need it | Lump-sum per company rule | No | No | Free within the company rule |
| Canteen meal | All | Welfare in kind | No | No | Free (not on payslip) |
| Paid leave and holiday pay | All | Salary for paid days | – | – | Taxable |

Adding a component later (for example a role bonus for line leaders) means adding a row here with its flags, not new calculation logic.

## 3. Worker pay

Workers share one base salary; the efficiency incentive is the main variable part, and the skill allowance is a stable extra for the few workers HR decides to recognise.

```latex
\text{Worker pay} = \text{base} \times \frac{\text{paid days}}{\text{standard days}} + \text{allowances} + \text{incentive} + \text{attendance bonus} + \text{OT pay}
```

### 3.1 Base salary

- One amount for all workers `[P 4,500,000]`, at or above the regional minimum wage.
- Keep headroom for minimum-wage increases; a proposed rise of about 7.8% from 1 Jan 2027 would take Region IV to roughly 3.99M.
- Separate base amounts by work area (sewing, cutting, finishing) are possible but not planned `[OPEN-02]`.

### 3.2 Skill allowance

A fixed monthly allowance that rewards proven skill and versatility independent of output, for example a highly skilled operator placed on low-volume or training work.

| Level | Amount `[P]` |
| --- | --- |
| S1 | 500,000 |
| S2 | 1,000,000 |
| S3 | 1,500,000 |

- **Decision:** HR grants, changes or removes the level. IE skill data (ILUO levels, tier, skill metrics) is a suggestion only.
- **Review:** every `[P 6 months]`. A level is removed or lowered only after `[P two]` consecutive reviews below its criteria `[OPEN-03]`.
- **Contract:** the level, amount and review rule are stated in a contract appendix, so a change after a review follows the contract.
- Fixed between reviews and tied to job complexity, so it is treated as part of the SI base and the OT base.

### 3.3 Duty allowance

- Paid while an employee holds a duty on top of their own job, such as acting line leader, deputy or safety officer. It stops when the duty ends; salary is unchanged.
- Amounts per duty in a table `[P]`. Full-time roles get a grade instead (§4).

### 3.4 Efficiency incentive

```latex
\text{Incentive} = U \times \text{rate per unit}
```

- **U** = payable incentive units for the month from the IE module (excess incentive minutes × tier multiplier). All rules for U are in the IE Business Logic Spec.
- **Rate per unit** `[P 1,500 VND]`, one rate for all workers `[OPEN-04]`. Checked against the IE self-funding report.
- Classified as a bonus under Art. 104: it depends on output and quality and is zero below the threshold. It is not part of the SI base or the OT base, and no OT premium applies to it.
- **Transition:** until the IE incentive is switched on after shadow mode, the current efficiency bonus is paid as an entered amount under the same classification.

### 3.5 Attendance bonus

- `[P 300,000]` for a month with no unexcused absence and no more than `[P 2]` late arrivals `[OPEN-05]`.
- Statutory paid leave (annual leave, public holidays, marriage and bereavement leave) and SI-paid leave (sickness, maternity) do not forfeit it. Penalising these risks a discrimination finding.
- The IE eligibility flag is not used in v1, so one absence is not penalised twice.

## 4. Production support, office and management pay

These roles are paid from a salary scale: the **grade** says what the job is worth, the **step** says where the person stands in it.

### 4.1 Grades

- Each role is placed in a grade by job evaluation on four factors: knowledge, complexity, responsibility and working conditions `[OPEN-06]`.
- Each grade has `[P 3]` steps. The amounts below are illustrative, taken from the payslip profiles.

| Grade | Typical roles | Step 1 | Step 2 | Step 3 |
| --- | --- | --- | --- | --- |
| G1 Support | Line QC, feeder, mechanic | 5,500,000 | 6,000,000 | 6,500,000 |
| G2 Supervision | Line leader | 7,500,000 | 8,000,000 | 8,500,000 |
| G3 Staff | QC staff, accounting staff | 9,000,000 | 10,000,000 | 11,000,000 |
| G4 Senior staff | QC senior, senior accountant | 13,000,000 | 14,000,000 | 15,000,000 |
| G5 Department head | QC manager, chief accountant | 16,000,000 | 17,000,000 | 18,000,000 |
| G6 Senior management | Factory manager, general manager | Individual | Individual | Individual |

- Line leaders do not produce SAM output and are outside the IE incentive, so they are placed in a grade rather than paid as workers with a duty allowance `[OPEN-07]`.
- G6 salaries are set individually in the contract.

### 4.2 Steps

- New hires start at step 1 unless HR records a reason for a higher step.
- Moving up a step follows an annual review `[P]`. Steps do not move down; a lower salary needs a new agreement with the employee.

### 4.3 KPI bonus

- Paid on KPI results under the bonus regulation, as an Art. 104 bonus outside the SI and OT bases.
- Period and size `[OPEN-08]`, for example monthly or quarterly, up to `[P 20%]` of grade salary.

### 4.4 Allowances

- Duty allowances as in §3.3.
- Phone lump-sum for roles that need it, per a company rule that sets the amount per role `[P]`.

## 5. Attendance and paid days

Everyone is paid by the same formula; only the source of days worked differs between groups.

```latex
\text{Salary for the month} = (\text{salary} + \text{fixed allowances}) \times \frac{\text{paid days}}{\text{standard days}}
```

- **Standard days:** `[P 26]` working days a month, 8 hours a day, under the company's work rules `[OPEN-09]`.
- **Paid days** = days worked + paid leave days + public holidays falling on working days.
- **Unpaid days** (unpaid leave, unexcused absence) reduce paid days. SI-paid leave (sickness, maternity) is unpaid by the company; the SI fund pays the employee.

|  | Workers and production support | Office and management |
| --- | --- | --- |
| Source of days worked | Attendance scans | Assumed present unless leave is registered |
| Scanning | Required; drives pay | Required for discipline; does not drive pay |
| Leave | Registered and approved in the system | Registered and approved in the system |
| OT | Approved in advance and scanned (§6) | Approved in advance and scanned (§6) |

- Attendance is the master clock for both payroll and IE. Its rules (shifts, rounding, missing scans, late arrival) belong in a separate attendance spec shared by both modules.
- Missing or doubtful scans are corrected by the supervisor before payroll close; payroll uses only closed attendance.

## 6. Overtime and night work

OT is paid on salary and fixed allowances only, at the statutory rates, for hours that were both approved in advance and attended.

```latex
\text{Hourly rate} = \frac{\text{salary} + \text{skill allowance} + \text{duty allowance}}{208}
```

| Situation | Rate |
| --- | --- |
| OT on a workday | 150% |
| OT on a weekly rest day | 200% |
| OT on a public holiday or paid leave day | 300% |
| Normal hours at night (22:00–06:00) | +30% |
| OT at night | OT rate + 30% + 20% of the day-time rate for that day type |

- **OT base** excludes the efficiency incentive, KPI bonus, attendance bonus, annual bonus and welfare items (§2).
- **Paid OT hours** = the lower of approved and attended OT hours. Approval records the employee's agreement.
- **Hour limits:** 40 hours a month and 300 hours a year (textile and garment). The provincial labour authority is notified in writing within 15 days of passing 200 hours a year.
- OT beyond the limits is not planned. If it happens, it is still paid at the statutory rate, and the excess is taxable.
- Office and management roles are eligible for OT when approved `[OPEN-10]`.

## 7. Welfare, annual bonus and other benefits

Welfare items stay outside the SI and OT bases; the canteen meal is also fully tax-free because it is provided in kind.

| Benefit | Who | Amount | Notes |
| --- | --- | --- | --- |
| Canteen meal | All | In kind | Not on the payslip |
| Travel allowance | Workers | `[P 200,000]` | Taxable |
| Childcare support | Workers with children under 6 | `[P]` | Whether to offer it `[OPEN-11]` |
| Life-event support (wedding, bereavement, sickness) | All | `[P]` per event | Outside SI and OT |
| Annual (Tet) bonus | All | `[P about one month's salary]`, scaled by months worked in the year | Art. 104 bonus, based on business results |

- The annual bonus and its conditions go in the bonus regulation together with the efficiency incentive and the KPI bonus.
- Cash meal allowances are not planned; if added, up to 1,200,000 a month is PIT-free.

## 8. Deductions and contributions

Only statutory deductions, union dues for members and damage compensation may be taken from pay.

| Item | Employee | Employer | Base |
| --- | --- | --- | --- |
| Social insurance | 8% | 17.5% | SI base, capped at 20 × reference level |
| Health insurance | 1.5% | 3% | SI base, same cap |
| Unemployment insurance | 1% | 1% | SI base, capped at 20 × regional minimum wage |
| Union fee | – | 2% | SI base |
| Union dues | 0.5%, members only, capped at 10% of base salary | – | SI base |
| Personal income tax | Withheld monthly | – | Taxable income after deductions |

- **SI base** = salary + skill allowance + duty allowance, never below the regional minimum wage. Probation contracts are outside compulsory SI.
- **PIT:** the employee registers dependents with HR; the company withholds monthly and handles year-end finalisation for employees who authorise it.
- **Damage compensation** for lost or damaged company property may be deducted only after the process in the work rules, and at most 30% of the month's pay after SI and PIT.
- No other deductions (fines, uniform charges) are taken from pay.

## 9. Pay administration

Each month's pay is calculated from closed attendance and IE figures, approved, then paid by bank transfer with a written payslip.

- **Probation:** at least 85% of the salary for the job `[P 85%]`; no compulsory SI during probation.
- **Monthly close:** attendance exceptions cleared, OT approvals complete and IE incentive units final before calculation. Payroll is reviewed by HR and approved by `[P director]` before payment.
- **Payslip:** every employee receives a written payslip each month showing each earning, OT and night pay, each deduction and net pay (Art. 95). The structure follows §2.
- **Payment:** by bank transfer on payday. Cash payments of 5,000,000 or more are not deductible for corporate income tax.
- **Corrections:** an error found after payment is corrected in the next month's payroll as a separate line, with the period it belongs to. Closed months are not recalculated.
- **Leavers:** final pay, including the incentive for the partial month and pay for untaken annual leave, within 14 working days of the last day.
- **Changes to this policy** follow the same consultation and publication as the original. Parameter values `[P]` change by effective date and are kept in the module's history.

## 10. Open decisions

| ID | Decision | Current proposal |
| --- | --- | --- |
| OPEN-01 | Role bonus for production support (line leaders, line QC, feeders, mechanics, cutting) | Not in v1; can be added as a new component later |
| OPEN-02 | One worker base salary, or one per work area | One base salary |
| OPEN-03 | Skill allowance criteria per level, review cycle and downgrade rule | HR decides; IE data as a suggestion; 6-month review; downgrade after two reviews |
| OPEN-04 | Incentive rate per unit, and whether it is one rate for all | One rate, set from shadow-mode data and the self-funding report |
| OPEN-05 | Attendance bonus amount and conditions (absences, late arrivals) | No unexcused absence, at most 2 late arrivals |
| OPEN-06 | Job evaluation method and grade boundaries | Simple four-factor scoring |
| OPEN-07 | Line leaders as a grade (G2) or as workers with a duty allowance | Grade, since they are outside the IE incentive |
| OPEN-08 | KPI bonus period and size | Monthly or quarterly, capped at a share of grade salary |
| OPEN-09 | Standard days: fixed 26, or the actual working days of each month | Fixed 26 |
| OPEN-10 | OT eligibility for office and management | Eligible when approved; management roles may be excluded |
| OPEN-11 | Childcare support for workers with young children | To decide |

**Next documents:** the attendance spec shared with IE, then the payroll requirements spec, with the payslip profiles turned into test cases.
