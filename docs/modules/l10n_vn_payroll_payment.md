# l10n_vn_payroll_payment

Salary advances and the payment lists of a payroll run for `l10n_vn_payroll`, without accounting. An
advance is requested alone or in a batch, approved by the HR manager, marked as paid, and settled on the
employee's payslips, oldest first, through the engine's hook; what net pay cannot cover stays open for the
next payslip. Posting belongs to `l10n_vn_payroll_account`.
Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.6.md` §23, PTD-16, PTD-24, on `Pay Policy v0.6.md`
§11 and `Payroll Requirements Specification v0.7.md` FR-43, FR-71, FR-77. Engine: `docs/modules/l10n_vn_payroll.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Advances: the record, batches, the limit at approval, approval, payment date, cancellation; settlement on payslips through `_l10n_vn_advances()`; the check at run approval; `vn.policy.advance_max_share` in the garment loader | done | 2026-11-19: `-u l10n_vn_payroll_garment`, then `-i`, then `-u l10n_vn_payroll`, each `exit=0`; 31 post-tests here, 0 failures (the last run 302: 243 engine + 28 garment + 31, the dependent modules upgraded with it). UI as officer, reviewer and approver on the three trial employees: single advance, a batch with a line above the limit refused until noted, share batch rounded down, cancelling, read-only approver |
| 1.1 | The limit on pay earned to date (attendance from `hr_attendance_day`), the limit kept at approval; eligibility by pay group, a hard refusal; share batches on earned pay; `vn.policy.advance_pay_groups` in the garment loader (its step 8) | done | 2026-11-19: `-u l10n_vn_payroll_payment` 34 tests, `-u l10n_vn_payroll_garment` 28 tests, each `exit=0`, 0 failures. UI on the trial employees dated 16 May: days worked and earned from May attendance, limit kept at approval, an employee without pay group refused even with a note and left out by *Generate* |
| 1.2 | With `l10n_vn_payroll` step 12: eligibility and the batch's pay group filter read the pay group of the main contract for the advance's month (D18) | done | 2026-11-19, with engine step 12: one `-u l10n_vn_payroll`, `exit=0`, 35 tests here, 0 failures; UI as expected |
| 2 | Payment lists (D19–D27): `l10n_vn.payroll.payment` and its lines, one mechanism for payday and advances; a run's list made at approval, an advance list from approved advances or a batch; the transfer file (the module's copy of the *Export Payslip Batch* layout, paying the amount to pay) and the cash list; *Mark as Paid* per method or per line with the payment date, which pays the advances and, once every line is paid, the run; step 1's advance payment wizard replaced | done | 2026-11-19, one run: `-u l10n_vn_payroll`, `exit=0`, 320 post-tests (245 engine, 28 garment, 47 here), 0 failures. UI on the test copy: advance lists from a batch and from selected advances, the transfer file against Peter's layout, transfers marked paid and the advances paid with that date, the approver read-only. Changed from the spec while coding: the run's own *Mark as Paid* pays a listed run's remaining lines instead of refusing (D25) |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §23.2: `payment_line_id`, `move_line_id`, settled amount and balance from the 3341 reconciliation; payment through `account.payment.order` | settlement records per payslip (D5); a payment date set by *Mark as Paid* (D4); no accounting field | PTD-24 and FR-77: advances work without the accounting module, which §23 had not caught up with. `l10n_vn_payroll_account` adds the 3341 side |
| 2 | §23.2: states `draft`, `approved`, `paid`, `settled`, `cancelled` | no `settled` state: a paid advance with `balance` 0 is settled (D6) | The balance already says it, and it changes with payslips, not with a user's step |
| 3 | §23.2: `period_id` on the advance | none: the month comes from `date` for the limit (D2), and `paid_date` decides the payslip (D7) | One date per question; a period would have to exist before an advance could be requested |
| 4 | §23.2: the batch is a wizard creating drafts | a batch record (D9) | It carries the group's approval and payment, and step 2 needs a record to export the group's transfer list from |
| 5 | §19.2, engine D66 and divergence 27: `advance_limit` as a check with a finder on payslips | applied at the advance's approval, through the catalogue record's level; no payslip finding (D3) | TC-F16 places it at approval. On a payslip a warning needs a second note before review (engine D74) |
| 6 | FR-71, Pay Policy §11: advances paid by bank | the record does not say how it is paid; step 2 lists it as transfer or cash by `paid_by_transfer`, as payday does | Casual workers are paid in cash |
| 7 | Engine D57, its divergence 27, the docstring of `_l10n_vn_advances()`: the hook and the finder belong to `l10n_vn_payroll_account` | this module overrides the hook (D7) | PTD-24 |
| 8 | Pay Policy §11: the limit on the monthly amount (base + productivity or performance pay at 100%) | on pay earned to date (D14, step 1.1) | A monthly limit ignores attendance: an absent worker, a new hire or a leaver could draw half a month not earned (Peter, 2026-11-19). Pay Policy §11 to be reworded |
| 9 | Pay Policy §11: no rule on who may take an advance | the pay groups of `vn.policy.advance_pay_groups`; others are refused (D16, step 1.1) | Eligibility is configuration, a limit of 0 inside it an exception the approver may grant, outside it no advance (Peter, 2026-11-19). Pay Policy §11 to be reworded |
| 10 | §23.1: payday through `account.payment.order`, a payment mode with the code `l10n_vn_bank_xlsx`, the run paid once the order's payments reconcile | a payment list of this module, its transfer file and *Mark as Paid* (D19, D25); the run paid when the list is | Payment works without accounting (PTD-24, FR-77). OCA's payment orders are built around payable journal items, which do not exist before posting. `l10n_vn_payroll_account` posts each payment from *Mark as Paid* to the bank's outstanding account, and the bank statement reconciles it (Peter, 2026-11-19) |
| 11 | Engine D72: *Mark as Paid* on the run, replaced by the reconciliation in `l10n_vn_payroll_account` | a run with a payment list is paid through it; the run's own button is hidden for it and, called anyway, pays the list's remaining lines dated today (D25) | One way to pay, the same for payday and advances, recording when each person was paid |

## Decisions

