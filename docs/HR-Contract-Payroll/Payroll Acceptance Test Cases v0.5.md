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

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| OT workday 20 h | 4,500,000 ÷ 208 × 150% × 20 | 649,038 |
| Efficiency incentive | 200 units × 1,500 | 300,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **5,949,038** |
| Social insurance | 8% × 4,500,000 | −360,000 |
| Health insurance | 1.5% × 4,500,000 | −67,500 |
| Unemployment insurance | 1% × 4,500,000 | −45,000 |
| Union dues | 0.5% × 4,500,000 | −22,500 |
| PIT | 5,949,038 − 649,038 exempt − 472,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,454,038** |

SI base 4,500,000 · OT hourly rate 4,500,000 ÷ 208 = 21,634.6154 · PIT-exempt 649,038 · Employer contributions 1,057,500 (787,500 SI + 135,000 HI + 45,000 UI + 90,000 union fee) · Employer cost 7,006,538

### TC-A02 Skilled worker

**Given:** Worker, base 4,500,000 + skill allowance S3 1,500,000. 0 dependents. Full month. OT 30 h on workdays. IE units 1,000. Attendance bonus earned.

**Proves:** FR-14, FR-15 (incentive not in the OT base), FR-16

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 30 h | 6,000,000 ÷ 208 × 150% × 30 | 1,298,077 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **9,298,077** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 9,298,077 − 1,298,077 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,668,077** |

SI base 6,000,000 · OT hourly rate 6,000,000 ÷ 208 = 28,846.1538 · PIT-exempt 1,298,077 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,708,077

### TC-A03 Line leader

**Given:** G2 step 2, 8,000,000. Outside the IE incentive; no travel allowance (workers only). 1 dependent. Full month. OT 30 h on workdays.

**Proves:** FR-14, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 8,000,000 |
| OT workday 30 h | 8,000,000 ÷ 208 × 150% × 30 | 1,730,769 |
| **Gross pay** |  | **9,730,769** |
| Social insurance | 8% × 8,000,000 | −640,000 |
| Health insurance | 1.5% × 8,000,000 | −120,000 |
| Unemployment insurance | 1% × 8,000,000 | −80,000 |
| PIT | 9,730,769 − 1,730,769 exempt − 840,000 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,890,769** |

SI base 8,000,000 · OT hourly rate 8,000,000 ÷ 208 = 38,461.5385 · PIT-exempt 1,730,769 · Employer contributions 1,880,000 (1,400,000 SI + 240,000 HI + 80,000 UI + 160,000 union fee) · Employer cost 11,610,769

### TC-A04 QC staff

**Given:** G3 step 2, 10,000,000. 0 dependents. Full month. OT 16 h on workdays. KPI bonus 1,000,000 entered.

**Proves:** FR-15 (KPI bonus not in the OT base), FR-18

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 10,000,000 |
| OT workday 16 h | 10,000,000 ÷ 208 × 150% × 16 | 1,153,846 |
| KPI bonus | Entered | 1,000,000 |
| **Gross pay** |  | **12,153,846** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| Unemployment insurance | 1% × 10,000,000 | −100,000 |
| PIT | 12,153,846 − 1,153,846 exempt − 1,050,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **11,103,846** |

SI base 10,000,000 · OT hourly rate 10,000,000 ÷ 208 = 48,076.9231 · PIT-exempt 1,153,846 · Employer contributions 2,350,000 (1,750,000 SI + 300,000 HI + 100,000 UI + 200,000 union fee) · Employer cost 14,503,846

### TC-A05 QC senior

**Given:** G4 step 2, 14,000,000. 0 dependents. Full month. OT 8 h on workdays. KPI bonus 1,500,000. Phone lump-sum 200,000.

**Proves:** FR-18, FR-19, FR-26 (phone lump-sum exempt)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 14,000,000 |
| OT workday 8 h | 14,000,000 ÷ 208 × 150% × 8 | 807,692 |
| KPI bonus | Entered | 1,500,000 |
| Phone lump-sum | PIT-free | 200,000 |
| **Gross pay** |  | **16,507,692** |
| Social insurance | 8% × 14,000,000 | −1,120,000 |
| Health insurance | 1.5% × 14,000,000 | −210,000 |
| Unemployment insurance | 1% × 14,000,000 | −140,000 |
| PIT | 16,507,692 − 1,007,692 exempt − 1,470,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **15,037,692** |

SI base 14,000,000 · OT hourly rate 14,000,000 ÷ 208 = 67,307.6923 · PIT-exempt 1,007,692 (OT 807,692 + phone 200,000) · Employer contributions 3,290,000 (2,450,000 SI + 420,000 HI + 140,000 UI + 280,000 union fee) · Employer cost 19,797,692

### TC-A06 QC manager

**Given:** G5 step 2, 17,000,000. 1 dependent. Full month, no OT. KPI bonus 3,000,000. Phone lump-sum 500,000.

