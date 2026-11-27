# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MRP Production Owner Invoice",
    "summary": "Propose the periodic invoice of processing done for an owner",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Manufacturing/Manufacturing",
    "depends": [
        "mrp_production_partner_owner",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/owner_invoice_wizard_views.xml",
    ],
    "installable": True,
}
