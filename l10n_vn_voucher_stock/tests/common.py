# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase

ACTION_IN = "l10n_vn_voucher_stock.action_report_stock_voucher_in"
ACTION_OUT = "l10n_vn_voucher_stock.action_report_stock_voucher_out"

COPIES = (
    "Liên 1: Kế toán lưu\n"
    "Liên 2: Thủ kho giữ để ghi thẻ kho\n"
    "Liên 3: Giao cho người giao hàng"
)


class StockVoucherCase(TransactionCase):
    """Shared fixtures; holds no test methods.

    A Vietnamese company of its own with the vn chart, real-time valuation at
    standard cost, and the interim accounts 3399 and 1599 the garment company
    uses. Built on TransactionCase, not on account's AccountTestInvoicingCommon,
    whose package cannot be imported on this image.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Stock Voucher Test Company",
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

        Account = cls.env["account.account"]
        # The chart's raw-materials account. The vn chart pads codes to four
        # digits (code_digits "4"), so its code is 1520, as on the instance.
        cls.account_1520 = cls.env.ref(f"account.{cls.company.id}_chart152")
        cls.account_3399 = Account.create(
            {
                "code": "3399",
                "name": "Goods Received Not Purchased (test)",
                "account_type": "liability_current",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.account_1599 = Account.create(
            {
                "code": "1599",
                "name": "Goods Issued Not Invoiced (test)",
                "account_type": "asset_current",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        stock_journal = cls.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.category = (
            cls.env["product.category"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Stock Voucher Test Category",
                    "property_valuation": "real_time",
                    "property_cost_method": "standard",
                    "property_stock_valuation_account_id": cls.account_1520.id,
                    "property_stock_account_input_categ_id": cls.account_3399.id,
                    "property_stock_account_output_categ_id": cls.account_1599.id,
                    "property_stock_journal": stock_journal.id,
                }
            )
        )
        cls.product = (
            cls.env["product.product"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Vải test",
                    "default_code": "VTEST1",
                    "is_storable": True,
                    "categ_id": cls.category.id,
                    "standard_price": 1000.0,
                }
            )
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Nhà cung cấp test",
                "street": "12 Lê Lợi",
                "city": "Hồ Chí Minh",
                "country_id": cls.env.ref("base.vn").id,
            }
        )

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.in_type = cls.warehouse.in_type_id
        cls.out_type = cls.warehouse.out_type_id
        cls.int_type = cls.warehouse.int_type_id
        cls.in_type.write(
            {
                "l10n_vn_voucher_kind": "in",
                "l10n_vn_voucher_reason": "Nhập kho mua hàng",
                "l10n_vn_voucher_copies": COPIES,
            }
        )
        cls.out_type.write(
            {
                "l10n_vn_voucher_kind": "out",
                "l10n_vn_voucher_reason": "Xuất kho bán hàng",
            }
        )
        cls.int_type.write(
            {
                "l10n_vn_voucher_kind": "out",
                "l10n_vn_voucher_reason": "Xuất nguyên liệu cho sản xuất",
            }
        )

        cls.storekeeper = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Voucher Storekeeper",
                    "login": "l10n_vn_voucher_stock_storekeeper",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("stock.group_stock_user").id])
                    ],
                }
            )
        )
        cls.action_in = cls.env.ref(ACTION_IN)
        cls.action_out = cls.env.ref(ACTION_OUT)

    def _picking(self, picking_type, qty, partner=None, **values):
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
                        "product_uom_qty": qty,
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
        for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def _receipt_done(self, qty=10):
        return self._validate(self._picking(self.in_type, qty, self.partner))

    def _data(self, picking):
        return picking._l10n_vn_voucher_data()

    def _valid(self, picking):
        actions = self.action_in | self.action_out
        return set(actions.get_valid_action_reports("stock.picking", picking.ids))

    def _html(self, picking, action, env=None):
        reports = (env or self.env)["ir.actions.report"]
        html, _type = reports._render_qweb_html(action, picking.ids)
        return html.decode()
