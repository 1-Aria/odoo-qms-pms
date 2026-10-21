# IE Module — Technical Design

**Version:** v0.3 (draft) · 2026-10-21 · **chunks 1–2 of 4: foundations, time and quality**
**Supersedes:**
- `IE_Technical_Design_v0.2.md` (chunks 1–2);
- `IE_Design_Note_Single_Scan_v0.1.md`, which this version folds in, as refined in discussion on 2026-10-21.

Both are kept as history.

**Roadmap step:** 6 (technical design)

**Based on:**
- `IE_Business_Logic_Spec_v0.6.md` (the rules of record) and `IE_Framework_Rationale_v0.6.md`;
- `IE_Module_Function_Map.md` (v0.8) and `IE_Acceptance_Test_Cases_v0.3.md`;
- `IE_Fit_Gap_v0.3.md`, whose decisions (FG-xx) this document builds on;
- Peter's decisions of 2026-10-21 on single-scan capture, off-standard time, repair and removal (TD-27 to TD-36);
- the Odoo CE 18 core and OCA repositories the instance runs, read 2026-10-21.

**Purpose:** The models, fields, relations, rules and computations that implement the spec on Odoo, module by module. It contains no code. The code-level specification of each module comes later in `docs/modules/<module>.md`, when that module is built.

Where this design departs from the business documents, §12 lists the change as a proposal for the document workflow.

| Chunk | Content | Status |
|-------|---------|--------|
| **1. Foundations** | Conventions, module map, master data, capture, production records | **This version** (capture rewritten for single scan) |
| **2. Time and quality** | Off-standard grants, attendance and time accounting, data-quality exceptions, defects and repair | **This version** (rewritten) |
| 3. Metrics and pay | Metric family, skill matrix, tiers, PF, thresholds and ramp-up, period record, payroll fields, shadow mode, self-funding | To do |
| 4. The rest | Valuation, line engineering and targets, real-time, parameter catalogue, security summary, computation schedule, test strategy | To do |

**Conventions:**
- Status labels as in the fit-gap: **Agreed** (confirmed by Peter, with date), **Proposed** (designed here, not yet confirmed), **Superseded** or **Withdrawn** (kept for traceability), **Open** (§11).
- Source references are `path:line` relative to `Odoo-Build/`.

---

## 0. Decisions

| ID | Decision | Status |
|----|----------|--------|
| TD-01 | **Naming.** IE modules `ie_*`, models `ie.*`, fields on core and OCA models `ie_*`. MES modules `mes_*`, models `mes.*`, fields `mes_*`. The capture layer shared with MES is `mes_capture`. Closes FG-OPEN-03. | Agreed 2026-10-21 |
| TD-02 | **Periods are IE's own `ie.period`:** a month, with a state (open or closed) and a mode (shadow or live). Closes FG-OPEN-06. | Agreed 2026-10-21 |
| TD-03 | **Roles.** IE has four groups: User, Line leader, Engineer, Manager (§3.11). MES has two: Station and Supervisor (§4.7). The Supervisor group edits the credited worker (TD-30). Valuation rights are set in chunk 4. | IE groups Agreed 2026-10-21; Supervisor permission Agreed 2026-10-21; MES group names Proposed |
| TD-04 | **Computation cadence.** Production records are built incrementally by a scheduled job and rebuilt at close. Period figures are computed on demand while the period is open, and frozen at close. Real-time figures are computed live and never stored. | Agreed 2026-10-21 |
| TD-05 | **The insurance layer is a production record per credit** (`ie.production.record`, §5): one per credited work order, and one per passed repair. It is IE's denormalised, versioned copy of each credit. Every IE calculation reads it, never `mrp.workorder` directly. It is built by a scheduled job from capture's fields, never inside a scan, so an IE fault can never refuse a scan. | Proposed (revised v0.3) |
| TD-06 | **The capture journal records scans only** (`mes.scan.event`, §4.3). It gives idempotency, ordering and refusals in one place. Changes to the credited worker are tracked in the MO's chatter instead (TD-30). Closes FG-OPEN-07. | Proposed (revised v0.3) |
| TD-07 | ~~Stop reasons live in capture (`mes.stop.reason`).~~ Capture no longer pauses, so the codes move to IE as `ie.offstandard.code` (§6.1, TD-31). | Superseded by TD-31 |
| TD-08 | **Event time.** An event that arrives promptly takes the server time. A queued event takes its device time, corrected by the clock offset the PWA learned. Late events are flagged on the journal (§4.4). | Proposed |
| TD-09 | ~~Operator-state checks run in capture, with a hook that IE extends for off-standard time.~~ The scan rules (TD-27) are the only checks. Off-standard time has no clock time, so there is nothing to check against. | Superseded by TD-27 |
| TD-10 | **The line on the MO is set in capture** (`mes_line_id`). It is re-applied after "Update BoM". Closes FG-OPEN-13. | Proposed |
| TD-11 | **The credit date** is the local date of the credit: the scan, or the moment a supervisor set the worker by hand. It is stored on the work order in the company calendar's timezone (§4.2). It replaces the completion date (spec §8 rule 5). | Agreed 2026-10-21 |
| TD-12 | **SAM versions per method.** BoM operation times follow the current version. A production record uses the version in force on its credit date. A retroactive version rebuilds the production records of open periods only (§3.6). | Proposed |
| TD-13 | **A parameter helper over OCA `base_time_parameter`.** It reads versions explicitly, so 0 and False are real values and a missing value raises. Closes FG-OPEN-09. | Proposed |
| TD-14 | **Badges are resolved with elevated rights.** `hr.employee.barcode` is readable by HR officers only (`odoo/addons/hr/models/hr_employee.py:145`). | Proposed |
| TD-15 | ~~One off-standard record per operator, with a batch reference.~~ Grants are per worker by nature (TD-31). The multi-worker form simply creates one grant per worker (§6.4). | Superseded by TD-31 |
| TD-16 | ~~Approval by channel.~~ Every grant counts as approved when it is entered. | Withdrawn 2026-10-21 |
| TD-17 | ~~A pause's off-standard period ends at the operator's next scan.~~ There are no pauses. | Withdrawn 2026-10-21 |
| TD-18 | ~~No overlaps with other records or bundle time.~~ Grants have no clock time, so nothing can overlap. | Withdrawn 2026-10-21 |
| TD-19 | **Time accounting per operator-day** (`ie.operator.day`): A, OS by code, NAM, planned minutes and bundle minutes. It is rebuilt by a scheduled job from whatever changed (§7). | Proposed (revised v0.3) |
| TD-20 | **Attendance completeness is a date on the period** (`attendance_through`). It is set after each import, so monthly and daily imports work the same way (§7.4, FG-21). | Proposed |
| TD-21 | **OPEN-15: option B.** Bundle time counts only inside attendance. Until a day's attendance arrives, it counts inside the employee's working calendar instead (§7.3). | Agreed 2026-10-21 (calendar fallback Agreed 2026-10-21) |
| TD-22 | **Data-quality exceptions are records** with open, resolved and dismissed states. There are three types. Period close is blocked while any are open, and an IE manager can dismiss one with a note (§8). | Proposed (revised v0.3) |
| TD-23 | ~~The nightly pause job is optional and off by default.~~ There is nothing to pause. | Withdrawn 2026-10-21 |
| TD-24 | **Defects.** One record per bundle × operation, with DD at the SAM credited for that work order, booked on the detection date. FLAG-TECH-13 is a constraint on the model (§9.1). | Proposed |
| TD-25 | **Repair earns credit instead of off-standard time:** the repaired quantity × the defect's SAM, credited to the repairer when the repair passes re-inspection. No time is recorded and OS-05 is retired (§9.2). | Repair credit Agreed 2026-10-21; crediting on pass Proposed |
| TD-26 | **QC users record defects and repairs.** IE grants the Quality Control user group access to its own defect and repair models; no foreign model is opened (§9.3). | Proposed |
| TD-27 | **Single-scan capture.** A worker scans each bundle operation once. That scan credits her and ends her previous bundle. Re-scanning her current bundle means "done". There is no pause, resume or finish scan, and nothing to do at breaks or shift end (§4.4). | Agreed 2026-10-21 |
| TD-28 | **No Odoo timer.** Capture never calls `button_start`, so Odoo creates no time rows, calendar leaves or line-state changes at a scan. The bundle a scan ends is marked done with `button_finish` (§4.4). Odoo's work-order durations become its expected-duration fill-ins at MO close and are not used by IE. | Agreed 2026-10-21 |
| TD-29 | **One stretch of time per work order,** held on the work order itself: from the credit scan to the worker's next scan, her done scan or the MO's close, whichever comes first (§4.2, §5.2). A credit set by hand has no stretch. | Agreed 2026-10-21 |
| TD-30 | **Removing or setting a worker** is an edit of the work order's Worker field. Only the MES Supervisor group may make it, and each change posts a note in the MO's chatter. Removal is never a scan (§4.5). | Agreed 2026-10-21 |
| TD-31 | **Off-standard time is a list of grants:** worker, date, code, minutes and note, entered by a line leader or manager. A grant counts as approved when it is entered, is tracked, and has no clock time (§6). | Agreed 2026-10-21 |
| TD-32 | **A daily cap per worker,** adjustable in Settings (default 60 minutes), checked when a grant is entered (§6.3). | Agreed 2026-10-21 |
| TD-33 | **Bundle time ignores off-standard time.** A stretch's minutes count on the days they fall on, inside attendance (§7.3). | Agreed 2026-10-21 |
| TD-34 | **Station protocol (MES premise).** Every trip to a station is two scans: the badge, then the operation coupon. Shared and personal stations work the same way (§4.1). | Agreed 2026-10-21 (MES premise) |
| TD-35 | **No maintenance link.** Line leaders create maintenance requests themselves. RT-3 (breakdown call) and the `ie_maintenance` bridge are dropped, and FG-13 is withdrawn. | Agreed 2026-10-21 |
| TD-36 | **Configuration rule R5:** BoM lines of IE styles are not assigned to an operation ("Consumed in Operation" empty). `button_finish` picks the components of the operations it finishes (`odoo/addons/mrp/models/mrp_workorder.py:669-682`), and R5 keeps stock writes out of scans. Components are consumed at MO close. | Proposed |

