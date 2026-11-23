# l10n_vn_hr_contract_document

The Vietnamese labour, probation and training contracts printed from the Odoo contract, with the data they need;
later the contract's approval, its lock and its amendments printed as annexes. Generic: any Vietnamese company's
wording is configuration. Design: `docs/HR-Contract-Payroll/Contract Documents — Design Note v0.2.md` (CD-xx); the
forms' text: `docs/HR-Contract-Payroll/Contract Forms — Research and Drafts v0.1.md` §5–§6. Payroll engine:
`docs/modules/l10n_vn_payroll.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Data fields on the company, the employee, the contract and the contract type; the print mode on pay components; the company's wording record; the report with the labour, probation and training forms; *Print Draft*; the list of missing data on the contract | done | 2026-11-21: installed with garment step 9; runs 1–3 corrected two tests (`report_action` needs `config=False`; the garment calendar works Saturdays and has lunch-only Sundays); run 3: 24 tests, 0 failures. UI check: *Print Draft* stopped on an amount it could not read (D4 changed); run 4: `-u l10n_vn_hr_contract_document`, 26 tests, 0 failures; run 5 with engine step 12.1: `-u l10n_vn_payroll`, 363 post-tests, 0 failures. UI checked by Peter on the test copy: company representative, contract-type kinds, the missing-data warning, *Print Draft* (blanks and reasons for amounts not readable on the start date), company wording, a probation clause |
| 1.1 | Extra articles per company and form, on the company's wording record; individual terms per contract; both numbered after the fixed articles, before the closing article (D15–D19) | done | 2026-11-21, one run: `-u l10n_vn_hr_contract_document --test-enable`, `exit=0`, 32 tests, 0 failures. UI checked by Peter: extra articles ordered and numbered after the fixed ones, individual terms as *Thỏa thuận khác*, an archived article dropped and the numbers closed up |
| 2 | Versions and term snapshots; *Approve*, alone and on a selection; numbering; *Print* from a version, one report for drafts and approved contracts; the approval switch; the lock and the pay-line rules (D20–D35) | done | 2026-11-21: run 1, 52 tests, 1 error: `test_approve_needs_manager`'s positive control, a user of core's *Employee Manager* contract group, could not read the contract: that group is the line manager's, limited to the employees it manages. Test corrected; run 2: 52 tests, 0 failures. UI check by Peter: approval, numbers, print and lock as expected, with two findings: the warning did not show what approval checks beyond the missing data (D36), and `wage` could be edited on an approved contract (D37); run 3: 53 tests, 0 failures, UI rechecked by Peter |
| 3 | Amendments and the annex form; *Annexes for a Date*; *Next Contract* (D38–D52) | code delivered | 2026-11-21: 68 tests expected |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | CD-07, §4: wording in QWeb templates of the company module, chosen through a form record per company and kind | The forms are QWeb templates of this module; the company's own clauses are fields of a wording record per company (D5), which the garment module fills | QWeb inheritance is global: a company module replacing clauses in the templates would change them for every company, the trading company included. A record per company keeps each company's wording apart, and HR can correct it in the UI |
| 2 | §3.3, §4.1: `l10n_vn.contract.form` with the template and the number sequence | No form model. The template follows the contract type's kind (D3); numbering comes with step 2 | Without template choice the record would hold only a sequence, which step 2 can place itself |
| 3 | §2.4: the missing data listed at approval | Also shown on the contract form from step 1 (D9) | HR enters the go-live data before approval exists; the list shows what each contract still lacks |
| 4 | §3.2: `res.company.l10n_vn_contract_code` | Step 2, with the numbers that use it | Step 1 prints no number |
| 5 | §1.2: with the switch off the module "refuses nothing" | The switch governs only that a contract becomes Running through approval; an approved contract is locked whether the switch is on or off (D28) | Approval is an explicit act on one contract; a lock that depends on a company setting would let a switch turned off unlock every approved contract at once |
| 6 | §1.2: *Print* and *Print Draft* | One report, *Contract*, replacing step 1's *Contract (Draft)*: it prints the approved version when there is one, else the draft (D26) | One entry in the Print menu, and no way to print a draft of an approved contract by mistake |
| 7 | §1.4, §4.1: HR officers (`hr_contract.group_hr_contract_employee_manager`) open amendments and use *Next Contract* | Contract administrators do (D38) | Core's *Employee Manager* contract group is the line manager's, read-only and limited to the employees it manages (`ir_rule_hr_contract_employee_manager`); core has no officer level for contracts (found in step 2) |
| 8 | §1.4: *Cancel Amendment* cancels the draft version | It deletes the draft version, which never had a number or a print (D44) | A cancelled version would keep its sequence and leave a gap in the annex numbers |
| 9 | §1.3, §1.4: an amendment unlocks the locked fields except end date, type and probation form | It also keeps the start date, the probation clause and the training kind locked, and refuses adding or removing a training commitment (D40) | Each of these is part of article 1, the term, which an annex may not change (Art. 22.2), or changes the article numbering an annex cites |

## Decisions

| # | Decision |
|---|---|
| D1 | **Print mode** (CD-06, design §2.3): `l10n_vn.payroll.component.l10n_vn_contract_print`, a stored editable compute. `none` when `kind` is not `earning`, or `legal_nature` is one of `overtime`, `night`, `leave_pay`, `severance`, `statutory`, `union`, `damage`, `advance`, `adjustment`, `total`; else `welfare` for `bonus` and `welfare`; else `reference` when `variable` or `legal_nature == "variable_salary"`; else `amount`. On the test copy this gives `BASE`, `DAILY`, `DUTY` amount, `PROD`, `PERF` reference, `ATT`, `PHONE` welfare; `TRAIN` amount |
| D2 | **Where an amount line prints** (Research and Drafts §6): `legal_nature` `job_salary` in the salary clause (labour 3.1, probation 3.1, training 3.1), `fixed_allowance` as allowances (labour 3.2), any other `amount` line as a fixed supplement (labour 3.3, c1); `reference` lines as variable supplements (c2) by name; `welfare` lines in article 4.2 (labour only), with their amount, except components of nature `bonus`, which print by name with *theo quy định của Công ty*. The unit is *đồng/ngày* when the component's `proration` is `per_day`, else *đồng/tháng* |
| D3 | **Which form:** `hr.contract.type.l10n_vn_document_kind` (`labour`, `probation`, `training`, `none`); the contract reads it through a related field. Empty counts as `none`: no form, no *Print Draft*, no missing list |
| D4 | **The terms of a draft** are read on the contract's `date_start`: the pay lines in force that day (`_l10n_vn_in_force`) and their amounts (`_l10n_vn_amount_on`), `vn.policy.probation_rate` that day. An amount or the rate that cannot be read (a parameter or scale without a value that day) prints as a dotted blank, and the strict reader's message, prefixed with the component's code for an amount, joins the missing list (D9). Changed in step 1 after the UI check: the first version let the error stop the print, which showed users a QWeb traceback |
| D5 | **Company wording:** `l10n_vn.contract.wording`, one per company, holds the `[C]` clauses: duties and payday as plain text set into a sentence, the other clauses as whole article bodies in HTML. Fields start from the module's generic texts (`DEFAULT_WORDING`); a company without a record prints those texts. Wording holds no placeholders: values come only from the templates |
| D6 | **Parties print as they are now;** in step 1 every term does too. The text is Vietnamese whatever the user's language: values are read with `lang="vi_VN"`, so component and country names print in Vietnamese where translated |
| D7 | **Draft marks:** *BẢN NHÁP* above the motto; the number line reads *Số: ……*; a missing value prints as a dotted space to fill in by hand; an empty signing date prints *ngày …… tháng …… năm ……* |
| D8 | **Who prints:** payroll users (`payroll.group_payroll_user`), since the forms show pay. `_l10n_vn_document_values()` refuses others with an `AccessError` unless superuser, then reads as superuser (pay lines carry payroll groups, engine D11, D14) |
| D9 | **Missing data** (design §2.4 without the approval): `hr.contract.l10n_vn_document_missing`, a non-stored Text computed as superuser, one label per line, empty when nothing is missing or the kind is `none`. Labels are the fields' labels in the user's language, plus fixed messages where a rule is broken (D10) |
| D10 | **What a form needs:** company: `l10n_vn_legal_rep_id`, `l10n_vn_legal_rep_title`, `vat`, `street`, and `state_id` or `city`; employee: `birthday`, `gender`, `l10n_vn_personal_id` of 12 digits, `l10n_vn_id_issue_date`, `l10n_vn_id_issue_place`, `l10n_vn_permanent_address`; contract: `job_id`, `l10n_vn_work_address_id`, at least one pay line in force on `date_start` whose component prints as `amount`; with a probation clause (`l10n_vn_probation_form == "clause"`) or on a `probation` form: `l10n_vn_probation_job`, and `trial_date_end` (clause) or `date_end` (probation form); on a `training` form: `date_end` |
| D11 | **Lengths:** a fixed term prints in months when `date_end` + 1 day is exactly N months after `date_start`, else in days (`date_end − date_start + 1`). A probation length prints in working days for job category `other`, counted on the contract's calendar with the engine's `l10n_vn.payroll.check._scheduled_dates`, and in calendar days for the other categories (as the engine's `probation_length` check, D66) |
| D12 | **Amounts** print with `.` as thousands separator and no decimals (`4.500.000`); in words with `num2words(lang="vi")`, first letter upper case, followed by *đồng* (as `l10n_vn_voucher`, without depending on it) |
| D13 | **Workplace default:** `l10n_vn_work_address_id` follows the employee's work address (`address_id`) when the employee changes, like core's `job_id` and `department_id` (`hr_contract.py:96-102`); editable |
| D14 | **Place of signing** is the company's province (`state_id`), else its `city` |
| D15 | **Extra articles** (step 1.1, Peter 2026-11-21): `l10n_vn.contract.article`, lines of the company's wording record, each for one form (`labour`, `probation` or `training`) with a title and a body; active ones print in `sequence` order after the form's fixed articles. They hold no placeholders (D5). A clause wanted on two forms is two lines |
| D16 | **Individual terms** (step 1.1): `hr.contract.l10n_vn_individual_terms`, free text agreed with this employee, printed as one article *Thỏa thuận khác* (the title of Decree 145's sample contract, Art. 10) after the extra articles, on every form, when not empty (`odoo.tools.is_html_empty`). Step 2's lock covers it |
| D17 | **Numbering:** the fixed articles keep their numbers (labour 1–11, probation 1–6, training 1–6, and 7 with a commitment); extra articles follow from the next number, then the individual terms, then the closing article. An annex therefore cites a fixed article by the same number on every contract of its form |
| D18 | **A wording record not saved yet** (`_for_company` without a record) has no extra articles; extra articles exist only on a saved record |
| D19 | **Who edits:** extra articles with the wording record (contract administrators); individual terms by whoever edits the contract, like its other fields |
| D20 | **Versions** (CD-01, step 2): `l10n_vn.contract.version` holds each approved state of a contract; step 2 makes version 0, the contract itself; annexes (versions 1, 2 …) come with step 3. A version is written only by the contract's actions, as superuser |
| D21 | **Approve** (`hr_contract.group_hr_contract_manager`): for a contract in `draft` or `open`, not approved yet, the approval problems (D22) must be empty; then, in one transaction: the number (D23), version 0 with its snapshot (D24), `l10n_vn_approved`, and the state: `open` when `date_start` is on or before today, else `kanban_state = done` (core's *Incoming*, opened by core's cron on its start date). A contract already `open` (running before the switch) keeps its state. `close` and `cancel` are refused. A contract whose kind is `none` is approved with no number and no data check |
| D22 | **Approval problems:** the missing list (D9, D10, D4), then the legal limits a form states: a probation (clause or form) longer than `vn.probation.max_days` for its job category (working days on the contract's calendar for `other`, calendar days otherwise, as D11) or a `vn.policy.probation_rate` below `vn.probation.min_rate`, both on `date_start`; a fixed-term labour contract whose `date_end` + 1 day is after `date_start` + 36 months; a training contract whose `date_end` + 1 day is after `date_start` + 3 months. Approval refuses with all of them in one `UserError` |
| D23 | **Numbers:** one `ir.sequence` per company and form kind, found by `code` `l10n_vn.contract.<kind>` and `company_id`, created when missing (`padding` 4, `use_date_range` True, no prefix or suffix), drawn with `next_by_id(sequence_date=date_start)`, so numbering restarts each year by the contract's start. `implementation` `no_gap`, so a failed approval in a selection leaves no gap. The number is `{nnnn}/{yyyy}/{abbreviation}`, plus `-{company l10n_vn_contract_code}` when set: *0012/2026/HĐLĐ-QP*. Abbreviations: labour *HĐLĐ*, probation *HĐTV*, training *HĐĐT*. `name` is not changed |
| D24 | **The snapshot** (`terms`, Json): `render`, the term part of the values as printed on `date_start` (keys `kind`, `title`, `party_b`, `term`, `probation`, `job`, `workplace`, `salary`, `allowances`, `supplements`, `variable`, `welfare`, `paid_by_transfer`, `payment_text`, `insured`, `training`, and `individual_terms_body` as a string or `None`); and `raw`, the locked fields' values (ids, dates as `YYYY-MM-DD`, text) and the pay lines in force or starting later (`id`, `component_id`, `date_from`, `date_to`), for step 3's comparison and cancellation |
| D25 | **Printing an approved contract:** the terms come from version 0's `render`; the parties (company, representative, employee), the signing date and place, the company's wording and its extra articles are read as they are now; the number prints and the draft mark does not. The individual terms' text, stored as a string, is printed as markup (it was sanitized when saved). So an approved contract reprints the same terms, and a corrected address reprints corrected |
| D26 | **One report:** `action_report_contract`, *Contract*, replaces step 1's `action_report_contract_draft` (removed with the module's data); template `report_contract` replaces `report_contract_draft`. Per contract it prints version 0 when approved, else the draft. `print_report_name`: the number and the employee when approved (*0012-2026-HDLD-QP - Name*), else *Hop dong (nhap) - Name*. *Print Draft* becomes *Print* and shows for every contract with a form |
| D27 | **The switch** `res.company.l10n_vn_contract_approval` (*Contracts become Running only through approval*), default False. When the contract's company has it: `create` refuses `state = open`, and `write` refuses `state = open` for a contract without approval, both with a `ValidationError` (core's cron catches only that, `hr_contract.py:270-283`, and skips the contract), unless our context key `l10n_vn_contract_unlock` is set |
| D28 | **The lock follows approval** (divergence 5): an approved contract refuses, with a `ValidationError` naming the fields, a write changing one of `_l10n_vn_locked_fields()`: `employee_id`, `company_id`, `contract_type_id`, `date_start`, `trial_date_end`, `job_id`, `l10n_vn_work_address_id`, `l10n_vn_participant_type_id`, `l10n_vn_probation_form`, `l10n_vn_probation_job`, `l10n_vn_training_kind`, `l10n_vn_commitment_months`, `l10n_vn_training_cost`, `l10n_vn_training_cost_items`, `l10n_vn_individual_terms`; and `date_end` moved later or removed (earlier, or set where empty, is allowed: a leaver, the departure wizard, core's cron). A field counts as changed when the value written, converted as the ORM does (`convert_to_cache`, `convert_to_record`), differs from the record's. Every other field stays free, `state` included. The superuser is not exempt (core writes contracts as superuser); only `l10n_vn_contract_unlock` is |
| D29 | **The lock's message:** *Contract %(contract)s is approved: %(fields)s cannot change. Use an amendment or a new contract.*, the fields by their labels |
| D30 | **Pay lines of an approved contract** (design §1.3), after D77: a line whose component prints as `amount` cannot be created, deleted, or written except `note`, `granted_by`, `review_date`; a `reference` line can be created only for a component the contract already has, written except `component_id` and `contract_id`, and deleted only while another line of its component remains; `welfare` and `none` lines are free |
| D31 | **Approving a selection:** the server action *Approve Contracts* on the contract list (contract administrators) approves each selected contract in its own savepoint. A single contract that fails raises its problems; for several, the failures are listed in a sticky warning notification, each with its reasons, and the others are approved |
| D32 | **The form while the switch is on:** core's two statusbar fields are read-only (`readonly="l10n_vn_company_approval"`, a related field of the company's switch), so the state is not clicked into an error |
| D33 | **Access to versions:** read for contract administrators and payroll users (the snapshot holds pay); no write, create or unlink for anyone (D20); a multi-company rule |
| D34 | **The copy of a contract** carries no version and is not approved (`copy=False` on the new fields) |
| D35 | **An approved contract is not deleted** (added while coding): `unlink` refuses it with *Contract %(contract)s is approved and cannot be deleted; cancel it instead.* Deleting it would also delete its versions and, through the cascade, refuse on its pay lines with a less clear message |
| D36 | **The warning shows what approval checks** (UI check, 2026-11-21): `l10n_vn_document_missing`, string *Before Approval*, holds `_l10n_vn_approval_problems()` (D22), not only the missing data, under the heading *Before this contract can be approved:*; empty once approved. Step 1's version listed missing data only, so approval could still refuse a contract with a clear warning (an unread `vn.probation.min_rate`, a probation beyond its limit) |
| D37 | **`wage` is read-only on the form once approved** (UI check, 2026-11-21): it is a display copy of the pay lines (engine D5) that payroll never reads, so editing it on an approved contract looks like a salary change and is none. Only the view: payroll's wage sync still writes it |
| D38 | **Who amends** (divergence 7): contract administrators (`hr_contract.group_hr_contract_manager`) amend, approve and cancel amendments, run *Annexes for a Date* and *Next Contract*; each action checks the group, then works as superuser with `l10n_vn_contract_unlock` |
| D39 | **Amend:** a wizard on an approved contract in state `open`, or `draft` and *Incoming*, without an amendment open, asks for the effective date and the reason. The date must fall within the contract (on or after `date_start`; on or before `date_end` when set) and after `_l10n_vn_paid_until()`, the last `date_to` of the contract's payslips that are locked (engine D76, `hr.payslip._l10n_vn_locked()`). It creates version `max(sequence) + 1`, kind `annex`, state `draft`, with `terms = {"raw_before": _l10n_vn_document_raw()}` (the contract as it is when the amendment opens), and sets `hr.contract.l10n_vn_amendment_id` |
| D40 | **What an amendment unlocks** (divergence 9): `job_id`, `l10n_vn_work_address_id`, `l10n_vn_participant_type_id`, `l10n_vn_commitment_months` (but not from 0 to more or back), `l10n_vn_training_cost`, `l10n_vn_training_cost_items`, `l10n_vn_individual_terms`, and the pay lines under D41. Everything else of D28 stays locked, and so do `date_start`, `trial_date_end`, `l10n_vn_probation_job` and `l10n_vn_training_kind` |
| D41 | **Pay lines during an amendment**, for every print mode except `welfare` and `none`: an existing line may only receive a `date_to`, on or after the effective date − 1 day, or have `note`, `granted_by`, `review_date` written; a new line starts on or after the effective date; no line is deleted. D77 applies on top |
| D42 | **Approve Amendment:** the approval problems (D22) on the effective date must be empty (`_l10n_vn_approval_problems(date)`, D10 and D22 reading the pay lines and parameters on that date); the terms are computed on the effective date (`_l10n_vn_document_terms(date)`) and compared with the current version's `render` by group (D43); no printed group changed refuses (*Nothing printed in contract %(contract)s changes on %(date)s.*). Then: number `{nn:02d}/{contract number}` (no number for kind `none`), `terms = {"render", "raw", "raw_before", "changes"}`, state `approved`, `approved_by`, `approved_at`; the contract's `l10n_vn_version_id` becomes it; `l10n_vn_amendment_id` cleared; a chatter message *Annex approved: %(number)s* |
| D43 | **Groups and articles:** `work` (`job`, `workplace`), `salary` (`salary`, `allowances`, `supplements`, `variable`, `payment_text`), `bonus` (`welfare`), `insurance` (`insured`), `training` (`commitment_months`, `cost_text`, `cost_items`), `individual` (`individual_terms_body`). A row compares by `name`, `amount_text` and `unit`. A group prints in an annex as the article it fills on the contract's form: labour `work` 2, `salary` 3, `bonus` 4, `insurance` 8; probation `work` 2, `salary` 3; training `work` 1, `salary` 3, `training` 7; and `individual` at the number it has in the version being amended (or the next free one when it is new). A group the form does not print does not count as a change. `changes` lists `{"group", "number", "title", "action"}` with `action` `modify`, `add` (individual terms added) or `remove` (removed) |
| D44 | **Cancel Amendment** (divergence 8): the locked fields are written back from `raw_before`; pay lines whose id is not in `raw_before` are deleted; the lines of `raw_before` get their `date_to` back; the draft version is deleted; `l10n_vn_amendment_id` cleared |
| D45 | **The contract prints version 0;** an annex prints itself. `_l10n_vn_document_values()` reads version 0's `render` (not `l10n_vn_version_id`'s), and `l10n_vn_number` becomes a non-stored compute: version 0's number |
| D46 | **The annex** (Research and Drafts §6.5): report `action_report_contract_annex` on `l10n_vn.contract.version`, *Contract Annex*, payroll users, printed from the *Print* button of an approved annex in the contract's *Versions* tab. Title by the contract's form (*PHỤ LỤC HỢP ĐỒNG LAO ĐỘNG*, *… THỬ VIỆC*, *… ĐÀO TẠO*); the number; the bases, naming the contract's number and signing date (dotted when not set); the parties as now; *Hai bên thỏa thuận sửa đổi, bổ sung Hợp đồng số … như sau:*; article 1, one item per change: *Sửa đổi Điều {n} ({title}) như sau:* followed by that article's body rendered from the annex's terms, or *Bổ sung Điều {n}. Thỏa thuận khác như sau:*, or *Bãi bỏ Điều {n} (Thỏa thuận khác).*; article 2, effect (*có hiệu lực kể từ ngày …*), the rest unchanged, two copies; the signatures. No draft mark: only approved annexes print |
| D47 | **Article bodies are templates of their own,** so the contract and the annex print the same text: the forms call them, and the annex calls the ones that changed |
| D48 | **Annexes for a Date:** a wizard (contract administrators) with a date, a reason (default *Điều chỉnh tiền lương*) and contracts (default the selected ones). Its lines list the approved contracts without an amendment open whose terms on the date differ from their current version in a group their form prints, with the groups; *Confirm* opens and approves an amendment for each line (D39, D42) in its own savepoint, and reports failures as D31 does. The annexes then print together from the version list |
| D49 | **Next Contract:** a wizard (contract administrators) on a contract in state `open`, `close`, or approved and *Incoming*, with the new start date (default the day after `date_end`, or after `trial_date_end` for a probation contract, else today), the contract type (default the current one; a probation contract defaults to the first type whose kind is `labour`), and the end date (optional) |
| D50 | **What Next Contract makes:** `copy()` with `date_start`, `date_end`, `contract_type_id`, `state` `draft`, `l10n_vn_probation_form` `none`, `trial_date_end` False, no pay lines, and the participant type of the new contract type when it has one; then, for each pay line of the current contract in force on its last day before the new start (the new start − 1 day), a new line with the same component, amount, scale key, `in_cell`, `granted_by`, `review_date` and `note`, from the new start, without end. The current contract ends on the new start − 1 day when it has no end or ends later (allowed by D28). The wizard opens the new contract |
| D51 | **The contract form during an amendment:** a banner *Amendment in progress, effective %(date)s: %(reason)s*; header buttons *Approve Amendment* and *Cancel Amendment* (contract administrators) in place of *Amend*; the warning shows the approval problems on the effective date |
| D52 | **The version list** gains `reason` and a *Print* button on approved annexes |

## Folder structure

```
l10n_vn_hr_contract_document/
├── __init__.py
├── __manifest__.py
├── data/
│   └── report_paperformat.xml
├── models/
│   ├── __init__.py
│   ├── hr_contract.py
│   ├── hr_contract_type.py
│   ├── hr_employee.py
│   ├── l10n_vn_contract_document.py
│   ├── l10n_vn_contract_wording.py
│   ├── l10n_vn_payroll_component.py
│   └── res_company.py
├── readme/
│   ├── DESCRIPTION.md
│   └── USAGE.md
├── report/
│   ├── l10n_vn_contract_document_reports.xml
│   └── l10n_vn_contract_document_templates.xml
├── security/
│   ├── ir.model.access.csv
│   └── l10n_vn_contract_document_security.xml
├── static/
│   └── src/scss/l10n_vn_contract_document.scss
├── tests/
│   ├── __init__.py
│   ├── common.py
│   ├── test_document_data.py
│   └── test_document_report.py
└── views/
    ├── hr_contract_type_views.xml
    ├── hr_contract_views.xml
    ├── hr_employee_views.xml
    ├── l10n_vn_contract_wording_views.xml
    ├── l10n_vn_payroll_component_views.xml
    ├── res_company_views.xml
    └── menus.xml
