# IE Module — Technical Design

**Version:** v0.2 (draft) · 2026-10-21 · **chunks 1–2 of 4: foundations, time and quality**
**Supersedes:** `IE_Technical_Design_v0.1.md` (chunk 1), which is kept as history.
**Roadmap step:** 6 (technical design)
**Based on:**
- `IE_Business_Logic_Spec_v0.6.md` (the rules of record) and `IE_Framework_Rationale_v0.6.md`;
- `IE_Module_Function_Map.md` (v0.8) and `IE_Acceptance_Test_Cases_v0.3.md`;
- `IE_Fit_Gap_v0.3.md`, whose decisions (FG-xx) this document builds on;
- the Odoo CE 18 core and OCA repositories the instance runs, read 2026-10-21.

**Purpose:** The models, fields, relations, rules and computations that implement the spec on Odoo, module by module. It contains no code. The code-level specification of each module comes later in `docs/modules/<module>.md`, when that module is built.

| Chunk | Content | Status |
|-------|---------|--------|
| **1. Foundations** | Conventions, module map, master data, capture, production records | **Written (v0.1)** |
| **2. Time and quality** | Off-standard bucket, attendance and time accounting, data-quality exceptions, defects and repair | **This version** |
| 3. Metrics and pay | Metric family, skill matrix, tiers, PF, thresholds and ramp-up, period record, payroll fields, shadow mode, self-funding | To do |
| 4. The rest | Valuation, line engineering and targets, real-time, parameter catalogue, security summary, computation schedule, test strategy | To do |

**Conventions:** status labels as in the fit-gap: **Agreed** (confirmed by Peter, with date), **Proposed** (designed here, not yet confirmed), **Open** (§7). Source references are `path:line` relative to `Odoo-Build/`.

---

## 0. Decisions

| ID | Decision | Status |
|----|----------|--------|
| TD-01 | **Naming.** IE modules `ie_*`, models `ie.*`, fields on core and OCA models `ie_*`. MES modules `mes_*`, models `mes.*`, fields `mes_*`. The capture layer shared with MES is `mes_capture`. Closes FG-OPEN-03. | Agreed 2026-10-21 |
| TD-02 | **Periods are IE's own `ie.period`:** a month, with a state (open or closed) and a mode (shadow or live). Closes FG-OPEN-06. | Agreed 2026-10-21 |
| TD-03 | **Roles.** IE has four groups: User, Line leader, Engineer, Manager (§3.11). MES has two: Station and Supervisor (§4.7). Valuation rights are set in chunk 4. | IE groups Agreed 2026-10-21; MES groups Proposed |
| TD-04 | **Computation cadence.** Production records are built incrementally by a scheduled job and rebuilt at close. Period figures are computed on demand while the period is open, and frozen at close. Real-time figures are computed live and never stored. | Agreed 2026-10-21 |
| TD-05 | **The insurance layer is a production record per credited work order** (`ie.production.record`, §5), not a daily aggregate. It is IE's denormalised, versioned copy of each finished bundle operation. Every IE calculation reads it, never `mrp.workorder` directly. Daily, family and line figures are groupings of it. | Proposed |
| TD-06 | **One capture journal.** `mes.scan.event` records every scan and every reassignment. It gives idempotency, ordering, rejections and the reassignment audit trail in one place. Closes FG-OPEN-07. | Proposed |
| TD-07 | **Stop reasons live in capture** (`mes.stop.reason`), seeded with the spec's OS-01 to OS-09 (spec §3.2). MES shows them at pause, and IE's off-standard bucket uses them as its codes (chunk 2). | Proposed |
| TD-08 | **Event time.** An event that arrives promptly takes the server time. A queued event takes its device time, corrected by the clock offset the PWA learned. Rows are stamped with the event time. Late events are flagged (§4.4). | Proposed |
| TD-09 | **Operator-state checks run in capture**, with a hook that IE extends for off-standard time (§4.4). | Proposed |
| TD-10 | **The line on the MO is set in capture** (`mes_line_id`). It is re-applied after "Update BoM". Closes FG-OPEN-13. | Proposed |
| TD-11 | **The local completion date** is stored on each finished work order, in the company calendar's timezone (§4.1). | Proposed |
| TD-12 | **SAM versions per method.** BoM operation times follow the current version. A retroactive version rebuilds the production records of open periods only (§3.6). | Proposed |
| TD-13 | **A parameter helper over OCA `base_time_parameter`.** It reads versions explicitly, so 0 and False are real values and a missing value raises. Closes FG-OPEN-09. | Proposed |
| TD-14 | **Badges are resolved with elevated rights.** `hr.employee.barcode` is readable by HR officers only (`odoo/addons/hr/models/hr_employee.py:145`). | Proposed |
| TD-15 | **One off-standard record per operator.** A multi-operator or line-wide entry creates one record per operator, tied by a batch reference (§6.1). | Proposed |
| TD-16 | **Approval by channel.** Channel 1 (pause) is pending until a line leader approves it. Channel 2 (leader entry) is approved on entry by the leader who enters it (spec §3.3). Channel 3 (repair) is approved on creation, because the repair record is its evidence (§6.2). | Proposed |
| TD-17 | **A pause's off-standard period ends at the operator's next scan,** or when a channel-2 record starts. One still open at the end of its day becomes an exception (§6.3, §8.2). | Proposed |
| TD-18 | **No overlaps.** An off-standard record that would overlap the operator's other records or their recorded bundle time is rejected. One that starts while the operator has a bundle open pauses that bundle through capture (§6.1, §6.3). | Proposed |
| TD-19 | **Time accounting per operator-day** (`ie.operator.day`): A, OS by code, NAM, planned minutes and bundle minutes. It is rebuilt by a scheduled job from whatever changed (§7). | Proposed |
| TD-20 | **Attendance completeness is a date on the period** (`attendance_through`). It is set after each import, so monthly and daily imports work the same way (§7.4, FG-21). | Proposed |
| TD-21 | **OPEN-15: option B.** Bundle time counts only inside attendance (§7.3). Pauses at lunch and shift end are therefore no longer needed for the figures, and the nightly pause job and two exception types are dropped (§8). | Agreed 2026-10-21 |
| TD-22 | **Data-quality exceptions are records** with open, resolved and dismissed states. Period close is blocked while any are open, and an IE manager can dismiss one with a note (§8). | Proposed |
| TD-23 | ~~The nightly pause job is optional and off by default.~~ **Withdrawn 2026-10-21:** with option B (TD-21), a bundle left open outside attendance no longer distorts anything, so the job has nothing to fix (§8.4). | Withdrawn |
| TD-24 | **Defects.** One record per bundle × operation, with DD at the SAM credited for that work order, booked on the detection date. FLAG-TECH-13 is a constraint on the model (§9.1). | Proposed |
| TD-25 | **Repair.** A repair record creates its OS-05 off-standard record automatically. The re-inspection result sits on the repair, and failures are counted on the defect (§9.2). | Proposed |
| TD-26 | **QC users record defects and repairs.** IE grants the Quality Control user group access to its own defect and repair models; no foreign model is opened (§9.3). | Proposed |

