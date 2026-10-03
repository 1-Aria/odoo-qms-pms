# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Equipment Status Automation",
    "summary": "Set the equipment's status from the stage its corrective request reaches",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    "depends": ["maintenance", "maintenance_equipment_status"],
    "data": ["views/maintenance_stage_views.xml"],
    "installable": True,
}
