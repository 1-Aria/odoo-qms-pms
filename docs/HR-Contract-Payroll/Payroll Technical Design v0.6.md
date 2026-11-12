# Payroll Technical Design

v0.6 (draft) · Nov 12, 2026 · @Peter · **chunks 1–3 of 3; v0.6 adds the go-live design for November 2026**

**Supersedes:** v0.5, kept as history with v0.1 to v0.4. v0.6 adds the design for the first cycle, November 2026, run on the new policy rather than on the previous payroll's figures (Peter, 2026-11-11), following Pay Policy v0.6, Requirements v0.7 (FR-72 to FR-79) and the Regulation Reference v0.4: contract types and two participant types, PIT by contract, the identification and bank checks, attendance corrections, a contract-term check, base salary by group, and payment apart from posting (PTD-19 to PTD-25). It is not built yet; §33 records corrections once it is.

v0.5 folded in:
- time from Odoo's attendance through `hr_attendance_day` (attendance design note v0.2, `docs/modules/hr_attendance_day.md`) and `l10n_vn_payroll` steps 10 and 10.1 (236 tests, Nov 8, 2026);
- the garment configuration as built, steps 1 and 5 of `docs/modules/l10n_vn_payroll_garment.md`, made before `l10n_vn_payroll_account`;
- Peter's decisions of Nov 7–8 on PIT: untaken-leave pay exempt, the OT exemption within the monthly and yearly limits only.

v0.4 folded in what building `l10n_vn_payroll` steps 1–9 corrected. The sections below are updated where a correction changes them; §33 lists every correction with its module doc's divergence number.

**Based on:**
- Payroll Requirements Specification v0.4 (FR-01 to FR-70), Pay Policy v0.4, Attendance Specification v0.3, Payroll Acceptance Test Cases v0.4 with `payroll_reference_calc.py`, Vietnam Payroll Regulation Reference v0.2;
- Requirements v0.5 (FR-71, salary advances), Pay Policy v0.5 and Acceptance Test Cases v0.5;
- Payroll Fit-Gap v0.1, whose decisions (PFG-xx) this design builds on (go-ahead from Peter, 2026-10-30);
- the OCA and core code the instance runs, read 2026-10-30, and `hr_attendance`, `hr`, `hr_contract`, `resource` read 2026-11-08;
- Attendance Daily Time — Design Note v0.2 (Route A, Peter 2026-11-08) and the May 2026 comparison on the test copy.

**Purpose:** the models, fields, relations and computations that implement the requirements on OCA payroll, module by module. It contains no code. The code-level specification of each module comes later in `docs/modules/<module>.md`, when that module is built. Where this design departs from the business documents, §32 lists the change as a proposal.

| Chunk | Content | Status |
| --- | --- | --- |
| **1. Foundations** | Decisions, modules, conventions, groups and access, parameters, components, scales, contract pay lines, participant types, people data | Written in v0.1; small corrections in v0.2 |
| **2. Calculation** | Periods and monthly inputs, contract selection, the pay context, OT, SI, union, PIT, damage compensation, generic rules, lines and rounding, snapshot, checks | Written in v0.1; small corrections in v0.2 |
| **3. Run and outputs** | Run states, segregation and lock, corrections, posting per run, payment and bank file, payslip report, statutory statements, reports, audit, the garment configuration, go-live and clean-up, test strategy | **This version** (§20–§30) |

**Conventions:** status labels as in the fit-gap: **Agreed** (confirmed by Peter, with date), **Proposed** (designed here), **Open** (§31). Source references are `path:line` relative to `Odoo-Build/`.

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
| PTD-07 | **One monthly input record per employee,** with segments and entered lines: its time figures built from the attendance (PTD-17), attainment and entered lines by the payroll officer, and later IE's figures. (§10) | Built (v0.5) |
| PTD-08 | **The payslip's main contract is the latest contract overlapping the month in state open or closed.** The rules run once, against it. The pay context reads every overlapping contract. (§11) | Proposed |
| PTD-09 | **A new rule type, `l10n_vn_component`,** on `hr.salary.rule.amount_select` and `condition_select`. Such a rule names its component and returns that component's line from the pay context; the line exists only when the context has one. (§17) | Proposed |
| PTD-10 | **Lines carry their exact amount.** A component line is written with quantity 1, rate 100 and the rounded total as amount; hours, factor and unit amount are kept in display fields. OCA's `quantity × rate × amount` never recomputes a figure. (§17.2) | Proposed |
| PTD-11 | **Check levels are parameters** (`vn.check.<code>`, optionally `.<component code>`), so they are dated, audited and per component (FR-59). Check results are records on the payslip. (§19) | Proposed |
| PTD-12 | **The run carries the workflow:** Draft → Calculated → Reviewed → Approved → Paid, added to OCA's batch; payslips are confirmed at approval; the preparer cannot approve; nothing returns from Approved. (§20, §21) | Proposed |
| PTD-13 | **One entry per run** posted at approval from cost groups (department) and component accounts; each employee's 3341 debits are reconciled against the gross credit so the residual is net pay. (§22) | 3341 gross with reconciled deductions **Agreed 2026-10-31**; the rest Proposed |
| PTD-14 | **File layouts are templates.** The bank file and the statutory statements are `excel_import_export` templates, so a new bank or a changed form is a template change. (§23, §25) | Proposed |
| PTD-15 | **Statements read approved snapshots,** never recalculate. Opening data for the months before go-live is its own model. (§25) | Proposed |
| PTD-16 | **Salary advances** are their own records, paid through the payroll payment order with their payment booked Dr 3341 / Cr bank, and settled on the month's payslip by the 3341 reconciliation. The payslip shows `ADVANCE` and `TO_PAY` lines; nothing extra is posted at settlement. (§23.2) | Proposed |
| PTD-17 | **Time comes from Odoo's attendance through `hr_attendance_day`.** Odoo decides how much time: expected hours from the contract's calendar, worked hours, the day's overtime with its two tolerances (grace period 5 minutes, OT minimum 48 minutes) and its approval. `hr_attendance_day` derives each day's figures: day type, normal hours, normal night hours, overtime and its night part, days worked by hours per paid day, late arrival, absence, days without check-out. The monthly summary reads them; payroll keeps who pays and the legal limits (§10.4, §14). | Agreed 2026-11-08 |
| PTD-18 | **The garment configuration is loaded per company** from *Settings → Payroll* by a payroll manager, matched by code, keeping what exists. It is built before `l10n_vn_payroll_account`, which brings the account mapping (§28). | Agreed 2026-11-07 |
| PTD-19 | **Contract types give participant types.** `hr.contract.type` gains `l10n_vn_participant_type_id`, the default for a new contract of that type: Labour → `LABOUR`, Probation → `PROBATION`, Training → `TRAINING` (new), Casual → `CASUAL` (new). Participant types gain `paid_by_transfer` and `posted` (§8.1). | Agreed 2026-11-11 |
| PTD-20 | **PIT method by contract** (§8.2): a participant type's flat rate gives way to the progressive method when the employee filed the commitment form for the year; `PROBATION` is progressive, flat only when the contract runs under 3 months. | Agreed 2026-11-12 |
| PTD-21 | **One ID, and the bank where pay is by transfer:** `missing_ids` asks for the CCCD (`l10n_vn_personal_id`, the SI number and tax code) from everyone paid, and a bank account where the participant type is `paid_by_transfer`; Odoo's `ssnid` is no longer asked for. | Agreed 2026-11-11 |
| PTD-22 | **Attendance corrections are reviewed with the payroll.** `hr_attendance_day` adds a *Correction Reason* to `hr.attendance`; a day with a corrected attendance is flagged in its figures, and payroll's check `attendance_corrections` (policy, warning) lists them for the reviewer's note. | Agreed 2026-11-11 |
| PTD-23 | **Contract terms:** a check `contract_term` (legal, warning) finds a third fixed-term labour contract in a row and a training contract longer than 3 months. | Agreed 2026-11-12 |
| PTD-24 | **Payment apart from posting.** A new module `l10n_vn_payroll_payment` holds salary advances and the run's payment lists (bank file for transfers, cash list); `l10n_vn_payroll_account` only posts, and leaves out payslips whose participant type is not `posted` (§22, §23). | Agreed 2026-11-11 |
| PTD-25 | **Base salary by group:** `BASE` takes its amount from a dated scale `BASE` keyed by group (`WORKER`, and one key per grade of the other roles); `PERF` and `PROD` stay the rest of the person's agreed amount (§28). | Agreed 2026-11-11 |

---

## 1. Modules and dependencies

| Module | Holds | Depends on |
| --- | --- | --- |
| `base_time_parameter_strict` | The strict reader (§4.1) | `base_time_parameter` |
| `hr_attendance_day` | Each day's attendance figures from Odoo's attendance; hours per paid day and the night window on the calendar (PTD-17) | `hr_attendance`, `hr_contract` |
| `l10n_vn_payroll` | Components, scales, contract pay lines, participant types, people fields, periods and inputs, the pay context, the rule type, checks, run workflow, payslip report, statutory exports, groups, statutory parameters | `payroll`, `base_time_parameter_strict`, `hr_employee_relative`, `excel_import_export`, `hr_attendance_day` |
| `l10n_vn_payroll_payment` | Salary advances, the run's payment lists (bank file, cash list), payment state (PTD-24, §23) | `l10n_vn_payroll` |
| `l10n_vn_payroll_account` | Department cost groups, component accounts, posting per run of the payslips whose participant type is `posted` (§22) | `l10n_vn_payroll_payment`, `payroll_account` |
| `l10n_vn_payroll_garment` | The current scheme as configuration, loaded per company: components, scales, structure and rules, policy parameters, check levels; later `auditlog` rules and the account mapping (§27, §28) | `l10n_vn_payroll`; `auditlog` and `l10n_vn_payroll_account` with the later steps |

