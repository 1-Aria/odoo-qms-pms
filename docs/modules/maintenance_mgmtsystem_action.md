# maintenance_mgmtsystem_action

The Action ↔ Maintenance Request relation: a field on the action, a count and a smart
button on the request.
Plan: §7.10, §8, D19, D21, D22, D31.

Two consumers need this relation — `qms_maintenance` in Phase 1 and
`maintenance_plan_action_template` in Phase 2 — which is why it is its own module rather than
a part of either (D22). It depends only on core `maintenance` and OCA `mgmtsystem_action`, so
it is contributable upstream (D19), and that shapes two decisions below: no `qms_` prefix, and
no reliance on this system's role matrix.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `mgmtsystem.action.maintenance_request_id` and the field on the action form; `action_ids`, an overridable count and a smart button on the request, plus the button box the request form lacks | proposed | |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | Appendix B: fields added to OCA models take the `qms_` prefix | `maintenance_request_id`, `action_ids`, `action_count`, all unprefixed | The prefix marks a field as belonging to this quality system. A module meant for upstream carries no such mark, and plan §7.10 names the field `maintenance_request_id` itself. Checked for collisions: no module in OCA/maintenance declares `action_ids` or `action_count` on `maintenance.request` |
| 2 | §7.10: "one relation plus two buttons", with a count of zero opening a new form carrying the context defaults and a count of one or more opening the matching records filtered | **only the request gets a button**, and it opens the filtered list whatever the count, with the default on the action so New prefills. The action side has the `maintenance_request_id` field alone | A Many2one on a form is already a link to its record, so a button beside it duplicates it; a count of many actions is what no field shows. `qms_quality_control` was retrofitted to the same rule on 2026-09-24, which also settles the button-box clash: neither OCA form has one, and with only the aggregate side buttoned each module creates a box on a different form |
| 3 | §7.10 does not mention access | the request's actions button names `mgmtsystem.group_mgmtsystem_viewer`; the action's `maintenance_request_id` field carries no group at all | D31, applied to what each read actually requires. `mgmtsystem.action` read belongs to the management-system viewer group and up (`mgmtsystem_action/security/ir.model.access.csv:2-5`), so the button reading it is gated. `maintenance.request` read is granted to `base.group_user` by core (`maintenance/security/ir.model.access.csv:4`), so every internal user already has it and a gate would only hide a working field. Gating on the read rather than on our role matrix is what makes this module safe to contribute |
| 4 | §8 gives this module the relation and the buttons, and nothing about how the count is built | the count reads `_action_domain()`, a method holding only the direct link here | `qms_maintenance` extends it with the arms through the nonconformity — its action plan and its immediate action — as `qms_quality_control` already does for inspections. This module cannot know about nonconformities: `mgmtsystem_nonconformity` is not a dependency, and adding one would put the whole management system into a bridge that two Phase 2 modules want (D19, D22) |

## Folder structure

```
maintenance_mgmtsystem_action/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── mgmtsystem_action.py                              # 1
│   └── maintenance_request.py                            # 1
├── views/
│   ├── mgmtsystem_action_views.xml                       # 1
│   └── maintenance_request_views.xml                     # 1
├── tests/__init__.py, test_maintenance_mgmtsystem_action.py   # 1
└── readme/ DESCRIPTION.md, USAGE.md                      # 1
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance Actions` |
| `summary` | `Link management-system actions to maintenance requests` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance`, `mgmtsystem_action` |
| `data` | `views/mgmtsystem_action_views.xml`, `views/maintenance_request_views.xml` |
| `installable` | `True` |

No access file: the module adds fields and buttons to existing models, whose access rules
come from `maintenance` and `mgmtsystem_action`.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mgmtsystem_action`, `from . import maintenance_request` |

## Models

### `mgmtsystem.action` — `models/mgmtsystem_action.py`

`_inherit = "mgmtsystem.action"`

| Field | Type | Attributes |
|---|---|---|
| `maintenance_request_id` | Many2one → `maintenance.request` | `string="Maintenance Request"`, `ondelete="set null"`, `index=True` |

No method: the field is the link, so this side has no smart button (divergence 2).

`ondelete="set null"`, as `qms_quality_control` chose for the inspection link and for the same
reason: an action is the record of work done and must outlive its source. Core places no guard
on deleting a request, so `restrict` here would be worse than in the inspection case — it
would make a request undeletable because someone raised an action from it.

### `maintenance.request` — `models/maintenance_request.py`

`_inherit = "maintenance.request"`

