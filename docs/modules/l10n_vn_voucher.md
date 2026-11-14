# l10n_vn_voucher

The shared layout of the Vietnamese printed vouchers: an A4 paper format, the QWeb blocks every form is
built from (record wrapper, copies, header, title box, dotted fields, amount in words, signatures), and
the helpers they read. Step 2 adds *Phiếu thu* and *Phiếu chi* from cash journal entries. The stock
vouchers live in `l10n_vn_voucher_stock`, the purchase forms in `l10n_vn_purchase_report`.
Design: `docs/Accounting/VN Vouchers — Design.md` (§4).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Paper format; QWeb blocks; `l10n_vn.voucher` helpers; `res.currency.l10n_vn_amount_to_words`; report stylesheet (design §4.1–4.3, §4.5). Installed together with `l10n_vn_voucher_stock` step 1, the first form that uses them | delivered | 2026-11-13, first run: `-i`, `exit=1`, 6 tests, 2 errors (`test_blocks_render`, `test_copies_render`): the signature cell's width, `t-att-style="'width: %.2f%%;' % (...)"`, reached Odoo with `%%` collapsed to `%`, and the formatting failed. Fixed with `table-layout: fixed` on the signature table and no computed width |
| 2 | Cash vouchers: fields on `account.move` and `account.journal`, the PT/PC series, *Phiếu thu* and *Phiếu chi* (design §4.4) | planned | |

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
| `voucher_header` | `company`, `department`, `form_code` | `table.l10n_vn_voucher_header`, two cells. Left: *Đơn vị:* `company.name` (bold); *Địa chỉ:* `_address(company.partner_id)`; *Bộ phận:* `department`, or the dotted span when empty. Right, centred: *Mẫu số* `form_code` (bold) |
| `voucher_title` | `title`, `voucher_date`, `copy_label`, `number`, `debit_accounts`, `credit_accounts`, `show_accounts` | `table.l10n_vn_voucher_title`, three cells. Middle: `title` (h2, upper case as given); `_date_text(voucher_date)` (italic); `copy_label` (italic), when set. Right: *Số:* `number`; when `show_accounts` is not False, *Nợ:* and *Có:*, each the accounts joined with `", "`, or the dotted span when empty |
| `voucher_field` | `pairs`, or `label` and `value` | One line, `table.l10n_vn_voucher_field`, holding for each `(label, value)` of `pairs` (or of `[(label, value)]`) a `td.o_label` with the label and `":"` and a `td.o_value` with the value; an empty value's cell gets class `o_dots` and stays blank |
| `voucher_amount_words` | `currency`, `amount`, `label` | `voucher_field` with `pairs` False, `label` (default *Tổng số tiền (viết bằng chữ)*) and `currency.l10n_vn_amount_to_words(amount)` when `amount` is not False and `currency` is set, else empty |
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
| `test_blocks_render` | with form code `01-VT`, number `WH/IN/00001`, debit `["152"]`, credit `["3399"]`, amount 10,000 VND and two signers: the output holds *Mẫu số*, `01-VT`, the main company's name, `WH/IN/00001`, `152`, `3399`, *Mười nghìn đồng*, both roles, *(Ký, họ tên)*; with debit, credit and reason empty, at least three dotted elements; with `show_accounts` False, no *Nợ:* |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | The shared layout of the Vietnamese printed vouchers: A4, the company header with the form code, the title box with number and accounts, copies (*liên*) with their labels, amounts in words in Vietnamese, signature rows. Used by `l10n_vn_voucher_stock` and `l10n_vn_purchase_report`; step 2 adds *Phiếu thu* and *Phiếu chi* |
| `readme/USAGE.md` | How copy lists are written (one label per line), where they are set (operation types; cash journals from step 2); that the forms print in Vietnamese; that signed vouchers are scanned and attached to their record |
