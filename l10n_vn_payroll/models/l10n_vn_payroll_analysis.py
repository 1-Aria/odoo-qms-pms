# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


def _component_selection(name):
    return lambda self: self.env["l10n_vn.payroll.component"]._fields[name].selection


class L10nVnPayrollAnalysis(models.Model):
    """One row per line of a Vietnamese payslip in a run (D82)."""

    _name = "l10n_vn.payroll.analysis"
    _description = "Payroll Analysis"
    _auto = False
    _order = "date_from desc, employee_id"

    date_from = fields.Date(string="Month", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    run_id = fields.Many2one("hr.payslip.run", string="Run", readonly=True)
    run_state = fields.Selection(
        lambda self: self.env["hr.payslip.run"]._fields["state"].selection,
        string="Run Status",
        readonly=True,
    )
    payslip_id = fields.Many2one("hr.payslip", readonly=True)
    employee_id = fields.Many2one("hr.employee", readonly=True)
    department_id = fields.Many2one("hr.department", readonly=True)
    component_id = fields.Many2one("l10n_vn.payroll.component", readonly=True)
    kind = fields.Selection(_component_selection("kind"), readonly=True)
    section = fields.Selection(_component_selection("section"), readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    amount = fields.Monetary(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT line.id AS id,
                       slip.date_from AS date_from,
                       slip.company_id AS company_id,
                       run.id AS run_id,
                       run.state AS run_state,
                       slip.id AS payslip_id,
                       slip.employee_id AS employee_id,
                       employee.department_id AS department_id,
                       component.id AS component_id,
                       component.kind AS kind,
                       component.section AS section,
                       company.currency_id AS currency_id,
                       line.total AS amount
                  FROM hr_payslip_line line
                  JOIN hr_payslip slip ON slip.id = line.slip_id
                  JOIN hr_payslip_run run
                    ON run.id = slip.payslip_run_id AND run.l10n_vn_period_id IS NOT NULL
                  JOIN hr_employee employee ON employee.id = slip.employee_id
                  JOIN l10n_vn_payroll_component component
                    ON component.id = line.l10n_vn_component_id
                  JOIN res_company company ON company.id = slip.company_id
            )
            """
        )
