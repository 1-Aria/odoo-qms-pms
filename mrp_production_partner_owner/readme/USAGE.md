1. Install OCA *Stock Owner Restriction*, which this module depends on. Leave *Owner restriction* on the
   manufacturing and *Pick Components* types on *Standard behavior*: the order decides.
2. Contract processing: a manufacturing operation type with *Goods Owner* (and the subcontracting type
   if subcontracted orders are processing too); *Products Belong to the Owner* on.
3. Order processing: a manufacturing operation type with *Partner Owns the Goods* and *Products Belong
   to the Owner* off; a route with MTO and a manufacture rule on that type, on the processed products;
   their components resupplied from the customer (*Resupply From Customer on Order*).
4. The warehouse's own manufacturing type, without owner, for the company's own production.
5. The order's *Goods Owner* and *Products Belong to the Owner* show in its *Miscellaneous* tab and can
   be changed while the order is draft or confirmed.
