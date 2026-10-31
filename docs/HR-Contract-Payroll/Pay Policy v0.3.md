# Pay Policy

v0.3 · Oct 30, 2026 · @Peter

This policy sets the company's pay rules: what each employee group is paid, how each component is calculated, and how it is treated for social insurance (SI), overtime (OT) and personal income tax (PIT). It is the business input for the payroll module; the legal limits it works within are in the Vietnam Payroll Regulation Reference.

It has two layers (§2): the **current scheme**, which pays what employees are paid today and goes live with the module, and the **target policy**, the longer-term restructure, still undecided. v0.3 fixes the worker scheme: a base salary at the regional minimum plus **productivity pay**, a variable salary that replaces v0.2's skill pay, travel and housing support and OT supplement (§3). It also maps today's pay items into the scheme. Change log at the end.

Once in force, the current scheme becomes three official documents: the **salary scale and pay table** (Labor Code Art. 93), the **pay regulation** (quy chế lương) and the **bonus regulation** (Art. 104). Before they apply, the scale and the bonus regulation must be discussed with the worker representative organisation and published at the workplace.

**Conventions** (same as the IE spec)

- `[P]`: configurable parameter, stored with an effective date. Values are the current proposal.
- `[OPEN-n]`: undecided item, listed in §13. IDs from earlier versions are kept.
- Amounts are VND per month unless stated.

## 1. Scope

The policy covers the garment company's employees in four pay groups, plus owners and managers paid without a labour contract.

| Group | Who | Pay structure |
| --- | --- | --- |
| Workers | Sewing, cutting, finishing and helper roles on SAM-measured work | Base salary, productivity pay, efficiency bonus (§3) |
| Production support | Line leaders, line QC, feeders, mechanics (outside the IE incentive) | Grade salary (§4) |
| Office and management | QC staff and above, accounting, HR, planning, managers | Grade and step salary, KPI bonus (§4) |
| Daily-paid workers | Seasonal and short-term staff paid by the day | Daily rate (§5) |
| Owners and managers without a labour contract | Paid a salary, contributing as managers | Salary set by the owners; own contribution profile (§6) |

- **Pay period:** calendar month. **Payday:** `[P day 10 of the following month]`. No mid-month advance.
- **Workplace region:** phường Chi Lăng, An Giang, Region IV: minimum wage 3,700,000 a month from 1 Jan 2026.
- **Out of scope in v1:** the trading company's employees.

## 2. Actual pay, current scheme and target policy

The module must pay what employees are actually paid today; the scheme is the structure that justifies that pay, and it can be restructured later without changing the pay.

**Actual pay** is what workers have come to expect:

| | Entry worker | Skilled worker |
| --- | --- | --- |
| Monthly pay for a full month at normal output | 4,500,000 | 5,000,000 to 6,500,000 |
| Hourly base for OT | That amount ÷ 208 | That amount ÷ 208 |
| SI base | 3,700,000 | 3,700,000 |

**The current scheme** (§3–§11) pays exactly this at normal output. The company effectively started on 24 Oct 2026, so the scheme is written into new contract appendices (§3.6).

**The target policy** (§12) is the longer-term restructure, still undecided. The payroll module enforces neither layer: every classification is configuration, so moving from one to the other changes data, not code.

## 3. Current scheme for workers

Decided by Peter on 2026-10-30: option A of v0.2 (variable skill pay, SI base 3,700,000), with the 800,000 that v0.2 paid as travel and housing support folded into the same variable component.

### 3.1 Components

| Component | Amount `[P]` | SI base | OT base | PIT | Paid by |
| --- | --- | --- | --- | --- | --- |
| Base salary | 3,700,000 | Yes | Yes | Taxable | Paid days |
| Productivity pay | Level amount (§3.2) × attainment | No | Yes, at the amount earned | Taxable | Paid days and attainment |
| Efficiency bonus | IE units × rate; an entered amount until IE is live | No | No | Taxable | Monthly result |
| One-time bonus | Entered, approved by the director | No | No | Taxable | Per decision |
| Annual (13th-month) bonus | §9 | No | No | Taxable | Once a year |

- **Base salary** equals the Region IV minimum. When the minimum rises (proposed about 3.99M from 1 Jan 2027), the base rises with it, and the level amounts are reviewed then, by decision, not by formula.
- No travel or housing support, no OT supplement and no attendance bonus in the current scheme: none is part of today's pay. Each stays available as configuration (Requirements FR-63; target policy §12).

### 3.2 Productivity pay

```latex
\text{Productivity pay} = \text{level amount} \times \frac{\text{paid days}}{\text{standard days}} \times a
\qquad a = \min\!\left(1,\ \frac{\text{output}}{\text{target}}\right)
```

