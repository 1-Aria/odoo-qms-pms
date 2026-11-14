# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare, float_is_zero, float_round

MAX_DEPTH = 10
WARNING_LIST_MAX = 10
QUANTITY_KEYS = ("in", "used", "pending", "awaiting", "not_received", "no_receipt")


class SaleMaterialBatch(models.Model):
    _name = "sale.material.batch"
    _description = "Material Transfer Batch"
    _inherit = ["mail.thread"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(required=True, readonly=True, copy=False, default="New")
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("covered", "Covered"),
            ("cancel", "Cancelled"),
        ],
        compute="_compute_state",
        store=True,
        index=True,
        tracking=True,
    )
    cancelled = fields.Boolean(readonly=True, copy=False)
    date_request = fields.Datetime(string="Requested On", readonly=True, copy=False)
    requested_by_id = fields.Many2one(
        comodel_name="res.users", string="Requested By", readonly=True, copy=False
    )
    order_ids = fields.Many2many(
        comodel_name="sale.order",
        relation="sale_material_batch_order_rel",
        column1="batch_id",
        column2="order_id",
        string="Sales Orders",
        copy=False,
        check_company=True,
        domain="[('company_id', '=', company_id), ('state', '=', 'sale')]",
    )
    need_line_ids = fields.One2many(
        comodel_name="sale.material.batch.need",
        inverse_name="batch_id",
        readonly=True,
    )
    request_line_ids = fields.One2many(
        comodel_name="sale.material.batch.request",
        inverse_name="batch_id",
        readonly=True,
    )
    amount_total = fields.Monetary(
        string="Requested Amount", compute="_compute_amount_total"
    )
    bill_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="material_batch_id",
        string="Bills",
        readonly=True,
    )
    bill_count = fields.Integer(compute="_compute_bill_count")
    warning = fields.Text(compute="_compute_warning")
    note = fields.Text()

    _sql_constraints = [
        (
            "name_company_unique",
            "UNIQUE (name, company_id)",
            "A transfer batch number must be unique per company.",
        ),
    ]

    @api.depends(
        "cancelled",
        "date_request",
        "request_line_ids.request_qty",
        "bill_ids.state",
        "bill_ids.move_type",
        "bill_ids.currency_id",
        "bill_ids.amount_untaxed",
        "bill_ids.amount_tax",
        "bill_ids.amount_total",
        "bill_ids.l10n_vn_einvoice_ids.direction",
        "bill_ids.l10n_vn_einvoice_ids.correction_state",
        "bill_ids.l10n_vn_einvoice_ids.currency_id",
        "bill_ids.l10n_vn_einvoice_ids.amount_untaxed",
        "bill_ids.l10n_vn_einvoice_ids.amount_tax",
        "bill_ids.l10n_vn_einvoice_ids.amount_total",
    )
    def _compute_state(self):
        """Spec D12. A stored compute runs as superuser (odoo/odoo/fields.py:443)."""
        for batch in self:
            if batch.cancelled:
                batch.state = "cancel"
            elif not batch.date_request:
                batch.state = "draft"
            elif batch._material_covered():
                batch.state = "covered"
            else:
                batch.state = "requested"

    def _material_covered(self):
        self.ensure_one()
        if not any(
            float_compare(line.request_qty, 0.0, precision_rounding=line.product_id.uom_id.rounding)
            > 0
            for line in self.request_line_ids
        ):
            return True
        bills = self._material_bills()
        return bool(bills) and all(bill._material_einvoice_ok() for bill in bills)

    def _material_bills(self):
        """The batch's vendor bills that are not cancelled."""
        return self.bill_ids.filtered(
            lambda m: m.move_type == "in_invoice" and m.state != "cancel"
        )

    @api.depends("bill_ids")
    def _compute_bill_count(self):
        for batch in self:
            batch.bill_count = len(batch.bill_ids)

    @api.depends("request_line_ids.amount")
    def _compute_amount_total(self):
        for batch in self:
            batch.amount_total = sum(batch.request_line_ids.mapped("amount"))

    @api.depends("state", "need_line_ids")
    def _compute_warning(self):
        for batch in self:
            if batch.state != "draft" or not batch.need_line_ids:
                batch.warning = False
                continue
            messages = []
            unexploded = batch.need_line_ids.filtered(lambda n: not n.exploded).product_id
            if unexploded:
                messages.append(
                    self.env._(
                        "Not exploded (no BoM): %(products)s",
                        products=self._material_list(unexploded.mapped("display_name")),
                    )
                )
            materials = batch.need_line_ids.filtered("exploded").product_id
            if materials:
                quantities = self._ownership_quantities(batch.company_id, materials)
                for key, label in (
                    ("awaiting", self.env._("Bills awaiting their e-invoice: %(materials)s")),
                    ("not_received", self.env._("Billed, not received: %(materials)s")),
                ):
                    found = [
                        f"{product.display_name} ({quantities[product.id][key]:g} "
                        f"{product.uom_id.name})"
                        for product in materials
                        if float_compare(
                            quantities[product.id][key],
                            0.0,
                            precision_rounding=product.uom_id.rounding,
                        )
                        > 0
                    ]
                    if found:
                        messages.append(label % {"materials": self._material_list(found)})
                priced = materials.with_company(batch.company_id)
                zero_cost = priced.filtered(lambda p: not p.standard_price)
                if zero_cost:
                    messages.append(
                        self.env._(
                            "Zero unit cost, would be requested at 0: %(materials)s",
                            materials=self._material_list(zero_cost.mapped("display_name")),
                        )
                    )
                periodic = priced.filtered(lambda p: p.valuation != "real_time")
                if periodic:
                    messages.append(
                        self.env._(
                            "Not valued in real time, the bill line would not post to the "
                            "clearing account: %(materials)s",
                            materials=self._material_list(periodic.mapped("display_name")),
                        )
                    )
            batch.warning = "\n".join(messages) or False

    @api.model
    def _material_list(self, items):
        """Up to WARNING_LIST_MAX items, then a count of the rest."""
        items = list(items)
        text = ", ".join(items[:WARNING_LIST_MAX])
        if len(items) > WARNING_LIST_MAX:
            text += self.env._(
                " and %(count)s more (see Sales → Reporting → Material Ownership)",
                count=len(items) - WARNING_LIST_MAX,
            )
        return text

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                company = (
                    self.env["res.company"].browse(vals["company_id"])
                    if vals.get("company_id")
                    else self.env.company
                )
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(company)
                    .next_by_code("sale.material.batch")
                    or "New"
                )
        batches = super().create(vals_list)
        for batch in batches:
            if batch.order_ids:
                batch._explode_orders(batch.order_ids)
        return batches

    def write(self, vals):
        if "order_ids" not in vals:
            return super().write(vals)
        for batch in self:
            if batch.state != "draft":
                raise UserError(
                    self.env._(
                        "%(batch)s is no longer a draft: its orders cannot change.",
                        batch=batch.name,
                    )
                )
        before = {batch.id: batch.order_ids for batch in self}
        res = super().write(vals)
        for batch in self:
            removed = before[batch.id] - batch.order_ids
            added = batch.order_ids - before[batch.id]
            if removed:
                batch.need_line_ids.filtered(lambda n: n.order_id in removed).unlink()
            if added:
                batch._explode_orders(added)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_requested(self):
        if any(batch.state not in ("draft", "cancel") for batch in self):
            raise UserError(
                self.env._("Only draft or cancelled transfer batches can be deleted.")
            )

    def _explode_orders(self, orders):
        """Write the need lines of the orders' lines not yet in a batch (spec D2-D4)."""
        self.ensure_one()
        start = self._material_start()
        vals_list = []
        for order in orders:
            if order.company_id != self.company_id or order.state != "sale":
                raise UserError(
                    self.env._(
                        "%(order)s is not a confirmed order of %(company)s.",
                        order=order.name,
                        company=self.company_id.name,
                    )
                )
            if not order._material_in_scope():
                raise UserError(
                    self.env._(
                        "%(order)s was confirmed before the ownership start (%(date)s): "
                        "its goods need no transfer.",
                        order=order.name,
                        date=fields.Date.to_string(start),
                    )
                )
            all_lines = order.order_line._material_lines()
            lines = all_lines.filtered(lambda line: not line._material_batch_needs())
            if not lines:
                if not all_lines:
                    raise UserError(
                        self.env._("%(order)s has no goods to transfer.", order=order.name)
                    )
                raise UserError(
                    self.env._(
                        "%(order)s has nothing left to transfer: its lines are already "
                        "in %(batches)s.",
                        order=order.name,
                        batches=", ".join(
                            all_lines._material_batch_needs().batch_id.mapped("name")
                        ),
                    )
                )
            for line in lines:
                qty = line.product_uom._compute_quantity(
                    line.product_uom_qty, line.product_id.uom_id, round=False
                )
                materials, unexploded, bom = self._explode(line.product_id, qty)
                for products, exploded in ((materials, True), (unexploded, False)):
                    for product, material_qty in products.items():
                        vals_list.append(
                            {
                                "batch_id": self.id,
                                "order_line_id": line.id,
                                "bom_id": bom.id,
                                "line_qty": qty,
                                "product_id": product.id,
                                "material_qty": material_qty,
                                "exploded": exploded,
                            }
                        )
        return self.env["sale.material.batch.need"].create(vals_list)

    def _explode(self, product, qty):
        """The materials in qty (product's UoM) of product, by BoM norms (spec D3).

        Returns (materials, unexploded, top_bom): two dicts of product -> quantity in
        that product's UoM, and the BoM the product itself was exploded with.
        """
        self.ensure_one()
        materials = defaultdict(float)
        unexploded = defaultdict(float)
        Bom = self.env["mrp.bom"].sudo()
        company = self.company_id

        def walk(prod, quantity, depth):
            if prod.categ_id.material_ownership:
                materials[prod] += quantity
                return Bom
            bom = Bom._bom_find(prod, company_id=company.id)[prod] if depth <= MAX_DEPTH else Bom
            if not bom:
                unexploded[prod] += quantity
                return Bom
            factor = prod.uom_id._compute_quantity(
                quantity, bom.product_uom_id, round=False
            ) / (bom.product_qty or 1.0)
            _boms, lines = bom.explode(prod, factor)
            for bom_line, data in lines:
                component = bom_line.product_id
                walk(
                    component,
                    bom_line.product_uom_id._compute_quantity(
                        data["qty"], component.uom_id, round=False
                    ),
                    depth + 1,
                )
            return bom

        top_bom = walk(product.sudo(), qty, 0)
        return dict(materials), dict(unexploded), top_bom

    def _material_start(self):
        """The company's ownership start; refuses to work on orders without one."""
        self.ensure_one()
        start = self.company_id.material_ownership_start
        if not start:
            raise UserError(
                self.env._(
                    "Set the ownership start date of %(company)s in Sales settings first "
                    "(block Material Ownership).",
                    company=self.company_id.name,
                )
            )
        return start

    def action_add_uncovered(self):
        self.ensure_one()
        self._material_start()
        orders = self.env["sale.order"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("state", "=", "sale"),
                ("material_coverage", "in", ["not_batched", "partly"]),
            ],
            order="date_order, id",
        )
        if orders:
            self.write({"order_ids": [fields.Command.link(order.id) for order in orders]})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "info",
                "sticky": False,
                "message": (
                    self.env._("%(count)s orders added.", count=len(orders))
                    if orders
                    else self.env._("No order to add.")
                ),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def action_refresh(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(
                self.env._(
                    "%(batch)s is no longer a draft: its orders cannot change.",
                    batch=self.name,
                )
            )
        self.need_line_ids.unlink()
        if self.order_ids:
            self._explode_orders(self.order_ids)
        return True

    def action_request(self):
        """Net the batch's materials against the owned balance and prepare the material
        owner's draft bill for the rest (spec D9-D11)."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(self.env._("Only a draft batch can be requested."))
        needs = self.need_line_ids.filtered("exploded")
        if not needs:
            raise UserError(
                self.env._("%(batch)s has no material to request.", batch=self.name)
            )
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(
                self.env._(
                    "Requesting a transfer batch creates a vendor bill: it needs the "
                    "Accounting / Invoicing group."
                )
            )
        company = self.company_id
        if not company.material_owner_partner_id or not company.material_fiscal_position_id:
            raise UserError(
                self.env._(
                    "Set the material owner and the material transfer fiscal position in "
                    "Sales settings first."
                )
            )
        # One request at a time per company (spec D10).
        self.env.cr.execute(
            "SELECT id FROM sale_material_batch WHERE company_id = %s FOR UPDATE",
            [company.id],
        )
        need_by_product = defaultdict(float)
        for need in needs:
            need_by_product[need.product_id] += need.material_qty
        materials = needs.product_id
        quantities = self._ownership_quantities(company, materials, exclude_batch=self)
        vals_list = []
        for product in materials.sorted(lambda p: (p.default_code or "", p.name or "")):
            figures = quantities[product.id]
            rounding = product.uom_id.rounding
            need = need_by_product[product]
            available = figures["in"] - figures["used"] + figures["pending"]
            request = float_round(
                max(0.0, need - available), precision_rounding=rounding, rounding_method="UP"
            )
            if float_is_zero(request, precision_rounding=rounding):
                request = 0.0
            unit_cost = product.with_company(company).standard_price
            vals_list.append(
                {
                    "batch_id": self.id,
                    "product_id": product.id,
                    "need_qty": need,
                    "available_qty": available,
                    "shortfall_qty": max(0.0, -available),
                    "request_qty": request,
                    "unit_cost": unit_cost,
                    "amount": company.currency_id.round(request * unit_cost),
                }
            )
        self.env["sale.material.batch.request"].create(vals_list)
        self.write({"date_request": fields.Datetime.now(), "requested_by_id": self.env.uid})
        to_bill = self.request_line_ids.filtered(lambda line: line.request_qty > 0)
        if to_bill:
            self._create_bill(to_bill)
        return True

    def _create_bill(self, request_lines):
        """The material owner's draft bill (spec D11). Its lines take the stock input
        account mapped by the fiscal position, and it is never posted here."""
        self.ensure_one()
        company = self.company_id
        return (
            self.env["account.move"]
            .with_company(company)
            .with_context(default_move_type="in_invoice")
            .create(
                {
                    "move_type": "in_invoice",
                    "company_id": company.id,
                    "partner_id": company.material_owner_partner_id.id,
                    "fiscal_position_id": company.material_fiscal_position_id.id,
                    "invoice_origin": self.name,
                    "material_batch_id": self.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": line.product_id.id,
                                "product_uom_id": line.product_id.uom_id.id,
                                "quantity": line.request_qty,
                                "price_unit": line.unit_cost,
                            }
                        )
                        for line in request_lines
                    ],
                }
            )
        )

    def action_cancel(self):
        self.ensure_one()
        if self.state == "cancel":
            return True
        if self.state == "covered":
            raise UserError(
                self.env._(
                    "%(batch)s is covered and can no longer be cancelled.", batch=self.name
                )
            )
        if any(bill.state == "posted" for bill in self.bill_ids):
            raise UserError(
                self.env._(
                    "%(batch)s has a posted bill. Reset the bill to draft or reverse it first.",
                    batch=self.name,
                )
            )
        self.bill_ids.filtered(lambda m: m.state == "draft").button_cancel()
        self.cancelled = True
        return True

    def action_view_bills(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        if len(self.bill_ids) == 1:
            action.update(
                {"res_id": self.bill_ids.id, "view_mode": "form", "views": [(False, "form")]}
            )
        else:
            action["domain"] = [("id", "in", self.bill_ids.ids)]
        action["context"] = {"create": False}
        return action

    def _material_document_data(self):
        """Everything the Bảng kê prints (spec, step 3). The owned part of each material
        is allocated to the orders oldest first; each order prints what remains."""
        self.ensure_one()
        batch = self.with_context(lang="vi_VN")
        company = batch.company_id
        Precision = self.env["decimal.precision"]

        def partner_data(partner):
            address = partner._display_address(without_company=True) or ""
            return {
                "name": partner.name or "",
                "vat": partner.vat or "",
                "address": ", ".join(p.strip() for p in address.splitlines() if p.strip()),
            }

        def material_row(product, qty, line=None):
            row = {
                "code": product.default_code or "",
                "name": product.with_context(display_default_code=False).display_name,
                "uom": product.uom_id.name,
                "qty": qty,
            }
            if line:
                row.update(unit_cost=line.unit_cost, amount=line.amount)
            return row

        def material_key(product):
            return (product.default_code or "", product.name or "")

        requests = {line.product_id: line for line in batch.request_line_ids}
        pools = {product: max(line.available_qty, 0.0) for product, line in requests.items()}
        needs = batch.need_line_ids.filtered("exploded")
        orders = []
        for order in needs.order_id.sorted(lambda o: (o.date_order, o.id)):
            order_needs = needs.filtered(lambda n, order=order: n.order_id == order)
            materials = []
            for product in order_needs.product_id.sorted(material_key):
                need = sum(
                    order_needs.filtered(lambda n, product=product: n.product_id == product)
                    .mapped("material_qty")
                )
                owned = min(pools.get(product, 0.0), need)
                pools[product] = pools.get(product, 0.0) - owned
                requested = need - owned
                if float_compare(
                    requested, 0.0, precision_rounding=product.uom_id.rounding
                ) > 0:
                    materials.append(material_row(product, requested))
            if not materials:
                continue
            goods = []
            for line in order_needs.order_line_id:
                goods.append(
                    {
                        "name": line.product_id.with_context(
                            display_default_code=False
                        ).display_name,
                        "qty": order_needs.filtered(
                            lambda n, line=line: n.order_line_id == line
                        )[:1].line_qty,
                        "uom": line.product_id.uom_id.name,
                    }
                )
            orders.append(
                {
                    "name": order.name,
                    "date": fields.Datetime.context_timestamp(batch, order.date_order).date(),
                    "partner": order.partner_id.display_name,
                    "goods": goods,
                    "materials": materials,
                }
            )
        lines = batch.request_line_ids.sorted(lambda l: material_key(l.product_id))
        shortfall = [
            material_row(line.product_id, line.shortfall_qty)
            for line in lines
            if float_compare(
                line.shortfall_qty, 0.0, precision_rounding=line.product_id.uom_id.rounding
            )
            > 0
        ]
        totals = [
            material_row(line.product_id, line.request_qty, line)
            for line in lines
            if line.request_qty > 0
        ]
        return {
            "number": batch.name,
            "date": batch.date_request
            and fields.Datetime.context_timestamp(batch, batch.date_request).date(),
            "seller": partner_data(company.material_owner_partner_id),
            "buyer": partner_data(company.partner_id),
            "orders": orders,
            "shortfall": shortfall,
            "totals": totals,
            "total": sum(row["amount"] for row in totals),
            "currency": company.currency_id,
            "qty_digits": Precision.precision_get("Product Unit of Measure"),
            "price_digits": Precision.precision_get("Product Price"),
        }

    @api.model
    def _ownership_quantities(self, company, products=None, exclude_batch=None):
        """Owned, used and pending quantities per material, in its UoM (spec D6, D7).

        Returns {product id: {key: quantity}} for the keys of QUANTITY_KEYS, leaving out
        exclude_batch's own need and request lines.
        """
        result = defaultdict(lambda: dict.fromkeys(QUANTITY_KEYS, 0.0))
        domain = [
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "in", ("in_invoice", "in_refund")),
            ("display_type", "=", "product"),
            ("product_id.categ_id.material_ownership", "=", True),
        ]
        if products is not None:
            domain.append(("product_id", "in", products.ids))
        lines = self.env["account.move.line"].sudo().search(domain)
        counts = {}
        po_groups = defaultdict(lambda: {"counted": 0.0, "awaiting": 0.0})
        for line in lines:
            move = line.move_id
            if move.id not in counts:
                counts[move.id] = move._material_einvoice_ok()
            product = line.product_id
            qty = (line.product_uom_id or product.uom_id)._compute_quantity(
                line.quantity, product.uom_id, round=False
            )
            refund = move.move_type == "in_refund"
            figures = result[product.id]
            if line.purchase_line_id:
                group = po_groups[line.purchase_line_id]
                if refund:
                    group["counted"] -= qty
                elif counts[move.id]:
                    group["counted"] += qty
                else:
                    group["awaiting"] += qty
            elif refund:
                figures["in"] -= qty
            elif not counts[move.id]:
                figures["awaiting"] += qty
            elif move.material_batch_id:
                figures["in"] += qty
            else:
                figures["no_receipt"] += qty
        for po_line, group in po_groups.items():
            product = po_line.product_id
            figures = result[product.id]
            received = po_line.product_uom._compute_quantity(
                po_line.qty_received, product.uom_id, round=False
            )
            figures["in"] += min(group["counted"], received)
            figures["not_received"] += max(group["counted"] - received, 0.0)
            figures["awaiting"] += group["awaiting"]

        batch_domain = [("batch_id.company_id", "=", company.id)]
        if products is not None:
            batch_domain.append(("product_id", "in", products.ids))
        if exclude_batch:
            batch_domain.append(("batch_id", "!=", exclude_batch.id))
        needs = self.env["sale.material.batch.need"].sudo().search(
            [
                *batch_domain,
                ("exploded", "=", True),
                ("batch_id.state", "in", ("requested", "covered")),
            ]
        )
        for need in needs:
            effective = need.order_line_id._material_effective_qty(need.line_qty)
            result[need.product_id.id]["used"] += (
                need.material_qty / need.line_qty * effective
            )
        requests = self.env["sale.material.batch.request"].sudo().search(
            [*batch_domain, ("batch_id.state", "=", "requested")]
        )
        for line in requests:
            result[line.product_id.id]["pending"] += line.request_qty
        return result


class SaleMaterialBatchNeed(models.Model):
    _name = "sale.material.batch.need"
    _description = "Material Transfer Batch Need"
    _order = "batch_id, order_id, order_line_id, product_id"

    batch_id = fields.Many2one(
        comodel_name="sale.material.batch", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="batch_id.company_id", store=True)
    order_line_id = fields.Many2one(
        comodel_name="sale.order.line", required=True, ondelete="cascade", index=True
    )
    order_id = fields.Many2one(related="order_line_id.order_id", store=True, index=True)
    sold_product_id = fields.Many2one(
        related="order_line_id.product_id", string="Sold Product"
    )
    bom_id = fields.Many2one(comodel_name="mrp.bom", string="BoM", ondelete="set null")
    line_qty = fields.Float(
        string="Sold Quantity", digits="Product Unit of Measure", required=True
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Material", required=True, ondelete="restrict"
    )
    uom_id = fields.Many2one(related="product_id.uom_id")
    material_qty = fields.Float(
        string="Quantity", digits="Product Unit of Measure", required=True
    )
    exploded = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "line_material_unique",
            "UNIQUE (batch_id, order_line_id, product_id)",
            "A material appears once per order line in a batch.",
        ),
        ("line_qty_positive", "CHECK (line_qty > 0)", "The sold quantity must be positive."),
    ]


class SaleMaterialBatchRequest(models.Model):
    _name = "sale.material.batch.request"
    _description = "Material Transfer Batch Request"
    _order = "batch_id, id"

    batch_id = fields.Many2one(
        comodel_name="sale.material.batch", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="batch_id.company_id", store=True)
    currency_id = fields.Many2one(related="batch_id.currency_id")
    product_id = fields.Many2one(
        comodel_name="product.product", string="Material", required=True, ondelete="restrict"
    )
    uom_id = fields.Many2one(related="product_id.uom_id")
    need_qty = fields.Float(string="Needed", digits="Product Unit of Measure", readonly=True)
    available_qty = fields.Float(
        string="Available", digits="Product Unit of Measure", readonly=True
    )
    shortfall_qty = fields.Float(
        string="Earlier Shortfall", digits="Product Unit of Measure", readonly=True
    )
    request_qty = fields.Float(
        string="Requested", digits="Product Unit of Measure", readonly=True
    )
    unit_cost = fields.Float(digits="Product Price", readonly=True)
    amount = fields.Monetary(readonly=True)
    billed_qty = fields.Float(
        string="Billed", digits="Product Unit of Measure", compute="_compute_billed_qty"
    )
    difference_qty = fields.Float(
        string="Difference", digits="Product Unit of Measure", compute="_compute_billed_qty"
    )

    _sql_constraints = [
        (
            "batch_product_unique",
            "UNIQUE (batch_id, product_id)",
            "A material is requested once per batch.",
        ),
    ]

    @api.depends(
        "request_qty",
        "batch_id.bill_ids.state",
        "batch_id.bill_ids.invoice_line_ids.quantity",
        "batch_id.bill_ids.l10n_vn_einvoice_ids",
    )
    def _compute_billed_qty(self):
        """The material on the batch's counting bills, minus its posted refunds."""
        for line in self:
            billed = 0.0
            for bill in line.batch_id.sudo().bill_ids:
                if bill.move_type == "in_invoice":
                    if not bill._material_einvoice_ok():
                        continue
                    sign = 1
                elif bill.move_type == "in_refund" and bill.state == "posted":
                    sign = -1
                else:
                    continue
                material = line.product_id
                for move_line in bill.invoice_line_ids:
                    if move_line.product_id != material:
                        continue
                    uom = move_line.product_uom_id or material.uom_id
                    billed += sign * uom._compute_quantity(
                        move_line.quantity, material.uom_id, round=False
                    )
            line.billed_qty = billed
            line.difference_qty = billed - line.request_qty
