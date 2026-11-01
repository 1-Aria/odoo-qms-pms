# l10n_vn_payroll

Vietnamese payroll on OCA `payroll`: pay components with their SI, OT and PIT treatment, salary and
productivity scales, dated pay lines on contracts, contribution profiles, monthly inputs, the pay
context that calculates every payslip, checks, the run workflow and lock, the payslip and the
statutory statements. Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.3.md` (PTD-xx),
on `Payroll Requirements Specification v0.5.md` (FR-xx) and `Pay Policy v0.5.md`. Base module:
`docs/modules/base_time_parameter_strict.md`. Posting, the bank file and advances are
`l10n_vn_payroll_account`; the garment company's configuration is `l10n_vn_payroll_garment`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Components, scales, contract pay lines and the wage they set; payroll groups, the officer record rule, the new-user template, the parameter group for payroll managers; statutory parameters per Vietnamese company; configuration views and menus | planned | |
| 2 | Participant types; contract fields (participant type, declared SI base, probation form); employee fields; dependents on `hr_employee_relative` | planned | |
| 3 | Periods; monthly inputs with segments and entered lines; the Excel import template; entry lists for supervisors and managers | planned | |
| 4 | Calculation I: payslip contract choice, worked days from inputs, the pay context, component lines, OT, the `l10n_vn_component` rule type, exact lines, the snapshot | planned | |
| 5 | Calculation II: SI, HI, UI and union; PIT; damage compensation; the advance hook for `l10n_vn_payroll_account` | planned | |
| 6 | Checks: catalogue, levels from parameters, results | planned | |
| 7 | Runs: states, segregation, the lock, corrections, off-cycle runs; payslip access for approvers and readers | planned | |
| 8 | The bilingual payslip report | planned | |
| 9 | Statutory statements and opening data | planned | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §1, §4.2: statutory parameters ship with no company | created for every company whose country is Vietnam, and kept up to date at every install and upgrade (D9) | OCA's global rule on parameters, `[('company_id', 'in', company_ids)]` (`oca/server-tools/base_time_parameter/security/security.xml:6-13`), matches no parameter without a company, so they would show on no screen (`base_time_parameter_strict` divergence 1) |
| 2 | §3.2: officers, reviewers and readers read parameters | only payroll managers see parameters, through OCA's *Manage Time Parameters* group, which their group now implies (D7) | The calculation reads parameters as superuser (`base_time_parameter_strict` D1), so other roles need no access; the design's convention of not granting another module's models through `ir.model.access` rows is kept |
| 3 | §7: `wage` follows "the base salary line" | follows the lines whose component has `sets_wage` (D5) | The design names no field that marks the base salary component |
| 4 | §3.2: approver and reader read payslips | in step 7, with the run workflow | Their access is tested where they use it, approving and reading runs |

## Decisions

| # | Decision |
|---|---|
| D1 | **Naming** (PTD-01): models `l10n_vn.payroll.*`, fields on core and OCA models `l10n_vn_*`, parameter codes `vn.*` |
| D2 | **A component's amount source decides what its pay lines hold** (PTD-04): `line` → `amount`; `parameter` → the parameter `amount_parameter` on the date; `scale` → the cell `scale_key` of the version in force, unless the line has an `amount`; `scale_remainder` → that cell (or `amount`) minus the line amounts flagged `in_cell` on the same contract on the date. Components with source `entered`, `ie_units`, `ot` or `engine` never sit on a contract |
| D3 | **Configuration rules are checked when a component is saved** (design §5.3), so a run never meets a half-configured component. The checks are one `@api.constrains` on the required fields `kind` and `amount_source` among others, so they also run at creation |
| D4 | **A line's amount on a date is one method,** `_l10n_vn_amount_on(date)`, used by the wage and later by the pay context |
| D5 | **`wage` = the sum of the lines in force today whose component has `sets_wage`,** written after every change to a contract's lines. When an amount cannot be read (a parameter not configured yet), `wage` is left as it is and the reason is logged: setting up lines never fails because of `wage`. Payroll never reads `wage` |
| D6 | **Pay lines do not overlap:** two lines of one component on one contract cannot share a day, and two `scale_remainder` lines of one scale cannot either. A change is a new line, the old one ended the day before (design §7) |
| D7 | **Groups** (design §3.1): reviewer (implies officer), approver and reader (each implies internal user), in OCA's *Payroll* category. `payroll.group_payroll_manager` gains `base_time_parameter.group_time_parameter` |
| D8 | **New users get no payroll group** (PFG-10): `base.default_user` loses `payroll.group_payroll_user` and `payroll.group_payroll_manager`, in a `noupdate` record. Odoo's template also carries every app's top groups (on the instance: HR, contracts, accounting, stock, purchase and more); those stay as they are |
| D9 | **Statutory parameters per Vietnamese company:** the table `STATUTORY_PARAMETERS` in `models/res_company.py` holds each code, name, type and dated versions. `res.company._l10n_vn_payroll_ensure_parameters()` creates, for every company with country `VN`, each missing parameter and each missing version (by `date_from`); it never changes an existing version, so edits made in the UI stay. A data `<function>` runs it at every install and upgrade, so a new company or a new statutory version arrives with the next upgrade. Each company is processed in a savepoint; a failure is logged and the install continues (safe to fail) |
| D10 | **Officers see every payslip of their companies:** a rule for `payroll.group_payroll_user` with domain `[(1, '=', 1)]` on `hr.payslip`. Rules of a user's groups combine with OR, so OCA's narrower officer rule (`oca/payroll/payroll/security/hr_payroll_security.xml:28-36`) no longer limits them; OCA's global company rule still applies |
| D11 | **Pay lines are visible only to payroll groups:** `l10n_vn_line_ids` on the contract carries `groups="payroll.group_payroll_user"`, and the page that shows it the same |

## Folder structure

```
l10n_vn_payroll/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_payroll_component.py
│   ├── l10n_vn_payroll_scale.py
│   ├── l10n_vn_payroll_contract_line.py
│   ├── hr_contract.py
│   └── res_company.py
├── data/
│   └── l10n_vn_payroll_parameters.xml
├── security/
│   ├── l10n_vn_payroll_security.xml
│   └── ir.model.access.csv
├── views/
│   ├── l10n_vn_payroll_component_views.xml
│   ├── l10n_vn_payroll_scale_views.xml
│   ├── hr_contract_views.xml
│   └── menus.xml
├── tests/
│   ├── __init__.py, common.py
│   ├── test_component.py
│   ├── test_scale.py
│   ├── test_contract_line.py
│   ├── test_statutory_parameters.py
│   └── test_security.py
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

