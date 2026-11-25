Manufacturing orders that work for an owner (processing, *gia công*). The order's owner is taken
first from the order it supplies (a child order), else from the operation type's fixed *Goods
Owner* (from *Stock Picking Type Partner Owner*), else, on a type with *Partner Owns the Goods*,
from the customer of the sales order behind it. Such an order reserves the owner's components first
and the company's after, for its own component moves and for the transfers that supply them (*Pick
Components*, *Resupply Subcontractor*).

*Products Belong to the Owner*, per manufacturing type, says what happens to the goods produced:

- on (contract processing): they belong to the owner and stay out of the company's valuation; the
  company's components consumed are charged to the product's expense account, to be invoiced to the
  owner;
- off (order processing): they remain the company's, valued at its input, and are sold on the sales
  order, whose invoice costs them as usual.

An order without an owner is the company's own production and reserves only the company's stock. A
scrap made from an order takes the owner's goods when the owner holds the product at the scrap's
location. Two reports under *Manufacturing → Reporting* list, for contract processing, the
company's material consumed and the goods produced.
