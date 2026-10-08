# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Zalo Notifications: Garment Manufacturing",
    "summary": "Zalo notifications for corrective maintenance, SLA alerts and quality "
    "inspections",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Productivity",
    "depends": [
        "zalo_oa",
        # The stages the paused and restored rules name, and through
        # maintenance_sla the SLA records the time-based rules watch.
        "maintenance_sla_garment",
        # Fields the templates print: the request's code, the equipment's
        # location, the request's employee.
        "maintenance_request_sequence",
        "maintenance_location",
        "hr_maintenance",
        "quality_control_oca",
    ],
    # noupdate data: after install the templates and rules belong to the site,
    # and an upgrade does not overwrite what was tuned. The rules naming
    # maintenance_sla_garment's stages are created by post_init_hook.
    "data": [
        "data/zalo_template_data.xml",
        "data/base_automation_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
