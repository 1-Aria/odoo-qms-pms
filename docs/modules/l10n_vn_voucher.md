# l10n_vn_voucher

The shared layout of the Vietnamese printed vouchers: an A4 paper format, the QWeb blocks every form is
built from (record wrapper, copies, header, title box, dotted fields, amount in words, signatures), and
the helpers they read. Step 2 adds the blocks the order forms share (parties, order lines, totals, the
compact grouping); step 3 adds *Phiếu thu* and *Phiếu chi* from cash journal entries. The stock vouchers
live in `l10n_vn_voucher_stock`, the order forms in `l10n_vn_purchase_report` and `l10n_vn_sale_report`.
Design: `docs/Accounting/VN Vouchers — Design.md` (§4).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Paper format; QWeb blocks; `l10n_vn.voucher` helpers; `res.currency.l10n_vn_amount_to_words`; report stylesheet (design §4.1–4.3, §4.5). Installed together with `l10n_vn_voucher_stock` step 1, the first form that uses them | done | 2026-11-13, first run: `-i`, `exit=1`, 6 tests, 2 errors (`test_blocks_render`, `test_copies_render`): the signature cell's width, `t-att-style="'width: %.2f%%;' % (...)"`, reached Odoo with `%%` collapsed to `%`, and the formatting failed. Fixed with `table-layout: fixed` on the signature table and no computed width. Second run: `-u`, `exit=0`, 6 post-tests, 0 failures. UI checked as admin with `l10n_vn_voucher_stock` (its step 1) |
| 2 | Order-form blocks: `voucher_header` without form code or department, `voucher_party`, `voucher_order_lines`, `voucher_variant_grids`, `voucher_totals`; `l10n_vn.voucher._compact_rows`, `_numbered_rows`, `_date_short`, `_qty_text`; version `18.0.1.1.0` (design §6.2, §6.4; design step 3). Installed with `l10n_vn_purchase_report` step 1 | done | 2026-11-15: `-u`, `exit=0`, 10 post-tests, 0 failures. UI checked with the purchase and sales forms |
| 3 | Cash vouchers: fields on `account.move` and `account.journal`, the PT/PC series, *Phiếu thu* and *Phiếu chi* (design §4.4; design step 7); version `18.0.1.2.0` | done | 2026-11-17: `-u`, `exit=0`, 19 post-tests, 0 failures. UI check found that Odoo 18 lets hand-keyed entries use only *Miscellaneous* journals; cash entries come from the cash journal's transactions, which post on creation and keep their number when reconciled (D8, readme corrected). UI checked with transactions in *Cash* and *Petty Cash*: Phiếu chi and Phiếu thu numbered per journal, accounts after reconciliation, person override, repost keeping the number. Printing before reconciliation shows the suspense account in *Nợ/Có* (accepted, Peter 2026-11-17) |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §4.2: the blocks are QWeb templates | the logic they need — copy labels, date text, one-line address — is in an abstract model, `l10n_vn.voucher`, which the templates call through `env` | QWeb expressions stay one-liners and the logic is tested in Python |
| 2 | §4.2: a *Copies* block repeats the form once per copy | each form loops over `_copy_labels` itself and calls `voucher_page` once per copy (D6) | QWeb renders a `t-call`'s body once, before the call, with the caller's variables (`odoo/odoo/addons/base/models/ir_qweb.py:2200`): a block cannot repeat its caller's body with a different label each time |

## Decisions

