# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    qms_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        relation="qms_profile_categ_rel",
        column1="categ_id",
        column2="profile_id",
        string="Catalog Profiles",
    )
    qms_effective_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        string="Effective Catalog Profiles",
        compute="_compute_qms_effective_profile_ids",
        recursive=True,
        help="Profiles assigned to this category and to all of its parents.",
    )

    @api.depends("qms_profile_ids", "parent_id.qms_effective_profile_ids")
    def _compute_qms_effective_profile_ids(self):
        """Own profiles plus every ancestor category's.

        The walk up parent_id is deliberate, not naive: it must follow the same
        path as @api.depends. For a non-stored recursive field, modified() only
        cascades through records whose value is already in cache
        (odoo/models.py:7218-7227). Reading a child this way computes and caches
        every ancestor, which is the trail the cascade follows. Resolving the
        chain in one parent_of search instead returns the same value but caches
        no ancestor, so a write to a grandparent leaves the child stale.
        """
        for category in self:
            category.qms_effective_profile_ids = (
                category.qms_profile_ids | category.parent_id.qms_effective_profile_ids
            )
