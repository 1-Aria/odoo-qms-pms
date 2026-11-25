# Processing — Step-by-step Guide

Draft in English for testing; Vietnamese after review. Each case gives the screens to open, what to fill in, which
button to press, and what you should see. Menu paths are those of the English interface; operation types are given
with their Vietnamese name first and the English one in brackets.

Cases: **1.** Contract processing for the trading company · **2.** Order processing for a customer ·
**3.** Buying subcontracting (Nhà Bàng) · **4.** Own production and own sales · **5.** Scrap and downgrade ·
**6.** Inventory count · **7.** Using the trading company's goods ourselves · **8.** Staff sales of seconds.

*Inventory → Reporting* (Locations, Moves History, Valuation) and *Company Material in Processing* need
*Inventory Administrator* rights. Warehouse staff see owners on the transfers themselves.

**Never deliver or move more than *Check Availability* reserved.** Odoo does not stop it: the extra quantity leaves
under the transfer's owner and leaves negative stock of that owner, to be corrected by a count.

---

## How to see who owns goods

| Where | What you see |
|---|---|
| On any transfer, a product line → the **details icon** (≡) at the end of the line | Column **Owner**: *Công ty TNHH DV TM Quang Phương* = the trading company's goods; a customer's name = that customer's; **empty = ours**. Read-only on deliveries and internal transfers: reservation chooses it |
| On a receipt | Field **Owner** in the header |
| The MO's *Component Status* and a product's *On Hand* | **Not by owner**: they count every owner's stock. Do not use them to decide whether we have enough of our own (see 1.2a) |
| *Inventory → Reporting → Locations*, then *Group By → Owner* | Stock on hand per owner |
| *Inventory → Reporting → Moves History*, search the transfer's reference | Every line done, with column **Owner** |
| *Inventory → Reporting → Valuation* | Only our goods appear here. Goods owned by others never do |

---

## Case 1 — Contract processing for the trading company (*gia công dài hạn*)

The trading company sends material without a purchase order; we make goods for it; its goods go out without a sales
order; once a month we invoice it the processing fees and any of our material we used.

### 1.1 Receive the trading company's material

1. *Inventory → Operations → Transfers → Receipts* → **New**.
2. **Operation Type**: *Nhận hàng Công ty TM* (Trading Company Receipts).
3. **Receive From**: *Công ty TNHH DV TM Quang Phương*.
4. Check: **Owner** shows *Công ty TNHH DV TM Quang Phương* by itself.
5. Tab *Operations* → **Add a Product**: product, **Quantity** actually received. One line per product.
6. **Mark as Todo**, then **Validate**.
7. Print: **Print → Phiếu nhập kho**, and **Biên bản giao nhận** if the delivery is handed over against a signature.

You should see:
- *Locations* grouped by owner: the quantity under *Công ty TNHH DV TM Quang Phương*.
- *Valuation*: nothing for this receipt.
- The *Phiếu nhập kho* shows quantities, **no prices or amounts** (the goods are not ours).

Do not: receive the trading company's goods from a purchase order. They would become ours and be valued.

### 1.2 Make a manufacturing order for the trading company

1. *Manufacturing → Operations → Manufacturing Orders* → **New**.
2. **Product**, **Quantity**. *Bill of Materials* fills itself.
3. Tab *Miscellaneous* → **Operation Type**: *Gia công dài hạn* (Contract Processing).
4. Check, same tab: **Goods Owner** = *Công ty TNHH DV TM Quang Phương*; **Products Belong to the Owner** ticked.
5. **Confirm**.

You should see: a *Pick Components* transfer (smart button at the top of the order, WH/PC/…).

If the MO was made on *Manufacturing* by mistake, it is our own production: it reserves only our stock and
*Check availability* finds nothing of the trading company's. While the MO is draft or confirmed, change the
*Operation Type* to *Gia công dài hạn*; *Goods Owner* follows. Then on its *Pick Components*: **Unreserve** →
**Check Availability**.

### 1.2a Own production or processing? Check our stock first

The direction is to make goods as our own whenever our material covers the order, and to process for the trading
company only when it does not.

1. Create the MO on **Manufacturing** (own production) → **Confirm**.
2. Open its *Pick Components* → **Check Availability**.
3. Everything reserved (status *Ready*): our stock covers it. Carry on as case 4.2.
4. Not everything reserved: we do not have enough. On the MO → tab *Miscellaneous* → **Operation Type**: *Gia công
   dài hạn*. On *Pick Components*: **Unreserve** → **Check Availability**. It now takes the trading company's material
   first, ours for the rest. Carry on as 1.3.

