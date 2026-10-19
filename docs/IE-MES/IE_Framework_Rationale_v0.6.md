# IE Framework — Rationale & Walkthrough

**Version:** v0.6 · 2026-10-19
**Companion to:** `IE_Business_Logic_Spec_v0.6.md` (the rules), `IE_Module_Function_Map.md` v0.8 (the scope, plus the document set and workflow) and `IE_Acceptance_Test_Cases_v0.3.md` (expected results)
**Purpose:** Explains *what* the framework is, *why* its parts fit together and **how the numbers add up**, for human review. It contains no new rules. If this document and the spec disagree, the spec wins.

> **About the numbers.** All figures come from one fictional running example (§2) and are **illustrative**. Parameter values such as the 70% threshold, the proficiency factors, the caps, the ramp profiles and the tier multipliers are spec placeholders (`[P]`), to be calibrated in shadow mode (spec §14). They are not proposals. Every parameter is configurable and versioned with an effective date (spec DEC-21), so tuning on real data needs no code change. Every calculation in this document was checked by script. Currency is VND.

**How each formula section reads:** **Formula** (with every term in plain words) → **Worked numbers** → **Why this form** → **Edge checks**.

**Symbols used throughout**

| Symbol | Meaning | Symbol | Meaning |
|--------|---------|--------|---------|
| A | Attended minutes | IM | Incentive minutes (EM adjusted by PF, minus DD) |
| OS | Approved off-standard minutes | PF | Proficiency factor (learning leeway) |
| NAM | Net available minutes = A − OS | θ, θ_day | Threshold factor (normal / per day) |
| EM_g | Gross earned minutes = pieces × SAM | TM | Threshold minutes |
| DD | Defect deduction | X | Excess incentive minutes = IM − TM (min 0) |
| EM_n | Net earned minutes = EM_g − DD | U, M_tier | Payable units = X × tier multiplier |
| P | Plateau efficiency | r(d), e(d) | Ramp profile; learning curve e(d) = P × r(d) |
| E_plan | Order-average planned efficiency | F | Familiarity score of a new style |

---

## 1. The framework in one page

The IE module answers four questions:

1. **How long should this garment take?** → *Standards* (SAM from timeSSD, governed)
2. **What will it cost, and how should we run the line?** → *Planning* (costing, capacity, balancing, changeover ramp-up)
3. **What actually happened on the floor?** → *Measurement* (bundles, time accounting, quality)
4. **Who performed how well, and what did they earn?** → *Evaluation* (efficiency, skill, incentive metrics for payroll)

Everything is measured in **standard minutes**. The cost of a garment, the capacity of a line, an operator's performance and the size of their incentive are all expressed in the same unit, so they can be compared and added up without conversion.

```
   STANDARDS ──────► PLANNING ──────► EXECUTION ──────► MEASUREMENT ──────► EVALUATION
   SAM (timeSSD)     cost per minute  bundle = MO       time accounting     skill matrix
   versioned,        CM cost, E_plan  1 operator per    earned minutes      incentive minutes
   governed          balancing,       bundle×operation  defects → deduct    ramp-adjusted threshold
                     ramp class                                             → payroll
        ▲                                                    │
        └──── planned vs actual SAM, lost time, fitted ramp profiles ◄──┘   (continuous improvement)
```

---

## 2. The running example

### 2.1 Style PS-01 (polo shirt): Operation Bulletin, sewing department

| # | Operation | Operation family | Grade | Machine class | Skill-evaluated | SAM (min) |
|---|-----------|------------------|-------|---------------|-----------------|-----------|
| 1 | Placket attach | Placket setting | A | SNLS | yes | 1.60 |
| 2 | Shoulder join | Seam join | C | Overlock (OL) | yes | 0.60 |
| 3 | Collar attach | Collar setting | A | SNLS | yes | 1.80 |
| 4 | Sleeve attach | Sleeve setting | B | Overlock (OL) | yes | 1.40 |
| 5 | Side seam | Seam join | C | Overlock (OL) | yes | 1.20 |
| 6 | Sleeve hem | Hemming | C | Flatlock (FL) | yes | 0.90 |
| 7 | Bottom hem | Hemming | C | Flatlock (FL) | yes | 0.80 |
| 8 | Buttonhole & button sew | Buttonholing | C | Buttonhole (automatic) | **no** | 1.70 |
| | **Garment sewing SAM** | | | | | **10.00** |

Two points to note:
- Shoulder join and side seam belong to the **same family** (Seam join), as do both hems. That's the point of families: skill on one counts for the other.
- **Buttonholing** runs on an automatic machine, so it is graded C and **not skill-evaluated** (spec DEC-12). Its work still earns incentive minutes; it just doesn't build a skill record.

Other departments (simplified): cutting SAM 1.20, finishing SAM 2.00.

### 2.2 The cast
- **Line 1:** 30 operators, 480 attended minutes per day (08:00–17:00, less 60 minutes unpaid lunch).
- **Operator A, "the steady one":** independent (U) in Seam join and Hemming, so tier T2. Works side seam all month, plus some overtime.
- **Operator B, "the learner":** U in Hemming (tier T1). This month she also starts **sleeve setting**, a family new to her.
- **Operator C, "the floater":** U in 6 skill-evaluated families:
  - Placket setting, Collar setting and Sleeve setting from this style;
  - Pocket setting, Cuff setting and Hemming from other styles;
  - including 2 Grade A, across SNLS, OL and FL;
  - which makes her tier **T4**. She is also able to run the buttonhole machine, but that doesn't count towards her tier.

  She is moved around the line all month.

---

## 3. The foundation: time accounting

### 3.1 Formula
```
A    = attended minutes (paid presence, excluding unpaid breaks)
OS   = approved off-standard minutes (breakdown, material wait, waiting for work, power, repair,
       meeting, non-SAM task, other, changeover setup)
NAM  = A − OS          net available minutes: time the operator is accountable for output
```

### 3.2 Worked numbers: Operator A, one normal day
| Item | How it was recorded | Minutes |
|------|---------------------|---------|
| Attended A | Attendance (master clock) | 480 |
| Machine breakdown (OS-01) | Channel 1: she paused her open bundle with a reason; the leader approved | 25 |
| Waiting for work (OS-03) | Channel 2: no bundle at her station; the leader entered it | 20 |
| **OS total** | | **45** |
| **NAM = 480 − 45** | | **435** |

**One bucket, three channels.** Off-standard records all have the same shape: operator(s), time, reason, approver. They reach the bucket by three routes:
1. a **work-order pause** with a reason, for stops during a bundle;
2. a **manual entry by the line leader**, for stops between bundles: waiting for work, meetings, changeover setup, line-wide stops;
3. **repair records**.

Everything downstream reads only the bucket, so the channel doesn't change any calculation.

### 3.3 Why this form
- **Fair:** the 45 minutes she couldn't use are removed explicitly, each with a reason and an approver.
- **Accountable:** any idle time that is *not* approved stays in the 435. Either the operator or the leader who failed to log the stop owns it.
- **One split feeds everything:** the same 45 minutes appear in lost-time analysis (25 breakdown, 20 waiting) and in line balancing (the waiting minutes).

### 3.4 Edge checks
- **A day of pure downtime** (A = 480, OS = 480 → NAM = 0): no output is expected, and the day adds 0 to both the numerator and the denominator of the monthly figures. It cannot hurt or help her.
- **Unapproved 30-minute chat:** stays in NAM. Her efficiency falls, as it should.
- **Changeover setup** (resetting machines, swapping attachments) has its own code, OS-09. Setup time is never confused with the learning effect handled in §12.
- **Overlapping records:** an off-standard record can't overlap another one or active bundle time. Starting an off-standard period pauses the open bundle, so no minute is counted twice.

### 3.5 Two time sources, one master clock
Time reaches the system from **attendance** (clock-in/out) and from **bundle scans**. They can disagree, for example when a bundle is left open over lunch. **Attendance is the master clock for pay:** A and NAM come only from attendance and the off-standard bucket.

Bundles are paused or finished by operators and line leaders at breaks and shift end. There is no automatic pause, because production can legitimately run into breaks or overtime. An optional nightly job pauses bundles still open. Server timestamps and a data-quality exception list (scans outside attendance, coverage above 100%, bundles open at clock-out, unapproved pauses) catch the rest before payroll close.

*Two legitimate options, decided during technical design (spec OPEN-15).* Take a bundle scanned 11:50 → 13:10 across a 12:00–13:00 unpaid lunch:
- **(A) No clipping:** it counts 80 minutes. The extra 60 minutes only shift the time split between families on a mixed-family day and distort the diagnostics. The fallbacks below (pausing, the optional nightly job, the exception list) catch it before payroll close.
- **(B) Bundle time only inside attendance:** it counts 20 minutes, and the case corrects itself. The cost: if work really did continue through the unpaid break, its pieces still count but its minutes don't, so that family's efficiency looks slightly higher.

Which one fits depends on how reliably bundle and attendance data line up in practice, which the technical design will show.

**Why residual inaccuracy is tolerable.** Bundle time reaches pay only through the time split between families (§10). On a day spent in one family, the split is 100% whatever the durations. Errors matter only on mixed-family days, and they are diluted further by 60-day windows and pass/fail bands.

**Idle-gap analysis.** Time when a station has no active bundle *and* no off-standard record is *unexplained idle time*. It is reported per line and station for balancing and planning, never for pay.

---

## 4. Standards and SAM governance

### 4.1 Formula
```
Garment SAM = Σ SAM of all operations in the OB      (10.00 for PS-01)
```

### 4.2 Disputes: what the system does and what people do
Verification is engineering and management judgement, so it happens **outside** the system. The IE module records the process around it:

| Step | Who | What the system records |
|------|-----|-------------------------|
| 1. Raise | Line leader | Dispute: operation, OB, reason, date |
| 2. Verify | IE, outside the system | Evidence attached. Method check first; preferred evidence is a timeSSD re-analysis of the observed method, with a time study as support |
| 3. Decide | IE manager (and management if pay is affected) | Decision and approver |
| 4. Amend | System | New SAM version and effective date. Past records are never silently rewritten |

*Example:* a dispute on sleeve attach (SAM 1.40) is upheld after re-analysis shows the original timeSSD analysis missed a handling element (a standard error). A new version (e.g. SAM 1.55) takes effect from the start of the current pay period; records before that date keep 1.40. Had the cause been a buyer spec change instead, the new SAM would apply from the date of the change.

### 4.3 Why this form
- SAM drives pay, so it must change only on evidence, never on pressure.
- **The method check comes first:** a slow operation is often a method problem, and fixing the method is better than loosening the standard.
- Production records keep the SAM version valid on their completion date, so an amendment never silently rewrites the past.

### 4.4 Grading families: the rubric
Each family's grade comes from four questions, following common garment grading practice:
- Is it **critical**?
- Is it **visible** on the face of the garment?
- Does it need **precision or difficult handling**?
- Is the **machine manual or automatic**?

In PS-01:
- **Collar and placket setting** are critical, face-visible and high-precision → **A**.
- **Sleeve setting** needs ease control but is less visible → **B**.
- **Seam join and hemming** are simple, mostly hidden seams → **C**.
- **Buttonholing** runs on an automatic machine → **C** and not skill-evaluated.

---

## 5. Costing

*Scope note: costing (CPM, CM cost, E_plan) is not in v1; it is kept here because it explains the learning curve and will come with a later release. The self-funding check (§13) is in v1.*

### 5.1 Cost per minute (CPM)

**Formula**
```
CPM = (Direct labour cost + Allocated overhead) ÷ Direct-operator attended minutes
```

**Worked numbers (sewing department, one month)**
| Item | Value |
|------|-------|
| Operators | 200 |
| Attended minutes per operator | 26 days × 480 = 12,480 |
| Total attended minutes | 200 × 12,480 = **2,496,000** |
| Direct labour cost | 200 × 8,500,000 = 1,700,000,000 |
| Allocated overhead | 900,000,000 |
| **Total cost** | **2,600,000,000** |
| **CPM** | 2,600,000,000 ÷ 2,496,000 = **1,041.67 VND/min** |

**Why this form.** The denominator is *operator* minutes, so CPM doesn't change when a line grows or shrinks. Headcount affects how long an order takes, not what a garment costs. Machine minutes would be wrong, because idle machines inflate the denominator and understate the cost.

### 5.2 Planned efficiency (E_plan): the order-average, including ramp-up

**Formula**
```
Learning curve            e(d) = P × r(d)        P = line plateau (overall basis), r(d) = ramp profile of the style's class (§12)
Daily output on day d     Q(d) = N × T × e(d) ÷ SAM
Days to finish order      D    = days until Σ Q(d) reaches order quantity Q (last day fractional)
Planned efficiency        E_plan = (Q × SAM) ÷ (N × T × D)
```
- N = operators, T = attended minutes per operator per day.
- The plateau is on the **overall-efficiency basis** (M3), because N × T counts attended minutes. *(C-3, applied in spec §7.7.6.)*

**Worked numbers.** Line 1: N = 30, T = 480, so 14,400 line minutes per day. PS-01 is a new style for this line, class **R2**: r = 0.500 → 0.6875 → 0.875 → 1.00, with plateau P = 80%. That gives e(d) = 40% → 55% → 70% → 80%.

| Day | e(d) | Output that day = 14,400 × e ÷ 10.00 | Cumulative |
|-----|------|----------------------------------------|------------|
| 1 | 40% | 576 | 576 |
| 2 | 55% | 792 | 1,368 |
| 3 | 70% | 1,008 | 2,376 |
| 4+ | 80% | 1,152 per day | … |

*Small order, Q = 3,000:*
- After day 3, 3,000 − 2,376 = 624 pieces remain.
- 624 ÷ 1,152 = 0.542 day, so D = **3.542 days**.
- E_plan = (3,000 × 10) ÷ (14,400 × 3.542) = 30,000 ÷ 51,000 = **58.8%**.

*Large order, Q = 20,000:*
- After day 3, 17,624 pieces remain.
- 17,624 ÷ 1,152 = 15.299 days, so D = **18.299 days**.
- E_plan = 200,000 ÷ (14,400 × 18.299) = **75.9%**.

### 5.3 Cut & Make (CM) cost

**Formula**
```
CM cost per garment = Σ over departments ( SAM_dept × CPM_dept ÷ E_plan_dept )
```

**Worked numbers** (cutting: SAM 1.20, CPM 950, E 85%; finishing: SAM 2.00, CPM 900, E 80%)

| Department | Small order (3,000) | Large order (20,000) |
|------------|---------------------|----------------------|
| Sewing | 10.00 × 1,041.67 ÷ 0.588 = 17,708 | 10.00 × 1,041.67 ÷ 0.759 = 13,724 |
| Cutting | 1.20 × 950 ÷ 0.85 = 1,341 | 1,341 |
| Finishing | 2.00 × 900 ÷ 0.80 = 2,250 | 2,250 |
| **CM per garment** | **21,300 VND** | **17,315 VND** |

**Why this form.** The small order really does cost about 23% more per garment, because most of its life is spent climbing the learning curve. Costing at plateau efficiency (80%) would price sewing at 10.00 × 1,041.67 ÷ 0.80 = 13,021 VND for both orders, under-pricing the small order's sewing by about 36% (17,708 vs 13,021).

**Edge check.** If the same style comes back as a repeat (class R0, no ramp), E_plan is simply the plateau, and the small-order penalty disappears. This is why the ramp class matters for costing as well as pay (§12).

---

## 6. Line planning and balancing

### 6.1 Formulas
```
Takt time          = Available minutes per day ÷ Daily target          (pace demand requires)
Pitch time         = Garment SAM ÷ Operators                            (average workload per operator)
Headcount needed   = (Daily target × Garment SAM) ÷ (T × e)              e = plateau P (steady state) or e(d) (ramp day)
Station load       = SAM of the operation(s) at the station ÷ operators sharing it
Max allowed load   = Takt × e                                           (load an operator can sustain at the day's expected efficiency)
Station output     = Operators at station × T × E ÷ SAM of the operation
Balance efficiency = Garment SAM ÷ (Operators × Max station load)
```
E_plan (§5.2) is an order average, used only for order-level load, capacity and costing. Day-to-day staffing and balancing use the efficiency expected on that day.

### 6.2 Worked numbers: Line 1, daily target 1,100 polos, plateau efficiency 80%
- Takt = 480 ÷ 1,100 = **0.436 min/pc**
- Headcount = (1,100 × 10.00) ÷ (480 × 0.80) = 28.6, so **29 operators minimum**. We run **30**.
- Pitch = 10.00 ÷ 30 = **0.333 min/pc**
- Max allowed load = 0.436 × 0.80 = **0.349 min/pc**

**First layout (30 operators)**
| Station | SAM | Operators | Load (SAM ÷ ops) | Output/day at 80% |
|---------|-----|-----------|-------------------|-------------------|
| Placket attach | 1.60 | 5 | 0.320 | 1,200 |
| Shoulder join | 0.60 | 2 | 0.300 | 1,280 |
| **Collar attach** | 1.80 | 5 | **0.360** | **1,067** ← bottleneck |
| Sleeve attach | 1.40 | 4 | 0.350 | 1,097 |
| Side seam | 1.20 | 4 | 0.300 | 1,280 |
| Sleeve + bottom hem (combined) | 1.70 | 5 | 0.340 | 1,129 |
| Buttonhole | 1.70 | 5 | 0.340 | 1,129 |
| **Total** | **10.00** | **30** | max 0.360 | line output = **1,067** |

- Balance efficiency = 10.00 ÷ (30 × 0.360) = **92.6%**
- The collar station's load (0.360) is above the allowed 0.349, so the line can only make **1,067/day**, short of 1,100.

**Fix:** a 6th operator on collar (31 operators).
- Collar load becomes 1.80 ÷ 6 = 0.300.
- The new bottleneck is sleeve attach (0.350), giving **1,097/day**: essentially on target.
- Balance efficiency = 10.00 ÷ (31 × 0.350) = **92.2%**.

**Why this form.** The headcount formula (29) assumes perfect balance. Station-level balancing reveals the real constraint, which here is the collar operation. Takt says what demand requires; pitch says how much work each operator carries on average; the comparison against max allowed load shows *where* the line will break.

### 6.3 Machine requirements: count per station, not per SAM
| Class | Stations using it (30-operator layout) | Machines | + 10% spare |
|-------|----------------------------------------|----------|-------------|
| SNLS | Placket 5 + Collar 5 | 10 | 11 |
| OL | Shoulder 2 + Sleeve 4 + Side 4 | 10 | 11 |
| FL | Hems 5 | 5 | 6 |
| BH | Buttonhole 5 | 5 | 6 |

Every operator position needs its own machine, so the count comes from the balanced layout. These counts are then checked against the CMMS machine register.

### 6.4 Daily target with absenteeism
```
Daily target = Operators present × T × e(d) ÷ Garment SAM
```
Day 2 of the style, 2 operators absent: 28 × 480 × 0.55 ÷ 10.00 = **739 pieces**.

---

## 7. Execution: why one bundle = one MO = one operator per operation

The single biggest data-integrity risk in shop-floor systems is **operators typing in quantities**. The framework removes it entirely:

- MOs are split by variant, then shade lot, then bundle size. Each bundle is its own MO.
- Each operation on a bundle is done by **one operator**, credited with the **whole bundle quantity**.
- Parallel operators on the same operation take different bundles. The faster one naturally completes more.
- The rare mid-bundle handover: a supervisor reassigns the whole bundle (logged).

