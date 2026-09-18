# CLAUDE.md

Working context for the Odoo QMS/PMS module development project.

---

## What this is

A set of custom Odoo 18.0 CE modules implementing a unified Quality Management
and Plant Maintenance pipeline on top of OCA modules.

**The architecture lives in `docs/Odoo-QMS-PMS-Development-Plan.md`.** Read it before
starting work on any module. It describes the intended models, fields, relationships
and delivery phases, and §9 records the design decisions with their rationale and
the alternatives that were rejected.

**The plan is a work in progress, not a specification to follow.** It was written
without inspecting the Odoo and OCA source, and it contains errors. Examples found
so far: the §7.6 filter traversed a `product.category.product_tmpl_ids` field that
does not exist, the plan's claim that category scoping matched `quality_control_oca`
was wrong because QC also walks up parent categories, and the `qms_catalog`
dependencies did not fit how the module is meant to be used. Treat every field
name, method, dependency and claim about OCA behaviour in the plan as unverified
until checked against the code. The technical reality in the code comes first.

This file says how to *work* here. The plan says *what* to build and *why*.
Neither duplicates the other. If something architectural is missing, it belongs
in the plan, not here.

---

## Ground rules

### 1. The reference code is the source of truth

The reference code is the **exact code the instance runs**. It lives next to this repo inside `Odoo-Build/`:

- `../odoo` (`Odoo-Build/odoo`): Odoo core, checked out at the image's pinned `ODOO_REF`.
  Core addons are in `odoo/addons/`; `base` and friends are in `odoo/odoo/addons/`.
- `../oca` (`Odoo-Build/oca`): the OCA repos mounted into the container, including the
  git-aggregated merges in `management-system`.

Reference and runtime are the same files, so they cannot drift. If in doubt, confirm that
`git -C ../odoo rev-parse HEAD` equals `ODOO_REF` in `../revisions/<ODOO_REVISION>`.

**Read the actual source before asserting how any OCA or core model behaves.**
Not from memory, not from the plan, not from an older Odoo version's API.

This is not a nicety. During the design phase, confident assertions about OCA
internals were wrong repeatedly and only caught by reading the source — a
proposed catalog structure that duplicated what OCA already had, a filtering
approach declared impossible that was in fact trivial, a field believed absent
that existed. Every one would have become a bug.

If a claim about OCA behaviour matters to a decision, open the file and quote it.

### 2. Never edit `../odoo` or `../oca`

They are the live code base. An edit there changes what the instance runs,
which is exactly what Peter controls. Read only.

### 3. Never modify OCA or core modules in place

Every change is additive, through `_inherit` from our own modules. The entire
design is built on this constraint — it is what makes OCA upgrades survivable.

If a task seems to require editing an OCA module, stop and raise it. There is
almost always an additive route; the plan's §7.14 is a worked example of finding
one where an override looked unavoidable.

### 4. Claude plans and writes instructions; Peter executes

Follow the ground rules in `Odoo-Build/CLAUDE.md`. Claude does not create or edit files, run upgrades,
tests or git commands unless Peter explicitly asks for that specific action. When code is designed,
deliver it as file contents plus the exact commands to install/upgrade/test. Then wait for Peter's
results rather than assuming success.

### 5. When the plan and the code disagree

The **code** comes first. It decides what a field is called, what a method does,
what exists and what is possible. The plan records intent, but it is a draft:
its intent can also turn out wrong once the code is read.

Never silently follow the plan over the code, or quietly work around the plan.
Say the discrepancy out loud, then propose the fix: usually a correction to the
plan. When the discrepancy touches intent, the dependencies between modules, or a
§9 decision, Peter decides.

---

## Where things live

```
Odoo-Build/addons/         ← this repo; our modules live here (mounted at /mnt/extra-addons)
Odoo-Build/odoo/           ← running Odoo core (read-only reference)
Odoo-Build/oca/            ← running OCA repos (read-only reference)
```

---

## The modules

Full specification in the plan, §8. Phase 1 is the core chain; Phase 2 is
independent and can be built in any order.