### 1.3 Pick the components

1. Open the *Pick Components* transfer (WH/PC/…).
2. **Check Availability**.
3. Check each line's **details icon** (≡), column **Owner**: the trading company's stock first; lines with an empty
   owner (ours) only for what it lacks.
4. **Validate**. Print **Phiếu xuất kho** if needed.

### 1.4 Produce

1. Back on the MO: **Check availability**.
2. Set the quantity produced, or press **Produce All** to produce everything.
3. Open the *Store Finished Product* transfer (WH/SFP/…) that follows → **Validate**.

You should see:
- *Locations* grouped by owner: the finished goods under *Công ty TNHH DV TM Quang Phương*.
- *Valuation*: no line for the finished goods. A line appears only for material of ours the order used, and its
  journal entry is **Dr 6320 / Cr 1520** (sold to the trading company, see 1.6).

### 1.5 Deliver the trading company's goods

To the trading company itself, or to its customer on its instruction.

1. *Inventory → Operations → Transfers → Deliveries* → **New**.
2. **Operation Type**: *Xuất hàng Công ty TM* (Trading Company Deliveries).
3. **Delivery Address**: whoever receives the goods (the trading company, or its customer).
4. Check: **Owner** = *Công ty TNHH DV TM Quang Phương*, by itself.
5. **Add a Product**: products and quantities.
6. **Mark as Todo** → **Check Availability**. It reserves only the trading company's goods.
7. **Validate** the reserved quantity only. If it has less than requested, deliver what was reserved and leave the
   rest as a backorder. Print **Phiếu xuất kho** (no prices) and **Biên bản giao nhận**.

You should see: no *Valuation* line, no journal entry. The trading company invoices its customer itself.

Do not: deliver its goods from a sales order or with *Lệnh giao hàng* (Delivery Orders). *Lệnh giao hàng* cannot
take them anyway.

### 1.6 Month end — accounting

**One-time setup**
1. A product category: *Inventory → Configuration → Products → Product Categories* → **New**: **Category** *Processing Services*
   (*Dịch vụ gia công*), **Parent Category** *All*, **Income Account** 5110 → save.
2. Two products, *Inventory → Products → Products* → **New**, for each:
   - **Product Type**: *Service* (never *Goods*: a goods product on a customer invoice gets a cost-of-sales line);
   - **Sales** ticked, **Purchase** unticked;
   - **Product Category**: *Processing Services*;
   - **Invoicing Policy**: *Ordered quantities*;
   - **Sales Price** 0 (prices go on the invoice);
   - **Customer Taxes**: the VAT rate the accountant applies (today 8%, as for our goods).

   Names: *Phí gia công* (processing fee) and *Vật tư cung cấp cho gia công* (our material supplied for processing).

Every month:
1. Quantities processed: *Manufacturing → Reporting → Processed Goods*. Rows are products, columns months.
2. Our material used: *Manufacturing → Reporting → Company Material in Processing*. Pivot view, total value per
   product (needs *Inventory Administrator* rights).
3. *Accounting → Customers → Invoices* → **New**:
   - **Customer**: *Công ty TNHH DV TM Quang Phương*;
   - one line *Phí gia công* per product style: description = style, quantity = quantity processed, price = the fee;
   - one line *Vật tư cung cấp cho gia công*: amount = the material value of step 2 (plus the agreed margin);
   - VAT as usual → **Confirm**, then issue the e-invoice.

Do not: invoice the material with its stock product (fabric, thread…). Odoo would add a cost-of-sales line at
standard price, although the cost was already booked when the material was used.

Entries of the month:

| Event | Entry |
|---|---|
| Our material used in its orders | Dr 6320 / Cr 1520 (at consumption, automatic) |
| Labour, overhead | stay in 622, 627; closed to cost of sales at month end |
| The invoice | Dr 131 / Cr 5110, Cr 33311 |
| Its goods received, made, delivered | none |

---

## Case 2 — Order processing for a customer (*gia công theo đơn*)

A customer orders goods made from its own material. The sales order carries the processing fee; confirming it
creates the manufacturing order and a receipt for the customer's material. The finished goods are ours until
delivered and invoiced at the fee.

### 2.0 One-time setup per product

**The finished product** (the style made for the customer):
1. *Inventory → Products → Products* → open the product (or **New**: **Product Type** *Goods*, **Track Inventory**
   ticked).
