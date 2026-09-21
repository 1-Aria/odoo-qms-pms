# qms_nonconformity

Nonconformity items, header additions, code filtering, severity roll-up.
Plan: §7.4, §7.6, §7.9, D6–D9, D16.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `qms.nonconformity.item`, header `item_ids`, items in Causes and Analysis, §7.6 code filtering | done | installed and tested 2026-09-21, `exit=0`, 7 tests, 0 failures; the Analysis Items dropdown was confirmed in the browser to offer only the product's profiled leaf codes, and the page reads Analysis → Analysis Items → Analysis Confirmation with no Causes section. Two failures on the way: `setUpClass` creating a product at `at_install` hit `product_template.sale_line_warn`, fixed with the `post_install` tag; and the first placement used `separator[@string='Causes']` as an inheritance selector, which core refuses, fixed by selecting the separator positionally |
| 2 | Header: `partner_id` relaxed, responsible / manager prefill, `disposition_id` and the `qms.disposition` model, and the `qms_nonconformity_hr` bridge for department and manager | done | two passes, both 2026-09-21. First: Selection-based disposition, `exit=0`, 12 tests + 2 in the bridge. Reopened the same day to make disposition a user-editable model while the column held no real data, and to move the manager prefill into the bridge — `res.users.employee_id` comes from `hr`, which `qms_nonconformity` does not depend on, so `default_get` would have raised `AttributeError` anywhere `hr` was absent. Second pass `exit=0`, 10 tests here and 4 in the bridge, UI checked: partner optional, prefill working, dispositions listed under Configuration → Nonconformities with `code` greyed out, archived filter working |
| 3 | `qms_severity_rank` shown on the severity form, `default_severity_id` on `qms.defect.code`, item severity default, header roll-up | done | upgraded and tested 2026-09-21, `exit=0`, 19 tests, 0 failures; the header recompute over existing nonconformities ran clean; UI checked: rank on the severity form, default severity on defect codes, items and header filling in. Rank seeding was dropped before any code was written — each implementation defines its own severities, so ranks start at 0 and the unconfigured state is documented and tested (the first item wins ties). A review then showed no test moved an existing item's `sequence`, so `item_ids.sequence` in `@api.depends` was unproven; `test_header_rollup_follows_reorder` closes that |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | O2 says `partner_id` is mandatory "in a view somewhere not yet located", and that base `mgmtsystem_nonconformity` does not mark it required in model or view | the base model does mark it required, in Python | `mgmtsystem_nonconformity/models/mgmtsystem_nonconformity.py:41`: `partner_id = fields.Many2one("res.partner", "Partner", required=True)`. O2 is answered, and the override in step 2 is the one line the plan hoped for |
| 2 | §7.6 resolves the product's category on the nonconformity | the header carries `qms_effective_profile_ids`, related to the product | The plan was amended for this on 2026-09-20; `qms_catalog` computes the resolved set, so the domain reads it directly |
| 3 | §8 lists `mgmtsystem_partner` among this module's dependencies | not a dependency | `mgmtsystem_partner` adds one line — a `quality` option to `res.partner.type` (`models/res_partner.py:16`) — and never touches `mgmtsystem.nonconformity`. `partner_id` and its `required=True` both come from base `mgmtsystem_nonconformity`, which we do depend on, and nothing here uses `type='quality'` |
| 4 | §7.4 says the header's `cause_ids` "remains for compatibility and rolls up from the items" | no roll-up; the header's cause list is hidden on the form | Cause is analysis, and analysis is per item: one nonconformity can hold three defects with three different causes, so a header list of them states nothing a reader can act on. Severity rolls up because it has a rank and a defensible aggregate — the most severe item. Cause has no such ordering. The field is hidden rather than removed, so it stays available to other views, to the API and to any OCA code that reads it |
| 5 | §8 lists nine modules and does not include an HR bridge | `qms_nonconformity_hr` exists | `department_id` belongs to `mgmtsystem_nonconformity_hr`, which is `auto_install` on `hr`. Depending on it directly would force `hr` onto every site running the quality system, so the default lives in an `auto_install` bridge — the same pattern OCA uses for the field |
| 6 | §7.9 makes `disposition` a Selection with five fixed values | `disposition_id`, a Many2one to a new `qms.disposition` model seeded with those five | Every other vocabulary in this system is a record the user controls; a hardcoded list is the odd one out and is exactly what a plant will want to extend. Logic branches on `qms.disposition.code`, not on ids |
| 7 | §7.4 has the item's `severity_id` "populated by onchange from `defect_code_id.default_severity_id`" | a stored, editable compute on `defect_code_id` | An onchange fires only in a form, so items created in code — the inspection prefill in `qms_quality_control` — would get no severity. The compute keeps the field editable, and a manual value stands until the defect code changes |

