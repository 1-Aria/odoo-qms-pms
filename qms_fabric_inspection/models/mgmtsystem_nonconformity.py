# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    def _qms_defect_item_values(self):
        """The checklist's items, then one per defect code found on the rolls.

        Codes in order of first appearance -- rolls in their order, each roll's
        entries in theirs -- so the list reads as the inspector entered it. The
        quantity is the number of entries, and the note names the rolls, which
        is what a decision on returning them needs. Entries on passing rolls
        count too: a defect found is a defect. Rolls left on an inspection
        switched to a plain test are ignored, as in its verdict.
        """
        values = super()._qms_defect_item_values()
        inspection = self.qc_inspection_id
        if not inspection.qms_roll_inspection:
            return values
        entries_by_code = {}
        for point in inspection.qms_roll_ids.point_ids:
            entries = entries_by_code.get(point.defect_code_id, point.browse())
            entries_by_code[point.defect_code_id] = entries | point
        for code, entries in entries_by_code.items():
            values.append(
                {
                    "nonconformity_id": self.id,
                    "defect_code_id": code.id,
                    "qty_affected": len(entries),
                    # entries.roll_id is each roll once, in entry order.
                    "note": self.env._(
                        "Point entries on rolls %(rolls)s",
                        rolls=", ".join(entries.roll_id.mapped("display_name")),
                    ),
                }
            )
        return values
