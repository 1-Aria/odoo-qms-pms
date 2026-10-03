# maintenance_equipment_status_automation

A corrective request moves its equipment's status as it moves through the stages: a stage can
name the status its equipment takes when a corrective request reaches it.
Plan: §7.13, §8, D19.

Independent of the QMS chain and of the SLA cluster: it keys on stages, whatever flow a site
runs, and depends only on core and OCA.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The whole module: the stage's status, the request hook, the stage list column, tests, readme | proposed | |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | §7.13 is a fixed table: *In Progress* → Down, *Repaired* → Operational, *Scrapped* → Scrapped | the mapping is configuration: `equipment_status_id` on each stage, empty by default | `maintenance_equipment_status` has no fixed statuses — `maintenance.equipment.status` is a list a site defines (`maintenance_equipment_status/models/maintenance_equipment_status.py`), and this instance holds only *New*. Stages are configuration as well, and the flow has changed since the plan was written (`maintenance_sla_garment`). Naming neither in code keeps the module right for any flow. With nothing configured it does nothing |
| 2 | §7.13 does not say when a request created directly in a mapped stage counts | creation counts: a corrective request created in a mapped stage sets the status at once | A kanban quick-create in a later column is a request that has reached that stage; ignoring it would leave the machine's status behind the request's |
| 3 | §7.13 is silent on a status limited to some categories | a status whose `category_ids` does not include the equipment's category is not applied | OCA limits a status to categories (`category_ids`, applied as a domain on the equipment form, `maintenance_equipment_status/views/maintenance_equipment_views.xml:14`); writing a status the form would not offer would put the machine in a state its own form calls invalid |

What the plan states and this module keeps: corrective requests only; one-directional — the
module writes the equipment's status and never reads it back, so a manual correction stands until
the next mapped stage change.

## Decisions

| # | Decision |
|---|---|
| D1 | **Only a real stage change applies the mapping.** The stage is compared before and after the write, as `maintenance_sla` does, so a request saved unchanged, or a later write that does not move it, never overwrites a status corrected by hand |
| D2 | **Written as `sudo()`.** Equipment is writable only by equipment managers (`maintenance/security/ir.model.access.csv:3`), while anyone who may move a request may trigger the mapping; the automation must not turn a stage move into an access error. The tracked change still carries the user who moved the request |
| D3 | **The last mapped move wins.** With two open corrective requests on one machine, moving either to a mapped stage sets the status, even if the other still holds the machine down. Deciding from all of a machine's open requests would make the module read state back, which the plan rules out; the status stays correctable by hand |
| D4 | **No statuses and no mapping are shipped** (the project's no-guessed-seeds rule). A preset — `maintenance_sla_garment` or another — may supply them later, depending on this module |

## Folder structure

```
maintenance_equipment_status_automation/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── maintenance_stage.py
│   └── maintenance_request.py
├── views/maintenance_stage_views.xml
├── tests/__init__.py, test_equipment_status_automation.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance Equipment Status Automation` |
| `summary` | `Set the equipment's status from the stage its corrective request reaches` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance`, `maintenance_equipment_status` |
| `data` | `views/maintenance_stage_views.xml` |
| `installable` | `True` |

No access file: the module adds no model.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import maintenance_stage`, `from . import maintenance_request` |
| `tests/__init__.py` | `from . import test_equipment_status_automation` |

## Models

### `maintenance.stage` — `models/maintenance_stage.py`

| Field | Type | Attributes |
|---|---|---|
| `equipment_status_id` | Many2one → `maintenance.equipment.status` | `string="Equipment Status"`, `ondelete="set null"`, help: the status the equipment of a corrective request takes when the request reaches this stage; empty leaves it alone |

### `maintenance.request` — `models/maintenance_request.py`

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`, then `_apply_equipment_status()` on the new requests |
| `write` | — | when `vals` has `stage_id`, each request's stage is kept by `id` before `super()`; afterwards `_apply_equipment_status()` runs on the requests whose stage actually changed (D1) |
| `_apply_equipment_status` | — | on `self.sudo()` (D2): for each request that is corrective, has equipment, and sits in a stage with an `equipment_status_id`, when the status has no `category_ids` or they include the equipment's `category_id` (divergence 3), and the equipment does not already hold it — `equipment.status_id = status` |

The last condition keeps a move between two stages mapped to the same status from writing, and
so from posting a tracking line that changes nothing.

## Views — `views/maintenance_stage_views.xml`

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `hr_equipment_stage_view_tree` | `maintenance.hr_equipment_stage_view_tree` | field `done` after | `equipment_status_id` (`options="{'no_create': True}"`) |

Core's stage list is its only editable view (no form), reached in debug mode under *Configuration →
Maintenance Stages*; `maintenance_sla` adds its *Cancels SLA* column to the same list.

## Tests — `tests/test_equipment_status_automation.py`

`TestEquipmentStatusAutomation(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create equipment, requests and a user. They create their own stages, statuses (*Down*,
*Operational*, and *Retired* limited to a category the machine is not in), a category and a
machine, and do not read the instance's.

| Test | Asserts |
|---|---|
| `test_reaching_a_mapped_stage_sets_the_status` | a corrective request moved to the *Down* stage sets the machine *Down*; moved on to the *Operational* stage, *Operational* |
| `test_unmapped_stage_leaves_the_status` | a move to a stage with no status leaves the machine's status as it was |
| `test_preventive_requests_ignored` | a preventive request reaching the *Down* stage changes nothing |
| `test_created_in_a_mapped_stage` | a corrective request created directly in the *Down* stage sets the machine *Down* (divergence 2) |
| `test_manual_status_survives_an_unchanged_stage` | after a hand-set status, a write that keeps the stage, and a write to another field, leave it (D1) |
| `test_status_limited_to_other_categories_skipped` | a stage mapped to *Retired*, limited to another category, leaves the machine's status alone (divergence 3) |
| `test_request_without_equipment_ignored` | a corrective request with no machine moves through a mapped stage without error |
| `test_any_request_mover_may_trigger_it` | a user without write access to equipment, the request's responsible, moves it to the *Down* stage and the machine becomes *Down* (D2); the user is the request's `user_id` for the reason `maintenance_sla` records — `hr_maintenance` empties `owner_user_id` |
| `test_no_write_when_unchanged` | moving between two stages mapped to the same status writes nothing on the machine: the equipment model's `write`, wrapped with `unittest.mock.patch.object`, is not called. `write_date` cannot show it — within one test transaction every write carries the same timestamp |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Keeps a machine's status in step with its corrective requests: a maintenance stage can name the equipment status a corrective request's machine takes when the request reaches it — *Down* when work starts, *Operational* when it is restored, *Retired* when it is scrapped, or whatever statuses the site defines |
| `readme/USAGE.md` | Define the statuses under *Maintenance → Configuration → Equipment Statuses*; set *Equipment Status* on the stages that should change it, in the stage list (debug mode). Only corrective requests, and only a real stage change; a status set by hand stands until the next mapped move. With two open requests on one machine, the last mapped move wins. A status limited to categories is skipped for other machines |
