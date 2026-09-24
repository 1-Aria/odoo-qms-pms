# qms_maintenance

The maintenance side of the pipeline: a nonconformity raised from a maintenance request, the
request's own view of what it produced, and the product that scopes the catalogs.
Plan: §7.10 (maintenance rows), §8, D19, D21, D22, D31.

The mirror of `qms_quality_control`, and the first consumer of the extension point
`maintenance_mgmtsystem_action` left behind: `maintenance.request._action_domain`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `mgmtsystem.nonconformity.qms_maintenance_request_id` and the field on the nonconformity form; `qms_nonconformity_ids`, a count and a smart button on the request, with prefill; `_action_domain` extended with the nonconformity arms | done | installed and tested 2026-09-24, `exit=0`, 12 tests, 0 failures; UI checked — the Nonconformities button beside Actions in the one button box, New from it carrying the request, equipment and product, the analysis dropdowns then offering the equipment product's profiled codes, equipment without a product offering none, and the Actions count including what the request's nonconformities produced |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | §7.10 names the field `mgmtsystem.nonconformity.maintenance_request_id`, and Appendix B exempts "the link fields in §7.10" from the `qms_` prefix | `qms_maintenance_request_id` | The exemption was written before the rule had been tested against a real upstream field. `qms_quality_control` already took the prefixed route for the same reason (its divergence 12): on an OCA model, an unprefixed `maintenance_request_id` is exactly the name a future upstream field could take. The rule this project now follows: **prefixed inside `qms_*` modules, unprefixed in modules meant for contribution** — which is why `mgmtsystem.action.maintenance_request_id` in `maintenance_mgmtsystem_action` carries no prefix and this field does |
| 2 | §7.10 adds `maintenance.request.product_id`, a related field through the equipment, and counts it as the "one field" the PM prefill costs | **no field at all**: the prefill reads `self.equipment_id.product_id` where it builds the context | The field had one consumer, and it was the context. §7.10 needed it because it prefilled from XML, where a context can only name fields of the record; building the context in Python removes that constraint. Nothing displayed it, nothing searched it, and one fewer field on an OCA model is one fewer thing to carry — adding it later is additive if something ever needs it |
| 3 | §7.10: a smart button on both models | the request gets the button; the nonconformity gets the field | The rule settled on 2026-09-24 and applied to `qms_quality_control` and `maintenance_mgmtsystem_action`: a Many2one on a form is already a link, so only the aggregate side earns a button |
| 4 | §8 lists this module's contents without mentioning the action count | `_action_domain` is extended here with the two nonconformity arms | The count on the request must reach the actions a nonconformity produced, exactly as the inspection's does. `maintenance_mgmtsystem_action` cannot: `mgmtsystem_nonconformity` is not among its dependencies, by D19 and D22 |

## Folder structure

```
qms_maintenance/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── mgmtsystem_nonconformity.py                       # 1
│   └── maintenance_request.py                            # 1
├── views/
│   ├── mgmtsystem_nonconformity_views.xml                # 1
│   └── maintenance_request_views.xml                     # 1
├── tests/__init__.py, test_qms_maintenance.py            # 1
└── readme/ DESCRIPTION.md, USAGE.md                      # 1
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Maintenance` |
| `summary` | `Nonconformities raised from maintenance requests` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_nonconformity`, `maintenance_product`, `mgmtsystem_nonconformity_maintenance_equipment`, `maintenance_mgmtsystem_action` |
| `data` | `views/mgmtsystem_nonconformity_views.xml`, `views/maintenance_request_views.xml` |
| `installable` | `True` |

`maintenance_product` supplies `maintenance.equipment.product_id`, which the prefill reads
through; `mgmtsystem_nonconformity_maintenance_equipment` supplies the
nonconformity's `equipment_id`, which the prefill carries. `maintenance_mgmtsystem_action`
brings the action count this module extends, and `base_maintenance` with it — so the request
form's button box is already there.

No access file: no new model, and every field sits on a model whose rules come from its own
module.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mgmtsystem_nonconformity`, `from . import maintenance_request` |