| # | Decision |
|---|---|
| D1 | **Forms do not use the company's external layout.** Each form draws its own header (*Đơn vị*, *Mẫu số*); the record wrapper is the `article` div of `web.basic_layout` (`odoo/addons/web/views/report_templates.xml:861-868`) without its `web.html_container` call, so a report template wraps all records in one `web.html_container` and calls the form per record |
| D2 | **Forms print in Vietnamese:** a report template calls the form with `t-lang="'vi_VN'"`, which sets the language number widgets format with (`.` thousands, `,` decimals on this database), and the form starts with `o = o.with_context(lang="vi_VN")`, so names read through `o` come out in Vietnamese. `t-lang` alone changes only the rendering context (`odoo/odoo/addons/base/models/ir_qweb.py:258-266`) |
| D3 | **Font: DejaVu Serif,** installed in the image and covering Vietnamese. The default report font is not relied on |
| D4 | **Amounts in words are VND only,** rounded half-up to the đồng, read by `num2words(lang="vi")`, first letter capitalised, followed by *đồng* (design §4.3). Core's `amount_to_text` is not used: it capitalises every word and VND's label is *Dong* (`odoo/odoo/addons/base/models/res_currency.py:177-190`) |
| D5 | **A copy list is one label per line;** blank lines are ignored, an empty list gives one unlabelled copy (design §4.5) |
| D6 | **Each copy is a `div.page`** from `voucher_page`, inside the form's own loop over `_copy_labels` with `t-as="copy_label"`; every copy after the first (`copy_label_first` False) starts on a new page (`page-break-before: always`). Table rows and the signature block do not break across pages; table headers repeat |
| D7 | **A cash entry is a posted entry of a journal of type *cash*; its cash lines are those on the journal's own account** (`default_account_id`): 1110 for the garment company's *Cash* (CSH1), 1111 for *Petty Cash* (PCSH) on this database. All cash lines debit: *Phiếu thu*; all credit: *Phiếu chi*; both, or none: no voucher (design §4.4) (step 3) |
| D8 | **The kind and number are given in `_post`,** after `super()`, to the moves it returns. In the UI, cash entries come from the cash journal's transactions (statement lines): Odoo 18 lets an entry keyed in by hand use only a *general* journal (`account/models/account_move.py:875-882`, `:921-928`). Creating a transaction posts its entry (`account/models/account_bank_statement_line.py:435`); reconciling it in OCA `account_reconcile_oca` rewrites its lines and posts it again (`oca/account-reconcile/account_reconcile_oca/models/account_bank_statement_line.py:917`), which keeps the number. A number is kept when the entry is reset and posted again with the same kind; a changed kind takes a new number of the new kind, and the old one is not reused (step 3) |
| D9 | **The series are `ir.sequence` records on the journal,** created as superuser the first time the journal posts a voucher of that kind: `implementation` `no_gap`, `use_date_range` True (a range per year, created by the sequence itself), prefix `PT/%(range_year)s/` or `PC/%(range_year)s/`, padding 4, the journal's company. The number is drawn with `next_by_id(sequence_date=move.date)`. Two cash journals have separate series with the same prefix; *Quyển số* (the journal's name) tells them apart, and a number is unique per journal (SQL) (step 3) |
| D10 | **The person paying or receiving defaults, at print, to the partner of the other lines when they have exactly one;** the entry's own `l10n_vn_voucher_person` and `l10n_vn_voucher_address`, editable before and after posting (neither is a hashed field, `account/models/account_move.py:4066-4073`), win (step 3) |
| D11 | **The reason is the entry's `ref`,** else the label of its first cash line, where a transaction puts its label (`payment_ref`); transactions leave `ref` empty (step 3) |
| D12 | **Nợ and Có list the debit and the credit accounts of the entry's lines,** the cash account among them, each code once, sorted; when a side has several accounts, each prints with its amount, as `code: amount`, in the currency's format (`formatLang`, Vietnamese grouping). It always matches the posting (step 3) |

## Folder structure

```
l10n_vn_voucher/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_voucher.py
│   ├── res_currency.py
│   ├── account_journal.py                    # 3
│   └── account_move.py                       # 3
├── data/
│   └── report_paperformat.xml
├── report/
│   ├── l10n_vn_voucher_templates.xml
│   ├── l10n_vn_cash_voucher_templates.xml   # 3
│   └── l10n_vn_cash_voucher_reports.xml     # 3
├── views/                                   # 3
│   ├── account_journal_views.xml
│   └── account_move_views.xml
├── static/src/scss/
│   └── l10n_vn_voucher.scss
├── tests/
│   ├── __init__.py
│   ├── test_l10n_vn_voucher.py
│   └── test_cash_voucher.py                 # 3
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Printed Vouchers` |
| `summary` | `Shared A4 layout of the Vietnamese printed vouchers: header, title box, copies, amount in words, signatures` |
| `version` | `18.0.1.1.0` (step 2); `18.0.1.2.0` (step 3) |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Accounting/Localizations` |
| `countries` | `["vn"]` |
| `depends` | `account` |
| `external_dependencies` | `{"python": ["num2words"]}` |
| `data` | `data/report_paperformat.xml`, `report/l10n_vn_voucher_templates.xml`; step 3 adds `report/l10n_vn_cash_voucher_templates.xml`, `report/l10n_vn_cash_voucher_reports.xml`, `views/account_journal_views.xml`, `views/account_move_views.xml` |
| `assets` | `{"web.report_assets_common": ["l10n_vn_voucher/static/src/scss/l10n_vn_voucher.scss"]}` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import l10n_vn_voucher`, `from . import res_currency`; step 3: `from . import account_journal`, `from . import account_move` |
| `tests/__init__.py` | `from . import test_l10n_vn_voucher`; step 3: `from . import test_cash_voucher` |

