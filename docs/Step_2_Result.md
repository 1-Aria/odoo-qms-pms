peter@odoo:~/Odoo-Build/addons$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_nonconformity --stop-after-init --no-http; echo "exit=$?"
2026-09-21 03:38:00,334 181228 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 03:38:00,338 181228 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 03:38:00,338 181228 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 03:38:00,339 181228 INFO ? odoo: database: odoo@db:5432
2026-09-21 03:38:00,634 181228 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 03:38:00,653 181228 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 03:38:01,019 181228 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 03:38:01,035 181228 INFO odoo odoo.modules.loading: 1 modules loaded in 0.02s, 0 queries (+0 extra)
2026-09-21 03:38:01,102 181228 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 03:38:01,108 181228 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 03:38:14,625 181228 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:38:14,625 181228 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:38:24,381 181228 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-21 03:38:24,512 181228 INFO odoo odoo.modules.loading: loading 307 modules...
2026-09-21 03:38:26,505 181228 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch

2026-09-21 03:38:26,944 181228 INFO odoo odoo.modules.loading: Loading module qms_nonconformity (227/307)
2026-09-21 03:38:28,384 181228 INFO odoo odoo.modules.registry: module qms_nonconformity: creating or updating database tables
2026-09-21 03:38:28,702 181228 INFO odoo odoo.modules.loading: loading qms_nonconformity/security/ir.model.access.csv
2026-09-21 03:38:29,382 181228 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/qms_nonconformity_item_views.xml
2026-09-21 03:38:29,441 181228 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/mgmtsystem_nonconformity_views.xml
2026-09-21 03:38:29,514 181228 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity: no translation for language vi_VN
2026-09-21 03:38:29,562 181228 INFO odoo odoo.modules.loading: Module qms_nonconformity loaded in 2.62s, 138 queries (+138 other)
2026-09-21 03:38:30,171 181228 INFO odoo odoo.modules.loading: 307 modules loaded in 5.66s, 138 queries (+138 extra)
2026-09-21 03:38:38,917 181228 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 03:38:38,956 181228 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 03:38:38,958 181228 INFO odoo odoo.modules.registry: Registry loaded in 38.026s
2026-09-21 03:38:38,959 181228 INFO odoo odoo.service.server: Stopping gracefully
exit=0
peter@odoo:~/Odoo-Build/addons$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -i qms_nonconformity_hr --stop-after-init --no-http; echo "exit=$?"
docker logs --since 3m odoo 2>&1 | grep -E "ERROR|WARNING|Traceback" -A8
2026-09-21 03:39:01,951 181278 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 03:39:01,953 181278 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 03:39:01,953 181278 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 03:39:01,953 181278 INFO ? odoo: database: odoo@db:5432
2026-09-21 03:39:02,302 181278 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 03:39:02,319 181278 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 03:39:02,889 181278 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 03:39:02,921 181278 INFO odoo odoo.modules.loading: 1 modules loaded in 0.03s, 0 queries (+0 extra)
2026-09-21 03:39:02,982 181278 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 03:39:02,995 181278 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 03:39:16,673 181278 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on ['QMS Nonconformity HR'] to user __system__ #1 via n/a
2026-09-21 03:39:16,956 181278 INFO odoo odoo.modules.loading: loading 307 modules...
2026-09-21 03:39:19,075 181278 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
2026-09-21 03:39:20,057 181278 INFO odoo odoo.modules.loading: 307 modules loaded in 3.10s, 0 queries (+0 extra)
2026-09-21 03:39:20,069 181278 INFO odoo odoo.modules.loading: loading 308 modules...
2026-09-21 03:39:20,070 181278 INFO odoo odoo.modules.loading: Loading module qms_nonconformity_hr (260/308)
2026-09-21 03:39:21,105 181278 INFO odoo odoo.modules.registry: module qms_nonconformity_hr: creating or updating database tables
2026-09-21 03:39:21,265 181278 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity_hr: no translation for language vi_VN
2026-09-21 03:39:21,420 181278 INFO odoo odoo.modules.loading: Module qms_nonconformity_hr loaded in 1.35s, 54 queries (+54 other)
2026-09-21 03:39:21,420 181278 INFO odoo odoo.modules.loading: 308 modules loaded in 1.35s, 54 queries (+54 extra)
2026-09-21 03:39:29,312 181278 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 03:39:29,357 181278 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 03:39:29,359 181278 INFO odoo odoo.modules.registry: Registry loaded in 26.571s
2026-09-21 03:39:29,360 181278 INFO odoo odoo.service.server: Stopping gracefully
exit=0
peter@odoo:~/Odoo-Build/addons$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_nonconformity \
  --test-enable --test-tags /qms_nonconformity --stop-after-init --no-http; echo "exit=$?"
