# Payroll Fit-Gap against OCA Payroll and Odoo CE 18

v0.1 · Oct 30, 2026 · @Peter

**Based on:**
- Payroll Requirements Specification v0.4, Pay Policy v0.4, Attendance Specification v0.3, Payroll Acceptance Test Cases v0.4, Vietnam Payroll Regulation Reference v0.2;
- the OCA repositories mounted into the container (`oca/`), read 2026-10-30: `payroll` 18.0.1.4.0, `payroll_account` 18.0.1.0.6 and the other `payroll` repo modules; `server-tools/base_time_parameter`, `auditlog`; `hr/hr_employee_relative`; `bank-payment/account_payment_order`; `reporting-engine/report_xlsx`;
- the Odoo CE 18 core the instance runs (`odoo/`);
- the instance's data (test copy of production), read-only, 2026-10-30.

**Purpose:** for every requirement, what OCA payroll, core Odoo or an installed OCA module provides, what has to be built, and which features payroll deliberately leaves alone. It closes the Requirements' FLAG-TECH-01 and FLAG-TECH-02 with a proposal and prepares the technical design. Where it implies a change to the business documents, §12 lists it.

**Conventions**
- Source references are `path:line`, relative to `Odoo-Build/`.
- Verdict codes:

| Code | Meaning |
| --- | --- |
| **OCA** | An OCA module, installed or available in `oca/`, used as it is or configured |
| **Core** | Standard Odoo CE 18 |
| **Ext** | An additive extension of an OCA or core model: fields, overrides, views |
| **New** | A new model or new logic in our modules |
| **Config** | Configuration data only: structures, rules, components, parameters |
| **Bypass** | A feature deliberately not used |

- Status labels: **Agreed** (confirmed by Peter, with date) · **Proposed** (recommended here) · **Finding** (a fact read from the code or the data) · **Open** (§11).

## 0. Decisions and findings

