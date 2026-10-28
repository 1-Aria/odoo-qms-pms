# CLAUDE.md

Working context for the custom Odoo modules in this repo: the QMS/PMS suite, the IE-MES suite and
the VN e-invoice modules.

---

## What this is

Custom Odoo 18.0 CE modules, built on top of OCA modules, in two suites, plus the Vietnamese
e-invoice modules:

- **QMS/PMS**, a unified Quality Management and Plant Maintenance pipeline.
  **Its architecture lives in `docs/QMS-PMS/Odoo-QMS-PMS-Development-Plan.md`.** Read it before
  starting work on any of its modules. It describes the intended models, fields, relationships
  and delivery phases, and §9 records the design decisions with their rationale and
  the alternatives that were rejected.
- **IE-MES**, Industrial Engineering for garment sewing lines (standards, time accounting,
  skill and incentive metrics), with shop-floor capture (MES). Its documents are in
  `docs/IE-MES/`; see *The IE-MES suite* below.
- **VN e-invoices**, Vietnamese e-invoices read from their XML and checked against the tax
  portal's list. Its documents are in `docs/Accounting/`; see *The VN e-invoice modules* below.

**The design documents are a work in progress, not a specification to follow.** They were
written without inspecting the Odoo and OCA source, and they contain errors. Examples found
so far: the QMS plan's §7.6 filter traversed a `product.category.product_tmpl_ids` field that
does not exist, the plan's claim that category scoping matched `quality_control_oca`
was wrong because QC also walks up parent categories, and the `qms_catalog`
dependencies did not fit how the module is meant to be used. Treat every field
name, method, dependency and claim about OCA behaviour in a design document as unverified
until checked against the code. The technical reality in the code comes first.

This file says how to *work* here. The design documents say *what* to build and *why*.
Neither duplicates the other. If something architectural is missing, it belongs
in those documents, not here.

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
tests or git commands unless Peter explicitly asks for that specific action. When Peter asks for a
step's code or a document, Claude writes those files in place (`addons/<module>/`, `docs/`) and gives
the exact commands to install/upgrade/test. Then wait for Peter's results rather than assuming success.

### 5. When a design document and the code disagree

The **code** comes first. It decides what a field is called, what a method does,
what exists and what is possible. A design document records intent, but it is a draft:
its intent can also turn out wrong once the code is read.

Never silently follow a design document over the code, or quietly work around it.
Say the discrepancy out loud, then propose the fix: usually a correction to the
document. When the discrepancy touches intent, the dependencies between modules, or a
recorded decision (the QMS plan's §9; the IE documents' DEC, FG and TD tables), Peter decides.

---

## Where things live

```
Odoo-Build/addons/         ← this repo; our modules live here (mounted at /mnt/extra-addons)
Odoo-Build/addons/docs/    ← QMS-PMS/, IE-MES/ and Accounting/ design documents; modules/ holds the per-module specs
Odoo-Build/odoo/           ← running Odoo core (read-only reference)
Odoo-Build/oca/            ← running OCA repos (read-only reference)
Odoo-Build/ie-prototype/   ← the IE step 5 prototype harness, outside the repo on purpose
```

---

## The QMS/PMS modules

Full specification in the plan, §8. Phase 1 is the core chain; Phase 2 is
independent and can be built in any order; Phase 3 extends the quality side.

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
| `maintenance_priority_matrix` | Criticality, urgency and priority rules |
| `maintenance_sla` | SLA rules, SLA records, stage-driven clocks, live state, reporting |
| `maintenance_equipment_status_automation` | Equipment state from corrective requests |
| `maintenance_plan_action_template` | Plan-seeded action generation |

The first two replace the plan's `maintenance_request_sla`; their design lives in
`docs/QMS-PMS/Maintenance SLA Engine — Technical Design.md`, which the plan's §7.12 points to.
`maintenance_equipment_status_automation` comes after them, because the SLA design changes
which stages a corrective request passes through and that module keys on the stages.

**Phase 3** — quality enhancements, on `qms_quality_control`

| Module | Role |
|---|---|
| `qms_fabric_inspection` | Roll-level fabric inspection at receipt: rolls as rows of the receipt line's inspection, 4-point scoring, shade, dye lot and band on the lot |
| `qms_quality_report` | Inspection and Defect Analysis — DHU, defective %, FTR, the defect Pareto — and the fabric section |

