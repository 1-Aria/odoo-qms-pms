# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
        requests._sla_apply()
        return requests

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

    def _sla_apply(self):
        """Bring the requests' SLA records in line with the rules.

        The one matching function. This is its creation case: per target stage,
        the first matching rule in (sequence, id) order wins, and a record is
        created when that stage has no record that is not cancelled. That guard
        makes a second run change nothing. Later steps add the reached case,
        the next cycle, and replacing an open record whose rule no longer wins.

        Runs as sudo(): the requester has no create right on the evidence, and a
        Many2many read applies the comodel's record rules, so a team list
        filtered empty would read as "any team".
        """
        rules = self.env["maintenance.sla"].sudo().search([])
        vals_list = []
        for request in self.sudo():
            # Nothing is promised on a request that is already cancelled.
            if request.archive or request.stage_id.sla_cancel:
                continue
            winners = {}
            for rule in rules:
                stage = rule.target_stage_id
                if stage not in winners and rule._matches(request):
                    winners[stage] = rule
            covered = request.sla_ids.filtered(
                lambda record: record.state != "cancelled"
            ).target_stage_id
            start_at = request._sla_start()
            for stage, rule in winners.items():
                if stage in covered:
                    continue
                vals_list.append(
                    {
                        "request_id": request.id,
                        "sla_id": rule.id,
                        "target_stage_id": stage.id,
                        "target_sequence": stage.sequence,
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
                        "cycle": 1,
                        "team_id": request.maintenance_team_id.id,
                        "equipment_id": request.equipment_id.id,
                        "category_id": request.category_id.id,
                        "priority": request.priority,
                        "maintenance_type": request.maintenance_type,
                    }
                )
        records = self.env["maintenance.request.sla"].sudo().create(vals_list)
        records._set_deadline()
        return records
