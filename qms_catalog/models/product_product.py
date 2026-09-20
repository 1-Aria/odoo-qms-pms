# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    qms_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        relation="qms_profile_product_rel",
        column1="product_id",
        column2="profile_id",
        string="Catalog Profiles",
    )
    qms_effective_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        string="Effective Catalog Profiles",
        compute="_compute_qms_effective_profile_ids",
        help="Profiles assigned to this variant, to its product and to its "
        "product category.",
    )

    @api.depends("qms_profile_ids", "product_tmpl_id.qms_effective_profile_ids")
    def _compute_qms_effective_profile_ids(self):
        # The template's set already folds in the product category's.
        for product in self:
            product.qms_effective_profile_ids = (
                product.qms_profile_ids
                | product.product_tmpl_id.qms_effective_profile_ids
            )