---

## 1. Modules and dependencies

This map is preliminary; roadmap step 7 finalises it. Chunk 1 defines `mes_capture` and `ie_base` in full.

| Module | Content | Depends on | Chunk |
|--------|---------|------------|-------|
| `mes_capture` | Credited operator, scan rows, stop reasons, the scan journal, operator-state checks, the line on the MO, the local completion date, the scan endpoint | `mrp`, `hr` | 1 |
| `ie_base` | Master data (product types, sections, machine types, families, methods, SAM versions), BoM, operation and line extensions, precedence builder, periods, parameter helper, IE groups, production records and their builder | `mes_capture`, `base_time_parameter` | 1 |
| `ie_time` | Off-standard bucket (three channels), attendance and time accounting, data-quality exceptions | `ie_base`, `hr_attendance` | 2 |
| `ie_quality` | Defects, repair, re-inspection | `ie_time`, `qms_catalog` | 2 |
| `ie_skill` | Metric family, skill matrix, tiers | `ie_quality` | 3 |
| `ie_line` | Station layout, balancing, plateau and targets, production runs, changeover and ramp-up | `ie_base` | 4 |
| `ie_incentive` | PF, ramp-adjusted threshold, excess and units, period record, payroll fields, shadow mode, self-funding check | `ie_skill`, `ie_line` | 3 |
| `ie_valuation` | Extra Unit Cost at close, the rate, the cost pool | `ie_base`, `mrp_account` | 4 |
| `ie_realtime` | RT candidates | `ie_time`, `ie_line` | 4 |
| `ie_maintenance` | Breakdown call (RT-3) | `mes_capture`, `maintenance` | 4 |

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
| Dates | Datetimes are UTC, as Odoo stores them. Every IE grouping by day or period uses a **stored local date** (§4.1). |
| Company | Every IE model with business data carries `company_id`; IE runs in the garment company (FG-31). |
| Access | No module grants another domain's models through `ir.model.access` rows. Cross-domain reads are covered by role assignment, and a view element that reads a foreign model names the group granting that read. |
| Rights | Writes that IE performs as a system (builders, scheduled jobs) run as superuser. User actions run as the user. |
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
- **Lookup.** `ie.method._ie_sam_at(date)` returns the version with the latest `date_from ≤ date`. A production record uses the version in force on its local completion date (spec §5.2).
- **Expected durations.** Whenever a method's versions change, `time_cycle_manual` on the BoM operations that reference it is set to the current SAM. This affects only Odoo's expected durations (rule R1).
- **Retroactive versions.** Creating, changing or deleting a version rebuilds the production records of that method in **open** periods (§5.2). Records in closed periods are never touched (spec §5.2, TC-EM-07).

### 3.7 Extensions of core models

| Model | Field | Type | Notes |
|-------|-------|------|-------|
| `mrp.bom` | `ie_product_type_id` | Many2one `ie.product.type` | the OB's product type (FG-19), the plateau key |
| `mrp.bom` | `ie_workflow_code` | Char | the timeSSD workflow code, for traceability |
| `mrp.routing.workcenter` | `ie_method_id` | Many2one `ie.method` | the OB operation's library method. Choosing it fills `name` and `time_cycle_manual` (current SAM) and sets `time_mode = manual`. |
| `mrp.routing.workcenter` | `ie_family_id`, `ie_section_id` | related | display only |
| `mrp.workcenter` | `ie_is_line` | Boolean | marks a sewing line |
| `mrp.workcenter` | `ie_config_warning` | Char, non-stored compute | set when an IE line has `default_capacity ≠ 1`, product capacities, or `costs_hour ≠ 0` (rules R1 and R2). Shown as a warning banner on the form; it does not block. |

