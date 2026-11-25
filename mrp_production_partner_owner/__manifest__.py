# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MRP Production Partner Owner",
    "summary": "Manufacturing orders that process another owner's goods",
    "version": "18.0.1.1.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Manufacturing/Manufacturing",
    "depends": [
        "mrp_account",
        "stock_owner_restriction",
        "stock_picking_type_partner_owner",
    ],
    "data": [
        "views/mrp_production_views.xml",
        "views/report_views.xml",
        "views/stock_picking_type_views.xml",
    ],
    "installable": True,
}
