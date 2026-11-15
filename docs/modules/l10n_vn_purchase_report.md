# l10n_vn_purchase_report

The purchase order printed in Vietnamese on the shared layout of `l10n_vn_voucher`, with our signers and
the supplier's confirmation, in a full and a compact version (one row per style). Titled *Yêu cầu báo giá*
before confirmation, *Đơn đặt hàng* after, *Đơn đặt hàng gia công* for subcontracted products. Step 2 adds
the blanket order (*hợp đồng nguyên tắc*, or *hợp đồng gia công* with its material norms).
Design: `docs/Accounting/VN Vouchers — Design.md` (§6.1–6.3).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Purchase order and compact purchase order (design §6.1, §6.2; design step 3). Installed with `l10n_vn_voucher` step 2 | done | 2026-11-15, first run: `-i`, `exit=1`, 9 post-tests, 2 failures (`test_full_rows`, `test_render_full`), both in the tests: OCA `product_sequence` gives every new product a code (`PR/00141`), so `display_name` read `[PR/00141] Áo test (S)` while the form prints the name without its code, as specified. `test_render_compact` passed for the wrong reason, checking the coded name absent. The tests now compare with the name read with `display_default_code=False`, as do `l10n_vn_sale_report`'s. Second run: `-u`, `exit=0`, 9 post-tests, 0 failures. UI checked: full and compact orders, the subcontracting title |
| 2 | Blanket order and processing contract, with the material-norms appendix (design §6.3; design step 5) | done | 2026-11-15: `-u`, `exit=0`, 16 post-tests, 0 failures. UI checked: a processing contract for Võng Mùng and a framework agreement. Peter then found *Vải Chằn* missing from the appendix: its bill lines name a *Component (product template)* (OCA `mrp_bom_attribute_match`) and no variant, and the appendix read only `product_id`. Fixed in 2.1 |
| 2.1 | Fix: the appendix resolves bill lines that name a component template, as manufacturing orders do (D12); `test_material_norms_component_template`; version `18.0.1.1.1` | done | 2026-11-15: `-u`, `exit=0`, 17 post-tests, 0 failures. UI checked: BO00011's appendix shows each Võng Mùng variant's *Vải Chằn* and *Tem Võng Số* with its length's norm |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | Module table: depends on `l10n_vn_voucher`, `purchase_requisition`, `purchase_product_matrix`, `mrp_subcontracting` | also `purchase_stock` | The delivery address reads the order's operation type, `picking_type_id`, which `purchase_stock` adds (`purchase_stock/models/purchase_order.py:23`) |
| 2 | §6.3: the blanket order's lines one row per product | grouped by style (D7) | A processing contract lists the subcontracted styles' variants (*Võng Mùng* has 99); the agreement's substance is the price per style |
| 3 | §6.3: signatures *Đại diện bên mua* and *Đại diện bên bán* | for a processing contract, *Bên đặt gia công* / *Bên nhận gia công* in the parties and the signatures (D11, proposed) | The usual names of the parties to a *hợp đồng gia công* |

## Decisions