---

## 1. Modules and dependencies

This map is preliminary; roadmap step 7 finalises it.

| Module | Content | Depends on | Chunk |
|--------|---------|------------|-------|
| `mes_capture` | The credited worker and her stretch on the work order, the scan journal and its rules, the Worker field and its chatter notes, the line on the MO, the scan endpoint, MES groups | `mrp`, `hr` | 1 |
| `ie_base` | Master data (product types, sections, machine types, families, methods, SAM versions), BoM, operation and line extensions, precedence builder, periods, parameter helper, IE groups, production records and their builder | `mes_capture`, `base_time_parameter` | 1 |
| `ie_time` | Off-standard codes and grants, the daily cap, attendance and time accounting, data-quality exceptions | `ie_base`, `hr_attendance` | 2 |
| `ie_quality` | Defects, repair and its credit, re-inspection | `ie_base`, `qms_catalog`, `quality_control_oca` | 2 |
| `ie_skill` | Metric family, skill matrix, tiers | `ie_time`, `ie_quality` | 3 |
| `ie_line` | Station layout, balancing, plateau and targets, production runs, changeover and ramp-up | `ie_base` | 4 |
| `ie_incentive` | PF, ramp-adjusted threshold, excess and units, period record, payroll fields, shadow mode, self-funding check | `ie_skill`, `ie_line` | 3 |
| `ie_valuation` | Extra Unit Cost at close, the rate, the cost pool | `ie_base`, `mrp_account` | 4 |
| `ie_realtime` | RT candidates | `ie_time`, `ie_line` | 4 |

Changes since v0.2:
- `ie_quality` no longer depends on `ie_time`, because repairs create credits instead of off-standard time.
- `ie_quality` declares `quality_control_oca`, whose user group its access rows name (`oca/manufacture/quality_control_oca/security/quality_control_security.xml:12`).
- `ie_maintenance` is dropped (TD-35).

**Build order for shadow mode:**
1. `mes_capture`
2. `ie_base`
3. `ie_time`
4. `ie_quality`
5. `ie_skill`

`ie_line` and `ie_incentive` come next, the rest after. MES needs at least a minimal scanning path (V5) before shadow mode can start.

---

## 2. Conventions

| Topic | Rule |
|-------|------|
| Names | `name` fields are `Char(required=True, translate=True)`, as in the QMS and PMS suites. |
| Codes | `code` fields hold the timeSSD code: `Char(required=True)`, unique per table (SQL constraint). |
| Minutes and SAM | `Float(digits=(16, 4))`. The spec's precision rule: full precision in calculations, rounding for display only. |
| Quantities | The `Product Unit of Measure` precision, as in core. |
| Dates | Datetimes are UTC, as Odoo stores them. Every IE grouping by day or period uses a **stored local date** (§4.2). |
| Company | Every IE model with business data carries `company_id`; IE runs in the garment company (FG-31). |
| Access | No module grants another domain's models through `ir.model.access` rows. Cross-domain reads are covered by role assignment, and a view element that reads a foreign model names the group granting that read. |
| Rights | Writes that IE performs as a system (builders, scheduled jobs) run as superuser. User actions run as the user. |
| Settings vs parameters | **Values a calculation uses** are versioned parameters (DEC-21, TD-13), so past periods stay reproducible. **Checks made when data is entered**, such as the off-standard cap (TD-32), are plain company settings in *Settings*: changing one never revisits existing records. |
| Tests | `TransactionCase`. Fixtures that create core records (`product.*`, `res.partner`, `res.users`) are `post_install`. No `HttpCase` on this image: routes stay thin, and their logic lives in model methods. |

---

## 3. `ie_base`: master data

The data comes from timeSSD and is entered by hand, or imported with `base_import` or `excel_import_export` (fit-gap §3). IE adds only the family, the section stage, the machine type's skill switch and SAM versions.

### 3.1 `ie.product.type` (timeSSD Product)

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | e.g. `SHR`, `TSH`; unique |
| `name` | Char | translate |
| `active` | Boolean | default True |

### 3.2 `ie.section` (timeSSD Group)

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | e.g. `SHR03`; unique |
| `name` | Char | translate |
| `product_type_id` | Many2one `ie.product.type` | required |
| `stage` | Selection | `preparation` / `assembly` / `finishing`, required, default `preparation`. Used only by the precedence builder (§3.8). |
| `active` | Boolean | |

### 3.3 `ie.machine.type` (timeSSD Machine)

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | e.g. `LOCK1`; unique |
| `name` | Char | translate |
| `purpose`, `principle` | Char | as delivered by timeSSD |
| `complexity` | Selection | `automat` / `semiautomat` / `mechanic` / `manual`, as delivered |
| `skill_evaluated` | Boolean | stored compute from `complexity` (True for `mechanic` and `manual`), `readonly=False`, so the IE can override it (FG-18). Changing the complexity recomputes it. |
| `active` | Boolean | |

### 3.4 `ie.family` (IE's addition, FG-17)

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | translate, e.g. "Collar setting" |
| `grade` | Selection | `A` / `B` / `C`, required |
| `machine_type_id` | Many2one `ie.machine.type` | required. A family's methods share it. |
| `skill_evaluated` | Boolean | related `machine_type_id.skill_evaluated` |
| `active` | Boolean | |

