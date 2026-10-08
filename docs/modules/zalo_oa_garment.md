# zalo_oa_garment

Zalo notifications for the garment setup: message templates and automation rules for corrective
maintenance requests, their SLA records and quality inspections, sent through `zalo_oa`. Install
it on top of `zalo_oa` and `maintenance_sla_garment`, then give each rule's action its
destinations — the rules ship without any.
Design: `docs/Zalo ↔ Odoo Integration Design Note.md`, §"Configuring notifications" and phase 3.
Pattern: `maintenance_sla_garment`, a preset with no company data in it. Plan: §8.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The whole module: eight templates and rules — new corrective request, paused, restored, technician assigned, SLA at risk, SLA breached, new inspection, inspection awaiting approval or failed — the install hook, tests, readme | done | 2026-10-08, one pass. `-i`, `exit=0`, 9 tests, 0 failures. While writing the tests: `_unregister_hook()` strips every rule's patches, installed ones included, so `setUp` registers them afresh rather than a `tearDown` stripping them (*Tests*). UI checked with the test chat on every action: each rule delivered in Vietnamese — a new corrective request, *Responsible* set, *Waiting for Parts*, *Restored – to Confirm*, the SLA rules at risk and breached, a new inspection, a failing one *chờ duyệt* then *không đạt*; a preventive request sending nothing. The SLA rules' first run notified every running record already past its moment, records of days before among them (D9); accepted, not fixed |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §"Configuring notifications": notifications built in the UI | a module of `noupdate` data and an install hook | The same rules on test and production, versioned and tested; after install they belong to the site, as `maintenance_sla_garment`'s values do |
| 2 | The design's table names destinations (*Maintenance group*, *Maintenance manager*) | the rules ship **without destinations**, and queue nothing until a site adds them | Zalo IDs are a site's business data and `addons/` is public; test and production send to different chats. An action with no destination queues nothing (`zalo_oa`, `_run_action_zalo_multi`), so the module is inert until configured — safe to fail |
| 3 | *Request paused*: filter `sla_live_state = 'paused'` | filter on the two waiting stages | A request counts as paused only when none of its SLA records runs, and one without SLA records never does (`maintenance_sla/models/maintenance_request.py:22-30, 92-96`); the stages are what the notification means |
| 4 | *SLA breached*: time-based on `deadline`, delay 0 | delay **1 minute** | A delay of 0 counts as none, and the automation cron then keeps its 4-hour default (`base_automation/models/base_automation.py:637-639`); any delay under 20 minutes runs it every minute |
| 5 | Three notifications | eight: adds *restored*, *technician assigned*, *SLA at risk*, *new inspection*, *inspection awaiting approval or failed*; all request rules corrective only | Peter's list, 2026-10-08 |

## Decisions

| # | Decision |
|---|---|
| D1 | **Templates and rules are `noupdate` data; rules naming this preset's stages are created by the hook** — `maintenance_sla_garment`'s pattern and the project's safe-to-fail rule: rules 2 and 3 filter on `maintenance_sla_garment`'s stages, which a site may have removed, so `post_init_hook` creates them through `env.ref(..., raise_if_not_found=False)` and skips one whose stages are all missing. Every other reference is to a model or field of a declared dependency, which cannot be missing while it is installed |
| D2 | **Every rule is *On save* (`on_create_or_write`) with its watched fields and filter set explicitly,** or time-based. Odoo's specific triggers (*Stage is set to*, *User is set*) compute their own filter (`base_automation.py:326-360`), which would drop the corrective condition |
| D3 | **A create counts as a change to every watched field** (`base_automation.py:751-753`): rule 1 watches *Created on*, so it fires once per new request; rule 4 also fires when a request is created with a technician already set — a second message beside rule 1's, accepted |
| D4 | **One message per inspection.** Each inspection comes from its own `create()` — one per trigger line per move (`quality_control_mrp_oca/models/mrp_production.py:29-55`, `quality_control_stock_oca/models/stock_move.py:58-66`) — at whatever timing its trigger says, so a rule on creation sees them one at a time. Grouping would need code in `zalo_oa`'s send path; not in this step |
| D5 | **Rule 7 notifies at both failure states:** *Confirm* of a failing inspection sets *Waiting supervisor approval*, the supervisor's *Approve* then *Quality failed* (`quality_control_oca/models/qc_inspection.py:145-165`), so a failing inspection notifies twice, the template wording each. A passing one goes straight to *Quality success* and notifies nothing |
| D6 | **The priority prints as its Vietnamese label, mapped in the template** — a selection renders as its stored value, `2`, otherwise, and a label read through the ORM follows the rendering user's language: the SLA rules run from the automation cron, in its user's. `PRIORITY` below stands for `{'0': 'Rất thấp', '1': 'Thấp', '2': 'Bình thường', '3': 'Cao'}.get(object.priority, '-')`, and `REQUEST_PRIORITY` for the same on `object.request_id.priority` — core's four values (`maintenance/models/maintenance.py:256`) |
| D7 | **The requester is `employee_id`, falling back to `create_uid`:** `employee_id` (`hr_maintenance`) is the employee the request is for; `create_uid` whoever saved it, who may have entered it for them. *Responsible* is `user_id` — the field named *Technician*, labelled *Responsible* on the form (`maintenance/views/maintenance_views.xml:112`) |
| D8 | **Bodies in Vietnamese, names in English.** A template's body is not translated (`zalo_oa` divergence 7), so it is written in the language the chats read; the template names are configuration labels, English as every name in this project's presets. Values the templates print — stage names, SLA rule names, products — appear as stored: on this instance `maintenance_sla_garment`'s stages and rules exist in English only |
| D9 | **The SLA rules' first run catches up, once.** A time-based rule's first `last_run` is empty and counts from 1970 (`base_automation/models/base_automation.py:1006`), so the first check after install notifies every running SLA record already at risk or overdue. Installing also changes the automation cron's interval but not its next run (`:585-589`), so that first check can wait for the cron's previous 4-hour slot. Both accepted: a one-time batch of messages, no wrong data, and none on an instance that installs this module with `maintenance_sla` |

