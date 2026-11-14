# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    material_ownership_start = fields.Date(
        string="Ownership Start",
        help="Sales orders confirmed from this date on need their materials transferred. "
        "Orders confirmed earlier were sold before the separation and are out of scope. "
        "Without a date, no order is in scope.",
    )
    material_owner_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Material Owner",
        help="The company that still owns the materials not covered by a vendor bill, "
        "and invoices them per transfer batch.",
    )
    material_fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Material Transfer Fiscal Position",
        domain="[('company_id', '=', id)]",
        help="Set on the material owner's batch bills. It maps the stock input account to "
        "the clearing account, so the bills do not value stock again.",
    )
