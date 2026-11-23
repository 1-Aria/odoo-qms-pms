# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

try:
    from num2words import num2words
except ImportError:
    num2words = None

from odoo import api, models
from odoo.tools import float_round


class L10nVnContractDocument(models.AbstractModel):
    """Helpers for the contract values and templates (D12)."""

    _name = "l10n_vn.contract.document"
    _description = "Contract Document Helpers"

    @api.model
    def _money(self, amount):
        """4500000 -> "4.500.000"; "" for None."""
        if amount is None:
            return ""
        value = int(float_round(amount, precision_digits=0))
        return f"{value:,}".replace(",", ".")

    @api.model
    def _words(self, amount):
        """The amount in Vietnamese words: "Bốn triệu năm trăm nghìn đồng"."""
        if amount is None or num2words is None:
            return ""
        value = int(float_round(abs(amount), precision_digits=0))
        words = num2words(value, lang="vi")
        return words[:1].upper() + words[1:] + " đồng"

    @api.model
    def _date(self, date):
        """dd/mm/yyyy, or ""."""
        if not date:
            return ""
        return "%02d/%02d/%d" % (date.day, date.month, date.year)

    @api.model
    def _date_parts(self, date):
        """("02", "11", "2026"), or None."""
        if not date:
            return None
        return ("%02d" % date.day, "%02d" % date.month, str(date.year))

    @api.model
    def _address(self, partner):
        """The partner's address on one line, without the company name."""
        if not partner:
            return ""
        lines = partner._display_address(without_company=True).splitlines()
        return ", ".join(line.strip() for line in lines if line.strip())
