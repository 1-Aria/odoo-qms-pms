# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestProductionOwner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Production Owner Test Company"})
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.warehouse.manufacture_steps = "pbm"
        cls.stock = cls.warehouse.lot_stock_id
        cls.owner = cls.env["res.partner"].create({"name": "Chủ hàng test", "is_company": True})

        def account(code, account_type):
            return cls.env["account.account"].create(
                {"code": code, "name": f"Test {code}", "account_type": account_type,
                 "company_ids": [Command.set(cls.company.ids)]}
            )

        cls.acc_valuation = account("152001", "asset_current")
        cls.acc_input = account("339901", "liability_current")
        cls.acc_output = account("159901", "asset_current")
        cls.acc_production = account("154101", "asset_current")
        cls.acc_expense = account("632001", "expense_direct_cost")
        cls.journal = cls.env["account.journal"].create(
            {"name": "Stock test", "code": "STKT", "type": "general", "company_id": cls.company.id}
        )
        cls.category = cls.env["product.category"].with_company(cls.company).create(
            {
                "name": "Owner test category",
                "property_cost_method": "average",
                "property_valuation": "real_time",
                "property_stock_valuation_account_id": cls.acc_valuation.id,
                "property_stock_account_input_categ_id": cls.acc_input.id,
                "property_stock_account_output_categ_id": cls.acc_output.id,
                "property_stock_account_production_cost_id": cls.acc_production.id,
                "property_account_expense_categ_id": cls.acc_expense.id,
                "property_stock_journal": cls.journal.id,
            }
        )
        Product = cls.env["product.product"].with_company(cls.company)
        cls.component = Product.create(
            {"name": "Vải test", "is_storable": True, "categ_id": cls.category.id, "standard_price": 10.0}
        )
        cls.finished = Product.create(
            {"name": "Áo test", "is_storable": True, "categ_id": cls.category.id}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1,
                "company_id": cls.company.id,
                "bom_line_ids": [Command.create({"product_id": cls.component.id, "product_qty": 1})],
            }
        )
        cls.own_type = cls.warehouse.manu_type_id
        cls.processing_type = cls.own_type.copy(
            {"name": "Processing test", "sequence_code": "PRCT", "owner_partner_id": cls.owner.id}
        )
        # Step 1.1: order processing for a customer.
        cls.customer = cls.env["res.partner"].create({"name": "Khách gia công test", "is_company": True})
        cls.contact = cls.env["res.partner"].create({"name": "Chị Hoa", "parent_id": cls.customer.id})
        cls.order_type = cls.own_type.copy(
            {
                "name": "Order processing test",
                "sequence_code": "OPRT",
                "owner_from_partner": True,
                "production_owned": False,
            }
        )

    # Helpers ------------------------------------------------------------------------------------

    def _stock(self, qty, owner=None, product=None):
        product = product or self.component
        if owner:
            self.env["stock.quant"]._update_available_quantity(product, self.stock, qty, owner_id=owner)
        else:
            self.env["stock.quant"].with_context(inventory_mode=True).create(
                {"product_id": product.id, "location_id": self.stock.id, "inventory_quantity": qty}
            ).action_apply_inventory()

    def _order(self, qty, picking_type, **values):
        vals = {
            "product_id": self.finished.id,
            "product_qty": qty,
            "bom_id": self.bom.id,
            "picking_type_id": picking_type.id,
            "company_id": self.company.id,
        }
        vals.update(values)
        production = self.env["mrp.production"].create(vals)
        production.action_confirm()
        return production

    def _pick(self, production):
        pick = production.picking_ids.filtered(
            lambda p: p.picking_type_id == self.warehouse.pbm_type_id
        )
        self.assertEqual(len(pick), 1)
        pick.action_assign()
        return pick

    def _validate_pick(self, production):
        pick = self._pick(production)
        pick.move_ids.picked = True
        pick.button_validate()
        self.assertEqual(pick.state, "done")
        production.action_assign()
        return pick

    def _produce(self, production, qty=None):
        production.qty_producing = qty or production.product_qty
        production._set_qty_producing()
        production.move_raw_ids.picked = True
        backorder = production.ids if qty and qty < production.product_qty else []
        production.with_context(
            skip_backorder=True, mo_ids_to_backorder=backorder
        ).button_mark_done()

    def _reserved(self, moves, owner):
        lines = moves.move_line_ids.filtered(lambda l: l.owner_id == owner)
        return sum(lines.mapped("quantity"))

    # Tests --------------------------------------------------------------------------------------

    def test_owner_from_type(self):
        processing = self._order(5, self.processing_type)
        self.assertEqual(processing.owner_id, self.owner)
        self.assertEqual(processing.move_finished_ids.restrict_partner_id, self.owner)
        own = self._order(5, self.own_type)
        self.assertFalse(own.owner_id)
        self.assertFalse(own.move_finished_ids.restrict_partner_id)
        other = self.env["res.partner"].create({"name": "Chủ hàng khác"})
        given = self._order(5, self.processing_type, owner_id=other.id)
        self.assertEqual(given.owner_id, other)

    def test_owner_from_form(self):
        with Form(self.env["mrp.production"]) as form:
            form.product_id = self.finished
            form.bom_id = self.bom
            form.product_qty = 5
            form.picking_type_id = self.processing_type
        production = form.record
        self.assertEqual(production.owner_id, self.owner)
        self.assertEqual(production.move_finished_ids.restrict_partner_id, self.owner)

    def test_reserve_owner_first(self):
        self._stock(6, owner=self.owner)
        self._stock(10)
        production = self._order(10, self.processing_type)
        pick = self._pick(production)
        self.assertEqual(self._reserved(pick.move_ids, self.owner), 6)
        self.assertEqual(self._reserved(pick.move_ids, self.env["res.partner"]), 4)

    def test_own_production_company_only(self):
        self._stock(6, owner=self.owner)
        self._stock(10)
        production = self._order(10, self.own_type)
        pick = self._pick(production)
        self.assertEqual(self._reserved(pick.move_ids, self.owner), 0)
        self.assertEqual(self._reserved(pick.move_ids, self.env["res.partner"]), 10)

    def test_own_production_partial(self):
        self._stock(6, owner=self.owner)
        self._stock(3)
        production = self._order(10, self.own_type)
        pick = self._pick(production)
        self.assertEqual(self._reserved(pick.move_ids, self.owner), 0)
        self.assertEqual(self._reserved(pick.move_ids, self.env["res.partner"]), 3)
        self.assertEqual(pick.move_ids.state, "partially_available")

    def _processing_done(self):
        self._stock(6, owner=self.owner)
        self._stock(4)
        production = self._order(10, self.processing_type)
        self._validate_pick(production)
        self.assertEqual(self._reserved(production.move_raw_ids, self.owner), 6)
        self.assertEqual(self._reserved(production.move_raw_ids, self.env["res.partner"]), 4)
        self._produce(production)
        self.assertEqual(production.state, "done")
        return production

    def test_finished_owned_not_valued(self):
        production = self._processing_done()
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.finished.id), ("location_id", "=", self.stock.id)]
        )
        self.assertEqual(quant.owner_id, self.owner)
        self.assertEqual(quant.quantity, 10)
        finished = production.move_finished_ids
        self.assertFalse(finished.stock_valuation_layer_ids.filtered(lambda v: v.value))
        self.assertFalse(finished.account_move_ids)
        layers = production.move_raw_ids.stock_valuation_layer_ids
        self.assertEqual(sum(layers.mapped("quantity")), -4)
        self.assertAlmostEqual(sum(layers.mapped("value")), -40)
        lines = layers.account_move_id.line_ids
        self.assertAlmostEqual(sum(lines.filtered(lambda l: l.account_id == self.acc_expense).mapped("balance")), 40)
        self.assertFalse(lines.filtered(lambda l: l.account_id == self.acc_production))

    def test_own_production_valued(self):
        self._stock(10)
        production = self._order(10, self.own_type)
        self._validate_pick(production)
        self._produce(production)
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.finished.id), ("location_id", "=", self.stock.id)]
        )
        self.assertFalse(quant.owner_id)
        self.assertAlmostEqual(sum(production.move_finished_ids.stock_valuation_layer_ids.mapped("value")), 100)
        lines = production.move_raw_ids.stock_valuation_layer_ids.account_move_id.line_ids
        self.assertAlmostEqual(sum(lines.filtered(lambda l: l.account_id == self.acc_production).mapped("balance")), 100)

    def test_excess_line_owned(self):
        production = self._order(5, self.processing_type)
        production.move_raw_ids.quantity = 5
        self.assertEqual(production.move_raw_ids.move_line_ids.owner_id, self.owner)

    def test_backorder_keeps_owner(self):
        self._stock(10, owner=self.owner)
        production = self._order(10, self.processing_type)
        self._validate_pick(production)
        self._produce(production, qty=4)
        backorder = production.procurement_group_id.mrp_production_ids - production
        self.assertEqual(len(backorder), 1)
        self.assertEqual(backorder.owner_id, self.owner)
        self.assertEqual(backorder.move_finished_ids.restrict_partner_id, self.owner)

    def test_reports(self):
        production = self._processing_done()
        Action = self.env["ir.actions.act_window"]
        material = Action._for_xml_id("mrp_production_partner_owner.action_processing_material")
        layers = self.env["stock.valuation.layer"].search(safe_eval(material["domain"]))
        self.assertIn(production.move_raw_ids.stock_valuation_layer_ids.filtered(lambda v: v.value), layers)
        goods = Action._for_xml_id("mrp_production_partner_owner.action_processed_goods")
        moves = self.env["stock.move"].search(safe_eval(goods["domain"]))
        self.assertIn(production.move_finished_ids, moves)

    # Step 1.1 -----------------------------------------------------------------------------------

    def _order_processing_done(self):
        self._stock(6, owner=self.customer)
        self._stock(4)
        production = self._order(10, self.order_type, owner_id=self.customer.id)
        self.assertFalse(production.production_owned)
        pick = self._pick(production)
        self.assertEqual(self._reserved(pick.move_ids, self.customer), 6)
        self.assertEqual(self._reserved(pick.move_ids, self.env["res.partner"]), 4)
        self._validate_pick(production)
        self._produce(production)
        self.assertEqual(production.state, "done")
        return production

    def test_order_processing_goods_ours(self):
        production = self._order_processing_done()
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.finished.id), ("location_id", "=", self.stock.id)]
        )
        self.assertFalse(quant.owner_id)
        self.assertEqual(quant.quantity, 10)
        finished = production.move_finished_ids
        self.assertFalse(finished.restrict_partner_id)
        self.assertAlmostEqual(sum(finished.stock_valuation_layer_ids.mapped("value")), 40)
        lines = production.move_raw_ids.stock_valuation_layer_ids.account_move_id.line_ids
        self.assertAlmostEqual(sum(lines.filtered(lambda l: l.account_id == self.acc_production).mapped("balance")), 40)
        self.assertFalse(lines.filtered(lambda l: l.account_id == self.acc_expense))

    def test_owner_from_sale_order(self):
        group_model = self.env["procurement.group"]
        if "sale_id" not in group_model._fields:
            self.skipTest("sale_stock is not installed")
        if "state" in self.bom._fields:
            # mrp_bom_version finds active BoMs only.
            self.bom.write({"state": "active"})
        order = self.env["sale.order"].create({"partner_id": self.contact.id})
        group = group_model.create({"name": "S-OPRT", "sale_id": order.id})
        route = self.env["stock.route"].create(
            {"name": "Order processing test", "product_selectable": True, "company_id": self.company.id}
        )
        self.warehouse.manufacture_pull_id.copy(
            {"name": "Order processing test", "route_id": route.id, "picking_type_id": self.order_type.id}
        )
        self.finished.route_ids = [Command.set(route.ids)]
        group_model.run([group_model.Procurement(
            self.finished, 5, self.finished.uom_id, self.stock, "S-OPRT", "S-OPRT", self.company,
            {"group_id": group, "warehouse_id": self.warehouse, "date_planned": fields.Datetime.now()},
        )])
        production = self.env["mrp.production"].search(
            [("origin", "=", "S-OPRT"), ("company_id", "=", self.company.id)]
        )
        self.assertEqual(len(production), 1)
        self.assertEqual(production.picking_type_id, self.order_type)
        self.assertEqual(production.owner_id, self.customer)
        self.assertFalse(production.production_owned)
        self.assertFalse(production.move_finished_ids.restrict_partner_id)

    def test_child_takes_parent_owner(self):
        parent = self._order(10, self.processing_type)
        child = self.env["mrp.production"].create(
            {
                "product_id": self.finished.id,
                "product_qty": 1,
                "bom_id": self.bom.id,
                "picking_type_id": self.own_type.id,
                "company_id": self.company.id,
                "move_dest_ids": [Command.link(parent.move_raw_ids.id)],
            }
        )
        self.assertEqual(child.owner_id, self.owner)
        self.assertTrue(child.production_owned)
        self.assertEqual(child.move_finished_ids.restrict_partner_id, self.owner)

    def test_scrap_owner(self):
        self._stock(6, owner=self.owner)
        self._stock(4)
        production = self._order(10, self.processing_type)
        self._validate_pick(production)
        pre = self.warehouse.pbm_loc_id
        Scrap = self.env["stock.scrap"]
        values = {"product_id": self.component.id, "scrap_qty": 1, "production_id": production.id,
                  "location_id": pre.id, "company_id": self.company.id}
        self.assertEqual(Scrap.create(values).owner_id, self.owner)
        # The owner's A gone from Pre-Production: the company's stock is scrapped.
        self.env["stock.quant"]._update_available_quantity(self.component, pre, -6, owner_id=self.owner)
        self.assertFalse(Scrap.create(values).owner_id)
        own = self._order(5, self.own_type)
        self.assertFalse(Scrap.create(dict(values, production_id=own.id)).owner_id)

    def test_reports_owned_only(self):
        production = self._order_processing_done()
        Action = self.env["ir.actions.act_window"]
        material = Action._for_xml_id("mrp_production_partner_owner.action_processing_material")
        layers = self.env["stock.valuation.layer"].search(safe_eval(material["domain"]))
        self.assertFalse(production.move_raw_ids.stock_valuation_layer_ids & layers)
        goods = Action._for_xml_id("mrp_production_partner_owner.action_processed_goods")
        moves = self.env["stock.move"].search(safe_eval(goods["domain"]))
        self.assertFalse(production.move_finished_ids & moves)

    def test_owner_change_reaches_existing_finished_lines(self):
        # An order confirmed without owner whose finished line already exists, then
        # given an owner (an existing order at go-live, or a type changed after
        # confirmation): the line takes the owner, so the goods are produced owned.
        self._stock(5, owner=self.owner)
        production = self._order(5, self.own_type)
        production.qty_producing = 5
        production._set_qty_producing()
        finished = production.move_finished_ids.filtered(lambda m: m.product_id == self.finished)
        self.assertTrue(finished.move_line_ids)
        self.assertFalse(finished.move_line_ids.owner_id)
        production.write({"owner_id": self.owner.id, "production_owned": True})
        self.assertEqual(finished.move_line_ids.owner_id, self.owner)
        production.picking_ids.do_unreserve()
        self._validate_pick(production)
        self._produce(production)
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.finished.id), ("location_id", "=", self.stock.id)]
        )
        self.assertEqual(quant.owner_id, self.owner)
        self.assertFalse(finished.stock_valuation_layer_ids.filtered(lambda v: v.value))
