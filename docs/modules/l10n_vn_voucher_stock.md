# l10n_vn_voucher_stock

*Phiếu nhập kho* (01-VT) and *Phiếu xuất kho* (02-VT) printed from transfers, on the shared layout of
`l10n_vn_voucher`. Each operation type says which voucher its transfers print, with what reason and how
many copies; a transfer may carry its own reason. Prices, amounts and accounts come from the posted
valuation of the transfer's moves. Step 2 adds the *Biên bản giao nhận hàng hóa*.
Design: `docs/Accounting/VN Vouchers — Design.md` (§5).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Operation-type settings; the transfer's reason; *Phiếu nhập kho* and *Phiếu xuất kho* (design §5.1–5.4; design step 2). Installed with `l10n_vn_voucher` step 1 | done | 2026-11-13, first run: `-i`, `exit=1`, 0 tests: `setUpClass` failed, the category refused with *The stock accounts should be set*. The fixtures searched the account by code `152`, but the `vn` chart pads codes to four digits, so it is `1520` and the search found nothing. Fixed by taking the chart's record (`account.<company id>_chart152`). Second run: `-u`, `exit=0`, 10 post-tests, 0 failures. UI checked as admin on WH Chi Lăng: receipt WH/IN/00068 (Nợ 1520 / Có 3399, three labelled copies), Pick Components WH/PC/01597 (17 lines, quantities only), Store Finished Product WH/SFP/01446, waiting delivery WH/OUT/00073 (dotted date and values), return WH/IN/00066 (default reason, then its own), Resupply Subcontractor WH/RES/00067, no voucher offered on a type without one, a mixed selection printing each transfer's own voucher. Not checked as a storekeeper in the UI: an existing test user could not be stripped of *Invoicing*, the hidden group `account.group_account_basic` implying it; the access path is covered by `test_render_as_storekeeper` |
| 2 | *Biên bản giao nhận hàng hóa* (design §5.5; design step 6); the partner fallback to the sales order's customer, for this form and the vouchers; version `18.0.1.1.0` | done | 2026-11-15, first run: `-u`, `exit=1`, 16 post-tests, 3 failures, all in the tests: two compared the place with an address read in English (*Vietnam*) while the form reads it in Vietnamese (*Việt Nam*); `test_partner_fallback` set `group_id` on the transfer, a read-only copy of its moves' group (`stock/models/stock_picking.py:582-584`), so the group was dropped. The tests now read addresses in `vi_VN` and set the group on the moves. Second run: `-u`, `exit=0`, 16 post-tests, 0 failures. UI checked: WH/RES/00067 (company to subcontractor, *Căn cứ* the PO) and WH/SBC/00027 (no partner on the transfer: *chị út nhí* from S00071 on the *Biên bản* and the *Phiếu nhập kho*, place the warehouse) |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §5.5: the place of handover is the partner's address | the receiving side's address: the warehouse's for an incoming type (D12) | Customer material arrives at our warehouse (*Resupply From Customer*), so the partner's address would be wrong there |
| 2 | §5.3, §5.5: the party is the transfer's partner | the transfer's partner, else its sales order's customer (D9) | Receipts created by a manufacturing order carry no partner (WH/SBC/00027) |

## Decisions

