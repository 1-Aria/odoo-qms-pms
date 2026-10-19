# Cross-module access policy

**Status:** adopted 2026-09-23. Recorded in the plan as D31, which points here for the
reasoning. Supersedes the first draft of this file, which proposed granting foreign model
access by ACL row; §5 says why that was dropped.

## 1. The problem

Every OCA module owns its own groups, and none of them imply each other. A field or button
that dereferences a model from another domain therefore raises `AccessError` for a user who
holds only their own domain's groups. It appeared three times during development:
`document.page` in `qms_determination`, `qc.inspection` in `qms_quality_control` step 2, and
`mgmtsystem.action` as step 3 was being specced.

**Referencing a Many2one is safe; reading through it is not.** In `web_read`, a Many2one
requested with only `display_name` never reads the comodel — `fields_to_read == ['id']`
short-circuits the `read()`, with a comment saying it "avoid[s] a call to read on the co-model
that might have different access rules" (`odoo/addons/web/models/models.py:79-84`) — and the
label itself is taken through `rec.sudo()` (`:122-123`). Any other field of the comodel goes
through the access-checked path at `:113-118`.

That is why the OCA bridge's `qc_inspection_id` displays on the nonconformity form for a user
with no quality-control rights, while a compute reading that inspection's `state` raises. A
plain compute is evaluated as the user: `compute_sudo` defaults to `store`, so `False` for a
non-stored field (`odoo/odoo/fields.py:443`, `309`). A **related** field is the opposite trap —
`related_sudo` defaults to `True` and `compute_sudo` inherits it (`:451`), so it is computed as
superuser and raises nothing on load, deferring the failure to the click.

## 2. The role matrix this system assumes

`mgmtsystem` is the shared layer between quality management and plant maintenance, and the
workflow requires the same people to work in both. Operational users therefore hold groups on
both sides:

| Role | Groups |
|---|---|
| Inspector / technician | *Quality control · User* and/or the maintenance side, **plus** *Management system · User* |
| Manager | *Quality control · Manager* and/or *Maintenance · Equipment Manager*, **plus** *Management system · Manager* |

Managers make the decisions staff do not: closing a nonconformity, confirming a failed
inspection.

Every cross-domain read our modules perform is covered by this assignment:

| Read | Granted by |
|---|---|
| `qc.inspection`, `qc.inspection.line`, `qc.test.question`, `qc.test.question.value` | `quality_control_oca.group_quality_control_user` (`quality_control_oca/security/ir.model.access.csv:2-9`) |
| `mgmtsystem.action`, `mgmtsystem.nonconformity` and their configuration models | `mgmtsystem.group_mgmtsystem_viewer`, implied by every other management-system group (`mgmtsystem/security/mgmtsystem_security.xml:11-49`) |
| `maintenance.request`, `maintenance.equipment` | `base.group_user` — core grants requests to every internal user (`maintenance/security/ir.model.access.csv:2-4`) |

## 3. The policy

**No module grants foreign model access by `ir.model.access` row.** Access comes from role
assignment, so neither OCA module's intent is widened.

**Any view element that dereferences a foreign model names the single group that grants that
read.** Its purpose is not access control — the audience already has the group — but that a
*misassigned* user gets a missing button instead of a record that cannot be opened at all.
One attribute buys that, and the failure it prevents is the worst kind: the whole form breaks,
not just the feature.

A `groups` attribute lists groups as a **union**: a comma means "member of at least one"
(`odoo/addons/base/models/res_users.py:1167-1170`, and the same matching in
`ir_ui_view._postprocess_access_rights`, `:1013-1040`). There is no way to spell "must hold
both", so a gate names the one group that guards the read, never a list assembled to look
thorough. `qms_quality_control` step 2 shipped a two-group list first, and it gated nothing.

**Two exceptions:**

1. **A comodel with per-record access control is filtered, not gated by group alone.** A
   related field to it carries `related_sudo=False`, so `Many2many.read` applies the user's
   record rules and unreadable records drop out instead of raising. `document.page` needs
   both: `related_sudo=False` for the per-page rules of `document_page_access_group`, and the
   group gate for Knowledge's `group_document_user`, which no management-system group implies.
2. **A module intended for upstream contribution gates without relying on this matrix.**
   `maintenance_mgmtsystem_action` is the case in hand: an OCA site has its own role design,
   so its buttons carry the group that grants the read regardless of what this system assumes.

**Testing.** Each cross-domain link gets one positive test in the module that owns it: a user
holding the intended combination reads through the link in both directions. Where a gate also
matters, a `get_view` assertion that the element is absent for a user without the group —
testing the arch, not only the compute, since the arch is what stops a form from breaking.

## 4. What this gives up

A single-domain user — an HR officer with management-system rights but no quality-control
role, an inspector with no management-system group — loses the cross-domain buttons. No such
role exists in this system today. If one appears, granting read by ACL row in the module that
owns the link is the fix, and it is purely additive: nothing has to be undone first.

## 5. Why not grant by ACL

The rejected draft proposed an `ir.model.access` row per link: read on `mgmtsystem.action` for
quality-control users, read on `qc.inspection` for management-system viewers, and so on. Three
reasons it was dropped.

- **It solves a problem only misassigned users have.** Every failure found during development
  came from a single-domain *test* user, not from a role anyone intends to create.
- **Model-level read is blanket.** Quality-control users would read every management-system
  action — audits, environment, HR — and management-system viewers every inspection and
  checklist. That is a real disclosure decision, taken to fix forms that work anyway under the
  matrix.
- **The grant is larger than it looks.** Populate Defect resolves its defect code through
  `qualitative_value` and `test_line`, so granting `qc.inspection` and `qc.inspection.line`
  alone moves the error from form load to the click; the honest grant is four models. A
  compute's reach is the dependency, not the field it is declared on.

## 6. Known gaps

**The maintenance side has no non-manager group.** Core defines only
`maintenance.group_equipment_manager`, and on this instance `maintenance_security` re-groups
the whole maintenance menu — dashboard, requests, equipment, reports — to it (that module
ships views only, no access rules, despite its name). A technician therefore has full record
rights on `maintenance.request` from core but no menu to reach it. This is a workflow question
to settle before `maintenance_mgmtsystem_action`: either technicians hold
`group_equipment_manager` as well, or the menu grouping is narrowed from one of our own
modules.

**An OCA bug, unfixed by decision.** `mgmtsystem_nonconformity_quality_control_oca` puts a
nonconformity count on the inspection form with no `groups`
(`views/qc_inspection.xml:12-33`), computing `len(rec.mgmtsystem_nonconformity_ids)` over a
model whose read is management-system-only. A quality-control user with no management-system
group therefore cannot open any inspection form. Under the matrix nobody is exposed to it, so
it is left alone here and is worth reporting upstream.
