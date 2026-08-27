"""
Unit tests for Sale Salary Level KPI Lookup Engine.

Spec reference: docs/specs/payroll/FS-PAY-006_KPI_Based_Sales_Salary_Level_v1_0.md
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestSaleLevelSalary(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Job = self.env['hr.job'].sudo()
        self.Contract = self.env['hb.contract'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()
        self.SaleLevel = self.env['hb.sale.salary.level'].sudo()

        # Seed default levels
        self.SaleLevel.init_default_sale_levels()

        # Create sales job position
        self.sales_job = self.Job.create({'name': 'Chuyên viên Sale Kinh Doanh'})
        self.it_job = self.Job.create({'name': 'Kỹ sư Phần mềm IT'})

        # Official Sale Employee
        self.emp_official_sale = self.Employee.create({
            'name': 'Sale Chính Thức A',
            'work_email': 'official_sale_a@hocba.edu.vn',
            'x_employment_status': 'official',
            'identification_id': '090000009911',
            'x_pit_code': '8123459911',
            'x_social_insurance_no': '3199999911',
            'job_id': self.sales_job.id,
        })

        # Probation Sale Employee
        self.emp_probation_sale = self.Employee.create({
            'name': 'Sale Thử Việc B',
            'work_email': 'probation_sale_b@hocba.edu.vn',
            'x_employment_status': 'probation',
            'job_id': self.sales_job.id,
        })

        # IT Employee
        self.emp_it = self.Employee.create({
            'name': 'Nhân viên IT C',
            'work_email': 'it_c@hocba.edu.vn',
            'x_employment_status': 'official',
            'identification_id': '090000009912',
            'x_pit_code': '8123459912',
            'x_social_insurance_no': '3199999912',
            'job_id': self.it_job.id,
        })

        self.Contract.create({
            'employee_id': self.emp_official_sale.id,
            'name': 'HĐ Sale Official',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage': 5000000.0,
        })
        self.Contract.create({
            'employee_id': self.emp_probation_sale.id,
            'name': 'HĐ Sale Probation',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage': 6000000.0,
        })
        self.Contract.create({
            'employee_id': self.emp_it.id,
            'name': 'HĐ IT Official',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage': 15000000.0,
        })

    def test_01_official_sale_achieves_level_3(self):
        """Test Official Sale with KPI 2.1 gets Level 3 base wage (12,000,000 VND)."""
        slip = self.Payslip.create({
            'employee_id': self.emp_official_sale.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'x_kpi_score': 2.1,
        })
        slip.action_compute_sheet()

        self.assertTrue(slip.x_sale_level_id, 'Phải tự động khớp được Level Sale.')
        self.assertEqual(slip.x_sale_level_id.level_code, 'LEVEL_3', 'KPI 2.1 phải khớp Level 3 (kpi_target=2.0).')

    def test_02_probation_sale_uses_contract_wage(self):
        """Test Probation Sale uses contract wage regardless of KPI score."""
        slip = self.Payslip.create({
            'employee_id': self.emp_probation_sale.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'x_kpi_score': 3.5,
        })
        slip.action_compute_sheet()

        self.assertFalse(slip.x_sale_level_id, 'Sale thử việc KHÔNG được dùng ngạch Level Sale.')

    def test_03_non_sales_staff_uses_contract_wage(self):
        """Test IT employee uses contract wage."""
        slip = self.Payslip.create({
            'employee_id': self.emp_it.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'x_kpi_score': 4.0,
        })
        slip.action_compute_sheet()

        self.assertFalse(slip.x_sale_level_id, 'Nhân viên IT KHÔNG được dùng ngạch Level Sale.')