Their designs are `docs/QMS-PMS/Fabric Inspection — Design.md` and
`docs/QMS-PMS/QMS Quality Reporting — Design.md`. The report's capture fields live in
`qms_quality_control` (its step 7). `zalo_oa` (`docs/QMS-PMS/Zalo ↔ Odoo Integration Design Note.md`)
is a supporting integration outside the phases.

**Supporting modules outside the phases**

| Module | Role |
|---|---|
| `qms_nonconformity_hr` | Fills a nonconformity's department from the reporting user's employee; auto-installs with `mgmtsystem_nonconformity_hr` |
| `maintenance_security_user_menu` | Restores core's maintenance menu visibility for internal users, which `maintenance_security` narrows |
| `maintenance_sla_garment` | A starting SLA configuration for a garment plant: stage flow, targets, priority grid |
| `zalo_oa_garment` | Zalo notification templates and rules for garment maintenance and quality, in Vietnamese |

---

## The IE-MES suite

Industrial Engineering for garment sewing lines: SAM standards from timeSSD, time accounting,
earned minutes, defects, the skill matrix and the incentive metrics that payroll pulls. MES is the
shop-floor capture interface, designed in its own phase. Claude decides the implementation, business
and technical, with Peter's confirmation.

**Documents** (`docs/IE-MES/`). Each is a versioned file, and older versions stay as history;
read the latest.

| Document | Role |
|---|---|
| `IE_Business_Logic_Spec_v*.md` | The business rules of record (DEC, OPEN, FLAG-TECH) |
| `IE_Framework_Rationale_v*.md` | The reasoning, with worked numbers |
| `IE_Module_Function_Map.md` | The v1 scope, and the workflow for changing the business documents |
| `IE_Acceptance_Test_Cases_v*.md`, `ie_reference_calc.py` | Expected results. The implementation is correct when it reproduces them. |
| `IE_Roadmap_to_Development.md` | The steps before development |
| `IE_Fit_Gap_v*.md` | Fit-gap against CE 18 and the step 5 prototype (FG decisions) |
| `IE_Technical_Design_v*.md` | Models, fields and rules per module (TD decisions), written in chunks. Its chunk table says where the design stands. |
| `IE_Design_Note_*.md` | One design question worked out before it is folded into the technical design |

- The business documents (spec, rationale, function map, test cases) change only through the
  function map's workflow. The fit-gap and the technical design list their proposed changes, which are
  applied in batches once Peter confirms. Until then, a technical design that departs from the spec
  says so.
- Planned modules, in build order for shadow mode: `mes_capture` (credited worker, scan journal, scan
  rules), `ie_base` (master data, SAM versions, periods, production records), `ie_time` (off-standard
  grants, time accounting, exceptions), `ie_quality` (defects, repair), `ie_skill`. Then `ie_line`,
  `ie_incentive`, `ie_valuation`, `ie_realtime`. The technical design's §1 holds the current map.

---

## The VN e-invoice modules

Vietnamese e-invoices as records in Odoo, and their reconciliation with the tax authority's portal.
Outside the QMS-PMS and IE-MES suites.

| Module | Role | Design |
|---|---|---|
| `l10n_vn_einvoice` | The e-invoice record (one per legal invoice per company) read from its XML; attaching an XML to a bill or invoice; draft vendor bills from XML; VAT codes mapped to taxes | `docs/Accounting/VN E-Invoice — Design.md` |
| `l10n_vn_einvoice_reconcile` | The portal's Excel lists imported through `excel_import_export`, grouped per invoice and matched to e-invoices | `docs/Accounting/VN E-Invoice Reconciliation — Design.md` |

- The XML format reference is `docs/Accounting/vn_einvoice_field_dictionary.json` (Peter's, from
  QĐ 1233/QĐ-CT, also in that folder). The design documents decide what Odoo stores and names.
- Sample XML invoices and recreated portal lists are in `docs/Accounting/samples/`. Lookup codes
  (*Mã số bí mật*, *Số bảo mật*) are replaced by `REDACTED`; do the same with any new sample before it
  is committed.
- `l10n_vn_edi_viettel` (core, installed) issues sales invoices through Viettel SInvoice. A bridge to it
  is planned, not built.

---

## Module docs

`docs/modules/<module>.md` is the technical specification of one module: folder tree,
manifest, models with every field and constraint, access rules, views, menus, and a
steps table that doubles as the progress log.

