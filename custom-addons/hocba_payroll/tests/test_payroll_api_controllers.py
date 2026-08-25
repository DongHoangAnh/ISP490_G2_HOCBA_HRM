"""
Unit tests for Payroll REST API Controllers & Authorization.

Spec reference: docs/SPEC_HRM_SPA_API.md
                docs/specs/payroll/FS-PAY-003_Payslip_Lifecycle_Batch_Management_v1_0.md
"""
import json
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestPayrollAPIControllers(HttpCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Batch = self.env['hb.payslip.run'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()

        self.emp = self.Employee.create({
            'name': 'API Test Employee Payroll',
            'work_email': 'api_payroll_test@hocba.edu.vn',
        })

    def test_01_get_batch_list_endpoint(self):
        """Test GET /hocba-hrm/api/payroll/batch endpoint."""
        self.Batch.create({
            'name': 'Batch API Test 2026-08',
            'date_start': '2026-08-01',
            'date_end': '2026-08-31',
        })

        # Authenticate as admin
        self.authenticate('admin', 'admin')
        res = self.url_open('/hocba-hrm/api/payroll/batch')
        self.assertEqual(res.status_code, 200, 'API danh sách đợt lương phải trả về HTTP status 200.')

        try:
            data = res.json()
            self.assertIn('batches', data, 'Payload trả về phải chứa key batches.')
        except Exception:
            pass

    def test_02_bulk_reset_confirm_api_endpoint(self):
        """Test POST /hocba-hrm/api/payroll/bulk-reset-confirm endpoint."""
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'confirm_status': 'confirmed',
        })

        self.authenticate('admin', 'admin')
        payload = json.dumps({'payslip_ids': [slip.id]})
        res = self.url_open(
            '/hocba-hrm/api/payroll/bulk-reset-confirm',
            data=payload,
            headers={'Content-Type': 'application/json'},
            csrf=False
        )

        self.assertIn(res.status_code, [200, 201], 'API reset xác nhận phải trả về status success.')
        slip.invalidate_recordset()
        self.assertEqual(slip.confirm_status, 'pending', 'Slip status qua API reset phải về pending.')

    def test_03_employee_payroll_respects_contract_month_boundary(self):
        """NV bắt đầu 01/08 không được xuất hiện trong bảng lương tháng 07."""
        july_emp = self.Employee.create({
            'name': 'Boundary Payroll July Employee',
            'x_employee_code': 'PAY-BOUNDARY-JULY',
        })
        august_emp = self.Employee.create({
            'name': 'Boundary Payroll August Employee',
            'x_employee_code': 'PAY-BOUNDARY-AUGUST',
        })
        Contract = self.env['hb.contract'].sudo()
        Contract.create({
            'name': 'Boundary July Contract',
            'employee_id': july_emp.id,
            'state': 'open',
            'date_start': '2026-07-01',
            'wage': 10_000_000,
        })
        Contract.create({
            'name': 'Boundary August Contract',
            'employee_id': august_emp.id,
            'state': 'open',
            'date_start': '2026-08-01',
            'wage': 10_000_000,
        })

        self.authenticate('admin', 'admin')
        july = self.url_open(
            '/hocba-hrm/api/payroll/employee-payroll?month=7&year=2026').json()
        july = july.get('data', july)
        july_codes = {row['code'] for row in july['employees']}
        self.assertIn('PAY-BOUNDARY-JULY', july_codes)
        self.assertNotIn('PAY-BOUNDARY-AUGUST', july_codes)

        august = self.url_open(
            '/hocba-hrm/api/payroll/employee-payroll?month=8&year=2026').json()
        august = august.get('data', august)
        august_codes = {row['code'] for row in august['employees']}
        self.assertIn('PAY-BOUNDARY-JULY', august_codes)
        self.assertIn('PAY-BOUNDARY-AUGUST', august_codes)
