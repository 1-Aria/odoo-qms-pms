# qms_catalog

Defect and object-part catalogs, catalog profiles, product assignment.
Plan: §7.1, §7.2, D2–D7, D24, D25.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Skeleton, `qms.catalog.mixin`, `qms.defect.code`, access, views, menus | done | installed 2026-09-18, `exit=0`; menus, group/code entry, `parent_path`, `ref_code` search and `domain_kind` carry-over all verified in the UI |
| 2 | Two-level constraint, unique `ref_code`, domain-kind compatibility, tests | done | upgraded and tested 2026-09-19, `exit=0`, 10 tests, 0 failures; `ref_code` NOT NULL and `qms_defect_code_ref_code_uniq` confirmed on the table |
| 3 | `qms.object.part`, shared test base class | done | upgraded and tested 2026-09-19, `exit=0`, 21 tests, 0 failures; `qms_object_part_ref_code_uniq` and `ref_code` NOT NULL confirmed on its own table; object parts created in the UI |
| 4 | `qms.catalog.profile`, groups-only constraint, `profile_ids` inverse | proposed | |
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
│         common.py               # 3 (shared test base class)
│         test_qms_catalog_profile.py   # 4
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
| `data` | `security/ir.model.access.csv`, `views/qms_defect_code_views.xml`, `views/qms_object_part_views.xml` (step 3), `views/qms_catalog_profile_views.xml` (step 4), `views/qms_catalog_menus.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_catalog_mixin`, `from . import qms_defect_code`, `from . import qms_object_part` (step 3), `from . import qms_catalog_profile` (step 4) |

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

### `qms.object.part` — `models/qms_object_part.py` (step 3)

`models.Model` · `_name = "qms.object.part"` · `_inherit = "qms.catalog.mixin"` · `_description = "Object Part"`

| Field | Type | Attributes |
|---|---|---|
| `parent_id` | Many2one → `qms.object.part` | `string="Group"`, `ondelete="restrict"`, `index=True` |
| `child_ids` | One2many → `qms.object.part` | inverse `parent_id`, `string="Codes"` |

Everything else — the depth and domain-kind constraints, `ref_code` uniqueness on
its own table, the display name, ordering and `parent_path` — comes from the mixin.

**Both catalogs gain the inverse of the profile's group fields** (step 4). It is the
other end of an existing relation, so it costs one line and no table, and §7.6 of the
plan filters through it.

| Model | Field | Type | Attributes |
|---|---|---|---|
| `qms.defect.code` | `profile_ids` | Many2many → `qms.catalog.profile` | `relation="qms_profile_defect_group_rel"`, `column1="defect_code_id"`, `column2="profile_id"`, `string="Profiles"` |
| `qms.object.part` | `profile_ids` | Many2many → `qms.catalog.profile` | `relation="qms_profile_object_part_group_rel"`, `column1="object_part_id"`, `column2="profile_id"`, `string="Profiles"` |

### `qms.catalog.profile` — `models/qms_catalog_profile.py` (step 4)

`models.Model` · `_name = "qms.catalog.profile"` · `_description = "Catalog Profile"` · `_order = "name"`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `active` | Boolean | `default=True` |
| `domain_kind` | Selection | same selection as the catalogs, `string="Domain"`, `required=True`, `default="both"` |
| `defect_group_ids` | Many2many → `qms.defect.code` | `relation="qms_profile_defect_group_rel"`, `column1="profile_id"`, `column2="defect_code_id"`, `string="Defect Groups"`, `domain=[("parent_id", "=", False)]` |
| `object_part_group_ids` | Many2many → `qms.object.part` | `relation="qms_profile_object_part_group_rel"`, `column1="profile_id"`, `column2="object_part_id"`, `string="Object Part Groups"`, `domain=[("parent_id", "=", False)]` |

`product_ids`, `product_tmpl_ids` and `categ_ids` come in step 5, declared beside the
fields they mirror on `product.product`, `product.template` and `product.category`.

