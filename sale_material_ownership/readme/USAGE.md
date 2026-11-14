1. Mark the material categories with *Counts as Material* (sub-categories are marked one by one). Each
   should use real-time valuation with the stock input account 3399, so the transfer bills map to the
   clearing account.
2. Create a fiscal position for the material owner's bills (*Accounting → Configuration → Fiscal
   Positions*): *Detect Automatically* off; *Account Mapping* 3399 → 33889; no tax mapping.
3. In *Sales → Configuration → Settings*, block *Material Ownership*, set the ownership start (orders
   confirmed earlier are out of scope), the material owner and that fiscal position.
4. Attach the e-invoice XML to every material bill with *Attach e-invoice*. A bill without a correct
   e-invoice does not count.
5. Create a batch under *Sales → Orders → Material Transfer Batches* and click *Add Uncovered Orders*, or
   add orders by hand. Read the warning above the batch, then click *Request* (Accounting / Invoicing).
6. Send the requested materials to the material owner. When its e-invoice arrives, open the draft bill
   from the batch's *Bills* button, match the quantities to the e-invoice, post it and attach the XML.
   The batch turns *Covered*; deliver its orders and issue their invoices.
7. When the rest of an order line will not ship, or goods came back, lower the line's quantity to what
   was delivered: its unused materials return to the balance.
8. *Sales → Reporting → Material Ownership* shows the balance per material.
