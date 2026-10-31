**Export from the portal.** On `hoadondientu.gdt.gov.vn`, logged in with the company's account,
look up the month's purchase or sales invoices (*Tra cứu HĐĐT mua vào / bán ra*) and export the
list to Excel.

**Import.** Under *Accounting → Accounting → E-Invoice Reconciliation → Portal Lists*, create a
list, choose purchases or sales and the list (ordinary or cash register), then *Import* and choose
the file. The file is read into rows and not kept.

**Refusals.** The import refuses a file that does not fit the list: the cash-register list on an
ordinary list or the reverse, a header that is not where the template expects it, or a row whose
tax code on the company's side is not the company's (another company's list, or a sales list
imported as purchases). Nothing is imported then.

**Results.** The *Invoices* tab holds one portal invoice per legal invoice; the *Rows* tab the file's
rows as written, with the reason when one could not be read. An invoice spread over several rows of
the list is shown with its rows and amounts of 0, to be checked by hand.

**Re-importing.** Importing again replaces the list's rows and invoices. Export and re-import
earlier months to pick up their later corrections: the portal shows each invoice's status as of the
day of the export.
