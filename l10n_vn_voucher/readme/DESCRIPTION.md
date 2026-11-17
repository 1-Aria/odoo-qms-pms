The shared layout of the Vietnamese printed vouchers, which the company designs itself under
Circular 99/2025/TT-BTC: an A4 page with the company header and the form code (*Mẫu số*), a title
box with the voucher's number and accounts (*Số*, *Nợ*, *Có*), copies (*liên*) each labelled with
who keeps it, amounts in Vietnamese words, and signature rows.

The forms themselves come from other modules: `l10n_vn_voucher_stock` prints *Phiếu nhập kho* and
*Phiếu xuất kho* from transfers. *Phiếu thu* and *Phiếu chi* from cash journal entries are planned
in this module.

Posted entries in cash journals print their *Phiếu thu* (form 01-TT) or *Phiếu chi* (form 02-TT): an
entry whose cash lines all receive money is a receipt, one whose cash lines all pay is a payment.
Each kind has its own series per cash journal, restarting every year (`PT/2026/0001`,
`PC/2026/0001`), numbered when the entry is posted.
