# `qms_determination` — revised plan

**Status:** implemented — `qms_determination` built and tested 2026-09-22. The main plan
points here for §7.3, §7.5, the Analysis and Action Plan steps of §7.8, the
`qms_determination` row of §8, and D26–D30. Implementation details that differ from this
text are logged in `docs/modules/qms_determination.md`.

**Scope:** replaces the determination parts of the plan — §7.3 in full, §7.5 in full,
the Analysis and Action Plan steps of §7.8, and the `qms_determination` row of §8 — and
revises D8, D16 and D17. Everything else in the plan remains the reference.

The plan's shape is kept: a rule table mapping analysis to a suggested response, lines on
the nonconformity recording what was suggested, and a human deciding what to do. This
revision does three things:

1. **Adds** what was decided in review: accumulated matching, automated action creation,
   and document access handling.
2. **Clarifies** points the plan left vague — what a rerun does, how empty values match,
   which state gates which button, what happens on delete.
3. **Fixes** places where the plan contradicts itself or the source.

---

## 1. Changes at a glance

| # | Plan says | Revised | Why |
|---|---|---|---|
| 1 | Rules are ranked by `specificity`, then `sequence`; the top rule wins (§7.3) | **Every matching rule applies.** No ranking, no `specificity` field | Outputs are lists. Under top-wins, a group-level rule's actions and documents are lost whenever a more specific rule also matches, so authors must copy them into every specific rule — the per-combination authoring D8 exists to avoid |
| 2 | The rule's severity is tier 2 and "overrides tier 1 when a rule matches"; the button "refines item severity" (§7.3, §7.8) | **The rule's severity is a suggestion shown on the response line.** The button never writes to the item | Item severity and suggested severity are two different things — see §4. It also removes any conflict between a rule and a human edit |
| 3 | The user creates actions, "optionally from the action templates listed on the response lines" (§7.8 step 4) | Unchanged — actions are still created by hand in the Action Plan table. **Generate Actions** is added as an optional shortcut that creates them from the response lines' templates | Choosing a template on an action fills its fields only through a form onchange, so a shortcut working from templates has to copy those fields itself — see §7 |
| 4 | `document_ids` holds "any type, not only procedures" (§7.3) | **Procedures and work instructions only**, and shown on the response line without bypassing record rules | Document pages carry per-page access rules; an unreadable page must not break the nonconformity — see §8 |
| 5 | Rerunning the button "is expected and fine" (§7.8) | Rerun **deletes every line, manual ones included, and regenerates** | The plan did not say what happens to existing lines. A full reset is the simplest behaviour; a person re-adds manual lines after rerunning |
| 5a | Every condition may be empty, so a rule with none matches every item (§7.3) | A rule needs **at least one condition** — defect code, object part or cause | A rule with no conditions is a catch-all nobody intends. Requiring the defect code specifically would rule out cause-only rules such as *Machine fault → Raise maintenance request* |
| 9 | Three conditions: defect code, object part, cause | **four** — origin joins them, matched against the item's `origin_id` | Added 2026-09-24. `qms_nonconformity` records origin per analysis item, so a rule can key on where the nonconformity came from without the engine reading a second subject |
| 5b | Lines carry `source`, `suggested` or `manual` (§7.5) | **No `source` field** | Rerun no longer treats the two differently, so nothing reads it. A manual line is one with no `item_id` |
| 6 | Running the button after the stage advances "requires reverting the stage, which is logged" (§7.8) | Unchanged in effect. Each button is **hidden outside its state**, which is what makes reverting the stage necessary; the revert is logged because `stage_id` is tracked | The plan stated the outcome without the mechanism. Hiding the button supplies it, and OCA's stage tracking already supplies the log |
| 7 | `domain_kind` on the rule, with no stated meaning (§7.3) | A classifier that **must not clash** with the rule's catalog conditions | Same invariant already enforced on catalogs and profiles |
| 8 | Depends on `document_page_mgmtsystem` (§8) | Depends on `document_page_procedure` and `document_page_work_instruction` | The document filter needs the page-type values those two modules add |

