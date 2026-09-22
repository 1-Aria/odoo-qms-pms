# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Determination",
    "summary": "Rules that suggest a response from nonconformity analysis",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_nonconformity",
        "mgmtsystem_action_template",
        # Declared because the document domain names the page types they add.
        "document_page_procedure",
        "document_page_work_instruction",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/qms_determination_rule_views.xml",
        "views/mgmtsystem_nonconformity_views.xml",
    ],
    "installable": True,
}