The display name is "name · machine code · grade", as in spec §2 ("Collar setting · SNLS · Grade A").

### 3.5 `ie.method` (timeSSD Method: the library operation)

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | timeSSD method code, unique. It is the **library operation code** of spec §2. |
| `name` | Char | translate |
| `product_type_id` | Many2one `ie.product.type` | |
| `section_id` | Many2one `ie.section` | required |
| `machine_type_id` | Many2one `ie.machine.type` | required |
| `family_id` | Many2one `ie.family` | required |
| `tst`, `allowance` | Float | optional, as delivered (SAM = TST × allowance) |
| `sam_version_ids` | One2many `ie.sam.version` | |
| `sam` | Float | the current SAM: non-stored compute of the version in force today |
| `active` | Boolean | |

**Constraint:** `family_id.machine_type_id == machine_type_id`, checked on both fields.

### 3.6 `ie.sam.version` (FG-27, TD-12)

| Field | Type | Notes |
|-------|------|-------|
| `method_id` | Many2one `ie.method` | required, `ondelete='cascade'` |
| `date_from` | Date | required. Unique together with `method_id`. |
| `sam` | Float (16, 4) | required. SQL CHECK `sam > 0`. |
| `reason` | Selection | `initial` / `method_change` / `standard_error`, required. Spec §5.3 and §5.4. |
| `note` | Text | |

Disputes (function map 2.3) arrive in a later chunk and add `dispute_id` here.

**Rules:**
- **Lookup.** `ie.method._ie_sam_at(date)` returns the version with the latest `date_from ≤ date`. A production record uses the version in force on its credit date (TD-11; spec §5.2 says completion date, §12).
- **Expected durations.** Whenever a method's versions change, `time_cycle_manual` on the BoM operations that reference it is set to the current SAM. This affects only Odoo's expected durations (rule R1).
- **Retroactive versions.** Creating, changing or deleting a version rebuilds the production records of that method in **open** periods (§5.3). Records in closed periods are never touched (spec §5.2, TC-EM-07).

### 3.7 Extensions of core models

| Model | Field | Type | Notes |
|-------|-------|------|-------|
| `mrp.bom` | `ie_product_type_id` | Many2one `ie.product.type` | the OB's product type (FG-19), the plateau key |
| `mrp.bom` | `ie_workflow_code` | Char | the timeSSD workflow code, for traceability |
| `mrp.routing.workcenter` | `ie_method_id` | Many2one `ie.method` | the OB operation's library method. Choosing it fills `name` and `time_cycle_manual` (current SAM) and sets `time_mode = manual`. |
| `mrp.routing.workcenter` | `ie_family_id`, `ie_section_id` | related | display only |
| `mrp.workcenter` | `ie_is_line` | Boolean | marks a sewing line |
| `mrp.workcenter` | `ie_config_warning` | Char, non-stored compute | set when an IE line has `default_capacity ≠ 1`, product capacities, or `costs_hour ≠ 0` (rules R1 and R2). Shown as a warning banner on the form; it does not block. |

**Configuration rules for IE lines and styles:** R1 to R4 as in fit-gap §2.3, plus **R5** (TD-36): BoM lines of IE styles leave "Consumed in Operation" empty.

### 3.8 Precedence builder (FG-20)
`mrp.bom.action_ie_build_dependencies()`, a button on the BoM:
1. Sets `allow_operation_dependencies = True`.
2. Within each section, links every operation to the one before it, in sequence order.
3. The first operation of the assembly stage waits for the last operation of every preparation section.
4. The first operation of the finishing stage waits for the last assembly operation.
5. Existing links are replaced.

Running it is optional: the IE can always set "Blocked By" on the operations by hand. Capture ignores precedence (§4.4), so it affects only Odoo's readiness display and, later, RT-5 and RT-6.

### 3.9 `ie.period` (TD-02)

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | `YYYY-MM`, computed from `date_from`, stored |
| `date_from` | Date | first day of the month, required |
| `date_to` | Date | last day of the month, stored compute |
| `state` | Selection | `open` / `closed`, default `open` |
| `mode` | Selection | `shadow` / `live`. Set at creation from the parameter `ie.mode` in force on `date_from`, and editable while open (spec §14.2, TC-INC-12). |
| `closed_by`, `closed_at` | Many2one `res.users`, Datetime | set at close |
| `company_id` | Many2one | required |

- **Uniqueness:** `(company_id, date_from)`.
- **Finding a period:** `ie.period._ie_period_for(date)` returns a date's period and creates it, open, if it does not exist.
- **Closing,** and what it freezes, is in chunk 3. Chunks 1–2 need only the state: builders skip closed periods, and grants, repairs and Worker edits are refused in them.

### 3.10 Parameter helper (TD-13)
`ie.parameter`, an AbstractModel with no table, provides `get(code, date)`:
1. Finds the `base.time.parameter` with that `code` in the current company or in no company.
2. Takes the version with the latest `date_from ≤ date`, and converts its value by the parameter's type (float, integer, boolean, JSON, …).
3. **Raises** if there is no such version.

So a stored 0 or False reads as itself. The OCA wrapper's falsy and never-raises quirks (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:72-73`, `models/base.py:22`) do not apply. IE parameters have `model_id` empty. The catalogue of codes, and who edits them, is in chunk 4.

### 3.11 Groups and access (TD-03)
Category "Industrial Engineering".

| Group | Implies | Holds |
|-------|---------|-------|
| `ie_base.group_ie_user` | `base.group_user` | Read IE data |
| `ie_base.group_ie_line_leader` | User | Off-standard grants (§6) |
| `ie_base.group_ie_engineer` | User | Master data and SAM |
| `ie_base.group_ie_manager` | Engineer, Line leader | Periods, parameters, settings, dismissing exceptions |

| Model | User | Engineer | Manager |
|-------|------|----------|---------|
| `ie.product.type`, `ie.section`, `ie.machine.type`, `ie.family`, `ie.method`, `ie.sam.version` | read | read, write, create, unlink | all |
| `ie.period` | read | read | read, write, create |
| `ie.production.record` | read | read | read |

Production records are written only by the builder, which runs as superuser.

---

## 4. `mes_capture`: capture

The single-scan note's rules map to this version as follows:

| Note | Here |
|------|------|
| R-1 one scan type, R-5 refusals, R-10 done scan | §4.4 |
| R-2 credit at the scan | §4.2, §5 |
| R-3 duration | §5.2, §7.3 |
| R-4 abnormal durations accepted | Unchanged; bounded by attendance (§7.3) |
| R-6 combined stations | Workers scan each operation when they start it. This is scanning discipline, with no system rule. |
| R-7 reassignment and clearing | §4.5, by Worker field edit (TD-30), not by journal event |
| R-8 off-standard | §6, as grants of minutes, not subtracted from bundle time (TD-33) |
| R-9 breakdown button | Dropped (TD-31, TD-35) |
| R-11 running-long list | Chunk 4. The current bundle and its scan time are on the work order, so the list (and a "too fast" list) is one query. |

### 4.1 Station protocol (MES premise, TD-34)
MES owns the station and its screens. Capture relies on this protocol:
- **Two scans per trip.** The worker scans her badge, and the station shows her name. She then scans the operation coupon. Her identity clears after the coupon, or after `[P 30 s]` with no coupon, so the next person must badge first.
- **Shared and personal stations** behave the same way.
- **One event per trip.** The station sends badge, coupon, device time, its learned clock offset, a station label and a UUID (§4.6).
- **Outcomes.** The station shows the result: started, done, ignored, or refused with its reason (§4.4).
- **Coupons.** A bundle ticket carries one coupon per operation, and each coupon's barcode is core's work-order barcode, `<MO name>/<work order id>` (`odoo/addons/mrp/models/mrp_workorder.py:33, 280-282`). MES prints the tickets.
- **Badges** are `hr.employee.barcode` (Badge ID). None of the 378 active employees has one yet; filling them in is a setup task before shadow mode.
- **No undo.** A wrong scan shows up as a refusal when the right worker scans. A supervisor then fixes it with the Worker field (§4.5).
- **Off-standard grants** are not part of the protocol. IE provides the action (§6). If MES ever offers it at a station, MES must pass on which leader granted it.

