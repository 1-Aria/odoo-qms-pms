# qms_determination

Determination rules, response lines, Suggest Response, Generate Actions.
Plan: `docs/qms_determination_plan_revised.md`, which the main plan now points to for
§7.3, §7.5, the Analysis and Action Plan steps of §7.8 and the `qms_determination` row of
§8, and which adds D26–D30. Divergences below are against the revised plan; entries 4 and 5
were also folded back into it on 2026-09-22.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `qms.determination.rule`: conditions, outputs, the at-least-one-condition and `domain_kind` constraints, access, views, menu | done | installed and tested 2026-09-22, `exit=0`, 8 tests, 0 failures; UI checked: menu after Catalogs, an empty rule refused, a Quality rule refusing a Maintenance code, documents gated and limited to procedures and work instructions. Before any code, a review showed `@api.constrains` would never fire for a rule created without condition fields (`odoo/api.py:184-190`), so the at-least-one-condition rule became the `has_condition` SQL CHECK |
| 2 | `qms.nonconformity.response`, header `response_ids`, matching, Suggest Response, lines in Causes and Analysis | done | upgraded and tested 2026-09-22, `exit=0`, 18 tests (8 rule, 10 response), 0 failures; UI checked: the button only in Analysis, one line per item per matching rule, manual lines locked once saved, rerun replacing every line, and a procedure page with an access group the viewing user lacked left out of their Documents column without an error. The other gate — the Documents column hidden for a user without Knowledge's `group_document_user` — was **not** exercised: with Central access to Documents on, every internal user has that group, so no such user can exist here. Needed a `display_name` on the item, added to `qms_nonconformity` as its step 4 |
| 3 | Generate Actions: confirmation on click, one action per typed template per response line, a notification naming skipped templates | done | upgraded and tested 2026-09-22, `exit=0`, 27 tests (8 rule, 10 response, 9 generate), 0 failures; UI checked: confirmation on click, actions without the `NEW` prefix, a template with no response type named in a notification while the others were created, the button only in Action Plan. Two designs were dropped before any code: a fallback to Corrective for untyped templates, replaced by skipping them, since the fallback would guess at the template author's intent; and a confirmation wizard listing skipped templates, replaced by the button's `confirm` plus a notification after the click, the simpler of the two |
| 4 | `origin_id` as a fourth rule condition: the field, the `has_condition` CHECK, matching, and the related field on the response line | done | upgraded and tested 2026-09-24, `exit=0`, 34 tests, 0 failures; UI checked — a rule saved with nothing but an origin, which the old CHECK refused, and an origin-only rule producing a response line for an item carrying that origin. Widening the CHECK made Odoo drop and recreate it, with every existing rule satisfying the wider version by construction |

## Divergences from the revised plan

| # | Revised plan | This module | Reason |
|---|---|---|---|
| 1 | §5 finds ancestors with `rec.search([("id", "parent_of", rec.id)])` | ancestors read from `rec.parent_path` (step 2) | A search is filtered by `active`, so an archived group would drop out of the list and every group-level rule would silently stop firing for its still-active codes. All three condition models are `_parent_store`, so the ids are already on the record, and no query is needed |
| 2 | §8 handles unreadable pages with `related_sudo=False` | also `groups="document_knowledge.group_document_user"` on every `document_ids` column | Record rules filter, but the model ACL raises: `document.page` is readable only by Knowledge's `group_document_user` (`document_page/security/ir.model.access.csv:2`), which no management-system group implies. Without the group, the client's read of the pages' names raises. OCA's own Procedures tab carries the same prerequisite. On this instance the gate hides nothing: the **Central access to Documents** setting (`document_knowledge/models/res_config.py:11-12`) makes every internal user imply `group_ir_attachment_user`, which implies `group_document_user` (`document_knowledge/security/document_knowledge_security.xml:9-13`). It matters on instances where that setting is off |
| 3 | §3 gives `domain_kind` no default | `default="both"` | Matches the catalogs and profiles: a rule is unrestricted until someone narrows it |
| 4 | §7 says of generated actions that "users remain free to delete what they do not want", and D27's rationale calls duplicates "harmless and deletable" | generated actions cannot be deleted; the button asks for confirmation | No group may delete a `mgmtsystem.action` — `perm_unlink` is 0 for viewer, user, auditor and manager alike (`mgmtsystem_action/security/ir.model.access.csv:2-5`). An unwanted action can only be cancelled through its stage. D27 is kept — no deduplication — and the confirmation on the button is the guard against a misclick |
| 5 | §7 falls back to Corrective when a template has no `type_action` | such a template is skipped, and a notification after the click names it | A template left without a type may be deliberate — not meant for automatic use — and defaulting it would be a guess about the author's intent |
| 6 | The revised plan §3 gives the rule three conditions — defect code, object part, cause — and D29 requires at least one of the three | **four conditions**: origin joins them, and at least one of the four is required | Origin is where a nonconformity came from, and `qms_nonconformity` step 7 records it per analysis item, beside cause. A condition the engine cannot read from an item would have a different subject from the other three, which is what keeps the rule table one thing: *(any defect, any part, any cause, External Supplier) → procurement works with the supplier* is now expressible. `mgmtsystem.nonconformity.origin` is `_parent_store`, so a group origin matches every origin beneath it through the same `parent_path` walk, and it is exempt from the `domain_kind` check as cause is — it has no such field |