## Models

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py`

`_inherit = "mgmtsystem.nonconformity"`

| Field | Type | Attributes |
|---|---|---|
| `qms_maintenance_request_id` | Many2one → `maintenance.request` | `string="Maintenance Request"`, `ondelete="set null"`, `index=True` |

`ondelete="set null"`, as both other links in this system: the nonconformity is the record of
what went wrong and outlives the request that surfaced it. No method and no button on this
side — the field is the link (divergence 3).

### `maintenance.request` — `models/maintenance_request.py`

`_inherit = "maintenance.request"`

| Field | Type | Attributes |
|---|---|---|
| `qms_nonconformity_ids` | One2many → `mgmtsystem.nonconformity` | inverse `qms_maintenance_request_id`, `string="Nonconformities"` |
| `qms_nonconformity_count` | Integer | `compute="_compute_qms_nonconformity_count"`, not stored |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_nonconformity_count` | `@api.depends("qms_nonconformity_ids")` | `len(request.qms_nonconformity_ids)` |
| `action_view_qms_nonconformities` | — | `ensure_one`, an `ir.actions.act_window` on `mgmtsystem.nonconformity`, `view_mode` `list,form`, domain on `qms_maintenance_request_id`, and the prefill context below |
| `_action_domain` | — | `super()`, OR'd with the two nonconformity arms |
| `_compute_action_count` | `@api.depends(…)` | `super()`, with the dependency list restated — see below |

**A plain `len()` here, not a `search_count`.** The nonconformity count has one path and no
extension point: nothing else can make a nonconformity belong to a request. The action count
is the opposite case, which is why it is a search over an overridable domain.

**The prefill context**

| Key | Value | Why |
|---|---|---|
| `default_qms_maintenance_request_id` | `self.id` | the link |
| `default_equipment_id` | `self.equipment_id.id` | from `mgmtsystem_nonconformity_maintenance_equipment` — the machine is the subject of a PM nonconformity |
| `default_product_id` | `self.equipment_id.product_id.id` | **what makes the catalogs work.** §7.6 scopes the defect and object-part dropdowns through the product's profiles, and on the maintenance side the product is reached through the equipment, which `maintenance_product` supplies. The chain is null-safe by construction: a request with no equipment, or equipment with no product, yields `False` with no guard, and the dropdowns fall back to empty — the documented §7.6 behaviour |
| `default_name` | `self.name` | the request's subject as an opening title, as the inspection side does |
| `default_company_id` | `self.company_id.id` | as the inspection side does |

No branch on the count: the list opens whatever it holds, and its New button carries the same
defaults. The same shape as `qc.inspection.action_view_qms_actions`, and for the same reason.

**Extending the action domain**

```python
def _action_domain(self):
    return expression.OR([
        super()._action_domain(),
        [
            "|",
            ("nonconformity_ids.qms_maintenance_request_id", "=", self.id),
            ("nonconformity_immediate_id.qms_maintenance_request_id", "=", self.id),
        ],
    ])
```

`expression.OR` rather than hand-written prefix operators (`odoo/osv/expression.py:308`): the
base domain is one leaf today, and an OR written by hand would have to be rewritten the moment
it is not. The two arms are `mgmtsystem.action`'s own inverse fields — `nonconformity_ids` for
the action plan, `nonconformity_immediate_id` for the containment action — exactly as
`qc.inspection._qms_action_domain` uses them.

**Dependencies merge across the MRO, so the override only names what it adds.** A computed
field resolves its compute through `resolve_mro` and *extends* the dependency list from every
definition of the method it finds (`odoo/fields.py:575-586`, `resolve_mro` at
`odoo/api.py:79-92`). The inherited `action_ids` dependency therefore still applies, and the
"override, declare the new dependencies, call `super()`" idiom is exactly how a module adds
paths to an inherited compute:

```python
@api.depends(
    "qms_nonconformity_ids.action_ids",
    "qms_nonconformity_ids.immediate_action_id",
)
def _compute_action_count(self):
    return super()._compute_action_count()
```

The method body adds nothing — it exists to carry the decorator. Worth a comment saying so,
since a bare `super()` override otherwise reads like something half-written.

