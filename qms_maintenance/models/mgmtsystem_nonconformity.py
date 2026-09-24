# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    # Prefixed, unlike mgmtsystem.action.maintenance_request_id in
    # maintenance_mgmtsystem_action: that module is meant for contribution
    # upstream, this one belongs to this quality system, and an unprefixed name
    # on an OCA model is what a future upstream field could take.
    #
    # ondelete="set null": the nonconformity is the record of what went wrong
    # and outlives the request that surfaced it.
    qms_maintenance_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        string="Maintenance Request",
        ondelete="set null",
        index=True,
        help="The maintenance request this nonconformity was raised from.",
    )

    # No smart button on this side: the field is itself a link to the request.
    # The aggregate direction earns one, and it lives on maintenance.request.
