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
| 3 | Cash vouchers: fields on `account.move` and `account.journal`, the PT/PC series, *Phiếu thu* and *Phiếu chi* (design §4.4; design step 7) | planned | |

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

## Folder structure

```
l10n_vn_voucher/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_voucher.py
│   └── res_currency.py
├── data/
│   └── report_paperformat.xml
├── report/
│   └── l10n_vn_voucher_templates.xml
├── static/src/scss/
│   └── l10n_vn_voucher.scss
├── tests/
│   ├── __init__.py
│   └── test_l10n_vn_voucher.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Printed Vouchers` |
| `summary` | `Shared A4 layout of the Vietnamese printed vouchers: header, title box, copies, amount in words, signatures` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Accounting/Localizations` |
| `countries` | `["vn"]` |
| `depends` | `account` |
| `external_dependencies` | `{"python": ["num2words"]}` |
| `data` | `data/report_paperformat.xml`, `report/l10n_vn_voucher_templates.xml` |
| `assets` | `{"web.report_assets_common": ["l10n_vn_voucher/static/src/scss/l10n_vn_voucher.scss"]}` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import l10n_vn_voucher`, `from . import res_currency` |
| `tests/__init__.py` | `from . import test_l10n_vn_voucher` |

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

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | The shared layout of the Vietnamese printed vouchers: A4, the company header with the form code, the title box with number and accounts, copies (*liên*) with their labels, amounts in words in Vietnamese, signature rows. Used by `l10n_vn_voucher_stock` and `l10n_vn_purchase_report`; step 2 adds *Phiếu thu* and *Phiếu chi* |
| `readme/USAGE.md` | How copy lists are written (one label per line), where they are set (operation types; cash journals from step 2); that the forms print in Vietnamese; that signed vouchers are scanned and attached to their record |
