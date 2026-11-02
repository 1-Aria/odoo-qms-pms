# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class L10nVnPayrollScale(models.Model):
    _name = "l10n_vn.payroll.scale"
    _description = "Payroll Scale"
    _order = "code"

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    kind = fields.Selection(
        [("grade_step", "Grade and step"), ("level", "Level")], required=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    version_ids = fields.One2many("l10n_vn.payroll.scale.version", "scale_id")

    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "A scale code must be unique per company.",
        ),
    ]

    def _version_on(self, date):
        self.ensure_one()
        versions = self.version_ids.filtered(lambda v: v.date_from <= date)
        return versions.sorted("date_from", reverse=True)[:1]

    def _cell_amount(self, key, date):
        self.ensure_one()
        version = self._version_on(date)
        if not version:
            raise UserError(
                self.env._(
                    "Scale %(scale)s has no version on %(date)s.",
                    scale=self.code,
                    date=date,
                )
            )
        cell = version.cell_ids.filtered(lambda c: c.key == key)
        if not cell:
            raise UserError(
                self.env._(
                    "Scale %(scale)s has no cell %(key)s on %(date)s.",
                    scale=self.code,
                    key=key,
                    date=date,
                )
            )
        return cell.amount

    def _has_key(self, key):
        self.ensure_one()
        return key in self.version_ids.cell_ids.mapped("key")


class L10nVnPayrollScaleVersion(models.Model):
    _name = "l10n_vn.payroll.scale.version"
    _description = "Payroll Scale Version"
    _order = "scale_id, date_from desc"
    _rec_name = "date_from"

    scale_id = fields.Many2one(
        "l10n_vn.payroll.scale", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="scale_id.company_id", store=True)
    date_from = fields.Date(required=True)
    note = fields.Char()
    cell_ids = fields.One2many("l10n_vn.payroll.scale.cell", "version_id", copy=True)

    _sql_constraints = [
        (
            "scale_date_unique",
            "unique(scale_id, date_from)",
            "A scale cannot have two versions starting the same day.",
        ),
    ]


class L10nVnPayrollScaleCell(models.Model):
    _name = "l10n_vn.payroll.scale.cell"
    _description = "Payroll Scale Cell"
    _order = "version_id, key"

    version_id = fields.Many2one(
        "l10n_vn.payroll.scale.version", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="version_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    key = fields.Char(required=True)
    grade = fields.Char()
    step = fields.Integer()
    amount = fields.Monetary(required=True)

    _sql_constraints = [
        (
            "version_key_unique",
            "unique(version_id, key)",
            "A key appears once in a scale version.",
        ),
    ]
