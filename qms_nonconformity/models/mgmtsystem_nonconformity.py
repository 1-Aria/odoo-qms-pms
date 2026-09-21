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
    # A nonconformity raised from an inspection or a maintenance request often
    # has no partner at all. Every other attribute is inherited.
    partner_id = fields.Many2one(required=False)
    responsible_user_id = fields.Many2one(
        default=lambda self: self._default_responsible_user_id()
    )
    manager_user_id = fields.Many2one(
        default=lambda self: self._default_manager_user_id()
    )
    disposition = fields.Selection(
        selection=[
            ("accept", "Accept"),
            ("accept_rework", "Accept after Rework"),
            ("scrap", "Scrap"),
            ("return_supplier", "Return to Supplier"),
            ("reinspect", "Re-inspect"),
        ],
        tracking=True,
        help="What was decided about the affected material or equipment.",
    )

    def _default_responsible_user_id(self):
        return self.env.user

    def _default_manager_user_id(self):
        """The reporter's manager, or nothing.

        sudo: hr.employee is readable by HR officers only
        (hr/security/ir.model.access.csv:4-5). Every hop may be missing -- no
        employee, no manager, a manager without a user -- and an empty result
        simply leaves the required field for the user to fill.
        """
        return self.env.user.sudo().employee_id.parent_id.user_id
