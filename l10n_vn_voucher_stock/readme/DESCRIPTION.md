Prints the Vietnamese stock vouchers from transfers: *Phiếu nhập kho* (form 01-VT) and *Phiếu
xuất kho* (form 02-VT), on the shared layout of `l10n_vn_voucher`.

Each operation type says which voucher its transfers print, the reason (*lý do*) printed on it, and
its copies (*liên*). Quantities come from the transfer. Prices, amounts and the accounts (*Nợ*,
*Có*) come from the valuation Odoo posted when the transfer was validated, so the voucher shows
what the books say. Transfers between internal locations, such as picking components for
production or storing finished goods, post nothing and print quantities only.

Operation types can also print the *Biên bản giao nhận hàng hóa*, the handover record both parties
sign when goods change hands: the basis (*căn cứ*), the giving and receiving parties with their
representatives, the place, the goods and quantities, and both signatures. An incoming type is the
partner handing over to the company; any other type is the company handing over to the partner.

A transfer without a partner, such as a receipt of customer material created by a manufacturing
order, takes the customer of the sales order behind it on all these forms.
