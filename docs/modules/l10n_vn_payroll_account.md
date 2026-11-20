# l10n_vn_payroll_account

Accounting for Vietnamese payroll runs: one journal entry per approved run for the payslips whose participant
type is posted, an entry for each payment made from a payment list, and each employee's 3341 reconciled so that
its open residual is what remains to pay. The accounts are configuration: department cost groups, an account on
each pay component, and the company's payroll journal, payable account and payment journals.
Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.7.md` §22, §23.1 (PTD-13, PTD-24, PTD-27), on
`Payroll Requirements Specification v0.7.md` FR-44 and FR-77. Engine: `docs/modules/l10n_vn_payroll.md`;
payments: `docs/modules/l10n_vn_payroll_payment.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Cost groups on departments with a contract override; an account on each component; company settings; the run entry at approval; payment entries from *Mark as Paid*; 3341 reconciled per employee; the integrity check `posting`; the run's OCA journal defaulted to the payroll journal | done | 2026-11-20: `-i`, then `-u l10n_vn_payroll` with every payroll module, 334 post-tests (245 engine, 28 garment, 47 payment, 14 here), 0 failures. Two fixes came from the runs: the test fixture creates the payroll journal after loading the chart, which deletes a company's journals; and posting became a per-company switch, off by default (D11), after 40 tests of the other modules failed review with posting always on. UI deferred to the garment mapping (its step 4) |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §22.1: two component fields, `l10n_vn_debit` (`cost` / `payable` / `none`) and `l10n_vn_credit_account_id` | one field, `l10n_vn_account_id`, whose side follows the component's kind (D2) | The kind already says which side the component posts on; a second field could only contradict it |
| 2 | §22.1: the cost group set on the department | the department's or its nearest ancestor's, unless the contract names one (D4) | The garment company's production departments sit under *Production*; one group there covers them. Line leaders and production support in a sewing department are factory staff (6271), not direct labour, which a department alone cannot say |
| 3 | §22.1: the payroll journal on the company | also the default of the run's own *Salary Journal* (OCA `payroll_account`, required), which otherwise takes the first general journal — *Miscellaneous Operations* on the instance (D3) | One journal for the run, wherever it is read |

## Decisions

