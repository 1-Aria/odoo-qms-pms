# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Stock Vouchers",
    "summary": "Phiếu nhập kho and phiếu xuất kho printed from transfers, with values and "
    "accounts as posted",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Inventory/Inventory",
    "countries": ["vn"],
    "depends": [
        "l10n_vn_voucher",
        "stock_account",
    ],
    "data": [
        "report/l10n_vn_voucher_stock_templates.xml",
        "report/l10n_vn_voucher_stock_reports.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