## Known traps in the base modules

**`action_nc_sent` with an empty partner** (`mgmtsystem_nonconformity_type/models/mgmtsystem_nonconformity.py:74-77`):

```python
contact_quality = self.partner_id["child_ids"].search(
    [("parent_id", "=", self.partner_id.id), ("type", "=", "quality")], limit=1)
```

`search()` on a recordset ignores that recordset, so with no partner the domain becomes
`parent_id = False, type = quality` and matches **any** top-level quality contact, which
the module then mails. Relaxing `partner_id` in step 2 makes that state reachable. The
button is manual and the module is only used deliberately, so this is recorded rather
than patched — `mgmtsystem_nonconformity_type` is OCA code we do not modify.

## Folder structure

```
qms_nonconformity/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── qms_nonconformity_item.py                         # 1
│   ├── mgmtsystem_nonconformity.py                       # 1 (item_ids, related profiles), 2, 3
│   ├── qms_disposition.py                                # 2
│   ├── mgmtsystem_nonconformity_severity.py              # 3 (qms_severity_rank)
│   └── qms_defect_code.py                                # 3 (default_severity_id)
├── data/qms_disposition.xml                              # 2 (noupdate)
├── security/ir.model.access.csv                          # 1, 2
├── views/
│   ├── qms_nonconformity_item_views.xml                  # 1
│   ├── qms_disposition_views.xml                         # 2
│   ├── mgmtsystem_nonconformity_views.xml                # 1 (items), 2 (disposition)
│   ├── mgmtsystem_nonconformity_severity_views.xml       # 3 (rank on the severity form)
│   └── qms_defect_code_views.xml                         # 3 (default severity on the code)
├── tests/__init__.py, test_qms_nonconformity_item.py     # 1
│         test_qms_nonconformity_header.py                # 2
│         test_qms_nonconformity_severity.py              # 3
└── readme/ DESCRIPTION.md, USAGE.md                      # 1 (DESCRIPTION), 3 (USAGE)
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Nonconformity` |
| `summary` | `Multi-line defect analysis on the nonconformity, scoped by catalog profile` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_catalog`, `mgmtsystem_nonconformity`, `mgmtsystem_nonconformity_product` |
| `data` | `security/ir.model.access.csv`, `data/qms_disposition.xml` (step 2), `views/qms_nonconformity_item_views.xml`, `views/qms_disposition_views.xml` (step 2), `views/mgmtsystem_nonconformity_views.xml`, `views/mgmtsystem_nonconformity_severity_views.xml` (step 3), `views/qms_defect_code_views.xml` (step 3) |
| `installable` | `True` |

`mgmtsystem_nonconformity_product` supplies `product_id`, which the filtering resolves
through. `mgmtsystem_partner` is **not** a dependency — see divergence 3.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_nonconformity_item`, `from . import qms_disposition` (step 2), `from . import mgmtsystem_nonconformity`, `from . import mgmtsystem_nonconformity_severity`, `from . import qms_defect_code` (step 3) |

## Models

### `qms.nonconformity.item` — `models/qms_nonconformity_item.py`

`models.Model` · `_name = "qms.nonconformity.item"` · `_description = "Nonconformity Item"` · `_order = "nonconformity_id, sequence, id"`

