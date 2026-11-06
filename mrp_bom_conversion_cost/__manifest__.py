# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "BoM Conversion Cost",
    "summary": "Value manufactured goods with a standard conversion cost: "
    "BoM minutes × an approved, dated rate per minute",
    "version": "18.0.1.1.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Manufacturing/Manufacturing",
    "depends": [
        "mrp_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/mrp_conversion_cost_rate_security.xml",
        "views/mrp_conversion_cost_rate_views.xml",
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
}
