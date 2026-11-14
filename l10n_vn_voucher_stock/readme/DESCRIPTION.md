Prints the Vietnamese stock vouchers from transfers: *Phiếu nhập kho* (form 01-VT) and *Phiếu
xuất kho* (form 02-VT), on the shared layout of `l10n_vn_voucher`.

Each operation type says which voucher its transfers print, the reason (*lý do*) printed on it, and
its copies (*liên*). Quantities come from the transfer. Prices, amounts and the accounts (*Nợ*,
*Có*) come from the valuation Odoo posted when the transfer was validated, so the voucher shows
what the books say. Transfers between internal locations, such as picking components for
production or storing finished goods, post nothing and print quantities only.
