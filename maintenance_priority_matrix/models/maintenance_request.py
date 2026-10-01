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
    # requests. The form shows it read-only: the machine's criticality is where
    # it is decided, and priority with its reason is where a request disagrees.
    # readonly=False keeps it writable by import or code.
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

    @api.model
    def _should_follow_suggestion(self, current_priority, old_priority, old_suggested):
        """Whether a priority may follow a moved suggestion.

        The one home of the rule. Both callers ask the same question and differ
        only in where "before" comes from: write() captures it from the database
        before super(), the onchange reads it from self._origin.

        current == old      nobody has moved the priority in this operation. In
                            write() that is implied, since a write naming
                            priority returns early; in the form it is the term
                            that protects a value the user just set or cleared.
        old == old_suggested the priority was never an override to begin with.
        """
        return current_priority == old_priority and old_priority == old_suggested

    @api.onchange("equipment_id", "criticality", "urgency")
    def _onchange_priority_follows_suggestion(self):
        """Move the priority in the form, so the suggestion never looks broken.

        Without this the form judged a half-finished state: changing urgency
        moved the suggestion while priority still held its old value, so the
        reason became required for a difference the save then removed by
        following the suggestion anyway.

        equipment_id is a trigger in its own right. The recompute does chain
        into this method today, because the web onchange loop reruns for fields
        whose value changed and are in the view's spec
        (addons/web/models/models.py:1041-1057) -- but only while criticality
        stays on the form. Naming equipment_id here does not depend on the view.
        """
        if self.priority_suggested and self._should_follow_suggestion(
            self.priority, self._origin.priority, self._origin.priority_suggested
        ):
            self.priority = self.priority_suggested

    @api.model_create_multi
    def create(self, vals_list):
        """A request created without a priority takes the suggestion.

        The test is on the *value*, not on the key: the web client sends
        priority: False for a field that is on the form and untouched, so
        "priority" not in vals skipped the fill on every request raised from the
        form. The falsy test costs nothing, because priority values are the
        strings "0" to "3" and "0" is truthy -- an explicit Very Low still
        counts as a choice.

        The consequence to know: a caller that means "create this with no
        priority" cannot say so while a suggestion exists, since that is
        indistinguishable from the form's untouched field. It can clear the
        value afterwards, which counts as an override.
        """
        requests = super().create(vals_list)
        for request, vals in zip(requests, vals_list):
            if not vals.get("priority") and request.priority_suggested:
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

        Whether the priority may follow is _should_follow_suggestion's
        decision, shared with the form's onchange so the two can never disagree
        about what "overridden" means. A cleared priority is an override too,
        which is intended: emptying the field is a decision.
        """
        before = {request.id: (request.priority, request.priority_suggested) for request in self}
        result = super().write(vals)
        if "priority" in vals:
            return result
        for request in self:
            old_priority, old_suggested = before[request.id]
            suggested = request.priority_suggested
            if (
                suggested
                and suggested != old_suggested
                and self._should_follow_suggestion(
                    request.priority, old_priority, old_suggested
                )
            ):
                request.priority = suggested
        return result
