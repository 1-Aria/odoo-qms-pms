# qms_catalog

Defect and object-part catalogs, catalog profiles, product assignment.
Plan: §7.1, §7.2, D2–D7, D24, D25.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Skeleton, `qms.catalog.mixin`, `qms.defect.code`, access, views, menus | done | installed 2026-09-18, `exit=0`; menus, group/code entry, `parent_path`, `ref_code` search and `domain_kind` carry-over all verified in the UI |
| 2 | Two-level constraint, unique `ref_code`, domain-kind compatibility, tests | done | upgraded and tested 2026-09-19, `exit=0`, 10 tests, 0 failures; `ref_code` NOT NULL and `qms_defect_code_ref_code_uniq` confirmed on the table |
| 3 | `qms.object.part` | — | |
| 4 | `qms.catalog.profile`, groups-only constraint | — | |
| 5 | Product / template / category assignment, product form views | — | |

## Divergences from the plan

Logged here, at the point of divergence. The plan is amended only when the
divergence is about intent rather than implementation (entry 4).

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | D25 says access "matches OCA's access rules for Cause and Origin", where read belongs to `mgmtsystem.group_mgmtsystem_user` and `group_mgmtsystem_viewer` (`mgmtsystem_nonconformity/security/ir.model.access.csv:4-9`). §7.2 says all internal users can read | read for `base.group_user` | Only the manager half matches OCA. Step 5 puts `qms_profile_ids` on the product, template and category forms, so an internal user opening a product would hit an access error on the profile and its catalog groups. Write, create and delete stay with `mgmtsystem.group_mgmtsystem_manager`, as in OCA |
| 2 | §7.1 lists `parent_id`, `child_ids` among the mixin's fields | declared on each concrete model | A Many2one in an `AbstractModel` cannot name the model that inherits it. `_parent_store`, `_order` and `parent_path` do stay in the mixin |
| 3 | §7.1 lists `display_name` as a computed field | only `_compute_display_name` is overridden | `display_name` already exists on every model, with `search="_search_display_name"` (`odoo/models.py:279-283`). Redeclaring the field, as OCA's Cause model does, drops that search function |
| 4 | §7.1 and D14 left `domain_kind` an unconstrained label; amended 2026-09-19 to define it as an enforced invariant | `_check_domain_kind` enforces it in the mixin | A `both` code under a `qm` group can never surface in maintenance, because profiles reference groups. The default carry-over means only a deliberate edit can break the rule |

## Folder structure

```
qms_catalog/
├── __init__.py, __manifest__.py                      # 1
├── models/
│   ├── __init__.py                                   # 1
│   ├── qms_catalog_mixin.py      # AbstractModel     # 1
│   ├── qms_defect_code.py                            # 1
│   ├── qms_object_part.py                            # 3
│   ├── qms_catalog_profile.py                        # 4
│   └── product_template.py, product_product.py, product_category.py   # 5
├── security/ir.model.access.csv                      # 1
├── views/
│   ├── qms_defect_code_views.xml                     # 1
│   ├── qms_object_part_views.xml                     # 3
│   ├── qms_catalog_profile_views.xml                 # 4
│   ├── product_views.xml          # template, variant, category forms   # 5
│   └── qms_catalog_menus.xml                         # 1
├── tests/__init__.py, test_qms_catalog.py            # 2
└── readme/ DESCRIPTION.md, USAGE.md                  # 1 (DESCRIPTION), 2 (USAGE: two-level rule)
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Catalog` |
| `summary` | `Defect and object-part catalogs with product-scoped profiles` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `product`, `mgmtsystem` |
| `data` | `security/ir.model.access.csv`, `views/qms_defect_code_views.xml`, `views/qms_catalog_menus.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_catalog_mixin`, `from . import qms_defect_code` |

## Models

### `qms.catalog.mixin` — `models/qms_catalog_mixin.py`

`models.AbstractModel` · `_name = "qms.catalog.mixin"` · `_description = "QMS Catalog Mixin"` · `_order = "parent_id, sequence"` ·
`_parent_store = True` · `_rec_names_search = ["name", "ref_code"]`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `ref_code` | Char | `string="Code"`, `required=True` (step 2 — a NOT NULL column, so the upgrade needs the existing rows to have a code) |
| `sequence` | Integer | `default=10` |
| `parent_path` | Char | `index=True` |
| `active` | Boolean | `default=True` |
| `domain_kind` | Selection | `[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")]`, `string="Domain"`, `required=True`, `default="both"` |

`parent_id` and `child_ids` are declared on each concrete model.

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("name", "parent_id.name")` | `"<parent.name> / <name>"` if `parent_id`, else `name` |

**Constraints** (step 2)

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_catalog_depth` | `@api.constrains("parent_id")` | a record's group must have no group of its own, and a record that has codes may not be given a group. Cycles are not its job: `_parent_store` checks for recursion while flushing `parent_id` and raises `UserError` first (`odoo/models.py:5378`) | `"Catalogs are two levels deep — a group and its codes. '%(name)s' cannot be nested further."` |
| `_check_domain_kind` | `@api.constrains("domain_kind", "parent_id")` | a code's domain must be compatible with its group's: `qm` under `qm`, `pm` under `pm`, any under `both`. Checked from both ends — the record against its group, and a group against its codes | `"Code '%(code)s' (%(code_kind)s) does not fit its group '%(group)s' (%(group_kind)s)."` |

**SQL constraints** (step 2)

| Name | Definition | Message |
|---|---|---|
| `ref_code_uniq` | `unique (ref_code)` | `"This code already exists."` |