| # | Decision |
|---|---|
| D1 | **Roles** (design §3): the officer requests, marks as paid and cancels before payment; the reviewer group, held by the HR manager, approves and cancels a paid advance. Each step checks the user's group and then works as superuser, as the run does (engine D72) |
| D2 | **Monthly amount and limit** (Pay Policy §11): the monthly amount is the sum, at 100%, of the pay lines of the employee's main contract for the month of `date` (the last of `_l10n_vn_period_contracts`), in force on that contract's last day in the month, whose component is active, in section `salary` and not prorated `per_day`. What is left = `vn.policy.advance_max_share` on `date` × the monthly amount − the employee's other `approved` and `paid` advances dated in the same month, never below 0. **Replaced in step 1.1** by pay earned to date (D14); the monthly amount stays its base |
| D3 | **Above the limit**, the level of the check `advance_limit` (`vn.check.advance_limit` on `date`, else its default `warning`) decides at approval: `off` and `note` approve; `warning` needs `limit_note`; `error` refuses. A missing `vn.policy.advance_max_share` refuses the approval with the strict reader's message; on screen the figures then read 0 |
| D4 | **Paid** is a recorded fact: *Mark as Paid* takes one payment date for the selected approved advances. How the money moved is outside this step |
| D5 | **Settlement records** follow the damage allocations (engine D56): one `l10n_vn.payroll.advance.settlement` per advance and payslip, replaced at each calculation, removed when the payslip stops |
| D6 | **Settled amount and balance:** `settled_amount` sums the settlements of `done` payslips, so it moves when the run is approved; `balance` = `amount` − `settled_amount` |
| D7 | **What a payslip settles:** `_l10n_vn_advances()` returns the employee's `paid` advances of the payslip's company with `paid_date` on or before the payslip's last day, oldest `paid_date` first, then by id. Each amount is the advance less its settlements on other payslips that are not cancelled, so a payslip not yet approved already reserves what it took; advances with nothing open are left out. An advance paid after the month's end, before payday included, belongs to the next month |
| D8 | **Run approval re-reads the advances:** approving a reviewed run is refused when a calculated payslip would now settle other advances or other amounts than its snapshot, the snapshot's net allocated oldest first over what `_l10n_vn_advances()` now returns; for instance an advance marked paid with an earlier date after calculation. Only what is settled is compared, so a later month's payslip reserving the carried rest does not refuse it. The officer calculates again |
| D9 | **Batches:** a batch holds the group's date and reason and a selection (pay group, departments) from which *Generate* adds one draft advance per eligible employee, keeping lines already there. An employee is eligible when active in the company, with a main contract for the month on a Vietnamese structure that has not ended before `date`. The amount is fixed, or a share of the monthly amount (of pay earned to date from step 1.1, D17), first rounded by the currency and then rounded down to `round_to`; an amount of 0 adds no line. Lines stay editable while draft, and the reviewer writes limit notes on them. Approving and marking as paid act on the batch's lines together |
| D10 | **After draft** an advance's employee, company, date, amount, reason and limit note do not change. `state`, `approved_by`, `approved_at` and `paid_date` are written only by the module's steps or as superuser, which is also how go-live data loads advances already paid |
| D11 | **Cancelling:** draft and approved advances by the officer; a paid one by the reviewer, only without a settlement on a `done` payslip. Cancelled is final; a new advance replaces it. Only draft advances are deleted |
| D12 | **A leaver's open balance stays open** and shows under the *Open Balance* filter; `advance_carried` has already reported it on the last payslip. Pay Policy §11 settles it with the employee in writing |
| D14 | **Pay earned to date** (step 1.1): days worked = the sum of `days_worked` that `hr.employee._attendance_days()` gives from the 1st of the month of `date` to the day before `date` (none when `date` is the 1st); earned = the monthly amount (D2) × days worked ÷ `vn.policy.std_days` on `date`, rounded by the currency. What is left = `vn.policy.advance_max_share` × earned − the month's other `approved` and `paid` advances, rounded, never below 0. Only attendance counts: no paid leave or holiday, and a pay group in *exception* mode that does not scan earns 0. Productivity counts at 100%, since attainment is unknown mid-month |
| D15 | **The limit at approval is kept** (step 1.1): approval stores what was left then in `limit_at_approval`, since the on-screen figures move as attendance arrives |
| D16 | **Eligibility** (step 1.1): `vn.policy.advance_pay_groups` on `date` is a comma-separated list of pay groups (`worker`, `support`, `office`, `daily`, `manager`). An employee whose `l10n_vn_pay_group` is not in it, or empty, gets no advance: approval refuses it whatever the note, and *Generate* leaves them out. Inside the list a limit above the amount, 0 included, follows D3. A missing parameter refuses approval and *Generate* with the strict reader's message |
| D17 | **Share batches on earned pay** (step 1.1): `share` × pay earned to date on the batch's `date` (D14), so a share of 0.5 meets the garment limit exactly |
| D18 | **The pay group of the month's contract** (step 1.2, engine step 12): eligibility (D16) and the batch's `pay_group` filter read `l10n_vn_pay_group` on the employee's main contract for the month of `date`, the contract D2 already reads; an employee without one is not eligible |
| D19 | **One payment mechanism** (step 2): a payment list `l10n_vn.payroll.payment` of kind `payroll` (one run) or `advance` (approved advances), with a line per payment: employee, amount, method (`transfer` / `cash`), bank account, status and payment date. The transfer file, the cash list and *Mark as Paid* are the same for both kinds. It replaces step 1's advance payment wizard (D4) |
| D20 | **A run's list is made at approval:** one line per payslip whose `l10n_vn_to_pay` is above 0, with that amount; `transfer` when the payslip's contract's participant type is `paid_by_transfer`, else `cash`; the employee's `bank_account_id` on transfer lines. No list when no payslip has anything to pay |
| D21 | **An advance list** is made from approved advances not yet on a list, chosen in the advance list or all those of a batch: one line per advance, its amount; the method from the participant type of the main contract for the advance's month |
| D22 | **The bank account is the line's:** set from the employee when the list is made, changeable on an unpaid line (an account corrected before the transfer), among the employee's own accounts. The file reads the line |
| D23 | **The transfer file** is the module's own copy of the layout of Peter's *Export Payslip Batch* (`Bank Template 1.xlsx`: sheet `in`, headers in row 1, a row per transfer from row 2), on the payment list, row field `transfer_line_ids`; Peter's template stays for the old runs. It is made by a button that refuses a list without transfer lines or with a transfer line without bank account, naming them; each file made is attached to the list. The columns stay as Peter's; Peter asks for changes when the bank needs them |
| D24 | **The cash list** is a printed list of the cash lines, a signature per person, the total and the signatures of preparer, chief accountant and director |
| D25 | **Mark as Paid** takes a payment date for the unpaid lines of one method, which the officer may narrow (a transfer the bank returned stays unpaid and is paid later). A paid line records its date; its advance becomes `paid` with that date; the list is `paid` when every line is, and its run then moves to `paid`. The engine's run button, hidden for a run with a list, keeps its meaning there: it pays the lines still to pay, dated today, under the same officer check — so the engine's own tests, which run with this module installed, still hold |
| D26 | **Deleting and cancelling:** an advance list without a paid line can be deleted, its advances going back to approved and off any list; a run's list cannot. Cancelling an approved advance removes its unpaid line |
| D27 | **No accounting here:** paying a line is the step `l10n_vn_payroll_account` extends to post the payment |
| D13 | **No change to the engine's code:** the module extends `_l10n_vn_advances`, `_l10n_vn_prepare_one`, `_l10n_vn_record_stop` and `action_l10n_vn_approve`. The check's level is read with the engine's `_l10n_vn_level`, given an object holding the advance's `date` as `date_to` and its `company_id` |

