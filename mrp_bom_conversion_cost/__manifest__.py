# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "BoM Conversion Cost",
    "summary": "Value manufactured goods with a standard conversion cost: "
    "BoM minutes × a company rate per minute",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Manufacturing/Manufacturing",
    "depends": [
        "mrp_account",
    ],
    "data": [
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
