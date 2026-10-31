# Payroll Acceptance Test Cases

v0.2 · Oct 30, 2026 · @Peter

These cases define the payroll module's expected results to the dong. The module is accepted when it reproduces every unblocked case exactly (Payroll Requirements Specification §10). Each case also becomes an automated test.

v0.2 adds group G for the current scheme (Pay Policy §3, options A and B) and new cases for late arrivals, office leave, a probation clause, the Tet bonus, a new dependent, a manager without a labour contract, daily-paid pay and configurable checks. It makes the existing cases lawful and consistent with the policy (probation lengths, no union members by default, the line leader's travel allowance). Change log at the end.

**How to read a case**

- **Given:** the employee's contract pay, attendance totals, IE units and entered amounts. Anything not stated is zero or absent.
- **Expected:** every payslip line, the SI base, taxable income, PIT, net pay and employer cost, with the arithmetic shown so it can be checked by hand.
- **Proves:** the FR numbers the case covers.
- A case marked **Blocked** depends on an open decision; its figures follow the current proposal and must be rechecked once the decision is made.

**Two configurations.** Groups A–F run on the **reference configuration**, the v0.1 target policy (worker base 4,500,000 and so on), to prove the engine. Group G runs on the **current scheme**, the configuration that goes live. Group H will hold the accountant's actual payslips for the parallel month (Requirements OPEN-07).

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
| Base salary | 3,700,000 |
| Skill pay | S1 500,000 · S2 1,000,000 · S3 1,500,000 · S4 2,000,000; option A: in OT base only, paid on the month's result; option B: in SI and OT base |
| Travel and housing support | 800,000 a month, per day worked (800,000 ÷ 26 a day); outside both bases; taxable |
| OT supplement | 3,846 per OT hour × factor; PIT-treated as OT |
| Efficiency bonus | Entered amount (IE in shadow mode) |
| Attendance bonus | 300,000, same condition |

PIT on taxable income T in the 10–30M bracket = 500,000 + 10% × (T − 10M); in the 30–60M bracket = 2,500,000 + 20% × (T − 30M); in the 60–100M bracket = 8,500,000 + 30% × (T − 60M).

## Coverage

| Requirement | Cases |
| --- | --- |
| FR-12, FR-61 proration by basis | B02, B05, B06, C01, C03, C05, G05, G06 |
| FR-13, FR-35, FR-36 probation, hire | C01, C02, C06 |
| FR-14 OT and night pay | A01–A05, B01, B04, G01–G06 |
| FR-15 OT base from flagged components | A02, A04 (bonus outside); G02, G03 (conditional skill pay inside) |
| FR-16 efficiency incentive | A01, A02, B01 |
| FR-17, FR-64 attendance bonus, conditional components | A01 paid; B02, B05, G05 forfeited; B03, C05, G06 kept on leave; G02, G03 skill pay met and not met |
| FR-18, FR-29 entered bonuses, taxed when paid | A04–A09, D04 |
| FR-19 other earnings | A01 (travel), A05 (phone), G01 (support) |
| FR-21, FR-22 SI base, rates, caps | All; A09 SI cap; D01 UI cap; G02 vs G04 base by option |
| FR-23, FR-39 no contributions in long-absence months | C04, C05 |
| FR-25 union dues | A01 member; every other case non-member |
| FR-26 PIT exemptions | B01 OT over limit; A05 phone; C03 untaken leave; D03 meal cap; E01 adjusted OT; G01 OT supplement |
| FR-27, FR-28 PIT methods and dependents | A07–A09, D01, D05, D06 progressive; C01, D02, D07 flat 10% |
| FR-30 adjustments | E01 |
| FR-31 damage deduction cap | E02 |
| FR-32, FR-33 net pay, employer cost | All |
| FR-38 leaver | C03 |
| FR-60 contribution profile | C01 (probation contract), C06 (probation clause), D06 (manager) |
| FR-63 OT supplement | G01–G06 |
| FR-65 daily-paid | D07 |
| §7 validations, FR-02, FR-51, FR-59 | F01–F11 |

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
| TC-F10 | The travel and housing support flagged *in OT base* | Warning: a welfare item in the OT base; approval needs a note | §7 legal-nature check |
| TC-F11 | Option A skill pay paid in full for 6 months running | Warning: a conditional component that never failed its condition | §7, Pay Policy §3.5 |

## Group G: Current scheme (Pay Policy §3)

The go-live configuration for workers. G01, G05 and G06 are the same under options A and B; G02–G03 are option A, G04 option B. All non-members, 0 dependents.

### TC-G01 Entry worker

**Given:** Base 3,700,000, no skill level. Full month: 26 days worked. OT 20 h on workdays. Efficiency bonus entered 300,000. Attendance bonus earned.

**Proves:** FR-19, FR-61 (support per day worked), FR-63 (OT supplement, PIT-treated as OT). OT pays what it paid on a 4,500,000 base: 533,654 + 115,380 = 649,034, against 649,038 before (the 3,846 rate is rounded).

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Travel and housing support | 26 days worked | 800,000 |
| OT workday 20 h | 3,700,000 ÷ 208 × 150% × 20 | 533,654 |
| OT supplement 20 h | 3,846 × 150% × 20 | 115,380 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| Attendance bonus |  | 300,000 |
| **Gross pay** |  | **5,749,034** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,749,034 − 649,034 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,360,534** |

SI base 3,700,000 · OT hourly rate 3,700,000 ÷ 208 = 17,788.4615 · PIT-exempt 649,034 (OT and OT supplement) · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,618,534

### TC-G02 S4 worker, option A, level met

**Given:** Base 3,700,000; certified S4, and the month's result confirms S4. Full month. OT 30 h on workdays. Efficiency bonus entered 1,000,000. Attendance bonus earned.

**Proves:** FR-15 (conditional skill pay in the OT base), FR-21 (and outside the SI base), FR-64

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Skill performance pay S4 | Certified S4, met this month | 2,000,000 |
| Travel and housing support | 26 days worked | 800,000 |
| OT workday 30 h | 5,700,000 ÷ 208 × 150% × 30 | 1,233,173 |
| OT supplement 30 h | 3,846 × 150% × 30 | 173,070 |
| Efficiency bonus | Entered (shadow mode) | 1,000,000 |
| Attendance bonus |  | 300,000 |
| **Gross pay** |  | **9,206,243** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 9,206,243 − 1,406,243 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,817,743** |

SI base 3,700,000 (skill performance pay is outside it) · OT hourly rate 5,700,000 ÷ 208 = 27,403.8462 · PIT-exempt 1,406,243 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 10,075,743

### TC-G03 S4 worker, option A, level not met

**Given:** As TC-G02, but the month's result shows performance at S2, and HR confirms it.

**Proves:** FR-64 (the condition changes the amount), FR-15 (the OT base follows the amount earned)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Skill performance pay | Certified S4; performed at S2 this month, HR confirmed | 1,000,000 |
| Travel and housing support | 26 days worked | 800,000 |
| OT workday 30 h | 4,700,000 ÷ 208 × 150% × 30 | 1,016,827 |
| OT supplement 30 h | 3,846 × 150% × 30 | 173,070 |
| Efficiency bonus | Entered (shadow mode) | 1,000,000 |
| Attendance bonus |  | 300,000 |
| **Gross pay** |  | **7,989,897** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 7,989,897 − 1,189,897 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **7,601,397** |

SI base 3,700,000 · OT hourly rate 4,700,000 ÷ 208 = 22,596.1538 · PIT-exempt 1,189,897 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 8,859,397

### TC-G04 S4 worker, option B

**Given:** As TC-G02, with the skill amount as a fixed allowance in the SI base.

**Proves:** FR-21 (SI base includes the fixed allowance). Against TC-G02: the worker's net pay is 210,000 lower and the employer's cost 470,000 higher.

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | Full month | 3,700,000 |
| Skill allowance S4 | Full month | 2,000,000 |
| Travel and housing support | 26 days worked | 800,000 |
| OT workday 30 h | 5,700,000 ÷ 208 × 150% × 30 | 1,233,173 |
| OT supplement 30 h | 3,846 × 150% × 30 | 173,070 |
| Efficiency bonus | Entered (shadow mode) | 1,000,000 |
| Attendance bonus |  | 300,000 |
| **Gross pay** |  | **9,206,243** |
| Social insurance | 8% × 5,700,000 | −456,000 |
| Health insurance | 1.5% × 5,700,000 | −85,500 |
| Unemployment insurance | 1% × 5,700,000 | −57,000 |
| PIT | 9,206,243 − 1,406,243 exempt − 598,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,607,743** |

SI base 5,700,000 · OT hourly rate 5,700,000 ÷ 208 = 27,403.8462 · PIT-exempt 1,406,243 · Employer contributions 1,339,500 (997,500 SI + 171,000 HI + 57,000 UI + 114,000 union fee) · Employer cost 10,545,743

### TC-G05 Entry worker with two unexcused absences

**Given:** As TC-G01, with 2 days of unexcused absence: 24 days worked and 24 paid days. Attendance bonus forfeited.

**Proves:** FR-12, FR-61 (base by paid days, support by days worked), FR-17

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 3,700,000 × 24/26 | 3,415,385 |
| Travel and housing support | 800,000 × 24/26 days worked | 738,462 |
| OT workday 20 h | 3,700,000 ÷ 208 × 150% × 20 | 533,654 |
| OT supplement 20 h | 3,846 × 150% × 20 | 115,380 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| Attendance bonus | Forfeited | 0 |
| **Gross pay** |  | **5,102,881** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,102,881 − 649,034 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **4,714,381** |

SI base 3,700,000 · PIT-exempt 649,034 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 5,972,381

### TC-G06 Entry worker with two days of annual leave

**Given:** As TC-G01, with 2 days of annual leave: 24 days worked, 26 paid days. Attendance bonus kept. **Blocked** on Pay Policy OPEN-13 (support per day worked or per paid day).

**Proves:** FR-61 (two components, two bases in one payslip)

| Line | Calculation | Amount |
| --- | --- | --: |
| Base salary | 26 paid days, full month | 3,700,000 |
| Travel and housing support | 800,000 × 24/26 days worked | 738,462 |
| OT workday 20 h | 3,700,000 ÷ 208 × 150% × 20 | 533,654 |
| OT supplement 20 h | 3,846 × 150% × 20 | 115,380 |
| Efficiency bonus | Entered (shadow mode) | 300,000 |
| Attendance bonus | Kept | 300,000 |
| **Gross pay** |  | **5,687,496** |
| Social insurance | 8% × 3,700,000 | −296,000 |
| Health insurance | 1.5% × 3,700,000 | −55,500 |
| Unemployment insurance | 1% × 3,700,000 | −37,000 |
| PIT | 5,687,496 − 649,034 exempt − 388,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,298,996** |

SI base 3,700,000 · PIT-exempt 649,034 · Employer contributions 869,500 (647,500 SI + 111,000 HI + 37,000 UI + 74,000 union fee) · Employer cost 6,556,996 · With support paid per paid day instead, the support line is 800,000 and net pay 61,538 higher

## Assumptions to confirm and blocked cases

Writing the expected values surfaced these decisions. Each blocked case must be rechecked once its item is settled.

| ID | Item | Cases affected | Current assumption |
| --- | --- | --- | --- |
| TC-R1 | Rounding convention | All | Rates at full precision; lines rounded to VND, half up; totals from rounded lines |
| OPEN-02 (spec) | Travel allowance and supports: per day worked, per paid day, or not prorated | B02, B05, C01, C03, C05, G06 | Reference: travel not prorated. Current scheme: support per day worked |
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
| TC-OPEN-9 | PIT treatment of the OT supplement | G01–G06 | Exempt with OT, within the limits |
| TC-OPEN-10 | PIT method in a month that mixes a probation contract and a labour contract | C02 | Progressive for the whole month |

**Cases to add once decided**

- **TC-C07 Skill level changed mid-month** (FR-37): reference configuration, S2 from working day 14: 1,000,000 × 13/26 = 500,000. SI base and OT rate wait for OPEN-04.
- **TC-C08 Transfer from worker to line leader mid-month** (FR-40): salary split by date, incentive for the worker days only. SI base waits for OPEN-04.
- **TC-B07 Standard days from the month's schedule** (FR-62 variant): a 24-day February and a 27-day October, full attendance.
- **Group H, parallel month:** the accountant's payslips for the go-live parallel month, reproduced by the current-scheme configuration (Requirements OPEN-07).
- **Non-resident** (flat 20%) and **off-cycle payslip** (FR-11), if those situations arise.

**Turning these into automated tests:** each case's Given becomes a fixture, and each table row an assertion to the dong. The PIT exemption, SI base and employer contribution figures under each table are assertions too.

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-30 | First draft. |
| 0.2 | 2026-10-30 | Two configurations: reference (A–F) and current scheme (new group G, six cases). No union members by default (A01 stays a member), so net pay rises by the dues in A02–A07, B, C02, C03, D03 and E. A03 loses the travel allowance (workers only). C01 and C02 use lawful 30-day probation contracts; C06 adds a probation clause. New B05 (late arrivals), B06 (office unpaid leave), D04 (Tet bonus), D05 (new dependent), D06 (manager without a labour contract), D07 (daily-paid), F09–F11 (check levels and nature checks). TC-OPEN-6 to TC-OPEN-10 added. All figures generated and checked by script. |
