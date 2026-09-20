peter@odoo:~/Odoo-Build/addons/docs$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_catalog --stop-after-init --no-http; echo "exit=$?"
2026-09-20 10:38:08,843 138654 INFO ? odoo: Odoo version 18.0.20260817
2026-09-20 10:38:08,844 138654 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-20 10:38:08,844 138654 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', '/opt/odoo/venv/lib/python3.12/site-packages/odoo/addons', '/var/lib/odoo/addons/18.0', '/opt/odoo/addons', '/mnt/extra-addons', '/var/lib/odoo/git/github.com/Mint-System/Odoo-Apps-Server-Tools', '/var/lib/odoo/git/github.com/OCA/account-budgeting', '/var/lib/odoo/git/github.com/OCA/account-financial-reporting', '/var/lib/odoo/git/github.com/OCA/account-financial-tools', '/var/lib/odoo/git/github.com/OCA/account-invoicing', '/var/lib/odoo/git/github.com/OCA/account-payment', '/var/lib/odoo/git/github.com/OCA/account-reconcile', '/var/lib/odoo/git/github.com/OCA/bank-payment', '/var/lib/odoo/git/github.com/OCA/bank-statement-import', '/var/lib/odoo/git/github.com/OCA/commission', '/var/lib/odoo/git/github.com/OCA/contract', '/var/lib/odoo/git/github.com/OCA/credit-control', '/var/lib/odoo/git/github.com/OCA/hr', '/var/lib/odoo/git/github.com/OCA/knowledge', '/var/lib/odoo/git/github.com/OCA/maintenance', '/var/lib/odoo/git/github.com/OCA/management-system', '/var/lib/odoo/git/github.com/OCA/manufacture', '/var/lib/odoo/git/github.com/OCA/mis-builder', '/var/lib/odoo/git/github.com/OCA/multi-company', '/var/lib/odoo/git/github.com/OCA/payroll', '/var/lib/odoo/git/github.com/OCA/product-attribute', '/var/lib/odoo/git/github.com/OCA/product-variant', '/var/lib/odoo/git/github.com/OCA/purchase-workflow', '/var/lib/odoo/git/github.com/OCA/reporting-engine', '/var/lib/odoo/git/github.com/OCA/server-auth', '/var/lib/odoo/git/github.com/OCA/server-backend', '/var/lib/odoo/git/github.com/OCA/server-tools', '/var/lib/odoo/git/github.com/OCA/server-ux', '/var/lib/odoo/git/github.com/OCA/stock-logistics-orderpoint', '/var/lib/odoo/git/github.com/OCA/stock-logistics-warehouse', '/var/lib/odoo/git/github.com/OCA/stock-logistics-workflow', '/var/lib/odoo/git/github.com/OCA/web', '/var/lib/odoo/git/management-system']
2026-09-20 10:38:08,844 138654 INFO ? odoo: database: odoo@db:5432
2026-09-20 10:38:09,078 138654 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-20 10:38:09,094 138654 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-20 10:38:09,529 138654 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-20 10:38:09,551 138654 INFO odoo odoo.modules.loading: 1 modules loaded in 0.02s, 0 queries (+0 extra)
2026-09-20 10:38:09,601 138654 INFO odoo odoo.modules.loading: updating modules list
2026-09-20 10:38:09,607 138654 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-20 10:38:23,419 138654 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Catalog'] to user __system__ #1 via n/a
2026-09-20 10:38:23,420 138654 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Catalog'] to user __system__ #1 via n/a
2026-09-20 10:38:32,572 138654 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-20 10:38:32,696 138654 INFO odoo odoo.modules.loading: loading 306 modules...
2026-09-20 10:38:33,815 138654 INFO odoo odoo.modules.loading: Loading module qms_catalog (82/306)
2026-09-20 10:38:34,216 138654 INFO odoo odoo.modules.registry: module qms_catalog: creating or updating database tables
2026-09-20 10:38:34,561 138654 INFO odoo odoo.modules.loading: loading qms_catalog/security/ir.model.access.csv
2026-09-20 10:38:35,261 138654 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_defect_code_views.xml
2026-09-20 10:38:35,359 138654 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_object_part_views.xml
2026-09-20 10:38:35,412 138654 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_catalog_profile_views.xml
2026-09-20 10:38:35,455 138654 INFO odoo odoo.modules.loading: loading qms_catalog/views/product_views.xml
2026-09-20 10:38:35,519 138654 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_catalog_menus.xml
2026-09-20 10:38:35,578 138654 INFO odoo odoo.addons.base.models.ir_module: module qms_catalog: no translation for language vi_VN
2026-09-20 10:38:35,624 138654 INFO odoo odoo.modules.loading: Module qms_catalog loaded in 1.81s, 292 queries (+292 other)
2026-09-20 10:38:36,590 138654 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
  File "/opt/odoo/venv/bin/odoo", line 8, in <module>
    odoo.cli.main()
  File "/opt/odoo/odoo/cli/command.py", line 76, in main
    o.run(args)
  File "/opt/odoo/odoo/cli/server.py", line 182, in run
    main(args)
  File "/opt/odoo/odoo/cli/server.py", line 175, in main
    rc = odoo.service.server.start(preload=preload, stop=stop)
  File "/opt/odoo/odoo/service/server.py", line 1510, in start
    rc = server.run(preload, stop)
  File "/opt/odoo/odoo/service/server.py", line 1037, in run
    rc = preload_registries(preload)
  File "/opt/odoo/odoo/service/server.py", line 1414, in preload_registries
    registry = Registry.new(dbname, update_module=update_module)
  File "/opt/odoo/venv/lib/python3.12/site-packages/decorator.py", line 232, in fun
    return caller(func, *(extras + args), **kw)
  File "/opt/odoo/odoo/tools/func.py", line 97, in locked
    return func(inst, *args, **kwargs)
  File "/opt/odoo/odoo/modules/registry.py", line 118, in new
    odoo.modules.load_modules(registry, force_demo, status, update_module)
  File "/opt/odoo/odoo/modules/loading.py", line 485, in load_modules
    processed_modules += load_marked_modules(env, graph,
  File "/opt/odoo/odoo/modules/loading.py", line 365, in load_marked_modules
    loaded, processed = load_module_graph(
  File "/opt/odoo/odoo/modules/loading.py", line 186, in load_module_graph
    load_openerp_module(package.name)
  File "/opt/odoo/odoo/modules/module.py", line 384, in load_openerp_module
    __import__(qualname)
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/__init__.py", line 3, in <module>
    from . import models
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/__init__.py", line 5, in <module>
    from . import kpi_threshold
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/kpi_threshold.py", line 8, in <module>
    class KPIThreshold(models.Model):
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/kpi_threshold.py", line 59, in KPIThreshold
    @api.model
  File "/opt/odoo/odoo/api.py", line 431, in model
    return model_create_single(method)
  File "/opt/odoo/odoo/api.py", line 484, in model_create_single
    warnings.warn(

2026-09-20 10:38:37,721 138654 INFO odoo odoo.modules.loading: 306 modules loaded in 5.02s, 292 queries (+292 extra)
2026-09-20 10:38:40,761 138654 INFO odoo odoo.modules.registry: verifying fields for every extended model
2026-09-20 10:38:46,268 138654 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-20 10:38:46,301 138654 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-20 10:38:46,316 138654 INFO odoo odoo.modules.registry: Registry loaded in 36.908s
2026-09-20 10:38:46,317 138654 INFO odoo odoo.service.server: Stopping gracefully
exit=0
peter@odoo:~/Odoo-Build/addons/docs$ docker exec db psql -U odoo -d odoo -c "select m.model, f.name from ir_model_fields f join ir_model m on m.id=f.model_id join ir_model_fields_group_rel r on r.field_id=f.id where f.name='qms_profile_ids'"
 model | name
-------+------
(0 rows)

peter@odoo:~/Odoo-Build/addons/docs$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_catalog \
  --test-enable --test-tags /qms_catalog --stop-after-init --no-http; echo "exit=$?"
2026-09-20 10:39:07,150 138704 INFO ? odoo: Odoo version 18.0.20260817
2026-09-20 10:39:07,150 138704 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-20 10:39:07,150 138704 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', '/opt/odoo/venv/lib/python3.12/site-packages/odoo/addons', '/var/lib/odoo/addons/18.0', '/opt/odoo/addons', '/mnt/extra-addons', '/var/lib/odoo/git/github.com/Mint-System/Odoo-Apps-Server-Tools', '/var/lib/odoo/git/github.com/OCA/account-budgeting', '/var/lib/odoo/git/github.com/OCA/account-financial-reporting', '/var/lib/odoo/git/github.com/OCA/account-financial-tools', '/var/lib/odoo/git/github.com/OCA/account-invoicing', '/var/lib/odoo/git/github.com/OCA/account-payment', '/var/lib/odoo/git/github.com/OCA/account-reconcile', '/var/lib/odoo/git/github.com/OCA/bank-payment', '/var/lib/odoo/git/github.com/OCA/bank-statement-import', '/var/lib/odoo/git/github.com/OCA/commission', '/var/lib/odoo/git/github.com/OCA/contract', '/var/lib/odoo/git/github.com/OCA/credit-control', '/var/lib/odoo/git/github.com/OCA/hr', '/var/lib/odoo/git/github.com/OCA/knowledge', '/var/lib/odoo/git/github.com/OCA/maintenance', '/var/lib/odoo/git/github.com/OCA/management-system', '/var/lib/odoo/git/github.com/OCA/manufacture', '/var/lib/odoo/git/github.com/OCA/mis-builder', '/var/lib/odoo/git/github.com/OCA/multi-company', '/var/lib/odoo/git/github.com/OCA/payroll', '/var/lib/odoo/git/github.com/OCA/product-attribute', '/var/lib/odoo/git/github.com/OCA/product-variant', '/var/lib/odoo/git/github.com/OCA/purchase-workflow', '/var/lib/odoo/git/github.com/OCA/reporting-engine', '/var/lib/odoo/git/github.com/OCA/server-auth', '/var/lib/odoo/git/github.com/OCA/server-backend', '/var/lib/odoo/git/github.com/OCA/server-tools', '/var/lib/odoo/git/github.com/OCA/server-ux', '/var/lib/odoo/git/github.com/OCA/stock-logistics-orderpoint', '/var/lib/odoo/git/github.com/OCA/stock-logistics-warehouse', '/var/lib/odoo/git/github.com/OCA/stock-logistics-workflow', '/var/lib/odoo/git/github.com/OCA/web', '/var/lib/odoo/git/management-system']
2026-09-20 10:39:07,151 138704 INFO ? odoo: database: odoo@db:5432
2026-09-20 10:39:07,414 138704 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-20 10:39:07,427 138704 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-20 10:39:07,774 138704 WARNING ? odoo.service.server: Unit testing in workers mode could fail; use --workers 0.
2026-09-20 10:39:07,821 138704 INFO odoo odoo.tests.common: Importing test framework
2026-09-20 10:39:07,914 138704 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-20 10:39:07,929 138704 INFO odoo odoo.modules.loading: 1 modules loaded in 0.01s, 0 queries (+0 extra)
2026-09-20 10:39:07,986 138704 INFO odoo odoo.modules.loading: updating modules list
2026-09-20 10:39:07,995 138704 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-20 10:39:19,897 138704 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Catalog'] to user __system__ #1 via n/a
2026-09-20 10:39:19,897 138704 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Catalog'] to user __system__ #1 via n/a
2026-09-20 10:39:28,645 138704 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-20 10:39:28,761 138704 INFO odoo odoo.modules.loading: loading 306 modules...
2026-09-20 10:39:29,643 138704 INFO odoo odoo.modules.loading: Loading module qms_catalog (82/306)
2026-09-20 10:39:30,025 138704 INFO odoo odoo.modules.registry: module qms_catalog: creating or updating database tables
2026-09-20 10:39:30,386 138704 INFO odoo odoo.modules.loading: loading qms_catalog/security/ir.model.access.csv
2026-09-20 10:39:31,150 138704 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_defect_code_views.xml
2026-09-20 10:39:31,216 138704 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_object_part_views.xml
2026-09-20 10:39:31,252 138704 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_catalog_profile_views.xml
2026-09-20 10:39:31,290 138704 INFO odoo odoo.modules.loading: loading qms_catalog/views/product_views.xml
2026-09-20 10:39:31,359 138704 INFO odoo odoo.modules.loading: loading qms_catalog/views/qms_catalog_menus.xml
2026-09-20 10:39:31,416 138704 INFO odoo odoo.addons.base.models.ir_module: module qms_catalog: no translation for language vi_VN
2026-09-20 10:39:31,490 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_depth_code_under_code ...
2026-09-20 10:39:31,501 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_depth_group_with_codes ...
2026-09-20 10:39:31,523 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_depth_self_parent ...
2026-09-20 10:39:31,556 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_display_name ...
2026-09-20 10:39:31,564 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_domain_kind_both_group ...
2026-09-20 10:39:31,597 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_domain_kind_group_narrowed ...
2026-09-20 10:39:31,622 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_domain_kind_mismatch ...
2026-09-20 10:39:31,648 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_name_search_ref_code ...
2026-09-20 10:39:31,657 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_ref_code_required ...
2026-09-20 10:39:31,671 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsDefectCode.test_ref_code_unique ...
2026-09-20 10:39:31,930 138704 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-20 10:39:31,969 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_depth_code_under_code ...
2026-09-20 10:39:31,982 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_depth_group_with_codes ...
2026-09-20 10:39:32,018 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_depth_self_parent ...
2026-09-20 10:39:32,042 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_display_name ...
2026-09-20 10:39:32,050 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_domain_kind_both_group ...
2026-09-20 10:39:32,072 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_domain_kind_group_narrowed ...
2026-09-20 10:39:32,087 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_domain_kind_mismatch ...
2026-09-20 10:39:32,108 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_name_search_ref_code ...
2026-09-20 10:39:32,118 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_ref_code_required ...
2026-09-20 10:39:32,128 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestQmsObjectPart.test_ref_code_unique ...
2026-09-20 10:39:32,354 138704 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-20 10:39:32,359 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog: Starting TestCatalogIndependence.test_ref_code_shared_across_catalogs ...
2026-09-20 10:39:32,643 138704 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-20 10:39:32,882 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_category_ancestor_invalidation ...
2026-09-20 10:39:32,947 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_category_chain ...
2026-09-20 10:39:32,974 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_product_effective ...
2026-09-20 10:39:33,016 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_product_without_assignment ...
2026-09-20 10:39:33,041 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_profile_inverse_assignment ...
2026-09-20 10:39:33,067 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_assignment: Starting TestCatalogAssignment.test_template_effective ...
2026-09-20 10:39:33,341 138704 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-20 10:39:33,394 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_defect_code_rejected ...
2026-09-20 10:39:33,405 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_domain_kind_both_accepted ...
2026-09-20 10:39:33,430 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_domain_kind_clash ...
2026-09-20 10:39:33,461 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_domain_kind_profile_narrowed ...
2026-09-20 10:39:33,488 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_groups_accepted ...
2026-09-20 10:39:33,520 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_object_part_code_rejected ...
2026-09-20 10:39:33,545 138704 INFO odoo odoo.addons.qms_catalog.tests.test_qms_catalog_profile: Starting TestCatalogProfile.test_profile_ids_inverse ...
2026-09-20 10:39:33,791 138704 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-20 10:39:33,833 138704 INFO odoo odoo.modules.loading: Module qms_catalog loaded in 4.19s (incl. 2.36s test), 292 queries (+524 test, +292 other)
2026-09-20 10:39:34,732 138704 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
  File "/opt/odoo/venv/bin/odoo", line 8, in <module>
    odoo.cli.main()
  File "/opt/odoo/odoo/cli/command.py", line 76, in main
    o.run(args)
  File "/opt/odoo/odoo/cli/server.py", line 182, in run
    main(args)
  File "/opt/odoo/odoo/cli/server.py", line 175, in main
    rc = odoo.service.server.start(preload=preload, stop=stop)
  File "/opt/odoo/odoo/service/server.py", line 1510, in start
    rc = server.run(preload, stop)
  File "/opt/odoo/odoo/service/server.py", line 1037, in run
    rc = preload_registries(preload)
  File "/opt/odoo/odoo/service/server.py", line 1414, in preload_registries
    registry = Registry.new(dbname, update_module=update_module)
  File "/opt/odoo/venv/lib/python3.12/site-packages/decorator.py", line 232, in fun
    return caller(func, *(extras + args), **kw)
  File "/opt/odoo/odoo/tools/func.py", line 97, in locked
    return func(inst, *args, **kwargs)
  File "/opt/odoo/odoo/modules/registry.py", line 118, in new
    odoo.modules.load_modules(registry, force_demo, status, update_module)
  File "/opt/odoo/odoo/modules/loading.py", line 485, in load_modules
    processed_modules += load_marked_modules(env, graph,
  File "/opt/odoo/odoo/modules/loading.py", line 365, in load_marked_modules
    loaded, processed = load_module_graph(
  File "/opt/odoo/odoo/modules/loading.py", line 186, in load_module_graph
    load_openerp_module(package.name)
  File "/opt/odoo/odoo/modules/module.py", line 384, in load_openerp_module
    __import__(qualname)
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/__init__.py", line 3, in <module>
    from . import models
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/__init__.py", line 5, in <module>
    from . import kpi_threshold
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/kpi_threshold.py", line 8, in <module>
    class KPIThreshold(models.Model):
  File "/var/lib/odoo/git/github.com/OCA/reporting-engine/kpi/models/kpi_threshold.py", line 59, in KPIThreshold
    @api.model
  File "/opt/odoo/odoo/api.py", line 431, in model
    return model_create_single(method)
  File "/opt/odoo/odoo/api.py", line 484, in model_create_single
    warnings.warn(

2026-09-20 10:39:35,672 138704 INFO odoo odoo.modules.loading: 306 modules loaded in 6.91s, 292 queries (+816 extra)
2026-09-20 10:39:38,777 138704 INFO odoo odoo.modules.registry: verifying fields for every extended model
2026-09-20 10:39:44,387 138704 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-20 10:39:44,426 138704 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-20 10:39:44,428 138704 INFO odoo odoo.modules.registry: Registry loaded in 36.653s
2026-09-20 10:39:44,428 138704 INFO odoo odoo.service.server: Starting post tests
2026-09-20 10:39:44,430 138704 INFO odoo odoo.service.server: 0 post-tests in 0.00s, 0 queries
2026-09-20 10:39:44,430 138704 INFO odoo odoo.tests.stats: qms_catalog: 44 tests 2.34s 524 queries
2026-09-20 10:39:44,430 138704 INFO odoo odoo.service.server: Stopping gracefully
exit=0
peter@odoo:~/Odoo-Build/addons/docs$ rm Step_6_Result.md
peter@odoo:~/Odoo-Build/addons/docs$

