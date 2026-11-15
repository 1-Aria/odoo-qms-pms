# l10n_vn_sale_report

The sales order printed in Vietnamese on the shared layout of `l10n_vn_voucher`, with our signers and the
customer's confirmation, in a full and a compact version (one row per style). Titled *Báo giá* before
confirmation and *Xác nhận đơn hàng* after. The purchase order's form (`l10n_vn_purchase_report`) with the
parties the other way round.
Design: `docs/Accounting/VN Vouchers — Design.md` (§6.4).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Sales order and compact sales order (design §6.4; design step 4) | done | 2026-11-15: `-i`, `exit=0`, 7 post-tests, 0 failures (its tests corrected for product codes before the run, as `l10n_vn_purchase_report` step 1 records). UI checked: quotation and confirmed order, full and compact with grids |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §6.2, §6.4: core's grids print beneath the compact form | a grid for every grouped style, from `_l10n_vn_report_matrixes` (D4) | Core draws a sales grid only for styles whose *Sales Variant Selection* is *Order Grid Entry* (`product_add_mode`, `sale_product_matrix/models/sale_order.py:159`). On this database 10 of the 24 sold multi-variant styles (226 of 669 variant lines) use the configurator, so the compact form would group them with no size breakdown |

## Decisions

| # | Decision |
|---|---|
| D1 | **Everything the form shows is computed in Python** by `sale.order._l10n_vn_order_data(compact)`, with the keys of `l10n_vn_purchase_report`'s, so both forms read the same `l10n_vn_voucher` blocks |
| D2 | **The lines are the order's reportable lines,** `_get_order_lines_to_report()` (`sale/models/sale_order.py:1848-1865`), which leaves out down payments not yet invoiced, as core's print does |
| D3 | **A line prints the product's name without its code,** not the line's description (`l10n_vn_purchase_report` D2) |
| D4 | **The compact form draws a grid for every style it groups:** `_l10n_vn_report_matrixes()`, core's `get_report_matrixes` (`sale_product_matrix/models/sale_order.py:151-169`) without its `product_add_mode == "matrix"` filter, still empty unless *Print Variant Grids* (`report_grids`) is set; drawn by `l10n_vn_voucher.voucher_variant_grids`. Core's own print is unchanged (divergence 1) |
| D5 | **Cancelled orders print no Vietnamese form:** both report actions have the domain `[("state", "!=", "cancel")]` |

## Folder structure

```
l10n_vn_sale_report/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   └── sale_order.py
├── report/
│   ├── l10n_vn_sale_report_reports.xml
│   └── l10n_vn_sale_report_templates.xml
├── tests/
│   ├── __init__.py
│   └── test_sale_order_report.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Sales Forms` |
| `summary` | `Sales orders printed in Vietnamese with signature blocks, in full and compact versions` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Sales/Sales` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_voucher`, `sale_product_matrix` |
| `data` | `report/l10n_vn_sale_report_templates.xml`, `report/l10n_vn_sale_report_reports.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import sale_order` |
| `tests/__init__.py` | `from . import test_sale_order_report` |

## Access

No access rules: the module adds no model.

## Models

### `sale.order` — `models/sale_order.py`

`_inherit = "sale.order"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_order_rows` | — | `ensure_one`. One dict per line of `_get_order_lines_to_report()` (D2), with the keys `voucher_order_lines` reads: `display_type`; `name` (`line.name` for sections and notes, else `product_id.with_context(display_default_code=False).display_name`, D3); `code` (`product_id.default_code or ""`); `uom` (`product_uom.name`); `qty` (`product_uom_qty`); `price` (`price_unit`); `discount`; `taxes` (the names of `tax_id`, joined with `", "`); `amount` (`price_subtotal`); `product` (`product_id`) |
| `_l10n_vn_report_matrixes` | — | `ensure_one`. `[]` unless `report_grids`. For each template of the lines with `is_configurable_product` that appears on more than one line: `_get_matrix(template)` with the rows whose quantities are all 0 removed, as core does (D4) |
| `_l10n_vn_order_data(compact=False)` | — | `ensure_one`. The dict below, read in `vi_VN` |

`_l10n_vn_order_data` keys:

| Key | Value |
|---|---|
| `title` | `"XÁC NHẬN ĐƠN HÀNG"` when `state` is *sale*, else `"BÁO GIÁ"` |
| `company` | `company_id` |
| `number` | `name` |
| `date` | the local date (`l10n_vn.voucher._local_date`) of `date_order` |
| `seller` | `company_id.partner_id` (*Bên bán*) |
| `buyer` | `partner_id` (*Bên mua*) |
| `customer_ref` | `client_order_ref or ""` |
| `validity_date` | before confirmation, `"%02d/%02d/%d"` of `validity_date`, or `""`; after confirmation False |
| `delivery_date` | `"%02d/%02d/%d"` of the local date of `commitment_date`, or `""` |
| `delivery_address` | `_address(partner_shipping_id)` |
| `payment_term` | `payment_term_id.name or ""` |
| `rows` | `l10n_vn.voucher._compact_rows(_l10n_vn_order_rows())` when `compact`, else `_l10n_vn_order_rows()` |
| `compact` | `compact` |
| `grids` | `_l10n_vn_report_matrixes()` when `compact`, else `[]` (D4) |
| `show_discount` | any product row with a `discount` |
| `currency` | `currency_id` |
| `untaxed`, `tax`, `total` | `amount_untaxed`, `amount_tax`, `amount_total` |
| `notes` | `note`, or False when empty (`is_html_empty`) |
| `signers` | Người lập phiếu (`name` `user_id.name`); Phụ trách kinh doanh; Giám đốc; Xác nhận của khách hàng with hint `"(Ký, ghi rõ họ tên, đóng dấu)"`. Each a dict with `role`, `hint` (`"(Ký, họ tên)"` unless named) and `name` (`""` unless named) |