---

## 2. What the module does

For each item on a nonconformity — a defect, optionally where and why — the module finds
every rule whose conditions fit, and lists each as a **response line**: the rule, the
item that triggered it, and what the rule suggests. The analyst reads the suggestions
and, in the Action Plan phase, creates actions — by hand in the Action Plan table as
always, or with one optional button that turns the suggested action templates into
actions.

The engine is an accelerator, not a dependency. Nothing is enforced: a nonconformity can
be analysed and closed with the button never pressed, and a person can add a response by
hand — though pressing the button again replaces every line, hand-added ones included.

---

## 3. The rule — `qms.determination.rule`

A rule has **conditions**, which decide whether it applies to an item, and **outputs**,
which say what it suggests.

`_order = "sequence, id"` — the author controls the order response lines appear in.

| Field | Type | Half | Notes |
|---|---|---|---|
| `name` | Char | — | required, translatable |
| `sequence` | Integer | — | display order only; plays no part in matching |
| `active` | Boolean | — | an archived rule stops matching; lines already pointing at it are kept |
| `domain_kind` | Selection `qm` / `pm` / `both` | — | classifier, see below |
| `defect_code_id` | Many2one → `qms.defect.code` | condition | empty = any; a group matches every code beneath it |
| `object_part_id` | Many2one → `qms.object.part` | condition | empty = any; a group matches every part beneath it |
| `cause_id` | Many2one → `mgmtsystem.nonconformity.cause` | condition | empty = any; matches every cause beneath it |
| `origin_id` | Many2one → `mgmtsystem.nonconformity.origin` | condition | empty = any; matches every origin beneath it. **Added 2026-09-24** |
| `severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | output | the suggested severity for this combination |
| `action_template_ids` | Many2many → `mgmtsystem.action.template` | output | templates Generate Actions turns into actions |
| `document_ids` | Many2many → `document.page` | output | procedures and work instructions only, see §8 |

**Removed:** `specificity`. Nothing ranks rules any more, so a stored compute with no
reader would only be maintenance.

**At least one condition.** A rule must set at least one of `defect_code_id`,
`object_part_id`, `cause_id` and `origin_id`. Under strict matching (§5) a rule with all three empty
would match every item on every nonconformity — a catch-all nobody intends. Any one
condition is enough: requiring the defect code specifically would rule out rules keyed on
cause, object part or origin alone. *Any defect / any part / Machine fault → Raise
maintenance request* bridges quality to maintenance, and *any defect / any part / any cause /
External Supplier → Procurement works with the supplier* is the same shape on the origin
dimension.

**`domain_kind` constraint.** A rule's domain must not contradict its catalog conditions:
a `qm` rule may not have a `pm` defect code or object part as a condition, and the
reverse; `both` on either side is accepted. This is the non-empty-intersection rule
`qms.catalog.profile` already applies to its groups. **Cause and origin are exempt** — neither
`mgmtsystem.nonconformity.cause` nor `mgmtsystem.nonconformity.origin` has a `domain_kind`.

**Delete versus archive.** Response lines point at rules, so a rule that has ever been
suggested is archived, not deleted (§5, `rule_id` is `ondelete="restrict"`). This is the
same archive-rather-than-delete rule the catalogs follow.

---

## 4. Two severities

The plan's three-tier table blurred two separate fields into one. They are distinct and do
not conflict.

| | Item severity | Suggested severity |
|---|---|---|
| Field | `qms.nonconformity.item.severity_id` | `qms.determination.rule.severity_id` |
| Built in | `qms_nonconformity` (step 3) | this module |
| Meaning | the item's severity — the defect code's default unless someone changed it | what this rule suggests for this defect × part × cause |
| Source | defaults from the defect code's `default_severity_id` when the code is picked; may be changed by hand | authored on the rule; readonly on the response line |
| Used in matching | **no** | — (an output) |
| Feeds | the nonconformity's header severity, by roll-up | nothing — it is read by the analyst on the response line |

So the plan's "the combination has to be able to set it" (D16) becomes **the combination
suggests it**. The suggestion is information on the response line, and nothing acts on it.
Changing an item's severity by hand is optional and has one consequence: it feeds the
header roll-up. The analytical point of D16 survives — a tear on a visible front panel and
on an internal facing can warrant different severities, and the rule table is where that
knowledge lives.

Accumulation fits this cleanly: two matching rules may suggest different severities for
the same item, and each line simply shows its own. There is nothing to resolve.

Severity remains an output only, never a condition — D16's reasoning against circularity
still holds.

---

## 5. Matching

A rule matches an item when **every non-empty condition** equals the item's value or is
an ancestor of it.

Three cases the plan left implicit:

| Rule condition | Item value | Matches? |
|---|---|---|
| empty | anything, including empty | **yes** — empty means any |
| a group or a code | a code at or beneath it | **yes** |
| a group or a code | **empty** | **no** — a rule that asks for a cause does not fire on an item with no cause |

The third row is what makes partial input work correctly: an item from an inspection
carries only a defect code, so only rules that leave object part and cause empty can match
it. The plan's R3 matches such an item; R1 does not.

**Every matching rule applies.** There is no ranking and nothing is outranked.

```python
def _match_rules(self, item):
    def self_and_ancestors(rec):
        # parent_of includes the record itself; all three models are _parent_store
        return rec.search([("id", "parent_of", rec.id)]).ids if rec else []
    return self.env["qms.determination.rule"].search([
        ("defect_code_id", "in", [False] + self_and_ancestors(item.defect_code_id)),
        ("object_part_id", "in", [False] + self_and_ancestors(item.object_part_id)),
        ("cause_id", "in", [False] + self_and_ancestors(item.cause_id)),
        # Added 2026-09-24, with origin_id on the item.
        ("origin_id", "in", [False] + self_and_ancestors(item.origin_id)),
    ])
