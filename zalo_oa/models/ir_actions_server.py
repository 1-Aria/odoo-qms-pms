# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IrActionsServer(models.Model):
    """A "Send Zalo Message" action type, as SMS adds "Send SMS"
    (sms/models/ir_actions_server.py:13-15, 72)."""

    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("zalo", "Send Zalo Message")],
        ondelete={"zalo": "cascade"},
    )
    zalo_template_id = fields.Many2one(
        comodel_name="zalo.template",
        string="Zalo Template",
        ondelete="set null",
    )
    zalo_destination_ids = fields.Many2many(
        comodel_name="zalo.destination",
        relation="ir_act_server_zalo_destination_rel",
        string="Zalo Destinations",
    )

    @api.constrains("model_id", "zalo_template_id")
    def _check_zalo_template_model(self):
        """Rendering against another model's records can only fail."""
        for action in self:
            template = action.zalo_template_id.sudo()
            if template and template.model_id != action.model_id:
                raise ValidationError(
                    self.env._(
                        "The Zalo template %(template)s applies to %(model)s, not to "
                        "this action's model.",
                        template=template.name,
                        model=template.model_id.name,
                    )
                )

    def _run_action_zalo_multi(self, eval_context=None):
        """Queue the template for the records, to every destination.

        Skips a run triggered only by a recompute, as SMS does
        (mail/models/ir_actions_server.py:201). Queueing never raises, so a
        broken template never fails the save that fired the rule.
        """
        if not self.zalo_template_id or not self.zalo_destination_ids:
            return False
        if self._is_recompute():
            return False
        eval_context = eval_context or {}
        records = eval_context.get("records") or eval_context.get("record")
        if not records:
            return False
        self.env["zalo.message"]._queue_from_template(
            self.zalo_template_id, records, self.zalo_destination_ids
        )
        return False
