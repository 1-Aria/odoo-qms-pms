# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import is_html_empty

from .purchase_order import CONFIRM_HINT, subcontracting_bom


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    def _l10n_vn_subcontracting_boms(self):
        """{product: subcontracting bill of materials for the vendor}, in line order."""
        self.ensure_one()
        boms = {}
        for line in self.line_ids.sorted("id"):
            product = line.product_id
            if product in boms:
                continue
            bom = subcontracting_bom(self.env, product, self.company_id, self.vendor_id)
            if bom:
                boms[product] = bom
        return boms

    def _l10n_vn_agreement_rows(self):
        self.ensure_one()
        return [
            {
                "display_type": False,
                "name": line.product_id.with_context(display_default_code=False).display_name,
                "code": line.product_id.default_code or "",
                "uom": line.product_uom_id.name or "",
                "qty": line.product_qty,
                "price": line.price_unit,
                "discount": 0.0,
                "taxes": "",
                "amount": 0.0,
                "product": line.product_id,
            }
            for line in self.line_ids.sorted("id")
        ]

    @staticmethod
    def _l10n_vn_bom_line_component(bom, bom_line, product):
        """The component a bill line consumes for the product. With OCA
        mrp_bom_attribute_match installed, a line may name a component template
        instead of a variant; the variant is the one matching the product's
        attributes, chosen as manufacturing orders choose it. No match: none."""
        if hasattr(bom, "_get_component_template_product"):
            return bom._get_component_template_product(bom_line, product, bom_line.product_id)
        return bom_line.product_id

    def _l10n_vn_material_norms(self):
        """The processing contract's appendix: per product, the components of its
        subcontracting bill of materials per one unit of the product; products with
        the same norms share one group."""
        self.ensure_one()
        groups = {}
        result = []
        for product, bom in self._l10n_vn_subcontracting_boms().items():
            bom_qty = bom.product_uom_id._compute_quantity(
                bom.product_qty, product.uom_id, round=False
            )
            rows = []
            key = []
            for bom_line in bom.bom_line_ids:
                if bom_line._skip_bom_line(product):
                    continue
                component = self._l10n_vn_bom_line_component(bom, bom_line, product)
                if not component:
                    continue
                qty = bom_line.product_qty / bom_qty if bom_qty else 0.0
                rows.append(
                    {
                        "name": component.with_context(
                            display_default_code=False
                        ).display_name,
                        "code": component.default_code or "",
                        "uom": bom_line.product_uom_id.name or "",
                        "qty": qty,
                    }
                )
                key.append((component.id, bom_line.product_uom_id.id, round(qty, 6)))
            name = product.with_context(display_default_code=False).display_name
            group = groups.get(tuple(key))
            if group:
                group["products"].append(name)
                continue
            group = {"products": [name], "rows": rows}
            groups[tuple(key)] = group
            result.append(group)
        return result

    def _l10n_vn_agreement_data(self):
        """Everything the Vietnamese blanket order prints; the template only lays it out."""
        self.ensure_one()
        agreement = self.with_context(lang="vi_VN")
        helpers = self.env["l10n_vn.voucher"]
        processing = bool(agreement._l10n_vn_subcontracting_boms())
        if processing:
            title = "HỢP ĐỒNG GIA CÔNG"
            buyer_title, seller_title = "Bên đặt gia công", "Bên nhận gia công"
        else:
            title = "HỢP ĐỒNG NGUYÊN TẮC"
            buyer_title, seller_title = "Bên mua", "Bên bán"
        return {
            "title": title,
            "buyer_title": buyer_title,
            "seller_title": seller_title,
            "company": agreement.company_id,
            "number": agreement.name,
            "date": agreement.date_start or False,
            "buyer": agreement.company_id.partner_id,
            "seller": agreement.vendor_id,
            "vendor_ref": agreement.reference or "",
            "date_start": helpers._date_short(agreement.date_start),
            "date_end": helpers._date_short(agreement.date_end),
            "currency": agreement.currency_id,
            "rows": helpers._compact_rows(agreement._l10n_vn_agreement_rows()),
            "terms": False if is_html_empty(agreement.description) else agreement.description,
            "norms": agreement._l10n_vn_material_norms() if processing else [],
            "signers": [
                {"role": "Đại diện " + buyer_title.lower(), "hint": CONFIRM_HINT, "name": ""},
                {"role": "Đại diện " + seller_title.lower(), "hint": CONFIRM_HINT, "name": ""},
            ],
        }
