# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Maintenance Menus for Internal Users",
    "summary": "Restore core's maintenance menu visibility, which "
    "maintenance_security narrows to equipment managers",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Maintenance",
    # maintenance_security is a dependency for load order, not for behaviour:
    # this module's data must be applied after the data it reverses. Without the
    # dependency the two sit at the same depth in the graph and are ordered by
    # name, which puts maintenance_security last.
    "depends": ["maintenance_security"],
    "data": [
        "data/maintenance_menus.xml",
    ],
    "installable": True,
}
