# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_owner_production(self):
        """The manufacturing order the move works for: its own (components,
        finished goods), else the order whose components it supplies (Pick
        Components, Resupply Subcontractor)."""
        self.ensure_one()
        production = self.raw_material_production_id or self.production_id
        if not production:
            production = self.move_dest_ids.raw_material_production_id[:1]
        return production

    def _action_assign(self, force_qty=False):
        # OCA stock_owner_restriction restricts by operation type; one Pick
        # Components type serves every order, so the order decides here through
        # the same context key (stock_owner_restriction/models/stock_quant.py).
        by_owner = {}
        others = self.browse()
        for move in self:
            production = move._get_owner_production()
            # A chained move reserves what its origin moves brought, line by line with
            # their owners (stock/models/stock_move.py, _action_assign): the owner was
            # chosen when the origin reserved. Forcing it here would turn the unowned
            # lines into the owner's.
            if production and not (
                move.move_orig_ids and not move._should_bypass_reservation()
            ):
                by_owner.setdefault(production.owner_id, self.browse())
                by_owner[production.owner_id] |= move
            else:
                others |= move
        res = None
        if others:
            res = super(StockMove, others)._action_assign(force_qty=force_qty)
        for owner, moves in by_owner.items():
            if owner:
                super(
                    StockMove, moves.with_context(force_restricted_owner_id=owner)
                )._action_assign(force_qty=force_qty)
                missing = moves.filtered(
                    lambda m: m.state in ("confirmed", "partially_available")
                )
                if missing:
                    super(
                        StockMove, missing.with_context(force_restricted_owner_id=False)
                    )._action_assign(force_qty=force_qty)
            else:
                super(
                    StockMove, moves.with_context(force_restricted_owner_id=False)
                )._action_assign(force_qty=force_qty)
        return res

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if not reserved_quant:
            production = self._get_owner_production()
            # Finished goods take the owner only when they belong to it (order
            # processing keeps them the company's).
            if production.owner_id and (
                not self.production_id or production.production_owned
            ):
                vals["owner_id"] = production.owner_id.id
        return vals

    def _get_dest_account(self, accounts_data):
        # The company's own components consumed for an owner are charged to cost
        # of sales: they are invoiced to the owner.
        if (
            self.raw_material_production_id.owner_id
            and self.raw_material_production_id.production_owned
            and self._is_production_consumed()
            and accounts_data.get("expense")
        ):
            return accounts_data["expense"].id
        return super()._get_dest_account(accounts_data)