### 4.2 Extensions of core models

| Model | Field | Type | Notes |
|-------|-------|------|-------|
| `mrp.workorder` | `mes_employee_id` | Many2one `hr.employee`, index | The **credited worker** (FG-04), labelled "Worker". Set by a scan or by hand (§4.5). |
| `mrp.workorder` | `mes_credited_at` | Datetime | When the credit was given: the scan's event time, or the moment a supervisor set the worker. |
| `mrp.workorder` | `mes_date` | Date, stored compute | The **credit date** (TD-11): the local date of `mes_credited_at` in the timezone of the company's working calendar (`company.resource_calendar_id.tz`, Asia/Ho_Chi_Minh). |
| `mrp.workorder` | `mes_scan_id` | Many2one `mes.scan.event` | The scan that gave the credit. Empty for a credit set by hand. |
| `mrp.workorder` | `mes_ended_at` | Datetime | The end of the worker's stretch: her next scan or her done scan. Empty while it is her current bundle. |
| `mrp.production` | `mes_line_id` | Many2one `mrp.workcenter` | The **line of the bundle** (FG-25). Copied by the split (`_split_productions` uses `copy_data`). Writing it sets `workcenter_id` on the MO's work orders that are not started or done. Core refuses the change for those (`mrp_workorder.py:475-480`), and with single scan no work order is ever started. |

- **A worker's current bundle** is the work order with her as `mes_employee_id`, `mes_scan_id` set and `mes_ended_at` empty. The scan rules (§4.4) keep it to at most one.
- **The MO's close** is not written to the work orders. The production record takes it into account when it computes the stretch's end (§5.2).
- **After "Update BoM"** (TD-10): `mrp.production._link_bom` is extended. It calls super, which resets the work orders' work centres to the BoM's (`odoo/addons/mrp/models/mrp_production.py:2570-2571`), then re-applies `mes_line_id`.
- **Removed since v0.2:**
  - `mes_employee_id` on time rows (capture writes no time rows);
  - `mes_date_local` (replaced by `mes_date`);
  - `mes.stop.reason` (TD-07).

### 4.3 `mes.scan.event`: the scan journal (TD-06)

| Field | Type | Notes |
|-------|------|-------|
| `uuid` | Char | client event ID, **unique**, required |
| `badge`, `coupon` | Char | as scanned |
| `employee_id` | Many2one `hr.employee` | resolved from the badge |
| `workorder_id` | Many2one `mrp.workorder` | resolved from the coupon, index |
| `ended_workorder_id` | Many2one `mrp.workorder` | the worker's previous bundle that this scan ended, if any |
| `station` | Char | device or station label, as sent |
| `device_time` | Datetime | the device's time, converted to UTC |
| `clock_offset` | Float | seconds, server minus device, as learned by the PWA |
| `received_at` | Datetime | server time on arrival |
| `event_time` | Datetime | the time applied (§4.4) |
| `late` | Boolean | arrived later than the late limit |
| `result` | Selection | `started` / `done` / `ignored` / `refused` |
| `message` | Char | what the station shows: the refusal reason, or a confirmation |
| `user_id` | Many2one `res.users` | the station user who sent it |
| `company_id` | Many2one | |

**Index:** `(employee_id, event_time)`. The journal is append-only: nobody edits or deletes events.

### 4.4 Applying a scan (TD-27, TD-28)
`mes.scan.event.mes_submit(payload)` is a model method, called by the endpoint (§4.6) and by tests. It returns `{result, message, event_time, server_time}`. `result` is one of the four above, or `duplicate`.

1. **Duplicate.** If the `uuid` exists, the method returns its stored outcome and does nothing else, so a queue can resend safely.
2. **Worker.** The badge is resolved with elevated rights (TD-14) to an active `hr.employee` of the company. An unknown badge is refused.
3. **Work order.** The coupon's text after its last `/` is the work-order ID. Capture reads that work order and checks that its `barcode` equals the coupon, so no search over the table is needed. An unknown or mismatched coupon is refused.
4. **Lock.** The work order's row is locked (`SELECT … FOR UPDATE`). Two workers scanning the same coupon at the same moment are then applied one after the other, and the second is refused.
5. **Time** (TD-08):
   - `corrected = device_time + clock_offset`.
   - If `received_at − corrected ≤` the prompt window, `event_time = received_at`. Otherwise `event_time = corrected`.
   - `late` is set when `received_at − corrected >` the late limit.
   - The prompt window `[P 30 s]` and the late limit `[P 15 min]` are parameters; MES confirms their values (FG-OPEN-12).
6. **Order.** A scan earlier than the worker's last applied scan is refused as out of order. A FIFO queue keeps a station's events in order.
7. **Rules,** checked in this order:

   | Situation | Result | Effect |
   |-----------|--------|--------|
   | The MO is draft | refused | "This bundle has not been released." Odoo 18 creates work orders on draft MOs (`mrp_production.py:581-583`). |
   | The MO is done | refused | "This bundle's MO is already completed." |
   | The MO or the work order is cancelled | refused | "This bundle is cancelled." |
   | The work order is credited to another worker | refused | "Credited to <name>." Only a supervisor can change it (§4.5). |
   | It is the worker's current bundle, scanned within `[P 30 s]` of its credit | ignored | An accidental double scan. Nothing changes. |
   | It is the worker's current bundle, later than that | done | `mes_ended_at = event_time`; Odoo finish (step 8). |
   | It is credited to the worker but is not her current bundle (already ended, or set by hand) | refused | "Already done." There is no resume. |
   | It is not credited | started | The worker's current bundle, if any, gets `mes_ended_at = event_time` and the Odoo finish (step 8). The scanned work order gets `mes_employee_id`, `mes_credited_at = event_time`, `mes_scan_id`, and an empty `mes_ended_at`. |

   Capture checks neither precedence nor component availability: workers follow the physical bundle.
8. **Odoo finish.** A work order whose stretch a scan ends gets `button_finish()` (TD-28), unless it is already done or cancelled. That method works on a work order that was never started and checks no predecessor (`mrp_workorder.py:664-695`). The call runs inside a savepoint. If it fails, the failure is logged and the scan still stands, because the MO's close finishes every remaining work order (`mrp_production.py:2129`).
9. **Journal.** The event is stored with its result and message.

**The calls run as the station user.** `mrp.group_mrp_user` suffices for `button_finish`, as the prototype measured (fit-gap §13).

**What Odoo then shows:**
- Each finished work order is done, with `date_finished` at the scan that ended it.
- When every work order of a bundle is done, the MO moves to "To Close" by itself (`mrp_production.py:569-570`). That gives planners a list of bundles ready to close.
- At close, Odoo fills every work order with no time with its expected duration (`mrp_production.py:1836-1842`). IE never reads those durations.
- With no `button_start`, the MO's quantity producing stays 0 until close, so closing takes Odoo's automatic-quantity path (`mrp_production.py:2243-2255, 2833-2842`). The P-05 prototype run did not time that path; the first build's tests do (§11).

