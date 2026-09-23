# Odoo QMS / PMS Development Plan

**Target platform:** Odoo 18.0 Community Edition
**Revision:** 2 (supersedes `Odoo-Custom-Module-Development-Plan.md`)

---

## 1. Premise

Build a unified Quality Management and Plant Maintenance system in Odoo 18 CE
that replicates the *functional architecture* of SAP QM/PM — a shared coded
vocabulary, a unified incident record, and divergent execution engines — using
OCA modules for the heavy lifting and a small, non-invasive custom layer on top.

The guiding constraint is **maintenance cost**. Every custom line written here
must be carried forward across OCA upgrades. The design therefore prefers:

- reusing an OCA model over defining a new one
- adding a field over overriding a method
- suggesting over enforcing
- leaving the primary transactions (Inspection, Maintenance Request) untouched

Where a more faithful SAP replication would cost significantly more to maintain,
the cheaper approximation wins.

---

## 2. Objective

A single problem-resolution pipeline serving both domains:

> **Event** (something went wrong) → **Notification** (structured record and
> analysis) → **Response** (actions, documents, disposition) → **Closure**

with a shared catalog vocabulary so that quality defects and equipment damage
are analysed, coded, and reported through one consistent structure.

---

## 3. Scope and Non-Goals

### In scope

| Area | Delivered by |
|---|---|
| Coded defect / damage vocabulary | New: `qms_catalog` |
| Coded object part / defect location vocabulary | New: `qms_catalog` |
| Per-product scoping of the vocabulary | New: `qms_catalog` |
| Multi-line nonconformity analysis (defect × part × cause) | New: `qms_nonconformity` |
| Response determination from analysis | New: `qms_determination` |
| Quality inspection ↔ nonconformity linkage | New: `qms_quality_control` |
| Maintenance request ↔ nonconformity linkage | New: `qms_maintenance` |
| Preventive maintenance engine | OCA `maintenance_plan` |
| Corrective/preventive action tracking | OCA `mgmtsystem_action` |
| Action effectiveness verification | OCA `mgmtsystem_action_efficacy` |
| Procedures and work instructions | OCA `document_page_*` |

### Explicit non-goals

| Not doing | Reason |
|---|---|
| **8D certification compliance** | 8D is an automotive reporting discipline. Unless a customer demands an 8D form as a deliverable, formal compliance buys nothing. The data model below happens to cover the eight disciplines (see Appendix C), so an 8D report remains a QWeb template away — but the system is not described as "8D-compliant". |
| **Functional location hierarchy** | SAP's IFLOT has no Odoo equivalent. `maintenance_equipment_hierarchy` models equipment-to-equipment parentage, which would force components like a feed dog to become tracked Equipment records. Object Part codes serve the same descriptive purpose at a fraction of the cost. |
| **Usage Decision on the Inspection** | `qc.inspection.state` is a `Selection`, not a stage model. Adding disposition states means extending a core selection that the module's own workflow methods branch on. Disposition lives on the Nonconformity instead. |
| **Inventory movements from disposition** | Deferred. The disposition field is structured so stock actions can be attached later without redesign. |
| **Gating primary transactions on the Nonconformity** | Rejected on principle — see Decision D11. |
| **Sampling plans / AQL** | Out of scope entirely. |

### The Equipment vs. Object Part rule

> If it has its own maintenance history, it is **Equipment**.
> If it only ever appears as a location in a description, it is an **Object Part**.

---

## 4. Reference Architecture

SAP QM and PM share one architecture. Four functional layers, described here
conceptually — **this document does not attempt to replicate SAP table
structures, and SAP table names are deliberately omitted**. What is replicated
is the separation of concerns.

| Layer | Purpose | Our implementation |
|---|---|---|
| **Coded vocabulary** | A controlled, hierarchical set of codes for defects, damage, object parts and causes — shared by both domains so analytics are comparable | `qms.defect.code`, `qms.object.part`, OCA `mgmtsystem.nonconformity.cause` |
| **Contextual scoping** | A per-object restriction narrowing the global vocabulary to what is relevant for this material or machine | `qms.catalog.profile` |
| **Unified intake** | One record type logging every event from either domain, carrying the analysis and the response | OCA `mgmtsystem.nonconformity` |
| **Divergent execution** | Domain-specific engines doing the actual work | `maintenance.request` (PM), `qc.inspection` (QM) |

The load-bearing idea, and the one worth preserving: **the record of the event
is decoupled from the labour of execution.** The Nonconformity is where an issue
is understood and dispositioned; the Maintenance Request and Inspection are
where work happens. Neither blocks the other.

---

## 5. Base Stack

All modules below verified present on the **18.0** branch unless noted.

### Odoo 18.0 CE core

`maintenance`, `product`, `stock`, `mrp`

### OCA/maintenance

| Module | Role |
|---|---|
| `maintenance_plan` | Preventive maintenance engine — plans, schedules, auto-generated requests |
| `maintenance_plan_only` | Restricts generation to planned requests |
| `maintenance_product` | **Load-bearing.** Unifies Equipment with Product — equipment takes its name, category, cost and supplier from a `product_id`. This unification is what lets one catalog profile serve both domains. |
| `maintenance_equipment_status` | Equipment operational state |
| `maintenance_location` | Flat equipment location |
| `maintenance_equipment_contract` | Warranty / service contracts |
| `maintenance_partner` | Equipment vendor linkage |
| `maintenance_request_purchase`, `maintenance_stock` | Spare-part procurement |
| `maintenance_equipment_sequence`, `maintenance_request_sequence` | Reference numbering |