### 3.8 Precedence builder (FG-20)
`mrp.bom.action_ie_build_dependencies()`, a button on the BoM:
1. Sets `allow_operation_dependencies = True`.
2. Within each section, links every operation to the one before it, in sequence order.
3. The first operation of the assembly stage waits for the last operation of every preparation section.
4. The first operation of the finishing stage waits for the last assembly operation.
5. Existing links are replaced.

Running it is optional: the IE can always set "Blocked By" on the operations by hand. Fit-gap §7.2 gives the rule, and the prototype BoM proved it (fit-gap §13.2, P-02).

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
- **Closing,** and what it freezes, is in chunk 3. Chunk 1 needs only the state, because builders skip closed periods.

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
| `ie_base.group_ie_line_leader` | User | Off-standard approvals (chunk 2) |
| `ie_base.group_ie_engineer` | User | Master data and SAM |
| `ie_base.group_ie_manager` | Engineer, Line leader | Periods, parameters, approvals |

| Model | User | Engineer | Manager |
|-------|------|----------|---------|
| `ie.product.type`, `ie.section`, `ie.machine.type`, `ie.family`, `ie.method`, `ie.sam.version` | read | read, write, create, unlink | all |
| `ie.period` | read | read | read, write, create |
| `ie.production.record` | read | read | read |

Production records are written only by the builder, which runs as superuser.

---

## 4. `mes_capture`: capture

### 4.1 Extensions of core models

| Model | Field | Type | Notes |
|-------|-------|------|-------|
| `mrp.workorder` | `mes_employee_id` | Many2one `hr.employee`, index | The **credited operator** (FG-04). Set by the first start; changed only by a reassignment (§4.5). |
| `mrp.workorder` | `mes_date_local` | Date, stored compute | The **local completion date** (TD-11). Computed only when `state == 'done'`, from `date_finished` in the timezone of the company's working calendar (`company.resource_calendar_id.tz`, Asia/Ho_Chi_Minh). Before `done`, `date_finished` is the planned end (`odoo/addons/mrp/models/mrp_workorder.py:82-85`), so the field stays empty. |
| `mrp.workcenter.productivity` | `mes_employee_id` | Many2one `hr.employee`, index | Who scanned this row. Ordinary `copy=True`, so it survives Odoo's "Reduced Speed" split (`mrp_workcenter.py:588-604`). Empty on rows that Odoo itself creates for unscanned work orders (FG-29). |
| `mrp.production` | `mes_line_id` | Many2one `mrp.workcenter` | The **line of the bundle** (FG-25). Copied by the split (`_split_productions` uses `copy_data`). Writing it sets `workcenter_id` on the MO's work orders that have not started. Core refuses the change for started work orders (`mrp_workorder.py:475-480`). |

**After "Update BoM"** (TD-10): `mrp.production._link_bom` is extended. It calls super, which resets the work orders' work centres to the BoM's (`odoo/addons/mrp/models/mrp_production.py:2570-2571`), then re-applies `mes_line_id`.

### 4.2 `mes.stop.reason` (TD-07)

| Field | Type | Notes |
|-------|------|-------|
| `code` | Char | unique, e.g. `OS-01` |
| `name` | Char | translate |
| `pause_allowed` | Boolean | Offered to operators at pause (channel 1). The spec's channel-1 cases are breakdown and material wait (spec §3.3). |
| `active` | Boolean | |

- **Seeded data** (`noupdate`): OS-01 to OS-09 with the spec's names (spec §3.2). `pause_allowed` is True for OS-01 and OS-02. These are the project's own vocabulary, not guessed configuration, and the IE edits them freely.
- **Extensions elsewhere:** `ie_time` adds the off-standard semantics (chunk 2), and `ie_maintenance` adds "opens a maintenance request" (chunk 4).

### 4.3 `mes.scan.event`: the capture journal (TD-06)

| Field | Type | Notes |
|-------|------|-------|
| `uuid` | Char | client event ID, **unique**, required |
| `event_type` | Selection | `start` / `pause` / `resume` / `finish` / `reassign` |
| `workorder_id` | Many2one `mrp.workorder` | required, index |
| `employee_id` | Many2one `hr.employee` | the operator, resolved from the badge. For `reassign`, the new operator. |
| `previous_employee_id` | Many2one `hr.employee` | `reassign` only |
| `stop_reason_id` | Many2one `mes.stop.reason` | `pause` only |
| `badge` | Char | the badge as scanned |
| `station` | Char | device or station label, as sent |
| `device_time` | Datetime | the device's time, converted to UTC |
| `clock_offset` | Float | seconds, server minus device, as learned by the PWA |
| `received_at` | Datetime | server time on arrival |
| `event_time` | Datetime | the time applied (§4.4) |
| `late` | Boolean | arrived later than the late limit |
| `state` | Selection | `applied` / `rejected` |
| `message` | Char | rejection reason, or the message shown on the station |
| `user_id` | Many2one `res.users` | the station or supervisor user who sent it |
| `note` | Text | `reassign` only |
| `company_id` | Many2one | |

**Index:** `(employee_id, event_time)`. The journal is append-only: nobody edits or deletes events.

