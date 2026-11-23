# Contract Documents — Design Note

v0.1 (draft for review) · Nov 20, 2026 · @Peter

The legal labour, probation and training contracts, and their annexes, printed from the Odoo contract. It
covers the contract's lifecycle in Odoo (approve-and-lock, amendments as annexes), the forms and their draft
Vietnamese wording, the data the forms need, and the two modules. No module spec exists yet: once Peter has
reviewed this note, `docs/modules/l10n_vn_hr_contract_document.md` follows, one step at a time.

**Based on:** Peter's proposal and answers of 2026-11-20, including his confirmation of the four levels below;
Pay Policy v0.7 §11 and §14; Payroll Technical Design v0.7 §7, §8, §21 and §29; `docs/modules/l10n_vn_payroll.md`
(pay lines, D77) and `docs/modules/l10n_vn_payroll_garment.md` (`BASE`, `PROD`, `TRAIN`, contract types D20);
Regulation Reference v0.4 *Contract types*; the code the instance runs, read 2026-11-20 (references are
`path:line` from `Odoo-Build/`); the test copy's data, read 2026-11-20.

**The four levels (Peter, 2026-11-20).** Ordered by value: (1) print from the system; (2) approve-and-lock: a
contract becomes Running only through approval, its key terms are then read-only, and the PDF is kept;
(3) changes through an amendment with an effective date, printed as an annex, which becomes the contract's next
version; (4) a signed flag and the signed scan, optional. Levels 1–3 are built; 4 is a small later step.

**Guard (Peter, 2026-11-20):** payroll go-live, payday 10 December 2026, does not wait for this. If the documents
are late, November's contracts are written in Word (§4.4).

This is design research, not legal advice. The wording in §2 is a draft for HR to check and for a labour lawyer
to review once before first use; the company owns it.

---

## 0. Decisions proposed

| ID | Decision |
| --- | --- |
| CD-01 | **A version per approved document.** A new model, `l10n_vn.contract.version`, holds each approved state of a contract: version 0 is the contract, versions 1, 2 … are annexes. Each keeps its number, effective date, a snapshot of the printed terms, the PDF made at approval and, later, the signed scan. (§1.2) |
| CD-02 | **Approval is the only way to Running,** behind a per-company switch that is off by default. With it on, `hr.contract` refuses `state = open` for a contract without an approved version 0. Core's statusbar, kanban drag, cron and imports all meet the same refusal. (§1.2, §1.8) |
| CD-03 | **The lock covers what the form prints,** not the whole contract: the parties, type, dates, probation, job, workplace, signing date, participant type and the printed pay lines. Department, working schedule, pay group, structure and notes stay editable, because the forms do not print them. (§1.3) |
| CD-04 | **An amendment opens the contract for editing and closes it with an annex.** *Amend* creates a draft annex version with an effective date and unlocks the key terms; *Approve Amendment* snapshots the terms, prints the annex from the difference and locks again; *Cancel Amendment* restores the snapshot. No mirror of the contract's fields on the amendment. (§1.4) |
| CD-05 | **An annex never changes the term** (Labor Code Art. 22.2). A change of end date, contract type or probation form is a new contract: *Next Contract* copies the contract with its pay lines in force, re-dated. OCA's `hr_contract_renew` is not used. (§1.5) |
| CD-06 | **Variable pay is printed by reference, without its level.** A component prints with its amount when it is in the SI base or a fixed allowance, and as *theo Quy chế trả lương* when it is variable or a bonus, from a print mode on the component derived from its flags. Levels and grades are not printed, so a level review needs no annex. (§2.3) |
| CD-07 | **Wording lives in QWeb templates in the company module;** a form record per company and kind names the template and its number sequence. Old contracts are reproduced from their kept PDFs, so templates need no versioning in the database. HR changes wording through a module change, reviewed like code. (§4.1) |
| CD-08 | **New data on the company and the employee, mandatory where used:** the legal representative and their title on the company; the ID card's issue date and place and the permanent address on the employee. Approval and printing list what is missing and stop; the forms stay unchanged. (§3) |
| CD-09 | **PDFs are attached to the version, not the contract,** and the version is readable only by contract administrators and payroll users, so a salary on paper is not exposed to every contract reader. (§1.7) |
| CD-10 | **Payroll is untouched.** The generic module depends on `l10n_vn_payroll`; nothing in payroll depends on it. Its later checks join payroll's catalogue from its own data. (§4) |

---

## 1. The contract's lifecycle

### 1.1 What the code does today

**Core `hr.contract`** (`odoo/addons/hr_contract/models/hr_contract.py`):

- States `draft` *New*, `open` *Running*, `close` *Expired*, `cancel` *Cancelled* (:44-49), with `group_expand`, so
  the kanban shows every state as a column and a contract can be dragged between them.
- The form's statusbar is **clickable for contract administrators** (`hr_contract.group_hr_contract_manager`)
  (`views/hr_contract_views.xml:152-153`): one click puts a contract in Running.
- `kanban_state` `done` on a draft contract means *Incoming*; the daily cron `update_state` opens every draft
  contract in `done` whose start has come (:243-246) and closes running contracts whose end date has passed (:236-241).
  The cron writes through `_safe_write_for_cron` (:270-283), which **catches `ValidationError` only**, logs it and goes on.
- `write` (:331-361): setting `state = open` makes the contract the employee's current one; writing an end date in
  the past closes a running contract at once (:351-354, unless `close_contract=False` in the context).
- `_check_current_contract` (:117-155): no overlapping contracts outside draft and cancelled.
- The departure wizard (`wizard/hr_departure_wizard.py:23-36`) writes, as superuser, the departure date as the
  running contract's end date, closes it and cancels the employee's draft contracts.
- There is no approval, no lock, no numbering, no version and no printed contract in core 18.

**OCA `hr`** (`oca/hr/`), none installed on the instance:

| Module | What it does | Use here |
| --- | --- | --- |
| `hr_contract_reference` | `name` read-only, numbered from one sequence `contract.ref` at creation | Not used: numbers at creation (drafts use up numbers) and one sequence for every kind; ours number at approval, per form |
| `hr_contract_renew` | A wizard that copies the contract from a new start date and ends the old one the day before | Not used: the copy carries pay lines dated before the new start, which `l10n_vn_payroll`'s line check refuses (`date_from ≥ contract.date_start`), and knows nothing of versions; *Next Contract* replaces it (§1.5) |
| `hr_contract_document` | A *Documents* smart button listing the contract's attachments | Not needed: the files belong to the versions (§1.7) |

