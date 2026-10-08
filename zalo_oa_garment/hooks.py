# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The rules that name maintenance_sla_garment's stages.

Seeding must be safe to fail: a data record naming a stage a site has removed
would raise at install. So these rules are created here, skipping what cannot
be found, and each is registered under this module's XML id with noupdate: a
second run finds it and skips it, and an upgrade leaves a tuned rule alone.
"""

MODULE = "zalo_oa_garment"

# Rule XML id, action XML id, template XML id, the rule's name, the stages'
# XML ids.
STAGE_RULES = [
    (
        "rule_request_paused",
        "action_request_paused",
        "template_request_paused",
        "Maintenance request paused",
        [
            "maintenance_sla_garment.stage_waiting_parts",
            "maintenance_sla_garment.stage_waiting_production",
        ],
    ),
    (
        "rule_request_restored",
        "action_request_restored",
        "template_request_restored",
        "Maintenance request restored",
        ["maintenance_sla_garment.stage_restored"],
    ),
]


def post_init_hook(env):
    _create_stage_rules(env)


def _create_stage_rules(env):
    """Rules on corrective requests reaching the named stages.

    A rule is skipped when its XML id already resolves, when its template is
    missing, or when none of its stages can be found.
    """
    model = env["ir.model"]._get("maintenance.request")
    stage_field = env.ref("maintenance.field_maintenance_request__stage_id")
    for rule_xmlid, action_xmlid, template_xmlid, name, stage_xmlids in STAGE_RULES:
        if env.ref(f"{MODULE}.{rule_xmlid}", raise_if_not_found=False):
            continue
        template = env.ref(f"{MODULE}.{template_xmlid}", raise_if_not_found=False)
        stages = [env.ref(xmlid, raise_if_not_found=False) for xmlid in stage_xmlids]
        stage_ids = [stage.id for stage in stages if stage]
        if not template or not stage_ids:
            continue
        rule = env["base.automation"].create(
            {
                "name": name,
                "model_id": model.id,
                "trigger": "on_create_or_write",
                "trigger_field_ids": [(6, 0, stage_field.ids)],
                "filter_domain": repr(
                    [
                        ("maintenance_type", "=", "corrective"),
                        ("stage_id", "in", stage_ids),
                    ]
                ),
            }
        )
        action = env["ir.actions.server"].create(
            {
                "name": name,
                "model_id": model.id,
                "state": "zalo",
                "usage": "base_automation",
                "base_automation_id": rule.id,
                "zalo_template_id": template.id,
            }
        )
        env["ir.model.data"].create(
            [
                {
                    "module": MODULE,
                    "name": rule_xmlid,
                    "model": "base.automation",
                    "res_id": rule.id,
                    "noupdate": True,
                },
                {
                    "module": MODULE,
                    "name": action_xmlid,
                    "model": "ir.actions.server",
                    "res_id": action.id,
                    "noupdate": True,
                },
            ]
        )
