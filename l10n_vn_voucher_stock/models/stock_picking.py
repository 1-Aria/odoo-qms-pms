# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

SIGN_HINT = "(Ký, họ tên)"
CHIEF_ACCOUNTANT_HINT = "(Hoặc bộ phận có nhu cầu nhập)\n(Ký, họ tên)"

KIND_TEXTS = {
    "in": {
        "title": "PHIẾU NHẬP KHO",
        "form_code": "01-VT",
        "party_role": "Người giao hàng",
        "party_label": "Họ và tên người giao hàng",
        "reason_label": "Lý do nhập kho",
        "warehouse_label": "Nhập tại kho",
        "done_label": "Thực nhập",
    },
    "out": {
        "title": "PHIẾU XUẤT KHO",
        "form_code": "02-VT",
        "party_role": "Người nhận hàng",
        "party_label": "Họ và tên người nhận hàng",
        "reason_label": "Lý do xuất kho",
        "warehouse_label": "Xuất tại kho (ngăn lô)",
        "done_label": "Thực xuất",
    },
}


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_vn_voucher_kind = fields.Selection(
        related="picking_type_id.l10n_vn_voucher_kind",
    )
    l10n_vn_voucher_reason = fields.Char(
        string="Voucher Reason",
        copy=False,
        help="Lý do nhập / xuất kho for this transfer's voucher. Empty: the operation "
        "type's, or for a return the transfer it returns.",
    )

    def _l10n_vn_voucher_reason_text(self):
        self.ensure_one()
        if self.l10n_vn_voucher_reason:
            return self.l10n_vn_voucher_reason
        if self.return_id:
            return "Trả lại hàng theo phiếu %s" % self.return_id.name
        picking_type = self.picking_type_id.with_context(lang="vi_VN")
        return picking_type.l10n_vn_voucher_reason or ""

    def _l10n_vn_voucher_lines(self):
        """One row per move not cancelled. Prices and amounts only from the layers
        of a done transfer, read as superuser: storekeepers cannot read layers."""
        self.ensure_one()
        done = self.state == "done"
        moves = self.move_ids.filtered(lambda move: move.state != "cancel").sorted(
            lambda move: (move.sequence, move.id)
        )
        lines = []
        for move in moves:
            price = amount = None
            layers = move.sudo().stock_valuation_layer_ids
            if done and layers:
                amount = abs(sum(layers.mapped("value")))
                price = amount / move.quantity if move.quantity else None
            lines.append(
                {
                    "name": move.product_id.with_context(
                        display_default_code=False
                    ).display_name,
                    "code": move.product_id.default_code or "",
                    "uom": move.product_uom.name,
                    "demand": move.product_uom_qty,
                    "done": move.quantity if done else None,
                    "price": price,
                    "amount": amount,
                }
            )
        return lines

    def _l10n_vn_voucher_accounts(self):
        """(debit codes, credit codes) of the posted valuation entries, read as
        superuser: storekeepers cannot read journal items."""
        self.ensure_one()
        if self.state != "done":
            return [], []
        entries = self.sudo().move_ids.account_move_ids.filtered(
            lambda entry: entry.state == "posted"
        )
        items = entries.line_ids

        def codes(lines):
            accounts = lines.account_id.with_company(self.company_id)
            return sorted(set(accounts.mapped("code")))

        return (
            codes(items.filtered(lambda line: line.debit > 0)),
            codes(items.filtered(lambda line: line.credit > 0)),
        )

    def _l10n_vn_voucher_data(self):
        """Everything the stock voucher prints; the template only lays it out."""
        self.ensure_one()
        kind = self.picking_type_id.l10n_vn_voucher_kind
        if not kind:
            raise UserError(
                _(
                    "%(transfer)s: its operation type %(type)s prints no Vietnamese "
                    "voucher.",
                    transfer=self.name,
                    type=self.picking_type_id.display_name,
                )
            )
        picking = self.with_context(lang="vi_VN")
        helpers = self.env["l10n_vn.voucher"]
        texts = KIND_TEXTS[kind]
        lines = picking._l10n_vn_voucher_lines()
        amounts = [line["amount"] for line in lines if line["amount"] is not None]
        debit_accounts, credit_accounts = picking._l10n_vn_voucher_accounts()
        partner = picking.partner_id
        warehouse = picking.picking_type_id.warehouse_id
        location = (
            picking.location_dest_id if kind == "in" else picking.location_id
        )
        signers = [
            {
                "role": "Người lập phiếu",
                "hint": SIGN_HINT,
                "name": picking.user_id.name or "",
            },
            {"role": texts["party_role"], "hint": SIGN_HINT, "name": ""},
            {"role": "Thủ kho", "hint": SIGN_HINT, "name": ""},
            {"role": "Kế toán trưởng", "hint": CHIEF_ACCOUNTANT_HINT, "name": ""},
        ]
        if kind == "out":
            signers.append({"role": "Giám đốc", "hint": SIGN_HINT, "name": ""})
        return {
            "kind": kind,
            "title": texts["title"],
            "form_code": texts["form_code"],
            "company": picking.company_id,
            "department": warehouse.name or "",
            "number": picking.name,
            "date": helpers._local_date(picking, picking.date_done)
            if picking.state == "done"
            else False,
            "debit_accounts": debit_accounts,
            "credit_accounts": credit_accounts,
            "party_label": texts["party_label"],
            "party": partner.display_name or "",
            "party_address": helpers._address(partner),
            "reason_label": texts["reason_label"],
            "reason": picking._l10n_vn_voucher_reason_text(),
            "source": picking.origin or "",
            "source_partner": partner.commercial_partner_id.name or "",
            "warehouse_label": texts["warehouse_label"],
            "warehouse": warehouse.name or "",
            "location": location.complete_name or "",
            "done_label": texts["done_label"],
            "lines": lines,
            "total": sum(amounts) if amounts else False,
            "currency": picking.company_id.currency_id,
            "copies": picking.picking_type_id.l10n_vn_voucher_copies,
            "signers": signers,
        }