```

`False` inside an `in` list matches empty values: `models.py:3189-3214` strips it from the
list and adds `OR field IS NULL`. For an empty item value the list is just `[False]`, which
matches only rules whose condition is also empty — the third row above.

`qms.defect.code` and `qms.object.part` are `_parent_store` through `qms.catalog.mixin`;
`mgmtsystem.nonconformity.cause` and `mgmtsystem.nonconformity.origin` are `_parent_store`
in OCA. The catalogs are held to two
levels; OCA places no depth limit on causes, and `parent_of` needs none.

**Worked example, revised.** Item *(Torn, Sleeves, Machine fault)*:

| Rule | Defect | Object part | Cause | Result |
|---|---|---|---|---|
| R1 | Torn | Sleeves | Machine fault | ✓ line |
| R2 | Torn | *(any)* | Incorrect operation | ✗ cause does not fit |
| R3 | Fabric Defect *(group)* | *(any)* | *(any)* | ✓ line |

Two response lines, R1 and R3. If R3 suggests *Quarantine lot* and R1 suggests *Rework
sleeve* and *Raise maintenance request*, all three appear — which is the point of writing
R3 at group level. Under the plan's top-wins rule R3 was "matched, outranked", and
*Quarantine lot* would have been lost.

Same rules, item *(Torn, —, —)* from an inspection: only R3 matches.

---

## 6. Response lines — `qms.nonconformity.response`

One line records one suggestion: a rule, and the item that triggered it if any.

| Field | Type | Notes |
|---|---|---|
| `nonconformity_id` | Many2one → `mgmtsystem.nonconformity` | required, `ondelete="cascade"` |
| `item_id` | Many2one → `qms.nonconformity.item` | set by Suggest Response; empty on a line a person added; `ondelete="cascade"` |
| `rule_id` | Many2one → `qms.determination.rule` | required, `ondelete="restrict"`; chosen once on a manual line, then frozen (`readonly="id"`) |
| the rule's conditions and outputs | related fields | readonly, shown so the line explains *why* it was suggested |
| `document_ids` | Many2many, `related="rule_id.document_ids"` | **`related_sudo=False`** — see §8 |

The nonconformity carries `response_ids`, the inverse One2many (§7.9 of the plan).

**A line is a pointer to a rule, not a copy of it.** Nothing about the rule can be edited
from the nonconformity. To change what a rule suggests, edit the rule.

**One line per item per matching rule.** Two items matching the same rule produce two
lines, each with its own `item_id`. Deduplicating would lose which item each suggestion
came from.

**Manual lines** are rules a person adds by hand. They carry no item — which is the only
thing that distinguishes them, so there is no `source` field. Like every other line they
are deleted by a rerun of Suggest Response, and a person re-adds them afterwards. The
rule picker offers any active rule; no further filtering.

**On delete:**

| Deleted | Effect |
|---|---|
| the nonconformity | its lines go with it |
| an item | the suggested lines it produced go with it |
| a rule that has lines | refused — archive it instead |

**Known limitation (O5, unchanged).** Lines point at the live rule, so editing a rule
changes what past nonconformities appear to have been told — now including the suggested
severity. Still accepted for v1; the fix is still additive snapshot columns on this model.

---

## 7. The buttons

Both sit in the nonconformity form's header, gated on `state`. The nonconformity's
`state` is `related="stage_id.state"` (`mgmtsystem_nonconformity.py:83`), so gating on
state works whatever stages a site configures.

Hiding a button outside its phase does not replace the stage history — it relies on it.
`stage_id` is tracked (`mgmtsystem_nonconformity.py:78`), so every stage change is already
in the chatter. Someone who wants to rerun Suggest Response after Analysis moves the
stage back, and that move is recorded like any other.

| Button | Visible when | Technical value |
|---|---|---|
| Suggest Response | Analysis | `state == 'analysis'` |
| Generate Actions | Action Plan | `state == 'pending'` |

**The Action Plan state is `pending`, not `action_plan`.** The label and the value differ
(`mgmtsystem_nonconformity_stage.py`, `_get_states`), and OCA's own Actions page is
already editable only in `pending` (`views/mgmtsystem_nonconformity.xml`, the `actions`
page). Use `!=` / `==` rather than OCA's `state not in 'pending'`, which matches substrings.

### Suggest Response

1. Delete **every** response line on this nonconformity, manual ones included.
2. For each item, run `_match_rules` and create one line per matching rule, with the
   item set.
3. Leave item severities untouched.

Rerunning is safe and gives the same result for the same items and rules. With no items it
simply clears the lines. A full reset rather than a selective one is deliberate: it keeps
the button's behaviour to one sentence, and the cost — re-adding any manual lines — falls
only within Analysis, since the button is hidden in every other state.

### Generate Actions

An optional shortcut. The Action Plan table on the nonconformity (`action_ids`, on OCA's
Actions page) is unchanged, and creating actions there by hand remains the normal way;
nothing in this module depends on the button being pressed.

For every response line — suggested or manual — and every action template on its rule,
create one `mgmtsystem.action` linked to the nonconformity. The generated actions appear
in the same Action Plan table as hand-made ones.

| Action field | Value |
|---|---|
| `name` | the template's name |
| `type_action` | the template's `type_action`; **a template without one is skipped** |
| `description` | the template's description |
| `user_id` | the template's `user_id` |
| `tag_ids` | the template's tags |
| `template_id` | the template |
| `nonconformity_ids` | this nonconformity |

**Why this is needed.** `mgmtsystem_action_template` fills an action from its template in
`_onchange_template_id`, which runs only when a user changes the field in a form. Creating
an action in code never triggers it. And `mgmtsystem.action` requires `name` and
`type_action` with no defaults (`mgmtsystem_action.py:22, 61`), so an action created with
only `template_id` set would **fail**, not merely be empty. The button must copy the fields
itself; the table above mirrors the onchange, which should be cited in a comment as the
source to diff against on an OCA upgrade.

**Why templates without a type are skipped.** `type_action` is optional on the template but
required on the action. A template left without one may be deliberate — not meant for
automatic use — and giving it a type would be a guess about its author's intent. The
skipped templates are named in a notification after the click, since the confirmation
before it is fixed text.

**Why no `"NEW "` prefix.** The onchange prefixes the name because in a form it is a
placeholder the user is about to overwrite. Generated actions are finished records.

**No deduplication and no memory of earlier presses.** A template on two lines gives two
actions, which usually means one action per affected defect. Pressing the button again
generates again. Actions cannot be deleted — no group has `unlink` on `mgmtsystem.action`
— so an unwanted one is cancelled through its stage. The controls are the button being
visible only in `pending` and a confirmation on the click. This is deliberate: guarding
against duplicates would cost more than they do.

---

## 8. Document access

**The concern.** Document pages can be restricted per page. `document_page_access_group` is
installed on this instance, and its record rule makes a page readable only if the user is
in one of its groups, is listed on it, or the page has no such restriction:

```
['|', ('groups_id', 'in', user.groups_id),
 '|', ('user_ids', 'in', [user.id]),
 '&', ('groups_id', '=', False), ('user_ids', '=', False)]
