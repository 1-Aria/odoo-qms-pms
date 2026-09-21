# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsDisposition(models.Model):
    """What was decided about the affected material or equipment.

    A record rather than a Selection, so a site can add its own verdicts.
    Logic branches on ``code``, never on ids: ids are not portable between
    databases. The views keep ``code`` readonly once the record exists, so a
    rename cannot quietly stop a ``code == "scrap"`` test from matching.
    """

    _name = "qms.disposition"
    _description = "Nonconformity Disposition"
    _order = "sequence, id"

    _sql_constraints = [
        ("code_uniq", "unique (code)", "This disposition code already exists."),
    ]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Stable key that automation matches on.")
    sequence = fields.Integer(default=10, help="Defines the order to present items")
    active = fields.Boolean(default=True)
    description = fields.Text()