- To install: `base_time_parameter` and `hr_employee_relative` (available in `oca/`, not installed).
- No dependency on IE (§10.4). The attendance module is `hr_attendance_day` (PTD-17); payroll depends on it, which also declares the attendance dependency the summary always had.
- Statutory values are created by `l10n_vn_payroll` for **every company whose country is Vietnam**, at each install and upgrade, never overwriting edited values: OCA's company rule on parameters (`[('company_id', 'in', company_ids)]`) hides a parameter without a company. The company's policy values ship in the garment module, on the company.

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

- The approver group does not imply the officer group, so a director who only approves cannot prepare (FR-02). The segregation itself is enforced on the run (§20).
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
| `l10n_vn.payroll.advance` | read, write, create (draft) | all; approve | read | read | all |
| `l10n_vn.payroll.check`, `.check.result` | read; write the note on a result | read; write the note | read | read | all |
| `hr.payslip`, `hr.payslip.line`, `hr.payslip.run` | OCA rows | as officer | read | read | OCA rows |
| `base.time.parameter`, `.version` | read | read | — | read | all |

OCA grants officers write and delete on payslip lines (`oca/payroll/payroll/security/ir.model.access.csv:7`); the lock (§21) refuses both once a run is approved.

## 4. Parameters

### 4.1 The strict reader (PTD-02)

`base_time_parameter_strict` adds `base.time.parameter._strict_get(code, date, company=None)`:

1. Finds the parameter with that `code` in the given company, else with no company. A company value overrides a statutory one.
2. Takes the version with the latest `date_from ≤ date` and converts its `value` by the parameter's type.
3. Raises a `UserError` naming the code and date if there is none.

OCA's own reader treats 0 and False as missing and never raises (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:72-73`, `models/base.py:22`). A 0% rate or a zero amount must stay a value, and a missing minimum wage must stop the run.

The pay context reads every parameter once per run per date and passes the values into each payslip; the snapshot keeps them (§18).

### 4.2 Statutory parameters (`l10n_vn_payroll`, per Vietnamese company)

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
| `vn.ot.limit.day_share`, `vn.ot.limit.day_total` | float | 0.5, 12: OT above half the day's normal hours, or work beyond 12 hours in the day; labour rules, reported by checks and not used by PIT (§14, §16.1) |
| `vn.damage.cap` | float | 0.30 |
| `vn.pit.meal_cap` | float | 1,200,000 from 2026-07-01 |
| `vn.probation.min_rate` | float | 0.85 (the legal floor; checked, §19) |
| `vn.probation.max_days` | JSON | limits per qualification level (Labor Code Art. 25) |

### 4.3 Policy parameters (`l10n_vn_payroll_garment`, on the company)