### 4.5 The Worker field: removal and manual credit (TD-30)
- **Where.** `mes_employee_id` appears as "Worker" in the MO form's Work Orders tab and on the work-order form. It is editable for `mes_capture.group_mes_supervisor` and read-only for everyone else.
- **Write rules.** A write of `mes_employee_id` from anywhere other than a scan:
  - is refused for users outside the Supervisor group;
  - **clearing it** empties `mes_credited_at`, `mes_scan_id` and `mes_ended_at`. If it was the worker's current bundle, she now has none. The work order's Odoo state is not touched: if a scan had already finished it, it stays done. The next worker scans the coupon normally and is credited;
  - **setting a worker** gives `mes_credited_at = now`, so the credit is dated today, with no scan and no stretch. This is how an "unscanned work order" exception is resolved (§8). A worker who scans a work order set to her by hand is refused ("Already done"). To let someone continue a bundle, clear the field and let her scan.
- **Tracking.** Each change posts a note in the MO's chatter: the operation, the old worker, the new worker or none, written by the editing user. Work orders have no chatter of their own (`mrp_workorder.py:14-15`), while the MO is a `mail.thread` (`mrp_production.py:30`).
- **Closed periods.** `ie_base` adds this rule: a change is refused when the work order's current credit date falls in a closed period ("This credit is in closed period YYYY-MM").
- **Scope.** The scan refusals of §4.4 do not apply here, because fixing finished bundles is this field's main use.

### 4.6 Endpoint
- `POST /mes/scan` (`type='json'`, `auth='user'`) calls `mes_submit` with one payload: `uuid`, `badge`, `coupon`, `station`, `device_time`, `clock_offset`.
- `POST /mes/scan/batch` takes a list, applied in order, for a queue flush. It returns one result per event.

The routes only parse and delegate. Their wiring is checked with `curl`, because this image cannot run `HttpCase` tests. The PWA itself belongs to the MES phase.

### 4.7 Groups and access
Category "MES".

| Group | Implies | Holds |
|-------|---------|-------|
| `mes_capture.group_mes_station` | `mrp.group_mrp_user` | Sending scans. The station devices' users. |
| `mes_capture.group_mes_supervisor` | Station | Editing the Worker field (§4.5), reading the journal. Production managers, and line leaders who have Odoo users. |

| Model | Station | Supervisor | `mrp.group_mrp_manager` |
|-------|---------|------------|-------------------------|
| `mes.scan.event` | create; read own | read | read |

- The work-order and MO fields follow core's manufacturing rights, except that `mes_employee_id` is editable only by the Supervisor group (§4.5).
- The other `mes_*` fields on the work order are written only by capture and are read-only in views.
- **Setup:** whoever edits the Worker field or grants off-standard time needs an Odoo user. None of the 6 "Line Leader" employees has one today. CE has no licence cost.

---

## 5. `ie_base`: production records (TD-05)

### 5.1 `ie.production.record`
There is one record per credit:
- **A production credit**, for each credited work order: spec §2's "production record", operator × operation × bundle.
- **A repair credit**, for each repair that passed re-inspection. `ie_quality` adds this kind (§9.2).

A record is a snapshot. Master data changes after its period closes do not alter it.

| Field | Type | Source |
|-------|------|--------|
| `kind` | Selection | `production`; `ie_quality` adds `repair` |
| `workorder_id` | Many2one `mrp.workorder` | required, `ondelete='cascade'` |
| `production_id` | Many2one `mrp.production` | the bundle |
| `employee_id` | Many2one `hr.employee` | the credited worker (`mes_employee_id`), or the repairer |
| `date` | Date | the credit date (`mes_date`), or the repair's result date |
| `date_start`, `date_end` | Datetime | the stretch (§5.2), for scanned production credits only. `date_end` is empty while the stretch is open. |
| `period_id` | Many2one `ie.period` | the period of `date` |
| `line_id` | Many2one `mrp.workcenter` | the work order's `workcenter_id` |
| `bom_id`, `product_tmpl_id` | Many2one | the OB and the style |
| `operation_id` | Many2one `mrp.routing.workcenter` | the OB operation |
| `method_id` | Many2one `ie.method` | `operation_id.ie_method_id`. Its code is the library code used for familiarity (FLAG-TECH-08). |
| `family_id`, `machine_type_id`, `section_id`, `product_type_id` | Many2one | from the method, and the BoM for the product type |
| `grade` | Selection | snapshot of `family_id.grade` |
| `skill_evaluated` | Boolean | snapshot of the family's flag |
| `qty` | Float | **production:** the work order's `qty_production`, the bundle quantity credited (DEC-04). **Repair:** the repaired quantity. |
| `sam_version_id`, `sam` | Many2one, Float (16, 4) | **production:** the method's version in force on `date` (§3.6). **Repair:** the defect's SAM (§9.2). |
| `em_gross` | Float (16, 4) | `qty × sam` (spec §2, EM_g per record) |
| `company_id` | Many2one | |

**Uniqueness:** one production credit per work order, as a partial unique index on `workorder_id` where `kind = 'production'`. `ie_quality` adds one repair credit per repair.

**Indexes:**
- `(employee_id, date)` for operator-days;
- `(line_id, date)` for lines;
- `(method_id, line_id, date)` for familiarity over 90 days;
- `(family_id, employee_id)` for skill;
- `(period_id)`.

**Expected size:** about 42,000 production credits a month and 500,000 a year (fit-gap §13.1), plus a few repair credits.

### 5.2 The stretch (TD-29)
- **Start:** `mes_credited_at` of a credit given by a scan.
- **End:** the earliest of the work order's `mes_ended_at` and, once the MO is done, the MO's `date_finished`. While neither exists, the stretch is open: it is the worker's current bundle.
- **A credit set by hand** has no stretch, and so no bundle time.
- **Pieces count from the scan** (R-2). `qty`, `sam` and `em_gross` never depend on the stretch. The stretch feeds only bundle time (§7.3).

### 5.3 Builder
`ie.production.record._ie_build(workorders)` writes the production credits. It runs as superuser.

- **Qualifying work orders:**
  - `mes_employee_id` set;
  - an operation with an `ie_method_id`;
  - neither the work order nor its MO cancelled.
- **For each one:**
  1. Find the period of `mes_date`. If it is **closed**, skip.
  2. Otherwise create or update its production credit from the sources above.
- **A production credit whose work order no longer qualifies,** in an open period, is deleted. That happens when the worker is cleared or the MO is cancelled.

It is called from three places:

| Caller | Candidates |
|--------|-----------|
| Scheduled job, every `[P 5 min]` (`ir.cron`, editable) | Work orders whose `write_date`, or their MO's `write_date`, is at or after the watermark. That covers scans, Worker edits, MO close and cancellation. The watermark is an `ir.config_parameter`, advanced to the job's start time on success. |
| A SAM version created, changed or deleted (§3.6) | The method's records in open periods |
| Period close (chunk 3) | Every qualifying work order of the period, before it is frozen |

**Not built:** a work order of a done MO that has no credited worker. Nobody scanned it, and the MO's close finished it (`mrp_production.py:2129`). It earns no one anything and appears on the exception list as `unscanned_workorder` (§8).

---

## 6. `ie_time`: off-standard grants (spec §3.2–3.3, TD-31, TD-32)

Off-standard time is a managerial grant of minutes: leeway for fairness in evaluating a worker, expected to be rare. It has no clock time, no states and no approval step.

### 6.1 `ie.offstandard.code`

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | unique, e.g. `OS-01` |
| `name` | Char | translate |
| `active` | Boolean | |

**Seeded data** (`noupdate`), with the spec's names (spec §3.2):

| Code | Name |
|------|------|
| OS-01 | Machine breakdown / mechanic wait |
| OS-02 | Material wait |
| OS-03 | Waiting for work |
| OS-04 | Power / utility outage |
| OS-06 | Company meeting / organised training |
| OS-07 | Non-standard assignment |
| OS-08 | Other approved |
| OS-09 | Style changeover setup |

- OS-05 (repair) is not seeded, because repairs earn credit (TD-25).
- These are the project's own vocabulary, not guessed configuration, and the IE edits them freely.

### 6.2 `ie.offstandard`
A `mail.thread`, so changes are tracked.

