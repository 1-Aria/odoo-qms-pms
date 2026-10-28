Keeps Vietnamese e-invoices as records in Odoo. Each record is one legal invoice of one company,
read from the invoice's XML (formats 2.1.0 and 2.1.1; VAT invoices and sales invoices, including
those issued from cash registers). It holds the invoice's key — seller tax code, form, symbol and
number — its parties, its totals and the original file, and links to the vendor bill or customer
invoice that books it.

An invoice can be read only once per company, and its status shows whether it is booked.
