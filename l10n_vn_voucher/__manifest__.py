# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Printed Vouchers",
    "summary": "Shared A4 layout of the Vietnamese printed vouchers: header, title box, "
    "copies, amount in words, signatures",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "countries": ["vn"],
    "depends": [
        "account",
    ],
    "external_dependencies": {"python": ["num2words"]},
    "data": [
        "data/report_paperformat.xml",
        "report/l10n_vn_voucher_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "l10n_vn_voucher/static/src/scss/l10n_vn_voucher.scss",
        ],
    },
    "installable": True,
}
