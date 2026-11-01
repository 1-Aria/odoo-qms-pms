# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nVnEinvoice(models.Model):
    _inherit = "l10n_vn.einvoice"

    portal_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice.portal",
        inverse_name="einvoice_id",
        string="On the Portal",
        # Invoicing users read e-invoices but not portal invoices.
        groups="account.group_account_readonly,account.group_account_manager",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """A new e-invoice links the portal invoices waiting for it (D19).
        As superuser: Invoicing users create e-invoices when they upload bills,
        and cannot read portal invoices."""
        records = super().create(vals_list)
        Portal = self.env["l10n_vn.einvoice.portal"].sudo()
        for einvoice in records:
            waiting = Portal.search(
                [
                    ("company_id", "=", einvoice.company_id.id),
                    (
                        "direction",
                        "=",
                        "purchase" if einvoice.direction == "received" else "sale",
                    ),
                    ("seller_vat", "=", einvoice.seller_vat),
                    ("form", "=", einvoice.form),
                    ("symbol", "=", einvoice.symbol),
                    ("number", "=", einvoice.number),
                    ("einvoice_id", "=", False),
                ]
            )
            if waiting:
                waiting.write({"einvoice_id": einvoice.id})
        return records