Files of later steps are added to this tree with their step.

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Payroll` |
| `summary` | `Vietnamese payroll on OCA payroll: pay components, scales and dated pay lines, SI, OT and PIT, statutory parameters` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Human Resources/Payroll` |
| `countries` | `["vn"]` |
| `depends` | `payroll`, `base_time_parameter_strict` (step 1); `hr_employee_relative` (step 2); `excel_import_export` (step 3) |
| `data` | `security/l10n_vn_payroll_security.xml`, `security/ir.model.access.csv`, `data/l10n_vn_payroll_parameters.xml`, `views/l10n_vn_payroll_component_views.xml`, `views/l10n_vn_payroll_scale_views.xml`, `views/hr_contract_views.xml`, `views/menus.xml` |
| `installable` | `True` |

The security file loads first: the access file names its groups.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import l10n_vn_payroll_component`, `from . import l10n_vn_payroll_scale`, `from . import l10n_vn_payroll_contract_line`, `from . import hr_contract`, `from . import res_company` |
| `tests/__init__.py` | `from . import test_component`, `from . import test_scale`, `from . import test_contract_line`, `from . import test_statutory_parameters`, `from . import test_security` |

## Groups and rules — `security/l10n_vn_payroll_security.xml`

| XML id | Model | Content |
|---|---|---|
| `group_payroll_reviewer` | `res.groups` | *Reviewer*; category `payroll.module_category_payroll`; implies `payroll.group_payroll_user` |
| `group_payroll_approver` | `res.groups` | *Approver*; category as above; implies `base.group_user` |
| `group_payroll_reader` | `res.groups` | *Reader*; category as above; implies `base.group_user` |
| `payroll.group_payroll_manager` | `res.groups` | `implied_ids`: `Command.link(ref('base_time_parameter.group_time_parameter'))` (D7) |
| `base.default_user` | `res.users` | in a `noupdate="1"` block: `groups_id`: `Command.unlink` of `payroll.group_payroll_manager` and `payroll.group_payroll_user` (D8) |
| `rule_payslip_officer_all` | `ir.rule` | `hr.payslip`; groups `payroll.group_payroll_user`; domain `[(1, '=', 1)]` (D10) |
| `rule_component_company` | `ir.rule` | `l10n_vn.payroll.component`; global; `[('company_id', 'in', company_ids)]` |
| `rule_scale_company` | `ir.rule` | `l10n_vn.payroll.scale`; global; the same |
| `rule_scale_version_company` | `ir.rule` | `l10n_vn.payroll.scale.version`; global; the same |
| `rule_scale_cell_company` | `ir.rule` | `l10n_vn.payroll.scale.cell`; global; the same |
| `rule_contract_line_company` | `ir.rule` | `l10n_vn.payroll.contract.line`; global; the same |

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_component_user` | `model_l10n_vn_payroll_component` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_component_reader` | `model_l10n_vn_payroll_component` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_component_manager` | `model_l10n_vn_payroll_component` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_user` | `model_l10n_vn_payroll_scale` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_manager` | `model_l10n_vn_payroll_scale` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_version_user` | `model_l10n_vn_payroll_scale_version` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_version_manager` | `model_l10n_vn_payroll_scale_version` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_cell_user` | `model_l10n_vn_payroll_scale_cell` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_cell_manager` | `model_l10n_vn_payroll_scale_cell` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_contract_line_user` | `model_l10n_vn_payroll_contract_line` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |

The reviewer and the manager reach these through the officer group they imply.

## Models

### `l10n_vn.payroll.component` — `models/l10n_vn_payroll_component.py`

`_name = "l10n_vn.payroll.component"`, `_description = "Payroll Component"`, `_order = "sequence, code"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `sequence` | Integer | default 10 |
| `active` | Boolean | default True |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `kind` | Selection | required, default `earning`: `earning` *Earning*, `deduction` *Deduction*, `employer` *Employer contribution*, `total` *Total*, `info` *Information* |
| `legal_nature` | Selection | required: `job_salary` *Salary by job*, `fixed_allowance` *Fixed allowance*, `fixed_supplement` *Fixed supplement*, `variable_salary` *Variable salary*, `bonus` *Bonus (Art. 104)*, `welfare` *Welfare support*, `overtime` *Overtime*, `night` *Night work*, `leave_pay` *Leave pay*, `severance` *Severance*, `statutory` *Statutory contribution or tax*, `union` *Union*, `damage` *Damage compensation*, `advance` *Advance*, `adjustment` *Adjustment*, `total` *Total* |
| `in_si_base` | Boolean | string *In SI base* |
| `in_ot_base` | Boolean | string *In OT base* |
| `pit_treatment` | Selection | `taxable` *Taxable*, `exempt` *Exempt*, `exempt_cap` *Exempt up to a cap*, `excluded` *Excluded*, `ot` *Exempt within the OT limits* |
| `pit_cap_parameter` | Char | parameter code of the cap |
| `amount_source` | Selection | required: `line` *Amount on the pay line*, `parameter` *Parameter*, `scale` *Scale cell*, `scale_remainder` *Remainder of a scale cell*, `entered` *Entered each month*, `ie_units` *IE units × unit rate*, `ot` *Per OT hour*, `engine` *Calculated* |
| `amount_parameter` | Char | parameter code (`parameter`; and the per-hour amount of a supplement, `ot` with `ot_category = all`) |
| `scale_id` | Many2one `l10n_vn.payroll.scale` | `ondelete="restrict"`, `check_company=True` |
| `proration` | Selection | `paid_days` *Paid days*, `days_worked` *Days worked*, `none` *Not prorated*, `per_day` *Daily rate × paid days* |
| `probation_applies` | Boolean | |
| `variable` | Boolean | |
| `attainment_source` | Selection | `supervisor`, `manager`, `ie` |
| `condition` | Selection | required, default `none`: `none`, `attendance` |
| `ot_category` | Selection | `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL`, `all` |
| `engine_code` | Selection | `GROSS`, `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT`, `DAMAGE`, `NET`, `ADVANCE`, `TO_PAY`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE` |
| `section` | Selection | required, default `salary`: `salary`, `ot`, `bonus`, `other`, `deduction`, `employer`, `total` |
| `register_id` | Many2one `hr.contribution.register` | `ondelete="restrict"` |
| `sets_wage` | Boolean | string *Sets the contract wage* (D5) |
| `legal_reference` | Char | |
| `note` | Text | |

**SQL constraint:** `code_company_unique`: `unique(code, company_id)`.

**`_check_configuration`** — `@api.constrains("kind", "amount_source", "scale_id", "amount_parameter", "engine_code", "ot_category", "proration", "pit_treatment", "pit_cap_parameter", "variable", "attainment_source")`, raising `ValidationError` naming the component and the rule:

| Rule |
|---|
| `scale` and `scale_remainder` need `scale_id`; other sources have none |
| `parameter` needs `amount_parameter`; `ot` with `ot_category = all` needs it too |
| `engine` needs `engine_code`; other sources have none |
| `ot` needs `ot_category` and `kind = earning` |
| `kind = earning` needs `pit_treatment`; with a source other than `ot` and `engine`, also `proration` |
| `pit_treatment = exempt_cap` needs `pit_cap_parameter` |
| `variable` only with `kind = earning`, and needs `attainment_source` |
| `per_day` proration only with source `line` |

### `l10n_vn.payroll.scale`, `.scale.version`, `.scale.cell` — `models/l10n_vn_payroll_scale.py`

**`l10n_vn.payroll.scale`** — `_description = "Payroll Scale"`, `_order = "code"`

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `kind` | Selection | required: `grade_step` *Grade and step*, `level` *Level* |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `version_ids` | One2many `l10n_vn.payroll.scale.version` | `scale_id` |

SQL: `code_company_unique`: `unique(code, company_id)`.

| Method | Behaviour |
|---|---|
| `_version_on(date)` | the version with the latest `date_from ≤ date`, or an empty recordset |
| `_cell_amount(key, date)` | the `amount` of the cell `key` in `_version_on(date)`; raises `UserError` when there is no version on the date (*Scale %(scale)s has no version on %(date)s.*) or no such cell (*Scale %(scale)s has no cell %(key)s on %(date)s.*) |
| `_has_key(key)` | True when any version holds the cell `key` |

**`l10n_vn.payroll.scale.version`** — `_description = "Payroll Scale Version"`, `_order = "scale_id, date_from desc"`, `_rec_name = "date_from"`

| Field | Type | Attributes |
|---|---|---|
| `scale_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `scale_id.company_id`, stored |
| `date_from` | Date | required |
| `note` | Char | |
| `cell_ids` | One2many `l10n_vn.payroll.scale.cell` | `version_id`, `copy=True` |