| # | Decision |
|---|---|
| D1 | **Everything the form shows is computed in Python** by `purchase.order._l10n_vn_order_data(compact)`; the template only lays it out, as in `l10n_vn_voucher_stock` |
| D2 | **A line prints the product's name without its code, not the line's description.** The description holds `[code] name` and any purchase description, while the code has its own column |
| D3 | **Subcontracting is read from the bill of materials as superuser:** `mrp.bom._bom_subcontract_find(product, company_id=…, bom_type="subcontract", subcontractor=partner)` (`mrp_subcontracting/models/mrp_bom.py:16`) with `sudo()`. Purchase users need not read bills of materials (`mrp/security/ir.model.access.csv:8,14,34`) |
| D4 | **The compact form shows core's grid list,** `get_report_matrixes()`, which is empty unless the order's *Print Variant Grids* (`report_grids`) is set (`purchase_product_matrix/models/purchase.py:142-160`), drawn by `l10n_vn_voucher.voucher_variant_grids` |
| D5 | **Cancelled orders print no Vietnamese form:** both report actions have the domain `[("state", "!=", "cancel")]` |
| D6 | **The subcontracting test is one function,** `subcontracting_bom(env, product, company, partner)` in `models/purchase_order.py`: `_bom_subcontract_find` as superuser (D3). The purchase order and the blanket order both call it (step 2) |
| D7 | **A blanket order prints one form, its lines grouped by style** through `l10n_vn.voucher._compact_rows`, without grids: an agreement fixes prices, and a processing contract can list every variant of a style (step 2) |
| D8 | **The lines carry no amount:** a blanket order agrees prices and, optionally, quantities; a quantity of 0 prints blank (step 2) |
| D9 | **The appendix groups the products whose norms are identical:** one table per distinct set of (component, unit, quantity per unit of product), titled with the names of the products sharing it. A subcontracting bill of materials can hold lines for some variants only (*Võng Mùng*: 22 of 34 lines, 99 variants), so one table per product would repeat near-identical tables (step 2) |
| D10 | **A norm is the bill-of-materials line's quantity per one unit of the product:** the line's `product_qty` divided by the bill's `product_qty` converted to the product's unit (`product_uom_id._compute_quantity(..., round=False)`), in the line's unit; lines that do not apply to the variant (`_skip_bom_line`) are left out (step 2) |
| D11 | **A processing contract names its parties *Bên đặt gia công* and *Bên nhận gia công*,** a framework agreement *Bên mua* and *Bên bán*; the signature row follows (*Đại diện bên đặt gia công*, …) (step 2; proposed) |
| D12 | **A bill line naming a component template is resolved as manufacturing orders resolve it** (step 2.1): with OCA `mrp_bom_attribute_match` installed, a line may leave *Component* empty and name a *Component (product template)*, the variant being the one matching the product's attributes. `_l10n_vn_bom_line_component` calls the module's `mrp.bom._get_component_template_product(line, product, line.product_id)` (`oca/manufacture/mrp_bom_attribute_match/models/mrp_bom.py:327-364`) when the method exists, else takes `product_id`; no match leaves the line out, as the module's `explode` does (`:248-256`). No dependency on the OCA module: without it, every line has a `product_id` |

## Folder structure

```
l10n_vn_purchase_report/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── purchase_order.py
│   └── purchase_requisition.py                     # 2
├── report/
│   ├── l10n_vn_purchase_report_reports.xml
│   └── l10n_vn_purchase_report_templates.xml
├── tests/
│   ├── __init__.py
│   ├── test_purchase_order_report.py
│   └── test_purchase_agreement_report.py           # 2
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Purchase Forms` |
| `summary` | `Purchase orders printed in Vietnamese with signature blocks, in full and compact versions` |
| `version` | `18.0.1.1.0` (step 2) |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Inventory/Purchase` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_voucher`, `purchase_stock`, `purchase_requisition`, `purchase_product_matrix`, `mrp_subcontracting` |
| `data` | `report/l10n_vn_purchase_report_templates.xml`, `report/l10n_vn_purchase_report_reports.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import purchase_order`, `from . import purchase_requisition` (step 2) |
| `tests/__init__.py` | `from . import test_purchase_order_report`, `from . import test_purchase_agreement_report` (step 2) |

## Access

No access rules: the module adds no model.

## Models

### `purchase.order` — `models/purchase_order.py`

`_inherit = "purchase.order"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_is_subcontracting` | — | `ensure_one`. True when a line's product has a subcontracting bill of materials for the vendor (D3); from step 2 through `subcontracting_bom` (D6) |
| `_l10n_vn_order_rows` | — | `ensure_one`. One dict per order line, ordered by `sequence, id`, with the keys `voucher_order_lines` reads: `display_type`; `name` (`line.name` for sections and notes, else `product_id.with_context(display_default_code=False).display_name`, D2); `code` (`product_id.default_code or ""`); `uom` (`product_uom.name`); `qty` (`product_qty`); `price` (`price_unit`); `discount`; `taxes` (the names of `taxes_id`, joined with `", "`); `amount` (`price_subtotal`); `product` (`product_id`) |
| `_l10n_vn_order_data(compact=False)` | — | `ensure_one`. The dict below, read in `vi_VN` (`self.with_context(lang="vi_VN")`) |

`_l10n_vn_order_data` keys:

| Key | Value |
|---|---|
| `title` | before confirmation (`state` not in *purchase*, *done*): `"YÊU CẦU BÁO GIÁ"`; after: `"ĐƠN ĐẶT HÀNG GIA CÔNG"` when `_l10n_vn_is_subcontracting()`, else `"ĐƠN ĐẶT HÀNG"` |
| `company` | `company_id` |
| `number` | `name` |
| `date` | the local date (`l10n_vn.voucher._local_date`) of `date_approve` after confirmation, else of `date_order` |
| `buyer` | `company_id.partner_id` (*Bên mua*) |
| `seller` | `partner_id` (*Bên bán*) |
| `vendor_ref` | `partner_ref or ""` |
| `agreement` | `requisition_id.name or ""` |
| `delivery_date` | `"%02d/%02d/%d"` of the local date of `date_planned`, or `""` |
| `delivery_address` | `_address(dest_address_id)` when set, else `_address(picking_type_id.warehouse_id.partner_id)` |
| `payment_term` | `payment_term_id.name or ""` |
| `rows` | `l10n_vn.voucher._compact_rows(_l10n_vn_order_rows())` when `compact`, else `_l10n_vn_order_rows()` |
| `compact` | `compact` |
| `grids` | `get_report_matrixes()` when `compact`, else `[]` (D4) |
| `show_discount` | any product row with a `discount` |
| `currency` | `currency_id` |
| `untaxed`, `tax`, `total` | `amount_untaxed`, `amount_tax`, `amount_total` |
| `notes` | `notes`, or False when empty (`is_html_empty`) |
| `signers` | Người lập phiếu (`name` `user_id.name`); Phụ trách mua hàng; Giám đốc; Xác nhận của nhà cung cấp with hint `"(Ký, ghi rõ họ tên, đóng dấu)"`. Each a dict with `role`, `hint` (`"(Ký, họ tên)"` unless named) and `name` (`""` unless named) |

### `purchase.requisition` — `models/purchase_requisition.py` (step 2)