### 4.4 Applying an event
`mes.scan.event.mes_submit(payload)` is a model method, called by the endpoint (§4.6) and by tests. It returns `{status, message, event_time, server_time}`, where `status` is `applied`, `duplicate` or `rejected`.

1. **Duplicate.** If the `uuid` exists, the method returns its stored outcome and does nothing else, so a queue can resend safely.
2. **Operator.** The badge is resolved with elevated rights (TD-14) to an active `hr.employee` of the company. An unknown badge is rejected.
3. **Time** (TD-08):
   - `corrected = device_time + clock_offset`.
   - If `received_at − corrected ≤` the prompt window, `event_time = received_at`. Otherwise `event_time = corrected`.
   - `late` is set when `received_at − corrected >` the late limit.
   - The prompt window `[P 30 s]` and the late limit `[P 15 min]` are parameters; MES confirms their values (FG-OPEN-12).
4. **Order.** An event earlier than the operator's last applied event is rejected as out of order. A FIFO queue keeps events in order.
5. **Checks, by type** (TD-09, spec §3.3 rule 2, FLAG-TECH-07). An operator's open row is a time row with their `mes_employee_id` and no `date_end`.

   | Type | Rejected when |
   |------|---------------|
   | `start` | The work order is done or cancelled; it is credited to another operator; the operator has an open row anywhere; or the hook `_mes_check_operator_free(employee, event_time)` returns a message. `ie_time` extends the hook: no start during off-standard time. |
   | `resume` | As `start`, and the work order must already be credited to this operator. |
   | `pause` | The operator has no open row on this work order. A pause sent from a station needs a `stop_reason_id` with `pause_allowed`. |
   | `finish` | The work order is credited to another operator, or is done. Finishing a paused work order is allowed. |

6. **Apply,** as the sending user, through core's methods so that Odoo's own state handling runs (MO start, calendar leave, dependencies, component consumption):
   - **start / resume:** `button_start()`. Then the row it opened gets `date_start = event_time` and `mes_employee_id`. On the first start the work order gets `mes_employee_id`.
   - **pause:** `button_pending()`. Then the row it closed gets `date_end = event_time`.
   - **finish:** `button_finish()`.
     - Every row it closed gets `date_end = min(date_end, event_time)`.
     - A row that would then start after `event_time` is deleted. Only Odoo's "Reduced Speed" split can produce one.
     - The work order's `date_finished` is set to `event_time`.
7. **After.** The event is stored with its state and message. The hook `_mes_after_apply(event)` lets other modules react: `ie_time` turns a pause into a pending channel-1 off-standard record (chunk 2), and `ie_maintenance` turns an OS-01 pause into a request (chunk 4).

For prompt events the stamping changes the times by milliseconds. It matters only for queued ones.

**System pauses** (added in v0.2): `mes.scan.event._mes_system_pause(employee, at, note)`.
- It closes the operator's open row at `at` and journals a `pause` event without a stop reason.
- Its callers are off-standard entry (§6.3) and reassignment (§4.5).
- With no stop reason, no channel-1 off-standard record results.

### 4.5 Reassignment (spec §8 rule 3, TC-EM-09)
A `reassign` event is sent by a supervisor (§4.7) for a work order that is not done.
1. If the previous operator has an open row on the work order, it is closed at `event_time`. No stop reason is recorded, so no off-standard time results.
2. `mes_employee_id` becomes the new operator, and the event records `previous_employee_id`.

The previous operator's rows stay as history but no longer count as this bundle's time (§5.1). The whole bundle goes to the operator who finishes it. The event is the audit record: supervisor, time, both operators, the bundle.

### 4.6 Endpoint
- `POST /mes/scan` (`type='json'`, `auth='user'`) calls `mes_submit` with one payload.
- `POST /mes/scan/batch` takes a list, applied in order, for a queue flush. It returns one result per event.

The routes only parse and delegate. Their wiring is checked with `curl`, because this image cannot run `HttpCase` tests. The PWA itself belongs to the MES phase.

### 4.7 Groups and access
Category "MES".

| Group | Implies | Holds |
|-------|---------|-------|
| `mes_capture.group_mes_station` | `mrp.group_mrp_user` | Sending scans. Station devices and the line leaders who scan for operators. |
| `mes_capture.group_mes_supervisor` | Station | Reassignment, reading the journal |

| Model | Station | Supervisor | `mrp.group_mrp_manager` |
|-------|---------|------------|-------------------------|
| `mes.scan.event` | create; read own | create, read | read |
| `mes.stop.reason` | read | read | all |

- The work-order, time-row and MO fields follow core's manufacturing rights.
- `mes_employee_id` on the work order is read-only in views. It changes only through events.
- **The prototype measured station rights:** `mrp.group_mrp_user` suffices to start, pause and finish work orders, including the calendar leaves that creates (fit-gap §13).

---

## 5. `ie_base`: production records (TD-05)

### 5.1 `ie.production.record`
One record per finished work order that has a credited operator: spec §2's "production record", operator × operation × bundle. It is a snapshot. Master data changes after close do not alter it.

