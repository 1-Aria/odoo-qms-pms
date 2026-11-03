# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The pay context: every figure of a Vietnamese payslip, computed from configuration.

Rules only read it (design §12). Amounts are computed in ``Decimal`` from the stored
values and rounded once per line, to whole dong, half up (FR-34).
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal

from odoo import fields
from odoo.exceptions import UserError

HOURS_PER_DAY = 8
ONE = Decimal(1)


def _dec(value):
    return Decimal(str(value or 0))


def _round(value):
    return int(value.quantize(ONE, rounding=ROUND_HALF_UP))


def _iso(date):
    return date.isoformat() if date else None


def _jsonable(value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


class PayContext:
    """Builds the contexts of a batch of payslips, sharing parameter reads.

    ``env`` is a superuser environment, so record rules do not apply: every
    component search names the payslip's company.
    """

    def __init__(self, env):
        self.env = env
        self.params = {}
        self._used = {}

    def param(self, code, date, company):
        key = (code, date, company.id)
        if key not in self.params:
            self.params[key] = self.env["base.time.parameter"]._strict_get(
                code, date, company=company
            )
        self._used[(code, date)] = self.params[key]
        return self.params[key]

    # ------------------------------------------------------------------ build
    def build(self, payslip, contract, inp):
        self._used = {}
        company = payslip.company_id
        month_end = payslip.date_to
        employee = inp.employee_id
        names = {"employee": employee.name, "month": f"{payslip.date_from:%m/%Y}"}

        pieces = self._pieces(inp, names)
        multi = len(pieces) > 1
        std = _dec(self.param("vn.policy.std_days", month_end, company))
        pay_lines = []
        for index, piece in enumerate(pieces):
            in_force = piece["contract"].l10n_vn_line_ids._l10n_vn_in_force(piece["date_to"])
            piece["pay_lines"] = [
                (line, _dec(line._l10n_vn_amount_on(piece["date_to"])))
                for line in in_force
                if line.component_id.active
            ]
            pay_lines += [
                {
                    "id": line.id,
                    "piece": index,
                    "component": line.component_id.code,
                    "scale_key": line.scale_key or None,
                    "amount": float(amount),
                }
                for line, amount in piece["pay_lines"]
            ]

        attainment = self._attainment(pieces, inp, company, month_end, names)
        lines = self._pay_line_lines(pieces, multi, std, attainment, inp, company, month_end)
        lines += self._ot_lines(pieces, multi, std, attainment, inp, company, names)
        lines += self._ie_lines(inp, company, month_end)
        # adjustments come after the month's own line of the same component
        unapproved = []
        lines += self._entered_lines(inp, unapproved)
        gross = sum(line["amount"] for line in lines if line["kind"] == "earning")
        for component in self._components(company, [("engine_code", "=", "GROSS")]):
            lines.append(self._line(component, Decimal(gross)))

        return {
            "version": 1,
            "employee_id": employee.id,
            "contract_id": contract.id,
            "input_id": inp.id,
            "date_from": _iso(payslip.date_from),
            "date_to": _iso(payslip.date_to),
            "parameters": [
                {"code": code, "date": _iso(date), "value": _jsonable(value)}
                for (code, date), value in self._used.items()
            ],
            "input": {
                "paid_days": inp.paid_days,
                "days_worked": inp.days_worked,
                "unpaid_days": inp.unpaid_days,
                "scheduled_days": inp.scheduled_days,
                "si_absence_days": inp.si_absence_days,
                "unexcused_absences": inp.unexcused_absences,
                "late_arrivals": inp.late_arrivals,
                "ot_hours_json": inp.ot_hours_json or {},
                "ot_hours_ytd": inp.ot_hours_ytd,
                "attainment": inp.attainment,
                "attainment_source": inp.attainment_source or None,
                "ie_units": inp.ie_units,
                "figures_locked": inp.figures_locked,
                "built_at": fields.Datetime.to_string(inp.built_at) if inp.built_at else None,
            },
            "std_days": float(std),
            "attainment": float(attainment) if attainment is not None else None,
            "pieces": [
                {
                    "date_from": _iso(piece["date_from"]),
                    "date_to": _iso(piece["date_to"]),
                    "contract_id": piece["contract"].id,
                    "probation": piece["probation"],
                    "paid_days": float(piece["paid_days"]),
                    "days_worked": float(piece["days_worked"]),
                    "ot_hours_json": piece["ot_hours_json"],
                    "ot_base": float(piece["ot_base"]),
                    "hourly": round(float(piece["hourly"]), 4),
                }
                for piece in pieces
            ],
            "pay_lines": pay_lines,
            "lines": lines,
            "unapproved": unapproved,
            "gross": gross,
        }

    # ------------------------------------------------------------------ steps
    def _pieces(self, inp, names):
        """The month's pieces with their figures (D33, D34)."""
        pieces = inp._l10n_vn_pieces()
        if len(pieces) == 1:
            pieces[0].update(
                paid_days=_dec(inp.paid_days),
                days_worked=_dec(inp.days_worked),
                ot_hours_json=inp.ot_hours_json or {},
            )
            return pieces
        segments = {(s.date_from, s.date_to): s for s in inp.segment_ids}
        wanted = [(p["date_from"], p["date_to"]) for p in pieces]
        if sorted(segments) != wanted:
            raise UserError(
                self.env._(
                    "The monthly input of %(employee)s for %(month)s needs segments for "
                    "%(pieces)s; rebuild it.",
                    pieces=", ".join(f"{start}–{end}" for start, end in wanted),
                    **names,
                )
            )
        for piece in pieces:
            segment = segments[(piece["date_from"], piece["date_to"])]
            piece.update(
                paid_days=_dec(segment.paid_days),
                days_worked=_dec(segment.days_worked),
                ot_hours_json=segment.ot_hours_json or {},
            )
        if inp.ot_hours_json and not any(piece["ot_hours_json"] for piece in pieces):
            # segments without OT hours: the month's hours go to the last piece (PTD-OPEN-04)
            pieces[-1]["ot_hours_json"] = inp.ot_hours_json
        return pieces

    def _attainment(self, pieces, inp, company, month_end, names):
        """The attainment applied to variable components, or None (D37)."""
        variable = any(
            line.component_id.variable for piece in pieces for line, _amount in piece["pay_lines"]
        )
        if not variable:
            return None
        if not inp.attainment_source:
            raise UserError(
                self.env._("%(employee)s has no attainment or score for %(month)s.", **names)
            )
        cap = _dec(self.param("vn.policy.attainment_cap", month_end, company))
        return min(_dec(inp.attainment), cap)

    def _rate(self, piece, component, company):
        if piece["probation"] and component.probation_applies:
            return _dec(self.param("vn.policy.probation_rate", piece["date_to"], company))
        return ONE

    def _factor(self, component, attainment):
        return attainment if component.variable else ONE

    def _pay_line_lines(self, pieces, multi, std, attainment, inp, company, month_end):
        """Pay line components (D36, D38)."""
        lines, month_level = [], {}
        for index, piece in enumerate(pieces):
            for pay_line, amount in piece["pay_lines"]:
                component = pay_line.component_id
                r = self._rate(piece, component, company)
                a = self._factor(component, attainment)
                if component.proration == "none":
                    # paid once a month, from the last piece holding the component
                    month_level[component.id] = (pay_line, amount * r * a, a)
                    continue
                if component.proration == "per_day":
                    days = piece["paid_days"]
                    value = amount * days * r * a
                else:
                    days = piece[
                        "paid_days" if component.proration == "paid_days" else "days_worked"
                    ]
                    value = amount * days / std * r * a
                value = self._condition(component, value, inp, company, month_end)
                lines.append(
                    self._line(
                        component,
                        value,
                        name=self._piece_name(component.name, piece, multi),
                        days=float(days),
                        piece=index,
                        date_from=_iso(piece["date_from"]) if multi else None,
                        date_to=_iso(piece["date_to"]) if multi else None,
                        attainment=float(a) if component.variable else None,
                        pay_line_id=pay_line.id,
                    )
                )
        for pay_line, value, a in month_level.values():
            component = pay_line.component_id
            value = self._condition(component, value, inp, company, month_end)
            lines.append(
                self._line(
                    component,
                    value,
                    attainment=float(a) if component.variable else None,
                    pay_line_id=pay_line.id,
                )
            )
        return lines

    def _condition(self, component, value, inp, company, month_end):
        """The attendance condition: the line is paid as computed or zeroed (D38)."""
        if component.condition != "attendance":
            return value
        limit = self.param("vn.policy.attendance_late_max", month_end, company)
        if inp.unexcused_absences or inp.late_arrivals > limit:
            return Decimal(0)
        return value

    def _entered_lines(self, inp, unapproved):
        """Approved entered amounts and adjustments (D39)."""
        lines = []
        for item in inp.line_ids:
            if not item.approved_by:
                unapproved.append(item.id)
                continue
            name = item.description or item.component_id.name
            if item.period_ref:
                name = f"{name} ({item.period_ref:%m/%Y})"
            lines.append(
                self._line(
                    item.component_id,
                    _dec(item.amount),
                    name=name,
                    hours=item.hours or None,
                    period_ref=_iso(item.period_ref),
                    input_line_id=item.id,
                )
            )
        return lines

    def _ie_lines(self, inp, company, month_end):
        """IE units × the unit rate (D39)."""
        if not inp.ie_units:
            return []
        components = self._components(company, [("amount_source", "=", "ie_units")])
        if not components:
            return []
        rate = _dec(self.param("vn.policy.unit_rate", month_end, company))
        return [self._line(c, _dec(inp.ie_units) * rate) for c in components]

    def _ot_lines(self, pieces, multi, std, attainment, inp, company, names):
        """OT on the OT base of each piece (D40)."""
        components = self._components(company, [("amount_source", "=", "ot")])
        per_category = components.filtered(lambda c: c.ot_category != "all")
        supplements = components - per_category
        paid = set(per_category.mapped("ot_category"))
        for piece in pieces:
            base = Decimal(0)
            for pay_line, amount in piece["pay_lines"]:
                component = pay_line.component_id
                if not component.in_ot_base:
                    continue
                if component.proration == "per_day":
                    amount = amount * std
                base += amount * self._rate(piece, component, company) * self._factor(
                    component, attainment
                )
            piece["ot_base"] = base
            piece["hourly"] = base / (std * HOURS_PER_DAY)
            for category, hours in piece["ot_hours_json"].items():
                if hours and category not in paid:
                    raise UserError(
                        self.env._(
                            "%(employee)s has %(category)s overtime and no active component "
                            "pays it.",
                            category=category,
                            **names,
                        )
                    )
        lines = []
        for index, piece in enumerate(pieces):
            hours_by = {c: _dec(h) for c, h in piece["ot_hours_json"].items() if h}
            if not hours_by:
                continue
            factors = self.param("vn.ot.factors", piece["date_to"], company)

            def factor(category):
                if category not in factors:
                    raise UserError(
                        self.env._(
                            "vn.ot.factors has no factor for %(category)s.", category=category
                        )
                    )
                return _dec(factors[category])

            name_of = lambda component: self._piece_name(component.name, piece, multi)  # noqa: E731
            dates = {
                "date_from": _iso(piece["date_from"]) if multi else None,
                "date_to": _iso(piece["date_to"]) if multi else None,
            }
            for component in per_category:
                hours = hours_by.get(component.ot_category)
                if not hours:
                    continue
                f = factor(component.ot_category)
                lines.append(
                    self._line(
                        component,
                        piece["hourly"] * f * hours,
                        name=name_of(component),
                        hours=float(hours),
                        factor=float(f),
                        unit_amount=round(float(piece["hourly"]), 4),
                        piece=index,
                        **dates,
                    )
                )
            for component in supplements:
                supplement = _dec(
                    self.param(component.amount_parameter, piece["date_to"], company)
                )
                weighted = sum((factor(c) * h for c, h in hours_by.items()), Decimal(0))
                lines.append(
                    self._line(
                        component,
                        supplement * weighted,
                        name=name_of(component),
                        hours=float(sum(hours_by.values())),
                        unit_amount=float(supplement),
                        piece=index,
                        **dates,
                    )
                )
        return lines

    # ------------------------------------------------------------------ helpers
    def _components(self, company, domain):
        return self.env["l10n_vn.payroll.component"].search(
            [("company_id", "=", company.id), ("active", "=", True)] + domain
        )

    def _piece_name(self, name, piece, multi):
        """Line names (D45)."""
        parts = []
        if multi:
            parts.append(f"{piece['date_from']:%d/%m}–{piece['date_to']:%d/%m}")
        if piece["probation"]:
            parts.append(self.env._("probation"))
        return f"{name} ({', '.join(parts)})" if parts else name

    def _line(self, component, amount, name=None, **values):
        line = {
            "component_id": component.id,
            "code": component.code,
            "kind": component.kind,
            "name": name or component.name,
            "amount": _round(amount),
            "days": None,
            "hours": None,
            "factor": None,
            "unit_amount": None,
            "date_from": None,
            "date_to": None,
            "attainment": None,
            "period_ref": None,
            "pay_line_id": None,
            "input_line_id": None,
            "piece": None,
        }
        line.update(values)
        return line