## Folder structure

```
qms_determination/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── qms_determination_rule.py                         # 1
│   ├── qms_nonconformity_response.py                     # 2
│   └── mgmtsystem_nonconformity.py                       # 2 (response_ids, Suggest Response), 3 (Generate Actions)
├── security/ir.model.access.csv                          # 1, 2
├── views/
│   ├── qms_determination_rule_views.xml                  # 1
│   └── mgmtsystem_nonconformity_views.xml                # 2, 3
├── tests/__init__.py, test_qms_determination_rule.py     # 1
│         test_qms_nonconformity_response.py              # 2
│         test_qms_generate_actions.py                    # 3
│         test_qms_determination_origin.py              # 4
└── readme/ DESCRIPTION.md                                # 1
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Determination` |
| `summary` | `Rules that suggest a response from nonconformity analysis` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_nonconformity`, `mgmtsystem_action_template`, `document_page_procedure`, `document_page_work_instruction` |
| `data` | `security/ir.model.access.csv`, `views/qms_determination_rule_views.xml`, `views/mgmtsystem_nonconformity_views.xml` (step 2) |
| `installable` | `True` |

The two `document_page_*` modules are declared because the `document_ids` domain names
the page types they add (`selection_add` in each `models/document_page.py`).

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qms_determination_rule`, `from . import qms_nonconformity_response`, `from . import mgmtsystem_nonconformity` (step 2) |

## Models

### `qms.determination.rule` — `models/qms_determination_rule.py`

`models.Model` · `_name = "qms.determination.rule"` · `_description = "Determination Rule"` · `_order = "sequence, id"`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `sequence` | Integer | `default=10`; display order only, no part in matching |
| `active` | Boolean | `default=True` |
| `domain_kind` | Selection | `[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")]`, `string="Domain"`, `required=True`, `default="both"` |
| `defect_code_id` | Many2one → `qms.defect.code` | `ondelete="restrict"`; condition, a group matches every code beneath it |
| `object_part_id` | Many2one → `qms.object.part` | `ondelete="restrict"`; condition |
| `cause_id` | Many2one → `mgmtsystem.nonconformity.cause` | `ondelete="restrict"`; condition |
| `origin_id` (step 4) | Many2one → `mgmtsystem.nonconformity.origin` | `ondelete="restrict"`; condition, a group matches every origin beneath it |
| `severity_id` | Many2one → `mgmtsystem.nonconformity.severity` | `ondelete="restrict"`, `string="Suggested Severity"`; output |
| `action_template_ids` | Many2many → `mgmtsystem.action.template` | `relation="qms_determination_rule_action_template_rel"`, `column1="rule_id"`, `column2="template_id"`, `string="Action Templates"`; output |
| `document_ids` | Many2many → `document.page` | `relation="qms_determination_rule_document_page_rel"`, `column1="rule_id"`, `column2="page_id"`, `string="Documents"`, `domain=[("mgmtsystem_page_type", "in", ("procedure", "work_instruction"))]`; output |

`ondelete="restrict"` on the three conditions: nothing a rule depends on can be
deleted under it. A defect code or object part is archived instead, as the catalogs
already require. A **cause cannot be archived** — `mgmtsystem.nonconformity.cause` has no
`active` field — so a cause a rule uses cannot be removed until the rule stops using it.
`set null` would be worse on both counts: on a cause-only rule it breaks `has_condition`,
and on any other rule it silently broadens it, so *Torn + Machine fault* would start
firing on every tear.

**SQL constraints**

