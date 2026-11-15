# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Purchase Forms",
    "summary": "Purchase orders printed in Vietnamese with signature blocks, in full and "
    "compact versions",
    "version": "18.0.1.1.1",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Inventory/Purchase",
    "countries": ["vn"],
    "depends": [
        "l10n_vn_voucher",
        "purchase_stock",
        "purchase_requisition",
        "purchase_product_matrix",
        "mrp_subcontracting",
    ],
    "data": [
        "report/l10n_vn_purchase_report_templates.xml",
        "report/l10n_vn_purchase_report_reports.xml",
    ],
    "installable": True,
}
