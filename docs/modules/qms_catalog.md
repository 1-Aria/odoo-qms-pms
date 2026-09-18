# qms_catalog

Defect and object-part catalogs, catalog profiles, product assignment.
Plan: §7.1, §7.2, D2–D7, D24, D25.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Skeleton, `qms.catalog.mixin`, `qms.defect.code`, access, views, menus | proposed | |
| 2 | Two-level constraint, unique `ref_code`, tests | — | |
| 3 | `qms.object.part` | — | |
| 4 | `qms.catalog.profile`, groups-only constraint | — | |
| 5 | Product / template / category assignment, product form views | — | |

## Divergences from the plan

Logged here, at the point of divergence; the plan is not amended.

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | D25 says access "matches OCA's access rules for Cause and Origin", where read belongs to `mgmtsystem.group_mgmtsystem_user` and `group_mgmtsystem_viewer` (`mgmtsystem_nonconformity/security/ir.model.access.csv:4-9`). §7.2 says all internal users can read | read for `base.group_user` | Only the manager half matches OCA. Step 5 puts `qms_profile_ids` on the product, template and category forms, so an internal user opening a product would hit an access error on the profile and its catalog groups. Write, create and delete stay with `mgmtsystem.group_mgmtsystem_manager`, as in OCA |
| 2 | §7.1 lists `parent_id`, `child_ids` among the mixin's fields | declared on each concrete model | A Many2one in an `AbstractModel` cannot name the model that inherits it. `_parent_store`, `_order` and `parent_path` do stay in the mixin |
| 3 | §7.1 lists `display_name` as a computed field | only `_compute_display_name` is overridden | `display_name` already exists on every model, with `search="_search_display_name"` (`odoo/models.py:279-283`). Redeclaring the field, as OCA's Cause model does, drops that search function |

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
| `ref_code` | Char | `string="Code"` |
| `sequence` | Integer | `default=10` |
| `parent_path` | Char | `index=True` |
| `active` | Boolean | `default=True` |
| `domain_kind` | Selection | `[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")]`, `string="Domain"`, `required=True`, `default="both"` |

`parent_id` and `child_ids` are declared on each concrete model.

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("name", "parent_id.name")` | `"<parent.name> / <name>"` if `parent_id`, else `name` |

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

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | `Coded vocabularies for defects and object parts, organised as two-level trees (group → code), scoped to products through catalog profiles.` |
