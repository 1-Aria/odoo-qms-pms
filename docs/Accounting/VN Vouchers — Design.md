# VN Vouchers — Design

Nov 13, 2026 · @Peter · Revised Nov 13, 2026 · Status: draft

Printed Vietnamese vouchers and purchase forms, made from Odoo records, printed on A4 and signed by hand.
Three modules outside the QMS-PMS, IE-MES and payroll suites:

| Module | Depends on | Prints |
|---|---|---|
| `l10n_vn_voucher` | `account` | The shared layout; *Phiếu thu* and *Phiếu chi* from cash journal entries |
| `l10n_vn_voucher_stock` | `l10n_vn_voucher`, `stock_account` | *Phiếu nhập kho* and *Phiếu xuất kho* from transfers; the *Biên bản giao nhận hàng hóa* |
| `l10n_vn_purchase_report` | `l10n_vn_voucher`, `purchase_requisition`, `purchase_product_matrix`, `mrp_subcontracting` | The purchase order (and subcontracting order), its compact version, the blanket order |

The forms are the company's own (D1), modelled on 01-VT, 02-VT, 01-TT and 02-TT, which the company
has used until now as store-bought pads printed to Circular 200's layout. They will be refined after
use. Changing a form means editing its template and upgrading the module.

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| V1 | **Stock movements print their voucher** | A transfer of a configured operation type prints its *Phiếu nhập kho* or *Phiếu xuất kho* from the Print menu |
| V2 | **Cash movements print their voucher** | A posted entry in a cash journal prints its *Phiếu thu* or *Phiếu chi*, numbered in its own series |
| V3 | **Purchase documents carry signature blocks** | The purchase order and the blanket order print with our signers and the supplier's confirmation |
| V4 | **A voucher shows what the books say** | Accounts, prices and amounts come from the posted entries, never typed into the form |
| V5 | **One print gives every copy** | The PDF holds each *liên*, labelled with who keeps it |
| V6 | **Forms can change without data changes** | A form's layout lives in one template; no stored data depends on it |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| *Phiếu nhập kho*, *Phiếu xuất kho* (any operation type) | In | V1 |
| *Phiếu thu*, *Phiếu chi* (cash journals, VND) | In | V2 |
| Purchase order and request for quotation, in Vietnamese | In | V3 |
| Compact purchase order (one row per style) | In | A company requirement (D9) |
| Blanket order, processing contract | In | V3 |
| *Biên bản giao nhận hàng hóa* | In | Goods sent to subcontractors (§5.5) |
| *Purchase Template* agreements | Out | Internal, never sent for signature (§2) |
| Sales order form | Out | Not required by law, not asked for (§3) |
| Bank vouchers | Out | The bank's own documents (*ủy nhiệm chi*, *giấy báo Nợ/Có*) are the vouchers |
| Foreign-currency cash (*tỷ giá*, *số tiền quy đổi*) | Out | All cash is VND |
| Digital signatures | Out | Paper and hand signatures in v1 (D2, §9) |
| Prices on production transfers (*Pick Components*, *Store Finished Product*) | Out | Internal moves carry no value (§2, §5.4) |

## 2. Facts that shape the design

Checked against the running code and database on 2026-11-12 and 13.

