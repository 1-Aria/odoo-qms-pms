# qms_nonconformity

Nonconformity items, header additions, code filtering, severity roll-up.
Plan: §7.4, §7.6, §7.9, D6–D9, D16.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `qms.nonconformity.item`, header `item_ids`, items in Causes and Analysis, §7.6 code filtering | done | installed and tested 2026-09-21, `exit=0`, 7 tests, 0 failures; the Analysis Items dropdown was confirmed in the browser to offer only the product's profiled leaf codes, and the page reads Analysis → Analysis Items → Analysis Confirmation with no Causes section. Two failures on the way: `setUpClass` creating a product at `at_install` hit `product_template.sale_line_warn`, fixed with the `post_install` tag; and the first placement used `separator[@string='Causes']` as an inheritance selector, which core refuses, fixed by selecting the separator positionally |
| 2 | Header: `partner_id` relaxed, responsible / manager prefill, `disposition`, and the `qms_nonconformity_hr` bridge for department | proposed | |
| 3 | `qms_severity_rank`, seed hook (must be safe to fail — inert ranks beat a failed install), `default_severity_id` on `qms.defect.code`, header roll-up, and confirming the ranks on this instance | — | |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | O2 says `partner_id` is mandatory "in a view somewhere not yet located", and that base `mgmtsystem_nonconformity` does not mark it required in model or view | the base model does mark it required, in Python | `mgmtsystem_nonconformity/models/mgmtsystem_nonconformity.py:41`: `partner_id = fields.Many2one("res.partner", "Partner", required=True)`. O2 is answered, and the override in step 2 is the one line the plan hoped for |
| 2 | §7.6 resolves the product's category on the nonconformity | the header carries `qms_effective_profile_ids`, related to the product | The plan was amended for this on 2026-09-20; `qms_catalog` computes the resolved set, so the domain reads it directly |
| 3 | §8 lists `mgmtsystem_partner` among this module's dependencies | not a dependency | `mgmtsystem_partner` adds one line — a `quality` option to `res.partner.type` (`models/res_partner.py:16`) — and never touches `mgmtsystem.nonconformity`. `partner_id` and its `required=True` both come from base `mgmtsystem_nonconformity`, which we do depend on, and nothing here uses `type='quality'` |
| 4 | §7.4 says the header's `cause_ids` "remains for compatibility and rolls up from the items" | no roll-up; the header's cause list is hidden on the form | Cause is analysis, and analysis is per item: one nonconformity can hold three defects with three different causes, so a header list of them states nothing a reader can act on. Severity rolls up because it has a rank and a defensible aggregate — the most severe item. Cause has no such ordering. The field is hidden rather than removed, so it stays available to other views, to the API and to any OCA code that reads it |
| 5 | §8 lists nine modules and does not include an HR bridge | `qms_nonconformity_hr` exists | `department_id` belongs to `mgmtsystem_nonconformity_hr`, which is `auto_install` on `hr`. Depending on it directly would force `hr` onto every site running the quality system, so the default lives in an `auto_install` bridge — the same pattern OCA uses for the field |

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
│   ├── mgmtsystem_nonconformity_severity.py              # 3 (qms_severity_rank)
│   └── qms_defect_code.py                                # 3 (default_severity_id)
├── security/ir.model.access.csv                          # 1
├── views/
│   ├── qms_nonconformity_item_views.xml                  # 1
│   └── mgmtsystem_nonconformity_views.xml                # 1 (Items tab), 2
├── data/ or hooks in __init__.py                         # 3 (severity rank seed)
├── tests/__init__.py, test_qms_nonconformity_item.py     # 1
└── readme/ DESCRIPTION.md, USAGE.md                      # 1 (DESCRIPTION), later (USAGE)
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
| `data` | `security/ir.model.access.csv`, `views/qms_nonconformity_item_views.xml`, `views/mgmtsystem_nonconformity_views.xml` |
| `installable` | `True` |

`mgmtsystem_nonconformity_product` supplies `product_id`, which the filtering resolves
through. `mgmtsystem_partner` is **not** a dependency — see divergence 3.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_nonconformity_item`, `from . import mgmtsystem_nonconformity` |

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
| `disposition` | Selection | `[("accept", "Accept"), ("accept_rework", "Accept after Rework"), ("scrap", "Scrap"), ("return_supplier", "Return to Supplier"), ("reinspect", "Re-inspect")]`, `tracking=True`, no default |

| Method | Decorator | Behaviour |
|---|---|---|
| `_default_responsible_user_id` | — | `self.env.user`, mirroring how the base model defaults `user_id` |
| `_default_manager_user_id` | — | `self.env.user.employee_id.parent_id.user_id`, read **through `sudo()`**, empty when any hop is missing |

`hr.employee` is readable only by `hr.group_hr_user` and `base.group_system`
(`hr/security/ir.model.access.csv:4-5`), so a management-system user walking
`employee_id.parent_id` unprivileged would raise `AccessError`. The defaults read the
chain with `sudo()` and return nothing rather than raising when the user has no
employee, no manager, or a manager with no user account — `manager_user_id` stays
required, so the form simply asks for it.

Both are **defaults, not computes**: they fill a new record and never revisit it, so an
edit sticks and later changes to the org chart do not rewrite existing nonconformities.

**Department is not here**: it comes from `mgmtsystem_nonconformity_hr`, so its default lives in the `qms_nonconformity_hr` bridge below.

### Views — `views/mgmtsystem_nonconformity_views.xml`

| Position | Content |
|---|---|
| group `meta` inside | `disposition`, `readonly="state in ('done', 'cancel')"` |

`disposition` sits with responsible, manager and filled-in-by rather than on a page: it
is a header verdict, and plan §7.8 has it set at closure, by which point the analysis
pages are behind the user.

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

`sudo()` is needed for the same reason as the manager default, and for a second one:
`res.users.department_id` is declared `related_sudo=False`
(`hr/models/res_users.py:97`), so even reading it through the user record applies the
caller's own rights.

## Security — `security/ir.model.access.csv`

Mirrors the ACLs OCA gives the nonconformity itself
(`mgmtsystem_nonconformity/security/ir.model.access.csv:2-3`), since an item is part of
its parent record.

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_nonconformity_item_user` | `qms.nonconformity.item.user` | `model_qms_nonconformity_item` | `mgmtsystem.group_mgmtsystem_user` | 1 | 1 | 1 | 1 |
| `access_qms_nonconformity_item_viewer` | `qms.nonconformity.item.viewer` | `model_qms_nonconformity_item` | `mgmtsystem.group_mgmtsystem_viewer` | 1 | 0 | 0 | 0 |

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
