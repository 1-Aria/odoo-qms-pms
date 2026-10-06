# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Fabric Inspection",
    "summary": "Roll-level fabric inspection at receipt: 4-point scoring per roll "
    "within the receipt line's inspection",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_quality_control",
        "quality_control_stock_oca",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/qc_test_views.xml",
        "views/qc_inspection_views.xml",
    ],
    "installable": True,
}