| Field | Type | Attributes |
|---|---|---|
| `action_ids` | One2many → `mgmtsystem.action` | inverse `maintenance_request_id`, `string="Actions"` |
| `action_count` | Integer | `compute="_compute_action_count"`, not stored, `string="# Actions"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_action_domain` | — | `ensure_one`; `[("maintenance_request_id", "=", self.id)]` — the direct link, and the extension point |
| `_compute_action_count` | `@api.depends("action_ids")` | `search_count(request._action_domain())`, and `0` for an unsaved record |
| `action_view_actions` | — | `ensure_one`, returns an `ir.actions.act_window` on `mgmtsystem.action`, `view_mode` `list,form`, `domain=self._action_domain()`, `context={"default_maintenance_request_id": self.id}` |

**A method with one arm, and that is the point.** `qms_maintenance` overrides `_action_domain`
to add the actions reached through a nonconformity raised from the request — its action plan
and its immediate action — exactly as `qc.inspection._qms_action_domain` already does on the
quality side. Here the count would otherwise be written inline and the extension would mean
rewriting it.

**`search_count` rather than `len(action_ids)`**, so an override widening the domain widens the
count with it. `@api.depends("action_ids")` is what invalidates it; a search has no dependency
path of its own, and `qms_maintenance` adds its own paths to the list when it adds its arms.

**`0` for an unsaved record**: a `NewId` cannot go into a domain, and the compute runs during
onchange on a new request. The guard core writes as `isinstance(record.id, models.NewId)`
(`crm_lead.py:575`).

**No prefill beyond the link.** `default_maintenance_request_id` is the whole context. An
action's `name` is a subject and `type_action` is a judgement, so neither is guessed — the same
line `qms_quality_control` step 3 took.

## Views — `views/mgmtsystem_action_views.xml`

Inherits `mgmtsystem_action.view_mgmtsystem_action_form`.

| Position | Content |
|---|---|
| field `reference` after (inside `group[@name='meta']`) | `maintenance_request_id`, `options="{'no_create': True}"`, and no `groups` — divergence 3 |

No button and no button box on this side (divergence 2). `qms_quality_control` adds its own
`qms_inspection_id` after the same anchor; two modules extending one anchor is ordinary, and
with neither creating a button box there is nothing to collide over.

## Views — `views/maintenance_request_views.xml`

Inherits `maintenance.hr_equipment_request_view_form`.

| Position | Content |
|---|---|
| `//sheet/div[hasclass('oe_title')]` before | a `<div name="button_box" class="oe_button_box">` holding one `oe_stat_button`: `action_view_actions`, `icon="fa-tasks"`, `action_count` as the stat value with singular and plural labels, `groups="mgmtsystem.group_mgmtsystem_viewer"` |

The request form has no button box either — core's is on the *equipment* form
(`maintenance/views/maintenance_views.xml:372`), not the request
(`hr_equipment_request_view_form`, `:76-96`). Here the situation is simpler than on the action
form: no other module in this system adds one.

## Tests — `tests/test_maintenance_mgmtsystem_action.py`

`TestMaintenanceAction(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create equipment and users.

| Test | Asserts |
|---|---|
| `test_link_visible_both_ways` | an action created with `maintenance_request_id` appears in the request's `action_ids` and the count is 1; a second action makes it 2 |
| `test_count_zero` | a request with no action counts 0, which the always-visible button shows |
| `test_count_refreshes_within_transaction` | reading the count, then creating an action, gives the new number — what `@api.depends("action_ids")` buys a `search_count` |
| `test_view_actions_domain_and_context` | `action_view_actions` returns a `list,form` action whose domain is `_action_domain()` and whose context carries `default_maintenance_request_id`, so New prefills even from an empty list |
| `test_request_delete_keeps_action` | deleting a request that has an action leaves the action alive with an empty `maintenance_request_id` — the `ondelete="set null"` decision |
| `test_domain_is_the_extension_point` | `_action_domain()` returns the direct-link domain, and a subclass widening it widens `action_count` — the contract `qms_maintenance` relies on. Asserted by patching the method on the model in the test, not by defining a module |
| `test_actions_button_hidden_without_mgmtsystem` | `get_view` on the request form omits `action_count` for an internal user with no management-system group, and contains it for one with the viewer group |
| `test_request_field_has_no_group` | `get_view` on the action form contains `maintenance_request_id` for a management-system user with no maintenance group — core grants request read to every internal user, so gating it would hide a working field. The negative of the test above, and the reason the asymmetry is deliberate rather than an oversight |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Links a management-system action to the maintenance request it belongs to: a field on the action, and a count with a smart button on the request. Useful on its own; also the shared dependency of plan-seeded action generation and of the QMS maintenance bridge |
| `readme/USAGE.md` | The field on the action, the count on the request, that the count follows `_action_domain` and is meant to be extended, and the group each button needs |