| Field | Type | Attributes |
|---|---|---|
| `nonconformity_id` | Many2one → `mgmtsystem.nonconformity` | `required=True`, `ondelete="cascade"`, `index=True` |
| `sequence` | Integer | `default=10` |
| `defect_code_id` | Many2one → `qms.defect.code` | `required=True`, `ondelete="restrict"` |
| `object_part_id` | Many2one → `qms.object.part` | `ondelete="restrict"` |
| `cause_id` | Many2one → `mgmtsystem.nonconformity.cause` | `ondelete="restrict"` |
| `severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | `ondelete="restrict"`; defaulted from the defect code in step 3, not solicited |
| `qty_affected` | Float | |
| `note` | Char | |

`defect_code_id` is required and `object_part_id` is not: an item records what is wrong,
while where it is wrong may be unknown — and §7.6 notes that an inspection resolves only
a defect code.

`ondelete="restrict"` on the three catalog links keeps a code that has been used in
analysis from being deleted, which matches `qms_catalog`'s own archive-rather-than-delete
rule.

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py`

`_inherit = "mgmtsystem.nonconformity"`

| Field | Type | Attributes |
|---|---|---|
| `item_ids` | One2many → `qms.nonconformity.item` | inverse `nonconformity_id`, `string="Analysis Items"` |
| `qms_effective_profile_ids` | Many2many → `qms.catalog.profile` | `related="product_id.qms_effective_profile_ids"`, `readonly=True`, `string="Effective Catalog Profiles"` |

The related field is what the §7.6 domain reads. It is declared on the header because a
domain may only reach `parent.<field>`, and the client evaluates that to a plain id list.

## Code filtering (§7.6)

Both catalog fields on the item carry a static domain:

```xml
domain="[('parent_id.profile_ids', 'in', parent.qms_effective_profile_ids)]"
```

A code matches when its **group** belongs to one of the product's resolved profiles.
`parent_id.` is one hop, which is why `qms_catalog` holds the catalogs to two levels.

**The domain also excludes groups**, and that is deliberate. A group has
`parent_id = False`, so `parent_id.profile_ids` is empty and no group can ever match.
With `defect_code_id` required, an item therefore always carries a leaf code — "Fabric
Defect" is not selectable, only "Torn" or "Scratch" beneath it. It is a second job the
domain does silently, so it is written down here.

**Verified in the browser, 2026-09-21.** `parent.qms_effective_profile_ids` resolves
from inside a One2many line without the field appearing in the header arch: on a
nonconformity whose product carries a profile, the Defect Code dropdown offers only
that profile's leaf codes. This matches core's use of the same shape at
`odoo/addons/point_of_sale/views/pos_order_view.xml:157` against a non-stored related
x2many (`pos_order.py:353`), also undeclared.

A Python test cannot cover this — the domain is evaluated by the web client — so it
stays a browser check, worth repeating on an Odoo upgrade. Should a future version
stop resolving it, the fix is one line: declare `qms_effective_profile_ids`
`invisible="1"` on the header form.

**Fallback is by design:** a product with no profile gives an empty dropdown, and the
user removes the condition from the search panel to see the whole catalog. A
nonconformity with no product resolves to an empty set and behaves the same way.

