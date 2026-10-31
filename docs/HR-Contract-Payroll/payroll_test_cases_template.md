# Payroll Acceptance Test Cases

v0.5 · Oct 31, 2026 · @Peter

These cases define the payroll module's expected results to the dong. The module is accepted when it reproduces every unblocked case exactly (Payroll Requirements Specification §10). Each case also becomes an automated test.

Groups A–F prove the engine on a reference configuration; group G proves the current scheme that goes live (Pay Policy v0.4 §3–§4: a 3,700,000 base for everyone, with productivity pay for workers and performance pay for other roles). v0.5 adds salary advances: G14 (settled in the month), G15 (carried forward) and check F16. Change log at the end.

**How to read a case**

- **Given:** the employee's contract pay, attendance totals, IE units and entered amounts. Anything not stated is zero or absent.
- **Expected:** every payslip line, the SI base, taxable income, PIT, net pay and employer cost, with the arithmetic shown so it can be checked by hand.
- **Proves:** the FR numbers the case covers.
- A case marked **Blocked** depends on an open decision; its figures follow the current proposal and must be rechecked once the decision is made.

**Two configurations.** Groups A–F run on the **reference configuration**, the v0.1 target policy (worker base 4,500,000 and so on), to prove the engine. Group G runs on the **current scheme**, the configuration that goes live. Group H will hold the first live month, reviewed line by line (Requirements OPEN-07): no earlier payslips exist to reproduce.

**Rounding convention** (TC-R1, to confirm in technical design)

1. Rates such as the OT hourly rate are kept at full precision.
2. Each payslip line is rounded to whole VND (half up).
3. Gross pay, taxable income and net pay are sums of the rounded lines; PIT is calculated on that taxable income and rounded.

All expected values were worked out independently of the module's code, from the pay policy and the regulation reference, and recomputed by a script from the same inputs.

## Common parameters (October 2026)

Every case uses these values unless it says otherwise.

| Parameter | Value |
| --- | --- |
| Region IV minimum wage | 3,700,000 |
| SI reference level | 2,530,000 |
| SI and HI salary cap (20 × 2,530,000) | 50,600,000 |
| UI salary cap (20 × 3,700,000) | 74,000,000 |
| Standard days; hours | 26 days; 26 × 8 = 208 hours |
| Employee rates | SI 8%, HI 1.5%, UI 1% |
| Employer rates | SI 17.5%, HI 3%, UI 1%, union fee 2% |
| Union | No union members unless the case says so; union dues 0.5% of SI base, max 253,000 |
| OT factors | Workday 150%, rest day 200%, holiday 300%; night +30%; night OT workday 200% (210% after daytime OT), rest day 270%, holiday 390% |
| OT monthly limit | 40 hours |
| PIT deductions | 15,500,000 self; 6,200,000 per dependent |
| PIT brackets (monthly taxable) | 5% to 10M; 10% to 30M; 20% to 60M; 30% to 100M; 35% above |
| Cash meal PIT-free cap | 1,200,000 |
| Probation rate | 85% |

**Reference configuration** (groups A–F)

| Parameter | Value |
| --- | --- |
| Worker base salary | 4,500,000 |
| Skill allowance (fixed, in SI and OT base) | S1 500,000 · S2 1,000,000 · S3 1,500,000 |
| Incentive unit rate | 1,500 per unit |
| Attendance bonus | 300,000; forfeited by an unexcused absence or more than 2 late arrivals |
| Travel allowance, workers only | 200,000, not prorated (OPEN-02) |
| Salary scale | Pay Policy §4 (e.g. G2 step 2 = 8,000,000) |

**Current scheme** (group G)

