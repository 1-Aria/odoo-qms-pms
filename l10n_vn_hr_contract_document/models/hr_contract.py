# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import is_html_empty

from .hr_contract_type import FORM_KINDS

# set only by approval (and, from step 3, amendments): the one key that passes the lock
UNLOCK = "l10n_vn_contract_unlock"

TITLES = {
    "labour": "HỢP ĐỒNG LAO ĐỘNG",
    "probation": "HỢP ĐỒNG THỬ VIỆC",
    "training": "HỢP ĐỒNG ĐÀO TẠO",
}
ABBREVIATIONS = {"labour": "HĐLĐ", "probation": "HĐTV", "training": "HĐĐT"}
GENDERS = {"male": "Nam", "female": "Nữ", "other": "Khác"}
PROBATION_JOBS = {
    "manager": "công việc của người quản lý doanh nghiệp",
    "college": (
        "công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật từ cao đẳng "
        "trở lên"
    ),
    "vocational": (
        "công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật trung cấp, công "
        "nhân kỹ thuật, nhân viên nghiệp vụ"
    ),
    "other": "công việc khác",
}
TRAINING_KINDS = {"practice": "tập nghề", "apprenticeship": "học nghề"}
# fixed articles of each form before the closing one; training adds the repayment
# article when a commitment is set (D17)
FIXED_ARTICLES = {"labour": 11, "probation": 6, "training": 6}
# the terms an approved contract keeps (D28); date_end has its own rule
LOCKED_FIELDS = [
    "employee_id",
    "company_id",
    "contract_type_id",
    "date_start",
    "trial_date_end",
    "job_id",
    "l10n_vn_work_address_id",
    "l10n_vn_participant_type_id",
    "l10n_vn_probation_form",
    "l10n_vn_probation_job",
    "l10n_vn_training_kind",
    "l10n_vn_commitment_months",
    "l10n_vn_training_cost",
    "l10n_vn_training_cost_items",
    "l10n_vn_individual_terms",
]
# written only by approval and amendments
APPROVAL_FIELDS = ("l10n_vn_approved", "l10n_vn_version_id", "l10n_vn_amendment_id")
# what an amendment unlocks (D40); the pay lines follow D41
AMENDABLE_FIELDS = (
    "job_id",
    "l10n_vn_work_address_id",
    "l10n_vn_participant_type_id",
    "l10n_vn_commitment_months",
    "l10n_vn_training_cost",
    "l10n_vn_training_cost_items",
    "l10n_vn_individual_terms",
)
ANNEX_TITLES = {
    "labour": "PHỤ LỤC HỢP ĐỒNG LAO ĐỘNG",
    "probation": "PHỤ LỤC HỢP ĐỒNG THỬ VIỆC",
    "training": "PHỤ LỤC HỢP ĐỒNG ĐÀO TẠO",
}
FORM_NAMES = {"labour": "lao động", "probation": "thử việc", "training": "đào tạo"}
# the article each group fills on each form (D43)
GROUP_ARTICLES = {
    "labour": {"work": 2, "salary": 3, "bonus": 4, "insurance": 8},
    "probation": {"work": 2, "salary": 3},
    "training": {"work": 1, "salary": 3, "training": 7},
}
ARTICLE_TITLES = {
    ("labour", 2): "Công việc và địa điểm làm việc",
    ("labour", 3): "Tiền lương, phụ cấp lương và các khoản bổ sung khác",
    ("labour", 4): "Tiền thưởng và phúc lợi",
    ("labour", 8): "Bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp",
    ("probation", 2): "Công việc và địa điểm làm việc",
    ("probation", 3): "Tiền lương thử việc",
    ("training", 1): "Nghề, công việc đào tạo; thời gian và địa điểm",
    ("training", 7): "Cam kết làm việc và hoàn trả chi phí đào tạo",
}


def _rows(rows):
    return tuple((row["name"], row["amount_text"], row["unit"]) for row in rows or [])


# what each group compares (D43)
GROUP_KEYS = {
    "work": lambda t: (t.get("job"), t.get("workplace")),
    "salary": lambda t: (
        _rows(t.get("salary")),
        _rows(t.get("allowances")),
        _rows(t.get("supplements")),
        tuple(t.get("variable") or ()),
        t.get("payment_text"),
    ),
    "bonus": lambda t: _rows(t.get("welfare")),
    "insurance": lambda t: t.get("insured"),
    "training": lambda t: (
        (t.get("training") or {}).get("commitment_months"),
        (t.get("training") or {}).get("cost_text"),
        (t.get("training") or {}).get("cost_items"),
    ),
}