| Name | Definition | Message |
|---|---|---|
| `has_condition` | `CHECK (defect_code_id IS NOT NULL OR object_part_id IS NOT NULL OR cause_id IS NOT NULL OR origin_id IS NOT NULL)` | `"A rule needs at least one condition: a defect code, an object part, a cause or an origin."` |

**Step 4 widens this constraint.** Odoo drops and recreates a CHECK whose definition changed, and every existing row satisfies the wider version by construction — the old one was stricter — so the upgrade needs no data work. A rule carrying only an origin is legal from that point on.

A SQL constraint rather than `@api.constrains`: a Python constraint runs only when one of
its declared fields is in the `create` or `write` values (`odoo/api.py:184-190`), so a
rule created with just a name would never be checked. The CHECK covers every row however
it was written — form, import, RPC, code — including a write that clears the last
condition.

**Constraints**

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_domain_kind` | `@api.constrains("domain_kind", "defect_code_id", "object_part_id")` | clash-only, as on `qms.catalog.profile`: a `qm` rule may not have a `pm` defect code or object part, and the reverse; `both` on either side is accepted. Cause is exempt — it has no `domain_kind` | `"'%(condition)s' (%(condition_kind)s) does not fit rule '%(rule)s' (%(rule_kind)s)."` |

**Matching** (step 2)

| Method | Decorator | Behaviour |
|---|---|---|
| `_self_and_ancestor_ids(record)` | `@api.model` | the ids in `record.parent_path`, the record's own id last; `[]` for an empty record |
| `_match_item(item)` | `@api.model` | `search` for rules where each condition is `in [False] + _self_and_ancestor_ids(item.<value>)`, for defect code, object part, cause and origin (step 4) |

Revised plan §5, with ancestors read from `parent_path` rather than a `parent_of` search
(divergence 1). The `search` is filtered by `active` only on the rules, which is right: an
archived rule stops matching. An empty item value gives `[False]`, which matches only rules
whose condition is also empty (`models.py:3190-3214` turns `False` in an `in` list into
`IS NULL`). Results come back in rule order, `sequence, id`.

### `qms.nonconformity.response` — `models/qms_nonconformity_response.py` (step 2)

`models.Model` · `_name = "qms.nonconformity.response"` · `_description = "Nonconformity Response"` · `_order = "nonconformity_id, id"`

`id` order is creation order, which Suggest Response produces item by item and rule by
rule; a line added by hand goes to the end.

| Field | Type | Attributes |
|---|---|---|
| `nonconformity_id` | Many2one → `mgmtsystem.nonconformity` | `required=True`, `ondelete="cascade"`, `index=True` |
| `item_id` | Many2one → `qms.nonconformity.item` | `ondelete="cascade"`, `readonly=True`; set by Suggest Response, empty on a line a person added |
| `rule_id` | Many2one → `qms.determination.rule` | `required=True`, `ondelete="restrict"`; readonly in the view once saved |
| `rule_defect_code_id` | Many2one | `related="rule_id.defect_code_id"`, `string="Rule Defect Code"` |
| `rule_object_part_id` | Many2one | `related="rule_id.object_part_id"`, `string="Rule Object Part"` |
| `rule_cause_id` | Many2one | `related="rule_id.cause_id"`, `string="Rule Cause"` |
| `rule_origin_id` (step 4) | Many2one | `related="rule_id.origin_id"`, `string="Rule Origin"` |
| `suggested_severity_id` | Many2one | `related="rule_id.severity_id"`, `string="Suggested Severity"` |
| `action_template_ids` | Many2many | `related="rule_id.action_template_ids"` |
| `document_ids` | Many2many | `related="rule_id.document_ids"`, **`related_sudo=False`** |

Every related field is readonly and not stored: a line is a pointer to a rule, not a copy
(revised plan §6), and editing the rule changes what every line shows — the O5 limitation,
accepted. `related_sudo=False` on `document_ids` computes it as the user, so
`Many2many.read` applies their record rules and pages they cannot read drop out
(`document_page_access_group`); the default `related_sudo=True` would hand them over.

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py` (step 2)

`_inherit = "mgmtsystem.nonconformity"`

| Field | Type | Attributes |
|---|---|---|
| `response_ids` | One2many → `qms.nonconformity.response` | inverse `nonconformity_id`, `string="Suggested Responses"` |