2026-09-21 03:41:53,898 181403 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 03:41:53,899 181403 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 03:41:53,899 181403 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 03:41:53,901 181403 INFO ? odoo: database: odoo@db:5432
2026-09-21 03:41:54,144 181403 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 03:41:54,158 181403 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 03:41:54,508 181403 WARNING ? odoo.service.server: Unit testing in workers mode could fail; use --workers 0.
2026-09-21 03:41:54,545 181403 INFO odoo odoo.tests.common: Importing test framework
2026-09-21 03:41:54,655 181403 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 03:41:54,670 181403 INFO odoo odoo.modules.loading: 1 modules loaded in 0.01s, 0 queries (+0 extra)
2026-09-21 03:41:54,763 181403 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 03:41:54,773 181403 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 03:42:09,403 181403 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:42:09,403 181403 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:42:18,680 181403 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-21 03:42:18,808 181403 INFO odoo odoo.modules.loading: loading 308 modules...
2026-09-21 03:42:20,920 181403 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
2026-09-21 03:42:21,378 181403 INFO odoo odoo.modules.loading: Loading module qms_nonconformity (227/308)
2026-09-21 03:42:22,680 181403 INFO odoo odoo.modules.registry: module qms_nonconformity: creating or updating database tables
2026-09-21 03:42:22,943 181403 INFO odoo odoo.modules.loading: loading qms_nonconformity/security/ir.model.access.csv
2026-09-21 03:42:23,738 181403 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/qms_nonconformity_item_views.xml
2026-09-21 03:42:23,800 181403 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/mgmtsystem_nonconformity_views.xml
2026-09-21 03:42:23,858 181403 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity: no translation for language vi_VN
2026-09-21 03:42:23,903 181403 INFO odoo odoo.modules.loading: Module qms_nonconformity loaded in 2.53s, 124 queries (+124 other)
2026-09-21 03:42:24,062 181403 INFO odoo odoo.modules.loading: Loading module qms_nonconformity_hr (260/308)
2026-09-21 03:42:25,288 181403 INFO odoo odoo.modules.registry: module qms_nonconformity_hr: creating or updating database tables
2026-09-21 03:42:25,699 181403 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity_hr: no translation for language vi_VN
2026-09-21 03:42:25,733 181403 INFO odoo odoo.modules.loading: Module qms_nonconformity_hr loaded in 1.67s, 58 queries (+58 other)
2026-09-21 03:42:25,945 181403 INFO odoo odoo.modules.loading: 308 modules loaded in 7.14s, 182 queries (+182 extra)
2026-09-21 03:42:33,932 181403 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 03:42:33,971 181403 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 03:42:33,973 181403 INFO odoo odoo.modules.registry: Registry loaded in 39.465s
2026-09-21 03:42:33,974 181403 INFO odoo odoo.service.server: Starting post tests
2026-09-21 03:42:33,987 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_from_employee ...
2026-09-21 03:42:35,438 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_without_employee ...
2026-09-21 03:42:35,900 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_responsible_is_current_user ...
2026-09-21 03:42:35,923 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_disposition_tracked ...
2026-09-21 03:42:36,034 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: ======================================================================
2026-09-21 03:42:36,034 181403 ERROR odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: FAIL: TestNonconformityHeader.test_disposition_tracked
Traceback (most recent call last):
  File "/mnt/extra-addons/qms_nonconformity/tests/test_qms_nonconformity_header.py", line 76, in test_disposition_tracked
    self.assertGreater(len(nonconformity.message_ids), before)