| Parameter | Value |
| --- | --- |
| Base salary | 3,700,000; in SI and OT base |
| Productivity pay | Level amount × paid days/26 × attainment *a* (capped at 100%); outside the SI base; in the OT base at level amount × *a* |
| Level amounts | Entry 800,000 · S1 1,300,000 · S2 1,800,000 · S3 2,300,000 · S4 2,800,000 |
| Efficiency bonus | Entered amount (IE in shadow mode) |
| One-time bonus | Entered, with the director's approval |
| Attendance bonus, supports, OT supplement | None in the current scheme |
| Uniform value | 150,000 per set `[P]` |
| Production support, office, management | Base 3,700,000 + performance pay = (grade and step amount − 3,700,000) × paid days/26 × score *s* (capped at 100%); outside the SI base; in the OT base at the amount earned |
| Grade and step amounts | Pay Policy §4.1 (e.g. G2 step 2 = 8,000,000; G3 step 2 = 10,000,000) |

PIT on taxable income T in the 10–30M bracket = 500,000 + 10% × (T − 10M); in the 30–60M bracket = 2,500,000 + 20% × (T − 30M); in the 60–100M bracket = 8,500,000 + 30% × (T − 60M).

## Coverage

| Requirement | Cases |
| --- | --- |
| FR-12, FR-61 proration by basis | B02, B05, B06, C01, C03, C05, G04, G05, G08 |
| FR-13, FR-35, FR-36 probation, hire | C01, C02, C06 |
| FR-14 OT and night pay | A01–A05, B01, B04, D08, G01–G04 |
| FR-15 OT base from flagged components | A02, A04 (bonus outside); G02, G03 (productivity pay inside, at the amount earned); G04 (not prorated) |
| FR-16 efficiency incentive | A01, A02, B01 |
| FR-17, FR-64 attendance bonus, conditional components | A01 paid; B02, B05 forfeited; B03, C05 kept on leave |
| FR-04, FR-68 variable components, attainment and scores | G01–G06 (G03 below target; G06 measured work only); G10–G13 (G11 score 80%) |
| FR-18, FR-29, FR-69 entered bonuses, approver, taxed when paid | A04–A09, D04, G07; F13 |
| FR-19 other earnings | A01 (travel), A05 (phone) |
| FR-21, FR-22 SI base, rates, caps | All; A09 SI cap; D01 UI cap; G02 (variable pay outside the base) |
| FR-23, FR-39 no contributions in long-absence months | C04, C05 |
| FR-25 union dues | A01 member; every other case non-member |
| FR-26 PIT exemptions | B01 OT over limit; A05 phone; C03 untaken leave; D03 meal cap; D08 OT supplement; E01 adjusted OT |
| FR-27, FR-28 PIT methods and dependents | A07–A09, D01, D05, D06 progressive; C01, D02, D07 flat 10% |
| FR-30 adjustments | E01 |
| FR-31, FR-70 damage compensation and lawful deductions | E02 (cap), G08 (unreturned uniforms); F14 |
| FR-32, FR-33 net pay, employer cost | All |
| FR-38 leaver | C03 |
| FR-60 contribution profile | C01 (probation contract), C06 (probation clause), D06 (manager) |
| FR-63 OT supplement | D08 |
| FR-65 daily-paid | D07 |
| FR-71 salary advances | G14, G15; F16 |
| §7 validations, FR-02, FR-51, FR-59 | F01–F16 |

**Not yet covered:** standard days from the month's schedule (FR-62 variant), mid-month pay changes (FR-37) and transfers (FR-40), non-resident flat 20%, off-cycle payslips (FR-11). See the last section.

## Group A: Baseline payslips (reference configuration)

Full-month payslips for nine roles. Office and management roles carry no position allowance; canteen meals are not on the payslip.

### TC-A01 Entry worker, union member

**Given:** Worker, base salary only. **Union member** (the one member case), 0 dependents. Full month: 26 of 26 days. OT 20 h on workdays. IE units 200. Attendance bonus earned.

**Proves:** FR-12, FR-14, FR-16, FR-17, FR-19, FR-25

{{CASE:A01}}

### TC-A02 Skilled worker

**Given:** Worker, base 4,500,000 + skill allowance S3 1,500,000. 0 dependents. Full month. OT 30 h on workdays. IE units 1,000. Attendance bonus earned.

**Proves:** FR-14, FR-15 (incentive not in the OT base), FR-16

{{CASE:A02}}

### TC-A03 Line leader

