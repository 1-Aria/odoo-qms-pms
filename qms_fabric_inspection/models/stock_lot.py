# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.qms_quality_control.models.mgmtsystem_nonconformity import (
    INSPECTION_DONE_STATES,
)


class StockLot(models.Model):
    _inherit = "stock.lot"

    # Lots are named [Dye lot]-[Roll], the dye lot being the supplier's lot on
    # the packing list. Editable for a name that breaks the convention; a
    # rename recomputes it over a hand-corrected value.
    qms_dye_lot = fields.Char(
        string="Dye Lot",
        compute="_compute_qms_dye_lot",
        store=True,
        readonly=False,
        index=True,
        help='The supplier\'s dye lot, taken from the lot name up to its last "-" '
        "by the [Dye lot]-[Roll] convention; correct it here when a name does not "
        "follow it.",
    )
    # The band's dependency path; in no view.
    qms_roll_ids = fields.One2many(
        comodel_name="qms.inspection.roll",
        inverse_name="lot_id",
        string="Inspected Rolls",
    )
    # Stored computes run as superuser (compute_sudo follows store), so an
    # inspector without Inventory rights who confirms still updates the lot.
    qms_shade_band = fields.Char(
        string="Shade Band",
        compute="_compute_qms_shade_band",
        store=True,
        help="The band from this roll's latest confirmed fabric inspection; read "
        "with the dye lot.",
    )

    @api.depends("name")
    def _compute_qms_dye_lot(self):
        for lot in self:
            dye_lot, separator, _roll = (lot.name or "").rpartition("-")
            lot.qms_dye_lot = dye_lot if separator else False

    @api.depends(
        "qms_roll_ids.shade_band",
        "qms_roll_ids.inspection_id.state",
        "qms_roll_ids.inspection_id.qms_roll_inspection",
    )
    def _compute_qms_shade_band(self):
        """The band of the latest confirmed roll row that has one.

        Confirmed means a state in INSPECTION_DONE_STATES, whatever the
        verdict: the band describes the roll's colour, not its acceptance.
        Rolls left on an inspection switched to a plain test are ignored, as
        they are in its verdict. A later inspection that left the band empty
        keeps the earlier one.
        """
        for lot in self:
            rolls = lot.qms_roll_ids.filtered(
                lambda roll: roll.shade_band
                and roll.inspection_id.qms_roll_inspection
                and roll.inspection_id.state in INSPECTION_DONE_STATES
            )
            latest = rolls.sorted(lambda roll: (roll.inspection_id.id, roll.id))[-1:]
            lot.qms_shade_band = latest.shade_band or False
