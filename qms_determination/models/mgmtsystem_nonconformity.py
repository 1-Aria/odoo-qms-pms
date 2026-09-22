# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    response_ids = fields.One2many(
        comodel_name="qms.nonconformity.response",
        inverse_name="nonconformity_id",
        string="Suggested Responses",
    )

    def action_suggest_response(self):
        """Replace every response line with the rules that match each item.

        A full reset, manual lines included (D30): one sentence of behaviour,
        and the button is only visible during Analysis. Item severities are
        not touched -- a rule's severity is a suggestion shown on its line.
        """
        rule_model = self.env["qms.determination.rule"]
        for nonconformity in self:
            nonconformity.response_ids.unlink()
            values = [
                {
                    "nonconformity_id": nonconformity.id,
                    "item_id": item.id,
                    "rule_id": rule.id,
                }
                for item in nonconformity.item_ids
                for rule in rule_model._match_item(item)
            ]
            self.env["qms.nonconformity.response"].create(values)
        return True

    def action_generate_actions(self):
        """Create one action per template on every response line.

        Suggested and manual lines alike. No deduplication and no memory of
        earlier presses (D27); the button asks for confirmation first, since
        no group may delete an action.

        The values mirror mgmtsystem_action_template's _onchange_template_id
        (mgmtsystem_action_template/models/mgmtsystem_action.py:23) -- diff
        against it on an OCA upgrade. That onchange runs only in a form, and
        mgmtsystem.action requires name and type_action with no default, so
        the copy is needed, not a convenience. It omits the onchange's "NEW "
        prefix: a generated action is a finished record, not a placeholder.

        A template without a type_action is skipped rather than given a
        guessed type, and the skipped templates are named afterwards.
        """
        action_model = self.env["mgmtsystem.action"]
        skipped = self.env["mgmtsystem.action.template"]
        for nonconformity in self:
            values = []
            for line in nonconformity.response_ids:
                for template in line.rule_id.action_template_ids:
                    if not template.type_action:
                        skipped |= template
                        continue
                    values.append(
                        {
                            "name": template.name,
                            "type_action": template.type_action,
                            "description": template.description,
                            "user_id": template.user_id.id,
                            "tag_ids": [(6, 0, template.tag_ids.ids)],
                            "template_id": template.id,
                            "nonconformity_ids": [(4, nonconformity.id)],
                        }
                    )
            action_model.create(values)
        if not skipped:
            return True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "warning",
                "title": self.env._("Some action templates were skipped"),
                "message": self.env._(
                    "No response type: %(names)s",
                    names=", ".join(skipped.mapped("name")),
                ),
                # display_notification returns params.next once shown
                # (web/static/src/webclient/actions/client_actions.js:22-25);
                # the reload shows the actions that were created.
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }
