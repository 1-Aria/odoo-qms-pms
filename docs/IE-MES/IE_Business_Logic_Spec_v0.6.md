# IE Module — Business Logic Specification

**Version:** v0.6 (draft) · 2026-10-19
**Scope:** Business and functional logic of the Industrial Engineering (IE) module for garment manufacturing: definitions, formulas, rules and parameters. **Technical implementation is out of scope.** Technical concerns are only flagged (`FLAG-TECH`).
**Companion documents:** `IE_Module_Function_Map.md` (v0.8) is the scope index (and describes the document set and workflow); `IE_Framework_Rationale_v0.6.md` explains the reasoning, with worked numbers; `IE_Acceptance_Test_Cases_v0.3.md` turns the rules into expected results. This spec holds the rules.
**Context sources:** discussions of 2026-10-12 to 2026-10-17; `IE Design.md` (used for intent only, not as a template).

**Status:** Business logic baseline (2026-10-18). Further changes go through the document workflow (function map). Parameter values are configuration, not logic.

**Conventions**
- `[P]`: configurable parameter. Values shown are **illustrative defaults** to be set from factory data (see §14).
- `[OPEN]`: undecided item, listed in §15.
- `FLAG-TECH`: technical concern to resolve at implementation, listed in §15.
- Minutes are the common unit throughout.
- **Precision:** calculations run at full precision; rounding is for display and hand-over only. Targets are shown to the nearest whole piece; figures sent to payroll carry 2 decimals.

---

## 0. Decision log

| ID | Decision | Rationale (short) |
|----|----------|-------------------|
| DEC-01 | **Individual incentive** based on the operator's own earned minutes. A line/group share is kept as a future option, not used in v1. | Simple, flexible (operators can move freely between lines), and the bundle data supports it. Flow and WIP problems are handled by line balancing and monitoring, not by pay. |
| DEC-02 | **Efficiency denominator = clock time:** attended minutes minus approved off-standard minutes. **Bundle durations never enter the incentive denominator.** They are used only to split time between operation families for skill evaluation (§10.2), and as diagnostics. *(Rev. v0.2)* | Pay depends on good output against time on the clock. Bundle scan data is free, reliable enough under scanning discipline, and hard to game meaningfully, so it is suitable for allocating time between families. |
| DEC-03 | **Starvation protection** comes from an approved "Waiting for work" off-standard code (entered by the line leader), not from bundle timers. | Keeps DEC-02 intact and turns waiting into data for line balancing and for analysing what delayed production. |
| DEC-04 | **Bundle = MO. One operator per operation per bundle**, credited with the full bundle quantity. Operators never enter quantities. | Removes operator-entered quantities, the main data-integrity risk. |
| DEC-05 | **Defects are deducted from the responsible operator** (defective qty × SAM), booked on the detection date. **Repair is neutral** for whoever does it (approved off-standard time). | A direct, proportional penalty, while anyone can do the repair. |
| DEC-06 | **Skill is rewarded through an operator-tier multiplier** on the incentive. Skill metrics are also reported so payroll can grant a **special allowance** to highly skilled operators. | Variable pay that can be re-evaluated in both directions; the allowance remains a payroll decision. |
| DEC-07 | **Leeway for operators on unfamiliar work** comes from a **proficiency factor** inside the calculation, capped by **earned minutes** produced in the family. No manual tags. *(Rev. v0.2: cap in earned minutes instead of hours)* | Automatic, standardised and self-expiring: the established "run-in allowance" pattern, tied to skill level. A cap in earned minutes is simpler to explain and doesn't depend on how time is split between families. |
| DEC-08 | **IE outputs metrics only.** Payroll holds all rates, money, statutory premiums and allowances. | Clean module boundary. |
| DEC-09 | **Standards come from timeSSD** and are version-controlled, with a formal amendment and dispute process. | One source of truth, defensible once standards drive pay. |
| DEC-10 | **Earned minutes stay pure** (pieces × SAM). All pay-related adjustments live in separate *incentive minutes* or in the *threshold*. | Costing, planning and line efficiency are never distorted by pay rules. |
| DEC-11 | **Operation grades follow a rubric:** critical, position/visibility, precision/handling, machine type (§5.6). *(New v0.2)* | Matches common garment grading practice. Still one grade per family, so nothing downstream changes. |
| DEC-12 | **Families on automatic or programmable machines are "not skill-evaluated":** they earn incentive normally, but get no ILUO level, no proficiency factor, and don't count towards tiers (§10.1). *(New v0.2)* | The machine controls the stitching, so the work is easy to master. Excluding it keeps skill measures meaningful without needing a machine-class type parameter. |
| DEC-13 | **Style changeover ramp-up:** each changeover gets a **ramp class** from a calculated **familiarity score**. Each class has a **ramp profile** fitted from the factory's own changeover data. On ramp-up days the incentive threshold follows the ramp profile (§7.7, §11.3). *(New v0.2)* | Standard garment practice is to lower the bonus target during the learning period. It reuses the learning-curve family already needed for planning and costing, and needs no per-style curves. |
| DEC-14 | **Incentive scope = SAM-measured work**, by anyone doing it (seamstresses, automatic-machine operators, helpers on SAM work). Roles with no SAM output (line leaders, line QC, feeders, mechanics) are **outside the IE incentive**. IE supplies line metrics on request. *(New v0.2)* | The scheme measures output in standard minutes; roles without such output need a different basis, owned by HR/payroll. |
| DEC-15 | **Floaters:** no scheme adjustment. Rare cases are compensated through payroll's special allowance, using the skill data from IE. *(New v0.2)* | The base scheme rewards output, not flexibility. The role isn't established and is expected to be rare. |
| DEC-16 | **Shadow mode before pay:** skill levels, tiers, proficiency factors and ramp profiles are calculated without pay effect for a calibration period, then switched on (§14). *(New v0.2)* | Parameters must be tuned on real data before they affect anyone's earnings. |
| DEC-17 | **One off-standard bucket, three entry channels:** (1) a work-order pause with a reason, (2) a manual entry by the line leader for one or several operators, (3) repair records. Every record must be approved. Records can't overlap each other or bundle time (§3.3). *(New v0.3)* | The same record shape is needed anyway, so the manual channel costs almost nothing and covers between-bundle cases (waiting for work, meetings, setup). |
| DEC-18 | **Attendance is the master clock for pay** (A, NAM). Bundles are paused or finished by operators and line leaders, because production may continue into breaks and overtime; an optional nightly job pauses bundles left open. Server timestamps; data-quality exceptions cleared before payroll close (§3.4). *(New v0.3, corrected 2026-10-17)* | Two time sources (attendance, scans) can disagree. Pay uses attendance; bundle time reaches pay only through the family time split, so residual scan inaccuracy has limited effect. |
| DEC-19 | **Real-time monitoring uses the same definitions**, computed continuously, and is diagnostic only. Display to operators belongs to the separate MES interface; IE supplies the metrics (§13.2). *(New v0.3)* | One set of definitions means real-time and period figures always agree. |
| DEC-20 | **Real-time v1 scope = RT-1 to RT-7:** hourly production board, exception alerts, breakdown call to maintenance, operator figures feed, station WIP flags, live bottleneck (lowest throughput ratio among non-starved stations), station pace. Re-balancing suggestions are noted for later (§13.2). *(New v0.4)* | Ranked by value for cost: these reuse existing logic, plus the station layout that balancing already produces. |
| DEC-21 | **All `[P]` parameters are configurable and versioned with an effective date.** The current placeholders (industry-typical) are the shadow-mode starting values; tuning waits for real data. Every calculation uses the values effective for the period being calculated (§14). *(New 2026-10-18)* | Values can't be set meaningfully without factory data. Tuning must not need a developer, and past periods must stay reproducible. |
| DEC-22 | **Level O is purely data-based:** the U criteria met in two consecutive evaluations, with Efficiency_f ≥ 95% in the current one. No trainer designation. O has **no separate pay effect**; it is used for allocation, training planning and the skill metrics reported to payroll (§10.4, §10.6). *(New v0.5)* | An O operator's higher efficiency already pays through excess minutes (at 95% vs 80%, about 2.5× the excess of a U operator at θ = 0.70). Paying for the level as well would pay for the same skill twice. |
| DEC-23 | **PF_cap rules:** the cap counts the operator's cumulative gross earned minutes in the family across all periods and levels; it does **not reset** after dormancy. The lag from fixing levels at period start is accepted. PF_cap is a parameter **per grade** (A, B, C) (§11.2). *(New v0.5)* | Simple and not gameable. The lag is bounded by the cap. Hard families may need a larger learning allowance than easy ones; shadow-mode data shows how many earned minutes learners need per grade. |
| DEC-24 | **Product type** (for plateaus) is an IE field on the **product category**; styles take it from their category. The plateau is kept per line × product type (§7.7.4). *(New v0.5)* | Plateaus differ strongly by product (e.g. polos vs jackets), so targets need the right one. Product categories already group styles, so no separate list has to be maintained per style. |

