# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    l10n_vn_advance_settlement_ids = fields.One2many(
        "l10n_vn.payroll.advance.settlement",
        "payslip_id",
        string="Advance Settlements",
        readonly=True,
    )

    def _l10n_vn_advances(self):
        """Paid advances up to the month's end, oldest first, with what is open (D7)."""
        self.ensure_one()
        advances = (
            self.env["l10n_vn.payroll.advance"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("state", "=", "paid"),
                    ("paid_date", "<=", self.date_to),
                ],
                order="paid_date, id",
            )
        )
        open_amounts = advances._l10n_vn_open_amounts(self)
        return [
            {"id": advance.id, "amount": int(round(open_amounts[advance.id]))}
            for advance in advances
            if open_amounts[advance.id] > 0
        ]

    def _l10n_vn_prepare_one(self, builder, by_key):
        super()._l10n_vn_prepare_one(builder, by_key)
        payslip = self.sudo()
        payslip.l10n_vn_advance_settlement_ids.unlink()
        self.env["l10n_vn.payroll.advance.settlement"].sudo().create(
            [
                {"advance_id": advance["id"], "payslip_id": payslip.id,
                 "amount": advance["settled"]}
                for advance in (payslip.l10n_vn_context or {}).get("advances", [])
                if advance.get("settled", 0) > 0
            ]
        )

    def _l10n_vn_record_stop(self, code, message):
        super()._l10n_vn_record_stop(code, message)
        self.sudo().l10n_vn_advance_settlement_ids.unlink()
