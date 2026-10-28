# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - E-Invoice Records",
    "summary": "Vietnamese e-invoices read from their XML, one record per legal invoice, "
    "linked to bills and invoices",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "countries": ["vn"],
    "depends": [
        "account",
        "l10n_vn",
    ],
    "data": [
        "security/l10n_vn_einvoice_security.xml",
        "security/ir.model.access.csv",
        "wizard/l10n_vn_einvoice_attach_views.xml",
        "views/l10n_vn_einvoice_views.xml",
        "views/l10n_vn_einvoice_tax_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