### OCA/manufacture

| Module | Role |
|---|---|
| `quality_control_oca` | **Primary QM transaction.** `qc.test` (checklist), `qc.test.question`, `qc.test.question.value` (possible answers with an `ok` flag), `qc.inspection` |
| `quality_control_stock_oca` | Inspection triggers on stock pickings and lots |
| `quality_control_mrp_oca` | Post-production inspection checkpoints |

### OCA/management-system

| Module | Role |
|---|---|
| `mgmtsystem` | Framework base. Provides `mgmtsystem.system` |
| `mgmtsystem_nonconformity` | **Primary intake record.** Also defines `mgmtsystem.nonconformity.cause`, `.origin` (both hierarchical), `.severity` (flat), `.stage` |
| `mgmtsystem_nonconformity_type` | Nonconformity classification |
| `mgmtsystem_nonconformity_product` | **Load-bearing.** Adds `product_id` → `product.product`. This is the anchor for catalog profile resolution. |
| `mgmtsystem_nonconformity_maintenance_equipment` | Adds `equipment_id` |
| `mgmtsystem_nonconformity_mrp` | Adds workcenter linkage |
| `mgmtsystem_nonconformity_quality_control_oca` | Adds inspection linkage. **Not merged to the 18.0 branch**, but the port exists and is verified installing and functioning — see O1. Treated as a working dependency, not a risk |
| `mgmtsystem_action` | Action records. Carries `type_action`: `immediate` / `correction` / `prevention` / `improvement` |
| `mgmtsystem_action_template` | Reusable action definitions |
| `mgmtsystem_action_efficacy` | Effectiveness verification |
| `mgmtsystem_partner` | Partner linkage on the nonconformity |
| `document_page_mgmtsystem`, `document_page_procedure`, `document_page_work_instruction` | Procedures and work instructions |

---

## 6. Gap Analysis

The three OCA stacks were never designed to operate together. `mgmtsystem` in
particular originates as a compliance toolkit, not an incident pipeline. Four
gaps must be closed:

1. **No coded vocabulary for defects or object parts.** OCA provides Cause,
   Origin and Severity, but nothing describing *what is wrong* or *where*.

2. **No contextual scoping.** Nothing restricts which codes are offered for a
   given product or machine. At ~100 codes this becomes unusable.

3. **The nonconformity is header-level.** One cause set, one action plan. A real
   garment nonconformity is *three defects on one lot*, each on a different
   panel, each with its own cause.

4. **No path from analysis to response.** Nothing connects "torn sleeve caused by
   machine fault" to "the action for that is Rework plus raise a maintenance
   request."

---

## 7. Target Architecture

### 7.1 Catalog layer

Two new catalogs, each a **self-referencing tree**. A record with an empty
`parent_id` is a **code group**; its children are **codes**. This is the same
shape OCA already uses for `mgmtsystem.nonconformity.cause`.

Both inherit one abstract mixin so the pattern is written once.

```
qms.catalog.mixin  (AbstractModel)
  ├── qms.defect.code
  └── qms.object.part
```

**`qms.catalog.mixin`**

| Field | Type | Notes |
|---|---|---|
| `name` | Char | required, translatable |
| `ref_code` | Char | the short code — e.g. `FAB-01` |
| `sequence` | Integer | display ordering |
| `parent_id` | Many2one (self) | empty ⇒ this record is a code group |
| `child_ids` | One2many (self) | |
| `parent_path` | Char | indexed; `_parent_store = True` |
| `active` | Boolean | default True |
| `domain_kind` | Selection | `qm` / `pm` / `both`, default `both`; see D14 |
| `display_name` | Char | computed, renders `Group / Code` |

`_order = "parent_id, sequence"`

**`qms.defect.code` gains one field beyond the mixin:**