| Method | Behaviour |
|---|---|
| `action_suggest_response` | per nonconformity: unlink **every** `response_ids` line, manual ones included; then for each item, in item order, create one line per rule from `_match_item`, with `item_id` set. Item severities are not touched. With no items it only clears the lines |
| `action_generate_actions` (step 3) | for every response line — suggested or manual — and every template on its rule, create one `mgmtsystem.action` with the values below. A template with no `type_action` is skipped and its name collected, each once. No deduplication and no memory of earlier presses (D27). If anything was skipped, return a notification naming the skipped templates (below); otherwise return `True` |

**Notification when templates were skipped** (step 3)

| Key | Value |
|---|---|
| `type` | `"ir.actions.client"` |
| `tag` | `"display_notification"` |
| `params.type` | `"warning"` |
| `params.title` | `"Some action templates were skipped"` |
| `params.message` | `"No response type: %(names)s"`, the skipped template names joined with `", "` |
| `params.next` | `{"type": "ir.actions.client", "tag": "soft_reload"}` |

`display_notification` returns `params.next` once shown
(`odoo/addons/web/static/src/webclient/actions/client_actions.js:22-25`), and `soft_reload`
(`:96`) reloads the form so the actions that were created appear. The confirmation before
the click cannot list the skipped templates — a button's `confirm` is fixed text — so they
are reported after.

**Values for a generated action** (step 3)

| Action field | Value |
|---|---|
| `name` | the template's `name` — no `"NEW "` prefix |
| `type_action` | the template's `type_action`; a template without one is skipped, never defaulted |
| `description` | the template's `description` |
| `user_id` | the template's `user_id` |
| `tag_ids` | the template's `tag_ids` |
| `template_id` | the template |
| `nonconformity_ids` | this nonconformity |

These mirror `_onchange_template_id`
(`mgmtsystem_action_template/models/mgmtsystem_action.py:23`), which runs only when a
user changes the field in a form — never on a create from code. The method cites it in a
comment as the source to diff against on an OCA upgrade. The copy is required, not just
convenient: `name` and `type_action` are required on the action with no default
(`mgmtsystem_action/models/mgmtsystem_action.py:22`, `53-61`), so an action created with
only `template_id` would fail. `type_action` is optional on the template; a template without one is
skipped rather than given a guessed type. The `"NEW "` prefix is the
onchange marking a placeholder the user is about to overwrite; a generated action is a
finished record. The link is `mgmtsystem.action.nonconformity_ids`
(`mgmtsystem_nonconformity/models/mgmtsystem_action.py:13`), the inverse side of the
nonconformity's `action_ids`.

`item_id` renders through the item's `display_name`, *Torn · Sleeves*, which
`qms_nonconformity` provides (its step 4). Without it the column would read
`qms.nonconformity.item,12`, since the item has no name field.

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_qms_determination_rule_viewer` | `qms.determination.rule.viewer` | `model_qms_determination_rule` | `mgmtsystem.group_mgmtsystem_viewer` | 1 | 0 | 0 | 0 |
| `access_qms_determination_rule_user` | `qms.determination.rule.user` | `model_qms_determination_rule` | `mgmtsystem.group_mgmtsystem_user` | 1 | 0 | 0 | 0 |
| `access_qms_determination_rule_manager` | `qms.determination.rule.manager` | `model_qms_determination_rule` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |
| `access_qms_nonconformity_response_viewer` (step 2) | `qms.nonconformity.response.viewer` | `model_qms_nonconformity_response` | `mgmtsystem.group_mgmtsystem_viewer` | 1 | 0 | 0 | 0 |
| `access_qms_nonconformity_response_user` (step 2) | `qms.nonconformity.response.user` | `model_qms_nonconformity_response` | `mgmtsystem.group_mgmtsystem_user` | 1 | 1 | 1 | 1 |
| `access_qms_nonconformity_response_manager` (step 2) | `qms.nonconformity.response.manager` | `model_qms_nonconformity_response` | `mgmtsystem.group_mgmtsystem_manager` | 1 | 1 | 1 | 1 |

## Views — `views/qms_determination_rule_views.xml`

| XML id | Type | Content |
|---|---|---|
| `qms_determination_rule_view_list` | list | `sequence` (`widget="handle"`), `name`, `domain_kind`, `defect_code_id`, `object_part_id`, `cause_id`, `severity_id`, `active` (`column_invisible="True"`) |
| `qms_determination_rule_view_form` | form | see below |
| `qms_determination_rule_view_search` | search | fields `name`, `defect_code_id`, `object_part_id`, `cause_id`, `origin_id` (step 4); filter `archived`, `domain="[('active', '=', False)]"`; group by `domain_kind` |
| `qms_determination_rule_action` | action | `name`: `Determination Rules`, `res_model`: `qms.determination.rule`, `view_mode`: `list,form`, `search_view_id` |

**Form** `qms_determination_rule_view_form`

```
form
└── sheet
    ├── widget web_ribbon  title="Archived" bg_color="text-bg-danger" invisible="active"
    ├── field active  invisible="1"
    ├── group
    │   ├── group: name, domain_kind
    │   └── group: sequence
    ├── group name="conditions" string="When"
    │   └── defect_code_id, object_part_id, cause_id, origin_id (step 4) — each options="{'no_create': True}"
    └── group name="outputs" string="Suggest"
        ├── severity_id  options="{'no_create': True}"
        ├── action_template_ids  widget="many2many_tags"
        └── document_ids  widget="many2many_tags"  groups="document_knowledge.group_document_user"
