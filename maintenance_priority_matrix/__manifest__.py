# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Priority Matrix",
    "summary": "Derive maintenance request priority from equipment criticality "
    "and reported urgency",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    "depends": ["maintenance"],
    "data": [
        "security/ir.model.access.csv",
        "views/maintenance_priority_rule_views.xml",
        "views/maintenance_equipment_views.xml",
        "views/maintenance_request_views.xml",
    ],
    "installable": True,
}
