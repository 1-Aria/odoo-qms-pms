**Setting up.** Open an operation type (*Inventory → Configuration → Operation Types*), tab
*Vietnamese Voucher*: choose *Phiếu nhập kho* or *Phiếu xuất kho*, enter the reason, and list the
copies, one label per line. A type with no voucher prints none.

**A transfer's own reason.** When one transfer needs another reason than its type's, enter it under
*Additional Info → Voucher Reason*. A return without its own reason prints *Trả lại hàng theo
phiếu* followed by the transfer it returns.

**Printing.** *Print → Phiếu nhập kho* or *Phiếu xuất kho*, offered on transfers whose type prints
that voucher. Before validation the voucher has no date, no actual quantities and no values, for
the storekeeper to fill in by hand; after validation it is the voucher of record. Anything Odoo
does not know prints as a dotted line. Signed copies are scanned and attached to the transfer's
chatter.
