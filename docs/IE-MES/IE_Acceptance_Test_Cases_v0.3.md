# IE Module — Acceptance Test Cases

**Version:** v0.3 · 2026-10-19
**Based on:** `IE_Business_Logic_Spec_v0.6.md` (rules of record), `IE_Framework_Rationale_v0.6.md` (worked numbers), `IE_Module_Function_Map.md` v0.8 (v1 scope)
**Companion:** `ie_reference_calc.py` (reference calculator that computes and checks every calculated case)
**Purpose:** Turns the business logic into concrete input → expected-output cases. **The Odoo implementation is correct when it reproduces them.** If this document and the spec disagree, the spec wins and this document is corrected.

---

## How to use this document

**Case format.** Each case has an ID, the spec sections it tests, a type, and *Given → When → Then*.

| Type | Meaning |
|------|---------|
| **Calc** | Numeric. The expected values are computed and checked by `ie_reference_calc.py`. |
| **Rule** | Behaviour (what the system allows, blocks, records or flags). Checked by a functional test or by hand. |
| ⚠ **Provisional** | Depends on an open item. Expected result follows the current spec text and may change when the item is decided. |

**Priority**

| Priority | Meaning | Cases |
|----------|---------|-------|
| **P1** | Core pay chain and the shadow-mode switch. **Must pass before shadow mode starts.** | 17 |
| **P2** | Remaining pay logic and edge cases, skill rules, changeover, payroll feed, self-funding check. Build early in shadow mode, because calibration uses this data; **must pass before the incentive is switched on.** | 31 |
| **P3** | Operational features with no pay effect: balancing, targets, real-time monitoring. Follow the build order. | 8 |

P1 checklist: TC-TA-01 to 05 · TC-EM-01, 03, 07 · TC-MET-01 · TC-SK-01 · TC-INC-01 to 04, 07, 09, 12.

**Running the reference calculator**
```
python ie_reference_calc.py                                        # all calculated cases
python ie_reference_calc.py --doc IE_Acceptance_Test_Cases_v0.3.md  # also checks this document shows the same values
```

**Conventions**
1. **Parameters:** all cases use parameter set **P0** (Fixture F4), the spec placeholders at baseline. A case that uses another value says so.
2. **Precision:** calculations run at full precision; rounding is for display only. A result passes when it rounds to the value shown (half a unit of the last digit shown).
3. **Times** are server times. Minutes are attended minutes unless stated.
4. **Pay period** = one calendar month (spec §11.1). The fixture month has 26 working days.
5. **Changes:** when a rule changes, the spec, the rationale, this document and the calculator's expected values are updated in the same batch (function map, *Document set & workflow*).

---

## Common fixtures

### F1 · Style PS-01 (polo shirt), sewing OB

| # | Operation | Family | Grade | Machine class | Skill-evaluated | SAM |
|---|-----------|--------|-------|---------------|-----------------|-----|
| 1 | Placket attach | Placket setting | A | SNLS | yes | 1.60 |
| 2 | Shoulder join | Seam join | C | OL | yes | 0.60 |
| 3 | Collar attach | Collar setting | A | SNLS | yes | 1.80 |
| 4 | Sleeve attach | Sleeve setting | B | OL | yes | 1.40 |
| 5 | Side seam | Seam join | C | OL | yes | 1.20 |
| 6 | Sleeve hem | Hemming | C | FL | yes | 0.90 |
| 7 | Bottom hem | Hemming | C | FL | yes | 0.80 |
| 8 | Buttonhole & button sew | Buttonholing | C | BH (automatic) | **no** | 1.70 |
| | **Garment SAM** | | | | | **10.00** |

### F2 · Line 1
- 30 operators; 480 attended minutes per day (08:00–12:00 and 13:00–17:00; lunch unpaid).
- Plateau for polos P = 80% (overall basis). Runs PS-01 every week.
- Station layout (30 operators): Placket 5 · Shoulder 2 · Collar 5 · Sleeve 4 · Side seam 4 · Sleeve + bottom hem (combined) 5 · Buttonhole 5.

### F3 · Operators

| Operator | Levels at period start | Tier |
|----------|------------------------|------|
| A — steady | Seam join U, Hemming U | T2 |
| B — learner | Hemming U; Sleeve setting I (new, no earned minutes yet) | T1 |
| C — floater | U in Placket, Collar, Sleeve, Pocket, Cuff setting and Hemming (2 Grade A; SNLS, OL, FL); also runs buttonhole (not skill-evaluated) | T4 |

### F4 · Parameter set P0

| Parameter | Value | Parameter | Value |
|-----------|-------|-----------|-------|
| θ | 0.70 | θ_floor | 0.30 |
| k_def | 1.0 | PF (I / L / U, O / not skill-evaluated) | 1.25 / 1.10 / 1.00 / 1.00 |
| PF_cap per grade (A / B / C) | 2,400 / 2,400 / 2,400 EM per family, cumulative, no reset | M_tier (T1–T4) | 1.00 / 1.05 / 1.10 / 1.20 |
| ILUO L | Eff ≥ 55%, DR ≤ 3.0% | ILUO U | Eff ≥ 80%, DR ≤ 1.5% |
| ILUO O | U for 2 consecutive evaluations, Eff ≥ 95% | Minimum volume | 600 EM_g per family per window |
| Dormancy | 180 days | Familiarity bands | R0 ≥ 90%, R1 60–90%, R2 < 60% |
| Ramp R1 | 0.75 → 0.90 → 1.00 | Ramp R2 | 0.500 → 0.6875 → 0.875 → 1.00 |
| Ramp R3 | 0.40 → 0.55 → 0.70 → 0.85 → 0.95 → 1.00 | Ramp ends at | r ≥ 0.95 |
| Fitted profile needs | 10 runs | Run plateau | from day 6, min 5 days |
| Real-time window W | 60 min | Starved exclusion | > 10% of W |
| Alerts | line < 85%; OS pending > 30 min; bundle open > 3 × SAM × qty; starved > 15 min | WIP cap | 3 bundles |
| Minimum attendance flag | 80% of scheduled days | | |


