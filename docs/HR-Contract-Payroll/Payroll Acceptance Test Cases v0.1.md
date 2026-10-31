# Payroll Acceptance Test Cases

Oct 30, 2026 · @Peter

These cases define the payroll module's expected results to the dong. The module is accepted when it reproduces every unblocked case exactly (Payroll Requirements Specification §10). Each case also becomes an automated test.

**How to read a case**

- **Given:** the employee's contract pay, attendance totals, IE units and entered amounts. Anything not stated is zero or absent.
- **Expected:** every payslip line, the SI base, taxable income, PIT, net pay and employer cost, with the arithmetic shown so it can be checked by hand.
- **Proves:** the FR numbers the case covers.
- A case marked **Blocked** depends on an open decision; its figures follow the current proposal and must be rechecked once the decision is made.

**Rounding convention** (TC-R1, to confirm in technical design)

1. Rates such as the OT hourly rate are kept at full precision.
2. Each payslip line is rounded to whole VND (half up).
3. Gross pay, taxable income and net pay are sums of the rounded lines; PIT is calculated on that taxable income and rounded.

All expected values were worked out independently of the module's code, from the pay policy and the regulation reference.

## Common parameters (October 2026)

Every case uses these values unless it says otherwise. Values marked `[P]` are pay-policy placeholders.

| Parameter | Value |
| --- | --- |
| Region IV minimum wage | 3,700,000 |
| SI reference level | 2,530,000 |
| SI and HI salary cap (20 × 2,530,000) | 50,600,000 |
| UI salary cap (20 × 3,700,000) | 74,000,000 |
| Standard days; hours | 26 days; 26 × 8 = 208 hours |
| Employee rates | SI 8%, HI 1.5%, UI 1% |
| Employer rates | SI 17.5%, HI 3%, UI 1%, union fee 2% |
| Union dues (members) | 0.5% of SI base, max 253,000 |
| OT factors | Workday 150%, rest day 200%, holiday 300%; night +30%; night OT workday 200% (210% after daytime OT), rest day 270%, holiday 390% |
| OT monthly limit | 40 hours |
| PIT deductions | 15,500,000 self; 6,200,000 per dependent |
| PIT brackets (monthly taxable) | 5% to 10M; 10% to 30M; 20% to 60M; 30% to 100M; 35% above |
| Cash meal PIT-free cap | 1,200,000 |
| Worker base salary `[P]` | 4,500,000 |
| Skill allowance `[P]` | S1 500,000 · S2 1,000,000 · S3 1,500,000 |
| Incentive unit rate `[P]` | 1,500 per unit |
| Attendance bonus `[P]` | 300,000 |
| Travel allowance, workers `[P]` | 200,000 |
| Probation rate `[P]` | 85% |
| Salary scale `[P]` | Pay Policy §4.1 (e.g. G2 step 2 = 8,000,000) |

PIT on taxable income T in the 10–30M bracket = 500,000 + 10% × (T − 10M); in the 30–60M bracket = 2,500,000 + 20% × (T − 30M); in the 60–100M bracket = 8,500,000 + 30% × (T − 60M).

## Coverage

23 calculation cases and 8 validation cases cover the calculation and control requirements; 2 more are listed as blocked until their decisions are made.

