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
