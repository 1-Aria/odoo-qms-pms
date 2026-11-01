# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import json

from odoo import api, models
from odoo.exceptions import UserError


class BaseTimeParameter(models.Model):
    _inherit = "base.time.parameter"

    @api.model
    def _strict_get(self, code, date, company=None):
        """Return the value of parameter ``code`` in force on ``date``.

        A stored 0 or False is a value. A missing parameter, version or value,
        or a value that does not convert to the parameter's type, raises.
        Reads as superuser: parameters are configuration that calculations
        need whatever the user's groups.
        """
        if isinstance(date, datetime.datetime):
            date = date.date()
        elif not isinstance(date, datetime.date):
            raise TypeError(f"_strict_get needs a date, not {date!r}")
        company = company or self.env.company
        params = self.sudo()
        found = params.search([("code", "=", code), ("company_id", "=", company.id)])
        if not found:
            found = params.search([("code", "=", code), ("company_id", "=", False)])
        if len(found) > 1:
            raise UserError(
                self.env._(
                    "Several time parameters have the code %(code)s (company %(company)s).",
                    code=code,
                    company=company.name,
                )
            )
        if not found:
            raise UserError(
                self.env._(
                    "No time parameter with the code %(code)s (company %(company)s).",
                    code=code,
                    company=company.name,
                )
            )
        versions = found.version_ids.filtered(lambda v: v.date_from <= date).sorted(
            "date_from", reverse=True
        )
        if not versions:
            raise UserError(
                self.env._(
                    "Time parameter %(code)s has no value on %(date)s.",
                    code=code,
                    date=date,
                )
            )
        return self._strict_convert(found, versions[0])

    @api.model
    def _strict_convert(self, parameter, version):
        """Convert a version's stored value by its parameter's type."""
        kind = parameter.type
        if kind == "record":
            if not version.value_reference:
                raise self._strict_empty(parameter, version)
            return version.value_reference
        value = version.value
        if not value:
            raise self._strict_empty(parameter, version)
        if kind == "string":
            return value
        try:
            if kind == "boolean":
                text = value.strip().lower()
                if text in ("true", "1"):
                    return True
                if text in ("false", "0"):
                    return False
                raise ValueError(value)
            if kind == "date":
                return datetime.datetime.strptime(value.strip(), "%Y-%m-%d").date()
            if kind == "float":
                return float(value)
            if kind == "integer":
                number = float(value)
                if not number.is_integer():
                    raise ValueError(value)
                return int(number)
            if kind == "json":
                return json.loads(value)
        except ValueError as error:
            raise UserError(
                self.env._(
                    "Time parameter %(code)s, version of %(date_from)s: "
                    "%(value)r is not a valid %(type)s.",
                    code=parameter.code,
                    date_from=version.date_from,
                    value=value,
                    type=kind,
                )
            ) from error
        raise UserError(
            self.env._(
                "Time parameter %(code)s has a type this reader does not know: %(type)s.",
                code=parameter.code,
                type=kind,
            )
        )

    @api.model
    def _strict_empty(self, parameter, version):
        return UserError(
            self.env._(
                "Time parameter %(code)s has no value on %(date)s.",
                code=parameter.code,
                date=version.date_from,
            )
        )
