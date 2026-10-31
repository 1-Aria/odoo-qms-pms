# Pay Policy

v0.2 · Oct 30, 2026 · @Peter

This policy sets the company's pay rules: what each employee group is paid, how each component is calculated, and how it is treated for social insurance (SI), overtime (OT) and personal income tax (PIT). It is the business input for the payroll module; the legal limits it works within are in the Vietnam Payroll Regulation Reference.

v0.2 separates two layers (§2): the **current scheme**, which pays what employees are paid today and goes live with the module, and the **target policy**, the longer-term restructure, which is still undecided. For workers, the current scheme has two options, A and B, for Peter to decide with the accountant (§3). Change log at the end.

Once decided, the current scheme becomes three official documents: the **salary scale and pay table** (Labor Code Art. 93), the **pay regulation** (quy chế lương) and the **bonus regulation** (Art. 104). Before they apply, the scale and the bonus regulation must be discussed with the worker representative organisation and published at the workplace.

**Conventions** (same as the IE spec)

- `[P]`: configurable parameter, stored with an effective date. Values are the current proposal.
- `[OPEN-n]`: undecided item, listed in §13. IDs from v0.1 are kept.
- Amounts are VND per month unless stated.

## 1. Scope

The policy covers the garment company's employees in four pay groups, plus owners and managers paid without a labour contract.

| Group | Who | Pay structure |
| --- | --- | --- |
| Workers | Sewing, cutting, finishing and helper roles on SAM-measured work | Base salary, skill pay, travel and housing support, efficiency bonus (§3) |
| Production support | Line leaders, line QC, feeders, mechanics (outside the IE incentive) | Grade salary (§4) |
| Office and management | QC staff and above, accounting, HR, planning, managers | Grade and step salary, KPI bonus (§4) |
| Daily-paid workers | Seasonal and short-term staff paid by the day | Daily rate (§5) |
| Owners and managers without a labour contract | Paid a salary, contributing as managers | Salary set by the owners; own contribution profile (§6) |

- **Pay period:** calendar month. **Payday:** `[P day 10 of the following month]`. No mid-month advance.
- **Workplace region:** phường Chi Lăng, An Giang, Region IV: minimum wage 3,700,000 a month from 1 Jan 2026.
- **Out of scope in v1:** the trading company's employees.

## 2. Actual pay, current scheme and target policy

The module must pay what employees are actually paid today; the scheme is the structure that justifies that pay, and it can be restructured later without changing the pay.

**Actual pay** is what workers have come to expect, and it is fixed for now:

| | Entry worker | Skilled worker |
| --- | --- | --- |
| Monthly pay for a full month | 4,500,000 | 6,000,000 to 6,500,000 |
| Hourly base for OT | That full amount ÷ 208 | That full amount ÷ 208 |
| SI base | 3,700,000 | 3,700,000 (option A) or with the skill amount (option B) |

**The current scheme** (§3–§11) pays exactly this, with a structure chosen to be as consistent with the law as the pay allows. The company effectively started on 24 Oct 2026, so the scheme is written into new contract appendices; because pay does not change, the employees' consent is the main step (§3.6).

**The target policy** (§12) is the longer-term restructure, still undecided, because it involves what the law allows, what workers expect and what they want. The payroll module enforces neither layer: every classification is configuration, so moving from one to the other changes data, not code.

## 3. Current scheme for workers

### 3.1 Components common to both options

| Component | Amount `[P]` | SI base | OT base | PIT | Paid by |
| --- | --- | --- | --- | --- | --- |
| Base salary | 3,700,000 | Yes | Yes | Taxable | Paid days |
| Travel and housing support | 800,000 | No | No | Taxable | Days worked `[OPEN-13]` |
| OT supplement | 3,846 per OT hour × the OT factor | No | – | As OT | OT hours |
| Efficiency bonus | IE units × rate; an entered amount until IE is live | No | No | Taxable | Monthly result |
| Attendance bonus | 300,000 | No | No | Taxable | No unexcused absence and at most `[P 2]` late arrivals in the month; statutory and SI-paid leave do not forfeit it `[OPEN-05]` |

