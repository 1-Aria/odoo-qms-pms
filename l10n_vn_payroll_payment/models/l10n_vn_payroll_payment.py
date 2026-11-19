# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .l10n_vn_payroll_advance import OFFICER, _employee_names

METHODS = [("transfer", "Transfer"), ("cash", "Cash")]


class L10nVnPayrollPayment(models.Model):
    _name = "l10n_vn.payroll.payment"
    _description = "Payroll Payment List"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True)
    kind = fields.Selection(
        [("payroll", "Payroll"), ("advance", "Advances")], required=True, readonly=True
    )
    run_id = fields.Many2one(
        "hr.payslip.run", readonly=True, ondelete="restrict", index=True, check_company=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, readonly=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date = fields.Date(
        string="Payment Date Requested", required=True, default=fields.Date.context_today
    )
    company_bank_id = fields.Many2one(
        "res.partner.bank",
        string="Paying Account",
        domain="[('partner_id', '=', company_partner_id)]",
        default=lambda self: self._default_company_bank(),
    )
    company_partner_id = fields.Many2one(related="company_id.partner_id")
    line_ids = fields.One2many("l10n_vn.payroll.payment.line", "payment_id")
    transfer_line_ids = fields.One2many(
        "l10n_vn.payroll.payment.line", compute="_compute_method_lines"
    )
    cash_line_ids = fields.One2many(
        "l10n_vn.payroll.payment.line", compute="_compute_method_lines"
    )
    amount_transfer = fields.Monetary(string="Transfers", compute="_compute_totals", store=True)
    amount_cash = fields.Monetary(string="Cash", compute="_compute_totals", store=True)
    amount_total = fields.Monetary(string="Total", compute="_compute_totals", store=True)
    state = fields.Selection(
        [("to_pay", "To Pay"), ("paid", "Paid")],
        compute="_compute_totals",
        store=True,
        default="to_pay",
    )

    _sql_constraints = [
        ("run_unique", "unique(run_id)", "A run has one payment list."),
    ]

    @api.model
    def _default_company_bank(self, company=None):
        company = company or self.env.company
        return self.env["res.partner.bank"].sudo().search(
            [("partner_id", "=", company.partner_id.id)], order="sequence, id", limit=1
        )

    @api.depends("line_ids.method")
    def _compute_method_lines(self):
        for payment in self:
            payment.transfer_line_ids = payment.line_ids.filtered(lambda l: l.method == "transfer")
            payment.cash_line_ids = payment.line_ids.filtered(lambda l: l.method == "cash")

    @api.depends("line_ids.amount", "line_ids.method", "line_ids.state")
    def _compute_totals(self):
        for payment in self:
            lines = payment.line_ids
            payment.amount_transfer = sum(lines.filtered(lambda l: l.method == "transfer").mapped("amount"))
            payment.amount_cash = sum(lines.filtered(lambda l: l.method == "cash").mapped("amount"))
            payment.amount_total = sum(lines.mapped("amount"))
            payment.state = (
                "paid" if lines and all(line.state == "paid" for line in lines) else "to_pay"
            )

    def unlink(self):
        if any(payment.run_id for payment in self):
            raise UserError(self.env._("A run's payment list cannot be deleted."))
        if any(payment.line_ids.filtered(lambda l: l.state == "paid") for payment in self):
            raise UserError(self.env._("A list with paid lines cannot be deleted."))
        return super().unlink()

    # ------------------------------------------------------------------ making lists (D20, D21)
    @api.model
    def _l10n_vn_method(self, contract):
        participant = contract.sudo().l10n_vn_participant_type_id
        return "transfer" if participant.paid_by_transfer else "cash"

    @api.model
    def _l10n_vn_create_list(self, vals, lines):
        lines = sorted(lines, key=lambda line: (line["employee"].name or "", line["employee"].id))
        vals["line_ids"] = [
            Command.create(
                {
                    "sequence": sequence,
                    "employee_id": line["employee"].id,
                    "payslip_id": line.get("payslip_id"),
                    "advance_id": line.get("advance_id"),
                    "amount": line["amount"],
                    "method": line["method"],
                    "bank_account_id": (
                        line["employee"].bank_account_id.id
                        if line["method"] == "transfer"
                        else False
                    ),
                }
            )
            for sequence, line in enumerate(lines, start=1)
        ]
        return self.sudo().create(vals)

    @api.model
    def _l10n_vn_from_run(self, run):
        """The run's list: a line per payslip with something to pay (D20)."""
        run = run.sudo()
        lines = [
            {
                "employee": slip.employee_id,
                "payslip_id": slip.id,
                "amount": slip.l10n_vn_to_pay,
                "method": self._l10n_vn_method(slip.contract_id),
            }
            for slip in run.slip_ids
            if slip.l10n_vn_to_pay > 0
        ]
        if not lines:
            return self.browse()
        return self._l10n_vn_create_list(
            {
                "name": run.name,
                "kind": "payroll",
                "run_id": run.id,
                "company_id": run.company_id.id,
                "company_bank_id": self._default_company_bank(run.company_id).id,
            },
            lines,
        )

    @api.model
    def _l10n_vn_from_advances(self, advances, name):
        """A list of the approved advances not yet on one (D21)."""
        advances = advances.sudo().filtered(
            lambda a: a.state == "approved" and not a.payment_line_ids
        )
        if not advances:
            raise UserError(self.env._("No approved advance left to pay."))
        company = advances.company_id
        if len(company) > 1:
            raise UserError(self.env._("A payment list holds advances of one company."))
        lines = []
        for advance in advances:
            contract = advance._l10n_vn_month_contract(advance.employee_id, advance.date)
            lines.append(
                {
                    "employee": advance.employee_id,
                    "advance_id": advance.id,
                    "amount": advance.amount,
                    "method": self._l10n_vn_method(contract),
                }
            )
        return self._l10n_vn_create_list(
            {
                "name": name,
                "kind": "advance",
                "company_id": company.id,
                "company_bank_id": self._default_company_bank(company).id,
            },
            lines,
        )

    # ------------------------------------------------------------------ the files (D23, D24)
    def action_transfer_file(self):
        self.ensure_one()
        self.env["l10n_vn.payroll.advance"]._l10n_vn_require(OFFICER)
        transfers = self.transfer_line_ids
        if not transfers:
            raise UserError(self.env._("There is no transfer to pay in this list."))
        missing = transfers.filtered(lambda l: not l.bank_account_id)
        if missing:
            raise UserError(
                self.env._(
                    "No bank account on the transfers of %(employees)s.",
                    employees=_employee_names(missing),
                )
            )
        template = self.env.ref("l10n_vn_payroll_payment.xlsx_bank_transfer")
        out_file, _name = self.env["xlsx.export"].export_xlsx(template, self._name, self.ids)
        if isinstance(out_file, str):
            out_file = out_file.encode()
        # an .xlsx file is a zip archive ("PK"); anything else came base64-encoded
        content = out_file if out_file[:2] == b"PK" else base64.decodebytes(out_file)
        attachment = self.env["ir.attachment"].create(
            {
                "name": self.env._("%(name)s - transfer.xlsx", name=self.name),
                "datas": base64.b64encode(content),
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

    def action_print_cash_list(self):
        self.ensure_one()
        if not self.cash_line_ids:
            raise UserError(self.env._("There is no cash payment in this list."))
        return self.env.ref(
            "l10n_vn_payroll_payment.action_report_l10n_vn_cash_list"
        ).report_action(self)

    # ------------------------------------------------------------------ paying (D25)
    def _l10n_vn_open_pay(self, method):
        self.ensure_one()
        self.env["l10n_vn.payroll.advance"]._l10n_vn_require(OFFICER)
        lines = self.line_ids.filtered(lambda l: l.method == method and l.state == "to_pay")
        if not lines:
            raise UserError(self.env._("Nothing of this kind is left to pay."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Mark as Paid"),
            "res_model": "l10n_vn.payroll.payment.pay",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_payment_id": self.id,
                "default_method": method,
                "default_line_ids": [Command.set(lines.ids)],
            },
        }

    def action_open_pay_transfer(self):
        return self._l10n_vn_open_pay("transfer")

    def action_open_pay_cash(self):
        return self._l10n_vn_open_pay("cash")

    def _l10n_vn_after_paid(self):
        """A paid list pays its run (D25)."""
        for payment in self.sudo():
            if payment.state == "paid" and payment.run_id.state == "approved":
                payment.run_id.write({"state": "paid"})


class L10nVnPayrollPaymentLine(models.Model):
    _name = "l10n_vn.payroll.payment.line"
    _description = "Payroll Payment Line"
    _order = "payment_id, method, sequence, id"

    payment_id = fields.Many2one(
        "l10n_vn.payroll.payment", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer()
    number = fields.Integer(string="No.", compute="_compute_number")
    payslip_id = fields.Many2one("hr.payslip", readonly=True, ondelete="restrict", index=True)
    advance_id = fields.Many2one(
        "l10n_vn.payroll.advance", readonly=True, ondelete="restrict", index=True
    )
    employee_id = fields.Many2one("hr.employee", required=True, readonly=True)
    employee_partner_id = fields.Many2one(related="employee_id.work_contact_id")
    company_id = fields.Many2one(related="payment_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    amount = fields.Monetary(required=True, readonly=True)
    method = fields.Selection(METHODS, required=True, readonly=True)
    bank_account_id = fields.Many2one(
        "res.partner.bank",
        string="Bank Account",
        domain="[('partner_id', '=', employee_partner_id)]",
    )
    state = fields.Selection(
        [("to_pay", "To Pay"), ("paid", "Paid")], required=True, default="to_pay", readonly=True
    )
    paid_date = fields.Date(string="Payment Date", readonly=True)

    _sql_constraints = [
        (
            "one_source",
            "CHECK((payslip_id IS NULL) != (advance_id IS NULL))",
            "A payment line pays one payslip or one advance.",
        ),
    ]

    @api.depends("payment_id.line_ids.method", "payment_id.line_ids.sequence")
    def _compute_number(self):
        for line in self:
            same = line.payment_id.line_ids.filtered(lambda l: l.method == line.method).sorted(
                lambda l: (l.sequence, l.id)
            )
            line.number = (list(same.ids).index(line.id) + 1) if line.id in same.ids else 0

    def write(self, vals):
        if not self.env.su and any(line.state == "paid" for line in self):
            raise UserError(self.env._("A paid line does not change."))
        return super().write(vals)

    def _l10n_vn_mark_paid(self, paid_date):
        """Pays the lines, their advances and, once complete, the list's run (D25, D27)."""
        self.env["l10n_vn.payroll.advance"]._l10n_vn_require(OFFICER)
        if any(line.state != "to_pay" for line in self):
            raise UserError(self.env._("Only an unpaid line is marked as paid."))
        lines = self.sudo()
        lines.write({"state": "paid", "paid_date": paid_date})
        lines.advance_id._l10n_vn_mark_paid(paid_date)
        lines.payment_id._l10n_vn_after_paid()
        return True
