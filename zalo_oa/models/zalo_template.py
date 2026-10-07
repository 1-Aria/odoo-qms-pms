# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ZaloTemplate(models.Model):
    """Message text with field placeholders, for one model.

    SMS's shape (sms/models/sms_template.py:10-13): mail.render.mixin with
    unrestricted rendering, so the full {{ object.field }} syntax works and
    the mixin keeps creating or editing a dynamic template to template
    editors.
    """

    _name = "zalo.template"
    _description = "Zalo Template"
    _inherit = ["mail.render.mixin"]
    _unrestricted_rendering = True
    _order = "name"

    name = fields.Char(required=True, translate=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Applies to",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model = fields.Char(
        string="Model",
        related="model_id.model",
        store=True,
        index=True,
    )
    # Not translated, unlike SMS's body: a translated body is stored per
    # language and rendered in the language of whoever runs the action -- the
    # automation's superuser -- so an edit made in another language would
    # silently leave the rendered wording unchanged. The recipients are chats,
    # with no language to render for.
    body = fields.Text(
        required=True,
        help="The message, with placeholders such as {{ object.name }} for the "
        "record's fields. Plain text, not HTML.",
    )

    @api.depends("model")
    def _compute_render_model(self):
        for template in self:
            template.render_model = template.model
