# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

try:
    from num2words import num2words
except ImportError:
    num2words = None

from odoo import models
from odoo.tools import float_round


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def l10n_vn_amount_to_words(self, amount):
        """The amount in Vietnamese words, for VND only: "Một triệu năm nghìn đồng"."""
        self.ensure_one()
        if self.name != "VND" or num2words is None:
            return ""
        value = int(float_round(abs(amount), precision_digits=0))
        words = num2words(value, lang="vi")
        return words[:1].upper() + words[1:] + " đồng"