**Proves:** FR-18, FR-26, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 17,000,000 |
| KPI bonus | Entered | 3,000,000 |
| Phone lump-sum | PIT-free | 500,000 |
| **Gross pay** |  | **20,500,000** |
| Social insurance | 8% × 17,000,000 | −1,360,000 |
| Health insurance | 1.5% × 17,000,000 | −255,000 |
| Unemployment insurance | 1% × 17,000,000 | −170,000 |
| PIT | 20,500,000 − 500,000 exempt − 1,785,000 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **18,715,000** |

SI base 17,000,000 · PIT-exempt 500,000 · Employer contributions 3,995,000 (2,975,000 SI + 510,000 HI + 170,000 UI + 340,000 union fee) · Employer cost 24,495,000

### TC-A07 Chief accountant

**Given:** G5 step 3, 18,000,000. 0 dependents. Full month. KPI bonus 2,000,000. Phone lump-sum 300,000. The first profile that pays PIT.

**Proves:** FR-27, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 18,000,000 |
| KPI bonus | Entered | 2,000,000 |
| Phone lump-sum | PIT-free | 300,000 |
| **Gross pay** |  | **20,300,000** |
| Social insurance | 8% × 18,000,000 | −1,440,000 |
| Health insurance | 1.5% × 18,000,000 | −270,000 |
| Unemployment insurance | 1% × 18,000,000 | −180,000 |
| PIT | 20,300,000 − 300,000 exempt − 1,890,000 insurance − 15,500,000 deduction = 2,610,000 taxable; 5% × 2,610,000 | −130,500 |
| **Net pay** |  | **18,279,500** |

SI base 18,000,000 · PIT-exempt 300,000 · Employer contributions 4,230,000 (3,150,000 SI + 540,000 HI + 180,000 UI + 360,000 union fee) · Employer cost 24,530,000

### TC-A08 Factory manager

**Given:** G6, 45,000,000 on the contract. 2 dependents. Full month. KPI bonus 8,000,000. Phone lump-sum 1,000,000.

**Proves:** FR-27, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 45,000,000 |
| KPI bonus | Entered | 8,000,000 |
| Phone lump-sum | PIT-free | 1,000,000 |
| **Gross pay** |  | **54,000,000** |
| Social insurance | 8% × 45,000,000 | −3,600,000 |
| Health insurance | 1.5% × 45,000,000 | −675,000 |
| Unemployment insurance | 1% × 45,000,000 | −450,000 |
| PIT | 54,000,000 − 1,000,000 exempt − 4,725,000 insurance − 27,900,000 deduction = 20,375,000 taxable; 500,000 + 10% × 10,375,000 | −1,537,500 |
| **Net pay** |  | **47,737,500** |

SI base 45,000,000 · PIT-exempt 1,000,000 · Employer contributions 10,575,000 (7,875,000 SI + 1,350,000 HI + 450,000 UI + 900,000 union fee) · Employer cost 64,575,000

### TC-A09 General manager

**Given:** G6, 70,000,000 on the contract. 1 dependent. Full month. KPI bonus 15,000,000. Phone lump-sum 2,000,000.

**Proves:** FR-21 (SI and HI capped at 50,600,000; UI uncapped below 74,000,000), FR-27, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 70,000,000 |
| KPI bonus | Entered | 15,000,000 |
| Phone lump-sum | PIT-free | 2,000,000 |
| **Gross pay** |  | **87,000,000** |
| Social insurance | 8% × 50,600,000 (capped) | −4,048,000 |
| Health insurance | 1.5% × 50,600,000 (capped) | −759,000 |
| Unemployment insurance | 1% × 70,000,000 | −700,000 |
| PIT | 87,000,000 − 2,000,000 exempt − 5,507,000 insurance − 21,700,000 deduction = 57,793,000 taxable; 2,500,000 + 20% × 27,793,000 | −8,058,600 |
| **Net pay** |  | **73,434,400** |

SI base 70,000,000, capped to 50,600,000 for SI and HI · PIT-exempt 2,000,000 · Employer contributions 12,085,000 (8,855,000 SI + 1,518,000 HI + 700,000 UI + 1,012,000 union fee) · Employer cost 99,085,000

## Group B: Attendance, overtime and night work (reference configuration)

B01–B05 use the skilled worker from TC-A02 (base 4,500,000 + skill S3 1,500,000, 0 dependents) with different attendance.

### TC-B01 Peak month above the OT limit

**Given:** Full month. OT 36 h on workdays and 16 h on Sundays: 52 h, 12 h over the 40 h monthly limit. IE units 1,200. Attendance bonus earned.

**Proves:** FR-14 (rest-day rate), FR-26 (OT over the limit is taxable pro rata); the §7 OT check fires.

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 36 h | 6,000,000 ÷ 208 × 150% × 36 | 1,557,692 |
| OT rest day 16 h | 6,000,000 ÷ 208 × 200% × 16 | 923,077 |
| Efficiency incentive | 1,200 units × 1,500 | 1,800,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **10,780,769** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 10,780,769 − 1,908,284 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **10,150,769** |