| # | Decision |
|---|---|
| D1 | **One template prints both vouchers;** the transfer's kind chooses the title, form code, columns and signers. Two report actions name it, so the Print menu offers the voucher that fits (design §5.2) |
| D2 | **A transfer whose type has no voucher kind refuses to print** with a `UserError`. It is reached only by selecting it beside a transfer that has one; each other record prints its own kind's voucher |
| D3 | **Everything the form shows is computed in Python** by `stock.picking._l10n_vn_voucher_data()`; the template only lays it out |
| D4 | **Valuation layers and journal entries are read with `sudo()`.** Layers are readable by *Inventory Administrators* only (`stock_account/security/ir.model.access.csv:8`) and journal items by accounting groups only (`account/security/ir.model.access.csv:39-44`), while storekeepers print the vouchers. The voucher shows posted figures; nothing is written |
| D5 | **One row per stock move,** cancelled moves left out, in the moves' order (`sequence`, `id`). A product received in two moves prints twice |
| D6 | **A move's amount is the absolute sum of its layers' `value`; its unit price is that amount divided by its quantity,** both only when the transfer is done and the move has layers (design §5.4). Quantities print with *Product Unit of Measure* precision, prices with *Product Price*, amounts with the company currency's decimals |
| D7 | **Accounts:** the codes of the debit lines and of the credit lines of the posted entries in the moves' `account_move_ids`, each code once, sorted. Empty when there is no posted entry |
| D8 | **The voucher's date is the transfer's `date_done` in the user's time zone;** before validation the date and the signature date are dotted |
| D9 | **A transfer without a partner takes its sales order's customer** (step 2): `group_id.sale_id.partner_id`, when `sale_stock` adds `sale_id` to procurement groups (`sale_stock/models/stock.py:84`). A *Resupply From Customer* receipt is created by a manufacturing order and carries no partner; its group still names the sales order (WH/SBC/00027: group WH/MO/01716, sales order S00071). The transfer's own `sale_id` is not used: it was empty on that receipt. No dependency on `sale_stock`: the field is read only when it exists. The sales order is read as superuser (`_l10n_vn_sale_order`): storekeepers need not read sales orders. Used by the vouchers and the *Biên bản* alike; nothing is written to the transfer |
| D10 | **The *Biên bản*'s direction follows the operation type:** an *incoming* type is the partner handing over (*Bên giao*) to the company (*Bên nhận*); any other — outgoing, or internal such as *Resupply Subcontractor* — is the company handing over to the partner (step 2) |
| D11 | **The *Biên bản* carries no prices, accounts or copies** and prints in two originals, one per party, as its closing line says (design §5.5) |
| D12 | **The *Biên bản*'s place of handover is the receiving side's address:** the warehouse's for an incoming type, the partner's otherwise. Its *Căn cứ* is the sales order's name when D9 finds one, else the transfer's `origin` (step 2) |

## Folder structure

```
l10n_vn_voucher_stock/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── stock_picking_type.py
│   └── stock_picking.py
├── report/
│   ├── l10n_vn_voucher_stock_reports.xml
│   └── l10n_vn_voucher_stock_templates.xml
├── views/
│   ├── stock_picking_type_views.xml
│   └── stock_picking_views.xml
├── tests/
│   ├── __init__.py, common.py
│   ├── test_stock_voucher.py
│   └── test_handover.py                         # 2
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Stock Vouchers` |
| `summary` | `Phiếu nhập kho and phiếu xuất kho printed from transfers, with values and accounts as posted` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Inventory/Inventory` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_voucher`, `stock_account` |
| `data` | `report/l10n_vn_voucher_stock_templates.xml`, `report/l10n_vn_voucher_stock_reports.xml`, `views/stock_picking_type_views.xml`, `views/stock_picking_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import stock_picking_type`, `from . import stock_picking` |
| `tests/__init__.py` | `from . import test_stock_voucher`, `from . import test_handover` (step 2) |

## Access

No access rules: the module adds fields to existing models only.

## Models

### `stock.picking.type` — `models/stock_picking_type.py`