| Fact | Consequence |
|---|---|
| The Print menu sends each report action that has a `domain` to `ir.actions.report.get_valid_action_reports`, which keeps it when one selected record matches (`web/static/src/search/action_menus/action_menus.js:141-166`, `odoo/addons/base/models/ir_actions_report.py:1179-1191`). The domain may follow relations (`filtered_domain`) | **Each form is its own report action, shown only on the records it fits:** *Phiếu nhập kho* only on inbound operation types, *Phiếu thu* only on cash-in entries |
| `web.basic_layout` exists beside the company's external layout (`web/views/report_templates.xml:861`) | Forms use the basic layout and draw their own header (*Đơn vị*, *Mẫu số*). The company's letterhead layout is not used |
| `num2words` in the image reads Vietnamese correctly: *một triệu năm nghìn*, *một trăm lẻ năm*, *hai mươi mốt*. Core's `res.currency.amount_to_text` capitalises every word and VND's unit label is *Dong* in both languages (`odoo/addons/base/models/res_currency.py:177-190`; database) | **An amount-in-words helper of our own:** first letter capitalised, followed by *đồng* (§4.3) |
| `wkhtmltopdf 0.12.6.1 (with patched qt)` | Page breaks between copies and repeated table headers on long vouchers work |
| Garment company, WH Chi Lăng: receipts and deliveries are one step; manufacturing is three steps (`pbm_sam`). Done transfers on this database: *Store Finished Product* 1,434, *Pick Components* 1,338, *Delivery Orders* 65, *Receipts* 56, *Resupply Subcontractor* 30, *Consumption* 2 | The busiest vouchers are production's. **Which voucher an operation type prints is configured on the type** (§5.1) |
| A stock move's valuation entries and layers are linked to it: `stock.move.account_move_ids` and `stock_valuation_layer_ids` (`stock_account/models/stock_move.py:19-20`) | Prices, amounts and *Nợ/Có* are read from them (§5.4) |
| Entries posted by transfers of the garment company on this database: receipts mostly **Nợ 1520 / Có 3399** (145; 3399 is *Goods Received Not Purchased*, and 331 appears with the bill); deliveries mostly **Nợ 1599 / Có 1550** (398; 1599 is *Goods Issued Not Invoiced*, and 632 is posted with the customer invoice); consumption Nợ 6273 / Có 1550. Components are posted Nợ 1541 / Có 1520 when the MO is done | The voucher prints the accounts as posted, 3399 and 1599 included (D5, O7) |
| *Pick Components* (WH/Stock → WH/Pre-Production) and *Store Finished Product* (WH/Post-Production → WH/Stock) move between internal locations and create no layer or entry | Their vouchers carry quantities only; accounting fills in values by hand (§5.4) |
| *Resupply Subcontractor* moves WH/Stock → *Subcontracting Location*, an internal location (`is_subcontracting_location`); its transfers carry the subcontractor as partner and post no entry (WH/RES/00063–67) | Material sent to a subcontractor prints a quantity-only *Phiếu xuất kho* naming the subcontractor as receiver (§5.1) |
| A payment's counterpart can only be a receivable or payable account (`account/models/account_payment.py:134-140`). CSH1's payment methods post to 1131/1132 (money in transit), not 1111 | Advances, petty expenses, withdrawals and cash wages cannot be payments, and a cash payment would not touch 1111. **Cash vouchers belong to cash journal entries; the Pay button stays unused** (D3) |
| A bill's *Outstanding debits* lists any unreconciled payable line of its partner from any posted entry, whatever the journal (`account/models/account_move.py:1410-1430`) | A bill is paid in cash by posting Nợ 331 / Có 1111 in the cash journal and adding it from the bill. No payment record is needed |
| `account_reconcile_oca` is installed | Statement lines in a cash journal also create cash journal entries, so they print vouchers too |
| A journal's `payment_sequence` separates payments from other entries but not money in from money out (`account/models/account_move.py:3721-3729`) | **Separate PT and PC numbers are a field of our own** (§4.4, D4) |
| `purchase.requisition.requisition_type` is *Blanket Order* or *Purchase Template* (`purchase_requisition/models/purchase_requisition.py:21-22`). Core prints both with one report (`purchase_requisition/report/purchase_requisition_report.xml`). No agreements exist yet | The blanket order form shows only on blanket orders (§6.3) |
| `purchase_product_matrix` is installed. *Print Variant Grids* (`report_grids`, on by default) adds a size × colour grid per style **after** the order's details, and the full line list still prints (`purchase_product_matrix/models/purchase.py:142-160`, `report/purchase_order_templates.xml`). 204 product templates have several variants | The compact order replaces the lines of a style with one row and keeps core's grid under it (§6.2) |
| Purchase orders on this database: 58 done, 2 draft, 3 cancelled. The confirmation date is `date_approve`, the vendor's reference `partner_ref` | Request for quotation and purchase order share one form with two titles (§6.1) |

## 3. The law

