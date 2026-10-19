# IE Module — Fit-Gap against Odoo CE 18

**Version:** v0.1 (draft) · 2026-10-19
**Roadmap step:** 3 (fit-gap against Odoo CE 18)
**Based on:** `IE_Business_Logic_Spec_v0.6.md`, `IE_Framework_Rationale_v0.6.md`, `IE_Module_Function_Map.md` (v0.8), `IE_Acceptance_Test_Cases_v0.3.md`. Checked against the Odoo CE 18 core the instance runs (`odoo/`, at the image's pinned commit) and the mounted OCA repositories (`oca/`), read 2026-10-19.
**Purpose:** For every v1 function, this records:
- what standard Odoo, OCA or our existing modules already provide;
- what has to be built;
- which Odoo features IE must deliberately leave alone.

It also records the decisions taken during the fit-gap and plans the step 5 prototype. The business rules stay in the spec. Where this document implies a change to the spec, rationale, function map or roadmap, §12 lists it as a proposal for the document workflow.

**Conventions**
- Source references are `path:line`, relative to `Odoo-Build/`. After its first full mention in a section, a file may be named by a shorter path such as `mrp_workorder.py`.
- This document contains no instance data, because the repository is public. Every worked number comes from the rationale's fictional running example.
- Verdict codes:

| Code | Meaning |
|------|---------|
| **Core** | Standard Odoo CE 18, used as it is or configured |
| **OCA** | An OCA module, either installed or available in `oca/` |
| **Own** | One of our existing modules (the QMS or PMS suite) |
| **Ext** | An additive extension of a core or OCA model: new fields, wrappers, views |
| **New** | A new IE model or new IE logic |
| **Bypass** | A core feature IE deliberately does not use |
| **MES** | Belongs to the MES suite, not IE |

- Status labels: **Agreed** (confirmed by Peter, with date) · **Proposed** (recommended here, not yet confirmed) · **Open** (listed in §13).

---

## 0. Decisions and findings

| ID | Decision or finding | Status |
|----|---------------------|--------|
| FG-01 | **Two layers.** Use Odoo MRP's *record layer*: MOs, work orders, time logs, operation dependencies, BoM operations, stock and valuation. Bypass its *resource engine*: work-centre scheduling, capacity-based durations, work-centre load and hourly work-centre cost. IE holds the line layer. (§2) | Agreed 2026-10-19 |
| FG-02 | **Work order = production record. MO = physical bundle.** An MO is one size × colour × shade, split to whatever bundle size planning chooses. The system sets no maximum. Volume and concurrency are proven in step 5. (§4) | Agreed as the working premise; step 5 proves it |
| FG-03 | **Configuration rules for IE lines:** capacity 1, no hourly cost, no "Plan" on bundle MOs, and headcount kept in IE rather than in the work centre. (§2.3) | Proposed |
| FG-04 | **Operator identity.** Each work order gets a credited operator, and each time log gets the employee who scanned. Operators remain employees without user accounts. (§4.3) | Proposed |
| FG-05 | **The off-standard bucket is an IE model**, never Odoo's loss rows. One open loss row blocks every work order on the line. (§4.5) | Proposed |
| FG-06 | **Costing option C.** Finished goods carry a standard conversion cost through the MO's *Extra Unit Cost* = garment SAM × rate. Lines carry no hourly cost, so scanned time never reaches valuation. (§7) | Agreed 2026-10-19 |
| FG-07 | **The rate is the measured conversion cost per earned minute** over a trailing window, versioned with an effective date. Finance owns it and IE informs it. (§7.4–7.5) | Proposed; the accountant confirms |
| FG-08 | **Defects are an IE record** linked to the work order and coded with `qms_catalog` defect codes. The dependency on `qms_catalog` is accepted. (§8.1) | Agreed 2026-10-19 |
| FG-09 | **Payroll pulls** IE's period records through its salary rules. IE has no dependency on payroll. (§6.3) | Agreed 2026-10-19 |
| FG-10 | **Scanning belongs to MES.** The capture data (FG-04, pause reasons, operator-state checks) sits in one module that both MES and IE depend on. (§10) | Scanning in MES: Agreed 2026-10-19. Shared module: Proposed |
| FG-11 | **Parameters** (DEC-21) are stored with OCA `base_time_parameter`. (§6.2) | Proposed |
| FG-12 | **Finance enters one period cost pool.** It feeds both the valuation rate and the self-funding check, so IE needs no payroll dependency. (§7.6) | Proposed |
| FG-13 | **Breakdown call (RT-3):** a pause with reason OS-01 opens a core maintenance request, through a bridge module. (§8.2) | Proposed |
| FG-14 | **Planning visuals** use the core MO calendar at lot level. A production-run view comes later. (§5.2) | Proposed |
| FG-15 | **The prototype is a disposable run** on this instance, a test copy restored from production. Take a backup before it and restore afterwards. (§11) | Agreed 2026-10-19 |

---

## 1. Context

- Odoo CE has no Quality or Payroll app of its own. Both are present on this instance: the QMS suite runs on `quality_control_oca` and `mgmtsystem`, and OCA `payroll` is in use. Its salary rules already read data from other modules (attendance, leave, employee skills).
- Operators are `hr.employee` records without user accounts. The sewing lines already exist as work centres.
- Attendance arrives as imported `hr.attendance` records.
- The existing manufacturing records on the instance are tests. They do not show real production volume or shape.

---

## 2. The governing finding: Odoo MRP has two layers

### 2.1 What fits and what does not

| Layer | What it assumes | Fit for a garment line |
|-------|-----------------|------------------------|
| **Records**: MO, work orders, time logs, operation dependencies, BoM operations, stock and valuation | One document per job, one record per operation, who did it and when | **Fits.** The gaps are additive (§4). |
| **Resource engine**: work-centre scheduling, capacity-based durations, work-centre load, hourly work-centre cost | A work centre is *one* resource that does one job at a time | **Does not fit.** A line is a pool of N operators running many jobs in parallel, and N changes every day. |

Evidence from the code:
- **Capacity** is the number of pieces processed in parallel *inside one work order*: "the capacity is 5 and you need to produce 10 units, then the operation time … will be multiplied by two" (`odoo/addons/mrp/models/mrp_workcenter.py:36-38`). Its only use is to divide the quantity into cycles when computing expected duration (`odoo/addons/mrp/models/mrp_workorder.py:794-796`, `odoo/addons/mrp/models/mrp_routing.py:83-93, 188-189`).
- **The planner** places each work order in an interval "disjoint with all other workorders planned on this workcenter" (`mrp_workcenter.py:339-341`). So whatever its capacity, a work centre does one job at a time.
- **Each started work order** books a `resource.calendar.leaves` record on the work centre for its expected duration (`mrp_workorder.py:644-655`). That booking is how the planner sees the work centre as busy.
- **Hourly work-centre cost** multiplies logged time by `costs_hour` and adds it to the value of the finished goods (§7.1).

Read with capacity = headcount, a bundle work order's expected time becomes what the job would take if every operator on the line sewed that one bundle operation together. Read with capacity = 1, it becomes the single operator's standard time, quantity × SAM. That equals the work order's earned minutes, which is the meaning IE needs.

### 2.2 Bypass, not enhance

| Alternative | Verdict |
|-------------|---------|
| **Bypass**: use the record layer, configure the engine out of the way (§2.3), and keep the line layer in IE (headcount, stations, targets, efficiency, line planning) | **Chosen** (FG-01). No core method needs overriding for the engine. |
| **Enhance**: rework the engine (a parallel-aware planner, a line as N resources, new duration semantics) | Rejected. It means deep overrides of core scheduling, costly at every upgrade and against the project's additive rule. It also gains little, because IE plans with targets, learning curves and ramp-up, which Odoo's scheduler cannot express. |
| **A work centre per station**, where "one job at a time" would hold | Rejected. Layouts change at every changeover, so the work centres (master data with calendars and costs) would keep churning. |
| **Fallback**: MO = shade lot, with bundles as IE records under the lot's work orders | Kept only in case step 5 fails. It means more own code and less reuse of the record layer. |

Every gap found during development should land in one of two buckets: "record layer, additive gap" or "engine, bypassed and replaced by IE". If a gap fits neither, the premise needs revisiting.

### 2.3 Configuration rules for IE lines (FG-03)

| Rule | Setting | Why |
|------|---------|-----|
| R1 | Work-centre capacity = 1 (and no per-product capacity) | Expected duration then equals quantity × SAM, one operator's standard time. Capacity affects nothing else (§2.1). |
| R2 | `costs_hour` = 0 | Scanned time must never reach the value of finished goods (§7). A wrong value silently mis-values stock, so the work centre shows a warning when an IE line carries an hourly cost. |
| R3 | No "Plan" on bundle MOs | The planner would lay a day of parallel work end to end. One example: 55 bundles of a 10-minute garment is 11,000 minutes, which plots as about 23 working days. |
| R4 | Headcount from IE | Planned operators come from the station layout and present operators from attendance. Both are shown on the line (§5.1). |

---

## 3. Function-by-function verdicts (v1 scope, function map v0.8)

| # | Function | Verdict | Basis and gap |
|---|----------|---------|---------------|
| 1.1 | Operation master / library | New + Ext | New library operation model: code, name, family, machine class. OB operations are BoM operations (`mrp.routing.workcenter`) with the library code and family added. Grade and the skill-evaluated flag come from the family. |
| 1.2 | timeSSD ingestion | Core | Standard import (`base_import`) into the IE models. `excel_import_export` (OCA, installed) is available if templates help. The file format comes from step 4. |
| 1.4 | Difficulty grading | New | The family holds the grade A/B/C confirmed by the IE. The rubric is IE practice outside the system. |
| 1.6 | Family mapping | New | Family model holding grade, machine class and skill-evaluated flag. Each OB operation maps to exactly one family. |
| — | Product type (DEC-24) | Ext | A field on `product.category`. |
| 2.1 | Operation bulletin | Core + Ext | The BoM's operations are the OB (§5.1). |
| 2.2 | OB / SAM version control | New | A SAM-version table per OB operation, read at the completion date (§5.1). |
| 2.3 | SAM amendment and dispute records | New (+ OCA option) | A dispute record. Its approval could use `base_tier_validation` (OCA, installed). Open item FG-OPEN-08. |
| 4.1 | Line layout / station design | New | A station layout per line, with versions: operations per station, operators per station, machine per position (§5.2). |
| 4.2 | Takt and pitch | New | Computed from the layout, targets and garment SAM. |
| 4.3 | Balance metrics | New | Computed from the layout. |
| 4.4 | Skill-aware allocation | New | A report crossing the skill matrix with the layout. |
| 4.5 | Style changeover and learning curves | New | Production run, familiarity score, ramp class, ramp profiles and fitting. Production history per line × library code comes from work orders (FLAG-TECH-08). |
| 4.6 | Daily target and headcount | New | Operators present come from attendance (R4). |
| 5.1 | Bundle = MO, bundle ticket | Core + MES | Bundles are created with the MO split (§4.2). The bundle ticket and barcode belong to MES. |
| 5.2 | Bundle scans | Core + Ext + MES | Work-order time logs, with the employee added. The scanning UI belongs to MES (§4.3). |
| 5.5 | Off-standard bucket | New | §4.5 |
| 5.6 | Defect → repair → re-inspection | New | §8.1 |
| 5.7 | Time sources and data quality | Core + New | Attendance is core (§4.7). The exception list and the nightly pause job are new (§4.8). |
| 6.1 | Time accounting engine | New | Reads `hr.attendance` and the off-standard bucket. |
| 6.2 | Earned minutes engine | New | Reads work orders (quantity, operation, completion date, credited operator), the SAM versions and the defect records. |
| 6.3 | Efficiency metrics | New | M1 to M7 from the two engines above. |
| 6.4 | Dynamic skill matrix | New (+ Core option) | §6.1 |
| 6.5 | Operator tier | New | From the skill matrix. |
| 6.6 | Calibration and shadow mode | New | A versioned parameter (6.7) marks periods as shadow. |
| 6.7 | Parameter configuration | OCA | `base_time_parameter` (§6.2) |
| 7.1–7.6 | Incentive scope, PF, threshold, tier multiplier, defect deduction, off-standard protection | New | Spec §11, checked against the acceptance cases. |
| 7.7 | Special skill allowance metrics | New | Reported on the period record. |
| 7.8 | Payroll feeder | New | A stored record per operator per period, which payroll pulls (§6.3). |
| 7.9 | Self-funding check | New | Its cost input comes from the finance cost pool (§7.6). |
| 8.1–8.4, 8.6, 8.8, 8.9 | Analytics | Core | List, pivot and graph views over IE's stored figures. Spreadsheet dashboards (core, installed) for boards. `mis_builder` (OCA, installed) is optional. |
| 9.1 | Hourly production board (RT-1) | New + Core | Computed by IE. Live refresh through `bus` (core). |
| 9.2 | Exception alerts (RT-2) | New + Core + Own | Alerts as activities or notifications. `zalo_oa` (own, installed) is an optional channel. |
| 9.3 | Breakdown call (RT-3) | Core + New | `maintenance.request`, through a bridge module (§8.2). |
| 9.4 | Operator figures feed (RT-4) | New → MES | IE exposes today's provisional figures and MES displays them. |
| 9.5 | Station WIP flags (RT-5) | New | Buffers from work-order completions and starts, plus the layout (§4.3). |
| 9.6 | Live bottleneck (RT-6) | New | Computed from RT-5 and completions. |
| 9.7 | Station pace (RT-7) | New | Computed from time logs. |

---

## 4. Execution layer

The data model that everything else hangs on.

### 4.1 Mapping

| IE term | Odoo | Verdict |
|---------|------|---------|
| Bundle | `mrp.production`, one per bundle | Core |
| Lot (size × colour × shade) | The procurement group shared by the split MOs (`odoo/addons/mrp/models/mrp_production.py:1878-1938`) | Core |
| Style / OB | Product template, its BoM and the BoM's operations | Core |
| OB operation | `mrp.routing.workcenter` plus IE fields | Ext |
| Production record (operator × operation × bundle) | `mrp.workorder` | Core |
| Quantity credited | Work-order quantity, which is the MO quantity | Core |
| Operator credited | A new field on the work order | Ext |
| Start / pause / finish | `mrp.workcenter.productivity` rows (`time_ids`), stamped with server time | Core |
| Who scanned | A new employee field on each time log; core has only `user_id` (`mrp_workcenter.py:525-527`) | Ext |
| Completion date | Work order `date_finished` | Core |
| Pause reason | A new field captured at the pause; it opens an off-standard record | Ext |
| Line | Work centre | Core |
| Precedence, station buffer | Work-order dependencies | Core |
| SAM used | The SAM-version table, read at the completion date | New |
| Production run | OB × line, from changeover to the next OB | New |

### 4.2 Bundle MOs
- **Creation.** Core splits an MO into several (the `mrp.production.split` wizard, `_split_productions`, `mrp_production.py:1878`). The new MOs share the original's procurement group and are named with suffixes -001, -002 and so on. OCA `mrp_mass_production_order` (installed) creates many MOs in one step.
- **Size.** A bundle is size × colour × shade, then split to the bundle size planning chooses. The system sets no maximum (FG-02). Large bundles are allowed, and the shop floor pushes back through planning.
- **Shade.** Fabric lots already carry `qms_dye_lot` and `qms_shade_band` (from `qms_fabric_inspection`). How cut panels carry the shade through to sewing is checked in step 4 (FG-OPEN-04).
- **Side records per bundle** (counted in step 5):
  - stock moves and, under real-time valuation, journal entries;
  - chatter, since the MO is a `mail.thread` (`mrp_production.py:30`);
  - one calendar leave per started work order (`mrp_workorder.py:644-655`).
- **Readiness.** A work order is *ready* only when its components are reserved and its predecessors are done. Missing components make it *waiting*, and an unfinished predecessor makes it *pending* (`mrp_workorder.py:155-172`). So a bundle MO needs its cut panels reserved before Odoo reports it ready. IE's station buffer (RT-5) is therefore computed from predecessor completions and starts, not from Odoo's state.

### 4.3 Time logs and scanning
- **Scans.** MES writes the scans. A start creates a time row. A pause closes the open row (`button_pending`, `mrp_workorder.py:712-713`) and records the reason. A finish closes the work order (`button_finish`).
- **Combined stations** are scanned one operation after another. So every operator has at most one open work order at any time.
- **Shared station users** work with core's rules:
  - `button_start` skips a work order on which the *current user* already has an open row (`mrp_workorder.py:616-617`);
  - only one open row per user per work order is allowed (`mrp_workcenter.py:567-575`).
  With one operator per work order this is consistent. MES still records the employee on every row.
- **A finished work order cannot be restarted** (`mrp_workorder.py:618-621`). Together with the credited operator, this stops anyone from taking credit for another person's bundle.
- **Odoo side effects, all harmless to IE:**
  - When a work order closes after running past its expected duration, Odoo splits the time row and labels the excess "Reduced Speed" (`mrp_workcenter.py:588-604`). IE adds both rows together. Fields added to time rows must copy when Odoo splits a row by copying it. Ordinary fields do by default.
  - A work order's duration is the sum of all its time rows (`mrp_workorder.py:929-938`).
- **One shared row per line.** The line's `working_state` is stored on the work centre and recomputed whenever any of its time rows changes (`mrp_workcenter.py:57-60, 192-210`). So every scanner on a line writes the same work-centre row. Under concurrent scans this can cause serialization retries, which step 5 tests (P-04).

### 4.4 Operator state (FLAG-TECH-07)
An operator's state is derived, not stored separately:
- their current bundle = their open time row;
- whether they are off-standard = an open or covering off-standard record.

The checks, in the capture module:
- no second open work order;
- no start or resume during off-standard time;
- starting an off-standard period closes the open row (spec §3.3 rule 2).

### 4.5 Off-standard bucket (FLAG-TECH-10)
**This is a new model, not Odoo's loss rows (FG-05):**
1. An open time row with a non-productive loss marks the whole line *blocked* (`mrp_workcenter.py:192-210`). `button_start` then refuses every work order on that line (`mrp_workorder.py:613-614`). Blocking from a time row also ends every running work order on the line (`button_block`, `mrp_workcenter.py:577-579`).
2. A loss row attached to a work order counts in that work order's duration (`mrp_workorder.py:929-938`).
3. Loss rows have no multi-operator entry, no approval, no channel and no clipping to attendance.

**One record shape and three channels**, as in spec §3.3:
- **Channel 1:** a pause with a reason creates a pending record from the work order (written by MES), which the leader approves.
- **Channel 2:** the leader's form, for one operator or several. Line-wide stops such as OS-04 are a channel 2 entry for every operator on the line, not Odoo's block.
- **Channel 3:** repair records create OS-05 (§8.1).

**Clipping to attendance** (spec §3.3 rule 3, TC-TA-05) reuses core's interval arithmetic: attendance intervals minus calendar lunch (`odoo/addons/hr_attendance/models/hr_attendance.py:220-242`).

### 4.6 Mid-bundle reassignment
Reassignment is a supervisor-only change of the work order's credited operator. The finisher gets the whole bundle (spec §8 rule 3). Work orders are not `mail.thread` (`mrp_workorder.py:14-15`), so the audit trail comes from `auditlog` (OCA, installed) or a small log model (FG-OPEN-07). The time rows keep who actually scanned and when.

### 4.7 Attendance
- **Attended minutes (A)** come from `hr.attendance` intervals. For employees on a fixed calendar, core already subtracts the calendar's lunch (`hr_attendance.py:220-242`).
- **Identification.** `hr.employee.barcode` (Badge ID, `odoo/addons/hr/models/hr_employee.py:145`) is available for MES to identify operators.
- **Time categories** are not needed in v1 (spec §11.5). Overtime exists in core (`hr.attendance.overtime`) if they are ever needed.
- **OPEN-15** stays with the technical design. Option B (bundle time counted only inside attendance) uses the same interval arithmetic as clipping off-standard time, so its cost does not argue for option A.

### 4.8 Data quality
- The exception list (spec §3.4 item 5) is new: computed from attendance, time rows and the off-standard bucket.
- The optional nightly pause job is a scheduled action (`ir.cron`) that closes open time rows.

---

## 5. Standards and line engineering

### 5.1 OB and SAM
- **The BoM's operations are the OB:** sequence, work centre, time per piece.
  - Precedence (the OB flow chart) uses core operation dependencies (`allow_operation_dependencies`, `blocked_by_operation_ids`). Without dependencies, Odoo chains the work orders in sequence (`mrp_production.py:1582-1596`).
  - Garment SAM per department = Σ SAM of that department's operations.
- **SAM versions.** Odoo keeps one time per operation (`time_cycle_manual`) and uses it when the MO is created. IE needs SAM versions with effective dates, read at the completion date, including approved retroactive amendments (spec §5.2, TC-EM-07). So IE adds a SAM-version table per OB operation. `time_cycle_manual` is kept equal to the current version so that expected durations stay meaningful (R1).
- `mrp_bom_version` (OCA, installed) only marks a BoM as usable or not in manufacturing. It does not date SAMs.

### 5.2 Line, layout and planning
- **Station layout** (4.1) is a new model with versions: operations and operators per station, and the machine at each position. Neither CE nor OCA links maintenance equipment to work centres (`mrp_maintenance` is not part of CE), so the layout holds the machine link. That link is what RT-3 and "OS-01 minutes per machine" use.
- **The line shows** planned headcount (from the layout) and present headcount (from attendance). This replaces reading the work centre's capacity as headcount (R4).
- **Planning visuals (FG-14).** The core MO calendar (`odoo/addons/mrp/views/mrp_production_views.xml:601`) works at lot level, before lots are split into bundles. A work-order calendar coloured by work centre also exists (`odoo/addons/mrp/views/mrp_workorder_views.xml:314`). A production-run view (style × line × dates) belongs to planning features later; IE needs the production run anyway for the ramp calendar (FLAG-TECH-09).

---

## 6. Skill, parameters and payroll

### 6.1 Skill matrix
ILUO levels need IE's own model: warnings, downgrade grace, dormancy and evaluation history. Core `hr_skills` (installed) has employee skills with levels and a log (`hr.employee.skill`, `hr.employee.skill.log`), and the existing salary rules already read `hr.employee.skill`. Whether IE copies its levels into it is decided in technical design (FG-OPEN-05).

### 6.2 Parameters (DEC-21, FLAG-TECH-12)
OCA `base_time_parameter` (server-tools, available, not installed) provides:
- parameters with a code and a type (float, integer, boolean, date, JSON, record, text);
- versions with a start date;
- lookup of the version in force on a date (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:84-95`).

OCA payroll uses the same mechanism for its rule parameters (`payroll_rule_time_parameter`). Ramp profiles and PF tables fit its JSON type.

Two quirks to handle in technical design (FG-OPEN-09):
- A stored value that is falsy (0, 0.0, False) is read back as "no value" (`base_time_parameter.py:72-73`).
- `get_time_parameter` never raises when a value is missing (`models/base.py:22`).

So IE reads parameters through one helper of its own. The change history comes from the version records themselves (creator, date), with `auditlog` if more is needed.

### 6.3 Payroll feeder (FG-09)
IE stores one record per operator per period. It is locked at period close, carries the shadow/live flag, and holds the fields of spec §12 and TC-PAY-01. Payroll's salary rules read it. IE does not depend on payroll. Pay and evaluation periods could use `date_range` (OCA, installed) (FG-OPEN-06).

---

## 7. Costing and inventory valuation (FLAG-TECH-01)

### 7.1 How CE 18 values a manufactured product
1. **At MO done**, the finished goods' unit cost = (value of the components consumed + work-order cost + *Extra Unit Cost* × quantity) ÷ quantity (`odoo/addons/mrp_account/models/mrp_production.py:40-63`). Under average cost this blends into the product's cost, and from there into COGS and margin.
2. **Work-order cost** = logged time × the work centre's `costs_hour` (`odoo/addons/mrp/models/mrp_workorder.py:597-610`). At MO done, a work order with no logged time first gets its expected duration filled in (`mrp_production.py:1836-1842`). So Odoo uses actual time when there are scans and standard time when there are none.
3. **Extra Unit Cost** (`extra_cost`) is a flat amount per finished unit on the MO. Splitting an MO copies it to the new MOs (`mrp_account/models/mrp_production.py:67-69`).
4. **Journal entries** are posted under real-time valuation only (`odoo/addons/stock_account/models/stock_valuation_layer.py:86`):
   - components: debit the production account, credit component stock;
   - finished goods: debit stock, credit the production account (`mrp_account/models/stock_move.py:26-34`).

   The conversion cost absorbed this way stays as a credit on the production account (`mrp_account/models/product.py:126-130`). It is cleared against the actual wages and overhead, and what remains is the variance.

### 7.2 The choice
Valuation happens at MO done, continuously. The actual conversion cost is known only at payroll close, monthly. So any valuation has to use a rate fixed in advance, and the variance always lands in the period's P&L. The only question is **which minutes the rate multiplies**:

| Option | Mechanism | Finished goods carry | Effect on the premise |
|--------|-----------|----------------------|-----------------------|
| A. None | No hourly cost, no extra cost | Materials only; labour is expensed through payroll | None |
| B. Scanned minutes | `costs_hour` = an operator-hour rate, with the scans on the work orders | Scan time × rate | **Ties valuation to scanning** |
| C. Standard minutes | `costs_hour` = 0; *Extra Unit Cost* = garment SAM × rate | Materials + standard conversion cost | None |

**Why B fails:**
- A bundle left open overnight goes into stock value at MO done, long before the data-quality review at payroll close. Once it has blended into average cost, it cannot be corrected.
- A slow bundle becomes a more expensive garment, so inefficiency ends up in inventory.
- Scans do not cover off-standard time or gaps, so the amount absorbed moves with scanning discipline.

### 7.3 Decision (FG-06): option C
The finished goods carry standard conversion cost, and rule R2 keeps scanned time out of valuation.

The amount absorbed is Σ quantity × SAM × rate, which is **gross earned minutes × rate**. So accounting's variance and IE's efficiency figures describe the same thing: for a given rate, the variance moves with M3.

Accounting standards generally expect conversion costs in inventory, with abnormal waste expensed (IAS 2 §12–16; VAS 02 follows IAS 2 on conversion costs). The accountant confirms the position.

### 7.4 Rate basis (FG-07)
There are two candidates:
```
100% basis      rate = conversion cost ÷ attended minutes              (= CPM, spec §6.1)
measured basis  rate = conversion cost ÷ gross earned minutes          (= CPM ÷ M3, over a trailing window)
absorbed        = EM_g × rate
variance        = actual conversion cost − absorbed
```
Conversion cost = direct labour + production overhead.

*Worked numbers* use the rationale's Line 1: CPM 1,041.67 VND, 374,400 attended minutes, conversion cost 390.0M VND a month. Both months assume the same conversion cost.

| Month | EM_g (M3) | 100% basis: absorbed / variance | Measured basis (rate 1,494.25 VND per EM): absorbed / variance |
|-------|-----------|----------------------------------|------------------------------------------------------------------|
| Normal | 261,000 (69.7%) | 271.9M / **118.1M unfavourable** | 390.0M / **0** |
| Better | 285,000 (76.1%) | 296.9M / **93.1M unfavourable** | 425.9M / **35.9M favourable** |

For a polo with SAM 10.00, the conversion cost per unit is 10,417 VND on the 100% basis and 14,943 VND on the measured basis.

**Recommendation: the measured basis.**
- **No efficiency figure is chosen; it is measured.** The only settings are the window (e.g. 3 to 6 months) and how often the rate is revised (e.g. quarterly). Both are ordinary parameters.
- **Inventory and product margin carry the normal cost.** On the 100% basis, inventory permanently misses about 30% of conversion cost in this example, and Odoo's product margins are overstated by that amount.
- **The variance means something.** It is near zero in a normal month, and its sign says whether the month beat or missed normal efficiency. On the 100% basis it is large and unfavourable every month, even when efficiency improves.
- **It matches the standard costing rule.** IAS 2 §21 says standard costs reflect normal levels of efficiency and are reviewed regularly. Expect the accountant or auditor to move a 100%-basis gap back into inventory at year end.
- **Pay is unaffected** (DEC-08).

**Implications to accept:**
- A period heavy with changeovers lowers M3 and so raises the rate for later production. A longer window smooths this.
- Pricing an individual order at its real cost (small orders cost more, rationale §5.2) stays with the costing stream, not with inventory.

**Bootstrap.** Shadow mode produces EM_g, so the first measured rate can be set before IE costing goes live. Until then, finance's current figure or the 100% basis applies.

### 7.5 Rate ownership (FG-07)
- **Finance owns the rate.** It decides the cost pool (which labour and overhead accounts count) and answers for inventory value. Finance sets and approves the rate as a versioned parameter with an effective date (§6.2), editable by accounting managers.
- **IE informs it.** IE owns the denominator and the minutes per unit (EM_g, garment SAM), and shows the trailing cost per earned minute next to the rate in force.

### 7.6 Cost inputs (FG-12)
Finance enters one cost pool per period: direct labour (base wages, incentive paid, allowances) plus production overhead. It feeds:
- the suggested valuation rate (§7.4);
- the self-funding check (spec §11.8), which uses the labour part only.

So IE needs no payroll dependency. A bridge that reads payslip totals can come later if entering the pool by hand becomes a burden.

### 7.7 Mechanism
- At MO done, the bundle MO's *Extra Unit Cost* = sewing garment SAM (the SAM versions in force on the completion date) × the rate in force. Technical design chooses the hook.
- Cutting MOs keep their current treatment until their standards exist (OPEN-07).
- Only the rate moves into v1. The costing stream (CM estimates, E_plan, order-level load) stays deferred (function map area 3).

---

## 8. Quality, maintenance and notifications

### 8.1 Defects, repair, re-inspection (FG-08)
- **The defect record is new.** It holds the fields of spec §9.1:
  - the work order, which gives bundle, operation and credited operator;
  - the defect code (`qms.defect.code`, from `qms_catalog`);
  - defective quantity, detection point, responsibility, detection date and inspector.
- **Defects not traceable to an operation** are attributed to the line, with no work order (spec §9.2).
- **FLAG-TECH-13** becomes a check on this one model: the cumulative defective quantity per work order may not exceed the work-order quantity. A record that would exceed it is rejected with an error.
- **A repair record** (repairer, bundle, operation, quantity, start, end) creates OS-05 through channel 3. **Re-inspection** is a state on the defect: a pass closes it, a fail returns it to repair.
- **Capture is in MES.** IE's dependency on `qms_catalog` brings in `product` and `mgmtsystem`, both installed.
- **Formal inspections stay in QMS.** QC inspections and audits stay in `quality_control_oca` and the QMS suite. IE does not read them in v1.

### 8.2 Breakdown call (RT-3, FG-13)
- A pause with reason OS-01 opens a corrective `maintenance.request` (core). It names the machine from the station layout, plus the operator and the time. The PMS suite (SLA, priority matrix) then applies to it as to any corrective request.
- **It has to be created with sufficient rights.** On this instance a plain internal user can create only a request they can still read afterwards:
  - the request's owner defaults to its creator (`odoo/addons/maintenance/models/maintenance.py:249`);
  - `hr_maintenance` recomputes the owner from the request's employee and empties it when there is none (`odoo/addons/hr_maintenance/models/equipment.py:88-97`);
  - the own-requests rule then requires the user to be owner, follower or Responsible (`odoo/addons/maintenance/security/maintenance.xml:18`).
- **Placement.** A bridge module (IE or capture plus maintenance) holds this, so the IE core has no maintenance dependency.

### 8.3 Notifications and refresh
- **Live figures** use `bus` (core). Periodic figures use scheduled actions.
- **Alerts and breakdown calls** go out as activities or notifications. `zalo_oa` (own, installed) is an optional channel.

---

## 9. Integration: the roadmap's key gaps answered

| Partner | Answer |
|---------|--------|
| Quality | The QMS suite exists. IE keeps its own defect record coded from `qms_catalog` (§8.1). |
| Payroll | OCA `payroll` pulls IE's period records through salary rules (§6.3). |
| Maintenance / CMMS | Core maintenance plus the PMS suite. RT-3 goes through a bridge module (§8.2). The machine link lives in the station layout (§5.2). |
| HR / Attendance | `hr.attendance` (core). A is computed with core's lunch handling (§4.7). |
| Product master | Product type on `product.category` (DEC-24). |
| timeSSD | File import (1.2). The format comes from step 4. |
| MES interface | Shares the capture module (§10) and displays IE's figures (RT-4). |
| Sales / costing | Later, with the costing stream. The valuation rate is the exception (§7). |

---

## 10. Preliminary module shape (input to step 7)

| Layer | Content | Depends on |
|-------|---------|------------|
| Capture (shared by MES and IE) | Credited operator on the work order, employee on time rows, pause reason, operator-state checks | `mrp`, `hr` |
| IE master data | Library operations, families, grades, IE fields on BoM operations, SAM versions, product type, parameter helper | `mrp`, `base_time_parameter` |
| Off-standard and time accounting | The bucket and its three channels, attendance clipping, A / OS / NAM, data-quality exceptions | Capture, `hr_attendance` |
| Defects and repair | Defect and repair records, re-inspection state | Capture, `qms_catalog` |
| Metrics and skill | Earned minutes, the metric family, skill matrix, tiers | The layers above |
| Incentive and period record | PF, threshold, ramp-adjusted threshold, excess, units, the payroll period record, shadow mode | Metrics and skill |
| Valuation | Extra Unit Cost at MO done, the rate parameter, the cost pool | IE master data, `mrp_account` |
| Line engineering | Station layout, balancing, changeover and ramp-up | IE master data |
| Real-time | RT-1 to RT-7 | Metrics, line engineering |
| Bridge: maintenance | RT-3 | Capture, `maintenance` |

- Shadow mode needs capture, time accounting, metrics and skill. The incentive layer can be built last (roadmap step 7).
- Module names and the model and field prefixes for the IE and MES suites are open (FG-OPEN-03).

---

## 11. Step 5 prototype plan

**Goal:** prove the premise (FG-02) at real volume before the technical design is written. That means bundle MOs, work orders as production records, and scanning load.

**Inputs.** Step 4 supplies the real volume: pieces per month, lot sizes, bundle size, operations per garment, operators and lines. Until then the default sizing is the rationale's Line 1:
- 30 operators, 1,100 garments a day, 8 operations, bundles of 20;
- that gives 55 bundle MOs and 440 work orders per line per day, and about 1,430 MOs and 11,440 work orders per line per month;
- multiplied by the number of lines.

**Setup:**
1. Take a database backup (FG-15).
2. Create one style whose BoM has the OB operations with dependencies.
3. Configure the line work centres per R1 and R2.
4. Put cut panels in stock so the bundle MOs can reserve them.
5. Create lot MOs per size × colour.
6. Simulate scans with parallel JSON-RPC clients, each logged in as a station user.
7. Restore the backup afterwards.

| # | Scenario | Measured | Pass criterion `[P]` |
|---|----------|----------|----------------------|
| P-01 | Split a day's lots into bundle MOs | Time; records created | ≤ 1 min per 100 bundle MOs |
| P-02 | Confirm bundle MOs | Time; work orders, dependencies, reservation | ≤ 1 min per 100 MOs; work orders become *ready* as their predecessors finish |
| P-03 | Scan a day sequentially: start, finish, some pauses | Time per call; time rows created (including "Reduced Speed" splits) | ≤ 1 s per scan |
| P-04 | Concurrent scanning: K operators on one line at a burst (shift start), K up to the line's headcount | Latency; serialization retries; errors shown to users (the `working_state` row, §4.3) | ≤ 1 s at the 95th percentile, no errors shown to users |
| P-05 | Mark bundle MOs done with real-time valuation and Extra Unit Cost | Time per MO; journal entries per bundle; the value booked | ≤ 2 s per MO, or a day's bundles closed by a batch job within 15 min; value = materials + SAM × rate exactly |
| P-06 | Side records per bundle | Stock moves, valuation layers, journal entries, calendar leaves, time rows, chatter messages | Counted; Peter and accounting accept the totals |
| P-07 | Views with a year of bundle data | MO and work-order list, kanban and calendar load times | ≤ 3 s |
| P-08 | IE aggregation | Earned minutes per operator-day over a month; defect attribution through the work order | ≤ 30 s for a month |

**What to do if a scenario fails:**
- **Closing too slow:** close bundles in a batch job outside shifts.
- **Concurrency failures on the line's work-centre row:** measure first. Overriding the stored compute is an engine change and a last resort, so this result weighs heavily on the premise.
- **Journal volume unacceptable:** accounting can value the WIP category periodically. Odoo still computes the stock values but stops posting entries for it (`stock_valuation_layer.py:86`).
- **MO creation or closing fundamentally too heavy:** switch to the fallback premise (§2.2).

Results go into v0.2 of this document.

---

## 12. Consequences for the business documents (proposals, not applied)

Each item goes through the document workflow (function map, *Document set & workflow*).

1. **Spec §6, scope note, and §6.6.** Inventory valuation carries a standard conversion cost (§7) in v1. The rate comes from IE's minutes and finance's cost pool. FLAG-TECH-01 is resolved in principle.
2. **Spec DEC-04, §8 rule 1.** Bundle = MO is confirmed as the premise (FG-02). Bundle size is a planning parameter with no system maximum.
3. **Spec §8 rule 3.** Reassignment is a supervisor change of the work order's credited operator.
4. **Spec §3.3, channel 1.** The pause reason is captured by MES at the work-order pause.
5. **Spec §11.8 and §12.** The self-funding check takes its labour cost from the finance cost pool. Payroll pulls IE's figures; IE does not push.
6. **Spec §15.** FLAG-TECH-02, 06, 07, 10, 12 and 13 have a chosen approach (table below).
7. **Roadmap step 3.** The statement "CE has no Quality module and no Payroll module" is out of date for this instance (§1).
8. **Roadmap steps 5 and 8.** The development environment exists: this instance, a test copy restored from production. The volume part of step 4 comes before step 5.
9. **Function map 6.7 and 7.9.** Note the OCA parameter module and the cost-pool input.
10. **Rationale §8.4.** It says defects are "capped at the bundle quantity". Since spec v0.6 the record is rejected with an error, and the cap is on defective quantity (pieces), not on DD (minutes).
11. **Spec §10.4, dormancy.** It does not say whether a further 180 days without volume drops another level.

**FLAG-TECH status after the fit-gap**

| Flag | Status |
|------|--------|
| 01 Work centre study | Resolved in principle: two layers (§2) and costing C (§7) |
| 02 MO grouping | Lot = the split's procurement group; style/OB = BoM; production run = new IE record (§4.1) |
| 03 Family time from scans | Unchanged; time rows give the bundle time |
| 04 Bundles across days or categories | Unchanged; the completion date is the work order's `date_finished` |
| 05 SAM version referencing | SAM-version table read at the completion date (§5.1) |
| 06 Data model approach | Resolved: work orders as production records, with IE models beside them (FG-01, FG-02) |
| 07 Operator state | Derived from open time rows and off-standard records, enforced in the capture module (§4.4) |
| 08 Library codes | On BoM operations; history per line × code from work orders |
| 09 Ramp calendar | Technical design (production run, §5.2) |
| 10 Off-standard bucket | New model with three channels, not loss rows (§4.5) |
| 11 Real-time implementation | Partly set: `bus`, notifications, the RT-3 bridge, the layout; the MES feed format comes later |
| 12 Parameter configuration | OCA `base_time_parameter` (§6.2) |
| 13 Defect quantity validation | A check per work order on the defect model (§8.1) |
| 14 Leeway mechanism | Technical design |

---

## 13. Open items

| ID | Item |
|----|------|
| FG-OPEN-01 | Rate basis and owner (FG-07): confirm with the accountant, including the VAS 02 position. |
| FG-OPEN-02 | Real volume figures for the prototype (step 4). |
| FG-OPEN-03 | Module names and prefixes for the IE and MES suites, including whether the shared capture module takes an OCA-style name. |
| FG-OPEN-04 | Where a bundle's shade comes from (fabric lot dye lot or band) and how cut panels carry it (step 4). |
| FG-OPEN-05 | Whether ILUO levels are copied into `hr_skills` (technical design). |
| FG-OPEN-06 | Pay and evaluation periods on `date_range` or IE's own (technical design). |
| FG-OPEN-07 | Reassignment trail: `auditlog` or IE's own log (technical design). |
| FG-OPEN-08 | Dispute approval: `base_tier_validation` or a plain two-step state (technical design). |
| FG-OPEN-09 | `base_time_parameter` quirks: falsy values read back as missing, and missing values never raise. IE reads parameters through its own helper (technical design). |
| OPEN-15 | Stays with the technical design. Option B costs no more than option A (§4.7). |

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-19 | First version. Two-layer finding and the bypass decision; work order = production record and MO = bundle as the premise; line configuration rules; execution-layer mapping; off-standard bucket as its own model; costing option C with a measured rate basis; function-by-function verdicts; integration answers; preliminary module shape; step 5 prototype plan; proposals for the business documents; open items. |
