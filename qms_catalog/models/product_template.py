# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qms_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        relation="qms_profile_product_tmpl_rel",
        column1="product_tmpl_id",
        column2="profile_id",
        string="Catalog Profiles",
    )
    qms_effective_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        string="Effective Catalog Profiles",
        compute="_compute_qms_effective_profile_ids",
        help="Profiles assigned to this product and to its product category.",
    )

    @api.depends("qms_profile_ids", "categ_id.qms_effective_profile_ids")
    def _compute_qms_effective_profile_ids(self):
        for template in self:
            template.qms_effective_profile_ids = (
                template.qms_profile_ids | template.categ_id.qms_effective_profile_ids
            )