- **Circular 99/2025/TT-BTC** (in force 01/01/2026, replacing Circular 200) lets a company use its own
  voucher forms when they hold the content the Accounting Law requires (confirmed, Peter, 2026-11-13).
  Listing the forms in the company's accounting regulations (*quy chế*) is useful, not required. 01-VT,
  02-VT, 01-TT and 02-TT remain as reference forms. The required content, and where each form holds it:

  | Required content | Where on our forms |
  |---|---|
  | Name and number of the voucher | Title; *Số* |
  | Date it is made | *Ngày … tháng … năm …* |
  | Name and address of the company, and of the party receiving the voucher (customer, supplier, person delivering or receiving) | *Đơn vị*, *Địa chỉ*; the partner or the named person and address. Internal receivers (a workshop) are written by hand |
  | What the transaction is | *Lý do* / *Nội dung*: the operation type's reason, or the transfer's own (§5.1); the cash entry's reference |
  | Quantities, unit prices and amounts in figures; for *Phiếu thu* and *Phiếu chi* the total also in words | The lines and *Cộng*; the amount in words on every voucher that has values |
  | Signatures and full names of the preparer, the approver and the people concerned (cashier, storekeeper, person delivering or receiving) | The signature row, each role with *(Ký, họ tên)* |
- **Purchase and sales orders are not accounting vouchers,** and no rule requires them. A purchase order the
  supplier accepts in writing documents the contract. A written contract is part of the file for deducting
  input VAT on purchases paid later, and since 01/07/2025 (Decree 181/2025) input VAT on a purchase of
  5 million đồng or more, VAT included, is deductible only when paid by bank. Whether an accepted order
  counts as a contract under the Commercial Law was not confirmed. Hence the supplier-confirmation block on
  the purchase order (§6.1).
- Bank movements need no voucher of ours: the bank's documents are the vouchers.

## 4. The shared layout (`l10n_vn_voucher`)

### 4.1 Page

A4 portrait, through a paper format of the module's own (margins about 10 mm, no header space, since the
form draws its own header). Every form is printed in Vietnamese whatever the user's language
(`t-lang="'vi_VN'"`), so product names come out in Vietnamese too (D11). Core's English prints stay
for foreign suppliers.

### 4.2 Building blocks

QWeb templates that every form calls:

| Block | Content |
|---|---|
| Header | Left: *Đơn vị* (company name), *Địa chỉ*, *Bộ phận* (given by the form, or a dotted line). Right: the form code only, *Mẫu số 01-VT*, *02-VT*, *01-TT* or *02-TT*, with no circular named (D13) |
| Title | The form's title, its date (*Ngày … tháng … năm …*), the copy label, and the box with *Số*, *Nợ*, *Có* |
| Dotted line | Prints the value when there is one, a dotted line to fill in by hand when there is none |
| Amount in words | *Tổng số tiền (viết bằng chữ)* from §4.3 |
| Signatures | A row of roles, each with *(Ký, họ tên)* and, when the form knows it, the printed name under the signing space |
| Copies | Repeats the form once per configured copy, each on new pages, labelled (§4.5) |

### 4.3 Amount in words

A method on `res.currency`, `l10n_vn_amount_to_words(amount)`: for VND, the amount rounded to the đồng,
read by `num2words(lang="vi")`, first letter capitalised, followed by *đồng*:
*Một triệu năm nghìn đồng*. For any other currency it returns nothing and the form prints a dotted line.

### 4.4 Cash vouchers

**Which entries.** A posted `account.move` in a journal of type *cash*. Its **cash lines** are the lines on
the journal's own account (`default_account_id`, 1111 for CSH1).

| Cash lines | Voucher |
|---|---|
| All debit | *Phiếu thu* |
| All credit | *Phiếu chi* |
| Both | None. Printing is refused: split the entry, one per direction |
| None | None |

**Fields on `account.move`:**

