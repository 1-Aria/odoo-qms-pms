# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

RECIPIENT_TYPES = [("group", "Group chat"), ("user", "User")]


class ZaloDestination(models.Model):
    """A named recipient, so rules never hold raw Zalo IDs."""

    _name = "zalo.destination"
    _description = "Zalo Destination"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    recipient_type = fields.Selection(
        selection=RECIPIENT_TYPES,
        string="Type",
        required=True,
        default="group",
    )
    zalo_id = fields.Char(
        string="Zalo ID",
        required=True,
        help="The group's ID, or the user's ID as the OA knows it: the webhook's "
        "recipient.id of a group message, or sender.id of a 1:1 message.",
    )
    active = fields.Boolean(default=True)
