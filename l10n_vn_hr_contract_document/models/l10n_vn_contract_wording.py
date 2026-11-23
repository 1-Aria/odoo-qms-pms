# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# The generic texts of the company's own clauses (D5); a company replaces them
# with its wording record. No placeholders: values come from the templates.
DEFAULT_WORDING = {
    "duties": (
        "Thực hiện các công việc của chức danh theo bản mô tả công việc, định mức lao động "
        "và sự phân công, điều hành của người quản lý trực tiếp."
    ),
    "payday": "mỗi tháng một lần, theo Quy chế trả lương của Công ty.",
    "raises": (
        "<p>Bên B được xem xét nâng bậc, nâng lương theo điều kiện, thời gian và mức quy định "
        "trong Quy chế trả lương và thang lương, bảng lương của Công ty.</p>"
    ),
    "hours": (
        "<p>1. Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ "
        "trong 01 tuần, theo Nội quy lao động của Công ty.</p>"
        "<p>2. Làm thêm giờ: khi có nhu cầu, Bên A được tổ chức làm thêm giờ khi Bên B đồng ý, "
        "trong giới hạn của pháp luật.</p>"
        "<p>3. Nghỉ hằng tuần, nghỉ hằng năm, nghỉ lễ, tết, nghỉ việc riêng và nghỉ không hưởng "
        "lương: theo Bộ luật Lao động và Nội quy lao động của Công ty.</p>"
    ),
    "equipment": (
        "<p>Bên B được cấp phát trang bị bảo hộ lao động phù hợp với công việc theo quy định của "
        "Công ty và pháp luật về an toàn, vệ sinh lao động.</p>"
    ),
    "employee_rights": (
        "<p>1. Được trả lương đầy đủ, đúng hạn và hưởng các chế độ theo hợp đồng này, các quy chế "
        "của Công ty và pháp luật.</p>"
        "<p>2. Hoàn thành công việc được giao; chấp hành Nội quy lao động, quy định về an toàn, vệ "
        "sinh lao động và sự điều hành hợp pháp của Bên A.</p>"
        "<p>3. Bồi thường thiệt hại khi làm hư hỏng, mất tài sản của Công ty theo Nội quy lao động "
        "và pháp luật.</p>"
        "<p>4. Thông báo cho Bên A khi thay đổi nơi cư trú, số điện thoại hoặc tài khoản ngân "
        "hàng.</p>"
    ),
    "employer_rights": (
        "<p>1. Bố trí, điều hành công việc; khen thưởng và xử lý kỷ luật lao động theo Nội quy lao "
        "động và pháp luật.</p>"
        "<p>2. Trả lương đầy đủ, đúng hạn; bảo đảm điều kiện làm việc, an toàn, vệ sinh lao "
        "động.</p>"
        "<p>3. Đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp và thực hiện các nghĩa vụ "
        "khác theo hợp đồng này và pháp luật.</p>"
    ),
    "training_content": (
        "<p>Bên B được hướng dẫn thực hành công việc nêu tại Điều 1 tại nơi làm việc, dưới sự "
        "hướng dẫn của người được Bên A phân công, theo chương trình và tiêu chuẩn tay nghề của "
        "Công ty.</p>"
    ),
    "training_evaluation": (
        "<p>1. Bên A đánh giá tay nghề của Bên B trong và khi kết thúc thời gian đào tạo theo "
        "tiêu chuẩn của Công ty và thông báo kết quả cho Bên B.</p>"
        "<p>2. Bên A có quyền chấm dứt hợp đồng này trong thời gian đào tạo hoặc khi kết thúc nếu "
        "Bên B không đạt tiêu chuẩn tay nghề, sau khi thông báo kết quả đánh giá cho Bên B.</p>"
        "<p>3. Khi kết thúc thời gian đào tạo, nếu Bên B đạt tiêu chuẩn và đủ điều kiện theo Bộ "
        "luật Lao động, hai bên giao kết hợp đồng lao động.</p>"
    ),
}


class L10nVnContractWording(models.Model):
    _name = "l10n_vn.contract.wording"
    _description = "Contract Wording"
    _rec_name = "company_id"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        ondelete="cascade",
    )
    duties = fields.Text(
        string="Duties (Art. 2.2)", default=lambda self: DEFAULT_WORDING["duties"]
    )
    payday = fields.Char(
        string="Payday (Art. 3)", default=lambda self: DEFAULT_WORDING["payday"]
    )
    raises = fields.Html(string="Raises", default=lambda self: DEFAULT_WORDING["raises"])
    hours = fields.Html(
        string="Working and Rest Time", default=lambda self: DEFAULT_WORDING["hours"]
    )
    equipment = fields.Html(
        string="Protective Equipment", default=lambda self: DEFAULT_WORDING["equipment"]
    )
    employee_rights = fields.Html(
        string="Employee's Rights and Duties",
        default=lambda self: DEFAULT_WORDING["employee_rights"],
    )
    employer_rights = fields.Html(
        string="Employer's Rights and Duties",
        default=lambda self: DEFAULT_WORDING["employer_rights"],
    )
    training_content = fields.Html(
        string="Training: Content", default=lambda self: DEFAULT_WORDING["training_content"]
    )
    training_evaluation = fields.Html(
        string="Training: Evaluation and End",
        default=lambda self: DEFAULT_WORDING["training_evaluation"],
    )

    # extra articles of the forms (step 1.1, D15)
    article_ids = fields.One2many(
        "l10n_vn.contract.article",
        "wording_id",
        string="Extra Articles",
        context={"active_test": False},
    )

    _sql_constraints = [
        (
            "company_unique",
            "unique(company_id)",
            "A company has one contract wording.",
        ),
    ]

    @api.model
    def _for_company(self, company):
        """The company's wording, or an unsaved record holding the generic texts."""
        wording = self.sudo().search([("company_id", "=", company.id)], limit=1)
        if wording:
            return wording
        return self.sudo().new(dict(DEFAULT_WORDING, company_id=company.id))