| Requirement | Cases |
| --- | --- |
| FR-12 proration by paid days | B02, C01, C03, C05 |
| FR-13, FR-35, FR-36 probation, hire | C01, C02 |
| FR-14 OT and night pay | A01–A05, B01, B04 |
| FR-15 bonuses outside the OT base | A02 (incentive), A04 (KPI) |
| FR-16 efficiency incentive | A01, A02, B01 |
| FR-17 attendance bonus | A01 paid; B02 forfeited; B03, C05 kept on leave |
| FR-18 KPI bonus | A04–A09 |
| FR-19 other earnings | A01 (travel), A05 (phone) |
| FR-21, FR-22 SI base, rates, caps | All; A09 SI cap; D01 UI cap |
| FR-23, FR-39 no contributions in long-absence months | C04, C05 |
| FR-25 union dues | A01 member; A08 non-member |
| FR-26 PIT exemptions | B01 OT over limit; A05 phone; C03 untaken leave; D03 meal cap; E01 adjusted OT |
| FR-27, FR-28 PIT methods and dependents | A07–A09, D01 progressive; C01, D02 flat 10% |
| FR-30 adjustments | E01 |
| FR-31 damage deduction cap | E02 |
| FR-32, FR-33 net pay, employer cost | All |
| FR-38 leaver | C03 |
| §7 validations, FR-02, FR-51 | F01–F08 |

**Not yet covered:** non-resident flat 20% (no such employee planned), FR-37 mid-month pay changes and FR-40 transfers (blocked, see the last section), off-cycle payslips (FR-11).

## Group A: Baseline payslips

Full-month payslips for the nine profiles under the pay policy structure. Office and management roles carry no position allowance (Pay Policy §4); canteen meals are not on the payslip.

### TC-A01 Entry worker

**Given:** Worker, base salary only. Union member, 0 dependents. Full month: 26 of 26 days. OT 20 h on workdays. IE units 200. Attendance bonus earned.

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

**Given:** Worker, base 4,500,000 + skill allowance S3 1,500,000. Union member, 0 dependents. Full month. OT 30 h on workdays. IE units 1,000. Attendance bonus earned.

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 9,298,077 − 1,298,077 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,638,077** |

SI base 6,000,000 · OT hourly rate 6,000,000 ÷ 208 = 28,846.1538 · PIT-exempt 1,298,077 · Employer contributions 1,410,000 (1,050,000 SI + 180,000 HI + 60,000 UI + 120,000 union fee) · Employer cost 10,708,077

### TC-A03 Line leader

**Given:** G2 step 2, 8,000,000. Outside the IE incentive. Union member, 1 dependent. Full month. OT 30 h on workdays. Travel allowance.

**Proves:** FR-14, FR-28

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 8,000,000 |
| OT workday 30 h | 8,000,000 ÷ 208 × 150% × 30 | 1,730,769 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **9,930,769** |
| Social insurance | 8% × 8,000,000 | −640,000 |
| Health insurance | 1.5% × 8,000,000 | −120,000 |
| Unemployment insurance | 1% × 8,000,000 | −80,000 |
| Union dues | 0.5% × 8,000,000 | −40,000 |
| PIT | 9,930,769 − 1,730,769 exempt − 840,000 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **9,050,769** |

SI base 8,000,000 · OT hourly rate 8,000,000 ÷ 208 = 38,461.5385 · PIT-exempt 1,730,769 · Employer contributions 1,880,000 (1,400,000 SI + 240,000 HI + 80,000 UI + 160,000 union fee) · Employer cost 11,810,769

### TC-A04 QC staff

**Given:** G3 step 2, 10,000,000. Union member, 0 dependents. Full month. OT 16 h on workdays. KPI bonus 1,000,000 entered.

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
| Union dues | 0.5% × 10,000,000 | −50,000 |
| PIT | 12,153,846 − 1,153,846 exempt − 1,050,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **11,053,846** |

SI base 10,000,000 · OT hourly rate 10,000,000 ÷ 208 = 48,076.9231 · PIT-exempt 1,153,846 · Employer contributions 2,350,000 (1,750,000 SI + 300,000 HI + 100,000 UI + 200,000 union fee) · Employer cost 14,503,846

### TC-A05 QC senior

**Given:** G4 step 2, 14,000,000. Union member, 0 dependents. Full month. OT 8 h on workdays. KPI bonus 1,500,000. Phone lump-sum 200,000.

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
| Union dues | 0.5% × 14,000,000 | −70,000 |
| PIT | 16,507,692 − 1,007,692 exempt − 1,470,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **14,967,692** |

