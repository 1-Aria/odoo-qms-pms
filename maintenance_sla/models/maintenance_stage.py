# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MaintenanceStage(models.Model):
    _inherit = "maintenance.stage"

    # done is not a substitute: Repaired is a done stage and must stop clocks by
    # being reached, while Scrap must cancel them.
    sla_cancel = fields.Boolean(
        string="Cancels SLA",
        help="Reaching this stage cancels the request's open SLA records. "
        "Records already met keep their result.",
    )

    @api.constrains("sla_cancel")
    def _check_not_a_target(self):
        """The other end of maintenance.sla._check_target_not_cancel.

        That constraint fires only when a rule's target is written, and dotted
        names are ignored by @api.constrains (odoo/api.py:180). Archived rules
        count, so that un-archiving one cannot bring the conflict back: writing
        active triggers neither check. Searched as sudo(): stages carry no
        company, and the multi-company rule must not hide another company's
        rule from the check.
        """
        flagged = self.filtered("sla_cancel")
        if not flagged:
            return
        rule = (
            self.env["maintenance.sla"]
            .sudo()
            .with_context(active_test=False)
            .search([("target_stage_id", "in", flagged.ids)], limit=1)
        )
        if rule:
            raise ValidationError(
                self.env._(
                    "'%(stage)s' is the target stage of the SLA rule '%(rule)s', "
                    "so it cannot cancel SLA records.",
                    stage=rule.target_stage_id.display_name,
                    rule=rule.display_name,
                )
            )
