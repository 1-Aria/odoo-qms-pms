# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Scrap Downgrade",
    "summary": "Scrap goods into a lower-grade product at their cost",
    "version": "18.0.1.1.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Inventory/Inventory",
    "depends": [
        "stock_account",
    ],
    "data": [
        "views/stock_location_views.xml",
        "views/stock_scrap_views.xml",
    ],
    "installable": True,
}
