# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def action_l10n_vn_garment_load(self):
        self.ensure_one()
        result = self.company_id._l10n_vn_garment_load()
        none = self.env._("none")
        message = self.env._(
            "%(company)s: created %(created_count)s (%(created)s); "
            "kept as they were %(kept_count)s (%(kept)s).",
            company=self.company_id.display_name,
            created_count=len(result["created"]),
            created=", ".join(result["created"]) or none,
            kept_count=len(result["kept"]),
            kept=", ".join(result["kept"]) or none,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Garment pay scheme loaded"),
                "message": message,
                "type": "success",
                "sticky": True,
            },
        }
