# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    # In no view, and not what the count reads. It is here to give the
    # non-stored count a dependency path: a search_count has none, so without
    # this field -- and the two nonconformity paths beside it in @api.depends --
    # the count would be computed once per cache lifetime and never
    # invalidated, and an action created in the same transaction would not
    # appear. Being invisible, it cannot disagree with the button.
    qms_action_ids = fields.One2many(
        comodel_name="mgmtsystem.action",
        inverse_name="qms_inspection_id",
        string="Directly Linked Actions",
    )
    qms_action_count = fields.Integer(
        string="# Actions",
        compute="_compute_qms_action_count",
    )

    def _qms_action_domain(self):
        """Every action this inspection led to, by any of three paths.

        Counting the direct link alone would read 0 on the flow the system is
        built around: Populate Defect, then Suggest Response, then Generate
        Actions, which links each action to the *nonconformity*.

        - qms_inspection_id: raised on the inspection directly.
        - nonconformity_ids: the action plan of a nonconformity raised from it,
          which is what Generate Actions writes
          (mgmtsystem_nonconformity/models/mgmtsystem_action.py:12-18).
        - nonconformity_immediate_id: that nonconformity's immediate
          containment action, a Many2one on the nonconformity and absent from
          action_ids. OCA's own code treats the full set as
          action_ids + immediate_action_id (mgmtsystem_nonconformity.py:156),
          and plan 7.7 makes it the fast path for containment -- the action a
          failed inspection most often produces first.

        One search, so an action reachable by two paths is counted once.

        A method rather than an inline domain because the maintenance side
        meets the same gap: D19 and D22 have maintenance_mgmtsystem_action ship
        the direct arm while qms_maintenance extends it with the nonconformity
        arms, which only works if this is overridable.
        """
        self.ensure_one()
        return [
            "|",
            ("qms_inspection_id", "=", self.id),
            "|",
            ("nonconformity_ids.qc_inspection_id", "=", self.id),
            ("nonconformity_immediate_id.qc_inspection_id", "=", self.id),
        ]

    @api.depends(
        "qms_action_ids",
        "mgmtsystem_nonconformity_ids.action_ids",
        "mgmtsystem_nonconformity_ids.immediate_action_id",
    )
    def _compute_qms_action_count(self):
        action_model = self.env["mgmtsystem.action"]
        for inspection in self:
            # An unsaved record has a NewId, which no domain can carry.
            if isinstance(inspection.id, models.NewId):
                inspection.qms_action_count = 0
                continue
            inspection.qms_action_count = action_model.search_count(
                inspection._qms_action_domain()
            )

    def _qms_nonconformity_context(self):
        """The defaults a nonconformity raised from this inspection starts with.

        default_product_id is the one plan 7.10 asked for and the OCA bridge
        never set. It is what makes the 7.6 catalog filtering work on the new
        record: the product resolves the profiles that scope the defect and
        object-part dropdowns. An inspection on a picking resolves no product
        (product_id is computed from object_id and covers a product, a stock
        move or a lot only), so the prefill is empty there and the dropdowns
        fall back to asking the user to clear the filter -- by design.

        search_default_user_id, which the action carries in its own stored
        context, is deliberately not reproduced: on a list already scoped to one
        inspection, a "my nonconformities" filter hides the ones raised by
        colleagues.
        """
        self.ensure_one()
        return {
            "search_default_qc_inspection_id": self.id,
            "default_qc_inspection_id": self.id,
            "default_product_id": self.product_id.id,
            "default_name": self.name,
            "default_company_id": self.company_id.id,
        }

    def action_view_nonconformities(self):
        """OCA's button, with the defaults applied whatever the count.

        The bridge sets its context only in the branch it takes for zero or one
        nonconformity (mgmtsystem_nonconformity_quality_control_oca/models/
        qc_inspection.py); with two or more it sets a domain and leaves the
        action's stored context, so New from that list prefills nothing.
        Setting the context outside the branch makes plan 7.10's "the same
        defaults still on the action" true for every count.

        It replaces rather than merges because that stored context is the string
        {"search_default_user_id":uid}, evaluated by the client
        (mgmtsystem_nonconformity/views/mgmtsystem_nonconformity.xml:325), so
        merging into it would mean string surgery.
        """
        action = super().action_view_nonconformities()
        action["context"] = self._qms_nonconformity_context()
        return action

    def action_view_qms_actions(self):
        """Open this inspection's actions, whatever the count.

        No branch on the count, unlike OCA's own bridge
        (mgmtsystem_nonconformity_quality_control_oca/models/qc_inspection.py),
        which switches to a form for a single record and sets its context
        defaults only in that branch -- so creating from a list of many
        prefills nothing. Here the list is always the list: at zero it is
        empty and its New button carries the same default.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Actions"),
            "res_model": "mgmtsystem.action",
            "view_mode": "list,form",
            "domain": self._qms_action_domain(),
            "context": {"default_qms_inspection_id": self.id},
        }