## Access

No access rules: the module adds no stored model.

## Data — `data/report_paperformat.xml`

| XML id | Model | Values |
|---|---|---|
| `paperformat_l10n_vn_voucher` | `report.paperformat` | `name` *Vietnamese Voucher (A4)*, `format` `A4`, `orientation` `Portrait`, `margin_top` 10, `margin_bottom` 10, `margin_left` 12, `margin_right` 10, `header_line` False, `header_spacing` 0, `dpi` 90 |

Every voucher report action names it in `paperformat_id`.

## Models

### `l10n_vn.voucher` — `models/l10n_vn_voucher.py`

`_name = "l10n_vn.voucher"`, `_description = "Vietnamese Voucher Helpers"`, an `AbstractModel` with no
fields. Templates call it as `env["l10n_vn.voucher"]`.

| Method | Decorator | Behaviour |
|---|---|---|
| `_copy_labels(copies)` | `@api.model` | `copies` a text or False. Returns the stripped non-empty lines; `[False]` when there are none (D5) |
| `_date_text(date)` | `@api.model` | `date` a `date` or False. Returns `"Ngày %02d tháng %02d năm %d"` of it; for False, the module constant `DATE_DOTTED`, `"Ngày ..... tháng ..... năm ......."` |
| `_local_date(record, value)` | `@api.model` | `value` a UTC `datetime` or False. Returns `fields.Datetime.context_timestamp(record, value).date()`, or False |
| `_address(partner)` | `@api.model` | The partner's address on one line: the non-empty lines of `partner._display_address(without_company=True)` joined with `", "`; `""` for an empty partner |
| `_date_short(date)` | `@api.model` | Step 2. `"%02d/%02d/%d"` of the date, or `""` |
| `_numbered_rows(rows)` | `@api.model` | Step 2. The rows copied with a `number` key: product rows numbered from 1, section and note rows `False` |
| `_qty_text(qty)` | `@api.model` | Step 2. A grid quantity without trailing zeros, with a decimal comma: `"%g"` of it with `.` replaced by `,` (`10`, `2,5`) |
| `_compact_rows(rows)` | `@api.model` | Step 2. `rows` the order rows of `voucher_order_lines`. Drops section and note rows. A product row whose template `has_configurable_attributes` and appears on more than one product row joins a group keyed by template, `uom`, `price`, `discount` and `taxes`; the group is one row at the place of its first member: `name` the template's `name`, `code` `""`, `qty` and `amount` the members' sums, the other keys from the first member, `grouped` True. Every other row is copied with `grouped` False (design §6.2) |

### `res.currency` — `models/res_currency.py`

`_inherit = "res.currency"`

| Method | Decorator | Behaviour |
|---|---|---|
| `l10n_vn_amount_to_words(amount)` | — | `ensure_one`. `""` unless `name == "VND"` and `num2words` imported (imported as core does, `None` on `ImportError`). Otherwise the absolute amount rounded half-up to an integer (`float_round(..., precision_digits=0)`), read by `num2words(value, lang="vi")`, first letter upper-cased, followed by `" đồng"` (D4) |

### `account.journal` — `models/account_journal.py` (step 3)

`_inherit = "account.journal"`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_cash_in_sequence_id` | Many2one → `ir.sequence` | `string="Phiếu thu Sequence"`, `copy=False`, `check_company=True` |
| `l10n_vn_cash_out_sequence_id` | Many2one → `ir.sequence` | `string="Phiếu chi Sequence"`, `copy=False`, `check_company=True` |
| `l10n_vn_cash_in_copies` | Text | `string="Phiếu thu Copies"`, `help="One line per copy, with the label it prints. Empty: one copy without a label."` |
| `l10n_vn_cash_out_copies` | Text | `string="Phiếu chi Copies"`, same help |

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_voucher_sequence(kind)` | — | `ensure_one`. The journal's sequence for `kind` (`cash_in`, `cash_out`), created as superuser when missing and stored on the journal (D9): `name` `"%s – Phiếu thu"` / `"%s – Phiếu chi"` of the journal's name |