2. **Sales Price**: the processing fee per piece (include our material if we supply some).
3. Tab *Inventory* → **Routes**: tick **Replenish on Order (MTO)** and **Gia công theo đơn**; untick
   **Manufacture** and **Buy**.

**The material the customer supplies** (its fabric, its trims):
1. *Inventory → Products → Products* → open or **New** (*Goods*, **Track Inventory** ticked, a *Raw Materials*
   category, **Cost** 0).
2. Tab *Inventory* → **Routes**: tick **Replenish on Order (MTO)** and **Resupply From Customer on Order**; untick
   **Buy**.

**Material we supply** (thread, labels…): no change, it stays on **Buy**.

**The bill of materials**: *Manufacturing → Products → Bills of Materials* → **New**: the finished product, quantity,
the customer's material and ours as components → save → **Activate** (only active BoMs are used).

### 2.1 Sales order

1. *Sales → Orders → Quotations* → **New**.
2. **Customer**; order line: the finished product, quantity, unit price = the fee.
3. **Confirm**.

You should see, as smart buttons on the order: **Manufacturing** (1) and **Delivery** (1). Open the manufacturing
order:
- **Operation Type** *Gia công theo đơn* (Order Processing);
- tab *Miscellaneous*: **Goods Owner** = the customer; **Products Belong to the Owner** **not** ticked.

### 2.2 Receive the customer's material

1. *Inventory → Operations → Transfers → Receipts* → open the receipt *Resupply From Customer* (WH/SBC/…) created by
   the order (its *Source Document* is the manufacturing order).
2. **Quantity**: what actually arrived (it may be more than requested).
3. **Validate**. Print **Phiếu nhập kho** and **Biên bản giao nhận**.

You should see: **Owner** = the customer; *Locations* grouped by owner shows the material under the customer;
nothing in *Valuation*.

### 2.3 Pick and produce

As 1.3 and 1.4. On *Pick Components*, the line details show **Owner** = the customer for its material, empty for
ours.