**Given:** G2 step 2, 8,000,000. Outside the IE incentive; no travel allowance (workers only). 1 dependent. Full month. OT 30 h on workdays.

**Proves:** FR-14, FR-28

{{CASE:A03}}

### TC-A04 QC staff

**Given:** G3 step 2, 10,000,000. 0 dependents. Full month. OT 16 h on workdays. KPI bonus 1,000,000 entered.

**Proves:** FR-15 (KPI bonus not in the OT base), FR-18

{{CASE:A04}}

### TC-A05 QC senior

**Given:** G4 step 2, 14,000,000. 0 dependents. Full month. OT 8 h on workdays. KPI bonus 1,500,000. Phone lump-sum 200,000.

**Proves:** FR-18, FR-19, FR-26 (phone lump-sum exempt)

{{CASE:A05}}

### TC-A06 QC manager

**Given:** G5 step 2, 17,000,000. 1 dependent. Full month, no OT. KPI bonus 3,000,000. Phone lump-sum 500,000.

**Proves:** FR-18, FR-26, FR-28

{{CASE:A06}}

### TC-A07 Chief accountant

**Given:** G5 step 3, 18,000,000. 0 dependents. Full month. KPI bonus 2,000,000. Phone lump-sum 300,000. The first profile that pays PIT.

**Proves:** FR-27, FR-28

{{CASE:A07}}

### TC-A08 Factory manager

**Given:** G6, 45,000,000 on the contract. 2 dependents. Full month. KPI bonus 8,000,000. Phone lump-sum 1,000,000.

**Proves:** FR-27, FR-28

{{CASE:A08}}

### TC-A09 General manager

**Given:** G6, 70,000,000 on the contract. 1 dependent. Full month. KPI bonus 15,000,000. Phone lump-sum 2,000,000.

**Proves:** FR-21 (SI and HI capped at 50,600,000; UI uncapped below 74,000,000), FR-27, FR-28

{{CASE:A09}}

## Group B: Attendance, overtime and night work (reference configuration)

B01–B05 use the skilled worker from TC-A02 (base 4,500,000 + skill S3 1,500,000, 0 dependents) with different attendance.

### TC-B01 Peak month above the OT limit

**Given:** Full month. OT 36 h on workdays and 16 h on Sundays: 52 h, 12 h over the 40 h monthly limit. IE units 1,200. Attendance bonus earned.

**Proves:** FR-14 (rest-day rate), FR-26 (OT over the limit is taxable pro rata); the §7 OT check fires.

{{CASE:B01}}

### TC-B02 One unexcused absence

**Given:** 25 paid days of 26; 1 day unexcused absence. OT 20 h on workdays. IE units 900. Attendance bonus forfeited. **Blocked** on OPEN-02 (travel allowance shown unprorated).

**Proves:** FR-12 (proration), FR-17 (bonus forfeited), FR-21 (SI base not prorated)

{{CASE:B02}}

### TC-B03 Annual leave

**Given:** 24 days worked + 2 days annual leave = 26 paid days. OT 20 h on workdays. IE units 950. Attendance bonus kept (statutory leave does not forfeit it).

**Proves:** FR-12 (paid leave counts as paid days), FR-17

{{CASE:B03}}

### TC-B04 Night work and night OT

**Given:** Full month. Attendance reports: OT 20 h on workdays; 8 normal hours at night; 4 h night OT on a workday after daytime OT that day; 2 h night OT on a public holiday. IE units 1,000. Attendance bonus earned.

**Proves:** FR-14 (night factors), FR-26 (night pay exempt). OT hours for the limit: 20 + 4 + 2 = 26.

{{CASE:B04}}

### TC-B05 Late arrivals

**Given:** Full month with 3 late arrivals beyond the 5-minute grace, 45 late minutes in all, unpaid (Attendance §5.1). OT 20 h on workdays. IE units 1,000. **Blocked** on Attendance OPEN-04 (whether late minutes are deducted) and OPEN-02.

**Proves:** FR-12 (fractional paid days), FR-17 (3 late arrivals forfeit the bonus; 2 would keep it)

