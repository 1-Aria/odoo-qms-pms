# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date, formatLang

# Fields an approved rate keeps for good. A correction is a new rate.
LOCKED_FIELDS = {
    "company_id",
    "date_from",
    "rate",
    "state",
    "approved_by_id",
    "approved_date",
}


class MrpConversionCostRate(models.Model):
    _name = "mrp.conversion.cost.rate"
    _description = "Conversion Cost Rate"
    _inherit = ["mail.thread"]
    _order = "company_id, date_from desc, id desc"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(string="Valid From", required=True, tracking=True)
    # A Float, not a Monetary: a Monetary rounds to the currency, and VND
    # rounds to whole units, which would cut a rate such as 1,494.25.
    rate = fields.Float(
        string="Rate per Minute",
        digits="Product Price",
        required=True,
        tracking=True,
        help="Cost of one standard minute of conversion work (labour and "
        "overhead), in the company's currency.",
    )
    note = fields.Text(
        string="Basis",
        tracking=True,
        help="How the rate was set, e.g. the period's conversion cost and the "
        "minutes it is spread over.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_by_id = fields.Many2one(
        "res.users", string="Approved By", readonly=True, copy=False
    )
    approved_date = fields.Datetime(string="Approved On", readonly=True, copy=False)
    production_count = fields.Integer(compute="_compute_production_count")

    _sql_constraints = [
        (
            "rate_positive",
            "CHECK (rate > 0)",
            "The rate per minute must be positive.",
        ),
        (
            "company_date_unique",
            "UNIQUE (company_id, date_from)",
            "A company can have only one conversion cost rate per start date.",
        ),
    ]

    @api.depends("date_from", "rate")
    def _compute_display_name(self):
        digits = self.env["decimal.precision"].precision_get("Product Price")
        for record in self:
            if record.date_from:
                record.display_name = "%s · %s" % (
                    format_date(self.env, record.date_from),
                    formatLang(self.env, record.rate, digits=digits),
                )
            else:
                record.display_name = self.env._("New Rate")

    def _compute_production_count(self):
        # sudo: accounting users may read rates without manufacturing rights.
        counts = dict(
            self.env["mrp.production"]
            .sudo()
            ._read_group(
                [("conversion_rate_id", "in", self.ids)],
                ["conversion_rate_id"],
                ["__count"],
            )
        )
        for record in self:
            record.production_count = counts.get(record, 0)

    def write(self, vals):
        if LOCKED_FIELDS.intersection(vals) and any(
            record.state == "approved" for record in self
        ):
            raise UserError(
                self.env._(
                    "An approved conversion cost rate cannot be changed. "
                    "Approve a new rate with a later start date instead."
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_approved(self):
        if any(record.state == "approved" for record in self):
            raise UserError(
                self.env._("An approved conversion cost rate cannot be deleted.")
            )

    def action_approve(self):
        if any(record.state != "draft" for record in self):
            raise UserError(self.env._("Only draft rates can be approved."))
        today = fields.Date.context_today(self)
        if any(record.date_from < today for record in self):
            raise UserError(
                self.env._(
                    "A conversion cost rate cannot start before today "
                    "(%(today)s): manufacturing orders already done keep the "
                    "rate they were valued at.",
                    today=format_date(self.env, today),
                )
            )
        # The records are still drafts here, so write() allows it.
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.uid,
                "approved_date": fields.Datetime.now(),
            }
        )
        return True

    def action_view_productions(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Valued Manufacturing Orders"),
            "res_model": "mrp.production",
            "view_mode": "list,form",
            "domain": [("conversion_rate_id", "in", self.ids)],
            "context": {"create": False},
        }

    @api.model
    def _rate_on(self, company, date):
        """The approved rate of ``company`` in force on ``date``, or an empty
        recordset. Read as superuser: valuing an MO needs no rights on rates."""
        return self.sudo().search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "approved"),
                ("date_from", "<=", date),
            ],
            order="date_from desc, id desc",
            limit=1,
        )
