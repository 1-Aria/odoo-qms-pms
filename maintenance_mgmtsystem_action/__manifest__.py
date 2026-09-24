# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Actions",
    "summary": "Link management-system actions to maintenance requests",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    "depends": [
        "maintenance",
        "mgmtsystem_action",
        # For the request form's button box, which base_maintenance adds and
        # core does not. The dependency also fixes view application order and
        # keeps the inherited view from outliving the box it targets.
        "base_maintenance",
    ],
    "data": [
        "views/mgmtsystem_action_views.xml",
        "views/maintenance_request_views.xml",
    ],
    "installable": True,
}
