Copies are configured as a list with **one label per line, one line per copy**. Three lines print
three copies, each with its label under the title, for example:

    Liên 1: Kế toán lưu
    Liên 2: Thủ kho giữ để ghi thẻ kho
    Liên 3: Giao cho người giao hàng

An empty list prints one copy without a label. Stock vouchers take their list from the operation
type.

Every form prints in Vietnamese, whatever the user's language. Anything Odoo does not know prints
as a dotted line to fill in by hand. Signed vouchers are scanned and attached to their record's
chatter.

**Cash vouchers.** Odoo lets journal entries keyed in by hand use only *Miscellaneous* journals, so
cash movements are entered as transactions of the cash journal (statement lines): creating one posts
its entry and numbers it; reconciling it (choosing the bill or the counterpart account) keeps the
number. Open the transaction's journal entry to print. *Print → Phiếu thu* or *Phiếu chi*. The person paying or receiving and
their address default to the partner on the other lines; to name someone else, fill them in on the
entry's *Other Info* tab. The reason is the entry's *Reference*. Copies are set per cash journal, on
its *Vietnamese Vouchers* tab. An entry that both receives and pays cash prints no voucher: split it
into one entry per direction.