SI base 6,000,000 · PIT-exempt 1,908,284 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 12,190,769 · OT pay 2,480,769; exempt share 2,480,769 × 40/52 = 1,908,284; taxable OT 572,485

### TC-B02 One unexcused absence

**Given:** 25 paid days of 26; 1 day unexcused absence. OT 20 h on workdays. IE units 900. Attendance bonus forfeited. **Blocked** on OPEN-02 (travel allowance shown unprorated).

**Proves:** FR-12 (proration), FR-17 (bonus forfeited), FR-21 (SI base not prorated)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 25/26 | 4,326,923 |
| Skill allowance | 1,500,000 × 25/26 | 1,442,308 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Efficiency incentive | 900 units × 1,500 | 1,350,000 |
| Attendance bonus | Forfeited | 0 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **8,184,616** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 8,184,616 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **7,554,616** |

SI base 6,000,000 · PIT-exempt 865,385 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 9,594,616

### TC-B03 Annual leave

**Given:** 24 days worked + 2 days annual leave = 26 paid days. OT 20 h on workdays. IE units 950. Attendance bonus kept (statutory leave does not forfeit it).

**Proves:** FR-12 (paid leave counts as paid days), FR-17

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 26 paid days, full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Efficiency incentive | 950 units × 1,500 | 1,425,000 |
| Attendance bonus | Kept | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **8,790,385** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 8,790,385 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,160,385** |

SI base 6,000,000 · PIT-exempt 865,385 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,200,385

### TC-B04 Night work and night OT

**Given:** Full month. Attendance reports: OT 20 h on workdays; 8 normal hours at night; 4 h night OT on a workday after daytime OT that day; 2 h night OT on a public holiday. IE units 1,000. Attendance bonus earned.

**Proves:** FR-14 (night factors), FR-26 (night pay exempt). OT hours for the limit: 20 + 4 + 2 = 26.

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Night premium, normal hours 8 h | 6,000,000 ÷ 208 × 30% × 8 | 69,231 |
| Night OT workday after daytime OT 4 h | 6,000,000 ÷ 208 × 210% × 4 | 242,308 |
| Night OT holiday 2 h | 6,000,000 ÷ 208 × 390% × 2 | 225,000 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **9,401,924** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 9,401,924 − 1,401,924 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,771,924** |

SI base 6,000,000 · PIT-exempt 1,401,924 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,811,924

### TC-B05 Late arrivals

**Given:** Full month with 3 late arrivals beyond the 5-minute grace, 45 late minutes in all, unpaid (Attendance §5.1). OT 20 h on workdays. IE units 1,000. **Blocked** on Attendance OPEN-04 (whether late minutes are deducted) and OPEN-02.

**Proves:** FR-12 (fractional paid days), FR-17 (3 late arrivals forfeit the bonus; 2 would keep it)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 25.90625/26 | 4,483,774 |
| Skill allowance | 1,500,000 × 25.90625/26 | 1,494,591 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus | Forfeited: 3 late arrivals, limit 2 | 0 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **8,543,750** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 8,543,750 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **7,913,750** |

SI base 6,000,000 · PIT-exempt 865,385 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 9,953,750 · Paid days 26 − 45/480 = 25.90625

### TC-B06 Office employee on unpaid leave

**Given:** QC staff (G3 step 2, 10,000,000), exception-driven: paid days come from the calendar and registered leave, not scans. 2 days of approved unpaid leave; no OT. 0 dependents.

**Proves:** FR-12 (exception-driven paid days), FR-21 (SI base not prorated)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 10,000,000 × 24/26 | 9,230,769 |
| **Gross pay** |  | **9,230,769** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| Unemployment insurance | 1% × 10,000,000 | −100,000 |
| PIT | 9,230,769 − 1,050,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,180,769** |

SI base 10,000,000 · Employer contributions 2,350,000 (1,750,000 SI + 300,000 HI + 100,000 UI + 200,000 union fee) · Employer cost 11,580,769 · SI base not prorated

## Group C: Mid-month events (reference configuration)

### TC-C01 New hire on a probation contract

**Given:** Worker in a job needing a vocational qualification, on a separate 30-day probation contract (the legal maximum for such a job) at 85% of base salary, starting on working day 14: 13 paid days of 26. No IE units yet. No attendance bonus in the first, partial month. **Blocked** on OPEN-02 and TC-OPEN-1.

**Proves:** FR-13, FR-35, FR-23 and FR-60 (no SI on a probation contract), FR-27 (flat 10% applies only from 5,000,000)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 85% × 13/26 | 1,912,500 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **2,112,500** |
| PIT (flat 10%) | Payment 2,112,500 is under 5,000,000: no withholding | 0 |
| **Net pay** |  | **2,112,500** |

No SI base · Employer contributions 0 · Employer cost 2,112,500

### TC-C02 Probation contract ends mid-month

**Given:** Worker with no skill allowance. A 30-day probation contract that started in the previous month ends after working day 10; the labour contract starts on working day 11 (16 days). Full month attended. IE units 300. Attendance bonus earned.