You should see after production:
- the finished goods with **no owner** (they are ours until delivered);
- *Valuation*: the finished goods valued at **our** material only (the customer's adds no value).

### 2.4 Deliver and invoice

1. On the sales order → smart button **Delivery** → **Check Availability** → **Validate**. Print as usual.
2. On the sales order → **Create Invoice** → **Create Draft** → **Confirm**, then issue the e-invoice.

You should see in the invoice's journal entry: revenue 5110 = the fee; cost of sales **Dr 6320 / Cr 1599** = the
value of our material in the goods.

### 2.5 Return the customer's leftover material

1. *Inventory → Operations → Transfers → Deliveries* → **New**.
2. **Operation Type**: *Trả NPL cho khách* (Customer Material Returns).
3. **Delivery Address**: the customer. Check: **Owner** = the customer.
4. **Add a Product**: the leftover material and quantity.
5. **Mark as Todo** → **Check Availability** (it takes only this customer's material) → **Validate**. Print
   **Phiếu xuất kho** and **Biên bản giao nhận**.

Entries of case 2:

| Event | Entry |
|---|---|
| Customer's material received, used, returned | none |
| Our material used | Dr 1541 / Cr 1520 |
| Goods produced | Dr 1550 / Cr 1541 (our material, plus conversion cost if the BoM has minutes) |
| Delivery | Dr 1599 / Cr 1550 |
| Invoice | Dr 131 / Cr 5110, Cr 33311; Dr 6320 / Cr 1599 |

---

## Case 3 — Buying subcontracting (Nhà Bàng)

We send the trading company's material to Nhà Bàng, Nhà Bàng sews the hammocks and charges us a fee per piece. The
hammocks remain the trading company's; the fee is our cost, recovered in our processing fee (case 1.6).

### 3.0 One-time setup

- **The hammock's bill of materials**: *Manufacturing → Products → Bills of Materials* → the hammock's BoM →
  **BoM Type**: *Subcontracting*, **Subcontractors**: *Gia Công Võng Mùng (Nhà Bàng)* → **Activate**.
- **Its components** (fabric, net, cord…): tab *Inventory* → **Routes**: **Resupply Subcontractor on Order** ticked,
  so that a purchase order sends them to Nhà Bàng automatically.
- **Nhà Bàng's fiscal position** maps 3399 to 6277 (done by the go-live setup). Nothing to do.

**Why Nhà Bàng's work belongs to the trading company.** Two settings:
1. The warehouse's hidden *Subcontracting* operation type has **Goods Owner** = the trading company. Every
   subcontracted MO, whatever the subcontractor, is made on it, so it takes the trading company's material first and
   the goods it produces are the trading company's, not valued.
2. Nhà Bàng's fiscal position sends its bills to 6277 instead of 3399: the receipt of goods that are not ours books
   nothing to 3399 for the bill to clear.

**For now, all subcontracting is for the trading company.** Subcontracting our own goods (our material, goods valued
at our material plus the fee) needs the purchase order to say whose goods are processed; that change is planned
(subcontracting by purchase-order owner). Ask before placing the first such order.

**Adding another subcontractor**
1. The partner: if it is a household business without VAT invoices, the same fiscal position as Nhà Bàng. If it
   works on the trading company's goods, its fiscal position needs **3399 → 6277**: run the go-live setup script
   again, which adds it for every subcontractor named on a subcontracting BoM.
2. Its own location: on the partner, tab *Inventory* → **Subcontracting Location** → a location of its own (e.g.
   *Subcontracting / Xưởng X*). Without it all subcontractors share one location and you cannot see what each holds.
3. The BoM: **BoM Type** *Subcontracting*, the partner in **Subcontractors** → **Activate**.
4. The components: route **Resupply Subcontractor on Order**.
5. Optional: the fee on the product's *Purchase* tab as that vendor's price, so purchase orders fill it.

### 3.1 Order from Nhà Bàng

1. *Purchase → Orders → Requests for Quotation* → **New**.
2. **Vendor**: *Gia Công Võng Mùng (Nhà Bàng)*. Line: the hammock, quantity, **Unit Price** = Nhà Bàng's fee per
   piece (16,000).
3. **Confirm Order**.

You should see: a *Resupply Subcontractor* transfer (WH/RES/…) for the components, and a receipt for the hammocks.

### 3.2 Send the material to Nhà Bàng

1. *Inventory → Operations → Transfers → Internal* → open the *Resupply Subcontractor* transfer (WH/RES/…).
2. **Check Availability**. The ≡ details show **Owner** *Công ty TNHH DV TM Quang Phương*: the trading company's
   material goes first.
3. **Validate**. Print **Phiếu xuất kho** and **Biên bản giao nhận** for Nhà Bàng to sign.

### 3.3 Receive the hammocks

1. On the purchase order → **Receive Products**.
2. **Record components** if the button shows: confirm what Nhà Bàng actually used. What is not used stays at Nhà
   Bàng's location until returned.
3. **Quantity** received → **Validate**.

You should see: *Locations* grouped by owner: the hammocks under *Công ty TNHH DV TM Quang Phương*; nothing in
*Valuation*.

To bring back unused material from Nhà Bàng: *Inventory → Operations → Transfers → Internal* → **New**, from
*Subcontracting Location* to *WH/Stock*, the products and quantities → **Validate**. The owner stays as it was.

### 3.4 Nhà Bàng's bill — accounting

1. On the purchase order → **Create Bill**.
2. **Bill Date**, **Bill Reference** (Nhà Bàng's document number) → **Confirm**.

You should see: **Dr 6277 / Cr 331** for the fee (no VAT: Nhà Bàng is a household business). The fee is recovered
in the processing fee we invoice the trading company (case 1.6).

---

## Case 4 — Own production and own sales

Goods made from our own material and sold by us. Our own material is what we buy from real sellers.

### 4.1 Buy

1. *Purchase → Orders → Requests for Quotation* → **New**.
2. **Vendor**: the real seller, the one who issues the e-invoice. Never the trading company for goods it only sends
   us (those come in by case 1.1).
3. Lines, prices → **Confirm Order** → **Receive Products** → quantities → **Validate**. Print **Phiếu nhập kho**.
4. When the e-invoice arrives: **Create Bill** → **Bill Date**, **Bill Reference** = the e-invoice number → attach
   the e-invoice XML → **Confirm**.

Entries: receipt **Dr 1520 / Cr 3399**; bill **Dr 3399, Dr 1331 / Cr 331**.

### 4.2 Produce

1. *Manufacturing → Operations → Manufacturing Orders* → **New**, product, quantity.
2. Tab *Miscellaneous*: **Operation Type** *Manufacturing*; **Goods Owner** empty.
3. **Confirm** → *Pick Components* as in 1.3 → produce as in 1.4.

You should see: *Pick Components* takes only our stock (line details: **Owner** empty). If our stock is short, the
order waits; it never takes the trading company's or a customer's material. To decide between own production and
processing, see 1.2a.

Entries: **Dr 1541 / Cr 1520** (material), **Dr 1550 / Cr 1541** (finished goods, with conversion cost).

### 4.3 Sell

1. *Sales → Orders → Quotations* → **New** → customer, products, prices → **Confirm**.
2. Smart button **Delivery** → **Check Availability** (only our goods) → **Validate**. Print **Phiếu xuất kho**.
3. **Create Invoice** → **Create Draft** → **Confirm**, then issue the e-invoice.

Entries: delivery **Dr 1599 / Cr 1550**; invoice **Dr 131 / Cr 5110, Cr 33311**, **Dr 6320 / Cr 1599**.

---

## Case 5 — Scrap and downgrade

### 5.1 From a manufacturing order

1. On the MO: ⚙ **Actions → Scrap**.
2. **Product**, **Quantity**, **Source Location** (where the goods are, e.g. *WH/Pre-Production* for components).
3. **Owner** fills itself with the order's owner when that owner has the product there. Check it.
4. **Scrap Location**:
   - *Scrap* to destroy;
   - *Hạ loại 2* to downgrade: **Downgrade To** shows the seconds product (choose it the first time).
5. **Scrap** (or **Validate**).

### 5.2 In the warehouse

1. *Inventory → Operations → Adjustments → Scrap* → **New**.
2. **Product**, **Quantity**, **Source Location**, **Owner** = the owner of the goods (empty for ours).
3. **Scrap Location** as in 5.1 → **Validate**.

You should see: a downgrade creates the seconds product with **the same owner** as the goods downgraded.

Entries: our goods scrapped **Dr 6328 / Cr 1520 or 1550**; our goods downgraded **Dr 1550 / Cr 1550** (the value moves
to the seconds product); goods of others: **none**.

---

## Case 6 — Inventory count

1. *Inventory → Operations → Adjustments → Physical Inventory*.
2. Filter or search the product or location. Each line is **one product, one location, one owner**.
3. **Counted Quantity** on the line of the right owner. A product held for two owners has two lines; count each.
4. Goods found with no line: **New** → **Location**, **Product**, **Owner** (set it now: it cannot be changed after
   saving), **Counted Quantity**.
5. Select the lines → **Apply**.

Entries: our goods, shortage **Dr 6320 / Cr stock**, surplus **Dr stock / Cr 7110**; goods of others: **none**
(differences are reported to their owner).

On the test database the inventory adjustment accounts are still the old, swapped ones (shortage to 7110, surplus to
6320): the go-live setup corrects them on production only.

---

## Case 7 — Using the trading company's goods ourselves (e.g. uniforms)

Its goods become ours only when it sells them to us, with its e-invoice. The goods do not move; two documents change
the owner.

1. Agree the quantity and price; the trading company issues its e-invoice to us.
2. **Out of its stock**: *Inventory → Operations → Transfers → Deliveries* → **New** → **Operation Type** *Xuất hàng
   Công ty TM*, **Delivery Address** *Công ty TNHH DV TM Quang Phương*, the products and quantities → **Mark as
   Todo** → **Check Availability** → **Validate**.
3. **Into ours**: *Purchase → Orders → Requests for Quotation* → **New** → **Vendor** *Công ty TNHH DV TM Quang
   Phương*, the same products, the invoiced prices → **Confirm Order** → **Receive Products** → **Validate**.
   This is the only case where a purchase order names the trading company: it sold to us, with its e-invoice.
4. **Create Bill** → **Bill Reference** = its e-invoice number → attach the XML → **Confirm**.
5. Issue them: *Inventory → Operations → Transfers → Deliveries* → **New** → **Operation Type** *Consumption* →
   products → **Mark as Todo** → **Check Availability** → **Validate**.

Entries: receipt **Dr 1550 / Cr 3399**; bill **Dr 3399, Dr 1331 / Cr 331**; issue **Dr 6273 / Cr 1550**.

---

## Case 8 — Staff sales of seconds

**On hold** until the trading company is ready to invoice. The seconds (SCND…) are the trading company's goods, so
**the trading company sells them**, with its own e-invoice to each employee. We only hand them over:

1. *Inventory → Operations → Transfers → Deliveries* → **New** → **Operation Type** *Xuất hàng Công ty TM*.
2. **Delivery Address**: the employee. **Owner** = *Công ty TNHH DV TM Quang Phương* by itself.
3. The seconds products and quantities → **Mark as Todo** → **Check Availability** → **Validate**. Print **Phiếu xuất
   kho** and **Biên bản giao nhận**.

Entries in our books: **none**. The trading company invoices the employee and collects the money.
