# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    material_batch_id = fields.Many2one(
        comodel_name="sale.material.batch",
        string="Material Transfer Batch",
        readonly=True,
        copy=False,
        index="btree_not_null",
        ondelete="set null",
        check_company=True,
    )

    def _material_einvoice_ok(self):
        """A posted vendor bill backed by a correct received e-invoice: not replaced,
        and with the bill's untaxed amount, VAT and total (design D11)."""
        self.ensure_one()
        return (
            self.state == "posted"
            and self.move_type == "in_invoice"
            and any(
                einvoice.direction == "received"
                and einvoice.correction_state != "replaced"
                and not einvoice.amounts_differ
                for einvoice in self.l10n_vn_einvoice_ids
            )
        )