Declared here, applied per concrete table: `_build_model_attributes` collects
`_sql_constraints` from every base class (`odoo/models.py:826-840`) and each model
creates its own index in `_add_sql_constraints` (`odoo/models.py:3508`). So
`qms.object.part` inherits it in step 3. Archived records are covered too.

### `qms.defect.code` — `models/qms_defect_code.py`

`models.Model` · `_name = "qms.defect.code"` · `_inherit = "qms.catalog.mixin"` · `_description = "Defect Code"`

| Field | Type | Attributes |
|---|---|---|
| `parent_id` | Many2one → `qms.defect.code` | `string="Group"`, `ondelete="restrict"`, `index=True` |
| `child_ids` | One2many → `qms.defect.code` | inverse `parent_id`, `string="Codes"` |

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_defect_code_user` | `qms.defect.code.user` | `model_qms_defect_code` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_defect_code_manager` | `qms.defect.code.manager` | `model_qms_defect_code` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |

## Views — `views/qms_defect_code_views.xml`

| XML id | Type | Content |
|---|---|---|
| `qms_defect_code_view_list` | list | `sequence` (`widget="handle"`), `ref_code`, `name`, `parent_id`, `domain_kind`, `active` (`column_invisible="True"`) |
| `qms_defect_code_view_form` | form | see below |
| `qms_defect_code_view_search` | search | see below |

**Form** `qms_defect_code_view_form`

```
form
└── sheet
    ├── widget web_ribbon  title="Archived" bg_color="text-bg-danger" invisible="active"
    ├── field active  invisible="1"
    ├── group
    │   ├── group: name, ref_code
    │   └── group: parent_id, domain_kind
    └── notebook
        └── page name="codes" string="Codes"  invisible="parent_id"
            └── field child_ids  context="{'default_domain_kind': domain_kind}"
                └── list editable="bottom": sequence (widget="handle"), ref_code, name, domain_kind
```

**Search** `qms_defect_code_view_search`

| Element | Attributes |
|---|---|
| field `name` | `filter_domain="['\|', ('name', 'ilike', self), ('ref_code', 'ilike', self)]"` |
| field `parent_id` | |
| filter `groups` | `string="Groups"`, `domain="[('parent_id', '=', False)]"` |
| filter `codes` | `string="Codes"`, `domain="[('parent_id', '!=', False)]"` |
| separator | |
| filter `archived` | `string="Archived"`, `domain="[('active', '=', False)]"` |
| group by `group_by_parent` | `string="Group"`, `context="{'group_by': 'parent_id'}"` |
| group by `group_by_domain_kind` | `string="Domain"`, `context="{'group_by': 'domain_kind'}"` |

**Action** `qms_defect_code_action`

| Field | Value |
|---|---|
| model | `ir.actions.act_window` |
| `name` | `Defect Codes` |
| `res_model` | `qms.defect.code` |
| `view_mode` | `list,form` |
| `search_view_id` | `qms_defect_code_view_search` |

## Menus — `views/qms_catalog_menus.xml`

| XML id | Name | Parent | Action | Groups | Sequence |
|---|---|---|---|---|---|
| `menu_qms_catalog` | `Catalogs` | `mgmtsystem.menu_mgmtsystem_configuration` | — | `mgmtsystem.group_mgmtsystem_manager` | 20 |
| `menu_qms_defect_code` | `Defect Codes` | `menu_qms_catalog` | `qms_defect_code_action` | — | 10 |

## Tests — `tests/test_qms_catalog.py` (step 2)

`odoo.tests.common.TransactionCase` · class `TestQmsCatalog` · `tests/__init__.py`: `from . import test_qms_catalog`

`setUpClass` creates group `Fabric Defect` / `FAB` (`qm`) and code `Torn` / `FAB-01` (`qm`) under it.

Conventions: every `assertRaises` block runs inside `self.cr.savepoint()`, so the
rejected row is rolled back before the next assertion. `ValidationError` needs no
flush — `create()` and `write()` call `_validate_fields` directly
(`odoo/models.py:5297`, and `4835`, `4858`). Neither do the two database errors:
`_create` runs the INSERT straight away (`odoo/models.py:5224`), so a duplicate or
missing `ref_code` raises at `create()`. Those two tests still call `flush_model()`
under `mute_logger("odoo.sql_db")` — it costs nothing and covers the write path,
where UPDATEs really are deferred.

| Test | Asserts |
|---|---|
| `test_display_name` | group → `Fabric Defect`; code → `Fabric Defect / Torn` |
| `test_name_search_ref_code` | `name_search("FAB-01")` returns the code |
| `test_depth_code_under_code` | a code given a code as its group raises `ValidationError` |
| `test_depth_group_with_codes` | a group that has codes, given a group, raises `ValidationError` |
| `test_depth_self_parent` | a record set as its own group raises `UserError` from the `_parent_store` recursion check |
| `test_ref_code_unique` | a second record with `FAB-01` raises `IntegrityError` |
| `test_ref_code_required` | creating a record without `ref_code` raises `IntegrityError` |
| `test_domain_kind_mismatch` | a `pm` code under the `qm` group raises `ValidationError` |
| `test_domain_kind_both_group` | under a `both` group, `qm`, `pm` and `both` codes are all accepted |
| `test_domain_kind_group_narrowed` | a `both` group holding a `pm` code, changed to `qm`, raises `ValidationError` |

The `domain_kind` carry-over is a view context default, not Python, so it is verified in the UI rather than here.

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | `Coded vocabularies for defects and object parts, organised as two-level trees (group → code), scoped to products through catalog profiles.` |
| `readme/USAGE.md` (step 2) | The two-level rule: a record with no group is a code group, its children are codes, and no third level is allowed. A code's domain must fit its group's — `qm` under `qm`, `pm` under `pm`, any under `both`. `ref_code` is required and unique within each catalog |
