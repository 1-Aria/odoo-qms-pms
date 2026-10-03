# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The part of the preset that touches records this module does not own.

Seeding must be safe to fail: a data record naming a foreign XML id raises at
install when that record is missing, and a grid row for a pair a site already
configured violates the matrix's unique index. Each helper here skips what it
cannot find or what is already there, so the hook can also run again.

English only: names are written with lang="en_US".
"""

MODULE = "maintenance_sla_garment"

# Core's stages: XML id, sequence, English name to set (None keeps it), and
# whether reaching it cancels SLA records. Resequencing changes no ids, so
# existing requests keep their stages.
CORE_STAGES = [
    ("maintenance.stage_0", 1, None, False),
    ("maintenance.stage_1", 2, None, False),
    # Directly after "Restored – to Confirm", "Repaired" would read as the same
    # thing.
    ("maintenance.stage_3", 6, "Done", False),
    ("maintenance.stage_4", 7, None, True),
]

# Response rules, reaching core's In Progress: XML id, name, priority (False for
# the fallback), target in hours, sequence. The fallback's higher sequence makes
# it apply only where no priority rule matches.
RESPONSE_RULES = [
    ("sla_response_high", "Response, High priority", "3", 0.25, 10),
    ("sla_response_normal", "Response, Normal priority", "2", 1.0, 10),
    ("sla_response_low", "Response, Low priority", "1", 4.0, 10),
    ("sla_response_very_low", "Response, Very Low priority", "0", 24.0, 10),
    ("sla_response_any", "Response, no priority", False, 1.0, 100),
]

# Criticality x urgency -> priority. Safety is always High; a minor machine
# stopping a line is Normal, since on a sewing line a spare replaces it.
PRIORITY_GRID = [
    ("a", "safety", "3"),
    ("a", "line_stopped", "3"),
    ("a", "defects", "3"),
    ("a", "degraded", "2"),
    ("a", "no_impact", "1"),
    ("b", "safety", "3"),
    ("b", "line_stopped", "3"),
    ("b", "defects", "2"),
    ("b", "degraded", "2"),
    ("b", "no_impact", "1"),
    ("c", "safety", "3"),
    ("c", "line_stopped", "2"),
    ("c", "defects", "2"),
    ("c", "degraded", "1"),
    ("c", "no_impact", "0"),
]


def post_init_hook(env):
    _arrange_stages(env)
    _create_response_rules(env)
    _fill_priority_grid(env)


def _arrange_stages(env):
    """Resequence core's stages around this module's, rename one, flag Scrap."""
    for xml_id, sequence, name, cancels in CORE_STAGES:
        stage = env.ref(xml_id, raise_if_not_found=False)
        if not stage:
            continue
        values = {"sequence": sequence}
        if name:
            values["name"] = name
        if cancels:
            values["sla_cancel"] = True
        stage.with_context(lang="en_US").write(values)


def _create_response_rules(env):
    """The Response rules, which target core's In Progress.

    Each is registered under this module's XML id with noupdate, so a second run
    finds it and skips it, and an upgrade leaves a tuned rule alone.
    """
    in_progress = env.ref("maintenance.stage_1", raise_if_not_found=False)
    if not in_progress:
        return
    rules = env["maintenance.sla"].with_context(lang="en_US")
    for xml_id, name, priority, hours, sequence in RESPONSE_RULES:
        if env.ref(f"{MODULE}.{xml_id}", raise_if_not_found=False):
            continue
        rule = rules.create(
            {
                "name": name,
                "sequence": sequence,
                "maintenance_type": "corrective",
                "priority": priority,
                "target_stage_id": in_progress.id,
                "duration": hours,
            }
        )
        env["ir.model.data"].create(
            {
                "module": MODULE,
                "name": xml_id,
                "model": "maintenance.sla",
                "res_id": rule.id,
                "noupdate": True,
            }
        )


def _fill_priority_grid(env):
    """The company-less grid rows whose pair is not already taken.

    Archived rows count: the unique index ignores active. A pair a site has
    configured keeps its value.
    """
    grid = env["maintenance.priority.rule"].with_context(active_test=False)
    for criticality, urgency, priority in PRIORITY_GRID:
        if grid.search_count(
            [
                ("criticality", "=", criticality),
                ("urgency", "=", urgency),
                ("company_id", "=", False),
            ],
            limit=1,
        ):
            continue
        grid.create(
            {"criticality": criticality, "urgency": urgency, "priority": priority}
        )
