# Contract Documents — Design Note

v0.2 (draft for review) · Nov 20, 2026 · @Peter

How Odoo manages the labour, probation and training contracts and prints them, with their annexes. It covers the
contract's lifecycle (approve-and-lock, amendments as annexes), the data the forms need and the two modules. What
the forms say, and why, is in *Contract Forms — Research and Drafts v0.1*. Once Peter has reviewed this note,
`docs/modules/l10n_vn_hr_contract_document.md` follows, one step at a time.

**Supersedes** v0.1, kept as history. v0.2 takes in Peter's answers of 2026-11-20 and narrows the scope:

| v0.1 | v0.2 | Why |
| --- | --- | --- |
| The PDF kept at approval; *Regenerate* until signed; restricted access to stored PDFs | Nothing stored: every print is made on demand from the version's terms | The record that matters is the Odoo contract. Paper is an output: it is printed, signed and may be corrected by hand. A gap between the two is not something to control in the system (Peter) |
| Level 4: signed flag and scan | Dropped. A scan, if anyone wants one, goes in the contract's chatter | As above |
| *Approve from Paper* for existing paper contracts | Dropped | Everyone gets a new contract (Q1) |
| Clause references configured per form for annexes | The forms have fixed article numbers; the annex template knows them | Research and Drafts §5.1 |
| Payroll checks `contract_amending`, `contract_terms` | Dropped; *Annexes for a Date* lists contracts whose terms changed | Fewer moving parts |
| Variable pay printed without level (proposed) | Decided: named, "theo Quy chế trả lương", no level or amount | Peter (Q2); Circular 10 Art. 3.5.c2 |
| Department and schedule not printed (proposed) | Decided | Peter (Q3) |
| Approver to decide | Contract administrators (`hr_contract.group_hr_contract_manager`), given to the HR manager | Peter (Q6) |
| Training repayment to decide | Part of the training form, used per contract | Peter (Q5) |

**What stays from the four levels (Peter, 2026-11-20):** (1) print from the system; (2) approve-and-lock: a contract
becomes Running only through approval and its key terms are then read-only; (3) changes through an amendment with an
effective date, printed as an annex, which becomes the contract's next version. Level 4 is dropped (above).

**Guard:** payroll go-live, payday 10 December 2026, does not wait for this (§5.3).

---

## 0. Decisions proposed

| ID | Decision |
| --- | --- |
| CD-01 | **Versions hold the approved terms.** `l10n_vn.contract.version`: version 0 is the contract, versions 1, 2 … are annexes. Each keeps its number, effective date and a snapshot of the terms the form prints. Every print renders from a version: the terms from its snapshot, the parties from their records as they are today. No file is stored. (§1.2) |
| CD-02 | **Approval is the only way to Running,** behind a per-company switch, off by default. With it on, `hr.contract` refuses `state = open` for a contract without an approved version 0, whichever path asks (statusbar, kanban, cron, import). (§1.2, §1.7) |
| CD-03 | **The lock covers what the form prints:** parties, type, term, probation, job, workplace, participant type, the training terms and the printed pay lines. Department, schedule, pay group, structure and notes stay editable. (§1.3) |
| CD-04 | **An amendment opens the contract and closes it with an annex.** *Amend* creates a draft annex with an effective date and unlocks the terms; *Approve Amendment* snapshots them and locks again; *Cancel Amendment* restores the previous snapshot. (§1.4) |
| CD-05 | **An annex never changes the term** (Labor Code Art. 22.2). A change of end date, type or probation form is a new contract, made by *Next Contract*. (§1.5) |
| CD-06 | **Print modes on pay components:** a component prints as an amount (base salary, fixed allowances, the training allowance), by name with a reference to the pay regulation (productivity and performance pay), under bonuses and welfare, or not at all. Derived from the component's flags, editable. (§2.3) |
| CD-07 | **Wording in QWeb templates;** a form record per company and kind names the template and its number sequence. The generic module ships the `[G]` wording with neutral placeholders for `[C]`; the company module replaces them. (§4) |
| CD-08 | **Mandatory where used:** the data a form needs is checked at approval, which lists everything missing and stops. A draft prints with blanks and a draft mark. (§2.4) |
| CD-09 | **Payroll is untouched.** The generic module depends on `l10n_vn_payroll`; nothing in payroll depends on it. (§4) |
| CD-10 | **New contracts at go-live** are new `hr.contract` records from the go-live date, made by the go-live scripts; the old records end the day before. (§5.2) |

