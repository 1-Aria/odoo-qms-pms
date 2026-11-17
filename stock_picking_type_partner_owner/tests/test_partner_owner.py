# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerOwner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Partner Owner Test Company"})
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.product = (
            cls.env["product.product"]
            .with_company(cls.company)
            .create({"name": "Miếng cắt test", "is_storable": True, "standard_price": 100.0})
        )
        cls.customer = cls.env["res.partner"].create(
            {"name": "Khách hàng test", "is_company": True}
        )
        cls.contact = cls.env["res.partner"].create(
            {"name": "Chị Lan", "parent_id": cls.customer.id}
        )
        cls.other = cls.env["res.partner"].create({"name": "Chủ hàng khác"})
        cls.flag_type = cls.env["stock.picking.type"].create(
            {
                "name": "Resupply From Customer test",
                "code": "incoming",
                "sequence_code": "RFCT",
                "warehouse_id": cls.warehouse.id,
                "company_id": cls.company.id,
                "default_location_src_id": cls.env.ref("stock.stock_location_customers").id,
                "default_location_dest_id": cls.warehouse.lot_stock_id.id,
                "owner_from_partner": True,
            }
        )
        cls.receipt_type = cls.warehouse.in_type_id

    def _receipt(self, picking_type, partner=None, **values):
        vals = {
            "picking_type_id": picking_type.id,
            "location_id": picking_type.default_location_src_id.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "partner_id": partner.id if partner else False,
            "move_ids": [
                Command.create(
                    {
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_uom_qty": 5,
                        "product_uom": self.product.uom_id.id,
                        "location_id": picking_type.default_location_src_id.id,
                        "location_dest_id": picking_type.default_location_dest_id.id,
                    }
                )
            ],
        }
        vals.update(values)
        return self.env["stock.picking"].create(vals)

    def _validate(self, picking):
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def test_owner_on_validation(self):
        receipt = self._validate(self._receipt(self.flag_type, self.contact))
        self.assertEqual(receipt.owner_id, self.customer)
        self.assertEqual(receipt.move_ids.restrict_partner_id, self.customer)
        self.assertEqual(receipt.move_line_ids.owner_id, self.customer)
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", self.warehouse.lot_stock_id.id),
            ]
        )
        self.assertEqual(quant.owner_id, self.customer)

    def test_owner_kept(self):
        receipt = self._receipt(self.flag_type, self.contact, owner_id=self.other.id)
        self._validate(receipt)
        self.assertEqual(receipt.owner_id, self.other)

    def test_type_without_flag(self):
        receipt = self._validate(self._receipt(self.receipt_type, self.contact))
        self.assertFalse(receipt.owner_id)
        self.assertFalse(receipt.move_line_ids.owner_id)

    def test_onchange(self):
        picking = self.env["stock.picking"].new(
            {"picking_type_id": self.flag_type.id, "partner_id": self.contact.id}
        )
        picking._onchange_owner_from_partner()
        self.assertEqual(picking.owner_id, self.customer)
        # Changing the partner moves the owner with it.
        picking.partner_id = self.other
        picking._onchange_owner_from_partner()
        self.assertEqual(picking.owner_id, self.other)

        plain = self.env["stock.picking"].new(
            {"picking_type_id": self.receipt_type.id, "partner_id": self.contact.id}
        )
        plain._onchange_owner_from_partner()
        self.assertFalse(plain.owner_id)

    def test_sale_fallback(self):
        group_model = self.env["procurement.group"]
        if "sale_id" not in group_model._fields:
            self.skipTest("sale_stock is not installed")
        order = self.env["sale.order"].create({"partner_id": self.contact.id})
        group = group_model.create({"name": "WH/MO/TEST", "sale_id": order.id})
        receipt = self._receipt(self.flag_type)
        # A transfer's group is its moves' (stock/models/stock_picking.py:582-584).
        receipt.move_ids.group_id = group
        self._validate(receipt)
        self.assertFalse(receipt.partner_id)
        self.assertEqual(receipt.owner_id, self.customer)

    def test_no_valuation(self):
        if "stock.valuation.layer" not in self.env:
            self.skipTest("stock_account is not installed")
        owned = self._validate(self._receipt(self.flag_type, self.contact))
        layers = self.env["stock.valuation.layer"]
        self.assertFalse(layers.search([("stock_move_id", "in", owned.move_ids.ids)]))
        own = self._validate(self._receipt(self.receipt_type, self.contact))
        self.assertTrue(layers.search([("stock_move_id", "in", own.move_ids.ids)]))
