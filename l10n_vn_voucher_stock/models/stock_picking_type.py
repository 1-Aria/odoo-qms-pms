# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_vn_voucher_kind = fields.Selection(
        [("in", "Phiếu nhập kho"), ("out", "Phiếu xuất kho")],
        string="Voucher",
        help="The Vietnamese voucher this type's transfers print. Empty: none.",
    )
    l10n_vn_voucher_reason = fields.Char(
        string="Voucher Reason",
        translate=True,
        help="Lý do nhập / xuất kho printed on the voucher, unless the transfer has its own.",
    )
    l10n_vn_voucher_copies = fields.Text(
        string="Voucher Copies",
        help="One line per copy, with the label it prints, such as: Liên 1: Kế toán lưu. "
        "Empty: one copy without a label.",
    )