---

## 1. The contract's lifecycle

### 1.1 What the code does today

**Core `hr.contract`** (`odoo/addons/hr_contract/models/hr_contract.py`, read 2026-11-20):

- States `draft` *New*, `open` *Running*, `close` *Expired*, `cancel` *Cancelled* (:44-49), with `group_expand`, so
  the kanban shows every state and a card can be dragged between them.
- The form's statusbar is clickable for contract administrators (`views/hr_contract_views.xml:152-153`).
- A draft contract with `kanban_state = done` is *Incoming*; the daily cron `update_state` opens it on its start date
  (:243-246) and closes running contracts whose end has passed (:236-241). It writes through `_safe_write_for_cron`
  (:270-283), which catches `ValidationError` only, logs it and moves on.
- `write` (:331-361): `state = open` makes the contract the employee's current one; an end date in the past closes a
  running contract at once.
- The departure wizard (`wizard/hr_departure_wizard.py:23-36`) writes the departure date as the running contract's
  end, as superuser, closes it and cancels the employee's draft contracts.
- No approval, lock, numbering, version or printed contract in core 18.

**OCA `hr`** (none installed): `hr_contract_reference` numbers contracts at creation from one sequence (drafts use up
numbers; ours number at approval, per form); `hr_contract_renew` copies a contract from a new start date, but carries
pay lines dated before it, which `l10n_vn_payroll` refuses (`date_from ≥ contract.date_start`); `hr_contract_document`
lists attachments. None is used.

**Our payroll** (`docs/modules/l10n_vn_payroll.md`): pay lines are dated, and a change is a new line (Technical
Design §7). D77 freezes a line paid by an approved payslip. The workers' base salary comes from the dated `BASE` scale
by group (garment D16–D18), so raising the scale changes the base salary with no change to any contract.

So: one choke point, `hr.contract.create` and `write`, catches every path to Running; refusals are `ValidationError`,
so the cron skips a contract instead of stopping.

### 1.2 The lifecycle

```
          Approve                              (start date reached: core cron)
  New ──────────────► New, Incoming ────────────────────────────────────────► Running ── end / departure ──► Expired
   │  version 0: number,                                                      │   ▲
   │  terms snapshot                                         Amend            │   │  Approve Amendment
   │                                              (draft annex, terms open)   ▼   │  (annex: number, snapshot, locked)
   └── Cancel ──► Cancelled                                           Running, amending
                                                                              └── Cancel Amendment (snapshot restored)
```

- **Approve** (contract administrators): checks the data the form needs (§2.4) and the contract's own rules (probation
  within Art. 25, pay lines covering the start date), then in one transaction numbers version 0 from its form's
  sequence, snapshots the terms, and sets the contract Running when its start has come, otherwise *Incoming* so that
  core's cron opens it on the day. A failed approval changes nothing. *Approve* also runs on a selection from the
  contract list, for the go-live batch (§5.2); each contract that fails is listed with its reason and the others are
  approved.
- **Contracts without a form** (Casual; managers without a labour contract: a contract type whose kind is `none`) are
  approved and locked the same way, with no number and no data check beyond the contract's own.
- **The switch** `res.company.l10n_vn_contract_approval` (*Contracts become Running only through approval*), off by
  default: behaviour added to every company would otherwise run inside other modules' tests
  (`l10n_vn_payroll_account` step 1). Off, the module prints and keeps versions but refuses nothing.
- **Contracts running when the switch is turned on** stay running, unlocked and marked *Not approved* (a list filter)
  until approved.
- **Print** (payroll users with contract access, since the form shows pay): *Print* on a contract prints version 0; on
  an annex, that annex. Several contracts selected print as one PDF. Before approval, *Print Draft* prints the
  contract's current data with blanks where data is missing, no number and a *BẢN NHÁP* mark.

### 1.3 What is locked

