# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

from .maintenance_request_sla import FINISHED_STATES


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

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        requests._sla_post(requests._sla_apply())
        return requests

    def write(self, vals):
        """Drive the clocks from the stage, and make cancellation final.

        The stage is compared before and after rather than tested by key, so a
        write setting the stage a request already has does nothing. Core's own
        nested writes after a stage change (close_date, kanban_state) carry no
        stage_id and pass through.
        """
        self._sla_check_reopen(vals)
        stages_before = (
            {request.id: request.stage_id for request in self}
            if "stage_id" in vals
            else {}
        )
        result = super().write(vals)
        if not stages_before and not vals.get("archive"):
            return result
        now = fields.Datetime.now()
        requests = self.sudo()
        changed = self.env["maintenance.request.sla"].sudo()
        if vals.get("archive"):
            # Archiving hides a request without changing its stage, so nothing
            # else would ever stop its clocks.
            changed |= requests.sla_ids._sla_cancel(now)
        moved = requests.filtered(
            lambda request: request.id in stages_before
            and request.stage_id != stages_before[request.id]
        )
        if moved:
            changed |= moved.sla_ids._sla_evaluate(now)
            changed |= moved._sla_apply(next_cycles_only=True, now=now)
        requests._sla_post(changed)
        return result

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

    def _sla_apply(self, next_cycles_only=False, now=None):
        """Bring the requests' SLA records in line with the rules.

        The one matching function. Per target stage, the first matching rule in
        (sequence, id) order wins, and the request's latest record on that
        stage decides what happens:

            none                          a first record, unless
                                          next_cycles_only (a stage change
                                          never backfills a rule added later)
            open                          nothing
            cancelled                     nothing
            finished, at or past target   nothing
            finished, below target        the next cycle, starting now

        Every row but the first and the last leaves a target stage alone, which
        makes a second run change nothing. New records are then evaluated
        against the current stage, so a request created at or past a target has
        that record finished at once.

        Runs as sudo(): the requester has no create right on the evidence, and a
        Many2many read applies the comodel's record rules, so a team list
        filtered empty would read as "any team".

        Returns the records it created, in their evaluated state.
        """
        now = now or fields.Datetime.now()
        rules = self.env["maintenance.sla"].sudo().search([])
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
            for target, rule in winners.items():
                latest = request.sla_ids.filtered(
                    lambda record, target=target: record.target_stage_id == target
                ).sorted("id")[-1:]
                if not latest:
                    if next_cycles_only:
                        continue
                    start_at, cycle = request._sla_start(), 1
                elif latest.state in FINISHED_STATES and position < (
                    target.sequence,
                    target.id,
                ):
                    start_at, cycle = now, latest.cycle + 1
                else:
                    continue
                vals_list.append(
                    {
                        "request_id": request.id,
                        "sla_id": rule.id,
                        "target_stage_id": target.id,
                        "target_sequence": target.sequence,
                        "duration": rule.duration,
                        "at_risk_pct": rule.at_risk_pct,
                        "start_at": start_at,
                        "state": (
                            "paused"
                            if request.stage_id in rule.pause_stage_ids
                            else "running"
                        ),
                        "consumed": 0.0,
                        "paused_time": 0.0,
                        # From the start, not from the save: a backdated report
                        # counts from the report, and a clock starting in the
                        # future stays at rest until then.
                        "last_change_at": start_at,
                        "cycle": cycle,
                        "team_id": request.maintenance_team_id.id,
                        "equipment_id": request.equipment_id.id,
                        "category_id": request.category_id.id,
                        "priority": request.priority,
                        "maintenance_type": request.maintenance_type,
                    }
                )
        records = self.env["maintenance.request.sla"].sudo().create(vals_list)
        records._set_deadline()
        records._sla_evaluate(now)
        return records

    def _sla_post(self, records):
        """One internal note per request, one line per outcome among records."""
        lines_by_request = {}
        for record in records.sorted("id"):
            line = record._sla_note_line()
            if line:
                lines_by_request.setdefault(record.request_id, []).append(line)
        for request, lines in lines_by_request.items():
            # Markup.join escapes each line, so a rule name cannot inject markup.
            request.sudo()._message_log(body=Markup("<br/>").join(lines))