It contains **no commands and no instructions** — no install, upgrade, test or
troubleshooting steps — and no explanation of how things work. Reasoning belongs in
the design documents; commands belong in the chat reply beside the doc. Written out, the doc
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

### Tests that create core records

**A test whose fixtures create a record of a core model other modules extend —
`product.template`, `product.product`, `res.partner`, `res.users` — must be
`@tagged("post_install", "-at_install")`.**

`at_install` tests run the moment their own module loads, while modules further down
the graph are still unloaded. Columns those modules added are NOT NULL in the database
but absent from the registry, so no default applies and the INSERT fails. Seen twice:
`res_partner.autopost_bills` (from `account`) and `product_template.sale_line_warn`
(from `sale`). OCA documents the same trap in
`maintenance_plan/tests/common.py:10-14`.

Everything else stays `at_install`, where a test runs closest to the change it guards.

### Security

**Every new model needs an `ir.model.access.csv` entry** or it is inaccessible,
including to admin. This is the most common cause of a module that installs
cleanly and then appears broken.

### Naming

- Custom models are prefixed `qms.` — e.g. `qms.defect.code`.
- Fields added to OCA or core models are prefixed `qms_` when they are declared by a
  `qms_*` module, so they cannot collide with a future upstream field. Modules named in
  OCA's `<base_module>_<feature>` form and intended for contribution use unprefixed
  names, since the prefix would carry this system's name upstream —
  `mgmtsystem.action.maintenance_request_id` in `maintenance_mgmtsystem_action` is
  unprefixed for that reason, while `mgmtsystem.nonconformity.qms_maintenance_request_id`
  is not. This supersedes the plan's earlier exemption for the link fields §7.10 names
  without a prefix.
- Modules use `qms_` when they belong to this system, or OCA's
  `<base_module>_<feature>` form when generic enough to contribute upstream.
- The IE-MES suite uses `ie_` / `ie.` for IE modules, models and fields added to core or OCA models,
  and `mes_` / `mes.` for MES. The capture layer both share is `mes_capture` (technical design TD-01).
- The VN e-invoice modules follow core's localisation conventions: modules `l10n_vn_<feature>`; models
  `l10n_vn.<name>`, like core's `l10n_ke.item.code` or `l10n_latam.document.type`; and the `l10n_vn_`
  prefix on fields added to core or OCA models, as `l10n_vn_edi_viettel` does.

---

## Lessons from building

Each was found by running code, not by reading it. Details and source references are in
the module doc named.

**Tests**
- Tests creating core records are `post_install` — see *Tests that create core records* above.
- Test methods inherited from a shared base class are collected only with
  `allow_inherited_tests_method = True`; without it the run passes with zero tests. Check
  the test count, never just `exit=0`. (`qms_catalog`)
- Build fixture codes from `unique_code_prefix()` — `ref_code` is unique per table and the
  instance holds real data. (`qms_catalog`)
- Asserting on tracking takes two `self.env.cr.precommit.run()` calls: `create()` discards
  tracking for the rest of the transaction, and messages post only at commit. (`qms_nonconformity`)
- A dependency or constraint trigger that no test exercises is decoration. Write the test
  that changes that field on an existing record. (`qms_catalog`, `qms_nonconformity`, `qms_determination`)
- An access test needs a positive control — the same user succeeding at an ordinary write —
  or it passes for the wrong reason. (`qms_catalog`, dropped step 6)
- Tests and UI checks run as admin hide access bugs: the inspection's Nonconformities button had
  failed for every non-administrator since the OCA bridge was installed, and only a UI check as a
  role-matrix user found it. Check the UI as the users who will use it, and give each access path
  a test as such a user. (`qms_quality_control`, step 6)
- In a `TransactionCase`, start `patch.dict` per test — `self.startPatcher` in `setUp`, or a `with`
  block — never with `startClassPatcher`: after every test Odoo reads `.target` from each active
  patch, which `patch.dict` lacks, and every test errors (`odoo/odoo/tests/common.py:1117-1122`).
  (`zalo_oa`, step 1)
- A test that creates a `base.automation` must call `self.env["base.automation"]._unregister_hook()`
  in `tearDown`: the rule patches `create`, `write` and `_compute_field_value` onto the model class,
  the rollback does not undo it, and Odoo's after-test attribute check fails every later test
  (`base_automation/tests/test_automation.py:12-14`). (`zalo_oa`, step 3)