```

A user who cannot read a page listed on a response line must not get an error opening the
nonconformity.

**What already works.** Reading a Many2many applies the comodel's record rules —
`Many2many.read` calls `comodel._apply_ir_rules(query, 'read')` in `odoo/fields.py`. Pages a
user cannot read are silently left out. So the rule form is safe as it stands.

**The trap.** The natural way to show a rule's documents on a response line is
`related="rule_id.document_ids"`. Related fields are computed as superuser by default —
`compute_sudo` falls back to `related_sudo`, which defaults to `True` (`fields.py:451`). That
bypasses the record rules and hands the user pages they cannot read.

**The fix.** Declare it `related_sudo=False`. The value is then computed as the user,
`Many2many.read` applies their record rules, and unreadable pages drop out. This is the
same choice core makes for `res.users.department_id` (`hr/models/res_users.py:97`).

**The type restriction is for relevance, not access.** `document_ids` carries
`domain=[("mgmtsystem_page_type", "in", ("procedure", "work_instruction"))]`. The field is
declared empty by `document_page_mgmtsystem` and extended with `procedure` by
`document_page_procedure` and `work_instruction` by `document_page_work_instruction`. It
keeps rules pointing at controlled QMS documents rather than arbitrary pages. It does not
make those pages readable — a procedure can carry access groups like any other page. What
prevents the error is `related_sudo=False`.

---

## 9. Access rights and menus — proposed

Following the patterns already set in `qms_catalog` and `qms_nonconformity`.

| Model | `mgmtsystem.group_mgmtsystem_viewer` | `mgmtsystem.group_mgmtsystem_user` | `mgmtsystem.group_mgmtsystem_manager` |
|---|---|---|---|
| `qms.determination.rule` | read | read | full |
| `qms.nonconformity.response` | read | read, write, create, delete | full |

Rules are configuration, managed like catalogs and dispositions. Response lines are part of
the nonconformity record, like items. The viewer row matters: viewers can read a
nonconformity, so without it they would hit an access error on its response lines — the
same gap found on dispositions.

**Menu:** *Determination Rules* under *Management System → Configuration*, beside the
catalogs.

**Placement on the form:** response lines in the *Causes and Analysis* page, after the
Analysis Items, so the page reads narrative → items → suggestions.

---

## 10. Dependencies

| Module | Why |
|---|---|
| `qms_nonconformity` | items, the nonconformity header, `response_ids` |
| `mgmtsystem_action_template` | `mgmtsystem.action.template`, and `template_id` on actions |
| `document_page_procedure` | the `procedure` page type |
| `document_page_work_instruction` | the `work_instruction` page type |

`document_page_mgmtsystem` arrives through the last two. `document_page_procedure` already
arrives through `mgmtsystem_nonconformity`, but the domain names its value directly, so it
is declared. `document_page_work_instruction` is not otherwise in the chain.

---

## 11. Decisions affected

| # | Revision |
|---|---|
| D8 | Kept, and now fully honoured: a rule written at group level contributes its outputs to every item beneath it, *in addition to* any more specific rule. |
| D9 | Unchanged. Lines are written by the button, never by a compute. |
| D16 | Severity stays an output and never a condition. The rule's severity is now **suggested** on the response line, not written to the item; the item's own severity defaults from the defect code, may be changed by hand, and affects only the header roll-up (§4). Tier 2 of the plan's table no longer writes anything. |
| D17 | Unchanged. Lines reference rules rather than flattening their outputs onto the header. |
| D18 | Unchanged. The nonconformity's own *Procedures* tab stays for documents a person attached; rule documents live on the response lines. |

**New decisions:**

| # | Decision | Rationale | Rejected alternative |
|---|---|---|---|
| D26 | Every matching rule applies | Outputs are lists; top-wins drops a group rule's outputs whenever a narrower rule matches | Rank by specificity and take the top rule |
| D27 | Generate Actions creates actions from response lines without deduplication | Simple; the button is gated to `pending` and asks for confirmation, and an unwanted action is cancelled through its stage — actions cannot be deleted | Skip templates that already produced an action |
| D28 | Rule documents are shown with `related_sudo=False` and limited to procedures and work instructions | Per-page access rules must filter, not raise; the type limit keeps rules relevant | Any `document.page`; a superuser-computed related field |
| D29 | A rule must set at least one of its three conditions | Strict matching makes an all-empty rule a catch-all; any single condition keeps cause-only and part-only rules possible | Allow all-empty rules; require the defect code specifically |
| D30 | Suggest Response deletes every line, manual ones included, before regenerating | One-sentence behaviour; the cost is confined to Analysis, where the button lives | Keep manual lines across reruns, distinguished by a `source` field |

---

## 12. Out of scope

- **Writing suggested severity to the item.** Suggested severity stays on the response
  line. An item's severity changes only if someone edits it, which is optional.
- **Snapshots of rule outputs on lines** — O5, deferred.
- **Deduplicating actions** — D27.
- **Filtering rules by the product's catalog profile.** Profiles scope what the analyst can
  *choose* on an item (§7.6); by the time rules run, the item's codes are already in scope.

## 13. Deferred — exclusive rules

**The gap.** Accumulation means a group-level rule always applies alongside any more
specific rule beneath it. Occasionally a specific combination should get *only* its own
response, without the broader rule's.

**The workaround until then, needing no code:** narrow the broad rule. Attach its outputs
to the sibling codes that should receive them rather than to the whole group. That is
per-combination authoring, but only for the exception, which is the trade D8 accepts.

**If the case turns out to be common**, add an `exclusive` Boolean to the rule. When an
exclusive rule matches an item, the matching rules it refines are dropped for that item.
Another rule is refined by it when each of the other rule's conditions is empty or is an
ancestor-or-self of the exclusive rule's condition on the same dimension — a prefix check
on `parent_path`. A dimension the exclusive rule leaves empty does not count as refined, so
a rule that is narrower there is kept.

**Where the idea comes from.** SAP's condition technique, used for pricing and output
determination: condition records are looked up along an access sequence from most
specific to most general, and a step marked *exclusive* stops the search once it finds a
record. The default is to keep looking, and exclusivity is opted into per entry — the same
shape as here. This is a pattern borrowed, not a precedent: it is not verified that SAP's
QM task determination works this way, and D1 warns against letting SAP references carry
authority they have not earned.