**Our payroll** (`docs/modules/l10n_vn_payroll.md`): pay lines are dated records on the contract; a change is a new
line (Technical Design §7). D77 already freezes a pay line used by an approved payslip: its component, amount,
scale key, `in_cell`, contract and `date_from` cannot change, and its `date_to` cannot move before the last day it
was paid. `wage` follows the lines whose component `sets_wage` (D5). The base salary for workers comes from the
dated `BASE` scale by group, so a raise of the scale changes the amount with **no change to the contract**
(garment D16–D18).

What this means: the lock needs one choke point, `hr.contract.write` and `create`, because every path to Running
(statusbar, kanban, cron, import, the departure wizard's close) goes through them; and refusals must be
`ValidationError`, so the cron skips the contract instead of stopping.

### 1.2 The lifecycle proposed

```
            Approve                         (start reached: core cron)
  New ──────────────────► New + Incoming ──────────────────────────► Running ─── end date / departure ──► Expired
   │   version 0 approved,                                            │  ▲
   │   number, PDF kept                                Amend          │  │ Approve Amendment
   │                                       (draft annex, terms open)  ▼  │ (annex approved, PDF kept, locked)
   │                                                               Running, amending
   └── Cancel ──► Cancelled                                           │
                                                                      └── Cancel Amendment (snapshot restored)
```

- **Approve** (`group_hr_contract_manager`): checks the data the form needs (§3.3) and the contract's own rules
  (probation length, pay lines covering the start date), then, in one transaction: numbers version 0 from its
  form's sequence, snapshots the printed terms, renders the PDF and attaches it to the version, and sets the
  contract Running when its start has come, or *Incoming* (`kanban_state = done`) when it is in the future, so core's
  cron opens it on the day. An approval that fails changes nothing.
- **Contracts without a document** (Casual, managers without a labour contract: a contract type whose kind is
  *none*) are approved the same way and locked the same way; no number, no PDF, no data check beyond the contract's.
- **The switch** `res.company.l10n_vn_contract_approval` (*Contracts become Running only through approval*), off by
  default (the lesson of `l10n_vn_payroll_account` step 1: behaviour added to every company runs inside other modules'
  tests). Off, the module prints and keeps versions but refuses nothing.
- **Contracts already running when the switch is turned on** stay running and unlocked, marked *Not approved*
  (filter on the contract list). Approving one records version 0 and locks it from then on (§1.10).
- **Preparer and approver may be the same person.** The HR team is small; a payroll run's segregation (PTD-12) is
  not repeated here. The approver and time are on the version and in the chatter.

### 1.3 What is locked

On an approved contract (any version approved, no amendment open), a write touching these is refused with a
`ValidationError` naming the fields and pointing to *Amend*:

| Field | Why |
| --- | --- |
| `employee_id`, `company_id` | The parties |
| `contract_type_id`, `l10n_vn_probation_form` | They choose the form; a change is a new contract (§1.5) |
| `date_start`; `date_end` made later or removed | The term (Art. 21.1.d); an annex cannot change it (Art. 22.2) |
| `trial_date_end`, `l10n_vn_probation_job` | The probation clause |
| `job_id`, `l10n_vn_work_address_id` (new, §3.2) | Work and workplace (Art. 21.1.c) |
| `l10n_vn_sign_date` (new) | The date on the paper |
| `l10n_vn_participant_type_id` | It decides the insurance clause |
| Pay lines of printed components | The salary clause (Art. 21.1.đ); rules below |

**Allowed on a locked contract:** `date_end` set earlier, or set where empty (ending the contract: the departure
wizard, a leaver, core's cron filling the end of a closed contract, `hr_contract.py:248-268`); `state` to Expired or
Cancelled; `kanban_state`, `department_id`, `resource_calendar_id`, `l10n_vn_pay_group`, `struct_id`,
`hr_responsible_id`, `notes`, and every field the form does not print. The set is one method,
`hr.contract._l10n_vn_locked_fields()`, so a company module can extend it when its form prints more.

**Department and working schedule are not printed** (CD-03). Moves between departments (cost groups) and
calendar changes happen often; printing them would make each an annex. The form states the department nowhere
and the hours by reference to the work rules plus the company's weekly norm (§2.4).

**Pay lines on a locked contract** (no amendment open), by the component's print mode (§2.3):

| Print mode | Outside an amendment |
| --- | --- |
| `amount` (base salary, fixed allowances) | No create, write or unlink |
| `reference` (productivity, performance, other variable pay) | New dated lines of a component the contract already has, and a `date_to` on its lines, are allowed: a level review is not an amendment. A line of a component the contract does not have yet is refused |
| `none` | Free |

D77 keeps applying on top: a line paid in an approved payslip stays frozen whatever the contract's state.

**Who is exempt:** our own code through a context key set by approval, amendment and cancellation only. Not the
superuser: core and OCA write contracts as superuser (the departure wizard, `_assign_open_contract`), and the
superuser exemption of payroll's lock (D76) would let those paths change key terms silently.

### 1.4 Amendments

- **Amend** (HR officers, `hr_contract.group_hr_contract_employee_manager`): asks for the effective date and the
  reason, creates a draft annex version and sets `l10n_vn_amendment_id` on the contract; while it is set, the key
  terms are editable.
- **Rules during an amendment**, so that the change is well-defined and can be undone:
  - existing pay lines may only receive a `date_to`; new pay lines start on or after the effective date
    (a change is a new line, Technical Design §7);
  - the effective date is after the last day of the latest approved payslip of the contract: a change in a paid
    month goes through payroll's corrections (Technical Design §21), not an annex;
  - `date_end`, `contract_type_id` and `l10n_vn_probation_form` stay locked: *Next Contract* instead (§1.5).
- **Approve Amendment** (contract administrators): computes the printed terms on the effective date, refuses an
  empty difference, numbers the annex, renders it from the difference against the previous version (§2.8), keeps
  the PDF, clears `l10n_vn_amendment_id`. The contract is locked again.
- **Cancel Amendment:** restores the locked fields from the previous version's snapshot, deletes the pay lines
  created during the amendment and clears the `date_to` it set; the draft version is cancelled.
- **Payroll during an amendment:** payroll keeps reading the pay lines as they are, dated. A run calculated while an
  amendment is open would use its new lines from the effective date; a later check `contract_amending` (§4.3, step 4)
  lists such payslips for the reviewer. Approving payroll is still the run's approval.
- **Changes without a contract edit.** A raise of the `BASE` scale changes the printed base salary on its date
  with no write to any contract. *Annexes for a Date* (contract administrators) takes a date and a selection of
  running contracts, computes each one's printed terms on that date, and for each whose terms differ from its
  current version creates, approves and prints an annex in one go: the 4,500,000 base salary rise of a whole group
  becomes one action and a stack of PDFs (merged into one file for printing).
- **Labor Code Art. 33:** the side asking for a change gives at least 3 working days' notice. The module does not
  enforce it; the effective date the user enters is the agreed one.

### 1.5 Next contract, renewal, probation to labour

A fixed-term renewal, the move from a probation contract to a labour contract, from a training contract to a
labour contract (Art. 61.6), or from fixed-term to indefinite is a **new contract**, never an annex (Art. 22.2).
*Next Contract* (HR officers) on a running or expired approved contract:

- asks for the start date (default: the day after the current end, or after `trial_date_end` for a probation
  contract), the contract type and the end date;
- copies the contract with its pay lines **in force on the new start date**, re-dated from it (the copy that
  `hr_contract_renew` gets wrong), the participant type from the new type (payroll's D103), pay group, job and
  workplace;
- sets the current contract's end to the day before when it has none or a later one (allowed on a locked
  contract, §1.3);
- opens the new contract as *New*, to be checked and approved like any other.

Payroll's `contract_term` check (D107) still warns on a third fixed-term labour contract in a row.

### 1.6 Ending and cancelling

- **Ending:** the departure wizard and a shortened `date_end` work as today (§1.3). Termination decisions and the
  settlement letter are not part of v1.
- **Cancelling** a contract that never took effect (Pay Policy §14.3): allowed in any state for contract
  administrators; its versions stay as history and its numbers are not reused.
- **Probation result** (Art. 27.1): the employer must notify the result. A printed notice is a natural next form;
  not in v1.

### 1.7 Documents, signing and access

- **The PDF made at approval** is attached to the version (`res_model = l10n_vn.contract.version`). Its file name is
  the number and the employee: `HDLD 0012-2026 Nguyen Van A.pdf`.
- **Reprint before signing.** A personal detail found wrong on paper (an address, a date of birth) is corrected on
  the employee and *Regenerate* re-renders the same version with the same number and terms, while the version is
  not marked signed. Earlier files stay attached. Terms cannot change this way.
- **Signed** (level 4, optional): on the version, *Signed on* (date) and the scan (a PDF or image). A signed version
  cannot be regenerated. Nothing requires it; a later report lists approved versions not signed after N days.
- **Access** (CD-09): an attachment is readable by whoever can read its record. Versions are readable by contract
  administrators and payroll users (`payroll.group_payroll_user`), not by every contract reader, consistent with
  payroll's FR-54 (pay data only to payroll groups). Approval reads pay lines as superuser after the group check, as
  payroll's checks do (D14). The PDF is not posted to the contract's chatter.
- **Language:** the documents are Vietnamese only; a foreign employee's bilingual form is not in v1.

### 1.8 What is overridden

All by `_inherit` in our module; nothing in core or OCA is edited.

| Override | What it adds | Why it is needed |
| --- | --- | --- |
| `hr.contract.create` | With the switch on, refuses `state = open` without approval (imports, scripts), unless our context key | Creation in Running would bypass approval |
| `hr.contract.write` | With the switch on, refuses `state = open` without an approved version 0; on an approved contract, refuses changes to locked fields (§1.3) unless an amendment is open or our context key is set; all as `ValidationError` | The single choke point for statusbar, kanban, cron and forms; `ValidationError` so the cron skips (`hr_contract.py:270-283`) |
| `l10n_vn.payroll.contract.line.create/write/unlink` | The pay-line rules of §1.3 and §1.4, after D77's | Pay terms are on a separate model |
| `hr.contract.copy` | Versions, approval and amendment fields `copy=False`; *Next Contract* is the supported copy | A duplicated contract must start unapproved |
| Contract form view | Header buttons *Approve*, *Amend*, *Approve Amendment*, *Cancel Amendment*, *Next Contract*, *Print Draft*; a *Versions* tab; the statusbar made non-clickable while the switch is on | The write guard alone would let users click into an error |

Not overridden: core's cron, the departure wizard, `_check_current_contract`, payroll's lock.

### 1.9 Existing contracts at go-live

On the test copy (2026-11-20) the garment company has 287 running contracts (types Employee 41, Temporary 224,
Seasonal 22), none with a probation date. The go-live scripts move them to the new types and give them pay lines
(Technical Design §29 step 1c). For the documents, two routes, by what the employee already signed:

- **A new contract** (version 0 printed from Odoo): for everyone whose existing paper contract is with another
  legal entity or no longer matches the type (Temporary and Seasonal becoming Labour, Training or Casual).
- **Register the paper contract, then print an annex:** *Approve from Paper* records version 0 with the paper's
  number, signing date and optional scan, without printing; an annex for the new pay scheme (Pay Policy §3.6) then
  prints against it. For employees whose existing contract stays valid.

Which applies is for Peter and HR (§5, Q1): the company became independent on 24 Oct 2026, and whether today's
paper contracts are with the garment company as it is now registered decides it.

---

## 2. The forms

### 2.1 Legal basis

| Text | What it requires | Checked |
| --- | --- | --- |
| Labor Code 2019 Art. 14 | Written, two copies, one each; electronic form allowed; oral only under 1 month (with exceptions) | Read 2026-11-20 |
| Art. 20 | Indefinite, or fixed-term up to 36 months; after expiry, 30 days to sign a new one; one more fixed-term contract, then indefinite | Read |
| Art. 21.1 | Contents a–k: employer's name and address and the signer's name and title; employee's name, date of birth, sex, residence, ID number; work and workplace; term; salary for the job, payment method and date, allowances and other supplements; raises; working and rest time; protective equipment; SI, HI, UI; training. 21.2: an optional written agreement on trade secrets | Read |
| Art. 22 | The annex is part of the contract; it may detail or amend clauses but **not the term**; an amending annex states the clauses changed and the date it takes effect | Read |
| Art. 24 | Probation in the labour contract or in a separate probation contract; a probation contract contains the period and items a, b, c, đ, g, h of Art. 21.1 (no raises, SI or training); no probation under 1 month | Read |
| Art. 25 | Once per job; at most 180 days (enterprise managers), 60 days (college and above), 30 days (intermediate, technical workers, clerical staff), 6 working days (other work) | Read |
| Art. 26 | Probation pay at least 85% of the job's salary | Read |
| Art. 27 | Result notified at the end; passed: the labour contract continues, or one is signed after a probation contract; during probation either side may cancel without notice or compensation | Read |
| Art. 33 | A change requested with at least 3 working days' notice; made by an annex or a new contract | Read |
| Art. 61 | Apprenticeship (học nghề) and practice (tập nghề, at most 3 months) to work for the employer; age 14+ (18+ for listed heavy or hazardous work); pay as agreed when the learner works; a labour contract at the end when the conditions are met. **61.3 amended from 1 Jan 2026** by the Vocational Education Law 2025 (124/2025/QH15) Art. 43.1.b to "the employer may not charge tuition"; the earlier text also required a training contract under the vocational education law | Art. 61 read in its 2019 text; the amendment read on a third-party copy of Law 124/2025 Art. 43, **to confirm on the official text** |
| Art. 62 | Training of an employee at the employer's cost: trade, place, duration and pay during training, commitment period, cost and repayment, duties of each side; cost defined | Read |
| Circular 10/2020/TT-BLĐTBXH Art. 3 | The detail of each item of Art. 21.1 (employer's details and phone; the signer per Art. 18; residence and ID; workplaces; term in months; salary by the company's scale, time-based salary for piece-rate workers; allowances and supplements with and without fixed amounts; welfare items as separate content; payment method and period; raises; hours; equipment; insurance; training) | **Not read**: no source could be fetched. Written from memory; HR or the lawyer checks it against the official text. No repeal found as of 2026-11-20 |
| Decree 145/2020 Art. 18 | The employer's signer is the legal representative or a person authorised in writing | **Not read**, from memory |

Sources read: hethongphapluat.com, *Bộ luật Lao động 2019* Art. 14, 20–22, 24–27, 33, 61, 62, and *Luật Giáo dục nghề
nghiệp 2025* Art. 41, 43. thuvienphapluat.vn refused automated access.

### 2.2 Which form for which contract

`hr.contract.type` gains `l10n_vn_document_kind`: `labour`, `probation`, `training` or `none`.

| Contract type (garment D20) | Kind | Printed |
| --- | --- | --- |
| `VN_LABOUR` *Hợp đồng lao động* | `labour` | Labour contract; fixed-term or indefinite from `date_end`; the probation clause when `l10n_vn_probation_form = clause` |
| `VN_PROBATION` *Hợp đồng thử việc* | `probation` | Probation contract |
| `VN_TRAINING` *Hợp đồng đào tạo* | `training` | Training contract |
| `VN_CASUAL` *Làm việc thời vụ* | `none` | Nothing (Peter, 2026-11-20) |
| Any other | empty = `none` | Nothing |

Annexes have their own form (kind `annex`), one per company.

**Casual work is a legal exposure, recorded, not reopened:** Art. 14 allows no written contract only under 1 month,
and the SI Law 2024 brings agreements of 1 month or more under compulsory SI whatever their name when they
describe paid work under the employer's direction (from memory, to confirm). The same reading could reach a
training contract whose trainee produces output for pay. The Regulation Reference v0.4 treats both as outside SI;
the lawyer's review of the forms is the moment to confirm it (§5, Q4).

### 2.3 The salary clause

Every pay line in force on the version's effective date (the contract's start for version 0) prints by its
component's **print mode**, `l10n_vn.payroll.component.l10n_vn_contract_print`, a stored field computed from the
component's flags and editable:

| Component | Default mode | Prints |
| --- | --- | --- |
| `in_si_base` (the base salary; fixed allowances) | `amount` | Name, amount per month, amount in words. Base salary under clause 1, the others under clause 2 *Phụ cấp lương* |
| `variable`, or nature `variable_salary` or `bonus` (`PROD`, `PERF`, the efficiency bonus) | `reference` | Name, then *theo Quy chế trả lương của Công ty*; no amount, no level |
| Any other earning (a fixed welfare amount, the training allowance `TRAIN`) | `amount` | Name and amount, under clause 3 *Các khoản bổ sung khác*; welfare under its own clause (Circular 10, from memory) |
| Deductions, employer contributions, totals | `none` | Nothing (they are never on pay lines) |

**Why no level or grade** (CD-06): `PROD` and `PERF` are the rest of a level or grade total after the base salary
(garment D16–D18), reviewed every 6 months for workers (Pay Policy §3.2). Printing *S2* or an amount would make each
review an annex, and an amount fixed in the contract and paid every month is what the SI rules count in the SI base
(Regulation Reference, *How the law classifies pay*). The level is HR's decision under the pay regulation; the
contract states the rule, the payslip shows the month's figure. Pay Policy §3.6 asked for the worker's level in the
appendix; this note proposes to drop it (§5, Q2).

**Probation pay:** where probation applies, the clause adds the rate, `vn.policy.probation_rate` on the effective
date (garment: 100%), and the probation amount of each `amount` line whose component has `probation_applies`.

**The worker example** (from 1 Nov 2026, garment D17–D18): base salary 4,500,000 *(Bốn triệu năm trăm nghìn đồng)*;
productivity pay *theo Quy chế trả lương*; efficiency bonus and other bonuses by the bonus regulation. An office
employee on G3-1: base salary as in the `BASE` scale for G3 (OPEN-24), performance pay by reference.

### 2.4 Conventions of the drafts

- `[G]` generic wording, shipped by `l10n_vn_hr_contract_document`; `[C]` the garment company's wording, shipped by
  `l10n_vn_hr_contract_document_garment`, for HR to verify first.
- `{…}` a value filled from Odoo (§3.1). `{if …}…{end}` a part printed only when the condition holds.
- Header and closing are common to every form; each form below starts after the header.
- Times New Roman 13, A4 portrait, the national motto centred, as Vietnamese administrative papers.

**Common header** `[G]`

```text
                 CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
                     Độc lập – Tự do – Hạnh phúc
                     ───────────────────────────
                                                {sign_place}, ngày {dd} tháng {mm} năm {yyyy}

                            {FORM TITLE}
                            Số: {number}

Căn cứ Bộ luật Lao động số 45/2019/QH14 ngày 20 tháng 11 năm 2019 và các văn bản hướng dẫn thi hành;
{form-specific bases}
Căn cứ nhu cầu và khả năng của hai bên,

Chúng tôi gồm:

BÊN A – NGƯỜI SỬ DỤNG LAO ĐỘNG
Tên doanh nghiệp:   {COMPANY NAME}
Mã số doanh nghiệp: {company_vat}
Địa chỉ trụ sở:     {company_address}
Điện thoại:         {company_phone}
Đại diện:           {rep_salutation} {rep_name}        Chức danh: {rep_title}

BÊN B – {NGƯỜI LAO ĐỘNG | NGƯỜI HỌC NGHỀ, TẬP NGHỀ}
Họ và tên:          {employee_name}                    Giới tính: {Nam|Nữ}
Ngày sinh:          {birthday}                         Quốc tịch: {nationality}
Số định danh cá nhân (CCCD): {personal_id}    Ngày cấp: {id_issue_date}    Nơi cấp: {id_issue_place}
Nơi thường trú:     {permanent_address}
{if current address differs}Nơi ở hiện tại:     {current_address}{end}
{if phone}Điện thoại:         {private_phone}{end}
```

**Common closing** `[G]`

```text
Điều {n}. Điều khoản thi hành
1. Những vấn đề không ghi trong hợp đồng này thực hiện theo Nội quy lao động, các quy chế của Công ty,
   thỏa ước lao động tập thể (nếu có) và quy định của pháp luật.
2. Hợp đồng này được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản, có hiệu lực từ
   ngày {date_start}.
3. Các phụ lục hợp đồng do hai bên ký kết là một bộ phận của hợp đồng này và có hiệu lực như hợp đồng này.

        {BÊN B LABEL}                                     NGƯỜI SỬ DỤNG LAO ĐỘNG
     (Ký, ghi rõ họ tên)                               {REP_TITLE}
                                                  (Ký, ghi rõ họ tên, đóng dấu)



     {employee_name}                                    {rep_name}
```

### 2.5 Labour contract (with or without probation clause)

Title *HỢP ĐỒNG LAO ĐỘNG*; number `{seq}/{yyyy}/HĐLĐ-{company_code}`.

```text
Hai bên thỏa thuận giao kết hợp đồng lao động và cam kết thực hiện các điều khoản sau đây:

Điều 1. Loại hợp đồng và thời hạn hợp đồng                                                   [G]
1. Loại hợp đồng: {Hợp đồng lao động xác định thời hạn {months} tháng
                  | Hợp đồng lao động không xác định thời hạn}.
2. Thời hạn hợp đồng: {từ ngày {date_start} đến ngày {date_end} | bắt đầu từ ngày {date_start}}.

{if probation clause}
Điều 2. Thử việc                                                                             [G]
1. Thời gian thử việc: {trial_length} {ngày làm việc | ngày}, từ ngày {date_start} đến hết ngày {trial_date_end}.
2. Tiền lương thử việc: bằng {probation_rate}% mức lương của công việc quy định tại Điều 4 của hợp đồng này.
3. Trong thời gian thử việc, mỗi bên có quyền hủy bỏ hợp đồng này mà không cần báo trước và không phải
   bồi thường.
4. Khi kết thúc thời gian thử việc, Bên A thông báo kết quả thử việc cho Bên B. Trường hợp đạt yêu cầu,
   hai bên tiếp tục thực hiện hợp đồng này; trường hợp không đạt yêu cầu, hợp đồng này chấm dứt.
{end}

Điều {n}. Công việc và địa điểm làm việc
1. Chức danh công việc: {job_name}.                                                         [G]
2. Công việc phải làm: thực hiện các công việc của chức danh theo bản mô tả công việc, định mức và
   sự phân công của người quản lý trực tiếp.                                                [C]
3. Địa điểm làm việc: {work_address}.                                                       [G]

Điều {n}. Tiền lương, phụ cấp lương và các khoản bổ sung khác
1. Mức lương theo công việc hoặc chức danh: {base_amount} đồng/tháng
   (Bằng chữ: {base_amount_words}).                                                          [G]
2. Phụ cấp lương: {for each: {name}: {amount} đồng/tháng | Không có}.                       [G]
3. Các khoản bổ sung khác:                                                                   [G]
   {for each reference component: - {name}: theo Quy chế trả lương của Công ty, căn cứ năng suất
     và kết quả thực hiện công việc của Bên B.}
   {for each other amount component: - {name}: {amount} đồng/tháng.}
4. Tiền lương làm thêm giờ, làm việc vào ban đêm: theo quy định của Bộ luật Lao động.       [G]
5. Tiền thưởng: theo Quy chế thưởng của Công ty, căn cứ kết quả sản xuất, kinh doanh và mức độ
   hoàn thành công việc của Bên B.                                                          [G]
6. Hình thức trả lương: {chuyển khoản vào tài khoản ngân hàng mang tên Bên B | tiền mặt}.   [G]
7. Kỳ hạn trả lương: mỗi tháng một lần, chậm nhất vào ngày 10 của tháng kế tiếp.            [C]

Điều {n}. Chế độ nâng bậc, nâng lương                                                        [C]
Bên B được xem xét nâng bậc, nâng lương theo điều kiện, thời gian và mức quy định trong Quy chế trả lương
và thang lương, bảng lương của Công ty. Kết quả xem xét được Công ty thông báo bằng văn bản.

Điều {n}. Thời giờ làm việc, thời giờ nghỉ ngơi                                              [C]
1. Thời giờ làm việc bình thường: không quá 08 giờ/ngày và 48 giờ/tuần; ca làm việc, giờ bắt đầu,
   giờ kết thúc và thời gian nghỉ giữa ca theo lịch làm việc của bộ phận và Nội quy lao động.
2. Làm thêm giờ: khi có nhu cầu, Bên A được huy động Bên B làm thêm giờ khi có sự đồng ý của Bên B và
   trong giới hạn của pháp luật.
3. Nghỉ hằng tuần, nghỉ hằng năm, nghỉ lễ, tết, nghỉ việc riêng và nghỉ không hưởng lương: theo
   Bộ luật Lao động và Nội quy lao động của Công ty.

Điều {n}. Trang bị bảo hộ lao động                                                           [C]
Bên B được cấp phát trang bị bảo hộ lao động và đồng phục phù hợp với công việc theo quy định của Công ty.
Đồng phục và trang bị được cấp là tài sản của Công ty; Bên B có trách nhiệm bảo quản và hoàn trả khi
chấm dứt hợp đồng theo Nội quy lao động.

Điều {n}. Bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp                               [G]
Hai bên tham gia bảo hiểm xã hội bắt buộc, bảo hiểm y tế và bảo hiểm thất nghiệp theo quy định của
pháp luật. Tiền lương tháng đóng bảo hiểm gồm mức lương và các khoản phụ cấp lương, các khoản bổ sung
khác theo quy định của pháp luật về bảo hiểm xã hội. Phần đóng của Bên B được Bên A khấu trừ vào tiền
lương hằng tháng.

Điều {n}. Đào tạo, bồi dưỡng, nâng cao trình độ, kỹ năng nghề                                 [G]
Bên B được Bên A đào tạo, bồi dưỡng theo yêu cầu công việc. Trường hợp Bên B được đào tạo bằng kinh phí
của Bên A, hai bên ký hợp đồng đào tạo nghề riêng theo Điều 62 Bộ luật Lao động.

Điều {n}. Quyền và nghĩa vụ của Bên B                                                        [C]
1. Được trả lương đầy đủ, đúng hạn và hưởng các chế độ theo hợp đồng này, quy chế của Công ty và
   pháp luật.
2. Hoàn thành công việc được giao; chấp hành Nội quy lao động, an toàn, vệ sinh lao động và sự điều hành
   hợp pháp của Bên A.
3. Bồi thường thiệt hại theo Nội quy lao động và pháp luật khi làm hư hỏng, mất mát tài sản của Công ty.
4. Thông báo cho Bên A khi thay đổi thông tin cá nhân, nơi cư trú, tài khoản ngân hàng.

Điều {n}. Quyền và nghĩa vụ của Bên A                                                        [C]
1. Bố trí công việc, điều hành, khen thưởng, xử lý kỷ luật lao động theo Nội quy lao động và pháp luật.
2. Trả lương đầy đủ, đúng hạn; bảo đảm điều kiện làm việc, an toàn, vệ sinh lao động.
3. Đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp và thực hiện các nghĩa vụ khác theo
   hợp đồng này và pháp luật.

{common closing}
```

### 2.6 Probation contract

Title *HỢP ĐỒNG THỬ VIỆC*; number `{seq}/{yyyy}/HĐTV-{company_code}`. Contents per Art. 24.2: the period and items a,
b, c, đ, g, h of Art. 21.1; no raise, insurance or training clause.

```text
Hai bên thỏa thuận giao kết hợp đồng thử việc với các điều khoản sau đây:

Điều 1. Thời gian thử việc                                                                   [G]
Từ ngày {date_start} đến hết ngày {date_end} ({trial_length} {ngày | ngày làm việc}), áp dụng cho công việc
{job_name}, thuộc nhóm công việc {probation_job_label}.

Điều 2. Công việc và địa điểm làm việc                          (as the labour contract)   [G][C]

Điều 3. Tiền lương thử việc                                                                  [G]
1. Mức lương của công việc: {base_amount} đồng/tháng; phụ cấp lương: {…}.
2. Tiền lương thử việc: bằng {probation_rate}% mức lương của công việc, tức {probation_amount} đồng/tháng
   (Bằng chữ: {…}); {for each reference component: {name}: theo Quy chế trả lương của Công ty.}
3. Hình thức trả lương: {…}. Kỳ hạn trả lương: {…}.

Điều 4. Thời giờ làm việc, thời giờ nghỉ ngơi                   (as the labour contract)   [C]
Điều 5. Trang bị bảo hộ lao động                                (as the labour contract)   [C]

Điều 6. Kết thúc thời gian thử việc                                                          [G]
1. Trong thời gian thử việc, mỗi bên có quyền hủy bỏ hợp đồng này mà không cần báo trước và không phải
   bồi thường.
2. Khi kết thúc thời gian thử việc, Bên A thông báo kết quả thử việc cho Bên B. Trường hợp đạt yêu cầu,
   hai bên giao kết hợp đồng lao động; trường hợp không đạt yêu cầu, hợp đồng này chấm dứt.

{common closing}
```

### 2.7 Training contract

Title *HỢP ĐỒNG ĐÀO TẠO* (học nghề, tập nghề để làm việc cho Công ty); number `{seq}/{yyyy}/HĐĐT-{company_code}`.
Art. 61 governs it; since 1 Jan 2026 the Labor Code no longer names its contents (§2.1), so the draft keeps
Art. 62.2's list where it fits and Pay Policy §14.2's terms.

```text
Hai bên thỏa thuận giao kết hợp đồng đào tạo với các điều khoản sau đây:

Điều 1. Nghề, công việc đào tạo; thời gian và địa điểm                                       [G]
1. Hình thức: tập nghề để làm việc cho Bên A (Điều 61 Bộ luật Lao động).
2. Nghề, công việc: {job_name}.
3. Thời gian: từ ngày {date_start} đến hết ngày {date_end}.
4. Địa điểm: {work_address}.
5. Bên A không thu học phí của Bên B.

Điều 2. Nội dung và tổ chức đào tạo                                                          [C]
Bên B được hướng dẫn thực hành các công đoạn của công việc {job_name} tại chuyền sản xuất, dưới sự
hướng dẫn của người được Bên A phân công, theo chương trình và tiêu chuẩn tay nghề của Công ty.

Điều 3. Tiền lương trong thời gian tập nghề                                                  [G]
Khi trực tiếp hoặc tham gia lao động, Bên B được trả:
1. {TRAIN name}: {amount} đồng/tháng (Bằng chữ: {…}), tính theo số ngày làm việc thực tế trong tháng;
2. {for each reference component: {name}: theo Quy chế trả lương của Công ty.}
3. Hình thức trả lương: {…}. Kỳ hạn trả lương: {…}.

Điều 4. Thời giờ học nghề, tập nghề và nghỉ ngơi                (as the labour contract)   [C]
Điều 5. Trang bị bảo hộ lao động                                (as the labour contract)   [C]

Điều 6. Đánh giá và kết thúc                                                                 [C]
1. Bên A đánh giá tay nghề của Bên B trong và khi kết thúc thời gian tập nghề theo tiêu chuẩn của Công ty.
2. Bên A có quyền chấm dứt hợp đồng này trong thời gian tập nghề hoặc khi kết thúc nếu Bên B không đạt
   tiêu chuẩn tay nghề, sau khi thông báo kết quả đánh giá cho Bên B.
3. Khi kết thúc thời gian tập nghề, nếu Bên B đạt tiêu chuẩn và đủ điều kiện theo Bộ luật Lao động, hai bên
   giao kết hợp đồng lao động.

{if the company keeps a repayment clause — to decide with the lawyer, §5 Q5}
Điều 7. Cam kết làm việc và chi phí đào tạo                                                  [C]
1. Sau khi giao kết hợp đồng lao động, Bên B cam kết làm việc cho Bên A ít nhất {n} tháng.
2. Trường hợp Bên B tự ý chấm dứt hợp đồng trước thời hạn cam kết, Bên B hoàn trả chi phí đào tạo theo
   thỏa thuận tại Phụ lục chi phí đào tạo. Khoản hoàn trả không khấu trừ vào tiền lương.
{end}

{common closing, Bên B labelled NGƯỜI HỌC NGHỀ, TẬP NGHỀ}
```

### 2.8 Annex

Title *PHỤ LỤC HỢP ĐỒNG LAO ĐỘNG* (or *PHỤ LỤC HỢP ĐỒNG THỬ VIỆC | ĐÀO TẠO* by the contract's kind); number
`{nn}/{contract number}`, `nn` the version's sequence.

```text
Căn cứ Bộ luật Lao động số 45/2019/QH14;                                                    [G]
Căn cứ Hợp đồng {kind} số {contract_number} ký ngày {contract_sign_date} giữa hai bên;
Căn cứ thỏa thuận của hai bên,

{parties, as the common header}

Hai bên thỏa thuận sửa đổi, bổ sung hợp đồng {kind} số {contract_number} như sau:

Điều 1. Nội dung sửa đổi, bổ sung
{for each changed term group, in clause order:}
{i}. Sửa đổi {clause_ref} của Hợp đồng ({term group label}):
    - Nội dung đã thỏa thuận: {old text}
    - Nội dung sửa đổi:       {new text}

Điều 2. Hiệu lực
1. Phụ lục này là một bộ phận của Hợp đồng số {contract_number}, có hiệu lực kể từ ngày {effective_date}.
2. Các nội dung khác của Hợp đồng không thay đổi.
3. Phụ lục được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

{signatures}
```

- **Term groups** are what a version's snapshot holds and what an annex compares: work (job), workplace, salary
  (one entry per printed component: added, removed, amount changed), probation clause, insurance (participant type),
  and any group a company form adds.
- **`{clause_ref}`** comes from the form: each form record maps a term group to its clause reference in that form
  (`Điều 4`, `khoản 1 Điều 4`). Article numbers in the drafts are therefore fixed by the company's template, and the
  annex cites them; a template whose numbering changes keeps old contracts' references in their snapshot.
- Old and new text are rendered by the same blocks as the contract, so an annex reads like the contract it amends.

### 2.9 Points for HR and the lawyer

- Every `[C]` clause, and the payday, hours and uniform wording against the work rules (*Nội quy lao động*) actually
  registered.
- The insurance clause: whether to state each side's rates (today 21.5% and 10.5%, Regulation Reference) or keep the
  reference to the law, which survives a change of rates.
- The pay regulation and bonus regulation (Pay Policy intro) must exist and be published before contracts refer to
  them; the variable pay rests on that reference.
- The training contract: the repayment clause (§5, Q5), and SI on training and casual work (§2.2).
- Circular 10/2020 Art. 3 against these drafts, since it could not be read here.

---

## 3. The data

### 3.1 What a contract states, and where Odoo holds it

| Content (Art. 21.1, Circular 10 Art. 3) | Source in Odoo | State on the test copy, 287 running contracts |
| --- | --- | --- |
| Employer's name, enterprise code, address, phone | `res.company` / its partner: `name`, `vat`, street, `city`, state, `phone` | Present (1602237713; 191A TL948, phường Chi Lăng, An Giang) |
| Signer's name and title | **Missing** → `l10n_vn_legal_rep_id`, `l10n_vn_legal_rep_title` (§3.2) | Missing |
| Employee's name | `hr.employee.name` | Present |
| Date of birth, sex | `birthday`, `gender` (core) | **0 of 287** filled |
| Nationality | `country_id` (core); default Việt Nam when empty | — |
| Residence | **Permanent address missing** → `l10n_vn_permanent_address`; current address = core's `private_street` … `private_country_id` | 0 of 287 private addresses |
| ID number | `l10n_vn_personal_id` (payroll D70) | 3 of 287 (test values) |
| ID issue date and place | **Missing** → `l10n_vn_id_issue_date`, `l10n_vn_id_issue_place` | — |
| Work | `hr.contract.job_id`; the duties by reference to the job description (`hr.job.description`) | Job on 286 of 287; 0 of 8 jobs have a description |
| Workplace | **Missing on the contract** → `l10n_vn_work_address_id`, default the employee's work address (`address_id`) | Every employee's work address is the company |
| Term | `date_start`, `date_end`, contract type | Present |
| Probation | `l10n_vn_probation_form`, `trial_date_end`, `l10n_vn_probation_job`, `vn.policy.probation_rate` | Set by the go-live scripts |
| Salary, allowances, supplements | Pay lines, scale cells and parameters on the effective date (§2.3) | Set by the go-live scripts |
| Payment method | Participant type `paid_by_transfer` | Present |
| Payment date, raises, hours, equipment, training | Form wording `[C]` | — |
| Insurance | Participant type's funds | Present |
| Signing date and place | **Missing** → `l10n_vn_sign_date` (default the start date); place = the company's province | — |
| Contract number | The version, at approval | — |

### 3.2 New fields

| Model | Field | Type | Notes |
| --- | --- | --- | --- |
| `res.company` | `l10n_vn_legal_rep_id` | Many2one `res.partner` | *Legal Representative*, the person who signs: the director (Peter, 2026-11-20). A contact, so it works whether or not the director is an employee |
| | `l10n_vn_legal_rep_title` | Char | *Title*, e.g. *Giám đốc* |
| | `l10n_vn_contract_approval` | Boolean | The switch (§1.2), off by default |
| | `l10n_vn_contract_code` | Char | Short code in the numbers (`QP`) |
| `hr.employee` | `l10n_vn_id_issue_date` | Date | *ID Issue Date*, `groups="hr.group_hr_user"`, tracked, after `l10n_vn_personal_id` |
| | `l10n_vn_id_issue_place` | Char | *ID Issue Place*, e.g. *Bộ Công an* or *Cục Cảnh sát QLHC về TTXH*, as on the card |
| | `l10n_vn_permanent_address` | Char | *Permanent Address* (nơi thường trú), one line as on the card; after the 2025 merger of provinces the card's old address may differ from today's names: HR writes it as the card or the residence record shows |
| `hr.contract` | `l10n_vn_work_address_id` | Many2one `res.partner` | *Workplace*, default the employee's `address_id` |
| | `l10n_vn_sign_date` | Date | *Signing Date*, default `date_start` |
| | `l10n_vn_version_ids`, `l10n_vn_version_id` (current), `l10n_vn_amendment_id`, `l10n_vn_approved` | | §1.2–§1.4; `copy=False` |
| `hr.contract.type` | `l10n_vn_document_kind` | Selection | §2.2 |
| `l10n_vn.payroll.component` | `l10n_vn_contract_print` | Selection | `amount` / `reference` / `none`, editable stored compute (§2.3) |

**Why not `required=True`** (Peter's answer, 2026-11-20): it would refuse every save of the 287 existing employees
until each is completed, and every import. *Mandatory where used* asks for the data at the moment it is needed.

### 3.3 Mandatory where used

Approval, *Print Draft* and *Regenerate* stop with one message listing everything missing (like payroll's
`missing_ids`, D106), per contract:

| Needed for | Fields |
| --- | --- |
| Every form | Company: legal representative, title, `vat`, street, province. Employee: name, birthday, gender, `l10n_vn_personal_id` (12 digits), issue date, issue place, permanent address. Contract: job, workplace, signing date, a form for the company and kind, pay lines in force on the effective date with at least one `amount` line |
| Labour contract with probation, probation contract | `trial_date_end` (clause) or `date_end` (contract), `l10n_vn_probation_job`, the length within Art. 25 for that job (payroll's `vn.probation.max_days`), the rate at least 85% (`vn.probation.min_rate`) |
| Fixed-term labour contract | `date_end` within 36 months of `date_start` |
| Training contract | `date_end` within 3 months of `date_start` (payroll's `contract_term` rule, D107, as a block here) |
| Kind `none` | Nothing beyond the contract's own rules |

Printing a draft, before approval, carries a *BẢN NHÁP* (draft) watermark and no number.

### 3.4 Go-live data

The HR data entry already planned for go-live (every CCCD, bank accounts; Technical Design §29 step 1c) grows by the
birthday, sex, issue date and place and permanent address of everyone who gets a document: 287 people on the test
copy, all from the ID card. One spreadsheet imported through Odoo's standard employee import, matched on the
employee's reference, is the quickest route. Job descriptions (8 jobs) are not required, since the contract refers to
them; HR writes them when it can.

---

## 4. The modules

### 4.1 `l10n_vn_hr_contract_document` (generic)

- **Depends:** `l10n_vn_payroll` (pay lines, components, participant types, `l10n_vn_personal_id`,
  `l10n_vn_probation_job`, the parameters), which brings `hr_contract`, `mail` and OCA `payroll`. Python: `num2words`
  (already required by `l10n_vn_voucher`, so present in the image); the amount in words is a few lines of its own
  rather than a dependency on `l10n_vn_voucher`, which brings accounting.
- **Holds:** the fields of §3.2; `l10n_vn.contract.version`; `l10n_vn.contract.form` (company, kind, name, QWeb
  template key, number sequence, the clause references of §2.8); the lifecycle of §1 with its switch; the rendering
  (layout, header, closing, the salary blocks of §2.3, the amount in words) and **default forms** with the `[G]`
  wording and neutral `[C]` placeholders, so the module works for any Vietnamese company; *Annexes for a Date*;
  access (§1.7).
- **Groups:** no new group. Prepare and amend: `hr_contract.group_hr_contract_employee_manager`; approve, cancel,
  *Annexes for a Date*: `hr_contract.group_hr_contract_manager`; read versions: those two and payroll users. Editing
  pay lines needs payroll groups as today.
- **Nothing per company at install:** forms and the switch are set in *Settings → Employees → Contracts* or by a
  company module's loader.
- **Odoo 19** replaces `hr.contract` with versions on the employee (`hr.version`). The version model here maps onto
  it at that migration; nothing in this design prevents it.

### 4.2 `l10n_vn_hr_contract_document_garment` (company)

- **Depends:** `l10n_vn_hr_contract_document`, `l10n_vn_payroll_garment`.
- **Holds:** the garment company's QWeb templates (inheriting the generic forms, replacing the `[C]` clauses with
  the approved wording), and a loader, started from *Settings* by a contract administrator like the payroll
  loader (garment D1–D8), that creates for one company the four form records with their sequences and clause
  references, sets `l10n_vn_document_kind` on `VN_LABOUR`, `VN_PROBATION`, `VN_TRAINING`, `VN_CASUAL`, and sets the
  print mode on the garment components where the default differs. Only where empty; it never switches approval on:
  that is HR's go-live act, as posting is the accountant's (garment D24).
- QWeb templates are global, but a company prints them only through its own form records, so the trading company
  is unaffected.

### 4.3 Build steps

| # | Module | Scope | Gives |
| --- | --- | --- | --- |
| 1 | generic | Fields of §3.2 (without versions), form records, rendering, default forms, *Print Draft* with the data check of §3.3 | Level 1: contracts printed from Odoo |
| 1 | garment | The company wording, once HR has checked the drafts; the loader | The real forms |
| 2 | generic | Versions, *Approve* (number, snapshot, PDF), *Approve from Paper*, *Regenerate*, the switch, the write guards and pay-line rules of §1.3, access | Level 2 |
| 3 | generic | Amendments (§1.4), the annex form, *Annexes for a Date*, *Next Contract* | Level 3 |
| 4 | generic | Signed date and scan; checks added to payroll's catalogue from this module's data: `contract_unapproved` (note), `contract_amending` and `contract_terms` (printed terms on the month's last day differ from the version in force; warning) | Level 4 and the gap checks |

Tests per step as in payroll: `TransactionCase`, `post_install` (fixtures create employees and contacts), no `HttpCase`;
the PDF rendered and its text checked for the fields; the lock tested through each path (form write, statusbar
value, the cron's `update_state`, import-style create, the departure wizard) with a positive control; the pay-line
rules tested on a locked, an amending and an unlocked contract.

### 4.4 Go-live order

Payroll does not wait. The order of Technical Design §29 stays: go-live scripts → October rehearsal on a fresh
`prod_copy` → November on production, payday 10 December. The documents fit beside it:

1. **This note reviewed** (Peter), then the generic step 1 spec and code; in parallel HR checks the `[C]` wording
   and collects the ID card data (§3.4).
2. **Go-live scripts** put contract types, pay lines and pay groups on the contracts. The documents print exactly
   that data, so they come after the scripts on production, and the rehearsal on `prod_copy` is also the first full
   print run.
3. **Generic steps 1–2 and garment step 1** before the November contracts are signed; the switch is turned on per
   company once the November contracts are approved. Until then contracts run as today, and payroll pays them.
4. **Steps 3–4** after go-live; the first real annex is the next base-salary change (OPEN-24), with
   *Annexes for a Date*.

**Fallback:** if step 1 is not ready when the contracts must be signed, HR prints them from Word using the same
drafts (§2), and *Approve from Paper* registers them later, so annexes can still be printed from Odoo.

---

## 5. Questions for Peter

My recommendation is given with each; nothing below blocks the generic step 1.

| # | Question | Recommendation |
| --- | --- | --- |
| Q1 | November documents: new contracts for everyone, or annexes to the paper contracts they hold? | New contracts where the paper contract is with another entity or of another type (Temporary and Seasonal); annexes after *Approve from Paper* where it stays valid. HR knows which |
| Q2 | Drop the worker's level from the contract (Pay Policy §3.6 asked for it)? | Yes (CD-06): fewer annexes, and an amount fixed in the contract weakens the SI position. To fold into Pay Policy v0.8 |
| Q3 | Print the department and the working schedule? | No (CD-03): moves and calendar changes would each need an annex |
| Q4 | SI on training and casual contracts under the SI Law 2024 | Ask the lawyer during the form review; the Regulation Reference changes only if they disagree |
| Q5 | A repayment clause in the training contract | Leave it out unless the company really trains at a cost it wants back; Art. 61 forbids tuition, and Art. 62's repayment is for employees trained at the employer's cost. Lawyer to confirm |
| Q6 | Who approves in Odoo | The HR manager as contract administrator; the director signs the paper. No preparer–approver segregation |

---

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-11-20 | First draft: lifecycle, forms with draft wording, data, modules, build steps, questions. |
