# Payroll Technical Design

v0.1 (draft) · Oct 30, 2026 · @Peter · **chunks 1–2 of 3: foundations and calculation**

**Based on:**
- Payroll Requirements Specification v0.4 (FR-01 to FR-70), Pay Policy v0.4, Attendance Specification v0.3, Payroll Acceptance Test Cases v0.4 with `payroll_reference_calc.py`, Vietnam Payroll Regulation Reference v0.2;
- Payroll Fit-Gap v0.1, whose decisions (PFG-xx) this design builds on (go-ahead from Peter, 2026-10-30);
- the OCA and core code the instance runs, read 2026-10-30.

**Purpose:** the models, fields, relations and computations that implement the requirements on OCA payroll, module by module. It contains no code. The code-level specification of each module comes later in `docs/modules/<module>.md`, when that module is built. Where this design departs from the business documents, §21 lists the change as a proposal.

| Chunk | Content | Status |
| --- | --- | --- |
| **1. Foundations** | Decisions, modules, conventions, groups and access, parameters, components, scales, contract pay lines, participant types, people data | **This version** |
| **2. Calculation** | Periods and monthly inputs, contract selection, the pay context, OT, SI, union, PIT, damage compensation, generic rules, lines and rounding, snapshot, checks | **This version** |
| 3. Run and outputs | Run states, segregation and lock, adjustments, posting per run, payment and bank file, payslip report, statutory exports, reports, audit configuration, the garment configuration data, go-live and clean-up, test strategy | To do |

**Conventions:** status labels as in the fit-gap: **Agreed** (confirmed by Peter, with date), **Proposed** (designed here), **Open** (§20). Source references are `path:line` relative to `Odoo-Build/`.

---

## 0. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| PTD-01 | **Naming.** Modules `l10n_vn_payroll`, `l10n_vn_payroll_account`, `l10n_vn_payroll_garment`. Models `l10n_vn.payroll.*`, like core's `l10n_ke.item.code`. Fields added to core and OCA models start with `l10n_vn_`. Parameter codes start with `vn.` (statutory) and `vn.policy.` (company policy). (§1) | Proposed |
| PTD-02 | **A strict parameter reader in a shared module,** `base_time_parameter_strict`, used by payroll and proposed to IE in place of `ie.parameter` (IE TD-13). A stored 0 or False is a value; a missing version raises. (§4.1; closes PFG-OPEN-01 if IE agrees) | Proposed |
| PTD-03 | **Everything on a payslip is a component.** Earnings, OT categories, the OT supplement, adjustments, statutory deductions, employer contributions, damage compensation, gross and net: each is a `l10n_vn.payroll.component`. The engine computes some (statutory, totals); configuration defines the rest. (§5) | Proposed |
| PTD-04 | **Amounts come from a source named on the component:** a line amount, a parameter, a scale cell, the remainder of a scale cell after the fixed parts, an entered amount, or the engine. The current scheme's split (grade amount = base + performance pay) and the target policy's base per position are both configuration. (§5.2, §6) | Proposed |
| PTD-05 | **Pay terms are dated contract pay lines.** `wage` follows the base salary line. (§7) | Proposed |
| PTD-06 | **Contribution rules come from a participant type on the contract,** with a declared SI base for managers paid without a labour contract. Residency, union membership and the PIT commitment form are on the employee. (§8) | Proposed |
| PTD-07 | **One monthly input record per employee,** with optional segment breakdowns and entered lines, filled by import, by supervisors and managers, and later by the attendance module and IE. (§10) | Proposed |
| PTD-08 | **The payslip's main contract is the latest contract overlapping the month in state open or closed.** The rules run once, against it. The pay context reads every overlapping contract. (§11) | Proposed |
| PTD-09 | **A new rule type, `l10n_vn_component`,** on `hr.salary.rule.amount_select` and `condition_select`. Such a rule names its component and returns that component's line from the pay context; the line exists only when the context has one. (§17) | Proposed |
| PTD-10 | **Lines carry their exact amount.** A component line is written with quantity 1, rate 100 and the rounded total as amount; hours, factor and unit amount are kept in display fields. OCA's `quantity × rate × amount` never recomputes a figure. (§17.2) | Proposed |
| PTD-11 | **Check levels are parameters** (`vn.check.<code>`, optionally `.<component code>`), so they are dated, audited and per component (FR-59). Check results are records on the payslip. (§19) | Proposed |

---

## 1. Modules and dependencies

| Module | Holds | Depends on |
| --- | --- | --- |
| `base_time_parameter_strict` | The strict reader (§4.1) | `base_time_parameter` |
| `l10n_vn_payroll` | Components, scales, contract pay lines, participant types, people fields, periods and inputs, the pay context, the rule type, checks, run workflow, payslip report, statutory exports, groups, statutory parameters | `payroll`, `base_time_parameter_strict`, `hr_employee_relative`, `report_xlsx`, `excel_import_export` |
| `l10n_vn_payroll_account` | Department cost groups, component accounts, posting per run, bank file (chunk 3) | `l10n_vn_payroll`, `payroll_account`, `account_payment_order` |
| `l10n_vn_payroll_garment` | The current scheme as data: components, scales, structure and rules, policy parameters, check levels, account mapping, `auditlog` rules (chunk 3) | `l10n_vn_payroll_account`, `auditlog` |