| Code | Type | Current scheme |
| --- | --- | --- |
| `vn.policy.region` | string | `IV` |
| `vn.policy.std_days` | integer | 26 (FR-62; the variant from the month's schedule is not built) |
| `vn.policy.base_salary` | float | 3,700,000 |
| `vn.policy.probation_rate` | float | 0.85 |
| `vn.policy.attainment_cap` | float | 1.0 |
| `vn.policy.constant_months` | integer | 6 (the `variable_constant` check) |
| `vn.policy.net_change` | float | 0.30 (the `net_change` check) |
| `vn.check.variable_constant.PERF`, `vn.check.long_days` | string | `note` (§19) |

The garment loader creates these from 2026-01-01 (§28). Not created, each set when its feature is used: `vn.policy.unit_rate` (once IE is live, Pay Policy OPEN-04), `vn.policy.attendance_bonus` and `vn.policy.attendance_late_max` (with the `ATT` option), `vn.policy.ot_supplement` (no `SUPP` component), `vn.policy.advance_max_share` (with the advances, §23.2). `vn.policy.ot_min_hours_day` is retired: Odoo's company tolerance replaces it (PTD-17).

## 5. `l10n_vn.payroll.component` (PTD-03, PTD-04)

### 5.1 Fields

| Field | Type | Notes |
| --- | --- | --- |
| `code`, `name`, `sequence`, `active`, `company_id` | | `code` is the rule and line code |
| `kind` | Selection | `earning` / `deduction` / `employer` / `total` / `info` |
| `legal_nature` | Selection | `job_salary`, `fixed_allowance`, `fixed_supplement`, `variable_salary`, `bonus`, `welfare`, `overtime`, `night`, `leave_pay`, `severance`, `statutory`, `union`, `damage`, `advance`, `adjustment`, `total`. Drives the nature checks (§19). |
| `in_si_base`, `in_ot_base` | Boolean | |
| `pit_treatment` | Selection | `taxable` / `exempt` / `exempt_cap` / `excluded` / `ot` (exempt within the OT limits, §15) |
| `pit_cap_parameter` | Char | parameter code for `exempt_cap` (e.g. `vn.pit.meal_cap`) |
| `amount_source` | Selection | `line` (amount on the pay line), `parameter`, `scale`, `scale_remainder`, `entered` (input lines, §10.3), `ie_units` (IE units × `vn.policy.unit_rate`), `ot` (per hour, §14), `engine` |
| `amount_parameter` | Char | parameter code when `amount_source = parameter`, or the per-hour amount of an OT supplement |
| `scale_id` | Many2one `l10n_vn.payroll.scale` | for `scale` and `scale_remainder` |
| `proration` | Selection | `paid_days` / `days_worked` / `none` / `per_day` (a daily rate × paid days, FR-65) (FR-61) |
| `probation_applies` | Boolean | the probation rate multiplies it during probation |
| `variable` | Boolean | multiplied by the month's attainment or score (FR-68) |
| `attainment_source` | Selection | `supervisor` / `manager` / `ie` |
| `condition` | Selection | `none` / `attendance` (FR-64; the attendance bonus rule, §13.3) |
| `ot_category` | Selection | `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL`, or `all` for a supplement over every category |
| `engine_code` | Selection | for `amount_source = engine`: `GROSS`, `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT`, `DAMAGE`, `NET`, `ADVANCE`, `TO_PAY`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE` |
| `section` | Selection | payslip section: `salary`, `ot`, `bonus`, `other`, `deduction`, `employer`, `total` |
| `register_id` | Many2one `hr.contribution.register` | the partner for payable postings (SI agency, tax office) |
| `legal_reference`, `note` | Char, Text | |

Accounts are added by `l10n_vn_payroll_account` (§22).

### 5.2 Amount sources

| Source | Amount for a month |
| --- | --- |
| `line` | The pay line's amount |
| `parameter` | The parameter's value on the segment's date (e.g. base salary 3,700,000) |
| `scale` | The pay line's scale cell in the version in force (e.g. productivity level S4 → 2,800,000) |
| `scale_remainder` | The pay line's cell minus the amounts of the contract's other lines whose components take part in the cell (`in_cell = True` on the line). In the current scheme, performance pay = G2 step 2 (8,000,000) − base (3,700,000). |
| `entered` | The month's input lines for the component (one-time bonus, KPI bonus, efficiency bonus during shadow mode) |
| `ie_units` | The input's `ie_units` × `vn.policy.unit_rate` (FR-16, once IE is live) |
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
| `scale_key` | Char | for `scale` and `scale_remainder`; validated against the scale. An `amount` on such a line overrides the cell, for amounts set individually (G6). |
| `in_cell` | Boolean | the line's amount is part of its contract's scale cell (the base salary under the current scheme) |
| `date_from`, `date_to` | Date | inside the contract's dates; `date_to` empty = to the contract's end |
| `granted_by`, `review_date` | Many2one `res.users`, Date | for level lines (FR-05) |
| `note` | Char | reason for a step above 1, a change, a override |

- **A change is a new line.** Raising a level ends the old line the day before and starts a new one (FR-37). Lines are never edited after a run that used them is approved (lock, §21); the audit log records every change (FR-50).
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
| `TRAINING` (training contract, PTD-19) | none | – | – | flat_short |
| `CASUAL` (no written contract, PTD-19) | none | – | – | flat_short |

New fields (PTD-19): `paid_by_transfer` (Boolean; True for `LABOUR`, `PROBATION`, `MANAGER`, `TRAINING`, `SHORT`; False for `CASUAL`) and `posted` (Boolean; False for `CASUAL`, True otherwise). `PROBATION` changes to `progressive` (PTD-20). On `hr.contract.type`: `l10n_vn_participant_type_id`, the default participant type of a new contract of that type.

The manager row follows the Regulation Reference v0.2, marked *to confirm* there (TC-OPEN-7).

### 8.2 PIT method on a payslip

1. The employee is non-resident → `flat_nonresident`.
2. Else, when the employee filed the commitment form for the year → `progressive` (PTD-20).
3. Else the participant type says `flat_short`, or the contract runs under 3 months (`date_end − date_start`) → `flat_short`.
4. Else `progressive`.

The flat rate applies to a payment of `vn.pit.flat_short_threshold` (5,000,000) or more, on the whole payment (Regulation Reference v0.4).

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
| `attendance_closed` | Boolean | set by *Close Attendance*, which freezes the month's summaries (§10.4); a period whose run is approved cannot reopen |
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
| `paid_break_hours` | Float | included in `paid_days` |
| `ot_hours_json` | Json | hours by category: `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL` |
| `ot_hours_ytd` | Float | OT hours in the year before this month (for the yearly limit) |
| `late_arrivals`, `unexcused_absences` | Integer | days late beyond the grace period, days scheduled and not attended; scan mode only |
| `ot_over_daily_hours`, `long_days`, `incomplete_days` | Float, Integer, Integer | OT over the daily limit, days over 12 hours of work, days with an attendance without check-out (§14, §19) |
| `night_hours`, `ot_night_hours` | Float | normal hours at night (`NIGHT`) and night OT, from `ot_hours_json`; `ot_hours` leaves `NIGHT` out |
| `attainment` | Float | output ÷ target, or the score; capped by `vn.policy.attainment_cap` when used |
| `attainment_source` | Selection | `supervisor` / `manager` / `ie` / `override` |
| `attainment_note`, `attainment_by` | Char, Many2one `res.users` | an override needs the note (FR-68) |
| `ie_units` | Float | from IE (FR-16) |
| `segment_ids` | One2many | §10.2 |
| `line_ids` | One2many | §10.3 |

### 10.2 `l10n_vn.payroll.input.segment`

Needed only when terms change inside the month (FR-35 to FR-40). Fields: `input_id`, `date_from`, `date_to`, `paid_days`, `days_worked`, `ot_hours_json`. The segments must cover the month's employment days without overlap, and their days must add up to the input's totals. When the context finds a change of terms in the month and no segments, it stops the payslip with an integrity error naming the dates it needs (§19). The summary computes them from the daily figures; a summary corrected by hand needs them entered.

### 10.3 `l10n_vn.payroll.input.line`: entered amounts

| Field | Type | Notes |
| --- | --- | --- |
| `input_id` | Many2one | |
| `component_id` | Many2one | a component with `amount_source = entered`; or, for an adjustment (`period_ref` set), any earning or deduction component, whose flags the adjustment carries |
| `amount` | Monetary | signed |
| `hours` | Float | for an OT adjustment: counts towards the limits of `period_ref` |
| `period_ref` | Date | first day of the month an adjustment belongs to (FR-30) |
| `approved_by`, `approved_at` | Many2one `res.users`, Datetime | required before it is paid (FR-69) |
| `description` | Char | shown on the payslip |

### 10.4 Who fills the inputs

| Source | Fills | How |
| --- | --- | --- |
| The monthly summary (built) | days, leave by payer, OT hours by category with the night ones, paid breaks, late arrivals, absences, days without check-out, OT over the daily limit, long days, the month's scheduled days, segments | *Build Summaries* reads each day's figures from `hr_attendance_day` (`hr.employee._attendance_days()`), approved leave by payer and the contracts' calendars; *Close Attendance* freezes them. Days worked = normal hours ÷ hours per paid day; an employee in *exception* mode (`l10n_vn_attendance_mode`) gets the expected hours whatever the scans. No Excel import: fingerprint → pandas → `hr.attendance`, with early check-ins moved to the shift start by an Odoo automation rule (§29) |
| Supervisors | attainment for workers, until IE is live | A list view per line of the period's worker inputs |
| Managers, director | scores for other roles | A list view per manager of their staff's inputs |
| Officer | entered lines; approvers sign them | Form and list views |
| IE (later) | `ie_units`, attainment with `source = ie` | `l10n_vn_payroll` calls `employee.ie_period_record(date)` (IE TD §14.3) only when the method exists, so there is no dependency either way |

---

## 11. Contracts on a payslip (PTD-08)

- **Period contracts:** every `hr.contract` of the employee overlapping the month, in state `open` or `close`. Core's `_get_contracts` searches open contracts only (`odoo/addons/hr_contract/models/hr_employee.py:105-119`), and writing a past `date_end` closes a contract at once (`hr_contract.py:323-326`), so a leaver's contract would be lost.
- **Main contract:** the period contract with the latest `date_start`. `get_payslip_vals` is overridden to set it as `contract_id` (OCA takes `employee.contract_id`, `oca/payroll/payroll/models/hr_payslip.py:641`), and `_get_employee_contracts` returns only it, so OCA's loop over contracts (`hr_payslip.py:577-612`) runs the rules once. **Built:** all these overrides act only on payslips whose structure has `l10n_vn_payroll` (*Vietnamese Pay Context*), so the instance's other structures keep OCA's behaviour.
- **Structure:** the main contract's `struct_id`.
- **Worked days:** `get_worked_day_lines` is overridden to write the input record's figures as worked-day lines (`PAID`, `WORKED`, `UNPAID`, and one per leave type), for display. OCA's calendar figures (`WORK100`, `hr_payslip.py:377-397`) are not produced.

## 12. The pay context

`hr.payslip._l10n_vn_context()` builds one plain structure per payslip; `get_payroll_dict` returns it under the key `vn` (so rules can read `payroll.vn`), and the rule type reads it directly (§17). Built for a whole run in bulk: parameters once per date, inputs, contracts and pay lines in one read each.

Steps, in order:

1. **Parameters** for the month (§4), read at the month's last day; a segment reads its own date for dated values.
2. **Segments:** the month is cut at every contract start or end and every pay line start or end. Each segment knows its contract, its lines and whether it is in probation (a clause's `trial_date_end`, or a probation contract). One segment needs no breakdown; several need input segments (§10.2).
3. **Standard days:** `vn.policy.std_days` (the variant from the month's schedule is not built).
4. **Attainment:** the input's `attainment`, capped. Missing while a variable component is in force → integrity error.
5. **Component lines** (§13).
6. **OT** (§14).
7. **Gross** = the sum of earning lines.
8. **SI, HI, UI, union** (§15).
9. **PIT** (§16.1).
10. **Damage compensation** (§16.2).
11. **Net** = gross − employee insurance − union dues − PIT − damage compensation.
12. **Advances** (§23.2): settled = min(paid unsettled advances, net); **to pay** = net − settled.
13. **Checks** (§19).

Each line in the context carries: component code, amount (rounded), and for display the quantity, unit amount, factor, segment dates, attainment and the period an adjustment belongs to.

## 13. Component lines

### 13.1 Per segment, for each pay line in force

```latex
\text{line} = \operatorname{round}\!\left(\text{amount} \times \frac{\text{days on its basis in the segment}}{\text{standard days}} \times r \times a\right)
```

- *amount* from the component's source (§5.2) at the segment's date;
- the basis is the component's proration: the segment's `paid_days`, `days_worked`, or the full amount (`none`); for `per_day` the line is amount × the segment's paid days, with no division;
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
- **Categories (built, PTD-17):** per day, day OT under `WD`, `RD` or `HOL` by the day's type; night OT (inside the calendar's night window, 22:00–06:00 by default) under `NWD` on a workday without day OT, `NWD_AFTER` on a workday with day OT, `NRD` on a rest day, `NHOL` on a holiday; normal hours at night under `NIGHT`, paid as a premium at the `NIGHT` factor. `NIGHT` hours are normal time: they stay out of `ot_hours` and the OT limits.
- **How much OT** is Odoo's: the day's overtime above the company tolerance (48 minutes), in full; approved overtime when Odoo's validation is on. A stay within the tolerance is no overtime but makes up lateness (`hr_attendance_day` step 2).
- **Combined shifts:** a calendar's *Hours per Paid Day* makes each shift worked a day (quilting: 16-hour calendar, 8 hours per paid day, no OT up to 16 hours, Peter 2026-11-08).
- **The daily limit (labour rule):** OT above `vn.ot.limit.day_share` × the day's scheduled hours on a workday, or beyond `vn.ot.limit.day_total` hours of work, at most the day's OT, is summed in `ot_over_daily_hours` and reported by `ot_limit`. It does not change PIT (§16.1). Days with more than 12 hours of work are counted in `long_days` (§19).

## 15. SI, HI, UI and union

1. **Liability (built).** The main contract's participant type gives the funds. Days without SI = the month's scheduled working days (whole month, main contract's calendar) − the paid days under contracts whose participant type has SI funds; contributions only when that is under `vn.si.absence_days`. One rule covers hires, leavers, probation contracts and long absences (TC-OPEN-2, TC-OPEN-12; Peter, 2026-11-03).
2. **Base (built).** `components`: the sum of the main contract's lines in force **on its last day in the month** flagged *in SI base*, at full amount (not prorated, no attainment, no probation rate); a daily rate counts × standard days (TC-OPEN-8); `declared`: the contract's declared base. Then the floor: the region's monthly minimum wage, or the reference level. A change of base inside the month applies from `[OPEN-04]`; until decided, the base on that last day.
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
- The exemption follows the monthly and yearly limits only; the daily limits are labour rules (Peter, 2026-11-08). Untaken-leave pay is exempt (Law 109/2025/QH15). The night premium on normal hours (`OT_NIGHT` in the garment configuration) is `exempt`, outside the OT hour limits.
- PIT = the bracket sum on *T* from `vn.pit.brackets`, rounded; 0 when *T* ≤ 0.

**Flat:** `flat_short`: 10% of gross when gross ≥ the threshold, else 0 (TC-OPEN-3); `flat_nonresident`: 20% of gross.

The payslip stores *E*, *T* and the method in the context (for the PIT statements, §25).

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
- `_get_lines_dict` sums totals into categories at full precision (`hr_payslip.py:532-541`). For `l10n_vn_component` rules the totals are already whole dong, so categories match. Other rule types, if a configuration mixes them in, are rounded half up in an override of `_get_lines_dict` before they are summed (PFG-06). **Built:** the rounding applies to Vietnamese payslips only; an `l10n_vn_component` rule's line is split into one payslip line per context line after OCA files it (one line per pay line and segment).
- Display fields on `hr.payslip.line`: `l10n_vn_hours`, `l10n_vn_factor`, `l10n_vn_unit_amount`, `l10n_vn_date_from`, `l10n_vn_date_to`, `l10n_vn_attainment`, `l10n_vn_period_ref`.

## 18. Snapshot (FR-10, FR-53)

`hr.payslip.l10n_vn_context` (Json) stores the whole context at calculation: parameter values with their dates, the input record's values, the pay lines and scale cells used, every line, the bases, the PIT figures and the check results. Recalculation replaces it while the run is open; after approval it is frozen with the payslip (§21). Reproducing a payslip means recomputing from the snapshot's inputs and comparing (FR-53).

## 19. Checks (PTD-11, FR-59)

### 19.1 Models

- `l10n_vn.payroll.check`: `code`, `name`, `kind` (`integrity` / `legal` / `policy`), `default_level` (`error` / `warning` / `note` / `off`), `per_component` (Boolean). Data records; each code has a method `_l10n_vn_check_<code>(context)` that returns findings.
- **Level** for a finding: `vn.check.<code>.<component>` if set, else `vn.check.<code>`, else `default_level`. Integrity checks are always `error` and ignore parameters.
- `l10n_vn.payroll.check.result`: `payslip_id`, `run_id`, `check_id`, `component_id`, `level`, `message`, `note`, `noted_by`. A warning needs a note before review; an error blocks review and approval (§20).

### 19.2 Catalogue

| Code | Kind | Default | Finds |
| --- | --- | --- | --- |
| `period_open` | integrity | error | attendance or IE not closed for the period, or days with an attendance without check-out |
| `negative_net` | integrity | error | net < 0 |
| `missing_ids` | integrity | error | a paid employee without a CCCD (`l10n_vn_personal_id`, SI number and tax code), or without a bank account when the participant type is `paid_by_transfer` (PTD-21) |
| `missing_attainment` | integrity | error | a variable component in force and no attainment or score |
| `missing_segments` | integrity | error | terms change in the month and no input segments |
| `unapproved_entry` | integrity | error | an entered line without an approver |
| `min_wage` | legal | error | salary lines in SI base for full normal hours below the region's minimum |
| `daily_min` | legal | error | a daily rate below the hourly minimum × the day's hours |
| `nature` | legal | warning | flags inconsistent with legal nature: a `welfare` component in the OT base, a `fixed_allowance` outside the SI base, a `variable_salary` that is not variable |
| `probation_length` | legal | warning | probation longer than `vn.probation.max_days` for the job, or a rate below `vn.probation.min_rate` |
| `deduction_kind` | legal | warning | a deduction component whose nature is not `statutory`, `union` or `damage` (FR-70) |
| `ot_limit` | legal | warning | month over 40 h, year over 300 h, or OT over the daily limit |
| `long_days` | legal | warning | days with more than 12 hours of work; the garment configuration sets it to `note` |
| `variable_constant` | policy | warning, per component | a variable component at 100% (or conditional paid in full) for `vn.policy.constant_months` months running; the garment module sets it to `note` for performance pay (Pay Policy §4.2, TC-F15) |
| `net_change` | policy | warning | net pay changed more than `vn.policy.net_change` from the previous month |
| `ie_scope` | policy | warning | IE units for an employee outside IE scope |
| `level_review` | policy | warning | a level line past its review date |
| `dependent_document` | policy | warning | a PIT dependent without its document |
| `advance_limit` | policy | warning | an advance above `vn.policy.advance_max_share` of the monthly amount, checked when the advance is approved |
| `advance_carried` | policy | warning | paid advances larger than the month's net pay; the excess carries forward |
| `contract_term` | legal | warning | a third fixed-term labour contract in a row for the employee; a training contract longer than 3 months (PTD-23) |
| `attendance_corrections` | policy | warning | days of the month with an attendance corrected by hand, with their reasons (PTD-22) |

---

## 20. Runs (FR-02, FR-08, FR-09, FR-11)

### 20.1 `hr.payslip.run` additions

| Field | Type | Notes |
| --- | --- | --- |
| `state` | Selection (`selection_add`) | adds `calculated`, `reviewed`, `approved`, `paid` after OCA's `draft`; OCA's `close` stays for the 2026 history runs |
| `l10n_vn_period_id` | Many2one `l10n_vn.payroll.period` | required for new runs; sets the dates |
| `l10n_vn_kind` | Selection | `regular` / `off_cycle` |
| `l10n_vn_calculated_by`, `_at` | Many2one `res.users`, Datetime | last calculation |
| `l10n_vn_reviewed_by`, `_at` | | |
| `l10n_vn_approved_by`, `_at` | | |
| `l10n_vn_move_id` | Many2one `account.move` | added by `l10n_vn_payroll_account` (§22) |
| `l10n_vn_check_result_ids` | One2many | the run's check results (§19) |

### 20.2 Transitions

| From → to | Who | Conditions | Effect |
| --- | --- | --- | --- |
| draft → calculated | Officer | the period's inputs are closed (§9) | generates missing payslips (one per employee with a period contract, skipping employees already paid in an off-cycle run of the period); calculates all; records who and when |
| calculated → calculated | Officer | | recalculates all, or selected payslips; repeatable (FR-09) |
| calculated → reviewed | Reviewer | no `error` results; every `warning` has a note | |
| reviewed → calculated | Reviewer or officer | | any recalculation sends the run back (FR-08 step 5) |
| reviewed → approved | Approver | the approver is not `l10n_vn_calculated_by` (FR-02, TC-F07) | payslips → `done` (OCA `action_payslip_done`, with the setting *prevent compute on confirm* on, so nothing recomputes); posting (§22); lock (§21); the period's state becomes `paid` once the run is paid |
| approved → paid | Officer, or automatic | every 3341 line of the run's entry is reconciled (§23) | |

There is no transition back from `approved` (FR-51).

**Off-cycle runs** (FR-11) are runs of kind `off_cycle` with chosen employees, the same transitions and the same period. The regular run skips an employee who has an approved off-cycle payslip in the period.

**Payslip creation** goes through OCA's `get_payslip_vals` with our contract choice (§11). OCA's batch wizard is replaced on our runs by the *Calculate* button, which finds the employees itself.

## 21. Lock and corrections (FR-30, FR-50, FR-51)

- **Lock.** Once its run is approved, a payslip and its lines, worked days and inputs refuse `write` and `unlink` for everyone, superuser writes from our own code excepted. OCA's *Set to draft* (`oca/payroll/payroll/models/hr_payslip.py:203`) and *Cancel* are refused on them; `payroll.allow_cancel_payslips` stays off.
- **Inputs.** The period's input records, segments and lines are read-only once its run is approved.
- **Pay lines.** A contract pay line used by an approved payslip keeps its component, amount, scale key and `date_from`; only a `date_to` on or after the last approved period's end may still be set.
- **Corrections** go into a later period as input lines with `period_ref` (§10.3), on the component being corrected, so they carry its flags (FR-30, TC-E01). An OT correction carries its hours, which count towards the limits of the month it belongs to (§16.1).
- **Damage decisions** cannot be deleted once a deduction was made from them.

## 22. Posting per run (`l10n_vn_payroll_account`, FR-44)

### 22.1 Configuration

| Model or field | Notes |
| --- | --- |
| `l10n_vn.payroll.cost.group` | `code`, `name`, `expense_account_id`, `company_id`. Garment data: `DIRECT` 6220, `FACTORY` 6271, `SELLING` 6411, `ADMIN` 6421. |
| `hr.department.l10n_vn_cost_group_id` | set by the accountant per department; no default |
| `l10n_vn.payroll.component` additions | `l10n_vn_debit` (`cost` / `payable` / `none`), `l10n_vn_credit_account_id` |
| `res.company` additions (in *Settings*) | `l10n_vn_payroll_journal_id`, `l10n_vn_payroll_payable_account_id` (3341) |

### 22.2 What each component posts

| Component kind | Debit | Credit | Partner |
| --- | --- | --- | --- |
| Earning | the employee's cost group account | 3341 | employee's contact on 3341 |
| Employee deduction (SI, HI, UI, dues, PIT, damage) | 3341 | its credit account (33831, 33841, 33861, the employee union dues account, 33351, damage account) | employee on 3341; the component's register partner on the credit |
| Advance settlement, to pay (`ADVANCE`, `TO_PAY`) | — | — | settled by reconciliation (§23.2) |
| Employer contribution | cost group account | its credit account (33831 for pension, sickness and accident; 33841; 33861; 33821) | register partner |
| Total, info | — | — | — |

The union dues and damage accounts are set by the accountant (Requirements OPEN-08).

### 22.3 The entry

- One `account.move` per run, in the payroll journal, dated the period's last day, created and posted at approval.
- Expense and liability lines are summed by account, cost group and partner; 3341 lines stay one credit (gross) and one debit per deduction per employee.
- After posting, each employee's 3341 debits are reconciled against the gross credit: the run's deduction lines and the employee's open advance debits, oldest first, so the open residual is the amount remaining to pay (Agreed 2026-10-31). OCA's own posting (`oca/payroll/payroll_account/models/hr_payslip.py:46-134`) produces nothing, because our rules carry no accounts (`:130`).
- Integrity checks before approval: every employee's department has a cost group; every posting component has its accounts; the payroll journal and payable account are set.

## 23. Payment, bank file and advances (FR-43, FR-71)

**v0.6:** this section moves to `l10n_vn_payroll_payment` (PTD-24): advances and payment lists no longer need the accounting module. Posting an advance's payment (Dr 3341 / Cr bank) is `l10n_vn_payroll_account`'s, for the participant types that are posted.

### 23.1 Payday

- A payment mode in the garment module uses a new payment method code `l10n_vn_bank_xlsx`, bank journal set by the accountant.
- The officer creates an `account.payment.order` and adds the run's open 3341 lines with OCA's line wizard. Each line takes the employee's `bank_account_id` (a `res.partner.bank` of the employee's contact).
- `account.payment.order.generate_payment_file` returns `(False, False)` for *manual* and raises for unknown codes (`oca/bank-payment/account_payment_order/models/account_payment_order.py:381-392`). `l10n_vn_payroll_account` overrides it for `l10n_vn_bank_xlsx`: it renders the payment mode's `excel_import_export` template (`xlsx.export.export_xlsx`, `oca/server-tools/excel_import_export/models/xlsx_export.py:254`) and returns the file. Each bank's layout is a template, so a new bank needs no code (OPEN-06).
- When the order's payments post and reconcile, the run moves to `paid` (§20.2).
- An employee without a bank account is an integrity error at review (`missing_ids`, §19), so no one drops silently out of the file.

### 23.2 Salary advances (PTD-16)

`l10n_vn.payroll.advance`:

| Field | Type | Notes |
| --- | --- | --- |
| `employee_id`, `company_id` | | |
| `date` | Date | payment date requested |
| `amount` | Monetary | |
| `reason` | Char | |
| `state` | Selection | `draft` / `approved` / `paid` / `settled` / `cancelled` |
| `approved_by`, `approved_at` | | reviewer group (Pay Policy OPEN-22) |
| `limit_note` | Char | required when `advance_limit` fires (§19) |
| `payment_line_id` | Many2one `account.payment.line` | the payment order line that pays it |
| `move_line_id` | Many2one `account.move.line` | its 3341 debit, from the payment |
| `settled_amount`, `balance` | Monetary, computed | from the 3341 debit's reconciliation |
| `period_id` | Many2one | the period it belongs to |

- **Batch:** a wizard creates draft advances for chosen employees (filter by pay group, department), with a fixed amount or a share of each one's monthly amount; the reviewer approves them together.
- **Payment.** A button on the payment order adds approved advances as payment lines (`l10n_vn_advance_id` on `account.payment.line`, no journal item). OCA gives a line without a journal item the partner's default payable account (`oca/bank-payment/account_payment_order/models/account_payment_line.py:232-241`), which would book 331. `l10n_vn_payroll_account` overrides `_prepare_account_payment_vals` so that an advance line's payment uses the company's payroll payable account (3341): the payment posts Dr 3341 (employee) / Cr bank. The advance becomes `paid` and records that 3341 debit. The bank file is the same template as payday.
- **Settlement.** The month's payslip reads the employee's paid advances with an open balance, oldest first (§12 step 12). It shows `ADVANCE` (settled, capped at net) and `TO_PAY`. At run posting, those 3341 debits are reconciled against the gross credit (§22.3), which settles them in the books; no extra entry is posted. An advance is `settled` when its debit is fully reconciled.
- **Carry-forward.** An unsettled balance stays an open 3341 debit and is settled first by the next payslip (TC-G15). For a leaver's final payslip it stays open and is listed for the accountant.
- **Limit** at approval: `vn.policy.advance_max_share` × (base + variable components at 100%) − advances already approved in the period; above it, `advance_limit` warns and the approver writes `limit_note` (TC-F16).
- **Advances in cash** are recorded by the accountant as a core payment from the cash journal with 3341 as destination account, then linked to the advance; the settlement is the same.

## 24. Payslip report (FR-41, FR-42)

- A QWeb PDF report on `hr.payslip`, in place of OCA's `report_payslip`. Sections follow `component.section`; each line prints its Vietnamese and English name (the component's `name` read in `vi_VN` and `en_US`), and where set its hours × factor × unit amount, the segment dates, the attainment or score, and the period of an adjustment.
- The header holds employee, period, SI base, paid and unpaid days, OT and night hours; the footer net pay. Employer lines are not printed.
- Printing from the run produces one PDF for all its payslips. Sending (OCA's payslip mail template, the portal or Zalo) waits for OPEN-01.

## 25. Statutory statements (FR-45, FR-46, FR-47, FR-66)

### 25.1 `l10n_vn.payroll.statement`

| Field | Notes |
| --- | --- |
| `kind` | `si_monthly` (contribution list), `si_changes` (joiners, leavers, base changes, long absences, maternity), `pit_period` (withholding return), `pit_annual` (finalisation), `pit_certificate`, `union` |
| `date_from`, `date_to`, `company_id` | a month, a quarter or a year |
| `line_ids` | `l10n_vn.payroll.statement.line` |
| `state` | `draft` / `done`; regenerating a draft replaces its lines |

`l10n_vn.payroll.statement.line` holds one row per employee: `employee_id`, `ssnid`, `tax_code`, `change_type`, `change_date`, `si_base`, the employee and employer amounts per fund, `income_total`, `income_exempt`, `insurance`, `dependents`, `family_deduction`, `taxable`, `pit`, `pit_method`, `months`, `note`.

- **Source:** approved payslips' snapshots (§18), so a statement never recalculates pay. Year-to-date figures add the opening data (§25.2).
- **Change list:** joiners and leavers from contract dates and participant types; base changes from the SI base in consecutive months; long absences and maternity from `si_absence_days` and leave types.
- **Output (built v1):** plain lists: each statement's lines, exported with Odoo's own export. The filing tools' layouts become `excel_import_export` templates once Peter provides them (PTD-OPEN-08); no code change. Kinds built: `si_monthly`, `si_changes`, `pit_period`, `pit_annual`, `ot_schedule` (Decree 253 OT schedule, FR-46), `union`; the PIT certificate is the employee's annual line, printed later with its form.

### 25.2 `l10n_vn.payroll.opening` (FR-66)

Per employee and year, for the months before go-live: `income_total`, `income_exempt`, `insurance`, `family_deduction`, `taxable`, `pit`, `ot_hours`, `months`. Imported once from the records kept outside Odoo. The first input's `ot_hours_ytd` and the annual statements read it.

## 26. Reports (FR-48, FR-49)

- **Payroll register, cost by department and line, OT against the limits, incentive cost, change from the previous month:** list, pivot and graph views on `hr.payslip.line`, with stored fields added for reporting: `l10n_vn_period_id`, `l10n_vn_department_id`, `l10n_vn_cost_group_id`, `l10n_vn_pay_group`, `l10n_vn_section`. Excel through the views' export, or a template where a fixed layout is wanted.
- **Labour cost for IE** (FR-49): `l10n_vn.payroll.period._l10n_vn_labour_cost()` returns base wages, productivity and performance pay, incentive and OT cost of the period's approved runs, by line where the department maps to a line. IE's valuation (IE chunk 4) calls it when payroll is installed; payroll does not depend on IE.

## 27. Audit (FR-50, FR-54)

`auditlog` rules, shipped by the garment module (configuration, not code):

| Model | Read | Write, create, delete | Export |
| --- | --- | --- | --- |
| `hr.payslip`, `hr.payslip.line` | yes | yes | yes |
| `l10n_vn.payroll.contract.line` | yes | yes | yes |
| `l10n_vn.payroll.input`, `.input.line`, `.input.segment` | no | yes | yes |
| `l10n_vn.payroll.damage`, `.component`, `.scale.cell`, `.participant.type` | no | yes | no |
| `hr.contract`, `hr.employee` | no | yes (pay fields) | yes |
| `base.time.parameter.version` | no | yes | no |

Read logging on payslips and pay lines answers "who looked at pay" (FR-54). Volume is about 300 payslips a month; read logs are kept `[P 2 years]` with `auditlog`'s autovacuum.

## 28. The garment configuration (`l10n_vn_payroll_garment`)

Built 2026-11-08, before `l10n_vn_payroll_account` (Peter, 2026-11-07); `docs/modules/l10n_vn_payroll_garment.md` steps 1 and 5.

### 28.1 Loading (PTD-18)

- A payroll manager loads the scheme into a company from *Settings → Payroll → Load Garment Pay Scheme*. Nothing is created at install: components, scales, parameters, rules and structures belong to one company, the trading company is Vietnamese too, and the public repository names no company.
- Every record is matched by code and kept as it is when found; the loader only creates and reports what it created and kept. Loading again adds what a later version ships.
- Names are written in English and, when Vietnamese is active, in Vietnamese.

### 28.2 Components

| Group | Components |
| --- | --- |
| Pay lines | `BASE` (parameter `vn.policy.base_salary`, SI and OT base, sets the wage), `PROD` (scale `PROD`, variable, supervisor), `PERF` (remainder of scale `GRADE`, variable, manager), `DAILY` (line, per day). Probation applies to these and to `DUTY` |
| OT | `OT_WD`, `OT_RD`, `OT_HOL`; `OT_NIGHT` (PIT `exempt`); `OT_NWD`, `OT_NWD_AFTER`, `OT_NRD`, `OT_NHOL`. All active: night pay is statutory |
| Entered | `EFF` (until IE), `ONE`, `ANNUAL`, `LEAVE` (PIT `exempt`) |
| Options, inactive | `ATT` (amount from `vn.policy.attendance_bonus`, attendance condition), `DUTY` (fixed allowance, SI base), `PHONE` (welfare, PIT `exempt`); each with its rule, switched on by unarchiving it |
| Engine | `GROSS`, `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT`, `DAMAGE`, `NET`, `ADVANCE`, `TO_PAY`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE` |

Not shipped: `KPI` (as `ONE`) and `SUPP` (no such pay in use).

### 28.3 Other data

- **Scales:** `PROD` (Entry 800,000 to S4 2,800,000) and `GRADE` (G1-1 to G5-3, Pay Policy §4.1's placeholders; G6 on the pay line), versions from 2026-01-01.
- **Categories** `EARN`, `DED`, `ER`, `TOTAL`, a shared one reused when found; **structure** `VN_GARMENT` with one `l10n_vn_component` rule per component.
- **Parameters and check levels:** §4.3.

### 28.4 Later steps

**Step 6 (v0.6, for November 2026):** `BASE` from a dated scale `BASE` by group (PTD-25), replacing the parameter `vn.policy.base_salary`; a training-allowance component `TRAIN` (amount on the line, paid days, taxable, outside SI and the OT base); the contract types Labour, Probation, Training and Casual with their participant types (PTD-19). `auditlog` rules (§27; step 2), pay lines proposed on the contract and the go-live helper (§7, §29 step 4; step 3), and the account mapping: cost groups, component accounts, journal, contribution registers (§22; step 4, after `l10n_vn_payroll_account`).

## 29. Go-live and clean-up

| Step | What | Who |
| --- | --- | --- |
| 1 | Install `base_time_parameter`, `hr_employee_relative`, then `base_time_parameter_strict`, `hr_attendance_day`, `l10n_vn_payroll`, `l10n_vn_payroll_garment` (later `l10n_vn_payroll_account`), one at a time; load the garment scheme in the garment company (§28.1) | Peter |
| 1b | Attendance: *Tolerance Time In Favor Of Company* 48 and *In Favor Of Employee* 5 minutes, set once the last month paid by the old rules is closed (changing them recomputes all past overtime); an automation rule on attendance creation running the *Normalize Attendance* code; public holidays as whole days (00:00–23:59), so they cover every calendar; quilting's calendar *Hours per Paid Day* 8; no flexible calendars and no shifts crossing midnight (PTD-OPEN-10); pay groups filled, so office staff are in *exception* mode | Peter, HR |
| 1c | Go-live data for November (Peter, 2026-11-11): contract types renamed and created (Labour, Probation, Training, Casual) with their participant types; every employee's CCCD; a bank account for every labour, probation and training contract; contracts cancelled for employees who worked corrected to end on their departure date; workers' base 4,500,000 and the other groups' bases set in the `BASE` scale; casual workers paid monthly | Peter, HR |

**Build order to go-live** (Peter, 2026-11-12): `l10n_vn_payroll_payment` (advances, payment lists) → `l10n_vn_payroll_account` (posting per run of payslips whose participant type is `posted`, 3341 reconciliation, payment entries) → garment step 4 (account mapping by account code) → go-live scripts outside `addons/` (attendance settings, contract types and participant types, pay lines from wages, structure, corrected cancelled contracts, the month's entered lines) → **October rehearsal on `prod_copy`**: install, load the garment scheme, calculate, review, approve, pay and post October, compared with the old run 11 (233 payslips) and with the entry's 3341 balance per employee → November on production, payday 10 December 2026. Built so far (2026-11-12): `l10n_vn_payroll` steps 1–11, `hr_attendance_day` steps 1–3, `l10n_vn_payroll_garment` steps 1, 5, 6. From the accountant before the rehearsal: expense accounts by department group (622/627, 641, 642, Circular 99), the union-dues sub-account under 3388, the damage-compensation account, and confirmation of 3341 credited gross and reconciled per employee (PTD-13).
| 2 | Review Payroll Manager and Officer members (PFG-OPEN-04); the new-user template is fixed by step 1 | Peter |
| 3 | Fill SI numbers, bank accounts, pay groups, regions, union membership, dependents | HR |
| 4 | Contract set-up: participant type and pay lines for every open contract. A helper run through `odoo shell` (kept outside `addons/`, like the IE prototype) proposes lines from today's `wage`: workers' level from `wage − 3,700,000`, other roles' grade and step for HR to assign (Pay Policy OPEN-20). HR confirms each contract. | HR, with the helper |
| 5 | Department cost groups, accounts check, payment mode and bank template | Accountant |
| 6 | Opening data for 2026 (§25.2) | Accountant |
| 7 | Archive the old structures and rules (`MINW`, `BNOT`, `PALV`, `BNPC`, `COMD`, `BONP`, `NET`, the daily ones); cancel the May 2026 payslips in *verify* (PFG-OPEN-03) | Peter |
| 8 | First live month: build and close the summaries, enter attainment and entered lines, calculate, review every payslip line by line (group H), approve, pay | Payroll team |
| 9 | Retire the hand-made fields `x_status` and `x_bonus_amount` once nothing reads them | Peter |

## 30. Test strategy

- **Where:** engine tests in `l10n_vn_payroll` build the reference configuration in their fixtures and run groups A–F of the acceptance cases; `l10n_vn_payroll_garment` runs group G on its own data; `l10n_vn_payroll_account` tests the entry and the payment file.
- **Expected values:** `payroll_reference_calc.py` gains an option to write every case's expected lines and totals to a JSON file in the module's `tests/data/`; tests assert each line, gross, net, SI base, PIT exempt and taxable figures, and employer contributions to the dong. Regenerated whenever a case changes, never edited by hand.
- **Workflow and checks:** F01–F15 as tests on runs; the lock (FR-51) by attempting writes after approval; segregation by the preparer trying to approve.
- **Access:** each role tested as a user of that role with a positive control (the same user succeeding at an allowed action), including a non-payroll HR user failing to read pay lines.
- **Posting:** the run entry balances; 3341 residual per employee equals net pay less advances settled; partners on 3341 and 338x; cost groups by department.
- **Advances:** TC-G14 and TC-G15, through payment (Dr 3341 / Cr bank), settlement on the payslip and the 3341 reconciliation.
- **Tags:** fixtures create employees, whose contacts are `res.partner` records, so the tests are `post_install`. No `HttpCase`; no imports from core `tests` packages.
- **Performance:** before go-live, a run of `[P 3,000]` generated payslips on a copy, timed against FR-52.


## 31. Open items

| ID | Item | Proposal |
| --- | --- | --- |
| PTD-OPEN-01 | IE adopts `base_time_parameter_strict` instead of `ie.parameter` | Yes; one reader for both suites (a proposal to the IE technical design) |
| PTD-OPEN-02 | Probation recording (PFG-OPEN-02) | Both forms supported (§7) |
| PTD-OPEN-03 | The SI base when it changes inside a month (Requirements OPEN-04) | Until decided: the base on the main contract's last day in the month (§15, built) |
| PTD-OPEN-04 | OT in a split month without OT hours per segment | Last segment's OT base (§14); **built**: the summary gives every segment its OT hours, so this applies only to segments entered by hand |
| PTD-OPEN-05 | Untaken-leave pay computed from the leave balance | v1: entered by the officer (§13.4) |
| PTD-OPEN-06 | 3341 posting | **Closed:** gross with deductions and advances reconciled against it (Peter, 2026-10-31) |
| PTD-OPEN-07 | Accounts for union dues and damage compensation (Requirements OPEN-08) | Union: employer fee on 33821, employee dues on a separate detailed account under 3388, e.g. 338811 (decided, Peter 2026-10-31; code by the accountant). Damage account: accountant. Until set, the integrity check blocks a run that needs them. |
| PTD-OPEN-08 | The SI filing service's import layout and the 2026 PIT forms | **Deferred:** Peter provides the layouts later. Until then the statements exist as plain lists; the import-ready templates are added without code (§25). **Built:** plain lists (§25). |
| PTD-OPEN-09 | Advance limit, approver and dates (Pay Policy OPEN-22) | 50% of the monthly amount; HR manager; the 15th or on request |
| PTD-OPEN-10 | Calendars `hr_attendance_day` cannot measure: flexible calendars (Odoo's flexible overtime ignores both tolerances) and shifts crossing midnight (Odoo's overtime reads expected hours only to midnight, `hr_attendance/models/hr_attendance.py:394-395`) | None on the instance once employee 496 moved to a fixed 3-hour calendar (2026-11-08); a calendar of real fixed hours instead |

## 32. Proposals to the business documents

| Document | Proposal |
| --- | --- |
| Requirements §9 | Monthly attendance totals come from Odoo's own attendance through `hr_attendance_day` and the monthly summary (built); closing attendance for the month freezes them. Segments are computed. *(Was: imported until the attendance module is live.)* |
| Attendance Specification | v0.5: Route A status (attendance design note v0.2); rosters, off-site registration, OT approval windows and the exception queue deferred; the grace period and OT minimum are Odoo's tolerances; hours per paid day for combined shifts |
| Regulation Reference | v0.3: the OT exemption within the monthly and yearly limits only, the daily limits labour rules; untaken-leave pay exempt (Law 109/2025/QH15); `vn.ot.limit.day_share`, `vn.ot.limit.day_total` |
| IE Technical Design | Attended minutes from `hr.employee._attendance_days()` (normal + overtime hours); proposal P-01 obsolete |
| Requirements FR-59 | Check levels are parameters `vn.check.<code>[.<component>]`. |
| Acceptance Test Cases | The employer pension, sickness and accident lines are separate (FR-22). **Done:** Acceptance Test Cases v0.6 (2026-11-03). |
| IE Technical Design TD-13 | Use `base_time_parameter_strict` (PTD-02). |
| IE Technical Design chunk 4 | Valuation reads payroll's labour cost through `_l10n_vn_labour_cost()` when payroll is installed (§26). |
| Requirements FR-44 | Department cost groups and component accounts (§22), and 3341 reconciled to net per employee. |
| Acceptance Test Cases | Add posting and payment cases: the run entry for TC-G01, TC-G10 and TC-G13 together, and the bank file for them. |

## 33. As built: corrections from the modules

Building and testing `l10n_vn_payroll` (steps 1–10.1, 236 tests, UI-checked by Peter), `l10n_vn_payroll_garment` (steps 1 and 5, 25 tests) and `hr_attendance_day` (steps 1–2, 18 tests) corrected this design in the places below. The rows are the module doc's divergences (`docs/modules/l10n_vn_payroll.md`), whose decisions D1–D89 give the detail; the sections above are updated where a correction changes their text. Where this table and a section above disagree, this table and the module doc are right.

| # | Design | As built | Reason |
| --- | --- | --- | --- |
| 1 | §1, §4.2: statutory parameters ship with no company | created for every company whose country is Vietnam, and kept up to date at every install and upgrade (D9) | OCA's global rule on parameters, `[('company_id', 'in', company_ids)]` (`oca/server-tools/base_time_parameter/security/security.xml:6-13`), matches no parameter without a company, so they would show on no screen (`base_time_parameter_strict` divergence 1) |
| 2 | §3.2: officers, reviewers and readers read parameters | only payroll managers see parameters, through OCA's *Manage Time Parameters* group, which their group now implies (D7) | The calculation reads parameters as superuser (`base_time_parameter_strict` D1), so other roles need no access; the design's convention of not granting another module's models through `ir.model.access` rows is kept |
| 3 | §7: `wage` follows "the base salary line" | follows the lines whose component has `sets_wage` (D5) | The design names no field that marks the base salary component |
| 4 | §3.2: approver and reader read payslips | in step 7, with the run workflow | Their access is tested where they use it, approving and reading runs |
| 5 | §8.1: participant types without a word on companies | one list for all companies, no `company_id` (step 2, D12) | They describe the law's participant categories, which are the same for every Vietnamese company |
| 6 | §8.3: the region defaults from `vn.policy.region` | the same, and left empty when the company has no such parameter (step 2, D15) | The parameter ships with the garment module; before it, a guessed region would be wrong for a company in another region |
| 7 | §10.4: attendance totals imported from Excel until the attendance module exists | built from core's `hr.attendance`, approved leave and the contracts' working calendars (step 3, D20) | Peter, 2026-11-02: the fingerprint → pandas → `hr.attendance` pipeline, with early check-ins trimmed and the calendar's breaks, already gives the right time; payroll reads it rather than a second file. The Attendance Specification's own engine is not needed for payroll v1 |
| 8 | §10.2: segments entered by hand when terms change | computed by the summary from the daily figures (step 3, D24) | The summary works day by day, so it can cut the month at contract and pay line dates itself |
| 9 | §10.4: supervisors and managers enter attainment and scores in their own lists | the payroll officer enters them in an editable list (step 3, D27) | A role for supervisors needs record rules per department and field-level write limits; it waits until the officer's list proves too slow |
| 10 | §10.1: late arrivals from attendance | not computed; the field stays for the attendance bonus, inactive in the current scheme (step 3) | Core has no notion of lateness, and nothing in the current scheme uses it |
| 11 | §14: night hours | not computed (step 3) | No work after 22:00, none planned (Peter, 2026-11-02); the night components and factors stay available |
| 12 | §12 step 3: standard days from `vn.policy.std_days.mode` and `vn.policy.std_days` | `vn.policy.std_days` only (step 4, D36) | The current scheme is fixed at 26 (Pay Policy); the variant from the month's schedule has no case yet (TC-B07) and comes with it |
| 13 | §13.1: a `none` line computed per segment | paid once a month, from the last piece in which the component has a pay line (step 4, D36) | Computed per segment, a fixed amount is paid twice in a split month |
| 14 | §13.1: one payslip line per pay line per segment; §17.1: one rule per component | both: after OCA files the rule's line, it is split into one payslip line per context line (step 4, D43) | OCA files one line per rule and contract (`oca/payroll/payroll/models/hr_payslip.py:524`), so a rule alone cannot show a probation split (TC-C02, TC-C06) |
| 15 | §11: the payslip overrides apply to every payslip | only to payslips whose structure has `l10n_vn_payroll` (step 4, D30) | The instance's own structures (`MINW`, `BNOT` …) run in the same company until go-live (§29 step 7); their contract choice and `WORK100` worked days must not change |
| 16 | §10.2: segments cut at contract and pay line dates | also the day after a probation clause ends (step 4, D33) | §12 step 2 needs each segment to know whether it is in probation, and a clause ends inside a contract |
| 17 | §15.1: no contribution when `si_absence_days` ≥ 14, and a separate rule for a contract starting mid-month | one rule: the month's scheduled days less the paid days under contracts with SI funds; contributions when that is under `vn.si.absence_days` (step 5, D47) | `si_absence_days` counts only days of employment, so a leaver who worked 10 days would contribute (TC-OPEN-12 says not); one count covers hires, leavers and probation contracts (Peter, 2026-11-03) |
| 18 | §15.2: the SI base from the lines in force at the month's end | on the main contract's last day in the month (step 5, D49) | A leaver's contract has no line in force at the month's end (Peter, 2026-11-03) |
| 19 | §15.2: the SI base from the lines at full amount | a `per_day` line counts at its daily rate × `vn.policy.std_days` (step 5, D49) | TC-OPEN-8's assumption; the company pays no one daily today, so the rule is untested in use (Peter, 2026-11-03) |
| 20 | §16.1: `exempt_cap` lines up to their cap | the cap applies once per cap parameter, over all the lines that name it (step 5, D54) | A meal allowance and its correction share one monthly cap (Peter, 2026-11-03) |
| 21 | §16.2: `deducted` = the sum of `DAMAGE` lines on done payslips | allocation records per decision and payslip (step 5, D55) | A payslip's one `DAMAGE` line cannot say how much it took from each of several decisions |
| 22 | §12: the sign of deduction lines unstated | deductions negative, employer contributions positive (step 5, D51) | The test cases show deductions with a minus, and OCA's categories then add up to net pay |
| 23 | §19.2: the catalogue | adds `calculation` (integrity): every stop of the pay context that no other code names — dates, contract, monthly input, participant type, region, scheduled days, OT without a component, a component without a rule, a missing engine component (step 6, D62) | Each stop needs a result to land on, and these are all data or configuration to put right before the payslip can be calculated |
| 24 | §19.2: `probation_length` against the limit for the job | a field on the contract, `l10n_vn_probation_job`, gives the job's category; the length is checked only when it is set (step 6, D68) | Nothing on the instance classifies jobs by qualification (Labor Code Art. 25) |
| 25 | §19.2: `ie_scope`, IE units for an employee outside IE scope | outside scope = pay group other than *Worker* (step 6, D66) | IE is not installed and the pay group is the only scope there is. TC-F06's "not paid unless confirmed" is the warning's note before review (step 7); the units are paid |
| 26 | Requirements §7: a component without SI, OT, PIT or proration settings | no check: such a component cannot be saved (D3) | A run never meets one |
| 27 | §19.2: `advance_limit` | the catalogue record ships here; its finder comes with `l10n_vn_payroll_account`, which approves advances | Advances are that module's |
| 28 | §19, D44, D52: integrity stops raise an error that ends the calculation | recorded as error results; a stopped payslip keeps no lines and the batch goes on (step 6, D62) | TC-F12: the run cannot be calculated *for her*; the other employees must not wait |
| 29 | §8.3 and PFG-13: the personal tax code in core's `identification_id` | a field for the national ID number, `hr.employee.l10n_vn_personal_id`, used as the tax code (step 6, D70) | On the instance OCA's `hr_employee_id` fills `identification_id` with the employee number (374 of 375 employees, values like `22` or `A00039`), so neither the tax code nor the national ID has a field; since 1 July 2025 the personal identification number is the tax code, so one field serves both (found by `test_missing_ids`; Peter, 2026-11-04) |
| 30 | §20.2: payslips confirmed with OCA's setting *prevent compute on confirm* on | confirmed with the context key `without_compute_sheet`, the setting left as it is (step 7, D74) | OCA skips the recalculation for that key (`oca/payroll/payroll/models/hr_payslip.py:206-212`), so approval never depends on a company-wide setting someone may change |
| 31 | §21: the period's inputs read-only once its run is approved | an input is read-only once a payslip that read it sits in an approved or paid run (step 7, D76) | An approved off-cycle run covers a few employees; their inputs lock, the others stay open for the regular run |
| 32 | §20.2: the run carries the workflow, nothing on runs' access | officers create and calculate runs; reviewers, approvers and readers read them (step 7, D78) | OCA grants `hr.payslip.run` to payroll managers only (`oca/payroll/payroll/security/ir.model.access.csv:10`), so an officer could not open a run |
| 33 | §24: a payslip report alone | totals on the payslip, an analysis view and Excel templates beside it, all reading the same approved figures (step 8, D79–D84) | Peter works payroll in Excel through `excel_import_export`; Labor Code Art. 95(3) needs a statement per employee per payment, the accountant a register, HR a signed attendance sheet (Peter, 2026-11-07) |
| 34 | §25.1: each kind with an `excel_import_export` template in the filing tool's layout | plain lists: the statement's lines, exported with Odoo's own export (step 9, D86) | The SI e-declaration and tax portal layouts are not available yet (PTD-OPEN-08, Peter 2026-11-07); a template is added later without code |
| 35 | §25.1 kinds: `pit_certificate`; no OT schedule | no `pit_certificate` kind, its figures are the annual statement's line for the employee; an `ot_schedule` kind for the OT hours and amounts Decree 253 requires (FR-46) (step 9, D85) | The certificate is a printed document from the annual figures, added with its form; FR-46 names the OT schedule, §25.1 does not |
| 36 | §25.2 and FR-66: opening data with leave balances and dependents | income, PIT, insurance and OT hours only (step 9, D88) | Leave balances live in core's time off allocations and dependents on the employee's relatives (step 2); both are entered there |
| 37 | §1: no dependency on the attendance module | `l10n_vn_payroll` depends on `hr_attendance_day` (step 10) | Attendance design note v0.2 (Peter, 2026-11-08): time rules in the attendance module, pricing in payroll |
| 38 | §10.4: OT counted from `vn.policy.ot_min_hours_day` per day | Odoo's company tolerance (48 minutes) decides it; the parameter is retired (step 10) | One OT figure, Odoo's; a stay within the tolerance still makes up lateness (`hr_attendance_day` step 2) |
| 39 | §10.1 and divergence 10: late arrivals not computed | days late beyond the grace period (Odoo's employee tolerance, 5 minutes), scan mode only (step 10) | `hr_attendance_day` computes them; the attendance bonus needs them |
| 40 | §14 and divergence 11: night hours not computed | `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL` from the day figures; `NIGHT` out of the OT totals (step 10) | Quilting works past 22:00; the module captures night time even where none is planned |
| 41 | §19.2: `ot_limit` against the monthly and yearly limits | also the daily limit, at most the day's OT; a labour rule, PIT unchanged (steps 10, 10.1) | Labor Code Art. 107; the exemption follows the monthly and yearly limits only (Peter, 2026-11-08) |
| 42 | §19.2: the catalogue | adds `long_days`: days with more than 12 hours of work (step 10) | Quilting's double shifts: reported, never enforced |

**From `l10n_vn_payroll_garment`** (its module doc's divergences):

| # | Design | As built | Reason |
| --- | --- | --- | --- |
| G1 | §1: depends on `l10n_vn_payroll_account` and `auditlog` | `l10n_vn_payroll` only; the others with later steps | Built first (Peter, 2026-11-07) |
| G2 | §28: data files and a `post_init_hook` | a loader per company from *Settings* (PTD-18) | Per-company records in a two-company database; the public repository names no company |
| G3 | §28.1: eight OT components; `ATT`, `KPI`, `SUPP`, `DUTY`, `PHONE` inactive | day and night OT active; `ATT`, `DUTY`, `PHONE` inactive options; no `KPI` or `SUPP` | Night pay is statutory; options kept apart from the target policy (Peter, 2026-11-07) |
| G4 | §4.3: `std_days.mode`, `ot_supplement`, `unit_rate`, `attendance_late_max`, `advance_max_share` | not created | Each is set when its feature is used |
| G5 | §28.1: `ATT` from the pay line | from `vn.policy.attendance_bonus` | One amount for every worker |
| G6 | §28.2: versions from the go-live month | from 2026-01-01 | The go-live month is open (Pay Policy OPEN-16) |
| G7 | §28.1: `OT_NIGHT` exempt within the OT limits | fully `exempt` (step 5) | A premium on normal hours, not OT hours |

**From `hr_attendance_day`:** shifts crossing midnight and flexible calendars are not supported (PTD-OPEN-10); a stay within Odoo's company tolerance makes up lateness without counting as overtime (step 2, found by the May 2026 comparison).

**Also settled while building** (decisions, not departures): the pay context is computed in `Decimal` and rounded once per line, half up (D36); deductions show negative (D51); integrity stops become check results so a batch goes on (D62); the national ID number, `l10n_vn_personal_id`, serves as the tax code (D70); approval confirms payslips without recalculation and an employee is paid by one approved run per month (D74); every report reads the payslip's frozen totals (D79–D84).

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-30 | Chunks 1 and 2: decisions PTD-01 to PTD-11, modules, groups and access, parameters, components, scales, pay lines, participant types, people data, periods and inputs, contract selection, the pay context, component lines, OT, SI, PIT, damage compensation, rule type, exact lines, snapshot, checks. |
| 0.2 | 2026-10-30 | Chunk 3 (§20–§30): run states and segregation, lock and corrections, posting per run, payment and bank file, payslip report, statutory statements and opening data, reports and IE labour cost, audit, the garment configuration, go-live, test strategy; PTD-12 to PTD-15. Chunks 1–2 corrected: `per_day` proration, `ie_units` source, individual amounts on scale lines, adjustments on any component, `report_xlsx` dropped for `excel_import_export` templates. Open items and proposals renumbered to §31–§32. |
| 0.3 | 2026-10-31 | Salary advances (PTD-16, §23.2): model, batch, payment through the payment order with an override to 3341, settlement by reconciliation, carry-forward, limit check; `ADVANCE` and `TO_PAY` components; access, pay-context step, checks, garment components and tests updated. PTD-OPEN-06 closed (3341 gross, Agreed); union fee and dues on separate accounts (PTD-OPEN-07); statement layouts deferred (PTD-OPEN-08); PTD-OPEN-09 added. |
| 0.4 | 2026-11-07 | Corrected against the built `l10n_vn_payroll` (steps 1–9): statutory parameters per Vietnamese company (§1, §4.2); the monthly summary from Odoo's attendance replaces the Excel import (§10.4); the overrides gated by the structure's *Vietnamese Pay Context* (§11); the 14-day rule over the whole month and the SI base on the main contract's last day (§15); rounding and the split of lines (§17.2); statements as plain lists until the filing layouts arrive (§25); PTD-OPEN-03, -04, -08 updated; Requirements §9 proposal reworded; §33 lists all 36 corrections. |
| 0.5 | 2026-11-08 | Time from Odoo's attendance through `hr_attendance_day` (PTD-17; §1, §10, §14, §29); the garment configuration as built, loaded per company (PTD-18; §4.3, §28); the daily OT limit and `long_days` (§4.2, §14, §19); PIT: the OT exemption within the monthly and yearly limits only, untaken-leave pay exempt, the night premium exempt (§16.1); go-live attendance settings (§29 step 1b); PTD-OPEN-10; proposals to the Attendance Specification, Regulation Reference and IE; §33 rows 37–42, G1–G7. |
| 0.6 | 2026-11-12 | Go-live design for November 2026 (Peter, 2026-11-11 and 2026-11-12): contract types giving participant types, `TRAINING` and `CASUAL`, `paid_by_transfer` and `posted` (PTD-19, §8.1); PIT method with the commitment form first and `PROBATION` progressive over 3 months (PTD-20, §8.2); `missing_ids` with the CCCD and the bank where paid by transfer (PTD-21); attendance corrections and `contract_term` checks (PTD-22, PTD-23, §19.2); `l10n_vn_payroll_payment` for advances and payment lists, posting apart (PTD-24, §1, §23); base salary by group (PTD-25); go-live step 1c. |