---

## 1. Design principles

1. **Layered flow:** master data → engineered standard → line design → execution → feedback.
2. **Standards change only through governance (§5).** The gap between actual and standard drives improvement work; it never silently rewrites the standard.
3. **Output over duration.** Performance means good output in standard minutes against clock time.
4. **One time-accounting model (§3)** feeds every metric, so metrics cannot contradict each other.
5. **Pure vs pay quantities are separate:** gross/net earned minutes for operations and costing; incentive minutes and thresholds for pay.
6. **Pay-grade rigour:** every input that affects pay (SAM version, off-standard approval, defect attribution, skill level, ramp class) is traceable to a record and an approver.
7. **Calibrate before pay:** every pay-relevant parameter is tuned on the factory's own data (§14).

---

## 2. Core definitions

| Term | Definition |
|------|------------|
| **Operation** | A style-specific work step in the Operation Bulletin (OB), e.g. "Attach collar – Style 1234". |
| **Library operation code** | The identifier of the standard library operation (timeSSD method) an OB operation was built from. Kept on every OB operation; used for the familiarity score (§7.7). |
| **Operation family** | A generic, style-independent class of operations, e.g. "Collar setting · SNLS · Grade A". Every operation maps to exactly one family. **Skill is measured at family level** so that it carries across styles. |
| **Operation grade** | Difficulty tier A/B/C assigned to a family by the rubric in §5.6. Used in skill-tier criteria (§10), not as a direct pay multiplier. |
| **Skill-evaluated flag** | Family attribute. *No* for families performed on automatic or programmable machines (DEC-12); *yes* otherwise. |
| **Machine class** | e.g. SNLS, 3/4/5-thread overlock, flatlock, bartack, buttonhole, programmable/template. |
| **SAM** | Standard allowed minutes for one piece of an operation, from timeSSD, for a specific **SAM version**. |
| **Garment SAM** | Σ SAM of all operations in the style's OB (by department, see §6). |
| **Bundle** | A physical group of cut pieces of one variant (size/colour) and one shade lot, of size ≤ bundle size `[P]`. One bundle = one MO. |
| **Production record** | Operator × operation × bundle, with quantity = bundle quantity, plus start/finish timestamps. |
| **Production run** | One OB on one line, from its changeover until the line switches to another OB (a break of up to `[P 2]` production days doesn't end the run). Ramp days, run plateau and efficiency progression are measured per run. *(New v0.3)* |
| **Attended minutes (A)** | Paid presence time from attendance, excluding unpaid breaks (there are no scheduled paid breaks), split by time category. |
| **Approved off-standard minutes (OS)** | Time in the off-standard bucket: approved records under an off-standard code (§3.2–3.3). |
| **Net available minutes (NAM)** | A − OS. The operator is accountable for output during this time. |
| **Gross earned minutes (EM_g)** | Σ (pieces on production records × SAM). |
| **Defect deduction (DD)** | Σ (defective qty attributed to the operator × SAM of the operation × k_def). |
| **Net earned minutes (EM_n)** | EM_g − DD. |
| **Incentive minutes (IM)** | Pay quantity: earned minutes adjusted by the proficiency factor, minus deductions (§11). |
| **Time category** | Normal / overtime weekday / rest day / public holiday / night. Comes with attended minutes from attendance. The incentive is **not** split by time category in v1 (§11.5). |
| **ILUO level** | Skill level per operator × skill-evaluated family: **I** learning · **L** can do with supervision · **U** independent at standard · **O** expert, can train others. |
| **Operator tier** | Versatility grade (T1–T4) derived from the operator's ILUO levels across skill-evaluated families (§10.5). |
| **Style changeover** | The first production day of an OB on a line (§7.7). Colour/size variants of the same OB are not changeovers. |
| **Familiarity score (F)** | Share of a new OB's SAM made of library operations the line has run recently (§7.7). |
| **Ramp class (R0–R3)** | Changeover class chosen from F (IE may override). Determines the ramp profile. |
| **Plateau (P)** | The efficiency a line settles at on a style once ramp-up is over. |
| **Ramp profile r(d)** | Efficiency on production day d of a changeover as a **fraction of plateau** (r = 1 means plateau). One profile per ramp class. |
| **Learning curve e(d)** | `e(d) = P × r(d)`: the expected efficiency on day d. Used for targets and costing. |

---

## 3. Time accounting model

### 3.1 Decomposition of attended time

Every attended minute of an operator belongs to exactly one bucket:

```
Attended minutes (A)
├── Approved off-standard (OS)          → excluded from operator accountability
│     coded by reason (§3.2)
└── Net available minutes (NAM = A − OS) → operator accountable for output
      ├── Bundle active time              (diagnostic; family time allocation §10.2)
      └── Gaps: handling, unapproved idle, unscanned time (diagnostic only)
```

### 3.2 Off-standard codes `[P]`

| Code | Reason | Typical scope |
|------|--------|---------------|
| OS-01 | Machine breakdown / mechanic wait | Operator |
| OS-02 | Material wait (cut panels, trims, thread) | Line or operator |
| OS-03 | **Waiting for work** (no WIP at station, line imbalance) | Operator |
| OS-04 | Power / utility outage | Line |
| OS-05 | **Repair / rework** (own or others' defects) | Operator. Created automatically from repair records (§9). |
| OS-06 | Company meeting / organised training | Line or operator |
| OS-07 | Non-standard assignment (samples, special tasks with no SAM) | Operator |
| OS-08 | Other approved | Operator |
| OS-09 | **Style changeover setup** (machine resetting, attachment changes, line re-layout at a changeover) *(new v0.2)* | Line or operator |

### 3.3 Off-standard bucket: channels and rules *(rev. v0.3)*
**One record shape:** operator(s) · start–end (or minutes) · reason code · approver · source channel.

**Three entry channels** feed the same bucket (DEC-17):

| Channel | Typical cases | How it works |
|---------|---------------|--------------|
| 1. Work-order pause | Breakdown or material wait during a bundle | The operator pauses the open bundle with a reason; the line leader approves. The bundle clock stops while paused. |
| 2. Manual entry by the line leader | Waiting for work (OS-03), meetings, changeover setup, line-wide stops, material wait between bundles | The leader enters operator(s), time and reason; entering it counts as approving it. |
| 3. Repair record | Repair/rework (OS-05) | Created automatically from repair records (§9.4). |

**Rules**
1. Off-standard time counts **only when approved**. An unapproved pause or idle time stays in NAM: the operator is accountable for it.
2. **No overlaps:** an operator's off-standard records may not overlap each other or bundle active time. An open bundle is paused when an off-standard period starts. `FLAG-TECH-07`
3. Off-standard time counts only **inside attended time** (§3.4).
4. **Audit:** off-standard minutes are reported by code, line and **approving leader** (§13), so unusual approval patterns are visible.
5. Downstream logic (NAM, lost-time analysis, pay) reads only the bucket; it doesn't depend on the channel.

### 3.4 Time sources and data quality *(new v0.3)*
1. **Attendance is the master clock** (DEC-18). Unpaid lunch is excluded from attended time; there are no scheduled paid breaks.
2. **Server timestamps** are used for scans, pauses and entries, not device clocks.
3. **Pausing bundles:** operators and line leaders pause or finish open bundles at breaks and shift end. There is no automatic pause at those times, because production may legitimately continue into breaks or overtime. An optional **nightly job** `[P]` pauses bundles still open.
4. **Bundle time outside attendance** (e.g. a bundle left open over unpaid lunch): two legitimate options, to be decided during technical design `[OPEN-15]`:
   - **(A) No clipping.** Bundle time is what the scans show. Consequence: a bundle left open over a break inflates that family's time share on mixed-family days and distorts the diagnostics (pace, coverage, station pace). Fallbacks: pausing by operators and leaders, the optional nightly pause job, and the data-quality exceptions in item 5, cleared before payroll close.
   - **(B) Bundle time counts only inside attended time.** Attendance is the clock for bundle time too, so break-spanning bundles correct themselves. Consequence: work done during an unpaid break keeps its pieces but loses its minutes, so that family's efficiency looks slightly higher.
5. **Data-quality exceptions,** cleared by the supervisor before payroll close:
   - scans outside attendance;
   - bundle coverage (M7) above 100%;
   - bundles open at clock-out;
   - unapproved pauses.
6. Bundle time affects pay only through the family time split (§10.2). On a day spent in one family the split is 100% whatever the durations, so residual inaccuracy matters only on mixed-family days.

### 3.5 Idle-gap analysis *(new v0.3)*
- **Station / work-centre idle time** = time within the line's working hours when a station has no active bundle and no off-standard record.
- It is reported per line and station as a planning and balancing metric (unexplained idle time). It is never used for pay.

---

## 4. Metric family

All metrics are calculated per operator, per line and per factory, for any period (day, week, pay period).

| # | Metric | Formula | Purpose |
|---|--------|---------|---------|
| M1 | **Operator on-standard efficiency** | `EM_n ÷ NAM` | Operator performance, skill matrix input |
| M2 | **Incentive efficiency** | `IM ÷ NAM` | Pay basis (§11) |
| M3 | **Overall efficiency** | `EM_g ÷ A` | Line/factory KPI, costing calibration, learning-curve basis |
| M4 | **Line on-standard efficiency** | `Σ EM_g ÷ Σ NAM` (line operators) | Line performance |
| M5 | **Off-standard ratio** | `OS ÷ A`, by code | Lost-time analysis (§13) |
| M6 | **Pace** *(diagnostic)* | `EM_g ÷ bundle active minutes`, by operation | Planned vs actual SAM; never pay |
| M7 | **Bundle coverage** *(diagnostic)* | `bundle active minutes ÷ NAM` | Flow and scanning-discipline monitoring |
| M8 | **Idle-gap ratio** *(diagnostic)* | `station idle minutes ÷ line working minutes` (§3.5) | Unexplained idle time, for balancing and planning |

**Relationship (exact at line level):** `M3 = M4 × (1 − M5)`. Overall losses split into a performance loss (M4) and an off-standard loss (M5).

**Note on gross vs net (C-5).** Line metrics (M3, M4) use **gross** earned minutes; operator metrics (M1, M2) use **net**. Σ operators' EM_n = line EM_g − Σ DD. The difference is intended: the line did produce the pieces (repair time appears as OS-05), while each operator is accountable for their own defects.

---

## 5. Standards and SAM governance

### 5.1 Source and structure
- SAM per operation comes from **timeSSD**, with method description, machine class, attachments and the allowances included.
- Each OB operation keeps its **library operation code** and maps to an **operation family**, a **grade** and a **machine class** (§2).
- Garment SAM = Σ operation SAMs in the OB, kept per department (cutting, sewing, finishing, see §6).

### 5.2 Versioning
- Every SAM has a version with an effective date.
- A production record uses the **SAM version effective on its completion date**.
- Past records are never recalculated, except for an approved retroactive amendment (§5.4).

### 5.3 Amendment triggers
A SAM may be amended **only** for:
1. **A spec or method change** (new attachment, construction change, buyer requirement).
2. **A proven standard error**, demonstrated by IE verification (§5.4).

"The target is not reachable" is **not** a trigger in itself.

### 5.4 Dispute process *(simplified v0.3)*
**What the IE module records:**
1. The dispute: operation, OB, raised by, reason, date.
2. Evidence attachments.
3. The decision: upheld or rejected, with the approver. The IE manager approves; management also approves when pay is affected.
4. If upheld: a new SAM version with its effective date (§5.2). Method or spec changes take effect from the change date. Upheld standard-error disputes take effect from the start of the current pay period `[P]`.

**Practice note (outside the system).** Verification is engineering and management judgement:
- The IE checks the method first; a deviating method is corrected rather than the SAM changed.
- The preferred evidence is a timeSSD re-analysis of the method actually observed, with a time study as support.

### 5.5 Calibration (first months)
- Time-study a sample of operations per family and compare with timeSSD.
- Check that the timeSSD allowances (personal, fatigue, delay) match actual factory conditions.
- Systematic gaps are corrected through the allowance settings, not by editing individual SAMs.

### 5.6 Operation grading rubric *(new v0.2)*
The IE grades each **family** once, using four factors:

| Factor | Question |
|--------|----------|
| Critical | Does a defect here make the garment unsellable or a buyer reject? |
| Position / visibility | Is the seam on the face of the garment (collar, placket, pocket, front) or hidden? |
| Precision and handling | Curves, matching, ease control, multiple plies, slippery or difficult fabric? |
| Machine type | Manual skill machine, or automatic/programmable? |

Guideline `[P]`:
- **A** = critical **and** (high precision **or** face-visible).
- **C** = non-critical, hidden and low precision.
- **B** = everything else.
- Families on **automatic/programmable** machines are graded C and flagged **not skill-evaluated** (DEC-12).

The IE confirms each grade. Grades are reviewed when a family's method changes.

---

## 6. Costing and capacity

*Scope note (2026-10-18): the costing stream (§6.1–6.3, order-level load in §6.4, §6.5, §6.6) is not in v1 and is kept here for later. Daily headcount (§6.4) is in v1. The self-funding check (§11.8) is in v1 and doesn't depend on costing.*

### 6.1 Cost per minute (CPM)
```
CPM_dept = (Direct labour cost_dept + Allocated overhead_dept) ÷ Direct-operator attended minutes_dept
```
- The denominator is **direct-operator attended minutes** (a 100%-efficiency base), not machine minutes.
- Calculated per department `[P]`: cutting, sewing, finishing. v1 may start with sewing only plus a provisional cutting/finishing rate `[OPEN-07]`.
- CPM is expressed **per operator-minute**, so it does not depend on line headcount.

### 6.2 Cut & Make (CM) cost estimate
```
CM cost per garment = Σ_dept ( SAM_dept × CPM_dept ÷ E_plan_dept )
```

### 6.3 Planned efficiency for costing (E_plan)
E_plan is the **order-average** efficiency, including ramp-up, not the plateau efficiency.
1. Determine the style's ramp class (§7.7) and the line's plateau P for the product type, on the **overall-efficiency (M3) basis** (C-3).
2. Learning curve: `e(d) = P × r(d)`.
3. Daily output: `Q(d) = N × T × e(d) ÷ SAM` (N operators, T attended minutes per operator per day).
4. Accumulate days until Σ Q(d) ≥ order quantity Q; that gives the number of days D (last day fractional).
5. `E_plan = Q × SAM ÷ (N × T × D)`

*Example:* SAM 20, N = 40, T = 480, P = 80%, ramp class R2 (r = 0.500 → 0.6875 → 0.875 → 1.00), so e(d) = 40% → 55% → 70% → 80%. Daily output: 384, 528, 672, 768, 768…
- Q = 3,000 pcs: D ≈ 4.8 days → E_plan ≈ 65%.
- Q = 20,000 pcs: E_plan ≈ 77%.
- Small orders cost noticeably more per garment.

### 6.4 Capacity and headcount
```
Load (min)       = Q × SAM ÷ E_plan
Capacity (min)   = Operators × T × Days
Headcount needed = (Daily target × SAM) ÷ (T × e)          e = plateau P at steady state, e(d) on ramp days
```
- E_plan (order average) is used only for order-level load, capacity and costing; daily headcount, station loads and hourly output use the day's expected efficiency e.

### 6.5 Machine requirements
- Machines are calculated **per station after balancing (§7.2)**, not by adding up SAM per machine class: every station needs its own machine.
- Requirement per class = number of stations using that class × (1 + spare `[P 5–10%]`).
- Checked against the available machine register in the Maintenance/CMMS module.

### 6.6 Actual cost
```
Actual labour cost = Attended minutes × CPM
```
Not bundle durations, which exclude waiting and gaps and would understate cost. `FLAG-TECH-01`

---

## 7. Line planning and balancing

### 7.1 Takt and pitch
```
Takt time  = Available minutes per day ÷ Daily target         (pace demand requires)
Pitch time = Garment SAM ÷ Operators on line                  (average workload per operator)
Max allowed station load = Takt × e                            e = plateau P at steady state, e(d) on ramp days
Planned hourly output = Operators × 60 × e ÷ Garment SAM
```

### 7.2 Station design
- Operations are assigned to stations respecting **precedence** and **machine class**.
- A high-SAM operation may be split across k operators (each station load = SAM ÷ k). Low-SAM operations may be combined at one station.
- `Station load = Σ SAM assigned to the station (÷ k if shared)`.
- **Bottleneck** = the station with the maximum load. Line output is limited by the bottleneck.
- The resulting **station layout** (operations per station, operators per station) is recorded and versioned per line; real-time monitoring uses it (§13.2).

### 7.3 Balance metrics
```
Line balance efficiency = Garment SAM ÷ (Operators × Max station load)
Balancing loss %        = 1 − Line balance efficiency
Unused minutes per station = Max station load − Station load
```

### 7.4 Skill-aware allocation
- Bottleneck and Grade A stations go only to operators at level **U or O** in that operation family.
- Placing an operator below U at a station is allowed. The proficiency factor (§11.2) compensates them automatically.
- Allocation follows the skill matrix, not the leader's preference. This keeps pay-relevant assignment objective.

### 7.5 Daily target
```
Daily target = Operators present × T × e(d) ÷ Garment SAM        e(d) = P × r(d)
```
After absenteeism, the target is recalculated with the actual headcount.

### 7.6 WIP and flow
- Buffer per station is tracked from bundle completions and starts.
- WIP cap per buffer `[P e.g. 3 bundles]`. Exceeding it, or a station with no buffer, raises a flag.
- **The line leader controls bundle release** into the line.
- Waiting time (OS-03) per station and per line is the primary **line-balancing KPI**.

### 7.7 Style changeover and learning curves *(rewritten v0.2)*

**7.7.1 Changeover and production run.** A changeover is the first production day of an OB on a line; it starts a **production run** (§2). Colour/size variants of the same OB and SAM amendments without new library operations are not changeovers. Ramp days are counted in **production days of that OB on that line** (day 1 = first day with output).

**7.7.2 Familiarity score.**
```
F = SAM of the new OB's operations whose library operation code this line has run
    within the last [P 90] days  ÷  Garment SAM of the new OB
```

**7.7.3 Ramp class.** The system suggests a class from F; the IE confirms or overrides it with a recorded reason.

| Class | F `[P]` | Meaning | Bootstrap ramp profile r(d) `[P]` |
|-------|---------|---------|-----------------------------------|
| **R0** Minor / repeat | ≥ 90% | Same or nearly the same garment | No ramp (r = 1) |
| **R1** Similar | 60–90% | Same product type, a few new operations | 0.75 → 0.90 → 1.00 |
| **R2** New | < 60% | New construction | 0.500 → 0.6875 → 0.875 → 1.00 (= 40/55/70/80% at an 80% plateau) |
| **R3** Complex | IE only | New product type or difficult fabric | 0.40 → 0.55 → 0.70 → 0.85 → 0.95 → 1.00 |

- A profile ends when r(d) ≥ `[P 0.95]`; from then on r = 1.
- The class mix per line is reported monthly, so drift towards generous classes is visible (§13).

**7.7.4 Plateau.** P is the line's typical plateau for the product type `[P]`, taken from history (median plateau of recent runs). The product type is an IE field on the product category; a style takes it from its category (DEC-24). It is used only for planning and costing (§6.3, §7.5). **The incentive uses r(d) only**, never P.

**7.7.5 Fitting ramp profiles from data.** For each completed changeover:
```
Observed r(d) = On-standard efficiency on day d ÷ Run plateau
Run plateau   = average on-standard efficiency from day [P 6] to the end of the run (minimum [P 5] plateau days)
```
- To isolate the style effect from individual learning, the efficiency used comes **only from production by operators at U/O** in the families concerned.
- Runs that never reach a plateau are excluded.
- Each class's profile = **median observed r(d) per day** across its runs.
- A fitted profile replaces the bootstrap once the class has `[P 10]` runs, and is refitted `[P quarterly]`.

**7.7.6 Basis (C-3).** r(d) is a ratio, so it is the same on any efficiency basis. For planning and costing, e(d) uses the **overall (M3) plateau**. The incentive applies r(d) to the threshold (§11.3).

**7.7.7 Future refinement `[OPEN-11]`.** Once enough data exists, the bands can be replaced by a continuous model, e.g. day-1 level = 1 − α × (1 − F), if day-1 levels prove to follow F closely.

---

## 8. Shop-floor execution rules

1. **MO splitting:** by variant (size/colour), then by shade lot, then by **bundle size** `[P 10–30 pcs]`. One bundle = one MO.
2. **One operator per operation per bundle.** The production record gets the full bundle quantity.
3. **Mid-bundle reassignment** (absence, shift end): a supervisor deletes the first operator's record, and the whole bundle is credited to the operator who finishes it. Supervisor-only action, written to an audit log.
4. **Scans:** start and finish scans per bundle operation. Timestamps are used for diagnostics (pace, flow, coverage) and for family time allocation (§10.2), never for the incentive denominator.
5. **Completion date** of a record = the date of the finish timestamp `[P simplification]`. The finish time also gives the record's time category, should it ever be needed (§11.5). `FLAG-TECH-04`
6. Off-standard entries follow §3.3.

---

## 9. Quality: defect → repair → re-inspection

### 9.1 Data received from the Quality module
For each defect record:
- bundle/MO
- **operation** (chosen from that bundle's operations)
- defect code
- defective quantity
- detection point (inline / end of line / final audit)
- **responsibility category** (operator / material / cutting / machine / unknown)
- detection date
- inspector

### 9.2 Attribution
- If responsibility = *operator*, the defect goes to the operator on the production record for that bundle × operation.
- Defects that cannot be traced to an operation (e.g. some final-audit findings) are attributed to the **line**, with no operator deduction.

### 9.3 Defect deduction
```
DD = Defective qty × SAM_operation × k_def        k_def [P] default 1.0
```
- Booked against the responsible operator on the **detection date**. Closed periods are not reopened.
- Cumulative defective quantity per bundle × operation cannot exceed the bundle quantity. A defect record that would exceed it is **rejected with an error** and returned to QC for correction; nothing of it is booked until corrected. *(Rev. v0.6)* `FLAG-TECH-13`
- Applies to all families, including those not skill-evaluated.

### 9.4 Repair
- Repair is recorded as a **repair record**: repairer, bundle, operation, quantity, start and end.
- Repair time is automatically **OS-05** for the repairer, whoever they are. Repair earns nothing and costs nothing.
- The repaired pieces do **not** restore the deduction (no "earn-back" in v1).

### 9.5 Re-inspection
- Pass closes the defect.
- A failed repair returns to repair. No further deduction for the original operator and no deduction for the repairer. Repeat failures are reported as a repairer quality diagnostic (§13.1). *(Settled v0.5)*

### 9.6 Quality metrics produced by IE
```
Operator defect rate (family f, window) = Attributed defective qty_f ÷ Pieces produced_f
```
Also reported: line defect rate, defects by operation and code, and repair minutes (OS-05) by line.

---

## 10. Skill matrix

### 10.1 Unit and scope
- Operator × **skill-evaluated** operation family, evaluated every evaluation period `[P monthly]` over a rolling window `[P 60 days]`.
- **Not-skill-evaluated families** (DEC-12):
  - still count in earned minutes, efficiency, incentive and defect deductions;
  - get **no ILUO level** and **no proficiency factor**;
  - **don't count towards tiers**, and neither do their machine classes;
  - still count in the family time allocation (§10.2), so other families' efficiency isn't inflated.

### 10.2 Family efficiency
NAM is allocated to families in proportion to bundle active time (DEC-02):
```
share_f        = Bundle active minutes_f ÷ Σ Bundle active minutes
NAM_f          = NAM × share_f
Efficiency_f   = EM_n,f ÷ NAM_f
```
- The weighted average of family efficiencies equals overall on-standard efficiency (M1). Bundle durations only redistribute time between families; they never change the total.
- `FLAG-TECH-03`

### 10.3 Minimum volume
A family level is evaluated only if EM_g,f in the window ≥ `[P 600 min]`. Otherwise the previous level is kept.

### 10.4 ILUO criteria `[P]`

| Level | Criteria (rolling window) |
|-------|---------------------------|
| **I** | Default for a new family, or below the L criteria |
| **L** | Efficiency_f ≥ 55% and defect rate_f ≤ 3.0% |
| **U** | Efficiency_f ≥ 80% and defect rate_f ≤ 1.5% |
| **O** | U criteria met in 2 consecutive evaluations, and Efficiency_f ≥ 95% in the current one. Purely data-based; no separate pay effect (DEC-22) |

- **Upgrades** take effect at the evaluation that meets the higher criteria (subject to minimum volume, §10.3). *(Rev. v0.6)*
- **Downgrade grace:** one evaluation below the criteria raises a warning; a second consecutive one downgrades by one level `[P]`. Falling below on defect rate alone is treated the same way as falling below on efficiency.
- **Dormancy:** no volume in a family for `[P 180 days]` downgrades it by one level (minimum L, if the operator previously reached U).
- **Quality counts twice by design (C-4).** Defect deductions reduce Efficiency_f (the output cost of defects), and the defect rate separately gates the level, so a fast but sloppy operator cannot reach U.

### 10.5 Operator tier (versatility) `[P]`

| Tier | Criteria (skill-evaluated families at level ≥ U) |
|------|--------------------------------------------------|
| T1 | Fewer than 2 families |
| T2 | ≥ 2 families |
| T3 | ≥ 4 families, incl. ≥ 1 Grade A, across ≥ 2 machine classes |
| T4 | ≥ 6 families, incl. ≥ 2 Grade A, across ≥ 3 machine classes |

- Machine classes are counted only from skill-evaluated families, so automatic machines never add diversity.
- The tier is fixed for the whole following pay period.

### 10.6 Uses
1. Line allocation (§7.4) and training planning.
2. Tier multiplier (§11.4).
3. Skill metrics reported to payroll for a possible **special allowance** to highly skilled operators (DEC-06). The allowance itself is decided by payroll/HR. This is also how rare floater cases are compensated (DEC-15).

---

## 11. Incentive metrics (IE side)

IE calculates incentive **quantities**; payroll converts them to money (DEC-08).

### 11.0 Scope *(new v0.2)*
- Applies to all SAM-measured work, whoever performs it (DEC-14).
- Roles without SAM output are outside the IE incentive.
- **Cutting** is outside bundle capture and the incentive. It is tracked through its own MOs (progress per cut order/batch). *(v0.3)*

### 11.1 Aggregation period
- **Monthly** (pay period). *(Confirmed v0.3)*
- Daily values (pieces, earned minutes, efficiency, progress against the monthly threshold, defect deductions) are **provisional** and supplied to the MES interface for operator feedback (§13.2). Displaying them is outside IE scope.

### 11.2 Proficiency factor (leeway)
```
IM = Σ_records ( Pieces × SAM × PF ) − DD
```

| Operator level in the family | PF `[P]` |
|---|---|
| I | 1.25 |
| L | 1.10 |
| U / O | 1.00 |
| Not-skill-evaluated family | 1.00 |

- **Cap (rev. v0.5):** PF applies only to the first **PF_cap** gross earned minutes the operator produces in that family, counted cumulatively across all periods and levels (DEC-23). PF_cap is set **per grade** `[P A 2,400 · B 2,400 · C 2,400 EM]`.
- It ends at whichever comes first: reaching U, or using up PF_cap.
- The level used is the one fixed at the start of the pay period; an operator who meets the U criteria mid-period keeps PF until the period ends (within the cap).
- PF_cap does **not reset** after dormancy.
- **Record crossing the cap (interim rule):** the record is split; the part within the remaining cap gets PF, the rest counts at 1.00. Records count in order of completion. The leeway mechanism and its basis are to be reconsidered in technical design for simplicity and reliable implementation `FLAG-TECH-14`.

### 11.3 Threshold and excess *(rev. v0.2: ramp-adjusted)*
```
Daily threshold factor    θ_day = max( θ_floor ,  θ × [ Σ_k s_k × r_k(d_k)  +  (1 − Σ_k s_k) ] )
Threshold minutes         TM    = Σ_days ( θ_day × NAM_day )
Incentive efficiency      E_inc = IM ÷ NAM
Excess incentive minutes  X     = max(0, IM − TM)
```
- θ `[P 0.70]` is the normal threshold factor. It must be reachable by a typical U-level operator at plateau, so pay stays predictable.
- k = each style the operator worked on that day that is in ramp-up on its line. d_k = its ramp day; r_k(d_k) = its ramp profile value (§7.7).
- s_k = the operator's share of that day's EM_g on style k (quantity-based).
- θ_floor `[P 0.30]` stops the bar from dropping too far on a complex style's first day.
- On days with no ramping style, θ_day = θ, so TM = θ × NAM as in v0.1.

*Example (R2 profile, θ = 0.70):*
- A full day on the new style gives θ_day = 35.0% on day 1, 48.1% on day 2, 61.3% on day 3, then 70%.
- Half the day on the new style on day 1 gives θ_day = 0.70 × (0.5 × 0.50 + 0.5) = 52.5%.

**Stacking with PF.** PF corrects an *individual's* unfamiliarity with a family (it raises credited minutes). The ramp profile corrects a *style's* newness for everyone (it lowers the bar). Each is fitted on data that excludes the other's cause (§7.7.5, §14), so their effects multiply without double counting.

### 11.4 Tier multiplier
```
Payable incentive units  U = X × M_tier
```

| Tier | M_tier `[P]` |
|---|---|
| T1 | 1.00 |
| T2 | 1.05 |
| T3 | 1.10 |
| T4 | 1.20 |

### 11.5 Time categories *(rev. v0.6)*
The incentive is **not split by time category** in v1: IE reports U as one total per operator per period. Statutory overtime, rest-day, holiday and night rules belong to payroll/HR (DEC-08).

*Note (not in v1):* if HR/payroll determine that statutory premiums apply to incentive earned in overtime, IE can supply earned minutes by time category: every production record carries its finish date and time (§8 rule 5).

### 11.6 Eligibility flags `[P]`
- Minimum attendance in the period (e.g. ≥ 80% of scheduled days).
- Flags are reported to payroll; payroll decides the consequences.

### 11.7 Worked example (one operator, one month, no ramp days)

| Item | Value |
|------|-------|
| Attended A | 26 days × 480 = **12,480** min |
| Approved OS | waiting 300 + breakdown 180 + repair 120 = **600** min |
| NAM | **11,880** min |
| Family X (level U), SAM 0.80 | 9,000 pcs → 7,200 min |
| Family Y (level L, within PF_cap), SAM 1.20 | 1,500 pcs → 1,800 min |
| EM_g | **9,000** min |
| Defects attributed (family X) | 50 pcs × 0.80 → DD = **40** min |
| EM_n | **8,960** min |
| M1 on-standard efficiency | 8,960 ÷ 11,880 = **75.4%** |
| M3 overall efficiency | 9,000 ÷ 12,480 = **72.1%** |
| IM | 7,200 + 1,800 × 1.10 − 40 = **9,140** min |
| E_inc | 9,140 ÷ 11,880 = **76.9%** |
| TM (θ = 0.70, no ramp days) | **8,316** min |
| X | **824** min |
| Tier T2 → U | 824 × 1.05 = **865.2** units → to payroll |

*(The rationale document works through ramp-day, learner and floater cases in full.)*

### 11.8 Self-funding check (IE report)
```
Labour cost per earned minute = (Base wages + Incentive paid + Allowances) ÷ Σ EM_g
```
- Tracked by month and plotted against M3.
- It should stay flat or fall as efficiency rises. If it doesn't, θ, the rate or the multipliers need review.

---

## 12. Interfaces (business level)

| Direction | Partner | Data |
|-----------|---------|------|
| **IE → Payroll** (per operator per period) | Payroll | A; OS by code; NAM; EM_g; DD; EM_n; IM; M1; E_inc; X; U (one total, §11.5); tier and M_tier; family levels and special-allowance metrics; eligibility flags |
| IE → Planning | MRP / planning | SAM, garment SAM, ramp class, r(d), plateau, learning curve e(d), capacity load, daily targets |
| IE → Sales / costing | Sales | CM cost estimate, E_plan |
| IE → Maintenance | CMMS | Machine requirements per class; OS-01 minutes by machine (where known); **breakdown calls** that open maintenance requests (RT-3) |
| Quality → IE | Quality | Defect, repair and re-inspection records (§9.1) |
| HR → IE | Attendance | Attended minutes, shifts, time categories |
| IE → MES interface | Shop floor | Operator and line metrics for display, computed with the same definitions (§13.2) |
| timeSSD → IE | PMTS | Operations, library operation codes, methods, SAM, machine classes, attachments |
| Product master → IE | Product | Product type on the product category (for plateau, §7.7.4) |

---

## 13. Analytics

### 13.1 Period analytics

1. **Planned vs actual SAM:** pace (M6) per operation vs SAM. This flags inaccurate standards, method deviations and fabric-handling issues, and feeds §5.4.
2. **Line efficiency progression:** daily efficiency vs the learning curve e(d), per style/MO.
3. **Lost-time analysis:** OS by code, line and station. Waiting (OS-03) highlights balancing problems; OS-01 and OS-02 supply and maintenance problems; OS-09 changeover setup cost.
4. **Balancing:** planned balance efficiency vs actual waiting; WIP flags.
5. **Quality:** defects by operation family, operator, code and detection point; repair minutes.
6. **Skill coverage:** per line, the number of U/O operators per critical family.
7. **Incentive health:** distribution of E_inc, the share of operators above θ, the self-funding check (§11.8).
8. **Changeover analysis** *(new v0.2)*: observed r(d) per changeover vs its class profile; class mix and IE overrides per line; refit status per class.
9. **Off-standard audit** *(new v0.3)*: off-standard minutes by code, channel and approving leader; data-quality exception volumes (§3.4).
10. **Idle-gap analysis** *(new v0.3)*: unexplained station and work-centre idle time (§3.5).

### 13.2 Real-time monitoring *(rev. v0.4)*

**Principles** (DEC-19): the same definitions as the period metrics, computed continuously over a rolling window. Diagnostic only: pay still closes monthly, and the **hourly** figures are the official record. Refresh mechanism, displays and the MES feed format belong to the technical design (`FLAG-TECH-11`).

**Definitions**
```
Rolling window              W  [P 60 min]
Hourly target               = Operators present × 60 × e(d) ÷ Garment SAM
Line output (W)             = pieces completed at the last operation of the OB within W
Station planned output (W)  = Operators at station × W × e(d) ÷ SAM at the station (Σ SAM if operations are combined)
Station throughput ratio    = Completions at the station within W ÷ Station planned output (W)
Station input buffer        = bundles finished at the preceding operation(s) and not yet started at this station
Starved time (W)            = minutes within W with an empty input buffer and no active bundle
```
- **Live bottleneck** = the station with the **lowest throughput ratio among stations not starved** for more than `[P 10%]` of W. Stations downstream of a bottleneck also look slow, but they are starved: they are victims, not the cause.
- **Station layout:** each line's current assignment of operations to stations, with operators per station, comes from balancing (§7.2). It is recorded and versioned, because real-time WIP and bottleneck detection depend on it.

**v1 features** (DEC-20)

| # | Feature | Content |
|---|---------|---------|
| RT-1 | **Hourly production board** | Per line: output vs hourly target (current hour and cumulative today), rolling efficiency, headcount present, off-standard minutes today. |
| RT-2 | **Exception alerts** `[P]` | Line output < 85% of target within W; off-standard pending approval > 30 min; bundle open > 3 × SAM × quantity; station starved > 15 min; input buffer above the WIP cap. |
| RT-3 | **Breakdown call** | A work-order pause with reason OS-01 notifies the mechanic and opens a maintenance request in the CMMS. The operator resumes the bundle when the machine is fixed. |
| RT-4 | **Operator figures feed** | Today's provisional figures (pieces, earned minutes, efficiency, progress against the monthly threshold, defect deductions) supplied to the MES interface. |
| RT-5 | **Station WIP flags** | Input buffer per station; starved and overloaded flags. |
| RT-6 | **Live bottleneck** | As defined above. |
| RT-7 | **Station pace** | Live pace vs SAM per station. Diagnostic; uses bundle durations. |

**Noted for later (not v1):** re-balancing suggestions from the skill matrix. High value, but they need optimisation logic and mature skill data.

---

## 14. Calibration and shadow mode *(new v0.2, rev. 2026-10-18)*

### 14.1 Parameter groups (DEC-21)

| Group | Examples | Owner | When set |
|-------|----------|-------|----------|
| **A. Pay policy** | θ, tier multipliers, PF values, PF_cap per grade, θ_floor, k_def, eligibility (minimum attendance) | Management | Placeholders during shadow mode; finalised at its end from shadow data |
| **B. Calibrated from data** | ILUO thresholds, minimum volume, windows, tier criteria, plateaus per product type, F bands, ramp profiles | IE | During shadow mode; ramp profiles keep refitting after go-live |
| **C. Operational settings** | Bundle size, WIP caps, alert thresholds, real-time window W, nightly pause job, machine spare %, run-break days, familiarity look-back | IE / production | Any reasonable start value; tuned in use. No direct pay effect |
| **D. Master data** | Operation families, grades, skill-evaluated flags, off-standard codes, CPM inputs, product types | IE / finance | Before shadow mode starts |

### 14.2 Shadow mode
The full system runs (capture, metrics, skill levels, tiers, ramp-ups, incentive units), but the **incentive is not paid out**. Pay stays on the existing scheme. Shadow mode also:
- **builds the skill history,** so operators start live pay at their real levels rather than all at level I;
- **produces calibration data** for groups A and B;
- **lets discipline settle** (scanning, pausing, off-standard approvals) before errors cost money;
- **shows management the projected incentive cost** (self-funding check) before committing.

Whether operators see their "would-be" incentive during shadow mode is part of `[OPEN-12]`.

### 14.3 Calibration steps

1. **Shadow period** `[P 2–3 months]`: skill levels, tiers, PF and ramp-adjusted thresholds are calculated and reported but **don't affect pay**. Pay during this period follows the base rules (θ × NAM, PF = 1, M_tier = 1) or the factory's existing scheme `[OPEN-12]`.
2. **What is tuned:**
   - ILUO thresholds and minimum volume: check the level distribution with the IE team and line leaders.
   - Tier criteria.
   - PF values and PF_cap per grade: from operators' first production in new families on **established styles only** (ramp days excluded); the earned minutes learners need to reach U, per grade, set the caps.
   - Ramp profiles: from changeovers, using **U/O operators only** (§7.7.5).
   - θ: reachability check.
3. **Separation rule:** PF is tuned excluding ramp days, and ramp profiles excluding learners, so the two leeways can stack (§11.3).
4. **Acceptance checks before switch-on** `[OPEN-12]`:
   - Incentive efficiency on ramp days should be comparable to normal days.
   - The share of U-level operators with X > 0 in a normal month should be in a sensible range.
   - The self-funding check should be healthy.
5. Before enough changeovers exist per class, the bootstrap profiles (§7.7.3) apply.

---

## 15. Open items and technical flags

### Open business items
| ID | Item |
|----|------|
| OPEN-01 | Tune `[P]` values from shadow-mode data (groups A and B, §14.1). Starting values = current placeholders. |
| OPEN-02 | *Closed in v0.3:* one off-standard bucket with three channels (DEC-17, §3.3). |
| OPEN-03 | *Closed in v0.3:* monthly. |
| OPEN-04 | *Closed in v0.5:* purely data-based, no trainer designation, no separate pay effect (DEC-22). |
| OPEN-05 | *Closed in v0.5:* no reset after dormancy; level lag accepted; PF_cap per grade (DEC-23). |
| OPEN-06 | *Closed in v0.5:* no deduction for anyone in v1; repeat failures reported as a repairer diagnostic (§9.5). |
| OPEN-07 | Standards and CPM for cutting and finishing. |
| OPEN-08 | *Removed in v0.3:* statutory classification of pay is outside IE scope (payroll/HR, DEC-08). |
| OPEN-09 | *Closed in v0.2:* floater paradox, handled by payroll exception (DEC-15). |
| OPEN-10 | Line/group share (hybrid) as a future option if WIP or quality problems persist. |
| OPEN-11 | Continuous familiarity model (§7.7.7) to replace the bands, once data supports it. |
| OPEN-12 | Shadow-mode design: duration, pay basis during the shadow period, acceptance criteria for switch-on. |
| OPEN-13 | *Closed in v0.5:* product type is an IE field on the product category (DEC-24). |
| OPEN-14 | *Closed in v0.4 (business side):* definitions and v1 features settled (DEC-20, §13.2). Technical side moved to FLAG-TECH-11. |
| OPEN-15 | Bundle time outside attendance: option (A) no clipping, with the existing fallbacks, or option (B) bundle time counted only inside attended time (§3.4 item 4). Both are legitimate; **decide during technical design**. |

### Technical flags
| ID | Flag |
|----|------|
| FLAG-TECH-01 | **Odoo work centre study.** Work centres assume a fixed, discrete capacity and cost work orders as *duration × hourly rate*. IE costs *attended operator-minutes × CPM*, with variable line headcount. These are different definitions. The work centre is a core object for IE (likely one per sewing line, plus cutting and finishing) and needs a dedicated study. Actual cost must use attended minutes, not work order durations. |
| FLAG-TECH-02 | **MO proliferation and grouping.** One MO per bundle. Check whether Odoo MOs can be tied to a source document (sales order / demand forecast); otherwise define a common grouping key. IE needs at least three grouping keys: source document, OB/style, and **production run** (OB × line), because many metrics are order- or run-based, not bundle-based. A **cut order / lay** level may sit between style order and bundles. |
| FLAG-TECH-03 | Family time allocation (§10.2) relies on bundle durations; needs consistent start/finish scans. |
| FLAG-TECH-04 | Bundles spanning two time categories or two days are attributed by the finish timestamp. |
| FLAG-TECH-05 | Production records must reference the SAM version effective on the completion date. |
| FLAG-TECH-06 | Data model approach: dedicated IE models linked to Odoo work centres, employees and products, vs extending MRP routing (formerly D2 in the function map). |
| FLAG-TECH-07 | **Operator state awareness.** An Odoo work order only records who did the work on an operation. It has no notion of the operator's *current state*, which the bundle logic assumes. The MES layer must know at least each operator's current bundle and its status (active / paused / none) and whether they are in an off-standard period, so it can enforce rules such as: no starting or continuing a bundle while busy with or paused on another; no bundle activity during off-standard time (§3.3 rule 3); handling of open bundles at shift end or reassignment (§8.3). |
| FLAG-TECH-08 | **Library operation codes** must be kept on every OB operation (from timeSSD / the operation library), and production history must be queryable per line × library code, to compute familiarity (§7.7.2). *(New v0.2)* |
| FLAG-TECH-09 | **Ramp calendar:** per line × OB, the ramp class, the ramp day count in production days, and per operator-day the EM share by ramping style (s_k), for §11.3. *(New v0.2)* |
| FLAG-TECH-10 | **Off-standard bucket:** one record model fed by work-order pauses, a leader entry form and repair records; overlap checks; optional nightly pause job for bundles left open; data-quality exception queue (§3.3–3.4). *(New v0.3)* |
| FLAG-TECH-11 | **Real-time implementation:** refresh mechanism (event-driven for WIP and alerts; periodic for efficiency figures), line boards and displays, notification channel for alerts and breakdown calls, CMMS request creation, MES feed format, recorded station layout per line. *(New v0.4)* |
| FLAG-TECH-12 | **Parameter configuration:** every `[P]` value editable by its owner (§14.1), stored with an effective date; calculations pick the values valid for the period; change history kept. *(New 2026-10-18)* |
| FLAG-TECH-13 | **Defect quantity validation:** a defect record that would take cumulative defects for a bundle × operation above the bundle quantity must be rejected with an error (§9.3). Where and how the check runs (QC entry, interface, nightly validation) is decided in technical design. *(New v0.6)* |
| FLAG-TECH-14 | **Leeway mechanism (PF):** the interim rule splits a record that crosses the cap (§11.2). Technical design reconsiders the mechanism and its basis (earned minutes, quantity, or another rule) for simplicity and reliable implementation. A **time-based** cap carries a known problem: in v0.1 an hours cap let bundle scan durations move the bonus (rationale §18, C-1), which is why DEC-07 uses earned minutes. *(New v0.6)* |

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-12 | First draft, written fresh from the discussion of 2026-10-12. |
| 0.1 | 2026-10-13 | Added FLAG-TECH-07 (operator state awareness). |
| 0.2 | 2026-10-16 | Coherence review applied (C-1 to C-5). DEC-02 and DEC-07 revised (durations only for family allocation; PF cap in earned minutes). New DEC-11 to DEC-16: grading rubric (§5.6), not-skill-evaluated families, style changeover with familiarity score, ramp classes, fitted ramp profiles and ramp-adjusted threshold (§7.7, §11.3), incentive scope, floater handled by payroll, shadow mode (§14). OS-09 changeover setup code. Learning curve redefined as plateau × ramp profile. Open items and flags updated (OPEN-09 closed; OPEN-11 to 13, FLAG-TECH-08 and 09 added). Open items moved to §15. |
| 0.3 | 2026-10-17 | Off-standard as one bucket with three channels (DEC-17, §3.3); time sources and data quality with attendance as master clock (DEC-18, §3.4); idle-gap analysis (§3.5, M8); production run defined; dispute process simplified to system records (§5.4); cutting scope note; monthly aggregation confirmed; real-time monitoring principles (DEC-19, §13.2); analytics split into period (§13.1) and real-time (§13.2). OPEN-02, 03 closed; OPEN-08 removed; OPEN-14 added; FLAG-TECH-01, 02 extended; FLAG-TECH-10 added. |
| 0.3 rev. | 2026-10-17 | Correction: no automatic pause at lunch or shift end (operators and leaders pause; optional nightly job); clipping bundle time to attendance is not decided (OPEN-15). DEC-18, §3.4 and FLAG-TECH-10 corrected. |
| 0.3 rev. 2 | 2026-10-17 | Review fix: daily headcount, max station load and hourly output use the day's expected efficiency e (plateau or e(d)), not E_plan; E_plan is for order-level load, capacity and costing only (§6.4, §7.1). |
| 0.4 | 2026-10-17 | Real-time monitoring defined (§13.2): rolling window, hourly target, station planned output and throughput ratio, input buffer, starved time, live bottleneck excluding starved stations, station layout recorded from balancing (§7.2); v1 features RT-1 to RT-7 (DEC-20); re-balancing suggestions noted for later. Breakdown call to the CMMS added to interfaces. OPEN-14 closed (business side); FLAG-TECH-11 added. |
| 0.4 rev. | 2026-10-18 | Baseline status. DEC-21: parameters configurable and versioned with effective dates; current placeholders are the shadow-mode starting values. §14 restructured: parameter groups and owners (§14.1), shadow mode purpose (§14.2). OPEN-01 reworded; FLAG-TECH-12 added. |
| 0.4 rev. 2 | 2026-10-18 | Scope note in §6: costing stream not in v1 (function map v0.6). |
| 0.5 | 2026-10-18 | Open items settled: DEC-22 level O data-based with no separate pay effect (OPEN-04); DEC-23 PF_cap cumulative, no reset, level lag accepted, cap per grade (OPEN-05); DEC-24 product type on the product category (OPEN-13); failed repairs (OPEN-06) settled in §9.5. OPEN-15 restated as two options (A) and (B), decided during technical design (§3.4). Companion documents updated (rationale v0.5, function map v0.7, acceptance test cases v0.2). |
| 0.6 | 2026-10-19 | Test-case assumptions settled: precision convention; R2 day 2 = 0.6875 (§7.7.3, §6.3); upgrades immediate, downgrade grace also for defect rate (§10.4); defect records exceeding the bundle rejected with an error (§9.3, FLAG-TECH-13); interim split rule for a record crossing PF_cap (§11.2, FLAG-TECH-14). Time-category split of the incentive removed; U reported as one total; note kept for possible statutory needs (§11.5, §2, §8, §12). |