```

## Manifest

| Key | Value |
|---|---|
| `name` | *Vietnam - Labour Contract Documents* |
| `summary` | *Labour, probation and training contracts printed from the Odoo contract* |
| `version` | `18.0.1.0.0` |
| `author`, `website`, `license` | `1-Aria`, `https://github.com/1-Aria/odoo-qms-pms`, `AGPL-3` |
| `category` | `Human Resources/Contracts` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_payroll` |
| `external_dependencies` | `{"python": ["num2words"]}` |
| `data` | `security/l10n_vn_contract_document_security.xml`, `security/ir.model.access.csv`, `data/report_paperformat.xml`, `report/l10n_vn_contract_document_templates.xml`, `report/l10n_vn_contract_document_reports.xml`, `views/res_company_views.xml`, `views/hr_employee_views.xml`, `views/hr_contract_type_views.xml`, `views/hr_contract_views.xml`, `views/l10n_vn_payroll_component_views.xml`, `views/l10n_vn_contract_wording_views.xml`, `views/menus.xml` |
| `assets` | `web.report_assets_common`: `l10n_vn_hr_contract_document/static/src/scss/l10n_vn_contract_document.scss` |
| `installable` | `True` |

## Models

### `res.company` — `models/res_company.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_legal_rep_id` | Many2one `res.partner` | string *Legal Representative*, help *The person who signs labour contracts for the company.* |
| `l10n_vn_legal_rep_title` | Char | string *Representative's Title*, help *As printed under the signature, e.g. Giám đốc.* |

### `hr.employee` — `models/hr_employee.py`

All `groups="hr.group_hr_user"`, `tracking=True`, as core's personal fields.

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_id_issue_date` | Date | string *ID Issue Date* |
| `l10n_vn_id_issue_place` | Char | string *ID Issued By*, help *The issuing authority as printed on the card.* |
| `l10n_vn_permanent_address` | Char | string *Permanent Address*, help *Nơi thường trú, as on the ID card or the residence record.* |

