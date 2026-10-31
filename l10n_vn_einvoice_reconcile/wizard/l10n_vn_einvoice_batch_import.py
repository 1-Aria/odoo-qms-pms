# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnEinvoiceBatchImport(models.TransientModel):
    _name = "l10n_vn.einvoice.batch.import"
    _description = "Import a Portal List"

    batch_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice.batch",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    list_kind = fields.Selection(related="batch_id.list_kind")
    # A database column, not an attachment: the file is read into rows and not
    # kept, and the transient vacuum removes this record (D1).
    file = fields.Binary(string="Portal List (.xlsx)", required=True, attachment=False)
    filename = fields.Char()

    def action_import(self):
        self.ensure_one()
        content = self.with_context(bin_size=False, bin_size_file=False).file
        self.batch_id._import_file(content, self.filename or "portal.xlsx")
        return {"type": "ir.actions.act_window_close"}
