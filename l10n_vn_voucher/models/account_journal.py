# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

COPIES_HELP = "One line per copy, with the label it prints. Empty: one copy without a label."


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_vn_cash_in_sequence_id = fields.Many2one(
        "ir.sequence", string="Phiếu thu Sequence", copy=False, check_company=True
    )
    l10n_vn_cash_out_sequence_id = fields.Many2one(
        "ir.sequence", string="Phiếu chi Sequence", copy=False, check_company=True
    )
    l10n_vn_cash_in_copies = fields.Text(string="Phiếu thu Copies", help=COPIES_HELP)
    l10n_vn_cash_out_copies = fields.Text(string="Phiếu chi Copies", help=COPIES_HELP)

    def _l10n_vn_voucher_sequence(self, kind):
        """The journal's series for cash_in or cash_out, created the first time it
        is needed: PT/2026/0001, PC/2026/0001, a new range each year, no gaps.
        Created and read as superuser: whoever posts the entry draws the number."""
        self.ensure_one()
        cash_in = kind == "cash_in"
        fname = "l10n_vn_cash_in_sequence_id" if cash_in else "l10n_vn_cash_out_sequence_id"
        journal = self.sudo()
        sequence = journal[fname]
        if not sequence:
            label, prefix = ("Phiếu thu", "PT") if cash_in else ("Phiếu chi", "PC")
            sequence = journal.env["ir.sequence"].create(
                {
                    "name": "%s – %s" % (journal.name, label),
                    "implementation": "no_gap",
                    "prefix": prefix + "/%(range_year)s/",
                    "padding": 4,
                    "use_date_range": True,
                    "company_id": journal.company_id.id,
                }
            )
            journal[fname] = sequence
        return sequence
