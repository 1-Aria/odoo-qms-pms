# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Plan Action Templates",
    "summary": "Generate management-system actions from templates on every request "
    "a maintenance plan creates",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    "depends": [
        "maintenance_plan",
        "mgmtsystem_action_template",
        "maintenance_mgmtsystem_action",
    ],
    "data": ["views/maintenance_plan_views.xml"],
    "installable": True,
}
