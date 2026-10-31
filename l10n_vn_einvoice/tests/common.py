# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import Command
from odoo.tests import TransactionCase
from odoo.tools import file_open

# The trading company's tax code, to which four of the six samples are addressed.
COMPANY_VAT = "0317253698"

# The other parties of the samples. Partners are shared across companies, so a
# partner on the instance holding one of these (one made by Create Supplier during
# a UI check, say) would be found by the tests' lookups. setUpClass clears them,
# inside the test transaction, which is rolled back.
SAMPLE_PARTY_VATS = [
    "0308965730",  # C26TQL394
    "0314071202",  # 1_001_C26TAA_21013_8446
    "1200253539",  # K26TDB122621
    "1701032837",  # 2_001_C26TMX_41_10860
    "1602181122",  # 1602181122_1C26TTD_130
    "3700150535",  # C26THM_10867, 10868, 10870
    "0301097482",  # C26TQP_950, 1118 (buyer)
]


class EInvoiceCase(TransactionCase):
    """Shared fixtures; holds no test methods.

    Built on TransactionCase, not on account's AccountTestInvoicingCommon: importing
    anything from odoo.addons.account.tests runs that package's __init__, which imports
    mail's tests, whose __init__ imports a subfolder this image's build deletes.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.partner"].with_context(active_test=False).search(
            [("vat", "in", SAMPLE_PARTY_VATS)]
        ).write({"vat": False})
        cls.company = cls._create_company("E-Invoice Test Company", COMPANY_VAT)
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.partner_a = cls.env["res.partner"].create({"name": "E-Invoice Test Partner"})

    @classmethod
    def _create_company(cls, name, vat, chart=True):
        """A Vietnamese company of its own, so the tests never meet the instance's
        e-invoices, taxes or journals. As core's test helpers do it
        (odoo/addons/base/tests/common.py:124-131, account/tests/common.py:295-303)."""
        company = cls.env["res.company"].create(
            {
                "name": name,
                "vat": vat,
                "country_id": cls.env.ref("base.vn").id,
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env.user.company_ids = [Command.link(company.id)]
        if chart:
            cls.env["account.chart.template"].try_loading(
                "vn", company=company, install_demo=False
            )
        return company

    @classmethod
    def _sample(cls, name):
        with file_open(f"l10n_vn_einvoice/tests/data/{name}", "rb") as handle:
            return handle.read()

    def _edited(self, name, old, new):
        content = self._sample(name)
        old, new = old.encode(), new.encode()
        self.assertEqual(content.count(old), 1, f"{old!r} must occur once in {name}")
        return content.replace(old, new)

    def _document(self, move_type="in_invoice", **values):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-10-01",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "test line",
                            "quantity": 1.0,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
                **values,
            }
        )

    def _bill(self, **values):
        return self._document("in_invoice", **values)

    def _customer_invoice(self, **values):
        return self._document("out_invoice", **values)

    def _wizard(self, content, move, filename="einvoice.xml"):
        if isinstance(content, str):
            filename, content = content, self._sample(content)
        return self.env["l10n_vn.einvoice.attach"].create(
            {
                "move_id": move.id,
                "file": base64.b64encode(content),
                "filename": filename,
            }
        )

    def _attach(self, content, move):
        """Attach a sample (by file name) or raw bytes to a document through the
        wizard; return the document's e-invoice."""
        self._wizard(content, move).action_attach()
        return move.l10n_vn_einvoice_id


class EInvoiceBillCase(EInvoiceCase):
    """Fixtures for creating bills from XML (steps 2 and 3); no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_8 = cls.env["account.tax"].create(
            {
                "name": "Test 8%",
                "amount": 8.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            }
        )
        VatCode = cls.env["l10n_vn.einvoice.tax"]
        cls.code_8 = VatCode.create({"code": "8%", "tax_id": cls.tax_8.id})
        cls.code_kkknt = VatCode.create({"code": "KKKNT"})
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "CÔNG TY TNHH QUANG QUANG LINH",
                "vat": "0308965730",
                "is_company": True,
            }
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _upload(self, content, move_type="in_invoice", user=None):
        filename = "einvoice.xml"
        if isinstance(content, str):
            filename, content = content, self._sample(content)
        env = self.env(user=user) if user else self.env
        attachment = env["ir.attachment"].create({"name": filename, "raw": content})
        action = (
            self.purchase_journal.with_env(env)
            .with_context(default_move_type=move_type)
            .create_document_from_attachment(attachment.ids)
        )
        return env["account.move"].browse(action["res_id"])

    def _replaced(self, content, old, new, count):
        if isinstance(content, str):
            content = self._sample(content)
        old, new = old.encode(), new.encode()
        self.assertEqual(content.count(old), count, f"{old!r} must occur {count} times")
        return content.replace(old, new)

    def _messages(self, record):
        return self.env["mail.message"].search(
            [("model", "=", record._name), ("res_id", "=", record.id)]
        )

    def _bodies(self, record):
        return " ".join(str(body or "") for body in self._messages(record).mapped("body"))

    def _message_count(self, record):
        return len(self._messages(record))

    def _einvoices(self):
        return self.env["l10n_vn.einvoice"].search([("company_id", "=", self.company.id)])
