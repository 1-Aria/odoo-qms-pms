# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import D, ContractDocumentCase

REPORT = "l10n_vn_hr_contract_document.action_report_contract"


@tagged("post_install", "-at_install")
class TestDocumentArticles(ContractDocumentCase):
    def _html(self, contract):
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(REPORT, contract.ids)
        return html.decode()

    def _article(self, kind, title, sequence=10, company=None, **values):
        company = company or self.company
        Wording = self.env["l10n_vn.contract.wording"]
        wording = Wording.search([("company_id", "=", company.id)]) or Wording.create(
            {"company_id": company.id}
        )
        return self.env["l10n_vn.contract.article"].create(
            dict(
                {
                    "wording_id": wording.id,
                    "kind": kind,
                    "title": title,
                    "sequence": sequence,
                    "body": f"<p>Nội dung {title}</p>",
                },
                **values,
            )
        )

    def test_extra_articles_numbered_after_fixed(self):
        self._article("labour", "Đồng phục", sequence=20)
        self._article("labour", "Bảo mật thông tin", sequence=10)
        contract = self._doc_contract("labour")
        values = contract._l10n_vn_document_values()
        self.assertEqual(
            [(a["number"], a["title"]) for a in values["extra_articles"]],
            [(12, "Bảo mật thông tin"), (13, "Đồng phục")],
        )
        self.assertEqual(values["closing_number"], 14)
        html = self._html(contract)
        self.assertIn("Điều 12. Bảo mật thông tin", html)
        self.assertIn("Nội dung Bảo mật thông tin", html)
        self.assertIn("Điều 14. Điều khoản thi hành", html)

    def test_extra_articles_by_form(self):
        self._article("probation", "Bảo mật thông tin")
        labour = self._doc_contract("labour")
        self.assertEqual(labour._l10n_vn_document_values()["extra_articles"], [])
        probation = self._doc_contract(
            "probation", date_end=D(2026, 12, 1), l10n_vn_probation_job="college"
        )
        html = self._html(probation)
        self.assertIn("Điều 7. Bảo mật thông tin", html)
        self.assertIn("Điều 8. Điều khoản thi hành", html)

    def test_inactive_article_not_printed(self):
        self._article("labour", "Đồng phục", active=False)
        values = self._doc_contract("labour")._l10n_vn_document_values()
        self.assertEqual(values["extra_articles"], [])
        self.assertEqual(values["closing_number"], 12)

    def test_individual_terms(self):
        self._article("labour", "Đồng phục")
        contract = self._doc_contract(
            "labour", l10n_vn_individual_terms="<p>Bên B được bố trí xe đưa đón.</p>"
        )
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["individual_terms"]["number"], 13)
        self.assertEqual(values["closing_number"], 14)
        html = self._html(contract)
        self.assertIn("Điều 13. Thỏa thuận khác", html)
        self.assertIn("Bên B được bố trí xe đưa đón.", html)
        contract.l10n_vn_individual_terms = "<p><br></p>"
        values = contract._l10n_vn_document_values()
        self.assertIsNone(values["individual_terms"])
        self.assertEqual(values["closing_number"], 13)

    def test_training_articles_after_repayment(self):
        self._article("training", "Nội quy tập nghề")
        contract = self._doc_contract(
            "training", date_end=D(2027, 1, 31), l10n_vn_commitment_months=6
        )
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["extra_articles"][0]["number"], 8)
        self.assertEqual(values["closing_number"], 9)
        html = self._html(contract)
        self.assertIn("Điều 7. Cam kết làm việc và hoàn trả chi phí đào tạo", html)
        self.assertIn("Điều 8. Nội quy tập nghề", html)
        self.assertIn("Điều 9. Điều khoản thi hành", html)

    def test_articles_of_other_company_ignored(self):
        other = self.env["res.company"].create(
            {
                "name": "Other Document Company",
                "country_id": self.env.ref("base.vn").id,
                "currency_id": self.env.ref("base.VND").id,
            }
        )
        self._article("labour", "Đồng phục", company=other)
        values = self._doc_contract("labour")._l10n_vn_document_values()
        self.assertEqual(values["extra_articles"], [])
        self.assertEqual(values["closing_number"], 12)