AssertionError: 1 not greater than 1

2026-09-21 03:42:36,049 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_partner_optional ...
2026-09-21 03:42:36,139 181403 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 3 checked, 3 removed
2026-09-21 03:42:36,408 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_defect_code_restrict ...
2026-09-21 03:42:36,452 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_object_parts ...
2026-09-21 03:42:36,487 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_profile_codes ...
2026-09-21 03:42:36,526 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_without_product ...
2026-09-21 03:42:36,617 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_effective_profiles_related ...
2026-09-21 03:42:36,644 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_cascade ...
2026-09-21 03:42:36,738 181403 INFO odoo odoo.models.unlink: User #1 deleted mail.message records with IDs: [53061]
2026-09-21 03:42:36,747 181403 INFO odoo odoo.models.unlink: User #1 deleted mgmtsystem.nonconformity records with IDs: [10]
2026-09-21 03:42:36,765 181403 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_created ...
2026-09-21 03:42:36,798 181403 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-21 03:42:36,800 181403 INFO odoo odoo.service.server: 12 post-tests in 2.83s, 957 queries
2026-09-21 03:42:36,800 181403 INFO odoo odoo.tests.stats: qms_nonconformity: 16 tests 2.82s 957 queries
2026-09-21 03:42:36,800 181403 INFO odoo odoo.service.server: Stopping gracefully
exit=1
peter@odoo:~/Odoo-Build/addons$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_nonconformity_hr \
  --test-enable --test-tags /qms_nonconformity_hr --stop-after-init --no-http; echo "exit=$?"
2026-09-21 03:42:48,585 181447 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 03:42:48,585 181447 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 03:42:48,585 181447 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 03:42:48,587 181447 INFO ? odoo: database: odoo@db:5432
2026-09-21 03:42:48,839 181447 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 03:42:48,854 181447 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 03:42:49,197 181447 WARNING ? odoo.service.server: Unit testing in workers mode could fail; use --workers 0.
2026-09-21 03:42:49,242 181447 INFO odoo odoo.tests.common: Importing test framework
2026-09-21 03:42:49,399 181447 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 03:42:49,415 181447 INFO odoo odoo.modules.loading: 1 modules loaded in 0.02s, 0 queries (+0 extra)
2026-09-21 03:42:49,471 181447 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 03:42:49,479 181447 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 03:43:04,788 181447 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Nonconformity HR'] to user __system__ #1 via n/a
2026-09-21 03:43:04,789 181447 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Nonconformity HR'] to user __system__ #1 via n/a
2026-09-21 03:43:16,457 181447 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-21 03:43:16,621 181447 INFO odoo odoo.modules.loading: loading 308 modules...
2026-09-21 03:43:18,778 181447 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
2026-09-21 03:43:19,491 181447 INFO odoo odoo.modules.loading: Loading module qms_nonconformity_hr (260/308)
2026-09-21 03:43:21,073 181447 INFO odoo odoo.modules.registry: module qms_nonconformity_hr: creating or updating database tables
2026-09-21 03:43:21,355 181447 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity_hr: no translation for language vi_VN
2026-09-21 03:43:21,402 181447 INFO odoo odoo.modules.loading: Module qms_nonconformity_hr loaded in 1.91s, 57 queries (+57 other)
2026-09-21 03:43:21,706 181447 INFO odoo odoo.modules.loading: 308 modules loaded in 5.09s, 57 queries (+57 extra)
2026-09-21 03:43:30,772 181447 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 03:43:30,800 181447 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 03:43:30,802 181447 INFO odoo odoo.modules.registry: Registry loaded in 41.604s
2026-09-21 03:43:30,802 181447 INFO odoo odoo.service.server: Starting post tests
2026-09-21 03:43:30,875 181447 INFO odoo odoo.addons.qms_nonconformity_hr.tests.test_qms_nonconformity_hr: Starting TestNonconformityDepartment.test_default_department_from_employee ...
2026-09-21 03:43:31,494 181447 INFO odoo odoo.addons.qms_nonconformity_hr.tests.test_qms_nonconformity_hr: Starting TestNonconformityDepartment.test_default_department_without_employee ...
2026-09-21 03:43:32,085 181447 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 2 checked, 2 removed
2026-09-21 03:43:32,088 181447 INFO odoo odoo.service.server: 2 post-tests in 1.29s, 410 queries
2026-09-21 03:43:32,088 181447 INFO odoo odoo.tests.stats: qms_nonconformity_hr: 4 tests 1.28s 410 queries
2026-09-21 03:43:32,089 181447 INFO odoo odoo.service.server: Stopping gracefully
exit=0
peter@odoo:~/Odoo-Build/addons$
peter@odoo:~/Odoo-Build/addons/docs$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_nonconformity \
  --test-enable --test-tags /qms_nonconformity --stop-after-init --no-http; echo "exit=$?"
