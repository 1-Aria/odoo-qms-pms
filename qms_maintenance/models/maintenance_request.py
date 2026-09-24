# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    qms_nonconformity_ids = fields.One2many(
        comodel_name="mgmtsystem.nonconformity",
        inverse_name="qms_maintenance_request_id",
        string="Nonconformities",
    )
    qms_nonconformity_count = fields.Integer(
        string="# Nonconformities",
        compute="_compute_qms_nonconformity_count",
    )

    # A plain len(), unlike the action count beside it: nothing else can make a
    # nonconformity belong to a request, so there is one path and no extension
    # point to search over.
    @api.depends("qms_nonconformity_ids")
    def _compute_qms_nonconformity_count(self):
        for request in self:
            request.qms_nonconformity_count = len(request.qms_nonconformity_ids)

    def _qms_nonconformity_context(self):
        """The defaults a nonconformity raised from this request starts with.

        default_product_id is what makes the catalogs work: 7.6 scopes the
        defect and object-part dropdowns through the product's profiles, and on
        the maintenance side the product is reached through the equipment, which
        maintenance_product supplies. The chain is null-safe by construction --
        a request with no equipment, or equipment with no product, yields False
        with no guard, and the dropdowns then fall back to empty as 7.6
        describes.

        Plan 7.10 added a related product_id field on the request for this. It
        needed one because it prefilled from XML, where a context can only name
        fields of the record; built here, the path is read directly and the
        field is not declared at all.
        """
        self.ensure_one()
        return {
            "default_qms_maintenance_request_id": self.id,
            "default_equipment_id": self.equipment_id.id,
            "default_product_id": self.equipment_id.product_id.id,
            "default_name": self.name,
            "default_company_id": self.company_id.id,
        }

    def action_view_qms_nonconformities(self):
        """Open this request's nonconformities, whatever the count.

        No branch on the count: at zero the list is empty and its New button
        carries the same defaults, which is what a branch would be for.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Nonconformities"),
            "res_model": "mgmtsystem.nonconformity",
            "view_mode": "list,form",
            "domain": [("qms_maintenance_request_id", "=", self.id)],
            "context": self._qms_nonconformity_context(),
        }

    def _action_domain(self):
        """Add the actions a nonconformity raised from this request produced.

        The extension point maintenance_mgmtsystem_action left: its own domain
        matches actions pointing at the request, and these two arms reach the
        action plan and the immediate containment action of a nonconformity
        raised from it -- the same two arms qc.inspection uses on the quality
        side.

        expression.OR rather than hand-written prefix operators: the inherited
        domain is one leaf today, and an OR written by hand would have to be
        rewritten the moment it is not.
        """
        return expression.OR(
            [
                super()._action_domain(),
                [
                    "|",
                    ("nonconformity_ids.qms_maintenance_request_id", "=", self.id),
                    (
                        "nonconformity_immediate_id.qms_maintenance_request_id",
                        "=",
                        self.id,
                    ),
                ],
            ]
        )

    # The body adds nothing: this override exists to carry the decorator.
    # Dependencies merge across the MRO -- a computed field resolves its compute
    # through resolve_mro and extends the dependency list from every definition
    # it finds (fields.py:575-586, api.py:79-92) -- so the inherited action_ids
    # dependency still applies and only the new paths are named here.
    @api.depends(
        "qms_nonconformity_ids.action_ids",
        "qms_nonconformity_ids.immediate_action_id",
    )
    def _compute_action_count(self):
        return super()._compute_action_count()
