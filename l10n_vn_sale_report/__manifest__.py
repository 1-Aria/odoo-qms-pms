# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Sales Forms",
    "summary": "Sales orders printed in Vietnamese with signature blocks, in full and "
    "compact versions",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Sales/Sales",
    "countries": ["vn"],
    "depends": [
        "l10n_vn_voucher",
        "sale_product_matrix",
    ],
    "data": [
        "report/l10n_vn_sale_report_templates.xml",
        "report/l10n_vn_sale_report_reports.xml",
    ],
    "installable": True,
}