**Proves:** FR-36 (split at the probation end date), FR-21 (SI on the full contract base from the contract month)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary, probation 10 days | 4,500,000 × 85% × 10/26 | 1,471,154 |
| Salary, contract 16 days | 4,500,000 × 16/26 | 2,769,231 |
| Efficiency incentive | 300 units × 1,500 | 450,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **5,190,385** |
| Social insurance | 8% × 4,500,000 | −360,000 |
| Health insurance | 1.5% × 4,500,000 | −67,500 |
| Unemployment insurance | 1% × 4,500,000 | −45,000 |
| PIT | 5,190,385 − 472,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **4,717,885** |

SI base 4,500,000 · Employer contributions 1,057,500 (787,500 SI + 135,000 HI + 45,000 UI + 90,000 union fee) · Employer cost 6,247,885

Assumptions to confirm: a labour contract starting mid-month with 14 or more working days in the month contributes for the whole month (TC-OPEN-2); PIT for the month is progressive, because a labour contract of 3 months or more is in force when it is paid (TC-OPEN-10).

### TC-C03 Leaver

**Given:** Skilled worker (base + S3) resigns; last working day is working day 18: 18 paid days. 5 days of annual leave untaken. IE units 600 for the partial month. No attendance bonus in the partial month. Fully covered by UI throughout service, so no severance allowance. **Blocked** on OPEN-02 and TC-OPEN-1.

**Proves:** FR-38, FR-26 (untaken-leave pay exempt)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 18/26 | 3,115,385 |
| Skill allowance | 1,500,000 × 18/26 | 1,038,462 |
| Efficiency incentive | 600 units × 1,500 | 900,000 |
| Untaken annual leave 5 days | 6,000,000 × 5/26 (contract salary of the previous month) | 1,153,846 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **6,407,693** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 6,407,693 − 1,153,846 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,777,693** |

SI base 6,000,000 (18 working days, so the month is contributed) · PIT-exempt 1,153,846 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 7,817,693 · Paid within 14 working days of the last day

### TC-C04 Maternity leave all month

**Given:** Skilled worker (base + S3) on maternity leave for the whole month: 0 days worked, 0 paid days. **Blocked** on OPEN-03.

**Proves:** FR-23, FR-39

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary and skill allowance | 6,000,000 × 0/26 | 0 |
| **Gross pay** |  | **0** |
| PIT | 0 − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **0** |

No contributions: not working and not paid for 14 days or more · Employer contributions 0 · Employer cost 0 · The SI fund pays the HI contribution during maternity leave · The employee appears on the SI change report as on maternity leave

### TC-C05 Long sick leave

**Given:** Skilled worker (base + S3) on SI-paid sick leave for 15 working days; 11 days worked. IE units 300. Attendance bonus kept (sick leave does not forfeit it). **Blocked** on OPEN-02 and OPEN-03.

**Proves:** FR-12, FR-17, FR-23 (no contributions in a month with 14 or more unpaid days)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 11/26 | 1,903,846 |
| Skill allowance | 1,500,000 × 11/26 | 634,615 |
| Efficiency incentive | 300 units × 1,500 | 450,000 |
| Attendance bonus | Kept | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **3,488,461** |
| PIT | 3,488,461 − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **3,488,461** |

No contributions: 15 working days not worked and not paid by the company · Employer contributions 0 · Employer cost 3,488,461 · The SI fund pays the sick-leave benefit separately

### TC-C06 Probation clause inside the labour contract

**Given:** Worker (no skill allowance) on a labour contract from working day 1 whose first 6 working days are probation at 85% (the limit for a job needing no qualification). Full month attended: 26 paid days. No IE units in the first month. Attendance bonus earned.

**Proves:** FR-36, FR-60 (a probation clause is part of a labour contract, so SI applies from the first day)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary, probation clause 6 days | 4,500,000 × 85% × 6/26 | 882,692 |
| Salary, after probation 20 days | 4,500,000 × 20/26 | 3,461,538 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **4,844,230** |
| Social insurance | 8% × 4,500,000 | −360,000 |
| Health insurance | 1.5% × 4,500,000 | −67,500 |
| Unemployment insurance | 1% × 4,500,000 | −45,000 |
| PIT | 4,844,230 − 472,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **4,371,730** |

SI base 4,500,000 from the contract's first day, probation days included · Employer contributions 1,057,500 (787,500 SI + 135,000 HI + 45,000 UI + 90,000 union fee) · Employer cost 5,901,730

## Group D: Caps, tax methods, participants and exempt income (reference configuration)

### TC-D01 Both insurance caps

**Given:** G6 executive, 80,000,000 on the contract. 0 dependents. Full month, nothing else.

**Proves:** FR-21 (SI and HI capped at 50,600,000; UI capped at 74,000,000), FR-28 (20% bracket)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 80,000,000 |
| **Gross pay** |  | **80,000,000** |
| Social insurance | 8% × 50,600,000 (capped) | −4,048,000 |
| Health insurance | 1.5% × 50,600,000 (capped) | −759,000 |
| Unemployment insurance | 1% × 74,000,000 (capped) | −740,000 |
| PIT | 80,000,000 − 5,547,000 insurance − 15,500,000 deduction = 58,953,000 taxable; 2,500,000 + 20% × 28,953,000 | −8,290,600 |
| **Net pay** |  | **66,162,400** |