2026-09-21 03:52:58,636 181967 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 03:52:58,636 181967 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 03:52:58,636 181967 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 03:52:58,637 181967 INFO ? odoo: database: odoo@db:5432
2026-09-21 03:52:58,858 181967 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 03:52:58,870 181967 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 03:52:59,150 181967 WARNING ? odoo.service.server: Unit testing in workers mode could fail; use --workers 0.
2026-09-21 03:52:59,183 181967 INFO odoo odoo.tests.common: Importing test framework
2026-09-21 03:52:59,286 181967 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 03:52:59,298 181967 INFO odoo odoo.modules.loading: 1 modules loaded in 0.01s, 0 queries (+0 extra)
2026-09-21 03:52:59,375 181967 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 03:52:59,381 181967 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 03:53:14,534 181967 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:53:14,534 181967 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 03:53:25,521 181967 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-21 03:53:25,642 181967 INFO odoo odoo.modules.loading: loading 308 modules...
2026-09-21 03:53:27,735 181967 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
2026-09-21 03:53:28,169 181967 INFO odoo odoo.modules.loading: Loading module qms_nonconformity (227/308)
2026-09-21 03:53:29,546 181967 INFO odoo odoo.modules.registry: module qms_nonconformity: creating or updating database tables
2026-09-21 03:53:29,778 181967 INFO odoo odoo.modules.loading: loading qms_nonconformity/security/ir.model.access.csv
2026-09-21 03:53:30,550 181967 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/qms_nonconformity_item_views.xml
2026-09-21 03:53:30,629 181967 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/mgmtsystem_nonconformity_views.xml
2026-09-21 03:53:30,715 181967 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity: no translation for language vi_VN
2026-09-21 03:53:30,777 181967 INFO odoo odoo.modules.loading: Module qms_nonconformity loaded in 2.61s, 123 queries (+123 other)
2026-09-21 03:53:30,972 181967 INFO odoo odoo.modules.loading: Loading module qms_nonconformity_hr (260/308)
2026-09-21 03:53:32,146 181967 INFO odoo odoo.modules.registry: module qms_nonconformity_hr: creating or updating database tables
2026-09-21 03:53:32,563 181967 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity_hr: no translation for language vi_VN
2026-09-21 03:53:32,606 181967 INFO odoo odoo.modules.loading: Module qms_nonconformity_hr loaded in 1.63s, 58 queries (+58 other)
2026-09-21 03:53:32,841 181967 INFO odoo odoo.modules.loading: 308 modules loaded in 7.20s, 181 queries (+181 extra)
2026-09-21 03:53:41,654 181967 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 03:53:41,689 181967 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 03:53:41,693 181967 INFO odoo odoo.modules.registry: Registry loaded in 42.542s
2026-09-21 03:53:41,693 181967 INFO odoo odoo.service.server: Starting post tests
2026-09-21 03:53:41,710 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_from_employee ...
2026-09-21 03:53:43,193 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_without_employee ...
2026-09-21 03:53:43,637 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_responsible_is_current_user ...
2026-09-21 03:53:43,660 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_disposition_tracked ...
2026-09-21 03:53:43,745 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: ======================================================================
2026-09-21 03:53:43,745 181967 ERROR odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: FAIL: TestNonconformityHeader.test_disposition_tracked
Traceback (most recent call last):
  File "/mnt/extra-addons/qms_nonconformity/tests/test_qms_nonconformity_header.py", line 81, in test_disposition_tracked
    self.assertGreater(len(nonconformity.message_ids), before)
