# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - E-Invoice Reconciliation",
    "summary": "The tax portal's invoice lists imported and checked against the e-invoices in Odoo",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "countries": ["vn"],
    "depends": [
        "l10n_vn_einvoice",
        "excel_import_export",
    ],
    "external_dependencies": {"python": ["openpyxl"]},
    "data": [
        "security/l10n_vn_einvoice_reconcile_security.xml",
        "security/ir.model.access.csv",
        "data/xlsx_template.xml",
        "wizard/l10n_vn_einvoice_batch_import_views.xml",
        "views/l10n_vn_einvoice_portal_views.xml",
        "views/l10n_vn_einvoice_batch_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
