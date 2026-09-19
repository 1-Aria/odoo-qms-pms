# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

GROUP_ONLY_DOMAIN = [("parent_id", "=", False)]


class QmsCatalogProfile(models.Model):
    _name = "qms.catalog.profile"
    _description = "Catalog Profile"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    domain_kind = fields.Selection(
        selection=[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")],
        string="Domain",
        required=True,
        default="both",
    )
    defect_group_ids = fields.Many2many(
        comodel_name="qms.defect.code",
        relation="qms_profile_defect_group_rel",
        column1="profile_id",
        column2="defect_code_id",
        string="Defect Groups",
        domain=GROUP_ONLY_DOMAIN,
    )
    object_part_group_ids = fields.Many2many(
        comodel_name="qms.object.part",
        relation="qms_profile_object_part_group_rel",
        column1="profile_id",
        column2="object_part_id",
        string="Object Part Groups",
        domain=GROUP_ONLY_DOMAIN,
    )

    @property
    def _catalog_group_fields(self):
        return ("defect_group_ids", "object_part_group_ids")

    def _catalog_groups(self):
        """Every catalog record this profile bundles, whatever the catalog."""
        # A list, not a recordset union: the two fields hold different models.
        self.ensure_one()
        groups = []
        for field_name in self._catalog_group_fields:
            groups.extend(self[field_name])
        return groups

    @api.constrains("defect_group_ids", "object_part_group_ids")
    def _check_groups_only(self):
        """A profile bundles code groups, never individual codes.

        The field domain only filters the dropdown. A code attached directly
        would be skipped by the profile filtering without any error.
        """
        for profile in self:
            for group in profile._catalog_groups():
                if group.parent_id:
                    raise ValidationError(
                        self.env._(
                            "A profile bundles code groups, not codes. "
                            "'%(name)s' belongs to '%(group)s'.",
                            name=group.name,
                            group=group.parent_id.name,
                        )
                    )

    @api.constrains("domain_kind", "defect_group_ids", "object_part_group_ids")
    def _check_domain_kind(self):
        """Reject a direct clash between the profile's domain and a group's.

        Unlike a code, which has one group, a group belongs to many profiles,
        so a ``both`` group is free to sit in a ``qm`` and a ``pm`` profile.
        """
        kinds = dict(self._fields["domain_kind"]._description_selection(self.env))
        for profile in self:
            if profile.domain_kind == "both":
                continue
            for group in profile._catalog_groups():
                if group.domain_kind in ("both", profile.domain_kind):
                    continue
                raise ValidationError(
                    self.env._(
                        "Group '%(group)s' (%(group_kind)s) does not fit profile "
                        "'%(profile)s' (%(profile_kind)s).",
                        group=group.name,
                        group_kind=kinds[group.domain_kind],
                        profile=profile.name,
                        profile_kind=kinds[profile.domain_kind],
                    )
                )
