# Processing Invoice and Own Subcontracting — Design

Nov 27, 2026 · @Peter · Status: draft for review

Two follow-ups of `Processing for an Owner — Design.md`: the switch to subcontracting our own goods (its §6
step 1.2) and the periodic invoice of contract processing (its step 2). Principle (Peter, 2026-11-27): the
arrangement with the trading company is not expected to last or to be repeated with others, so what serves only
it is **configuration or a suggestive tool**, uninstallable without consequence. The generic mechanics
(`stock_picking_type_partner_owner`, `mrp_production_partner_owner`) stay.

---

## 1. Own subcontracting: a configuration switch, no code (former step 1.2)

No period is expected in which our own goods and the trading company's are subcontracted side by side (Peter,
2026-11-27). Subcontracting our own goods is then standard Odoo: the subcontracted MO without owner consumes our
material, the receipt is valued at our material plus the fee (the fee as the MO's extra cost, credited to 3399,
`mrp_subcontracting_account/models/stock_move.py:31`), and the subcontractor's bill clears 3399.

**The switch**, once the last subcontracting for the trading company is received and billed:

| # | Setting | Change |
|---|---|---|
| 1 | The warehouse's *Subcontracting* operation type (hidden: *Inventory → Configuration → Operation Types*, filter *Archived*) | clear **Goods Owner** |
| 2 | Each subcontractor's fiscal position (Nhà Bàng: *Hộ cá nhân – không hóa đơn*) | remove the mapping **3399 → 6277** |

Order matters: a bill of a receipt made before the switch (the trading company's goods, nothing in 3399) still
needs the mapping; one made after (our goods, valued) must not have it. Hence the switch after the last such bill.
Subcontracted MOs still open at the switch keep the owner they have.

If an overlap ever becomes necessary, the rule is ready to build in the generic module: the subcontracted MO takes
the owner of its purchase order (OCA `purchase_order_owner`), and the bill line of a purchase order with an owner
goes to the processing-cost account instead of 3399.

---

## 2. The periodic invoice of contract processing (step 2)

### 2.1 What it is

A wizard proposes **one ordinary draft customer invoice per owner and month**; the accountant edits it, confirms
it and issues the e-invoice. Nothing else is written: no state, no link field on invoices or stock. Uninstalling
the module leaves the invoices, the pricelist and the products as ordinary records.

Module: `mrp_production_owner_invoice` (generic name, uninstallable on its own), depending on
`mrp_production_partner_owner` and `account`.

### 2.2 Sources

| # | Line on the draft | Computed from | Price |
|---|---|---|---|
| 1 | **Processing fee** per product style (product template): quantity = finished goods produced in the month by orders of that owner whose products belong to it (done finished moves, `production_id.owner_id`, `production_owned`, `date` in the month), subcontracted orders included | quantities | the fee **pricelist** (§2.3); a style without a price gets a line at 0 and a warning |
| 2 | **Our material supplied**: one line, the value of our components consumed by those orders in the month (valuation layers of their component moves, the *Company Material in Processing* report) | value | **at cost** (Peter, 2026-11-27) |
| 3 | **Late attributions**: listed in the wizard as suggestions, not added: journal items in the month on the cost account (6320) whose label contains a marker text (default "đã dùng cho đơn") | value | the accountant adds the ones that belong |
| 4 | **Anything else** (the November conversion register, returns, rework, claims) | — | by hand on the draft |

### 2.3 The fee per style: an ordinary pricelist

A sales pricelist (e.g. *Phí gia công Công ty TM*) with one rule per product template (`applied_on` *Product*),
price = the fee per piece. The wizard reads it with `pricelist._get_product_price(product, quantity)`
(`product/models/product_pricelist.py:104`). Kept in Odoo like any pricelist; edited by sales or accounting.

### 2.4 Settings (per company)

The fee product (service *Phí gia công*), the material product (service *Vật tư cung cấp cho gia công*), and the
fee pricelist: three fields on *Settings → Manufacturing*, proposed as the wizard's defaults. Removed with the
module; nothing depends on them.

### 2.5 The draft

- Customer = the owner; invoice date = the month's last day; journal = sales.
- **Invoice origin** (core's `invoice_origin`, `account/models/account_move.py:648`) = "Gia công <owner> MM/YYYY".
  The wizard **warns** (never blocks) when a draft or posted invoice of that owner already carries it.
- Lines: one per style (`name` = "Phí gia công <style> – MM/YYYY"), then the material line
  ("Vật tư cung cấp cho gia công – MM/YYYY"). Taxes from the products.
- After creating it, the wizard opens the draft.

### 2.6 Not in it

Payment and netting with what the trading company invoices us (uniforms, case 7); approval steps; any record of
which goods were invoiced (the month is the key; a second run of the same month only warns).

## 3. Open points

1. The marker text for late attributions: "đã dùng cho đơn" as agreed for the Quang Quang Linh bill line, or
   another wording.
2. Rounding: fee lines at the pricelist price; the material line to the đồng.
