# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import MaterialOwnershipCase

ACTION = "sale_material_ownership.action_report_material_batch"


@tagged("post_install", "-at_install")
class TestDocument(MaterialOwnershipCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("vi_VN")

    def _rows(self, rows):
        return {row["code"]: row["qty"] for row in rows}

    def test_allocation_oldest_first(self):
        self._counted_bill(self.fabric, 10)
        first = self._order([(self.shirt, 10)])
        second = self._order([(self.shirt, 10)])
        batch = self._request(self._batch(first, second))
        fabric = {line.product_id: line for line in batch.request_line_ids}[self.fabric]
        self.assertAlmostEqual(fabric.request_qty, 20)
        data = batch._material_document_data()
        self.assertEqual([o["name"] for o in data["orders"]], [first.name, second.name])
        self.assertAlmostEqual(self._rows(data["orders"][0]["materials"])["MOFAB"], 5)
        self.assertAlmostEqual(self._rows(data["orders"][1]["materials"])["MOFAB"], 15)
        self.assertAlmostEqual(self._rows(data["orders"][0]["materials"])["MOBTN"], 50)
        self.assertAlmostEqual(self._rows(data["totals"])["MOFAB"], 20)
        self.assertFalse(data["shortfall"])

    def test_shortfall_section(self):
        batch_a = self._request(self._batch(self._order([(self.shirt, 10)])))
        bill = batch_a.bill_ids
        bill.invoice_line_ids.filtered(lambda l: l.product_id == self.button).quantity = 45
        self._post(bill)
        self._einvoice(bill)
        batch_b = self._request(self._batch(self._order([(self.shirt, 4)])))
        data = batch_b._material_document_data()
        self.assertAlmostEqual(self._rows(data["shortfall"])["MOBTN"], 5)
        ordered = sum(self._rows(o["materials"]).get("MOBTN", 0) for o in data["orders"])
        self.assertAlmostEqual(ordered, 20)
        self.assertAlmostEqual(
            ordered + self._rows(data["shortfall"])["MOBTN"],
            self._rows(data["totals"])["MOBTN"],
        )

    def test_render(self):
        order = self._order([(self.button, 50)])
        batch = self._request(self._batch(order))
        html, _type = self.env["ir.actions.report"]._render_qweb_html(ACTION, batch.ids)
        html = html.decode()
        self.assertIn("BẢNG KÊ NGUYÊN PHỤ LIỆU ĐỀ NGHỊ XUẤT HÓA ĐƠN", html)
        self.assertIn(batch.name, html)
        self.assertIn(order.name, html)
        self.assertIn("25.000", html)
        self.assertIn("MO Trading Company", html)

    def test_draft_not_printed(self):
        action = self.env.ref(ACTION)
        draft = self._batch(self._order([(self.button, 5)]))
        self.assertEqual(action.get_valid_action_reports(draft._name, draft.ids), [])
        self._request(draft)
        self.assertEqual(action.get_valid_action_reports(draft._name, draft.ids), [action.id])

    def test_warning_cost_and_valuation(self):
        Product = self.env["product.product"].with_company(self.company)
        free = Product.create(
            {
                "name": "MO Free Trim",
                "is_storable": True,
                "categ_id": self.categ_material.id,
                "standard_price": 0.0,
            }
        )
        periodic_categ = (
            self.env["product.category"]
            .with_company(self.company)
            .create(
                {
                    "name": "MO Periodic Materials",
                    "material_ownership": True,
                    "property_valuation": "manual_periodic",
                    "property_cost_method": "standard",
                }
            )
        )
        label = Product.create(
            {
                "name": "MO Label",
                "is_storable": True,
                "categ_id": periodic_categ.id,
                "standard_price": 10.0,
            }
        )
        batch = self._batch(self._order([(free, 5), (label, 3), (self.button, 1)]))
        warning = batch.warning
        self.assertIn("Zero unit cost", warning)
        self.assertIn("MO Free Trim", warning)
        self.assertIn("Not valued in real time", warning)
        self.assertIn("MO Label", warning)
        self.assertNotIn("MO Button", warning.split("Not valued in real time")[1])
