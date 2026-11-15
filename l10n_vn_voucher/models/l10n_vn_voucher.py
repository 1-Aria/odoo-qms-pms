# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

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

    @api.model
    def _date_short(self, date):
        """dd/mm/yyyy, or "" for no date."""
        if not date:
            return ""
        return "%02d/%02d/%d" % (date.day, date.month, date.year)

    @api.model
    def _numbered_rows(self, rows):
        """The rows with a "number" key: product rows numbered from 1, sections
        and notes not counted (False)."""
        number = 0
        numbered = []
        for row in rows:
            if row.get("display_type"):
                numbered.append(dict(row, number=False))
            else:
                number += 1
                numbered.append(dict(row, number=number))
        return numbered

    @api.model
    def _compact_rows(self, rows):
        """One row per style on the compact order forms.

        Sections and notes are dropped. The rows of a configurable template that
        appears on more than one row, the products core's variant grid shows, are
        grouped by template, unit, price, discount and taxes; a group takes the
        place of its first member. Other rows are kept as they are.
        """
        product_rows = [row for row in rows if not row.get("display_type")]
        counts = Counter(
            row["product"].product_tmpl_id.id for row in product_rows if row.get("product")
        )
        groups = {}
        result = []
        for row in product_rows:
            template = row["product"].product_tmpl_id if row.get("product") else False
            if template and template.has_configurable_attributes and counts[template.id] > 1:
                key = (template.id, row["uom"], row["price"], row["discount"], row["taxes"])
                group = groups.get(key)
                if group:
                    group["qty"] += row["qty"]
                    group["amount"] += row["amount"]
                    continue
                group = dict(row, name=template.name, code="", grouped=True)
                groups[key] = group
                result.append(group)
            else:
                result.append(dict(row, grouped=False))
        return result

    @api.model
    def _qty_text(self, qty):
        """A grid quantity without trailing zeros, Vietnamese decimal comma: 10, 2,5."""
        return ("%g" % (qty or 0)).replace(".", ",")
