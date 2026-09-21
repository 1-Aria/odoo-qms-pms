# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "QMS Nonconformity HR",
    "summary": "Fill the nonconformity's department from the user who reports it",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Management System",
    "depends": [
        "qms_nonconformity",
        "mgmtsystem_nonconformity_hr",
    ],
    "installable": True,
    # Installs itself where both sides are present, as
    # mgmtsystem_nonconformity_hr does for the field it adds.
    "auto_install": True,
}