On an approved contract with no amendment open, a write touching these fields is refused with a `ValidationError`
naming them and pointing to *Amend*:

| Field | Printed as |
| --- | --- |
| `employee_id`, `company_id` | The parties |
| `contract_type_id`, `l10n_vn_probation_form` | The form itself (a change is a new contract, §1.5) |
| `date_start`; `date_end` moved later or removed | The term |
| `trial_date_end`, `l10n_vn_probation_job` | The probation clause |
| `job_id`, `l10n_vn_work_address_id` | Article 2: work and workplace |
| `l10n_vn_participant_type_id` | The insurance article (or its absence) |
| `l10n_vn_training_kind`, `l10n_vn_commitment_months`, `l10n_vn_training_cost`, `l10n_vn_training_cost_items` | The training contract's articles 1 and 7 |
| Pay lines of printed components | Articles 3 and 4 (rules below) |

**Allowed on a locked contract:** `date_end` moved earlier or set where empty (a leaver, the departure wizard, core's
cron completing a closed contract, `hr_contract.py:248-268`); `state` to Expired or Cancelled; every other field,
including `department_id`, `resource_calendar_id`, `l10n_vn_pay_group`, `struct_id`, `kanban_state`, `notes` and the
signing date. The list is one method, `hr.contract._l10n_vn_locked_fields()`, which a company module can extend when
its form prints more.

**Pay lines on a locked contract**, by the component's print mode (§2.3), outside an amendment:

| Print mode | Allowed |
| --- | --- |
| `amount` | Nothing: no create, write or unlink |
| `reference` | New dated lines of a component the contract already has, and a `date_to` on its lines: a level review is not an amendment. A line of a component the contract does not have is refused |
| `welfare`, `none` | Everything |

D77 applies on top: a line paid by an approved payslip stays frozen in any case.

**Who is exempt:** our own code, through a context key set only by approval, amendment and cancellation. Not the
superuser: core writes contracts as superuser (the departure wizard, `_assign_open_contract`), and a superuser
exemption would let those paths change terms silently.

### 1.4 Amendments

- **Amend** (HR officers, `hr_contract.group_hr_contract_employee_manager`, with payroll access for pay changes): asks
  for the effective date and a reason, creates a draft annex version and sets `l10n_vn_amendment_id` on the contract.
  While it is set, the locked fields can be edited, under these rules, which keep the change dated and reversible:
  - existing pay lines may only receive a `date_to`; new pay lines start on or after the effective date;
  - the effective date falls after the last day of the contract's latest approved payslip: a change to a paid month
    goes through payroll's corrections (Technical Design §21);
  - `date_end`, `contract_type_id` and `l10n_vn_probation_form` stay locked (§1.5).
- **Approve Amendment** (contract administrators): computes the terms on the effective date, refuses when nothing
  printed has changed, numbers the annex, stores the snapshot, clears `l10n_vn_amendment_id`. The annex prints the new
  text of each article that changed (Research and Drafts §6.5).
- **Cancel Amendment:** restores the locked fields from the previous snapshot, deletes the pay lines created during
  the amendment, clears the `date_to` values it set, and cancels the draft version.
- **Payroll meanwhile** reads the pay lines as they are, dated. An amendment is meant to be opened and approved the
  same day; the run's own review and approval remain the control on pay.
- **Annexes for a Date** (contract administrators): for changes that touch no contract, such as a new version of the
  `BASE` scale. It takes a date and a selection of running contracts, lists those whose printed terms on that date
  differ from their current version, and on confirmation creates and approves an annex for each; the annexes print
  as one PDF. It is also the way to see which contracts have drifted from their approved terms.