| Level | Level amount `[P]` | Full month at target output |
| --- | --- | --- |
| Entry | 800,000 | 4,500,000 |
| S1 | 1,300,000 | 5,000,000 |
| S2 | 1,800,000 | 5,500,000 |
| S3 | 2,300,000 | 6,000,000 |
| S4 | 2,800,000 | 6,500,000 |

- **Level:** HR certifies each worker's level and reviews it every `[P 6 months]`. IE skill data is a suggestion; the decision is HR's. New workers start at Entry.
- **Attainment a:** the month's output against target over the worker's **measured work**, capped at 100% `[P cap]`. Days on unmeasured work (training others, samples, off-site work, maintenance stops) are left out of both output and target, so they neither raise nor lower *a*. Absence does not lower *a* either; paid days handle it.
- **Measure until IE is live:** the piece counts already kept by hand for today's pieces pay, against a target per operation or line `[P]`, recorded per worker per month by the supervisor. **Once IE is live:** IE's monthly figures over net available minutes (IE spec §11), so off-standard time is already excluded `[OPEN-18]`.
- **Target:** set where an experienced worker at her certified level normally arrives, and **at or below the IE incentive threshold**, so that productivity pay covers output up to target and the efficiency bonus covers output above it, with no overlap `[OPEN-18]`.
- **Overrides:** HR may correct a month's attainment with a recorded reason (for example a machine breakdown not booked as off-standard). Overrides are visible in the run review.
- **OT base:** base salary + level amount × *a*. That is the month's actual wage for the job (Decree 145 Art. 55), so a worker at target earns OT on the full 4,500,000 to 6,500,000, as today.
- **SI base:** excluded, because it varies with productivity (Decree 158/2025 Art. 7). That holds only if it actually varies: a target that every worker always reaches turns it into a fixed amount, which belongs in the SI base. The module warns when a worker is paid at 100% for `[P 6]` months running (Requirements §7).

### 3.3 Worked examples

From the acceptance test cases (group G), full month unless stated.

| Case | Entry, at target (G01) | S4, at target (G02) | S4, a = 80% (G03) | Entry, 2 days absent (G04) |
| --- | --- | --- | --- | --- |
| Base salary | 3,700,000 | 3,700,000 | 3,700,000 | 3,415,385 |
| Productivity pay | 800,000 | 2,800,000 | 2,240,000 | 738,462 |
| OT (20 h or 30 h on workdays) | 649,038 | 1,406,250 | 1,285,096 | 649,038 |
| Efficiency bonus | 300,000 | 1,000,000 | 0 | 300,000 |
| Gross pay | 5,449,038 | 8,906,250 | 7,225,096 | 5,102,885 |
| Employee insurance (on 3,700,000) | 388,500 | 388,500 | 388,500 | 388,500 |
| Net pay | 5,060,538 | 8,517,750 | 6,836,596 | 4,714,385 |
| Employer cost | 6,318,538 | 9,775,750 | 8,094,596 | 5,972,385 |

At target, pay and OT match today's to the dong (4,500,000 ÷ 208 × 150% × 20 = 649,038). Annual leave and public holidays are paid days, so they cost the worker nothing (TC-G05).

### 3.4 Assessment

| Part | Strength | Risk |
| --- | --- | --- |
| Base at the minimum wage | Lawful | No headroom: it must follow each minimum-wage rise |
| Productivity pay | The law's own category for pay that counts for OT but not SI; one component instead of three | Holds only if it varies. If the target is never missed, it is a fixed amount and the SI base should include it, with back-payment and fines (Decree 274/2025) if an inspector finds so |
| Efficiency bonus | Art. 104 bonus above target | The bonus regulation must be written and published |
| SI base at 3,700,000 | Lawful for this structure | Workers' sickness, maternity and pension benefits follow 3,700,000, not their full pay |

This is an analysis of the rules for system design, not legal advice. The accountant or a labour lawyer reviews the pay regulation before workers sign.

### 3.5 What changes for workers

- **At normal output, nothing:** the same monthly pay and the same OT pay.
- **Below target, pay is lower**, down to the 3,700,000 base at zero attainment. This is the change the appendix must explain: today's 4,500,000 is in practice guaranteed; under the scheme, the part above 3,700,000 is earned by output.
- **Leave and holidays** are paid in full, as today.

### 3.6 Putting it in place

