**VAT codes first.** *Configuration → Accounting → E-Invoice VAT Codes* maps each VAT code an
e-invoice writes (0%, 5%, 8%, 10%, KCT, KKKNT…) to a purchase tax that excludes VAT from the price.
Leave the tax empty for a code that carries no VAT. A bill cannot be created from an e-invoice
whose codes have no row.

**A bill from its e-invoice.** On the Bills list, *Upload* the supplier's XML. The draft bill is
filled from it: supplier (found by tax code only), reference, date, lines and VAT. Its chatter says
what needs a look: no supplier found, a line whose quantity × price did not give its amount (entered
as 1 × the amount), a VAT difference larger than rounding, totals that differ. When no supplier has
the tax code, choose one on the bill or use *Create Supplier* on the e-invoice. If the upload is
refused, the reason is in the empty bill's chatter; fix it and drop the file on that bill again.
Uploading an e-invoice that is already on a bill opens nothing new and points to it.

When the supplier is found and exactly one open purchase order of that supplier has the same total,
Odoo links the bill to the order and takes the order's lines.

**Replacements and adjustments.** A replacing invoice is uploaded like any other and becomes a vendor
bill; it is linked to the invoice it replaces, in whichever order the two are read. A document whose
e-invoice has been replaced cannot be posted; if it already is, reverse it. An adjustment is always
its own document: its upload is refused, so enter the bill or refund by hand and attach the XML,
which links it to the adjusted invoice. Banners on the document and the e-invoice show what has been
replaced or adjusted, and the e-invoice lists can be filtered on it.

**Attaching an e-invoice.** Open an existing vendor bill (for example one from a purchase order),
refund, customer invoice or credit note and click *Attach E-Invoice*. Choose the XML. The dialog
shows what it read beside the document and warns when the partner's tax code, the date or the total
differs. *Attach* links the e-invoice to the document without changing it.

**Posting.** A bill or invoice carrying an e-invoice posts only when its partner has the e-invoice's
tax code. A partner without one receives it, unless another partner already holds it.

**Lists.** *Vendors → E-Invoices* lists received e-invoices, *Customers → E-Invoices* issued ones,
each with its status: not booked, draft or booked.
