# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    action_ids = fields.One2many(
        comodel_name="mgmtsystem.action",
        inverse_name="maintenance_request_id",
        string="Actions",
    )
    action_count = fields.Integer(
        string="# Actions",
        compute="_compute_action_count",
    )

    def _action_domain(self):
        """Every action belonging to this request.

        One arm here, and that is the extension point: a module that knows about
        nonconformities widens this to include the actions reached through a
        nonconformity raised from the request -- its action plan and its
        immediate action. This module cannot do that itself, since
        mgmtsystem_nonconformity is not a dependency and adding one would put
        the whole management system into a bridge that two other modules want.
        """
        self.ensure_one()
        return [("maintenance_request_id", "=", self.id)]

    # search_count rather than len(action_ids), so widening the domain widens
    # the count with it. The depends list is what invalidates a count a search
    # produces: a search has no dependency path of its own, and a module adding
    # an arm adds its paths here too.
    @api.depends("action_ids")
    def _compute_action_count(self):
        action_model = self.env["mgmtsystem.action"]
        for request in self:
            # An unsaved record has a NewId, which no domain can carry.
            if isinstance(request.id, models.NewId):
                request.action_count = 0
                continue
            request.action_count = action_model.search_count(request._action_domain())

    def action_view_actions(self):
        """Open this request's actions, whatever the count.

        No branch on the count: at zero the list is empty and its New button
        carries the same default, which is what a branch would be for. The
        context is the link and nothing else -- an action's name is a subject
        and its response type a judgement, so neither is guessed.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Actions"),
            "res_model": "mgmtsystem.action",
            "view_mode": "list,form",
            "domain": self._action_domain(),
            "context": {"default_maintenance_request_id": self.id},
        }
