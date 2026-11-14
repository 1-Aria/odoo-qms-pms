# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Material Ownership",
    "summary": "Materials owned per vendor bill and e-invoice; transfer batches of "
    "sales orders invoiced by the former owner",
    "version": "18.0.1.2.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Sales/Sales",
    "depends": ["sale_stock", "mrp", "purchase_stock", "l10n_vn_einvoice"],
    "data": [
        "security/ir.model.access.csv",
        "security/sale_material_ownership_security.xml",
        "data/ir_sequence_data.xml",
        "views/sale_material_batch_views.xml",
        "views/sale_material_ownership_balance_views.xml",
        "views/sale_order_views.xml",
        "views/product_category_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/stock_picking_views.xml",
        "report/sale_material_batch_templates.xml",
        "report/sale_material_batch_reports.xml",
    ],
    "installable": True,
}
