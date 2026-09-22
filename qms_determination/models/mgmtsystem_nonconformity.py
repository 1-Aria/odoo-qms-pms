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
