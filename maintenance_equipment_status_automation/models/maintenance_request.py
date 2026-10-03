# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    @api.model_create_multi
    def create(self, vals_list):
        """A request created in a mapped stage has reached it."""
        requests = super().create(vals_list)
        requests._apply_equipment_status()
        return requests

    def write(self, vals):
        """Only a real stage change applies the mapping.

        The stage is compared before and after rather than tested by key, so a
        request saved unchanged, or a write that does not move it, never
        overwrites a status corrected by hand.
        """
        stages_before = (
            {request.id: request.stage_id for request in self}
            if "stage_id" in vals
            else {}
        )
        result = super().write(vals)
        if stages_before:
            self.filtered(
                lambda request: request.stage_id != stages_before[request.id]
            )._apply_equipment_status()
        return result

    def _apply_equipment_status(self):
        """Give each corrective request's machine the status of its stage.

        Written as sudo(): equipment is writable only by equipment managers,
        while anyone who may move a request triggers this; the tracked change
        still carries the user. One-directional, as the plan has it: the
        machine's status is written, never read back, and the last mapped move
        wins. A status limited to categories that exclude the machine's is not
        applied, as the equipment form would not offer it.
        """
        for request in self.sudo():
            status = request.stage_id.equipment_status_id
            equipment = request.equipment_id
            if request.maintenance_type != "corrective" or not equipment or not status:
                continue
            if status.category_ids and equipment.category_id not in status.category_ids:
                continue
            # Unchanged, it is not written, so it posts no empty tracking line.
            if equipment.status_id != status:
                equipment.status_id = status
