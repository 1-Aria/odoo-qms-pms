# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Quality Report",
    "summary": "Inspection and defect analysis: DHU, defective %, FTR, defect-free "
    "share and the defect Pareto",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_quality_control",
        "qms_fabric_inspection",
        "quality_control_mrp_oca",
        "quality_control_stock_oca",
    ],
    "data": [
        "views/qc_inspection_report_views.xml",
        "views/qc_inspection_line_report_views.xml",
        "views/qms_quality_report_menus.xml",
    ],
    "installable": True,
}