SQL: `scale_date_unique`: `unique(scale_id, date_from)`.

**`l10n_vn.payroll.scale.cell`** — `_description = "Payroll Scale Cell"`, `_order = "version_id, key"`

| Field | Type | Attributes |
|---|---|---|
| `version_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `version_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `key` | Char | required (`G2-2`, `S4`) |
| `grade` | Char | |
| `step` | Integer | |
| `amount` | Monetary | required |

SQL: `version_key_unique`: `unique(version_id, key)`.

### `l10n_vn.payroll.contract.line` — `models/l10n_vn_payroll_contract_line.py`

`_description = "Contract Pay Line"`, `_order = "contract_id, date_from, component_id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `contract_id` | Many2one `hr.contract` | required, `ondelete="cascade"`, index |
| `employee_id` | Many2one | related `contract_id.employee_id`, stored |
| `company_id` | Many2one | related `contract_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `component_id` | Many2one `l10n_vn.payroll.component` | required, `ondelete="restrict"`, domain `[('amount_source', 'in', ('line', 'parameter', 'scale', 'scale_remainder'))]`, `check_company=True` |
| `amount_source` | Selection | related `component_id.amount_source` |
| `amount` | Monetary | for `line`; for `scale` and `scale_remainder`, overrides the cell |
| `scale_key` | Char | |
| `in_cell` | Boolean | string *Part of the scale cell* |
| `date_from` | Date | required |
| `date_to` | Date | empty = until the contract ends |
| `granted_by` | Many2one `res.users` | |
| `review_date` | Date | |
| `note` | Char | |