## Header changes (step 2)

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py`

| Field | Type | Attributes |
|---|---|---|
| `partner_id` | Many2one → `res.partner` | `required=False` — the whole override; every other attribute is inherited |
| `disposition_id` | Many2one → `qms.disposition` | `tracking=True`, `ondelete="restrict"`, no default |

| Method | Decorator | Behaviour |
|---|---|---|
| `_default_responsible_user_id` | — | `self.env.user`, mirroring how the base model defaults `user_id` |
`_default_responsible_user_id` is **a default, not a compute**: it fills a new record and
never revisits it, so an edit sticks and later changes do not rewrite old records.

**The manager prefill is not here.** It reads `res.users.employee_id`, which `hr` adds
(`hr/models/res_users.py:89`), so a module that does not depend on `hr` would raise
`AttributeError` in `default_get` wherever `hr` is absent. It lives in the bridge with
the department default.

**Department is not here**: it comes from `mgmtsystem_nonconformity_hr`, so its default lives in the `qms_nonconformity_hr` bridge below.

### `qms.disposition` — `models/qms_disposition.py`

`models.Model` · `_name = "qms.disposition"` · `_description = "Nonconformity Disposition"` · `_order = "sequence, id"`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `code` | Char | `required=True`, readonly in the views once the record exists — the stable key logic branches on |
| `sequence` | Integer | `default=10` |
| `active` | Boolean | `default=True` |
| `description` | Text | |

| Name | Definition | Message |
|---|---|---|
| `code_uniq` | `unique (code)` | `"This disposition code already exists."` |

**Why a model rather than the Selection the plan specifies.** Disposition is vocabulary,
and every other vocabulary here is a record the user controls. A plant will want
"Concession", "Downgrade" or "Sort and re-grade" without a developer. The cost is that
database ids are not portable, so logic must branch on `code` — hence the field.

**`code` is the anchor, and only `code`.** It is readonly in the list and the form once
the record exists (`readonly="id"`), so a rename cannot silently stop
`code == "scrap"` from matching; the label is what users edit. The seeds carry xml ids
too, but those are for our own data files and tests — logic does not use them, because a
deleted seed breaks `env.ref` exactly as an edited code would break the other anchor,
and defending one key is better than half-defending two.

### Data — `data/qms_disposition.xml`, `noupdate="1"`

The plan's five values, seeded so a fresh install is usable and a site that renames or
reorders them is never overwritten on upgrade.

| xml id | code | name | sequence |
|---|---|---|---|
| `disposition_accept` | `accept` | Accept | 10 |
| `disposition_accept_rework` | `accept_rework` | Accept after Rework | 20 |
| `disposition_scrap` | `scrap` | Scrap | 30 |
| `disposition_return_supplier` | `return_supplier` | Return to Supplier | 40 |
| `disposition_reinspect` | `reinspect` | Re-inspect | 50 |

These are our own records and the plan's own starting vocabulary, so a plain data file is
right. Severity ranks are deliberately **not** seeded (step 3): they would be guesses about
meaning OCA never defined, onto records this module does not own.

### Views — `views/qms_disposition_views.xml`

| XML id | Type | Content |
|---|---|---|
| `qms_disposition_view_list` | list | editable `bottom`: `sequence` (`widget="handle"`), `code`, `name`, `active` (`column_invisible="True"`) |
| `qms_disposition_view_form` | form | archived ribbon, `name`, `code`, `sequence`, `description` |
| `qms_disposition_view_search` | search | field `name`; field `code`; filter `archived`, `domain="[('active', '=', False)]"` |
| `qms_disposition_action` | action | `name`: `Dispositions`, `res_model`: `qms.disposition`, `view_mode`: `list,form`, `search_view_id` |

The search view exists for the Archived filter: Odoo hides archived records from every
list and dropdown, so without it a retired disposition cannot be found again — the same
gap `qms_catalog` closed for the catalogs. `active` is kept rather than dropped, since a
disposition must stay on the historical records that used it.

| Menu | Parent | Groups | Sequence |
|---|---|---|---|
| `menu_qms_disposition` "Dispositions" | `mgmtsystem_nonconformity.menu_mgmtsystem_configuration_nonconformities` | inherited from the parent | 40 |

Beside Causes, Origins and Severities, which is where a user looks for this kind of list.

### Views — `views/mgmtsystem_nonconformity_views.xml`

| Position | Content |
|---|---|
| group `meta` inside | `disposition_id`, `readonly="state in ('done', 'cancel')"`, `options="{'no_create': True}"` |

It sits with responsible, manager and filled-in-by rather than on a page: it is a header
verdict, and plan §7.8 has it set at closure, by which point the analysis pages are
behind the user.

### `qms_nonconformity_hr` — the department bridge (step 2)

A separate module, so `qms_nonconformity` never depends on `hr`. It installs itself
exactly when both sides are present, which is what `mgmtsystem_nonconformity_hr` does
for the field itself.

```
qms_nonconformity_hr/
├── __init__.py, __manifest__.py
├── models/__init__.py, mgmtsystem_nonconformity.py
└── readme/DESCRIPTION.md
```

| Key | Value |
|---|---|
| `name` | `QMS Nonconformity HR` |
| `summary` | `Fill the nonconformity's department from the user who reports it` |
| `depends` | `qms_nonconformity`, `mgmtsystem_nonconformity_hr` |
| `auto_install` | `True` |
| `data` | none |

| Method | Decorator | Behaviour |
|---|---|---|
| `_default_department_id` | — | `self.env.user.sudo().department_id`, empty when the user has no employee |
| `_default_manager_user_id` | — | `self.env.user.sudo().employee_id.parent_id.user_id`, empty when any hop is missing |

