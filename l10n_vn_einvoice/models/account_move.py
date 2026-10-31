# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .l10n_vn_einvoice import normalise_vat


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_vn_einvoice_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice",
        inverse_name="move_id",
        string="E-Invoices",
        copy=False,
    )
    l10n_vn_einvoice_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice",
        string="E-Invoice",
        compute="_compute_l10n_vn_einvoice_id",
    )

    l10n_vn_einvoice_correction_state = fields.Selection(
        string="E-Invoice Correction",
        related="l10n_vn_einvoice_id.correction_state",
    )

    @api.depends("l10n_vn_einvoice_ids")
    def _compute_l10n_vn_einvoice_id(self):
        for move in self:
            move.l10n_vn_einvoice_id = move.l10n_vn_einvoice_ids[:1]

    def action_l10n_vn_einvoice_attach(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_vn_einvoice.l10n_vn_einvoice_attach_action"
        )
        action["context"] = {"default_move_id": self.id}
        return action

    def action_l10n_vn_einvoice_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_vn.einvoice",
            "res_id": self.l10n_vn_einvoice_id.id,
            "views": [(False, "form")],
            "view_mode": "form",
        }

    # ----------------------------------------------------------------------
    # Import (step 2)
    # ----------------------------------------------------------------------

    def _get_edi_decoder(self, file_data, new=False):
        # EXTENDS 'account': claim Vietnamese e-invoices (root HDon).
        if (
            file_data.get("type") == "xml"
            and file_data.get("xml_tree") is not None
            and etree.QName(file_data["xml_tree"]).localname == "HDon"
        ):
            return self.env["l10n_vn.einvoice"]._import_document
        return super()._get_edi_decoder(file_data, new=new)

    # ----------------------------------------------------------------------
    # Posting check (step 2, design D7)
    # ----------------------------------------------------------------------

    def _post(self, soft=True):
        self._l10n_vn_einvoice_check_replaced()
        self._l10n_vn_einvoice_check_partners()
        return super()._post(soft=soft)

    def _l10n_vn_einvoice_check_replaced(self):
        """A document whose e-invoice has been replaced is not posted (step 3)."""
        for move in self.filtered("l10n_vn_einvoice_ids"):
            einvoice = move.l10n_vn_einvoice_ids[:1]
            if einvoice.correction_state != "replaced":
                continue
            replacements = einvoice.correction_ids.filtered(
                lambda correction: correction.relation_type in ("1", "3")
            )
            raise UserError(
                _(
                    "%(document)s: its e-invoice %(name)s was replaced by %(replacements)s. "
                    "Book the replacement instead, and cancel this document.",
                    document=move.display_name,
                    name=einvoice.name,
                    replacements=", ".join(replacements.mapped("name")),
                )
            )

    def _l10n_vn_einvoice_check_partners(self):
        Einvoice = self.env["l10n_vn.einvoice"]
        for move in self.filtered("l10n_vn_einvoice_ids"):
            einvoice = move.l10n_vn_einvoice_ids[:1]
            if move.is_purchase_document(include_receipts=True):
                vat = einvoice.seller_vat
            else:
                vat = einvoice.buyer_vat
            partner = move.commercial_partner_id
            if not vat or not partner:
                continue
            partner_vat = normalise_vat(partner.vat)
            if partner_vat == vat:
                continue
            if partner_vat:
                raise UserError(
                    _(
                        "%(document)s: its partner %(partner)s has tax code "
                        "%(partner_vat)s, but e-invoice %(name)s names %(vat)s. Choose the "
                        "partner with that tax code, or correct the partner's.",
                        document=move.display_name,
                        partner=partner.display_name,
                        partner_vat=partner.vat,
                        name=einvoice.name,
                        vat=vat,
                    )
                )
            others = Einvoice._find_partner(vat, move.company_id) - partner
            if others:
                raise UserError(
                    _(
                        "%(document)s: its partner %(partner)s has no tax code, while "
                        "%(others)s already hold %(vat)s, the tax code on e-invoice "
                        "%(name)s. Choose that partner.",
                        document=move.display_name,
                        partner=partner.display_name,
                        others=", ".join(others.mapped("display_name")),
                        vat=vat,
                        name=einvoice.name,
                    )
                )
            # sudo: writing partners needs Contact Creation, and this fill follows
            # from the check, not from the user's edit (D19).
            partner.sudo().write({"vat": vat})
            partner.sudo().message_post(
                body=_(
                    "Tax code %(vat)s set from e-invoice %(name)s when %(document)s was "
                    "posted.",
                    vat=vat,
                    name=einvoice.name,
                    document=move.display_name,
                ),
                author_id=self.env.user.partner_id.id,
            )