**Constraints**

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_groups_only` | `@api.constrains("defect_group_ids", "object_part_group_ids")` | every referenced record must be a group, i.e. have no `parent_id`. The field `domain` only filters the dropdown; §7.6 skips a code attached directly, so it would fail silently | `"A profile bundles code groups, not codes. '%(name)s' belongs to '%(group)s'."` |
| `_check_domain_kind` | `@api.constrains("domain_kind", "defect_group_ids", "object_part_group_ids")` | **decision pending** — see below | `"Group '%(group)s' (%(group_kind)s) does not fit profile '%(profile)s' (%(profile_kind)s)."` |

**Pending: does the domain invariant reach the profile?** The group/code rule does
not transfer unchanged. A code has exactly one group, so the group's domain is a
ceiling. A group belongs to many profiles, so a `both` group legitimately appears
in a `qm` profile and a `pm` one at the same time.

| Option | Rejects |
|---|---|
| a — clash only (recommended) | a `pm` group in a `qm` profile, and the reverse. `both` on either side is accepted |
| b — ceiling, as for codes | anything whose domain differs from the profile's, unless the profile is `both` |
| c — no constraint | nothing; `domain_kind` on the profile stays a label |

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_defect_code_user` | `qms.defect.code.user` | `model_qms_defect_code` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_defect_code_manager` | `qms.defect.code.manager` | `model_qms_defect_code` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_object_part_user` (step 3) | `qms.object.part.user` | `model_qms_object_part` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_object_part_manager` (step 3) | `qms.object.part.manager` | `model_qms_object_part` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_catalog_profile_user` (step 4) | `qms.catalog.profile.user` | `model_qms_catalog_profile` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_catalog_profile_manager` (step 4) | `qms.catalog.profile.manager` | `model_qms_catalog_profile` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |

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

## Views — `views/qms_object_part_views.xml` (step 3)

The defect-code views with `qms.defect.code` replaced by `qms.object.part` and the
ids renamed to `qms_object_part_view_list` / `_form` / `_search` and
`qms_object_part_action` (`name`: `Object Parts`). Same structure, same filters,
same Codes tab and carry-over context.

## Views — `views/qms_catalog_profile_views.xml` (step 4)

| XML id | Type | Content |
|---|---|---|
| `qms_catalog_profile_view_list` | list | `name`, `domain_kind`, `active` (`column_invisible="True"`) |
| `qms_catalog_profile_view_form` | form | archived ribbon and hidden `active` as in the catalogs; group: `name`, `domain_kind`; then `defect_group_ids` and `object_part_group_ids`, each `widget="many2many_tags"` with `options="{'no_create': True}"`. Step 5 adds the assignment tab |
| `qms_catalog_profile_view_search` | search | field `name`; field `defect_group_ids`; field `object_part_group_ids`; filter `archived`; group by `domain_kind` |
| `qms_catalog_profile_action` | action | `name`: `Catalog Profiles`, `res_model`: `qms.catalog.profile`, `view_mode`: `list,form`, `search_view_id` |

## Menus — `views/qms_catalog_menus.xml`

| XML id | Name | Parent | Action | Groups | Sequence |
|---|---|---|---|---|---|
| `menu_qms_catalog` | `Catalogs` | `mgmtsystem.menu_mgmtsystem_configuration` | — | `mgmtsystem.group_mgmtsystem_manager` | 20 |
| `menu_qms_defect_code` | `Defect Codes` | `menu_qms_catalog` | `qms_defect_code_action` | — | 10 |
| `menu_qms_object_part` (step 3) | `Object Parts` | `menu_qms_catalog` | `qms_object_part_action` | — | 20 |
| `menu_qms_catalog_profile` (step 4) | `Catalog Profiles` | `menu_qms_catalog` | `qms_catalog_profile_action` | — | 30 |

## Tests — `tests/` (step 2, restructured in step 3)

| File | Content |
|---|---|
| `tests/__init__.py` | `from . import common`, `from . import test_qms_catalog`, `from . import test_qms_catalog_profile` (step 4) |
| `tests/common.py` | `CatalogCommon`, a plain class holding `setUpClass` and every test method, driven by a `model_name` attribute, with `allow_inherited_tests_method = True`. The loader never scans this file anyway: `_get_tests_modules` only imports modules named `test_*` (`odoo/tests/loader.py:56-67`) |
| `tests/test_qms_catalog.py` | `TestQmsDefectCode(CatalogCommon, TransactionCase)` with `model_name = "qms.defect.code"`, and `TestQmsObjectPart(CatalogCommon, TransactionCase)` with `model_name = "qms.object.part"`; plus `TestCatalogIndependence(TransactionCase)` |

The base class order is load-bearing: `CatalogCommon` comes **first**, so its
`setUpClass` is the one that runs and its `super().setUpClass()` reaches
`TransactionCase` through the MRO. Reversed, `TransactionCase.setUpClass` wins,
the fixtures are never created and every test fails on a missing attribute.

`allow_inherited_tests_method = True` is equally load-bearing, and fails quietly
rather than loudly. Odoo collects test methods from a class's own `__dict__`
only, unless that flag is set (`odoo/tests/loader.py:29-38`); without it the two
subclasses yield no tests at all and the run reports success. It is declared once
on `CatalogCommon`, since `getattr` walks the MRO. The loader calls the mechanism
provisional in a comment, so re-check it on any Odoo upgrade.

**The run must report 21 tests** through step 3 — ten per catalog plus the
independence test — and 21 plus the profile class from step 4 on. A smaller number
means collection broke, not that the suite got faster.

Both catalogs are the mixin's behaviour, so the suite runs twice over the same
assertions — 20 tests instead of 10 — and step 4 adds its profile tests without
copying any of this.

`setUpClass` creates group `Group A` / `GRP` (`qm`) and code `Code One` / `GRP-01`
(`qm`) under it, in `cls.env[cls.model_name]`.

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
| `test_display_name` | group → `Group A`; code → `Group A / Code One` |
| `test_name_search_ref_code` | `name_search("GRP-01")` returns the code |
| `test_depth_code_under_code` | a code given a code as its group raises `ValidationError` |
| `test_depth_group_with_codes` | a group that has codes, given a group, raises `ValidationError` |
| `test_depth_self_parent` | a record set as its own group raises `UserError` from the `_parent_store` recursion check |
| `test_ref_code_unique` | a second record with `GRP-01` raises `IntegrityError` |
| `test_ref_code_required` | creating a record without `ref_code` raises `IntegrityError` |
| `test_domain_kind_mismatch` | a `pm` code under the `qm` group raises `ValidationError` |
| `test_domain_kind_both_group` | under a `both` group, `qm`, `pm` and `both` codes are all accepted |
| `test_domain_kind_group_narrowed` | a `both` group holding a `pm` code, changed to `qm`, raises `ValidationError` |

The `domain_kind` carry-over is a view context default, not Python, so it is verified in the UI rather than here.

**`TestCatalogProfile(TransactionCase)`** (step 4), in `tests/test_qms_catalog_profile.py`, imported from `tests/__init__.py`:

| Test | Asserts |
|---|---|
| `test_groups_accepted` | a profile takes a defect group and an object-part group |
| `test_defect_code_rejected` | a code in `defect_group_ids` raises `ValidationError` |
| `test_object_part_code_rejected` | a code in `object_part_group_ids` raises `ValidationError` |
| `test_profile_ids_inverse` | after assignment, the group's `profile_ids` contains the profile, and removing the group from the profile empties it |
| `test_domain_kind_*` | per the option chosen above |

**`TestCatalogIndependence(TransactionCase)`** (step 3), outside `CatalogCommon`:

| Test | Asserts |
|---|---|
| `test_ref_code_shared_across_catalogs` | the same `ref_code` created in `qms.defect.code` and `qms.object.part` in one transaction, then flushed, leaves both records alive — uniqueness is per table, not across the catalogs |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | `Coded vocabularies for defects and object parts, organised as two-level trees (group → code), scoped to products through catalog profiles.` |
| `readme/USAGE.md` (step 2) | The two-level rule: a record with no group is a code group, its children are codes, and no third level is allowed. A code's domain must fit its group's — `qm` under `qm`, `pm` under `pm`, any under `both`. `ref_code` is required and unique within each catalog |