| Field | Type | Notes |
|---|---|---|
| `default_severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | baseline severity for this defect — tier 1 of the severity resolution in §7.3 |

⚠ **This field is declared in `qms_nonconformity`, not `qms_catalog`.**
`mgmtsystem.nonconformity.severity` belongs to `mgmtsystem_nonconformity`, and
`qms_catalog` depends only on `product` and the `mgmtsystem` base (see D24), not
on the nonconformity module. The catalog module defines the model; the
nonconformity module extends it with the severity default.

`qms.object.part` carries no severity: a location is not more or less serious on
its own.

**Example — `qms.defect.code`**

| id | name | ref_code | parent_id | domain_kind |
|---|---|---|---|---|
| 1 | Fabric Defect | FAB | *(empty)* | qm |
| 2 | Torn | FAB-01 | 1 | qm |
| 3 | Scratch | FAB-02 | 1 | qm |
| 4 | Blemish | FAB-03 | 1 | qm |
| 5 | Seam Defect | SEAM | *(empty)* | qm |
| 6 | Broken stitch | SEAM-01 | 5 | qm |
| 7 | Mechanical | MECH | *(empty)* | pm |
| 8 | Bearing failure | MECH-01 | 7 | pm |

**Example — `qms.object.part`**

| id | name | ref_code | parent_id | domain_kind |
|---|---|---|---|---|
| 1 | Shirt Construction | SHIRT | *(empty)* | qm |
| 2 | Front Half | SH-01 | 1 | qm |
| 3 | Back Half | SH-02 | 1 | qm |
| 4 | Sleeves | SH-03 | 1 | qm |
| 5 | Machine Assemblies | MACH | *(empty)* | pm |
| 6 | Needle bar | MA-01 | 5 | pm |

**Cause, Origin, Severity are reused unchanged from OCA.** Cause and Origin are
already hierarchical with `ref_code`; Severity is correctly flat, being a scale
rather than a vocabulary.

### 7.2 Scoping layer

**`qms.catalog.profile`** — a flat record bundling **code groups** across
catalogs. Never nested, never references individual codes.

| Field | Type | Notes |
|---|---|---|
| `name` | Char | required |
| `domain_kind` | Selection | `qm` / `pm` / `both` |
| `defect_group_ids` | Many2many → `qms.defect.code` | `domain=[('parent_id','=',False)]` |
| `object_part_group_ids` | Many2many → `qms.object.part` | `domain=[('parent_id','=',False)]` |
| `product_ids` | Many2many → `product.product` | inverse |
| `product_tmpl_ids` | Many2many → `product.template` | inverse |
| `categ_ids` | Many2many → `product.category` | inverse |

The `domain` on the group fields is what enforces *groups only* — only
parent-less records are selectable. There is no separate group model.

**Example**

| id | name | domain_kind |
|---|---|---|
| 1 | Shirt | qm |
| 2 | Sewing Machine | pm |

*`qms_profile_defect_group_rel`*

| profile_id | defect_code_id |
|---|---|
| 1 | 1 *(Fabric Defect)* |
| 1 | 5 *(Seam Defect)* |
| 2 | 7 *(Mechanical)* |

**Assignment** — three plain Many2many fields, no line models:

```
product.product.qms_profile_ids    → qms.catalog.profile
product.template.qms_profile_ids   → qms.catalog.profile
product.category.qms_profile_ids   → qms.catalog.profile
```

Assignment is **additive across all three levels** — profiles *widen* the
available vocabulary, they do not override. Template allows SEAM + FABRIC,
variant adds DYE, result is all three. This matches the additive semantics
`quality_control_oca` already uses for Test assignment, so users learn one rule.

**Category assignment includes parent categories**, as in `quality_control_oca`.
A profile on *All / Garments* applies to products in *All / Garments / Shirts*.
QC resolves categories the same way, walking up from the product's category
(`qc_trigger_product_category_line.py`):

```python
category = product.categ_id
while category:
    ...
    category = category.parent_id
```

**Access and menus** (D24, D25): catalog and profile menus sit under
*Management System → Configuration*. All internal users can read catalogs and
profiles, since product forms display the assignment. Only
`mgmtsystem.group_mgmtsystem_manager` can create, edit or delete them, which is
also the group that sees the *Configuration* menu.

**Resolution.** `qms_catalog` exposes the result as `qms_effective_profile_ids`, a
computed, non-stored Many2many on `product.category` (own profiles plus every
ancestor's), `product.template` (own plus its category's) and `product.product`
(own plus its template's). This is the single place the additive rule is expressed.

**Equipment needs no assignment of its own.** `maintenance_product` gives
`maintenance.equipment.product_id`, so equipment resolves its profile through its
product. One resolution path serves both domains.

### 7.3 Determination layer

**Superseded by `docs/qms_determination_plan_revised.md`**, §3–§5, which the module implements.
In short: a rule has conditions (defect code, object part, cause — at least one) and
outputs (suggested severity, action templates, documents); **every** matching rule applies
(D26), so there is no specificity ranking; and a rule's severity is shown as a suggestion,
never written to the item.

### 7.4 Nonconformity items

**`qms.nonconformity.item`** — the analysis grain. One nonconformity, many items.

| Field | Type | Notes |
|---|---|---|
| `nonconformity_id` | Many2one → `mgmtsystem.nonconformity` | ondelete cascade |
| `sequence` | Integer | |
| `defect_code_id` | Many2one → `qms.defect.code` | domain-filtered by profile |
| `object_part_id` | Many2one → `qms.object.part` | domain-filtered by profile |
| `cause_id` | Many2one → `mgmtsystem.nonconformity.cause` | |
| `severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | **defaulted, not solicited** — see below |
| `qty_affected` | Float | |
| `note` | Char | |

This replaces the single header-level cause field as the locus of analysis. The
header's `cause_ids` remains for compatibility and rolls up from the items.

`severity_id` is populated by onchange from `defect_code_id.default_severity_id`,
then refined by the determination engine, then editable by hand. It stores the
severity that was *actually applied*, so later edits to the catalog or the rules
do not rewrite it.

### 7.5 Applied responses

**Superseded by `docs/qms_determination_plan_revised.md`**, §6–§7. A response line points at a rule
and, when suggested, the item that fired it; there is no `source` field, and a rerun of
Suggest Response replaces every line (D30).

### 7.6 Code filtering

The item's defect and object-part fields carry a **static search domain** that
reads the product's resolved profiles:

```python
[('parent_id.profile_ids', 'in', parent.qms_effective_profile_ids)]
```

`qms_catalog` computes those profiles as `qms_effective_profile_ids` on
`product.product` — its own profiles, its template's, and its category's
including every ancestor category (§7.2). The nonconformity exposes the
product's set as a related field of the same name (§7.9), and the domain matches
any code whose group belongs to one of them.

This requires `profile_ids` as the inverse Many2many on the catalog models —
free, being the other end of an existing relation.

The additive rule of D6 lives in the computation, not here, so it is stated once
and tested in `qms_catalog`. Core uses the same shape of domain — an x2many read
from the parent record — at
`odoo/addons/point_of_sale/views/pos_order_view.xml:157`, against the non-stored
field at `pos_order.py:353`.