Labor Code Art. 33 (3 working days' notice of a requested change) is the HR process; the module does not enforce it.

### 1.5 Next contract

A renewal, probation to labour, training to labour (Art. 61.6), or fixed-term to indefinite is a new contract, never
an annex (Art. 22.2). *Next Contract* (HR officers), on an approved contract:

- asks for the start date (default: the day after its end, or after `trial_date_end` for a probation contract), the
  contract type and the end date;
- copies the contract with the pay lines in force on the new start date, re-dated from it; the participant type
  comes from the new type (payroll D103); pay group, job, workplace and schedule are kept;
- ends the current contract the day before when it has no end or a later one (allowed on a locked contract);
- opens the new contract as *New*, to be checked and approved.

Payroll's `contract_term` check (D107) still warns on a third fixed-term labour contract in a row.

### 1.6 Ending and cancelling

Ending works as today: a shorter `date_end`, or the departure wizard. Cancelling a contract that never took effect
(Pay Policy §14.3) is allowed for contract administrators in any state; its versions stay and its numbers are not
reused. Termination letters and the probation result notice (Art. 27.1) are possible later forms, not in this scope.

### 1.7 What is overridden

All through `_inherit`; nothing in core or OCA is edited.

| Override | Adds | Why |
| --- | --- | --- |
| `hr.contract.create` | With the switch on, refuses `state = open` unless our context key is set | Creation in Running (imports, scripts) would bypass approval |
| `hr.contract.write` | With the switch on, refuses `state = open` without an approved version 0; on an approved contract, refuses changes to locked fields unless an amendment is open or our key is set; `ValidationError` | The one choke point for statusbar, kanban, cron and forms |
| `l10n_vn.payroll.contract.line` `create`, `write`, `unlink` | The rules of §1.3 and §1.4, after D77 | Pay terms live on their own model |
| `hr.contract.copy` | Versions and approval fields `copy=False` | A duplicate starts unapproved |
| Contract form | Buttons *Approve*, *Amend*, *Approve Amendment*, *Cancel Amendment*, *Next Contract*, *Print*, *Print Draft*; a *Versions* tab; the statusbar not clickable while the switch is on | Users should not click into an error |

Not overridden: core's cron, the departure wizard, `_check_current_contract`, payroll's lock.

---

## 2. Forms and terms

### 2.1 Which form

`hr.contract.type.l10n_vn_document_kind`: `labour`, `probation`, `training` or `none` (empty counts as `none`). The
garment types (garment D20): `VN_LABOUR` → `labour` (with the probation clause when `l10n_vn_probation_form = clause`),
`VN_PROBATION` → `probation`, `VN_TRAINING` → `training`, `VN_CASUAL` → `none`. Annexes use the company's `annex` form
for whichever kind the contract has.

### 2.2 The terms snapshot

A version's snapshot is what its form prints, grouped by the article it belongs to, in values ready to render (names,
amounts, dates), not record ids:

| Group | Contents | Article (labour form) |
| --- | --- | --- |
| `term` | Type, start, end, months; probation length, end, rate, job category | 1 |
| `work` | Job title, workplace address | 2 |
| `salary` | Per printed component: code, name, mode, amount | 3 |
| `bonus` | Bonus and welfare components: name, amount or reference | 4 |
| `insurance` | Whether the participant type has funds | 8 |
| `training` | Kind, commitment months, cost and its items (training form) | 1, 7 |

Comparing two snapshots group by group gives an annex its content and *Annexes for a Date* its list. The parties
(names, addresses, ID) are not in the snapshot: they print as they are today, so a corrected address reprints
correctly without an annex.

Cancelling an amendment needs the raw values too (ids of job, workplace, participant type; pay line ids and dates); the
snapshot keeps them beside the rendered values.

### 2.3 Print modes on pay components

`l10n_vn.payroll.component.l10n_vn_contract_print`, a stored computed field, editable:

| Mode | Default when | Printed |
| --- | --- | --- |
| `amount` | `in_si_base`, or an earning not variable and not a bonus or welfare (`TRAIN`) | Name and amount, in article 3: the base salary under 3.1, allowances under 3.2, other fixed supplements under 3.3 |
| `reference` | `variable`, or nature `variable_salary` (`PROD`, `PERF`) | Name and "theo Quy chế trả lương của Công ty", in 3.3 |
| `welfare` | Nature `bonus` or `welfare` (efficiency, one-time and annual bonuses; a phone allowance) | Article 4: bonuses by reference to the bonus regulation, welfare items by amount or reference |
| `none` | Deductions, employer contributions, totals, OT | Nothing |