- **Base salary** equals the Region IV minimum. When the minimum rises (proposed about 3.99M from 1 Jan 2027), the base must rise with it. The support is not reduced by a formula to compensate: an amount defined as "4,500,000 minus the base" would itself show that it is salary.
- **Travel and housing support** is welfare support on the list excluded from both bases (Decree 145 Art. 55; Official Letter 1198). It is the same for every worker, written in the pay regulation as support for coming to work and for housing, and paid per day worked: 800,000 ÷ 26 a day. It is not called a meal allowance, because workers eat in the canteen, and a cash meal allowance on top of a meal in kind is visibly not meal support.
- **OT supplement:** the company pays OT above the statutory rate. On top of the statutory OT pay on the OT base, each OT hour earns 3,846 × the hour's factor (150%, 200%, 300%, and the night factors). 3,846 is 800,000 ÷ 208, so OT pays what it paid when the 800,000 was part of the base. Its PIT treatment follows OT `[to confirm with the tax advisor]`.
- **Efficiency bonus:** the IE efficiency incentive (§3.4 of v0.1) once IE leaves shadow mode. Until then, the current efficiency bonus is entered per worker under the same component. How today's pieces pay, bonus hours and bonus pay map into it is `[OPEN-12]`.

### 3.2 Option A: skill performance pay (variable)

| Component | Amount `[P]` | SI base | OT base | PIT | Paid by |
| --- | --- | --- | --- | --- | --- |
| Skill performance pay | S1 500,000 · S2 1,000,000 · S3 1,500,000 · S4 2,000,000 | No | **Yes** | Taxable | Paid days, and the month's condition |

- **Level:** HR certifies each worker's level. IE skill data is a suggestion; the decision is HR's.
- **Monthly condition:** the level's amount is paid for a month only when the worker performed at her certified level that month. If she performed at a lower level, the month pays that level, or nothing. Until IE is live, the evidence is the supervisor's monthly skill confirmation; once IE is live, it is IE's monthly figures, which HR confirms or overrides with a recorded reason.
- **Why it sits in the OT base but not the SI base:** salary for the job that varies with productivity or quality is excluded from the SI base (Decree 158/2025 Art. 7) but included in the OT base (Decree 145 Art. 55). It is the only lawful category with that treatment, and it holds only if the pay actually varies.

### 3.3 Option B: skill allowance (fixed)

| Component | Amount `[P]` | SI base | OT base | PIT | Paid by |
| --- | --- | --- | --- | --- | --- |
| Skill allowance | S1 500,000 · S2 1,000,000 · S3 1,500,000 · S4 2,000,000 | **Yes** | Yes | Taxable | Paid days |

- HR grants, changes or removes the level after a review every `[P 6 months]`; IE skill data is a suggestion (v0.1 §3.2, unchanged).
- A fixed allowance for skill or job complexity is named in the SI base by Decree 158/2025 Art. 7, so option B is the classification that matches its nature.

### 3.4 What the options cost

Figures from the acceptance test cases (TC-G01 to TC-G04), for a full month with 20 or 30 OT hours.

| | Entry worker (A = B) | S4 worker, option A | S4 worker, option B |
| --- | --- | --- | --- |
| Gross pay | 5,749,034 | 9,206,243 | 9,206,243 |
| SI base | 3,700,000 | 3,700,000 | 5,700,000 |
| Employee insurance | 388,500 | 388,500 | 598,500 |
| Net pay | 5,360,534 | 8,817,743 | 8,607,743 |
| Employer cost | 6,618,534 | 10,075,743 | 10,545,743 |
| Maternity benefit, 6 months at 100% of the SI base | 22,200,000 | 22,200,000 | 34,200,000 |

- Option B costs the employer 23.5% of the skill amount (352,500 a month at S3, 470,000 at S4) and the worker 10.5% (210,000 at S4).
- In return, the worker's sickness, maternity and pension benefits follow the higher base. With a mostly female workforce, the maternity row is the one workers will notice.

### 3.5 Assessment

| Part | Strength | Risk |
| --- | --- | --- |
| Base at the minimum wage | Lawful | No headroom: it must follow each minimum-wage rise |
| Travel and housing support, per day worked | Defensible: excluded items, paid for coming to work | The weakest part in any option. It is a uniform amount that used to be part of the base; if an inspector judges it to be salary, the company owes back-payment with interest (Decree 274/2025) and fines |
| OT supplement | Sound: paying above the statutory OT rate is lawful | PIT treatment to confirm |
| Skill pay, option A | Lawful if it varies | It must be lost in months the level is not met, and that has to happen. If it is in practice always paid, it is a fixed allowance and belongs in the SI base |
| Skill pay, option B | Matches its nature | Costs more SI |
| Efficiency and attendance bonuses | Sound: Art. 104 bonus and a genuine condition | None beyond the bonus regulation being written and published |

This is an analysis of the rules for system design, not legal advice. The accountant or a labour lawyer reviews the pay regulation before workers sign.

### 3.6 Putting it in place

