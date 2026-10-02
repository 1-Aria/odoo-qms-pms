# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare

from .maintenance_sla import _request_selection

STATES = [
    ("running", "Running"),
    ("paused", "Paused"),
    ("achieved", "Achieved"),
    ("achieved_late", "Achieved late"),
    ("cancelled", "Cancelled"),
]
OPEN_STATES = ("running", "paused")
FINISHED_STATES = ("achieved", "achieved_late")

LIVE_STATES = [
    ("on_track", "On track"),
    ("at_risk", "At risk"),
    ("overdue", "Overdue"),
    ("paused", "Paused"),
]
# Worst first: the request shows the first of these any of its records holds.
# Paused is last, so it shows only when nothing runs.
LIVE_SEVERITY = ("overdue", "at_risk", "on_track", "paused")
SEARCH_OPERATORS = ("=", "in", "!=", "not in")


def _live_state_domain(state, now):
    """The records in this live state at now, as a domain on stored fields.

    The three running domains are disjoint however at_risk_pct is set: on
    track also requires the deadline ahead, so a share above 100 (risk_at after
    the deadline) reads as overdue once the deadline passes, never as both.
    """
    if not state:
        return [("state", "not in", list(OPEN_STATES))]
    if state == "paused":
        return [("state", "=", "paused")]
    running = [("state", "=", "running")]
    if state == "overdue":
        return running + [("deadline", "<=", now)]
    if state == "at_risk":
        return running + [("risk_at", "<=", now), ("deadline", ">", now)]
    return running + [("risk_at", ">", now), ("deadline", ">", now)]


def _search_values(env, operator, value):
    """The values a live-state search asks for, or UserError.

    = and in, and their negations: the custom filter editor offers "is not in"
    on a selection, so the negations are reachable from the UI.
    """
    if operator not in SEARCH_OPERATORS:
        raise UserError(
            env._("Operator %(operator)s is not supported here.", operator=operator)
        )
    return list(value) if operator in ("in", "not in") else [value]


def _search_result(model, operator, positive):
    """The positive domain, or its complement for the negated operators.

    Negating through the ids keeps the result right when False is among the
    values, where flipping each leaf would not.
    """
    if operator in ("=", "in"):
        return positive
    return [("id", "not in", model._search(positive))]


def _format_hours(hours):
    """Hours as H:MM, rounded to the minute."""
    minutes = round(hours * 60)
    return f"{minutes // 60}:{minutes % 60:02d}"