---

## Coverage index

| Area | Cases | Function map items |
|------|-------|--------------------|
| 1. Time accounting & data quality | TC-TA-01 … 08 | 5.5, 5.7, 6.1, 7.6 |
| 2. Earned minutes, defects, repair, SAM versions | TC-EM-01 … 09 | 2.2, 2.3, 5.1, 5.2, 5.6, 6.2, 7.5 |
| 3. Metrics | TC-MET-01 … 03 | 6.3 |
| 4. Skill matrix & tiers | TC-SK-01 … 08 | 6.4, 6.5 |
| 5. Incentive chain | TC-INC-01 … 12 | 6.6, 6.7, 7.1–7.4, 7.7 |
| 6. Style changeover | TC-CO-01 … 06 | 4.5 |
| 7. Balancing, targets, allocation | TC-BAL-01 … 03 | 4.1–4.4, 4.6 |
| 8. Real-time monitoring | TC-RT-01 … 05 | 9.1–9.7 |
| 9. Self-funding check & payroll feed | TC-SF-01, TC-PAY-01 | 7.8, 7.9 |

---

## 1. Time accounting and data quality

### TC-TA-01 · Normal day with two off-standard records
**Spec:** §3.1–3.3 · **Type:** Calc · **Priority:** P1
- **Given:** Operator A attends 480 min. Her machine breaks down mid-bundle; she pauses the bundle with reason OS-01 for 25 min and the leader approves (channel 1). Later the leader enters OS-03 "waiting for work" for her, 20 min (channel 2).
- **Then:** OS = **45**; NAM = 480 − 45 = **435**. Both records sit in the same bucket with code, approver and channel; downstream figures do not depend on the channel.

### TC-TA-02 · Day of pure downtime
**Spec:** §3.1 · **Type:** Calc · **Priority:** P1
- **Given:** A = 480; a power outage (OS-04) approved for the whole day, 480 min.
- **Then:** NAM = **0**. The day adds nothing to the monthly numerator or denominator, and the threshold for that day is 0.

### TC-TA-03 · Unapproved pause stays in NAM
**Spec:** §3.3 rule 1 · **Type:** Calc · **Priority:** P1
- **Given:** A = 480. The operator pauses a bundle for 30 min with reason OS-02; the leader never approves it.
- **Then:** OS = 0, NAM = **480**. The pause appears on the data-quality exception list as *unapproved pause* (TC-TA-06) until resolved before payroll close.

### TC-TA-04 · No overlaps: off-standard pauses the open bundle
**Spec:** §3.3 rule 2 · **Type:** Calc + Rule · **Priority:** P1
- **Given:** The operator has a bundle active from 09:00. The leader enters OS-03 for her from 09:30 to 09:50. She resumes the bundle at 09:50 and finishes at 10:00.
- **Then:**
  - The bundle is paused automatically at 09:30. Bundle active minutes = **40**; OS = **20**. No minute is counted twice.
  - A second off-standard record overlapping 09:30–09:50 for the same operator is **rejected**.
  - Starting or resuming any bundle while the operator is in an off-standard period is **rejected** (FLAG-TECH-07).

### TC-TA-05 · Off-standard counts only inside attendance
**Spec:** §3.3 rule 3, §3.4 · **Type:** Calc · **Priority:** P1
- **Given:** Attendance 08:00–12:00 and 13:00–17:00, so A = **480**. The leader enters OS-02 (material wait) 16:40–17:20; the operator clocked out at 17:00.
- **Then:** OS counted = **20** (16:40–17:00); NAM = **460**.

### TC-TA-06 · Data-quality exception list
**Spec:** §3.4 item 5 · **Type:** Rule · **Priority:** P2
- **Given / Then:** each of the following creates one exception for the supervisor, which must be cleared before payroll close:

| Situation | Exception |
|-----------|-----------|
| Bundle scan at 17:25, operator clocked out at 17:00 | Scan outside attendance |
| Operator-day with bundle active 470 min and NAM 435 | Bundle coverage (M7) above 100% |
| Bundle still active when the operator clocks out | Bundle open at clock-out |
| Work-order pause with reason, not approved | Unapproved pause |

- Payroll close for the period is **blocked** (or warned, technical choice) while exceptions are open.

### TC-TA-07 · Optional nightly pause job
**Spec:** §3.4 item 3 · **Type:** Rule · **Priority:** P2
- **Given:** Nightly job enabled. A bundle is still active at the job's run time.
- **Then:** The bundle is paused at the time the job runs, and the case still appears as *bundle open at clock-out* (TC-TA-06). With the job disabled, nothing is paused automatically, including at lunch and shift end.

### TC-TA-08 · Bundle spanning lunch ⚠ Two options (OPEN-15, decided during technical design)
**Spec:** §3.4 item 4 · **Type:** Rule · **Priority:** P2
- **Given:** Bundle started 11:50, finished 13:10; lunch 12:00–13:00 is unpaid.
- **Then:** A, OS and NAM are unaffected under either option (attendance is the master clock for pay). Bundle time depends on the option chosen:

| Option (spec §3.4 item 4) | Bundle minutes | Follow-up |
|---|---|---|
| (A) No clipping | 80 | Family split and diagnostics see 80 minutes; the case is caught by the exception list (TC-TA-06) if it pushes coverage above 100% or the bundle stays open at clock-out |
| (B) Only inside attendance | 20 | Corrects itself; no exception needed for the lunch hour |

- Once the option is chosen, this case keeps only the matching row.

---

## 2. Earned minutes, defects, repair and SAM versions

### TC-EM-01 · Earned minutes with a defect found today from yesterday's work
**Spec:** §2, §9.3 · **Type:** Calc · **Priority:** P1
- **Given:** Operator A completes 14 side-seam bundles of 20 pieces (280 pcs, SAM 1.20). QC today records 3 defective pieces from her side seam of *yesterday*, responsibility = operator.
- **Then:** EM_g = **336.0**; DD = 3 × 1.20 × 1.0 = **3.6**, booked **today** (detection date); EM_n = **332.4**. Yesterday's figures are unchanged.

### TC-EM-02 · Defect found after month-end
**Spec:** §9.3 · **Type:** Rule · **Priority:** P2
- **Given:** October is closed. On 3 November QC finds 5 defective pieces from an October bundle, attributed to Operator A.
- **Then:** The deduction is booked in **November**. October is not reopened or recalculated.

### TC-EM-03 · Defect records cannot exceed the bundle quantity
**Spec:** §9.3 · **Type:** Calc · **Priority:** P1
- **Given:** Bundle of 20, side seam (SAM 1.20), Operator A. Defect record 1: 15 pcs. Defect record 2 (later inspection): 10 pcs.
- **Then:**
  - Record 1 is accepted: **15** pcs, DD = **18.0**.
  - Record 2 is **rejected with an error** (15 + 10 > 20) and returned to QC. Nothing of it is booked; DD stays **18.0**.
  - If QC corrects record 2 to 5 pcs, it is accepted and total DD = 20 × 1.20 = **24.0**.
- How and where the check runs is decided in technical design (FLAG-TECH-13).

### TC-EM-04 · Defects not attributable to an operator
**Spec:** §9.2 · **Type:** Rule · **Priority:** P2
- **Given:** (a) A defect with responsibility = *material*. (b) A final-audit defect that cannot be traced to an operation.
- **Then:** (a) No operator deduction; counted in quality analytics by responsibility. (b) Attributed to the **line**, no operator deduction.

### TC-EM-05 · Deduction on not-skill-evaluated work
**Spec:** §9.3 · **Type:** Calc · **Priority:** P2
- **Given:** 5 defective buttonholes (SAM 1.70) attributed to Operator C.
- **Then:** DD = **8.5**. Deductions apply to all families, skill-evaluated or not.

### TC-EM-06 · Repair is neutral; failed repair
**Spec:** §9.4–9.5 · **Type:** Rule · **Priority:** P2
- **Given:** Operator B repairs the 3 pieces from TC-EM-01: repair record 14:00–14:12.
- **Then:**
  - B gets an OS-05 record of 12 min automatically (channel 3). B earns no EM for the repair and has no deduction.
  - Operator A's DD stays 3.6; the repair does not restore it.
  - Re-inspection **pass** closes the defect. Re-inspection **fail** sends it back to repair with no further deduction for A; the repeat is counted as a repairer diagnostic (OPEN-06).

### TC-EM-07 · SAM version used by production records
**Spec:** §5.2, §5.4 · **Type:** Calc · **Priority:** P1
- **Given:** Sleeve attach SAM 1.40. A standard-error dispute is upheld on 12 November; new SAM 1.55, effective from the start of the current pay period (1 November). Records: 100 pcs completed 30 October; 100 pcs completed 5 November.
- **Then:** October record = **140.0** EM (keeps 1.40; closed period untouched). November record = **155.0** EM (recalculated under the approved retroactive amendment).
- **Variant:** if the cause was a buyer spec change dated 20 November, the 5 November record stays at 140.0 and only records completed from 20 November use 1.55.