### `account.move` — `models/account_move.py` (step 3)

`_inherit = "account.move"`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_voucher_kind` | Selection `[("cash_in", "Phiếu thu"), ("cash_out", "Phiếu chi")]` | `string="Cash Voucher"`, `readonly=True`, `copy=False`, `index="btree_not_null"` |
| `l10n_vn_voucher_number` | Char | `string="Cash Voucher Number"`, `readonly=True`, `copy=False` |
| `l10n_vn_voucher_person` | Char | `string="Người nộp / nhận tiền"`, `copy=False` |
| `l10n_vn_voucher_address` | Char | `string="Địa chỉ người nộp / nhận tiền"`, `copy=False` |
| `l10n_vn_journal_type` | Selection | `related="journal_id.type"`, not stored; for the form |

`_sql_constraints`: `("l10n_vn_voucher_number_uniq", "unique(journal_id, l10n_vn_voucher_number)", "A cash voucher number is used once per journal.")`

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_cash_lines` | — | `ensure_one`. The lines on the journal's `default_account_id` when the journal is of type *cash*; empty otherwise (D7) |
| `_l10n_vn_voucher_kind_of` | — | `ensure_one`. `cash_in` when there are cash lines and all have a positive `balance`, `cash_out` when all have a negative one, else False (D7) |
| `_post(soft=True)` | — | `posted = super()._post(soft)`; for each of `posted`: its kind (`_l10n_vn_voucher_kind_of`); none, the stored kind cleared, the number kept on the entry but no longer printed; the same as the stored kind with a number, the number kept; otherwise kind written and `l10n_vn_voucher_number` drawn from `journal_id._l10n_vn_voucher_sequence(kind).next_by_id(sequence_date=move.date)` (D8). Returns `posted` |
| `_l10n_vn_side_accounts(lines)` | — | The accounts of `lines` for the *Nợ* or *Có* box (D12) |
| `_l10n_vn_voucher_partner` | — | `ensure_one`. The partner of the non-cash lines when there is exactly one, else an empty partner (D10) |
| `_l10n_vn_cash_voucher_data` | — | `ensure_one`. Raises `UserError` unless posted with a kind: `"%(entry)s is not a posted cash entry that only receives or only pays cash; split it into one entry per direction to print a voucher."` Otherwise the dict below, read in `vi_VN` |

`_l10n_vn_cash_voucher_data` keys:

| Key | *cash_in* (*Phiếu thu*) | *cash_out* (*Phiếu chi*) |
|---|---|---|
| `kind`, `title`, `form_code` | `cash_in`, `"PHIẾU THU"`, `"01-TT"` | `cash_out`, `"PHIẾU CHI"`, `"02-TT"` |
| `company`, `department` | `company_id`, `""` | same |
| `book` | the journal's name (*Quyển số*) | same |
| `number`, `date` | `l10n_vn_voucher_number`, `date` | same |
| `debit_accounts`, `credit_accounts` | `_l10n_vn_side_accounts` of the lines with a debit, and of those with a credit (D12) | same |
| `person_label`, `person` | `"Họ và tên người nộp tiền"`, `l10n_vn_voucher_person` or `_l10n_vn_voucher_partner().name` or `""` | `"Họ và tên người nhận tiền"`, same |
| `address` | `l10n_vn_voucher_address` or `l10n_vn.voucher._address(_l10n_vn_voucher_partner())` | same |
| `reason_label`, `reason` | `"Lý do nộp"`, `ref` or the first cash line's `name` or `""` (D11) | `"Lý do chi"`, same |
| `amount`, `currency` | the cash lines' total, absolute, in company currency; `company_currency_id` | same |
| `amount_text` | `formatLang` of `amount` at the currency's decimals, then the currency's name: `1.000.000 VND` | same |
| `copies` | `journal_id.l10n_vn_cash_in_copies` | `journal_id.l10n_vn_cash_out_copies` |
| `signers` | Giám đốc *(Ký, họ tên, đóng dấu)*; Kế toán trưởng; Người nộp tiền; Người lập phiếu (`create_uid.name`); Thủ quỹ | Giám đốc *(Ký, họ tên, đóng dấu)*; Kế toán trưởng; Thủ quỹ; Người lập phiếu (`create_uid.name`); Người nhận tiền |