```

The condition fields carry no dropdown filter: a rule may be keyed on a group or on a
code.

## Views — `views/mgmtsystem_nonconformity_views.xml` (step 2)

Inherits `mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_form`, after
`qms_nonconformity`'s own extension of it, which it depends on.

| Position | Content |
|---|---|
| field `stage_id` (in `<header>`) before | button `action_suggest_response`, `type="object"`, `string="Suggest Response"`, `invisible="state != 'analysis'"`, `groups="mgmtsystem.group_mgmtsystem_user"` |
| field `stage_id` (in `<header>`) before (step 3) | button `action_generate_actions`, `type="object"`, `string="Generate Actions"`, `confirm="Generate actions from the suggested responses?"`, `invisible="state != 'pending'"`, `groups="mgmtsystem.group_mgmtsystem_user"` |

The Action Plan state's value is `pending`, not `action_plan`
(`mgmtsystem_nonconformity_stage.py:18`). OCA's own Actions page is already editable only
in `pending`; the button uses `!=` rather than OCA's `state not in 'pending'`, which
matches substrings.
| `//group[@name='qms_code_scope']` after | separator "Suggested Responses", then `response_ids`, `readonly="state != 'analysis'"`, with the list below. Anchored on that group, which `qms_nonconformity` step 5 added, rather than on `item_ids`: the latter put these lines between the Analysis Items list and the switch governing its dropdowns |

**`response_ids` list**, `editable="bottom"`: `item_id` (readonly), `rule_id`
(`readonly="id"`, `options="{'no_create': True}"`), `rule_defect_code_id`,
`rule_object_part_id`, `rule_cause_id`, `rule_origin_id`, `suggested_severity_id`, `action_template_ids`
(`widget="many2many_tags"`), `document_ids` (`widget="many2many_tags"`,
`groups="document_knowledge.group_document_user"`).

The page then reads Analysis → Analysis Items → Suggested Responses → Analysis
Confirmation. The button is hidden outside `analysis` rather than disabled: rerunning
later means moving the stage back, which `stage_id`'s tracking already records (revised
plan §7).

## Menus — in `views/qms_determination_rule_views.xml`

| XML id | Name | Parent | Action | Groups | Sequence |
|---|---|---|---|---|---|
| `menu_qms_determination_rule` | `Determination Rules` | `mgmtsystem.menu_mgmtsystem_configuration` | `qms_determination_rule_action` | `mgmtsystem.group_mgmtsystem_manager` | 25 |

Sequence 25 places it directly after `qms_catalog`'s *Catalogs* (20).

## Tests — `tests/test_qms_determination_rule.py`

`TestDeterminationRule(TransactionCase)`, `at_install`: the fixtures create catalog
codes and causes only, no core records. Fixture codes use `unique_code_prefix()` from
`odoo.addons.qms_catalog.tests.common`.

| Test | Asserts |
|---|---|
| `test_rule_requires_condition` | creating a rule with only a name raises `IntegrityError` — the case `@api.constrains` would have missed — under `mute_logger("odoo.sql_db")` and a savepoint |
| `test_rule_clearing_last_condition` | a write that empties the only condition raises `IntegrityError` |
| `test_rule_cause_only_allowed` | a rule with only a cause is accepted |
| `test_domain_kind_clash_defect` | a `pm` rule on a `qm` defect code raises `ValidationError` |
| `test_domain_kind_clash_object_part` | a `qm` rule on a `pm` object part raises `ValidationError` |
| `test_domain_kind_both_accepted` | a `both` rule on a `qm` code, and a `qm` rule on a `both` code, are accepted |
| `test_domain_kind_rule_narrowed` | a `both` rule on a `pm` code, changed to `qm`, raises `ValidationError` — the only test covering `domain_kind` in the constraint's own trigger list |
| `test_condition_restrict` | deleting a defect code a rule uses raises `IntegrityError` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Determination rules map analysis — defect, object part, cause, origin — to a suggested response: a severity, action templates and documents. Every matching rule applies |