**Fallback behaviour is by design:** if a product resolves to no profile, the
dropdown is empty and the user removes the condition from the search panel to
see the full catalog. Using the standard search filter rather than a computed
field means the restriction is always visible and always escapable, which is the
unintrusive principle applied literally.

**Known constraint:** `parent_id.` is exactly one hop, so the catalog trees must
stay **two levels deep** (group → code). `qms_catalog` enforces that with
`_check_catalog_depth`.

### 7.7 Actions

**No new model and no new field.** Two independent axes already exist:

| Axis | Question answered | Existing mechanism |
|---|---|---|
| Kind of response | containment / corrective / preventive / improvement | `mgmtsystem.action.type_action` |
| Planned vs. performed | needs doing / was done | `stage_id` + `date_closed` |

Work performed but never planned is recorded as an action created and closed in
one step, `type_action = immediate`. `mgmtsystem.nonconformity.immediate_action_id`
is the purpose-built fast path for the single containment action.

### 7.8 Workflow

*The Analysis and Action Plan steps below are superseded by `docs/qms_determination_plan_revised.md`,
§7: Suggest Response no longer refines item severity, and Generate Actions is added as an
optional shortcut in the Action Plan phase.*

**Analysis phase**

1. User enters items — defect, object part, cause — with dropdowns scoped by the
   product's catalog profile. Severity defaults in from each defect code.
2. User presses **Suggest Response**. The determination engine matches each item
   and writes `qms.nonconformity.response` lines, and refines item severity where
   a matching rule carries one.
3. User may add, remove or adjust response lines by hand.

Response lines are **written by the button**, not by a `compute=` field. They
change only on explicit user action. Re-running the button within Analysis is
expected and fine; doing so after the stage has advanced requires reverting the
stage, which is logged.

**Action Plan phase**

4. User creates real `mgmtsystem.action` records, optionally from the action
   templates listed on the response lines, setting `type_action` on each.

The gap between the *response lines* and the *registered actions* is the audit
signal: what the system indicated versus what the organisation did.

**Closure**

5. User sets `disposition` on the nonconformity and closes it.

No gate between the primary transactions and the nonconformity — see D11.

### 7.9 Nonconformity header additions

| Field | Type | Notes |
|---|---|---|
| `item_ids` | One2many → `qms.nonconformity.item` | the analysis |
| `response_ids` | One2many → `qms.nonconformity.response` | what was indicated |
| `disposition` | Selection | `accept` / `accept_rework` / `scrap` / `return_supplier` / `reinspect` |
| `partner_id` | Many2one | **override to `required=False`** |
| `qms_effective_profile_ids` | Many2many → `qms.catalog.profile` | related `product_id.qms_effective_profile_ids`, readonly; feeds the §7.6 domain |

The existing **Procedures** tab (`procedure_ids` → `document.page`) is **left
untouched**. It holds documents a human attached; rule-derived documents live on
the response lines. Merging the two would permanently destroy the ability to
tell "someone judged this relevant" from "a rule fired" — and keeping them
separate costs nothing.

### 7.10 Linkage and prefill

The smart button is the primary connection between every element of the
pipeline. It is what lets the Nonconformity do the heavy lifting while the
Inspection and Maintenance Request stay essentially untouched: no automation
fires on the primary transactions, and the user moves between them by clicking.

**Mechanics.** A smart button is only a view element — a button in the button box
opening a window action. It carries no relationship semantics of its own. Two-way
visibility therefore means **one relation plus two buttons**: a Many2one on one
model gives the other an inverse One2many for free, and each side gets its own
button counting the other. The relation is stored once, never twice.

**Link inventory.**

| Connection | Relation | Status |
|---|---|---|
| NC ↔ Inspection | field on NC from `mgmtsystem_nonconformity_quality_control_oca` | exists ⚠ unmerged, see O1 |
| NC ↔ Action | `mgmtsystem.nonconformity.action_ids` (Many2many) | exists |
| NC ↔ Equipment | `equipment_id` from `mgmtsystem_nonconformity_maintenance_equipment` | exists |
| **NC ↔ Maintenance Request** | — | **must be built** |
| **Action ↔ Inspection** | — | **must be built** |
| **Action ↔ Maintenance Request** | — | **must be built** |

⚠ **Equipment is not the Maintenance Request.** The OCA bridge links a
nonconformity to a *machine*, and one machine has many requests over its life.
Nothing in the stack currently connects the PM event to its notification — that
relation has to be created.

**The three new fields.** `mgmtsystem.action` carries no generic `res_model` /
`res_id` pair, so there is nothing polymorphic to reuse; concrete Many2one fields
are both cheaper and better indexed.

| Field | Points to | Declared in |
|---|---|---|
| `mgmtsystem.nonconformity.maintenance_request_id` | `maintenance.request` | `qms_maintenance` |
| `mgmtsystem.action.inspection_id` | `qc.inspection` | `qms_quality_control` |
| `mgmtsystem.action.maintenance_request_id` | `maintenance.request` | `maintenance_mgmtsystem_action` |

Each gets its inverse One2many on the far side (`nonconformity_ids`,
`action_ids`) and a smart button on both models.

**Click behaviour.** Count of zero opens a new form carrying the context
defaults below. Count of one or more opens the matching records filtered, with
the same defaults still on the action so that creating from that list prefills
identically.

**Prefill.** The window action supplies defaults through `context` — pure XML,
no Python:

```xml
context="{'default_product_id': product_id,
          'default_equipment_id': equipment_id,
          'default_name': name}"
```

