# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestConversionCost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.conversion_cost_rate = 1500.0
        cls.categ = cls.env["product.category"].create(
            {
                "name": "Conversion Cost Test",
                "property_cost_method": "average",
                "property_valuation": "manual_periodic",
            }
        )
        product_vals = {"is_storable": True, "categ_id": cls.categ.id}
        cls.component = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Component", standard_price=10000.0)
        )
        cls.garment = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Garment")
        )
        cls.garment_b = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Garment B")
        )
        cls.bom = cls._bom(cls.garment, conversion_minutes=12.5)
        cls.bom_b = cls._bom(cls.garment_b)
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Conversion Cost Manager",
                "login": "test.conversion.manager",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "groups_id": [Command.set(cls.env.ref("mrp.group_mrp_manager").ids)],
            }
        )

    @classmethod
    def _bom(cls, product, **vals):
        return cls.env["mrp.bom"].create(
            dict(
                {
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "product_qty": 1.0,
                    "type": "normal",
                    # mrp_bom_version can create BoMs archived
                    "active": True,
                    "bom_line_ids": [
                        Command.create({"product_id": cls.component.id, "product_qty": 2.0})
                    ],
                },
                **vals,
            )
        )

    def _mo(self, product, qty=1, **vals):
        return self.env["mrp.production"].create(
            dict({"product_id": product.id, "product_qty": qty}, **vals)
        )

    def test_mo_gets_minutes_times_rate(self):
        mo = self._mo(self.garment)
        self.assertEqual(mo.bom_id, self.bom)
        self.assertAlmostEqual(mo.extra_cost, 18750.0)

    def test_bom_without_minutes(self):
        mo = self._mo(self.garment_b)
        self.assertEqual(mo.bom_id, self.bom_b)
        self.assertEqual(mo.extra_cost, 0.0)

    def test_given_value_wins(self):
        mo = self._mo(self.garment, extra_cost=5000.0)
        self.assertAlmostEqual(mo.extra_cost, 5000.0)

    def test_later_changes_do_not_reach_existing_mo(self):
        mo = self._mo(self.garment)
        self.assertAlmostEqual(mo.extra_cost, 18750.0)
        self.company.conversion_cost_rate = 2000.0
        self.bom.conversion_minutes = 20.0
        self.env.flush_all()
        self.assertAlmostEqual(mo.extra_cost, 18750.0)
        self.assertAlmostEqual(self._mo(self.garment).extra_cost, 40000.0)

    def test_bom_change_recomputes(self):
        mo = self._mo(self.garment)
        self.assertAlmostEqual(mo.extra_cost, 18750.0)
        bom_2 = self._bom(self.garment, conversion_minutes=20.0)
        mo.bom_id = bom_2
        self.assertAlmostEqual(mo.extra_cost, 30000.0)

    def test_split_keeps_figure(self):
        mo = self._mo(self.garment, qty=4)
        mo.action_confirm()
        productions = mo._split_productions({mo: [2, 2]})
        self.assertEqual(len(productions), 2)
        for production in productions:
            self.assertAlmostEqual(production.extra_cost, 18750.0)

    def test_valuation_at_done(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        mo = self._mo(
            self.garment,
            qty=2,
            location_src_id=warehouse.lot_stock_id.id,
            location_dest_id=warehouse.lot_stock_id.id,
        )
        mo.action_confirm()
        mo_form = Form(mo)
        mo_form.qty_producing = 2
        mo = mo_form.save()
        mo.move_raw_ids.picked = True
        mo.button_mark_done()
        self.assertEqual(mo.state, "done")
        finished = mo.move_finished_ids.filtered(lambda m: m.product_id == self.garment)
        # 2 garments × (2 components × 10,000 + 12.5 min × 1,500)
        self.assertAlmostEqual(sum(finished.stock_valuation_layer_ids.mapped("value")), 77500.0)

    def test_subcontract_bom_gives_zero(self):
        types = [value for value, _label in self.env["mrp.bom"]._fields["type"].selection]
        if "subcontract" not in types:
            self.skipTest("mrp_subcontracting is not installed")
        partner = self.env["res.partner"].create({"name": "Conversion Cost Subcontractor"})
        bom = self._bom(
            self.garment_b,
            type="subcontract",
            subcontractor_ids=[Command.set(partner.ids)],
            conversion_minutes=12.5,
        )
        mo = self._mo(self.garment_b, bom_id=bom.id)
        self.assertEqual(mo.bom_id, bom)
        self.assertEqual(mo.extra_cost, 0.0)

    def test_negative_values_refused(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.bom.conversion_minutes = -1.0
            self.bom.flush_recordset()
        self.bom.invalidate_recordset()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.company.conversion_cost_rate = -1.0
            self.company.flush_recordset()
        self.company.invalidate_recordset()

    def test_manager_form(self):
        env = self.env(
            user=self.manager,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        mo_form = Form(env["mrp.production"])
        mo_form.product_id = self.garment.with_env(env)
        self.assertAlmostEqual(mo_form.extra_cost, 18750.0)
        mo_form.extra_cost = 20000.0
        mo = mo_form.save()
        self.assertAlmostEqual(mo.extra_cost, 20000.0)