`manager_user_id` stays required on the model, so an empty result simply leaves the form
asking. `hr.employee` is readable only by `hr.group_hr_user` and `base.group_system`
(`hr/security/ir.model.access.csv:4-5`), which is why both defaults read through
`sudo()`.

`sudo()` is needed for the same reason as the manager default, and for a second one:
`res.users.department_id` is declared `related_sudo=False`
(`hr/models/res_users.py:97`), so even reading it through the user record applies the
caller's own rights.

## Severity (step 3)

### `mgmtsystem.nonconformity.severity` — `models/mgmtsystem_nonconformity_severity.py`

`_inherit = "mgmtsystem.nonconformity.severity"`

| Field | Type | Attributes |
|---|---|---|
| `qms_severity_rank` | Integer | `string="Severity Rank"`, `default=0`, higher is more severe, `help="Higher is more severe. A nonconformity takes the severity of its most severe item, so ranks must be set for that to mean anything."` |

An explicit rank rather than reusing `sequence`: OCA exposes `sequence` as an editable
field on the severity form (`views/mgmtsystem_severity.xml:19`), so anyone tidying the
display order of a configuration list would silently re-rank analytical severity. Integer
rather than Selection so a new severity can be slotted between two existing ones without
renumbering, and higher-is-worse so the roll-up is a plain `max()` that nobody misreads.
`sequence` keeps doing display order, untouched.

### `qms.defect.code` — `models/qms_defect_code.py`

`_inherit = "qms.defect.code"`

