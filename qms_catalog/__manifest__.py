# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Catalog",
    "summary": "Defect and object-part catalogs with product-scoped profiles",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": ["product", "mgmtsystem"],
    "data": [
        "security/ir.model.access.csv",
        "views/qms_defect_code_views.xml",
        "views/qms_object_part_views.xml",
        "views/qms_catalog_menus.xml",
    ],
    "installable": True,
}