| Field | Type | Source |
|-------|------|--------|
| `workorder_id` | Many2one `mrp.workorder` | **unique**, `ondelete='cascade'` |
| `production_id` | Many2one `mrp.production` | the bundle |
| `employee_id` | Many2one `hr.employee` | `mes_employee_id`, the credited operator |
| `date` | Date | `mes_date_local`, the local completion date |
| `date_finished` | Datetime | the work order's `date_finished` |
| `period_id` | Many2one `ie.period` | the period of `date` |
| `line_id` | Many2one `mrp.workcenter` | the work order's `workcenter_id` |
| `bom_id`, `product_tmpl_id` | Many2one | the OB and the style |
| `operation_id` | Many2one `mrp.routing.workcenter` | the OB operation |
| `method_id` | Many2one `ie.method` | `operation_id.ie_method_id`. Its code is the library code used for familiarity (FLAG-TECH-08). |
| `family_id`, `machine_type_id`, `section_id`, `product_type_id` | Many2one | from the method, and the BoM for the product type |
| `grade` | Selection | snapshot of `family_id.grade` |
| `skill_evaluated` | Boolean | snapshot of the family's flag |
| `qty` | Float | the work order's `qty_produced`, the bundle quantity credited (DEC-04) |
| `sam_version_id`, `sam` | Many2one, Float (16, 4) | the method's version in force on `date` (§3.6) |
| `em_gross` | Float (16, 4) | `qty × sam` (spec §2, EM_g per record) |
| `active_minutes` | Float (16, 4) | sum of `date_end − date_start` over the work order's closed rows whose `mes_employee_id` is the credited operator (FG-29). Rows without an employee, and other operators' rows, do not count. |
| `company_id` | Many2one | |

**Indexes:**
- `(employee_id, date)` for operator-days;
- `(line_id, date)` for lines;
- `(method_id, line_id, date)` for familiarity over 90 days;
- `(family_id, employee_id)` for skill;
- `(period_id)`.

**Expected size:** about 42,000 records a month and 500,000 a year (fit-gap §13.1).

**Clipping.** `active_minutes` is raw scan time. Clipping to attendance (OPEN-15 option B, if chosen) happens in time accounting, which has the attendance (chunk 2).

### 5.2 Builder
`ie.production.record._ie_build(workorders)` writes the records. It runs as superuser.

- **Qualifying work orders:** `state == 'done'`, `mes_employee_id` set, operation with an `ie_method_id`.
- **For each one:**
  1. Find the period of `mes_date_local`. If it is **closed**, skip.
  2. Otherwise create or update the record from the sources above.
- **A record whose work order no longer qualifies,** in an open period, is deleted.

It is called from three places:

| Caller | Candidates |
|--------|-----------|
| Scheduled job, every `[P 5 min]` (`ir.cron`, editable) | Work orders whose `write_date`, or the `write_date` of any of their time rows, is at or after the watermark. The watermark is an `ir.config_parameter`, advanced to the job's start time on success. |
| A SAM version created, changed or deleted (§3.6) | The method's records in open periods |
| Period close (chunk 3) | Every qualifying work order of the period, before it is frozen |

**Not built:** a finished work order without a credited operator, which happens when nobody scanned it and the MO's close finished it (`mrp_production.py:2129`). It earns no one anything and appears on the data-quality exception list (chunk 2) as "work order finished without a scan".

---

## 6. `ie_time`: the off-standard bucket (spec §3.2–3.3, DEC-17, FLAG-TECH-10)

### 6.1 `ie.offstandard`

| Field | Type | Notes |
|-------|------|-------|
| `employee_id` | Many2one `hr.employee` | required, index |
| `stop_reason_id` | Many2one `mes.stop.reason` | required: the OS code |
| `channel` | Selection | `pause` / `leader` / `repair`, required |
| `date_start` | Datetime | required |
| `date_end` | Datetime | Empty while running: a pause until the next scan, or an ongoing line stop |
| `minutes` | Float (16, 4) | stored compute, `date_end − date_start`. 0 while open. |
| `state` | Selection | `pending` / `approved` / `rejected` (TD-16) |
| `approved_by`, `approved_at` | Many2one `res.users`, Datetime | The audit by approving leader (spec §3.3 rule 4) reads these |
| `line_id` | Many2one `mrp.workcenter` | channel 1: the work order's line; channel 2: entered; channel 3: the bundle's line |
| `workorder_id`, `scan_event_id` | Many2one | channel 1: the paused work order and its pause event |
| `repair_id` | Many2one `ie.repair` | channel 3 |
| `batch_ref` | Char | channel 2: shared by the records of one multi-operator entry (TD-15) |
| `date` | Date | local date of `date_start`, stored |
| `note` | Text | |
| `company_id` | Many2one | |

**Constraints** (TD-18):
- SQL CHECK: `date_end > date_start` when set.
- No overlap with the same operator's other records that are not rejected (TC-TA-04).
- No overlap with that operator's closed scan rows. A retroactive entry over recorded bundle time is rejected, naming the bundle.
- Approved and rejected records are edited by IE managers only.

**Entry form.** The leader's entry form (`ie.offstandard.entry`, transient) takes operators, start, end, code and note, and creates one record per operator. A line-wide stop, such as OS-04, pre-selects the operators active on the line that day (§7.1).

### 6.2 Channels

| Channel | Created by | Starts | Ends | State |
|---------|-----------|--------|------|-------|
| 1 `pause` | the capture hook on a pause event with a stop reason (§4.4 step 7), as superuser | the pause's event time | the operator's next scan of any work order, or the start of a channel-2 record (TD-17) | `pending`; a line leader approves or rejects it |
| 2 `leader` | the line leader, through the entry form | as entered | as entered, or set later for an ongoing stop | `approved` by the leader who entered it (spec §3.3: "entering it counts as approving it") |
| 3 `repair` | a repair record (§9.2) | the repair's start | the repair's end | `approved` |