**Default:** `date_from` from the context key `default_contract_id`'s `date_start` when given (the contract form's list), else today.

**`_check_line`** — `@api.constrains("contract_id", "component_id", "date_from", "date_to", "amount", "scale_key")`, `ValidationError`:

| Rule |
|---|
| `date_from ≥ contract.date_start`; `date_to ≥ date_from` when set; when the contract has `date_end`, `date_from ≤ date_end` and `date_to ≤ date_end` |
| source `line`: `amount` set and not 0 |
| sources `scale`, `scale_remainder`: `scale_key` or `amount`; a `scale_key` must be found by the component's scale's `_has_key` |
| no other line of the same contract and component overlaps (D6) |
| no other line of the same contract with a `scale_remainder` component on the same scale overlaps (D6) |

Two lines overlap when `a.date_from ≤ (b.date_to or max)` and `b.date_from ≤ (a.date_to or max)`.

| Method | Behaviour |
|---|---|
| `_l10n_vn_in_force(date)` | lines of `self` with `date_from ≤ date` and (`date_to` empty or `≥ date`) |
| `_l10n_vn_amount_on(date)` | one line's amount on `date` (D2): `line` → `amount`; `parameter` → `base.time.parameter._strict_get(component.amount_parameter, date, company)`; `scale` → `amount` or `scale_id._cell_amount(scale_key, date)`; `scale_remainder` → (`amount` or the cell) − the sum of `_l10n_vn_amount_on(date)` over the contract's lines in force on `date` with `in_cell` |
| `create`, `write`, `unlink` | after the change, `contract_id._l10n_vn_sync_wage()` on the contracts touched (for `unlink`, read before deleting) |

