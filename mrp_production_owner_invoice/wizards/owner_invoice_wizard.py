# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
from odoo.fields import Command


def _previous_month(today):
    last = today.replace(day=1) - timedelta(days=1)
    return last.replace(day=1), last


class OwnerInvoiceWizard(models.TransientModel):
    _name = "mrp.production.owner.invoice.wizard"
    _description = "Processing Invoice for an Owner"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    owner_id = fields.Many2one("res.partner", string="Goods Owner", required=True)
    date_from = fields.Date(
        required=True,
        default=lambda self: _previous_month(fields.Date.context_today(self))[0],
    )
    date_to = fields.Date(
        required=True,
        default=lambda self: _previous_month(fields.Date.context_today(self))[1],
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Fee Pricelist",
        required=True,
        default=lambda self: self.env.company.owner_invoice_pricelist_id,
    )
    fee_product_id = fields.Many2one(
        "product.product",
        string="Fee Product",
        required=True,
        domain=[("type", "=", "service")],
        default=lambda self: self.env.company.owner_invoice_fee_product_id,
    )
    material_product_id = fields.Many2one(
        "product.product",
        string="Material Product",
        required=True,
        domain=[("type", "=", "service")],
        default=lambda self: self.env.company.owner_invoice_material_product_id,
    )
    marker = fields.Char(string="Late Attribution Marker", default="đã dùng cho đơn")
    late_account_id = fields.Many2one(
        "account.account",
        string="Late Attribution Account",
        compute="_compute_late_account_id",
        store=True,
        readonly=False,
    )
    origin = fields.Char(compute="_compute_origin")
    line_ids = fields.One2many(
        "mrp.production.owner.invoice.wizard.line",
        "wizard_id",
        compute="_compute_line_ids",
        store=True,
        readonly=False,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    material_amount = fields.Monetary(
        string="Company Material at Cost", compute="_compute_material_amount"
    )
    late_line_ids = fields.Many2many(
        "account.move.line", string="Late Attributions", compute="_compute_late_line_ids"
    )
    warning = fields.Text(compute="_compute_warning")

    # Helpers --------------------------------------------------------------------------------

    def _period_bounds(self):
        """The period's days in the user's time zone, as naive UTC datetimes."""
        self.ensure_one()
        tz = pytz.timezone(self.env.user.tz or "UTC")

        def utc(day):
            return tz.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)

        return utc(self.date_from), utc(self.date_to + timedelta(days=1))

    def _production_domain(self, prefix):
        self.ensure_one()
        return [
            (f"{prefix}.owner_id", "=", self.owner_id.id),
            (f"{prefix}.production_owned", "=", True),
            (f"{prefix}.company_id", "=", self.company_id.id),
        ]

    # Computes -------------------------------------------------------------------------------

    @api.depends("material_product_id", "company_id")
    def _compute_late_account_id(self):
        for wizard in self:
            template = wizard.material_product_id.product_tmpl_id.with_company(wizard.company_id)
            wizard.late_account_id = template._get_product_accounts()["expense"] if template else False

    @api.depends("owner_id", "date_to")
    def _compute_origin(self):
        for wizard in self:
            wizard.origin = (
                f"Gia công {wizard.owner_id.name} {wizard.date_to:%m/%Y}"
                if wizard.owner_id and wizard.date_to
                else False
            )

    @api.depends("owner_id", "date_from", "date_to", "pricelist_id", "company_id")
    def _compute_line_ids(self):
        for wizard in self:
            commands = [Command.clear()]
            if wizard.owner_id and wizard.date_from and wizard.date_to:
                start, end = wizard._period_bounds()
                moves = self.env["stock.move"].search(
                    wizard._production_domain("production_id")
                    + [("state", "=", "done"), ("date", ">=", start), ("date", "<", end)]
                )
                quantities = defaultdict(float)
                for move in moves.filtered(lambda m: m.product_id == m.production_id.product_id):
                    quantities[move.product_id.product_tmpl_id] += move.product_uom._compute_quantity(
                        move.quantity, move.product_id.uom_id
                    )
                for template in sorted(quantities, key=lambda t: t.display_name):
                    quantity = quantities[template]
                    rule = wizard.pricelist_id._get_product_rule(template, quantity) if wizard.pricelist_id else False
                    price = wizard.pricelist_id._get_product_price(template, quantity) if rule else 0.0
                    commands.append(Command.create({
                        "product_tmpl_id": template.id,
                        "quantity": quantity,
                        "price_unit": price,
                        "has_rule": bool(rule),
                    }))
            wizard.line_ids = commands

    @api.depends("owner_id", "date_from", "date_to", "company_id")
    def _compute_material_amount(self):
        for wizard in self:
            amount = 0.0
            if wizard.owner_id and wizard.date_from and wizard.date_to:
                start, end = wizard._period_bounds()
                # Valuation layers are readable by stock managers only.
                layers = self.env["stock.valuation.layer"].sudo().search(
                    wizard._production_domain("stock_move_id.raw_material_production_id")
                    + [("create_date", ">=", start), ("create_date", "<", end)]
                )
                amount = wizard.company_id.currency_id.round(-sum(layers.mapped("value")))
            wizard.material_amount = amount

    @api.depends("date_from", "date_to", "late_account_id", "marker", "company_id")
    def _compute_late_line_ids(self):
        for wizard in self:
            lines = self.env["account.move.line"]
            if wizard.late_account_id and wizard.marker and wizard.date_from and wizard.date_to:
                lines = lines.search([
                    ("company_id", "=", wizard.company_id.id),
                    ("parent_state", "=", "posted"),
                    ("account_id", "=", wizard.late_account_id.id),
                    ("date", ">=", wizard.date_from),
                    ("date", "<=", wizard.date_to),
                    ("name", "ilike", wizard.marker),
                ])
            wizard.late_line_ids = lines

    @api.depends("line_ids", "origin", "owner_id", "company_id")
    def _compute_warning(self):
        for wizard in self:
            messages = []
            missing = wizard.line_ids.filtered(lambda line: not line.has_rule)
            if missing:
                messages.append(
                    self.env._("No fee in the pricelist for: %s", ", ".join(missing.product_tmpl_id.mapped("display_name")))
                )
            if wizard.origin and wizard.owner_id:
                duplicate = self.env["account.move"].search([
                    ("move_type", "=", "out_invoice"),
                    ("company_id", "=", wizard.company_id.id),
                    ("commercial_partner_id", "=", wizard.owner_id.commercial_partner_id.id),
                    ("invoice_origin", "=", wizard.origin),
                    ("state", "!=", "cancel"),
                ], limit=1)
                if duplicate:
                    messages.append(
                        self.env._("An invoice for this period already exists: %s", duplicate.display_name)
                    )
            wizard.warning = "\n".join(messages) or False

    # Action ---------------------------------------------------------------------------------

    def action_create_invoice(self):
        self.ensure_one()
        period = f"{self.date_to:%m/%Y}"
        lines = [
            Command.create({
                "product_id": self.fee_product_id.id,
                "name": f"Phí gia công {line.product_tmpl_id.name} – {period}",
                "quantity": line.quantity,
                "price_unit": line.price_unit,
            })
            for line in self.line_ids
        ]
        if self.material_amount > 0:
            lines.append(Command.create({
                "product_id": self.material_product_id.id,
                "name": f"Vật tư cung cấp cho gia công – {period}",
                "quantity": 1,
                "price_unit": self.material_amount,
            }))
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.company_id.id)], limit=1
        )
        invoice = self.env["account.move"].with_company(self.company_id).create({
            "move_type": "out_invoice",
            "partner_id": self.owner_id.id,
            "invoice_date": self.date_to,
            "invoice_origin": self.origin,
            "journal_id": journal.id,
            "invoice_line_ids": lines,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }


class OwnerInvoiceWizardLine(models.TransientModel):
    _name = "mrp.production.owner.invoice.wizard.line"
    _description = "Processing Invoice Line"

    wizard_id = fields.Many2one(
        "mrp.production.owner.invoice.wizard", required=True, ondelete="cascade"
    )
    product_tmpl_id = fields.Many2one("product.template", string="Style", required=True)
    quantity = fields.Float(digits="Product Unit of Measure")
    price_unit = fields.Float(string="Fee", digits="Product Price")
    has_rule = fields.Boolean()
    amount = fields.Float(compute="_compute_amount")

    @api.depends("quantity", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.price_unit
