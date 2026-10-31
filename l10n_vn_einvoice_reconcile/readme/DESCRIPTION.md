Imports the tax portal's lists of sales or purchase invoices — the ordinary list and the
cash-register list — into Odoo. Each import keeps the list's rows exactly as they were in the file,
not the file itself, and groups them into one portal invoice per legal invoice, with its amounts and
the portal's status (new, replacing, adjusting, replaced, adjusted, cancelled).

A later version matches the portal invoices to the e-invoices of `l10n_vn_einvoice`.