SI base 14,000,000 · OT hourly rate 14,000,000 ÷ 208 = 67,307.6923 · PIT-exempt 1,007,692 (OT 807,692 + phone 200,000) · Employer contributions 3,290,000 (2,450,000 SI + 420,000 HI + 140,000 UI + 280,000 union fee) · Employer cost 19,797,692

### TC-A06 QC manager

**Given:** G5 step 2, 17,000,000. Union member, 1 dependent. Full month, no OT. KPI bonus 3,000,000. Phone lump-sum 500,000.

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
| Union dues | 0.5% × 17,000,000 | −85,000 |
| PIT | 20,500,000 − 500,000 exempt − 1,785,000 insurance − 21,700,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **18,630,000** |

SI base 17,000,000 · PIT-exempt 500,000 · Employer contributions 3,995,000 (2,975,000 SI + 510,000 HI + 170,000 UI + 340,000 union fee) · Employer cost 24,495,000

### TC-A07 Chief accountant

**Given:** G5 step 3, 18,000,000. Union member, 0 dependents. Full month. KPI bonus 2,000,000. Phone lump-sum 300,000. The first profile that pays PIT.

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
| Union dues | 0.5% × 18,000,000 | −90,000 |
| PIT | 20,300,000 − 300,000 exempt − 1,890,000 insurance − 15,500,000 deduction = 2,610,000 taxable; 5% × 2,610,000 | −130,500 |
| **Net pay** |  | **18,189,500** |

SI base 18,000,000 · PIT-exempt 300,000 · Employer contributions 4,230,000 (3,150,000 SI + 540,000 HI + 180,000 UI + 360,000 union fee) · Employer cost 24,530,000

### TC-A08 Factory manager

**Given:** G6, 45,000,000 on the contract. Not a union member, 2 dependents. Full month. KPI bonus 8,000,000. Phone lump-sum 1,000,000.

**Proves:** FR-25 (non-member, no dues), FR-27, FR-28

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

**Given:** G6, 70,000,000 on the contract. Not a union member, 1 dependent. Full month. KPI bonus 15,000,000. Phone lump-sum 2,000,000.

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

## Group B: Attendance, overtime and night work

All four cases use the skilled worker from TC-A02 (base 4,500,000 + skill S3 1,500,000, union member, 0 dependents) with different attendance.

### TC-B01 Peak month above the OT limit

**Given:** Full month. OT 36 h on workdays and 16 h on Sundays: 52 h, 12 h over the 40 h monthly limit. IE units 1,200. Attendance bonus earned.

**Proves:** FR-14 (rest-day rate), FR-26 (OT over the limit is taxable pro rata); the §7 OT warning fires.

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 10,780,769 − 1,908,284 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **10,120,769** |

OT pay 2,480,769; exempt share 2,480,769 × 40/52 = 1,908,284; taxable OT 572,485 · SI base 6,000,000 · Employer contributions 1,410,000 · Employer cost 12,190,769

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 8,184,616 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **7,524,616** |

SI base 6,000,000 · Employer contributions 1,410,000 · Employer cost 9,594,616

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 8,790,385 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,130,385** |

SI base 6,000,000 · Employer contributions 1,410,000 · Employer cost 10,200,385

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 9,401,924 − 1,401,924 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,741,924** |

SI base 6,000,000 · Employer contributions 1,410,000 · Employer cost 10,811,924

## Group C: Mid-month events

### TC-C01 New hire on probation

**Given:** Worker on a separate 2-month probation contract at 85% of base salary, starting on working day 14: 13 paid days of 26. No IE units yet. No attendance bonus in the first, partial month. **Blocked** on OPEN-02 (travel allowance unprorated) and TC-OPEN-1 (attendance bonus in partial months).