**Phase 1**

| Module | Role |
|---|---|
| `qms_catalog` | Defect and object-part catalogs, catalog profiles, product assignment |
| `qms_nonconformity` | Nonconformity items, disposition, code filtering |
| `qms_determination` | Determination rules, applied-response lines, Suggest Response |
| `qms_quality_control` | Inspection-side defect capture and linkage |
| `qms_maintenance` | Maintenance-side linkage |
| `maintenance_mgmtsystem_action` | Action ↔ Maintenance Request relation (shared) |

**Phase 2** — depends only on core and OCA, contributable upstream

| Module | Role |
|---|---|
| `maintenance_request_sla` | Response/resolution durations, tracked priority |
| `maintenance_equipment_status_automation` | Equipment state from corrective requests |
| `maintenance_plan_action_template` | Plan-seeded action generation |

---

## Module docs

`docs/modules/<module>.md` is the technical specification of one module: folder tree,
manifest, models with every field and constraint, access rules, views, menus, and a
steps table that doubles as the progress log.

It contains **no commands and no instructions** — no install, upgrade, test or
troubleshooting steps — and no explanation of how things work. Reasoning belongs in
the plan; commands belong in the chat reply beside the doc. Written out, the doc
should be enough to rebuild the module's code.

One step per cycle: spec the step in the doc → inspect it, flag uncertainties → Claude
delivers the files, Peter installs and tests → both inspect the result → correct the
doc → next step. Before the code exists the doc leads; once a step passes, the doc is
corrected against the code that actually runs. A gap between the two is a bug in the doc.

---

## Odoo 18 conventions

Verify any of these against `../odoo` and `../oca` if a detail matters — this list is
a starting point, not an authority.

### Module skeleton

```
module_name/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── model_name.py
├── views/
│   └── model_name_views.xml
├── security/
│   └── ir.model.access.csv
├── data/
└── readme/               ← OCA-style fragments: DESCRIPTION.md, USAGE.md, etc.
```

### Manifest

```python
{
    "name": "Module Title",
    "version": "18.0.1.0.0",        # OCA format: <odoo>.<major>.<minor>.<patch>
    "license": "AGPL-3",
    "category": "...",
    "depends": [...],
    "data": [
        "security/ir.model.access.csv",
        "views/...xml",
    ],
    "installable": True,
}
```

### Version-specific gotchas

These changed in Odoo 17 and catch code written against older versions:

- **`<tree>` is now `<list>`** in view XML.
- **`attrs` and `states` are gone.** Conditional display is a direct attribute
  holding a Python expression: `invisible="state == 'draft'"`,
  `readonly="not can_edit_priority"`, `required="nc_type == 'supplier'"`.
- Computed fields need `@api.depends`; the method is `_compute_<field_name>`.
- A stored computed field needs `store=True` explicitly.

### Security

**Every new model needs an `ir.model.access.csv` entry** or it is inaccessible,
including to admin. This is the most common cause of a module that installs
cleanly and then appears broken.

### Naming

- Custom models are prefixed `qms.` — e.g. `qms.defect.code`.
- Fields added to OCA or core models are prefixed `qms_` to avoid collision with
  future upstream fields. Exception: fields the plan names explicitly without the
  prefix, such as the link fields in §7.10.
- Modules use `qms_` when they belong to this system, or OCA's
  `<base_module>_<feature>` form when generic enough to contribute upstream.

---

## Working style

**Ask rather than assume** when a choice would change the architecture, add a
dependency between modules, or alter anything recorded in §9 of the plan.

**Decide alone** on ordinary implementation: method names, file organisation,
view layout, helper structure.

**Prefer** reusing an OCA model over defining a new one; adding a field over
overriding a method; suggesting over enforcing. This is the plan's governing
constraint — maintenance cost, not feature count, is the thing being optimised.

**When something doesn't work**, report what actually happened rather than
describing what should have. Real behaviour comes from the instance's logs and
test output, and from Peter. Treat those as authoritative and do not paper over a
failure with a plausible explanation.
