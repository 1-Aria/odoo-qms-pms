# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QmsCatalogMixin(models.AbstractModel):
    """Shared shape of the QMS catalogs: a two-level tree of groups and codes.

    Concrete models declare ``parent_id`` and ``child_ids`` themselves, since a
    Many2one cannot name the model that inherits this mixin.
    """

    _name = "qms.catalog.mixin"
    _description = "QMS Catalog Mixin"
    _order = "parent_id, sequence"
    _parent_store = True
    _rec_names_search = ["name", "ref_code"]

    name = fields.Char(required=True, translate=True)
    ref_code = fields.Char(string="Code")
    sequence = fields.Integer(default=10, help="Defines the order to present items")
    parent_path = fields.Char(index=True)
    active = fields.Boolean(default=True)
    domain_kind = fields.Selection(
        selection=[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")],
        string="Domain",
        required=True,
        default="both",
    )

    @api.depends("name", "parent_id.name")
    def _compute_display_name(self):
        for record in self:
            if record.parent_id:
                record.display_name = f"{record.parent_id.name} / {record.name}"
            else:
                record.display_name = record.name