class HrContract(models.Model):
    _inherit = "hr.contract"

    l10n_vn_document_kind = fields.Selection(related="contract_type_id.l10n_vn_document_kind")
    l10n_vn_work_address_id = fields.Many2one(
        "res.partner",
        string="Workplace",
        compute="_compute_l10n_vn_work_address",
        store=True,
        readonly=False,
        tracking=True,
    )
    l10n_vn_sign_date = fields.Date(
        string="Signing Date",
        help="Printed at the top of the contract; left empty, it is written by hand.",
    )
    l10n_vn_training_kind = fields.Selection(
        [
            ("practice", "Practice (tập nghề)"),
            ("apprenticeship", "Apprenticeship (học nghề)"),
        ],
        string="Training",
        default="practice",
    )
    l10n_vn_commitment_months = fields.Integer(
        string="Commitment (months)",
        help="Months the trainee commits to work after the labour contract. "
        "Empty: no repayment article.",
    )
    l10n_vn_training_cost = fields.Monetary(string="Training Cost")
    l10n_vn_training_cost_items = fields.Text(string="Training Cost Items")
    l10n_vn_individual_terms = fields.Html(
        string="Individual Terms",
        help="Terms agreed with this employee only, printed as their own article.",
    )
    l10n_vn_document_missing = fields.Text(
        string="Before Approval",
        compute="_compute_l10n_vn_document_missing",
        compute_sudo=True,
    )
    # step 2: approval (D20-D34)
    l10n_vn_version_ids = fields.One2many(
        "l10n_vn.contract.version",
        "contract_id",
        string="Versions",
        copy=False,
        groups="payroll.group_payroll_user",
    )
    l10n_vn_version_id = fields.Many2one(
        "l10n_vn.contract.version", string="Approved Version", copy=False, readonly=True
    )
    l10n_vn_approved = fields.Boolean(
        string="Approved", copy=False, readonly=True, tracking=True
    )
    l10n_vn_number = fields.Char(
        string="Contract Number", compute="_compute_l10n_vn_number", compute_sudo=True
    )
    # step 3: amendments (D39-D44)
    l10n_vn_amendment_id = fields.Many2one(
        "l10n_vn.contract.version", string="Amendment in Progress", copy=False, readonly=True
    )
    l10n_vn_amendment_date = fields.Date(related="l10n_vn_amendment_id.effective_date")
    l10n_vn_amendment_reason = fields.Char(related="l10n_vn_amendment_id.reason")
    l10n_vn_company_approval = fields.Boolean(
        related="company_id.l10n_vn_contract_approval"
    )

    @api.depends("l10n_vn_version_ids.number", "l10n_vn_version_ids.state")
    def _compute_l10n_vn_number(self):
        # the contract's own number: version 0's, not an annex's (D45)
        for contract in self:
            contract.l10n_vn_number = contract._l10n_vn_version_zero().number or False

    @api.depends("employee_id")
    def _compute_l10n_vn_work_address(self):
        # follows the employee like core's job and department (D13)
        for contract in self.filtered("employee_id"):
            contract.l10n_vn_work_address_id = contract.employee_id.address_id

    @api.depends(
        "contract_type_id.l10n_vn_document_kind",
        "company_id.l10n_vn_legal_rep_id",
        "company_id.l10n_vn_legal_rep_title",
        "employee_id.birthday",
        "employee_id.gender",
        "employee_id.l10n_vn_personal_id",
        "employee_id.l10n_vn_id_issue_date",
        "employee_id.l10n_vn_id_issue_place",
        "employee_id.l10n_vn_permanent_address",
        "job_id",
        "l10n_vn_work_address_id",
        "date_start",
        "date_end",
        "trial_date_end",
        "l10n_vn_probation_form",
        "l10n_vn_probation_job",
        "l10n_vn_line_ids",
        "l10n_vn_approved",
        "l10n_vn_amendment_id",
    )
    def _compute_l10n_vn_document_missing(self):
        for contract in self:
            # everything approval checks, not only the missing data (D36); during an
            # amendment, on its effective date (D51)
            if contract.l10n_vn_amendment_id:
                problems = contract._l10n_vn_approval_problems(contract.l10n_vn_amendment_date)
            elif contract.l10n_vn_approved:
                problems = []
            else:
                problems = contract._l10n_vn_approval_problems()
            contract.l10n_vn_document_missing = "\n".join(problems) if problems else False

    # ------------------------------------------------------------------ helpers
    def _l10n_vn_document_kind_value(self):
        kind = self.sudo().contract_type_id.l10n_vn_document_kind
        return kind if kind in FORM_KINDS else False

    def _l10n_vn_has_probation(self, kind):
        return kind == "probation" or (
            kind == "labour" and self.sudo().l10n_vn_probation_form == "clause"
        )

    def _l10n_vn_probation_end(self, kind):
        return self.date_end if kind == "probation" else self.trial_date_end

    def _l10n_vn_version_zero(self):
        return self.sudo().l10n_vn_version_ids.filtered(
            lambda version: version.sequence == 0 and version.state == "approved"
        )[:1]

    def _l10n_vn_document_missing(self, date=None):
        """Labels of what the contract's form still needs (D9, D10), pay read on ``date``."""
        self.ensure_one()
        contract = self.sudo()
        kind = contract._l10n_vn_document_kind_value()
        if not kind or not contract.date_start:
            return []
        date = date or contract.date_start
        fields_model = self.env["ir.model.fields"]
        missing = []

        def need(record, model, name):
            if not record[name]:
                missing.append(fields_model._get(model, name).field_description)

        company = contract.company_id
        for name in ("l10n_vn_legal_rep_id", "l10n_vn_legal_rep_title", "vat", "street"):
            need(company, "res.company", name)
        if not (company.state_id or company.city):
            missing.append(fields_model._get("res.company", "state_id").field_description)
        employee = contract.employee_id
        if not employee:
            need(contract, "hr.contract", "employee_id")
        else:
            need(employee, "hr.employee", "birthday")
            need(employee, "hr.employee", "gender")
            personal_id = (employee.l10n_vn_personal_id or "").strip()
            if not personal_id:
                need(employee, "hr.employee", "l10n_vn_personal_id")
            elif not (personal_id.isdigit() and len(personal_id) == 12):
                missing.append(self.env._("Personal ID No. (CCCD) must have 12 digits"))
            for name in (
                "l10n_vn_id_issue_date",
                "l10n_vn_id_issue_place",
                "l10n_vn_permanent_address",
            ):
                need(employee, "hr.employee", name)
        need(contract, "hr.contract", "job_id")
        need(contract, "hr.contract", "l10n_vn_work_address_id")
        lines = contract.l10n_vn_line_ids._l10n_vn_in_force(date)
        if not lines.filtered(lambda line: line.component_id.l10n_vn_contract_print == "amount"):
            missing.append(
                self.env._("A pay line in force on the start date with an amount in the contract")
            )
        # amounts the form prints but cannot read on the start date (D4)
        for line in lines.filtered(
            lambda line: line.component_id.l10n_vn_contract_print in ("amount", "welfare")
            and line.component_id.legal_nature != "bonus"
        ):
            error = contract._l10n_vn_read_amount(line, date)[1]
            if error:
                missing.append(error)
        if contract._l10n_vn_has_probation(kind):
            need(contract, "hr.contract", "l10n_vn_probation_job")
            need(contract, "hr.contract", "date_end" if kind == "probation" else "trial_date_end")
            error = contract._l10n_vn_probation_rate(date)[1]
            if error:
                missing.append(error)
        if kind == "training":
            need(contract, "hr.contract", "date_end")
        return missing

    def _l10n_vn_read_amount(self, line, date):
        """(amount, None), or (None, the reason) when the amount cannot be read (D4)."""
        try:
            return self.currency_id.round(line._l10n_vn_amount_on(date)), None
        except UserError as error:
            return None, f"{line.component_id.code}: {error.args[0]}"

    def _l10n_vn_probation_rate(self, date):
        """(rate, None), or (None, the reason) when the parameter cannot be read (D4)."""
        try:
            rate = self.env["base.time.parameter"].sudo()._strict_get(
                "vn.policy.probation_rate", date, company=self.company_id
            )
            return rate, None
        except UserError as error:
            return None, error.args[0]

    def _l10n_vn_probation_days(self, start, end, working_days):
        if working_days and self.resource_calendar_id and self.employee_id:
            return self.env["l10n_vn.payroll.check"]._scheduled_dates(self, start, end)
        return (end - start).days + 1

    def _l10n_vn_length(self, start, end, working_days=False):
        """A length as printed (D11)."""
        if not end:
            return ""
        if working_days and self.resource_calendar_id and self.employee_id:
            return f"{self._l10n_vn_probation_days(start, end, True)} ngày làm việc"
        if not working_days:
            span = relativedelta(end + datetime.timedelta(days=1), start)
            months = span.years * 12 + span.months
            if months and not span.days:
                return f"{months} tháng"
        return f"{(end - start).days + 1} ngày"

    # ------------------------------------------------------------------ values
    def _l10n_vn_document_terms(self, date=None):
        """The terms the form prints, read live on ``date``, default the start (D4, D24)."""
        self.ensure_one()
        contract = self.sudo().with_context(lang="vi_VN")
        kind = contract._l10n_vn_document_kind_value()
        doc = self.env["l10n_vn.contract.document"]
        date = date or contract.date_start
        currency = contract.currency_id

        salary, allowances, supplements, variable, welfare = [], [], [], [], []
        lines = contract.l10n_vn_line_ids._l10n_vn_in_force(date).sorted(
            lambda line: (line.component_id.sequence, line.component_id.code)
        )
        for line in lines:
            component = line.component_id
            mode = component.l10n_vn_contract_print
            if mode == "reference":
                variable.append(component.name)
                continue
            if mode not in ("amount", "welfare"):
                continue
            amount = None
            if mode == "amount" or component.legal_nature != "bonus":
                # an amount that cannot be read prints as a blank (D4)
                amount = contract._l10n_vn_read_amount(line, date)[0]
            row = {
                "name": component.name,
                "amount": amount,
                "amount_text": doc._money(amount) if amount else "",
                "words": doc._words(amount) if amount else "",
                "unit": "ngày" if component.proration == "per_day" else "tháng",
                "probation": component.probation_applies,
            }
            if mode == "welfare":
                welfare.append(row)
            elif component.legal_nature == "job_salary":
                salary.append(row)
            elif component.legal_nature == "fixed_allowance":
                allowances.append(row)
            else:
                supplements.append(row)

        probation = None
        if contract._l10n_vn_has_probation(kind):
            end = contract._l10n_vn_probation_end(kind)
            rate = contract._l10n_vn_probation_rate(date)[0]
            job = contract.l10n_vn_probation_job
            rows = [row for row in salary + allowances if row["probation"]]
            probation_amount = None
            percent = None
            if rate is not None:
                percent = round(rate * 100, 2)
                percent = int(percent) if percent == int(percent) else percent
                if all(row["amount"] is not None for row in rows):
                    probation_amount = currency.round(sum(row["amount"] for row in rows) * rate)
            probation = {
                "date_end": doc._date(end),
                "length": contract._l10n_vn_length(
                    contract.date_start, end, working_days=job == "other"
                ),
                "rate": percent,
                "job": PROBATION_JOBS.get(job, ""),
                "amount": probation_amount,
                "amount_text": doc._money(probation_amount),
                "words": doc._words(probation_amount),
            }

        participant = contract.l10n_vn_participant_type_id
        party_b = "NGƯỜI LAO ĐỘNG"
        if kind == "training":
            party_b = (
                "NGƯỜI HỌC NGHỀ"
                if contract.l10n_vn_training_kind == "apprenticeship"
                else "NGƯỜI TẬP NGHỀ"
            )
        cost = contract.l10n_vn_training_cost
        individual = contract.l10n_vn_individual_terms
        return {
            "kind": kind,
            "title": TITLES[kind],
            "party_b": party_b,
            "term": {
                "fixed": bool(contract.date_end),
                "length": contract._l10n_vn_length(contract.date_start, contract.date_end),
                "date_start": doc._date(contract.date_start),
                "date_end": doc._date(contract.date_end),
            },
            "probation": probation,
            "job": contract.job_id.name or "",
            "workplace": doc._address(contract.l10n_vn_work_address_id),
            "salary": salary,
            "allowances": allowances,
            "supplements": supplements,
            "variable": variable,
            "welfare": welfare,
            "paid_by_transfer": participant.paid_by_transfer,
            "payment_text": (
                "chuyển khoản vào tài khoản ngân hàng mang tên Bên B"
                if participant.paid_by_transfer
                else "tiền mặt"
            ),
            "insured": any(
                participant[name]
                for name in (
                    "fund_pension",
                    "fund_sickness",
                    "fund_accident",
                    "fund_hi",
                    "fund_ui",
                )
            ),
            "training": {
                "kind_text": TRAINING_KINDS.get(contract.l10n_vn_training_kind, "tập nghề"),
                "commitment_months": contract.l10n_vn_commitment_months or 0,
                "cost_text": doc._money(cost) if cost else "",
                "cost_words": doc._words(cost) if cost else "",
                "cost_items": contract.l10n_vn_training_cost_items or "",
            },
            "individual_terms_body": None if is_html_empty(individual) else str(individual),
        }

    def _l10n_vn_document_raw(self):
        """The locked values and pay lines, for step 3's comparison and cancellation (D24)."""
        self.ensure_one()
        contract = self.sudo()
        raw = {}
        for name in LOCKED_FIELDS + ["date_end"]:
            field = contract._fields[name]
            value = contract[name]
            if field.type == "many2one":
                raw[name] = value.id or False
            elif field.type == "date":
                raw[name] = fields.Date.to_string(value) if value else False
            else:
                raw[name] = str(value) if field.type == "html" and value else value
        raw["pay_lines"] = [
            {
                "id": line.id,
                "component_id": line.component_id.id,
                "date_from": fields.Date.to_string(line.date_from),
                "date_to": fields.Date.to_string(line.date_to) if line.date_to else False,
            }
            for line in contract.l10n_vn_line_ids.filtered(
                lambda line: not line.date_to or line.date_to >= contract.date_start
            )
        ]
        return raw

    def _l10n_vn_article_numbers(self, terms):
        """(extra articles, the individual terms' number or None, closing number) (D17)."""
        kind = terms["kind"]
        wording = self.env["l10n_vn.contract.wording"]._for_company(self.sudo().company_id)
        number = FIXED_ARTICLES[kind] + (
            1 if kind == "training" and terms["training"]["commitment_months"] else 0
        )
        extra_articles = []
        for article in wording.article_ids.filtered(
            lambda article: article.active and article.kind == kind
        ).sorted(lambda article: (article.sequence, article.id)):
            number += 1
            extra_articles.append(
                {"number": number, "title": article.title, "body": article.body}
            )
        individual_number = None
        if terms.get("individual_terms_body"):
            number += 1
            individual_number = number
        return extra_articles, individual_number, number + 1

    def _l10n_vn_document_values(self, terms=None):
        """Everything the forms print (D8, D25); ``terms`` given by an annex (D46)."""
        if not self.env.su and not self.env.user.has_group("payroll.group_payroll_user"):
            raise AccessError(
                self.env._("Only payroll users print contract documents, which show pay.")
            )
        self.ensure_one()
        contract = self.sudo().with_context(lang="vi_VN")
        if not contract._l10n_vn_document_kind_value():
            raise UserError(
                self.env._("Contract %(contract)s has no contract document.", contract=self.name)
            )
        version_zero = contract._l10n_vn_version_zero()
        if terms is not None:
            terms = dict(terms)
        elif contract.l10n_vn_approved and version_zero.terms:
            # the contract prints version 0; an annex prints itself (D45)
            terms = dict(version_zero.terms["render"])
        else:
            terms = contract._l10n_vn_document_terms()
        kind = terms["kind"]
        doc = self.env["l10n_vn.contract.document"]
        company = contract.company_id
        partner = company.partner_id
        employee = contract.employee_id

        current_address = ", ".join(
            part.strip()
            for part in (
                employee.private_street,
                employee.private_street2,
                employee.private_city,
                employee.private_state_id.name,
            )
            if part and part.strip()
        )
        permanent_address = (employee.l10n_vn_permanent_address or "").strip()
        if current_address == permanent_address:
            current_address = ""

        wording = self.env["l10n_vn.contract.wording"]._for_company(company)
        extra_articles, individual_number, closing_number = contract._l10n_vn_article_numbers(
            terms
        )
        individual_terms = None
        if individual_number:
            # sanitized when saved on the contract (D25)
            individual_terms = {
                "number": individual_number,
                "body": Markup(terms["individual_terms_body"]),
            }
        return dict(
            terms,
            sign_place=partner.state_id.name or partner.city or "",
            sign_date=doc._date_parts(contract.l10n_vn_sign_date),
            company={
                "name": company.name,
                "vat": company.vat or "",
                "address": doc._address(partner),
                "phone": partner.phone or "",
                "email": partner.email or "",
                "rep_name": company.l10n_vn_legal_rep_id.name or "",
                "rep_title": company.l10n_vn_legal_rep_title or "",
            },
            employee={
                "name": employee.name or "",
                "gender": GENDERS.get(employee.gender, ""),
                "birthday": doc._date(employee.birthday),
                "nationality": employee.country_id.name or "Việt Nam",
                "personal_id": employee.l10n_vn_personal_id or "",
                "id_issue_date": doc._date(employee.l10n_vn_id_issue_date),
                "id_issue_place": employee.l10n_vn_id_issue_place or "",
                "permanent_address": permanent_address,
                "current_address": current_address,
                "phone": employee.private_phone or "",
                "email": employee.private_email or "",
            },
            wording=wording,
            extra_articles=extra_articles,
            individual_terms=individual_terms,
            closing_number=closing_number,
            number=version_zero.number or "",
            draft=not contract.l10n_vn_approved,
        )

    # ------------------------------------------------------------------ approval
    def _l10n_vn_approval_problems(self, date=None):
        """What stops the approval: missing data on ``date`` and the legal limits (D22)."""
        self.ensure_one()
        contract = self.sudo()
        kind = contract._l10n_vn_document_kind_value()
        if not kind:
            return []
        problems = contract._l10n_vn_document_missing(date)
        start = contract.date_start
        Param = self.env["base.time.parameter"].sudo()
        _ = self.env._
        if contract._l10n_vn_has_probation(kind):
            end = contract._l10n_vn_probation_end(kind)
            job = contract.l10n_vn_probation_job
            if end and job:
                try:
                    limits = Param._strict_get("vn.probation.max_days", start, contract.company_id)
                except UserError as error:
                    problems.append(error.args[0])
                else:
                    length = contract._l10n_vn_probation_days(start, end, job == "other")
                    if job in limits and length > limits[job]:
                        problems.append(
                            _(
                                "Probation of %(length)s days is longer than the %(limit)s "
                                "allowed for this job.",
                                length=length,
                                limit=limits[job],
                            )
                        )
            rate = contract._l10n_vn_probation_rate(start)[0]
            if rate is not None:
                try:
                    minimum = Param._strict_get("vn.probation.min_rate", start, contract.company_id)
                except UserError as error:
                    problems.append(error.args[0])
                else:
                    if rate < minimum:
                        problems.append(
                            _(
                                "The probation rate %(rate)s is below the legal minimum "
                                "%(minimum)s.",
                                rate=rate,
                                minimum=minimum,
                            )
                        )
        after_end = contract.date_end and contract.date_end + datetime.timedelta(days=1)
        if kind == "labour" and after_end and after_end > start + relativedelta(months=36):
            problems.append(_("A fixed-term labour contract lasts at most 36 months."))
        if kind == "training" and after_end and after_end > start + relativedelta(months=3):
            problems.append(_("A training contract lasts at most 3 months."))
        return problems

    def _l10n_vn_next_number(self, kind):
        """The contract's number from the company's sequence of its form (D23)."""
        self.ensure_one()
        Sequence = self.env["ir.sequence"].sudo()
        code = f"l10n_vn.contract.{kind}"
        sequence = Sequence.search(
            [("code", "=", code), ("company_id", "=", self.company_id.id)], limit=1
        )
        if not sequence:
            sequence = Sequence.create(
                {
                    "name": f"Contract numbers ({kind})",
                    "code": code,
                    "company_id": self.company_id.id,
                    "padding": 4,
                    "use_date_range": True,
                    # a failed approval in a selection must not leave a gap
                    "implementation": "no_gap",
                }
            )
        number = sequence.next_by_id(sequence_date=self.date_start)
        result = f"{number}/{self.date_start.year}/{ABBREVIATIONS[kind]}"
        if self.company_id.l10n_vn_contract_code:
            result += f"-{self.company_id.l10n_vn_contract_code}"
        return result

    def _l10n_vn_approve_one(self):
        """Approve one contract (D21), as superuser."""
        self.ensure_one()
        _ = self.env._
        contract = self.sudo().with_context(**{UNLOCK: True})
        if contract.l10n_vn_approved:
            raise UserError(_("Contract %(contract)s is already approved.", contract=self.name))
        if contract.state not in ("draft", "open"):
            raise UserError(
                _("Contract %(contract)s is expired or cancelled.", contract=self.name)
            )
        kind = contract._l10n_vn_document_kind_value()
        problems = contract._l10n_vn_approval_problems()
        if problems:
            raise UserError(
                _("Contract %(contract)s cannot be approved:", contract=self.name)
                + "\n"
                + "\n".join(f"- {problem}" for problem in problems)
            )
        number = contract._l10n_vn_next_number(kind) if kind else False
        version = self.env["l10n_vn.contract.version"].sudo().create(
            {
                "contract_id": contract.id,
                "sequence": 0,
                "kind": "contract",
                "number": number,
                "effective_date": contract.date_start,
                "state": "approved",
                "terms": {
                    "render": contract._l10n_vn_document_terms() if kind else {},
                    "raw": contract._l10n_vn_document_raw(),
                },
                "approved_by": self.env.uid,
                "approved_at": fields.Datetime.now(),
            }
        )
        vals = {"l10n_vn_approved": True, "l10n_vn_version_id": version.id}
        if contract.state == "draft":
            if contract.date_start <= fields.Date.context_today(contract):
                vals["state"] = "open"
            else:
                vals["kanban_state"] = "done"
        contract.write(vals)
        contract.message_post(
            body=_("Contract approved: %(number)s", number=number)
            if number
            else _("Contract approved")
        )

    def action_l10n_vn_approve(self):
        """Approve the contracts (D21); a selection lists its failures (D31)."""
        self._l10n_vn_check_manager()
        if len(self) == 1:
            self._l10n_vn_approve_one()
            return False
        failures = []
        for contract in self:
            try:
                with self.env.cr.savepoint():
                    contract._l10n_vn_approve_one()
            except (UserError, ValidationError) as error:
                failures.append(error.args[0])
        if not failures:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "success",
                    "message": self.env._("%(count)s contracts approved.", count=len(self)),
                    "next": {"type": "ir.actions.client", "tag": "reload"},
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "warning",
                "sticky": True,
                "title": self.env._(
                    "%(failed)s of %(count)s contracts not approved",
                    failed=len(failures),
                    count=len(self),
                ),
                "message": "\n\n".join(failures),
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    # ------------------------------------------------------------------ amendments
    def _l10n_vn_check_manager(self):
        """Approving and amending: contract administration and payroll rights (D53)."""
        user = self.env.user
        if not self.env.su and not (
            user.has_group("hr_contract.group_hr_contract_manager")
            and user.has_group("payroll.group_payroll_user")
        ):
            raise AccessError(
                self.env._(
                    "Only contract administrators with payroll rights approve or change contracts."
                )
            )

    def _l10n_vn_paid_until(self):
        """The last day of the contract's payslips in approved runs, or False (D39)."""
        self.ensure_one()
        payslips = self.env["hr.payslip"].sudo().search([("contract_id", "=", self.id)])
        locked = payslips.filtered(lambda payslip: payslip._l10n_vn_locked())
        return max(locked.mapped("date_to")) if locked else False

    def _l10n_vn_changes(self, old, new, kind):
        """What an annex changes: the printed groups that differ, with their articles (D43)."""
        changes = []
        articles = GROUP_ARTICLES.get(kind, {})
        for group, number in sorted(articles.items(), key=lambda item: item[1]):
            if GROUP_KEYS[group](old) != GROUP_KEYS[group](new):
                title = ARTICLE_TITLES.get((kind, number))
                if kind == "training" and group == "salary":
                    title = "Tiền lương trong thời gian " + new["training"]["kind_text"]
                changes.append(
                    {"group": group, "number": number, "title": title, "action": "modify"}
                )
        old_body, new_body = old.get("individual_terms_body"), new.get("individual_terms_body")
        if (old_body or None) != (new_body or None):
            source = old if old_body else new
            number = self._l10n_vn_article_numbers(source)[1]
            action = "modify" if old_body and new_body else ("remove" if old_body else "add")
            changes.append(
                {
                    "group": "individual",
                    "number": number,
                    "title": "Thỏa thuận khác",
                    "action": action,
                }
            )
        return changes

    def _l10n_vn_amend(self, date, reason):
        """Open an amendment from ``date`` (D39), as superuser."""
        self.ensure_one()
        self._l10n_vn_check_manager()
        _ = self.env._
        contract = self.sudo().with_context(**{UNLOCK: True})
        if not contract.l10n_vn_approved:
            raise UserError(_("Contract %(contract)s is not approved.", contract=self.name))
        if contract.l10n_vn_amendment_id:
            raise UserError(
                _("Contract %(contract)s already has an amendment in progress.", contract=self.name)
            )
        if contract.state not in ("draft", "open"):
            raise UserError(
                _("Contract %(contract)s is expired or cancelled.", contract=self.name)
            )
        if date < contract.date_start or (contract.date_end and date > contract.date_end):
            raise UserError(
                _("The effective date must fall within contract %(contract)s.", contract=self.name)
            )
        paid_until = contract._l10n_vn_paid_until()
        if paid_until and date <= paid_until:
            raise UserError(
                _(
                    "Contract %(contract)s is paid until %(date)s in an approved run: correct a "
                    "paid month through payroll, and amend from a later date.",
                    contract=self.name,
                    date=paid_until,
                )
            )
        version = self.env["l10n_vn.contract.version"].sudo().create(
            {
                "contract_id": contract.id,
                "sequence": max(contract.l10n_vn_version_ids.mapped("sequence") or [0]) + 1,
                "kind": "annex",
                "state": "draft",
                "effective_date": date,
                "reason": reason,
                "terms": {"raw_before": contract._l10n_vn_document_raw()},
            }
        )
        contract.write({"l10n_vn_amendment_id": version.id})
        contract.message_post(
            body=_("Amendment opened from %(date)s: %(reason)s", date=date, reason=reason)
        )
        return version

    def _l10n_vn_approve_amendment_one(self):
        """Approve the amendment in progress as the contract's next version (D42)."""
        self.ensure_one()
        _ = self.env._
        contract = self.sudo().with_context(**{UNLOCK: True})
        version = contract.l10n_vn_amendment_id
        if not version:
            raise UserError(_("Contract %(contract)s has no amendment in progress.", contract=self.name))
        date = version.effective_date
        kind = contract._l10n_vn_document_kind_value()
        render, changes, number = {}, [], False
        if kind:
            problems = contract._l10n_vn_approval_problems(date)
            if problems:
                raise UserError(
                    _("The amendment of contract %(contract)s cannot be approved:", contract=self.name)
                    + "\n"
                    + "\n".join(f"- {problem}" for problem in problems)
                )
            render = contract._l10n_vn_document_terms(date)
            current = (contract.l10n_vn_version_id.terms or {}).get("render") or {}
            changes = contract._l10n_vn_changes(current, render, kind)
            if not changes:
                raise UserError(
                    _(
                        "Nothing printed in contract %(contract)s changes on %(date)s.",
                        contract=self.name,
                        date=date,
                    )
                )
            contract_number = contract._l10n_vn_version_zero().number
            if contract_number:
                number = f"{version.sequence:02d}/{contract_number}"
        version.write(
            {
                "number": number,
                "state": "approved",
                "terms": dict(
                    version.terms or {},
                    render=render,
                    raw=contract._l10n_vn_document_raw(),
                    changes=changes,
                ),
                "approved_by": self.env.uid,
                "approved_at": fields.Datetime.now(),
            }
        )
        contract.write({"l10n_vn_version_id": version.id, "l10n_vn_amendment_id": False})
        contract.message_post(
            body=_("Annex approved: %(number)s", number=number) if number else _("Amendment approved")
        )
        return version

    def action_l10n_vn_amend(self):
        self.ensure_one()
        self._l10n_vn_check_manager()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Amend Contract"),
            "res_model": "l10n_vn.contract.amend.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_contract_id": self.id},
        }

    def action_l10n_vn_approve_amendment(self):
        self._l10n_vn_check_manager()
        for contract in self:
            contract._l10n_vn_approve_amendment_one()
        return False

    def action_l10n_vn_cancel_amendment(self):
        """Put the contract back as it was when the amendment opened (D44)."""
        self._l10n_vn_check_manager()
        for contract in self.sudo().with_context(**{UNLOCK: True}):
            version = contract.l10n_vn_amendment_id
            if not version:
                continue
            raw = (version.terms or {}).get("raw_before") or {}
            vals = {}
            for name in LOCKED_FIELDS + ["date_end"]:
                if name not in raw:
                    continue
                field = contract._fields[name]
                value = raw[name]
                current = contract[name]
                if field.type == "many2one":
                    if current.id != (value or False):
                        vals[name] = value or False
                elif field.type == "date":
                    if (fields.Date.to_string(current) if current else False) != value:
                        vals[name] = value or False
                elif field.type == "html":
                    if str(current or "") != (value or ""):
                        vals[name] = value or False
                elif current != value:
                    vals[name] = value
            vals["l10n_vn_amendment_id"] = False
            contract.write(vals)
            kept = {line["id"]: line for line in raw.get("pay_lines", [])}
            # the new lines first, so the old ones can run on again without overlap
            contract.l10n_vn_line_ids.filtered(lambda line: line.id not in kept).unlink()
            for line in contract.l10n_vn_line_ids:
                date_to = kept[line.id]["date_to"]
                if (fields.Date.to_string(line.date_to) if line.date_to else False) != date_to:
                    line.date_to = date_to or False
            version.unlink()
            contract.message_post(body=self.env._("Amendment cancelled"))
        return False

    def action_l10n_vn_next_contract(self):
        self.ensure_one()
        self._l10n_vn_check_manager()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Next Contract"),
            "res_model": "l10n_vn.contract.next.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_contract_id": self.id},
        }

    def _l10n_vn_next_contract(self, date_start, contract_type, date_end=False):
        """The next contract from ``date_start`` (D50)."""
        self.ensure_one()
        self._l10n_vn_check_manager()
        contract = self.sudo()
        last_day = date_start - datetime.timedelta(days=1)
        if last_day < contract.date_start:
            raise UserError(
                self.env._(
                    "The next contract must start after contract %(contract)s starts.",
                    contract=self.name,
                )
            )
        lines = contract.l10n_vn_line_ids._l10n_vn_in_force(last_day)
        if not contract.date_end or contract.date_end > last_day:
            contract.date_end = last_day
        values = {
            "date_start": date_start,
            "date_end": date_end or False,
            "contract_type_id": contract_type.id,
            "state": "draft",
            "kanban_state": "normal",
            "l10n_vn_probation_form": "none",
            "trial_date_end": False,
            "l10n_vn_line_ids": [],
        }
        participant = contract_type.sudo().l10n_vn_participant_type_id
        if participant:
            values["l10n_vn_participant_type_id"] = participant.id
        new = contract.copy(values)
        Line = self.env["l10n_vn.payroll.contract.line"].sudo()
        for line in lines:
            Line.create(
                {
                    "contract_id": new.id,
                    "component_id": line.component_id.id,
                    "amount": line.amount,
                    "scale_key": line.scale_key,
                    "in_cell": line.in_cell,
                    "granted_by": line.granted_by.id,
                    "review_date": line.review_date,
                    "note": line.note,
                    "date_from": date_start,
                }
            )
        return new.with_env(self.env)

    # ------------------------------------------------------------------ lock
    def _l10n_vn_locked_fields(self):
        if self.sudo().l10n_vn_amendment_id:
            return [name for name in LOCKED_FIELDS if name not in AMENDABLE_FIELDS]
        return list(LOCKED_FIELDS)

    def _l10n_vn_check_running(self, vals):
        """D27: Running only through approval where the company says so."""
        if vals.get("state") != "open":
            return
        blocked = self.sudo().filtered(
            lambda contract: contract.company_id.l10n_vn_contract_approval
            and not contract.l10n_vn_approved
            and contract.state != "open"
        )
        if blocked:
            raise ValidationError(
                self.env._(
                    "Contract %(contract)s must be approved before it runs.",
                    contract=blocked[0].name,
                )
            )

    def _l10n_vn_check_lock(self, vals):
        """D28, D29: an approved contract keeps its terms."""
        if any(name in vals for name in APPROVAL_FIELDS):
            raise ValidationError(self.env._("Only the approval sets a contract approved."))
        fields_model = self.env["ir.model.fields"]
        for contract in self.sudo().filtered("l10n_vn_approved"):
            changed = []
            for name in contract._l10n_vn_locked_fields():
                if name not in vals:
                    continue
                field = contract._fields[name]
                new = field.convert_to_record(field.convert_to_cache(vals[name], contract), contract)
                old = contract[name]
                if field.type == "html":
                    new, old = str(new or ""), str(old or "")
                if new != old:
                    changed.append(name)
            if contract.l10n_vn_amendment_id and "l10n_vn_commitment_months" in vals:
                # a repayment article is added or removed only with a new contract (D40)
                if bool(vals["l10n_vn_commitment_months"]) != bool(
                    contract.l10n_vn_commitment_months
                ):
                    changed.append("l10n_vn_commitment_months")
            if "date_end" in vals and contract.date_end:
                new_end = fields.Date.to_date(vals["date_end"])
                if not new_end or new_end > contract.date_end:
                    changed.append("date_end")
            if changed:
                labels = ", ".join(
                    fields_model._get("hr.contract", name).field_description for name in changed
                )
                raise ValidationError(
                    self.env._(
                        "Contract %(contract)s is approved: %(fields)s cannot change. Use an "
                        "amendment or a new contract.",
                        contract=contract.name,
                        fields=labels,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(UNLOCK) and any(
            name in vals for vals in vals_list for name in APPROVAL_FIELDS
        ):
            raise ValidationError(self.env._("Only the approval sets a contract approved."))
        contracts = super().create(vals_list)
        if not self.env.context.get(UNLOCK):
            blocked = contracts.sudo().filtered(
                lambda contract: contract.state == "open"
                and contract.company_id.l10n_vn_contract_approval
                and not contract.l10n_vn_approved
            )
            if blocked:
                raise ValidationError(
                    self.env._(
                        "Contract %(contract)s must be approved before it runs.",
                        contract=blocked[0].name,
                    )
                )
        return contracts

    def write(self, vals):
        if not self.env.context.get(UNLOCK):
            self._l10n_vn_check_running(vals)
            self._l10n_vn_check_lock(vals)
        return super().write(vals)

    def unlink(self):
        approved = self.sudo().filtered("l10n_vn_approved")
        if approved:
            raise UserError(
                self.env._(
                    "Contract %(contract)s is approved and cannot be deleted; cancel it instead.",
                    contract=approved[0].name,
                )
            )
        return super().unlink()

    # ------------------------------------------------------------------ actions
    def action_l10n_vn_print(self):
        for contract in self:
            if not contract._l10n_vn_document_kind_value():
                raise UserError(
                    self.env._(
                        "Contract %(contract)s has no contract document.", contract=contract.name
                    )
                )
        # config=False: the forms do not use the company's document layout, so an
        # administrator is not sent to the layout wizard first
        return self.env.ref(
            "l10n_vn_hr_contract_document.action_report_contract"
        ).report_action(self, config=False)