| ID | Decision or finding | Status |
| --- | --- | --- |
| PFG-01 | **Build on OCA `payroll` and `payroll_account`.** Keep their engine and records: structures, rules, categories, contribution registers, payslips, lines, inputs, worked days and batches. Add a data-driven layer on top. Closes FLAG-TECH-01. (§2) | Proposed |
| PFG-02 | **A pay context per payslip.** Our code computes, once per payslip, every figure the policy needs from components, profiles, parameters and inputs, and hands it to the rules through `get_payroll_dict`. Salary rules become one-line sums that hold no amounts and no classification. (§3.1) | Proposed |
| PFG-03 | **One rule pass per payslip; dated pay lines do the splitting.** OCA runs every rule once per contract and the batch picks only the employee's current contract; core's contract lookup skips closed contracts. Mid-month changes are therefore handled by dated pay lines inside the pay context, never by OCA's contract loop. (§3.2) | Finding + Proposed |
| PFG-04 | **Pay terms live in dated contract pay lines,** a new model on `hr.contract`; `wage` is kept equal to the base salary line for compatibility. Closes FLAG-TECH-02. (§4.2) | Proposed |
| PFG-05 | **Parameters in OCA `base_time_parameter`,** read through a strict helper that treats 0 and False as values and raises when a value is missing, as IE TD-13 does. (§4.4) | Proposed; where the helper lives is PFG-OPEN-01 |
| PFG-06 | **Lines are rounded before they are summed.** OCA sums categories at full precision (`oca/payroll/payroll/models/hr_payslip.py:532`), which breaks FR-34 by a few dong. Our override rounds each line to VND, half up, first. (§3.3) | Finding + Proposed |
| PFG-07 | **One journal entry per run, by our code.** `payroll_account` posts one entry per payslip, at confirmation; it creates no entry when the rules carry no accounts (`oca/payroll/payroll_account/models/hr_payslip.py:130`). We leave rule accounts empty and post per run from component accounts and department cost groups. (§6.1) | Finding + Proposed |
| PFG-08 | **The employee is the partner on 3341.** `payroll_account` gives a *payable* line the contribution register's partner, not the employee (`oca/payroll/payroll_account/models/hr_payslip_line.py:40-58`), and 3341 is a payable account here. Our posting sets the employee's contact on 3341 lines, so net pay reconciles per person. (§6.1) | Finding + Proposed |
| PFG-09 | **Run workflow and lock are ours.** OCA has two batch states and four payslip states, no review or approval, and `action_payslip_draft` has no guard (`hr_payslip.py:203`); officers can write payslip lines (`security/ir.model.access.csv:7`). We add the run states, segregation and a hard lock. (§5) | Finding + Proposed |
| PFG-10 | **New users currently become Payroll Managers.** OCA puts both payroll groups on the new-user template `base.default_user` (`oca/payroll/payroll/security/hr_payroll_security.xml:25-27`); on the instance the template holds both. Every internal user created from now on sees all payslips. (§7) | Finding; fix proposed |
| PFG-11 | **Monthly inputs in one model.** Attendance totals, attainment, scores, IE units and entered amounts arrive per employee per month in a payroll input model. The attendance module and IE fill it when they exist; until then it is imported. Payroll does not wait for the attendance module. (§8) | Proposed |
| PFG-12 | **Dependents on OCA `hr_employee_relative`,** extended with the PIT registration fields. (§4.5) | Proposed |
| PFG-13 | **Identifiers in core fields:** SI number in `ssnid`, personal tax code in `identification_id` (the citizen ID serves as tax code from 1 Jul 2025, to confirm), bank in `bank_account_id`. On the instance no employee has an SI number and 121 of 375 have no bank account. (§4.5) | Finding + Proposed |
| PFG-14 | **Bank file through OCA `account_payment_order`** (installed) on the run's 3341 lines, with an Excel export in the paying bank's format. (§6.2) | Proposed; bank is OPEN-06 |
| PFG-15 | **Statutory data as Excel exports** (`report_xlsx`, installed) in the filing tools' import formats; no direct integration in v1. Closes FLAG-TECH-03 for v1. (§6.3) | Proposed |
| PFG-16 | **Audit through OCA `auditlog`** (installed): write logging on pay data for FR-50, read logging on payslips for FR-54. (§7) | Proposed |
| PFG-17 | **Bypassed:** OCA's calendar-based worked days, `contract.wage` as the pay source, `payroll_contract_advantages`, `payroll_hr_public_holidays`, `hr_payroll_document`, OCA's payslip report, core work entries, and `hr.attendance` overtime approval as an OT source. (§9) | Proposed |
| PFG-18 | **Three modules:** `l10n_vn_payroll` (engine layer and statutory rules), `l10n_vn_payroll_account` (run posting and bank file), `l10n_vn_payroll_garment` (the current scheme as configuration data). Attendance is its own module and its own fit-gap. (§10) | Proposed |

## 1. Context

**Installed:** OCA `payroll` and `payroll_account`; core `hr_contract`, `hr_attendance`, `hr_holidays`, `hr_work_entry`, `hr_skills`; OCA `auditlog`, `base_tier_validation`, `excel_import_export`, `report_xlsx`, `account_payment_order`, `account_payment_mode`.

**Available, not installed:** `base_time_parameter`, `payroll_rule_time_parameter`, `payroll_contract_advantages`, `payroll_hr_public_holidays`, `hr_payroll_document`, `hr_employee_relative`, `hr_employee_calendar_planning`.

**Data (test copy):** 375 active employees in the garment company; 287 open contracts; 1,375 payslips January to May 2026 from the old rules; 10 active internal users, 5 of them Payroll Managers (one login named `Tester@123`). The starting point is described in Requirements §11.

**Scale:** about 300 payslips a month today, `[P 3,000]` designed for (FR-52).

## 2. The governing finding: keep the engine, replace the rules

OCA payroll is a rule engine with a thin workflow around it.

| Part | What OCA does | Verdict |
| --- | --- | --- |
| Structures, rules, categories | Python or fixed rules, evaluated in sequence; category totals; parent structures | **OCA**, with generic rules (§3.1) |
| Payslip, lines, inputs, worked days | Records per employee and month; lines keep rule, quantity, rate, amount | **OCA** + **Ext** (snapshot, lock) |
| Batch (run) | `hr.payslip.run` with draft and close | **OCA** + **Ext** (states, approvals) |
| Contribution registers | A partner per register, used on payable lines | **OCA** (SI agency, tax office) |
| Accounting | One entry per payslip, accounts on rules | **Bypass** by configuration; posting per run is **New** (§6.1) |
| Worked days | From the working calendar and time off | **Bypass**; from attendance (§8) |
| Contract pay | `contract.wage` only | **Bypass**; dated pay lines are **New** (§4.2) |

