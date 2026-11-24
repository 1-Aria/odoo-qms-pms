Adds *Partner Owns the Goods* to operation types. Transfers of such a type assign the goods to
their partner (its company) as owner, or, when the transfer has no partner, to the customer of the
sales order behind it — a receipt created by a manufacturing order, for example. An owner already
set on the transfer is kept at validation.

Owned stock is reserved and consumed as usual, and stays out of the company's stock valuation. The
first use is material that customers send for processing.

An operation type can also name a fixed *Goods Owner*. Its transfers get that partner as owner when they
are created, and at validation if still empty, whoever their partner is: for example a delivery of goods
another company owns, whose partner is the buyer. With OCA *Stock Owner Restriction* set to *Picking
partner* on the type, the transfer then reserves only that owner's goods.