- **Contract appendix** for every worker: base salary 3,700,000; productivity pay at her certified level, with the attainment rule; the efficiency bonus and other bonuses by reference to the bonus regulation. Contract, SI declaration and payslip then agree.
- **Consent:** the appendix needs each worker's signature. Because the part above the base becomes output-dependent, explain the target and how attainment is measured, and show a payslip example.
- **Pay regulation and bonus regulation:** written, discussed with the worker representative organisation and published (Labor Code Arts. 93, 102, 104). The targets per operation or line are part of the pay regulation's annex.

### 3.7 Today's pay items in the scheme

| Today | Becomes |
| --- | --- |
| Base salary 4,500,000 and up | Base salary 3,700,000 + productivity pay at the worker's level |
| Pieces pay: per piece above a threshold, counted by hand | Efficiency bonus: entered amount until IE is live, then IE units × rate |
| Bonus hours: off-site work and forgotten scans | Not a pay item. Attendance corrections and off-site work registrations (Attendance §5.4, §8.3); the hours are then paid as normal time or OT |
| Bonus pay: paid holidays | Attendance: the public holiday status counts as paid days |
| Bonus pay: director-approved one-time bonus, project completion bonus | One-time bonus (§3.1), with the approver recorded |
| Bonus pay: 13th-month bonus | Annual bonus (§9) |
| Bonus pay: uniform deductions | Damage compensation for unreturned company property, after the work-rules process (§10) |
| Skill bonus on skill levels (`x_bonus_amount`) | Productivity pay levels S1–S4 |

## 4. Current scheme for production support, office and management

These roles stay on the salary scale of v0.1 §4 until the target policy is decided: the **grade** says what the job is worth, the **step** where the person stands in it.

| Grade | Typical roles | Step 1 | Step 2 | Step 3 |
| --- | --- | --- | --- | --- |
| G1 Support | Line QC, feeder, mechanic | 5,500,000 | 6,000,000 | 6,500,000 |
| G2 Supervision | Line leader | 7,500,000 | 8,000,000 | 8,500,000 |
| G3 Staff | QC staff, accounting staff | 9,000,000 | 10,000,000 | 11,000,000 |
| G4 Senior staff | QC senior, senior accountant | 13,000,000 | 14,000,000 | 15,000,000 |
| G5 Department head | QC manager, chief accountant | 16,000,000 | 17,000,000 | 18,000,000 |
| G6 Senior management | Factory manager, general manager | Individual | Individual | Individual |

- **Line leaders are G2** (decided, Peter 2026-10-30): outside the IE incentive, paid by grade.
- Grade salary is in both the SI and the OT base. Duty allowances per duty `[P]` and the phone lump-sum per role `[P]` apply as in v0.1 §3.3 and §4.4. The KPI bonus is an Art. 104 bonus `[OPEN-08]`. One-time and annual bonuses as for workers.
- How these roles are paid and declared for SI today, and whether the scale above matches it, is `[OPEN-14]`. The amounts are placeholders until then.

## 5. Daily-paid workers

- Paid a daily rate `[P]` × paid days. A daily rate must be at least the hourly minimum wage (17,800) × the day's normal hours.
- OT hourly base = daily rate ÷ 8, at the statutory factors.
- No productivity pay `[OPEN-15]`.
- Contracts of 1 month or more join SI, HI and UI; the base for a daily-paid contract is the time-based monthly wage it implies `[to confirm with the SI office]`.
- PIT: flat 10% on payments of 5,000,000 or more for contracts under 3 months, unless the employee has filed the commitment form.

## 6. Owners and managers without a labour contract

- Salary set by the owners, entered on the person's pay profile.
- They contribute as enterprise managers: SI and HI, no UI, on a declared base `[P per person]` that need not equal the salary paid, floored at the reference level `[to confirm with the SI office]`.
- PIT on the salary as employment income, progressive, with family deductions.
- Everything that differs from an employee lives in the person's contribution profile; no special pay rule is needed.

## 7. Attendance and paid days

Everyone is paid by the same formula; only the source of days differs between groups.

```latex
\text{Salary for the month} = \text{salary} \times \frac{\text{paid days}}{\text{standard days}}
```

- **Standard days:** `[P 26]`, fixed, as in today's contracts. The module can instead use each month's scheduled working days; changing it needs the employees' consent, because it changes pay.
- **Paid days** = days worked (including registered off-site work) + paid leave days + public holidays on working days + statutory paid break minutes, less late minutes beyond the grace period (Attendance §9).
- **Unpaid days** (unpaid leave, unexcused absence) and SI-paid leave (sickness, sick child, maternity) reduce paid days; the SI fund pays the SI-paid leave.
- Sources of days: scans for workers, daily-paid and production support; calendar and registered leave for office and management.

## 8. Overtime and night work