{{CASE:B05}}

### TC-B06 Office employee on unpaid leave

**Given:** QC staff (G3 step 2, 10,000,000), exception-driven: paid days come from the calendar and registered leave, not scans. 2 days of approved unpaid leave; no OT. 0 dependents.

**Proves:** FR-12 (exception-driven paid days), FR-21 (SI base not prorated)

{{CASE:B06}}

## Group C: Mid-month events (reference configuration)

### TC-C01 New hire on a probation contract

**Given:** Worker in a job needing a vocational qualification, on a separate 30-day probation contract (the legal maximum for such a job) at 85% of base salary, starting on working day 14: 13 paid days of 26. No IE units yet. No attendance bonus in the first, partial month. **Blocked** on OPEN-02 and TC-OPEN-1.

**Proves:** FR-13, FR-35, FR-23 and FR-60 (no SI on a probation contract), FR-27 (flat 10% applies only from 5,000,000)

{{CASE:C01}}

### TC-C02 Probation contract ends mid-month

**Given:** Worker with no skill allowance. A 30-day probation contract that started in the previous month ends after working day 10; the labour contract starts on working day 11 (16 days). Full month attended. IE units 300. Attendance bonus earned.

**Proves:** FR-36 (split at the probation end date), FR-21 (SI on the full contract base from the contract month)

{{CASE:C02}}

Assumptions to confirm: a labour contract starting mid-month with 14 or more working days in the month contributes for the whole month (TC-OPEN-2); PIT for the month is progressive, because a labour contract of 3 months or more is in force when it is paid (TC-OPEN-10).

### TC-C03 Leaver

**Given:** Skilled worker (base + S3) resigns; last working day is working day 18: 18 paid days. 5 days of annual leave untaken. IE units 600 for the partial month. No attendance bonus in the partial month. Fully covered by UI throughout service, so no severance allowance. **Blocked** on OPEN-02 and TC-OPEN-1.

**Proves:** FR-38, FR-26 (untaken-leave pay exempt)

{{CASE:C03}}

### TC-C04 Maternity leave all month

**Given:** Skilled worker (base + S3) on maternity leave for the whole month: 0 days worked, 0 paid days. **Blocked** on OPEN-03.

**Proves:** FR-23, FR-39

{{CASE:C04}}

### TC-C05 Long sick leave

**Given:** Skilled worker (base + S3) on SI-paid sick leave for 15 working days; 11 days worked. IE units 300. Attendance bonus kept (sick leave does not forfeit it). **Blocked** on OPEN-02 and OPEN-03.

**Proves:** FR-12, FR-17, FR-23 (no contributions in a month with 14 or more unpaid days)

{{CASE:C05}}

### TC-C06 Probation clause inside the labour contract

**Given:** Worker (no skill allowance) on a labour contract from working day 1 whose first 6 working days are probation at 85% (the limit for a job needing no qualification). Full month attended: 26 paid days. No IE units in the first month. Attendance bonus earned.

**Proves:** FR-36, FR-60 (a probation clause is part of a labour contract, so SI applies from the first day)

{{CASE:C06}}

## Group D: Caps, tax methods, participants and exempt income (reference configuration)

### TC-D01 Both insurance caps

**Given:** G6 executive, 80,000,000 on the contract. 0 dependents. Full month, nothing else.

**Proves:** FR-21 (SI and HI capped at 50,600,000; UI capped at 74,000,000), FR-28 (20% bracket)

{{CASE:D01}}

### TC-D02 Short contract, flat 10% PIT

**Given:** Seasonal worker on a 2-month labour contract, 6,000,000 a month, full month. No commitment form filed.

**Proves:** FR-27 (flat 10% on a payment of 5,000,000 or more), FR-22 (contracts of 1 month or more join SI, HI and UI)

{{CASE:D02}}

To confirm with the tax advisor: whether the 10% applies before or after employee insurance (shown here on gross), and UI coverage of 1–3 month contracts under the Employment Law 2025 (TC-OPEN-3). If the employee files the commitment form, PIT is 0.