Read in `vi_VN`, so amounts group with `.` (D12).

## Templates — `report/l10n_vn_voucher_templates.xml`

Building blocks, called with `t-call`; the variables each reads are set by the caller. None is a report
on its own.

| Template | Reads | Renders |
|---|---|---|
| `voucher_article` | `o` | `div.article.l10n_vn_voucher` with `data-oe-model` `o._name`, `data-oe-id` `o.id`, `data-oe-lang` `o.env.context.get("lang")`, holding the body (`t-out="0"`) (D1) |
| `voucher_page` | `copy_label_first` | `div.page.l10n_vn_voucher_page` holding the body, with `style="page-break-before: always;"` when `copy_label_first` is False (D6) |
| `voucher_header` | `company`, `department`, `form_code` | `table.l10n_vn_voucher_header`, two cells. Left: *Đơn vị:* `company.name` (bold); *Địa chỉ:* `_address(company.partner_id)`; unless `department` is None (step 2), *Bộ phận:* `department`, or the dotted span when empty. Right, centred, when `form_code` is set (step 2): *Mẫu số* `form_code` (bold) |
| `voucher_title` | `title`, `voucher_date`, `copy_label`, `number`, `debit_accounts`, `credit_accounts`, `show_accounts` | `table.l10n_vn_voucher_title`, three cells. Middle: `title` (h2, upper case as given); `_date_text(voucher_date)` (italic); `copy_label` (italic), when set. Right: *Số:* `number`; when `show_accounts` is not False, *Nợ:* and *Có:*, each the accounts joined with `", "`, or the dotted span when empty |
| `voucher_field` | `pairs`, or `label` and `value` | One line, `table.l10n_vn_voucher_field`, holding for each `(label, value)` of `pairs` (or of `[(label, value)]`) a `td.o_label` with the label and `":"` and a `td.o_value` with the value; an empty value's cell gets class `o_dots` and stays blank |
| `voucher_amount_words` | `currency`, `amount`, `label` | `voucher_field` with `pairs` False, `label` (default *Tổng số tiền (viết bằng chữ)*) and `currency.l10n_vn_amount_to_words(amount)` when `amount` is not False and `currency` is set, else empty |
| `voucher_party` | `party_title`, `partner` | Step 2. `div.l10n_vn_voucher_party`: *`party_title`:* and the commercial partner's name (bold); `voucher_field` rows *Địa chỉ* (`_address` of the commercial partner); *Mã số thuế* (`vat`) and *Điện thoại* (`phone` or `mobile`) on one line; *Người liên hệ* (`partner.name`) only when `partner` is not its commercial partner |
| `voucher_order_lines` | `rows`, `currency`, `show_discount` | Step 2. `table.l10n_vn_voucher_lines`. Header: *STT* · *Tên hàng hóa, dịch vụ* · *Mã số* · *ĐVT* · *Số lượng* · *Đơn giá* · *CK (%)* (only when `show_discount`) · *Thuế* · *Thành tiền*. Each row a dict with `display_type`, `name`, `code`, `uom`, `qty`, `price`, `discount`, `taxes`, `amount`: a `line_section` row is one cell across the table, bold; a `line_note` row one cell, italic; a product row with its `number` from `_numbered_rows` (sections and notes not counted), `qty` (*Product Unit of Measure*), `price` (*Product Price*), `discount` (precision 2), `taxes`, `amount` (precision `currency.decimal_places`) |
| `voucher_variant_grids` | `grids` | Step 2. For each matrix of `grids` (core's shape, `product_matrix`: `header` cells with a `name`; `matrix` rows whose first cell has a `name` and the others a `qty`), `table.o_product_variant_grid.l10n_vn_voucher_grid`: the header names; per row the first cell's name (bold) and each quantity through `_qty_text`. Nothing when `grids` is empty |
| `voucher_totals` | `currency`, `untaxed`, `tax`, `total` | Step 2. `table.l10n_vn_voucher_totals`, right-aligned: *Cộng tiền hàng*, *Thuế GTGT*, *Tổng cộng* (bold), amounts at the currency's decimals; *Loại tiền:* `currency.name` when it is not VND; then, for VND only, `voucher_amount_words` with label *Số tiền viết bằng chữ* and `total` |
| `voucher_signatures` | `sign_date`, `signers` | `div.l10n_vn_voucher_signatures`. When `sign_date` is not None: `_date_text(sign_date)` right-aligned (italic). Then a table of one equal-width column per signer, each a dict with `role`, `hint` and `name`: `role` (bold), `hint` (italic, default *(Ký, họ tên)*, a `\n` in it becomes a line break), an empty `div.o_sign_space`, then `name` when set |

The dotted span is `span.o_dots`. Callers set a block's variables with `t-set` inside the `t-call`; they reach the block only, not the caller.

## Templates — `report/l10n_vn_cash_voucher_templates.xml` (step 3)

**`report_cash_voucher`**: `web.html_container`; for each `o` of `docs`, `t-call` `report_cash_voucher_document`
with `t-lang="'vi_VN'"`.

**`report_cash_voucher_document`**: sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_cash_voucher_data()`, then `voucher_article` around a loop over `_copy_labels(v["copies"])`, one
`voucher_page` per copy holding:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`, `department` `""`, `form_code` |
| Title | `voucher_title`: `title`, `voucher_date`, `number`, `debit_accounts`, `credit_accounts`, `copy_label`; then `voucher_field` *Quyển số* / `book` |
| Person | `voucher_field` `person_label` / `person`; *Địa chỉ* / `address` |
| Reason | `voucher_field` `reason_label` / `reason` |
| Amount | `voucher_field` *Số tiền* / `amount_text`; `voucher_amount_words` with label *(Viết bằng chữ)* |
| Attachments | `voucher_field` *Kèm theo (chứng từ gốc)* / empty |
| Signatures | `voucher_signatures`: `sign_date` `date`, `signers` |
| Received | `voucher_field` *Đã nhận đủ số tiền (viết bằng chữ)* / empty |

## Reports — `report/l10n_vn_cash_voucher_reports.xml` (step 3)

| XML id | `name` | `domain` | `print_report_name` |
|---|---|---|---|
| `action_report_cash_in` | *Phiếu thu* | `[("l10n_vn_voucher_kind", "=", "cash_in"), ("state", "=", "posted")]` | `'Phiếu thu - %s' % (object.l10n_vn_voucher_number)` |
| `action_report_cash_out` | *Phiếu chi* | `[("l10n_vn_voucher_kind", "=", "cash_out"), ("state", "=", "posted")]` | `'Phiếu chi - %s' % (object.l10n_vn_voucher_number)` |

Both: `model` `account.move`, `report_type` `qweb-pdf`, `report_name` and `report_file`
`l10n_vn_voucher.report_cash_voucher`, `paperformat_id` `paperformat_l10n_vn_voucher`, `binding_model_id`
`account.model_account_move`, `binding_type` `report`.

## Views — `views/account_journal_views.xml` (step 3)

One record, `view_account_journal_form`, inheriting `account.view_account_journal_form`: after its last page, a
page *Vietnamese Vouchers*, `invisible="type != 'cash'"`, with the two sequences (`groups="base.group_no_one"`)
and the two copy lists (`placeholder` *Liên 1: Kế toán lưu*).

## Views — `views/account_move_views.xml` (step 3)

One record, `view_move_form`, inheriting `account.view_move_form`:

| Position | Content |
|---|---|
| `//group[@name='misc_group']` inside, last | `l10n_vn_journal_type` and `l10n_vn_voucher_kind` invisible; `l10n_vn_voucher_number`, `invisible="not l10n_vn_voucher_number"`; `l10n_vn_voucher_person` and `l10n_vn_voucher_address`, `invisible="l10n_vn_journal_type != 'cash'"` |

## Stylesheet — `static/src/scss/l10n_vn_voucher.scss`

All rules under `.l10n_vn_voucher`:

| Selector | Rules |
|---|---|
| `.l10n_vn_voucher` | `font-family: "DejaVu Serif", serif; font-size: 11pt; color: #000;` (D3) |
| `table` | `width: 100%; border-collapse: collapse;` |
| `.l10n_vn_voucher_header td` | `vertical-align: top;` the right cell `width: 35%; text-align: center;` |
| `.l10n_vn_voucher_title` | `margin: 4mm 0;` cells `vertical-align: top;` left and right cells `width: 25%`; `h2` `font-size: 15pt; font-weight: bold; margin: 0; text-align: center;` |
| `.l10n_vn_voucher_field td.o_label` | `white-space: nowrap; width: 1%; padding-right: 2mm;` |
| `.o_dots`, `td.o_dots` | `border-bottom: 1px dotted #000;` `span.o_dots` `display: inline-block; min-width: 40mm;` |
| `.l10n_vn_voucher_lines` | `border: 1px solid #000;` on the table and every `th`, `td`; `th` centred; `td.o_number` right-aligned; `thead` `display: table-header-group;` `tr` `page-break-inside: avoid;` (D6) |
| `.l10n_vn_voucher_party` | Step 2. `margin-bottom: 2mm;` |
| `.l10n_vn_voucher_lines tr.o_section td` | Step 2. `font-weight: bold;` `tr.o_note td` `font-style: italic;` |
| `.l10n_vn_voucher_totals` | Step 2. `width: 50%; margin-left: auto;` cells `padding: 0.5mm 1.5mm;` amount cells right-aligned; `tr.o_total` bold |
| `.l10n_vn_voucher_grid` | Step 2. `font-size: 9pt; margin-top: 2mm; width: auto; min-width: 50%;` cells bordered, `padding: 0.5mm 1.5mm;` header centred, quantities right-aligned |
| `.l10n_vn_voucher_signatures` | `margin-top: 6mm; page-break-inside: avoid;` its table `table-layout: fixed;` (equal columns, one per signer); cells `text-align: center; vertical-align: top;` `.o_role` bold; `.o_sign_space` `height: 22mm;` |

## Tests

`tests/test_l10n_vn_voucher.py`, `TestVoucherLayout(TransactionCase)`, `@tagged("post_install",
"-at_install")`: it creates a partner and a view.

**Fixtures:** `setUpClass` reads `base.VND`, `base.USD` and `base.main_company`; creates a partner with
street *12 Lê Lợi*, city *Hồ Chí Minh*, country `base.vn`; and creates a QWeb view (`ir.ui.view`, `type`
`qweb`, `key` `l10n_vn_voucher.test_blocks`) whose arch loops over `_copy_labels(copies)` as a form does
and, per copy, calls `voucher_page` around `voucher_header`, `voucher_title`, `voucher_field` (label
*Lý do*, value `reason`), `voucher_amount_words` and `voucher_signatures`, reading the values given at
render (defaults in `_render`). `_render(**values)` renders it through `self.env["ir.qweb"]._render(view.id, values)`
and returns the markup as text.

| Test | Asserts |
|---|---|
| `test_amount_to_words` | VND: 0 → *Không đồng*; 15 → *Mười lăm đồng*; 105 → *Một trăm lẻ năm đồng*; 1,005,000 → *Một triệu năm nghìn đồng*; 1,000,000.4 → *Một triệu đồng*; 999.5 → *Một nghìn đồng*; −2,500 → *Hai nghìn năm trăm đồng*. USD: `""` |
| `test_copy_labels` | `"Liên 1: A\n\n  Liên 2: B \n"` → `["Liên 1: A", "Liên 2: B"]`; `""`, `False` and `"\n \n"` → `[False]` |
| `test_date_text` | `date(2026, 11, 5)` → *Ngày 05 tháng 11 năm 2026*; False → the dotted text |
| `test_address` | the partner's address has no line break and contains *12 Lê Lợi* and *Hồ Chí Minh*; an empty partner gives `""` |
| `test_copies_render` | copies `"Liên 1: A\nLiên 2: B\nLiên 3: C"`: three `l10n_vn_voucher_page`, `page-break-before` twice, each label once; copies False: one page, no break |
| `test_compact_rows` | step 2. Rows of a configurable template *Áo test* (variants S and M) at 100 ×10, ×5 and M at 90 ×2; a product without variants ×3; a section row: three rows, in order — *Áo test* at 100, `qty` 15, `amount` 1,500, `code` `""`, grouped; the product without variants, not grouped; *Áo test* at 90, `qty` 2, grouped. A configurable template on one row only stays as it is, not grouped |
| `test_order_blocks_render` | step 2. The test view also renders `voucher_party`, `voucher_order_lines` and `voucher_totals` when `with_order` is set: with a partner company and its contact, a section row and a product row at discount 0, `show_discount` False, totals 1,000 / 100 / 1,100 VND: the output holds the party title, the company's name, *Người liên hệ* and the contact's name, the section's name, *Thuế*, `1.100`, *Một nghìn một trăm đồng*, and no *CK (%)* and no `o_product_variant_grid`; with a grid (header *Áo test*, *S*, *M*; row *Trắng*, 10 and 2.5), `o_product_variant_grid`, *Trắng* and `2,5`; with `show_discount` True, *CK (%)*; with USD totals, *Loại tiền:* `USD` and no *đồng* |
| `test_qty_text` | step 2. 10.0 → `10`, 2.5 → `2,5`, False → `0` |
| `test_header_without_code` | step 2. `form_code` False and `department` None: no *Mẫu số*, no *Bộ phận:* |
| `test_blocks_render` | with form code `01-VT`, number `WH/IN/00001`, debit `["152"]`, credit `["3399"]`, amount 10,000 VND and two signers: the output holds *Mẫu số*, `01-VT`, the main company's name, `WH/IN/00001`, `152`, `3399`, *Mười nghìn đồng*, both roles, *(Ký, họ tên)*; with debit, credit and reason empty, at least three dotted elements; with `show_accounts` False, no *Nợ:* |

### `tests/test_cash_voucher.py` (step 3)

`TestCashVoucher(TransactionCase)`, `@tagged("post_install", "-at_install")`.

**Fixtures (`setUpClass`):** a Vietnamese company with the `vn` chart, as the other modules' tests; its cash
journal (`type` `cash`, from the chart) and the chart's payable (`account.<company id>_chart3311`), receivable
(`_chart1311`) and expense (`_chart632`) accounts; two partners, one with an address; a user with
*Invoicing* (`account.group_account_invoice`) only, in that company.

**Helpers:** `_entry(lines, date=date(2026, 11, 10), **values)` creates an entry in the cash journal from
`(account, debit, credit, partner)` tuples and posts it; the cash account is the journal's `default_account_id`.

| Test | Asserts |
|---|---|
| `test_cash_out_series` | two payments (Nợ payable / Có cash 1,000,000): `cash_out`, `PC/2026/0001` and `PC/2026/0002`; a receipt (Nợ cash / Có receivable): `cash_in`, `PT/2026/0001` |
| `test_new_year` | a payment dated 2027-01-05 after one of 2026: `PC/2027/0001` |
| `test_no_voucher` | an entry in the cash journal that both receives and pays cash, and one that does not touch the cash account: no kind, no number; `_l10n_vn_cash_voucher_data` raises `UserError` |
| `test_repost` | a posted payment reset (`button_draft`) and posted again keeps its number; reset, its lines turned into a receipt and posted: `cash_in`, `PT/2026/0001`; the next payment takes `PC/2026/0002` |
| `test_person` | one partner on the other lines: `person` its name, `address` its address; two partners: `person` `""`; the entry's own person and address win |
| `test_accounts` | a payment to one account: `debit_accounts` the payable's code, `credit_accounts` the cash code; to the payable and the expense account (600,000 and 400,000): `debit_accounts` `"<code>: 600.000"` and `"<code>: 400.000"`, sorted |
| `test_render_cash_in` | with the journal's `l10n_vn_cash_in_copies` three lines, the receipt's render holds *PHIẾU THU*, *Mẫu số*, `01-TT`, its number, *Quyển số*, the journal's name, *Một triệu đồng*, *Người nộp tiền*, *Thủ quỹ*, *Đã nhận đủ số tiền*, each label once and `page-break-before` twice |
| `test_report_domains` | `get_valid_action_reports`: a posted receipt keeps only `action_report_cash_in`; a posted payment only `…_cash_out`; the payment reset to draft neither |
| `test_post_as_invoicing_user` | in a new cash journal without sequences, an *Invoicing* user posts a payment: `PC/2026/0001`, the sequence created; the same user renders it. Positive control: the user reads the entry's `name` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | The shared layout of the Vietnamese printed vouchers: A4, the company header with the form code, the title box with number and accounts, copies (*liên*) with their labels, amounts in words in Vietnamese, signature rows. Used by `l10n_vn_voucher_stock` and `l10n_vn_purchase_report`; step 2 adds *Phiếu thu* and *Phiếu chi* |
| `readme/USAGE.md` | Step 3 adds: cash transactions (statement lines) number their entries, which print their *Phiếu thu* / *Phiếu chi* (*Print*); entries keyed in by hand can only use *Miscellaneous* journals; the person and address on the entry's *Other Info*; copies and sequences on the cash journal's *Vietnamese Vouchers* tab; an entry that both receives and pays cash is split to print. How copy lists are written (one label per line), where they are set (operation types; cash journals from step 2); that the forms print in Vietnamese; that signed vouchers are scanned and attached to their record |