- **Contract appendix** for every worker: base 3,700,000, skill pay or allowance at the certified level, travel and housing support, the OT supplement, and the bonuses by reference to the bonus regulation. Contract, SI declaration and payslip then agree.
- **Consent:** pay does not change, so the appendix needs the worker's signature, not a negotiation. One change is visible: under per-day support, a day of annual leave or a public holiday pays no support (30,769 a day; TC-G06). Paying the support per paid day instead removes that loss but weakens the support's nature `[OPEN-13]`.
- **Pay regulation and bonus regulation:** written, discussed with the worker representative organisation and published (Labor Code Arts. 93, 102, 104).

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
- Grade salary is in both the SI and the OT base. Duty allowances (§3.3 of v0.1) and the phone lump-sum per role `[P]` apply as in v0.1 §4.4. The KPI bonus is an Art. 104 bonus `[OPEN-08]`.
- **The travel allowance is for workers only.** Production support, office and management do not receive the workers' travel and housing support.
- How these roles are paid and declared for SI today, and whether the scale above matches it, is `[OPEN-14]`. The amounts are placeholders until then.

## 5. Daily-paid workers

- Paid a daily rate `[P]` × paid days. A daily rate must be at least the hourly minimum wage (17,800) × the day's normal hours.
- OT hourly base = daily rate ÷ 8, at the statutory factors, plus the OT supplement if the pay regulation extends it to them `[OPEN-15]`.
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
- **Paid days** = days worked + paid leave days + public holidays on working days + statutory paid break minutes, less late minutes beyond the grace period (Attendance §9).
- **Days worked** drive the travel and housing support (§3.1).
- **Unpaid days** (unpaid leave, unexcused absence) and SI-paid leave (sickness, sick child, maternity) reduce paid days; the SI fund pays the SI-paid leave.
- Sources of days as in v0.1 §5: scans for workers, daily-paid and production support; calendar and registered leave for office and management.

## 8. Overtime and night work

OT is paid on the OT base at the statutory rates, plus the company's OT supplement, for hours approved in advance and attended.

```latex
\text{OT pay} = \frac{\text{OT base}}{208} \times \text{factor} \times \text{hours} \;+\; 3{,}846 \times \text{factor} \times \text{hours}
```

| Situation | Factor |
| --- | --- |
| OT on a workday | 150% |
| OT on a weekly rest day | 200% |
| OT on a public holiday or paid leave day | 300% |
| Normal hours at night (22:00–06:00) | +30% |
| Night OT, workday | 200%; 210% after daytime OT that day |
| Night OT, rest day / holiday | 270% / 390% |

- **OT base** = the components flagged *in OT base*: base salary and skill pay (either option) for workers; grade salary and duty allowances for other roles. Bonuses, supports and welfare items are excluded.
- **The OT supplement** applies to workers; whether it applies to night premiums on normal hours follows the same factor table `[P]`.
- **Paid OT hours** = the lower of approved and attended OT hours. Approval records the employee's agreement.
- **Hour limits:** 40 hours a month and 300 hours a year (textile and garment); the attendance system blocks requests beyond them by default. Notify the provincial labour authority within 15 days of passing 200 hours a year.
- OT worked beyond the limits is still paid; the excess is taxable.
- Office and management roles are eligible when approved `[OPEN-10]`.

## 9. Welfare, annual bonus and other benefits

| Benefit | Who | Amount | Notes |
| --- | --- | --- | --- |
| Canteen meal | All | In kind | Not on the payslip; PIT-free |
| Travel and housing support | Workers | `[P 800,000]` per §3.1 | Outside SI and OT bases |
| Childcare support | Workers with children under 6 | `[P]` | Whether to offer it `[OPEN-11]` |
| Life-event support (wedding, bereavement, sickness) | All | `[P]` per event | Outside SI and OT |
| Annual (Tet) bonus | All | `[P about one month's salary]`, scaled by months worked in the year | Art. 104 bonus |

- No cash meal allowance: meals are provided in kind.

## 10. Deductions and contributions

Only statutory deductions, union dues for members and damage compensation may be taken from pay.

| Item | Employee | Employer | Base |
| --- | --- | --- | --- |
| Social insurance | 8% | 17.5% | SI base, capped at 20 × reference level |
| Health insurance | 1.5% | 3% | SI base, same cap |
| Unemployment insurance | 1% | 1% | SI base, capped at 20 × regional minimum wage |
| Union fee | – | 2% | SI base; owed with or without a grassroots union |
| Union dues | 0.5%, members only, capped `[P 253,000]` | – | SI base |
| Personal income tax | Withheld monthly | – | Taxable income after deductions |

- **SI base** = the components flagged *in SI base*, never below the regional minimum wage, from each person's contribution profile. Probation *contracts* are outside compulsory SI; probation written into a labour contract is not.
- **Union:** there is no grassroots union yet, so no employee is a member and no dues are deducted. Membership is a flag on the employee, ready for when a union is formed. The 2% employer fee applies now.
- **PIT, damage compensation and the ban on other deductions:** as in v0.1 §8.