### `hr.contract.type` — `models/hr_contract_type.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_document_kind` | Selection | string *Contract Document*: `labour` *Labour contract*, `probation` *Probation contract*, `training` *Training contract*, `none` *No document*; help *The form printed for contracts of this type.* |

### `l10n_vn.payroll.component` — `models/l10n_vn_payroll_component.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_contract_print` | Selection | string *In the Contract*: `amount` *Amount*, `reference` *By reference to the pay regulation*, `welfare` *Bonus and welfare section*, `none` *Not printed*; `compute="_compute_l10n_vn_contract_print"`, `store=True`, `readonly=False` (D1) |

`_compute_l10n_vn_contract_print`: `@api.depends("kind", "legal_nature", "variable")`, D1.

### `hr.contract` — `models/hr_contract.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_document_kind` | Selection | related `contract_type_id.l10n_vn_document_kind` |
| `l10n_vn_work_address_id` | Many2one `res.partner` | string *Workplace*, `compute="_compute_l10n_vn_work_address"`, `store=True`, `readonly=False`, `tracking=True` (D13) |
| `l10n_vn_sign_date` | Date | string *Signing Date*, help *Printed at the top of the contract; left empty, it is written by hand.* |
| `l10n_vn_training_kind` | Selection | string *Training*: `practice` *Practice (tập nghề)*, `apprenticeship` *Apprenticeship (học nghề)*; default `practice` |
| `l10n_vn_commitment_months` | Integer | string *Commitment (months)*, help *Months the trainee commits to work after the labour contract. Empty: no repayment article.* |
| `l10n_vn_training_cost` | Monetary | string *Training Cost* |
| `l10n_vn_training_cost_items` | Text | string *Training Cost Items* |
| `l10n_vn_document_missing` | Text | string *Missing for the Contract Document*, `compute="_compute_l10n_vn_document_missing"`, `compute_sudo=True` (D9) |

