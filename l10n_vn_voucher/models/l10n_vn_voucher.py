# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

DATE_DOTTED = "Ngày ..... tháng ..... năm ......."


class L10nVnVoucher(models.AbstractModel):
    """Helpers the voucher templates call through env["l10n_vn.voucher"]."""

    _name = "l10n_vn.voucher"
    _description = "Vietnamese Voucher Helpers"

    @api.model
    def _copy_labels(self, copies):
        labels = [line.strip() for line in (copies or "").splitlines() if line.strip()]
        return labels or [False]

    @api.model
    def _date_text(self, date):
        if not date:
            return DATE_DOTTED
        return "Ngày %02d tháng %02d năm %d" % (date.day, date.month, date.year)

    @api.model
    def _local_date(self, record, value):
        if not value:
            return False
        return fields.Datetime.context_timestamp(record, value).date()

    @api.model
    def _address(self, partner):
        if not partner:
            return ""
        lines = partner._display_address(without_company=True).splitlines()
        return ", ".join(line.strip() for line in lines if line.strip())