## Views — `views/mgmtsystem_nonconformity_views.xml`

Inherits `mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_form`.

| Position | Content |
|---|---|
| field `system_id` after | `qms_maintenance_request_id`, `options="{'no_create': True}"`, no `groups` |

**To verify at implementation:** `qc_inspection_id` is added by
`mgmtsystem_nonconformity_quality_control_oca`, which this module does **not** depend on, so
the anchor must be `system_id` — the field the OCA bridge itself anchors to. Placing both
links beside each other is the goal; inheriting an anchor from a module we do not depend on is
not available.

The OCA quality bridge anchors `qc_inspection_id` after `system_id` as well, so on an instance
running both, the two link fields appear in whichever order the views load. Harmless, and
recorded so it is not read as a bug.

**No `groups` on this field.** Core grants `maintenance.request` read to `base.group_user`, so an attribute
here would document the read rather than restrict anything — the same call
`maintenance_mgmtsystem_action` made for the mirror field on the action. The reason belongs in a
comment, not an attribute.

## Views — `views/maintenance_request_views.xml`

Inherits `base_maintenance.equipment_request_view_form`, the module that owns the request
form's button box — which arrives as a dependency of `maintenance_mgmtsystem_action`.

| Position | Content |
|---|---|
| `//div[hasclass('oe_button_box')]` inside | an `oe_stat_button`: `action_view_qms_nonconformities`, `icon="fa-exclamation-triangle"`, `qms_nonconformity_count` as the stat value with singular and plural labels, `groups="mgmtsystem.group_mgmtsystem_viewer"` |

The group is what the count reads: `mgmtsystem.nonconformity` grants read to the
management-system viewer group and up, so a request opened by a user without it would
otherwise raise. The button sits beside the Actions button from
`maintenance_mgmtsystem_action`, in the one box `base_maintenance` provides.

## Tests — `tests/test_qms_maintenance.py`

`TestQmsMaintenance(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures
create a product, equipment, a request, nonconformities and users.

| Test | Asserts |
|---|---|
| `test_link_visible_both_ways` | a nonconformity created with `qms_maintenance_request_id` appears in the request's `qms_nonconformity_ids` and the count is 1; a second makes it 2 |
| `test_request_delete_keeps_nonconformity` | deleting the request leaves the nonconformity alive with an empty link — `ondelete="set null"` |
| `test_prefill_product_from_equipment` | the context's `default_product_id` is the equipment's product, and `False` for equipment with none, and for a request with no equipment — the case that leaves the catalog dropdowns empty by design |
| `test_view_nonconformities_domain_and_context` | the action's domain selects this request's nonconformities and its context carries all five defaults, so New from the list prefills |
| `test_prefill_scopes_catalog_dropdowns` | a nonconformity created with that context resolves the product's `qms_effective_profile_ids` — the end-to-end check that the maintenance side reaches the same catalogs as the quality side |
| `test_direct_action_counts` | an action pointing at the request counts, as before this module |
| `test_nonconformity_action_counts` | an action on a nonconformity raised from the request counts, though nothing points at the request |
| `test_immediate_action_counts` | that nonconformity's `immediate_action_id` counts |
| `test_unrelated_action_does_not_count` | an action on a nonconformity from another request, and one on a nonconformity with no request, are both excluded |
| `test_action_reachable_twice_counts_once` | an action both pointing at the request and sitting on its nonconformity counts once |
| `test_action_count_refreshes_on_every_arm` | the count rises as an action is added by each of the three paths. It proves all three arms invalidate the count; it does **not** police the override's dependency list, since the inherited `action_ids` dependency merges in whether or not this module restates it |
| `test_nonconformity_button_hidden_without_mgmtsystem` | `get_view` on the request form omits `qms_nonconformity_count` for an internal user with no management-system group, and contains it for a viewer |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Raises nonconformities from maintenance requests and brings the maintenance side into the same analysis, catalogs and action tracking as quality control |
| `readme/USAGE.md` | The Nonconformities button on the request and what it prefills; that the catalogs are scoped through the equipment's product, so equipment without one offers no codes; and that the request's Actions count now includes the actions its nonconformities produced |