| Method | Behaviour |
|---|---|
| `_compute_l10n_vn_work_address` | `@api.depends("employee_id")`: for contracts with an employee, `employee_id.address_id` |
| `_compute_l10n_vn_document_missing` | `@api.depends` on the fields of D10 that live on the contract and the employee; joins `_l10n_vn_document_missing()` with new lines |
| `_l10n_vn_read_amount(line, date)` | `(amount rounded by the currency, None)`, or `(None, "CODE: message")` when `_l10n_vn_amount_on` raises a `UserError` (D4) |
| `_l10n_vn_probation_rate(date)` | `(rate, None)` from `vn.policy.probation_rate`, or `(None, message)` (D4) |
| `_l10n_vn_document_missing()` | `ensure_one`; `[]` for kind `none` or empty; else the labels of D10 in that order, then one message per `amount` or `welfare` line (not `bonus`) whose amount cannot be read, and for probation the rate's message, each the field's `string` translated in the user's language (`self.env["ir.model.fields"]._get(model, name).field_description`); the 12-digit rule as *Personal ID No. (CCCD) must have 12 digits*; the pay-line rule as *A pay line in force on the start date with an amount in the contract* |
| `_l10n_vn_document_values()` | D8, then `ensure_one` and reads `self.sudo().with_context(lang="vi_VN")`. Returns the dict below. Raises `UserError` *Contract %(contract)s has no contract document.* for kind `none` or empty |
| `action_l10n_vn_print_draft()` | `ensure_one`; the `UserError` above for kind `none`; returns `self.env.ref("l10n_vn_hr_contract_document.action_report_contract_draft").report_action(self)` |

**`_l10n_vn_document_values()`** returns, with `doc = env["l10n_vn.contract.document"]` for the helpers:

| Key | Value |
|---|---|
| `kind` | `labour`, `probation` or `training` |
| `title` | *HỢP ĐỒNG LAO ĐỘNG*, *HỢP ĐỒNG THỬ VIỆC*, *HỢP ĐỒNG ĐÀO TẠO* |
| `sign_place`, `sign_date` | D14; `doc._date_parts(l10n_vn_sign_date)` (`("dd", "mm", "yyyy")` or `None`) |
| `company` | dict: `name`, `vat`, `address` (`doc._address(partner)`), `phone`, `email`, `rep_name`, `rep_title` |
| `employee` | dict: `name`; `gender` (*Nam*, *Nữ*, *Khác*, `""`); `birthday`, `id_issue_date` (`doc._date(…)`, `dd/mm/yyyy` or `""`); `nationality` (`country_id.name`, else *Việt Nam*); `personal_id`; `id_issue_place`; `permanent_address`; `current_address` (core's private street, street 2, city and province joined with `, `; `""` when empty or equal to the permanent address); `phone` (`private_phone`); `email` (`private_email`) |
| `party_b` | *NGƯỜI LAO ĐỘNG*; on a training form *NGƯỜI TẬP NGHỀ* or *NGƯỜI HỌC NGHỀ* by `l10n_vn_training_kind` |
| `term` | dict: `fixed` (`bool(date_end)`), `length` (D11 text: *12 tháng*, *45 ngày*, or `""` when not fixed), `date_start`, `date_end` (`dd/mm/yyyy`) |
| `probation` | `None`, or dict when the form is `probation` or the clause applies: `date_end` (`trial_date_end` for a clause, `date_end` for the form), `length` (D11: *6 ngày làm việc*, *30 ngày*), `rate` (`vn.policy.probation_rate` × 100, as an integer when whole, *85*), `job` (Vietnamese text of `l10n_vn_probation_job`: `manager` *công việc của người quản lý doanh nghiệp*, `college` *công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật từ cao đẳng trở lên*, `vocational` *công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật trung cấp, công nhân kỹ thuật, nhân viên nghiệp vụ*, `other` *công việc khác*), `amount` (the sum over `salary` and `allowances` rows whose component has `probation_applies`, × the rate, rounded by the currency) |
| `job`, `workplace` | `job_id.name`; `doc._address(l10n_vn_work_address_id)` |
| `salary`, `allowances`, `supplements` | lists of rows `{"name", "amount", "amount_text", "words", "unit"}` for the `amount` lines of D2, in `component_id.sequence` order |
| `variable` | list of component names, the `reference` lines |
| `welfare` | list of rows; `amount` `None` and `amount_text` empty for `bonus` components and for an amount of 0 |
| `paid_by_transfer` | `l10n_vn_participant_type_id.paid_by_transfer` |
| `payment_text` | *chuyển khoản vào tài khoản ngân hàng mang tên Bên B* when paid by transfer, else *tiền mặt* |
| `insured` | any `fund_*` flag of the participant type |
| `training` | dict: `kind_text` (*tập nghề* / *học nghề*), `commitment_months`, `cost_text`, `cost_words`, `cost_items` |
| `wording` | `env["l10n_vn.contract.wording"]._for_company(company)` |
| `draft` | `True` (step 1) |

### `l10n_vn.contract.document` — `models/l10n_vn_contract_document.py`

`AbstractModel`, `_description = "Contract Document Helpers"`. Helpers the values and templates use.

| Method | Behaviour |
|---|---|
| `_money(amount)` | D12: `"4.500.000"`; `""` for `None` |
| `_words(amount)` | D12: *Bốn triệu năm trăm nghìn đồng*; `""` when `num2words` is missing |
| `_date(date)` | `dd/mm/yyyy`, or `""` |
| `_date_parts(date)` | `("02", "11", "2026")`, or `None` |
| `_address(partner)` | the partner's `_display_address(without_company=True)` lines, stripped, empty ones dropped, joined with `, `; `""` for no partner |

### `l10n_vn.contract.wording` — `models/l10n_vn_contract_wording.py`

`_description = "Contract Wording"`, `_rec_name = "company_id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `company_id` | Many2one `res.company` | required, default `self.env.company`, `ondelete="cascade"` |
| `duties` | Text | string *Duties (Art. 2.2)* |
| `payday` | Char | string *Payday (Art. 3)* |
| `raises` | Html | string *Raises* |
| `hours` | Html | string *Working and Rest Time* |
| `equipment` | Html | string *Protective Equipment* |
| `employee_rights` | Html | string *Employee's Rights and Duties* |
| `employer_rights` | Html | string *Employer's Rights and Duties* |
| `training_content` | Html | string *Training: Content* |
| `training_evaluation` | Html | string *Training: Evaluation and End* |

Every field defaults to its `DEFAULT_WORDING` text. SQL: `company_unique`: `unique(company_id)`, *A company has one contract wording.*

| Method | Behaviour |
|---|---|
| `_for_company(company)` | `@api.model`, as superuser: the company's record, else a new record in memory (`self.new({"company_id": company.id})`), which carries the defaults |

**`DEFAULT_WORDING`** (module constant; the generic `[G]`-level texts of Research and Drafts §6, neutral where the
draft is the garment company's):

| Field | Text |
|---|---|
| `duties` | Thực hiện các công việc của chức danh theo bản mô tả công việc, định mức lao động và sự phân công, điều hành của người quản lý trực tiếp. |
| `payday` | mỗi tháng một lần, theo Quy chế trả lương của Công ty. |
| `raises` | `<p>Bên B được xem xét nâng bậc, nâng lương theo điều kiện, thời gian và mức quy định trong Quy chế trả lương và thang lương, bảng lương của Công ty.</p>` |
| `hours` | `<p>1. Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần, theo Nội quy lao động của Công ty.</p><p>2. Làm thêm giờ: khi có nhu cầu, Bên A được tổ chức làm thêm giờ khi Bên B đồng ý, trong giới hạn của pháp luật.</p><p>3. Nghỉ hằng tuần, nghỉ hằng năm, nghỉ lễ, tết, nghỉ việc riêng và nghỉ không hưởng lương: theo Bộ luật Lao động và Nội quy lao động của Công ty.</p>` |
| `equipment` | `<p>Bên B được cấp phát trang bị bảo hộ lao động phù hợp với công việc theo quy định của Công ty và pháp luật về an toàn, vệ sinh lao động.</p>` |
| `employee_rights` | `<p>1. Được trả lương đầy đủ, đúng hạn và hưởng các chế độ theo hợp đồng này, các quy chế của Công ty và pháp luật.</p><p>2. Hoàn thành công việc được giao; chấp hành Nội quy lao động, quy định về an toàn, vệ sinh lao động và sự điều hành hợp pháp của Bên A.</p><p>3. Bồi thường thiệt hại khi làm hư hỏng, mất tài sản của Công ty theo Nội quy lao động và pháp luật.</p><p>4. Thông báo cho Bên A khi thay đổi nơi cư trú, số điện thoại hoặc tài khoản ngân hàng.</p>` |
| `employer_rights` | `<p>1. Bố trí, điều hành công việc; khen thưởng và xử lý kỷ luật lao động theo Nội quy lao động và pháp luật.</p><p>2. Trả lương đầy đủ, đúng hạn; bảo đảm điều kiện làm việc, an toàn, vệ sinh lao động.</p><p>3. Đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp và thực hiện các nghĩa vụ khác theo hợp đồng này và pháp luật.</p>` |
| `training_content` | `<p>Bên B được hướng dẫn thực hành công việc nêu tại Điều 1 tại nơi làm việc, dưới sự hướng dẫn của người được Bên A phân công, theo chương trình và tiêu chuẩn tay nghề của Công ty.</p>` |
| `training_evaluation` | `<p>1. Bên A đánh giá tay nghề của Bên B trong và khi kết thúc thời gian đào tạo theo tiêu chuẩn của Công ty và thông báo kết quả cho Bên B.</p><p>2. Bên A có quyền chấm dứt hợp đồng này trong thời gian đào tạo hoặc khi kết thúc nếu Bên B không đạt tiêu chuẩn tay nghề, sau khi thông báo kết quả đánh giá cho Bên B.</p><p>3. Khi kết thúc thời gian đào tạo, nếu Bên B đạt tiêu chuẩn và đủ điều kiện theo Bộ luật Lao động, hai bên giao kết hợp đồng lao động.</p>` |

## Security

`security/l10n_vn_contract_document_security.xml`: rule `l10n_vn_contract_wording_company_rule` on
`l10n_vn.contract.wording`, global, `[('company_id', 'in', company_ids)]`.

`security/ir.model.access.csv`:

| id | model | group | r w c u |
|---|---|---|---|
| `access_l10n_vn_contract_wording_manager` | `l10n_vn.contract.wording` | `hr_contract.group_hr_contract_manager` | 1 1 1 1 |
| `access_l10n_vn_contract_wording_officer` | `l10n_vn.contract.wording` | `hr_contract.group_hr_contract_employee_manager` | 1 0 0 0 |
| `access_l10n_vn_contract_wording_payroll` | `l10n_vn.contract.wording` | `payroll.group_payroll_user` | 1 0 0 0 |

## Report

### `data/report_paperformat.xml`

`paperformat_l10n_vn_contract`: *Vietnamese Contract (A4)*, `A4`, portrait, margins top 20, bottom 20, left 30,
right 15 (mm), `header_line` False, `header_spacing` 0, `dpi` 90.

### `report/l10n_vn_contract_document_reports.xml`

`action_report_contract_draft`: `ir.actions.report`, model `hr.contract`, *Contract (Draft)*, `qweb-pdf`,
`report_name` and `report_file` `l10n_vn_hr_contract_document.report_contract_draft`, paperformat above,
`binding_model_id` `hr_contract.model_hr_contract`, `binding_type` `report`, `groups_id` `payroll.group_payroll_user`,
`print_report_name` `'Hop dong (nhap) - %s' % object.employee_id.name`.

### `report/l10n_vn_contract_document_templates.xml`

Building blocks read the variable `v` (the values dict) and `doc` (`env["l10n_vn.contract.document"]`). A value
shown through the block `value` prints as a dotted space (`span.o_dots`) when empty.

| Template | Content |
|---|---|
| `report_contract_draft` | `web.html_container`; for each record of `docs`: `v = o._l10n_vn_document_values()`, then a `div.article.l10n_vn_contract` (with `data-oe-model`, `data-oe-id`, `data-oe-lang`), its page breaking before every record after the first, calling `form_labour`, `form_probation` or `form_training` by `v['kind']` |
| `value` | `t-out` of `value`, or `span.o_dots` |
| `doc_header` | *BẢN NHÁP* line when `v['draft']`; the motto (*CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM* / *Độc lập – Tự do – Hạnh phúc*, the rule under it); place and date line right-aligned: `{sign_place}, ngày {dd} tháng {mm} năm {yyyy}`, with dotted parts when `sign_date` is `None`; the title; *Số: ……*; the basis lines of the form, given as `bases` (a list of strings) by the caller; *Chúng tôi gồm:*; party A (Research and Drafts §5.3: name, enterprise code, head-office address, phone, e-mail when set, representative and title); party B with `v['party_b']` (name and sex, birthday and nationality, CCCD with issue date and place, permanent address, current address when set, phone and e-mail when set) |
| `doc_closing` | The closing article, numbered by the caller's `article` (Research and Drafts §5.4), then a two-column signature table: left *BÊN B* / `v['party_b']` / *(Ký, ghi rõ họ tên)* / the employee's name; right *BÊN A* / the representative's title upper case / *(Ký, ghi rõ họ tên, đóng dấu)* / the representative's name |
| `amount_row` | one amount row: the row's name (left out when `with_name` is `False`), `amount_text` *đồng/*`unit` and *(Bằng chữ: …)*; a dotted space without an amount |
| `form_labour` | `doc_header` with bases [*Căn cứ Bộ luật Lao động số 45/2019/QH14 ngày 20 tháng 11 năm 2019 và các văn bản hướng dẫn thi hành;*, *Căn cứ nhu cầu và năng lực của hai bên,*]; the intro sentence; articles 1–11 of Research and Drafts §6.1 in their `[G]` text with the values of §5.2, where article 1.3 prints the probation clause or *Không áp dụng.*; 2.2 is the wording's `duties`; 3.1 the `salary` rows (one row: the amount and words, no name; several: each by name); 3.2 the `allowances` rows or *Không*; 3.3 the `supplements` rows and, for each `variable` name, *{name}: trả theo năng suất, kết quả thực hiện công việc của Bên B, theo Quy chế trả lương của Công ty.*, or *Không*; 3.4 the overtime sentence; 3.5 *Hình thức trả lương:* `payment_text`; 3.6 *Kỳ hạn trả lương:* the wording's `payday`; 4.1 the bonus sentence; 4.2 the `welfare` rows or *theo quy định của Công ty*; article 5 `raises`; 6 `hours`; 7 `equipment`; 8 the insurance sentence when `insured`, else *Bên B không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc theo quy định của pháp luật.*; 9 the training sentence; 10 `employee_rights`; 11 `employer_rights`; then `doc_closing` with `article` 12 |
| `form_probation` | `doc_header` with the labour bases; articles 1–6 of Research and Drafts §6.3: 1 period and job category from `v['probation']`; 2 work and workplace as labour article 2; 3 the job's salary (`salary` and `allowances` rows), the probation rate and `probation.amount` with words, the `variable` names by reference, then *Hình thức trả lương:* `payment_text`*. Kỳ hạn trả lương:* `payday` in one clause; 4 `hours`; 5 `equipment`; 6 the end of probation; `doc_closing` with `article` 7 |
| `form_training` | `doc_header` with bases [*Căn cứ Bộ luật Lao động số 45/2019/QH14 ngày 20 tháng 11 năm 2019, Điều 61;*, *Căn cứ nhu cầu và khả năng của hai bên,*]; articles 1–6 of Research and Drafts §6.4: 1 kind, job, term, workplace, no tuition; 2 `training_content`; 3 the `salary` rows as the training allowance *, tính theo số ngày làm việc thực tế trong tháng*, the `variable` names, then payment and payday in one clause as on the probation form; 4 `hours`; 5 `equipment`; 6 `training_evaluation`; article 7 only when `training.commitment_months`: commitment, cost with words and items, repayment; `doc_closing` with `article` 7 or 8 |

### `static/src/scss/l10n_vn_contract_document.scss`

`.l10n_vn_contract`: `font-family: "DejaVu Serif", serif` (the only serif font in the image), `font-size: 12pt`,
`line-height: 1.4`, `text-align: justify`, black; the motto and title centred, the title bold 14pt; `.o_dots`
dotted underline, `span.o_dots` inline-block 40 mm; `.o_draft` centred, bold, letter-spaced; tables full width,
collapsed; the signature table's cells centred, 25 mm space above the names.

## Views

| File | Record | Inherits | Content |
|---|---|---|---|
| `res_company_views.xml` | `res_company_view_form_l10n_vn_contract` | `base.view_company_form` | after `company_registry`: `country_code` (invisible; the form does not carry it, and a modifier needs its field in the view), `l10n_vn_legal_rep_id` and `l10n_vn_legal_rep_title`, both invisible when `country_code != 'VN'` |
| `hr_employee_views.xml` | `hr_employee_view_form_l10n_vn_contract` | `l10n_vn_payroll.hr_employee_view_form_l10n_vn_payroll` | after `l10n_vn_personal_id`: `l10n_vn_id_issue_date`, `l10n_vn_id_issue_place`, `l10n_vn_permanent_address` |
| `hr_contract_type_views.xml` | `hr_contract_type_view_form_l10n_vn_contract`, `hr_contract_type_view_tree_l10n_vn_contract` | `hr.hr_contract_type_view_form`, `hr.hr_contract_type_view_tree` | `l10n_vn_document_kind` after `name` |
| `l10n_vn_payroll_component_views.xml` | `l10n_vn_payroll_component_view_form_l10n_vn_contract` | `l10n_vn_payroll.l10n_vn_payroll_component_view_form` | `l10n_vn_contract_print` after `section` |
| `hr_contract_views.xml` | `hr_contract_view_form_l10n_vn_contract` | `hr_contract.hr_contract_view_form` | in `header`, button *Print Draft* (`action_l10n_vn_print_draft`, `groups="payroll.group_payroll_user"`, invisible when `l10n_vn_document_kind in (False, 'none')`); before `div[@name='button_box']`, `div.alert.alert-warning` (invisible when `not l10n_vn_document_missing`) with *Missing for the contract document:* and `l10n_vn_document_missing`; after page `information`, page *Contract Document* (`name="l10n_vn_document"`, invisible when `l10n_vn_document_kind in (False, 'none')`) with `l10n_vn_document_kind`, `l10n_vn_work_address_id`, `l10n_vn_sign_date`, and a group *Training* (invisible when `l10n_vn_document_kind != 'training'`) with `l10n_vn_training_kind`, `l10n_vn_commitment_months`, `l10n_vn_training_cost`, `l10n_vn_training_cost_items` |
| `l10n_vn_contract_wording_views.xml` | `l10n_vn_contract_wording_view_list`, `_view_form`, `action_l10n_vn_contract_wording` | | list: `company_id`; form: `company_id` (`groups="base.group_multi_company"`), then the fields in their order, `duties` and `payday` as text inputs, the others as HTML editors; action *Contract Wording* |
| `menus.xml` | `menu_l10n_vn_contract_wording` | | *Contract Wording* under `hr.menu_human_resources_configuration`, action above, `groups="hr_contract.group_hr_contract_manager"` |

## Tests

`TransactionCase`, `post_install` and `-at_install` (fixtures create employees and partners).

**`tests/common.py`** — `ContractDocumentCase(PayrollCase)` (`odoo.addons.l10n_vn_payroll.tests.common`). Fixtures:
the company gets `vat`, `street`, a province, `l10n_vn_legal_rep_id` (a new partner *Test Director*) and title
*Giám đốc*; the employee gets `birthday` 1995-03-04, `gender` `female`, `l10n_vn_personal_id` `001195012345`,
issue date 2021-05-06 and place *Cục Cảnh sát QLHC về TTXH*, permanent address *Ấp 1, xã Test, An Giang*, and a
work address partner; contract types `labour`, `probation`, `training` and `none` (codes prefixed `TEST_`); parameter
`vn.policy.probation_rate` 0.85 from 2026-01-01; components `BASE` (`job_salary`, `in_si_base`, `probation_applies`,
source `line`), `PROD` (`variable_salary`, `variable`, source `line`), `TRAIN` (`job_salary`, source `line`),
`PHONE` (`welfare`, source `line`); helper `_doc_contract(kind, **values)` creates a draft contract of that kind
for the employee from 2026-11-02 with `BASE` 4,500,000 and `PROD` 500,000 lines from its start.

**`tests/test_document_data.py`**

| Test | Asserts |
|---|---|
| `test_print_mode_defaults` | D1 on `BASE`, `PROD`, `TRAIN`, `PHONE`, a `bonus` earning and a `deduction`; an edited mode is kept after writing the component's `name` |
| `test_print_mode_follows_flags` | setting `variable` on a `job_salary` component turns `amount` into `reference` |
| `test_work_address_default` | a contract created for the employee takes `address_id`; changing the employee takes the new one's |
| `test_missing_none_when_complete` | the labour fixture contract lists nothing |
| `test_missing_lists_employee_fields` | blanking `birthday`, `l10n_vn_id_issue_place` and `l10n_vn_permanent_address` lists those three labels |
| `test_missing_personal_id_length` | an 11-digit ID gives the 12-digit message |
| `test_missing_company_representative` | no representative lists *Legal Representative* |
| `test_missing_probation_job` | a clause without `l10n_vn_probation_job` lists it |
| `test_missing_amount_line` | a contract with only the `PROD` line lists the pay-line message |
| `test_missing_empty_for_kind_none` | a contract of the `none` type lists nothing, whatever is missing |
| `test_warning_shows_approval_limits` | (step 2, D36) a clause of 8 working days for `other`: the missing data list is empty, the warning field names the limit |
| `test_wording_one_per_company` | a second wording record for the company raises |
| `test_wording_defaults_without_record` | `_for_company` without a record returns the `DEFAULT_WORDING` `payday` |

**`tests/test_document_report.py`**

| Test | Asserts |
|---|---|
| `test_helpers` | `_money(4500000)` = `4.500.000`; `_words(4500000)` = *Bốn triệu năm trăm nghìn đồng*; `_date` and `_date_parts` of 2026-11-02 |
| `test_values_labour` | 12-month contract (to 2026-11-01 next year): `term.length` *12 tháng*; `salary` one row `4.500.000`; `variable` the `PROD` name; `paid_by_transfer` and `insured` True; `probation` None |
| `test_values_length_in_days` | an end date not on a month boundary gives the length in days |
| `test_values_probation_clause` | clause to 2026-11-09, job `other`, the company calendar (Monday–Friday): `length` *6 ngày làm việc*, `rate` 85, `amount` 3,825,000 |
| `test_values_training` | `party_b` *NGƯỜI TẬP NGHỀ*; with `l10n_vn_commitment_months` 6 and a cost, `training` holds them; without, `commitment_months` 0 |
| `test_values_current_address` | empty private address → `current_address` `""`; a different one → printed |
| `test_report_labour_renders` | `_render_qweb_html` of the draft report: *BẢN NHÁP*, *HỢP ĐỒNG LAO ĐỘNG*, the employee's name, `4.500.000`, the words, *Theo Quy chế trả lương* sentence with the `PROD` name, *Điều 12* |
| `test_report_probation_and_training_render` | the probation form shows *HỢP ĐỒNG THỬ VIỆC* and *Điều 7*; the training form with a commitment shows *Điều 8* and without one *Điều 7* as its last article |
| `test_report_uses_company_wording` | a wording record with `payday` *vào ngày 10 của tháng kế tiếp* prints it |
| `test_report_dots_for_missing` | without an issue place the report still renders, with a dotted span |
| `test_print_draft_refused_for_none` | `action_l10n_vn_print_draft` on a `none` contract raises `UserError`; on a labour contract returns the report action |
| `test_unreadable_amount_prints_blank` | a `BASE`-like component on a parameter that does not exist: the salary row's amount is `None` and its text empty, the missing list holds one message starting with its code, the report renders |
| `test_unreadable_probation_rate_prints_blank` | a clause contract from 2025-12-01, before `vn.policy.probation_rate` starts: `rate` and `amount` `None`, one missing message naming the parameter, the report renders |
| `test_values_need_payroll_group` | a user in `hr_contract.group_hr_contract_manager` without payroll groups reads the contract's `name` (positive control) and gets `AccessError` from `_l10n_vn_document_values()`; a payroll user (`payroll.group_payroll_user` + contract manager) gets the values. Both through `_as` |

26 tests.

## Step 1.1: extra articles and individual terms

### Folder structure

`models/l10n_vn_contract_article.py` (new), `models/__init__.py` gains `from . import l10n_vn_contract_article`
after `l10n_vn_contract_wording`; `tests/test_document_articles.py` (new), imported in `tests/__init__.py`.
Version stays `18.0.1.0.0`.

### `l10n_vn.contract.article` — `models/l10n_vn_contract_article.py`

`_description = "Contract Article"`, `_order = "wording_id, kind, sequence, id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `wording_id` | Many2one `l10n_vn.contract.wording` | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `wording_id.company_id`, stored |
| `kind` | Selection | string *Form*: `labour` *Labour contract*, `probation` *Probation contract*, `training` *Training contract*; required, default `labour` |
| `sequence` | Integer | default 10 |
| `title` | Char | required, string *Title*, e.g. *Bảo mật thông tin* |
| `body` | Html | string *Text* |
| `active` | Boolean | default True |

### `l10n_vn.contract.wording` additions

| Field | Type | Attributes |
|---|---|---|
| `article_ids` | One2many `l10n_vn.contract.article` | `wording_id`, string *Extra Articles*, `context={"active_test": False}` |

### `hr.contract` additions

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_individual_terms` | Html | string *Individual Terms*, help *Terms agreed with this employee only, printed as their own article.* |

`_l10n_vn_document_values()` gains:

| Key | Value |
|---|---|
| `extra_articles` | list of `{"number", "title", "body"}`: the active articles of the company's saved wording record whose `kind` is the form's, in `sequence` order, numbered from the first number after the fixed articles (D17) |
| `individual_terms` | `None`, or `{"number", "body"}` when `l10n_vn_individual_terms` is not empty, numbered after the extra articles |
| `closing_number` | the number after the last of these |

Fixed article counts: labour 11; probation 6; training 6, or 7 when `l10n_vn_commitment_months` is set.

### Security

`ir.model.access.csv` gains, for `l10n_vn.contract.article`, the same three lines as the wording record: contract
administrators 1 1 1 1, line managers (`hr_contract.group_hr_contract_employee_manager`) 1 0 0 0, payroll users
1 0 0 0. `l10n_vn_contract_document_security.xml` gains the rule `l10n_vn_contract_article_company_rule`, global,
`[('company_id', 'in', company_ids)]`.

### Report

| Template | Change |
|---|---|
| `doc_extra` (new) | for each of `v['extra_articles']`: *Điều {number}. {title}* as an article heading, the body as a clause; then, when `v['individual_terms']`: *Điều {number}. Thỏa thuận khác* and its body |
| `form_labour`, `form_probation`, `form_training` | `doc_extra` before `doc_closing`; `doc_closing` gets `article` = `v['closing_number']` instead of the fixed 12, 7, 7 or 8 |

### Views

| File | Change |
|---|---|
| `l10n_vn_contract_wording_views.xml` | the form gains, after the training groups, a group *Extra Articles* with `article_ids` as an editable list: `sequence` (handle), `kind`, `title`, `active` (toggle); the body edited in a form opened from the line (`l10n_vn_contract_article_view_form`: `kind`, `title`, `active`, `body`) |
| `hr_contract_views.xml` | page *Contract Document* gains a group *Individual Terms* with `l10n_vn_individual_terms` (no label, full width) |

### Tests — `tests/test_document_articles.py`

`post_install`, `-at_install`, on `ContractDocumentCase`. Helper `_article(kind, title, sequence=10, **values)`
creates the company's wording record when missing and an article on it.

| Test | Asserts |
|---|---|
| `test_extra_articles_numbered_after_fixed` | two labour articles (sequences 20 and 10): `extra_articles` numbers 12 and 13 in sequence order; `closing_number` 14; the report shows *Điều 12.* with the sequence-10 title and *Điều 14. Điều khoản thi hành* |
| `test_extra_articles_by_form` | a probation article does not print on a labour contract; on a probation contract it is *Điều 7.* and the closing *Điều 8.* |
| `test_inactive_article_not_printed` | an archived labour article: `extra_articles` empty, closing 12 |
| `test_individual_terms` | `l10n_vn_individual_terms` set on a labour contract with one extra article: *Điều 13. Thỏa thuận khác* with the text, closing 14; set to `<p><br></p>`: not printed, closing 13 |
| `test_training_articles_after_repayment` | a training contract with a commitment and one training article: repayment *Điều 7.*, the article *Điều 8.*, closing 9 |
| `test_articles_of_other_company_ignored` | an article on another company's wording record does not print |

26 + 6 = 32 tests.

## Step 2: approve and lock

### Folder structure

`models/l10n_vn_contract_version.py` (new), imported after `l10n_vn_contract_article`; `data/l10n_vn_contract_actions.xml`
(new, the server action), after the report files in `data`; `tests/test_document_approval.py` and
`tests/test_document_lock.py` (new). The report file and template are renamed in place (D26). Version
`18.0.1.1.0`.

### `l10n_vn.contract.version` — `models/l10n_vn_contract_version.py`

`_description = "Contract Version"`, `_order = "contract_id, sequence"`, `_rec_name = "number"`.

| Field | Type | Attributes |
|---|---|---|
| `contract_id` | Many2one `hr.contract` | required, `ondelete="cascade"`, index |
| `company_id`, `employee_id` | Many2one | related from the contract, stored |
| `sequence` | Integer | 0 for the contract; annexes from 1 (step 3) |
| `kind` | Selection | `contract` *Contract* / `annex` *Annex*, required |
| `number` | Char | D23; empty for kind `none` |
| `effective_date` | Date | required; version 0: `date_start` |
| `state` | Selection | `draft` *Draft* / `approved` *Approved* / `cancelled` *Cancelled*; step 2 writes `approved` |
| `reason` | Char | for annexes (step 3) |
| `terms` | Json | D24 |
| `approved_by` | Many2one `res.users` | |
| `approved_at` | Datetime | |

SQL: `contract_sequence_unique`: `unique(contract_id, sequence)`.

### `res.company` additions

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_contract_code` | Char | string *Contract Number Code*, help *Added at the end of contract numbers, e.g. QP in 0012/2026/HĐLĐ-QP.* |
| `l10n_vn_contract_approval` | Boolean | string *Contracts Run Only When Approved*, help *A contract becomes Running only through approval of its contract document.* (D27) |

Both on the company form after `l10n_vn_legal_rep_title`, with the same visibility.

### `hr.contract` additions

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_version_ids` | One2many `l10n_vn.contract.version` | `contract_id`, string *Versions*, `copy=False`, groups `hr_contract.group_hr_contract_manager,payroll.group_payroll_user` |
| `l10n_vn_version_id` | Many2one `l10n_vn.contract.version` | string *Approved Version*, `copy=False`, readonly; the latest approved version |
| `l10n_vn_approved` | Boolean | string *Approved*, `copy=False`, readonly, `tracking=True` |
| `l10n_vn_number` | Char | related `l10n_vn_version_id.number`, string *Contract Number* |
| `l10n_vn_company_approval` | Boolean | related `company_id.l10n_vn_contract_approval` |

| Method | Behaviour |
|---|---|
| `_l10n_vn_document_terms()` | the `render` keys of D24 computed live on `date_start`: step 1's computation, moved out of `_l10n_vn_document_values` |
| `_l10n_vn_document_raw()` | the `raw` part of D24 |
| `_l10n_vn_document_values()` | D8 first; then terms = `l10n_vn_version_id.terms["render"]` when approved (D25), else `_l10n_vn_document_terms()`; merged with the parties, signing place and date, wording, extra articles, `closing_number` (from the terms' `kind`, commitment and individual terms), `number` (`l10n_vn_number` or `""`) and `draft` (`not l10n_vn_approved`). `individual_terms` is built from `individual_terms_body` (as `Markup`) |
| `_l10n_vn_approval_problems()` | D22: `_l10n_vn_document_missing()` + the limits, as strings; `[]` for kind `none` |
| `_l10n_vn_next_number()` | D23 |
| `action_l10n_vn_approve()` | D21, D31; refuses users outside `hr_contract.group_hr_contract_manager` with an `AccessError`, then works as superuser with `l10n_vn_contract_unlock`; posts *Contract approved: %(number)s* (or *Contract approved*) in the chatter |
| `_l10n_vn_locked_fields()` | the list of D28 |
| `create` | D27 |
| `write` | D27, D28, D29; checks before `super()` |
| `action_l10n_vn_print()` | step 1's `action_l10n_vn_print_draft`, renamed, returning `action_report_contract` with `config=False` |
| `unlink` | D35 |
| `_l10n_vn_approve_one()` | one contract's approval (D21), as superuser with `l10n_vn_contract_unlock`; `action_l10n_vn_approve` calls it directly for one contract and in a savepoint per contract for several, returning a success notification, or the warning of D31, each with a reload |

`l10n_vn_document_missing` is empty for an approved contract.

### `l10n_vn.payroll.contract.line` — `models/l10n_vn_payroll_contract_line.py` (new in this module)

`_inherit = "l10n_vn.payroll.contract.line"`. `create`, `write` and `unlink` apply D30 to lines whose contract is
approved, unless `l10n_vn_contract_unlock` is in the context, with a `ValidationError` *Contract %(contract)s is
approved: its pay line %(component)s cannot change. Use an amendment.*

### Data — `data/l10n_vn_contract_actions.xml`

`action_l10n_vn_contract_approve`: `ir.actions.server`, model `hr.contract`, *Approve Contracts*, `binding_model_id`
`hr_contract.model_hr_contract`, `binding_view_types` `list`, `groups_id` `hr_contract.group_hr_contract_manager`,
code `action = records.action_l10n_vn_approve()`.

### Security

`ir.model.access.csv`: `l10n_vn.contract.version`, read only, for `hr_contract.group_hr_contract_manager` and
`payroll.group_payroll_user`. `l10n_vn_contract_document_security.xml`: `l10n_vn_contract_version_company_rule`,
global, `[('company_id', 'in', company_ids)]`.

### Report

`l10n_vn_contract_document_reports.xml`: `action_report_contract` (D26) in place of `action_report_contract_draft`,
same paperformat, binding and groups; `print_report_name`
`(object.l10n_vn_number and (object.l10n_vn_number.replace('/', '-') + ' - ') or 'Hop dong (nhap) - ') + object.employee_id.name`.
Templates: `report_contract` in place of `report_contract_draft`; `doc_header` prints *Số: {number}* when
`v['number']`, else the dotted space.

### Views

| File | Change |
|---|---|
| `hr_contract_views.xml` | header: *Approve* (`action_l10n_vn_approve`, `groups="hr_contract.group_hr_contract_manager"`, `class="btn-primary"`, invisible when `l10n_vn_approved` or `state not in ('draft', 'open')`); *Print* (`action_l10n_vn_print`) in place of *Print Draft*, same visibility; both statusbar fields `readonly="l10n_vn_company_approval"` with the hidden field; the warning invisible when `l10n_vn_approved` too; page *Contract Document* gains `l10n_vn_approved` and `l10n_vn_number` (read-only) at the top, and a page *Versions* after it (`groups` as the field, invisible when no version) listing `sequence`, `kind`, `number`, `effective_date`, `state`, `approved_by`, `approved_at` |
| `hr_contract_views.xml` (list) | inherits `hr_contract.hr_contract_view_tree`: `l10n_vn_number` and `l10n_vn_approved`, optional shown |
| `res_company_views.xml` | the two new fields (above) |

### Tests

`post_install`, `-at_install`, on `ContractDocumentCase`, whose fixtures gain the company code *TC* and the statutory
parameters (`company._l10n_vn_payroll_ensure_parameters()`). Step 1's tests use `action_report_contract`.

**`tests/test_document_approval.py`**

| Test | Asserts |
|---|---|
| `test_approve_numbers_and_snapshot` | a labour contract from 2026-11-02 approved: version 0 `approved`, number *0001/2026/HĐLĐ-TC*, `render.salary[0].amount` 4,500,000, `raw` holds `job_id` and both pay lines; `l10n_vn_approved`; `state` `open`; a chatter message |
| `test_approve_future_is_incoming` | a contract from next year: `state` stays `draft`, `kanban_state` `done` |
| `test_numbers_per_form_and_year` | a second labour contract *0002/2026/HĐLĐ-TC*; a probation contract *0001/2026/HĐTV-TC*; a labour contract from 2027 *0001/2027/HĐLĐ-TC*; without company code, no suffix |
| `test_approve_refused_with_missing` | no birthday: `UserError` naming it; no version, not approved |
| `test_approve_refused_beyond_limits` | a clause of 8 working days for `other`; a fixed-term contract of 37 months; a training contract of 4 months: each refused with its limit |
| `test_approve_kind_none` | approved, no number, locked |
| `test_approve_needs_manager` | a line manager (`group_hr_contract_employee_manager`, the employee's manager, since that group reads only the contracts of the employees it manages, `ir_rule_hr_contract_employee_manager`) reads the contract (positive control) and gets `AccessError` approving |
| `test_approve_selection` | two contracts, one without birthday on its employee: the action returns a notification naming the failing one; the other is approved |
| `test_print_from_snapshot` | a contract on a parameter-based component approved at 4,500,000; the parameter's value then changed to 5,000,000: the report prints *4.500.000* and the number, without *BẢN NHÁP*; the live terms read 5,000,000 |
| `test_print_parties_live` | after approval the employee's permanent address changes: the report prints the new one |
| `test_versions_access` | an HR officer without payroll groups gets `AccessError` reading versions; a payroll user reads them |
| `test_copy_unapproved` | a copy of an approved contract has no version and is not approved |

**`tests/test_document_lock.py`**

| Test | Asserts |
|---|---|
| `test_switch_refuses_running` | switch on: `write({"state": "open"})` on a draft contract and `create` with `state` `open` raise `ValidationError`; core's `update_state()` on an unapproved *Incoming* contract leaves it draft without error; an approved *Incoming* contract opens |
| `test_switch_off_allows_running` | switch off: a draft contract can be set `open` |
| `test_lock_terms` | approved: writing `job_id` raises; writing `department_id`, `notes` and the same `job_id` value succeed (positive controls) |
| `test_lock_superuser` | `sudo()` writing `job_id` raises |
| `test_lock_date_end` | an earlier `date_end` is accepted; a later one and removing it raise |
| `test_departure_on_locked` | `hr.departure.wizard` on the employee with *Set Contract End Date*: the approved contract ends on the departure date and closes |
| `test_pay_lines_locked` | approved: the `BASE` line's amount, a new `BASE` line, and deleting it raise; a new `PROD` line from a later date and its `date_to` succeed; a line of a reference component the contract lacks raises; deleting the only `PROD` line raises; a `PHONE` line is free |
| `test_unapproved_not_locked` | an unapproved contract's job and pay lines change freely |

20 new tests, 52 in all.

## Step 3: amendments, annexes, next contract

### Folder structure

```
wizards/
├── __init__.py
├── l10n_vn_contract_amend_wizard.py        ← Amend (D39)
├── l10n_vn_contract_annex_batch_wizard.py  ← Annexes for a Date (D48)
├── l10n_vn_contract_next_wizard.py         ← Next Contract (D49, D50)
└── l10n_vn_contract_wizard_views.xml
```

`__init__.py` gains `from . import wizards`; `report/l10n_vn_contract_annex_templates.xml` (new), after the contract
templates; `tests/test_document_amendment.py` and `tests/test_document_next.py` (new). `data` gains the wizard views
after the server action. Access lines for the three wizards (`base.group_user`, 1 1 1 1; each action checks D38).
Version `18.0.1.2.0`.

### `hr.contract` additions and changes

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_amendment_id` | Many2one `l10n_vn.contract.version` | string *Amendment in Progress*, `copy=False`, readonly |
| `l10n_vn_amendment_date` | Date | related `l10n_vn_amendment_id.effective_date` |
| `l10n_vn_amendment_reason` | Char | related `l10n_vn_amendment_id.reason` |
| `l10n_vn_number` | Char | now `compute="_compute_l10n_vn_number"`: the number of the approved version of sequence 0 (D45) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_document_terms(date=None)` | as step 2, on `date` (default `date_start`): pay lines in force, amounts and `vn.policy.probation_rate` read on that date |
| `_l10n_vn_document_missing(date=None)`, `_l10n_vn_approval_problems(date=None)` | as step 2, the pay-line and parameter checks on `date` (default `date_start`); the limits of D22 stay on `date_start` |
| `_l10n_vn_paid_until()` | D39 |
| `_l10n_vn_changes(old, new, kind)` | D43: the `changes` list from two `render` dicts |
| `_l10n_vn_amend(date, reason)` | D39, as superuser |
| `action_l10n_vn_amend()` | opens the amend wizard (D38) |
| `action_l10n_vn_approve_amendment()` | D42 |
| `action_l10n_vn_cancel_amendment()` | D44 |
| `action_l10n_vn_next_contract()` | opens the next-contract wizard |
| `_l10n_vn_version_zero()` | the approved version of sequence 0 |
| `_l10n_vn_document_values()` | reads `_l10n_vn_version_zero().terms["render"]` (D45) |
| `_l10n_vn_locked_fields()` | during an amendment, the fields of D40 are left out, and a write moving `l10n_vn_commitment_months` between 0 and more is refused |
| `_compute_l10n_vn_document_missing` | during an amendment, `_l10n_vn_approval_problems(l10n_vn_amendment_date)` |

`l10n_vn.payroll.contract.line`: during an amendment of its contract, `create`, `write` and `unlink` follow D41
instead of D30, with the message *Contract %(contract)s is being amended from %(date)s: %(rule)s* naming the rule.

### `l10n_vn.contract.version` additions

| Method | Behaviour |
|---|---|
| `_l10n_vn_annex_values()` | D8's group check; the contract's parties as `_l10n_vn_document_values()` reads them, with `render` taken from this version; plus `annex_title`, `annex_number`, `contract_number`, `contract_sign_date` (`dd/mm/yyyy` or `""`), `effective_date` (`dd/mm/yyyy`), `changes` |
| `action_l10n_vn_print()` | `action_report_contract_annex` for an approved annex, `config=False` |

### Wizards

| Model | Fields | Action |
|---|---|---|
| `l10n_vn.contract.amend.wizard` (transient) | `contract_id` (required), `effective_date` (required, default today), `reason` (Char, required) | *Open Amendment*: `contract._l10n_vn_amend(effective_date, reason)` |
| `l10n_vn.contract.annex.batch.wizard` (transient) | `date` (required), `reason` (Char, required, default *Điều chỉnh tiền lương*), `contract_ids` (Many2many, default `active_ids`), `line_ids` (One2many `l10n_vn.contract.annex.batch.line`: `contract_id`, `groups` Char), filled by *Find Changes* | *Find Changes* fills the lines (D48); *Confirm* amends and approves each, returning D31's notification |
| `l10n_vn.contract.next.wizard` (transient) | `contract_id` (required), `date_start` (required), `contract_type_id` (required), `date_end` | *Create Contract*: D50, returning the new contract's form |

### Report

| File | Content |
|---|---|
| `l10n_vn_contract_document_templates.xml` | article bodies as templates (D47): `body_work`, `body_labour_salary`, `body_labour_bonus`, `body_labour_insurance`, `body_probation_salary`, `body_training_1`, `body_training_salary`, `body_training_commitment`, `body_individual`; the forms call them under their headings, so a printed contract is unchanged |
| `l10n_vn_contract_annex_templates.xml` | `report_contract_annex` (D46), on `docs` of `l10n_vn.contract.version`; `annex_body` calls the body template of each change's group for the contract's form |
| `l10n_vn_contract_document_reports.xml` | `action_report_contract_annex`: model `l10n_vn.contract.version`, *Contract Annex*, `qweb-pdf`, the contract paperformat, `groups_id` payroll users, no binding, `print_report_name` `object.number.replace('/', '-')` |

### Views

| File | Change |
|---|---|
| `hr_contract_views.xml` | header: *Amend* (`action_l10n_vn_amend`, contract administrators, visible when approved and no amendment open), *Approve Amendment* and *Cancel Amendment* (visible during an amendment), *Next Contract* (`action_l10n_vn_next_contract`, contract administrators, visible when approved); the amendment banner (D51) before the warning; the *Versions* list gains `reason` and a *Print* button (`action_l10n_vn_print`, payroll users, visible on approved annexes) |
| `wizards/l10n_vn_contract_wizard_views.xml` | the three wizard forms and their actions |
| `wizards/l10n_vn_contract_wizard_views.xml` | the window action *Annexes for a Date*, bound to the contract list (contract administrators), opening the batch wizard with the selection as its contracts |

### Tests

`post_install`, `-at_install`, on `ContractDocumentCase`.

**`tests/test_document_amendment.py`**

| Test | Asserts |
|---|---|
| `test_amend_opens` | an approved contract amended from 2027-01-01: version 1 `draft` with `raw_before`; `l10n_vn_amendment_id` set; `job_id` can be written; a later `date_end`, `contract_type_id` and `date_start` stay refused |
| `test_amend_dates` | an effective date before `date_start`, after `date_end`, or on or before `_l10n_vn_paid_until()` (patched to 2026-12-31) is refused |
| `test_amend_needs_manager` | a payroll user without contract administration gets `AccessError` opening an amendment |
| `test_amendment_pay_lines` | during an amendment from 2027-01-01: the `BASE` line's amount is refused; its `date_to` 2026-12-31 is accepted, 2026-12-30 refused; a new `BASE` line from 2027-01-01 is accepted, from 2026-12-15 refused; deleting a line is refused |
| `test_approve_amendment` | `BASE` 4,500,000 → 5,000,000 from 2027-01-01: version 1 `approved`, number *01/0001/2026/HĐLĐ-TC*, `changes` one `salary` item for article 3; `l10n_vn_version_id` is version 1; no amendment open; `job_id` locked again |
| `test_approve_amendment_without_change` | an amendment with no edit is refused |
| `test_cancel_amendment` | job changed, `BASE` ended and a new line added, then cancelled: job and `date_to` back, the new line gone, version 1 deleted, the contract locked |
| `test_prints_after_annex` | the contract still prints *4.500.000* and *0001/2026/HĐLĐ-TC*; `l10n_vn_number` unchanged; the annex prints *PHỤ LỤC HỢP ĐỒNG LAO ĐỘNG*, *01/0001/2026/HĐLĐ-TC*, *Sửa đổi Điều 3*, *5.000.000*, *có hiệu lực kể từ ngày 01/01/2027*, and no *Sửa đổi Điều 2* |
| `test_annex_individual_terms_and_job` | an amendment adding individual terms and changing the job: changes *Sửa đổi Điều 2* and *Bổ sung Điều 12. Thỏa thuận khác* |
| `test_annex_needs_payroll_group` | a contract administrator without payroll groups gets `AccessError` from `_l10n_vn_annex_values()` |

**`tests/test_document_next.py`**

| Test | Asserts |
|---|---|
| `test_annexes_for_date` | two approved contracts on a parameter-based `BASE`, one on a fixed amount; the parameter rises from 2027-01-01: *Find Changes* lists the first two with `salary`; *Confirm* gives each an approved annex; the third has none |
| `test_annexes_for_date_skips_open_amendment` | a contract with an amendment open is not listed |
| `test_next_contract_after_fixed_term` | an approved contract to 2027-11-01: the wizard defaults to 2027-11-02; the new contract is draft, not approved, with `BASE` and `PROD` lines from 2027-11-02 at their amounts on 2027-11-01; the old contract's end unchanged |
| `test_next_contract_ends_open_contract` | an approved contract without end and a new start 2027-06-01: the old contract ends on 2027-05-31 |
| `test_next_contract_after_probation` | a probation contract: the defaults are the day after its end and the labour type; the new contract has no probation |

15 new tests, 68 in all.