| Field | Type | Rule |
|---|---|---|
| `l10n_vn_voucher_kind` | Selection: *cash_in*, *cash_out* | Set at posting from the table above; empty otherwise |
| `l10n_vn_voucher_number` | Char, read-only, not copied | Given at the first posting from the journal's series for that kind. Kept when the entry is reset and posted again; replaced by a new number only if the kind changed. Unique per journal |
| `l10n_vn_voucher_person` | Char | *Họ và tên người nộp/nhận tiền*. Empty: the partner of the other lines when they have exactly one |
| `l10n_vn_voucher_address` | Char | *Địa chỉ*. Empty: that partner's address |

They show on the entry's form for cash journals.

**Series.** Two sequences per cash journal, `l10n_vn_cash_in_sequence_id` and `l10n_vn_cash_out_sequence_id`
on `account.journal`, created as superuser the first time the journal needs them: prefixes
`PT/%(range_year)s/` and `PC/%(range_year)s/`, four digits, a new range each year, no gaps. They are
ordinary sequences and can be edited from the journal (D4).

**The form.**

| Form field | From |
|---|---|
| *Đơn vị*, *Địa chỉ* | Company |
| *Quyển số* | Journal name |
| *Số* | `l10n_vn_voucher_number` |
| *Ngày* | Entry date |
| *Nợ*, *Có* | *Phiếu thu*: Nợ the cash account, Có the other lines' accounts. *Phiếu chi*: the reverse. With several other accounts, each prints with its amount |
| *Họ và tên người nộp / nhận tiền*, *Địa chỉ* | The person and address fields, or a dotted line |
| *Lý do nộp / chi* | Entry reference (`ref`) |
| *Số tiền*, *(Viết bằng chữ)* | Total of the cash lines |
| *Kèm theo … chứng từ gốc* | Dotted line |
| Signatures | *Phiếu thu*: Giám đốc, Kế toán trưởng, Người nộp tiền, Người lập phiếu, Thủ quỹ. *Phiếu chi*: Giám đốc, Kế toán trưởng, Thủ quỹ, Người lập phiếu, Người nhận tiền. *Người lập phiếu* prints the name of the entry's creator |
| Below | *Đã nhận đủ số tiền (viết bằng chữ)*: dotted line |

Two report actions on `account.move`, *Phiếu thu* and *Phiếu chi*, with domains on `l10n_vn_voucher_kind`.

### 4.5 Copies (*liên*)

A copy list is a text field with **one label per line, one line per copy**: three lines print three copies.
Each copy prints its label under the title, such as *Liên 2: Thủ kho giữ để ghi thẻ kho, sau đó chuyển cho
kế toán*. An empty list prints one copy without a label. The modules ship no labels; each company enters its
own (D6). Lists live on the operation type (§5.1) and on the cash journal (`l10n_vn_cash_in_copies`,
`l10n_vn_cash_out_copies`).

Recommended configuration, after the company's practice of one copy each for the other party, the
storekeeper and accounting (Peter, 2026-11-13). *Phiếu chi* has two copies: the person receiving the cash
signs it and keeps none, as on the old pads; a third line adds one when wanted.

| Form | Copies | Liên 1 | Liên 2 | Liên 3 |
|---|---|---|---|---|
| *Phiếu nhập kho* | 3 | Kế toán lưu | Thủ kho giữ để ghi thẻ kho | Giao cho người giao hàng |
| *Phiếu xuất kho* | 3 | Kế toán lưu | Thủ kho giữ để ghi thẻ kho | Giao cho người nhận hàng |
| *Phiếu thu* | 3 | Kế toán lưu | Thủ quỹ giữ để ghi sổ quỹ | Giao cho người nộp tiền |
| *Phiếu chi* | 2 | Kế toán lưu | Thủ quỹ giữ để ghi sổ quỹ | — |

## 5. Stock vouchers (`l10n_vn_voucher_stock`)

### 5.1 Configuration on `stock.picking.type`

| Field | Type | Meaning |
|---|---|---|
| `l10n_vn_voucher_kind` | Selection: *in* (*Phiếu nhập kho*), *out* (*Phiếu xuất kho*) | Empty: the type prints no voucher |
| `l10n_vn_voucher_reason` | Char, translatable | *Lý do nhập / xuất kho*, such as *Xuất nguyên liệu cho sản xuất* |
| `l10n_vn_voucher_copies` | Text | The copy list (§4.5) |
| `l10n_vn_handover_report` | Boolean | The type's transfers also print the *Biên bản giao nhận hàng hóa* (§5.5) |