`_inherit = "purchase.requisition"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_subcontracting_boms` | — | `ensure_one`. `{product: bill}` for each line's product that has a subcontracting bill of materials for `vendor_id` (D6), in line order |
| `_l10n_vn_agreement_rows` | — | `ensure_one`. One dict per line, ordered by `id`, with the keys of `voucher_order_lines`: `display_type` False; `name` (`product_id.with_context(display_default_code=False).display_name`); `code` (`default_code or ""`); `uom` (`product_uom_id.name`); `qty` (`product_qty`); `price` (`price_unit`); `discount` 0; `taxes` `""`; `amount` 0 (D8); `product` |
| `_l10n_vn_bom_line_component(bom, bom_line, product)` | `@staticmethod` | Step 2.1. The component the line consumes for the product (D12), or an empty recordset |
| `_l10n_vn_material_norms` | — | `ensure_one`. The appendix (D9, D10): for each product of `_l10n_vn_subcontracting_boms()`, its norm rows — per bill line not skipped for the product (`_skip_bom_line(product)`) whose component (`_l10n_vn_bom_line_component`, step 2.1) is found, a dict with `name` (the component without code), `code`, `uom` (the line's unit), `qty` (D10) — in the bill's line order; products with equal `(component id, unit id, qty rounded to 6 decimals)` tuples share one group. A list of groups, in the order of their first product, each `{"products": [names without code], "rows": [...]}` |
| `_l10n_vn_agreement_data` | — | `ensure_one`. The dict below, read in `vi_VN` |

`_l10n_vn_agreement_data` keys:

| Key | Processing contract (a bill in `_l10n_vn_subcontracting_boms()`) | Framework agreement |
|---|---|---|
| `title` | `"HỢP ĐỒNG GIA CÔNG"` | `"HỢP ĐỒNG NGUYÊN TẮC"` |
| `buyer_title`, `seller_title` | `"Bên đặt gia công"`, `"Bên nhận gia công"` (D11) | `"Bên mua"`, `"Bên bán"` |
| `company` | `company_id` | same |
| `number` | `name` | same |
| `date` | `date_start`, or False | same |
| `buyer`, `seller` | `company_id.partner_id`, `vendor_id` | same |
| `vendor_ref` | `reference or ""` | same |
| `date_start`, `date_end` | `l10n_vn.voucher._date_short` of each | same |
| `currency` | `currency_id` | same |
| `rows` | `l10n_vn.voucher._compact_rows(_l10n_vn_agreement_rows())` (D7) | same |
| `terms` | `description`, or False when empty (`is_html_empty`) | same |
| `norms` | `_l10n_vn_material_norms()` | `[]` |
| `signers` | *Đại diện bên đặt gia công* and *Đại diện bên nhận gia công* (D11) | *Đại diện bên mua* and *Đại diện bên bán* |

Each signer has the hint `"(Ký, ghi rõ họ tên, đóng dấu)"` and no name.

## Templates — `report/l10n_vn_purchase_report_templates.xml`

**`report_purchase_order_vn`** and **`report_purchase_order_vn_compact`**: `web.html_container`; for each `o`
of `docs`, `t-call` `report_purchase_order_vn_document` with `t-lang="'vi_VN'"`, `compact` set to False and
True respectively.

**`report_purchase_order_vn_document`**: sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_order_data(compact)`, then `l10n_vn_voucher.voucher_article` around one
`l10n_vn_voucher.voucher_page`, holding in order:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`; `department` None; `form_code` False |
| Title | `voucher_title`: `title`, `voucher_date` `v["date"]`, `number`; `show_accounts` False |
| Parties | `voucher_party` for *Bên mua* (`buyer`) and for *Bên bán* (`seller`); `voucher_field` *Số tham chiếu của nhà cung cấp* / `vendor_ref` |
| Agreement | when `agreement` is set: `voucher_field` *Theo hợp đồng nguyên tắc số* / `agreement` |
| Terms | `voucher_field` rows: *Ngày giao hàng dự kiến* / `delivery_date`; *Địa chỉ giao hàng* / `delivery_address`; *Điều khoản thanh toán* / `payment_term` |
| Lines | `voucher_order_lines`: `rows`, `currency`, `show_discount` |
| Grids | `voucher_variant_grids`: `grids` (D4) |
| Totals | `voucher_totals`: `currency`, `untaxed`, `tax`, `total` |
| Notes | when `notes`: *Ghi chú:* and the notes |
| Signatures | `voucher_signatures`: `sign_date` None, `signers` |

**`report_purchase_agreement_vn`** (step 2): `web.html_container`; for each `o` of `docs`, `t-call`
`report_purchase_agreement_vn_document` with `t-lang="'vi_VN'"`.

**`report_purchase_agreement_vn_document`** (step 2): sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_agreement_data()`, then `l10n_vn_voucher.voucher_article` around one `voucher_page` holding:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`; `department` None; `form_code` False |
| Title | `voucher_title`: `title`, `voucher_date` `v["date"]`, `number`; `show_accounts` False |
| Parties | `voucher_party` for `buyer_title` / `buyer` and `seller_title` / `seller`; `voucher_field` *Số tham chiếu* / `vendor_ref` |
| Validity | `voucher_field` on one line: *Hiệu lực từ ngày* / `date_start`, *đến ngày* / `date_end` |
| Currency | `voucher_field` *Loại tiền* / `currency.name` |
| Lines | `table.l10n_vn_voucher_lines`: *STT* · *Tên hàng hóa, dịch vụ* · *Mã số* · *ĐVT* · *Số lượng* · *Đơn giá*; one row per row of `rows`, numbered from 1; `qty` (*Product Unit of Measure*) blank when 0 (D8); `price` (*Product Price*) |
| Terms | when `terms`: *Điều khoản:* and the terms |
| Signatures | `voucher_signatures`: `sign_date` None, `signers` |
| Appendix | when `norms`: a `div` starting a new page (`page-break-before: always`) with the heading *PHỤ LỤC: ĐỊNH MỨC NGUYÊN PHỤ LIỆU*, then per group the products' names joined with `", "` (bold) and `table.l10n_vn_voucher_lines`: *STT* · *Tên nguyên phụ liệu* · *Mã số* · *ĐVT* · *Định mức / 1 sản phẩm*, the norm through `l10n_vn.voucher._qty_text` |

## Reports — `report/l10n_vn_purchase_report_reports.xml`

| XML id | `name` | `report_name` | `print_report_name` |
|---|---|---|---|
| `action_report_purchase_order_vn` | *Đơn đặt hàng (VN)* | `l10n_vn_purchase_report.report_purchase_order_vn` | `'Đơn đặt hàng - %s' % (object.name)` |
| `action_report_purchase_order_vn_compact` | *Đơn đặt hàng gọn (VN)* | `l10n_vn_purchase_report.report_purchase_order_vn_compact` | `'Đơn đặt hàng gọn - %s' % (object.name)` |

Both: `model` `purchase.order`, `report_type` `qweb-pdf`, `report_file` the same as `report_name`,
`paperformat_id` `l10n_vn_voucher.paperformat_l10n_vn_voucher`, `binding_model_id`
`purchase.model_purchase_order`, `binding_type` `report`, `domain` `[("state", "!=", "cancel")]` (D5).

Step 2: `action_report_purchase_agreement_vn`, *Hợp đồng nguyên tắc / gia công (VN)*, `model` `purchase.requisition`,
`report_name` and `report_file` `l10n_vn_purchase_report.report_purchase_agreement_vn`, the voucher paper format,
`binding_model_id` `purchase_requisition.model_purchase_requisition`, `binding_type` `report`, `domain`
`[("requisition_type", "=", "blanket_order"), ("state", "!=", "cancel")]`, `print_report_name`
`'Hợp đồng - %s' % (object.name)`. Core's *Purchase Agreements* print stays.

## Tests

`tests/test_purchase_order_report.py`, `TestPurchaseOrderReport(TransactionCase)`,
`@tagged("post_install", "-at_install")`: the fixtures create a company, products and partners. Not built on
`AccountTestInvoicingCommon` (CLAUDE.md, *Lessons*).

**Fixtures (`setUpClass`):**

- A Vietnamese company (`base.vn`, `base.VND`) linked to the test user, the `vn` chart loaded, put in the
  env's `allowed_company_ids`, as `l10n_vn_voucher_stock`'s tests do.
- A vendor company *Nhà cung cấp test* (`is_company`, `vat` `0300000001`, street, city, country `base.vn`).
- An attribute *Size test* (`create_variant` `always`) with values *S* and *M*; a template *Áo test* with
  that attribute line, giving two variants; a product *Chỉ test* (`default_code` `CTEST`) without variants.
- A purchase order of the vendor with lines: *Áo test (S)* 10 × 100, *Áo test (M)* 5 × 100, *Chỉ test* 3 × 50,
  each without taxes (`taxes_id` empty), so the totals are 1,650 / 0 / 1,650.
- A user with *Purchase / User* (`purchase.group_purchase_user`) only, in that company.

**Helpers:** `_data(order, compact=False)` returns `_l10n_vn_order_data(compact)`; `_html(order, xmlid, env=None)`
returns `_render_qweb_html` of the action decoded.

| Test | Asserts |
|---|---|
| `test_titles` | the draft order: *YÊU CẦU BÁO GIÁ*; after `button_confirm`: *ĐƠN ĐẶT HÀNG*; `date` the local date of `date_approve` |
| `test_subcontracting_title` | a subcontracting bill of materials (`type` `subcontract`, `subcontractor_ids` the vendor, one component) for *Chỉ test*; the confirmed order: *ĐƠN ĐẶT HÀNG GIA CÔNG* |
| `test_full_rows` | three rows; the first `name` *Áo test (S)*, its `code` the variant's; *Chỉ test*'s `code` `CTEST`, `taxes` `""`, `amount` 150 |
| `test_compact_rows` | two rows: *Áo test*, `qty` 15, `amount` 1,500, grouped; *Chỉ test*, not grouped |
| `test_agreement` | an order with `requisition_id` a blanket order of the vendor: `agreement` its name, and the full render holds *Theo hợp đồng nguyên tắc số* |
| `test_render_full` | the full render holds the title, the order's name, *Bên mua*, *Bên bán*, the vendor's name and `0300000001`, *Xác nhận của nhà cung cấp*, *(Ký, ghi rõ họ tên, đóng dấu)*, `1.650`, *Một nghìn sáu trăm năm mươi đồng*, *Áo test (S)*; no `o_product_variant_grid` |
| `test_render_compact` | the compact render holds `o_product_variant_grid` and `1.500`, and not *Áo test (S)* |
| `test_report_domains` | `get_valid_action_reports` keeps both actions for the draft order and neither once it is cancelled |
| `test_render_as_purchase_user` | with the subcontracting bill of materials, the full render in an env of the *Purchase / User* (`self.env(user=…, context=dict(…, allowed_company_ids=[company.id]))`) succeeds and holds *ĐƠN ĐẶT HÀNG GIA CÔNG* (D3); as a positive control the same user reads the order's `name` |

### `tests/test_purchase_agreement_report.py` (step 2)

`TestPurchaseAgreementReport(TransactionCase)`, `@tagged("post_install", "-at_install")`.

**Fixtures (`setUpClass`):** the Vietnamese company with the `vn` chart, the vendor and the purchase user, as
`TestPurchaseOrderReport`; the attribute *Size test* with *S*, *M* and *L*, the template *Áo test* with its
three variants; *Chỉ test* (`CTEST`); components *Vải test* (unit *m* of `uom.product_uom_meter`) and *Nút
test*; a subcontracting bill of materials for *Áo test*, `product_qty` 2, subcontractor the vendor, lines:
*Vải test* 2.4 m for every variant, *Nút test* 8 for *S* only, *Nút test* 10 for *M* and *L*; names without
code read under `display_default_code=False`.

**Helpers:** `_agreement(lines, **values)` creates a blanket order of the vendor from `(product, qty, price)`
tuples; `_html(agreement, env=None)` renders `action_report_purchase_agreement_vn`.

| Test | Asserts |
|---|---|
| `test_framework_agreement` | *Chỉ test* 100 × 50: *HỢP ĐỒNG NGUYÊN TẮC*, *Bên mua* / *Bên bán*, `norms` `[]`; the render holds *Đại diện bên mua* and no *PHỤ LỤC* |
| `test_processing_contract` | *Áo test* S, M, L at 100: *HỢP ĐỒNG GIA CÔNG*, *Bên đặt gia công* / *Bên nhận gia công*, the signers' roles |
| `test_rows_grouped` | *Áo test* S 10, M 5, L 5 at 100 and *Chỉ test* 3 at 50: two rows, *Áo test* `qty` 20 grouped, *Chỉ test* not |
| `test_material_norms` | the processing contract: two groups, in order — products [*Áo test (S)*] with *Vải test* 1.2 and *Nút test* 4; products [*Áo test (M)*, *Áo test (L)*] with *Vải test* 1.2 and *Nút test* 5 |
| `test_material_norms_component_template` | step 2.1; skipped without `mrp_bom_attribute_match`. A line naming the template *Lót test* (attribute *Size test*: S, M, L), 3 per bill of 2, added to the bill: three groups, one per size; each holds one *Lót test* row, the variant of its own size, at 1.5 |
| `test_render_processing_contract` | `date_start` 2026-12-01, `date_end` 2027-11-30, `reference` `HD-01`: the render holds the title, *Bên nhận gia công*, `01/12/2026`, `30/11/2027`, `HD-01`, *PHỤ LỤC: ĐỊNH MỨC NGUYÊN PHỤ LIỆU*, `1,2`, *Áo test (M), Áo test (L)*, `page-break-before`; a line of quantity 0 prints no `0,00` |
| `test_report_domains` | `get_valid_action_reports` keeps the action for a blanket order, not for a *Purchase Template* agreement nor a cancelled blanket order (`action_cancel`) |
| `test_render_as_purchase_user` | the processing contract rendered in an env of the *Purchase / User* succeeds and holds *HỢP ĐỒNG GIA CÔNG* and `1,2` (D6); as a positive control the user reads the agreement's `name` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Step 2 adds the blanket order as a *hợp đồng nguyên tắc*, or a *hợp đồng gia công* with the material norms appendix. Purchase orders printed in Vietnamese on the shared voucher layout: parties, terms, lines, totals with the amount in words, our signers and the supplier's confirmation. A compact version groups each style's variants into one row, with core's size grid beneath |
| `readme/USAGE.md` | Step 2 adds: on a blanket order, *Print → Hợp đồng nguyên tắc / gia công (VN)*; the processing-contract title, parties and appendix for subcontracted products; norms kept in the subcontracting bill of materials. *Print → Đơn đặt hàng (VN)* or *Đơn đặt hàng gọn (VN)*; the titles by state and for subcontracted products; *Print Variant Grids* on the order, shown in debug mode only (`purchase_product_matrix/views/purchase_views.xml:31`), to hide the grids on the compact version; core's English prints remain for foreign suppliers |