| # | Decision |
|---|---|
| D1 | **Accounts are configuration**, never codes in this module: department cost groups (`l10n_vn.payroll.cost.group`: code, name, expense account), an account on each pay component, and on the company the payroll journal, the payable account (3341), the bank journal for transfers and the cash journal for cash. The garment configuration maps them by account code (its step 4) |
| D2 | **What each component posts**, by its kind: an *earning* debits the payslip's cost group account (or the component's account when set) and credits 3341; a *deduction* debits 3341 and credits the component's account; an *employer* contribution debits the cost group account and credits the component's account; *total* and *info* components (`GROSS`, `NET`, `ADVANCE`, `TO_PAY`) post nothing. Damage compensation is a deduction like the others; the garment configuration credits it to 7110 *Thu nhập khác* (Peter, 2026-11-19) |
| D3 | **One entry per run at approval:** an `account.move` in the payroll journal, dated the period's last day, `ref` the run's name, linked to the run (`l10n_vn_move_id`) and posted, as superuser after the approval. Lines: expense debits summed by account and cost group; deduction and employer credits summed by account and the component register's partner; on 3341, per employee, one credit of gross pay and one debit per deduction component. The partner on 3341 is the employee's work contact. A run whose posted payslips give no line has no entry |
| D4 | **The cost group of a payslip:** its contract's `l10n_vn_cost_group_id` when set; else the first cost group found on the contract's department (else the employee's), then up its parents |
| D5 | **Only posted participants post:** a payslip posts when its contract's participant type is `posted`; a payment line when the participant type of the contract behind it is (the payslip's, or the main contract for the advance's month). `CASUAL` pay and its cash payments stay in payroll only (PTD-24, FR-77) |
| D6 | **Payments post from *Mark as Paid*:** paying payment lines (`l10n_vn.payroll.payment.line._l10n_vn_mark_paid`) posts, for the posted lines of each method, one entry in the bank journal (transfers) or the cash journal (cash), dated the payment date, `ref` the list's name: a debit of 3341 per line with the employee as partner, and one credit of the total to the journal's outstanding payments account (the account of its first outbound payment method line that has one; on the instance 1132 *Khoản chi chưa thanh toán*). The bank or cash statement line then reconciles that credit, as for any payment. Each line keeps its entry |
| D7 | **3341 reconciled per employee** after each entry this module posts: the employee's open 3341 lines on this module's entries (run entries and payment entries, marked on the move) are reconciled together. A run's gross credit thus meets its deductions, the employee's earlier advance payments and, at payday, the payment; the residual of 3341 per employee is what remains to pay, and an advance that net pay could not cover stays an open debit |
| D8 | **The check `posting`** (integrity, error, so review is blocked): on a payslip that posts, it names what posting would lack — the payroll journal, the payable account, a cost group or its account for the payslip, an account on a component with lines on the payslip — and any salary rule of the payslip's structure that carries an OCA account (`account_debit`, `account_credit`), since OCA's own posting would then add a second entry. Approval therefore does not fail on configuration. Payment journals are checked when a payment is marked (`UserError` naming the missing setting) |
| D9 | **OCA's posting stays silent:** our rules carry no accounts, so OCA `payroll_account`'s per-payslip entry gives no line and the payslip's `move_id` stays empty (`oca/payroll/payroll_account/models/hr_payslip.py:46-139`) |
| D11 | **Posting is switched on per company** (`l10n_vn_payroll_post`, *Post Payroll in Accounting*, off by default). Off: no `posting` check, no run entry, no payment entry; payroll and payments work as without this module (FR-77). On: D3–D8. The garment configuration switches it on for the garment company (its step 4). Found by the first full run: with the module installed and posting always on, every company without accounts failed review, including the engine's and payment module's test companies (40 tests) |
| D10 | **No reversal:** an approved run never goes back (engine D76) and a paid line never changes (payment D25); a correction is made in a later month or by the accountant's own entry |

## Folder structure

```
l10n_vn_payroll_account/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── account_move.py
│   ├── hr_contract.py
│   ├── hr_department.py
│   ├── hr_payslip.py
│   ├── hr_payslip_run.py
│   ├── l10n_vn_payroll_check.py
│   ├── l10n_vn_payroll_component.py
│   ├── l10n_vn_payroll_cost_group.py
│   ├── l10n_vn_payroll_payment.py
│   ├── res_company.py
│   └── res_config_settings.py
├── data/
│   └── l10n_vn_payroll_account_checks.xml
├── security/
│   ├── ir.model.access.csv
│   └── l10n_vn_payroll_account_security.xml
├── views/
│   ├── l10n_vn_payroll_cost_group_views.xml
│   ├── hr_department_views.xml
│   ├── hr_contract_views.xml
│   ├── l10n_vn_payroll_component_views.xml
│   ├── hr_payslip_run_views.xml
│   ├── l10n_vn_payroll_payment_views.xml
│   ├── res_config_settings_views.xml
│   └── menus.xml
├── readme/
│   └── DESCRIPTION.md
└── tests/
    ├── __init__.py
    ├── common.py
    ├── test_run_entry.py
    └── test_payment_entry.py
```

## Manifest

| Key | Value |
|---|---|
| `name` | Vietnam - Payroll Accounting |
| `summary` | Journal entries for Vietnamese payroll runs and their payments, 3341 reconciled per employee |
| `version` | `18.0.1.0.0` |
| `author`, `website`, `license`, `category`, `countries` | as `l10n_vn_payroll` |
| `depends` | `l10n_vn_payroll_payment`, `payroll_account` |
| `data` | `security/l10n_vn_payroll_account_security.xml`, `security/ir.model.access.csv`, `data/l10n_vn_payroll_account_checks.xml`, the views in the order of the folder, `views/menus.xml` last |
| `installable` | True |

## Python packages

`__init__.py` imports `models`; `models/__init__.py` imports every model file.

## Access

### `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_cost_group_user` | `model_l10n_vn_payroll_cost_group` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_cost_group_reader` | `model_l10n_vn_payroll_cost_group` | `l10n_vn_payroll.group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_cost_group_manager` | `model_l10n_vn_payroll_cost_group` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_cost_group_account` | `model_l10n_vn_payroll_cost_group` | `account.group_account_manager` | 1 | 1 | 1 | 1 |

### `security/l10n_vn_payroll_account_security.xml`

`rule_cost_group_company`: global, `[('company_id', 'in', company_ids)]`.

Entries are created and reconciled as superuser after the step's own group check (approver, officer); the users need no accounting rights.

## Models

### `l10n_vn.payroll.cost.group` — `models/l10n_vn_payroll_cost_group.py`

`_description = "Payroll Cost Group"`, `_order = "code"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `expense_account_id` | Many2one `account.account` | required, string *Expense Account*, `check_company=True` |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `active` | Boolean | default True |

SQL: `code_company_unique`: `unique(code, company_id)`, *A cost group code is unique in a company.*

### `hr.department` — `models/hr_department.py`

| Field or method | Behaviour |
|---|---|
| `l10n_vn_cost_group_id` | Many2one `l10n_vn.payroll.cost.group`, string *Payroll Cost Group*, `check_company=True` |
| `_l10n_vn_cost_group()` | `ensure_one`: its cost group, else its parent's, up the tree; empty when none (D4) |

### `hr.contract` — `models/hr_contract.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_cost_group_id` | Many2one `l10n_vn.payroll.cost.group` | string *Payroll Cost Group*, help *Overrides the department's.*, `groups="payroll.group_payroll_user"`, `check_company=True`, `tracking=True` |

### `l10n_vn.payroll.component` — `models/l10n_vn_payroll_component.py`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_account_id` | Many2one `account.account` | string *Account*, `check_company=True`; help *Earnings: the expense account, when not the cost group's. Deductions and employer contributions: the account credited.* (D2) |

### `res.company` — `models/res_company.py`, and `res.config.settings`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_payroll_post` | Boolean | string *Post Payroll in Accounting* (D11) |
| `l10n_vn_payroll_journal_id` | Many2one `account.journal` | string *Payroll Journal*, domain `type = general` |
| `l10n_vn_payroll_payable_account_id` | Many2one `account.account` | string *Payroll Payable Account* |
| `l10n_vn_payroll_bank_journal_id` | Many2one `account.journal` | string *Payroll Bank Journal*, domain `type = bank` |
| `l10n_vn_payroll_cash_journal_id` | Many2one `account.journal` | string *Payroll Cash Journal*, domain `type = cash` |

`res.config.settings`: the same five, `related="company_id.…"`, `readonly=False`.

### `account.move` — `models/account_move.py`

| Field or method | Behaviour |
|---|---|
| `l10n_vn_payroll_run_id` | Many2one `hr.payslip.run`, readonly, index, `copy=False` |
| `l10n_vn_payroll_payment_id` | Many2one `l10n_vn.payroll.payment`, readonly, index, `copy=False` |

**`account.move.line`** (same file):

| Method | Behaviour |
|---|---|
| `_l10n_vn_payroll_reconcile(company, partners)` | `@api.model`, as superuser, D7: for each partner, its unreconciled posted lines on the company's payroll payable account among moves with either field set; `reconcile()` when they hold both a debit and a credit |

### `hr.payslip` — `models/hr_payslip.py`

| Method | Behaviour |
|---|---|
| `_l10n_vn_posts()` | `ensure_one`: False when the company does not post (D11); else a Vietnamese payslip whose contract's participant type is `posted` (D5) |
| `_l10n_vn_cost_group()` | `ensure_one`, D4 |
| `_l10n_vn_posting_lines()` | `ensure_one`: its payslip lines with a total whose component is an earning, deduction or employer contribution |
| `_l10n_vn_posting_problems()` | `ensure_one`: the list of what posting lacks (D8), each a short text naming the setting, department, component or salary rule |

### `hr.payslip.run` — `models/hr_payslip_run.py`

| Field or method | Behaviour |
|---|---|
| `l10n_vn_move_id` | Many2one `account.move`, string *Journal Entry*, readonly, `copy=False` |
| `create` | for values with `l10n_vn_period_id` and no `journal_id`: the period company's `l10n_vn_payroll_journal_id` when set (divergence 3) |
| `_onchange_l10n_vn_period_journal` | `@api.onchange("l10n_vn_period_id")`: the same in the form, where OCA's default is already filled |
| `action_l10n_vn_approve()` | `super()`, then `_l10n_vn_post()` on the runs now approved |
| `_l10n_vn_entry_lines()` | `ensure_one`: the line values of D3 from the run's payslips that post, in this order: expense debits, 3341 credits, 3341 debits, other credits; each with `name` *%(component)s %(month)s* or, on 3341, the employee's name and *Lương %(month)s* |
| `_l10n_vn_post()` | as superuser, per run without an entry: `UserError` naming the first problem when a payslip that posts has one (the review should already have stopped it); the move created from `_l10n_vn_entry_lines()`, posted, linked both ways (`l10n_vn_move_id`, `l10n_vn_payroll_run_id`); then `_l10n_vn_payroll_reconcile` for the employees' partners |
| `action_open_l10n_vn_move()` | the entry in its form |

### `l10n_vn.payroll.payment` and `.payment.line` — `models/l10n_vn_payroll_payment.py`

| Field or method | Behaviour |
|---|---|
| line `l10n_vn_move_id` | Many2one `account.move`, string *Journal Entry*, readonly, `copy=False` |
| line `_l10n_vn_posts()` | False when the list's company does not post (D11); else D5 for the line |
| line `_l10n_vn_mark_paid(paid_date)` | `super()`, then `_l10n_vn_post_payment(paid_date)` |
| line `_l10n_vn_post_payment(paid_date)` | as superuser, D6: for each list and method among the lines that post, the journal from the company (`UserError` *Set the payroll %(kind)s journal in Payroll settings.*), its outstanding account (`UserError` *Journal %(journal)s has no outstanding payments account.*), the move created, posted and linked (`l10n_vn_payroll_payment_id`, each line's `l10n_vn_move_id`); then `_l10n_vn_payroll_reconcile` for the lines' employees |
| list `l10n_vn_move_ids` | Many2many `account.move`, non-stored compute: the entries of its lines |

### `l10n_vn.payroll.check` — `models/l10n_vn_payroll_check.py`

| Finder | Behaviour |
|---|---|
| `_l10n_vn_find_posting(payslip, context)` | for a payslip that posts with problems: one finding, *Posting needs: %(problems)s.* (D8) |

## Data — `data/l10n_vn_payroll_account_checks.xml`

Not `noupdate`, as the engine's catalogue: `check_posting`, code `posting`, *Accounts for posting missing*, integrity, default `error`, sequence 75 (after `missing_ids`).

## Views

| File | Content |
|---|---|
| `l10n_vn_payroll_cost_group_views.xml` | list (editable: `code`, `name`, `expense_account_id`, `company_id` multi-company), search, action *Payroll Cost Groups* |
| `hr_department_views.xml` | the department form: `l10n_vn_cost_group_id` after `parent_id`, for payroll managers and account managers |
| `hr_contract_views.xml` | the contract's payroll group `l10n_vn_profile` (engine view): `l10n_vn_cost_group_id` after `l10n_vn_pay_group` |
| `l10n_vn_payroll_component_views.xml` | the component form: `l10n_vn_account_id`, hidden for kinds `total` and `info` |
| `hr_payslip_run_views.xml` | a smart button *Journal Entry* (`action_open_l10n_vn_move`) when `l10n_vn_move_id` is set |
| `l10n_vn_payroll_payment_views.xml` | the payment list's lines: `l10n_vn_move_id` as an optional column |
| `res_config_settings_views.xml` | in the payroll settings' *Accounting* block: a setting *Post Payroll in Accounting* with `l10n_vn_payroll_post`, and the four other fields beneath, shown when it is on |
| `menus.xml` | *Payroll Cost Groups* under the payroll configuration menu, sequence 35 |

## Readme

`readme/DESCRIPTION.md`: the first paragraph of this document.

## Tests

All `@tagged("post_install", "-at_install")`.

### `tests/common.py` — `AccountCase(AdvanceCase)`

`AdvanceCase` from `odoo.addons.l10n_vn_payroll_payment.tests.common`. `setUpClass` loads the Vietnamese chart in the test company (`account.chart.template.try_loading("vn", company, install_demo=False)`); `_account(code, account_type, reconcile=False)` finds the company's account with the code or creates it. Accounts: 3341 (payable, reconcile), 33831, 33841, 33861, 338811, 33821 (payable, reconcile), 33351 (current liability), 7110 (other income), 6220, 6421 (expense), 1132 (current asset, reconcile). Loading the chart deletes the company's journals, so the payroll journal is created after it. The company settings: posting on, that payroll journal, 3341, the chart's bank and cash journals, whose outbound payment method lines get 1132. Cost groups `DIRECT` (6220) on a department *Production* with a child *Sewing*, and `ADMIN` (6421) on *Administration*; Alice's contract in *Sewing*, Bao's in *Administration*. Component accounts: `EE_SI` and the three `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT` → 33831; `EE_HI`, `ER_HI` → 33841; `EE_UI`, `ER_UI` → 33861; `DUES` → 338811; `UNION_FEE` → 33821; `PIT` → 33351; `DAMAGE` → 7110.

### `tests/test_run_entry.py` — `TestRunEntry(AccountCase)`

| Test | Proves |
|---|---|
| `test_entry_at_approval` | approving a run posts one entry in the payroll journal, dated 2026-10-31, linked both ways and balanced; approved by the approver, who has no accounting rights |
| `test_lines_by_kind` | 6220 debited Alice's gross plus her employer contributions, 6421 Bao's; 3341 credited each one's gross with the employee as partner; one 3341 debit per deduction per employee; 33831 credited the employees' and employer's SI together |
| `test_residual_is_to_pay` | after approval each employee's open 3341 residual is a credit of their `l10n_vn_to_pay` |
| `test_cost_group_from_parent_and_contract` | Alice's *Sewing* has no group: *Production*'s applies; a contract override to `ADMIN` moves her expense to 6421 |
| `test_damage_to_its_account` | a damage decision deducted: 7110 credited, without partner |
| `test_casual_not_posted` | Bao on `CASUAL`: no line for him in the entry, and his cash payment later posts nothing |
| `test_posting_check` | without a cost group, without a component account, and without the payroll journal: a `posting` error naming each, and the run cannot be reviewed; a salary rule with an OCA account is named too |
| `test_posting_off` | the company's posting off, and no payroll journal: the run is approved with no `posting` result and no entry; its transfers are paid without an entry |
| `test_run_journal_default` | a new run of a period takes the payroll journal as its *Salary Journal* |

### `tests/test_payment_entry.py` — `TestPaymentEntry(AccountCase)`

| Test | Proves |
|---|---|
| `test_transfer_entry` | marking the run's transfers paid posts one entry in the bank journal, dated the payment date: a 3341 debit per employee and one 1132 credit of the total; each line linked; every 3341 line of the two employees reconciled, residual 0 |
| `test_cash_entry` | a posted participant type paid in cash: the cash journal |
| `test_advance_before_run` | an advance list paid on 16 October posts Dr 3341 / Cr 1132; after the run, the advance debit is reconciled with the gross credit and the residual is the amount to pay; payday leaves 0 |
| `test_carried_advance_open` | an advance above net: after the run, an open 3341 debit of the advance less net pay remains |
| `test_missing_journal` | without the bank journal setting: `UserError`, and no line is paid |

**Expected count:** 14 tests in this module. Installing it changes no other module's count; upgrading `l10n_vn_payroll` afterwards also runs these.