SI base 80,000,000 · Employer contributions 12,125,000 (8,855,000 SI + 1,518,000 HI + 740,000 UI + 1,012,000 union fee) · Employer cost 92,125,000

### TC-D02 Short contract, flat 10% PIT

**Given:** Seasonal worker on a 2-month labour contract, 6,000,000 a month, full month. No commitment form filed.

**Proves:** FR-27 (flat 10% on a payment of 5,000,000 or more), FR-22 (contracts of 1 month or more join SI, HI and UI)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 6,000,000 |
| **Gross pay** |  | **6,000,000** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT (flat 10%) | 10% × 6,000,000 | −600,000 |
| **Net pay** |  | **4,770,000** |

SI base 6,000,000 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 7,410,000

To confirm with the tax advisor: whether the 10% applies before or after employee insurance (shown here on gross), and UI coverage of 1–3 month contracts under the Employment Law 2025 (TC-OPEN-3). If the employee files the commitment form, PIT is 0.

### TC-D03 Cash meal allowance above the cap

**Given:** QC staff (G3 step 2, 10,000,000), 0 dependents, full month. Cash meal allowance 1,500,000. Configuration test only: the pay policy provides meals in kind.

**Proves:** FR-26 (meal exempt only up to 1,200,000)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 10,000,000 |
| Cash meal allowance | PIT-free up to 1,200,000; 300,000 taxable | 1,500,000 |
| **Gross pay** |  | **11,500,000** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| Unemployment insurance | 1% × 10,000,000 | −100,000 |
| PIT | 11,500,000 − 1,200,000 exempt − 1,050,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **10,450,000** |

SI base 10,000,000 · PIT-exempt 1,200,000 · Employer contributions 2,350,000 (1,750,000 SI + 300,000 HI + 100,000 UI + 200,000 union fee) · Employer cost 13,850,000 · Taxable income before deductions 10,300,000 · SI base excludes the meal allowance

### TC-D04 Annual (Tet) bonus month

**Given:** QC staff (G3 step 2, 10,000,000), 0 dependents, full month, no OT. Annual bonus 10,000,000 paid with this month's salary.

**Proves:** FR-18, FR-29 (a bonus is taxed in the month paid), FR-21 (outside the SI base)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 10,000,000 |
| Annual (Tet) bonus | Entered | 10,000,000 |
| **Gross pay** |  | **20,000,000** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| Unemployment insurance | 1% × 10,000,000 | −100,000 |
| PIT | 20,000,000 − 1,050,000 insurance − 15,500,000 deduction = 3,450,000 taxable; 5% × 3,450,000 | −172,500 |
| **Net pay** |  | **18,777,500** |

SI base 10,000,000 · Employer contributions 2,350,000 (1,750,000 SI + 300,000 HI + 100,000 UI + 200,000 union fee) · Employer cost 22,350,000 · The bonus is outside the SI base and taxed in the month paid

### TC-D05 Dependent registered this month

**Given:** The chief accountant of TC-A07 registers a dependent from this month, with the registration document attached.

**Proves:** FR-06, FR-28 (family deductions use dependents registered for the month)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 18,000,000 |
| KPI bonus | Entered | 2,000,000 |
| Phone lump-sum | PIT-free | 300,000 |
| **Gross pay** |  | **20,300,000** |
| Social insurance | 8% × 18,000,000 | −1,440,000 |
| Health insurance | 1.5% × 18,000,000 | −270,000 |
| Unemployment insurance | 1% × 18,000,000 | −180,000 |
| PIT | 20,300,000 − 300,000 exempt − 1,890,000 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **18,410,000** |

SI base 18,000,000 · PIT-exempt 300,000 · Employer contributions 4,230,000 (3,150,000 SI + 540,000 HI + 180,000 UI + 360,000 union fee) · Employer cost 24,530,000 · Compare TC-A07: the same pay with no dependent withholds 130,500

### TC-D06 Manager paid without a labour contract

**Given:** An owner-manager paid 40,000,000 a month by decision of the owners, with no labour contract. Contribution profile: enterprise manager; SI and HI, no UI; declared SI base 10,000,000. 0 dependents. Progressive PIT. **Blocked** on TC-OPEN-7.

**Proves:** FR-60 (declared base, funds by participant type), FR-27

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Decided by the owners | 40,000,000 |
| **Gross pay** |  | **40,000,000** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| PIT | 40,000,000 − 950,000 insurance − 15,500,000 deduction = 23,550,000 taxable; 500,000 + 10% × 13,550,000 | −1,855,000 |
| **Net pay** |  | **37,195,000** |

Declared SI base 10,000,000; no UI · Employer contributions 2,250,000 (1,750,000 SI + 300,000 HI + 200,000 union fee) · Employer cost 42,250,000

