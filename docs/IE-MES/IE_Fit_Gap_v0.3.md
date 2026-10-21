# IE Module — Fit-Gap against Odoo CE 18

**Version:** v0.3 (draft) · 2026-10-21
**Roadmap steps:** 3 (fit-gap against Odoo CE 18) and 5 (prototype of the riskiest assumption). Most of step 4 (integration inventory) was answered on 2026-10-20 (§1).
**Based on:**
- `IE_Business_Logic_Spec_v0.6.md`, `IE_Framework_Rationale_v0.6.md`, `IE_Module_Function_Map.md` (v0.8), `IE_Acceptance_Test_Cases_v0.3.md`;
- the timeSSD export `TimeSSD Data.xlsx`;
- the Odoo CE 18 core the instance runs (`odoo/`, at the image's pinned commit) and the mounted OCA repositories (`oca/`), read 2026-10-19 to 2026-10-21;
- the prototype harness `Odoo-Build/ie-prototype/` (`ie_proto.py`, `burst.sh`, `README.md`), run on the instance 2026-10-21.

**Supersedes:** `IE_Fit_Gap_v0.2.md`. `v0.1` and `v0.2` are kept as history.

**Purpose:** For every v1 function, this records:
- what standard Odoo, OCA or our existing modules provide;
- what has to be built;
- which Odoo features IE deliberately leaves alone.

It also records the decisions taken during the fit-gap, and the step 5 prototype with its results and the viability gate (§13). The business rules stay in the spec. Where this document implies a change to the spec, rationale, function map, roadmap or test cases, §14 lists it as a proposal for the document workflow.

**Conventions**
- Source references are `path:line`, relative to `Odoo-Build/`. After its first full mention in a section, a file may be named by a shorter path such as `mrp_workorder.py`.
- Worked numbers come from the rationale's running example unless marked as instance or reported figures.
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

- Status labels: **Agreed** (confirmed by Peter, with date) · **Proposed** (recommended here, not yet confirmed) · **Working premise** (stated by Peter, to be settled in its own phase) · **Open** (listed in §15).

---

## 0. Decisions and findings

| ID | Decision or finding | Status |
|----|---------------------|--------|
| FG-01 | **Two layers.** Use Odoo MRP's *record layer*: MOs, work orders, time logs, operation dependencies, BoM operations, stock and valuation. Bypass its *resource engine*: work-centre scheduling, capacity-based durations, work-centre load and hourly work-centre cost. IE holds the line layer. (§2) | Agreed 2026-10-19 |
| FG-02 | **Work order = production record. MO = physical bundle.** The planner splits MOs on whatever basis they choose. The system sets no maximum bundle size. (§5) | Agreed 2026-10-19; **confirmed by the step 5 prototype**, 2026-10-21 (§13) |
| FG-03 | **Configuration rules for IE lines:** capacity 1, no hourly cost, no "Plan" on bundle MOs. Planned headcount comes from the layout and active headcount from scans. (§2.3) | Proposed |
| FG-04 | **Operator identity.** Each work order gets a credited operator, and each time log gets the employee who scanned. Operators remain employees without user accounts. (§5.4) | Proposed |
| FG-05 | **The off-standard bucket is an IE model**, never Odoo's loss rows. One open loss row blocks every work order on the line. (§5.6) | Proposed |
| FG-06 | **Costing option C.** Finished goods carry a standard conversion cost through the MO's *Extra Unit Cost* = garment SAM × rate. Lines carry no hourly cost, so scanned time never reaches valuation. (§9) | Agreed 2026-10-19 |
| FG-07 | **The rate is the measured conversion cost per earned minute** over a trailing window, versioned with an effective date. Finance owns it and IE informs it. (§9.4–9.5) | Proposed; no objection in the v0.1 review (2026-10-20); the accountant confirms |
| FG-08 | **Defects are an IE record** linked to the work order and coded with `qms_catalog` defect codes. (§10.1) | Agreed 2026-10-19 |
| FG-09 | **Payroll pulls** IE's period records through its salary rules. IE has no dependency on payroll. (§8.3) | Agreed 2026-10-19 |
| FG-10 | **Scanning belongs to MES.** The capture data sits in one module that both MES and IE depend on. (§6, §12) | Scanning in MES: Agreed 2026-10-19. Shared module: Proposed |
| FG-11 | **Parameters** (DEC-21) are stored with OCA `base_time_parameter`. (§8.2) | Proposed |
| FG-12 | **Finance enters one period cost pool.** It feeds both the valuation rate and the self-funding check. (§9.6) | Proposed |
| FG-13 | **Breakdown call (RT-3):** a pause with reason OS-01 opens a core maintenance request, through a bridge module. (§10.2) | Proposed |
| FG-14 | **Planning visuals** use the core MO calendar at lot level. A production-run view comes later. (§7.4) | Proposed |
| FG-15 | **The prototype is a disposable run** on this instance, a test copy restored from production. A backup was taken before it. (§13) | Done 2026-10-21 |
| FG-16 | **Master data follows timeSSD.** IE holds timeSSD's products, groups (sections), machines and methods. A style's OB is its BoM operations, each pointing to a method. The predetermined-time element breakdowns are not imported. (§3) | Agreed 2026-10-20 |
| FG-17 | **The operation family list is IE's one master-data addition.** A family is a name and a grade. Each method belongs to one family, and a family's methods share one machine type. (§3.3) | Agreed 2026-10-20 |
| FG-18 | **A skill-evaluated switch sits on the machine type.** It defaults from timeSSD complexity: yes for Mechanic and Manual, no for Automat and Semiautomat. It stays editable; the 5-thread overlock is set to yes. Families inherit it. (§3.4) | Agreed 2026-10-20 |
| FG-19 | **Product type = timeSSD Product, read from the style's OB.** The plateau is computed per line × product type, so system-computed targets stay. (§3.5, §7.1) | Agreed 2026-10-20 |
| FG-20 | **Default precedence comes from sections.** Operations in a section run in line order. Preparation sections run in parallel, assembly waits for preparation, and finishing waits for assembly. The IE edits exceptions on the BoM. (§7.2) | Agreed 2026-10-20 |
| FG-21 | **Attendance is an input, read when IE computes.** Open periods are recomputed whenever attendance arrives, so monthly and daily imports both work. (§5.8) | Agreed 2026-10-20 |
| FG-22 | **Real-time figures come from production records only.** "Operators active" is read from scans. The RT features are candidates, not commitments. (§7.3) | Agreed 2026-10-20 |
| FG-23 | **Capture works through scan events**: an event ID, type, operator badge and device time. Events are applied once and in order, with a fixed rule for their time. (§6.2) | Proposed |
| FG-24 | **IE dates are local factory dates** (UTC+7). Each production record stores its local completion date. (§6.3) | Proposed |
| FG-25 | **The line a bundle runs on is a field on the MO**, and it sets the work centre of the MO's work orders. (§5.3) | Proposed |
| FG-26 | **QMS alignment by codes, not by code coupling.** QMS object parts reuse timeSSD codes. IE does not use parts. (§3.7) | Proposed |
| FG-27 | **SAM versions belong to the method,** timeSSD's unit. A production record uses its method's version in force on the completion date. (§3.6) | Proposed |
| FG-28 | **Viability V1 passes.** At the reported volume, planning, scanning, closing and valuation all hold. Simultaneous scans collide only when a line flips between idle and busy, and Odoo's retry absorbs it. (§13.2) | Measured 2026-10-21 |
| FG-29 | **IE reads only scan rows.** When an MO closes, Odoo fills every work order that has no recorded time with its expected duration, creating a time row nobody scanned. IE's bundle time counts only rows that carry an employee. (§5.4) | Proposed |
| FG-30 | **Closing an MO needs Quality Control / User rights on this instance**, because `quality_control_mrp_oca` reads its trigger lines as the closing user. Whoever closes bundle MOs needs that group, or the lookup is made with elevated rights in an additive override. (§5.2) | Open: FG-OPEN-14 |
| FG-31 | **Run in the garment company.** IE runs in Công ty TNHH Dệt May Quang Phương, whose production warehouse WH Chi Lăng is three-step. Splitting a lot into bundles keeps one component picking per lot. (§1, §5.2) | Measured 2026-10-21 |

---

## 1. Context

Instance and reported facts, 2026-10-19 to 2026-10-21:
- **This instance** is a test copy restored from production. Its existing manufacturing records are Peter's tests, not real production.
- **Server:** 8 GB RAM, 4 vCPU, `workers = 2`, `db_maxconn = 16` (database connections per Odoo process).
- **Two companies.**
  - The garment company (Công ty TNHH Dệt May Quang Phương) owns WH Chi Lăng, which is three-step (pick components, manufacture, store). It holds all MOs, and the only real-time valuation settings (average cost) on Finished Goods, WIP and Raw Materials.
  - The trading company (Công ty TNHH DV TM Quang Phương) owns WH Bình Tân, which is one-step.

  IE runs in the garment company (FG-31).
- **Quality and payroll.** Odoo CE has no Quality or Payroll app of its own. Both are present here: the QMS suite runs on `quality_control_oca` and `mgmtsystem`, and OCA `payroll` is in use. Its salary rules already read attendance, leave, employee skills and timesheets.
- **Operators** are `hr.employee` records without user accounts. The sewing lines already exist as work centres ("Chuyền …").
- **Attendance** comes from biometric devices. Odoo matches it to resource calendars, and it is imported monthly today, possibly daily later. The calendars use Asia/Ho_Chi_Minh and the garment company Asia/Bangkok, both UTC+7 with no daylight saving.
- **Shade** comes from the QMS roll inspection (`qms_fabric_inspection`). It is advisory: planners split MOs into bundles at their own discretion.
- **timeSSD** data is entered into Odoo by hand. Automating it, if ever needed, uses the OCA import/export modules. The export shape in `TimeSSD Data.xlsx` is everything timeSSD provides.
- **Reported volume to size for:**
  - about 4,000 garments a day across about 5 lines of 20 to 30 operators;
  - bundles of about 50;
  - 15 to 25 operations per garment.

  That gives about 80 bundle MOs and 1,200 to 2,000 work orders a day, about 2,100 MOs and 42,000 work orders a month, and about 3,500 scan events a day.
- **MES** means the shop-floor capture interface. Peter's working premises are in §6.1.

---

## 2. The governing finding: Odoo MRP has two layers

### 2.1 What fits and what does not

| Layer | What it assumes | Fit for a garment line |
|-------|-----------------|------------------------|
| **Records**: MO, work orders, time logs, operation dependencies, BoM operations, stock and valuation | One document per job, one record per operation, who did it and when | **Fits.** The gaps are additive (§5). |
| **Resource engine**: work-centre scheduling, capacity-based durations, work-centre load, hourly work-centre cost | A work centre is *one* resource that does one job at a time | **Does not fit.** A line is a pool of N operators running many jobs in parallel, and N changes with the style and the day. |

Evidence from the code:
- **Capacity** is the number of pieces processed in parallel *inside one work order* (`odoo/addons/mrp/models/mrp_workcenter.py:36-38`). Its only use is to divide the quantity into cycles for the expected duration (`odoo/addons/mrp/models/mrp_workorder.py:794-796`, `odoo/addons/mrp/models/mrp_routing.py:83-93, 188-189`).
- **The planner** places each work order in an interval "disjoint with all other workorders planned on this workcenter" (`mrp_workcenter.py:339-341`).
- **Each started work order** books a `resource.calendar.leaves` record for its expected duration (`mrp_workorder.py:644-655`).
- **Hourly work-centre cost** multiplies logged time by `costs_hour` and adds it to the value of the finished goods (§9.1).

With capacity 1, a bundle work order's expected time is quantity × SAM, which is one operator's standard time and equals the work order's earned minutes.

### 2.2 Bypass, not enhance

| Alternative | Verdict |
|-------------|---------|
| **Bypass**: use the record layer, configure the engine out of the way (§2.3), keep the line layer in IE | **Chosen** (FG-01). No core method is overridden for the engine. |
| **Enhance**: rework the engine (a parallel-aware planner, a line as N resources, new duration semantics) | Rejected. It means deep overrides of core scheduling, costly at every upgrade and against the additive rule. IE plans with targets, learning curves and ramp-up, which Odoo's scheduler cannot express. |
| **A work centre per station** | Rejected. Layouts change at every changeover, so the work centres would keep churning. |
| **Fallback**: MO = shade lot, with bundles as IE records under the lot's work orders | Kept only in case step 5 fails. |

What the bypass gives up:
- **Automatic scheduling of lots onto lines.** Planners load lines by hand on the MO calendar. Automatic line scheduling would be a separate, new engine and is not part of IE v1.
- **What remained at risk** was the engine code that runs inside the record layer on every scan: the work-centre state row, the calendar leaves, the time-row splits and the readiness rules. Step 5 tested exactly that, and none of it blocks the premise (§13.2).

### 2.3 Configuration rules for IE lines (FG-03)

| Rule | Setting | Why |
|------|---------|-----|
| R1 | Work-centre capacity = 1 (and no per-product capacity) | Expected duration then equals quantity × SAM. Capacity affects nothing else (§2.1). |
| R2 | `costs_hour` = 0 | Scanned time must never reach the value of finished goods (§9). The work centre warns when an IE line carries an hourly cost. |
| R3 | No "Plan" on bundle MOs | The planner would lay a day of parallel work end to end. One example: 55 bundles of a 10-minute garment is 11,000 minutes, which plots as about 23 working days. |
| R4 | Headcount from IE | Planned headcount comes from the station layout and active headcount from today's scans (§7.3). The line shows both. |

---

## 3. Master data from timeSSD (FG-16 to FG-19, FG-26, FG-27)

### 3.1 What timeSSD provides

| timeSSD sheet | Content | Example from the export |
|---------------|---------|-------------------------|
| Product | Product types | BRA, DRESS, Jacket, Jeans, MTRO, SHR, TSH, … (13) |
| Group | Sections of a product type | SHR03 Shirt Collar, SHR06 Shirt Assembly, SHR07 Shirt Finishing, BRA01 Bra Cups |
| Machine | Machine types with purpose, principle, complexity, maker and model | LOCK1 single needle lockstitch, Mechanic; BHM buttonhole, Semiautomat; OVL5 5-thread overlock, Automat |
| Method | The **library operation**: code, description, SAM, product, group, machine | `AAS00101` "Join side panel and cups", 0.39, BRA, BRA04, LOCK1 |
| Method Detail | How the SAM is built: TST × allowance, then the predetermined-time elements | `A001`: TST 0.40 × allowance 1.15 = SAM 0.46 |
| Workflow + Detail | The **operation bulletin** of a model, plus reusable section workflows (`_MP`) | Bra: 16 lines, each a method code with SAM and machine, totalling 5.65 |
| Model | Styles | "Shirt example", "Bra example" |
| Parts | Garment parts | A0101 Cups, B0102 Collarstand |

The facts IE relies on, checked against the export:
- **Workflow lines are method codes.** `AAS00101` in the bra workflow is the same method, with the same SAM, as in the method library. So a library code is stable across styles, and the familiarity score (spec §7.7.2) works as specified.
- **SAM includes the allowance** (SAM = TST × allowance, set per method). Spec §5.5's allowance calibration therefore happens in timeSSD.
- **The export has no field relating parts to groups and no precedence field.**

### 3.2 The IE master-data model

| IE concept | Source | Odoo home | Added by IE |
|------------|--------|-----------|-------------|
| Product type | timeSSD Product | Small IE model (code, description) | — |
| Section | timeSSD Group | Small IE model (code, description, product type) | **Stage**: preparation, assembly or finishing (§7.2) |
| Machine type | timeSSD Machine | Small IE model (code, description, purpose, principle, complexity) | **Skill-evaluated** switch (§3.4) |
| Library method | timeSSD Method | IE model (code, description, product type, section, machine type; TST and allowance optional) | **Family** (§3.3) and **SAM versions** (§3.6) |
| Operation family | — | IE model (name, grade A/B/C) | The whole record |
| OB of a style | timeSSD Workflow, flattened | The style's BoM: its operations (`mrp.routing.workcenter`) each reference a method, with description and time defaulted from it. The BoM carries the workflow code and product type. | — |
| Style | timeSSD Model | Product template | — |
| Predetermined-time elements | Method Detail | **Not imported.** They stay in timeSSD as evidence for SAM disputes. | — |
| Parts | timeSSD Parts | Not used by IE (§3.7) | — |

### 3.3 Operation family (FG-17)
The method is too fine a unit to measure skill:
- **Volume.** Methods come in variants, so few operator-method pairs reach the minimum volume (600 EM in the window, spec §10.3).
- **Leeway.** The proficiency factor would restart on every variant, overpaying and inviting gaming.
- **Tiers.** Counting methods at U would inflate versatility.

timeSSD's sections cannot serve either: "Shirt Assembly" holds collar attach (hard), bottom hem (easy) and buttonhole (automatic). So families are IE's own grouping:
- a short list of operation types, each with a grade (e.g. "Collar setting · A");
- each method assigned to one family when it is entered;
- **a family's methods share one machine type**, so the family's machine class and skill-evaluated flag are unambiguous (spec §2: "Collar setting · SNLS · Grade A").

Grading a few dozen families replaces grading hundreds of methods.

### 3.4 Skill-evaluated switch (FG-18)
DEC-12 excludes work where the machine controls the stitching. timeSSD's complexity says this per machine type:

| Complexity | Default | Examples in the export |
|------------|---------|------------------------|
| Mechanic | skill-evaluated | LOCK1, LOCK2, OVL3, OVL4, CHA1, ZZM, CVSM |
| Manual | skill-evaluated | IWST ironing work station, QCT QC table |
| Semiautomat | not skill-evaluated | BHM buttonhole, BUTM button sew, BARM bartack, BLPM belt loop, presses |
| Automat | not skill-evaluated | fusing presses, PFA, AWP, ABHEM, OVA |

- The switch is editable per machine type. **OVL5 (5-thread overlock) is set to skill-evaluated** even though timeSSD lists it as Automat. timeSSD's complexity value stays as delivered.
- Families inherit the switch from their machine type.
- The grading rubric's machine-type factor (spec §5.6) reads the same switch: a family on a non-evaluated machine is graded C.

### 3.5 Product type (FG-19)
- A style's product type is its OB's timeSSD Product, held on the BoM.
- The product category stays an accounting tree and gets no IE field (this replaces DEC-24's design, §14).
- Product type is the plateau key (§7.1). IE also uses it to group and report.

### 3.6 SAM versions (FG-27)
- **SAM is a method property in timeSSD**, so IE versions it per method, with effective dates.
- A production record uses its method's version in force on the completion date (spec §5.2, TC-EM-07).
- **Disputes.** A dispute names the OB operation (spec §5.4). If upheld, it resolves into either a new method SAM version, which applies to every style using the method, or a new method code for a style-specific variant. That is the same choice the IE makes in timeSSD.
- **Expected durations.** The BoM operation's `time_cycle_manual` is kept equal to its method's current SAM.
- `mrp_bom_version` (OCA, installed) only marks a BoM usable or not. It does not date SAMs.

### 3.7 QMS overlap (FG-26)
- **Overlap.** timeSSD's product types, parts and machine types are the same vocabularies the QMS catalog was built for. The test catalog on the instance already holds a "Shirt" group with garment parts (quality) and a "Lockstitch" group with machine parts (maintenance), each scoped by profiles.
- **No overlap.** timeSSD has nothing on defect codes.
- **How to share.** Fill QMS object parts from timeSSD's lists and use timeSSD codes as their `ref_code`. IE keeps the same codes in its own small models, because it needs attributes the two-level catalog cannot hold (complexity, the skill switch, product type as the plateau key). Neither suite depends on the other's master data, and the duplication is a few dozen rows.
- **IE does not use parts.** They matter to QMS only, as defect locations.

---

## 4. Function-by-function verdicts (v1 scope, function map v0.8)

| # | Function | Verdict | Basis and gap |
|---|----------|---------|---------------|
| 1.1 | Operation master / library | New | timeSSD methods (§3.2). |
| 1.2 | timeSSD ingestion | Core / OCA | Entered by hand. Standard import (`base_import`) or `excel_import_export` (OCA, installed) if automated later. |
| 1.4 | Difficulty grading | New | The grade on the family (§3.3). The rubric is IE practice; the machine-type factor reads the skill switch (§3.4). |
| 1.6 | Family mapping | New | The family list and the method's family (§3.3). |
| — | Product type (DEC-24) | New | timeSSD Product on the BoM (§3.5). |
| 2.1 | Operation bulletin | Core + Ext | The BoM's operations reference methods (§3.2). Precedence follows §7.2. |
| 2.2 | OB / SAM version control | New | Method SAM versions (§3.6). |
| 2.3 | SAM amendment and dispute records | New (+ OCA option) | A dispute record. Approval could use `base_tier_validation` (OCA, installed): FG-OPEN-08. |
| 4.1 | Line layout / station design | New | Station layout per line, with versions (§7.4). |
| 4.2 | Takt and pitch | New | From the layout, targets and garment SAM. |
| 4.3 | Balance metrics | New | From the layout. |
| 4.4 | Skill-aware allocation | New | Skill matrix × layout. |
| 4.5 | Style changeover and learning curves | New | Production run, familiarity (method codes per line), ramp classes, profiles, fitting. |
| 4.6 | Daily target and headcount | New | System-computed: plateau per line × product type (§7.1) and planned headcount from the layout. |
| 5.1 | Bundle = MO, bundle ticket | Core + MES | Bundles come from the MO split (§5.2). The ticket and barcode belong to MES. |
| 5.2 | Bundle scans | Core + Ext + MES | Work-order time logs fed by scan events (§5.4, §6). |
| 5.5 | Off-standard bucket | New | §5.6 |
| 5.6 | Defect → repair → re-inspection | New | §10.1 |
| 5.7 | Time sources and data quality | Core + New | Attendance as an input (§5.8); exceptions and the nightly job (§5.9). |
| 6.1 | Time accounting engine | New | Attendance plus the off-standard bucket. |
| 6.2 | Earned minutes engine | New | Work orders, method SAM versions and defects. |
| 6.3 | Efficiency metrics | New | M1 to M7. |
| 6.4 | Dynamic skill matrix | New (+ Core option) | Per operator × family (§8.1). |
| 6.5 | Operator tier | New | From the skill matrix; machine classes come from the families' machine types. |
| 6.6 | Calibration and shadow mode | New | A versioned parameter (6.7). |
| 6.7 | Parameter configuration | OCA | `base_time_parameter` (§8.2) |
| 7.1–7.6 | Incentive chain | New | Spec §11, checked against the acceptance cases. |
| 7.7 | Special skill allowance metrics | New | On the period record. |
| 7.8 | Payroll feeder | New | A stored record per operator per period, which payroll pulls (§8.3). |
| 7.9 | Self-funding check | New | The finance cost pool (§9.6). |
| 8.1–8.4, 8.6, 8.8, 8.9 | Analytics | Core | Views over IE's stored figures. Spreadsheet dashboards (core, installed); `mis_builder` (OCA, installed) is optional. |
| 9.1–9.7 | Real-time (RT-1 to RT-7) | New + Core | Candidates computed from production records (§7.3). Live refresh through `bus` (core). RT-3 goes to maintenance (§10.2), RT-4 to MES. |

---

## 5. Execution layer

### 5.1 Mapping

| IE term | Odoo | Verdict |
|---------|------|---------|
| Bundle | `mrp.production`, one per bundle | Core |
| Lot | The procurement group shared by the split MOs (`odoo/addons/mrp/models/mrp_production.py:1878-1938`) | Core |
| Style / OB | Product template, its BoM and the BoM's operations | Core + Ext |
| OB operation | `mrp.routing.workcenter`, referencing a library method | Ext |
| Line of a bundle | A new field on the MO, which sets its work orders' work centre (§5.3) | Ext |
| Production record (operator × operation × bundle) | `mrp.workorder` | Core |
| Quantity credited | Work-order quantity, which is the MO quantity | Core |
| Operator credited | A new field on the work order | Ext |
| Start / pause / finish | `mrp.workcenter.productivity` rows (`time_ids`), written from scan events (§6) | Core |
| Who scanned | A new employee field on each time row; core has only `user_id` (`mrp_workcenter.py:525-527`) | Ext |
| Completion date | Work order `date_finished` (UTC) plus a stored local date (§6.3) | Core + Ext |
| Pause reason | A field on the pause event; it opens an off-standard record | Ext |
| Precedence, station buffer | Work-order dependencies (§7.2) | Core |
| SAM used | The method's SAM version on the completion date (§3.6) | New |
| Production run | BoM (OB) × line, from changeover to the next OB | New |

### 5.2 Bundle MOs
- **Creation.** Core splits an MO into several (`mrp.production.split`, `_split_productions`, `mrp_production.py:1878`). The new MOs share the original's procurement group. OCA `mrp_mass_production_order` (installed) creates many MOs in one step.
- **Split basis.** The planner chooses it: variant, shade (advisory, from the roll inspection), size or anything else. The system sets no maximum bundle size; about 50 pieces is reported.
- **Side records per bundle**, measured in step 5 with 2 components and 20 operations:

  | Record | Per bundle | Source |
  |--------|-----------|--------|
  | Work orders | 20 | one per BoM operation |
  | Calendar leaves | 20 | one per started work order (`mrp_workorder.py:644-655`) |
  | Stock moves, move lines, valuation layers | 3 each | two components and the finished product |
  | Journal entries | 3 (6 journal items) | real-time valuation |
  | Chatter messages, followers | 4.5, 1 | the MO is a `mail.thread` (`mrp_production.py:30`) |

  At about 25,000 bundles a year that is about 75,000 valuation journal entries and 500,000 calendar leaves. Both are small for Postgres.
- **Three-step route (WH Chi Lăng).**
  - Confirming a lot of 200 created **one "Pick Components" picking with 2 moves**.
  - Splitting it into 4 bundles left it at **one picking with 2 moves**, so pickings stay per lot and do not multiply with bundles.
  - The bundles draw their components from WH/Pre-Production.
  - The store step runs when bundles close. The route sample was cancelled before that, so the store step is not measured.
- **Readiness.** A work order is *ready* only when its components are reserved and its predecessors are done (`mrp_workorder.py:155-172`).
  - In step 5, with section dependencies, 240 of 1,600 work orders were ready after confirmation. That is exactly the first operation of each of the three preparation sections in 80 bundles.
  - IE's station buffer (RT-5) is computed from completions and starts, not from Odoo's state.
- **Closing (FG-30).** Marking an MO done runs `quality_control_mrp_oca`'s `_post_inventory`, which reads `qc.trigger.*_line` records as the closing user (`oca/manufacture/quality_control_mrp_oca/models/mrp_production.py:29-55`). A user with manufacturing rights but without Quality Control / User gets an `AccessError`. On this instance that is 5 active users. Step 5 hit it and gave its planner user the group.

### 5.3 Line of a bundle (FG-25)
Work orders take their work centre from the BoM operation (`mrp_production.py:619`). A style's BoM names one line, but a lot may run on any line. So the MO carries the line:
- it is set when the lot is planned;
- the split copies it to the bundles;
- it writes the work centre of the MO's work orders.

The MO's "Update BoM" action resets the work orders' work centres to the BoM's (`_link_bom`, `mrp_production.py:2507, 2570-2571`). IE re-applies the MO's line after it, or that action is not used on bundle MOs. Technical design chooses.

### 5.4 Time logs and scanning
- **Scans** arrive as events (§6). A start opens a time row. A pause closes the open row and records the reason. A finish closes the work order.
- **Combined stations** are scanned one operation after another, so every operator has at most one open work order at any time.
- **Shared station users** fit core's rules:
  - `button_start` skips a work order on which the current user already has an open row (`mrp_workorder.py:616-617`);
  - only one open row per user per work order is allowed (`mrp_workcenter.py:567-575`).

  With one operator per work order this is consistent, and the capture module records the employee on every row.
- **A finished work order cannot be restarted** (`mrp_workorder.py:618-621`). Together with the credited operator, this stops anyone from taking credit for another person's bundle.
- **Harmless side effects:**
  - When a work order closes after running past its expected duration, Odoo splits the time row and labels the excess "Reduced Speed" (`mrp_workcenter.py:588-604`). IE adds both rows together. Fields added to time rows must copy, which ordinary fields do by default.
  - A work order's duration is the sum of all its rows (`mrp_workorder.py:929-938`).
- **Rows nobody scanned (FG-29).** When an MO closes, every work order with a duration of 0 gets its expected duration, written through `_set_duration`, which creates a time row (`mrp_production.py:1836-1842`, `mrp_workorder.py:334-364`).
  - Step 5's instantaneous scans recorded about 0.00 minutes, so roughly 960 of 3,198 rows were invented this way.
  - Real scans take minutes, so this does not happen to them. It does happen to any work order nobody scanned.
  - So IE's bundle time (family split, pace, coverage) counts only rows that carry an employee, i.e. rows the capture module wrote.
- **One shared row per line.** The line's `working_state` is stored on the work centre and recomputed on every time-row change (`mrp_workcenter.py:57-60, 192-210`). Step 5 measured what that means (§13.2):
  - The row is written only when its value changes: from idle to "in progress" when the first open row appears, and back when the last one closes.
  - Simultaneous scans that flip it collide (`could not serialize access`), and Odoo's retry resolves them.
  - On a busy line, scans do not write it and do not collide.
  - Simultaneous finishes can leave it stale ("In Progress" with no open row), because each transaction still sees the others' rows as open. That is cosmetic, and IE never reads `working_state`.

### 5.5 Operator state (FLAG-TECH-07)
An operator's state is derived, not stored separately:
- their current bundle = their open time row;
- whether they are off-standard = an off-standard record covering now.

The capture module checks:
- no second open work order;
- no start or resume during off-standard time;
- starting an off-standard period closes the open row (spec §3.3 rule 2).

### 5.6 Off-standard bucket (FLAG-TECH-10)
**This is a new model, not Odoo's loss rows (FG-05):**
1. An open time row with a non-productive loss marks the whole line *blocked* (`mrp_workcenter.py:192-210`). `button_start` then refuses every work order on that line (`mrp_workorder.py:613-614`). Blocking from a time row also ends every running work order on the line (`button_block`, `mrp_workcenter.py:577-579`).
2. A loss row on a work order counts in its duration (`mrp_workorder.py:929-938`).
3. Loss rows have no multi-operator entry, no approval, no channel and no clipping to attendance.

**One record shape and three channels**, as in spec §3.3:
- **Channel 1:** a pause event with a reason creates a pending record, which the leader approves.
- **Channel 2:** the leader's form, for one operator or several. Line-wide stops such as OS-04 are a channel 2 entry for every operator on the line.
- **Channel 3:** repair records create OS-05 (§10.1).

**Clipping to attendance** (spec §3.3 rule 3, TC-TA-05) runs when attendance is available (§5.8). It reuses core's interval arithmetic: attendance intervals minus calendar lunch (`odoo/addons/hr_attendance/models/hr_attendance.py:220-242`).

### 5.7 Mid-bundle reassignment
Reassignment is a supervisor-only change of the work order's credited operator. The finisher gets the whole bundle (spec §8 rule 3). Work orders are not `mail.thread` (`mrp_workorder.py:14-15`), so the trail comes from `auditlog` (OCA, installed) or a small log model (FG-OPEN-07). The time rows keep who actually scanned and when.

### 5.8 Attendance (FG-21)
- **A (attended minutes)** comes from `hr.attendance` intervals. For employees on a fixed calendar, core subtracts the calendar's lunch (`hr_attendance.py:220-242`).
- **Attendance is an input that IE reads when it computes, not an event it waits for:**
  - Open periods are recomputed whenever attendance arrives or changes. Locking happens only at period close, and closed periods are never reopened (spec §9.3).
  - Each operator-day records whether its attendance has arrived. **Before** it arrives, pieces and earned minutes are live, and time-based figures (NAM, efficiency) are provisional or not shown. **After**, the day is final-able.
  - A monthly import leaves days provisional until close. A daily import firms them up the next day. Neither needs a change in IE.
- **Period close order:** attendance imported → IE period computed (off-standard clipped, exceptions found) → exceptions cleared → period locked → payroll pulls.
- **Identification.** `hr.employee.barcode` (Badge ID, `odoo/addons/hr/models/hr_employee.py:145`) identifies operators at scanning.
- **Time categories** are not needed in v1 (spec §11.5).
- **OPEN-15** stays with the technical design. Option B (bundle time counted only inside attendance) uses the same interval arithmetic as clipping, so its cost does not argue for option A. Under either option, bundle time is final only once attendance has arrived.

### 5.9 Data quality
- **Daily exceptions:** unapproved pauses, bundles still open (the optional nightly pause job, an `ir.cron`), out-of-order or late scan events (§6.2).
- **Exceptions that need attendance** appear when attendance arrives: scans outside attendance, bundles open at clock-out, coverage above 100%. With a monthly import they arrive as a month-end batch.

---

## 6. Capture: scan events and MES working premises

### 6.1 MES working premises (stated by Peter, 2026-10-20)
These are a working premise, not a design. MES gets its own phase.
1. A custom Odoo module serves a PWA at the instance's URL (e.g. `/mes`). It is the shop-floor interface for scanning bundles.
2. Scans go to an Odoo JSON-RPC endpoint and are sent at once. Under normal conditions there is no delay.
3. The PWA may queue events for resilience against network problems and to smooth load. Whether it does is not yet decided.
4. Validation happens in Odoo. Whether MES also validates is for later discussion.
5. MES stays a simple data pipeline.
6. Timestamps need care, because Odoo stores UTC.

### 6.2 Scan events (FG-23)
**The boundary:** MES is the interface and the transport. The capture module receives events, validates them and writes the records. IE calculates.

**An event carries:**
- a client event ID (a UUID);
- the type: start, pause (with reason), resume, finish;
- the work order, or the bundle and operation;
- the operator's badge;
- the device time with its timezone offset.

**Processing rules:**
1. **Applied once.** An event ID already seen is acknowledged and ignored, so a queue can resend safely.
2. **Event time.** An event that arrives promptly takes the server's time. A queued event takes its device time, corrected by the clock difference the PWA learns from each server reply. An event that arrives later than a set limit is flagged (§5.9). This keeps DEC-18's intent of never trusting raw device clocks, even across an outage.
3. **In order.** Events for one operator are applied in order. An out-of-order event (a finish without a start, a start while another bundle is open) is rejected with a reason.
4. **Rejections.** A rejection of a prompt event is shown on the station screen. A rejection of a queued event lands on the leader's exception list.
5. **Validation** is the operator-state checks (§5.5) and the work-order rules (§5.4).

**Testing.** The endpoint stays thin and the logic lives in model methods, tested by `TransactionCase`. This image cannot run `HttpCase` tests (`addons/CLAUDE.md`, *Lessons from building*). The HTTP wiring is checked with `curl`.

**Load.** About 3,500 events a day, with a burst at shift start, is modest. A queue is for resilience, not load.

### 6.3 Local dates (FG-24)
- Odoo stores datetimes in UTC. The factory is at UTC+7.
- So an event before 07:00 local falls on the previous UTC day, and the first seven hours of a month fall in the previous UTC month.
- Spec §8 rule 5 (completion date = finish date), the daily figures, ramp days and pay periods must all use the **local** date.
- Each production record therefore stores its local completion date when it is written, computed with the factory's calendar timezone (Asia/Ho_Chi_Minh). Every IE date grouping uses that field. Core attendance does the equivalent through the calendar's timezone (`hr_attendance.py:231`).

---

## 7. Line engineering, targets and planning

### 7.1 Plateau and system-computed targets (FG-19)
- **System-computed targets stay.** The plateau feeds the daily target, the takt check (max station load), the hourly target, the station planned output and the line-progress curve. It never touches pay: the incentive uses r(d) only (spec §7.7.4).
- **The plateau is computed, not maintained.** It is the median run plateau of recent runs per line × product type (spec §7.7.4). A starting value per product type, a versioned parameter, applies until history exists.

### 7.2 Precedence from sections (FG-20)
Garment operations run in parallel: a bundle's collar, cuffs, front placket, pocket and sleeve parts are prepared at separate stations at the same time and joined in assembly. Unless a BoM has operation dependencies switched on (`allow_operation_dependencies`, `blocked_by_operation_ids`, `mrp_routing.py:53-62`), Odoo chains work orders strictly one after another (`mrp_production.py:1590-1596`).

**Default rule when an OB is built:**
1. Within a section, operations run in workflow line order.
2. Preparation sections run in parallel.
3. The first assembly operation waits for the last operation of every preparation section.
4. The first finishing operation waits for the last assembly operation.

The section's stage (§3.2) says which is which; the IE sets it once per section. The IE then edits any exceptions directly on the BoM's operations. Pay does not depend on precedence; routing, readiness and RT-5/6 do.

### 7.3 Real-time candidates (FG-22)
- Real-time figures come from production records and the layout: line progress against target, balance, pace, buffers and bottleneck.
- **"Operators active"** = operators with a scan on the line today. It replaces "operators present" in the hourly target, so real-time needs no attendance.
- RT-1 to RT-7 are candidates. Which ones are built follows their value once the data runs.

### 7.4 Layout and planning
- **Station layout** (4.1) is a new model with versions: operations and operators per station, the machine at each position, and the planned headcount. Neither CE nor OCA links maintenance equipment to work centres (`mrp_maintenance` is not part of CE), so the layout holds the machine link that RT-3 and "OS-01 minutes per machine" use.
- **Planning visuals (FG-14).** The core MO calendar (`odoo/addons/mrp/views/mrp_production_views.xml:601`) works at lot level. A work-order calendar coloured by work centre also exists (`odoo/addons/mrp/views/mrp_workorder_views.xml:314`). A production-run view (style × line × dates) comes later; IE needs the production run anyway for the ramp calendar (FLAG-TECH-09).

---

## 8. Skill, parameters and payroll

### 8.1 Skill matrix
- ILUO levels are kept per operator × family (§3.3), with warnings, downgrade grace, dormancy and history, in IE's own model.
- Families on machine types switched off (§3.4) get no level and no proficiency factor, and do not count towards tiers. They still take their share of time (spec §10.1).
- Core `hr_skills` (installed) has employee skills with a log (`hr.employee.skill`, `hr.employee.skill.log`), and the existing salary rules already read `hr.employee.skill`. Whether IE copies its levels into it is FG-OPEN-05.

### 8.2 Parameters (DEC-21, FLAG-TECH-12)
OCA `base_time_parameter` (server-tools, available, not installed) provides:
- parameters with a code and a type (float, integer, boolean, date, JSON, record, text);
- versions with a start date;
- lookup of the version in force on a date (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:84-95`).

OCA payroll uses the same mechanism (`payroll_rule_time_parameter`). Ramp profiles and PF tables fit its JSON type.

Two quirks to handle in technical design (FG-OPEN-09):
- a stored falsy value (0, 0.0, False) reads back as "no value" (`base_time_parameter.py:72-73`);
- `get_time_parameter` never raises when a value is missing (`models/base.py:22`).

So IE reads parameters through one helper of its own.

### 8.3 Payroll feeder (FG-09)
IE stores one record per operator per period, holding the fields of spec §12 and TC-PAY-01. It is locked at period close (§5.8) and carries the shadow/live flag. Payroll's salary rules read it. Pay and evaluation periods could use `date_range` (OCA, installed): FG-OPEN-06.

---

## 9. Costing and inventory valuation (FLAG-TECH-01)

### 9.1 How CE 18 values a manufactured product
1. **At MO done**, the finished goods' unit cost = (value of components consumed + work-order cost + *Extra Unit Cost* × quantity) ÷ quantity (`odoo/addons/mrp_account/models/mrp_production.py:40-63`). Under average cost it blends into the product's cost, and from there into COGS and margin.
2. **Work-order cost** = logged time × the work centre's `costs_hour` (`odoo/addons/mrp/models/mrp_workorder.py:597-610`). At MO done, a work order with no logged time first gets its expected duration (`mrp_production.py:1836-1842`).
3. **Extra Unit Cost** (`extra_cost`) is a flat amount per finished unit on the MO. Splitting copies it (`mrp_account/models/mrp_production.py:67-69`).
4. **Journal entries** are posted under real-time valuation only (`odoo/addons/stock_account/models/stock_valuation_layer.py:86`):
   - components: debit the production account, credit component stock;
   - finished goods: debit stock, credit the production account (`mrp_account/models/stock_move.py:26-34`).

   The conversion cost absorbed this way stays as a credit on the production account (`mrp_account/models/product.py:126-130`). It is cleared against actual wages and overhead, and what remains is the variance.

### 9.2 The choice
Valuation happens at MO done, continuously. The actual conversion cost is known only at payroll close, monthly. So valuation needs a rate fixed in advance, and the variance lands in the period's P&L. The question is which minutes the rate multiplies:

| Option | Mechanism | Finished goods carry | Effect on the premise |
|--------|-----------|----------------------|-----------------------|
| A. None | No hourly cost, no extra cost | Materials only | None |
| B. Scanned minutes | `costs_hour` = an operator-hour rate, scans on work orders | Scan time × rate | **Ties valuation to scanning** |
| C. Standard minutes | `costs_hour` = 0; *Extra Unit Cost* = garment SAM × rate | Materials + standard conversion cost | None |

**Why B fails:**
- A bundle left open overnight reaches stock value before the data-quality review, and cannot be corrected once it has blended into average cost.
- A slow bundle becomes a more expensive garment.
- The amount absorbed moves with scanning discipline.

### 9.3 Decision (FG-06): option C
The amount absorbed is Σ quantity × SAM × rate = **gross earned minutes × rate**. For a given rate, accounting's variance moves with M3. Accounting standards generally expect conversion costs in inventory, with abnormal waste expensed (IAS 2 §12–16; VAS 02 follows IAS 2 on conversion costs). The accountant confirms the position.

### 9.4 Rate basis (FG-07)
```
100% basis      rate = conversion cost ÷ attended minutes              (= CPM, spec §6.1)
measured basis  rate = conversion cost ÷ gross earned minutes          (= CPM ÷ M3, trailing window)
absorbed        = EM_g × rate
variance        = actual conversion cost − absorbed
```
Conversion cost = direct labour + production overhead.

*Worked numbers* use the rationale's Line 1: CPM 1,041.67 VND, 374,400 attended minutes, conversion cost 390.0M VND a month. Both months assume the same conversion cost.

| Month | EM_g (M3) | 100% basis: absorbed / variance | Measured basis (1,494.25 VND per EM): absorbed / variance |
|-------|-----------|----------------------------------|-------------------------------------------------------------|
| Normal | 261,000 (69.7%) | 271.9M / **118.1M unfavourable** | 390.0M / **0** |
| Better | 285,000 (76.1%) | 296.9M / **93.1M unfavourable** | 425.9M / **35.9M favourable** |

**Recommendation: the measured basis.**
- No efficiency figure is assumed. The settings are the window (e.g. 3 to 6 months) and the revision frequency (e.g. quarterly).
- Inventory and product margin carry the normal cost. On the 100% basis, inventory misses about 30% of conversion cost in this example.
- The variance is near zero in a normal month, and its sign says whether the month beat normal efficiency.
- It matches IAS 2 §21: standard costs reflect normal levels of efficiency and are reviewed regularly.
- Pay is unaffected (DEC-08).

**Implications:**
- Periods heavy with changeovers raise the rate for later production. A longer window smooths this.
- Pricing an individual order at its real cost stays with the costing stream.

**Bootstrap.** Shadow-mode data gives the first measured rate. Until then, finance's current figure or the 100% basis applies.

### 9.5 Rate ownership (FG-07)
- **Finance** sets and approves the rate as a versioned parameter with an effective date (§8.2), editable by accounting managers.
- **IE** owns the minutes (EM_g, garment SAM) and shows the trailing cost per earned minute next to the rate in force.

### 9.6 Cost inputs (FG-12)
Finance enters one cost pool per period: direct labour (base wages, incentive paid, allowances) plus production overhead. It feeds:
- the suggested valuation rate;
- the self-funding check (spec §11.8), which uses the labour part only.

A bridge reading payslip totals can come later.

### 9.7 Mechanism
- At MO done, the bundle MO's *Extra Unit Cost* = sewing garment SAM (method SAM versions in force on the completion date) × the rate in force. Technical design chooses the hook.
- Cutting MOs keep their treatment until their standards exist (OPEN-07).
- Only the rate moves into v1. The costing stream stays deferred.

---

## 10. Quality, maintenance and notifications

### 10.1 Defects, repair, re-inspection (FG-08)
- **The defect record is new.** It holds:
  - the work order, which gives bundle, operation and credited operator;
  - the defect code (`qms.defect.code`, from `qms_catalog`);
  - defective quantity, detection point, responsibility, detection date and inspector.
- **Defects not traceable to an operation** are attributed to the line (spec §9.2).
- **FLAG-TECH-13** becomes a check on this one model: the cumulative defective quantity per work order may not exceed the work-order quantity. A record that would exceed it is rejected with an error.
- **A repair record** creates OS-05 through channel 3. **Re-inspection** is a state on the defect.
- **Capture is in MES.** The dependency on `qms_catalog` brings in `product` and `mgmtsystem`, both installed.
- **Formal inspections stay in QMS** (`quality_control_oca` and the QMS suite).

### 10.2 Breakdown call (RT-3, FG-13)
- A pause with reason OS-01 opens a corrective `maintenance.request` (core). It names the machine from the layout, plus the operator and the time. The PMS suite (SLA, priority matrix) applies as to any corrective request.
- **It must be created with sufficient rights:**
  - the request's owner defaults to its creator (`odoo/addons/maintenance/models/maintenance.py:249`);
  - `hr_maintenance` recomputes the owner from the request's employee and empties it when there is none (`odoo/addons/hr_maintenance/models/equipment.py:88-97`);
  - the own-requests rule requires owner, follower or Responsible (`odoo/addons/maintenance/security/maintenance.xml:18`).
- A bridge module holds this, so the IE core has no maintenance dependency.

### 10.3 Notifications and refresh
- **Live figures** use `bus` (core). Periodic figures use scheduled actions.
- **Alerts and breakdown calls** go out as activities or notifications. `zalo_oa` (own, installed) is an optional channel.

---

## 11. Integration: the roadmap's key gaps answered

| Partner | Answer |
|---------|--------|
| timeSSD | Its export shape is the master-data shape (§3). Data is entered by hand; automated import via OCA if wanted. |
| Quality | The QMS suite exists. IE keeps its own defect record coded from `qms_catalog` (§10.1). Object parts align with timeSSD codes (§3.7). |
| Payroll | OCA `payroll` pulls IE's period records through salary rules (§8.3). |
| Maintenance / CMMS | Core maintenance plus the PMS suite. RT-3 goes through a bridge module (§10.2). The machine link lives in the layout (§7.4). |
| HR / Attendance | The biometric pipeline into `hr.attendance`, read as an input, monthly or daily (§5.8). |
| Product master | Product type from the OB (§3.5). Product categories stay accounting's. |
| MES interface | Scan events into the capture module (§6). MES displays IE's figures (RT-4). |
| Sales / costing | Later, with the costing stream. The valuation rate is the exception (§9). |

---

## 12. Preliminary module shape (input to step 7)

| Layer | Content | Depends on |
|-------|---------|------------|
| IE master data | Product types, sections (with stage), machine types (with the skill switch), methods (with family and SAM versions), families, the BoM-operation link to methods, product type on the BoM, the parameter helper | `mrp`, `base_time_parameter` |
| Capture (shared by MES and IE) | The scan-event endpoint and model, credited operator, employee on time rows, pause reason, operator-state checks, the line on the MO, the local completion date | `mrp`, `hr`, IE master data |
| Off-standard and time accounting | The bucket and its three channels, attendance handling and clipping, A / OS / NAM, data-quality exceptions | Capture, `hr_attendance` |
| Defects and repair | Defect and repair records, re-inspection state | Capture, `qms_catalog` |
| Metrics and skill | The daily production table (operator × day × family), earned minutes, the metric family, skill matrix, tiers | The layers above |
| Incentive and period record | PF, ramp-adjusted threshold, excess, units, the payroll period record, shadow mode | Metrics and skill |
| Valuation | Extra Unit Cost at MO done, the rate parameter, the cost pool | IE master data, `mrp_account` |
| Line engineering | Station layout, precedence from sections, balancing, plateau and targets, changeover and ramp-up | IE master data |
| Real-time | RT candidates | Metrics, line engineering |
| Bridge: maintenance | RT-3 | Capture, `maintenance` |

**Insurance on the premise.** IE's calculations read the daily production table, not work orders directly. If the premise (FG-02) ever changes, only the table's builder changes.

**Build order.** Shadow mode needs master data, capture, time accounting, metrics and skill. The incentive layer comes last. MES needs at least a minimal scanning path before shadow mode can start.

Module names and prefixes are FG-OPEN-03.

---

## 13. Step 5 prototype: plan, results and viability gate

### 13.1 Plan

**Goal:** prove the premise (FG-02) at the reported volume before the technical design is written.

**Sizing (reported, §1):**

| | Per day | Per month (26 days) | Per year |
|---|---|---|---|
| Bundle MOs (4,000 garments ÷ 50) | 80 | ≈ 2,100 | ≈ 25,000 |
| Work orders (15–25 operations) | 1,200 – 2,000 | ≈ 42,000 | ≈ 500,000 |
| Time rows (≈ 2 per work order) | ≈ 3,200 | ≈ 84,000 | ≈ 1,000,000 |
| Scan events | ≈ 3,500 | | |

About 125 operators, each scanning every 15 to 20 minutes, with a burst of up to about 125 starts at shift start, about 25 per line.

**Setup, as run** (`Odoo-Build/ie-prototype/`, through `odoo shell`):
1. **Backup.** A database backup was taken first (FG-15).
2. **Test records**, all named `IE-PROTO …`, in the garment company and WH Chi Lăng:
   - five line work centres per R1 and R2;
   - one shirt style whose BoM has 20 operations (garment SAM 10.05) with dependencies built by the §7.2 rule (19 links);
   - two components (cut panels in WIP, thread in Raw Materials);
   - a station user (Manufacturing / User) and a planner user (Manufacturing / Administrator, plus Quality Control / User, FG-30).
3. **Lots and bundles.** The planner creates lot MOs of 4 bundles × 50, confirms them, splits them with core's `_split_productions`, and sets each lot's line on its work orders (FG-25). The Extra Unit Cost is set on the lot: SAM × 1,494.25 = 15,017.21 per unit.
   - The measured bundles take components from WH/Stock and deliver to it, so unvalidated picking transfers cannot hold them up.
   - One extra lot per day run goes through the warehouse's own three-step route, unscanned, and is then cancelled.
4. **Scanning.** The station user calls the core work-order methods (`button_start`, `button_pending`, `button_finish`) directly, each committed like a request.
   - About 10% of work orders are paused and resumed once.
   - About 30% are backdated past their expected time, so Odoo creates "Reduced Speed" rows.
   - The capture layer does not exist yet, so the scan costs are a lower bound.
5. **Burst.** Parallel database sessions run in separate `odoo shell` processes (`burst.sh`), synchronised to a common start time and using Odoo's own retry wrapper (`odoo.service.model.retrying`). There were two runs: 2 processes × 12 threads on an idle line, then 4 × 6 on a busy one. `db_maxconn = 16` caps threads per process.

| # | Scenario | Measured | Pass criterion `[P]` |
|---|----------|----------|----------------------|
| P-01 | Split a day's lots into 80 bundle MOs | Time; records created | ≤ 1 min per 100 bundle MOs |
| P-02 | Confirm bundle MOs | Time; work orders, dependencies, reservation | ≤ 1 min per 100 MOs; work orders become *ready* as predecessors finish |
| P-03 | Scan a day sequentially: start, finish, some pauses | Time per call; time rows created (including "Reduced Speed" splits) | ≤ 1 s per scan |
| P-04 | Concurrent scanning: 25 parallel database sessions on one line, then 125 across five lines, in a shift-start burst | Latency; serialization retries; errors (the `working_state` row, §5.4) | ≤ 1 s at the 95th percentile, no errors that a user would see |
| P-05 | Mark bundle MOs done with real-time valuation and Extra Unit Cost | Time per MO; journal entries per bundle; value booked | ≤ 2 s per MO, or a day's bundles closed by a batch job within 15 min; value = materials + SAM × rate exactly |
| P-06 | Side records per bundle | Stock moves, valuation layers, journal entries, calendar leaves, time rows, chatter messages | Counted; Peter and accounting accept the totals |
| P-07 | Views with a year of data (≈ 25,000 MOs, 500,000 work orders) | MO and work-order list, kanban and calendar load times | ≤ 3 s |
| P-08 | IE aggregation | The daily production table for a month; defect attribution through the work order | ≤ 30 s for a month |

P-04 uses database sessions directly, so the result does not depend on this instance's two HTTP workers. The workers needed for the burst then follow from the measured cost per scan.

**Fallbacks prepared in advance** (none was needed):
- closing in a batch job outside shifts;
- an override of the work centre's stored state;
- periodic valuation for WIP (`stock_valuation_layer.py:86`);
- the fallback premise (§2.2).

### 13.2 Results (2026-10-21)

| # | Result | Criterion | Verdict |
|---|--------|-----------|---------|
| P-01 | Split: 2.8 s per lot of 4 bundles (0.7 s per bundle, about 70 s per 100). Setting the line: 1.3 s per lot. | ≤ 1 min per 100 | **Narrow miss**; operationally negligible (a day's 80 bundles take under 2 minutes of planning in all) |
| P-02 | Create 0.6 s and confirm 0.55 s per lot. After confirmation 240 of 1,600 work orders were *ready* and 1,360 *pending*, which is exactly the dependency rule (§5.2). Splitting copied the Extra Unit Cost to every bundle. | ≤ 1 min per 100; ready as predecessors finish | **Pass** |
| P-03 | 3,528 scans: mean 119 ms, p95 177 ms, max 1.6 s. Start mean 156 ms / p95 472 ms (a bundle's first start also starts its MO). Finish 99 ms, pause 26 ms, resume 50 ms. | ≤ 1 s per scan | **Pass** |
| P-04 cold | 24 simultaneous starts on an idle line (2 × 12). All succeeded. 23 hit `could not serialize access`, all on the line's `working_state` update, and each succeeded on its first retry. Start latency about 25–28 s. Finishes 1.2–1.5 s with no retries. No errors. | ≤ 1 s at p95; no user-visible errors | **No errors: pass.** Latency: see below |
| P-04 warm | The same on a busy line (4 × 6): **0 collisions, 0 retries, 0 errors.** Starts a uniform 11.7–12.3 s, finishes 0.9–1.2 s. | as above | **No errors: pass.** Latency: see below |
| P-05 | 80 of 80 closed: mean 1.5 s, p95 1.9 s, max 3.2 s. Value check exact to rounding (max difference 0.5 VND), work-centre cost 0. Sample bundle: components 1,075,000 + extra cost 750,860.5 = finished value 1,825,861 VND. | ≤ 2 s per MO; value exact | **Pass** (requires FG-30) |
| P-06 | Counted (table in §5.2). One component picking per lot in the three-step route. | Counted; accepted | **Counted**; acceptance goes with V3 |
| P-07, P-08 | Not run. These are the lowest-risk scenarios: Odoo paginates lists and indexes their keys, and the daily production table is IE's own query, better tuned later against real data. The harness phases `bulk` and `read` remain available. | | Deferred |

**Reading the burst latency.** The 12 to 28 seconds come from the test conditions, not from locking:
- **No lock waits in the warm run.** It had no collisions, yet every thread finished at almost the same moment. That is the signature of shared processing time, not of waiting for a lock.
- **Threads share one interpreter.** Within one `odoo shell` process, the threads' Python work runs one at a time, so each process's latency grows with its thread count.
- **Fresh processes, heaviest scans.** The processes had just started, so every thread paid its first-call costs at once. And every burst scan was a bundle's first scan, the heavier kind (about 0.5 s on its own in P-03).
- **Comparison.** Cutting the threads per process from 12 to 6 and removing the collision brought the latency from about 27 s to about 12 s.

Production workers are long-running processes. With `workers = 2`, at most two scans run at the same time and the rest queue behind them. The latency an operator actually sees is therefore measured over HTTP during the scanning spike (V5, FG-OPEN-15).

**The collision is narrow.** It happens only when the line flips between idle and busy (§5.4): at shift start, and after a break in which every open row was closed. Odoo's retry absorbs it: 24 simultaneous starts needed one retry each. The MES queue (§6.1) can smooth that moment if it ever matters.

### 13.3 Viability gate

| # | Condition | Status |
|---|-----------|--------|
| V1 | Step 5 passes: volume and concurrency | **Pass** (FG-28). The latency over HTTP is measured in V5 |
| V2 | The master-data shape is confirmed | **Done** (§3) |
| V3 | The accountant accepts option C, the rate basis, and about 3 journal entries per bundle | Open (FG-OPEN-01) |
| V4 | The planners accept manual line loading on the MO calendar for v1 | Open (FG-OPEN-16) |
| V5 | A minimal scanning path is proven: badge, bundle ticket, start, pause with reason, finish, with scan latency measured over HTTP | Open (MES phase, FG-OPEN-12, FG-OPEN-15) |

**Recommendation (Proposed):** start the technical design now, and run V3 to V5 alongside it.
- The premise is no longer at risk.
- Each remaining condition is confined to one module (valuation, planning scope, capture), and none can overturn the premise the way V1 could have.

---

## 14. Consequences for the business documents (proposals, not applied)

Each item goes through the document workflow (function map, *Document set & workflow*).

**Spec**
1. **§6, scope note, and §6.6.** v1 carries a standard conversion cost into inventory (§9). FLAG-TECH-01 is resolved in principle.
2. **DEC-04, §8 rule 1.** Bundle = MO is confirmed as the premise. The split basis (variant, shade, size) is the planner's choice, not a system rule. Bundle size is a planning parameter with no system maximum.
3. **§8 rule 3.** Reassignment is a supervisor change of the work order's credited operator.
4. **§8 rule 5.** The completion date is the local factory date (FG-24).
5. **§2, §5.1.** Library operation code = timeSSD method code. SAM = TST × allowance, set in timeSSD. The OB = the timeSSD workflow. SAM versions are kept per method (FG-27). The element breakdowns stay in timeSSD.
6. **DEC-24.** Product type is the timeSSD Product of the style's OB, not a field on the product category (FG-19).
7. **DEC-12, §5.6, §10.1.** The skill-evaluated flag sits on the machine type and defaults from timeSSD complexity (Semiautomat and Automat = not skill-evaluated). Families inherit it. A family's methods share one machine type (FG-17, FG-18).
8. **§3.3, channel 1.** The pause reason arrives with the MES pause event.
9. **§3.4 and DEC-18.** Attendance is read when available, and the attendance-based exceptions appear when it arrives. Queued scan events take the device time corrected by the learned clock offset, and late events are flagged (§6.2).
10. **§7.5, §13.2.** The hourly target uses operators active (from scans). The daily target uses planned headcount from the layout. The RT features are candidates (FG-22).
11. **§11.1.** Daily time-based figures are provisional until attendance arrives (§5.8).
12. **§11.8 and §12.** The self-funding check takes its labour cost from the finance cost pool. Payroll pulls IE's figures.
13. **§10.4, dormancy.** It does not say whether a further 180 days without volume drops another level.
14. **§15.** Update the FLAG-TECH statuses (table below).

**Rationale**

15. **§8.4.** It says defects are "capped at the bundle quantity". Since spec v0.6 the record is rejected, and the cap is on pieces, not DD minutes.

**Function map**

16. **1.1, 1.2, 1.4, 1.6, 2.1, 2.2** follow §3. **6.7** uses the OCA parameter module, **7.9** the cost pool, **9.x** the candidates of §7.3.

**Roadmap**

17. **Step 3.** "CE has no Quality module and no Payroll module" is out of date for this instance.
18. **Step 4** was largely answered on 2026-10-20 (§1).
19. **Steps 5 and 8.** The development environment exists: this instance, a test copy restored from production.
20. **Step 5** was run on 2026-10-21 and the premise holds (§13). The shop-floor scanning and pausing experience, also named in step 5, moves to the MES scanning spike (V5).
21. **Step 6** (technical design) can start with V3 to V5 still open (§13.3, Proposed).

**Acceptance test cases**

22. **Fixture F1** machine classes map onto timeSSD codes (e.g. SNLS → LOCK1, overlock → OVL3/OVL4, buttonhole → BHM). The expected values are unchanged.

**FLAG-TECH status after the fit-gap**

| Flag | Status |
|------|--------|
| 01 Work centre study | Resolved in principle: two layers (§2), costing C (§9) |
| 02 MO grouping | Lot = the split's procurement group; OB = BoM; production run = BoM × line, a new IE record |
| 03 Family time from scans | Time rows give bundle time; only rows from scans count, because Odoo invents rows for unscanned work orders at close (FG-29) |
| 04 Bundles across days | The local completion date (§6.3) |
| 05 SAM version referencing | Method SAM versions on the completion date (§3.6) |
| 06 Data model approach | Resolved: work orders as production records, IE models beside them, a daily production table between them (§12) |
| 07 Operator state | Derived from open time rows and off-standard records; enforced in capture (§5.5) |
| 08 Library codes | timeSSD method codes on BoM operations; history per line × code from work orders |
| 09 Ramp calendar | Technical design (production run, §7.4) |
| 10 Off-standard bucket | New model, three channels, not loss rows (§5.6) |
| 11 Real-time implementation | Partly set: `bus`, scan events, the RT-3 bridge, the layout; the MES feed format comes later |
| 12 Parameter configuration | OCA `base_time_parameter` (§8.2) |
| 13 Defect quantity validation | A check per work order on the defect model (§10.1) |
| 14 Leeway mechanism | Technical design; PF counts per family (§3.3) |

---

## 15. Open items

| ID | Item |
|----|------|
| FG-OPEN-01 | Rate basis and owner: confirm with the accountant, including the VAS 02 position. |
| FG-OPEN-03 | Module names and prefixes for the IE and MES suites, including the shared capture module. |
| FG-OPEN-05 | Whether ILUO levels are copied into `hr_skills` (technical design). |
| FG-OPEN-06 | Pay and evaluation periods on `date_range` or IE's own (technical design). |
| FG-OPEN-07 | Reassignment trail: `auditlog` or IE's own log (technical design). |
| FG-OPEN-08 | Dispute approval: `base_tier_validation` or a plain two-step state (technical design). |
| FG-OPEN-09 | `base_time_parameter` quirks: IE's own helper (technical design). |
| FG-OPEN-10 | The IE data to enter once: the family list with grades, each method's family, each section's stage, each machine type's skill switch. This is data, not design. |
| FG-OPEN-11 | Whether daily time-based figures are shown provisionally before attendance arrives (§5.8). |
| FG-OPEN-12 | MES phase: whether the PWA queues, whether MES validates too, the late-event limit, the event format (§6). |
| FG-OPEN-13 | The MO "Update BoM" action on bundle MOs: re-apply the line, or do not use it (§5.3). |
| FG-OPEN-14 | Closing MOs needs Quality Control / User (FG-30): give that group to whoever closes bundle MOs (role design), or read the trigger lines with elevated rights in an additive override in the QMS bridge. It affects 5 active users today, independently of IE. |
| FG-OPEN-15 | Scan latency as an operator sees it, over HTTP with long-running workers, measured in the MES scanning spike (V5). That includes the shift-start wave with this server's `workers = 2` (§13.2). |
| FG-OPEN-16 | Planners accept manual line loading on the MO calendar for v1 (V4, §2.2). |
| OPEN-15 | Stays with the technical design; option B costs no more than option A (§5.8). |

Closed since v0.1:
- **FG-OPEN-02** (volume): reported figures, §1.
- **FG-OPEN-04** (shade source): shade is advisory and IE does not key on it, §5.2.

The prototype's `IE-PROTO` records remain on the instance until the pre-prototype backup is restored.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-19 | First version: two-layer finding and bypass; work order = production record, MO = bundle; line rules; execution-layer mapping; off-standard bucket as its own model; costing option C; function verdicts; integration answers; module shape; prototype plan; document proposals; open items. |
| 0.2 | 2026-10-20 | Master data follows timeSSD (§3): products, sections with stage, machines with a skill switch, methods with family and SAM versions; family list as IE's one addition; product type from the OB; QMS alignment by codes. Precedence from sections (§7.2). Attendance as an input, monthly or daily (§5.8). Real-time from production records, operators active from scans (§7.3). Scan events, MES working premises and local dates (§6). Line of a bundle on the MO (§5.3). Reported volume, prototype resized, viability gate (§13). Decisions FG-16 to FG-27; proposals and open items updated. Instance figures used where they help. |
| 0.3 | 2026-10-21 | The step 5 prototype was run, and its results are recorded (§13.2). The premise is confirmed and V1 passes (FG-28). Findings: Odoo invents time rows for unscanned work orders at close, so IE reads scan rows only (FG-29); closing MOs needs Quality Control / User (FG-30); the line's state collides only when it flips between idle and busy, and can go stale (§5.4). The three-step route keeps one picking per lot, and IE runs in the garment company (FG-31). Side records per bundle measured (§5.2). Two companies and server figures added (§1). Viability gate status, with a recommendation to start the technical design (§13.3). Open items FG-OPEN-14 to 16 added. |