Quantities are always true by construction, and every piece can be traced to the person who sewed each operation. That traceability is what makes defect attribution (§8) possible without extra work at QC. *(The system must know each operator's current state to enforce this; see FLAG-TECH-07.)*

Bundle start and finish scans also give time per bundle. That is used for diagnostics and to split an operator's time between families for skill evaluation (§10), but **never in the incentive denominator** (spec DEC-02).

---

## 8. Earned minutes and defect deductions

### 8.1 Formulas
```
Gross earned minutes   EM_g = Σ (pieces on production records × SAM of the operation)
Defect deduction       DD   = Σ (defective qty attributed to the operator × SAM of that operation × k_def)   k_def [P] = 1.0
Net earned minutes     EM_n = EM_g − DD        (DD booked on the defect's detection date)
```

### 8.2 Worked numbers: Operator A's day (continued from §3)
- 14 side-seam bundles of 20 pieces = 280 pieces → EM_g = 280 × 1.20 = **336.0**
- QC today found 3 defective pieces from *yesterday's* side seam, traced to her → DD = 3 × 1.20 = **3.6**
- EM_n = 336.0 − 3.6 = **332.4**

### 8.3 Why this form
- **Proportional:** a defect on a 1.80-minute collar costs more than one on a 0.60-minute shoulder join, which matches the value of the work.
- **Booked on the detection date:** past days and closed months are never reopened. A defect found next month simply reduces next month.
- **Repair is neutral:** whoever repairs logs a repair record, and that time becomes approved off-standard time (OS-05). The repairer is neither paid for it nor penalised, and the maker is penalised once, through DD.

### 8.4 Edge checks
- **Defect found after month-end:** goes into the next month's DD. No recalculation of paid months.
- **Defects can't exceed the bundle:** cumulative DD on one bundle × operation is capped at the bundle quantity.
- **Fabric or cutting defects:** responsibility ≠ operator, so no DD.
- **Automatic-machine work** (e.g. buttonhole) is deducted the same way. Quality applies to all work, skill-evaluated or not.

---

## 9. The metric family

### 9.1 Formulas
| # | Metric | Formula | Used for |
|---|--------|---------|----------|
| M1 | On-standard efficiency | EM_n ÷ NAM | Operator performance, skill |
| M2 | Incentive efficiency | IM ÷ NAM | Pay (§11) |
| M3 | Overall efficiency | EM_g ÷ A | Line/factory KPI, costing, learning-curve basis |
| M4 | Line on-standard efficiency | Σ EM_g ÷ Σ NAM | Line performance |
| M5 | Off-standard ratio | OS ÷ A | Lost-time analysis |
| M6 | Pace *(diagnostic)* | EM_g ÷ bundle active minutes | Planned vs actual SAM |
| M7 | Bundle coverage *(diagnostic)* | Bundle active minutes ÷ NAM | Flow and scan discipline |
| M8 | Idle-gap ratio *(diagnostic)* | Station idle minutes ÷ line working minutes | Unexplained idle time (§3.5) |

### 9.2 Worked numbers: Operator A's day
Bundle active minutes (from scans) = 390.

| Metric | Calculation | Result |
|--------|-------------|--------|
| M1 | 332.4 ÷ 435 | **76.4%** |
| M3 | 336.0 ÷ 480 | **70.0%** |
| On-standard on a gross basis | 336.0 ÷ 435 | 77.2% |
| M5 | 45 ÷ 480 | 9.4% |
| M6 pace | 336.0 ÷ 390 | 86.2% |
| M7 coverage | 390 ÷ 435 | 89.7% |

### 9.3 How the metrics relate
```
Overall = On-standard (gross) × (1 − Off-standard ratio)
70.0%   = 77.2% × (1 − 0.094)           ✔ exact, because EM_g/A = (EM_g/NAM) × (NAM/A)
```
Overall losses therefore split cleanly into a **performance loss** (77.2% vs 100%) and an **off-standard loss** (9.4% of time).

### 9.4 Why bundle timers don't touch the incentive denominator: a gaming test
Suppose Operator A scans sloppily, so her bundles show 300 active minutes instead of 390:
- Pace M6 jumps to 336 ÷ 300 = 112%.
- Coverage M7 drops to 69%.
- **M1 stays 76.4% and her pay is unchanged.** Only the diagnostics are distorted, and low coverage flags the sloppy scanning.

The one place durations reach pay is the time split between families on mixed-family days (§10). Operator A works one family all day, so her split is 100% whatever the scans say.

---

## 10. Skill: family efficiency, ILUO levels and tiers

### 10.1 Formulas
```
Family share        share_f = Bundle active minutes in family f ÷ Σ bundle active minutes
Family NAM          NAM_f   = NAM × share_f
Family efficiency   Eff_f   = EM_n,f ÷ NAM_f
Defect rate         DR_f    = Defective qty attributed in f ÷ pieces produced in f
```

| Level | Criteria (rolling window, minimum volume 600 EM `[P]`) |
|-------|---------------------------------------------------------|
| I | Default for a new family, or below L |
| L | Eff_f ≥ 55% and DR_f ≤ 3.0% |
| U | Eff_f ≥ 80% and DR_f ≤ 1.5% |
| O | U for 2 consecutive evaluations and Eff_f ≥ 95% |

| Tier | Skill-evaluated families at ≥ U |
|------|----------------------------------|
| T1 | < 2 |
| T2 | ≥ 2 |
| T3 | ≥ 4, incl. ≥ 1 Grade A, ≥ 2 machine classes |
| T4 | ≥ 6, incl. ≥ 2 Grade A, ≥ 3 machine classes |

### 10.2 Worked numbers: Operator B's month
NAM = 12,180 (A 12,480 − OS 300).

| | Hemming | Sleeve setting (new) | Total |
|--|---------|----------------------|-------|
| Pieces | 7,000 | 1,900 | |
| EM_g | 7,000 × 0.90 = 6,300 | 1,900 × 1.40 = 2,660 | 8,960 |
| Defects attributed | 0 | 40 pcs → DD 56 | 56 |
| EM_n | 6,300 | 2,604 | 8,904 |
| Bundle active minutes | 6,800 | 3,800 | 10,600 |
| Share | 64.15% | 35.85% | 100% |
| NAM_f | 7,813.6 | 4,366.4 | 12,180 |
| **Eff_f** | 6,300 ÷ 7,813.6 = **80.6%** | 2,604 ÷ 4,366.4 = **59.6%** | 8,904 ÷ 12,180 = 73.1% |
| DR_f | 0% | 40 ÷ 1,900 = **2.11%** | |
| **Level next period** | **U** (80.6% ≥ 80%, 0% ≤ 1.5%) | **L** (59.6% ≥ 55%, 2.11% ≤ 3.0%; volume 2,660 ≥ 600) | |

Check: the weighted family efficiencies add back to her overall M1 of 73.1%. The time split only *redistributes* her NAM between families; it never changes the total.

**Tiers:**
- **A:** U in Seam join and Hemming → 2 families → **T2**.
- **B:** U in Hemming only → **T1**. Sleeve setting reaching U later would make her T2.
- **C:** U in 6 skill-evaluated families, incl. 2 Grade A, across SNLS, OL and FL → **T4**. Her buttonhole work counts in her output and pay, not in her tier.

### 10.3 Why this form
- **Families make skill portable:** B's sleeve-setting progress counts on any future style with a sleeve-setting operation.
- **Separate pass/fail criteria** for efficiency and quality. A fast but sloppy operator can't reach U. Defects count in both on purpose: the deduction measures their output cost, and the defect rate gates the level. *(C-4, noted in spec §10.4.)*
- **Automatic-machine work is excluded from skill evaluation.** Industry grading folds machine type into the operation grade instead of counting machine classes. Our tiers *do* count machine classes, so excluding automatic families is what keeps "machine diversity" meaningful: a buttonhole machine is easy to master and shouldn't make anyone look more versatile.
- **Levels are fixed for the following pay period:** pay rules use a stable level, not one that changes mid-month.
- **Allocation follows the matrix:** bottleneck and Grade A stations go to operators at U or O in that family (spec §7.4). Because assignments affect pay, they follow skill levels rather than the leader's preference. Placing someone below U is allowed; the proficiency factor compensates them.
- **Why bundle durations for the family split?** To tell a strong family from a weak one, you need time per family. Splitting by earned minutes instead would give every family the operator's overall efficiency, so nothing could be told apart. Bundle scans give that split for free and are reliable enough under scanning discipline.
- **Why level O carries no separate pay (spec DEC-22).** O operators are the most skilled, and they already earn the most, through their output. On a month with 12,000 NAM at θ = 0.70, a U operator at 80% earns (0.80 − 0.70) × 12,000 = **1,200** excess minutes; an O operator at 95% earns (0.95 − 0.70) × 12,000 = **3,000**, i.e. 2.5×. Paying for the level as well would pay for the same skill twice. O is used where expertise matters without a pay rule: allocation to bottleneck and Grade A stations, training planning, and the skill metrics payroll uses for the special allowance. O is purely data-based; there is no trainer designation.

### 10.4 Edge checks
- **Too little volume** (< 600 EM in the window): the previous level is kept, so a few bundles can't promote or demote anyone.
- **One bad evaluation:** a warning only; a second consecutive one downgrades by one level.
- **No work in a family for 180 days:** drops one level (minimum L if the operator had reached U).
- **Automatic families still take a share of time** in the split, so the other families' efficiency isn't inflated.

---

## 11. The incentive chain

### 11.1 Formulas
```
Incentive minutes        IM   = Σ (pieces × SAM × PF) − DD
   PF by level in the family: I 1.25 · L 1.10 · U/O 1.00 · not-skill-evaluated 1.00   [P]
   PF applies only to the first PF_cap [P 2,400, set per grade] earned minutes in that family (cumulative across months), or until U
Daily threshold factor   θ_day = θ on normal days; lowered on style ramp-up days (§12)    θ [P 0.70]
Threshold minutes        TM   = Σ_days θ_day × NAM_day     (= θ × NAM when there are no ramp days)
Excess incentive minutes X    = max(0, IM − TM)     (aggregated over the pay period)
Payable incentive units  U    = X × M_tier     T1 1.00 · T2 1.05 · T3 1.10 · T4 1.20   [P]
```
Payroll converts U into money with its own rates. U is one total per operator per period; it is not split by time category (spec §11.5).

### 11.2 Worked numbers: the three operators, one month (no ramp days)

| Step | A — steady (T2) | B — learner (T1) | C — floater (T4) |
|------|-----------------|------------------|------------------|
| Attended A | 12,480 normal + 1,200 OT = **13,680** | **12,480** | **12,480** |
| Approved OS | 400 (waiting 150, breakdown 250) | 300 (material 200, meeting 100) | 250 (waiting 150, breakdown 100) |
| **NAM** | **13,280** | **12,180** | **12,230** |
| Work done | Side seam: 7,800 pcs normal + 950 pcs OT × 1.20 | Hemming 7,000 × 0.90; sleeve setting 1,900 × 1.40 | Collar 1,500 × 1.80; placket 1,600 × 1.60; buttonhole 1,200 × 1.70; sleeve 700 × 1.40 |
| **EM_g** | 9,360 + 1,140 = **10,500** | 6,300 + 2,660 = **8,960** | 2,700 + 2,560 + 2,040 + 980 = **8,280** |
| DD | 30 × 1.20 = **36** | 40 × 1.40 = **56** | 10 × 1.80 = **18** |
| **EM_n** | **10,464** | **8,904** | **8,262** |
| **M1** | 10,464 ÷ 13,280 = **78.8%** | 8,904 ÷ 12,180 = **73.1%** | 8,262 ÷ 12,230 = **67.6%** |
| PF effect | none (U) | Sleeve setting is new, so level I and PF 1.25 on the first 2,400 EM: 2,400 × 0.25 = **+600** | none (U, or not skill-evaluated for buttonhole) |
| **IM** | **10,464** | 8,960 + 600 − 56 = **9,504** | **8,262** |
| TM = 0.70 × NAM | **9,296** | **8,526** | **8,561** |
| **X** | **1,168** | **978** | **0** (299 short) |
| × M_tier | × 1.05 | × 1.00 | × 1.20 |
| **U to payroll** | **1,226.4** | **978** | **0** |

**No time-category split.** A's 1,200 overtime minutes simply add to her attended time and her 1,140 overtime earned minutes to her output; the incentive is computed on the month as a whole, and IE sends payroll **1,226.4** units as one figure. An earlier draft split units between normal time and overtime in proportion to incentive minutes, so payroll could apply overtime premiums to the overtime share. That made the incentive logic more complex (for example, which category a defect deduction comes out of) for little benefit, so it was removed. If HR/payroll ever determine that statutory premiums apply to incentive earned in overtime, IE can supply earned minutes by time category, because every production record carries its finish date and time (spec §11.5).

### 11.3 What the three cases demonstrate
- **A:** the straightforward case. Good output, a few defects (36 minutes lost), a versatility bonus of 5% on the excess.
- **B:** the proficiency factor at work. Without it, B's excess would be 8,904 − 8,526 = **378**. With it, **978**, about 2.6×. That is the leeway that makes taking on a new family worth her while. *(The size of this effect depends entirely on PF and PF_cap, which are placeholders. Shadow-mode calibration sets them so the leeway roughly offsets the learning loss, no more.)*
- **C:** the floater. She has the highest tier and the most valuable skills, yet earns **no incentive**, because constant moves kept her below the threshold. The decision (spec DEC-15) is deliberate: the base scheme rewards output, not flexibility. Floating is not an established role and is expected to be rare, so such cases are compensated by **payroll's special allowance**, using the tier and level data IE reports.

### 11.4 Why this form
- **Individual and output-based:** each operator's numbers depend only on their own good output and their own accountable time.
- **A reachable threshold, linear above it, aggregated monthly:** predictable pay. One bad day doesn't erase a good month.
- **The threshold scales with NAM:** C's threshold is 8,561, not a fixed number. Approved stops lower the bar automatically.
- **Pure vs pay quantities stay apart:** B's 600 PF bonus exists only in IM. Her EM_g (8,960) and M1 (73.1%) are untouched, so costing and line efficiency aren't distorted.
- **The cap is in earned minutes, not hours:** "the first 2,400 minutes of work in a new family get the learning factor" is easy to explain to an operator, and doesn't depend on how her time is split between families.
- **Scope:** anyone doing SAM work is in the scheme, including automatic-machine operators and helpers on SAM tasks. Roles with no SAM output (line leaders, line QC, feeders, mechanics) are outside the IE incentive (spec DEC-14). Cutting is outside bundle capture and the incentive; it is tracked through its own MOs.
- **Eligibility:** IE also reports flags such as minimum attendance in the period `[P]`. Payroll decides their consequences.

### 11.5 Edge checks
- **Below threshold:** X = 0, never negative. A bad month costs the incentive, never base pay.
- **Level changes mid-month:** ignored until the next period, because the level is fixed at period start.
- **PF cap reached mid-month:** PF applies only to the first 2,400 EM; later pieces in the family count at 1.00.
- **A bundle that crosses the cap (interim rule):** it is split. With 2,350 EM used and a 70-EM sleeve bundle, 50 EM get PF 1.25 and 20 count at 1.00, a bonus of 12.5. The mechanism is to be reconsidered in technical design for simplicity (spec FLAG-TECH-14). A time-based cap should only return if it avoids the C-1 problem (§18), where scan durations moved the bonus.
- **The cap carries across months (spec DEC-23):** an operator who used 2,000 EM of the cap last month has 400 left this month. It does **not reset** after a long break from the family, which keeps the rule simple and impossible to game.
- **Reaching U mid-month:** the level is fixed at the start of the month, so she keeps PF until month-end (within the cap). The lag is bounded by the cap and accepted.
- **Cap per grade:** a Grade A family such as collar setting may take longer to master than a Grade C family such as hemming. PF_cap is therefore a parameter per grade, all starting at 2,400; shadow-mode data shows how many earned minutes learners actually need per grade. For an easy family a shared cap does no harm, because PF stops anyway when she reaches U.

---

## 12. Style changeover: familiarity, ramp profiles and the ramp-adjusted threshold

### 12.1 The problem
On a new style, even expert operators start slower: new specs, machine settings, guides, material handling, and a line that has to rebalance and get work flowing. The proficiency factor doesn't help here, because the operators already know those *families*. Without an adjustment, every changeover takes a bite out of everyone's incentive. Standard garment practice is to **lower the bonus target during the learning period**, following the learning curve.

### 12.2 One curve family, three uses
```
Learning curve   e(d) = P × r(d)
   P    = plateau: the efficiency a line settles at (depends on product type and line; used for planning only).
          The product type is an IE field on the product category, so a style gets it from its category (spec DEC-24).
   r(d) = ramp profile: day-d efficiency as a fraction of plateau (depends on how unfamiliar the style is)
```

| Use | Uses | Where |
|-----|------|-------|
| Daily targets | e(d) = P × r(d) | §6.4 |
| Costing (E_plan) | The average of e(d) over the order quantity | §5.2 |
| Incentive threshold on ramp days | r(d) only, never P | §12.5 |

There are no per-style curves. There are a few **ramp profiles**, one per class, and the plateau is kept separate. A difficult but familiar style gets a low plateau with **no** ramp; an easy but unfamiliar style gets a normal plateau **with** a ramp.

### 12.3 How unfamiliar is a style? The familiarity score
```
F = SAM of the new OB's operations whose library operation code this line ran in the last [P 90] days
    ÷ Garment SAM of the new OB
```

| Class | F `[P]` | Bootstrap ramp profile r(d) `[P]` |
|-------|---------|-----------------------------------|
| R0 Minor / repeat | ≥ 90% | No ramp |
| R1 Similar | 60–90% | 0.75 → 0.90 → 1.00 |
| R2 New | < 60% | 0.500 → 0.6875 → 0.875 → 1.00 |
| R3 Complex | IE only | 0.40 → 0.55 → 0.70 → 0.85 → 0.95 → 1.00 |

The system suggests the class, and the IE confirms or overrides it with a reason. Overrides are reported monthly per line.

**Worked numbers: two variants of PS-01 (garment SAM 10.00) on Line 1, which runs PS-01 every week**

| Variant | Change | New garment SAM | Familiar SAM | **F** | **Class** |
|---------|--------|-----------------|--------------|-------|-----------|
| V1 | Bottom hem → bottom hem with side vents (0.80 → 0.95) | 10.15 | 10.15 − 0.95 = 9.20 | **90.6%** | **R0**, no ramp |
| V2 | Collar attach → contrast collar with tipping (1.80 → 2.10) | 10.30 | 10.30 − 2.10 = 8.20 | **79.6%** | **R1**, short ramp |

Each variant differs from PS-01 by one operation, but changing the critical collar gets a ramp while the hem variant doesn't. Weighting by SAM makes that happen without any special rule. (The rubric-based IE override covers cases where a small-SAM change is still hard.)

### 12.4 Where the ramp profiles come from: fitting on your own data
For every completed changeover:
```
Observed r(d) = On-standard efficiency on day d ÷ Run plateau
Run plateau   = average on-standard efficiency from day [P 6] to the end of the production run (one OB on one line)
```
Only production by **U/O operators** is used, so the curve measures the *style's* effect, not individual learning.

Profiles are fitted on on-standard efficiency, while planning uses overall efficiency (§5.2). Both are fine, because r(d) is a **ratio to a plateau on the same basis**: the basis cancels out. Planning multiplies r(d) by the overall plateau; the incentive uses r(d) alone.

**Worked numbers: four past R2 changeovers**

| Day | Run 1 | Run 2 | Run 3 | Run 4 | **Fitted r(d) = median** |
|-----|-------|-------|-------|-------|--------------------------|
| 1 | 0.45 | 0.52 | 0.48 | 0.55 | **0.50** |
| 2 | 0.62 | 0.70 | 0.66 | 0.71 | **0.68** |
| 3 | 0.85 | 0.90 | 0.86 | 0.92 | **0.88** |
| 4 | 0.95 | 0.98 | 0.97 | 1.00 | **0.975** → counts as plateau (≥ 0.95) |

Before a class has enough runs (`[P 10]`), the bootstrap profile applies. Once fitted profiles exist, they replace the bootstrap and are refitted periodically. Nothing is assigned by judgement once the data exists.

### 12.5 The ramp-adjusted threshold

**Formula**
```
θ_day = max( θ_floor , θ × [ Σ_k s_k × r_k(d_k) + (1 − Σ_k s_k) ] )
   s_k = operator's share of that day's earned minutes on ramping style k (quantity-based)
   θ_floor [P 0.30]
TM = Σ_days θ_day × NAM_day
```

**Worked numbers: θ_day for a full day on an R2 style (θ = 0.70)**
| Ramp day | r(d) | θ_day |
|----------|------|-------|
| 1 | 0.500 | **35.0%** |
| 2 | 0.6875 | **48.1%** |
| 3 | 0.875 | **61.3%** |
| 4+ | 1.00 | **70.0%** |

- **Half a day on the new style (day 1):** θ_day = 0.70 × (0.5 × 0.50 + 0.5) = **52.5%**.
- **R3 style, day 1:** 0.70 × 0.40 = 28%, so the floor applies and θ_day = **30%**.

**Worked numbers: a month with two R2 changeovers.** One operator with 465 NAM a day, performing at 79% normally and at 40% / 55% / 70% on the 6 ramp days:

| | Normal month (no changeovers) | 2 changeovers, flat threshold | 2 changeovers, ramp-adjusted threshold |
|---|---|---|---|
| IM | 9,551.1 | 8,881.5 | 8,881.5 |
| TM | 8,463.0 | 8,463.0 | 7,852.7 |
| **X** | **1,088.1** | **418.5** (−61.5%) | **1,028.8** (94.6% of normal) |

An operator who performs *at* the curve keeps about 95% of a normal month's bonus. Beating the curve still pays more, so a fast ramp-up is rewarded.

### 12.6 Stacking with the proficiency factor
| | Proficiency factor | Ramp-adjusted threshold |
|--|-------------------|-------------------------|
| Cause | *This operator* hasn't mastered this family | *This style* is new, for everyone |
| Acts on | Incentive minutes (raises credited output) | Threshold (lowers the bar) |
| Tuned on | First production in new families, **ramp days excluded** | Changeovers, **U/O operators only** |

| Operator performing as expected | Established style | New R2 style, day 1 (bar 35%) |
|---------------------------------|-------------------|-------------------------------|
| U level | 80% vs bar 70% → **+10 points** | 40% vs bar 35% → **+5 points** |
| Learner, level I (PF 1.25) | 56% × 1.25 = 70% vs 70% → **at the bar** | 28% × 1.25 = 35% vs 35% → **at the bar** |

Each mechanism cancels only its own cause, so their effects multiply without double counting. That holds because each is tuned on data that excludes the other's cause.

### 12.7 Edge checks
- **Colour or size variant of the same OB:** not a changeover.
- **Style resumes after a short pause:** it ran within 90 days, so its familiarity is high → R0.
- **Same style on a line that never ran it:** familiarity is measured per line, so that line gets its own class.
- **Re-coding a style to get a ramp:** familiarity is calculated from library codes, the IE confirms the class, and class mix and overrides are reported monthly.
- **Changeover setup time** (machine resetting, attachments): OS-09, separate from the ramp.

---

## 13. Self-funding check

### 13.1 Formula
```
Labour cost per earned minute = (Base wages + Incentive paid + Allowances) ÷ Σ EM_g
```
This should **fall or stay flat** as overall efficiency (M3) rises.

### 13.2 Worked numbers: Line 1 (30 operators, A = 30 × 12,480 = 374,400 min/month)
| Month | Base | Incentive | Allowances | Total | Σ EM_g | M3 | **Cost per EM** |
|-------|------|-----------|------------|-------|--------|-----|-----------------|
| 1 | 255 M | 20 M | 5 M | 280 M | 261,000 | 69.7% | **1,072.8** |
| 2 (healthy) | 255 M | 40 M | 5 M | 300 M | 285,000 | 76.1% | **1,052.6** ↓ |
| 2 (unhealthy) | 255 M | 70 M | 5 M | 330 M | 285,000 | 76.1% | **1,157.9** ↑ |

In the healthy case the company pays 20 M more in incentives but each earned minute gets cheaper: the extra output more than funds the bonus. In the unhealthy case, the scheme pays out more than the productivity it buys, so θ, the payroll rate or the multipliers need review.

---

## 14. Line reconciliation: do the parts add up?

### 14.1 The three operators summed
| | A | B | C | **Σ** |
|--|---|---|---|-------|
| Attended | 13,680 | 12,480 | 12,480 | **38,640** |
| OS | 400 | 300 | 250 | **950** |
| NAM | 13,280 | 12,180 | 12,230 | **37,690** |
| EM_g | 10,500 | 8,960 | 8,280 | **27,740** |
| DD | 36 | 56 | 18 | **110** |
| EM_n | 10,464 | 8,904 | 8,262 | **27,630** |

| Metric | Calculation | Result |
|--------|-------------|--------|
| Line on-standard M4 (gross) | 27,740 ÷ 37,690 | **73.6%** |
| Operators' pooled M1 (net) | 27,630 ÷ 37,690 | **73.3%** |
| Overall M3 | 27,740 ÷ 38,640 | **71.8%** |
| Off-standard ratio M5 | 950 ÷ 38,640 | **2.46%** |
| Check | 73.6% × (1 − 0.0246) | **71.8%** ✔ |

### 14.2 Why line and operator figures differ, by exactly the defects
The gap between 73.6% and 73.3% is the **110 deducted minutes**. The line *did* produce those pieces; they were repaired later, and the repair time shows up as lost time. The individuals are accountable for their defects. Both views are correct for their purpose, and the difference is always explainable as Σ DD. *(C-5, noted in spec §4.)*

### 14.3 Lost time by reason
| Code | Minutes |
|------|---------|
| Breakdown (OS-01) | 350 |
| Waiting for work (OS-03) | 300 |
| Material wait (OS-02) | 200 |
| Meeting (OS-06) | 100 |
| **Total** | **950** ✔ = Σ OS |

---

## 15. Real-time monitoring: the same logic, more often

### 15.1 Formulas
```
Rolling window              W  [P 60 min]
Hourly target               = Operators present × 60 × e(d) ÷ Garment SAM
Line output (W)             = pieces completed at the last operation within W
Station planned output (W)  = Operators at station × W × e(d) ÷ SAM at the station
Station throughput ratio    = Completions at the station within W ÷ Station planned output (W)
Starved time (W)            = minutes in W with an empty input buffer and no active bundle
Live bottleneck             = lowest throughput ratio among stations NOT starved > [P 10%] of W
```
Nothing here is new logic. These are the spec's period definitions applied to a one-hour window, plus the station layout that balancing (§6.2) already produces.

### 15.2 Worked numbers: Line 1, 10:00–11:00 on a plateau day
- Hourly target = 30 × 60 × 0.80 ÷ 10.00 = **144** polos.
- On day 2 of a new R2 style with 28 operators present: 28 × 60 × 0.55 ÷ 10.00 = **92.4**. The board follows the ramp and attendance automatically.

| Station (in line order) | Planned (W) | Completed | Ratio | Input buffer | Starved (min) |
|-------------------------|-------------|-----------|-------|--------------|---------------|
| Placket attach | 150.0 | 148 | 98.7% | 5 | 0 |
| Shoulder join | 160.0 | 158 | 98.8% | 4 | 0 |
| **Collar attach** | 133.3 | 112 | **84.0%** | 7 ↑ | 0 |
| Sleeve attach | 137.1 | 118 | 86.0% | 1 | 12 |
| Side seam | 160.0 | 115 | 71.9% | 1 | 15 |
| Sleeve + bottom hem | 141.2 | 113 | 80.0% | 1 | 16 |
| Buttonhole & button sew | 141.2 | 112 | 79.3% | 0 | 18 |

**Reading it:**
- **Line output** = 112 (last station) against a target of 144 = **77.8%**, which triggers the "line below 85%" alert.
- **Naive bottleneck:** side seam has the lowest ratio (71.9%). But it was starved for 15 of 60 minutes: it is slow because nothing reached it.
- **Live bottleneck:** among stations not starved (placket, shoulder, collar), the lowest ratio is **collar attach (84.0%)**, and its input buffer is growing (7 bundles). Every station after it is starved.
- **What the leader sees:** move a U-level collar operator in, or check the collar machines. This is the same conclusion the planned layout predicted (§6.2: collar was the planned bottleneck at 0.360 load). Real time shows it is happening *now*, and how much it costs.

### 15.3 Why exclude starved stations
On a line, a bottleneck starves everything after it, so downstream stations show low throughput too. Plain "lowest ratio" would send the leader to the wrong station (here, side seam). Excluding starved stations points to the cause, not the victims.

### 15.4 v1 features (spec DEC-20)
| # | Feature | Why it's worth it |
|---|---------|-------------------|
| RT-1 | Hourly production board | The industry-standard line board; pure aggregation |
| RT-2 | Exception alerts | Simple checks on data already recorded |
| RT-3 | Breakdown call → maintenance request | Reuses the work-order pause; shortens downtime directly |
| RT-4 | Operator figures feed to the MES interface | Today's slice of existing metrics; drives engagement |
| RT-5 | Station WIP flags | Needs only the recorded station layout |
| RT-6 | Live bottleneck | Comes almost free with RT-5 (§15.2) |
| RT-7 | Station pace | Diagnostic; uses bundle durations |

Re-balancing suggestions are noted for later: high value, but they need optimisation logic and mature skill data.

---

## 16. How it fits together

### Who is protected from what
| Risk | Protected party | Mechanism | Where shown |
|---|---|---|---|
| Breakdown, material shortage, power cut | Operator | Approved off-standard codes | §3, §14.3 |
| No work at the station | Operator | "Waiting for work" entered by the leader; leader reassignment | §3 |
| Being moved to an unfamiliar family | Operator | Proficiency-factor leeway | §11, Operator B |
| A new style for the whole line | Operator | Ramp-adjusted threshold | §12 |
| Arbitrary allocation | Operator | Skill-matrix allocation rules | §10 |
| Unfair SAM | Operator | Governance and dispute process | §4 |
| Unpredictable earnings | Operator | Reachable threshold, linear incentive, monthly aggregation | §11 |
| Floating at a cost to own output | Operator | Payroll special allowance (rare cases) | §11.3 |
| Paying for defective work | Company | Defect deduction | §8 |
| Gaming of scans or durations | Company | Clock-time denominator; attendance as master clock | §3.5, §9.4 |
| Favouritism in off-standard approvals | Company | Off-standard reported by approving leader | §3.2 |
| Fake quantities | Company | One operator per bundle | §7 |
| Generous changeover classes | Company | Calculated familiarity, IE confirmation, override reporting | §12.7 |
| Inflated skill from easy machines | Company | Automatic families not skill-evaluated | §10.3 |
| Scheme costing more than it earns | Company | Self-funding check | §13 |
| Untested parameters affecting pay | Both | Shadow mode before switch-on | spec §14 |
| Hidden line problems | Both | Lost time by reason; waiting as a balancing KPI; idle-gap analysis | §3.5, §14.3 |
| Problems found too late to fix | Both | Hourly board, alerts, live bottleneck | §15 |
| Long breakdowns | Both | Breakdown call opens a maintenance request | §15.4 |

### How each role's incentives line up
| Role | What they want | How the framework aligns it with the factory's interest |
|---|---|---|
| Operator | Higher earnings | Earnings rise only with good output and versatility |
| Line leader | Smooth line | Measured on waiting, WIP and line efficiency; approvals are logged |
| IE | Accurate standards | Planned-vs-actual analysis; disputes resolved on evidence; ramp profiles fitted from data |
| Management | Cost and delivery | Order-size- and familiarity-aware costing; capacity in minutes; self-funding check |

### Why individual (and not group or hybrid)
- **Simple and flexible:** no group definition, and operators can move freely between lines.
- The usual weaknesses of individual schemes are covered by specific mechanisms:
  - quantity over quality → defect deduction
  - resistance to moves → proficiency factor and tier reward
  - starvation → waiting code
  - WIP build-up → bundle release control
- The line share remains a lever for later if flow or quality problems persist.

### Why IE stops at "units"
IE is good at minutes; payroll is good at money and law. Rates, statutory premiums, social insurance and allowances stay in payroll, so legal changes never require reworking IE logic.

---

## 17. Alternatives considered and why they were set aside

| Alternative | Why not (for now) |
|---|---|
| Group or hybrid incentive | Adds the group definition and pool rules, and conflicts with flexible staffing. Kept as a future lever. |
| Bundle-duration denominator for pay | Makes gaming matter (§9.4 shows why clock time is robust). |
| Off-standard only through work-order pauses | Between-bundle stops (waiting for work, meetings, setup) would count against operators. The same record shape with a leader entry channel costs almost nothing extra. |
| A rated time study as the formal verification formula | Rating is a judgement call anyway, and verification happens outside the system; the system records the dispute, evidence and decision. |
| Pace-outlier flag | Unnecessary once durations don't affect pay. |
| Manual "training" tag | Arbitrary; the proficiency factor builds the leeway into the calculation. |
| Leader station-assignment log as the time basis for skill | A new leader duty at every move, for little gain; bundle scans already give time per family. |
| Splitting time between families by earned minutes | Gives every family the same efficiency, so skill levels couldn't tell families apart (§10.3). |
| Difficulty multiplier on earned minutes | Distorts efficiency and costing; difficulty enters through tier criteria. |
| Machine-class "type" parameter for tier diversity | An extra parameter only for skill; flagging automatic families as not skill-evaluated is simpler. |
| Weighted composite skill score (60% efficiency / 40% yield) | Yield ≈ 99% for nearly everyone, so the weighting is illusory. Separate pass/fail criteria instead. |
| Daily all-or-nothing quality gate | A cliff effect on small, noisy samples, and unpredictable pay. |
| No defect capture in v1 | Loses attribution and quality data for one cheap scan saved. |
| Fixed skill allowance as the main skill reward | Sticky in contracts and adds to the social insurance base. Kept as an optional payroll allowance. |
| Station-change allowance and a designated floater role | Not needed for a rare, unestablished role; payroll handles exceptions. |
| "New OB = new style" | Too generous for minor variants and invites re-coding; familiarity measures the actual difference. |
| A learning curve per style | Impossible to know before production and unnecessary; a few class profiles fitted from data do the job. |
| Ignoring style ramp-up in pay | About 61% of incentive lost in a month with two changeovers (§12.5), for a cause outside the operator's control. |
| Re-balancing suggestions in v1 | Needs optimisation logic and mature skill data; noted for later. |
| "Lowest throughput" bottleneck without excluding starved stations | Points to the victims downstream instead of the cause (§15.3). |
| Work-centre cost per line-hour | Must be re-keyed whenever headcount changes; cost per operator-minute (§5.1) doesn't. |

---

## 18. Coherence review: status

The v0.1 review findings, now resolved in spec v0.2:

| Finding | What it was | Resolution |
|---------|-------------|------------|
| **C-1** Bundle durations reaching pay | The PF cap was in hours, which depend on the time split: a 500-minute scan shift moved B's PF bonus by 42.5 minutes. | **Applied.** PF cap is now in earned minutes (DEC-07). Durations are used only to split time between families for skill evaluation, a documented and bounded use (DEC-02 rev.). |
| **C-2** No leeway for new styles | Two changeovers cut a month's incentive by about 61%. | **Applied.** Familiarity score → ramp class → fitted ramp profile → ramp-adjusted threshold (DEC-13, §12). |
| **C-3** Learning-curve basis | A curve on the wrong basis overstated targets by 7.5% and understated CM by 7.0%. | **Applied.** e(d) = P × r(d) with plateau on the overall basis (spec §7.7.6). |
| **C-4** Quality counted twice in skill | | **Kept by design;** noted in spec §10.4. |
| **C-5** Line vs operator totals | | **Intended;** noted in spec §4. |
| **C-6** Operator state | | **Flagged** (FLAG-TECH-07). |

Items added in v0.2:
- OPEN-11: continuous familiarity model
- OPEN-12: shadow-mode design
- OPEN-13: product-type taxonomy for plateaus
- FLAG-TECH-08: library operation codes on OB operations
- FLAG-TECH-09: ramp calendar

Resolved or added in v0.3:
- OPEN-02 closed: one off-standard bucket, three channels
- OPEN-03 closed: monthly aggregation
- OPEN-08 removed: statutory classification is payroll's concern
- OPEN-14 added: real-time monitoring design
- FLAG-TECH-10 added: off-standard bucket implementation
- Time-source rules added (attendance as master clock)
- Production run defined

Added in v0.4:
- Real-time monitoring definitions and v1 features (DEC-20); OPEN-14 closed (business side)
- FLAG-TECH-11: real-time implementation

Added at baseline (2026-10-18):
- DEC-21: parameters configurable and versioned; tuning waits for shadow-mode data
- FLAG-TECH-12: parameter configuration

Settled in v0.5:
- OPEN-04 closed: level O data-based, no separate pay (DEC-22)
- OPEN-05 closed: PF_cap cumulative, no reset, level lag accepted, cap per grade (DEC-23)
- OPEN-06 closed: failed repairs cost no one; repeat failures reported
- OPEN-13 closed: product type on the product category (DEC-24)
- OPEN-15 restated: options (A) and (B), decided during technical design

Settled in v0.6 (from the acceptance test cases):
- Precision convention; R2 day 2 = 0.6875
- Upgrades immediate; downgrade grace also when failing on defect rate
- Defect records exceeding the bundle rejected with an error (FLAG-TECH-13)
- Interim split for a bundle crossing PF_cap (FLAG-TECH-14)
- Time-category split of the incentive removed; U is one total

**Overall assessment.** The core chain still reconciles exactly (§14):
time accounting → pure earned minutes → incentive minutes and threshold → payroll units.
The changeover mechanism reuses the planning curve family rather than adding a parallel one. The two leeways are separable by construction. What remains open is mainly parameter values and calibration, which shadow mode is designed to settle.

---

## 19. What to watch after go-live

1. **Off-standard discipline:** M5 by line, code, channel and approving leader; leaders approving too much (inflated efficiency) or too little (frustrated operators).
2. **Threshold reachability:** the share of U-level operators with X > 0 in a normal month.
3. **Changeovers:** class mix and IE overrides per line; observed vs fitted ramp profiles; incentive efficiency on ramp days vs normal days.
4. **Leeway sizing:** whether PF and the ramp threshold roughly offset the learning loss, without becoming a windfall.
5. **The self-funding curve (§13).**
6. **SAM calibration gaps:** M6 pace by family in the first months.
7. **Defect attribution disputes:** many disputes mean the QC operation coding needs training or clearer defect codes.
8. **Payroll exceptions for floaters:** if they stop being rare, revisit DEC-15.
9. **Data-quality exceptions:** volume of scans outside attendance and bundles open at clock-out. A falling trend means scanning discipline is taking hold.
10. **Unexplained idle time:** idle-gap analysis per station.
11. **Alerts:** volume and leader response time. Too many alerts get ignored, so tune the `[P]` thresholds.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-13 | First version: rationale for Spec v0.1, coherence review C-1 to C-6. |
| 0.1 rev. | 2026-10-14 | Restructured around one running example; all formulas with worked numbers; numbers for C-1 to C-5. |
| 0.2 | 2026-10-16 | Aligned with Spec v0.2: grading rubric and not-skill-evaluated families (buttonholing); PF cap in earned minutes (Operator B recomputed: X 978); new §12 on style changeover (familiarity score with worked variants, ramp classes, fitting example, ramp-adjusted threshold, stacking); floater handled by payroll; incentive scope; coherence review turned into a status table; alternatives and watch list extended. All arithmetic re-checked by script. |
| 0.3 | 2026-10-17 | Aligned with Spec v0.3: off-standard bucket with three channels (§3.2); time sources, master clock, clipping example and idle-gap analysis (§3.5); dispute section rewritten as system records vs human verification (§4.2, rating example removed); cutting scope; real-time monitoring principle (§15); production run in ramp fitting; protection, alternatives, status and watch lists updated. |
| 0.3 rev. | 2026-10-17 | Correction to §3.5: no automatic pause at breaks or shift end; clipping is an undecided option (OPEN-15). |
| 0.3 rev. 2 | 2026-10-17 | Review fixes: symbol glossary; dispute example now a standard error (effective-date rule); daily headcount and max load use the day's efficiency, not E_plan; M8 added; §9.4 heading and family-split caveat; allocation rule (§10.3); eligibility flags (§11.4); basis-independence of r(d) (§12.4); buttonhole operation relabelled. |
| 0.4 | 2026-10-17 | New §15 Real-time monitoring with worked numbers (hourly target, station throughput ratios, why starved stations are excluded from the bottleneck, v1 features); later sections renumbered 16–19; protection, alternatives, status and watch lists updated. |
| 0.4 rev. | 2026-10-18 | Baseline: note on configurable, versioned parameters (DEC-21). |
| 0.4 rev. 2 | 2026-10-18 | Scope note in §5: costing not in v1. |
| 0.5 | 2026-10-18 | Aligned with Spec v0.5: why level O carries no separate pay, with numbers (§10.3); PF_cap carry-over, no reset, level lag and cap per grade (§11.1, §11.5); product type from the product category (§12.2); OPEN-15 options (A) and (B) presented equally (§3.5); status list (§18). |
| 0.6 | 2026-10-19 | Aligned with Spec v0.6: time-category split removed from the incentive chain (§11.1, §11.2) with the reason; interim rule for a bundle crossing the cap (§11.5); R2 day 2 written as 0.6875; status list (§18). |
