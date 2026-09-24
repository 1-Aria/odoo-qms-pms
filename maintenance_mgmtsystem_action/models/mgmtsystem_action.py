# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemAction(models.Model):
    _inherit = "mgmtsystem.action"

    # No qms_ prefix: that marks a field as belonging to one quality system, and
    # this module depends only on core maintenance and mgmtsystem_action, so it
    # is meant to be contributable upstream.
    #
    # ondelete="set null": an action is the record of work done and must outlive
    # its source. Core places no guard on deleting a maintenance request, so
    # "restrict" would make a request undeletable because someone raised an
    # action from it.
    maintenance_request_id = fields.Many2one(
        comodel_name="maintenance.request",
        string="Maintenance Request",
        ondelete="set null",
        index=True,
        help="The maintenance request this action belongs to.",
    )

    # No smart button on this side: a Many2one on a form already opens its
    # record. What earns a button is the aggregate direction, a count of many
    # actions that no field shows, and that lives on maintenance.request.
