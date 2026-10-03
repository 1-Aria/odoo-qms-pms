# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from .maintenance_request_sla import (
    FINISHED_STATES,
    LIVE_SEVERITY,
    LIVE_STATES,
    OPEN_STATES,
    _search_result,
    _search_values,
)


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    # Not required: a NOT NULL column on maintenance.request would break the
    # at_install tests of every module loaded before this one. _sla_start()
    # falls back to create_date instead. Installing fills existing requests with
    # the install time (fields.py:1145-1148); they get no SLA records, so the
    # value is never read as a clock start.
    reported_at = fields.Datetime(
        string="Reported At",
        default=fields.Datetime.now,
        tracking=True,
        copy=False,
        help="When the problem was reported. Corrective SLA clocks start here.",
    )
    # copy=False: a copy would duplicate finished records, snapshots and waivers
    # onto the new request. Core's recurring path and the UI's Duplicate both
    # reach copy().
    sla_ids = fields.One2many(
        comodel_name="maintenance.request.sla",
        inverse_name="request_id",
        string="SLA Records",
        copy=False,
    )
    # Stored because the kanban orders by it. The order is the kanban's
    # default_order, not the model's _order: core sets "id desc", and changing
    # it would reorder every list and dropdown in the app.
    next_deadline = fields.Datetime(
        string="Next SLA Deadline",
        compute="_compute_next_deadline",
        store=True,
    )
    sla_live_state = fields.Selection(
        selection=LIVE_STATES,
        string="SLA State",
        compute="_compute_sla_live_state",
        search="_search_sla_live_state",
        help="The worst live state among this request's SLA records.",
    )
    reported_at_locked = fields.Boolean(
        compute="_compute_reported_at_locked",
        help="Reported At can no longer be corrected: an SLA record of this "
        "request has paused, finished or been cancelled.",
    )

    @api.depends("sla_ids.state", "sla_ids.start_at", "sla_ids.last_change_at")
    def _compute_reported_at_locked(self):
        """Locked once any record has changed state.

        A correction moves a record's start. Once a record has paused or
        resumed, its counters were booked against the old start; a record that
        has not changed state has booked nothing yet.
        """
        for request in self:
            request.reported_at_locked = any(
                record.state not in OPEN_STATES
                or record.last_change_at != record.start_at
                for record in request.sla_ids
            )

    @api.depends("sla_ids.state", "sla_ids.deadline")
    def _compute_next_deadline(self):
        for request in self:
            request.next_deadline = min(
                (
                    record.deadline
                    for record in request.sla_ids
                    if record.state == "running" and record.deadline
                ),
                default=False,
            )

    @api.depends("sla_ids.state", "sla_ids.deadline", "sla_ids.risk_at")
    def _compute_sla_live_state(self):
        for request in self:
            states = set(request.sla_ids.mapped("live_state"))
            request.sla_live_state = next(
                (state for state in LIVE_SEVERITY if state in states), False
            )

    def _search_sla_live_state(self, operator, value):
        """Search by the worst state, as the badge shows it.

        at_risk means at least one record at risk and none overdue, paused at
        least one paused and none running: a request answers exactly one of
        the filters, the one its badge shows.
        """

        def having(*states):
            return [("sla_ids", "any", [("live_state", "in", list(states))])]

        def without(*states):
            return [("sla_ids", "not any", [("live_state", "in", list(states))])]

        by_state = {
            "overdue": having("overdue"),
            "at_risk": having("at_risk") + without("overdue"),
            "on_track": having("on_track") + without("overdue", "at_risk"),
            "paused": having("paused")
            + [("sla_ids", "not any", [("state", "=", "running")])],
            False: [("sla_ids", "not any", [("state", "in", list(OPEN_STATES))])],
        }
        positive = expression.OR(
            [
                by_state.get(state, expression.FALSE_DOMAIN)
                for state in _search_values(self.env, operator, value)
            ]
        )
        return _search_result(self, operator, positive)

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        requests._sla_post(requests._sla_apply())
        return requests

    def write(self, vals):
        """Drive the clocks from the stage, re-match on changed inputs.

        Every input is compared before and after rather than read from vals:
        category_id is a stored related on equipment_id, and
        maintenance_priority_matrix writes priority from inside its own write()
        and create(). Its nested write re-enters this one, which is what makes
        load order irrelevant: whichever runs first, the second _sla_apply()
        finds the winner already holding each stage. A write setting the stage a
        request already has does nothing; core's own nested writes after a
        stage change carry no stage_id and pass through.
        """
        self._sla_check_reopen(vals)
        inputs_before = {request.id: request._sla_inputs() for request in self}
        stages_before = (
            {request.id: request.stage_id for request in self}
            if "stage_id" in vals
            else {}
        )
        starts_before = (
            {request.id: request._sla_start() for request in self}
            if "reported_at" in vals
            else {}
        )
        result = super().write(vals)
        rematched = self.filtered(
            lambda request: request._sla_inputs() != inputs_before[request.id]
        )
        moved = self.filtered(
            lambda request: request.id in stages_before
            and request.stage_id != stages_before[request.id]
        )
        shifted = self.filtered(
            lambda request: request.id in starts_before
            and request._sla_start() != starts_before[request.id]
        )
        archiving = bool(vals.get("archive"))
        if not (rematched or moved or shifted or archiving):
            return result
        now = fields.Datetime.now()
        changed = self.env["maintenance.request.sla"].sudo()
        if archiving:
            # Archiving hides a request without changing its stage, so nothing
            # else would ever stop its clocks.
            changed |= self.sudo().sla_ids._sla_cancel(now)
        if shifted:
            shifted.sudo()._sla_shift_start(starts_before)
        if moved:
            changed |= moved.sudo().sla_ids._sla_evaluate(now)
        if rematched:
            changed |= rematched.sudo()._sla_apply(now=now)
        if moved - rematched:
            changed |= (moved - rematched).sudo()._sla_apply(
                next_cycles_only=True, now=now
            )
        self.sudo()._sla_post(changed)
        return result

    def _sla_inputs(self):
        """What re-matching depends on: the five match inputs, and the machine.

        equipment_id is a reporting dimension that can change while the
        category does not, so it is captured too.
        """
        self.ensure_one()
        return (
            self.priority,
            self.maintenance_team_id.id,
            self.category_id.id,
            self.maintenance_type,
            self.company_id.id,
            self.equipment_id.id,
        )

    def _sla_dimensions(self):
        """The grouping dimensions a record copies from its request."""
        self.ensure_one()
        return {
            "team_id": self.maintenance_team_id.id,
            "equipment_id": self.equipment_id.id,
            "category_id": self.category_id.id,
            "priority": self.priority,
            "maintenance_type": self.maintenance_type,
        }

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sla_records(self):
        """A request under SLA is cancelled, never deleted.

        Deleting it would take its records with it (request_id cascades), and
        SLA records are evidence, never deleted (R10). Applies to every user,
        sudo() included; at_uninstall=False lets an uninstall remove the
        module's data. Nothing in the installed stack deletes requests in code,
        and no parent cascades into them: equipment, stage and plan are all
        restrict.
        """
        for request in self.sudo():
            if request.sla_ids:
                raise UserError(
                    self.env._(
                        "%(request)s has SLA commitments recorded against it, so "
                        "it cannot be deleted. Cancel it instead.",
                        request=request.display_name,
                    )
                )

    def _sla_check_reopen(self, vals):
        """Refuse the way back from a cancellation, for a request under SLA.

        A cancelled work order is final; reopening is raising a new request.
        Both ways back are covered: leaving a stage flagged sla_cancel, and
        un-archiving, which core's reset_equipment_request does as well.
        Requests without SLA records keep core's behaviour.
        """
        leaving = "stage_id" in vals
        unarchiving = "archive" in vals and not vals["archive"]
        if not leaving and not unarchiving:
            return
        new_stage = self.env["maintenance.stage"].browse(vals.get("stage_id"))
        for request in self.sudo():
            if not request.sla_ids:
                continue
            if (
                leaving and request.stage_id.sla_cancel and not new_stage.sla_cancel
            ) or (unarchiving and request.archive):
                raise UserError(
                    self.env._(
                        "%(request)s was cancelled with SLA commitments recorded "
                        "against it, so it cannot be reopened. Raise a new "
                        "request instead.",
                        request=request.display_name,
                    )
                )

    def _sla_start(self):
        """Where this request's clocks start.

        A preventive clock starts at the scheduled date, and at the report when
        there is none: core does not require schedule_date, and only
        maintenance_plan always sets it. create_date is the last fallback, for a
        caller that passed reported_at=False: start_at is required, and without
        it the record's INSERT would block the request's creation.
        """
        self.ensure_one()
        if self.maintenance_type == "preventive":
            return self.schedule_date or self.reported_at or self.create_date
        return self.reported_at or self.create_date

    def _sla_shift_start(self, old_starts):
        """Move the clocks that still start at the old start to the new one.

        Only open cycle-1 records that started there and have not changed state
        since: every other record has booked time against its start, or starts
        elsewhere (a next cycle at its move, a preventive record at its
        scheduled date).
        """
        for request in self:
            old_start, new_start = old_starts[request.id], request._sla_start()
            records = request.sla_ids.filtered(
                lambda record, old_start=old_start: record.cycle == 1
                and record.state in OPEN_STATES
                and record.start_at == old_start
                and record.last_change_at == record.start_at
            )
            records.write({"start_at": new_start, "last_change_at": new_start})
            records._set_deadline()

    def _sla_apply(self, next_cycles_only=False, now=None):
        """Bring the requests' SLA records in line with the rules.

        The one matching function. Per target stage that has a winner (the
        first matching rule in (sequence, id) order) or an open record, the
        request's latest record on that stage decides:

            none                        a first record, from a winner created no
                                        later than the request
            open, its own rule wins     kept, dimensions refreshed
            open, another rule wins     cancelled and replaced, the clock carried
            open, no winner             cancelled
            cancelled, below target     resumed: a replacement carrying its clock
            cancelled, at or past       nothing
            finished, at or past        nothing
            finished, below target      the next cycle, starting now

        With next_cycles_only (a stage change) only the last row applies: a
        stage change never backfills a rule added later. An open record is
        always below its target here, since stage changes are evaluated first.
        A first record and a replacement are then evaluated against the current
        stage, so a request created at or past a target has that record finished
        at once.

        Runs as sudo(): the requester has no create right on the evidence, and a
        Many2many read applies the comodel's record rules, so a team list
        filtered empty would read as "any team".

        Returns the records it created, in their evaluated state, and those it
        cancelled.
        """
        now = now or fields.Datetime.now()
        rules = self.env["maintenance.sla"].sudo().search([])
        records = self.env["maintenance.request.sla"].sudo()
        cancelled = records
        vals_list = []
        for request in self.sudo():
            # Nothing is promised on a request that is already cancelled.
            if request.archive or request.stage_id.sla_cancel:
                continue
            position = (request.stage_id.sequence, request.stage_id.id)
            winners = {}
            for rule in rules:
                target = rule.target_stage_id
                if target not in winners and rule._matches(request):
                    winners[target] = rule
            open_records = request.sla_ids.filtered(
                lambda record: record.state in OPEN_STATES
            )
            targets = (
                open_records.target_stage_id
                | self.env["maintenance.stage"].concat(*winners)
            ).sorted(lambda stage: (stage.sequence, stage.id))
            for target in targets:
                rule = winners.get(target)
                below = position < (target.sequence, target.id)
                latest = request.sla_ids.filtered(
                    lambda record, target=target: record.target_stage_id == target
                ).sorted("id")[-1:]
                if not latest:
                    if (
                        next_cycles_only
                        or not rule
                        or rule.create_date > request.create_date
                    ):
                        continue
                    start_at = request._sla_start()
                    clock = {
                        "start_at": start_at,
                        "last_change_at": start_at,
                        "cycle": 1,
                        "consumed": 0.0,
                        "paused_time": 0.0,
                    }
                elif latest.state in OPEN_STATES:
                    if next_cycles_only:
                        continue
                    if rule == latest.sla_id:
                        # Refreshed while open, fixed once finished: the
                        # dimensions describe the request as it stood when the
                        # commitment was met.
                        dimensions = request._sla_dimensions()
                        if latest._sla_dimensions() != dimensions:
                            latest.write(dimensions)
                        continue
                    cancelled |= latest._sla_cancel(now)
                    if not rule:
                        continue
                    clock = self._sla_carried_clock(latest, now)
                elif latest.state == "cancelled":
                    if next_cycles_only or not rule or not below:
                        continue
                    clock = self._sla_carried_clock(latest, now)
                else:
                    if not rule or not below:
                        continue
                    clock = {
                        "start_at": now,
                        "last_change_at": now,
                        "cycle": latest.cycle + 1,
                        "consumed": 0.0,
                        "paused_time": 0.0,
                    }
                vals_list.append(
                    {
                        "request_id": request.id,
                        "sla_id": rule.id,
                        "target_stage_id": target.id,
                        "target_sequence": target.sequence,
                        "duration": rule.duration,
                        "at_risk_pct": rule.at_risk_pct,
                        "state": (
                            "paused"
                            if request.stage_id in rule.pause_stage_ids
                            else "running"
                        ),
                        **clock,
                        **request._sla_dimensions(),
                    }
                )
        records = records.create(vals_list)
        records._set_deadline()
        records._sla_evaluate(now)
        return records | cancelled

    @api.model
    def _sla_carried_clock(self, latest, now):
        """The clock a replacement or a resumed record takes over.

        Same start, the time counted and paused so far, the same cycle; it runs
        from now. The time between a cancellation and a resumption counts
        nowhere: no rule applied, so nothing was promised.
        """
        return {
            "start_at": latest.start_at,
            "last_change_at": now,
            "cycle": latest.cycle,
            "consumed": latest.consumed,
            "paused_time": latest.paused_time,
            "replaced_id": latest.id,
        }

    def _sla_post(self, records):
        """One internal note per request, one line per outcome among records.

        A cancelled record whose replacement is among the same records gets no
        line of its own: the replacement's line says it.
        """
        replaced = records.replaced_id
        lines_by_request = {}
        for record in records.sorted("id"):
            if record in replaced:
                continue
            line = record._sla_note_line()
            if line:
                lines_by_request.setdefault(record.request_id, []).append(line)
        for request, lines in lines_by_request.items():
            # Markup.join escapes each line, so a rule name cannot inject markup.
            request.sudo()._message_log(body=Markup("<br/>").join(lines))
