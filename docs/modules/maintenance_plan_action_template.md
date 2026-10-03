# maintenance_plan_action_template

Action templates on a maintenance plan: every request the plan generates gets one
management-system action per template, linked to it.
Plan: §7.14, §8, D19, D22, D23, O6.

The preventive counterpart of `qms_determination`'s *Generate Actions*: a corrective request
reaches its actions through a nonconformity, a preventive one through its plan. Independent of
the QMS chain and of the SLA cluster.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The whole module: `action_template_ids` on the plan, action generation in the request's `create()`, the plan form page, tests, readme | done | 2026-10-03, one pass. `exit=0`, 7 tests, 0 failures; UI checked: a typed and an untyped template on a plan, manual generation giving each request one action from the typed template, due on its scheduled date and linked back; nothing from the untyped one |

## O6, checked

Generation still routes through `maintenance.request.create()` with `maintenance_plan_id` in the
values: the cron (`_cron_generate_requests`) and the plan's *manual generation* button
(`button_manual_request_generation`) both call `maintenance.equipment._create_new_request`, which
calls `request_model.create(vals)` (`maintenance_plan/models/maintenance_equipment.py:156`)
with values from `_prepare_request_from_plan`, `maintenance_plan_id` among them (`:81-118`, the key at `:107`).
Checked 2026-10-03; re-check on any `maintenance_plan` upgrade, since a batch or SQL path would make
this module stop firing without failing. `test_plan_generation_creates_actions` runs the real
path, so such a change would show as a failing test rather than silence.

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | §7.14 says nothing on access | actions are created as `sudo()` | Creating an action needs a management-system group (`mgmtsystem_action/security/ir.model.access.csv:3,5`). The cron runs as superuser, but the *manual generation* button runs as the user, and a maintenance user outside the management system would have the plan's request generation fail on the actions. This project's role matrix gives maintenance people that group; a module meant for contribution cannot assume it (D19), and generation must not become a choke point |
| 2 | §7.14 says nothing on templates without a type | skipped, and logged | `mgmtsystem.action.type_action` is required with no default; `qms_determination` skips such a template rather than guess a type. Generation often runs from the cron, with no screen to warn on, so the skip is logged |
| 3 | §7.14 says nothing on the action's deadline | `date_deadline` is the request's scheduled date | `maintenance_plan` always sets `schedule_date` (`maintenance_equipment.py:99`); it is when the work is due, and the action belongs to that work |

## Decisions

| # | Decision |
|---|---|
| D1 | **At creation only** (D23). A request given a plan by a later write gets no actions; one raised by hand with a plan set does. Changing a plan's templates later reaches only the requests it generates afterwards |
| D2 | **The action's values mirror `mgmtsystem_action_template`'s onchange**, as `qms_determination` does (`qms_determination/models/mgmtsystem_nonconformity.py:37-75`): `name`, `type_action`, `description`, `user_id`, `tag_ids` from the template, `template_id` the template, without the onchange's "NEW " prefix — a generated action is a finished record. Diff against `mgmtsystem_action_template/models/mgmtsystem_action.py:23` on an OCA upgrade |
| D3 | **The name is the template's**, no request reference added: the action links to its request through `maintenance_request_id`, which the action form shows |
| D4 | **Generated up front.** The plan creates requests up to its horizon ahead, so those requests' actions exist from that moment, each due on its request's date. Deferring them until the request is due would need a scheduler of its own, which the plan's design avoided |

## Folder structure

```
maintenance_plan_action_template/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── maintenance_plan.py
│   └── maintenance_request.py
├── views/maintenance_plan_views.xml
├── tests/__init__.py, test_maintenance_plan_action_template.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance Plan Action Templates` |
| `summary` | `Generate management-system actions from templates on every request a maintenance plan creates` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance_plan`, `mgmtsystem_action_template`, `maintenance_mgmtsystem_action` |
| `data` | `views/maintenance_plan_views.xml` |
| `installable` | `True` |

No access file: no new model. Templates are readable and editable by every internal user
(`mgmtsystem_action_template/security/ir.model.access.csv:2`).

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import maintenance_plan`, `from . import maintenance_request` |
| `tests/__init__.py` | `from . import test_maintenance_plan_action_template` |

## Models

### `maintenance.plan` — `models/maintenance_plan.py`

| Field | Type | Attributes |
|---|---|---|
| `action_template_ids` | Many2many → `mgmtsystem.action.template` | `string="Action Templates"`, help: one action per template is created on every request this plan generates |

### `maintenance.request` — `models/maintenance_request.py`

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`, then `_create_plan_actions()` on the new requests (D1) |
| `_create_plan_actions` | — | reading the requests and their plans as `sudo()` — a requester raising a request by hand with a plan set needs no read access to plans — for each request with a `maintenance_plan_id`, one action per template of the plan that has a `type_action`, all created in one batched `create()` on `mgmtsystem.action` as `sudo()` (divergence 1), with D2's values plus `maintenance_request_id` the request and `date_deadline` the date of its `schedule_date` (divergence 3). A template without a type is skipped and logged at `INFO`, naming the template and the request (divergence 2) |

## Views — `views/maintenance_plan_views.xml`

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `maintenance_plan_view_form` | `maintenance_plan.maintenance_plan_view_form` | `//notebook` inside | page `Action Templates` (`name="action_templates"`) holding `action_template_ids` (`nolabel="1"`, `widget="many2many_tags"`, `options="{'no_create': True}"`) |

## Tests — `tests/test_maintenance_plan_action_template.py`

`TestPlanActionTemplate(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create equipment, a plan, requests and a user. Two templates with a type, one without,
a tag, and a plan on the test's own machine with a monthly interval, a two-month horizon and
today's start, so generation yields several requests. `_generate` runs the plan's own button and
`_actions` searches actions by `maintenance_request_id`; the log is asserted on the module's own
logger, `odoo.addons.maintenance_plan_action_template.models.maintenance_request`.

| Test | Asserts |
|---|---|
| `test_plan_generation_creates_actions` | the plan's own `button_manual_request_generation()` generates at least one request, and each gets one action per typed template, linked by `maintenance_request_id` — the real path O6 depends on |
| `test_action_values` | an action carries its template's name, type, description, responsible and tags, `template_id`, and `date_deadline` equal to the request's scheduled date |
| `test_template_without_type_skipped` | the untyped template produces no action, and the skip is logged at `INFO` (`assertLogs`) |
| `test_request_given_a_plan_by_hand` | a request created by hand with `maintenance_plan_id` gets the actions too |
| `test_request_without_plan_gets_none` | a request with no plan gets no action |
| `test_plan_set_later_gets_none` | a plan written onto an existing request creates no action (D1) |
| `test_generation_outside_the_management_system` | an equipment manager with no management-system group generates the plan's requests and the actions are created (divergence 1); the control: the same user creating an action directly raises `AccessError` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Adds action templates to maintenance plans: every request a plan generates gets one management-system action per template, linked to the request and due on its scheduled date. The preventive counterpart of actions generated from a nonconformity |
| `readme/USAGE.md` | Define templates under *Management System → Configuration → Action Templates*, each with a response type — one without is skipped. Add them on the plan's *Action Templates* page. Requests the plan generates from then on carry the actions, visible from the request's *Actions* button; a request raised by hand with a plan set does too. Changing a plan's templates does not reach requests already generated. Since a plan generates requests up to its horizon ahead, their actions appear at once, each due on its request's date |