Nothing is set at install (D6). For WH Chi Lăng the expected setting is: *in* for Receipts and Store
Finished Product; *out* for Delivery Orders, Pick Components, Consumption and Resupply Subcontractor
(Peter, 2026-11-13).

Material sent to a subcontractor travels with this *Phiếu xuất kho*, the processing contract or the
subcontracting order (§6.1), and a *Biên bản giao nhận hàng hóa* (§5.5). It is not one of the cases the
law requires a *phiếu xuất kho kiêm vận chuyển nội bộ* for (Peter, 2026-11-13).

**The transfer's own reason.** One reason per type does not fit every transfer: a return to a supplier
uses the receipt type's return type, a customer return comes in through Receipts (25 returns on this
database). On `stock.picking`:

| Field | Type | Meaning |
|---|---|---|
| `l10n_vn_voucher_reason` | Char | *Lý do* for this transfer. Empty: for a return (`return_id`, `stock/models/stock_picking.py:558`) *Trả lại hàng theo phiếu* and the original transfer's reference; otherwise the operation type's reason |

It shows on the transfer's form for types with a voucher kind.

### 5.2 Which transfers

Two report actions on `stock.picking`, *Phiếu nhập kho* and *Phiếu xuất kho*, with domains
`[('picking_type_id.l10n_vn_voucher_kind', '=', 'in'), ('state', '!=', 'cancel')]` and the same for *out*.
A transfer prints in any other state: before validation the storekeeper fills in the actual quantities by
hand, and after validation the print is the voucher of record.

### 5.3 The form

| Form field | From |
|---|---|
| *Đơn vị*, *Bộ phận* | Company; warehouse name |
| *Số* | Transfer reference (`name`) (D7) |
| *Ngày* | `date_done`; a dotted date when not done |
| *Nợ*, *Có* | §5.4 |
| *Họ và tên người giao / nhận hàng*, *Địa chỉ (bộ phận)* | The transfer's partner and address; dotted lines when it has none (production) |
| *Lý do nhập / xuất kho* | The transfer's reason, as §5.1 resolves it |
| *Theo … số … ngày … của …* | *Phiếu nhập kho* only. *số*: the source document (`origin`); *của*: the partner; *ngày*: dotted |
| *Nhập / xuất tại kho*, *Địa điểm* | Warehouse; destination location (*in*) or source location (*out*) |
| Lines | One row per stock move: *STT*; *Tên, nhãn hiệu, quy cách* (product name with its variant values, no code); *Mã số* (internal reference); *Đơn vị tính*; *Số lượng theo chứng từ* (demand, `product_uom_qty`); *Thực nhập / Thực xuất* (`quantity`, when done); *Đơn giá*; *Thành tiền* |
| *Cộng* | Sum of *Thành tiền* |
| *Tổng số tiền (viết bằng chữ)* | §4.3, from *Cộng*; dotted when there are no values |
| *Số chứng từ gốc kèm theo* | Dotted line |
| Signatures | *Phiếu nhập kho*: Người lập phiếu, Người giao hàng, Thủ kho, Kế toán trưởng (hoặc bộ phận có nhu cầu nhập). *Phiếu xuất kho*: the same with Người nhận hàng, plus Giám đốc. *Người lập phiếu* prints the transfer's responsible (`user_id`) |

### 5.4 Values and accounts

Only for a done transfer, and only from what was posted (V4, D12):

- **A row's amount** is the absolute sum of its move's valuation layers (`stock_valuation_layer_ids.value`),
  landed costs included. **Its price** is that amount divided by the quantity done. A move without layers,
  such as a consumable or an internal move, prints both blank.
- **Nợ / Có** are the debit and the credit accounts of the posted entries of the transfer's moves
  (`account_move_ids`), each listed once, by code.
- Internal transfers, *Pick Components* and *Store Finished Product* among them, print quantities only. The
  values posted when the manufacturing order is done are not traced back in v1 (§9).