- To install: `base_time_parameter` and `hr_employee_relative` (available in `oca/`, not installed).
- No dependency on the attendance module or on IE (§10.4).
- Statutory values ship in `l10n_vn_payroll` with no company, so any Vietnamese company shares them. The company's policy values ship in the garment module, on the company.

## 2. Conventions

| Topic | Rule |
| --- | --- |
| Names and codes | `name`: `Char(required=True, translate=True)`. `code`: `Char(required=True)`, unique per company (SQL constraint). |
| Money | `Monetary` in the company currency (VND, rounding 1). Engine figures are computed at full precision and rounded once, per line, half up (FR-34). |
| Rates and factors | `Float(digits=(16, 6))`. |
| Days and hours | `Float(digits=(16, 4))`. |
| Months | A period is a calendar month (§9). Dates are local dates. |
| Company | Every model with business data carries `company_id`. |
| Effective dates | Values a calculation uses are dated: parameters, scale versions, pay lines, dependents. Past months recompute to the same result (FR-03). |
| Security on pay fields | Every pay field added to a core or OCA model has `groups=` set to the payroll groups (§3), so it disappears from other users' views and exports (FR-54). |
| Tests | `TransactionCase`. Fixtures that create `res.partner`, `res.users` or product records are `post_install`. No import from core `tests` packages. No `HttpCase`. |

## 3. Groups and access

### 3.1 Groups

| Group | Implies | Who | Holds |
| --- | --- | --- | --- |
| `payroll.group_payroll_user` (OCA, *Officer*) | `hr.group_hr_user`, contract manager | Payroll officer | Pay data, inputs, runs up to *Calculated* |
| `l10n_vn_payroll.group_payroll_reviewer` | Officer | HR manager | Review a run; certify levels; set targets; approve contract pay |
| `l10n_vn_payroll.group_payroll_approver` | `base.group_user` | Director | Approve a run; read payslips |
| `l10n_vn_payroll.group_payroll_reader` | `base.group_user` | Accountant | Read runs, payslips and totals |
| `payroll.group_payroll_manager` (OCA, *Manager*) | Officer | Payroll administrator | Components, scales, structures, rules, parameters, check levels |

- The approver group does not imply the officer group, so a director who only approves cannot prepare (FR-02). The segregation itself is enforced on the run (chunk 3).
- **New-user template (PFG-10).** `l10n_vn_payroll` removes both OCA payroll groups from `base.default_user` (`oca/payroll/payroll/security/hr_payroll_security.xml:25-27`) in a `noupdate` record.
- **Record rules.** OCA's officer rule limits an officer to their own payslips, employees without a department and departments they manage (`hr_payroll_security.xml:28-36`). `l10n_vn_payroll` adds a rule for the officer group with domain `[(1, '=', 1)]`; rules of one user's groups combine with OR, so officers see every payslip of their companies, and OCA's global company rules still apply. Reviewer, approver and reader get the same read rule.

### 3.2 Access

| Model | Officer | Reviewer | Approver | Reader | Manager |
| --- | --- | --- | --- | --- | --- |
| `l10n_vn.payroll.component`, `.scale*`, `.participant.type` | read | read | — | read | all |
| `l10n_vn.payroll.contract.line` | read, write, create, unlink | all | — | — | all |
| `l10n_vn.payroll.period` | read, write, create | read, write | read | read | all |
| `l10n_vn.payroll.input`, `.input.segment`, `.input.line` | read, write, create, unlink | all | read | read | all |
| `l10n_vn.payroll.damage` | read, write, create | all | read | read | all |
| `l10n_vn.payroll.check`, `.check.result` | read; write the note on a result | read; write the note | read | read | all |
| `hr.payslip`, `hr.payslip.line`, `hr.payslip.run` | OCA rows | as officer | read | read | OCA rows |
| `base.time.parameter`, `.version` | read | read | — | read | all |

OCA grants officers write and delete on payslip lines (`oca/payroll/payroll/security/ir.model.access.csv:7`); the lock in chunk 3 refuses both once a run is approved.

## 4. Parameters

### 4.1 The strict reader (PTD-02)

`base_time_parameter_strict` adds `base.time.parameter._strict_get(code, date, company=None)`:

1. Finds the parameter with that `code` in the given company, else with no company. A company value overrides a statutory one.
2. Takes the version with the latest `date_from ≤ date` and converts its `value` by the parameter's type.
3. Raises a `UserError` naming the code and date if there is none.

OCA's own reader treats 0 and False as missing and never raises (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:72-73`, `models/base.py:22`). A 0% rate or a zero amount must stay a value, and a missing minimum wage must stop the run.

The pay context reads every parameter once per run per date and passes the values into each payslip; the snapshot keeps them (§18).

### 4.2 Statutory parameters (`l10n_vn_payroll`, no company)