## Folder structure

```
zalo_oa_garment/
├── __init__.py, __manifest__.py, hooks.py
├── data/
│   ├── zalo_template_data.xml
│   └── base_automation_data.xml
├── tests/__init__.py, test_zalo_garment.py
└── readme/ DESCRIPTION.md, USAGE.md
```

No `models/`, `security/` or `views/`: the module adds no model, field, access or view.

## Manifest

| Key | Value |
|---|---|
| `name` | `Zalo Notifications: Garment Manufacturing` |
| `summary` | `Zalo notifications for corrective maintenance, SLA alerts and quality inspections` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Productivity` |
| `depends` | `zalo_oa`; `maintenance_sla_garment` — the stages, and `maintenance_sla`'s SLA records; `maintenance_request_sequence` — the request's `code`; `maintenance_location` — the equipment's `location_id`; `hr_maintenance` — the request's `employee_id`; `quality_control_oca` — `qc.inspection` |
| `data` | `data/zalo_template_data.xml`, `data/base_automation_data.xml` |
| `post_init_hook` | `post_init_hook` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from .hooks import post_init_hook` |
| `tests/__init__.py` | `from . import test_zalo_garment` |

## The notifications

| # | Template / rule / action | Model | Trigger | Watched fields | Filter (`filter_domain`) |
|---|---|---|---|---|---|
| 1 | `template_request_new`, `rule_request_new`, `action_request_new` | `maintenance.request` | *On save* | *Created on* | `[('maintenance_type', '=', 'corrective')]` |
| 2 | `template_request_paused`, `rule_request_paused`, `action_request_paused` | `maintenance.request` | *On save* | *Stage* | corrective, and `stage_id` in *Waiting for Parts* and *Waiting for Production* — by the hook (D1) |
| 3 | `template_request_restored`, `rule_request_restored`, `action_request_restored` | `maintenance.request` | *On save* | *Stage* | corrective, and `stage_id` = *Restored – to Confirm* — by the hook (D1) |
| 4 | `template_request_assigned`, `rule_request_assigned`, `action_request_assigned` | `maintenance.request` | *On save* | *Technician* (`user_id`) | `[('maintenance_type', '=', 'corrective'), ('user_id', '!=', False)]` |
| 5 | `template_sla_at_risk`, `rule_sla_at_risk`, `action_sla_at_risk` | `maintenance.request.sla` | *Based on date field*: *At Risk From* (`risk_at`), 1 minute after | — | `[('state', '=', 'running')]` |
| 6 | `template_sla_breached`, `rule_sla_breached`, `action_sla_breached` | `maintenance.request.sla` | *Based on date field*: *Deadline* (`deadline`), 1 minute after | — | `[('state', '=', 'running')]` |
| 7 | `template_inspection_new`, `rule_inspection_new`, `action_inspection_new` | `qc.inspection` | *On save* | *Created on* | — |
| 8 | `template_inspection_failed`, `rule_inspection_failed`, `action_inspection_failed` | `qc.inspection` | *On save* | *State* | `[('state', 'in', ['waiting', 'failed'])]` |

Numbering here is the module's; Peter's list of 2026-10-08 named *technician assigned* last. The
`maintenance_type` and SLA `state` filters keep preventive requests out: the plans' cron creates
those as the system user.

### Templates — `data/zalo_template_data.xml`