### TC-EM-08 · Record date and time category from the finish timestamp
**Spec:** §8 rule 5 · **Type:** Rule · **Priority:** P2
- **Given:** A bundle started 16:40 (normal time) and finished 17:20 (weekday overtime).
- **Then:** The whole record is dated on the finish day. A bundle started 23:50 and finished 00:20 belongs to the later day. (The finish time also gives the record's time category, overtime here; the incentive does not use it in v1, spec §11.5.)

### TC-EM-09 · Mid-bundle reassignment
**Spec:** §8 rule 3 · **Type:** Rule · **Priority:** P2
- **Given:** Operator X starts a 20-piece bundle and leaves sick. A supervisor reassigns the bundle; Operator Y finishes it.
- **Then:** X's production record is deleted; Y is credited the full 20 pieces. An audit log entry records supervisor, time, both operators and the bundle. The action is unavailable to line leaders and operators.

---

## 3. Metrics

### TC-MET-01 · Operator A's day
**Spec:** §4 · **Type:** Calc · **Priority:** P1
- **Given:** A = 480, OS = 45, NAM = 435, EM_g = 336.0, EM_n = 332.4 (TC-TA-01, TC-EM-01). Bundle active minutes from scans = 390.
- **Then:**

| Metric | Expected |
|--------|----------|
| M1 on-standard efficiency (EM_n ÷ NAM) | **76.4%** |
| M3 overall efficiency (EM_g ÷ A) | **70.0%** |
| On-standard, gross basis (EM_g ÷ NAM) | **77.2%** |
| M5 off-standard ratio | **9.4%** |
| M6 pace (EM_g ÷ bundle minutes) | **86.2%** |
| M7 bundle coverage (bundle minutes ÷ NAM) | **89.7%** |
| Identity check: 77.2% × (1 − 9.4%) = M3 | **70.0%** |

### TC-MET-02 · Sloppy scanning does not change pay
**Spec:** DEC-02, §4 · **Type:** Calc · **Priority:** P2
- **Given:** Same day as TC-MET-01, but scans show only 300 bundle minutes.
- **Then:** M6 = **112.0%**, M7 = **69.0%** (both diagnostics move); M1 stays **76.4%**, so the incentive is unchanged. Low coverage shows up in scanning-discipline monitoring.

### TC-MET-03 · Line reconciliation (operators A, B and C, one month)
**Spec:** §4 (incl. note C-5) · **Type:** Calc · **Priority:** P2
- **Given:** The monthly figures of TC-INC-02, TC-INC-03 and TC-INC-04.
- **Then:**

| | Expected |
|--|----------|
| Σ A | **38,640** |
| Σ OS | **950** (breakdown 350, waiting 300, material 200, meeting 100) |
| Σ NAM | **37,690** |
| Σ EM_g | **27,740** |
| Σ DD | **110** |
| Σ EM_n | **27,630** |
| M4 line on-standard (gross) | **73.6%** |
| Operators' pooled M1 (net) | **73.3%** |
| M3 overall | **71.8%** |
| M5 off-standard ratio | **2.46%** |
| Identity M4 × (1 − M5) | **71.8%** |

- The difference between line (gross) and pooled operator (net) figures equals Σ DD exactly.

---

## 4. Skill matrix and tiers

### TC-SK-01 · Family efficiency and levels: Operator B's month
**Spec:** §10.2–10.4 · **Type:** Calc · **Priority:** P1
- **Given:** B's month (TC-INC-03): NAM 12,180. Hemming 7,000 pcs × 0.90 (no defects), 6,800 bundle min. Sleeve setting 1,900 pcs × 1.40, 40 defective pcs (DD 56), 3,800 bundle min. Window = this month only; previous levels: Hemming U (met U last time), Sleeve setting I.
- **Then:**

| | Hemming | Sleeve setting |
|--|---------|----------------|
| Time share | **64.15%** | **35.85%** |
| NAM_f | **7,813.6** | **4,366.4** |
| Eff_f | **80.6%** | **59.6%** |
| DR_f | 0% | **2.11%** |
| Level for next period | **U** | **L** (volume 2,660 ≥ 600) |

- Weighted family efficiencies add back to her M1 of **73.1%**.

### TC-SK-02 · Minimum volume
**Spec:** §10.3 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Operator at L in Seam join; only **500** EM_g in the family in the window, at 40% efficiency.
- **Then:** No evaluation; level stays **L**, no warning.

### TC-SK-03 · Downgrade grace
**Spec:** §10.4 · **Type:** Rule (checked by the calculator) · **Priority:** P2
- **Given:** Operator at U in Hemming. Evaluation 1: Eff 75%, DR 1.0%. Evaluation 2 (next month): Eff 76%, DR 1.0%. Volume sufficient both times.
- **Then:** After evaluation 1: still **U**, with a **warning**. After evaluation 2: **L**.

### TC-SK-04 · Dormancy
**Spec:** §10.4 · **Type:** Rule (checked by the calculator) · **Priority:** P2

| Level before | Ever reached U? | Days without volume | Level after |
|--------------|-----------------|---------------------|-------------|
| U | yes | 180 | **L** |
| O | yes | 200 | **U** |
| L | yes (downgraded earlier) | 190 | **L** (floor) |
| L | no | 190 | **I** |
| U | yes | 179 | **U** (not yet dormant) |

### TC-SK-05 · Level O
**Spec:** §10.4 · **Type:** Rule (checked by the calculator) · **Priority:** P2
- **Given / Then:**
  - At U, met U criteria in the previous evaluation, now Eff 96%, DR 0.5% → **O**.
  - At L (did not meet U last time), now Eff 96%, DR 0.5% → **U** only.
  - At U, met U last time, now Eff 96% but DR 2.0% → stays **U** with a **warning** (below U criteria on quality).
- O is purely data-based and changes no pay figure (DEC-22): PF is 1.00 for both U and O, and tiers count families at U or above.

### TC-SK-06 · Tiers
**Spec:** §10.5 · **Type:** Rule (checked by the calculator) · **Priority:** P2

| Operator | Families at ≥ U (skill-evaluated) | Grade A | Machine classes | Tier |
|----------|-----------------------------------|---------|-----------------|------|
| A | Seam join, Hemming | 0 | OL, FL | **T2** |
| B | Hemming (Sleeve setting at I) | 0 | FL | **T1** |
| C | 6 (Placket, Collar, Sleeve, Pocket, Cuff, Hemming); buttonhole ignored | 2 | SNLS, OL, FL | **T4** |
| C without Hemming | 5 | 2 | SNLS, OL | **T3** |
| 4 families all on SNLS, 1 Grade A | 4 | 1 | SNLS | **T2** (fails T3 on machine classes) |
| U in Buttonholing and Hemming only | 1 (buttonhole doesn't count) | 0 | FL | **T1** |

### TC-SK-07 · Not-skill-evaluated work takes its share of time
**Spec:** §10.1–10.2, DEC-12 · **Type:** Calc · **Priority:** P2
- **Given:** Operator D, month NAM 12,000. Collar setting 2,500 pcs × 1.80 = **4,500** EM, 6,000 bundle min. Buttonholing 2,000 pcs × 1.70 = **3,400** EM, 4,000 bundle min. No defects.
- **Then:** Collar share = **60.0%**, NAM_collar = **7,200**, Eff_collar = **62.5%** → level L criteria met. Buttonholing gets **no ILUO level**, but its 40% time share is taken out of the collar time, so collar efficiency is not distorted.

### TC-SK-08 · Levels and tiers fixed for the pay period
**Spec:** §10.5, §11.2 · **Type:** Rule · **Priority:** P2
- **Given:** B's sleeve-setting evaluation at the end of October gives L (TC-SK-01).
- **Then:** October incentive uses the level fixed at 1 October (**I**, PF 1.25). L applies from 1 November. B's tier for November is computed from levels at the end of October and does not change during November.

---

## 5. Incentive chain

### TC-INC-01 · Spec worked example (§11.7)
**Spec:** §11.2–11.4, §11.7 · **Type:** Calc · **Priority:** P1
- **Given:** A = 12,480; OS 600 (waiting 300, breakdown 180, repair 120). Family X at U: 9,000 pcs × 0.80. Family Y at L, within PF_cap: 1,500 pcs × 1.20. Defects 50 pcs in family X. Tier T2. No ramp days.
- **Then:**

| | Expected |
|--|----------|
| NAM | **11,880** |
| EM_g | **9,000** |
| DD | **40** |
| EM_n | **8,960** |
| M1 | **75.4%** |
| M3 | **72.1%** |
| IM = 7,200 + 1,800 × 1.10 − 40 | **9,140** |
| E_inc | **76.9%** |
| TM = 0.70 × 11,880 | **8,316** |
| X | **824** |
| U = 824 × 1.05 | **865.2** |

### TC-INC-02 · Operator A's month with overtime
**Spec:** §11.3–11.5 · **Type:** Calc · **Priority:** P1
- **Given:** A = 12,480 normal + 1,200 weekday OT = **13,680**. OS 400 (OS-03 150, OS-01 250). Side seam (U): 7,800 pcs in normal time, 950 pcs in OT, SAM 1.20. Defects 30 pcs. Tier T2.
- **Then:**

| | Expected |
|--|----------|
| NAM | **13,280** |
| EM_g | **10,500** (normal 9,360, OT 1,140) |
| DD | **36** |
| EM_n | **10,464** |
| M1 | **78.8%** |
| IM | **10,464** |
| TM | **9,296** |
| X | **1,168** |
| U | **1,226.4**, one total |

- Overtime minutes and overtime output count like any other; the incentive is **not split by time category** (spec §11.5).

### TC-INC-03 · Learner with proficiency factor (Operator B)
**Spec:** §11.2 · **Type:** Calc · **Priority:** P1
- **Given:** B's month: A 12,480, OS 300, Hemming 6,300 EM (U), Sleeve setting 2,660 EM at level I with no previous EM in the family, DD 56. Tier T1.
- **Then:** NAM **12,180**; EM_g **8,960**; M1 **73.1%** (untouched by PF). PF bonus = 2,400 × 0.25 = **600** (the last 260 EM are past the cap, at 1.00). IM = **9,504**; TM = **8,526**; X = **978**; U = **978.0**. Without the PF, X would be **378**.

### TC-INC-04 · Floater below threshold (Operator C)
**Spec:** §11.3, DEC-15 · **Type:** Calc · **Priority:** P1
- **Given:** C's month: A 12,480, OS 250. Collar 1,500 × 1.80; placket 1,600 × 1.60; buttonhole 1,200 × 1.70 (not skill-evaluated, PF 1.00); sleeve 700 × 1.40; all U. Defects 10 collar pcs. Tier T4.
- **Then:** NAM **12,230**; EM_g **8,280**; PF bonus **0**; IM **8,262**; TM **8,561**; she is **299** short, so X = **0** and U = **0**. Never negative. Her tier and levels are still reported for payroll's special allowance (DEC-06, DEC-15).

### TC-INC-05 · PF_cap carries across periods
**Spec:** §11.2 · **Type:** Calc · **Priority:** P2
- **Given:** Operator produced 2,000 EM in Sleeve setting last month at level I. This month she is at L and produces 1,500 EM in the family.
- **Then:** PF 1.10 applies to the remaining 400 EM: bonus = **40.0**, IM in the family = **1,540.0**. If she had already used the full 2,400, the bonus would be **0**.
- The cap is read from the family's grade (Sleeve setting, Grade B: 2,400 in P0) and does **not reset** after a period of dormancy (DEC-23).

### TC-INC-06 · Proficiency factor and ramp stack without double counting
**Spec:** §11.3 (stacking) · **Type:** Calc · **Priority:** P2

| Operator performing as expected | Established style | New R2 style, day 1 |
|---------------------------------|-------------------|---------------------|
| U level | 80% vs bar 70% → **+10.0** points | 40% vs bar **35.0%** → **+5.0** points |
| Learner, level I (PF 1.25) | 56% × 1.25 = **70.0%** → at the bar | 28% × 1.25 = **35.0%** → at the bar |

### TC-INC-07 · Daily threshold factor θ_day
**Spec:** §11.3 · **Type:** Calc · **Priority:** P1

| Day situation | θ_day |
|---------------|-------|
| Full day on an R2 style, ramp day 1 (r 0.500) | **35.0%** |
| Ramp day 2 (r 0.6875) | **48.1%** |
| Ramp day 3 (r 0.875) | **61.3%** |
| Ramp day 4+ (r 1.00) | **70.0%** |
| Half the day's EM_g on an R2 style on its day 1, rest on established work | **52.5%** |
| Full day on an R3 style, day 1: raw 0.70 × 0.40 = **28.0%** → floor | **30.0%** |
| 30% of EM_g on an R2 style (day 1), 20% on an R1 style (day 2, r 0.90), 50% established | **58.1%** |

- s_k is the operator's share of that day's **EM_g** (quantity-based), not of time.

### TC-INC-08 · Month with two R2 changeovers
**Spec:** §11.3 · **Type:** Calc · **Priority:** P2
- **Given:** 26 days, NAM 465 per day. On normal days the operator performs at 79%. Two R2 changeovers give 6 ramp days at 40% / 55% / 70% (twice).
- **Then:**

| | Normal month | 2 changeovers, flat θ | 2 changeovers, ramp-adjusted θ |
|--|--------------|----------------------|-------------------------------|
| IM | **9,551.1** | **8,881.5** | 8,881.5 |
| TM | **8,463.0** | 8,463.0 | **7,852.7** |
| X | **1,088.1** | **418.5** (**-61.5%**) | **1,028.8** (**94.6%** of normal) |

- The system must produce the **ramp-adjusted** column.

### TC-INC-09 · Excess is aggregated over the period, not per day
**Spec:** §11.1, §11.3 · **Type:** Calc · **Priority:** P1
- **Given:** A two-day period: day 1 IM 250, day 2 IM 450; NAM 480 each day; no ramp.
- **Then:** TM = **672**; X = max(0, 700 − 672) = **28**. Summing daily excesses would wrongly give **114**.

### TC-INC-10 · Eligibility flag
**Spec:** §11.6 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Operator attended 20 of 26 scheduled days.
- **Then:** Attendance = **76.9%** < 80% → *minimum attendance* flag sent to payroll. IE still calculates and reports X and U; payroll decides the consequence.

### TC-INC-11 · Parameter versioning
**Spec:** DEC-21, §14.1 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Operator A's month (TC-INC-02) is November. θ is changed from 0.70 to 0.72 with effective date 1 December. The same inputs are then calculated for a December period.
- **Then:** Recalculating November still gives X = **1,168** (values effective in November). The December period uses 0.72: TM = **9,561.6**, X = **902.4**. The change history shows who changed θ, when, and from which date it applies.

### TC-INC-12 · Shadow mode ⚠ Provisional (OPEN-12)
**Spec:** DEC-16, §14.2–14.3 · **Type:** Rule · **Priority:** P1
- **Given:** Shadow mode on for October.
- **Then:** All figures (levels, tiers, PF, ramp-adjusted TM, X, U) are calculated and reported exactly as in live mode, but the payroll feed marks U as **not payable**. Pay follows the basis decided under OPEN-12. Switching shadow mode off is itself a versioned parameter with an effective date.

---

## 6. Style changeover

### TC-CO-01 · Familiarity score and ramp class
**Spec:** §7.7.2–7.7.3 · **Type:** Calc · **Priority:** P2
- **Given:** Line 1 runs PS-01 every week.

| Variant | Change | New garment SAM | F | Class |
|---------|--------|-----------------|---|-------|
| V1 | Bottom hem → hem with side vents (0.80 → 0.95), new library code | **10.15** | **90.6%** | **R0** (no ramp) |
| V2 | Collar attach → contrast collar with tipping (1.80 → 2.10), new library code | **10.30** | **79.6%** | **R1** |
| PS-01 on a line that has never run any of its library codes | — | 10.00 | **0.0%** | **R2** |

- The class is suggested; the IE confirms or overrides (TC-CO-06).

### TC-CO-02 · Ramp days count production days of the OB on the line
**Spec:** §2 (production run), §7.7.1 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Line 1 starts new R2 style S on Monday (day 1) and Tuesday (day 2), runs another OB on Wednesday and Thursday, and returns to S on Friday.
- **Then:** The break is 2 production days, so the run continues and Friday is **ramp day 3**: full-day θ_day = **61.3%**.
- **Variant:** a break of 3 production days ends the run. Friday starts a new run; S ran on this line within 90 days, so F ≥ 90% → R0, θ_day = **70.0%**.

### TC-CO-03 · Variants that are not changeovers
**Spec:** §7.7.1 · **Type:** Rule · **Priority:** P2
- **Given:** (a) Line 1 switches PS-01 from navy to white. (b) A SAM amendment on PS-01 with no new library operation.
- **Then:** Neither is a changeover: no new production run, no ramp class, ramp day count continues.

### TC-CO-04 · Fitting a ramp profile (median)
**Spec:** §7.7.5 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Four completed R2 runs with observed r(d): day 1 = 0.45 / 0.52 / 0.48 / 0.55; day 2 = 0.62 / 0.70 / 0.66 / 0.71; day 3 = 0.85 / 0.90 / 0.86 / 0.92; day 4 = 0.95 / 0.98 / 0.97 / 1.00.
- **Then:** Fitted profile = **0.50** → **0.68** → **0.88** → **0.975**; it ends at day 4 (≥ 0.95). With only 4 runs (< 10) the fitted profile is **reported** (changeover analysis) but the **bootstrap profile stays in force**.

### TC-CO-05 · Observed r(d) and run plateau
**Spec:** §7.7.5 · **Type:** Calc + Rule · **Priority:** P2
- **Given:** Run 1: on-standard efficiency of U/O operators by day: 40%, 55%, 70%, 76%, 78%, then days 6–10: 78%, 80%, 79%, 81%, 82%. Run 2 ends after day 8 (only 3 plateau days).
- **Then:** Run 1 plateau = **80.0%**; observed r(1) = **0.50**, r(3) = **0.875**. Run 2 is **excluded** (fewer than 5 plateau days). Production by operators below U is excluded from the efficiencies.

### TC-CO-06 · IE override of the ramp class
**Spec:** §7.7.3 · **Type:** Rule · **Priority:** P2
- **Given:** System suggests R0 for V1 (TC-CO-01); the IE sets R1 because the vented hem is difficult on this fabric.
- **Then:** R1 applies; the override is stored with the IE, date and reason, and appears in the monthly class-mix and override report per line.

---

## 7. Balancing, targets and allocation

### TC-BAL-01 · Line 1, daily target 1,100 polos at plateau
**Spec:** §7.1–7.3 · **Type:** Calc · **Priority:** P3
- **Given:** Fixture F2 layout (30 operators), target 1,100, e = 80%.
- **Then:**

| | Expected |
|--|----------|
| Takt (480 ÷ 1,100) | **0.436** min/pc |
| Headcount needed (1,100 × 10.00 ÷ (480 × 0.80)) | **28.6** → 29 |
| Pitch (10.00 ÷ 30) | **0.333** min/pc |
| Max allowed station load (takt × e) | **0.349** |
| Bottleneck | Collar attach, load **0.360** |
| Line output | **1,067** /day |
| Balance efficiency | **92.6%** |

- **Fix:** 6 operators on collar (31 total): new bottleneck sleeve attach (**0.350**), output **1,097** /day, balance efficiency **92.2%**.

### TC-BAL-02 · Daily target on a ramp day with absenteeism
**Spec:** §7.5 · **Type:** Calc · **Priority:** P3
- **Given:** PS-01 as a new R2 style, ramp day 2 (e = 0.80 × 0.6875 = 55%), 28 of 30 operators present.
- **Then:** Daily target = 28 × 480 × 0.55 ÷ 10.00 = **739.2** pieces, recalculated from actual headcount. E_plan is never used here.

### TC-BAL-03 · Skill-aware allocation report
**Spec:** §7.4 · **Type:** Rule · **Priority:** P3
- **Given:** Operators A, B, C (F3); station *Collar attach* (Grade A, current bottleneck).
- **Then:** The qualified-operator report for the collar station lists **C** (U in Collar setting) and not A or B. Assigning B there is **allowed** (it is not blocked); her proficiency factor applies automatically.

---

## 8. Real-time monitoring

### TC-RT-01 · Hourly target
**Spec:** §13.2 · **Type:** Calc · **Priority:** P3
- **Then:** Plateau day, 30 present: 30 × 60 × 0.80 ÷ 10.00 = **144** polos per hour. Ramp day 2 of an R2 style with 28 present: **92.4**. The board follows ramp day and attendance automatically.

### TC-RT-02 · Live bottleneck excludes starved stations
**Spec:** §13.2 (RT-6) · **Type:** Calc · **Priority:** P3
- **Given:** Line 1, 10:00–11:00 on a plateau day (W = 60):

| Station | Planned (W) | Completed | Ratio | Input buffer | Starved (min) |
|---------|-------------|-----------|-------|--------------|---------------|
| Placket attach | **150.0** | 148 | **98.7%** | 5 | 0 |
| Shoulder join | **160.0** | 158 | **98.8%** | 4 | 0 |
| Collar attach | **133.3** | 112 | **84.0%** | 7 | 0 |
| Sleeve attach | **137.1** | 118 | **86.0%** | 1 | 12 |
| Side seam | **160.0** | 115 | **71.9%** | 1 | 15 |
| Sleeve + bottom hem | **141.2** | 113 | **80.0%** | 1 | 16 |
| Buttonhole & button sew | **141.2** | 112 | **79.3%** | 0 | 18 |

- **Then:**
  - Line output = 112 against 144 = **77.8%** → "line below target" alert.
  - Stations starved more than 6 min (10% of W) are excluded: sleeve attach, side seam, both hems, buttonhole.
  - **Live bottleneck = Collar attach** (lowest ratio among non-starved stations), not side seam (lowest ratio overall).

### TC-RT-03 · Exception alerts
**Spec:** §13.2 (RT-2, RT-5) · **Type:** Calc + Rule · **Priority:** P3
- **Given:** The hour in TC-RT-02, plus: a 20-piece side-seam bundle open for 75 min; an off-standard pause pending approval for 35 min.
- **Then:**
  - Bundle open too long: limit = 3 × 1.20 × 20 = **72** min → alert at 75.
  - Off-standard pending > 30 min → alert.
  - Station starved > 15 min → alerts for *Sleeve + bottom hem* (16) and *Buttonhole* (18); side seam at exactly 15 does **not** alert.
  - Buffer above the WIP cap (3) → flags for placket (5), shoulder (4) and collar (7).
  - Line below 85% → alert (TC-RT-02).

### TC-RT-04 · Breakdown call opens a maintenance request
**Spec:** §13.2 (RT-3), §12 · **Type:** Rule · **Priority:** P3
- **Given:** Operator pauses her bundle with reason OS-01 at 10:05; the mechanic fixes the machine; she resumes at 10:30; the leader approves.
- **Then:** At 10:05 a maintenance request is created in the CMMS (station, machine where known, operator, time) and the mechanic is notified. The off-standard record runs 10:05–10:30 (25 min, OS-01) and, once approved, reduces her NAM. OS-01 minutes are reported per machine where known.

### TC-RT-05 · Real-time and period figures agree
**Spec:** DEC-19 · **Type:** Rule · **Priority:** P3
- **Given:** Any operator-day after all records are final (exceptions cleared).
- **Then:** The end-of-day real-time figures (pieces, EM_g, DD, NAM, M1) equal the period calculation for that day. Real-time figures before that point are marked **provisional** (RT-4 feed).

---

## 9. Self-funding check and payroll feed

### TC-SF-01 · Labour cost per earned minute
**Spec:** §11.8 · **Type:** Calc · **Priority:** P2
- **Given:** Line 1 (30 operators, A = 374,400 min/month).

| Month | Base + incentive + allowances (VND) | Σ EM_g | M3 | Cost per EM | Signal |
|-------|-------------------------------------|--------|----|-------------|--------|
| 1 | 255 M + 20 M + 5 M = 280 M | 261,000 | **69.7%** | **1,072.8** | baseline |
| 2 healthy | 255 M + 40 M + 5 M = 300 M | 285,000 | **76.1%** | **1,052.6** | falls → healthy |
| 2 unhealthy | 255 M + 70 M + 5 M = 330 M | 285,000 | 76.1% | **1,157.9** | rises while M3 rises → review θ, rate or multipliers |

### TC-PAY-01 · Payroll feed record for Operator A
**Spec:** §12, DEC-08 · **Type:** Rule (values from TC-INC-02) · **Priority:** P2
- **Then:** One record per operator per period containing at least:

| Field | Value |
|-------|-------|
| A | 13,680 |
| OS by code | OS-03 150; OS-01 250 |
| NAM | 13,280 |
| EM_g / DD / EM_n | 10,500 / 36 / 10,464 |
| IM | 10,464 |
| M1 / E_inc | 78.8% / 78.8% |
| X | 1,168.00 |
| U (one total) | 1,226.40 |
| Tier / M_tier | T2 / 1.05 |
| Family levels | Seam join U; Hemming U |
| Eligibility flags | none |
| Mode | live (or *not payable* in shadow mode, TC-INC-12) |

- The feed contains **no money**. Rates, premiums and allowances are payroll's.

---

## 10. Assumptions: resolved

The assumptions raised by v0.1 are settled; the spec now states each one.

| # | Assumption | Resolution | Used in |
|---|------------|------------|---------|
| AS-01 | Bundle crossing the PF cap | Interim rule: split (spec §11.2); mechanism reconsidered in technical design (FLAG-TECH-14). Cap cumulative across periods and levels (DEC-23). | TC-INC-03, TC-INC-05 |
| AS-02 | Defect record exceeding the bundle | Rejected with an error (spec §9.3); check designed in technical design (FLAG-TECH-13). | TC-EM-03 |
| AS-03 | Time category of defect deductions | Withdrawn: the incentive is not split by time category (spec §11.5). | TC-INC-02 |
| AS-04 | Upgrades and downgrade grace | Upgrades immediate; downgrade grace also when failing on defect rate (spec §10.4). | TC-SK-01, TC-SK-03, TC-SK-05 |
| AS-05 | Level O | Spec DEC-22. | TC-SK-05 |
| AS-06 | R2 day 2 | 0.6875 (spec §7.7.3). | TC-INC-07, TC-INC-08, TC-BAL-02 |
| AS-07 | Rounding | Full precision; targets to the nearest whole piece; payroll figures to 2 decimals (spec conventions). | TC-BAL-02, TC-PAY-01 |

---

## 11. Not covered

- **Costing stream** (CPM, CM cost, E_plan, order-level load, machine requisition, actual cost): not in v1 (function map area 3). Spec §6 logic is kept for later.
- **Idle-gap analysis** (M8): a later addition in the function map.
- **Master data screens** (function map 1.1, 1.2, 1.4, 1.6: operation library, timeSSD file import, grading, family mapping): data entry and import; checked during the integration inventory (roadmap step 4) with real files.
- **Analytics reports** (function map 8.1–8.4, 8.6, 8.8, 8.9): views over the figures tested here. Acceptance = each report's totals match the underlying cases (e.g. lost time by code in TC-MET-03).
- **timeSSD import format, MES display, notification channels**: technical design (FLAG-TECH-11).
- **Shadow-mode acceptance criteria for switch-on**: OPEN-12.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-18 | First version, from spec v0.4, rationale v0.4 and function map v0.6. 40 calculated cases checked by `ie_reference_calc.py`; rule cases; assumptions AS-01 to AS-07 to confirm. |
| 0.1 rev. | 2026-10-18 | Priority added to every case (P1 before shadow mode, P2 before live pay, P3 build order). |
| 0.2 | 2026-10-18 | Aligned with Spec v0.5: TC-SK-05 and TC-INC-05 no longer provisional (DEC-22, DEC-23); PF_cap per grade in F4; TC-TA-08 shows both OPEN-15 options; AS-05 answered, AS-01 narrowed. |
| 0.3 | 2026-10-19 | Aligned with Spec v0.6: TC-EM-03 rejects the over-limit record; TC-INC-02 and TC-PAY-01 without time-category split; TC-EM-08 wording; assumptions AS-01 to AS-07 resolved (§10). |
