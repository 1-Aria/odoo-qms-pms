# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    @api.model_create_multi
    def create(self, vals_list):
        """Requests created with a plan get the plan's actions.

        maintenance_plan generates requests through this create() with
        maintenance_plan_id in the values (maintenance_equipment.py:156), from
        its cron and its manual button alike, so no OCA method is touched
        (plan D23). A request raised by hand with a plan set gets them too; a
        plan written onto a request later does not.
        """
        requests = super().create(vals_list)
        requests._create_plan_actions()
        return requests

    def _create_plan_actions(self):
        """One action per typed template of each request's plan.

        The values mirror mgmtsystem_action_template's onchange
        (mgmtsystem_action_template/models/mgmtsystem_action.py:23), as
        qms_determination's Generate Actions does, without its "NEW " prefix;
        diff against it on an OCA upgrade. mgmtsystem.action requires a type
        with no default, so a template without one is skipped rather than given
        a guessed type, and logged, since the cron has no screen to warn on.

        Created as sudo(): the plan's manual button runs as the user, and
        creating an action needs a management-system group that a maintenance
        user may not hold.
        """
        vals_list = []
        for request in self.sudo().filtered("maintenance_plan_id"):
            for template in request.maintenance_plan_id.action_template_ids:
                if not template.type_action:
                    _logger.info(
                        "Action template %s has no response type: no action "
                        "created for maintenance request %s.",
                        template.display_name,
                        request.display_name,
                    )
                    continue
                vals_list.append(
                    {
                        "name": template.name,
                        "type_action": template.type_action,
                        "description": template.description,
                        "user_id": template.user_id.id,
                        "tag_ids": [(6, 0, template.tag_ids.ids)],
                        "template_id": template.id,
                        "maintenance_request_id": request.id,
                        # Due when the work is: maintenance_plan always sets
                        # the scheduled date.
                        "date_deadline": request.schedule_date
                        and request.schedule_date.date(),
                    }
                )
        if vals_list:
            self.env["mgmtsystem.action"].sudo().create(vals_list)
