# qms_catalog

Defect and object-part catalogs, catalog profiles, product assignment.
Plan: §7.1, §7.2, D2–D7, D24, D25.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Skeleton, `qms.catalog.mixin`, `qms.defect.code`, access, views, menus | done | installed 2026-09-18, `exit=0`; menus, group/code entry, `parent_path`, `ref_code` search and `domain_kind` carry-over all verified in the UI |
| 2 | Two-level constraint, unique `ref_code`, domain-kind compatibility, tests | done | upgraded and tested 2026-09-19, `exit=0`, 10 tests, 0 failures; `ref_code` NOT NULL and `qms_defect_code_ref_code_uniq` confirmed on the table |
| 3 | `qms.object.part`, shared test base class | done | upgraded and tested 2026-09-19, `exit=0`, 21 tests, 0 failures; `qms_object_part_ref_code_uniq` and `ref_code` NOT NULL confirmed on its own table; object parts created in the UI |
| 4 | `qms.catalog.profile`, groups-only constraint, `profile_ids` inverse | done | upgraded and tested 2026-09-19, `exit=0`, 28 tests, 0 failures; `qms_catalog_profile` plus `qms_profile_defect_group_rel` and `qms_profile_object_part_group_rel` confirmed in the database; profile built in the UI with groups-only dropdowns |
| 5 | Product / template / category assignment, effective-profile resolution, product form views | done | upgraded and tested 2026-09-20, `exit=0`, 34 tests, 0 failures; forms checked in the UI. The first run failed `test_category_ancestor_invalidation`: the category compute resolved the chain with one `parent_of` search, which caches no ancestor, so a write to a grandparent left a descendant stale. Fixed by walking `parent_id`, which is the path `@api.depends` names |
| ~~6~~ | ~~Assignment restricted to the management-system manager~~ | dropped | attempted and reverted 2026-09-20; the tree is back to the step 5 state |

**Why step 6 was dropped.** Writing `qms_profile_ids` from a product form only checks
write access on the product, so any departmental administrator with product write
could change catalog assignment. The attempt put
`groups="mgmtsystem.group_mgmtsystem_manager"` on the three `qms_profile_ids` fields
and `compute_sudo=True` on the three effective fields. It was reverted because the
cost outweighed the protection:

- `categ_id` stays writable by those same administrators, and moving a product between
  categories changes its effective profiles anyway. Restricting one field and not the
  other is a half-door.
- Field-level `groups` removes the field from imports, exports and `copy()` for
  everyone else, so assignment would be dropped silently rather than refused.
- Every future module touching `qms_profile_ids` would have to remember `sudo()`.
- The plan prefers suggesting over enforcing, with maintenance cost as the governing
  constraint, and the threat model here is trusted administrators.

**Two things learned, worth keeping:**

1. A test that creates `res.users` or `res.partner` must be
   `@tagged("post_install", "-at_install")`. `at_install` runs as the module loads —
   `qms_catalog` is 82nd of 306, before `account` — and `res.partner.autopost_bills`
   is then NOT NULL in the database but absent from the registry, so no default
   applies and the INSERT fails. OCA documents the same trap in
   `maintenance_plan/tests/common.py:10-14`.
2. An access test proves nothing unless the user can perform the operation for every
   other reason. The first version's "write refused" test passed because the user
   lacked write on `product.product` entirely, not because of the field restriction;
   it would have passed with the restriction removed. Such a test needs a positive
   control — the same user writing an ordinary field first — and the acting users need
   `product.group_product_manager`.


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
│         test_qms_catalog_assignment.py # 5
└── readme/ DESCRIPTION.md, USAGE.md                  # 1 (DESCRIPTION), 2 and 5 (USAGE)
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
| `data` | `security/ir.model.access.csv`, `views/qms_defect_code_views.xml`, `views/qms_object_part_views.xml` (step 3), `views/qms_catalog_profile_views.xml` (step 4), `views/product_views.xml` (step 5), `views/qms_catalog_menus.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_catalog_mixin`, `from . import qms_defect_code`, `from . import qms_object_part` (step 3), `from . import qms_catalog_profile` (step 4), `from . import product_category`, `from . import product_template`, `from . import product_product` (step 5) |

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

**Assignment fields** (step 5). Each shares its table with the `qms_profile_ids` field
it mirrors, so every relation is declared twice and created once.

| Field | Type | Attributes |
|---|---|---|
| `product_ids` | Many2many → `product.product` | `relation="qms_profile_product_rel"`, `column1="profile_id"`, `column2="product_id"`, `string="Products"` |
| `product_tmpl_ids` | Many2many → `product.template` | `relation="qms_profile_product_tmpl_rel"`, `column1="profile_id"`, `column2="product_tmpl_id"`, `string="Product Templates"` |
| `categ_ids` | Many2many → `product.category` | `relation="qms_profile_categ_rel"`, `column1="profile_id"`, `column2="categ_id"`, `string="Product Categories"` |