## Folder structure

```
l10n_vn_payroll_payment/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── hr_payslip.py
│   ├── hr_payslip_run.py
│   ├── l10n_vn_payroll_advance.py
│   └── l10n_vn_payroll_advance_batch.py
├── wizards/
│   ├── __init__.py
│   ├── l10n_vn_payroll_advance_pay.py
│   └── l10n_vn_payroll_advance_pay_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── l10n_vn_payroll_payment_security.xml
├── views/
│   ├── l10n_vn_payroll_advance_views.xml
│   ├── l10n_vn_payroll_advance_batch_views.xml
│   └── menus.xml
├── readme/
│   └── DESCRIPTION.md
└── tests/
    ├── __init__.py
    ├── common.py
    ├── test_advance.py
    ├── test_settlement.py
    └── test_batch.py
```

## Manifest

| Key | Value |
|---|---|
| `name` | Vietnam - Payroll Payment |
| `summary` | Salary advances and the payment lists of Vietnamese payroll runs |
| `version` | `18.0.1.0.0` |
| `author`, `website`, `license`, `category`, `countries` | as `l10n_vn_payroll` |
| `depends` | `l10n_vn_payroll` |
| `data` | `security/l10n_vn_payroll_payment_security.xml`, `security/ir.model.access.csv`, `views/l10n_vn_payroll_advance_views.xml`, `views/l10n_vn_payroll_advance_batch_views.xml`, `wizards/l10n_vn_payroll_advance_pay_views.xml`, `views/menus.xml` |
| `installable` | True |

## Python packages

`__init__.py` imports `models` and `wizards`. `models/__init__.py` imports `l10n_vn_payroll_advance`,
`l10n_vn_payroll_advance_batch`, `hr_payslip`, `hr_payslip_run`. `wizards/__init__.py` imports
`l10n_vn_payroll_advance_pay`.

## Access

### `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_advance_user` | `model_l10n_vn_payroll_advance` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_advance_reader` | `model_l10n_vn_payroll_advance` | `l10n_vn_payroll.group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_advance_approver` | `model_l10n_vn_payroll_advance` | `l10n_vn_payroll.group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_advance_batch_user` | `model_l10n_vn_payroll_advance_batch` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_advance_batch_reader` | `model_l10n_vn_payroll_advance_batch` | `l10n_vn_payroll.group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_advance_batch_approver` | `model_l10n_vn_payroll_advance_batch` | `l10n_vn_payroll.group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_advance_settlement_user` | `model_l10n_vn_payroll_advance_settlement` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_advance_settlement_reader` | `model_l10n_vn_payroll_advance_settlement` | `l10n_vn_payroll.group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_advance_settlement_approver` | `model_l10n_vn_payroll_advance_settlement` | `l10n_vn_payroll.group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_advance_pay_user` | `model_l10n_vn_payroll_advance_pay` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |

The reviewer and the manager reach these through the officer group they imply.

### `security/l10n_vn_payroll_payment_security.xml`

Global rules, `[('company_id', 'in', company_ids)]`: `rule_advance_company`, `rule_advance_batch_company`,
`rule_advance_settlement_company`.

## Models

### `l10n_vn.payroll.advance` — `models/l10n_vn_payroll_advance.py`

`_description = "Salary Advance"`, `_order = "date desc, id desc"`, `_check_company_auto = True`.
Module constants: `OFFICER`, `REVIEWER` (the engine's group ids), `CONTROLLED = {"state", "approved_by",
"approved_at", "paid_date"}`, `FROZEN = {"employee_id", "company_id", "date", "amount", "reason", "limit_note"}`.

| Field | Type | Attributes |
|---|---|---|
| `employee_id` | Many2one `hr.employee` | required, `ondelete="restrict"`, index, `check_company=True` |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `batch_id` | Many2one `l10n_vn.payroll.advance.batch` | string *Batch*, `ondelete="restrict"`, index, `check_company=True`, `copy=False` |
| `date` | Date | required, string *Requested Payment Date*, default today |
| `amount` | Monetary | required |
| `reason` | Char | required |
| `state` | Selection | `draft` *Draft*, `approved` *Approved*, `paid` *Paid*, `cancelled` *Cancelled*; required, default `draft`, readonly, `copy=False`, index |
| `monthly_amount` | Monetary | non-stored compute, `compute_sudo=True`, string *Monthly Amount* (D2) |
| `limit_left` | Monetary | same compute, string *Limit Left* (D2) |
| `over_limit` | Boolean | same compute, string *Above Limit*: `amount` > `limit_left` and the check's level is not `off` |
| `limit_note` | Char | string *Limit Note*, `copy=False` |
| `approved_by` | Many2one `res.users` | readonly, `copy=False` |
| `approved_at` | Datetime | readonly, `copy=False` |
| `paid_date` | Date | string *Payment Date*, readonly, `copy=False` |
| `settlement_ids` | One2many `l10n_vn.payroll.advance.settlement` | `advance_id`, readonly |
| `settled_amount` | Monetary | stored compute, string *Settled* (D6); depends `amount`, `settlement_ids.amount`, `settlement_ids.payslip_id.state` |
| `balance` | Monetary | same compute |

SQL: `amount_positive`: `CHECK(amount > 0)`, *An advance has an amount above 0.*

`_compute_display_name`: *%(employee)s, %(date)s*.

`_compute_limit` depends `employee_id`, `company_id`, `date`, `amount`; a record without employee or date, or a
`UserError` from the parameter or a scale cell, gives 0, 0 and False.

| Method | Behaviour |
|---|---|
| `create` | refused with `AccessError` unless superuser when values hold a `CONTROLLED` field; with `batch_id`, missing `company_id`, `date` and `reason` come from the batch |
| `write` | unless superuser: `AccessError` for a `CONTROLLED` field; `UserError` *Only a draft advance can change.* for a `FROZEN` field on a record not in `draft` |
| `unlink` | `UserError` *Only a draft advance can be deleted.* for any other state |
| `_l10n_vn_require(*groups)` | `AccessError` unless superuser or the user has one of the groups |
| `_l10n_vn_monthly_amount_of(employee, company, date)` | `@api.model`, D2; 0 without a contract; also used by the batch |
| `_l10n_vn_monthly_amount()` | the same for the advance, `ensure_one` |
| `_l10n_vn_limit_left()` | D2, `ensure_one`, rounded by the currency; raises the strict reader's `UserError` |
| `_l10n_vn_limit_level()` | D3, D13; `off` when the check is archived |
| `_l10n_vn_open_amounts(payslip)` | `{id: amount − the settlements on payslips other than payslip and not cancelled}` (D7) |
| `action_approve()` | reviewer; every record `draft`, else `UserError` *Only a draft advance is approved.*; applies D3 record by record, oldest `date` first; afterwards one `UserError` naming up to three employees for each kind of refusal (*Above the limit, a note is needed: %(employees)s.* / *Above the limit: %(employees)s.*); writes `state`, `approved_by`, `approved_at` |
| `action_open_pay()` | officer; the wizard for the `approved` records of `self`; `UserError` *No approved advance is selected.* without one |
| `_l10n_vn_mark_paid(paid_date)` | officer; every record `approved`, else `UserError` *Only an approved advance is marked as paid.*; writes `state` `paid`, `paid_date` |
| `action_cancel()` | D11: officer for `draft` and `approved`; `paid` needs the reviewer and no settlement on a `done` payslip (*This advance is already settled on a payslip.*); `cancelled` refused |

### `l10n_vn.payroll.advance.settlement` — `models/l10n_vn_payroll_advance.py`

`_description = "Salary Advance Settlement"`, `_order = "advance_id, id"`.

| Field | Type | Attributes |
|---|---|---|
| `advance_id` | Many2one | required, `ondelete="restrict"`, index |
| `payslip_id` | Many2one `hr.payslip` | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `advance_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `amount` | Monetary | |
| `payslip_state` | Selection | related `payslip_id.state`, string *Payslip status* |

