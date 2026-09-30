# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .maintenance_priority_rule import (
    CRITICALITY,
    URGENCY,
    _request_priority_selection,
)


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    # A snapshot, not a live read of the machine: what the request was worth is
    # part of its history, and re-rating a machine must not rewrite past
    # requests. Editable, so a one-off can be rated differently.
    criticality = fields.Selection(
        selection=CRITICALITY,
        string="Criticality",
        compute="_compute_criticality",
        store=True,
        readonly=False,
        help="Criticality of the machine when this request was raised.",
    )
    urgency = fields.Selection(
        selection=URGENCY,
        string="Urgency",
        tracking=True,
        help="Impact on production as reported.",
    )
    priority_suggested = fields.Selection(
        selection=lambda self: _request_priority_selection(self),
        string="Suggested Priority",
        compute="_compute_priority_suggested",
        store=True,
        help="What the priority rules make of this criticality and urgency.",
    )
    # Tracking is the only change: the native field keeps its label, its
    # selection and every view and filter that references it. Deliberately not
    # turned into a compute -- that would recompute every existing request on
    # install, move core's team KPI counters, and contest every other writer.
    priority = fields.Selection(tracking=True)
    priority_reason = fields.Char(
        string="Priority Reason",
        tracking=True,
        copy=False,
        help="Why this request's priority differs from the suggestion.",
    )

    @api.depends("equipment_id")
    def _compute_criticality(self):
        for request in self:
            if request.equipment_id.criticality:
                request.criticality = request.equipment_id.criticality

    @api.depends("criticality", "urgency", "company_id")
    def _compute_priority_suggested(self):
        rules = self.env["maintenance.priority.rule"]
        for request in self:
            request.priority_suggested = (
                rules._priority_for(
                    request.criticality, request.urgency, request.company_id
                )
                or False
            )

    @api.model_create_multi
    def create(self, vals_list):
        """A request created without a priority takes the suggestion."""
        requests = super().create(vals_list)
        for request, vals in zip(requests, vals_list):
            if "priority" not in vals and request.priority_suggested:
                request.priority = request.priority_suggested
        return requests

    def write(self, vals):
        """Follow a moved suggestion, unless the priority was overridden.

        The pair is captured per record before super(), because write() acts on
        a recordset and two requests can hold different pairs. Capturing on
        every write rather than on a trigger list is deliberate: criticality is
        itself a compute on equipment_id, so reassigning a request to another
        machine moves the suggestion while vals mentions neither field, and a
        trigger list would have to be kept in step with the compute graph.

        Equality between the old priority and the old suggestion is what "not
        overridden" means -- no second flag. A cleared priority is therefore an
        override too, which is intended: emptying the field is a decision.
        """
        before = {request.id: (request.priority, request.priority_suggested) for request in self}
        result = super().write(vals)
        if "priority" in vals:
            return result
        for request in self:
            old_priority, old_suggested = before[request.id]
            suggested = request.priority_suggested
            if suggested and suggested != old_suggested and old_priority == old_suggested:
                request.priority = suggested
        return result