| Field | Type | Attributes |
|---|---|---|
| `default_severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | `ondelete="restrict"` |

Plan §7.1 puts this field here rather than in `qms_catalog`, which knows nothing of the
severity model. Shown on the defect-code form and list by an inherited view.

**No ranks are seeded.** Each implementation defines its own severities and their order;
OCA's three records are placeholders with no defined meaning, so ranking them would
impose a guess. Every rank starts at 0, and the roll-up's tie rule makes that state
well-defined: with no ranks set, a nonconformity takes the severity of its first item by
`sequence` then `id`. Configuring the ranks is the implementor's job, and the field is
exposed where they configure severities.

### Views — `views/mgmtsystem_nonconformity_severity_views.xml`

Inherits `mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_severity_form`.

| Position | Content |
|---|---|
| field `sequence` after | `qms_severity_rank` |

OCA ships a form but no list view for severities, so the form is where the rank goes.

### Views — `views/qms_defect_code_views.xml`

| Inherits | Position | Content |
|---|---|---|
| `qms_catalog.qms_defect_code_view_form` | field `domain_kind` after | `default_severity_id`, `options="{'no_create': True}"` |
| `qms_catalog.qms_defect_code_view_list` | field `domain_kind` after | `default_severity_id`, `optional="show"` |

### Item severity — `models/qms_nonconformity_item.py`

| Field | Change |
|---|---|
| `severity_id` | becomes `compute="_compute_severity_id"`, `store=True`, `readonly=False`, `@api.depends("defect_code_id")` |

Plan §7.4 says onchange. A compute is used instead because an onchange only fires in a
form: items created by the inspection prefill in `qms_quality_control` would get no
severity at all. The overridable-compute pattern keeps the value editable, and a manual
severity survives until the defect code itself changes — at which point re-deriving is
the right answer, because the item is now about a different defect.

### Header roll-up — `models/mgmtsystem_nonconformity.py`

| Field | Change |
|---|---|
| `severity_id` | becomes `compute="_compute_severity_id"`, `store=True`, `readonly=False`, `tracking=True`, `@api.depends("item_ids.severity_id", "item_ids.sequence")` |

Rules, all of which the doc states because the field is a stored compute with a
deliberately incomplete dependency list:

- **no items** — leave the value alone rather than blanking what someone set; an
  editable stored compute keeps a record's value when the method does not assign it, as
  `hr.employee._compute_parent_id` relies on (`hr/models/hr_employee_base.py:253-256`)
- **items with no severity** — skipped, not treated as rank 0
- **highest `qms_severity_rank` wins**; ties, including the common case where every rank
  is still 0, resolve to the first item by `sequence` then `id`, so it degrades to "the
  first item's severity" rather than to something arbitrary — which is why
  `item_ids.sequence` is a dependency: reordering items can change the answer
- **`qms_severity_rank` is deliberately absent from `@api.depends`.** Re-ranking severities
  would otherwise recompute every nonconformity that has not been overridden, rewriting
  closed records and, because the field is tracked, posting chatter on each. The roll-up
  uses the ranks current when the items last changed, which matches how item severity
  stores what was applied (D16)

## Security — `security/ir.model.access.csv`

Mirrors the ACLs OCA gives the nonconformity itself
(`mgmtsystem_nonconformity/security/ir.model.access.csv:2-3`), since an item is part of
its parent record.

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_disposition_user` (step 2) | `qms.disposition.user` | `model_qms_disposition` | `mgmtsystem.group_mgmtsystem_user` | 1 | 0 | 0 | 0 |
| `access_qms_disposition_viewer` (step 2) | `qms.disposition.viewer` | `model_qms_disposition` | `mgmtsystem.group_mgmtsystem_viewer` | 1 | 0 | 0 | 0 |
| `access_qms_disposition_manager` (step 2) | `qms.disposition.manager` | `model_qms_disposition` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_nonconformity_item_user` | `qms.nonconformity.item.user` | `model_qms_nonconformity_item` | `mgmtsystem.group_mgmtsystem_user` | 1 | 1 | 1 | 1 |
| `access_qms_nonconformity_item_viewer` | `qms.nonconformity.item.viewer` | `model_qms_nonconformity_item` | `mgmtsystem.group_mgmtsystem_viewer` | 1 | 0 | 0 | 0 |

A viewer needs its own read row on `qms.disposition`: `group_mgmtsystem_user` implies
viewer, but not the reverse, and OCA lets a viewer read the nonconformity
(`mgmtsystem_nonconformity/security/ir.model.access.csv:3`) — rendering `disposition_id`
without read on the comodel raises an access error.

Unlike the nonconformity, the user group gets `unlink`: a mistyped analysis line is
removed, not cancelled.

## Views

### `views/qms_nonconformity_item_views.xml`

| XML id | Type | Content |
|---|---|---|
| `qms_nonconformity_item_view_list` | list | editable `bottom`: `sequence` (`widget="handle"`), `defect_code_id`, `object_part_id`, `cause_id`, `severity_id`, `qty_affected`, `note` — the two catalog fields carrying the §7.6 domain |
| `qms_nonconformity_item_view_form` | form | the same fields in a group, for the dialog a list row opens on small screens |

### `views/mgmtsystem_nonconformity_views.xml`

Inherits `mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_form`.

| Position | Content |
|---|---|
| field `analysis` after | separator "Analysis Items" and `field name="item_ids"`, `readonly="state != 'analysis'"`, using the list above |
| separator before `cause_ids` (xpath `//field[@name='cause_ids']/preceding-sibling::separator[1]`) | `invisible` 1 |
| field `cause_ids` | `invisible` 1 |

The items live **in the existing Causes and Analysis page**, after the Analysis text and
before Analysis Confirmation, which is where the header's `severity_id` already sits —
so analysis reads top to bottom: narrative, items, resolved severity. No new tab.

The header's cause list is hidden, not removed: `cause_ids` stays on the model for other
views, the API and OCA code. Its separator is hidden too, or an empty "Causes" heading
would remain — and it is selected by position rather than by `@string`, since view
inheritance rejects any translated attribute as a selector
(`odoo/addons/base/models/ir_ui_view.py:332-351`). The first attempt used
`separator[@string='Causes']` and the upgrade refused to load the view.

`readonly="state != 'analysis'"` mirrors how OCA gates `analysis` and `cause_ids` on the
same page, written as an explicit comparison rather than OCA's `state not in 'analysis'`,
which relies on substring matching. Two consequences worth knowing: the whole page is
`invisible="state in ('draft', 'cancel')"` in the base view, so items are not visible on
a draft nonconformity, and readonly is a view rule only — code that creates items during
prefill (`qms_quality_control`) is unaffected.

The header needs no `qms_effective_profile_ids` field in the arch: step 1 confirmed the
line domain resolves it without one.

## Tests — `tests/test_qms_nonconformity_item.py`