### `l10n_vn.payroll.advance.batch` — `models/l10n_vn_payroll_advance_batch.py`

`_description = "Salary Advance Batch"`, `_order = "date desc, id desc"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required, stored editable compute with `precompute=True`, depends `date`: keeps a name, else *Advances %(date)s* |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `date` | Date | required, string *Requested Payment Date*, default today |
| `reason` | Char | required |
| `pay_group` | Selection | string *Pay Group*, the selection of `hr.employee.l10n_vn_pay_group` |
| `department_ids` | Many2many `hr.department` | relation `l10n_vn_advance_batch_department_rel`, string *Departments* |
| `amount_mode` | Selection | `fixed` *Fixed Amount*, `share` *Share of Monthly Amount*; required, default `fixed` |
| `fixed_amount` | Monetary | |
| `share` | Float | |
| `round_to` | Integer | string *Round Down To*, default 1000 |
| `advance_ids` | One2many `l10n_vn.payroll.advance` | `batch_id`, string *Advances* |
| `amount_total` | Monetary | stored compute: the sum of the lines not cancelled |
| `state` | Selection | stored compute from the lines, `draft`, `approved`, `paid`, `cancelled`: `draft` without lines or with a draft line; else `approved` with an approved line; else `paid` with a paid line; else `cancelled` |

| Method | Behaviour |
|---|---|
| `unlink` | `UserError` *Only a batch of draft advances can be deleted.* unless every line is draft; the lines are deleted with it |
| `_l10n_vn_employees()` | D9, as superuser: active employees of the company, `pay_group` and `department_id child_of department_ids` when set, with an eligible main contract |
| `action_generate()` | officer; state `draft`, else `UserError`; `fixed_amount` > 0 or `share` > 0 by mode, else `UserError` *Enter the amount or share of the batch.*; adds a line per eligible employee without one in the batch (D9) |
| `action_approve()` | `advance_ids` in `draft`: `action_approve()` |
| `action_open_pay()` | `advance_ids.action_open_pay()` |
| `action_cancel()` | `advance_ids` in `draft` or `approved`: `action_cancel()` |

### Step 1.1 changes

**`l10n_vn.payroll.advance`**

| Field | Type | Attributes |
|---|---|---|
| `days_worked` | Float | `(16, 4)`, in `_compute_limit`, string *Days Worked to Date* (D14) |
| `earned_amount` | Monetary | in `_compute_limit`, string *Earned to Date* (D14) |
| `eligible` | Boolean | in `_compute_limit`, string *Eligible* (D16) |
| `limit_at_approval` | Monetary | readonly, `copy=False`, string *Limit at Approval* (D15); added to `CONTROLLED` |

`_compute_limit` gives every figure 0 and `eligible` False on a `UserError`; `over_limit` = `eligible`, `amount` > `limit_left` and the level not `off`.

| Method | Behaviour |
|---|---|
| `_l10n_vn_param(code, company, date)` | `@api.model`: the strict reader, as superuser |
| `_l10n_vn_days_worked_of(employee, date)` | `@api.model`, D14 |
| `_l10n_vn_earned_from(monthly, days, company, date)` | `@api.model`, D14: 0 without days |
| `_l10n_vn_earned_of(employee, company, date)` | `@api.model`, D14 |
| `_l10n_vn_pay_groups(company, date)` | `@api.model`, D16: the set of pay groups the parameter lists; raises the strict reader's `UserError` without it |
| `_l10n_vn_eligible_of(employee, company, date)` | `@api.model`, D16 |
| `_l10n_vn_limit_left()` | `_l10n_vn_left_from(_l10n_vn_earned_of(…))` |
| `_l10n_vn_left_from(earned)` | D14: share × earned less the month's other advances, rounded, at least 0 |

`_compute_limit` reads the monthly amount and days worked once and derives earned and left from them.
| `action_approve()` | first refuses the ineligible records together, *Not in a pay group eligible for advances: %(employees)s.*, then D3 as before; writes `limit_at_approval` with the state |

**`l10n_vn.payroll.advance.batch`**

| Method | Behaviour |
|---|---|
| `_l10n_vn_employees()` | also leaves out the employees `_l10n_vn_eligible_of` refuses |
| `_l10n_vn_amount_for(employee)` | mode `share`: `share` × `_l10n_vn_earned_of`, then rounded as before |

**Views:** the advance form shows `eligible`, `days_worked`, `earned_amount` before `monthly_amount`, and `limit_at_approval` after `approved_at`; the batch's advance list shows `eligible`, `days_worked` and `earned_amount`, with `decoration-danger="not eligible and state == 'draft'"`.

### Step 1.2 changes

**Manifest:** `depends` unchanged; needs `l10n_vn_payroll` 18.0.1.2.0 (step 12).

| Where | Change |
|---|---|
| `l10n_vn.payroll.advance._l10n_vn_eligible_of(employee, company, date)` | the pay group of `employee._l10n_vn_period_contracts(first, last)[-1:]` for the month of `date` (D18) |
| `l10n_vn.payroll.advance.batch.pay_group` | selection from `hr.contract.l10n_vn_pay_group` |
| `l10n_vn.payroll.advance.batch._l10n_vn_employees()` | the domain no longer filters the pay group; an employee is kept when the main contract's group is in the eligible list and, when `pay_group` is set, equal to it |

### `hr.payslip` — `models/hr_payslip.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_advance_settlement_ids` | One2many `l10n_vn.payroll.advance.settlement` | `payslip_id`, string *Advance Settlements*, readonly |

| Method | Behaviour |
|---|---|
| `_l10n_vn_advances()` | D7: a list of `{"id", "amount"}`, `amount` an `int` above 0 |
| `_l10n_vn_prepare_one(builder, by_key)` | `super()`; the payslip's settlements replaced, as superuser, by one per entry of the snapshot's `advances` with `settled` above 0 |
| `_l10n_vn_record_stop(code, message)` | `super()`; the payslip's settlements removed |

### `hr.payslip.run` — `models/hr_payslip_run.py`

| Method | Behaviour |
|---|---|
| `_l10n_vn_check_advances()` | D8: for each `reviewed` run of a period, its payslips with a snapshot, comparing `(id, amount)` of the snapshot's `advances` with `_l10n_vn_advances()`; `UserError` *The advances of %(employees)s changed after the run was calculated; calculate it again.* |
| `action_l10n_vn_approve()` | the approver group checked (`_l10n_vn_require`), `self.sudo()._l10n_vn_check_advances()`, then `super()` |

### `l10n_vn.payroll.advance.pay` — `wizards/l10n_vn_payroll_advance_pay.py`

`TransientModel`, `_description = "Mark Salary Advances as Paid"`.

| Field | Type | Attributes |
|---|---|---|
| `advance_ids` | Many2many `l10n_vn.payroll.advance` | required, relation `l10n_vn_advance_pay_rel` |
| `paid_date` | Date | required, string *Payment Date*, default today |
| `advance_count`, `amount_total` | Integer, Monetary | non-stored computes, shown in the form |
| `currency_id` | Many2one | related to the first advance's currency |

`action_confirm()`: `advance_ids._l10n_vn_mark_paid(paid_date)`.

## Views

### `views/l10n_vn_payroll_advance_views.xml`

| Record | Content |
|---|---|
| `l10n_vn_payroll_advance_view_list` | header buttons on the selection: *Approve* (`action_approve`, reviewer), *Mark as Paid* (`action_open_pay`, officer), *Cancel* (`action_cancel`, officer). Columns `employee_id`, `date`, `amount`, `reason`, `batch_id` (optional), `over_limit` (optional), `limit_note` (optional), `paid_date`, `settled_amount`, `balance`, `state` as badge; `decoration-warning="over_limit and state == 'draft'"` |
| `l10n_vn_payroll_advance_view_form` | header: *Approve* (`draft`, reviewer), *Mark as Paid* (`approved`, officer), *Cancel* (`draft` or `approved`, officer; `paid`, reviewer), statusbar `draft,approved,paid`. Left group `employee_id`, `date`, `amount`, `reason`, `batch_id`; right group `monthly_amount`, `limit_left`, `over_limit`, `limit_note`, `approved_by`, `approved_at`, `paid_date`, `settled_amount`, `balance`, `company_id` (multi-company). Fields of the left group and `limit_note` readonly outside `draft`. Page *Settlements*: `payslip_id`, `payslip_state`, `amount` |
| `l10n_vn_payroll_advance_view_search` | `employee_id`, `batch_id`, `reason`; filters *Draft*, *To Pay* (`approved`), *Open Balance* (`paid` and `balance` > 0); group by employee, batch, state, month of `date` |
| `l10n_vn_payroll_advance_action` | *Salary Advances*, `list,form` |

### `views/l10n_vn_payroll_advance_batch_views.xml`

| Record | Content |
|---|---|
| `l10n_vn_payroll_advance_batch_view_list` | `name`, `date`, `reason`, `amount_total`, `state` as badge |
| `l10n_vn_payroll_advance_batch_view_form` | header: *Generate* (`draft`, officer), *Approve* (`draft`, reviewer), *Mark as Paid* (`approved`, officer), *Cancel* (`draft` or `approved`, officer), statusbar `draft,approved,paid`. Groups: `name`, `date` and `reason` (readonly once there are lines), `company_id`; `pay_group`, `department_ids`, `amount_mode`, `fixed_amount` (mode `fixed`), `share` as percentage and `round_to` (mode `share`); these readonly outside `draft`. Page *Advances*: `advance_ids` as an editable list, `employee_id`, `amount`, `monthly_amount`, `limit_left`, `over_limit`, `limit_note`, `state`, with the employee, amount and note readonly outside `draft`, `decoration-warning="over_limit and state == 'draft'"`. `amount_total` below |
| `l10n_vn_payroll_advance_batch_action` | *Advance Batches*, `list,form` |

### `wizards/l10n_vn_payroll_advance_pay_views.xml`

Form: `advance_count`, `amount_total`, `paid_date`; footer *Mark as Paid* (`action_confirm`), *Cancel*.

### `views/menus.xml`

Under `l10n_vn_payroll.menu_l10n_vn_payroll_inputs_root`: *Salary Advances* (sequence 8), *Advance Batches* (sequence 9).

## Step 2: payment lists

### Changes to the module

| Where | Change |
|---|---|
| `__manifest__.py` | `depends` adds `excel_import_export` (already a dependency of `l10n_vn_payroll`, now used directly); `data` adds `views/l10n_vn_payroll_payment_views.xml`, `wizards/l10n_vn_payroll_payment_pay_views.xml`, `report/l10n_vn_payroll_cash_list.xml`, `data/l10n_vn_payroll_payment_templates.xml`, and drops `wizards/l10n_vn_payroll_advance_pay_views.xml` |
| folders | new `models/l10n_vn_payroll_payment.py`, `wizards/l10n_vn_payroll_payment_pay.py` and its view, `views/l10n_vn_payroll_payment_views.xml`, `report/l10n_vn_payroll_cash_list.xml`, `data/l10n_vn_payroll_payment_templates.xml`, `templates/bank_transfer.xlsx` (a copy of the template file of Peter's *Export Payslip Batch*), `tests/test_payment.py`; `wizards/l10n_vn_payroll_advance_pay.py` and its view removed |
| `security/ir.model.access.csv` | `access_payment_user`, `access_payment_line_user` (officer, 1 1 1 1); `access_payment_reader`, `access_payment_approver`, `access_payment_line_reader`, `access_payment_line_approver` (read); `access_payment_pay_user` (officer, 1 1 1 1); `access_advance_pay_user` removed |
| `security/l10n_vn_payroll_payment_security.xml` | `rule_payment_company`, `rule_payment_line_company`, as the others |
| `views/menus.xml` | *Payment Lists* under *Monthly Inputs*, sequence 10 |
| `version` | `18.0.1.1.0` |

### `l10n_vn.payroll.payment` — `models/l10n_vn_payroll_payment.py`

`_description = "Payroll Payment List"`, `_inherit = ["mail.thread"]`, `_order = "date desc, id desc"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required |
| `kind` | Selection | `payroll` *Payroll*, `advance` *Advances*; required, readonly |
| `run_id` | Many2one `hr.payslip.run` | readonly, `ondelete="restrict"`, index; SQL `unique(run_id)` |
| `company_id` | Many2one `res.company` | required, readonly |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `date` | Date | required, string *Payment Date Requested*, default today; the file's value date |
| `company_bank_id` | Many2one `res.partner.bank` | string *Paying Account*, domain the company's partner's accounts; default the first of them (`sequence`, `id`) |
| `line_ids` | One2many `l10n_vn.payroll.payment.line` | `payment_id` |
| `transfer_line_ids`, `cash_line_ids` | One2many `l10n_vn.payroll.payment.line` | non-stored computes: the lines of each method, in line order |
| `amount_transfer`, `amount_cash`, `amount_total` | Monetary | stored computes over the lines |
| `state` | Selection | stored compute: `to_pay` *To Pay*, `paid` *Paid* when there are lines and all are paid; depends `line_ids.state` |

