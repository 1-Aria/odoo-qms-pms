# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import is_html_empty

SIGN_HINT = "(Ký, họ tên)"
CONFIRM_HINT = "(Ký, ghi rõ họ tên, đóng dấu)"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _l10n_vn_order_rows(self):
        """The order's reportable lines, as core's print takes them (down payments
        not yet invoiced left out)."""
        self.ensure_one()
        rows = []
        for line in self._get_order_lines_to_report():
            product = line.product_id
            row = {
                "display_type": line.display_type or False,
                "name": line.name or "",
                "code": "",
                "uom": "",
                "qty": 0.0,
                "price": 0.0,
                "discount": 0.0,
                "taxes": "",
                "amount": 0.0,
                "product": product,
            }
            if not line.display_type:
                row.update(
                    {
                        "name": product.with_context(display_default_code=False).display_name,
                        "code": product.default_code or "",
                        "uom": line.product_uom.name or "",
                        "qty": line.product_uom_qty,
                        "price": line.price_unit,
                        "discount": line.discount,
                        "taxes": ", ".join(line.tax_id.mapped("name")),
                        "amount": line.price_subtotal,
                    }
                )
            rows.append(row)
        return rows

    def _l10n_vn_report_matrixes(self):
        """Core's get_report_matrixes (sale_product_matrix/models/sale_order.py:151-169)
        without its product_add_mode == "matrix" filter: the compact form groups
        every configurable style on several lines, so it shows a grid for each."""
        self.ensure_one()
        if not self.report_grids:
            return []
        matrixes = []
        templates = self.order_line.filtered("is_configurable_product").product_template_id
        for template in templates:
            lines = self.order_line.filtered(lambda line: line.product_template_id == template)
            if len(lines) > 1:
                matrix = self._get_matrix(template)
                matrix["matrix"] = [
                    row for row in matrix["matrix"] if any(cell["qty"] != 0 for cell in row[1:])
                ]
                matrixes.append(matrix)
        return matrixes

    def _l10n_vn_order_data(self, compact=False):
        """Everything the Vietnamese sales order prints; the template only lays it out."""
        self.ensure_one()
        order = self.with_context(lang="vi_VN")
        helpers = self.env["l10n_vn.voucher"]
        confirmed = order.state == "sale"
        rows = order._l10n_vn_order_rows()
        if compact:
            rows = helpers._compact_rows(rows)
        return {
            "title": "XÁC NHẬN ĐƠN HÀNG" if confirmed else "BÁO GIÁ",
            "company": order.company_id,
            "number": order.name,
            "date": helpers._local_date(order, order.date_order),
            "seller": order.company_id.partner_id,
            "buyer": order.partner_id,
            "customer_ref": order.client_order_ref or "",
            "validity_date": False if confirmed else helpers._date_short(order.validity_date),
            "delivery_date": helpers._date_short(
                helpers._local_date(order, order.commitment_date)
            ),
            "delivery_address": helpers._address(order.partner_shipping_id),
            "payment_term": order.payment_term_id.name or "",
            "rows": rows,
            "compact": compact,
            "grids": order._l10n_vn_report_matrixes() if compact else [],
            "show_discount": any(
                row["discount"] for row in rows if not row.get("display_type")
            ),
            "currency": order.currency_id,
            "untaxed": order.amount_untaxed,
            "tax": order.amount_tax,
            "total": order.amount_total,
            "notes": False if is_html_empty(order.note) else order.note,
            "signers": [
                {"role": "Người lập phiếu", "hint": SIGN_HINT, "name": order.user_id.name or ""},
                {"role": "Phụ trách kinh doanh", "hint": SIGN_HINT, "name": ""},
                {"role": "Giám đốc", "hint": SIGN_HINT, "name": ""},
                {"role": "Xác nhận của khách hàng", "hint": CONFIRM_HINT, "name": ""},
            ],
        }