`TestNonconformityItem(TransactionCase)`, decorated `@tagged("post_install", "-at_install")`
because the fixtures create a product — see the rule in `addons/CLAUDE.md`; step 1's
first run hit it as `product_template.sale_line_warn` being NOT NULL in the database
but absent from the registry, `sale` not having loaded yet.

**Asserting on tracking takes two `self.env.cr.precommit.run()` calls.** Tracking
messages are written from the cursor's precommit queue
(`odoo/addons/mail/models/mail_thread.py:513`), which a test transaction never reaches,
and `create()` additionally calls `_track_discard` (`:335`), parking `None` against the
new record so that nothing it does later in the same transaction is tracked at all. So:
create, run the queue to clear the discard, write, run the queue again, invalidate
`message_ids`, then count. Step 2 failed twice here — once for each half.

`setUpClass` builds a catalog group and code, an
object-part group and code, a profile holding both groups, a product carrying the profile,
and a nonconformity on that product with the fields `mgmtsystem_nonconformity` requires
(`partner_id`, `origin_ids`, `description`, `responsible_user_id`, `manager_user_id`,
`user_id`). Fixture codes use `unique_code_prefix()`, imported from
`odoo.addons.qms_catalog.tests.common` — `ref_code` is unique per table and the instance
is a working database.

| Test | Asserts |
|---|---|
| `test_item_created` | an item on the nonconformity holds its defect code, and `item_ids` shows it |
| `test_item_cascade` | deleting the nonconformity deletes its items |
| `test_defect_code_restrict` | deleting a defect code used by an item raises `IntegrityError` |
| `test_effective_profiles_related` | the header's `qms_effective_profile_ids` equals the product's |
| `test_domain_matches_profile_codes` | searching `qms.defect.code` with the §7.6 domain, with the header's profiles substituted, returns the code in the profile and not one outside it, and excludes the group itself |
| `test_domain_matches_object_parts` | the same domain string against `qms.object.part` — a different model, a different relation table — returns the part in the profile and not one outside it |
| `test_domain_without_product` | the same search for a nonconformity with no product returns nothing |

The last two exercise the domain as a **search**, which is what the client ultimately
sends. Whether the client resolves `parent.` to fill it is the browser check above.

## Tests — `tests/test_qms_nonconformity_severity.py` (step 3)

`TestNonconformitySeverity(TransactionCase)`, `@tagged("post_install", "-at_install")` like
the other two classes. Fixtures create their **own** severities with explicit ranks —
`Low` 10, `High` 20, `Unranked` 0 — rather than relying on OCA's records, whose ranks
this module never sets.

| Test | Asserts |
|---|---|
| `test_item_severity_from_defect_code` | a new item takes its defect code's `default_severity_id` |
| `test_item_severity_manual_kept` | a severity set by hand on the item survives a write to another field |
| `test_item_severity_rederived_on_code_change` | changing the item's defect code replaces a manual severity with the new code's default |
| `test_header_rollup_highest_rank` | with a `Low` and a `High` item, the header takes `High` |
| `test_header_rollup_all_zero_first_item` | with every rank at 0 — the unconfigured state — the header takes the first item's severity by `sequence`, not the last or an arbitrary one |
| `test_header_rollup_follows_reorder` | two rank-0 items; moving the first below the second switches the header to the other's severity — the only test that changes an existing item's `sequence`, so the only one exercising `item_ids.sequence` in `@api.depends`. Equal ranks are deliberate: with different ranks order never decides |
| `test_header_rollup_skips_unset` | an item without severity does not count as rank 0 and does not win |
| `test_header_no_items_untouched` | a severity set on a header with no items is not blanked |
| `test_rank_change_does_not_recompute` | raising `Low`'s rank above `High` leaves the stored header severity unchanged until an item changes — `qms_severity_rank` is deliberately outside `@api.depends` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Multi-line analysis on the nonconformity, catalog dropdowns scoped to the product's profiles |
| `readme/USAGE.md` (step 3) | Analysis items in Causes and Analysis; the header's cause list is hidden because cause is per item; dispositions are configurable, and automation matches on their code. **Severity ranks start at 0 and must be set** under *Configuration → Nonconformities → Severities*: higher is more severe, and a nonconformity takes the severity of its most severe item. Until ranks are set it takes its first item's severity. Re-ranking does not rewrite existing nonconformities |