- Only **approved** records count (spec §3.3 rule 1). A rejected or still-pending pause stays in NAM, and a pending one becomes an exception at the end of its day (TC-TA-03).
- Downstream logic reads the records, never the channel (spec §3.3 rule 5).

### 6.3 Interplay with capture
- **`_mes_check_operator_free(employee, at)`** (§4.4 step 5) is extended. It rejects a start or resume while a channel-2 or channel-3 record that is not rejected covers `at`, with the message "Off-standard OS-0x since hh:mm".
- **`_mes_after_apply(event)`** is extended:
  - A pause with a stop reason creates the channel-1 record, pending, starting at the event time.
  - A start, resume or finish ends the operator's open channel-1 record at the event time.
- **A channel-2 record that starts while the operator has a bundle open** closes it through a system pause at the record's start (§4.4). The bundle is paused automatically, as TC-TA-04 requires.
- **A channel-2 record that starts while the operator has an open channel-1 record** ends that record at its start.

---

## 7. `ie_time`: attendance and time accounting (spec §3.1, §3.4, DEC-18)

### 7.1 `ie.operator.day`

| Field | Type | Notes |
|-------|------|-------|
| `employee_id` | Many2one `hr.employee` | required |
| `date` | Date | local, required. Unique together with `employee_id`. |
| `period_id` | Many2one `ie.period` | |
| `line_id` | Many2one `mrp.workcenter` | the line with most of the day's earned minutes, used for line figures. Chunk 3 confirms this for operators who work several lines in a day. |
| `attendance_arrived` | Boolean | `date ≤ period.attendance_through` (§7.4) |
| `attended_minutes` | Float (16, 4) | A |
| `offstandard_minutes` | Float (16, 4) | OS: approved records, clipped to attendance |
| `nam` | Float (16, 4) | `A − OS`, never below 0 |
| `planned_minutes` | Float (16, 4) | the calendar's planned working minutes, for provisional display (FG-OPEN-11) |
| `bundle_minutes` | Float (16, 4) | Σ `counted_minutes` of the day's production records (§7.3) |
| `offstandard_line_ids` | One2many `ie.operator.day.offstandard` | OS by code |
| `company_id` | Many2one | |

The child model `ie.operator.day.offstandard` holds `day_id`, `stop_reason_id`, `channel` and `minutes`. It gives OS by code and channel for M5, the payroll feed (spec §12) and the audit by channel. Chunk 3 adds the metric fields (EM, DD, efficiencies) to the operator-day.

### 7.2 One operator-day, computed
The window is the local day [d 00:00, d+1 00:00) in the company calendar's timezone, converted to UTC.
1. **Attendance intervals:** each `hr.attendance` of the operator that overlaps the window, cut to the window, minus the lunch intervals of the operator's calendar (`employee._employee_attendance_intervals(start, stop, lunch=True)`, `odoo/addons/hr/models/hr_employee.py:644-650`).
2. **A** = the total length of those intervals. This is the same as core's `_get_worked_hours_in_range` (`odoo/addons/hr_attendance/models/hr_attendance.py:220-242`), and it counts night shifts in the day they fall in.
3. **OS:** for each approved record overlapping the window, the length of its interval ∩ the attendance intervals (spec §3.3 rule 3, TC-TA-05), summed and grouped by code into the child lines.
4. **NAM** = A − OS.
5. **`planned_minutes`** = `employee._get_expected_attendances(start, stop)` within the window (`hr_employee.py:652`).
6. **`bundle_minutes`** = Σ `counted_minutes` of the production records dated d.

Until attendance arrives, A and NAM hold what exists so far, and `attendance_arrived = False` marks them as provisional.

### 7.3 Bundle time and attendance (OPEN-15, TD-21)
`ie_time` adds **`counted_minutes`** (Float 16, 4) to `ie.production.record`. It is the bundle time every family split and diagnostic uses.

**Option B (decided 2026-10-21):** `counted_minutes` is the credited operator's scan rows on that work order, intersected with the attendance intervals. It equals `active_minutes` until attendance arrives.
- A bundle left open over an unpaid lunch or overnight corrects itself: 20 minutes instead of 80 (TC-TA-08 keeps only its option B row).
- It costs the same intersection as clipping off-standard time.
- It keeps attendance as the single clock (DEC-18).
- Bundle time that counts lies inside attendance and never overlaps off-standard time (§6.1), so it can never exceed NAM. Coverage (M7) stays at or below 100% by construction.

The cost the spec names (§3.4 item 4): work done during an unpaid break keeps its pieces but loses its minutes, so the family split and the diagnostics count slightly less time for that family. Pay is unaffected.

**What option B changes on the shop floor:**
- Pausing or finishing bundles at lunch and shift end is no longer needed for the figures. Neither is a job that does it for them.
- **What still matters:**
  - **Pauses with a reason.** A breakdown or a material wait is how an operator gets protected time (channel 1). Option B does not replace that.
  - **One open bundle per operator.** An operator who left a bundle open must finish or pause it before starting a different one. Capture rejects the start and says which bundle is open.
  - **A forgotten bundle is credited only when finished.** Its pieces and minutes land on the day it is finished.
  - **Attendance accuracy.** Option B makes attendance the clock for bundle time as well, so a missing or wrong punch would cut bundle time. `scan_outside_attendance` (§8.2) catches that.