### TC-D03 Cash meal allowance above the cap

**Given:** QC staff (G3 step 2, 10,000,000), 0 dependents, full month. Cash meal allowance 1,500,000. Configuration test only: the pay policy provides meals in kind.

**Proves:** FR-26 (meal exempt only up to 1,200,000)

{{CASE:D03}}

### TC-D04 Annual (Tet) bonus month

**Given:** QC staff (G3 step 2, 10,000,000), 0 dependents, full month, no OT. Annual bonus 10,000,000 paid with this month's salary.

**Proves:** FR-18, FR-29 (a bonus is taxed in the month paid), FR-21 (outside the SI base)

{{CASE:D04}}

### TC-D05 Dependent registered this month

**Given:** The chief accountant of TC-A07 registers a dependent from this month, with the registration document attached.

**Proves:** FR-06, FR-28 (family deductions use dependents registered for the month)

{{CASE:D05}}

### TC-D06 Manager paid without a labour contract

**Given:** An owner-manager paid 40,000,000 a month by decision of the owners, with no labour contract. Contribution profile: enterprise manager; SI and HI, no UI; declared SI base 10,000,000. 0 dependents. Progressive PIT. **Blocked** on TC-OPEN-7.

**Proves:** FR-60 (declared base, funds by participant type), FR-27

{{CASE:D06}}

### TC-D07 Daily-paid worker

**Given:** Seasonal worker on a 2-month contract paid 350,000 a day; 26 days worked; no OT. No commitment form. **Blocked** on TC-OPEN-8 (SI base of a daily-paid contract) and TC-OPEN-3.

**Proves:** FR-65, FR-27 (flat 10%), and the daily-rate minimum check (350,000 ≥ 17,800 × 8 = 142,400)

{{CASE:D07}}

### TC-D08 OT supplement (configuration test)

**Given:** The skilled worker of TC-A02 with an OT supplement of 3,846 per OT hour × factor configured: a capability the current scheme does not use. Full month. OT 30 h on workdays. IE units 1,000. Attendance bonus earned. **Blocked** on TC-OPEN-9.

**Proves:** FR-63 (supplement per OT hour × factor, PIT-treated as OT), FR-26

{{CASE:D08}}

## Group E: Adjustments and deductions (reference configuration)

Both cases use the skilled worker from TC-A02 with a normal month: full month, OT 20 h on workdays, IE units 1,000, attendance bonus earned.

### TC-E01 Correction to a locked period

**Given:** 4 h of workday OT worked in September 2026 were missed from the locked September run. September's contract pay was the same (6,000,000) and September OT stayed within the 40 h limit.