### TC-D07 Daily-paid worker

**Given:** Seasonal worker on a 2-month contract paid 350,000 a day; 26 days worked; no OT. No commitment form. **Blocked** on TC-OPEN-8 (SI base of a daily-paid contract) and TC-OPEN-3.

**Proves:** FR-65, FR-27 (flat 10%), and the daily-rate minimum check (350,000 ≥ 17,800 × 8 = 142,400)

| Line | Calculation | Amount |
| --- | --- | --: |
| Daily wage | 350,000 × 26 days | 9,100,000 |
| **Gross pay** |  | **9,100,000** |
| Social insurance | 8% × 9,100,000 | −728,000 |
| Health insurance | 1.5% × 9,100,000 | −136,500 |
| Unemployment insurance | 1% × 9,100,000 | −91,000 |
| PIT (flat 10%) | 10% × 9,100,000 | −910,000 |
| **Net pay** |  | **7,234,500** |

SI base 350,000 × 26 = 9,100,000 (assumption) · Employer contributions 2,138,500 (1,592,500 SI + 273,000 HI + 91,000 UI + 182,000 union fee) · Employer cost 11,238,500

### TC-D08 OT supplement (configuration test)

**Given:** The skilled worker of TC-A02 with an OT supplement of 3,846 per OT hour × factor configured: a capability the current scheme does not use. Full month. OT 30 h on workdays. IE units 1,000. Attendance bonus earned. **Blocked** on TC-OPEN-9.

**Proves:** FR-63 (supplement per OT hour × factor, PIT-treated as OT), FR-26

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 30 h | 6,000,000 ÷ 208 × 150% × 30 | 1,298,077 |
| OT supplement 30 h | 3,846 × 150% × 30 | 173,070 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **9,471,147** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 9,471,147 − 1,471,147 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,841,147** |

SI base 6,000,000 · PIT-exempt 1,471,147 (OT and OT supplement) · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,881,147

## Group E: Adjustments and deductions (reference configuration)

Both cases use the skilled worker from TC-A02 with a normal month: full month, OT 20 h on workdays, IE units 1,000, attendance bonus earned.

### TC-E01 Correction to a locked period

**Given:** 4 h of workday OT worked in September 2026 were missed from the locked September run. September's contract pay was the same (6,000,000) and September OT stayed within the 40 h limit.

