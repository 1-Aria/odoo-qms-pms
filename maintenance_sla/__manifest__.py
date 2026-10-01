# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance SLA",
    "summary": "Configured response and restore commitments on maintenance "
    "requests, with immutable evidence",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    # mail is declared although maintenance brings it: this module posts to the
    # request's chatter itself, so the dependency is used directly.
    "depends": ["maintenance", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/maintenance_sla_views.xml",
        "views/maintenance_stage_views.xml",
    ],
    "installable": True,
}