AssertionError: 1 not greater than 1

2026-09-21 03:53:43,764 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_partner_optional ...
2026-09-21 03:53:43,869 181967 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 3 checked, 3 removed
2026-09-21 03:53:44,221 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_defect_code_restrict ...
2026-09-21 03:53:44,286 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_object_parts ...
2026-09-21 03:53:44,331 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_profile_codes ...
2026-09-21 03:53:44,363 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_without_product ...
2026-09-21 03:53:44,458 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_effective_profiles_related ...
2026-09-21 03:53:44,507 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_cascade ...
2026-09-21 03:53:44,642 181967 INFO odoo odoo.models.unlink: User #1 deleted mail.message records with IDs: [53080]
2026-09-21 03:53:44,653 181967 INFO odoo odoo.models.unlink: User #1 deleted mgmtsystem.nonconformity records with IDs: [15]
2026-09-21 03:53:44,673 181967 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_created ...
2026-09-21 03:53:44,723 181967 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-21 03:53:44,724 181967 INFO odoo odoo.service.server: 12 post-tests in 3.03s, 958 queries
2026-09-21 03:53:44,724 181967 INFO odoo odoo.tests.stats: qms_nonconformity: 16 tests 3.02s 958 queries
2026-09-21 03:53:44,724 181967 INFO odoo odoo.service.server: Stopping gracefully
exit=1
peter@odoo:~/Odoo-Build/addons/docs$
peter@odoo:~/Odoo-Build/addons/docs$ docker exec odoo odoo -c /etc/odoo/odoo.conf -d odoo -u qms_nonconformity \
  --test-enable --test-tags /qms_nonconformity --stop-after-init --no-http; echo "exit=$?"