**Proves:** FR-30 (adjustment line naming its period, with its component's flags), FR-29, FR-51 (September is not reopened)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| Adjustment for September 2026: OT workday 4 h | 6,000,000 ÷ 208 × 150% × 4; PIT-free | 173,077 |
| **Gross pay** |  | **9,038,462** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 9,038,462 − 1,038,462 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,408,462** |

SI base unchanged at 6,000,000 (OT is outside it) · PIT-exempt 1,038,462 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,448,462 · The adjustment counts towards September's OT hours, not October's

### TC-E02 Damage deduction above the 30% cap

**Given:** A damage compensation of 3,000,000 approved under the work rules, to be deducted this month.

**Proves:** FR-31 (deduction capped at 30% of pay after insurance and PIT; the rest carries forward)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 4,500,000 |
| Skill allowance | Full month | 1,500,000 |
| OT workday 20 h | 6,000,000 ÷ 208 × 150% × 20 | 865,385 |
| Efficiency incentive | 1,000 units × 1,500 | 1,500,000 |
| Attendance bonus |  | 300,000 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **8,865,385** |
| Social insurance | 8% × 6,000,000 | −480,000 |
| Health insurance | 1.5% × 6,000,000 | −90,000 |
| Unemployment insurance | 1% × 6,000,000 | −60,000 |
| PIT | 8,865,385 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| Damage compensation | 30% × (8,865,385 − 630,000 − 0) = 2,470,615.5 | −2,470,616 |
| **Net pay** |  | **5,764,769** |

SI base 6,000,000 · PIT-exempt 865,385 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,275,385 · Carried to next month: 3,000,000 − 2,470,616 = 529,384 · The deduction does not change employer cost

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

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, Entry | 800,000 × 100% | 800,000 |
| OT workday 20 h | (3,700,000 + 800,000) ÷ 208 × 150% × 20 | 649,038 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| **Gross pay** |  | **5,449,038** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,449,038 − 649,038 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,060,538** |

SI base 3,700,000 (productivity pay is outside it) · OT hourly rate 4,500,000 ÷ 208 = 21,634.6154 · PIT-exempt 649,038 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,318,538

### TC-G02 S4 worker at target

**Given:** Certified S4. Full month. Attainment 100%. OT 30 h on workdays. Efficiency bonus entered 1,000,000.

**Proves:** FR-68, FR-15, FR-21 (productivity pay outside the SI base)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, S4 | 2,800,000 × 100% | 2,800,000 |
| OT workday 30 h | (3,700,000 + 2,800,000) ÷ 208 × 150% × 30 | 1,406,250 |
| Efficiency bonus | Entered (shadow mode) | 1,000,000 |
| **Gross pay** |  | **8,906,250** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 8,906,250 − 1,406,250 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,517,750** |

SI base 3,700,000 (productivity pay is outside it) · OT hourly rate 6,500,000 ÷ 208 = 31,250.0000 · PIT-exempt 1,406,250 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 9,775,750

### TC-G03 S4 worker below target

**Given:** As TC-G02, but the month's output reaches 80% of target. No efficiency bonus (below the incentive threshold).

**Proves:** FR-68 (attainment lowers the pay), FR-15 (the OT base follows the amount earned)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, S4 | 2,800,000 × 80% | 2,240,000 |
| OT workday 30 h | (3,700,000 + 2,240,000) ÷ 208 × 150% × 30 | 1,285,096 |
| Efficiency bonus | Below the incentive threshold | 0 |
| **Gross pay** |  | **7,225,096** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 7,225,096 − 1,285,096 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **6,836,596** |

SI base 3,700,000 (productivity pay is outside it) · OT hourly rate 5,940,000 ÷ 208 = 28,557.6923 · PIT-exempt 1,285,096 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 8,094,596

### TC-G04 Entry worker with two unexcused absences

**Given:** As TC-G01, with 2 days of unexcused absence: 24 paid days. Attainment on the 24 days worked: 100%.

**Proves:** FR-12, FR-61 (both lines by paid days), FR-15 (the OT base is not prorated)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 3,700,000 × 24/26 | 3,415,385 |
| Productivity pay, Entry | 800,000 × 24/26 × 100% | 738,462 |
| OT workday 20 h | (3,700,000 + 800,000) ÷ 208 × 150% × 20 | 649,038 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| **Gross pay** |  | **5,102,885** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,102,885 − 649,038 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **4,714,385** |

SI base 3,700,000 (productivity pay is outside it) · PIT-exempt 649,038 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 5,972,385 · The OT base is not prorated by paid days

### TC-G05 Entry worker with two days of annual leave

**Given:** As TC-G01, with 2 days of annual leave: 24 days worked, 26 paid days. Attainment on the days worked: 100%.

**Proves:** FR-61 (leave days are paid days for productivity pay too)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 26 paid days, full month | 3,700,000 |
| Productivity pay, Entry | 800,000 × 100% | 800,000 |
| OT workday 20 h | (3,700,000 + 800,000) ÷ 208 × 150% × 20 | 649,038 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| **Gross pay** |  | **5,449,038** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,449,038 − 649,038 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,060,538** |

SI base 3,700,000 (productivity pay is outside it) · PIT-exempt 649,038 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,318,538 · Same payslip as TC-G01: annual leave days are paid days for both lines

### TC-G06 S2 worker who spends part of the month training others

**Given:** Certified S2. Full month, no OT. 10 days training new workers (unmeasured work), 16 days on measured work at 100% of target. No efficiency bonus.

**Proves:** FR-68 (attainment counts measured work only, so training days neither raise nor lower it)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, S2 | 1,800,000 × 100% (16 measured days; 10 training days excluded) | 1,800,000 |
| **Gross pay** |  | **5,500,000** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,500,000 − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,111,500** |

SI base 3,700,000 (productivity pay is outside it) · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,369,500

### TC-G07 One-time bonus

**Given:** As TC-G01, plus a project completion bonus of 500,000 approved by the director.

**Proves:** FR-18, FR-69 (paid because approved), FR-29

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, Entry | 800,000 × 100% | 800,000 |
| OT workday 20 h | (3,700,000 + 800,000) ÷ 208 × 150% × 20 | 649,038 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| One-time bonus: project completion | Entered; approved by the director | 500,000 |
| **Gross pay** |  | **5,949,038** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,949,038 − 649,038 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,560,538** |

SI base 3,700,000 (productivity pay is outside it) · PIT-exempt 649,038 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,818,538

### TC-G08 Leaver who does not return her uniforms

**Given:** Entry worker; last working day is working day 20: 20 paid days, attainment 100%, no OT. Efficiency bonus entered 200,000. She does not return 2 uniform sets; the work-rules process decides compensation of 2 × 150,000 = 300,000.

**Proves:** FR-31 (damage compensation on a recorded decision, within the cap), FR-38, FR-70

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 3,700,000 × 20/26 | 2,846,154 |
| Productivity pay, Entry | 800,000 × 20/26 × 100% | 615,385 |
| Efficiency bonus | Entered (shadow mode) | 200,000 |
| **Gross pay** |  | **3,661,539** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 3,661,539 − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| Damage compensation: 2 uniform sets not returned | 300,000 per the work-rules decision; cap 30% × (3,661,539 − 388,500 − 0) = 981,911.7 | −300,000 |
| **Net pay** |  | **2,973,039** |

SI base 3,700,000 (20 working days, so the month is contributed) · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 4,531,039 · The deduction is within the cap, so nothing carries forward

### TC-G10 Line leader, full score

**Given:** G2 step 2, 8,000,000. Score 100%. Full month. OT 30 h on workdays. 1 dependent.

**Proves:** FR-04 (the grade and step amount split into base and performance pay), FR-68, FR-15 (OT on the full 8,000,000), FR-21 (SI base 3,700,000)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Performance pay | (8,000,000 − 3,700,000) × 100% | 4,300,000 |
| OT workday 30 h | (3,700,000 + 4,300,000) ÷ 208 × 150% × 30 | 1,730,769 |
| **Gross pay** |  | **9,730,769** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 9,730,769 − 1,730,769 exempt − 388,500 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **9,342,269** |

SI base 3,700,000 (performance pay is outside it) · OT hourly rate 8,000,000 ÷ 208 = 38,461.5385 · PIT-exempt 1,730,769 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 10,600,269

### TC-G11 Line leader, score 80%

**Given:** As TC-G10, with a score of 80%.

**Proves:** FR-68 (the score lowers the pay), FR-15 (the OT base follows the amount earned)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Performance pay | (8,000,000 − 3,700,000) × 80% | 3,440,000 |
| OT workday 30 h | (3,700,000 + 3,440,000) ÷ 208 × 150% × 30 | 1,544,712 |
| **Gross pay** |  | **8,684,712** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 8,684,712 − 1,544,712 exempt − 388,500 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,296,212** |

SI base 3,700,000 (performance pay is outside it) · OT hourly rate 7,140,000 ÷ 208 = 34,326.9231 · PIT-exempt 1,544,712 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 9,554,212

### TC-G12 QC staff

**Given:** G3 step 2, 10,000,000. Score 100%. Full month. OT 16 h on workdays.

**Proves:** FR-04, FR-68, FR-15

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Performance pay | (10,000,000 − 3,700,000) × 100% | 6,300,000 |
| OT workday 16 h | (3,700,000 + 6,300,000) ÷ 208 × 150% × 16 | 1,153,846 |
| **Gross pay** |  | **11,153,846** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 11,153,846 − 1,153,846 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **10,765,346** |

SI base 3,700,000 (performance pay is outside it) · OT hourly rate 10,000,000 ÷ 208 = 48,076.9231 · PIT-exempt 1,153,846 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 12,023,346

### TC-G13 Factory manager

**Given:** G6, 45,000,000 on the contract. Score 100%, entered by the director. Full month, no OT. 2 dependents.

**Proves:** FR-68 (director's score), FR-27, FR-28; the gap between declared income and SI base that Pay Policy §4.3 describes

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Performance pay | (45,000,000 − 3,700,000) × 100% | 41,300,000 |
| **Gross pay** |  | **45,000,000** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 45,000,000 − 388,500 insurance − 27,900,000 deduction = 16,711,500 taxable; 500,000 + 10% × 6,711,500 | −1,171,150 |
| **Net pay** |  | **43,440,350** |

SI base 3,700,000 (performance pay is outside it) · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 45,869,500 · The PIT return declares 45,000,000 of income against an SI base of 3,700,000 (Pay Policy §4.3)

### TC-G14 Entry worker with a salary advance

**Given:** As TC-G01. An advance of 1,500,000, approved and paid by bank on the 15th through a payment order.

**Proves:** FR-71 (the advance is settled on the month's payslip; the bank file pays only the remainder). Net pay, SI and PIT are the same as TC-G01: the advance is part of the month's pay, not a deduction.

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Productivity pay, Entry | 800,000 × 100% | 800,000 |
| OT workday 20 h | (3,700,000 + 800,000) ÷ 208 × 150% × 20 | 649,038 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| **Gross pay** |  | **5,449,038** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,449,038 − 649,038 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,060,538** |
| Advance settled | Advance paid on the 15th, approved | −1,500,000 |
| **Remaining to pay** |  | **3,560,538** |

SI base 3,700,000 (productivity pay is outside it) · PIT-exempt 649,038 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,318,538

Posting: the advance's payment booked Dr 3341 / Cr bank on the 15th; at approval the run posts the gross credit on 3341, and the employee's 3341 debits (insurance 388,500 and the advance 1,500,000) are reconciled against it, leaving 3,560,538 open for the payment order.

### TC-G15 Advance larger than the month's pay

**Given:** Entry worker. An advance of 2,000,000 paid on the 15th; she then takes 16 days of approved unpaid leave: 10 paid days, attainment 100%, no OT, no efficiency bonus.

**Proves:** FR-71 (settlement capped at net pay; the rest carries to the next month), FR-23 (no contributions with 16 days neither worked nor paid)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 3,700,000 × 10/26 | 1,423,077 |
| Productivity pay, Entry | 800,000 × 10/26 × 100% | 307,692 |
| **Gross pay** |  | **1,730,769** |
| PIT | 1,730,769 − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **1,730,769** |
| Advance settled | Advance paid on the 15th; capped at net pay | −1,730,769 |
| **Remaining to pay** |  | **0** |

No contributions: 16 working days neither worked nor paid · Employer contributions 0 · Employer cost 1,730,769 · Advance carried to next month: 2,000,000 − 1,730,769 = 269,231

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
