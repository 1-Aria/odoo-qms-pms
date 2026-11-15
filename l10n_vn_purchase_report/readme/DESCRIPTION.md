Prints purchase orders in Vietnamese on the shared voucher layout of `l10n_vn_voucher`: both
parties (*Bên mua*, *Bên bán*), the delivery and payment terms, the lines, the totals with the
amount in words, our signers (*Người lập phiếu*, *Phụ trách mua hàng*, *Giám đốc*) and the
supplier's confirmation.

The order is titled *Yêu cầu báo giá* before confirmation, *Đơn đặt hàng* after, and *Đơn đặt
hàng gia công* when it buys subcontracted products. An order drawn on a blanket order names it.

A compact version groups the variants of each style into one row (total quantity and amount),
with Odoo's size and colour grid beneath the lines.

Blanket orders print as a *hợp đồng nguyên tắc* (framework agreement): both parties, the validity
period, the agreed products, quantities and prices grouped by style, the terms, and both parties'
signatures. When the agreement covers products the vendor makes for us under a subcontracting bill
of materials, it prints as a *hợp đồng gia công* (processing contract) between *bên đặt gia công*
and *bên nhận gia công*, with an appendix of material norms (*định mức nguyên phụ liệu*) per unit of
product, taken from the bill of materials; variants with the same norms share one table.
