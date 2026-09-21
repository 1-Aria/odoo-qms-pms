# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    item_ids = fields.One2many(
        comodel_name="qms.nonconformity.item",
        inverse_name="nonconformity_id",
        string="Analysis Items",
    )
    # Read by the item lines' domain. It lives on the header because a domain
    # can only reach parent.<field>, which the client evaluates to an id list.
    qms_effective_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        related="product_id.qms_effective_profile_ids",
        string="Effective Catalog Profiles",
        readonly=True,
    )
