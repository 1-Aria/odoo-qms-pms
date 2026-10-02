# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError

from ..models.maintenance_request_sla import FINISHED_STATES


class MaintenanceRequestSlaWaive(models.TransientModel):
    """Waive a finished SLA record, with a reason.

    The access row, managers only, is the guard: the wizard writes the
    evidence as sudo(), and without an access row a user can neither create
    it nor call its methods over RPC, since access rights apply to transient
    models too.
    """

    _name = "maintenance.request.sla.waive"
    _description = "Waive an SLA Record"

    sla_record_id = fields.Many2one(
        comodel_name="maintenance.request.sla",
        string="SLA Record",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    # Required, unlike crm.lost.reason in its wizard: a waiver without a
    # classified reason defeats reporting by reason. A Many2one dropdown offers
    # active reasons only, so an archived one is not offered.
    reason_id = fields.Many2one(
        comodel_name="maintenance.sla.waive.reason",
        string="Reason",
        required=True,
    )
    note = fields.Char()

    def action_confirm(self):
        """Waive the record, once, and say so on the request.

        Finished records only: a waiver judges an outcome. An open record that
        should not count belongs to a request that should be cancelled.
        """
        self.ensure_one()
        record = self.sla_record_id.sudo()
        if record.waived or record.state not in FINISHED_STATES:
            raise UserError(
                self.env._(
                    "Only a finished SLA record that is not yet waived can be "
                    "waived."
                )
            )
        record.write(
            {
                "waived": True,
                "waive_reason_id": self.reason_id.id,
                "waive_note": self.note,
                "waived_by_id": self.env.uid,
                "waived_at": fields.Datetime.now(),
            }
        )
        values = {
            "rule": record.sla_id.name,
            "reason": self.reason_id.name,
            "note": self.note,
        }
        if self.note:
            body = self.env._("%(rule)s waived: %(reason)s — %(note)s", **values)
        else:
            body = self.env._("%(rule)s waived: %(reason)s", **values)
        record.request_id._message_log(body=body)
        return {"type": "ir.actions.act_window_close"}