Related fields make the chains reachable from context, and are **null-safe by
construction** — a related field through an empty Many2one yields `False`, so
equipment without a product resolves to no product with no guard code.

| Target | Source path | Cost |
|---|---|---|
| Product (QM) | `qc.inspection.product_id` — exists | free |
| Inspection | direct | free |
| Equipment (PM) | `maintenance.request.equipment_id` — exists | free |
| Product (PM) | `maintenance.request.product_id = related("equipment_id.product_id")` | one field |
| ~~Workcenter~~ | only via `object_id`, a Reference field | **deferred** |

### 7.11 Defect capture at inspection

`quality_control_oca` records a qualitative answer as a `qc.test.question.value`
carrying an `ok` boolean ("Correct answer?"). Two fields turn that into a defect
source:

| Model | Field | Type | Notes |
|---|---|---|---|
| `qc.test.question.value` | `defect_code_id` | Many2one → `qms.defect.code` | the defect this answer represents |
| `qc.test.question.value` | `defect_severity_id` | Many2one, related, readonly | `defect_code_id.default_severity_id` — displayed beside the code |

Severity is already a property of the defect code, so displaying it here is free
— it simply lets whoever writes the checklist see which answer carries which
severity without opening the catalog.

**Populate Defect** — a button on the nonconformity. Reads the source
inspection's answered lines where the chosen value has `ok = False` and a defect
code set, and creates one `qms.nonconformity.item` per distinct defect, carrying
the severity through. Object part and cause are left empty for the analyst — the
wildcard matching in §7.3 handles partial input natively.

Inspection only. A maintenance request has no structured defect source; giving it
one would mean building a checklist model, which is a separate project. Manual
item entry covers the PM side.

### 7.12 Maintenance request SLA fields

Three fields formalise response measurement on `maintenance.request`.

| Field | Type | Notes |
|---|---|---|
| `time_to_response` | Float, computed, stored | creation → In Progress |
| `time_to_resolution` | Float, computed, stored | creation → close stage |
| `priority` | Selection | **override**: add `tracking=True` |
| `can_edit_priority` | Boolean, computed, not stored | requester or maintenance manager |

Core's `priority` is a star widget that is neither tracked nor restricted —
effectively cosmetic. For SLA purposes it has to be an auditable commitment, so:

- `tracking=True` puts every change in the chatter
- the view sets `readonly="not can_edit_priority"`
- a `write()` guard raises `AccessError` for anyone who is neither the requester
  nor a maintenance manager, so the restriction holds at API level and not only
  in the form

Core's existing `duration` field is left alone. It is a manual float used for
calendar and gantt display; repurposing it would break those views.

### 7.13 Equipment status automation

A corrective request drives the state of its equipment:

| Request stage | Equipment state |
|---|---|
| In Progress | Down |
| Repaired | Operational |
| Scrapped | Scrapped |

Applies **only** when `maintenance_type == 'corrective'`. Preventive and any
other type leave equipment state alone. The automation is one-directional — it
writes equipment state and never reads it back, so a manual correction is never
fought by the system.

### 7.14 Preventive action generation

A maintenance plan carries `action_template_ids`. When the plan generates a
request, that request should also get the actions the plan seeds — this is the
preventive counterpart to the determination engine, and it is why preventive
work needs no nonconformity to hang its actions on.

**The hook is a `create()` override on our own model, not on any OCA method.**
`maintenance_plan` generates requests through
`maintenance.request.create()` with `maintenance_plan_id` present in the values
(the plan exposes `maintenance_ids = One2many("maintenance.request",
"maintenance_plan_id")`, and `_prepare_requests_from_plan` sets that key). So
`maintenance_plan_action_template` overrides `create()` on `maintenance.request`,
checks for `maintenance_plan_id`, and generates actions from that plan's
templates, linking them through `maintenance_request_id`.

Nothing in `maintenance_plan` is touched. The override sits on a model the
module already extends, which is ordinary Odoo practice, and it also catches a
request that has a plan assigned by hand rather than by the generator.

**Verify at implementation:** that generation still routes through `create()`
rather than a batch or SQL path. If a future OCA version changes that, this is
the one place in the design that would silently stop firing.

---

## 8. Module Breakdown

| Module | Contents | Depends on |
|---|---|---|
| **`qms_catalog`** | `qms.catalog.mixin`, `qms.defect.code`, `qms.object.part`, `qms.catalog.profile`, product/template/category assignment fields, configuration menus | `product`, `mgmtsystem` |
| **`qms_nonconformity`** | `qms.nonconformity.item`, header fields, `disposition`, code filtering, `partner_id` override, `default_severity_id` on `qms.defect.code` | `qms_catalog`, `mgmtsystem_nonconformity`, `mgmtsystem_nonconformity_product`, `mgmtsystem_partner` |
| **`qms_determination`** | `qms.determination.rule`, `qms.nonconformity.response`, Suggest Response, Generate Actions — see `docs/qms_determination_plan_revised.md` | `qms_nonconformity`, `mgmtsystem_action_template`, `document_page_procedure`, `document_page_work_instruction` |
| **`qms_quality_control`** | `defect_code_id` + related severity on `qc.test.question.value`, Populate Defect, `mgmtsystem.action.inspection_id`, NC and Action smart buttons + prefill | `qms_nonconformity`, `quality_control_oca`, `mgmtsystem_nonconformity_quality_control_oca`, `mgmtsystem_action` |
| **`qms_maintenance`** | `mgmtsystem.nonconformity.maintenance_request_id`, NC smart button + prefill, `product_id` related field | `qms_nonconformity`, `maintenance_product`, `mgmtsystem_nonconformity_maintenance_equipment`, `maintenance_mgmtsystem_action` |
| **`maintenance_mgmtsystem_action`** | `mgmtsystem.action.maintenance_request_id`, inverse `action_ids`, smart buttons both ways | `maintenance`, `mgmtsystem_action` |
| **`maintenance_request_sla`** | `time_to_response`, `time_to_resolution`, tracked and restricted `priority` | `maintenance` |
| **`maintenance_equipment_status_automation`** | equipment state driven by corrective request progression | `maintenance`, `maintenance_equipment_status` |
| **`maintenance_plan_action_template`** | `action_template_ids` on the plan; action generation via `create()` override | `maintenance_plan`, `mgmtsystem_action_template`, `maintenance_mgmtsystem_action` |