Writing dedicated models instead would rebuild the payslip, its lines, the batch and the history browser for no gain, and would strand this year's 1,375 payslips. The engine's extension points cover everything the policy needs:

- `get_payroll_dict` (`oca/payroll/payroll/models/hr_payslip.py:428`), evaluated once per payslip, exposes values under `payroll.` in every rule;
- `get_current_contract_dict` (`:448`) and `localdict_hook` (`:614`);
- `_get_lines_dict` (`:529`), where line totals are made.

The rules keep access to `payslip`, `employee` and `contract` (`:591-596`), which is how IE's payroll pull is designed (IE TD-49).

## 3. The engine

### 3.1 Pay context and generic rules (PFG-02)

For each payslip, our code builds one pay context before the rules run:

1. **Inputs:** the month's attendance totals, attainment or score, IE units and entered amounts (§8).
2. **Terms:** the dated pay lines in force on each day of the period, from every contract that overlaps it (§3.2).
3. **Components:** each pay line's amount, prorated on its basis (FR-61) and multiplied by attainment where it is variable (FR-68), with its flags.
4. **Bases:** the OT base, the SI base from the contribution profile, PIT exempt amounts, taxable income, PIT, union dues, damage compensation within its cap.
5. **Checks:** every §7 check, at its configured level (FR-59).

The rules then read the context. A rule per component looks like `result = payroll.lines.PRODUCTIVITY`; the SI rule is `result = payroll.si.employee_si`. The structure orders them and the categories group them for the payslip and the reports. Policy changes are component and parameter changes; no rule is edited (FR-07, FR-56).

The context is stored on the payslip as a JSON snapshot (FR-10, FR-53), with the parameter values and inputs it used.

### 3.2 Contracts and mid-month changes (PFG-03)

Three findings decide this:

- `_get_lines_dict` runs every rule once per contract and keys lines by contract (`hr_payslip.py:577-612`). With two contracts in a month, each rule, including SI and PIT, would run twice.
- The batch wizard builds each payslip from `employee.contract_id`, the employee's current contract only (`hr_payslip.py:641`).
- Core's `_get_contracts` searches *open* contracts only (`odoo/addons/hr_contract/models/hr_employee.py:105-119`). A leaver's contract or a finished probation contract, once closed, drops out of its last month.

So the pay context collects every contract overlapping the period, open or closed, splits the month at each change of pay line or contract (FR-35 to FR-40), and the rules run once, against the payslip's main contract. Each line on the payslip still states the period it covers.

**Probation:** a probation clause is a contract with `trial_date_end` (`odoo/addons/hr_contract/models/hr_contract.py:36`) and a probation rate on its pay lines; a separate probation contract is its own `hr.contract` with the probation contract type, which its contribution profile excludes from SI (FR-60). Confirm HR's practice: PFG-OPEN-02.

### 3.3 Rounding (PFG-06)

`_get_lines_dict` computes `total = quantity × rate × amount / 100` at full precision and adds it to the category totals (`hr_payslip.py:532-541`). The stored line total is then rounded to the currency's precision (VND rounding is 1 on the instance), but the category totals that later rules read are not. Gross and net would differ from the sum of their lines by a few dong. Our override rounds the total, half up, before it reaches the categories (FR-34, TC-R1).

### 3.4 Performance (FLAG-TECH-04)

Each payslip evaluates its rules with `safe_eval` and creates its lines through the ORM (`hr_payslip.py:277-294`). The pay context is computed in bulk per run (one query per input table, not per employee). At 300 payslips this is seconds; 3,000 payslips with about 20 lines each is about 60,000 line records a run. To be measured in the technical design's prototype before FR-52 is promised.

## 4. Master data

### 4.1 Function-by-function verdicts