- No `HttpCase` or tour can run on this image. Before a post-install suite that holds an `HttpCase`,
  Odoo pregenerates every asset bundle (`odoo/odoo/service/server.py:1437-1440`), and the image's build
  deletes every subfolder of each `tests/` folder (`images/odoo/Dockerfile:49`), so core's test bundles
  name missing files and the whole post-install run aborts. The at-install tests have passed by then, so
  their count alone looks green: check the post-install count too. Core runs from the image's
  `/opt/odoo`, so `../odoo` still holds the deleted files. Put route logic in a model method tested by a
  `TransactionCase`, keep the route thin, and check its HTTP wiring with `curl`. (`zalo_oa`, step 4)
- Never import from a core module's `tests` package (`odoo.addons.account.tests.common` and its
  `AccountTestInvoicingCommon`, and the like). On this image that package's `__init__` reaches
  `mail/tests/__init__.py`, which imports its `discuss` subfolder, deleted by the same build step, and the
  whole `-i`/`-u` run fails before any test (`No module named 'odoo.addons.mail.tests.discuss'`). Build
  fixtures on `TransactionCase`: create a company, link it to the test user, load its chart with
  `account.chart.template.try_loading`. The failed run still commits the module's tables, menus and
  views while its state stays *uninstalled*; running `-i` again completes it. (`l10n_vn_einvoice`, step 1)

**Scripts**
- Scripts run through `odoo shell`, such as the IE prototype harness, live outside `addons/`:
  auto-reload watches every `.py` under the addons path, so a script there restarts the server.
  (`ie-prototype`)

**ORM**
- `@api.constrains` runs only when its fields are in the create/write values, so it cannot
  catch an absent value; use a SQL CHECK. (`qms_determination`)
- A non-stored recursive compute must read through the same path its `@api.depends` names:
  invalidation cascades only through cached records. (`qms_catalog`, step 5)
- An editable stored compute keeps a record's value when the method does not assign it.
  (`qms_nonconformity`)
- Read ancestors from `parent_path`, not a `parent_of` search, which drops archived
  records. (`qms_determination`)
- `related_sudo=False` applies the user's record rules; a model ACL still raises, so gate
  the column with `groups`. (`qms_determination`)
- Anything reaching `hr` fields (`employee_id`) needs `hr` declared — put it in a bridge
  module. (`qms_nonconformity_hr`)
- A field left out of `create()` is cached as its empty value (`0.0` for a Float) while its
  column stays NULL, and a write equal to the cached value is skipped: writing `0` over a NULL
  in the transaction that created the record can silently do nothing. A fetch in a later
  transaction caches NULL as `None`, so the bug hides outside it. Invalidate the field first,
  and assert stored values through SQL, not the ORM. (`maintenance_sla`)
- A stored compute does not run when its dependency is written: it is marked pending and runs
  at the next read or flush, reading its sources as they are then. A snapshot that copies a
  source it does not depend on therefore copies that source's value at the first read, not at
  the write — so a test that edits the source before reading the snapshot sees the edit copied.
  Read the field before changing the source. (`qms_fabric_inspection`)
- Odoo 18 lets only *Settings* read `ir.actions.act_window` records, so `env.ref(action).read()`
  raises for everyone else — some OCA 18 ports still do it. Read an action with
  `self.env["ir.actions.act_window"]._for_xml_id(xmlid)`, which reads it as superuser.
  (`qms_quality_control`, step 6)

**Views**
- View inheritance may not select on a translated attribute such as `@string`; select
  positionally. (`qms_nonconformity`)
- A button's `confirm=` is fixed text; report anything dynamic after the click with a
  `display_notification`. (`qms_determination`)
- A field `domain` may be a bare field name or a domain expression, not an attribute access:
  `domain="parent.x"` fails view validation on install. Write `domain="parent.x or []"`.
  (`qms_fabric_inspection`, step 1)

---

## Working style

**Ask rather than assume** when a choice would change the architecture, add a
dependency between modules, or alter a recorded decision (the QMS plan's §9; the IE
documents' DEC, FG and TD tables).

**Decide alone** on ordinary implementation: method names, file organisation,
view layout, helper structure.

**Prefer** reusing an OCA model over defining a new one; adding a field over
overriding a method; suggesting over enforcing. This is the governing constraint of
both suites — maintenance cost, not feature count, is the thing being optimised.

**When something doesn't work**, report what actually happened rather than
describing what should have. Real behaviour comes from the instance's logs and
test output, and from Peter. Treat those as authoritative and do not paper over a
failure with a plausible explanation.