## 11. Pay administration

Each month's pay is calculated from closed attendance and IE figures, approved, then paid by bank transfer with a written payslip.

- **Probation:** at least 85% of the salary for the job `[P 85%]`, for no longer than the law allows for the job (Labor Code Art. 25): 6 working days for jobs without a required qualification, 30 days for jobs needing vocational or technical qualifications, 60 days for jobs needing a college degree or higher, 180 days for enterprise managers. A separate probation contract has no compulsory SI; a probation clause inside the labour contract does.
- **Monthly close, payslip, payment, corrections:** as in v0.1 §9.
- **Leavers:** final pay, including the partial month's efficiency bonus and pay for untaken annual leave (contract salary of the previous month ÷ standard days, per day), within 14 working days of the last day.
- **Go-live:** the first month calculated in the module is `[OPEN-16]`. Pay before it, from 24 Oct 2026, is calculated outside the module; its year-to-date figures (OT hours, taxable income, PIT withheld, leave balances) are loaded as opening data.
- **Changes to this policy** follow the same consultation and publication as the original. Parameter values change by effective date and are kept in the module's history.

## 12. Target policy (undecided)

The direction from v0.1 stays the reference for a later restructure, once workers' expectations and the legal position are weighed:

- One worker base salary at or above the minimum with headroom (v0.1 §3.1), a skill allowance as a fixed allowance, and the efficiency incentive as an Art. 104 bonus.
- A salary scale with job evaluation for all non-worker roles (v0.1 §4).
- Every pay item classified by its nature, so that welfare items are genuine support and nothing is in the OT base that is outside the SI base unless it varies.

The module supports this policy without code changes; the acceptance test cases in groups A–F are written against it, to prove the engine.

## 13. Open decisions

| ID | Decision | Current proposal |
| --- | --- | --- |
| OPEN-01 | Role bonus for production support | Not in v1; a new component later |
| OPEN-02 | One worker base salary, or one per work area | One base salary |
| OPEN-03 | Skill level criteria, review cycle and downgrade rule | HR decides; IE data as a suggestion; 6-month review |
| OPEN-04 | Incentive rate per unit, and whether it is one rate for all | One rate, set from shadow-mode data and the self-funding report |
| OPEN-05 | Attendance bonus amount and conditions | No unexcused absence, at most 2 late arrivals |
| OPEN-06 | Job evaluation method and grade boundaries | Simple four-factor scoring |
| OPEN-07 | Line leaders as a grade or as workers with a duty allowance | **Decided: grade G2** (Peter, 2026-10-30) |
| OPEN-08 | KPI bonus period and size | Monthly or quarterly, capped at a share of grade salary |
| OPEN-09 | Standard days: fixed 26, or the month's scheduled days | **Fixed 26 for now**; the module supports both (Peter, 2026-10-30) |
| OPEN-10 | OT eligibility for office and management | Eligible when approved; management may be excluded |
| OPEN-11 | Childcare support for workers with young children | To decide |
| OPEN-12 | How today's pieces pay, bonus hours, bonus pay and skill bonus map into the current scheme, and what is paid as the efficiency bonus during IE shadow mode | From the accountant's payroll sheet for a recent month |
| OPEN-13 | Travel and housing support paid per day worked, or per paid day | Per day worked (stronger nature; costs 30,769 per leave or holiday day) |
| OPEN-14 | How production support, office and management are paid and declared for SI today | From the accountant's payroll sheet |
| OPEN-15 | Whether daily-paid workers get the OT supplement and the supports | No: daily rate and statutory OT only |
| OPEN-16 | First month calculated in the module | After the module passes the acceptance cases and one parallel month |
| **OPEN-17** | **Worker scheme: option A or option B (§3)** | **Peter and the accountant decide** |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-29 | First draft (filed as "Pay Policy Draft v0.1"). |
| 0.2 | 2026-10-30 | Split into actual pay, current scheme and target policy (§2). New worker scheme with options A and B, their costs, assessment and roll-out (§3). Daily-paid workers (§5) and owners and managers without a labour contract (§6) added. Region IV at phường Chi Lăng confirmed; trading company out of scope. Line leaders decided as G2; the travel allowance limited to workers. OT supplement (§8). No cash meal allowance. Union: none yet, fee owed, dues off (§10). Probation limits by job (§11). Go-live and opening data (§11). Target policy summarised (§12). OPEN-07 and OPEN-09 decided; OPEN-12 to OPEN-17 added. |
