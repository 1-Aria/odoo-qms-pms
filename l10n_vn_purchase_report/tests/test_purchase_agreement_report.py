# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import date

from odoo import Command
from odoo.tests import TransactionCase, tagged

ACTION = "l10n_vn_purchase_report.action_report_purchase_agreement_vn"


@tagged("post_install", "-at_install")
class TestPurchaseAgreementReport(TransactionCase):
    """Built on TransactionCase, not on account's AccountTestInvoicingCommon,
    whose package cannot be imported on this image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Agreement Form Test Company",
                "country_id": cls.env.ref("base.vn").id,
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env["account.chart.template"].try_loading(
            "vn", company=cls.company, install_demo=False
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )

        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Xưởng gia công test",
                "is_company": True,
                "vat": "0300000003",
                "country_id": cls.env.ref("base.vn").id,
            }
        )
        size = cls.size = cls.env["product.attribute"].create(
            {
                "name": "Size test",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "S"}),
                    Command.create({"name": "M"}),
                    Command.create({"name": "L"}),
                ],
            }
        )
        cls.shirt = cls.env["product.template"].create(
            {
                "name": "Áo test",
                "attribute_line_ids": [
                    Command.create(
                        {"attribute_id": size.id, "value_ids": [Command.set(size.value_ids.ids)]}
                    )
                ],
            }
        )
        cls.variants = {
            variant.product_template_attribute_value_ids.name: variant
            for variant in cls.shirt.product_variant_ids
        }
        ptavs = cls.shirt.attribute_line_ids.product_template_value_ids

        def ptav(*names):
            return ptavs.filtered(lambda value: value.name in names)

        # Names as the form prints them, without the code OCA product_sequence adds.
        cls.names = {
            size_name: variant.with_context(display_default_code=False).display_name
            for size_name, variant in cls.variants.items()
        }
        cls.thread = cls.env["product.product"].create(
            {"name": "Chỉ test", "default_code": "CTEST"}
        )
        meter = cls.env.ref("uom.product_uom_meter")
        cls.fabric = cls.env["product.product"].create(
            {"name": "Vải test", "uom_id": meter.id, "uom_po_id": meter.id}
        )
        cls.button = cls.env["product.product"].create({"name": "Nút test"})
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.shirt.id,
                "product_qty": 2,
                "type": "subcontract",
                "subcontractor_ids": [Command.set(cls.vendor.ids)],
                "company_id": cls.company.id,
                "bom_line_ids": [
                    Command.create(
                        {"product_id": cls.fabric.id, "product_qty": 2.4, "product_uom_id": meter.id}
                    ),
                    Command.create(
                        {
                            "product_id": cls.button.id,
                            "product_qty": 8,
                            "bom_product_template_attribute_value_ids": [Command.set(ptav("S").ids)],
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.button.id,
                            "product_qty": 10,
                            "bom_product_template_attribute_value_ids": [
                                Command.set(ptav("M", "L").ids)
                            ],
                        }
                    ),
                ],
            }
        )
        cls.purchase_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Agreement Form User",
                    "login": "l10n_vn_purchase_report_agreement_user",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("purchase.group_purchase_user").id])
                    ],
                }
            )
        )

    @classmethod
    def _agreement(cls, lines, **values):
        vals = {
            "vendor_id": cls.vendor.id,
            "requisition_type": "blanket_order",
            "line_ids": [
                Command.create({"product_id": product.id, "product_qty": qty, "price_unit": price})
                for product, qty, price in lines
            ],
        }
        vals.update(values)
        return cls.env["purchase.requisition"].create(vals)

    def _processing(self, qty=0, **values):
        return self._agreement(
            [(self.variants[size], qty, 125.5) for size in ("S", "M", "L")], **values
        )

    def _html(self, agreement, env=None):
        reports = (env or self.env)["ir.actions.report"]
        html, _type = reports._render_qweb_html(ACTION, agreement.ids)
        return html.decode()

    def test_framework_agreement(self):
        agreement = self._agreement([(self.thread, 100, 50)])
        data = agreement._l10n_vn_agreement_data()
        self.assertEqual(data["title"], "HỢP ĐỒNG NGUYÊN TẮC")
        self.assertEqual((data["buyer_title"], data["seller_title"]), ("Bên mua", "Bên bán"))
        self.assertEqual(data["norms"], [])
        html = self._html(agreement)
        self.assertIn("Đại diện bên mua", html)
        self.assertNotIn("PHỤ LỤC", html)

    def test_processing_contract(self):
        data = self._processing()._l10n_vn_agreement_data()
        self.assertEqual(data["title"], "HỢP ĐỒNG GIA CÔNG")
        self.assertEqual(
            (data["buyer_title"], data["seller_title"]),
            ("Bên đặt gia công", "Bên nhận gia công"),
        )
        self.assertEqual(
            [signer["role"] for signer in data["signers"]],
            ["Đại diện bên đặt gia công", "Đại diện bên nhận gia công"],
        )

    def test_rows_grouped(self):
        agreement = self._agreement(
            [
                (self.variants["S"], 10, 100),
                (self.variants["M"], 5, 100),
                (self.variants["L"], 5, 100),
                (self.thread, 3, 50),
            ]
        )
        rows = agreement._l10n_vn_agreement_data()["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Áo test")
        self.assertEqual(rows[0]["qty"], 20)
        self.assertTrue(rows[0]["grouped"])
        self.assertEqual(rows[1]["code"], "CTEST")
        self.assertFalse(rows[1]["grouped"])

    def test_material_norms(self):
        norms = self._processing()._l10n_vn_material_norms()
        self.assertEqual(len(norms), 2)
        small, others = norms
        self.assertEqual(small["products"], [self.names["S"]])
        self.assertEqual([row["name"] for row in small["rows"]], ["Vải test", "Nút test"])
        self.assertAlmostEqual(small["rows"][0]["qty"], 1.2)
        self.assertAlmostEqual(small["rows"][1]["qty"], 4)
        self.assertEqual(others["products"], [self.names["M"], self.names["L"]])
        self.assertAlmostEqual(others["rows"][0]["qty"], 1.2)
        self.assertAlmostEqual(others["rows"][1]["qty"], 5)

    def test_material_norms_component_template(self):
        # OCA mrp_bom_attribute_match: a line naming a component template takes,
        # for each product, the variant matching its attributes.
        if "component_template_id" not in self.env["mrp.bom.line"]._fields:
            self.skipTest("mrp_bom_attribute_match is not installed")
        lining = self.env["product.template"].create(
            {
                "name": "Lót test",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": self.size.id,
                            "value_ids": [Command.set(self.size.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        self.bom.write(
            {
                "bom_line_ids": [
                    Command.create({"component_template_id": lining.id, "product_qty": 3})
                ]
            }
        )
        norms = self._processing()._l10n_vn_material_norms()
        # The lining differs per size, so no two sizes share a table any more.
        self.assertEqual(
            [group["products"] for group in norms],
            [[self.names["S"]], [self.names["M"]], [self.names["L"]]],
        )
        for size_name, group in zip(("S", "M", "L"), norms):
            lining_rows = [row for row in group["rows"] if row["name"].startswith("Lót test")]
            self.assertEqual(len(lining_rows), 1, size_name)
            self.assertIn(size_name, lining_rows[0]["name"])
            self.assertAlmostEqual(lining_rows[0]["qty"], 1.5)

    def test_render_processing_contract(self):
        agreement = self._processing(
            date_start=date(2026, 12, 1), date_end=date(2027, 11, 30), reference="HD-01"
        )
        html = self._html(agreement)
        for text in (
            "HỢP ĐỒNG GIA CÔNG",
            "Bên nhận gia công",
            "01/12/2026",
            "30/11/2027",
            "HD-01",
            "PHỤ LỤC: ĐỊNH MỨC NGUYÊN PHỤ LIỆU",
            "1,2",
            "%s, %s" % (self.names["M"], self.names["L"]),
            "page-break-before",
        ):
            self.assertIn(text, html)
        # Quantities of 0 print blank.
        self.assertFalse(re.search(r">\s*0,00\s*<", html))

    def test_report_domains(self):
        action = self.env.ref(ACTION)

        def valid(agreement):
            return action.get_valid_action_reports("purchase.requisition", agreement.ids)

        blanket = self._agreement([(self.thread, 100, 50)])
        self.assertEqual(valid(blanket), action.ids)
        template = self._agreement(
            [(self.thread, 100, 50)], requisition_type="purchase_template"
        )
        self.assertEqual(valid(template), [])
        blanket.action_cancel()
        self.assertEqual(valid(blanket), [])

    def test_render_as_purchase_user(self):
        agreement = self._processing()
        user_env = self.env(
            user=self.purchase_user,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        # Positive control: the purchase user reads the agreement.
        self.assertEqual(agreement.with_env(user_env).name, agreement.name)
        html = self._html(agreement, env=user_env)
        self.assertIn("HỢP ĐỒNG GIA CÔNG", html)
        self.assertIn("1,2", html)
