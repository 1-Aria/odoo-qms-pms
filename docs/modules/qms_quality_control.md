# qms_quality_control

Defect capture at inspection, Populate Defect, the action ↔ inspection link, and
nonconformity prefill from an inspection.
Plan: §7.10 (inspection rows), §7.11.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `qms_defect_code_id` on `qc.test.question.value`, shown on the question form | proposed | |
| 2 | Populate Defect on the nonconformity, visible in Analysis | — | |
| 3 | `mgmtsystem.action.inspection_id`, its inverse, smart buttons both ways | — | |
| 4 | Nonconformity prefill when created from an inspection | — | |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | §7.11 names the field on `qc.test.question.value` `defect_code_id` | `qms_defect_code_id` | Fields added to OCA models take the `qms_` prefix; a plain `defect_code_id` on a QC model is exactly the name a future OCA field could take |
| 2 | §7.11: Populate Defect creates "one `qms.nonconformity.item` per distinct defect" | one item per failed answer, in question order | Two answers pointing at the same defect are two findings; merging them would hide one. Question 1 → A, question 2 → A, question 3 → B gives two items for A and one for B |
| 3 | §7.11 does not say what a second press does | it deletes **every** item on the nonconformity, then repopulates | The same full-reset behaviour as Suggest Response (D30). Items entered by hand go too, and so do the response lines that pointed at the deleted items (`item_id` is `ondelete="cascade"` in `qms_determination`) |
| 4 | §7.11: "carrying the severity through" to the item | nothing to carry | `qms_nonconformity` derives an item's severity from its defect code in a stored compute (its step 3), for items created in code as well |
| 5 | §7.10 lists NC ↔ Inspection as existing, via the OCA bridge | confirmed: `qc_inspection_id` on the nonconformity, `mgmtsystem_nonconformity_ids` and a count on the inspection, and `action_view_nonconformities` (`mgmtsystem_nonconformity_quality_control_oca/models/`) | Only the prefill context remains to add, in step 4 |
| 6 | §7.11 adds `defect_severity_id`, the code's default severity shown beside it on the answer | omitted | The defect code is enough on a checklist; the severity is visible on the code itself, and the item takes it from there |

## Folder structure

```
qms_quality_control/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── qc_test_question_value.py                         # 1
│   ├── mgmtsystem_nonconformity.py                       # 2 (Populate Defect), 4
│   ├── mgmtsystem_action.py                              # 3
│   └── qc_inspection.py                                  # 3, 4
├── views/
│   ├── qc_test_views.xml                                 # 1
│   ├── mgmtsystem_nonconformity_views.xml                # 2
│   ├── mgmtsystem_action_views.xml                       # 3
│   └── qc_inspection_views.xml                           # 3, 4
├── tests/__init__.py, test_qms_quality_control.py        # 1
└── readme/ DESCRIPTION.md                                # 1
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Quality Control` |
| `summary` | `Defect codes on inspection answers, and nonconformity analysis from inspections` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_nonconformity`, `quality_control_oca`, `mgmtsystem_nonconformity_quality_control_oca`, `mgmtsystem_action` |
| `data` | `views/qc_test_views.xml` |
| `installable` | `True` |

No access file in step 1: the module adds fields to existing models, whose access rules
come from `quality_control_oca`.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qc_test_question_value` |

## Models

### `qc.test.question.value` — `models/qc_test_question_value.py`

`_inherit = "qc.test.question.value"`. OCA's model carries only `test_line`, `name` and
`ok` ("Correct answer?") — `quality_control_oca/models/qc_test.py:104-112`.

| Field | Type | Attributes |
|---|---|---|
| `qms_defect_code_id` | Many2one → `qms.defect.code` | `string="Defect Code"`, `ondelete="restrict"`, `help="The defect this answer records when it is given."` |

`ondelete="restrict"`, as elsewhere: a defect code a checklist uses is archived, not
deleted.

## Views — `views/qc_test_views.xml`

Inherits `quality_control_oca.qc_test_question_form_view`. Answers are edited in the
question form; the test form shows them only as a column.

| Position | Content |
|---|---|
| field `ok` inside the `ql_values` list, after | `qms_defect_code_id` (`options="{'no_create': True}"`) |

The code carries no dropdown filter: a checklist is written per test, not per product, so
there is no profile to scope by.

## Tests — `tests/test_qms_quality_control.py`

`TestAnswerDefectCode(TransactionCase)`, `at_install`: the fixtures create catalog codes and QC
test records, no core records. Codes use `unique_code_prefix()` from
`odoo.addons.qms_catalog.tests.common`.

| Test | Asserts |
|---|---|
| `test_answer_takes_defect_code` | an answer value holds its defect code |
| `test_defect_code_restrict` | deleting a defect code an answer uses raises `IntegrityError` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Records which defect a failed inspection answer represents, so a nonconformity raised from the inspection can be analysed from it |