- **Real-time figures,** which run without attendance, clip live bundle time by the calendar's breaks instead (chunk 4).

### 7.4 Attendance completeness (TD-20)
`ie_time` adds **`attendance_through`** (Date) to `ie.period`: the last date with complete attendance.
- An IE manager sets it after each import, or the import pipeline writes it.
- Days up to that date are final-able and get the attendance-based exceptions (§8.2).
- Days after it stay provisional.

This works the same for monthly and daily imports (FG-21).

### 7.5 Builder
`ie.operator.day._ie_build(pairs)` runs as superuser. It also recomputes `counted_minutes` on the production records of those pairs.

**When it runs:**
- **A scheduled job every `[P 15 min]`.** It takes the (operator, date) pairs whose sources changed since its watermark: `hr.attendance` (every date an attendance touches), `ie.offstandard`, `ie.production.record`, and every day of a period whose `attendance_through` moved.
- **At period close** (chunk 3).
- **The manager's "Recompute period" action.** Deleted attendances leave no `write_date`, so only the close and this action catch them.

Closed periods are skipped. Within one run the order is: production records (§5.2), then operator-days, then exceptions (§8).

---

## 8. `ie_time`: data-quality exceptions (spec §3.4)

### 8.1 `ie.exception` (TD-22)

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

| Type | Raised when | Needs attendance | Basis |
|------|-------------|------------------|-------|
| `unapproved_pause` | a channel-1 record is still pending at the end of its day | no | spec §3.4, TC-TA-03 |
| `open_offstandard` | an off-standard record has no end at the end of its day | no | §6.2 |
| `unscanned_workorder` | a work order finished without a credited operator | no | FG-29, §5.2 |
| `late_event` | a scan event was flagged late | no | TD-08 |
| `rejected_queued_event` | a rejected event that arrived late, so the operator never saw the rejection | no | §4.4 |
| `scan_outside_attendance` | a scan event happened outside the operator's attendance intervals: a missing check-in, a wrong punch, or work off the clock | yes | spec §3.4, TC-TA-06 |

Two types from spec §3.4 item 5 are **dropped under option B** (TD-21):
- **"Bundle open at clock-out"** no longer distorts anything, because the time outside attendance does not count.
- **"Coverage above 100%"** can no longer happen (§7.3).

- **Detection** is a job that runs after the operator-day build. Attendance-based types are checked only for days up to `attendance_through`.
- **When the condition no longer holds** (the pause is approved, the end is set), the exception resolves itself.
- **A line leader resolves** an exception by fixing its cause. **An IE manager can dismiss** one with a note.

### 8.3 Close
Period close (chunk 3) is blocked while the period has open exceptions. TC-TA-06 leaves "blocked or warned" to technical design: blocked is chosen, with dismissal as the escape.

### 8.4 No nightly pause job (TD-23 withdrawn)
Spec §3.4 item 3 offered an optional job that pauses bundles left open. Under option B there is nothing for it to correct, so IE has no such job, and nothing is ever paused automatically. TC-TA-07 becomes obsolete.

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
| `employee_id` | Many2one `hr.employee` | set at creation: the work order's credited operator when `responsibility = operator`, otherwise empty |
| `sam` | Float (16, 4) | the SAM credited for this bundle × operation, i.e. its production record's `sam`. Before the work order is finished, the method's SAM on the detection date. |
| `k_def` | Float | the parameter `ie.k_def` on the detection date |
| `dd` | Float (16, 4) | `qty × sam × k_def` when `employee_id` is set, else 0 (spec §9.3) |
| `period_id` | Many2one `ie.period` | the detection date's period: DD is booked there |
| `state` | Selection | `open` / `closed`; a passing re-inspection closes it |
| `reinspection_failures` | Integer | failed re-inspections, the repairer diagnostic (spec §9.5) |
| `company_id` | Many2one | |

**Rules:**
- **FLAG-TECH-13.** A work order's defects may total at most its quantity: `qty_produced` once finished, `qty_production` before. A record that would exceed it is rejected with an error and nothing of it is booked (TC-EM-03). This is a constraint on `qty` and `workorder_id`. Two inspectors booking the same bundle at the same instant could both pass, and that is accepted.
- **Booking.** DD is booked on the detection date, and closed periods are never reopened (TC-EM-02).
- **Every family.** DD applies to every family, skill-evaluated or not (TC-EM-05).
- **Why a snapshot.** `employee_id` is set at creation, not computed, so a later reassignment cannot move a deduction already booked.

### 9.2 `ie.repair` (TD-25)

| Field | Type | Notes |
|-------|------|-------|
| `defect_id` | Many2one `ie.defect` | required |
| `employee_id` | Many2one `hr.employee` | the repairer, required |
| `production_id`, `workorder_id` | Many2one | related from the defect, stored |
| `qty` | Float | > 0, at most the defect's quantity |
| `date_start`, `date_end` | Datetime | required |
| `result` | Selection | `pending` / `pass` / `fail`, default `pending` |
| `offstandard_id` | Many2one `ie.offstandard` | its OS-05 record, read-only |
| `company_id` | Many2one | |