`_inherit = "stock.picking.type"`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_voucher_kind` | Selection `[("in", "Phiếu nhập kho"), ("out", "Phiếu xuất kho")]` | `string="Voucher"`, `help="The Vietnamese voucher this type's transfers print. Empty: none."` |
| `l10n_vn_voucher_reason` | Char | `string="Voucher Reason"`, `translate=True`, `help="Lý do nhập / xuất kho printed on the voucher, unless the transfer has its own."` |
| `l10n_vn_handover_report` | Boolean | Step 2. `string="Handover Record"`, `help="This type's transfers also print the Biên bản giao nhận hàng hóa."` |
| `l10n_vn_voucher_copies` | Text | `string="Voucher Copies"`, `help="One line per copy, with the label it prints, such as: Liên 1: Kế toán lưu. Empty: one copy without a label."` |

### `stock.picking` — `models/stock_picking.py`

`_inherit = "stock.picking"`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_voucher_kind` | Selection | `related="picking_type_id.l10n_vn_voucher_kind"`, not stored |
| `l10n_vn_voucher_reason` | Char | `string="Voucher Reason"`, `copy=False`, `help="Lý do nhập / xuất kho for this transfer's voucher. Empty: the operation type's, or for a return the transfer it returns."` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_l10n_vn_voucher_reason_text` | — | `ensure_one`. `l10n_vn_voucher_reason`; else, when `return_id` is set, `"Trả lại hàng theo phiếu %s" % return_id.name`; else the type's `l10n_vn_voucher_reason` read in `vi_VN`; else `""` |
| `_l10n_vn_voucher_lines` | — | `ensure_one`. One dict per move not in state `cancel`, ordered by `sequence, id` (D5): `name` (`product_id.with_context(display_default_code=False).display_name`), `code` (`product_id.default_code or ""`), `uom` (`product_uom.name`), `demand` (`product_uom_qty`), `done` (`quantity` when the transfer is `done`, else None), `price` and `amount` (D6; None when not done or without layers). Layers read with `sudo()` (D4) |
| `_l10n_vn_voucher_accounts` | — | `ensure_one`. `(debit_codes, credit_codes)` from the posted entries of `move_ids.account_move_ids`, read with `sudo()` (D4, D7). Empty lists unless the transfer is `done` |
| `_l10n_vn_sale_order` | — | Step 2. `ensure_one`. `group_id.sale_id` read with `sudo()`; False when procurement groups have no `sale_id` (D9) |
| `_l10n_vn_partner` | — | Step 2. `ensure_one`. `partner_id`; else, when procurement groups have `sale_id`, `group_id.sale_id.partner_id`; else an empty partner (D9) |
| `_l10n_vn_handover_data` | — | Step 2. `ensure_one`. The dict below the voucher keys, read in `vi_VN` |
| `_l10n_vn_voucher_data` | — | `ensure_one`. Raises `UserError` when the type has no kind (D2): `"%(transfer)s: its operation type %(type)s prints no Vietnamese voucher."` Otherwise the dict below |

`_l10n_vn_voucher_data` keys, read in `vi_VN` (`self.with_context(lang="vi_VN")`):

| Key | *in* (*Phiếu nhập kho*) | *out* (*Phiếu xuất kho*) |
|---|---|---|
| `kind` | `"in"` | `"out"` |
| `title` | `"PHIẾU NHẬP KHO"` | `"PHIẾU XUẤT KHO"` |
| `form_code` | `"01-VT"` | `"02-VT"` |
| `company` | `company_id` | same |
| `department` | `picking_type_id.warehouse_id.name` or `""` | same |
| `number` | `name` | same |
| `date` | `l10n_vn.voucher._local_date(self, date_done)` when `done`, else False (D8) | same |
| `debit_accounts`, `credit_accounts` | `_l10n_vn_voucher_accounts()` | same |
| `party_label` | `"Họ và tên người giao hàng"` | `"Họ và tên người nhận hàng"` |
| `party` | `_l10n_vn_partner().display_name` or `""` (step 2; `partner_id` in step 1) | same |
| `party_address` | `l10n_vn.voucher._address` of `_l10n_vn_partner()` (step 2) | same |
| `reason_label` | `"Lý do nhập kho"` | `"Lý do xuất kho"` |
| `reason` | `_l10n_vn_voucher_reason_text()` | same |
| `source` | `origin or ""` | not used |
| `source_partner` | `_l10n_vn_partner().commercial_partner_id.name` or `""` (step 2) | not used |
| `warehouse_label` | `"Nhập tại kho"` | `"Xuất tại kho (ngăn lô)"` |
| `warehouse` | the warehouse's name or `""` | same |
| `location` | `location_dest_id.complete_name` | `location_id.complete_name` |
| `done_label` | `"Thực nhập"` | `"Thực xuất"` |
| `lines` | `_l10n_vn_voucher_lines()` | same |
| `total` | the sum of the lines' `amount` when any is set, else False | same |
| `currency` | `company_id.currency_id` | same |
| `copies` | `picking_type_id.l10n_vn_voucher_copies` | same |
| `signers` | Người lập phiếu (`name` `user_id.name`); Người giao hàng; Thủ kho; Kế toán trưởng with hint `"(Hoặc bộ phận có nhu cầu nhập)\n(Ký, họ tên)"` | the same with Người nhận hàng in second place, then Giám đốc |

Every signer is a dict with `role`, `hint` (`"(Ký, họ tên)"` unless named above) and `name` (`""` unless
named above).

`_l10n_vn_handover_data` keys (step 2):

| Key | Value |
|---|---|
| `title` | `"BIÊN BẢN GIAO NHẬN HÀNG HÓA"` |
| `company` | `company_id` |
| `number` | `name` |
| `date` | as the vouchers' (D8) |
| `basis` | the sales order's name (D9), else `origin or ""` (D12) |
| `giver`, `receiver` | incoming type: `_l10n_vn_partner()`, `company_id.partner_id`; otherwise the reverse (D10) |
| `place` | incoming type: `_address(picking_type_id.warehouse_id.partner_id)`; otherwise `_address(_l10n_vn_partner())` (D12) |
| `lines` | one dict per move not cancelled, ordered as the vouchers': `name`, `code`, `uom`, and `qty` — `quantity` when done, else `product_uom_qty` |
| `signers` | *Đại diện bên giao* and *Đại diện bên nhận*, each with hint `"(Ký, ghi rõ họ tên)"` and no name |

## Templates — `report/l10n_vn_voucher_stock_templates.xml`

**`report_stock_voucher`**: `web.html_container`; for each `o` of `docs`, `t-call`
`report_stock_voucher_document` with `t-lang="'vi_VN'"` (`l10n_vn_voucher` D2).

**`report_stock_voucher_document`**: sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_voucher_data()` and the number options (quantities *Product Unit of Measure*, prices *Product
Price*, amounts the currency's decimals), then `l10n_vn_voucher.voucher_article` around a loop over
`env["l10n_vn.voucher"]._copy_labels(v["copies"])` (`t-as="copy_label"`), calling
`l10n_vn_voucher.voucher_page` per copy (`l10n_vn_voucher` D6), each page holding, in order:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`, `department`, `form_code` from `v` |
| Title | `voucher_title`: `title`, `voucher_date` (`v["date"]`), `number`, `debit_accounts`, `credit_accounts` from `v`; `copy_label` from the loop |
| Fields | `voucher_field` rows: `party_label` / `party`; *Địa chỉ (bộ phận)* / `party_address`; `reason_label` / `reason`; for *in* only, one row *Theo* / `source`, *ngày* dotted, *của* / `source_partner`, as three label–value pairs on one line; `warehouse_label` / `warehouse` and *Địa điểm* / `location` on one line |
| Lines | `table.l10n_vn_voucher_lines`. Header rows: *STT* · *Tên, nhãn hiệu, quy cách, phẩm chất vật tư, dụng cụ, sản phẩm, hàng hóa* · *Mã số* · *Đơn vị tính* · *Số lượng* spanning *Theo chứng từ* and `done_label` · *Đơn giá* · *Thành tiền*; then the letter row *A B C D 1 2 3 4*. One row per line: index from 1; `name`; `code`; `uom`; `demand` and `done` (`float`, *Product Unit of Measure*); `price` (`float`, *Product Price*); `amount` (`float`, precision `currency.decimal_places`). An empty value leaves its cell blank. A last row *Cộng* with `total` under *Thành tiền* |
| Words | `voucher_amount_words`: `currency`, `amount` `v["total"]` |
| Attachments | `voucher_field`: *Số chứng từ gốc kèm theo*, empty |
| Signatures | `voucher_signatures`: `sign_date` `v["date"]`, `signers` `v["signers"]` |

**`report_stock_handover`** (step 2): `web.html_container`; for each `o` of `docs`, `t-call`
`report_stock_handover_document` with `t-lang="'vi_VN'"`.

**`report_stock_handover_document`** (step 2): sets `o` to `o.with_context(lang="vi_VN")` and `v` to
`o._l10n_vn_handover_data()`, then `voucher_article` around one `voucher_page` holding:

| Part | Content |
|---|---|
| Header | `voucher_header`: `company`; `department` None; `form_code` False |
| Title | `voucher_title`: `title`, `voucher_date` `v["date"]`, `number`; `show_accounts` False |
| Basis | `voucher_field` *Căn cứ* / `basis` |
| Parties | `voucher_party` for *Bên giao* / `giver` and *Bên nhận* / `receiver`, each followed by `voucher_field` pairs *Đại diện* / dotted and *Chức vụ* / dotted |
| Place | `voucher_field` *Địa điểm giao nhận* / `place` |
| Lines | `table.l10n_vn_voucher_lines`: *STT* · *Tên hàng hóa* · *Mã số* · *ĐVT* · *Số lượng* · *Ghi chú (tình trạng hàng hóa)*; quantities with *Product Unit of Measure* precision; the note cell blank |
| Closing | *Biên bản được lập thành 02 bản, mỗi bên giữ 01 bản, có giá trị như nhau.* |
| Signatures | `voucher_signatures`: `sign_date` `v["date"]`, `signers` |

## Reports — `report/l10n_vn_voucher_stock_reports.xml`

| XML id | `name` | `domain` |
|---|---|---|
| `action_report_stock_voucher_in` | *Phiếu nhập kho* | `[("picking_type_id.l10n_vn_voucher_kind", "=", "in"), ("state", "!=", "cancel")]` |
| `action_report_stock_voucher_out` | *Phiếu xuất kho* | `[("picking_type_id.l10n_vn_voucher_kind", "=", "out"), ("state", "!=", "cancel")]` |

Both: `model` `stock.picking`, `report_type` `qweb-pdf`, `report_name` and `report_file`
`l10n_vn_voucher_stock.report_stock_voucher`, `paperformat_id`
`l10n_vn_voucher.paperformat_l10n_vn_voucher`, `binding_model_id` `stock.model_stock_picking`,
`binding_type` `report`; `print_report_name` `'Phiếu nhập kho - %s' % (object.name)` and `'Phiếu xuất kho - %s' % (object.name)`.

Step 2: `action_report_stock_handover`, *Biên bản giao nhận hàng hóa*, `model` `stock.picking`, `report_name` and
`report_file` `l10n_vn_voucher_stock.report_stock_handover`, the voucher paper format, the same binding, `domain`
`[("picking_type_id.l10n_vn_handover_report", "=", True), ("state", "!=", "cancel")]`, `print_report_name`
`'Biên bản giao nhận - %s' % (object.name)`.

## Views — `views/stock_picking_type_views.xml`

One record, `view_picking_type_form`, inheriting `stock.view_picking_type_form`.

| Position | Content |
|---|---|
| `//page[@name='hardware']` after | `page` `name="l10n_vn_voucher"`, `string="Vietnamese Voucher"`, holding a group with `l10n_vn_voucher_kind`; `l10n_vn_voucher_reason` and `l10n_vn_voucher_copies` (`placeholder` *Liên 1: Kế toán lưu*), both `invisible="not l10n_vn_voucher_kind"`; from step 2, `l10n_vn_handover_report` in the second group, always shown |

## Views — `views/stock_picking_views.xml`

One record, `view_picking_form`, inheriting `stock.view_picking_form`.

| Position | Content |
|---|---|
| `//group[@name='other_infos']` inside, last | `l10n_vn_voucher_kind` invisible; `l10n_vn_voucher_reason`, `invisible="not l10n_vn_voucher_kind"`, `readonly="state == 'cancel'"` |

## Tests

`StockVoucherCase(TransactionCase)` in `tests/common.py` holds the fixtures and no test methods.
`TestStockVoucher(StockVoucherCase)` in `tests/test_stock_voucher.py` is
`@tagged("post_install", "-at_install")`: the fixtures create a company, products and partners. Not built on
`AccountTestInvoicingCommon` (CLAUDE.md, *Lessons*).

**Fixtures (`setUpClass`):**

- A Vietnamese company (`base.vn`, `base.VND`) linked to the test user, the `vn` chart loaded through
  `account.chart.template.try_loading(..., install_demo=False)`, put in the env's `allowed_company_ids`, as
  `l10n_vn_einvoice`'s tests do. Its warehouse is the one `stock` creates with the company.
- Two accounts in it: `3399` (`liability_current`) and `1599` (`asset_current`); and the chart's raw-materials account, `account.<company id>_chart152`, whose code is `1520`: the `vn` chart pads codes to four digits (`code_digits`, `l10n_vn/models/template_vn.py:14`).
- A product category: `property_valuation` `real_time`, `property_cost_method` `standard`, valuation `1520`,
  input `3399`, output `1599`, journal the company's `STJ` (set `with_company`).
- A product *Vải test*, `default_code` `VTEST1`, `is_storable`, in that category, `standard_price` 1,000
  (`with_company`).
- A partner *Nhà cung cấp test* with street, city and country `base.vn`.
- The warehouse's receipt type: kind *in*, reason *Nhập kho mua hàng*, copies
  `"Liên 1: Kế toán lưu\nLiên 2: Thủ kho giữ để ghi thẻ kho\nLiên 3: Giao cho người giao hàng"`. Its
  delivery type: kind *out*, reason *Xuất kho bán hàng*. Its internal type: kind *out*, reason
  *Xuất nguyên liệu cho sản xuất*.
- A user with *Inventory / User* (`stock.group_stock_user`) only, in that company.

**Helpers:** `_picking(picking_type, qty, partner=None, **values)` creates a transfer of the product with
the type's default locations and one move of `qty`; `_validate(picking)` confirms it, sets every move's
`quantity` to its demand and `picked`, calls `button_validate` and asserts the transfer is done;
`_receipt_done(qty=10)` validates a receipt from the partner. `_data(picking)` returns
`_l10n_vn_voucher_data()`. `_valid(picking)` returns the XML ids of the two actions that
`(action_in | action_out).get_valid_action_reports("stock.picking", picking.ids)` keeps.
`_html(picking, action)` returns
`self.env["ir.actions.report"]._render_qweb_html(action, picking.ids)[0]` decoded.

| Test | Asserts |
|---|---|
| `test_receipt_done` | a receipt of 10 from the partner, validated: `title` *PHIẾU NHẬP KHO*, `form_code` `01-VT`, `number` the transfer's name, `date` the local date of `date_done`; `debit_accounts` `["1520"]`, `credit_accounts` `["3399"]`; one line: `name` *Vải test* (no code), `code` `VTEST1`, `demand` 10, `done` 10, `price` 1,000, `amount` 10,000; `total` 10,000; `party` the partner; `reason` *Nhập kho mua hàng* |
| `test_receipt_not_done` | the same receipt confirmed only: `date` False, line `done`, `price`, `amount` None, `total` False, both account lists empty |
| `test_delivery_done` | after the receipt, a delivery of 4: `title` *PHIẾU XUẤT KHO*, `form_code` `02-VT`; `debit_accounts` `["1599"]`, `credit_accounts` `["1520"]`; `amount` 4,000; five signers, the last *Giám đốc* |
| `test_internal_quantities_only` | after the receipt, an internal transfer of 3, validated: kind *out*, `done` 3, `price` and `amount` None, `total` False, no accounts; `location` the source location |
| `test_reason` | the type's reason by default; the transfer's own when set; a transfer created with `return_id` the receipt and no reason of its own: *Trả lại hàng theo phiếu* and the receipt's name |
| `test_cancelled_move_left_out` | a receipt with a move of the product and one of a second product *Chỉ test* (`VTEST2`; two moves of one product merge at confirmation), the second cancelled after confirmation, then validated: one line, `VTEST1` |
| `test_no_kind_refused` | a transfer of a type with no kind: `_l10n_vn_voucher_data` raises `UserError` |
| `test_report_domains` | `get_valid_action_reports` on the two actions: a receipt keeps only `action_report_stock_voucher_in`, a delivery only `…_out`; a cancelled receipt and a transfer of a type without kind keep neither |
| `test_render_receipt` | `_html` of the validated receipt with `…_in`: *PHIẾU NHẬP KHO*, *Mẫu số*, `01-VT`, the transfer's name, `10.000` (Vietnamese grouping), *Mười nghìn đồng*, each of the three copy labels once, two `page-break-before` |
| `test_render_as_storekeeper` | the same render in an env of the *Inventory / User* (`self.env(user=…, context=dict(…, allowed_company_ids=[company.id]))`): succeeds and holds `10.000`, `1520` and `3399` (D4); as a positive control, the same user reads the transfer's `name` |

### `tests/test_handover.py` (step 2)

`TestStockHandover(StockVoucherCase)`, `@tagged("post_install", "-at_install")`. The fixtures' receipt and
delivery types get `l10n_vn_handover_report` in `setUpClass`; the internal type does not.

| Test | Asserts |
|---|---|
| `test_handover_delivery` | after a receipt, a delivery of 4 to the partner, validated: `title`; `giver` the company's partner, `receiver` the partner; `place` the partner's address read in `vi_VN`; one line, `qty` 4; `date` set |
| `test_handover_receipt` | a receipt of 10 from the partner, not validated: `giver` the partner, `receiver` the company's partner; `place` the warehouse's address read in `vi_VN`; `qty` 10 (the demand); `date` False |
| `test_handover_domain` | `get_valid_action_reports` keeps the handover action for a receipt, not for an internal transfer (type without the flag) nor a cancelled receipt |
| `test_partner_fallback` | skipped when procurement groups have no `sale_id`. A sales order for the partner; a receipt without partner whose moves get a group (`procurement.group`) with that `sale_id`, the transfer's `group_id` following them: `_l10n_vn_partner()` is the partner; the voucher's `party` and the *Biên bản*'s `giver` name it; the *Biên bản*'s `basis` is the sales order's name; the transfer's `partner_id` stays empty |
| `test_render_handover` | the delivery's render holds *BIÊN BẢN GIAO NHẬN HÀNG HÓA*, *Bên giao*, *Bên nhận*, *Đại diện bên giao*, *Địa điểm giao nhận*, *Biên bản được lập thành 02 bản*, and no *Đơn giá*, *Nợ:* nor *Liên* |
| `test_render_handover_as_storekeeper` | the same render in an env of the *Inventory / User* succeeds; as a positive control the user reads the transfer's `name` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Step 2 adds the *Biên bản giao nhận hàng hóa*, a handover record both parties sign, on the operation types that ask for it. *Phiếu nhập kho* and *Phiếu xuất kho* printed from transfers on the shared voucher layout; values and accounts from the posted valuation; production and other internal transfers print quantities only |
| `readme/USAGE.md` | Step 2 adds: *Handover Record* on the operation type's *Vietnamese Voucher* tab; *Print → Biên bản giao nhận hàng hóa*; the parties by direction; the customer taken from the sales order when a transfer has none. Setting an operation type's voucher, reason and copies (*Vietnamese Voucher* tab); a transfer's own reason (*Additional Info*); printing from *Print*; printing before validation for the storekeeper to fill in, and after validation as the voucher of record; scanning the signed copy into the chatter |