The last four are independent of the QMS chain, depend only on core and OCA
modules, and are candidates for upstream contribution. Keeping them separate
means a site can adopt SLA measurement, status automation or plan-seeded actions
without installing the quality system at all.

`maintenance_mgmtsystem_action` exists because **two** consumers need the
Action ↔ Maintenance Request relation — `qms_maintenance` and
`maintenance_plan_action_template`. Without it, the Phase 2 module would have to
depend on the whole QMS chain. Action ↔ Inspection has only one consumer and so
lives directly in `qms_quality_control`; the asymmetry is deliberate.

### Dependency graph

```
                 product (core), mgmtsystem
                             │
                        qms_catalog
                             │
                      qms_nonconformity
              (mgmtsystem_nonconformity, _product,
                     mgmtsystem_partner)
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
  qms_determination  qms_quality_control  qms_maintenance
  (action_template,  (quality_control_oca, (maintenance_product,
   document_page)     _nonconformity_qc,    _nonconformity_maint_eq,
                      mgmtsystem_action)    maintenance_mgmtsystem_action)
                                                    │
  ── independent of the QMS chain ──────────────────┼──────
                                                    ▼
  maintenance_mgmtsystem_action           →  maintenance
                                             mgmtsystem_action
        △
        └──────────────────────────────┐
  maintenance_plan_action_template  ────┘
                                          →  maintenance_plan
                                             mgmtsystem_action_template

  maintenance_request_sla                 →  maintenance
  maintenance_equipment_status_automation →  maintenance
                                             maintenance_equipment_status
```

---

## 9. Design Decisions

Recorded so future work does not relitigate them.