| Field | Type | Notes |
|-------|------|-------|
| `employee_id` | Many2one `hr.employee` | required, index, tracked |
| `date` | Date | required, default today (local), tracked. Production may grant after the fact, so an earlier date in an open period is allowed. |
| `code_id` | Many2one `ie.offstandard.code` | required, tracked |
| `minutes` | Float (16, 4) | required, tracked. SQL CHECK `minutes > 0`. |
| `note` | Text | |
| `period_id` | Many2one `ie.period` | stored, from `date` |
| `company_id` | Many2one | |

**Rules:**
- **Approved on entry.** A grant counts from the moment it is entered. Who granted it is `create_uid`, which the audit by granting user reads (spec §3.3 rule 4).
- **Grants add up.** Two grants for the same worker on the same day both count, whatever their codes. There is no overlap check and no time of day.
- **Daily cap** (§6.3). The total of a worker's grants on one date may not exceed the cap. A grant that would exceed it is refused: "<Worker> already has N min on <date>; the daily cap is M min."
- **Open periods only.** Creating, changing or deleting a grant whose date falls in a closed period is refused.
- **Bundle time is not reduced by grants** (TD-33, §7.3).

**Access:**

| | IE user | IE line leader | IE manager |
|--|---------|----------------|------------|
| `ie.offstandard` | read | read, create, write, unlink | all |
| `ie.offstandard.code` | read | read | all |

### 6.3 Daily cap (TD-32)
- **The setting:** `res.company.ie_offstandard_cap`, a Float in minutes, default 60, required and positive. It is shown in *Settings → Industrial Engineering* through a related field on `res.config.settings`, and edited by IE managers.
- **Not versioned:** it is checked when a grant is entered (§2, *Settings vs parameters*). Changing it never revisits existing grants.
- **Long stops:** a stop longer than the cap, such as a long power cut, cannot be granted in full. Such cases are handled outside IE, by reallocating or sending workers home, or by HR and payroll rules.

### 6.4 Granting to several workers
`ie.offstandard.grant` (transient) takes workers, date, code, minutes and note, and creates one grant per worker. Every grant is checked against the cap, and the wizard creates all of them or none. It serves line-wide events such as a meeting (OS-06) or a short outage (OS-04).

### 6.5 What IE offers MES
`ie.offstandard.ie_grant(employee, code, minutes, date, note)` creates one grant as the calling user, with the same rules. If MES ever offers grants at a station, it calls this method and must pass the granting leader's identity. That is for the MES phase.

---

## 7. `ie_time`: attendance and time accounting (spec §3.1, §3.4, DEC-18)

### 7.1 `ie.operator.day`

| Field | Type | Notes |
|-------|------|-------|
| `employee_id` | Many2one `hr.employee` | required |
| `date` | Date | local, required. Unique together with `employee_id`. |
| `period_id` | Many2one `ie.period` | |
| `line_id` | Many2one `mrp.workcenter` | the line with most of the day's earned minutes, used for line figures. Chunk 3 confirms this for workers on several lines in a day (TD-OPEN-05). |
| `attendance_arrived` | Boolean | `date ≤ period.attendance_through` (§7.4) |
| `attended_minutes` | Float (16, 4) | A |
| `offstandard_minutes` | Float (16, 4) | OS: the day's grants |
| `nam` | Float (16, 4) | `max(0, A − OS)` |
| `planned_minutes` | Float (16, 4) | the calendar's planned working minutes |
| `bundle_minutes` | Float (16, 4) | the minutes of the worker's stretches that fall on this day, counted inside attendance or the calendar (§7.3) |
| `offstandard_line_ids` | One2many `ie.operator.day.offstandard` | OS by code |
| `company_id` | Many2one | |

The child model `ie.operator.day.offstandard` holds `day_id`, `code_id` and `minutes`. It gives OS by code for M5, the payroll feed (spec §12) and the audit. Chunk 3 adds the metric fields (EM, DD, efficiencies) and the bundle minutes per family that the family split needs.

### 7.2 One operator-day, computed
The window is the local day [d 00:00, d+1 00:00) in the company calendar's timezone, converted to UTC.
1. **Attendance intervals:** each `hr.attendance` of the worker that overlaps the window, cut to the window, minus the lunch intervals of the worker's calendar (`employee._employee_attendance_intervals(start, stop, lunch=True)`, `odoo/addons/hr/models/hr_employee.py:644-650`).
2. **A** = the total length of those intervals. This is the same as core's `_get_worked_hours_in_range` (`odoo/addons/hr_attendance/models/hr_attendance.py:220-242`), and it counts night shifts in the day they fall in.
3. **OS** = the sum of the worker's grants dated d, grouped by code into the child lines.
4. **NAM** = A − OS, never below 0. With the daily cap (§6.3), the floor matters only on a day with less attendance than its grants.
5. **`planned_minutes`** = the worker's calendar intervals within the window (`employee._get_expected_attendances(start, stop)`, `hr_employee.py:652`).
6. **`bundle_minutes`** = for each scanned production credit of the worker whose stretch overlaps the window: the stretch, cut to the window, intersected with the **counting intervals**, then summed. An open stretch counts up to now.
   - The counting intervals are the attendance intervals of step 1 once the day's attendance has arrived (§7.4).
   - Before that, they are the calendar intervals of step 5.

Until attendance arrives, A and NAM hold what exists so far, and `attendance_arrived = False` marks them as provisional.

### 7.3 Bundle time (OPEN-15 option B, TD-21, TD-33)
`ie_time` adds **`counted_minutes`** (Float 16, 4) to `ie.production.record`: its stretch intersected with the counting intervals of every day it touches. It is the sum of that record's share of each day's `bundle_minutes`. Repair credits and credits set by hand have none.

What this means:
- **Breaks, nights and days off add nothing.** A stretch from 16:50 Monday to 08:20 Tuesday counts 10 minutes on Monday and 20 on Tuesday, if the worker attended 16:50–17:00 and 08:00–08:20. The pieces are credited on Monday, the scan date.
- **The shop floor does nothing at breaks or shift end.** A forgotten done scan costs nothing, because only attended time counts.
- **Before attendance arrives,** the calendar gives sensible provisional figures, with lunch and nights excluded. That is the same rule as the live "running long" list (chunk 4).
- **Off-standard grants are not subtracted** (TD-33). On a day with grants, coverage (M7 = bundle minutes ÷ NAM) can exceed 100%. M7 is a diagnostic, and the family split uses each family's share of bundle time, so grants barely move it.
- **Handling time is bundle time.** The gap between finishing one bundle and scanning the next counts towards the earlier bundle, so pace (M6) and coverage (M7) are rougher than with start and finish scans. Pay is unaffected.
- **Attendance accuracy matters,** since attendance is the clock for bundle time as well. `scan_outside_attendance` (§8) catches missing or wrong punches.
- **Night shifts.** Credits are dated by the scan's local date, while A splits a night shift at midnight. Daily figures for night workers are therefore uneven, but monthly figures are not affected except at the month boundary. The same was true of the completion date.

### 7.4 Attendance completeness (TD-20)
`ie_time` adds **`attendance_through`** (Date) to `ie.period`: the last date with complete attendance.
- An IE manager sets it after each import, or the import pipeline writes it.
- Days up to that date count bundle time inside attendance, are final-able, and get the attendance-based exception (§8).
- Days after it stay provisional and count bundle time inside the calendar.

This works the same for monthly and daily imports (FG-21).

### 7.5 Builder
`ie.operator.day._ie_build(pairs)` runs as superuser. It also recomputes `counted_minutes` on the production records concerned.

**When it runs:**
- **A scheduled job every `[P 15 min]`.** It takes the (worker, date) pairs whose sources changed since its watermark:
  - `hr.attendance` (every date an attendance touches);
  - `ie.offstandard`;
  - `ie.production.record`;
  - every day of a period whose `attendance_through` moved;
  - today, for every worker with an open stretch, since that stretch keeps growing.
