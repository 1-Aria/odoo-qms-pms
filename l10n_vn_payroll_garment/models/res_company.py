# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models
from odoo.exceptions import AccessError, UserError

from .garment_scheme import (
    CATEGORIES,
    COMPONENTS,
    CONTRACT_TYPES,
    DATE_FROM,
    ENGINE_CODES,
    PARAMETERS,
    SCALES,
    STRUCTURE,
)

VI = "vi_VN"


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_vn_garment_load(self):
        """Create the garment pay scheme in this company, keeping what already exists.

        Every record is matched by code; a record found is left as it is. Returns
        ``{"created": [labels], "kept": [labels]}`` in load order.
        """
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group("payroll.group_payroll_manager")):
            raise AccessError(self.env._("Only payroll managers can load the garment pay scheme."))
        company = self.sudo()
        if company.country_id.code != "VN":
            raise UserError(
                self.env._(
                    "The garment pay scheme is for Vietnamese companies; %(company)s is not one.",
                    company=company.display_name,
                )
            )
        company._l10n_vn_payroll_ensure_parameters()
        env = company.env(context=dict(company.env.context, active_test=False))
        vietnamese = VI in dict(env["res.lang"].get_installed())
        result = {"created": [], "kept": []}
        names = []  # (record, Vietnamese name) for the records created

        def done(label, created):
            result["created" if created else "kept"].append(label)

        # parameters
        Param = env["base.time.parameter"]
        for code, name, kind, value in PARAMETERS:
            if Param.search([("code", "=", code), ("company_id", "=", company.id)], limit=1):
                done(f"parameter {code}", False)
                continue
            Param.create(
                {
                    "name": name,
                    "code": code,
                    "type": kind,
                    "company_id": company.id,
                    "country_id": company.country_id.id,
                    "version_ids": [Command.create({"date_from": DATE_FROM, "value": value})],
                }
            )
            done(f"parameter {code}", True)

        # scales
        Scale = env["l10n_vn.payroll.scale"]
        scales = {}
        for code, (en, vi), kind, versions in SCALES:
            scale = Scale.search([("code", "=", code), ("company_id", "=", company.id)], limit=1)
            if scale:
                done(f"scale {code}", False)
            else:
                scale = Scale.create(
                    {
                        "code": code,
                        "name": en,
                        "kind": kind,
                        "company_id": company.id,
                        "version_ids": [
                            Command.create(
                                {
                                    "date_from": date_from,
                                    "cell_ids": [
                                        Command.create(
                                            dict(
                                                {"key": key, "amount": amount},
                                                **_grade_step(kind, key),
                                            )
                                        )
                                        for key, amount in cells.items()
                                    ],
                                }
                            )
                            for date_from, cells in versions.items()
                        ],
                    }
                )
                names.append((scale, vi))
                done(f"scale {code}", True)
            scales[code] = scale

        # categories
        Category = env["hr.salary.rule.category"]
        categories = {}
        for code, (en, vi), kinds in CATEGORIES:
            category = Category.search(
                [("code", "=", code), ("company_id", "=", company.id)], limit=1
            ) or Category.search([("code", "=", code), ("company_id", "=", False)], limit=1)
            if category:
                done(f"category {code}", False)
            else:
                category = Category.create({"code": code, "name": en, "company_id": company.id})
                names.append((category, vi))
                done(f"category {code}", True)
            for kind in kinds:
                categories[kind] = category

        # components
        Component = env["l10n_vn.payroll.component"]
        components = []
        for sequence, (code, (en, vi), values) in enumerate(COMPONENTS, start=1):
            component = Component.search(
                [("code", "=", code), ("company_id", "=", company.id)], limit=1
            )
            if component:
                done(f"component {code}", False)
            else:
                vals = dict(values)
                scale_code = vals.pop("scale", None)
                if scale_code:
                    vals["scale_id"] = scales[scale_code].id
                if code in ENGINE_CODES:
                    vals["engine_code"] = code
                vals.update(
                    code=code, name=en, sequence=sequence * 10, company_id=company.id
                )
                component = Component.create(vals)
                names.append((component, vi))
                done(f"component {code}", True)
            components.append((component, code, sequence * 10, en, vi))

        # contract types, shared by all companies (D20)
        ContractType = env["hr.contract.type"]
        for code, (en, vi), participant_xmlid in CONTRACT_TYPES:
            if ContractType.search([("code", "=", code)], limit=1):
                done(f"contract type {code}", False)
                continue
            participant = env.ref(participant_xmlid, raise_if_not_found=False)
            contract_type = ContractType.create(
                {
                    "name": en,
                    "code": code,
                    "l10n_vn_participant_type_id": participant.id if participant else False,
                }
            )
            names.append((contract_type, vi))
            done(f"contract type {code}", True)

        # structure
        Structure = env["hr.payroll.structure"]
        structure_code, (structure_en, structure_vi) = STRUCTURE
        structure = Structure.search(
            [("code", "=", structure_code), ("company_id", "=", company.id)], limit=1
        )
        if structure:
            done(f"structure {structure_code}", False)
        else:
            structure = Structure.create(
                {
                    "code": structure_code,
                    "name": structure_en,
                    "company_id": company.id,
                    "parent_id": False,
                    "l10n_vn_payroll": True,
                }
            )
            names.append((structure, structure_vi))
            done(f"structure {structure_code}", True)

        # rules
        Rule = env["hr.salary.rule"]
        existing = {rule.code for rule in structure.rule_ids}
        for component, code, sequence, en, vi in components:
            if code in existing:
                done(f"rule {code}", False)
                continue
            rule = Rule.create(
                {
                    "name": en,
                    "code": code,
                    "sequence": sequence,
                    "category_id": categories[component.kind].id,
                    "company_id": company.id,
                    "amount_select": "l10n_vn_component",
                    "condition_select": "l10n_vn_component",
                    "l10n_vn_component_id": component.id,
                }
            )
            structure.rule_ids = [Command.link(rule.id)]
            names.append((rule, vi))
            done(f"rule {code}", True)

        if vietnamese:
            for record, vi in names:
                # a name that is not translated has one value only: keep it English
                if record._fields["name"].translate:
                    record.with_context(lang=VI).name = vi
        return result


def _grade_step(kind, key):
    """``G2-3`` → grade ``G2``, step 3 on a grade-and-step scale."""
    if kind != "grade_step":
        return {}
    grade, step = key.split("-")
    return {"grade": grade, "step": int(step)}
