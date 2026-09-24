# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Maintenance",
    "summary": "Nonconformities raised from maintenance requests",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_nonconformity",
        # maintenance.equipment.product_id, which the prefill reads through.
        "maintenance_product",
        # mgmtsystem.nonconformity.equipment_id, which the prefill carries.
        "mgmtsystem_nonconformity_maintenance_equipment",
        # The action count this module extends, and base_maintenance with it, so
        # the request form's button box is already there.
        "maintenance_mgmtsystem_action",
    ],
    "data": [
        "views/mgmtsystem_nonconformity_views.xml",
        "views/maintenance_request_views.xml",
    ],
    "installable": True,
}