| Method | Behaviour |
|---|---|
| `_l10n_vn_from_run(run)` | `@api.model`, as superuser: D20; the list's `name` the run's, `date` today; lines in employee name order; returns the list or an empty recordset |
| `_l10n_vn_from_advances(advances, name)` | `@api.model`: D21 for the advances `approved` and without a line; `UserError` *No approved advance left to pay.* without one |
| `action_transfer_file()` | officer; D23: `xlsx.export.export_xlsx` with `l10n_vn_payroll_payment.xlsx_bank_transfer`, the file attached to the list (`res_model`, `res_id`), named *%(name)s - transfer.xlsx*; returns an `ir.actions.act_url` downloading it. `UserError` *There is no transfer to pay in this list.* / *No bank account on the transfers of %(employees)s.* |
| `action_print_cash_list()` | the report `action_report_l10n_vn_cash_list`; `UserError` *There is no cash payment in this list.* |
| `action_open_pay_transfer()`, `action_open_pay_cash()` | officer; the wizard with the list, the method and its unpaid lines; `UserError` *Nothing of this kind is left to pay.* |
| `_l10n_vn_after_paid()` | for a `paid` list with a run in `approved`: the run's `state` `paid`, as superuser |
| `unlink` | D26: `UserError` *A run's payment list cannot be deleted.* / *A list with paid lines cannot be deleted.* |