class MaintenanceRequestSla(models.Model):
    """One commitment on one request, for one cycle.

    Every field is plain and written imperatively by the engine, never a
    compute: in helpdesk.ticket.sla the state and deadline are stored computes
    that a recompute re-derives from scratch, discarding accumulated history.
    The exceptions are company_id, which must not drift from its request, and
    display_name.

    Readable by every internal user within their companies, with no delegation
    to the request. Record access is enforced in _search, which search(),
    read_group() and the reading of stored fields all go through, so a
    _check_access override would restrict almost nothing; and what a
    restriction would hide is a rule name and some times.
    """

    _name = "maintenance.request.sla"
    _description = "Maintenance Request SLA"
    _order = "id"

    request_id = fields.Many2one(
        comodel_name="maintenance.request",
        string="Request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sla_id = fields.Many2one(
        comodel_name="maintenance.sla",
        string="SLA Rule",
        required=True,
        ondelete="restrict",
    )

    # Snapshots of the rule, taken when the record is created: later edits to
    # the rule do not reach them. restrict on the target means a stage that was
    # ever a target cannot be deleted, and stages have no active field to retire
    # them with; renaming or resequencing stays possible. The rule's pause
    # stages are deliberately not snapshotted: they are read live.
    target_stage_id = fields.Many2one(
        comodel_name="maintenance.stage",
        string="Target Stage",
        required=True,
        ondelete="restrict",
    )
    # Evidence of what "reached" meant when the record was made. Evaluation
    # always compares against the live stage order, never against this.
    target_sequence = fields.Integer(string="Target Position")
    duration = fields.Float(string="Target (hours)")
    at_risk_pct = fields.Integer(string="At Risk (%)")

    # The clock.
    start_at = fields.Datetime(string="Clock Start", required=True)
    state = fields.Selection(
        selection=STATES, required=True, default="running", index=True
    )
    consumed = fields.Float(
        string="Counted (hours)",
        help="Running time accumulated up to the last change.",
    )
    paused_time = fields.Float(string="Paused (hours)")
    last_change_at = fields.Datetime(string="Last Change")
    deadline = fields.Datetime(help="Set while running, empty otherwise.")
    risk_at = fields.Datetime(
        string="At Risk From", help="Set while running, empty otherwise."
    )
    reached_at = fields.Datetime(string="Reached At")
    elapsed = fields.Float(string="Elapsed (hours)")
    # Written only when a record finishes, never before: a Float written False
    # stores 0.0 (Float.convert_to_column), and an average counts zeros, so a
    # running record would read as a breach. Left out, the column stays NULL,
    # which AVG skips.
    on_time = fields.Float(string="On Time (%)", aggregator="avg")
    cycle = fields.Integer(default=1)
    # The cancelled record this one took over from: a replacement when another
    # rule started to win, a resumption when a rule matched again. Without it a
    # record cancelled by re-matching would look like one cancelled with its
    # request.
    replaced_id = fields.Many2one(
        comodel_name="maintenance.request.sla",
        string="Replaces",
        ondelete="set null",
    )

    # The waiver: a manager's judgement on a finished outcome, set once through
    # the waiver wizard and never undone, since undoing it would be rewriting
    # evidence.
    waived = fields.Boolean(readonly=True, index=True)
    # restrict: a reason that has been used is evidence, so it is archived,
    # never deleted.
    waive_reason_id = fields.Many2one(
        comodel_name="maintenance.sla.waive.reason",
        string="Waiver Reason",
        readonly=True,
        ondelete="restrict",
    )
    waive_note = fields.Char(string="Waiver Note", readonly=True)
    waived_by_id = fields.Many2one(
        comodel_name="res.users", string="Waived By", readonly=True
    )
    waived_at = fields.Datetime(string="Waived At", readonly=True)

    # Grouping dimensions: plain fields, copied from the request. A related
    # stored field would rewrite finished evidence whenever the request changed.
    # The Many2ones keep the default ondelete="set null": refusing to delete a
    # team over historical evidence would turn a report column into a lock.
    team_id = fields.Many2one(comodel_name="maintenance.team", string="Team")
    equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment", string="Equipment"
    )
    category_id = fields.Many2one(
        comodel_name="maintenance.equipment.category", string="Equipment Category"
    )
    priority = fields.Selection(
        selection=lambda self: _request_selection(self, "priority"),
        string="Priority",
    )
    maintenance_type = fields.Selection(
        selection=lambda self: _request_selection(self, "maintenance_type"),
        string="Maintenance Type",
    )
    # Related rather than copied: maintenance.request is _check_company_auto, and
    # a company on the evidence that could drift from its request would be an
    # inconsistency nothing checks.
    company_id = fields.Many2one(
        related="request_id.company_id", store=True, string="Company"
    )
    # Computed on read, searched through stored fields: filters and colours
    # need no scheduled job.
    live_state = fields.Selection(
        selection=LIVE_STATES,
        string="Live State",
        compute="_compute_live_state",
        search="_search_live_state",
    )

    @api.depends("sla_id", "request_id")
    def _compute_display_name(self):
        # The request's name is read through sudo(): whoever reads the evidence
        # may not be able to read the request itself.
        for record in self:
            record.display_name = (
                f"{record.sla_id.name} · {record.request_id.sudo().display_name}"
            )

    @api.depends("state", "deadline", "risk_at")
    def _compute_live_state(self):
        """The same comparisons as _live_state_domain, in the same order."""
        now = fields.Datetime.now()
        for record in self:
            if record.state == "paused":
                record.live_state = "paused"
            elif record.state != "running":
                record.live_state = False
            elif record.deadline and record.deadline <= now:
                record.live_state = "overdue"
            elif record.risk_at and record.risk_at <= now:
                record.live_state = "at_risk"
            else:
                record.live_state = "on_track"

    def _search_live_state(self, operator, value):
        now = fields.Datetime.now()
        positive = expression.OR(
            [
                _live_state_domain(state, now)
                for state in _search_values(self.env, operator, value)
            ]
        )
        return _search_result(self, operator, positive)

    def _sla_dimensions(self):
        """The grouping dimensions as written, shaped like the request's."""
        self.ensure_one()
        return {
            "team_id": self.team_id.id,
            "equipment_id": self.equipment_id.id,
            "category_id": self.category_id.id,
            "priority": self.priority,
            "maintenance_type": self.maintenance_type,
        }

    def _set_deadline(self):
        """Deadline and at-risk time from the clock, or empty when not running.

        The base is max(last_change_at, start_at): time before the clock starts
        is never counted, so a clock starting in the future is at rest until
        then.
        """
        for record in self:
            if record.state != "running":
                record.write({"deadline": False, "risk_at": False})
                continue
            base = max(record.last_change_at or record.start_at, record.start_at)
            deadline = base + timedelta(hours=record.duration - record.consumed)
            margin = (1 - record.at_risk_pct / 100) * record.duration
            record.write(
                {
                    "deadline": deadline,
                    "risk_at": deadline - timedelta(hours=margin),
                }
            )

    def _sla_close(self, now):
        """Book the time since the last change, and make now the last change.

        Running time goes to consumed, paused time to paused_time. Both count
        from max(last_change_at, start_at) and are clamped at zero, so neither
        counts anything before the clock starts.
        """
        for record in self:
            base = max(record.last_change_at or record.start_at, record.start_at)
            hours = max(0.0, (now - base).total_seconds() / 3600)
            if record.state == "running":
                record.consumed += hours
            elif record.state == "paused":
                record.paused_time += hours
            record.last_change_at = now

    def _sla_cancel(self, now):
        """Cancel the open records among self; finished ones keep their state."""
        records = self.filtered(lambda record: record.state in OPEN_STATES)
        records._sla_close(now)
        records.write({"state": "cancelled"})
        records._set_deadline()
        return records

    def _sla_evaluate(self, now):
        """Bring each open record in line with its request's current stage.

        Positions are compared as (sequence, id) pairs read live, the order the
        board itself uses; target_sequence is evidence, never an input. A record
        is written only when its state changes: a move between two counting
        stages leaves it exactly as it was.

        Returns the records that finished or were cancelled.
        """
        changed = self.browse()
        for record in self.filtered(lambda record: record.state in OPEN_STATES):
            stage = record.request_id.stage_id
            target = record.target_stage_id
            if stage.sla_cancel:
                changed |= record._sla_cancel(now)
            elif (stage.sequence, stage.id) >= (target.sequence, target.id):
                record._sla_close(now)
                # consumed is a sum of second counts divided by 3600: a target
                # reached exactly at its deadline can come out a hair over.
                on_time = (
                    float_compare(
                        record.consumed, record.duration, precision_digits=6
                    )
                    <= 0
                )
                record.write(
                    {
                        "reached_at": now,
                        "elapsed": record.consumed,
                        "state": "achieved" if on_time else "achieved_late",
                        "on_time": 100.0 if on_time else 0.0,
                    }
                )
                record._set_deadline()
                changed |= record
            else:
                pausing = stage in record.sla_id.pause_stage_ids
                if pausing == (record.state == "paused"):
                    continue
                record._sla_close(now)
                record.state = "paused" if pausing else "running"
                record._set_deadline()
        return changed

    def action_waive(self):
        """Open the waiver wizard on this record.

        The wizard's access row, managers only, is what guards the waiver; the
        button's groups only hide it.
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "maintenance_sla.maintenance_request_sla_waive_action"
        )
        action["context"] = {"default_sla_record_id": self.id}
        return action

    def _sla_note_line(self):
        """The chatter line for this record's outcome, or None.

        Outcomes only: met on time or late, cancelled, a replacement or
        resumption, or a next cycle opened. A first record and a pause or resume
        post nothing; the stage tracking already records the move.
        """
        self.ensure_one()
        values = {
            "rule": self.sla_id.name,
            "old": self.replaced_id.sla_id.name,
            "elapsed": _format_hours(self.elapsed),
            "target": _format_hours(self.duration),
            "cycle": self.cycle,
        }
        if self.state == "achieved":
            return self.env._(
                "%(rule)s met on time: %(elapsed)s of %(target)s", **values
            )
        if self.state == "achieved_late":
            return self.env._("%(rule)s met late: %(elapsed)s of %(target)s", **values)
        if self.state == "cancelled":
            return self.env._("%(rule)s cancelled", **values)
        if self.replaced_id:
            if self.replaced_id.sla_id == self.sla_id:
                return self.env._("%(rule)s resumed", **values)
            return self.env._("%(old)s replaced by %(rule)s", **values)
        if self.cycle > 1:
            return self.env._("%(rule)s: cycle %(cycle)s started", **values)
        return None