### `hr.contract` — `models/hr_contract.py`

`_inherit = "hr.contract"`.

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_line_ids` | One2many `l10n_vn.payroll.contract.line` | `contract_id`, string *Pay Lines*, `groups="payroll.group_payroll_user"`, `copy=True` |

| Method | Behaviour |
|---|---|
| `_l10n_vn_sync_wage()` | per contract, as superuser: today = `fields.Date.context_today(contract)`; lines = `l10n_vn_line_ids._l10n_vn_in_force(today)` with `component_id.sets_wage`; none → nothing. Otherwise the sum of `_l10n_vn_amount_on(today)`; a `UserError` while reading is caught, logged at `info` with the contract and the message, and `wage` left as it is (D5). Writes `wage` only when it differs |
| `_check_l10n_vn_line_dates` | `@api.constrains("date_start", "date_end")`: runs the lines' `_check_line` again, so a contract cannot be shortened past its lines |

### `res.company` — `models/res_company.py`

`_inherit = "res.company"`.

**`STATUTORY_PARAMETERS`**, a module-level list of `(code, name, type, versions)`, `versions` a list of `(date_from, value)` with the value as stored text:

| Code | Name | Type | Versions |
|---|---|---|---|
| `vn.min_wage.month` | Regional minimum wage, monthly | json | 2026-01-01 `{"I": 5310000, "II": 4730000, "III": 4140000, "IV": 3700000}` |
| `vn.min_wage.hour` | Regional minimum wage, hourly | json | 2026-01-01 `{"I": 25500, "II": 22700, "III": 19900, "IV": 17800}` |
| `vn.si.reference_level` | SI reference level | float | 2024-07-01 `2340000`; 2026-07-01 `2530000` |
| `vn.si.cap_multiple` | SI and HI cap, multiple of the reference level | float | 2026-01-01 `20` |
| `vn.ui.cap_multiple` | UI cap, multiple of the regional minimum wage | float | 2026-01-01 `20` |
| `vn.rate.ee.si` | Employee SI rate | float | 2026-01-01 `0.08` |
| `vn.rate.ee.hi` | Employee HI rate | float | 2026-01-01 `0.015` |
| `vn.rate.ee.ui` | Employee UI rate | float | 2026-01-01 `0.01` |
| `vn.rate.er.pension` | Employer pension and survivorship rate | float | 2026-01-01 `0.14` |
| `vn.rate.er.sickness` | Employer sickness and maternity rate | float | 2026-01-01 `0.03` |
| `vn.rate.er.accident` | Employer occupational accident rate | float | 2026-01-01 `0.005` |
| `vn.rate.er.hi` | Employer HI rate | float | 2026-01-01 `0.03` |
| `vn.rate.er.ui` | Employer UI rate | float | 2026-01-01 `0.01` |
| `vn.rate.union_fee` | Employer union fee rate | float | 2026-01-01 `0.02` |
| `vn.rate.union_dues` | Union dues rate, members | float | 2026-01-01 `0.005` |
| `vn.union_dues.cap` | Union dues cap | float | 2026-01-01 `253000` |
| `vn.si.absence_days` | Working days without work or pay that suspend contributions | integer | 2026-01-01 `14` |
| `vn.pit.self` | PIT personal deduction | float | 2026-01-01 `15500000` |
| `vn.pit.dependent` | PIT deduction per dependent | float | 2026-01-01 `6200000` |
| `vn.pit.brackets` | PIT monthly brackets | json | 2026-01-01 `[[10000000, 0.05], [30000000, 0.10], [60000000, 0.20], [100000000, 0.30], [null, 0.35]]` |
| `vn.pit.flat_short` | PIT flat rate, contracts under 3 months | float | 2026-01-01 `0.10` |
| `vn.pit.flat_short_threshold` | PIT flat rate threshold per payment | float | 2026-01-01 `5000000` |
| `vn.pit.nonresident` | PIT rate, non-residents | float | 2026-01-01 `0.20` |
| `vn.pit.meal_cap` | PIT-free cash meal allowance | float | 2026-01-01 `730000`; 2026-07-01 `1200000` |
| `vn.ot.factors` | OT and night factors | json | 2026-01-01 `{"WD": 1.5, "RD": 2.0, "HOL": 3.0, "NIGHT": 0.3, "NWD": 2.0, "NWD_AFTER": 2.1, "NRD": 2.7, "NHOL": 3.9}` |
| `vn.ot.limit.month` | OT hours limit per month | integer | 2026-01-01 `40` |
| `vn.ot.limit.year` | OT hours limit per year, textile and garment | integer | 2026-01-01 `300` |
| `vn.damage.cap` | Damage compensation cap, share of pay after insurance and PIT | float | 2026-01-01 `0.30` |
| `vn.probation.min_rate` | Minimum probation pay rate | float | 2026-01-01 `0.85` |
| `vn.probation.max_days` | Maximum probation by job | json | 2026-01-01 `{"manager": 180, "college": 60, "vocational": 30, "other": 6}` (`other` in working days) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_payroll_ensure_parameters()` | for each company in `self` with `country_id.code == "VN"`, as superuser, inside `self.env.cr.savepoint()`: for each entry, the parameter with that `code` and `company_id` is found or created (`name`, `code`, `type`, `company_id`, `country_id` the company's country); each version whose `date_from` the parameter lacks is created. Existing versions are not touched. An exception is logged at `warning` with the company and the code, and the next company continues (D9) |
| `_l10n_vn_payroll_ensure_parameters_all()` | `@api.model`: calls the above on every company |

## Data — `data/l10n_vn_payroll_parameters.xml`

`<function model="res.company" name="_l10n_vn_payroll_ensure_parameters_all"/>`, not in a `noupdate` block, so it runs at every install and upgrade (D9).

## Views

### `views/l10n_vn_payroll_component_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_component_view_list` | list | `sequence` (handle), `code`, `name`, `kind`, `legal_nature`, `amount_source`, `in_si_base`, `in_ot_base`, `pit_treatment`, `proration`, `variable`, `company_id` (multi-company group), `active` (hidden) |
| `l10n_vn_payroll_component_view_form` | form | title `code` and `name`; groups *Treatment* (`kind`, `legal_nature`, `in_si_base`, `in_ot_base`, `pit_treatment`, `pit_cap_parameter` visible when `pit_treatment == 'exempt_cap'`), *Amount* (`amount_source`, `amount_parameter` visible when `amount_source in ('parameter', 'ot')`, `scale_id` visible when `amount_source in ('scale', 'scale_remainder')`, `proration`, `probation_applies`, `variable`, `attainment_source` visible when `variable`, `condition`, `ot_category` visible when `amount_source == 'ot'`, `engine_code` visible when `amount_source == 'engine'`), *Payslip and posting* (`section`, `sequence`, `register_id`, `sets_wage`), *Legal* (`legal_reference`, `note`); `company_id`, `active` |
| `l10n_vn_payroll_component_view_search` | search | `code`, `name`; filters by `kind`, *Variable*, *Archived*; group by `kind`, `legal_nature`, `amount_source` |
| `l10n_vn_payroll_component_action` | action | *Pay Components*, list, form |

### `views/l10n_vn_payroll_scale_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_scale_view_list` | list | `code`, `name`, `kind`, `company_id` |
| `l10n_vn_payroll_scale_view_form` | form | `code`, `name`, `kind`, `company_id`; `version_ids` as a list (`date_from`, `note`) opening the version form |
| `l10n_vn_payroll_scale_version_view_form` | form | `scale_id` (read-only), `date_from`, `note`; `cell_ids` as an editable list (`key`, `grade`, `step`, `amount`) |
| `l10n_vn_payroll_scale_action` | action | *Pay Scales*, list, form |

### `views/hr_contract_views.xml`

| XML id | Inherits | Content |
|---|---|---|
| `hr_contract_view_form_l10n_vn_payroll` | `hr_contract.hr_contract_view_form` | after the page `information`, a page *Pay Lines* (`name="l10n_vn_pay_lines"`, `groups="payroll.group_payroll_user"`) with `l10n_vn_line_ids` as an editable list: `component_id`, `scale_key`, `amount`, `in_cell`, `date_from`, `date_to`, `granted_by` (optional), `review_date` (optional), `note` (optional); the list's context sets `default_contract_id` |

### `views/menus.xml`

Under `payroll.payroll_menu_configuration` (*Payroll → Configuration*, payroll managers):

| XML id | Name | Action | Sequence |
|---|---|---|---|
| `menu_l10n_vn_payroll_component` | Pay Components | `l10n_vn_payroll_component_action` | 30 |
| `menu_l10n_vn_payroll_scale` | Pay Scales | `l10n_vn_payroll_scale_action` | 31 |
| `menu_l10n_vn_payroll_parameter` | Time Parameters | `base_time_parameter.base_time_parameter_action` | 32 |

## Tests

All classes derive from `PayrollCase(TransactionCase)` in `tests/common.py`, which holds no test methods, and are `@tagged("post_install", "-at_install")`: the fixtures create a company, employees and users, core records later modules extend. No import from any core `tests` package.

**Fixtures** (`setUpClass`): `company` — a new `res.company` with `country_id` `base.vn`, `currency_id` `base.VND`, added to the env's `allowed_company_ids`; `calendar` — the company's `resource_calendar_id`; `department`; `employee` in that company and department; `contract` — `hr.contract` for `employee`, `date_start` 2026-01-01, `wage` 1, `resource_calendar_id` `calendar`, state `open`. Codes are prefixed `TEST_`. **Helpers:** `_component(code, **values)` creates a component in `company` with `kind` `earning`, `legal_nature` `job_salary`, `pit_treatment` `taxable`, `proration` `paid_days`, `amount_source` `line` unless given; `_scale(code, kind, versions)` creates a scale with versions from `{date_from: {key: amount}}`; `_line(component, **values)` creates a pay line on `contract`; `_parameter(code, versions)` creates a float `base.time.parameter` in `company`; `_user(login, groups)` creates an internal user in `company` with the groups' XML ids.

### `tests/test_component.py` — `TestComponent(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_scale_source_needs_scale` | `amount_source = scale` without `scale_id` raises `ValidationError` |
| `test_engine_needs_code` | `engine` without `engine_code` raises; `line` with an `engine_code` raises |
| `test_ot_needs_category` | `ot` without `ot_category` raises; `ot_category = all` without `amount_parameter` raises |
| `test_earning_needs_treatment` | an earning with source `line` and no `proration` raises; with no `pit_treatment` raises |
| `test_variable_needs_source` | `variable` without `attainment_source` raises; `variable` on a deduction raises |
| `test_exempt_cap_needs_parameter` | `exempt_cap` without `pit_cap_parameter` raises |
| `test_code_unique_per_company` | a second component with the same code in `company` raises; in another company it is accepted |
| `test_valid_examples` | `BASE` (parameter), `PROD` (scale, variable, supervisor), `PERF` (scale_remainder), `OT_WD` (ot, `WD`), `PIT` (engine) are created without error |

### `tests/test_scale.py` — `TestScale(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_cell_by_date` | versions 2026-01-01 `{S4: 2800000}` and 2027-01-01 `{S4: 3000000}`: 2026-12-31 → 2,800,000; 2027-01-01 → 3,000,000 |
| `test_missing_cell_raises` | key `S9` raises `UserError`; a date before the first version raises `UserError` |
| `test_has_key` | `S4` True; `S9` False |
| `test_unique_version_date` | a second version on the same date raises |

### `tests/test_contract_line.py` — `TestContractLine(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_line_inside_contract` | `date_from` before `date_start` raises; with `date_end` set, `date_to` after it raises |
| `test_line_amount_required` | source `line` with no amount raises |
| `test_scale_key_checked` | a `scale` line with key `S9`, absent from the scale, raises |
| `test_no_overlap` | two lines of one component from 2026-01-01 and 2026-06-01, the first open-ended, raise; with the first ended 2026-05-31, accepted |
| `test_one_remainder_per_scale` | two different `scale_remainder` components on one scale, overlapping, raise |
| `test_amounts_by_source` | parameter `TEST.base` 3,700,000: `BASE` line → 3,700,000; `PROD` at `S4` → 2,800,000; `PROD` with `amount` 3,000,000 → 3,000,000 |
| `test_remainder` | grade scale `G2-2` = 8,000,000; `BASE` (parameter 3,700,000, `in_cell`) and `PERF` at `G2-2` → `PERF` 4,300,000; `PERF` with `amount` 45,000,000 (G6) → 41,300,000 |
| `test_wage_follows_lines` | `BASE` with `sets_wage` from 2026-01-01 → `contract.wage` 3,700,000; a new `BASE` line from tomorrow, the old one ended today → still 3,700,000 today; deleting all lines leaves `wage` unchanged |
| `test_wage_safe_without_parameter` | a `sets_wage` component on a parameter code with no parameter: the line is created, `wage` keeps its value, no error |
| `test_contract_shortened_past_lines` | a line to 2026-12-31; setting the contract's `date_end` to 2026-06-30 raises |

### `tests/test_statutory_parameters.py` — `TestStatutoryParameters(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_created_for_vietnamese_company` | after `_l10n_vn_payroll_ensure_parameters()` on `company`: every code of `STATUTORY_PARAMETERS` exists in `company` with all its versions; `_strict_get("vn.si.reference_level", 2026-06-30, company)` → 2,340,000 and on 2026-07-01 → 2,530,000; `vn.pit.brackets` reads as a list of five pairs |
| `test_idempotent_and_keeps_edits` | after editing the 2026-01-01 version of `vn.rate.ee.si` to `0.09` and running again: no new parameter or version, the value still `0.09` |
| `test_missing_version_added` | after deleting the 2026-07-01 version of `vn.si.reference_level` and running again: it is back with `2530000` |
| `test_not_for_other_countries` | a company with `country_id` `base.fr` gets no `vn.*` parameter |

### `tests/test_security.py` — `TestSecurity(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_new_user_template` | `base.default_user` has neither `payroll.group_payroll_user` nor `payroll.group_payroll_manager` |
| `test_manager_manages_parameters` | `payroll.group_payroll_manager` implies `base_time_parameter.group_time_parameter` |
| `test_officer_sees_all_payslips` | a payslip of `employee`, whose department has a manager who is not the officer: an officer finds it with `search` (OCA's officer rule alone would hide it) |
| `test_hr_user_cannot_read_pay_lines` | a user in `hr_contract.group_hr_contract_manager` without payroll groups reads `contract.name` (positive control) and gets `AccessError` reading `l10n_vn.payroll.contract.line` |
| `test_officer_writes_pay_lines` | an officer creates and edits a pay line (positive), and cannot create a component (`AccessError`) |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Vietnamese payroll on OCA payroll; step 1: pay components with their SI, OT and PIT treatment and amount sources, salary and productivity scales with dated versions, dated pay lines on contracts that keep the contract wage in step, the payroll roles, and the statutory parameters created for Vietnamese companies |
| `readme/USAGE.md` | *Payroll → Configuration → Pay Components, Pay Scales, Time Parameters*; the *Pay Lines* page on a contract: a change is a new line from its date, the old one ended the day before; what each amount source expects on a line; the roles (Officer, Reviewer, Approver, Reader, Manager) and that new users receive no payroll role |
