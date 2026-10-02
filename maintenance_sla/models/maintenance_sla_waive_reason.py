# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MaintenanceSlaWaiveReason(models.Model):
    """Why an SLA outcome does not count, from a configured list.

    The shape of core's crm.lost.reason: a list makes waivers a policy rather
    than a sentence each manager phrases differently, and makes them
    reportable. No company: a reason is vocabulary. A reason that has been used
    cannot be deleted, so retiring one is archiving it, which also takes it out
    of the waiver wizard's dropdown. The module ships none.
    """

    _name = "maintenance.sla.waive.reason"
    _description = "SLA Waiver Reason"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