**Rules:**
- **The OS-05 record.** Creating a repair creates its channel-3 OS-05 record (stop reason `OS-05`, seeded in §4.2) for the repairer over the repair's interval, approved. Changing the dates or the repairer updates it, and deleting the repair deletes it. The record obeys §6.1, so a repair recorded over the repairer's own bundle time is rejected.
- **Neutral.** The repair earns nothing and costs nothing (spec §9.4). The defect's DD stays, with no earn-back.
- **Re-inspection.** `pass` closes the defect. `fail` adds 1 to `reinspection_failures` and leaves the defect open for another repair, with no further deduction for anyone (spec §9.5, TC-EM-06).

### 9.3 Access (TD-26)

| Model | QC user (`quality_control_oca.group_quality_control_user`) | IE user | IE line leader | IE manager |
|-------|-----------|---------|----------------|------------|
| `ie.defect` | read, create, write | read | read | all |
| `ie.repair` | read, create, write | read | read, create, write | all |
| `ie.offstandard` | — | read | read, create, write, approve | all |
| `ie.operator.day` and its lines | — | read | read | read |
| `ie.exception` | — | read | read, resolve | all, including dismiss |

- Inspectors hold their own domain group, as the role matrix has it. IE grants that group access to IE's own two models, and nothing foreign is opened.
- Channel-1 records are created by the capture hook as superuser. Channel-3 records are created by the repair, as superuser.

### 9.4 What stays in QMS
Formal QC inspections and nonconformities stay in the QMS suite. IE's defects are the attribution records for pay and skill. They use the same `qms_catalog` codes, so quality reporting can combine both.

---

## 10. FLAG-TECH items settled by chunks 1–2

| Flag | How |
|------|-----|
| 02 MO grouping | Lot = the split's procurement group; bundle = MO; OB = BoM; line = `mes_line_id`. Production runs follow in chunk 4. |
| 03 Family time from scans | `active_minutes` comes from the credited operator's scan rows only (§5.1). `counted_minutes` applies OPEN-15 (§7.3). |
| 04 Bundles across days | The local completion date (§4.1) dates the whole record (spec §8 rule 5). |
| 05 SAM version referencing | `sam_version_id` on each production record, in force on its date (§3.6, §5.1) |
| 06 Data model approach | Work orders as production records, with `ie.production.record` as IE's layer between them and every calculation (TD-05) |
| 07 Operator state | Capture's checks (§4.4), plus off-standard time through the hook (§6.3) |
| 08 Library codes | `ie_method_id` on BoM operations; history per line × code from production records (index in §5.1) |
| 10 Off-standard bucket | One model, three channels, overlap and attendance rules, the leader's entry form, exceptions; no nightly job under option B (§6–8) |
| 13 Defect quantity validation | A constraint per work order on `ie.defect` (§9.1) |

---

## 11. Open items

| ID | Item |
|----|------|
| TD-OPEN-01 | Prompt window and late limit values, and whether the PWA queues: MES phase (FG-OPEN-12) |
| TD-OPEN-02 | Who edits IE parameters in `base.time.parameter` without rights to every other parameter there. Likely an access row plus a record rule limited to IE's codes. Chunk 4. |
| TD-OPEN-03 | Whether stations identify the line they belong to (a station model) or send it as a label. MES phase. |
| TD-OPEN-05 | The line of an operator-day for operators who work several lines in a day: confirm "the line with most earned minutes" in chunk 3. |
| TD-OPEN-06 | Whether provisional time figures are shown before attendance arrives (FG-OPEN-11). `planned_minutes` is stored for it either way. |

Carried from the fit-gap: FG-OPEN-01 (accountant), 05, 08, 10, 11, 12, 14, 15, 16. OPEN-15 is decided: option B (TD-21).

**For the business documents** (proposals, to go through the document workflow):
- spec §3.4 items 3–5 and OPEN-15: option B, no nightly job, two exception types dropped;
- test cases TC-TA-06 to TC-TA-08 adjusted accordingly.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-21 | Chunk 1, foundations. Naming, periods, roles and cadence agreed (TD-01 to TD-04). Module map. `ie_base` master data, SAM versions, core extensions, precedence builder, periods, parameter helper and groups. `mes_capture` fields, stop reasons, scan journal, event application, reassignment, endpoint and groups. Production records and their builder. Closes FG-OPEN-03, 06, 07, 09 and 13. |
| 0.2 | 2026-10-21 | Chunk 2, time and quality (TD-15 to TD-26). `ie_time`: the off-standard bucket (one record per operator, approval by channel, the pause period ending at the next scan, no overlaps, interplay with capture); time accounting per operator-day (A, OS by code, NAM, planned and bundle minutes); OPEN-15 option B recommended (`counted_minutes`); attendance completeness on the period; data-quality exceptions with close blocking; the nightly pause job. `ie_quality`: defects with DD at the credited SAM and the FLAG-TECH-13 constraint, repairs creating OS-05, re-inspection, access for QC users. Capture amended: station pauses need a stop reason, and system pauses exist. |
| 0.2 rev. | 2026-10-21 | OPEN-15 decided: option B (TD-21 Agreed), with its shop-floor consequences (§7.3). Nightly pause job withdrawn (TD-23); exception types "bundle open at clock-out" and "coverage above 100%" dropped (§8.2). TD-OPEN-04 closed. |