## Tests — `tests/test_qms_determination_origin.py` (step 4)

`TestDeterminationOrigin(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create nonconformities. Origins: a group *External* with a child *External Supplier*,
and an unrelated *Internal Audit*.

| Test | Asserts |
|---|---|
| `test_rule_origin_only_allowed` | a rule with only an origin is accepted — the widened `has_condition` |
| `test_matches_on_origin` | an item whose origin is *External Supplier* matches an origin-only rule, and an item with a different origin does not |
| `test_matches_origin_group` | a rule keyed on the *External* group matches an item carrying *External Supplier* |
| `test_item_without_origin_does_not_match` | an item with no origin matches no rule that asks for one, while rules leaving origin empty still match — the `[False]` rule applied to a fourth dimension |
| `test_four_conditions_together` | a rule setting all four conditions matches only the item that fits all four |
| `test_response_line_shows_rule_origin` | the line's `rule_origin_id` reads the rule's origin |
| `test_origin_restrict` | deleting an origin a rule uses raises `IntegrityError` |

## Tests — `tests/test_qms_nonconformity_response.py` (step 2)

`TestNonconformityResponse(TransactionCase)`, `@tagged("post_install", "-at_install")`:
the fixtures create nonconformities, a model later modules extend. Catalog codes use
`unique_code_prefix()`. Rules follow the revised plan's worked example: R1 *Torn +
Sleeves + Machine fault*, R2 *Torn + Incorrect operation*, R3 *Fabric Defect* (the group).

| Test | Asserts |
|---|---|
| `test_worked_example` | item *(Torn, Sleeves, Machine fault)* gets lines for R1 and R3, not R2 |
| `test_partial_item` | item *(Torn, —, —)* gets a line for R3 only |
| `test_two_items_same_rule` | two items matching R3 give two lines, one per `item_id` |
| `test_rerun_replaces_all_lines` | a manual line and the suggested lines are all replaced by a rerun, which regenerates the same suggestions |
| `test_no_items_clears_lines` | on a nonconformity with no items, the button leaves no lines |
| `test_item_severity_untouched` | an item's severity is the same before and after the button, even when a matching rule suggests another |
| `test_archived_group_still_matches` | with the *Fabric Defect* group archived, R3 still matches *Torn* — the case a `parent_of` search would miss |
| `test_archived_rule_not_matched` | an archived rule produces no line |
| `test_item_delete_cascades` | deleting an item deletes its lines and keeps a manual line |
| `test_rule_with_lines_restrict` | deleting a rule that has lines raises `IntegrityError` |

Not covered by a test: that `document_ids` hides pages the user cannot read. That depends
on `document_page_access_group`, which this module does not depend on, so it is checked in
the browser with a restricted page and a user outside its group.

## Tests — `tests/test_qms_generate_actions.py` (step 3)

`TestGenerateActions(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create nonconformities and actions. Two templates — *Typed*, with `type_action =
"prevention"`, a description, a responsible user and a tag; *Untyped*, with no
`type_action` — on a group-level rule, so every *Torn* item matches it.

| Test | Asserts |
|---|---|
| `test_one_action_per_typed_template` | one item gives one action, for *Typed*, in the nonconformity's `action_ids` |
| `test_copies_template_fields` | name, type, description, user, tags and `template_id` match *Typed*, and the name carries no `"NEW "` prefix |
| `test_untyped_template_skipped` | *Untyped* produces no action |
| `test_skipped_templates_notified` | the return value is a `display_notification` whose message names *Untyped* once, even across two lines |
| `test_nothing_skipped_returns_true` | with only typed templates, the button returns `True` |
| `test_manual_line_included` | a hand-added line's templates generate actions too |
| `test_two_lines_two_actions` | two items on the same rule give two actions for *Typed* — no deduplication |
| `test_generate_twice_generates_twice` | pressing again doubles the actions — D27, deliberate |
| `test_no_lines_no_actions` | a nonconformity with no response lines generates nothing |