**Constraints**

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_groups_only` | `@api.constrains("defect_group_ids", "object_part_group_ids")` | every referenced record must be a group, i.e. have no `parent_id`. The field `domain` only filters the dropdown; §7.6 skips a code attached directly, so it would fail silently | `"A profile bundles code groups, not codes. '%(name)s' belongs to '%(group)s'."` |
| `_check_domain_kind` | `@api.constrains("domain_kind", "defect_group_ids", "object_part_group_ids")` | **clash only**: reject a `pm` group in a `qm` profile and a `qm` group in a `pm` profile. `both` on either side is accepted | `"Group '%(group)s' (%(group_kind)s) does not fit profile '%(profile)s' (%(profile_kind)s)."` |

The group/code ceiling of step 2 deliberately does **not** transfer here. A code has
exactly one group, so its group's domain can be a ceiling; a group belongs to many
profiles, so a `both` group must be free to sit in a `qm` profile and a `pm` one at
the same time. Only the direct clash is wrong.

### `product.category` — `models/product_category.py` (step 5)

`_inherit = "product.category"`

| Field | Type | Attributes |
|---|---|---|
| `qms_profile_ids` | Many2many → `qms.catalog.profile` | `relation="qms_profile_categ_rel"`, `column1="categ_id"`, `column2="profile_id"`, `string="Catalog Profiles"` |
| `qms_effective_profile_ids` | Many2many → `qms.catalog.profile` | `compute="_compute_qms_effective_profile_ids"`, `recursive=True`, `string="Effective Catalog Profiles"`, not stored |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_effective_profile_ids` | `@api.depends("qms_profile_ids", "parent_id.qms_effective_profile_ids")` | `category.qms_profile_ids | category.parent_id.qms_effective_profile_ids` — a walk up the chain, one level per hop |

**The computation must follow the dependency path.** For a non-stored recursive
field, `modified()` cascades only through records whose value is already in cache
(`odoo/models.py:7218-7227`, the `else` branch). Walking `parent_id` computes and
caches every ancestor on the way up, which is the trail the cascade follows, so a
write at any level invalidates everything below it. Where nothing is cached, nothing
needs invalidating: the next read rebuilds the chain.

Resolving the chain in one `parent_of` search instead — which `product.category`
supports, being `_parent_store` — returns the same value but caches no ancestor.
Step 5's first run proved the difference: `test_category_ancestor_invalidation`
failed, the child keeping a stale empty set after a profile was added to its
grandparent. `stock.location.child_internal_location_ids` is written the search way
(`odoo/addons/stock/models/stock_location.py:55-61`, `163-167`) and carries the same
latent staleness; it simply has no test that exposes it.

`recursive=True` is required by the dependency shape (`odoo/fields.py:259-261`; Odoo
sets it itself with a warning at `821-823`). Without the self-referential dependency
the best declarable one stops at `parent_id`, and editing a grandparent would never
reach a grandchild at all.

### `product.template` — `models/product_template.py` (step 5)

`_inherit = "product.template"`

| Field | Type | Attributes |
|---|---|---|
| `qms_profile_ids` | Many2many → `qms.catalog.profile` | `relation="qms_profile_product_tmpl_rel"`, `column1="product_tmpl_id"`, `column2="profile_id"`, `string="Catalog Profiles"` |
| `qms_effective_profile_ids` | Many2many → `qms.catalog.profile` | computed, not stored, `@api.depends("qms_profile_ids", "categ_id.qms_effective_profile_ids")` → own profiles `|` the category's effective set |

### `product.product` — `models/product_product.py` (step 5)

`_inherit = "product.product"`

| Field | Type | Attributes |
|---|---|---|
| `qms_profile_ids` | Many2many → `qms.catalog.profile` | `relation="qms_profile_product_rel"`, `column1="product_id"`, `column2="profile_id"`, `string="Catalog Profiles"` |
| `qms_effective_profile_ids` | Many2many → `qms.catalog.profile` | computed, not stored, `@api.depends("qms_profile_ids", "product_tmpl_id.qms_effective_profile_ids")` → own profiles `|` the template's effective set, which already folds in the category |

Neither product-level field is recursive: neither depends on itself. The three
computations together are the whole of plan D6 — additive across the levels, with a
category profile reaching its subcategories — expressed once, in Python, and
testable here rather than only through a view domain in `qms_nonconformity`.

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_defect_code_user` | `qms.defect.code.user` | `model_qms_defect_code` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_defect_code_manager` | `qms.defect.code.manager` | `model_qms_defect_code` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_object_part_user` (step 3) | `qms.object.part.user` | `model_qms_object_part` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_object_part_manager` (step 3) | `qms.object.part.manager` | `model_qms_object_part` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_catalog_profile_user` (step 4) | `qms.catalog.profile.user` | `model_qms_catalog_profile` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_qms_catalog_profile_manager` (step 4) | `qms.catalog.profile.manager` | `model_qms_catalog_profile` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |

Step 5 adds no rows: `product.product`, `product.template` and `product.category`
carry their own access rules from core.

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
| `qms_catalog_profile_view_form` | form | archived ribbon and hidden `active` as in the catalogs; group: `name`, `domain_kind`; then `defect_group_ids` and `object_part_group_ids`, each `widget="many2many_tags"` with `options="{'no_create': True}"`. Step 5 adds a notebook page `assignment` "Assignment" holding `product_ids`, `product_tmpl_ids` and `categ_ids`, each `widget="many2many_tags"` |
| `qms_catalog_profile_view_search` | search | field `name`; field `defect_group_ids`; field `object_part_group_ids`; filter `archived`; group by `domain_kind` |
| `qms_catalog_profile_action` | action | `name`: `Catalog Profiles`, `res_model`: `qms.catalog.profile`, `view_mode`: `list,form`, `search_view_id` |

## Views — `views/product_views.xml` (step 5)

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `product_template_form_view` | `product.product_template_form_view` | `<notebook>` inside | page `qms_catalog_profiles` "Catalog Profiles": `qms_profile_ids` (`string="Assigned"`, `widget="many2many_tags"`, `options="{'no_create': True}"`) and `qms_effective_profile_ids` (`string="Effective"`, `widget="many2many_tags"`, `readonly="1"`) |
| `product_category_form_view` | `product.product_category_form_view` | group `name="first"` after | group "Catalog Profiles" with the same two fields |

The label is "Catalog Profiles", not "Quality Catalog": a profile carries
`domain_kind` and serves maintenance as readily as quality.

The variant form needs no inheritance of its own: core builds
`product.product_normal_form_view` from the template form in `mode="primary"`
(`odoo/addons/product/views/product_views.xml:480-486`), so the page appears there
resolved against `product.product` — the variant's own profiles, and its own
effective set, which shows what the template and category contribute.

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
| `tests/__init__.py` | `from . import common`, `from . import test_qms_catalog`, `from . import test_qms_catalog_profile` (step 4), `from . import test_qms_catalog_assignment` (step 5) |
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

**The run must report 34 tests** from step 5 on. Earlier: 28 through step 4,
21 through step 3. A smaller number means collection broke, not that the
suite got faster. `odoo.tests.stats` counts module-level entries on top.

Both catalogs are the mixin's behaviour, so the suite runs twice over the same
assertions — 20 tests instead of 10 — and step 4 adds its profile tests without
copying any of this.

`setUpClass` creates group `Group A` and code `Code One` (`qm`) under it, in
`cls.env[cls.model_name]`.

**Fixtures must not assume an empty table.** `ref_code` is unique across the whole
table and the instance is a working database, so every fixture code is built from
`cls.code_prefix = unique_code_prefix()` — for example `f"{cls.code_prefix}-GRP-01"`.
`unique_code_prefix()` is a module-level helper in `tests/common.py`, used by all
three test files. Fixed codes such as `FAB` passed only until the same code existed
for real, then failed in `setUpClass` and took a whole class down with them.

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
| `test_name_search_ref_code` | `name_search(f"{code_prefix}-GRP-01")` returns the code |
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
| `test_domain_kind_clash` | a `pm` group in a `qm` profile raises `ValidationError`, and the reverse |
| `test_domain_kind_profile_narrowed` | a `both` profile holding a `pm` group, changed to `qm`, raises `ValidationError` — the only test covering `domain_kind` in the constraint's own trigger list |
| `test_domain_kind_both_accepted` | a `both` group in a `qm` profile, and any group in a `both` profile, are accepted |

**`TestCatalogAssignment(TransactionCase)`** (step 5), in `tests/test_qms_catalog_assignment.py`.
Fixtures: categories `Parent` → `Child`, a template in `Child` with one variant, and
three profiles — one on the parent category, one on the template, one on the variant.

| Test | Asserts |
|---|---|
| `test_category_chain` | the child category's effective set contains the parent category's profile |
| `test_template_effective` | the template's effective set is its own profile plus the category chain's |
| `test_product_effective` | the variant's effective set is all three — the additive rule of plan D6, in one assertion |
| `test_product_without_assignment` | a product with no profile anywhere resolves to an empty set, which is what makes the §7.6 dropdown fall back to empty rather than to everything |
| `test_category_ancestor_invalidation` | read the child's effective set, add a profile to the **grand**parent category, read again — the new profile is there. This is what `recursive=True` buys; with a `parent_id`-only dependency the second read returns the cached value |
| `test_profile_inverse_assignment` | assigning from the profile side populates `qms_profile_ids` on the product, template and category, and clearing it empties them |

**`TestCatalogIndependence(TransactionCase)`** (step 3), outside `CatalogCommon`:

| Test | Asserts |
|---|---|
| `test_ref_code_shared_across_catalogs` | the same `ref_code` created in `qms.defect.code` and `qms.object.part` in one transaction, then flushed, leaves both records alive — uniqueness is per table, not across the catalogs |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | `Coded vocabularies for defects and object parts, organised as two-level trees (group → code), scoped to products through catalog profiles.` |
| `readme/USAGE.md` (steps 2, 5) | Two sections. **Catalogs**: the two-level rule, the domain rule, and `ref_code` required and unique within each catalog including archived records. **Catalog profiles**: profiles bundle groups not codes, a group's domain must not clash with the profile's, assignment on variant / product / category is additive and reaches parent categories, the Effective field shows the result, and a product with no profile offers no codes until the filter is cleared |
