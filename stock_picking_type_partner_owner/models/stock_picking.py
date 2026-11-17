# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_partner_owner(self):
        """The commercial partner of the transfer's partner; without a partner,
        the customer of the sales order behind its procurement group, when
        sale_stock links groups to sales orders (read as superuser)."""
        self.ensure_one()
        if self.partner_id:
            return self.partner_id.commercial_partner_id
        group = self.group_id
        if "sale_id" in group._fields:
            customer = group.sudo().sale_id.partner_id.commercial_partner_id
            return self.env["res.partner"].browse(customer.ids)
        return self.env["res.partner"]

    @api.onchange("partner_id", "picking_type_id")
    def _onchange_owner_from_partner(self):
        if self.picking_type_id.owner_from_partner and self.partner_id:
            self.owner_id = self.partner_id.commercial_partner_id

    def _action_done(self):
        # Before super(), which copies the owner to the moves and move lines.
        for picking in self:
            if picking.picking_type_id.owner_from_partner and not picking.owner_id:
                owner = picking._get_partner_owner()
                if owner:
                    picking.owner_id = owner
        return super()._action_done()
