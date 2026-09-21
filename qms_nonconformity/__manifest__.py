# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Nonconformity",
    "summary": "Multi-line defect analysis on the nonconformity, "
    "scoped by catalog profile",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_catalog",
        "mgmtsystem_nonconformity",
        "mgmtsystem_nonconformity_product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/qms_disposition.xml",
        "views/qms_nonconformity_item_views.xml",
        "views/qms_disposition_views.xml",
        "views/mgmtsystem_nonconformity_views.xml",
        "views/mgmtsystem_nonconformity_severity_views.xml",
        "views/qms_defect_code_views.xml",
    ],
    "installable": True,
}
