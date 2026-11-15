# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import is_html_empty

SIGN_HINT = "(Ký, họ tên)"
CONFIRM_HINT = "(Ký, ghi rõ họ tên, đóng dấu)"


def subcontracting_bom(env, product, company, partner):
    """The product's subcontracting bill of materials for the partner, or an empty
    recordset. Read as superuser: purchase users need not read bills of materials."""
    boms = env["mrp.bom"].sudo()
    if not product or not partner:
        return boms
    return boms._bom_subcontract_find(
        product, company_id=company.id, bom_type="subcontract", subcontractor=partner
    )


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _l10n_vn_is_subcontracting(self):
        """A line's product has a subcontracting bill of materials for the vendor."""
        self.ensure_one()
        return any(
            subcontracting_bom(self.env, line.product_id, self.company_id, self.partner_id)
            for line in self.order_line.filtered("product_id")
        )

    def _l10n_vn_order_rows(self):
        self.ensure_one()
        rows = []
        for line in self.order_line.sorted(lambda line: (line.sequence, line.id)):
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
                        "qty": line.product_qty,
                        "price": line.price_unit,
                        "discount": line.discount,
                        "taxes": ", ".join(line.taxes_id.mapped("name")),
                        "amount": line.price_subtotal,
                    }
                )
            rows.append(row)
        return rows

    def _l10n_vn_order_data(self, compact=False):
        """Everything the Vietnamese purchase order prints; the template only lays it out."""
        self.ensure_one()
        order = self.with_context(lang="vi_VN")
        helpers = self.env["l10n_vn.voucher"]
        confirmed = order.state in ("purchase", "done")
        if not confirmed:
            title = "YÊU CẦU BÁO GIÁ"
        elif order._l10n_vn_is_subcontracting():
            title = "ĐƠN ĐẶT HÀNG GIA CÔNG"
        else:
            title = "ĐƠN ĐẶT HÀNG"
        rows = order._l10n_vn_order_rows()
        if compact:
            rows = helpers._compact_rows(rows)
        delivery_partner = (
            order.dest_address_id or order.picking_type_id.warehouse_id.partner_id
        )
        return {
            "title": title,
            "company": order.company_id,
            "number": order.name,
            "date": helpers._local_date(
                order, order.date_approve if confirmed else order.date_order
            ),
            "buyer": order.company_id.partner_id,
            "seller": order.partner_id,
            "vendor_ref": order.partner_ref or "",
            "agreement": order.requisition_id.name or "",
            "delivery_date": helpers._date_short(
                helpers._local_date(order, order.date_planned)
            ),
            "delivery_address": helpers._address(delivery_partner),
            "payment_term": order.payment_term_id.name or "",
            "rows": rows,
            "compact": compact,
            "grids": order.get_report_matrixes() if compact else [],
            "show_discount": any(
                row["discount"] for row in rows if not row.get("display_type")
            ),
            "currency": order.currency_id,
            "untaxed": order.amount_untaxed,
            "tax": order.amount_tax,
            "total": order.amount_total,
            "notes": False if is_html_empty(order.notes) else order.notes,
            "signers": [
                {"role": "Người lập phiếu", "hint": SIGN_HINT, "name": order.user_id.name or ""},
                {"role": "Phụ trách mua hàng", "hint": SIGN_HINT, "name": ""},
                {"role": "Giám đốc", "hint": SIGN_HINT, "name": ""},
                {"role": "Xác nhận của nhà cung cấp", "hint": CONFIRM_HINT, "name": ""},
            ],
        }