| Code | Type | Value from the Regulation Reference v0.2 |
| --- | --- | --- |
| `vn.min_wage.month` | JSON | `{"I": 5310000, "II": 4730000, "III": 4140000, "IV": 3700000}` from 2026-01-01 |
| `vn.min_wage.hour` | JSON | `{"I": 25500, "II": 22700, "III": 19900, "IV": 17800}` from 2026-01-01 |
| `vn.si.reference_level` | float | 2,340,000; 2,530,000 from 2026-07-01 |
| `vn.si.cap_multiple`, `vn.ui.cap_multiple` | float | 20, 20 |
| `vn.rate.ee.si`, `vn.rate.ee.hi`, `vn.rate.ee.ui` | float | 0.08, 0.015, 0.01 |
| `vn.rate.er.pension`, `vn.rate.er.sickness`, `vn.rate.er.accident`, `vn.rate.er.hi`, `vn.rate.er.ui` | float | 0.14, 0.03, 0.005, 0.03, 0.01 |
| `vn.rate.union_fee`, `vn.rate.union_dues`, `vn.union_dues.cap` | float | 0.02, 0.005, 253,000 |
| `vn.si.absence_days` | integer | 14 (FR-23) |
| `vn.pit.self`, `vn.pit.dependent` | float | 15,500,000; 6,200,000 from 2026-01-01 |
| `vn.pit.brackets` | JSON | `[[10000000, 0.05], [30000000, 0.10], [60000000, 0.20], [100000000, 0.30], [null, 0.35]]` |
| `vn.pit.flat_short`, `vn.pit.flat_short_threshold`, `vn.pit.nonresident` | float | 0.10; 5,000,000; 0.20 |
| `vn.ot.factors` | JSON | `{"WD": 1.5, "RD": 2.0, "HOL": 3.0, "NIGHT": 0.3, "NWD": 2.0, "NWD_AFTER": 2.1, "NRD": 2.7, "NHOL": 3.9}` |
| `vn.ot.limit.month`, `vn.ot.limit.year` | integer | 40, 300 |
| `vn.damage.cap` | float | 0.30 |
| `vn.pit.meal_cap` | float | 1,200,000 from 2026-07-01 |
| `vn.probation.min_rate` | float | 0.85 (the legal floor; checked, §19) |
| `vn.probation.max_days` | JSON | limits per qualification level (Labor Code Art. 25) |

### 4.3 Policy parameters (`l10n_vn_payroll_garment`, on the company)

| Code | Type | Current scheme |
| --- | --- | --- |
| `vn.policy.region` | string | `IV` |
| `vn.policy.std_days.mode`, `vn.policy.std_days` | string, integer | `fixed`, 26 (FR-62) |
| `vn.policy.base_salary` | float | 3,700,000 |
| `vn.policy.probation_rate` | float | 0.85 |
| `vn.policy.attainment_cap` | float | 1.0 |
| `vn.policy.ot_supplement` | float | not set: the component is inactive in the current scheme |
| `vn.policy.unit_rate` | float | 1,500 (efficiency incentive, once IE is live) |
| `vn.policy.attendance_late_max` | integer | 2 (attendance bonus; inactive in the current scheme) |
| `vn.policy.constant_months` | integer | 6 (the `variable_constant` check) |
| `vn.policy.net_change` | float | 0.30 (the `net_change` check) |
| `vn.check.*` | string | check levels (§19) |

## 5. `l10n_vn.payroll.component` (PTD-03, PTD-04)

### 5.1 Fields