2026-09-21 04:07:31,409 182662 INFO ? odoo: Odoo version 18.0.20260817
2026-09-21 04:07:31,409 182662 INFO ? odoo: Using configuration file at /etc/odoo/odoo.conf
2026-09-21 04:07:31,409 182662 INFO ? odoo: addons paths: ['/opt/odoo/odoo/addons', 
2026-09-21 04:07:31,410 182662 INFO ? odoo: database: odoo@db:5432
2026-09-21 04:07:31,686 182662 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2026-09-21 04:07:31,708 182662 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2026-09-21 04:07:32,102 182662 WARNING ? odoo.service.server: Unit testing in workers mode could fail; use --workers 0.
2026-09-21 04:07:32,146 182662 INFO odoo odoo.tests.common: Importing test framework
2026-09-21 04:07:32,269 182662 INFO odoo odoo.modules.loading: loading 1 modules...
2026-09-21 04:07:32,281 182662 INFO odoo odoo.modules.loading: 1 modules loaded in 0.01s, 0 queries (+0 extra)
2026-09-21 04:07:32,350 182662 INFO odoo odoo.modules.loading: updating modules list
2026-09-21 04:07:32,355 182662 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-09-21 04:07:48,206 182662 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 04:07:48,206 182662 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['QMS Nonconformity'] to user __system__ #1 via n/a
2026-09-21 04:07:58,993 182662 INFO odoo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-09-21 04:07:59,134 182662 INFO odoo odoo.modules.loading: loading 308 modules...
2026-09-21 04:08:01,215 182662 WARNING odoo py.warnings: /opt/odoo/odoo/api.py:484: DeprecationWarning: The model odoo.addons.kpi.models.kpi_threshold is not overriding the create method in batch
2026-09-21 04:08:01,577 182662 INFO odoo odoo.modules.loading: Loading module qms_nonconformity (227/308)
2026-09-21 04:08:03,055 182662 INFO odoo odoo.modules.registry: module qms_nonconformity: creating or updating database tables
2026-09-21 04:08:03,381 182662 INFO odoo odoo.modules.loading: loading qms_nonconformity/security/ir.model.access.csv
2026-09-21 04:08:04,228 182662 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/qms_nonconformity_item_views.xml
2026-09-21 04:08:04,320 182662 INFO odoo odoo.modules.loading: loading qms_nonconformity/views/mgmtsystem_nonconformity_views.xml
2026-09-21 04:08:04,389 182662 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity: no translation for language vi_VN
2026-09-21 04:08:04,453 182662 INFO odoo odoo.modules.loading: Module qms_nonconformity loaded in 2.88s, 123 queries (+123 other)
2026-09-21 04:08:04,613 182662 INFO odoo odoo.modules.loading: Loading module qms_nonconformity_hr (260/308)
2026-09-21 04:08:05,733 182662 INFO odoo odoo.modules.registry: module qms_nonconformity_hr: creating or updating database tables
2026-09-21 04:08:06,140 182662 INFO odoo odoo.addons.base.models.ir_module: module qms_nonconformity_hr: no translation for language vi_VN
2026-09-21 04:08:06,195 182662 INFO odoo odoo.modules.loading: Module qms_nonconformity_hr loaded in 1.58s, 58 queries (+58 other)
2026-09-21 04:08:06,496 182662 INFO odoo odoo.modules.loading: 308 modules loaded in 7.36s, 181 queries (+181 extra)
2026-09-21 04:08:14,456 182662 INFO odoo odoo.modules.loading: Modules loaded.
2026-09-21 04:08:14,523 182662 INFO odoo odoo.modules.registry: Registry changed, signaling through the database
2026-09-21 04:08:14,526 182662 INFO odoo odoo.modules.registry: Registry loaded in 42.422s
2026-09-21 04:08:14,527 182662 INFO odoo odoo.service.server: Starting post tests
2026-09-21 04:08:14,538 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_from_employee ...
2026-09-21 04:08:16,073 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_manager_without_employee ...
2026-09-21 04:08:16,649 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_default_responsible_is_current_user ...
2026-09-21 04:08:16,668 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_disposition_tracked ...
2026-09-21 04:08:16,813 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_header: Starting TestNonconformityHeader.test_partner_optional ...
2026-09-21 04:08:16,914 182662 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 3 checked, 3 removed
2026-09-21 04:08:17,246 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_defect_code_restrict ...
2026-09-21 04:08:17,322 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_object_parts ...
2026-09-21 04:08:17,373 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_matches_profile_codes ...
2026-09-21 04:08:17,419 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_domain_without_product ...
2026-09-21 04:08:17,541 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_effective_profiles_related ...
2026-09-21 04:08:17,579 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_cascade ...
2026-09-21 04:08:17,714 182662 INFO odoo odoo.models.unlink: User #1 deleted mail.message records with IDs: [53095]
2026-09-21 04:08:17,729 182662 INFO odoo odoo.models.unlink: User #1 deleted mgmtsystem.nonconformity records with IDs: [20]
2026-09-21 04:08:17,756 182662 INFO odoo odoo.addons.qms_nonconformity.tests.test_qms_nonconformity_item: Starting TestNonconformityItem.test_item_created ...
2026-09-21 04:08:17,800 182662 INFO odoo odoo.addons.base.models.ir_attachment: filestore gc 0 checked, 0 removed
2026-09-21 04:08:17,804 182662 INFO odoo odoo.service.server: 12 post-tests in 3.28s, 962 queries
2026-09-21 04:08:17,805 182662 INFO odoo odoo.tests.stats: qms_nonconformity: 16 tests 3.27s 962 queries
2026-09-21 04:08:17,805 182662 INFO odoo odoo.service.server: Stopping gracefully
exit=0