### 5.5 *Biên bản giao nhận hàng hóa*

A handover record both parties sign when goods change hands, printed from a transfer of a type with
`l10n_vn_handover_report` (Resupply Subcontractor first; Delivery Orders when a customer asks for one). Not
an accounting voucher: no prices, no accounts, no *liên*.

| Part | Content |
|---|---|
| Title | *BIÊN BẢN GIAO NHẬN HÀNG HÓA*; *Số* (transfer reference); *Ngày* (`date_done`, dotted when not done) |
| *Căn cứ* | The source document (`origin`): the order or subcontracting order |
| Parties | **Bên giao** and **Bên nhận**: company and partner by direction, each with name, address, tax code, and dotted lines for the representative's name and position |
| Place | The partner's address |
| Lines | *STT*, product name, *Mã số*, *ĐVT*, *Số lượng* (done, or demand before validation), *Ghi chú* (dotted, for the goods' condition) |
| Closing | *Biên bản được lập thành 02 bản, mỗi bên giữ 01 bản, có giá trị như nhau.* |
| Signatures | **ĐẠI DIỆN BÊN GIAO** and **ĐẠI DIỆN BÊN NHẬN**, each *(Ký, ghi rõ họ tên)* |

One report action on `stock.picking`, *Biên bản giao nhận hàng hóa*, with domain
`[('picking_type_id.l10n_vn_handover_report', '=', True), ('state', '!=', 'cancel')]`.

## 6. Purchase forms (`l10n_vn_purchase_report`)

Printed in Vietnamese beside core's English prints, which stay. Amounts in words only for VND orders.

### 6.1 Purchase order

One report action on `purchase.order`, *Đơn đặt hàng (VN)*. Titled *YÊU CẦU BÁO GIÁ* before confirmation
and *ĐƠN ĐẶT HÀNG* after (states *purchase* and *done*). An order for subcontracted products, a line whose
product has a subcontracting bill of materials for the vendor (`mrp_subcontracting` is installed), is
titled *ĐƠN ĐẶT HÀNG GIA CÔNG* (D18).

| Part | Content |
|---|---|
| Header | Our company (*Bên mua*: name, address, tax code); *Số* (order reference); *Ngày* (`date_approve`, or `date_order` before confirmation) |
| Supplier | *Bên bán*: name, address, tax code, contact; *Số tham chiếu của nhà cung cấp* (`partner_ref`) |
| Terms | Expected arrival (`date_planned`), delivery address (the receipt type's warehouse, or the drop-ship address), payment terms |
| Lines | *STT*, product name, *Mã số*, *ĐVT*, *Số lượng*, *Đơn giá*, *Thuế*, *Thành tiền* (untaxed) |
| Totals | *Cộng tiền hàng*, *Thuế GTGT*, *Tổng cộng*, amount in words |
| Notes | The order's terms (`notes`) |
| Agreement | An order placed under a blanket order prints *Theo hợp đồng nguyên tắc số …* with the agreement's reference (`requisition_id`, `purchase_requisition/models/purchase.py:26`) |
| Signatures | **Bên mua:** Người lập phiếu, Phụ trách mua hàng, Giám đốc (Peter, 2026-11-13). **Xác nhận của nhà cung cấp** *(Ký, ghi rõ họ tên, đóng dấu)* |

### 6.2 Compact purchase order

A second report action, *Đơn đặt hàng gọn (VN)*: the same form, but the lines of each product with several
variants are grouped into **one row per style, unit, price and taxes**: the style's name and code,
the total quantity, the price and the summed amount. Core's quantity grid for that style
(`product_matrix.matrix`, from `get_report_matrixes`) prints beneath the lines table. Products without
variants print as single rows, as on the full form.

### 6.3 Blanket order

Odoo's *Blanket Order* is the agreement for recurring purchases: prices, and optionally quantities, agreed
with one vendor for a period, with each delivery ordered by a purchase order that draws on it. Those orders
print with the purchase order form (§6.1). The blanket order itself is the one document that holds the
agreed prices and period, and the only one the vendor signs for them, so it has a form too. That form is
the purchase order's layout with the agreement's fields, not a design of its own. Its title is *HỢP ĐỒNG
NGUYÊN TẮC* (Peter, 2026-11-13). *Purchase Template* agreements are internal and get no form.

**Processing contract.** A blanket order with a subcontractor for subcontracted products is the processing
contract: its lines are the finished products at the agreed processing price, and the orders drawn on it
are the *đơn đặt hàng gia công* (§6.1). By the same rule as §6.1, a blanket order with a line whose product
has a subcontracting bill of materials for the vendor is titled *HỢP ĐỒNG GIA CÔNG*, and prints an appendix,
*Định mức nguyên phụ liệu*: for each such product, the components of that bill of materials with their
quantity per unit of the product and their unit (D19). The contract's other terms (losses, leftover
material, quality, payment) are the agreement's *Terms*. Where the company keeps a contract drafted
outside Odoo, this print serves as its appendix of products, prices and material norms.

One report action on `purchase.requisition`, *Hợp đồng nguyên tắc (VN)*, with domain
`[('requisition_type', '=', 'blanket_order')]`.

| Part | Content |
|---|---|
| Header | *Số* (agreement reference), *Ngày*, validity (`date_start` – `date_end`), the vendor's reference (`reference`) |
| Parties | *Bên mua* (our company), *Bên bán* (`vendor_id`): name, address, tax code |
| Lines | *STT*, product name, *Mã số*, *ĐVT*, agreed quantity (`product_qty`), *Đơn giá* (`price_unit`) |
| Terms | The agreement's terms (`description`) |
| Signatures | **ĐẠI DIỆN BÊN MUA** and **ĐẠI DIỆN BÊN BÁN**, each *(Ký, ghi rõ họ tên, đóng dấu)* |
| Appendix | Processing contracts only: *Định mức nguyên phụ liệu*, one table per subcontracted product (*STT*, component, *Mã số*, *ĐVT*, quantity per unit of the product) |

## 7. Links to other modules

- **Payroll.** `l10n_vn_payroll_account` should post cash wages and advances in a cash journal against the
  cash account; each such entry then prints its *Phiếu chi* with no further work. To be recorded in the
  payroll technical design when its posting is specified.
- **Signed copies.** A signed voucher is scanned and attached to its record's chatter. No code.

## 8. Refusals and edge cases

| Case | Behaviour |
|---|---|
| Cash entry that both receives and pays cash | No kind or number; printing raises *split the entry* |
| Cash entry whose kind changes after a reset to draft | New number of the new kind at the next posting; the old number is not reused |
| Cancelled transfer | The stock voucher is not offered |
| Transfer not done | Prints without date, actual quantities, values or accounts |
| Operation type without a voucher kind | No stock voucher offered |
| Order in a currency other than VND | Amounts in that currency; no amount in words |

## 9. Later

- **Values on production vouchers,** read from the manufacturing order once it is done
  (`stock.picking.production_ids`, `mrp/models/stock_picking.py:139`).
- **Digital signatures.** Vietnamese law accepts electronic vouchers signed with digital signatures (USB
  token or remote signing such as VNPT SmartCA or Viettel MySign). It needs a signing service for each
  signer and a PDF-signing module, which OCA does not offer for 18.0. A project of its own.
- **Signer names from configuration** (director, chief accountant), if printed names are wanted under every
  role.
- **Sales order form,** if a customer asks for one.

## 10. Decisions

| # | Decision |
|---|---|
| D1 | **The company's own forms,** modelled on 01-VT, 02-VT, 01-TT, 02-TT and refined after use (Peter, 2026-11-12) |
| D2 | **Printed and signed by hand;** the signed scan is attached to the record. No digital signatures in v1 |
| D3 | **Cash vouchers are printed from cash journal entries, not payments.** The Pay button stays unused (Peter, 2026-11-13) |
| D4 | **Separate PT and PC series per cash journal,** yearly, no gaps (Peter, 2026-11-13) |
| D5 | **Vouchers print the accounts as posted,** including 3399 on receipts and 1599 on deliveries (Peter, 2026-11-13; account names may be changed later) |
| D6 | **Copies and their labels are configured per operation type and per cash journal,** one label per line; nothing seeded (Peter, 2026-11-13, labels wanted) |
| D7 | **A stock voucher's number is the transfer reference** (Peter, 2026-11-12) |
| D8 | **A4 portrait** for every form (Peter, 2026-11-12) |
| D9 | **Purchase order, compact purchase order and blanket order forms,** mainly for their signature blocks (Peter, 2026-11-13) |
| D10 | **Signer roles are fixed in the templates,** changed by editing them |
| D11 | **Forms print in Vietnamese only;** core's English prints remain for foreign suppliers |
| D12 | **Values come only from posted valuation;** internal transfers print quantities only |
| D13 | **The header prints the form code** (*Mẫu số 01-VT* …) without naming a circular (Peter, 2026-11-13) |
| D14 | **Material sent to a subcontractor prints a *Phiếu xuất kho*** (Peter, 2026-11-13) |
| D15 | **The blanket order prints the purchase order's layout as a *hợp đồng nguyên tắc*;** orders under it name it (§6.3; title Peter, 2026-11-13) |
| D16 | **A transfer may carry its own reason;** returns name their original transfer (§5.1) |
| D17 | **A *Biên bản giao nhận hàng hóa* prints from transfers of the types that ask for it** (§5.5) |
| D18 | **A purchase order for subcontracted products is titled *Đơn đặt hàng gia công*** (§6.1) |
| D19 | **A blanket order for subcontracted products is the processing contract,** titled *Hợp đồng gia công*, with the material norms from the subcontracting bill of materials as its appendix (§6.3; Peter, 2026-11-13) |

## 11. Steps (provisional)

| # | Module | Scope |
|---|---|---|
| 1 | `l10n_vn_voucher` | Paper format, layout blocks, amount in words (§4.1–4.3, §4.5). Installed together with step 2, which is the first form that uses them |
| 2 | `l10n_vn_voucher_stock` | Operation-type settings, the transfer's reason; *Phiếu nhập kho* and *Phiếu xuất kho* (§5.1–5.4) |
| 2b | `l10n_vn_voucher_stock` | *Biên bản giao nhận hàng hóa* (§5.5) |
| 3 | `l10n_vn_voucher` | Cash-entry fields, series, *Phiếu thu* and *Phiếu chi* (§4.4) |
| 4 | `l10n_vn_purchase_report` | Purchase order and compact purchase order (§6.1, §6.2) |
| 5 | `l10n_vn_purchase_report` | Blanket order and processing contract (§6.3) |

Tests render each report to HTML (`ir.actions.report._render_qweb_html`) in a `TransactionCase` and check
its content: the number, accounts, amounts, words and copy labels. Tests that create products, partners or
companies are `post_install`. None imports a core module's `tests` package.

## 12. References

| Source | Used for |
|---|---|
| `odoo/odoo/addons/base/models/ir_actions_report.py`, `web/static/src/search/action_menus/action_menus.js` | Report domains (§2) |
| `odoo/odoo/addons/base/models/res_currency.py` | Core's amount in words, not used (§4.3) |
| `odoo/addons/web/views/report_templates.xml` | `web.basic_layout` (§4.1) |
| `odoo/addons/stock_account/models/stock_move.py` | Layers and entries per move (§5.4) |
| `odoo/addons/account/models/account_payment.py`, `account_move.py` | Payment limits, outstanding lines, payment numbering (§2, §4.4) |
| `odoo/addons/purchase_requisition/models/purchase_requisition.py` | Agreement types and fields (§6.3) |
| `odoo/addons/purchase_product_matrix`, `odoo/addons/product_matrix` | The variant grid (§6.2) |
| Circular 99/2025/TT-BTC; Decree 181/2025/NĐ-CP | §3, through secondary sources |

## 13. Open questions

| # | Question | Settles |
|---|---|---|
None. Settled on 2026-11-13: O1 (§3), O2 (D13), O3 (§4.5), O4 (§5.1), O5 (§6.1), O6 (§6.3), O7 (D5).