OT is paid on the OT base at the statutory rates, for hours approved in advance and attended.

```latex
\text{OT pay} = \frac{\text{OT base}}{208} \times \text{factor} \times \text{hours}
```

| Situation | Factor |
| --- | --- |
| OT on a workday | 150% |
| OT on a weekly rest day | 200% |
| OT on a public holiday or paid leave day | 300% |
| Normal hours at night (22:00–06:00) | +30% |
| Night OT, workday | 200%; 210% after daytime OT that day |
| Night OT, rest day / holiday | 270% / 390% |

- **OT base** = the components flagged *in OT base*: base salary + productivity pay earned for workers (§3.2); grade salary and duty allowances for other roles. Bonuses and welfare items are excluded. The OT base is not prorated by paid days.
- **Paid OT hours** = the lower of approved and attended OT hours. Approval records the employee's agreement.
- **Hour limits:** 40 hours a month and 300 hours a year (textile and garment); the attendance system blocks requests beyond them by default. Notify the provincial labour authority within 15 days of passing 200 hours a year.
- OT worked beyond the limits is still paid; the excess is taxable.
- Office and management roles are eligible when approved `[OPEN-10]`.

## 9. Welfare, annual bonus and other benefits

| Benefit | Who | Amount | Notes |
| --- | --- | --- | --- |
| Canteen meal | All | In kind | Not on the payslip; PIT-free |
| Childcare support | Workers with children under 6 | `[P]` | Whether to offer it `[OPEN-11]` |
| Life-event support (wedding, bereavement, sickness) | All | `[P]` per event | Outside SI and OT |
| Annual (13th-month, Tet) bonus | All | `[P about one month's salary]`, scaled by months worked in the year | Art. 104 bonus, in the bonus regulation |
| One-time bonus (project completion, director's award) | Named employees | Per decision | Art. 104 bonus; each payment records the approver |

- No cash meal allowance: meals are provided in kind.

## 10. Deductions and contributions

Only statutory deductions, union dues for members and damage compensation may be taken from pay (Labor Code Art. 102). Fines are forbidden (Art. 127).

| Item | Employee | Employer | Base |
| --- | --- | --- | --- |
| Social insurance | 8% | 17.5% | SI base, capped at 20 × reference level |
| Health insurance | 1.5% | 3% | SI base, same cap |
| Unemployment insurance | 1% | 1% | SI base, capped at 20 × regional minimum wage |
| Union fee | – | 2% | SI base; owed with or without a grassroots union |
| Union dues | 0.5%, members only, capped `[P 253,000]` | – | SI base |
| Personal income tax | Withheld monthly | – | Taxable income after deductions |
| Damage compensation | At most 30% of the month's pay after insurance and PIT | – | Work-rules decision (Art. 129) |

- **SI base** = the components flagged *in SI base*, never below the regional minimum wage, from each person's contribution profile. Probation *contracts* are outside compulsory SI; probation written into a labour contract is not.
- **Union:** there is no grassroots union yet, so no employee is a member and no dues are deducted. Membership is a flag on the employee, ready for when a union is formed. The 2% employer fee applies now.
- **Uniforms:** a uniform is company property issued for work. The work rules require its return on leaving and set its value per set `[P]`. A uniform not returned is a loss of company property: after the work-rules process, the decided amount is deducted as damage compensation, within the 30% cap, with any excess carried to the next payment. A charge made *because* the worker resigned early is a penalty and is not deducted.
- **PIT:** the employee registers dependents with HR; the company withholds monthly and handles year-end finalisation for employees who authorise it.
- No other deductions are taken from pay.

## 11. Pay administration

Each month's pay is calculated from closed attendance and IE figures, approved, then paid by bank transfer with a written payslip.

- **Probation:** at least 85% of the salary for the job `[P 85%]`, for no longer than the law allows for the job (Labor Code Art. 25): 6 working days for jobs without a required qualification, 30 days for jobs needing vocational or technical qualifications, 60 days for jobs needing a college degree or higher, 180 days for enterprise managers. A separate probation contract has no compulsory SI; a probation clause inside the labour contract does. For workers, 85% applies to the base salary and the Entry productivity amount.
- **Monthly close:** attendance exceptions cleared, OT approvals complete, attainment recorded for every worker, IE incentive units final before calculation. Payroll is reviewed by HR and approved by `[P director]` before payment.
- **Payslip:** every employee receives a written payslip each month showing each earning, the attainment behind productivity pay, OT and night pay, each deduction and net pay (Art. 95).
- **Payment:** by bank transfer on payday. Cash payments of 5,000,000 or more are not deductible for corporate income tax.
- **Corrections:** an error found after payment is corrected in the next month's payroll as a separate line, with the period it belongs to. Closed months are not recalculated.
- **Leavers:** final pay, including the partial month's productivity pay and efficiency bonus and pay for untaken annual leave (contract salary of the previous month ÷ standard days, per day), within 14 working days of the last day. Unreturned uniforms per §10.
- **Go-live:** the first month calculated in the module is `[OPEN-16]`. Pay before it, from 24 Oct 2026, is calculated outside the module; its year-to-date figures (OT hours, taxable income, PIT withheld, leave balances) are loaded as opening data.
- **Changes to this policy** follow the same consultation and publication as the original. Parameter values change by effective date and are kept in the module's history.

## 12. Target policy (undecided)

The direction from v0.1 stays the reference for a later restructure, once workers' expectations and the legal position are weighed:

- One worker base salary at or above the minimum with headroom (v0.1 §3.1), a skill allowance as a fixed allowance, the efficiency incentive as an Art. 104 bonus, and an attendance bonus `[P 300,000]` conditional on no unexcused absence and at most `[P 2]` late arrivals (v0.1 §3.5) `[OPEN-05]`.
- A salary scale with job evaluation for all non-worker roles (v0.1 §4).
- Every pay item classified by its nature.

The module supports this policy without code changes; the acceptance test cases in groups A–F are written against it, to prove the engine.

## 13. Open decisions

| ID | Decision | Current proposal |
| --- | --- | --- |
| OPEN-01 | Role bonus for production support | Not in v1; a new component later |
| OPEN-02 | One worker base salary, or one per work area | One base salary |
| OPEN-03 | Level criteria, review cycle and downgrade rule | HR decides; IE data as a suggestion; 6-month review |
| OPEN-04 | Incentive rate per unit, and whether it is one rate for all | One rate, set from shadow-mode data and the self-funding report |
| OPEN-05 | Attendance bonus: whether and when to introduce it | Target policy only; not in the current scheme |
| OPEN-06 | Job evaluation method and grade boundaries | Simple four-factor scoring |
| OPEN-07 | Line leaders as a grade or as workers with a duty allowance | **Decided: grade G2** (Peter, 2026-10-30) |
| OPEN-08 | KPI bonus period and size | Monthly or quarterly, capped at a share of grade salary |
| OPEN-09 | Standard days: fixed 26, or the month's scheduled days | **Fixed 26 for now**; the module supports both (Peter, 2026-10-30) |
| OPEN-10 | OT eligibility for office and management | Eligible when approved; management may be excluded |
| OPEN-11 | Childcare support for workers with young children | To decide |
| OPEN-12 | How today's pay items map into the current scheme | **Decided** (§3.7; Peter, 2026-10-30) |
| OPEN-13 | Travel and housing support basis | **Withdrawn**: no support in the current scheme |
| OPEN-14 | How production support, office and management are paid and declared for SI today | From the accountant's payroll sheet |
| OPEN-15 | Whether daily-paid workers get productivity pay | No: daily rate and statutory OT only |
| OPEN-16 | First month calculated in the module | After the module passes the acceptance cases and one parallel month |
| OPEN-17 | Worker scheme: option A or option B | **Decided: option A, as productivity pay** (Peter, 2026-10-30) |
| OPEN-18 | Targets per operation or line, the attainment measure before and after IE, and the full-pay point against the IE incentive threshold | Hand piece counts against line targets until IE; then IE's monthly figures; target at or below the IE threshold |
| OPEN-19 | Level amounts and the uniform value per set | Entry 800,000; S1–S4 in 500,000 steps to 2,800,000; uniform value from purchase cost |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-29 | First draft (filed as "Pay Policy Draft v0.1"). |
| 0.2 | 2026-10-30 | Actual pay, current scheme and target policy; worker options A and B; daily-paid; owners and managers; Region IV; line leaders G2; OT supplement; union position; probation limits; go-live. |
| 0.3 | 2026-10-30 | Option A decided, as **productivity pay**: Entry 800,000 to S4 2,800,000 × paid days × attainment, in the OT base at the amount earned, outside the SI base (§3.1–§3.6). Travel and housing support, OT supplement and attendance bonus removed from the current scheme (the attendance bonus moves to the target policy). Today's pay items mapped (§3.7). One-time bonus added (§3.1, §9). Uniforms handled as damage compensation for unreturned property; fines excluded (§10). Off-site work counts as days worked (§7). Probation rate applies to the Entry productivity amount (§11). OPEN-12 and OPEN-17 decided; OPEN-13 withdrawn; OPEN-05 and OPEN-15 reworded; OPEN-18 and OPEN-19 added. |