Lines are read on the version's effective date: the contract's start for version 0, the effective date for an annex.
Amounts come from the pay line, the scale cell or the parameter, as payroll reads them (`_l10n_vn_amount_on`). Where
probation applies, the probation amount is the job's amount × `vn.policy.probation_rate` on that date.

### 2.4 What approval requires

Approval lists everything missing and stops (like payroll's `missing_ids`, D106):

| For | Required |
| --- | --- |
| Every form | Company: legal representative and title, `vat`, street, province. Employee: name, birthday, gender, `l10n_vn_personal_id` (12 digits), its issue date and place, permanent address. Contract: job, workplace, a form for the company and kind, pay lines in force on the start date with at least one `amount` line |
| Probation (clause or contract) | `trial_date_end` (clause) or `date_end` (contract); `l10n_vn_probation_job`; the length within `vn.probation.max_days` for that job; the rate at least `vn.probation.min_rate` |
| Fixed-term labour contract | `date_end` within 36 months of `date_start` |
| Training contract | `date_end` within 3 months of `date_start`; when `l10n_vn_commitment_months` is set, `l10n_vn_training_cost` too |
| Kind `none` | The contract's own rules only |

Approving an amendment repeats the check for the groups it changes. The issue date and place are not required by
Circular 10, but the company prints them (Research and Drafts §2), so they are checked with the rest.

---

## 3. The data

### 3.1 What exists and what is missing

From Research and Drafts §2 against the models and the test copy (287 running contracts in the garment company,
2026-11-20):

| Needed | In Odoo | On the test copy |
| --- | --- | --- |
| Employer name, enterprise code, address, phone, e-mail | `res.company` and its partner | Present, except e-mail to check |
| Signer and title | **Missing** | — |
| Employee name, birthday, sex | `name`, `birthday`, `gender` (core) | Birthday and sex on 0 of 287 |
| Residence | **Permanent address missing**; current address in core's `private_street` … | Private address on 0 of 287 |
| Phone, e-mail (if any) | `private_phone`, `private_email` (core) | — |
| ID number | `l10n_vn_personal_id` (payroll D70) | 3 of 287 (test values) |
| ID issue date and place | **Missing** | — |
| Job | `job_id` | 286 of 287 |
| Workplace | **Missing on the contract**; the employee's work address (`address_id`) | Every employee: the company |
| Probation, pay, payment method, insurance | Payroll fields, pay lines, participant type | Set by the go-live scripts |
| Training kind, commitment, cost | **Missing** | — |
| Signing date | **Missing** | — |

### 3.2 New fields

| Model | Field | Type | Notes |
| --- | --- | --- | --- |
| `res.company` | `l10n_vn_legal_rep_id` | Many2one `res.partner` | *Legal Representative*: the director (Peter, 2026-11-20) |
| | `l10n_vn_legal_rep_title` | Char | *Title*: *Giám đốc* |
| | `l10n_vn_contract_code` | Char | Short code in contract numbers, e.g. `QP` |
| | `l10n_vn_contract_approval` | Boolean | The switch (§1.2), off by default |
| `hr.employee` | `l10n_vn_id_issue_date` | Date | *ID Issue Date*, after `l10n_vn_personal_id`, `groups="hr.group_hr_user"`, tracked |
| | `l10n_vn_id_issue_place` | Char | *ID Issue Place*, as on the card |
| | `l10n_vn_permanent_address` | Char | *Permanent Address* (nơi thường trú), one line as on the card or the residence record |
| `hr.contract` | `l10n_vn_work_address_id` | Many2one `res.partner` | *Workplace*, default the employee's `address_id` |
| | `l10n_vn_sign_date` | Date | *Signing Date*, optional; empty prints "ngày … tháng … năm …" to fill in by hand. Not locked |
| | `l10n_vn_training_kind` | Selection | `practice` *Tập nghề* / `apprenticeship` *Học nghề*, default `practice`; training contracts |
| | `l10n_vn_commitment_months` | Integer | Training: months to work after the labour contract; empty = no repayment article |
| | `l10n_vn_training_cost`, `l10n_vn_training_cost_items` | Monetary, Text | Training: the cost and what it consists of |
| | `l10n_vn_version_ids`, `l10n_vn_version_id`, `l10n_vn_amendment_id`, `l10n_vn_approved` | | §1.2–§1.4, `copy=False` |
| `hr.contract.type` | `l10n_vn_document_kind` | Selection | §2.1 |
| `l10n_vn.payroll.component` | `l10n_vn_contract_print` | Selection | §2.3 |

No field is `required=True`: that would refuse every save of the 287 existing employees and every import until each
is complete. Approval asks for the data when it is needed (§2.4).

### 3.3 `l10n_vn.contract.version`

| Field | Type | Notes |
| --- | --- | --- |
| `contract_id` | Many2one `hr.contract` | required, cascade |
| `company_id`, `employee_id` | related, stored | |
| `sequence` | Integer | 0 for the contract, 1, 2 … for annexes |
| `kind` | Selection | `contract` / `annex` |
| `number` | Char | Version 0: from the form's sequence, `0012/2026/HĐLĐ-QP`; annex: `{nn}/{contract number}` |
| `effective_date` | Date | Version 0: `date_start` |
| `state` | Selection | `draft` (an amendment in progress) / `approved` / `cancelled` |
| `reason` | Char | Annexes |
| `terms` | Json | The snapshot (§2.2) |
| `approved_by`, `approved_at` | | |

Access: read for contract administrators and payroll users, since the terms hold pay; written only through the
contract's actions.

### 3.4 Go-live data

The HR entry already planned for go-live (CCCD and bank accounts, Technical Design §29 step 1c) grows by the
birthday, sex, ID issue date and place and permanent address of everyone who gets a contract: 287 people on the test
copy, all from the ID card. One spreadsheet through Odoo's standard employee import is the quickest route. The company
needs its legal representative, title and contract code set once.

---

## 4. The modules

### 4.1 `l10n_vn_hr_contract_document`

- **Depends:** `l10n_vn_payroll` (pay lines, components, participant types, `l10n_vn_personal_id`,
  `l10n_vn_probation_job`, the parameters), which brings `hr_contract`. Python `num2words` for amounts in words,
  already in the image for `l10n_vn_voucher`; a few lines of its own rather than a dependency on `l10n_vn_voucher`,
  which brings accounting.
- **Holds:** the fields of §3.2; `l10n_vn.contract.version`; `l10n_vn.contract.form` (company, kind, name, QWeb
  template, number sequence); the lifecycle of §1 and its switch; the snapshot and comparison; the report with the
  common header and closing, the salary and bonus blocks, and the five forms with the `[G]` wording of Research and
  Drafts §6 and neutral placeholders for `[C]`; *Annexes for a Date*; *Next Contract*.
- **Groups:** none new. HR officers (`hr_contract.group_hr_contract_employee_manager`) prepare, amend and use *Next
  Contract*; contract administrators (`hr_contract.group_hr_contract_manager`, the HR manager) approve, cancel and run
  *Annexes for a Date* (Peter, Q6). Pay lines need payroll groups, as today.
- **Nothing per company at install:** form records and the switch are set in *Settings* or by a company module's
  loader.
- **Odoo 19** replaces `hr.contract` with versions on the employee (`hr.version`); the version model maps onto it at
  that migration.

### 4.2 `l10n_vn_hr_contract_document_garment`

- **Depends:** `l10n_vn_hr_contract_document`, `l10n_vn_payroll_garment`.
- **Holds:** the garment company's templates, inheriting the generic forms and replacing the `[C]` clauses with the
  wording HR has checked; a loader, started from *Settings* by a contract administrator like the payroll loader
  (garment D1–D8), which for one company creates the five form records with their sequences, sets
  `l10n_vn_document_kind` on the four `VN_*` contract types and the print mode on garment components where the default
  differs, only where empty. It never turns the approval switch on: that is HR's act at go-live.
- QWeb templates are global, but a company prints only through its own form records, so the trading company is not
  affected.

### 4.3 Build steps

| # | Module | Scope |
| --- | --- | --- |
| 1 | generic | Fields of §3.2 except versions; print modes; form records; the report and the five generic forms; *Print Draft* |
| 1 | garment | The checked wording; the loader |
| 2 | generic | Versions and snapshots; *Approve*, alone and on a selection; numbering; *Print* from a version; the switch; the write guards and pay-line rules (§1.3, §1.7) |
| 3 | generic | Amendments and the annex (§1.4); *Annexes for a Date*; *Next Contract* (§1.5) |

Tests as in payroll: `TransactionCase`, `post_install` (fixtures create employees and contacts), no `HttpCase`. The
report rendered as HTML and checked for its values; each path to Running tested against the switch (form write,
statusbar value, `update_state`, create, the departure wizard) with a positive control; pay-line rules on a locked,
an amending and an unlocked contract; an amendment approved and one cancelled, the contract back to its snapshot.

---

## 5. Go-live

### 5.1 Order

Payroll does not wait. Technical Design §29 stays: go-live scripts → October rehearsal on a fresh `prod_copy` →
November on production, payday 10 December. The documents fit beside it:

1. This note reviewed; generic step 1 spec and code. In parallel, HR checks the `[C]` wording and collects the ID card
   data (§3.4).
2. Go-live scripts on production (§5.2), with the contract data the forms print.
3. Generic steps 1–2 and garment step 1 installed; the November contracts approved in one batch and printed in one
   PDF; signed. The switch is turned on afterwards.
4. Step 3 after go-live; the first real annexes come with the next base-salary change (Pay Policy OPEN-24).

**Fallback:** if step 1 is not ready when the contracts must be signed, HR prints them from Word using Research and
Drafts §6. The Odoo contracts still exist and are approved once step 2 is installed; approval gives them their numbers,
which HR writes on the paper copies.

### 5.2 New contracts for everyone (Q1)

Every employee signs a new contract (Peter, 2026-11-20). In Odoo the clean form of that is a **new `hr.contract` per
employee from the go-live date**, with the new type, participant type, pay group and pay lines, while today's record
ends the day before. The Odoo contract then is the legal contract: version 0 prints exactly it, its start date is the
paper's, and its history begins clean. Payroll reads both without change: a month's main contract is the latest one
overlapping the month (PTD-08), so October reads the old record and November the new.

This changes the planned go-live scripts, which were to convert the existing records in place (Technical Design §29
step 1c, step 4): they create the new contracts instead, with the pay lines from the go-live date, and the October
rehearsal keeps the old records as they are. The scripts are on hold for this design anyway.

The start date of the new contracts is Peter's and HR's to set: **1 November 2026 is recommended**, the first month
paid on the new scheme and the first payroll cycle. Seniority from before it (annual leave, severance) is a question
for the lawyer's review, not for the module.

### 5.3 Proposals to other documents

| Document | Proposal |
| --- | --- |
| Pay Policy §3.6 | The contract names productivity pay and refers to the pay regulation; no level, no amount (Peter, Q2). For v0.8 |
| Pay Policy §14 | Every employee signs a new contract at go-live, printed from Odoo (Q1). For v0.8 |
| Technical Design §29 | Steps 1c and 4: new contracts from the go-live date instead of converting the existing ones (§5.2); the contract documents in the go-live order (§5.1) |

---

## 6. Settled points (Peter, 2026-11-20)

| # | Point | Decision |
| --- | --- | --- |
| 1 | The new contracts' start date | 1 November 2026 (§5.2) |
| 2 | Word output for editing before signing | Not now: a PDF, corrected by hand where needed |
| 3 | A signer other than the director (Art. 18.3) | Not now: the director signs |
| 4 | Employees under 18 (Art. 18.4) | Outside the module: the company does not plan to hire anyone under 18, and handles it separately if it ever does |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-11-20 | First draft: lifecycle, forms with draft wording, data, modules, build steps, questions. |
| 0.2 | 2026-11-20 | §6 settled by Peter the same day: start date 1 Nov 2026, no Word output, the director signs, under-18s outside the module. The forms moved to *Contract Forms — Research and Drafts v0.1*. Peter's answers (Q1–Q6) taken in. Stored PDFs, regeneration, the signed flag and scan, *Approve from Paper*, configured clause references and the two payroll checks dropped: the system keeps the contract's integrity, and paper is printed from it. Added: batch approval and printing, the training contract's fields, new contracts at go-live as new records (§5.2), proposals to other documents (§5.3). |