**Proves:** FR-13, FR-35, FR-23 (no SI on a probation contract), FR-27 (flat 10% applies only from 5,000,000)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | 4,500,000 × 85% × 13/26 | 1,912,500 |
| Travel allowance |  | 200,000 |
| **Gross pay** |  | **2,112,500** |
| SI, HI, UI, union dues | Probation contract: none | 0 |
| PIT (flat 10%) | Payment 2,112,500 is under 5,000,000: no withholding | 0 |
| **Net pay** |  | **2,112,500** |

No SI base · Employer contributions 0 · Employer cost 2,112,500

### TC-C02 Probation ends mid-month

**Given:** Worker with no skill allowance. Probation ends after working day 10; the labour contract starts on working day 11 (16 days). Full month attended. IE units 300. Attendance bonus earned.

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
| Union dues | 0.5% × 4,500,000 | −22,500 |
| PIT (progressive) | 5,190,385 − 472,500 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **4,695,385** |

SI base 4,500,000 · Employer contributions 1,057,500 (787,500 SI + 135,000 HI + 45,000 UI + 90,000 union fee) · Employer cost 6,247,885

Assumption to confirm with the SI office: a labour contract starting mid-month with 14 or more working days in the month contributes for the whole month.

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 6,407,693 − 1,153,846 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **5,747,693** |

SI base 6,000,000 (18 working days, so the month is contributed) · Employer contributions 1,410,000 · Employer cost 7,817,693 · Paid within 14 working days of the last day

### TC-C04 Maternity leave all month

**Given:** Skilled worker (base + S3) on maternity leave for the whole month: 0 days worked, 0 paid days. **Blocked** on OPEN-03.

**Proves:** FR-23, FR-39

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary and skill allowance | 6,000,000 × 0/26 | 0 |
| SI, HI, UI | Not working and not paid for 14 days or more: no contribution | 0 |
| Union dues | Exempt while on leave without pay from the company | 0 |
| **Net pay** |  | **0** |

Employer contributions 0 (the SI fund pays the HI contribution during maternity leave) · The employee appears on the SI change report as on maternity leave.

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
| SI, HI, UI, union dues | 15 working days not worked and not paid by the company: no contribution | 0 |
| PIT | 3,488,461 − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **3,488,461** |

Employer contributions 0 · Employer cost 3,488,461 · The SI fund pays the sick-leave benefit separately.

## Group D: Caps, tax methods and exempt income

### TC-D01 Both insurance caps

**Given:** G6 executive, 80,000,000 on the contract. Not a union member, 0 dependents. Full month, nothing else.

**Proves:** FR-21 (SI and HI capped at 50,600,000; UI capped at 74,000,000), FR-28 (30% bracket)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 80,000,000 |
| **Gross pay** |  | **80,000,000** |
| Social insurance | 8% × 50,600,000 | −4,048,000 |
| Health insurance | 1.5% × 50,600,000 | −759,000 |
| Unemployment insurance | 1% × 74,000,000 | −740,000 |
| PIT | 80,000,000 − 5,547,000 insurance − 15,500,000 deduction = 58,953,000 taxable; 2,500,000 + 20% × 28,953,000 | −8,290,600 |
| **Net pay** |  | **66,162,400** |

Employer contributions 12,125,000 (8,855,000 SI + 1,518,000 HI + 740,000 UI + 1,012,000 union fee) · Employer cost 92,125,000

### TC-D02 Short contract, flat 10% PIT

**Given:** Seasonal worker on a 2-month labour contract, 6,000,000 a month, full month. No commitment form filed. Not a union member.

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

Employer contributions 1,410,000 · Employer cost 7,410,000

To confirm with the tax advisor: whether the 10% applies before or after employee insurance (shown here on gross), and UI coverage of 1–3 month contracts under the Employment Law 2025. If the employee files the commitment form, PIT is 0.

### TC-D03 Cash meal allowance above the cap

**Given:** QC staff (G3 step 2, 10,000,000), union member, 0 dependents, full month. Cash meal allowance 1,500,000. Configuration test only: the pay policy provides meals in kind.

