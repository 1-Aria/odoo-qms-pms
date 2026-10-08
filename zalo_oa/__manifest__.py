# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Zalo Official Account",
    "summary": "Send Zalo Official Account messages from Odoo: tokens, a send queue, "
    "templates and automation",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Productivity",
    # base_automation serves step 3's server action; declared now so the
    # dependency never changes under an installed module.
    "depends": ["mail", "base_automation"],
    "data": [
        "security/zalo_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/zalo_token_views.xml",
        "views/zalo_destination_views.xml",
        "views/zalo_message_views.xml",
        "views/zalo_template_views.xml",
        "views/ir_actions_server_views.xml",
    ],
    "installable": True,
}
