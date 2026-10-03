# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance SLA: Garment Manufacturing",
    "summary": "A starting SLA configuration for garment manufacturing: stage flow, "
    "targets, priority grid, waive reasons",
    "version": "18.0.1.1.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    "depends": [
        "maintenance_sla",
        "maintenance_priority_matrix",
        "maintenance_equipment_status_automation",
    ],
    # noupdate data: after install the records belong to the site, and an
    # upgrade of this module does not overwrite what was tuned. Everything
    # touching records this module does not own is in post_init_hook.
    "data": [
        "data/maintenance_stage_data.xml",
        "data/maintenance_equipment_status_data.xml",
        "data/maintenance_sla_waive_reason_data.xml",
        "data/maintenance_sla_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