| Requirement | Verdict | Basis and gap |
| --- | --- | --- |
| Pay component with flags (§2, FR-07) | New | Code, legal nature, in SI base, in OT base, PIT treatment and cap, proration basis, variable or conditional, attainment source, payslip section, accounts, check level overrides. |
| Parameters (FR-03, FR-56) | OCA + New | `base_time_parameter` with a strict helper (§4.4). JSON values hold tables such as PIT brackets. |
| Salary scale, productivity levels (FR-04) | New | Grade × step amounts and productivity levels, with effective dates. |
| Employee pay profile (§2) | Ext | Fields on `hr.employee`: pay group, attendance mode, region, residency, union member. |
| Contribution profile (FR-60) | New | Participant type, funds, base source, declared base, floor, PIT method; defaults per participant type. |
| Contract pay (FR-04, FR-37) | New + Ext | Dated pay lines on `hr.contract` (§4.2). |
| Dependents (FR-06, FR-28) | OCA + Ext | `hr_employee_relative` + PIT fields (§4.5). |
| SI number, tax code, bank account | Core | `ssnid`, `identification_id`, `bank_account_id` (§4.5). |
| Productivity level line (FR-05) | New | Level, review date, granted by; IE's suggestion shown beside it. |

### 4.2 Contract pay lines (PFG-04)

A pay line belongs to a contract: component, amount or level, date from, date to, and for probation a rate. A grade and step, or a productivity level, generates the lines through configuration (FR-04). Changes are new lines with an effective date, tracked (FR-37, FR-50). `wage` is kept equal to the base salary line, so core and OCA views that show it stay meaningful.

`payroll_contract_advantages` (`oca/payroll/payroll_contract_advantages/models/hr_contract_advantage.py`) offers an amount per template on the contract, with no dates, no flags and no proration. It does not fit and is not installed.

### 4.3 Grade, step and level tables

Plain dated tables (New). They hold amounts only; how an amount splits into components is component configuration, so the current scheme (base + performance pay) and the target policy (base per position + allowances) are both data.

### 4.4 Parameters (PFG-05)

`base_time_parameter` stores a parameter by code with dated versions and typed values, including JSON. Two quirks make it unsafe for pay as it is:

- a stored 0 or False is treated as missing (`oca/server-tools/base_time_parameter/models/base_time_parameter.py:72-73`), so a 0% rate or a zero cap disappears;
- the record helper never raises (`oca/server-tools/base_time_parameter/models/base.py:22`), so a missing minimum wage would compute silently.

IE TD-13 already plans a strict helper over the same module. Payroll needs the same helper. `payroll_rule_time_parameter` only wraps the lax one and is not used.

### 4.5 People data (PFG-12, PFG-13)

| Data | Where | Gap |
| --- | --- | --- |
| SI number | `hr.employee.ssnid` (`odoo/addons/hr/models/hr_employee.py:89`) | Empty for every employee on the instance |
| Personal tax code | `identification_id` (`:91`) | Filled for 374 of 375; the citizen ID is the tax code from 1 Jul 2025 `[to confirm]` |
| Bank account | `bank_account_id` (`:93`) | 121 of 375 missing; FR-43 blocks them |
| Dependents | `hr_employee_relative`: relation, name, birth date | Add dependent tax code, registered from and to months, registration document, PIT flag (Ext). Core's `children` count is not enough for FR-06. |
| Residency, union member, pay group | — | New fields (Ext) |

## 5. The monthly run

| Requirement | Verdict | Basis and gap |
| --- | --- | --- |
| Run states (FR-08) | Ext | `hr.payslip.run` has `draft` and `close` only (`oca/payroll/payroll/models/hr_payslip_run.py`). Add Calculated, Reviewed, Approved, Paid with `selection_add`; payslips go to `done` at approval. |
| Segregation (FR-02) | New | Record who calculated, reviewed and approved; refuse approval by the preparer. `base_tier_validation` (installed) could carry the approvals; two fixed steps are simpler in our code (PFG-OPEN-05). |
| Repeatable calculation (FR-09) | OCA + Ext | `compute_sheet` deletes and recreates lines (`hr_payslip.py:277-294`); the pay context is deterministic. |
| Snapshot (FR-10, FR-53) | New | JSON of the pay context on the payslip (§3.1). |
| Lock (FR-51) | Ext | `action_payslip_draft` has no state guard (`hr_payslip.py:203`) and officers may write and delete lines (`security/ir.model.access.csv:7`). Override `write` and `unlink` on payslips, lines, inputs and worked days of an approved run; keep `payroll.allow_cancel_payslips` off. |
| Off-cycle payslips (FR-11) | OCA | A payslip outside a batch, or a one-person batch. |
| Corrections to locked periods (FR-30) | New | Adjustment entries naming their period, carried by the next run. OCA's refund (`refund_sheet`) reverses a whole payslip and is not used for corrections. |
| Validations (§7, FR-59) | New | Checks with levels per check and per component; results stored on the run and the payslip. |