**Proves:** FR-26 (meal exempt only up to 1,200,000)

| Line | Calculation | Amount |
| --- | --- | --: |
| Salary | Full month | 10,000,000 |
| Cash meal allowance | PIT-free up to 1,200,000; 300,000 taxable | 1,500,000 |
| **Gross pay** |  | **11,500,000** |
| Social insurance | 8% × 10,000,000 | −800,000 |
| Health insurance | 1.5% × 10,000,000 | −150,000 |
| Unemployment insurance | 1% × 10,000,000 | −100,000 |
| Union dues | 0.5% × 10,000,000 | −50,000 |
| PIT | 11,500,000 − 1,200,000 exempt − 1,050,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **10,400,000** |

Taxable income before deductions 10,300,000 · SI base 10,000,000 (meal allowance outside it) · Employer contributions 2,350,000 · Employer cost 13,850,000

## Group E: Adjustments and deductions

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 9,038,462 − 1,038,462 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| **Net pay** |  | **8,378,462** |

SI base unchanged at 6,000,000 (OT is outside it) · Employer contributions 1,410,000 · Employer cost 10,448,462 · The adjustment counts towards September's OT hours, not October's.

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
| Union dues | 0.5% × 6,000,000 | −30,000 |
| PIT | 8,865,385 − 865,385 exempt − 630,000 insurance − 15,500,000 deduction → below zero, no tax | 0 |
| Damage compensation | 30% × (8,865,385 − 630,000 − 0) = 2,470,615.5 | −2,470,616 |
| **Net pay** |  | **5,734,769** |

Carried to next month: 3,000,000 − 2,470,616 = 529,384 · Employer cost 10,275,385 (the deduction does not change it)

## Group F: Validations

Each case sets up one fault in an otherwise valid run and checks the module's response.

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

## Assumptions to confirm and blocked cases

Writing the expected values surfaced these decisions. Each blocked case must be rechecked once its item is settled.

| ID | Item | Cases affected | Current assumption |
| --- | --- | --- | --- |
| TC-R1 | Rounding convention | All | Rates at full precision; lines rounded to VND; totals from rounded lines |
| OPEN-02 (spec) | Travel allowance prorated by paid days? | B02, C01, C03, C05 | Not prorated |
| OPEN-03 (spec) | No-contribution rule for 14 or more unpaid working days, and HI during sick leave | C04, C05 | No SI, HI or UI that month |
| OPEN-04 (spec) | Month from which a changed SI base applies | Blocked cases below | – |
| TC-OPEN-1 (new) | Attendance bonus for a partial month (new hire, leaver) | C01, C03 | Not paid |
| TC-OPEN-2 (new) | SI for a labour contract starting mid-month | C02 | Whole month contributed when 14 or more working days fall under the contract |
| TC-OPEN-3 (new) | Flat 10% PIT: on gross or after employee insurance; UI for 1–3 month contracts | D02 | On gross; UI applies |
| TC-OPEN-4 (new) | Pay basis for untaken annual leave | C03 | Contract salary of the month before leaving (Decree 145 Art. 67) |
| TC-OPEN-5 (new) | Night OT factors (200% / 210% / 270% / 390%) | B04 | As in Decree 145 Art. 57; confirm with the accountant |

**Cases to add once decided**

- **TC-C06 Skill allowance granted mid-month** (FR-37): S2 from working day 14. Earnings: 1,000,000 × 13/26 = 500,000. SI base and OT rate wait for OPEN-04.
- **TC-C07 Transfer from worker to line leader mid-month** (FR-40): salary split by date, incentive for the worker days only. SI base waits for OPEN-04.
- **Non-resident** (flat 20%) and **off-cycle payslip** (FR-11), if those situations arise.

**Turning these into automated tests:** each case's Given becomes a fixture, and each table row an assertion to the dong. The PIT exemption, SI base and employer contribution figures under each table are assertions too.
