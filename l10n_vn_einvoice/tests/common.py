# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import Command
from odoo.tests import TransactionCase
from odoo.tools import file_open

# The trading company's tax code, to which four of the six samples are addressed.
COMPANY_VAT = "0317253698"


class EInvoiceCase(TransactionCase):
    """Shared fixtures; holds no test methods.

    Built on TransactionCase, not on account's AccountTestInvoicingCommon: importing
    anything from odoo.addons.account.tests runs that package's __init__, which imports
    mail's tests, whose __init__ imports a subfolder this image's build deletes.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