### `l10n_vn.payroll.payment.line` — `models/l10n_vn_payroll_payment.py`

`_description = "Payroll Payment Line"`, `_order = "payment_id, method, sequence, id"`.

| Field | Type | Attributes |
|---|---|---|
| `payment_id` | Many2one | required, `ondelete="cascade"`, index |
| `sequence` | Integer | the creation order |
| `number` | Integer | non-stored compute: the position among the list's lines of the same method, from 1 |
| `payslip_id` | Many2one `hr.payslip` | readonly, `ondelete="restrict"`, index |
| `advance_id` | Many2one `l10n_vn.payroll.advance` | readonly, `ondelete="restrict"`, index |
| `employee_id` | Many2one `hr.employee` | required, readonly |
| `company_id` | Many2one | related `payment_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `amount` | Monetary | required, readonly |
| `method` | Selection | `transfer` *Transfer*, `cash` *Cash*; required, readonly |
| `bank_account_id` | Many2one `res.partner.bank` | domain the employee's contact's accounts (D22) |
| `state` | Selection | `to_pay` *To Pay*, `paid` *Paid*; required, default `to_pay`, readonly |
| `paid_date` | Date | readonly |

SQL: `one_source`: `CHECK((payslip_id IS NULL) != (advance_id IS NULL))`, *A payment line pays one payslip or one advance.*

| Method | Behaviour |
|---|---|
| `write` | unless superuser: `bank_account_id` only on a line `to_pay`, else `UserError` *A paid line does not change.* |
| `_l10n_vn_mark_paid(paid_date)` | officer (`l10n_vn.payroll.advance._l10n_vn_require`); every line `to_pay`, else `UserError` *Only an unpaid line is marked as paid.*; as superuser writes `paid` and `paid_date`, calls `advance_id._l10n_vn_mark_paid(paid_date)` for advance lines, then `payment_id._l10n_vn_after_paid()` (D25, D27) |

### `l10n_vn.payroll.payment.pay` — `wizards/l10n_vn_payroll_payment_pay.py`

`TransientModel`, `_description = "Mark Payroll Payments as Paid"`: `payment_id` (Many2one, required), `method` (Selection as the line's, required), `line_ids` (Many2many lines, relation `l10n_vn_payment_pay_line_rel`, required; domain the list's unpaid lines of the method), `paid_date` (Date, required, default today), `amount_total` (non-stored compute). `action_confirm()`: `line_ids._l10n_vn_mark_paid(paid_date)`.

### Changes to `l10n_vn.payroll.advance` and its batch

| Where | Change |
|---|---|
| advance fields | `payment_line_ids` One2many (`advance_id`, readonly); `payment_id` non-stored compute, the list of its line |
| `action_open_pay()` | removed with the wizard `l10n_vn.payroll.advance.pay` |
| `action_create_payment()` (new) | officer; `_l10n_vn_from_advances(self, name)` with *Advances %(date)s* (today); returns the new list's form |
| `_l10n_vn_mark_paid(paid_date)` | unchanged; called by the payment line |
| `action_cancel()` | an approved advance's unpaid line is deleted, as superuser (D26); an advance on a paid line is `paid` and follows the paid rule |
| batch `action_open_pay()` | replaced by `action_create_payment()`: `_l10n_vn_from_advances(advance_ids, name)` with the batch's name |
| views | the advance list's header button *Create Payment List* (officer) instead of *Mark as Paid*; the form's *Mark as Paid* removed, `payment_id` shown after `paid_date`; the batch's *Mark as Paid* replaced by *Create Payment List* (state `approved`) |

### Changes to `hr.payslip.run` — `models/hr_payslip_run.py`

| Field or method | Behaviour |
|---|---|
| `l10n_vn_payment_ids` | One2many `l10n_vn.payroll.payment`, `run_id`, readonly |
| `action_l10n_vn_approve()` | after `super()`, for each run now `approved` without a list: `_l10n_vn_from_run(run)` (D20) |
| `action_l10n_vn_mark_paid()` | for runs with a list: the officer group checked (`AccessError` otherwise), each run `approved` (*Only an approved run is marked as paid.*), their lines still `to_pay` marked paid today through `_l10n_vn_mark_paid` as the user, then `_l10n_vn_after_paid()`; the other runs go to `super()` |
| `action_open_l10n_vn_payment()` | the run's list in its form |
| view | a smart button *Payment List* when the run has one; the engine's *Mark as Paid* hidden for a run with a list |

### Views — `views/l10n_vn_payroll_payment_views.xml`

| Record | Content |
|---|---|
| list | `name`, `kind`, `date`, `amount_transfer`, `amount_cash`, `amount_total`, `state` as badge |
| form | header: *Transfer File*, *Print Cash List*, *Mark Transfers as Paid*, *Mark Cash as Paid* (officer; the pay buttons while there are unpaid lines of the method), statusbar `to_pay,paid`. Fields `name`, `kind`, `run_id`, `date`, `company_bank_id` (editable while `to_pay`), the three totals. Page *Payments*: `line_ids` editable without create or delete — `number`, `employee_id`, `method`, `bank_account_id` (readonly when paid), `amount` (sum), `state`, `paid_date`, `payslip_id` and `advance_id` optional. Chatter, which shows the files made |
| search | `name`, `run_id`; filters *To Pay*, *Payroll*, *Advances* |
| action | *Payment Lists*, `list,form` |

Wizard form: `method` (readonly), `line_ids` as a list (`employee_id`, `bank_account_id`, `amount`) where lines can be removed, `amount_total`, `paid_date`; footer *Mark as Paid*, *Cancel*.

### Data — `data/l10n_vn_payroll_payment_templates.xml`

`noupdate="1"`: `xlsx_bank_transfer`, *Bank Transfer*, `res_model` `l10n_vn.payroll.payment`, `fname` `bank_transfer.xlsx`, `datas` from `templates/bank_transfer.xlsx`, with a `sheet` line (`1`), a `row` line on `transfer_line_ids` and these data cells in row 2:

| Cell | Header (Peter's) | Field | Condition |
|---|---|---|---|
| A2 | Số thứ tự (No.) | `number` | |
| B2 | Tên nhân viên | `employee_id.name` | |
| C2 | Bộ phận | `employee_id.department_id.name` | |
| D2 | Chức vụ | `employee_id.job_id.name` | |
| E2 | Tài khoản nguồn (Debit Acc) | `payment_id.company_bank_id.acc_number` | |
| F2 | Tài khoản đích (Credit Acc) | `bank_account_id.acc_number` | |
| G2 | Tên người thụ hưởng (Ben Name) | `bank_account_id.acc_holder_name` | `${value or object.employee_id.name}` |
| H2 | Số tiền (Amount) | `amount` | |
| I2 | Tên ngân hàng đích | `bank_account_id.bank_id.name` | |
| J2 | Mã Ngân hàng (Bank Code/CITAD) | `bank_account_id.bank_id.bic` | |
| K2 | Nội dung (Remark) | — | empty, as Peter's |
| L2 | Loại phí (Fee Type) | `id` | `${"OUR"}` |
| M2 | Ngày hiệu lực (Value Date) | `payment_id.date` | |

### Report — `report/l10n_vn_payroll_cash_list.xml`

`action_report_l10n_vn_cash_list`, QWeb PDF on `l10n_vn.payroll.payment`, A4, `web.external_layout`, officer group. Title *DANH SÁCH CHI LƯƠNG BẰNG TIỀN MẶT* for `payroll`, *DANH SÁCH CHI TẠM ỨNG LƯƠNG BẰNG TIỀN MẶT* for `advance`, with English beneath as in the payslip; the list's name and payment date. Columns: STT, Mã NV (`identification_id`), Họ tên, Bộ phận, Số tiền, Ký nhận; a total row; signatures *Người lập biểu*, *Kế toán trưởng*, *Giám đốc*.

### Step 2 tests — `tests/test_payment.py`, `TestPayment(AdvanceCase)`

| Test | Proves |
|---|---|
| `test_run_list_at_approval` | approving the run makes one list of kind `payroll`: a line per payslip, amount its to pay, `transfer`, the employee's bank account |
| `test_cash_and_nothing_to_pay` | Bao on a `CASUAL` contract: a `cash` line without bank account; Alice with a paid advance above her net: no line |
| `test_transfer_file` | the file attached to the list; row 2 holds 1, Alice's name, the paying account, her account, her to pay, `OUR` and the date; the cash line is not in it |
| `test_transfer_file_needs_bank` | a transfer line whose account was cleared: refused naming the employee |
| `test_mark_paid_by_method` | transfers paid: their lines `paid` with the date, the list still `to_pay`, the run `approved`; cash paid: the list `paid`, the run `paid` |
| `test_returned_transfer` | one line removed from the wizard stays `to_pay`; paid later, the list becomes `paid` |
| `test_run_button_pays_the_rest` | Alice's transfer paid on 20 October through the list; the reader's *Mark as Paid* on the run: `AccessError`; the officer's pays Bao's line today, keeps Alice's date, and the run is `paid` |
| `test_cash_list_report` | the report's HTML holds the cash line's employee and amount, and the title for `payroll` |
| `test_advance_list` | approved advances give an advance list; a second call has nothing left; paying it makes the advances `paid` with the date and their batch `paid` |
| `test_cancel_removes_line` | cancelling an approved advance on a list deletes its unpaid line |
| `test_roles` | the reader reads the list and cannot mark it paid; the officer can |
| `test_unlink` | an advance list without paid lines is deleted and its advances can be listed again; a run's list and a list with a paid line are refused |

`test_advance.test_mark_paid` and `test_batch.test_approve_and_pay_together` pay through a payment list instead of the removed wizard.

**Expected count from step 2:** 35 + 12 = 47 tests in this module.

## Readme

`readme/DESCRIPTION.md`: the first paragraph of this document.

## Change to `l10n_vn_payroll_garment` (its step 7)

| Where | Change |
|---|---|
| `models/garment_scheme.py`, `PARAMETERS` | adds `("vn.policy.advance_max_share", "Advance limit, share of the monthly amount", "float", "0.5")` after `vn.policy.net_change` |
| `__manifest__.py` | version `18.0.1.3.0` |
| `tests/test_load.py` | `TOTAL = 9 + 3 + 4 + 36 + 4 + 1 + 36` (93) |
| `docs/modules/l10n_vn_payroll_garment.md` | step 7 in the table, the parameter in `PARAMETERS`, divergence 4 without `advance_max_share`, the load total in *Expected count* |

## Change to `l10n_vn_payroll_garment` (its step 8, with step 1.1)

| Where | Change |
|---|---|
| `models/garment_scheme.py`, `PARAMETERS` | adds `("vn.policy.advance_pay_groups", "Pay groups eligible for advances", "string", "worker")` after `vn.policy.advance_max_share` |
| `__manifest__.py` | version `18.0.1.4.0` |
| `tests/test_load.py` | `TOTAL = 10 + 3 + 4 + 36 + 4 + 1 + 36` (94); `test_load_creates` reads `vn.policy.advance_pay_groups` = `worker` |
| `docs/modules/l10n_vn_payroll_garment.md` | step 8 in the table, the parameter in `PARAMETERS`, the load total |

## Tests

All `@tagged("post_install", "-at_install")`. Figures from the acceptance cases come from the engine's
`acceptance_cases.json`.

### `tests/common.py`

| Class | Content |
|---|---|
| `AdvanceMixin` | `_advance(employee, amount, date=D(2026, 10, 15), **values)` creates a draft advance as the fixtures' superuser; `_paid_advance(employee, amount, paid_date=D(2026, 10, 15), **values)` creates one in `paid` |
| `AdvanceCase(AdvanceMixin, RunCase)` | `RunCase` from `odoo.addons.l10n_vn_payroll.tests.run_common`, holding no test methods; `setUpClass` adds `vn.policy.advance_max_share` 0.5 from 2026-01-01. Alice and Bao earn 4,500,000, so the limit is 2,250,000 |

### `tests/test_advance.py` — `TestAdvance(AdvanceCase)`

| Test | Proves |
|---|---|
| `test_limit_figures` | Alice with `skill` 1,500,000 added, plus a `travel` line with its component moved to section `other` and a `daily` line: monthly amount 6,000,000, limit left 3,000,000 |
| `test_other_advances_reduce_limit` | an approved and a paid advance of the month reduce it; a draft, a cancelled and another month's do not |
| `test_within_limit` | the reviewer approves without a note; `approved_by` and `approved_at` set |
| `test_above_limit_needs_note` | TC-F16: refused naming the employee, approved once `limit_note` is written |
| `test_level_off` | `vn.check.advance_limit` `off`: `over_limit` False, approved without a note |
| `test_level_error` | `error`: refused even with a note |
| `test_missing_parameter` | without the parameter the figures read 0, and approval raises |
| `test_only_reviewer_approves` | the officer gets `AccessError`; the reviewer succeeds |
| `test_controlled_fields` | the officer edits a draft's amount, and gets `AccessError` writing `state` |
| `test_frozen_after_draft` | an approved advance refuses a new amount for the officer |
| `test_mark_paid` | the officer's wizard sets `paid` and `paid_date`; a draft is refused |
| `test_cancel` | officer on draft and approved; on a paid one `AccessError`, the reviewer succeeds; a cancelled one is refused |
| `test_unlink_draft_only` | a draft goes, an approved one is refused |
| `test_read_roles` | reader and approver read and cannot create; the officer creates |
| `test_company_rule` | an advance of another company is invisible to the officer |

### `tests/test_settlement.py`

**`TestSettlement(AdvanceCase)`**

| Test | Proves |
|---|---|
| `test_oldest_first` | 3,000,000 paid 1 October and 3,000,000 paid 10 October on a net of 4,027,500: 3,000,000 and 1,027,500, in that order |
| `test_paid_after_month_end_waits` | `paid_date` 2026-11-05 is not settled on October |
| `test_approved_not_paid_waits` | an approved advance is not settled |
| `test_recalculate_replaces` | calculating twice leaves one settlement |
| `test_stop_clears` | a payslip whose input was deleted stops and has no settlement |
| `test_balance_moves_at_approval` | after calculation `balance` is unchanged; after run approval it is 0 |
| `test_carried_to_next_payslip` | the excess over net is settled on a second payslip once the first is `done` |
| `test_run_approval_rereads_advances` | an advance paid after review refuses approval; calculating and reviewing again passes and settles it |
| `test_cancel_refused_once_settled` | the reviewer cannot cancel an advance settled on a `done` payslip |

**`TestAdvanceAcceptance(AdvanceMixin, GroupGCases, PayslipCase)`**, no inherited tests collected:

| Test | Proves |
|---|---|
| `test_g14_settled` | TC-G14: a paid advance of 1,500,000; `_run` with `to_pay` checked, `ADVANCE` and `l10n_vn_advance` equal the case's `settled` |
| `test_g15_carried` | TC-G15: a paid advance of 2,000,000; `to_pay` 0, `advance_carried` reported, `balance` = 2,000,000 − the case's `settled` once `done` |

### `tests/test_batch.py` — `TestBatch(AdvanceCase)`

| Test | Proves |
|---|---|
| `test_generate_fixed` | pay group `worker` selects Alice and not Bao (`office`); a second *Generate* adds nothing and keeps an edited amount |
| `test_generate_share` | share 0.33 of 4,500,000 with `round_to` 1000 gives 1,485,000; at `round_to` 100,000 gives 1,400,000 |
| `test_generate_eligible` | a contract ended before `date` and a contract on a non-Vietnamese structure give no line |
| `test_approve_and_pay_together` | the reviewer approves the batch, the officer marks it paid; lines and batch state follow |
| `test_over_limit_named` | a line above the limit stops the batch's approval and names the employee; with its note all pass |

### Step 1.1 changes to the tests

**`AdvanceCase`:** `setUpClass` also adds `vn.policy.advance_pay_groups` `worker` and a Monday–Saturday calendar of 8 hours (07:00–11:00, 12:00–16:00, `Asia/Ho_Chi_Minh`, as the engine's `InputCase`), with Odoo's tolerances 5 and 48 minutes. `setUp` gives Alice and Bao that calendar and timezone, pay group `worker`, and attendance 07:00–16:00 on every scheduled day from 1 to 15 October: 13 days. `_advance` defaults to 16 October, so the limit is 0.5 × 4,500,000 × 13 ÷ 26 = 1,125,000.

| Test | Change |
|---|---|
| `test_limit_figures` | days worked 13, monthly 6,000,000, earned 3,000,000, limit 1,500,000 |
| `test_earned_to_date` (new) | dated 8 October: 6 days, earned 1,038,462, limit 519,231; dated 1 October: 0 days, limit 0 |
| `test_other_advances_reduce_limit` | an approved 300,000 and a paid 200,000 leave 625,000 |
| `test_within_limit` | 1,000,000 approved; `limit_at_approval` 1,125,000 |
| `test_above_limit_needs_note` | 1,500,000 |
| `test_not_eligible` (new) | Bao in `office`, and an employee without pay group, are refused even with a note; Alice in the same call is not approved either |
| `test_eligible_at_zero_limit` (new) | dated 1 October, Alice needs a note and is approved with one |
| `TestBatch` | the batch dated 16 October; `test_generate_share` with share 0.5: 1,125,000 at `round_to` 1000, 1,100,000 at 100,000; `test_generate_eligible` also leaves out Bao in `office`; `test_approve_and_pay_together` at 1,000,000 each; `test_over_limit_named` at 1,500,000 |

**Expected count from step 1.1:** 34 tests in this module; `l10n_vn_payroll_garment` stays at 28.

### Step 1.2 changes to the tests

| Where | Change |
|---|---|
| `AdvanceCase.setUp` | the pay group `worker` written on `alice_contract` and `bao_contract` instead of the employees |
| `test_not_eligible`, `TestBatch` | pay groups written on the contracts (`bao_contract`, and the contracts `_hire` returns for Carl and Dan) |
| `test_eligibility_by_month` (new) | `alice_contract` ending 2026-10-31 and a new contract for Alice from 2026-11-01 in `office`: an advance dated 16 October is approved, one dated 16 November is refused as not eligible |

**Expected count from step 1.2:** 35 tests in this module.

**Expected count:** 31 tests in this module. `l10n_vn_payroll_garment` stays at 28, `l10n_vn_payroll` at 243.