## 6. Outputs

### 6.1 Accounting (PFG-07, PFG-08)

`payroll_account` builds one entry per payslip when it is confirmed, from each rule's debit and credit accounts, and posts it (`oca/payroll/payroll_account/models/hr_payslip.py:46-134`). It creates no entry when no line has an account (`:130`). FR-44 wants one entry per run, with the cost account chosen by department. So:

- rules carry no accounts, and `payroll_account`'s posting produces nothing;
- each component carries its liability account and, per cost group, its expense account; each department carries its cost group (direct labour 6220, factory 6271, selling 6411, administration 6421);
- at approval our code posts one entry per run, summed by account, cost group and partner;
- 3341 lines carry the employee's contact as partner (`payroll_account` would give a payable line the register's partner instead, `hr_payslip_line.py:52-58`); 338x and 33351 lines carry the SI agency and the tax office through OCA contribution registers.

`payroll_account` stays installed: its fields hold the links of the 2026 payslips to their entries.

### 6.2 Payment (PFG-14)

`account_payment_order` (installed) builds a payment order from open payable lines with a partner bank account. The run's 3341 lines qualify once they carry the employee's partner. Its file formats are SEPA; Vietnamese banks take their own Excel or CSV layout, so the export is ours, in `report_xlsx`, in the paying bank's format (OPEN-06). Marking the run paid follows the payment order's reconciliation (FR-08).

### 6.3 Statutory data and reports (PFG-15)

| Output | Verdict | Basis and gap |
| --- | --- | --- |
| SI contribution list and change list (FR-45) | New | Excel in the import format of the filing service in use; the change list comes from contract and profile changes and long absences. |
| PIT withholding return, annual finalisation, certificates (FR-46) | New | Excel for the tax portal's import; year-to-date sums from done payslips (OCA's `payslips.sum`, `oca/payroll/payroll/models/base_browsable.py:88-101`). The OT and night schedule Decree 253 requires comes from attendance inputs. |
| Union totals (FR-47) | New | From the run. |
| Payslip (FR-41, FR-42) | New | A bilingual QWeb report with sections from the components; OCA's `report_payslip` is not used. Distribution (portal, Zalo) waits for OPEN-01. |
| Register, cost by department and line, OT against limits, incentive cost (FR-48, FR-49) | Core + New | List and pivot views over payslip lines with component and department; Excel through `report_xlsx`. |

## 7. Security (PFG-10, PFG-16)

| Finding | Proposal |
| --- | --- |
| The new-user template carries both payroll groups (`oca/payroll/payroll/security/hr_payroll_security.xml:25-27`); confirmed on the instance | Our module removes them from `base.default_user`. The OCA record is `noupdate`, so the removal sticks. |
| 5 of 10 internal users are Payroll Managers, including a login `Tester@123` | Peter reviews the list (PFG-OPEN-04). |
| The Officer record rule shows an officer only their own payslips, those of employees without a department and those of departments they manage (`hr_payroll_security.xml:28-36`) | Roles map to groups: payroll officer → Officer, with a rule of all payslips of their companies; HR manager, director, accountant → groups of our own (FR-01, FR-02). |
| `wage` has no field group (`odoo/addons/hr_contract/models/hr_contract.py:42`), and contracts are readable by the employee-manager group | Pay lines and amounts get `groups=` restricted to payroll roles; `wage` is hidden from non-payroll groups in views and exports (FR-54, FLAG-TECH-05). |
| No read logging | `auditlog` rules: write logging on pay data, read logging on payslips (FR-50, FR-54). |

## 8. Inputs from attendance and IE (PFG-11)

Payroll reads one record per employee per month: scheduled, paid and unpaid days, days worked, the SI 14-day count, leave by type, paid break minutes, OT and night hours by category, late arrivals, unexcused absences, OT year to date, attainment or score, IE units, entered amounts with approvers.

