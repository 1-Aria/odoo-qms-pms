# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    _sql_constraints = [
        ("ref_code_uniq", "unique (ref_code)", "This code already exists."),
    ]

    name = fields.Char(required=True, translate=True)
    ref_code = fields.Char(string="Code", required=True)
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

    @api.constrains("parent_id")
    def _check_catalog_depth(self):
        """Keep the catalog two levels deep: a group and its codes."""
        for record in self:
            if not record.parent_id:
                continue
            if record.parent_id.parent_id or record.child_ids:
                raise ValidationError(
                    self.env._(
                        "Catalogs are two levels deep — a group and its codes. "
                        "'%(name)s' cannot be nested further.",
                        name=record.name,
                    )
                )

    @api.constrains("domain_kind", "parent_id")
    def _check_domain_kind(self):
        """A code's domain must fit its group's.

        ``qm`` under ``qm``, ``pm`` under ``pm``, anything under ``both``.
        Checked from both ends, so narrowing a group with codes fails too.
        """
        for record in self:
            if record.parent_id:
                record._check_domain_kind_fits(record.parent_id, record)
            for child in record.child_ids:
                record._check_domain_kind_fits(record, child)

    def _check_domain_kind_fits(self, group, code):
        if group.domain_kind == "both" or group.domain_kind == code.domain_kind:
            return
        kinds = dict(self._fields["domain_kind"]._description_selection(self.env))
        raise ValidationError(
            self.env._(
                "Code '%(code)s' (%(code_kind)s) does not fit its group "
                "'%(group)s' (%(group_kind)s).",
                code=code.name,
                code_kind=kinds[code.domain_kind],
                group=group.name,
                group_kind=kinds[group.domain_kind],
            )
        )