| # | Decision | Rationale | Rejected alternative |
|---|---|---|---|
| D1 | SAP fidelity is functional, not literal. No SAP table names in this document. | Half-correct table references lend false authority and cannot be maintained. | Documenting the SAP schema alongside ours |
| D2 | Catalogs are self-referencing trees; a code group is a parent-less row | This is how OCA already models Cause and Origin; matching it costs nothing and keeps the UX consistent | Separate group and code tables |
| D3 | Separate catalog models sharing an abstract mixin | Generic-model-with-type-discriminator would have prevented reuse of OCA's existing catalogs and forced duplicate Cause/Origin models | One generic catalog model |
| D4 | Profiles reference groups only — never codes, never other profiles | Two tiers already exist inside the catalog; nesting profiles would let one restriction be expressed two ways | Recursive profiles |
| D5 | Profiles attach to Product only | `maintenance_product` unifies Equipment with Product, so one resolution path serves both domains — cheaper than SAP's dual assignment | Separate equipment profile fields |
| D6 | Assignment is additive across product / template / category, and a category profile also applies to subcategories. The rule is computed in `qms_catalog` as `qms_effective_profile_ids`, never re-encoded in a domain | Profiles widen vocabulary; override would silently drop the broader set. Mirrors `quality_control_oca` Test assignment, which is additive and walks up the category tree. Expressing it once, in Python, makes it testable where it is defined and leaves the filter with no rule to drift from | Nearest-level-wins; direct category only; the rule spelled out again in the §7.6 domain |
| D7 | Filtering by static search domain, over a computed set of profiles | The domain keeps the restriction visible and removable in the search panel, which is the point of the decision. Resolving *which* profiles apply is a computation, and doing it in Python beats a second encoding of D6 inside the domain | A domain that walks the assignment relations itself; a computed field that filters the codes directly |
| D8 | Determination by wildcard conditions ranked by specificity | Pre-creating every defect × part × cause combination is combinatorially impossible. Group-level rules collapse dozens of cases into one | Pre-built profile picklist |
| D9 | Suggestions written by button, not `compute=` | A `compute=` field silently rewrites historical suggestions when rules change, destroying the audit comparison | Computed suggestion field |
| D10 | No Activity model. `type_action` plus stage lifecycle covers it | "Kind of response" and "planned vs performed" are independent axes and both already exist | Separate activity log, or an extra NC phase |
| D11 | No gate between primary transactions and the nonconformity | A forcing function people route around is worse than none. Departments are measured on performance, not nonconformity creation rate | Closure gates in both directions |
| D12 | Disposition lives on the nonconformity | `qc.inspection.state` is a Selection its own workflow methods branch on; extending it is the most invasive change available | Usage Decision stages on the Inspection |
| D13 | Object Part codes instead of equipment hierarchy | `maintenance_equipment_hierarchy` would force components to become tracked Equipment | Equipment parent/child |
| D14 | `domain_kind` on catalogs; `system_id` left alone. `domain_kind` classifies catalog entries, profiles and rules by domain for configuration, filtering and reporting, **and is an enforced invariant**: a code's domain must be compatible with its group's — `qm` under `qm`, `pm` under `pm`, any under `both` | `mgmtsystem.system` is a user-editable record meant for compliance scope; keying logic to it is fragile. Unenforced, `domain_kind` discriminates nothing: profiles reference groups, so a `both` code under a `qm` group can never surface in maintenance, and the data would claim otherwise | `system_id` as the PM/QM discriminator; `domain_kind` as an unconstrained label |
| D15 | No 8D compliance claim | 8D is a reporting discipline, not a standard to comply with | Describing the system as 8D-compliant |
| D16 | Severity is an output resolved in three tiers, never a rule condition | Soliciting severity from staff makes the most analytically important field the least reliable. Severity genuinely depends on the defect *combination* — a tear on a visible panel versus an internal facing — so the rule must be able to set it. Allowing it as both condition and output would make resolution circular | Severity as staff input; severity as a rule condition; severity from the defect code alone |
| D17 | The nonconformity holds **response lines** referencing rules, not flattened suggestion fields | Reuses an existing structure; shows *why* a response was indicated rather than only *what*; lines can be added by hand, so the determination engine is an accelerator rather than a dependency | `suggested_action_template_ids` / `suggested_procedure_ids` on the header |
| D18 | The existing Procedures tab is left untouched | It holds human-attached documents; rule-derived documents have different provenance. Merging them destroys the ability to distinguish the two, and separating them costs nothing | Repurposing `procedure_ids` as the suggestion holder |
| D19 | Maintenance SLA and equipment-status automation are separate modules depending only on core and OCA | Neither needs the QMS chain. Separating them lets a site adopt SLA measurement without the quality system, and makes both contributable upstream | Folding both into `qms_maintenance` |
| D20 | `priority` is made tracked and write-restricted rather than replaced | Core's star widget is untracked and unrestricted, so it cannot carry an SLA commitment. Overriding the existing field keeps every view and filter that already references it | A separate SLA priority field |
| D21 | Links are concrete Many2one fields, not a generic `res_model`/`res_id` pair | `mgmtsystem.action` has no generic pair to reuse, so the polymorphic route would mean *building* one. Concrete fields are indexed, give free inverse One2many for smart-button counts, and match how the OCA bridge modules already work | A generic reference pair on `mgmtsystem.action` |
| D22 | Action ↔ Maintenance Request lives in its own small bridge module | Two consumers need it — `qms_maintenance` and `maintenance_plan_action_template`. Putting it in the former would force a Phase 2 module to depend on the whole QMS chain, breaking D19 | Declaring it in `qms_maintenance` |
| D23 | Plan-seeded actions are generated by a `create()` override on `maintenance.request`, not by modifying `maintenance_plan` | Generation already routes through `maintenance.request.create()` with `maintenance_plan_id` in the values, so no OCA method is touched at all. It also catches requests given a plan by hand | Overriding `_create_new_request` or `_prepare_requests_from_plan` |
| D24 | `qms_catalog` depends on `mgmtsystem` | The catalogs exist to serve the management system. The dependency places their menus under *Management System → Configuration*, beside OCA's Cause and Origin. `mgmtsystem` is the light framework base, so no nonconformity dependency comes with it | `qms_catalog` on `product` alone, with menus deferred to `qms_nonconformity` |
| D25 | Catalogs and profiles are managed by `mgmtsystem.group_mgmtsystem_manager`; all internal users can read them | Matches OCA's access rules for Cause and Origin. The same group already sees *Management System → Configuration*, so menu visibility and edit rights coincide. A dedicated group can be added later without breaking anything | A dedicated catalog manager group; `product.group_product_manager` |
| D26 | Every matching rule applies | Outputs are lists; top-wins drops a group rule's outputs whenever a narrower rule matches | Rank by specificity and take the top rule |
| D27 | Generate Actions creates actions from response lines without deduplication | Simple; the button is gated to `pending` and asks for confirmation, and an unwanted action is cancelled through its stage — actions cannot be deleted | Skip templates that already produced an action |
| D28 | Rule documents are shown with `related_sudo=False` and limited to procedures and work instructions | Per-page access rules must filter, not raise; the type limit keeps rules relevant | Any `document.page`; a superuser-computed related field |
| D29 | A rule must set at least one of its three conditions | Strict matching makes an all-empty rule a catch-all; any single condition keeps cause-only and part-only rules possible | Allow all-empty rules; require the defect code specifically |
| D30 | Suggest Response deletes every line, manual ones included, before regenerating | One-sentence behaviour; the cost is confined to Analysis, where the button lives | Keep manual lines across reruns, distinguished by a `source` field |
| D31 | An operational user holds their domain group **and** the management-system group at the matching level, so cross-domain reads are in scope by role assignment and **no module grants foreign model access by ACL row**. A view element that dereferences a foreign model names the single group granting that read; a related field to a comodel with per-record rules uses `related_sudo=False` so those rules filter instead of raising; a module meant for upstream contribution gates without relying on the matrix. Reasoning and the verified access tables: `docs/Cross_Module_Access_Policy.md` | `mgmtsystem` is the shared layer between QM and PM and the workflow requires the same people in both, so a single-domain user is a misassignment, not a role. Granting would widen each OCA module's intent — quality-control users reading every management-system action, management-system viewers every inspection — to fix forms that work under the matrix. The group on the element still matters: without it a misassigned user cannot open the record at all, rather than merely missing a button | Granting foreign read by ACL row in each linking module; relying on view gating alone, with no matrix on the record |

---

## 10. Delivery Phases

### Phase 1 — the core chain

