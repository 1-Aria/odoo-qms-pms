# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Quality Control",
    "summary": "Defect codes on inspection answers, and nonconformity analysis "
    "from inspections",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_nonconformity",
        "quality_control_oca",
        "mgmtsystem_nonconformity_quality_control_oca",
        "mgmtsystem_action",
    ],
    "data": [
        "views/qc_test_views.xml",
        "views/qc_inspection_views.xml",
        "views/mgmtsystem_nonconformity_views.xml",
    ],
    "installable": True,
}