- **Attendance module** (Attendance Spec v0.3) fills it at attendance close. Until the module exists, the month's totals are imported from Excel through `excel_import_export` (installed), with the same validations. Payroll v1 does not wait for the attendance module.
- **IE** fills units and, once live, attainment at IE close, through the pull IE TD-49 describes. Payroll calls it only when IE is installed, so neither module depends on the other.
- **Supervisors and managers** enter attainment and scores until IE and KPI processes exist (FR-68).
- OCA's worked days (`WORK100` from the calendar, `hr_payslip.py:377-397`) and core's `hr.attendance` overtime approval are bypassed: they count planned time and time beyond the calendar, not the paid time and approved OT windows of Attendance §5 and §7.
- A closed attendance or IE period is required before a run calculates (FR-58, TC-F01); an imported month is closed when its import is confirmed.

## 9. Bypassed

| Feature | Why |
| --- | --- |
| OCA worked days from the calendar | Planned time, not paid time (§8) |
| `contract.wage` as the pay source | One number cannot carry components and dates (§4.2) |
| `payroll_account` per-payslip posting | FR-44 wants one entry per run by department (§6.1) |
| `payroll_contract_advantages` | No dates or flags (§4.2) |
| `payroll_rule_time_parameter` | Wraps the lax parameter reader (§4.4) |
| `payroll_hr_public_holidays` | Needs `calendar_public_holiday`, not mounted; holidays come from attendance |
| `hr_payroll_document` | Splits and emails payslip PDFs produced elsewhere; ours are generated |
| OCA payslip report | Not bilingual, not sectioned by component |
| Core work entries | Not used by OCA payroll's rules; attendance supplies paid time |
| `hr.attendance` overtime approval | Every record on the instance is *approved*; it is not the approved-window rule |

## 10. Module map (PFG-18)

| Module | Holds | Depends on |
| --- | --- | --- |
| `l10n_vn_payroll` | Components, pay lines, scales and levels, contribution profiles, the employee and dependent fields, the monthly input model and its import, the pay context and generic rules, rounding, run states, segregation and lock, checks, snapshot, the bilingual payslip, statutory exports, security groups and the new-user template fix | `payroll`, `base_time_parameter`, `hr_employee_relative`, `report_xlsx`, `excel_import_export` |
| `l10n_vn_payroll_account` | Department cost groups, component accounts, posting per run, the bank file on payment orders | `l10n_vn_payroll`, `payroll_account`, `account_payment_order` |
| `l10n_vn_payroll_garment` | The current scheme as data: components and flags, productivity levels, grade and step amounts, structure and rules, parameters for Region IV, check levels, account mapping | `l10n_vn_payroll_account` |

- Statutory values (rates, caps, brackets, deductions, minimum wages) ship as parameters in `l10n_vn_payroll`, so they are shared by any Vietnamese company; the company's policy values ship in the garment module.
- The names follow the repo's VN localisation convention (`l10n_vn_` modules and field prefixes), as the e-invoice modules do.
- `auditlog` rules are configuration in the garment module.

## 11. Open items

| ID | Item | Proposal |
| --- | --- | --- |
| PFG-OPEN-01 | Where the strict parameter helper lives, since IE's `ie_base` needs it too | A small shared module both depend on, rather than two copies |
| PFG-OPEN-02 | How HR records probation: a clause in the labour contract, a separate probation contract, or both | Support both (§3.2); HR confirms which is used |
| PFG-OPEN-03 | The old structures, rules and the May 2026 run in *verify* | Archive the old structures and rules at go-live; cancel the May run's payslips, which were never confirmed |
| PFG-OPEN-04 | Who should hold Payroll Manager and Officer | Peter reviews the 5 managers, including `Tester@123` |
| PFG-OPEN-05 | Approvals in our code or with `base_tier_validation` | Our code: two fixed steps with segregation |
| PFG-OPEN-06 | Missing employee data before go-live: SI numbers (all), bank accounts (121) | HR collects them; the run blocks without them (FR-43, §7 of the Requirements) |
| PFG-OPEN-07 | Whether the citizen ID number serves as the personal tax code | Confirm with the accountant |

## 12. Proposals to the business documents

| Document | Proposal |
| --- | --- |
| Requirements FR-44 | Add that each department carries a cost group, and each component an expense account per cost group and a liability account. |
| Requirements §9 | Add that monthly attendance totals may be imported until the attendance module is live, with the same closing rule. |
| Requirements §11 | Add the new-user template finding and the user review (PFG-10, PFG-OPEN-04) to the starting point. |
| Requirements FR-08 | State that payslips are confirmed at run approval and that the run carries the states. |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-30 | First version: decisions PFG-01 to PFG-18, verdicts per requirement, module map, open items. |