- **At period close** (chunk 3).
- **The manager's "Recompute period" action.** Deleted attendances leave no `write_date`, so only the close and this action catch them.

Closed periods are skipped. Within one run the order is: production records (§5.3), then operator-days, then exceptions (§8).

---

## 8. `ie_time`: data-quality exceptions (spec §3.4, TD-22)

### 8.1 `ie.exception`

| Field | Type | Notes |
|-------|------|-------|
| `exception_type` | Selection | §8.2 |
| `employee_id`, `date`, `line_id` | | where it belongs |
| `res_model`, `res_id` | Char, Integer | the record concerned |
| `message` | Char | |
| `state` | Selection | `open` / `resolved` / `dismissed` |
| `resolved_by`, `resolved_at`, `note` | | |
| `period_id`, `company_id` | Many2one | |

**Uniqueness:** `(exception_type, res_model, res_id)`.

### 8.2 Types

| Type | Raised when | Resolved by | Needs attendance |
|------|-------------|-------------|------------------|
| `unscanned_workorder` | A work order of a done MO, on an operation with a method, has no credited worker. Someone did that work without being credited. | Setting the worker in the Worker field (§4.5) | no |
| `rejected_queued_event` | A refused scan arrived late (`late` set), so the worker never saw the refusal | A supervisor checks the bundle and fixes the Worker field if needed, then dismisses | no |
| `scan_outside_attendance` | A started or done scan's event time lies outside the worker's attendance intervals: a missing check-in, a wrong punch, or work off the clock (TC-TA-06) | Correcting attendance | yes |

**Dropped:**
- `unapproved_pause` and `open_offstandard`: nothing is pending, and grants have no end;
- `late_event`: a late scan that applied needs no action, and its `late` flag stays on the journal for review;
- "bundle open at clock-out" and "coverage above 100%", under option B (v0.2).

- **Detection** is a job that runs after the operator-day build. `scan_outside_attendance` is checked only for days up to `attendance_through`.
- **When the condition no longer holds,** the exception resolves itself.
- **An IE manager can dismiss** an exception with a note.

### 8.3 Close
Period close (chunk 3) is blocked while the period has open exceptions. TC-TA-06 leaves "blocked or warned" to technical design: blocked is chosen, with dismissal as the escape.

---

## 9. `ie_quality`: defects, repair, re-inspection (spec §9)

### 9.1 `ie.defect` (TD-24)

| Field | Type | Notes |
|-------|------|-------|
| `production_id` | Many2one `mrp.production` | the bundle, required |
| `workorder_id` | Many2one `mrp.workorder` | the bundle × operation. Empty when the defect cannot be traced to an operation, in which case it is attributed to the line (spec §9.2). |
| `line_id` | Many2one `mrp.workcenter` | the bundle's `mes_line_id` |
| `defect_code_id` | Many2one `qms.defect.code` | required. Codes only (`parent_id` set), with `domain_kind` `qm` or `both`. |
| `qty` | Float | required, > 0 |
| `detection_point` | Selection | `inline` / `end_of_line` / `final_audit`, required |
| `responsibility` | Selection | `operator` / `material` / `cutting` / `machine` / `unknown`, required |
| `detection_date` | Date | local, default today. Must fall in an open period. |
| `detected_at` | Datetime | default now |
| `inspector_id` | Many2one `hr.employee` | optional. The creating user is kept as well. |
| `employee_id` | Many2one `hr.employee` | set at creation: the work order's credited worker when `responsibility = operator`, otherwise empty |
| `sam` | Float (16, 4) | the SAM credited for this bundle × operation: its production credit's `sam`, which exists from the scan. For a work order nobody is credited for, the method's SAM on the detection date. |
| `k_def` | Float | the parameter `ie.k_def` on the detection date |
| `dd` | Float (16, 4) | `qty × sam × k_def` when `employee_id` is set, else 0 (spec §9.3) |
| `period_id` | Many2one `ie.period` | the detection date's period: DD is booked there |
| `state` | Selection | `open` / `closed`; a passing repair closes it |
| `reinspection_failures` | Integer | failed repairs, the repairer diagnostic (spec §9.5) |
| `company_id` | Many2one | |

**Rules:**
- **FLAG-TECH-13.** A work order's defects may total at most its quantity (`qty_production`). A record that would exceed it is rejected with an error, and nothing of it is booked (TC-EM-03). This is a constraint on `qty` and `workorder_id`. Two inspectors booking the same bundle at the same instant could both pass, and that is accepted.
- **Booking.** DD is booked on the detection date, and closed periods are never reopened (TC-EM-02).
- **Every family.** DD applies to every family, skill-evaluated or not (TC-EM-05).
- **Why a snapshot.** `employee_id` is set at creation, not computed, so a later change of the Worker field cannot move a deduction already booked.

### 9.2 `ie.repair` (TD-25)

| Field | Type | Notes |
|-------|------|-------|
| `defect_id` | Many2one `ie.defect` | required |
| `employee_id` | Many2one `hr.employee` | the repairer, required |
| `production_id`, `workorder_id` | Many2one | related from the defect, stored |
| `qty` | Float | > 0, at most the defect's quantity |
| `sam` | Float (16, 4) | snapshot of the defect's `sam` at creation |
| `result` | Selection | `pending` / `pass` / `fail`, default `pending` |
| `result_date` | Date | the local date the result was set. Must fall in an open period. |
| `company_id` | Many2one | |

**Rules:**
- **Credit on pass.** A repair whose result is `pass` gets a repair credit (§5.1):
  - `kind = repair` and `repair_id`;
  - employee = the repairer;
  - `qty` = the repaired quantity;
  - `sam` = the defect's SAM;
  - `date` = `result_date`.

  `ie_quality` adds `repair_id` (unique) to `ie.production.record` and builds these records, as superuser, when a result changes.
- **Fail.** A failed repair earns nothing. It adds 1 to the defect's `reinspection_failures`, and the defect stays open for another repair, by the same or another repairer (spec §9.5, TC-EM-06).
- **Pass closes the defect.**
- **A worker who repairs her own defect nets to zero,** because the defect's DD and the repair credit use the same quantity and SAM. Her repair time is her own cost. Nobody gains by making defects.
- **No time is recorded,** and no off-standard time results. OS-05 is retired (§6.1).
- **Changing a result** in an open period updates or removes the repair credit. Closed periods are untouched.
- **Effect on line figures:** repair credits add to line EM_g. Repaired pieces are re-credited at one operation's SAM, which is well under 1% of a line's earned minutes, so the effect is ignored.

### 9.3 Access (TD-26)

| Model | QC user (`quality_control_oca.group_quality_control_user`) | IE user | IE line leader | IE manager |
|-------|-----------|---------|----------------|------------|
| `ie.defect` | read, create, write | read | read | all |
| `ie.repair` | read, create, write | read | read, create, write | all |
| `ie.operator.day` and its lines | — | read | read | read |
| `ie.exception` | — | read | read | all, including dismiss |

- Inspectors hold their own domain group, as the role matrix has it. IE grants that group access to IE's own two models, and nothing foreign is opened.
- Repair credits are written by the builder as superuser.

### 9.4 What stays in QMS
Formal QC inspections and nonconformities stay in the QMS suite. IE's defects are the attribution records for pay and skill. They use the same `qms_catalog` codes, so quality reporting can combine both.

---

## 10. FLAG-TECH items settled by chunks 1–2