## Templates — `report/l10n_vn_sale_report_templates.xml`

**`report_sale_order_vn`** and **`report_sale_order_vn_compact`**: `web.html_container`; for each `o` of
`docs`, `t-call` `report_sale_order_vn_document` with `t-lang="'vi_VN'"`, `compact` set to False and True
respectively.

**`report_sale_order_vn_document`**: sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_order_data(compact)`, then `l10n_vn_voucher.voucher_article` around one
`l10n_vn_voucher.voucher_page`, holding in order:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`; `department` None; `form_code` False |
| Title | `voucher_title`: `title`, `voucher_date` `v["date"]`, `number`; `show_accounts` False |
| Parties | `voucher_party` for *Bên bán* (`seller`) and for *Bên mua* (`buyer`); `voucher_field` *Số tham chiếu của khách hàng* / `customer_ref` |
| Terms | `voucher_field` rows: *Báo giá có hiệu lực đến* / `validity_date`, only when it is not False; *Ngày giao hàng* / `delivery_date`; *Địa chỉ giao hàng* / `delivery_address`; *Điều khoản thanh toán* / `payment_term` |
| Lines | `voucher_order_lines`: `rows`, `currency`, `show_discount` |
| Grids | `voucher_variant_grids`: `grids` (D4) |
| Totals | `voucher_totals`: `currency`, `untaxed`, `tax`, `total` |
| Notes | when `notes`: *Ghi chú:* and the notes |
| Signatures | `voucher_signatures`: `sign_date` None, `signers` |

## Reports — `report/l10n_vn_sale_report_reports.xml`

| XML id | `name` | `report_name` | `print_report_name` |
|---|---|---|---|
| `action_report_sale_order_vn` | *Đơn bán hàng (VN)* | `l10n_vn_sale_report.report_sale_order_vn` | `'Đơn bán hàng - %s' % (object.name)` |
| `action_report_sale_order_vn_compact` | *Đơn bán hàng gọn (VN)* | `l10n_vn_sale_report.report_sale_order_vn_compact` | `'Đơn bán hàng gọn - %s' % (object.name)` |

Both: `model` `sale.order`, `report_type` `qweb-pdf`, `report_file` the same as `report_name`,
`paperformat_id` `l10n_vn_voucher.paperformat_l10n_vn_voucher`, `binding_model_id` `sale.model_sale_order`,
`binding_type` `report`, `domain` `[("state", "!=", "cancel")]` (D5).

## Tests

`tests/test_sale_order_report.py`, `TestSaleOrderReport(TransactionCase)`, `@tagged("post_install",
"-at_install")`: the fixtures create a company, products and partners.

**Fixtures (`setUpClass`):** a Vietnamese company with the `vn` chart, as `l10n_vn_purchase_report`'s tests;
a customer company *Khách hàng test* (`is_company`, `vat` `0300000002`, street, city, country `base.vn`) and
its contact *Chị Lan*; the attribute *Size test* (S, M), the template *Áo test* with two variants and the
product *Chỉ test* (`CTEST`); a user with *Sales / User: Own Documents Only*
(`sales_team.group_sale_salesman`) only, in that company; a sales order for the contact, `user_id` that
salesman, `validity_date` 2026-12-31, with lines *Áo test (S)* 10 × 100, *Áo test (M)* 5 × 100,
*Chỉ test* 3 × 50, without taxes (`tax_id` empty), and a section line *Đợt 1* first.

**Helpers:** `_data(order, compact=False)`; `_html(order, xmlid, env=None)`, as in `l10n_vn_purchase_report`.

| Test | Asserts |
|---|---|
| `test_titles` | the quotation: *BÁO GIÁ*, `validity_date` `31/12/2026`; after `action_confirm`: *XÁC NHẬN ĐƠN HÀNG*, `validity_date` False |
| `test_full_rows` | four rows: the section *Đợt 1* (`display_type` `line_section`), *Áo test (S)*, *Áo test (M)*, *Chỉ test* |
| `test_compact_rows` | two rows, the section left out: *Áo test*, `qty` 15, `amount` 1,500, grouped; *Chỉ test*, not grouped |
| `test_render_full` | the full render holds *BÁO GIÁ*, the order's name, *Bên bán*, *Bên mua*, *Khách hàng test*, `0300000002`, *Người liên hệ* and *Chị Lan*, *Báo giá có hiệu lực đến*, *Đợt 1*, *Xác nhận của khách hàng*, `1.650`, *Một nghìn sáu trăm năm mươi đồng*; no `o_product_variant_grid` |
| `test_render_compact` | *Áo test* uses the configurator (`product_add_mode`), and core's `get_report_matrixes()` is empty; the compact render holds `o_product_variant_grid` and `1.500`, and neither *Áo test (S)* nor *Đợt 1* |
| `test_report_domains` | `get_valid_action_reports` keeps both actions for the quotation and neither once it is cancelled (`_action_cancel`) |
| `test_render_as_salesman` | the full render in an env of the salesman (`self.env(user=…, context=dict(…, allowed_company_ids=[company.id]))`) succeeds and holds the order's name; as a positive control the salesman reads the order's `name` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Sales orders printed in Vietnamese on the shared voucher layout: parties, terms, lines, totals with the amount in words, our signers and the customer's confirmation. A compact version groups each style's variants into one row, with core's size grid beneath |
| `readme/USAGE.md` | *Print → Đơn bán hàng (VN)* or *Đơn bán hàng gọn (VN)*; the titles by state; *Print Variant Grids* on the order (debug mode, `sale_product_matrix/views/sale_order_views.xml:18`) to hide the grids on the compact version; core's prints remain |