`noupdate="1"`. Each is a `zalo.template` with `name`, `model_id` (the model's `ir.model` XML id) and
`body`, plain text, one message per line break:

| XML id | `name` | `model_id` |
|---|---|---|
| `template_request_new` | *New maintenance request* | `maintenance.model_maintenance_request` |
| `template_request_paused` | *Maintenance request paused* | `maintenance.model_maintenance_request` |
| `template_request_restored` | *Maintenance request restored* | `maintenance.model_maintenance_request` |
| `template_request_assigned` | *Technician assigned* | `maintenance.model_maintenance_request` |
| `template_sla_at_risk` | *SLA at risk* | `maintenance_sla.model_maintenance_request_sla` |
| `template_sla_breached` | *SLA breached* | `maintenance_sla.model_maintenance_request_sla` |
| `template_inspection_new` | *New inspection* | `quality_control_oca.model_qc_inspection` |
| `template_inspection_failed` | *Inspection not passed* | `quality_control_oca.model_qc_inspection` |

Bodies, in Vietnamese (D8; `PRIORITY`, `REQUEST_PRIORITY`: D6):

`template_request_new`
```
Yêu cầu bảo trì mới {{ object.code }}
Thiết bị: {{ object.equipment_id.name or '-' }} ({{ object.equipment_id.serial_no or '-' }})
Vị trí: {{ object.equipment_id.location_id.display_name or '-' }}
Mức ưu tiên: {{ PRIORITY }}
```

`template_request_paused`
```
{{ object.code }} tạm dừng: {{ object.stage_id.name }}
Người phụ trách: {{ object.user_id.name or '-' }}
```

`template_request_restored`
```
{{ object.code }} đã khắc phục, chờ xác nhận
Người yêu cầu: {{ object.employee_id.name or object.create_uid.name }}
Người phụ trách: {{ object.user_id.name or '-' }}
```

`template_request_assigned`
```
{{ object.code }} đã giao cho {{ object.user_id.name }}
Thiết bị: {{ object.equipment_id.name or '-' }}
Mức ưu tiên: {{ PRIORITY }}
```

`template_sla_at_risk`
```
SLA sắp trễ hạn: {{ object.sla_id.name }} – {{ object.request_id.code }}
Mức ưu tiên: {{ REQUEST_PRIORITY }}
Người phụ trách: {{ object.request_id.user_id.name or '-' }}
```

`template_sla_breached`
```
SLA đã trễ hạn: {{ object.sla_id.name }} – {{ object.request_id.code }}
Mức ưu tiên: {{ REQUEST_PRIORITY }}
Người phụ trách: {{ object.request_id.user_id.name or '-' }}
```

`template_inspection_new`
```
Phiếu kiểm tra mới {{ object.name }}
Bài kiểm tra: {{ object.test.name or '-' }}
Tham chiếu: {{ object.object_id.display_name if object.object_id else '-' }}
Sản phẩm: {{ object.product_id.display_name or '-' }}
Số lượng: {{ '%g' % object.qty }}
```

`template_inspection_failed`
```
Phiếu kiểm tra {{ object.name }} {{ 'chờ duyệt' if object.state == 'waiting' else 'không đạt' }}
Bài kiểm tra: {{ object.test.name or '-' }}
Tham chiếu: {{ object.object_id.display_name if object.object_id else '-' }}
Sản phẩm: {{ object.product_id.display_name or '-' }}
Người phụ trách: {{ object.user.name or '-' }}
```

In the XML file the body is the field's text with its lines flush left, so no indentation enters the
message.

### Rules and actions — `data/base_automation_data.xml`

`noupdate="1"`. Rules 1 and 4–8: for each, a `base.automation` with `name` (the template's),
`model_id`, `trigger`, `trigger_field_ids` (`[(6, 0, [ref(<field>)])]`) or `trg_date_id`,
`trg_date_range` 1 and `trg_date_range_type` `minutes`, and `filter_domain`, from the table above;
then an `ir.actions.server` with `name` (the template's), `model_id`, `state` `zalo`, `usage`
`base_automation`, `base_automation_id` the rule, `zalo_template_id` the template, and no
`zalo_destination_ids`.

| Field reference | XML id |
|---|---|
| *Created on*, request | `maintenance.field_maintenance_request__create_date` |
| *Stage*, request | `maintenance.field_maintenance_request__stage_id` |
| *Technician*, request | `maintenance.field_maintenance_request__user_id` |
| *At Risk From*, SLA record | `maintenance_sla.field_maintenance_request_sla__risk_at` |
| *Deadline*, SLA record | `maintenance_sla.field_maintenance_request_sla__deadline` |
| *Created on*, inspection | `quality_control_oca.field_qc_inspection__create_date` |
| *State*, inspection | `quality_control_oca.field_qc_inspection__state` |

Creating the time-based rules sets the automation cron, *Automation Rules: check and execute*, to
every minute (`base_automation.py:576-589`, divergence 4).

## The install hook — `hooks.py`

`post_init_hook(env)` runs `_create_stage_rules(env)`: for rules 2 and 3, from a module-level
constant `STAGE_RULES` — the rule's XML id, its action's, its template's, and its stages' XML ids
(`maintenance_sla_garment.stage_waiting_parts` and `stage_waiting_production`; `stage_restored`):

- skipped when the rule's XML id already resolves, so the hook can run again;
- the stages through `env.ref(xml_id, raise_if_not_found=False)`; none found, skipped;
- otherwise a `base.automation` — *On save*, watching *Stage*, `filter_domain`
  `repr([('maintenance_type', '=', 'corrective'), ('stage_id', 'in', <found ids>)])` — and its
  `ir.actions.server`, as in the data file, each registered under this module's XML id with
  `noupdate=True`.

## Tests — `tests/test_zalo_garment.py`

`TestZaloGarment(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures create
requests and inspections, core records later modules extend. The rules fire through patches
`base_automation` puts on the model classes when the registry loads, and `_unregister_hook()` strips
every one (`base_automation/models/base_automation.py:983-991`) — tests that create a rule call it in
`tearDown`, `zalo_oa`'s template tests among them. So `setUp` registers the rules afresh
(`_unregister_hook()`, then `_register_hook()`) and, when `maintenance.request`'s class had no
patched `create` before, adds a cleanup that strips them again: Odoo's after-test check fails on
attributes a class did not have at `setUpClass` (`odoo/odoo/tests/common.py:1111-1141`). No test
creates a rule, so none needs the `tearDown` of `addons/CLAUDE.md`'s lesson.
Fixtures: a destination, written onto every one of the module's actions — the shipped rules queue
nothing without one; a piece of equipment; a qc test; an archived SLA rule, so it matches no other
request, to which the SLA test attaches its records by hand. Messages are read from `zalo.message`
by `template_id`, `res_model` and `res_id`; nothing is sent, since the send cron does not run in a
test.

| Test | Asserts |
|---|---|
| `test_shipped_without_destinations` | every action of the module has no destination, as installed — read before the fixture writes them (divergence 2) |
| `test_templates_render` | each template renders for a fixture record of its model without error, and the request's `code`, the inspection's `name` and the Vietnamese priority label — not its value — appear where expected |
| `test_new_corrective_request` | a corrective request queues one message from `template_request_new`; a preventive one none |
| `test_paused_and_restored` | a corrective request moved to *Waiting for Parts*, then to *Waiting for Production*, queues two messages from `template_request_paused`; moved to *Restored – to Confirm*, one from `template_request_restored`; a preventive request through the same stages none |
| `test_technician_assigned` | setting `user_id` on a corrective request with none queues one message from `template_request_assigned` naming the technician; clearing it queues none |
| `test_sla_time_rules` | with a running SLA record's `risk_at` and `deadline` set two minutes ago by SQL and the two rules' `last_run` ten minutes ago, `base.automation._check()` queues one message from each template; a paused record with the same dates none |
| `test_inspection_rules` | creating an inspection queues one message from `template_inspection_new`; writing its state *waiting*, then *failed*, queues two from `template_inspection_failed`, worded *chờ duyệt* and *không đạt*; another written *success* none |
| `test_hook_runs_again` | a second `post_init_hook(env)` creates no rule |
| `test_hook_survives_missing_stages` | with rules 2 and 3 and the three stages' XML ids removed, `post_init_hook(env)` completes without error and creates neither rule |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Zalo notifications for a garment plant's maintenance and quality: new corrective requests, pauses for parts or production, restores to confirm, technician assignments, SLA records at risk and breached, new inspections, and inspections awaiting approval or failed — templates and automation rules on top of `zalo_oa` and `maintenance_sla_garment` |
| `readme/USAGE.md` | **Nothing is sent until destinations are added:** in *Settings → Technical → Automation Rules*, open each *Zalo* rule's action and set its destinations — a test chat on a test instance. The rules and templates are a starting point, their text in Vietnamese: after install they belong to the site, and an upgrade does not overwrite them. Stage and SLA rule names print as stored — translate or rename them in Odoo to have them in Vietnamese too. **Technician assigned** fires when *Responsible* is set, also on a new request created with it — leave *Technician* on equipment and *Responsible* on equipment categories empty if assignment should be a manager's explicit step, since core fills a new request's *Responsible* from them. **SLA alerts** arrive within about two minutes of the moment; installing sets the automation cron to run every minute. Its first run after install, which can come up to four hours later, notifies every running SLA record already at risk or overdue, once. **Inspections** notify one by one, as their triggers create them |
