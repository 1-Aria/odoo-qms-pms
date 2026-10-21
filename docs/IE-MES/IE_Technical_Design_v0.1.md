# IE Module — Technical Design

**Version:** v0.1 (draft) · 2026-10-21 · **chunk 1 of 4: foundations**
**Roadmap step:** 6 (technical design)
**Based on:**
- `IE_Business_Logic_Spec_v0.6.md` (the rules of record) and `IE_Framework_Rationale_v0.6.md`;
- `IE_Module_Function_Map.md` (v0.8) and `IE_Acceptance_Test_Cases_v0.3.md`;
- `IE_Fit_Gap_v0.3.md`, whose decisions (FG-xx) this document builds on;
- the Odoo CE 18 core and OCA repositories the instance runs, read 2026-10-21.

**Purpose:** The models, fields, relations, rules and computations that implement the spec on Odoo, module by module. It contains no code. The code-level specification of each module comes later in `docs/modules/<module>.md`, when that module is built.

| Chunk | Content | Status |
|-------|---------|--------|
| **1. Foundations** | Conventions, module map, master data, capture, production records | **This version** |
| 2. Time and quality | Off-standard bucket, attendance and time accounting, data-quality exceptions, defects and repair | To do |
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
   | `pause` | The operator has no open row on this work order. A `stop_reason_id` with `pause_allowed` is required. |
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

## 6. FLAG-TECH items settled by chunk 1

| Flag | How |
|------|-----|
| 02 MO grouping | Lot = the split's procurement group; bundle = MO; OB = BoM; line = `mes_line_id`. Production runs follow in chunk 4. |
| 04 Bundles across days | The local completion date (§4.1) dates the whole record (spec §8 rule 5). |
| 05 SAM version referencing | `sam_version_id` on each production record, in force on its date (§3.6, §5.1) |
| 06 Data model approach | Work orders as production records, with `ie.production.record` as IE's layer between them and every calculation (TD-05) |
| 07 Operator state | The checks in §4.4, with `ie_time` adding off-standard time through the hook |
| 08 Library codes | `ie_method_id` on BoM operations; history per line × code from production records (index in §5.1) |

---

## 7. Open items

| ID | Item |
|----|------|
| TD-OPEN-01 | Prompt window and late limit values, and whether the PWA queues: MES phase (FG-OPEN-12) |
| TD-OPEN-02 | Who edits IE parameters in `base.time.parameter` without rights to every other parameter there. Likely an access row plus a record rule limited to IE's codes. Chunk 4. |
| TD-OPEN-03 | Whether stations identify the line they belong to (a station model) or send it as a label. MES phase. |

Carried from the fit-gap: FG-OPEN-01 (accountant), 05, 08, 10, 11, 12, 14, 15, 16, and OPEN-15.

---

## Change log

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-10-21 | Chunk 1, foundations. Naming, periods, roles and cadence agreed (TD-01 to TD-04). Module map. `ie_base` master data, SAM versions, core extensions, precedence builder, periods, parameter helper and groups. `mes_capture` fields, stop reasons, scan journal, event application, reassignment, endpoint and groups. Production records and their builder. Closes FG-OPEN-03, 06, 07, 09 and 13. |