1. `qms_catalog` — catalogs, profile, assignment
2. `qms_nonconformity` — items, disposition, filtering, partner override
3. `qms_determination` — rules, response lines, Suggest Response
4. `qms_quality_control` — defect code on answers, Populate Defect, smart button
5. `qms_maintenance` — smart button, product related field

After Phase 1 the pipeline is complete and usable end to end.

### Phase 2 — quality-of-life

6. `maintenance_request_sla`
7. `maintenance_equipment_status_automation`
8. `maintenance_plan_action_template`

None of these depend on the QMS chain, so Phase 2 can run in parallel with
Phase 1 or be skipped entirely.

`maintenance_mgmtsystem_action` is shared: it is a dependency of
`qms_maintenance` in Phase 1 and of `maintenance_plan_action_template` in
Phase 2, so it is built as part of Phase 1 step 5.

### Deferred

- Nonconformity closure gates — revisit only if manual discipline proves insufficient
- Workcenter prefill — requires traversing a Reference field
- Cause group scoping on profiles — add if the cause list outgrows a single dropdown
- Response line snapshots — see O5
- Stock actions driven by disposition
- 8D report template

---

## 11. Open Items

| # | Item | Action needed |
|---|---|---|
| O1 | `mgmtsystem_nonconformity_quality_control_oca` is not on the 18.0 branch | **Not a blocker.** The 18.0 port exists and has been verified installing and functioning; it stalled on OCA merge process rather than on code quality, and the same work was merged successfully for 19.0. Pin the commit and vendor it into the reference clone. Open only so that the officially merged version is adopted if and when it lands. |
| O2 | Source of `partner_id` being mandatory | Confirmed mandatory in practice. Base `mgmtsystem_nonconformity` does **not** mark it required, in model or view. `mgmtsystem_nonconformity_type` is the likely motive — it adds `quality_contact_name` / `quality_contact_email` and an `action_nc_sent` method that mails the partner's quality contact — but it does **not** override `partner_id` in its Python either, so the requirement is set in a view somewhere not yet located. Find it at implementation; the fix is one line whether it turns out to be Python (`required=False`) or XML (`required="0"`). |
| O3 | Catalog tree depth | The static filter domain requires exactly two levels. Add a constraint or user guidance preventing a third. |
| ~~O4~~ | ~~`type_action` on generated actions~~ | **Closed.** `mgmtsystem.action.type_action` is present (`immediate` / `correction` / `prevention` / `improvement`), and `mgmtsystem.action.template.type_action` carries the same selection, sharing it through `_selection_type_action()`. The response-type axis in §7.7 and the plan-seeded generation in §7.14 both rest on fields that already exist. |
| O5 | Response lines link live rules rather than snapshotting them | **Deferred by decision.** Editing a rule retroactively changes what historical nonconformities appear to have been told. Revisit if rules turn out to churn, or if an audit ever needs "what did policy say at the time". The fix is additive: add `severity_id`, `action_template_ids`, `document_ids` snapshot columns to `qms.nonconformity.response` and populate them at suggestion time. Nothing else changes. |
| O6 | Plan-seeded action generation depends on `create()` | The `create()` override in `maintenance_plan_action_template` fires because OCA's generator routes through `maintenance.request.create()` with `maintenance_plan_id` in the values. Confirm this at implementation, and re-check on any `maintenance_plan` upgrade — if generation ever moves to a batch or SQL path, this is the one place in the design that would silently stop firing rather than fail loudly. |

---

## Appendix A — Terminology

Conceptual correspondence only. **Not** an assertion of schema equivalence.

| SAP concept | Odoo / this system |
|---|---|
| Catalog | `qms.defect.code`, `qms.object.part`, `mgmtsystem.nonconformity.cause` |
| Code group | A catalog record with empty `parent_id` |
| Code | A catalog record with a parent |
| Catalog profile | `qms.catalog.profile` |
| Notification | `mgmtsystem.nonconformity` |
| Notification item | `qms.nonconformity.item` |
| Defect class | `qms.defect.code.default_severity_id` |
| Task | `mgmtsystem.action` in an open stage |
| Activity | `mgmtsystem.action` in a closed stage |
| Maintenance order | `maintenance.request` |
| Inspection lot | `qc.inspection` |
| Master inspection characteristic | `qc.test.question` |
| Usage decision | `mgmtsystem.nonconformity.disposition` |
| Equipment | `maintenance.equipment` |
| Material master | `product.product` |

## Appendix B — Naming conventions

- Custom modules are prefixed `qms_` where they belong to this system, or follow
  OCA `<base_module>_<feature>` naming where they are generic enough to be
  contributed upstream.
- Custom models are prefixed `qms.`.
- Fields added to OCA models are prefixed `qms_` to avoid collision with future
  upstream fields.

## Appendix C — Problem-resolution coverage

Not a compliance claim. Recorded so that if an 8D report is ever required, the
data is already present and only a template is missing.

| Discipline | Covered by |
|---|---|
| D1 — Team | `responsible_user_id`, `manager_user_id` |
| D2 — Problem description | `description` + `item_ids` (defect × object part) |
| D3 — Interim containment | `immediate_action_id`, actions with `type_action = immediate` |
| D4 — Root cause | `item_ids.cause_id` |
| D5 — Permanent corrective action | actions with `type_action = correction` |
| D6 — Implementation | action stage lifecycle, `date_closed` |
| D7 — Prevention | actions with `type_action = prevention`; `mgmtsystem_action_efficacy` |
| D8 — Closure | `disposition`, closing stage, `closing_date` |