| Flag | How |
|------|-----|
| 02 MO grouping | Lot = the split's procurement group; bundle = MO; OB = BoM; line = `mes_line_id`. Production runs follow in chunk 4. |
| 03 Family time from scans | Each credit's stretch, from its scan to the next scan, counted inside attendance (§5.2, §7.3) |
| 04 Bundles across days | Credited on the scan's local date (TD-11). The stretch's minutes count on the days they fall on (§7.2). |
| 05 SAM version referencing | `sam_version_id` on each production credit, in force on its credit date (§3.6, §5.1) |
| 06 Data model approach | Work orders as production records, with `ie.production.record` as IE's layer between them and every calculation (TD-05) |
| 07 Operator state | A worker's state is her current bundle: the work order with no end (§4.2). The scan rules keep it to one (§4.4). There is no off-standard state. |
| 08 Library codes | `ie_method_id` on BoM operations; history per line × code from production records (index in §5.1) |
| 10 Off-standard bucket | Grants of minutes with a daily cap; no channels, approvals, overlaps or clipping (§6) |
| 11 Real-time implementation | Partly: the breakdown call (RT-3) is dropped (TD-35). The rest is chunk 4. |
| 13 Defect quantity validation | A constraint per work order on `ie.defect` (§9.1) |

---

## 11. Open items

| ID | Item |
|----|------|
| TD-OPEN-01 | Prompt window and late limit values, and whether the PWA queues: MES phase (FG-OPEN-12) |
| TD-OPEN-02 | Who edits IE parameters in `base.time.parameter` without rights to every other parameter there. Likely an access row plus a record rule limited to IE's codes. Chunk 4. |
| TD-OPEN-05 | The line of an operator-day for workers on several lines in a day: confirm "the line with most earned minutes" in chunk 3. |
| TD-OPEN-06 | Whether provisional time figures are shown before attendance arrives (FG-OPEN-11). With the calendar fallback (§7.3) they are now sensible. |
| TD-OPEN-07 | MO close with quantity producing 0 takes Odoo's automatic-quantity path (§4.4), which P-05 did not time. `mes_capture`'s tests close bundle MOs through it; a slow close would show there. |

**Closed since v0.2:**
- TD-OPEN-03: stations no longer need to identify their line, because the coupon gives the work order and its line.

**Setup before shadow mode** (data, not design):
- Badge IDs for the workers (none set today).
- Odoo users for the line leaders and production managers who grant off-standard time or edit the Worker field.
- The FG-OPEN-10 master data.
- Rule R5 on IE BoMs (TD-36).

**Carried from the fit-gap:**
- FG-OPEN-01, 05, 08, 10, 11, 12, 14, 15 and 16;
- the viability gates V3 (accountant), V4 (planners) and V5 (scanning spike).

**No longer open:**
- OPEN-15 is decided: option B (TD-21).
- FG-13 is withdrawn (TD-35).
- FG-29 is obsolete: IE reads no time rows.

---

## 12. Proposals for the business documents (not applied)

These go through the document workflow (function map, *Document set & workflow*). They replace the lists in v0.2 §11 and in the single-scan note §6. The fit-gap's own list (fit-gap §14) still stands.

**Spec**
1. **§8 rules 3–5.**
   - One scan per bundle operation replaces start and finish scans.
   - The credit is given at the scan and dated by the scan's local date, not the finish date.
   - Removing or changing the credited worker is an edit by an authorised Odoo user, tracked in the MO's chatter. Line leaders may hold that right if they have Odoo users (TC-EM-09 says "unavailable to line leaders").
   - The time category, if ever needed, comes from the scan time.
2. **DEC-17 and §3.2–3.3.**
   - Off-standard time is a grant of minutes per worker and date, entered by authorised users, and approved by being entered.
   - A daily cap per worker applies, set in Settings.
   - There is no work-order pause channel, no overlap rule and no clipping to attendance. Rule 3 is replaced by the cap and NAM ≥ 0.
   - OS-05 is removed from §3.2.
3. **DEC-05 and §9.4–9.5.** Repair earns credit: repaired quantity × the defect's SAM, credited to the repairer when the repair passes re-inspection. A failed repair earns nothing. Repair is no longer off-standard time.
4. **DEC-18 and §3.4.**
   - There is no pausing or finishing at breaks and shift end, and no nightly job.
   - Bundle time is the time between scans, counted inside attendance (option B), or inside the calendar before attendance arrives.
   - Three exception types remain.
5. **§4 (M6, M7) and §13.1.** Pace and coverage include handling time between scans. Coverage can exceed 100% on days with off-standard grants.
6. **§13.2 and DEC-20.**
   - RT-2 loses "off-standard pending approval". "Bundle open > 3 × SAM × qty" becomes "current bundle running past 3 × SAM × qty since its scan".
   - RT-3 is removed.
7. **§12.** "Breakdown calls" and "OS-01 minutes by machine" are removed from the interface to maintenance.
8. **§3.5 and M8 (idle-gap).** Not computable with single scan. It was already a later addition.
9. **OPEN-15** is closed: option B.

**Rationale:** §3 (channels, edge checks), §7 (start and finish scans), §8.3–8.4 (repair) and §15.4 (RT-3) follow the spec changes above.

**Function map:**
- 5.2: one scan per bundle operation;
- 5.5: grants;
- 5.6: repair credit;
- 5.7: time sources;
- 9.2: alerts;
- 9.3: removed.

**Acceptance test cases:**
- TC-TA-01 and TC-TA-02: off-standard entered as grants. The TC-TA-01 numbers are unchanged. TC-TA-02's all-day outage exceeds the cap and is restated.
- TC-TA-03, TC-TA-04 and TC-TA-07: obsolete.
- TC-TA-05: restated as the cap and the NAM floor.
- TC-TA-06: the three exception types.
- TC-TA-08: keeps only the option B row.
- TC-EM-06: B earns 3 × 1.20 = 3.6 when the repair passes, instead of 12 minutes of OS-05. A's DD of 3.6 stays.
- TC-EM-08: dated by the scan.
- TC-EM-09: removal by Worker field edit, tracked in the MO's chatter.
- TC-RT-03: running long since the scan.
- TC-RT-04: obsolete.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-21 | Chunk 1, foundations. Naming, periods, roles and cadence agreed (TD-01 to TD-04). Module map. `ie_base` master data, SAM versions, core extensions, precedence builder, periods, parameter helper and groups. `mes_capture` fields, stop reasons, scan journal, event application, reassignment, endpoint and groups. Production records and their builder. Closes FG-OPEN-03, 06, 07, 09 and 13. |
| 0.2 | 2026-10-21 | Chunk 2, time and quality (TD-15 to TD-26): off-standard bucket with three channels, time accounting per operator-day, attendance completeness, data-quality exceptions, defects and repair. OPEN-15 decided: option B. Nightly pause job withdrawn. |
| 0.3 | 2026-10-21 | **Single-scan capture**, folding in `IE_Design_Note_Single_Scan_v0.1.md` as refined with Peter (TD-27 to TD-36). <br>• **Capture:** one scan per bundle operation, credit at the scan, the next scan ends the previous bundle, re-scan = done, no resume, no Odoo timer, `button_finish` at the next scan, and one stretch per work order. <br>• **Station protocol:** badge then coupon (MES premise), with core's work-order barcode as the coupon. <br>• **Removal and manual credit:** by Worker field edit for the Supervisor group, tracked in the MO's chatter. <br>• **Off-standard:** grants of minutes, approved on entry, with a daily cap in Settings; codes moved to `ie_time`, OS-05 retired. <br>• **Bundle time:** inside attendance, or the calendar before it arrives; counted on the days it falls on; not reduced by grants. <br>• **Exceptions:** cut to three. <br>• **Repair:** earns credit on pass. <br>• **Withdrawn:** the maintenance link (`ie_maintenance`, FG-13). <br>• **Withdrawn or superseded:** TD-07, 09 and 15 to 18; TD-05, 06, 11, 19, 21, 22 and 25 revised. <br>• **Proposals for the business documents** consolidated (§12). |