| Field | Type | Notes |
| --- | --- | --- |
| `code`, `name`, `sequence`, `active`, `company_id` | | `code` is the rule and line code |
| `kind` | Selection | `earning` / `deduction` / `employer` / `total` / `info` |
| `legal_nature` | Selection | `job_salary`, `fixed_allowance`, `fixed_supplement`, `variable_salary`, `bonus`, `welfare`, `overtime`, `night`, `leave_pay`, `severance`, `statutory`, `union`, `damage`, `adjustment`, `total`. Drives the nature checks (§19). |
| `in_si_base`, `in_ot_base` | Boolean | |
| `pit_treatment` | Selection | `taxable` / `exempt` / `exempt_cap` / `excluded` / `ot` (exempt within the OT limits, §15) |
| `pit_cap_parameter` | Char | parameter code for `exempt_cap` (e.g. `vn.pit.meal_cap`) |
| `amount_source` | Selection | `line` (amount on the pay line), `parameter`, `scale`, `scale_remainder`, `entered` (input lines, §10.3), `ot` (per hour, §14), `engine` |
| `amount_parameter` | Char | parameter code when `amount_source = parameter`, or the per-hour amount of an OT supplement |
| `scale_id` | Many2one `l10n_vn.payroll.scale` | for `scale` and `scale_remainder` |
| `proration` | Selection | `paid_days` / `days_worked` / `none` (FR-61) |
| `probation_applies` | Boolean | the probation rate multiplies it during probation |
| `variable` | Boolean | multiplied by the month's attainment or score (FR-68) |
| `attainment_source` | Selection | `supervisor` / `manager` / `ie` |
| `condition` | Selection | `none` / `attendance` (FR-64; the attendance bonus rule, §13.3) |
| `ot_category` | Selection | `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL`, or `all` for a supplement over every category |
| `engine_code` | Selection | for `amount_source = engine`: `GROSS`, `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT`, `DAMAGE`, `NET`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE` |
| `section` | Selection | payslip section: `salary`, `ot`, `bonus`, `other`, `deduction`, `employer`, `total` |
| `register_id` | Many2one `hr.contribution.register` | the partner for payable postings (SI agency, tax office) |
| `legal_reference`, `note` | Char, Text | |

Accounts are added by `l10n_vn_payroll_account` (chunk 3).

### 5.2 Amount sources

| Source | Amount for a month |
| --- | --- |
| `line` | The pay line's amount |
| `parameter` | The parameter's value on the segment's date (e.g. base salary 3,700,000) |
| `scale` | The pay line's scale cell in the version in force (e.g. productivity level S4 → 2,800,000) |
| `scale_remainder` | The pay line's cell minus the amounts of the contract's other lines whose components take part in the cell (`in_cell = True` on the line). In the current scheme, performance pay = G2 step 2 (8,000,000) − base (3,700,000). |
| `entered` | The month's input lines for the component (one-time bonus, KPI bonus, efficiency bonus during shadow mode, adjustments) |
| `ot` | Hours × factor × hourly rate, or hours × factor × the supplement per hour (§14) |
| `engine` | Computed by the engine (§15–§16) |

### 5.3 Constraints

- `scale` and `scale_remainder` need `scale_id`; `parameter` needs `amount_parameter`; `engine` needs `engine_code`.
- At most one `scale_remainder` component per scale on a contract's lines in force (checked on the pay lines).
- A component with `kind = earning` must have `in_si_base`, `in_ot_base`, `pit_treatment` and `proration` set (the integrity check of Requirements §7 is enforced here, at configuration time).

## 6. Scales (FR-03, FR-04, FR-05)

| Model | Fields |
| --- | --- |
| `l10n_vn.payroll.scale` | `code`, `name`, `kind` (`grade_step` / `level`), `company_id` |
| `l10n_vn.payroll.scale.version` | `scale_id`, `date_from`, `note`; unique `(scale_id, date_from)` |
| `l10n_vn.payroll.scale.cell` | `version_id`, `key` (Char: `G2-2`, `S4`), `grade` (Char), `step` (Integer), `amount` (Monetary); unique `(version_id, key)` |

- A cell is read from the version with the latest `date_from ≤` the segment's date. A new version is how HR changes amounts (FR-03); pay lines keep their key.
- **Current scheme data:** scale `PROD` (levels Entry, S1–S4: 800,000 to 2,800,000) and scale `GRADE` (G1-1 to G5-3; G6 has no cells, its amount is on the pay line).

## 7. Contract pay lines (PTD-05, FR-04, FR-37)

`l10n_vn.payroll.contract.line`:

| Field | Type | Notes |
| --- | --- | --- |
| `contract_id` | Many2one `hr.contract` | required, cascade |
| `component_id` | Many2one | required; its `amount_source` is `line`, `parameter`, `scale` or `scale_remainder` |
| `amount` | Monetary | for `line` |
| `scale_key` | Char | for `scale` and `scale_remainder`; validated against the scale |
| `in_cell` | Boolean | the line's amount is part of its contract's scale cell (the base salary under the current scheme) |
| `date_from`, `date_to` | Date | inside the contract's dates; `date_to` empty = to the contract's end |
| `granted_by`, `review_date` | Many2one `res.users`, Date | for level lines (FR-05) |
| `note` | Char | reason for a step above 1, a change, a override |

- **A change is a new line.** Raising a level ends the old line the day before and starts a new one (FR-37). Lines are never edited after a run that used them is approved (chunk 3 lock); the audit log records every change (FR-50).
- **`wage`.** On every write, `hr.contract.wage` is set to the amount of the base salary line in force today, so OCA and core screens that show it stay right. Payroll never reads `wage`.
- **Generating lines.** Choosing a pay group and a scale key on the contract form proposes the lines from the garment module's templates: worker → base salary + productivity pay at the level; other roles → base salary + performance pay at the grade and step. HR can edit the proposal.

**`hr.contract` additions:** `l10n_vn_line_ids`, `l10n_vn_participant_type_id` (§8), `l10n_vn_declared_si_base` (Monetary, for participant types that use a declared base), `l10n_vn_probation_form` (`none` / `clause` / `contract`). The probation period of a clause is core's `trial_date_end` (`odoo/addons/hr_contract/models/hr_contract.py:36`); a separate probation contract is its own contract with `l10n_vn_probation_form = contract` (PFG-OPEN-02).

## 8. Participant types and people data (PTD-06)

### 8.1 `l10n_vn.payroll.participant.type`

| Field | Notes |
| --- | --- |
| `code`, `name` | |
| `fund_pension`, `fund_sickness`, `fund_accident`, `fund_hi`, `fund_ui`, `fund_union_fee` | Booleans: which funds apply |
| `dues_allowed` | union dues apply to members |
| `base_source` | `components` (sum of lines flagged *in SI base*) / `declared` (the contract's declared base) |
| `floor` | `min_wage` / `reference_level` / `none` |
| `pit_method` | `progressive` / `flat_short` / `flat_nonresident` |

Data (`l10n_vn_payroll`):

| Code | Funds | Base | Floor | PIT |
| --- | --- | --- | --- | --- |
| `LABOUR` (labour contract of 1 month or more) | all | components | min_wage | progressive |
| `PROBATION` (separate probation contract) | none | – | – | flat_short |
| `MANAGER` (paid without a labour contract) | pension, sickness, accident, HI, union fee | declared | reference_level | progressive |
| `SHORT` (under 1 month) | none | – | – | flat_short |

The manager row follows the Regulation Reference v0.2, marked *to confirm* there (TC-OPEN-7).

### 8.2 PIT method on a payslip

1. The employee is non-resident → `flat_nonresident`.
2. Else the main contract's type says `flat_short`, or the contract runs under 3 months (`date_end − date_start`), and the employee has not filed the commitment form for the year → `flat_short`.
3. Else `progressive`.

### 8.3 `hr.employee` additions

All with `groups` = payroll groups.

| Field | Type | Notes |
| --- | --- | --- |
| `l10n_vn_pay_group` | Selection | `worker` / `support` / `office` / `daily` / `manager` |
| `l10n_vn_attendance_mode` | Selection | `scan` / `exception`; default from the pay group (Attendance §5) |
| `l10n_vn_region` | Selection | `I`–`IV`; default `vn.policy.region` |
| `l10n_vn_resident` | Boolean | default True |
| `l10n_vn_union_member` | Boolean | |
| `l10n_vn_pit_commitment_year` | Integer | year of the latest commitment form for short contracts |

SI number, tax code and bank account stay in core's `ssnid`, `identification_id` and `bank_account_id` (PFG-13).

### 8.4 Dependents (`hr.employee.relative` additions)

`l10n_vn_pit_dependent` (Boolean), `l10n_vn_tax_code` (Char), `l10n_vn_from` and `l10n_vn_to` (Date, first day of a month), `l10n_vn_document_ref` (Char), `l10n_vn_document` (Binary attachment). A dependent counts in a month when it is a PIT dependent and `from ≤ month ≤ to` (FR-06, FR-28). Missing document → policy check (§19).

---

## 9. `l10n_vn.payroll.period`

| Field | Type | Notes |
| --- | --- | --- |
| `name` | Char | `YYYY-MM` |
| `date_from`, `date_to` | Date | the calendar month |
| `company_id` | Many2one | unique `(company_id, date_from)` |
| `attendance_closed` | Boolean | set by the attendance module's close, or by confirming the month's import (§10.4) |
| `ie_required` | Boolean | True when IE is installed and in use for the month |
| `ie_closed` | Boolean | set from IE's period state when IE is installed |
| `state` | Selection | `open` / `inputs_closed` / `paid` |

A run is linked to a period. Calculating a run needs `attendance_closed`, and `ie_closed` when `ie_required` (FR-58, TC-F01). The period's inputs are read-only once it is `inputs_closed`; later corrections are entered in the next period as adjustments (FR-30).

## 10. Monthly inputs (PTD-07)

### 10.1 `l10n_vn.payroll.input`: one per employee per period

| Field | Type | Notes |
| --- | --- | --- |
| `period_id`, `employee_id`, `company_id` | | unique `(period_id, employee_id)` |
| `scheduled_days`, `paid_days`, `unpaid_days`, `days_worked` | Float | Attendance §9 |
| `si_absence_days` | Float | working days neither worked nor paid by the company (FR-23) |
| `leave_days_json` | Json | days by leave type |
| `paid_break_minutes` | Float | included in `paid_days` |
| `ot_hours_json` | Json | hours by category: `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL` |
| `ot_hours_ytd` | Float | OT hours in the year before this month (for the yearly limit) |
| `late_arrivals`, `unexcused_absences` | Integer | |
| `attainment` | Float | output ÷ target, or the score; capped by `vn.policy.attainment_cap` when used |
| `attainment_source` | Selection | `supervisor` / `manager` / `ie` / `override` |
| `attainment_note`, `attainment_by` | Char, Many2one `res.users` | an override needs the note (FR-68) |
| `ie_units` | Float | from IE (FR-16) |
| `segment_ids` | One2many | §10.2 |
| `line_ids` | One2many | §10.3 |
| `source` | Selection | `import` / `attendance` / `manual` |

### 10.2 `l10n_vn.payroll.input.segment`

Needed only when terms change inside the month (FR-35 to FR-40). Fields: `input_id`, `date_from`, `date_to`, `paid_days`, `days_worked`, `ot_hours_json`. The segments must cover the month's employment days without overlap, and their days must add up to the input's totals. When the context finds a change of terms in the month and no segments, it stops the payslip with an integrity error naming the dates it needs (§19). The attendance module fills segments from its daily records; with imports the officer enters them.

### 10.3 `l10n_vn.payroll.input.line`: entered amounts

| Field | Type | Notes |
| --- | --- | --- |
| `input_id` | Many2one | |
| `component_id` | Many2one | a component with `amount_source = entered` |
| `amount` | Monetary | signed |
| `hours` | Float | for an OT adjustment: counts towards the limits of `period_ref` |
| `period_ref` | Date | first day of the month an adjustment belongs to (FR-30) |
| `approved_by`, `approved_at` | Many2one `res.users`, Datetime | required before it is paid (FR-69) |
| `description` | Char | shown on the payslip |

### 10.4 Who fills the inputs

| Source | Fills | How |
| --- | --- | --- |
| Import (v1) | days, OT hours, late arrivals, absences, segments | An `excel_import_export` template on `l10n_vn.payroll.input`; confirming the import sets the period's `attendance_closed` |
| Supervisors | attainment for workers, until IE is live | A list view per line of the period's worker inputs |
| Managers, director | scores for other roles | A list view per manager of their staff's inputs |
| Officer | entered lines; approvers sign them | Form and list views |
| Attendance module (later) | days, OT, segments, `source = attendance` | Writes at attendance close; `l10n_vn_payroll` does not depend on it |
| IE (later) | `ie_units`, attainment with `source = ie` | `l10n_vn_payroll` calls `employee.ie_period_record(date)` (IE TD §14.3) only when the method exists, so there is no dependency either way |

---

## 11. Contracts on a payslip (PTD-08)

- **Period contracts:** every `hr.contract` of the employee overlapping the month, in state `open` or `close`. Core's `_get_contracts` searches open contracts only (`odoo/addons/hr_contract/models/hr_employee.py:105-119`), and writing a past `date_end` closes a contract at once (`hr_contract.py:323-326`), so a leaver's contract would be lost.
- **Main contract:** the period contract with the latest `date_start`. `get_payslip_vals` is overridden to set it as `contract_id` (OCA takes `employee.contract_id`, `oca/payroll/payroll/models/hr_payslip.py:641`), and `_get_employee_contracts` returns only it, so OCA's loop over contracts (`hr_payslip.py:577-612`) runs the rules once.
- **Structure:** the main contract's `struct_id`.
- **Worked days:** `get_worked_day_lines` is overridden to write the input record's figures as worked-day lines (`PAID`, `WORKED`, `UNPAID`, and one per leave type), for display. OCA's calendar figures (`WORK100`, `hr_payslip.py:377-397`) are not produced.

## 12. The pay context

`hr.payslip._l10n_vn_context()` builds one plain structure per payslip; `get_payroll_dict` returns it under the key `vn` (so rules can read `payroll.vn`), and the rule type reads it directly (§17). Built for a whole run in bulk: parameters once per date, inputs, contracts and pay lines in one read each.

Steps, in order:

1. **Parameters** for the month (§4), read at the month's last day; a segment reads its own date for dated values.
2. **Segments:** the month is cut at every contract start or end and every pay line start or end. Each segment knows its contract, its lines and whether it is in probation (a clause's `trial_date_end`, or a probation contract). One segment needs no breakdown; several need input segments (§10.2).
3. **Standard days:** `vn.policy.std_days` when the mode is `fixed`, else the input's `scheduled_days`.
4. **Attainment:** the input's `attainment`, capped. Missing while a variable component is in force → integrity error.
5. **Component lines** (§13).
6. **OT** (§14).
7. **Gross** = the sum of earning lines.
8. **SI, HI, UI, union** (§15).
9. **PIT** (§16.1).
10. **Damage compensation** (§16.2).
11. **Net** = gross − employee insurance − union dues − PIT − damage compensation.
12. **Checks** (§19).

Each line in the context carries: component code, amount (rounded), and for display the quantity, unit amount, factor, segment dates, attainment and the period an adjustment belongs to.

## 13. Component lines

### 13.1 Per segment, for each pay line in force

```latex
\text{line} = \operatorname{round}\!\left(\text{amount} \times \frac{\text{days on its basis in the segment}}{\text{standard days}} \times r \times a\right)
```

- *amount* from the component's source (§5.2) at the segment's date;
- the basis is the component's proration: the segment's `paid_days`, `days_worked`, or the full amount (`none`);
- *r* is `vn.policy.probation_rate` when the segment is in probation and the component has `probation_applies`, else 1;
- *a* is the attainment when the component is `variable`, else 1.

One line per pay line per segment, so a probation split shows two salary lines (TC-C02, TC-C06).

### 13.2 Entered components

One line per input line, with its description and, for an adjustment, its `period_ref`. An input line without an approver is not paid and raises the integrity check (FR-69, TC-F13).

### 13.3 Conditional components

`condition = attendance`: paid in full when the input has no unexcused absence and `late_arrivals ≤ vn.policy.attendance_late_max`; otherwise zero (FR-17). It is inactive in the current scheme.

### 13.4 Leaver items

Untaken annual leave is an entered component with `legal_nature = leave_pay` and `pit_treatment = exempt`, computed by the officer from the previous month's contract salary ÷ standard days (TC-OPEN-4). A later version can compute it from the leave balance.

## 14. Overtime

```latex
\text{OT base} = \sum_{\text{lines in OT base}} \text{amount} \times r \times a \qquad
\text{hourly} = \frac{\text{OT base}}{\text{standard days} \times 8}
```

- The OT base uses the amounts of the lines in force, **not prorated by days**, with the probation rate and attainment (FR-15, TC-G04). For a daily-paid contract the hourly rate is the daily rate ÷ 8 (FR-65).
- **With segments,** each segment's OT hours use that segment's OT base; without segments the month's hours use the last segment's.
- **Lines:** for each OT component with a category *c*: `round(hourly × factor_c × hours_c)`, factors from `vn.ot.factors`. A supplement component (`ot_category = all`) adds `round(supplement × Σ factor_c × hours_c)`.
- The display fields keep hours, factor and hourly rate.

## 15. SI, HI, UI and union

1. **Liability.** The main contract's participant type gives the funds. No contribution for the month when the input's `si_absence_days ≥ vn.si.absence_days` (FR-23). When a liable contract starts mid-month, the month is contributed if its working days under the liable contract reach `vn.si.absence_days` (TC-OPEN-2).
2. **Base.** `components`: the sum of the main contract's lines in force at the month's end flagged *in SI base*, at full amount (not prorated, no attainment); `declared`: the contract's declared base. Then the floor: the region's monthly minimum wage, or the reference level. A change of base inside the month applies from `[OPEN-04]`; until decided, the base in force at the month's end.
3. **Caps.** SI and HI base ≤ `cap_multiple × reference level`; UI base ≤ `cap_multiple × minimum wage` of the region.
4. **Lines.** Employee SI, HI, UI and employer pension, sickness, accident, HI, UI each `round(rate × capped base)`; union fee `round(rate × SI base)`; union dues for members `min(round(rate × SI base), cap)`. Rates per fund are parameters (FR-22).

## 16. PIT and damage compensation

### 16.1 PIT

**Progressive** (FR-26 to FR-28):

```latex
T = \text{gross} - E - \text{employee insurance} - \text{self} - n \times \text{dependent}
```

- *E*, the exempt amount: lines with `pit_treatment = exempt`; `exempt_cap` lines up to their cap; and OT lines (`ot`) for hours within the limits. OT within the limits is apportioned by hours over the month's OT pay, including the supplement: exempt share = min(1, allowed ÷ hours), where allowed = min(month limit, year limit − `ot_hours_ytd`) (TC-B01, TC-OPEN-6). Adjustment hours count in the month they belong to (TC-E01).
- *n*: dependents counted for the month (§8.4).
- PIT = the bracket sum on *T* from `vn.pit.brackets`, rounded; 0 when *T* ≤ 0.

**Flat:** `flat_short`: 10% of gross when gross ≥ the threshold, else 0 (TC-OPEN-3); `flat_nonresident`: 20% of gross.

The payslip stores *E*, *T* and the method in the context (for the PIT exports, chunk 3).

### 16.2 `l10n_vn.payroll.damage` (FR-31)

| Field | Notes |
| --- | --- |
| `employee_id`, `company_id` | |
| `decision_ref`, `decision_date`, `reason` | the work-rules decision |
| `amount` | total decided |
| `deducted` | computed: sum of DAMAGE lines on done payslips |
| `balance` | computed |
| `state` | `open` / `done` |

On a payslip: deduction = min(Σ open balances, `vn.damage.cap` × (gross − employee insurance − PIT)), allocated to decisions oldest first; the rest carries to the next payslip (TC-E02, TC-G08).

## 17. Rules and lines

### 17.1 The rule type (PTD-09)

`l10n_vn_payroll` adds:

- `l10n_vn_component` to `hr.salary.rule.amount_select` and to `condition_select` (`selection_add`), and `l10n_vn_component_id` on `hr.salary.rule`. Fields added to the rule also reach `hr.payslip.line`, which inherits it (on the instance, `payroll_account`'s rule fields are columns of `hr_payslip_line`).
- `_satisfy_condition_l10n_vn_component`: True when the context has a line for the component. OCA calls `_satisfy_condition_<select>` and `_compute_rule_<select>` by name (`oca/payroll/payroll/models/hr_salary_rule.py:202-210`, `:292-305`).
- `_compute_rule_l10n_vn_component`: returns the context line: name (with the segment dates or period reference when set), quantity 1, rate 100, amount = the rounded line.

A structure is one rule per component, in sequence; categories group them for the payslip and reports. The garment module ships the structure.

### 17.2 Exact lines (PTD-10)

- The line's `total` is `quantity × amount × rate / 100` (`oca/payroll/payroll/models/hr_payslip_line.py` `_compute_total`) = the context's rounded amount, so it cannot drift.
- `_get_lines_dict` sums totals into categories at full precision (`hr_payslip.py:532-541`). For `l10n_vn_component` rules the totals are already whole dong, so categories match. Other rule types, if a configuration mixes them in, are rounded half up in an override of `_get_lines_dict` before they are summed (PFG-06).
- Display fields on `hr.payslip.line`: `l10n_vn_hours`, `l10n_vn_factor`, `l10n_vn_unit_amount`, `l10n_vn_date_from`, `l10n_vn_date_to`, `l10n_vn_attainment`, `l10n_vn_period_ref`.

## 18. Snapshot (FR-10, FR-53)

`hr.payslip.l10n_vn_context` (Json) stores the whole context at calculation: parameter values with their dates, the input record's values, the pay lines and scale cells used, every line, the bases, the PIT figures and the check results. Recalculation replaces it while the run is open; after approval it is frozen with the payslip (chunk 3). Reproducing a payslip means recomputing from the snapshot's inputs and comparing (FR-53).

## 19. Checks (PTD-11, FR-59)

### 19.1 Models

- `l10n_vn.payroll.check`: `code`, `name`, `kind` (`integrity` / `legal` / `policy`), `default_level` (`error` / `warning` / `note` / `off`), `per_component` (Boolean). Data records; each code has a method `_l10n_vn_check_<code>(context)` that returns findings.
- **Level** for a finding: `vn.check.<code>.<component>` if set, else `vn.check.<code>`, else `default_level`. Integrity checks are always `error` and ignore parameters.
- `l10n_vn.payroll.check.result`: `payslip_id`, `run_id`, `check_id`, `component_id`, `level`, `message`, `note`, `noted_by`. A warning needs a note before review; an error blocks review and approval (chunk 3).

### 19.2 Catalogue

| Code | Kind | Default | Finds |
| --- | --- | --- | --- |
| `period_open` | integrity | error | attendance or IE not closed for the period |
| `negative_net` | integrity | error | net < 0 |
| `missing_ids` | integrity | error | no bank account, tax code or SI number for a paid employee |
| `missing_attainment` | integrity | error | a variable component in force and no attainment or score |
| `missing_segments` | integrity | error | terms change in the month and no input segments |
| `unapproved_entry` | integrity | error | an entered line without an approver |
| `min_wage` | legal | error | salary lines in SI base for full normal hours below the region's minimum |
| `daily_min` | legal | error | a daily rate below the hourly minimum × the day's hours |
| `nature` | legal | warning | flags inconsistent with legal nature: a `welfare` component in the OT base, a `fixed_allowance` outside the SI base, a `variable_salary` that is not variable |
| `probation_length` | legal | warning | probation longer than `vn.probation.max_days` for the job, or a rate below `vn.probation.min_rate` |
| `deduction_kind` | legal | warning | a deduction component whose nature is not `statutory`, `union` or `damage` (FR-70) |
| `ot_limit` | legal | warning | month over 40 h or year over 300 h |
| `variable_constant` | policy | warning, per component | a variable component at 100% (or conditional paid in full) for `vn.policy.constant_months` months running; the garment module sets it to `note` for performance pay (Pay Policy §4.2, TC-F15) |
| `net_change` | policy | warning | net pay changed more than `vn.policy.net_change` from the previous month |
| `ie_scope` | policy | warning | IE units for an employee outside IE scope |
| `level_review` | policy | warning | a level line past its review date |
| `dependent_document` | policy | warning | a PIT dependent without its document |

---

## 20. Open items

| ID | Item | Proposal |
| --- | --- | --- |
| PTD-OPEN-01 | IE adopts `base_time_parameter_strict` instead of `ie.parameter` | Yes; one reader for both suites (a proposal to the IE technical design) |
| PTD-OPEN-02 | Probation recording (PFG-OPEN-02) | Both forms supported (§7) |
| PTD-OPEN-03 | The SI base when it changes inside a month (Requirements OPEN-04) | Until decided: the base at the month's end (§15) |
| PTD-OPEN-04 | OT in a split month without OT hours per segment | Last segment's OT base (§14) |
| PTD-OPEN-05 | Untaken-leave pay computed from the leave balance | v1: entered by the officer (§13.4) |

## 21. Proposals to the business documents

| Document | Proposal |
| --- | --- |
| Requirements §9 | Monthly attendance totals may be imported until the attendance module is live; confirming the import closes attendance for the month. Segments are needed only in a month whose terms change. |
| Requirements FR-59 | Check levels are parameters `vn.check.<code>[.<component>]`. |
| Acceptance Test Cases | The employer pension, sickness and accident lines are separate (FR-22); the test footers that show one employer SI figure should show the three funds. |
| IE Technical Design TD-13 | Use `base_time_parameter_strict` (PTD-02). |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-30 | Chunks 1 and 2: decisions PTD-01 to PTD-11, modules, groups and access, parameters, components, scales, pay lines, participant types, people data, periods and inputs, contract selection, the pay context, component lines, OT, SI, PIT, damage compensation, rule type, exact lines, snapshot, checks. |