**Proves:** FR-30 (adjustment line naming its period, with its component's flags), FR-29, FR-51 (September is not reopened)

{{CASE:E01}}

### TC-E02 Damage deduction above the 30% cap

**Given:** A damage compensation of 3,000,000 approved under the work rules, to be deducted this month.

**Proves:** FR-31 (deduction capped at 30% of pay after insurance and PIT; the rest carries forward)

{{CASE:E02}}

## Group F: Validations

Each case sets up one fault in an otherwise valid run and checks the module's response at the default check levels, unless the case changes a level.

| Case | Given | Expected | Proves |
| --- | --- | --- | --- |
| TC-F01 | October attendance not yet closed | Run cannot be calculated; error names the open period | §7, FR-58 |
| TC-F02 | A worker contract with salary 3,500,000 for full normal hours | Error: below the Region IV minimum wage 3,700,000; approval blocked | §7 |
| TC-F03 | A leaver whose recovery of a 3,000,000 overpayment exceeds the month's pay | Error: negative net pay; approval blocked | FR-32, §7 |
| TC-F04 | A worker with no bank account on file | Error before approval; employee missing from the bank file is not allowed | FR-43, §7 |
| TC-F05 | TC-B01 run (52 OT hours) | Warning: monthly OT limit exceeded; approval needs a reviewer's note | §7 |
| TC-F06 | IE units imported for the line leader in TC-A03 | Warning: employee outside IE scope; units not paid unless confirmed | §7 |
| TC-F07 | The payroll officer who calculated the run tries to approve it | Approval refused | FR-02 |
| TC-F08 | An approved run; a user edits a payslip line | Edit refused; the change must go through an adjustment in the next run (TC-E01) | FR-08, FR-51 |
| TC-F09 | TC-F02 again, with the minimum-wage check's level set to *warning* | Warning instead of error; approval proceeds with a reviewer's note; the run records the check, its level and the approver | FR-59 |
| TC-F10 | A welfare support component (e.g. travel) flagged *in OT base* | Warning: a welfare item in the OT base; approval needs a note | §7 legal-nature check |
| TC-F11 | A worker's productivity pay at 100% attainment for 6 months running | Warning: a variable component that never varied | §7, Pay Policy §3.2 |
| TC-F12 | A worker with productivity pay and no attainment recorded for the month | Error: the run cannot be calculated for her until attainment is entered | FR-68, §7 |
| TC-F13 | A one-time bonus entered without an approver | Error: not paid; approval blocked until approved or removed | FR-69, §7 |
| TC-F14 | A deduction component "uniform charge" configured outside damage compensation | Warning: a deduction of a kind the law does not allow | FR-70, §7 |
| TC-F15 | The 6-month check set to *warning* for productivity pay and *note* for performance pay; a worker and a line leader both at 100% for 6 months | Warning for the worker; a note, not blocking, for the line leader | FR-59 (level per component) |
| TC-F16 | An advance request above `vn.policy.advance_max_share` of the employee's monthly amount | Warning at approval of the advance; approval needs a note | FR-71, §7 |

## Group G: Current scheme (Pay Policy §3–§4)

The go-live configuration. G01–G08 are workers: base 3,700,000 + productivity pay, attainment entered by the supervisor (IE in shadow mode). G10–G13 are other roles: base 3,700,000 + performance pay, scored by the manager. All non-members; 0 dependents unless stated.

### TC-G01 Entry worker at target

**Given:** Entry level. Full month: 26 paid days. Attainment 100%. OT 20 h on workdays. Efficiency bonus entered 300,000.

**Proves:** FR-68, FR-15 (OT on 3,700,000 + 800,000), FR-21 (SI base 3,700,000). Pay and OT equal today's 4,500,000 contract: 4,500,000 ÷ 208 × 150% × 20 = 649,038.

{{CASE:G01}}

### TC-G02 S4 worker at target

**Given:** Certified S4. Full month. Attainment 100%. OT 30 h on workdays. Efficiency bonus entered 1,000,000.

**Proves:** FR-68, FR-15, FR-21 (productivity pay outside the SI base)

{{CASE:G02}}

### TC-G03 S4 worker below target

**Given:** As TC-G02, but the month's output reaches 80% of target. No efficiency bonus (below the incentive threshold).

**Proves:** FR-68 (attainment lowers the pay), FR-15 (the OT base follows the amount earned)

{{CASE:G03}}

### TC-G04 Entry worker with two unexcused absences

**Given:** As TC-G01, with 2 days of unexcused absence: 24 paid days. Attainment on the 24 days worked: 100%.

**Proves:** FR-12, FR-61 (both lines by paid days), FR-15 (the OT base is not prorated)

{{CASE:G04}}

### TC-G05 Entry worker with two days of annual leave

**Given:** As TC-G01, with 2 days of annual leave: 24 days worked, 26 paid days. Attainment on the days worked: 100%.

**Proves:** FR-61 (leave days are paid days for productivity pay too)

{{CASE:G05}}

### TC-G06 S2 worker who spends part of the month training others

**Given:** Certified S2. Full month, no OT. 10 days training new workers (unmeasured work), 16 days on measured work at 100% of target. No efficiency bonus.

**Proves:** FR-68 (attainment counts measured work only, so training days neither raise nor lower it)

{{CASE:G06}}

### TC-G07 One-time bonus

**Given:** As TC-G01, plus a project completion bonus of 500,000 approved by the director.

**Proves:** FR-18, FR-69 (paid because approved), FR-29

{{CASE:G07}}

### TC-G08 Leaver who does not return her uniforms

**Given:** Entry worker; last working day is working day 20: 20 paid days, attainment 100%, no OT. Efficiency bonus entered 200,000. She does not return 2 uniform sets; the work-rules process decides compensation of 2 × 150,000 = 300,000.

**Proves:** FR-31 (damage compensation on a recorded decision, within the cap), FR-38, FR-70

{{CASE:G08}}

### TC-G10 Line leader, full score

**Given:** G2 step 2, 8,000,000. Score 100%. Full month. OT 30 h on workdays. 1 dependent.

**Proves:** FR-04 (the grade and step amount split into base and performance pay), FR-68, FR-15 (OT on the full 8,000,000), FR-21 (SI base 3,700,000)

{{CASE:G10}}

### TC-G11 Line leader, score 80%

**Given:** As TC-G10, with a score of 80%.

**Proves:** FR-68 (the score lowers the pay), FR-15 (the OT base follows the amount earned)

{{CASE:G11}}

### TC-G12 QC staff

**Given:** G3 step 2, 10,000,000. Score 100%. Full month. OT 16 h on workdays.

**Proves:** FR-04, FR-68, FR-15

{{CASE:G12}}

### TC-G13 Factory manager

**Given:** G6, 45,000,000 on the contract. Score 100%, entered by the director. Full month, no OT. 2 dependents.

**Proves:** FR-68 (director's score), FR-27, FR-28; the gap between declared income and SI base that Pay Policy §4.3 describes

{{CASE:G13}}

### TC-G14 Entry worker with a salary advance

**Given:** As TC-G01. An advance of 1,500,000, approved and paid by bank on the 15th through a payment order.

**Proves:** FR-71 (the advance is settled on the month's payslip; the bank file pays only the remainder). Net pay, SI and PIT are the same as TC-G01: the advance is part of the month's pay, not a deduction.

{{CASE:G14}}

Posting: the advance's payment booked Dr 3341 / Cr bank on the 15th; at approval the run posts the gross credit on 3341, and the employee's 3341 debits (insurance 388,500 and the advance 1,500,000) are reconciled against it, leaving 3,560,538 open for the payment order.

### TC-G15 Advance larger than the month's pay

**Given:** Entry worker. An advance of 2,000,000 paid on the 15th; she then takes 16 days of approved unpaid leave: 10 paid days, attainment 100%, no OT, no efficiency bonus.

**Proves:** FR-71 (settlement capped at net pay; the rest carries to the next month), FR-23 (no contributions with 16 days neither worked nor paid)

{{CASE:G15}}

Check: `advance_carried` warning on the payslip. The 269,231 stays an open debit on the employee's 3341 and is settled first in the next month.

## Assumptions to confirm and blocked cases

Writing the expected values surfaced these decisions. Each blocked case must be rechecked once its item is settled.

| ID | Item | Cases affected | Current assumption |
| --- | --- | --- | --- |
| TC-R1 | Rounding convention | All | Rates at full precision; lines rounded to VND, half up; totals from rounded lines |
| OPEN-02 (spec) | Travel allowance proration (reference configuration only) | B02, B05, C01, C03, C05 | Not prorated |
| OPEN-03 (spec) | No-contribution rule for 14 or more unpaid working days, and HI during sick leave | C04, C05 | No SI, HI or UI that month |
| OPEN-04 (spec) | Month from which a changed SI base applies | Cases to add below | – |
| Attendance OPEN-04 | Whether late minutes beyond the grace period are deducted | B05 | Deducted, as a fraction of a day |
| TC-OPEN-1 | Attendance bonus for a partial month (new hire, leaver) | C01, C03 | Not paid |
| TC-OPEN-2 | SI for a labour contract starting mid-month | C02 | Whole month contributed when 14 or more working days fall under the contract |
| TC-OPEN-3 | Flat 10% PIT: on gross or after employee insurance; UI for 1–3 month contracts | D02, D07 | On gross; UI applies |
| TC-OPEN-4 | Pay basis for untaken annual leave | C03 | Contract salary of the month before leaving ÷ standard days (Decree 145 Art. 67) |
| TC-OPEN-5 | Night OT factors (200% / 210% / 270% / 390%) | B04 | As in Decree 145 Art. 57; confirm with the accountant |
| TC-OPEN-6 | Splitting OT pay above the monthly limit into exempt and taxable | B01 | Pro rata by hours over the whole month's OT pay; the alternative takes the last hours worked |
| TC-OPEN-7 | Manager paid without a labour contract: funds, base floor, union fee | D06 | SI and HI on the declared base; no UI; union fee on that base |
| TC-OPEN-8 | SI base of a daily-paid contract | D07 | Daily rate × 26 |
| TC-OPEN-9 | PIT treatment of the OT supplement | D08 | Exempt with OT, within the limits |
| TC-OPEN-11 | Targets and the attainment measure (Pay Policy OPEN-18) | G01–G08 | Attainment entered by the supervisor from piece counts |
| TC-OPEN-13 | Each employee's grade and step amount (Pay Policy OPEN-20) and the scoring method (OPEN-21) | G10–G13 | Amounts from Pay Policy §4.1; score entered by the manager |
| TC-OPEN-12 | SI for a leaver's last month | G08 | Contributed when 14 or more working days fall before the last day |
| TC-OPEN-10 | PIT method in a month that mixes a probation contract and a labour contract | C02 | Progressive for the whole month |

**Cases to add once decided**

- **TC-C07 Level changed mid-month** (FR-37): reference configuration, skill allowance S2 from working day 14: 1,000,000 × 13/26 = 500,000; and the current scheme, productivity level Entry to S1 on working day 14. SI base and OT rate wait for OPEN-04.
- **TC-C08 Transfer from worker to line leader mid-month** (FR-40): salary split by date, incentive for the worker days only. SI base waits for OPEN-04.
- **TC-B07 Standard days from the month's schedule** (FR-62 variant): a 24-day February and a 27-day October, full attendance.
- **TC-G09 Probation on the current scheme:** 85% of the base salary and the Entry productivity amount (Pay Policy §11).
- **Group H, first live month:** every payslip of the first month calculated in the module, reviewed line by line against what each employee expected (Requirements OPEN-07).
- **Non-resident** (flat 20%) and **off-cycle payslip** (FR-11), if those situations arise.

**Turning these into automated tests:** each case's Given becomes a fixture, and each table row an assertion to the dong. The PIT exemption, SI base and employer contribution figures under each table are assertions too.

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-30 | First draft. |
| 0.2 | 2026-10-30 | Two configurations: reference (A–F) and current scheme (new group G, six cases). No union members by default (A01 stays a member), so net pay rises by the dues in A02–A07, B, C02, C03, D03 and E. A03 loses the travel allowance (workers only). C01 and C02 use lawful 30-day probation contracts; C06 adds a probation clause. New B05 (late arrivals), B06 (office unpaid leave), D04 (Tet bonus), D05 (new dependent), D06 (manager without a labour contract), D07 (daily-paid), F09–F11 (check levels and nature checks). TC-OPEN-6 to TC-OPEN-10 added. All figures generated and checked by script. |
| 0.3 | 2026-10-30 | Group G rebuilt for Pay Policy v0.3: base salary + productivity pay with attainment (G01–G06), one-time bonus (G07), unreturned uniforms as damage compensation (G08). The OT supplement moves to a configuration test, TC-D08. Checks F12–F14 added; F10 and F11 reworded. TC-OPEN-11 and TC-OPEN-12 added. Coverage updated for FR-68 to FR-70. |
| 0.4 | 2026-10-30 | Current scheme for production support, office and management: staff cases G10–G13 (line leader at 100% and 80%, QC staff, factory manager) and check F15 (6-month check level per component). Group H becomes the first live month's review. TC-OPEN-13 added. |
| 0.5 | 2026-10-31 | Salary advances: TC-G14 (settled, remaining to pay), TC-G15 (capped at net, carried forward), check TC-F16 (advance above the limit). |
