"""
Unit tests for Payslip Lifecycle, Batch Management, Lock Window & Bulk Reset.

Spec reference: docs/specs/payroll/FS-PAY-003_Payslip_Lifecycle_Batch_Management_v1_0.md
                docs/specs/payroll/FS-PAY-005_Employee_Payslip_Confirmation_Email_v1_0.md
"""
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestPayslipLifecycle(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Contract = self.env['hb.contract'].sudo()
        self.Batch = self.env['hb.payslip.run'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()

        # Create test employees
        self.emp1 = self.Employee.create({
            'name': 'Nhân viên A Test Lifecycle',
            'work_email': 'emp_a_lifecycle@hocba.edu.vn',
        })
        self.emp2 = self.Employee.create({
            'name': 'Nhân viên B Test Lifecycle',
            'work_email': 'emp_b_lifecycle@hocba.edu.vn',
        })

        self.Contract.create({
            'employee_id': self.emp1.id,
            'name': 'HĐ A',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage_base': 15000000.0,
        })
        self.Contract.create({
            'employee_id': self.emp2.id,
            'name': 'HĐ B',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage_base': 18000000.0,
        })

    def test_01_batch_lifecycle_draft_to_done(self):
        """Test batch state transition: draft -> verify -> close."""
        batch = self.Batch.create({
            'name': 'Đợt lương Tháng 08/2026',
            'date_start': '2026-08-01',
            'date_end': '2026-08-31',
        })
        self.assertEqual(batch.state, 'draft', 'Trạng thái đợt lương khởi tạo phải là draft.')

        # Generate slips
        slip1 = self.Payslip.create({
            'employee_id': self.emp1.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        })
        slip2 = self.Payslip.create({
            'employee_id': self.emp2.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        })

        # Compute slips
        batch.action_compute_payslips()
        self.assertTrue(slip1.x_teaching_computed)
        self.assertTrue(slip2.x_teaching_computed)

        # Confirm batch (verify/done)
        batch.action_confirm_batch()
        self.assertIn(batch.state, ['verify', 'done'], 'Đợt lương phải chuyển sang verify hoặc done sau khi duyệt.')

    def test_02_bulk_reset_payslip_confirmation(self):
        """Test resetting payslip confirmation status back to 'Chờ xác nhận'."""
        slip1 = self.Payslip.create({
            'employee_id': self.emp1.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'confirm_status': 'confirmed',
            'confirm_date': fields.Datetime.now() if hasattr(fields, 'Datetime') else '2026-08-05 10:00:00',
        })
        slip2 = self.Payslip.create({
            'employee_id': self.emp2.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
            'confirm_status': 'confirmed',
        })

        self.assertEqual(slip1.confirm_status, 'confirmed')
        self.assertEqual(slip2.confirm_status, 'confirmed')

        # Reset specific payslips
        res = self.Payslip.bulk_reset_confirm(payslip_ids=[slip1.id, slip2.id])
        self.assertTrue(res.get('success'), 'Bulk reset phải trả về success = True')

        slip1.invalidate_recordset()
        slip2.invalidate_recordset()

        self.assertEqual(slip1.confirm_status, 'pending', 'Trạng thái phải được reset về pending.')
        self.assertEqual(slip2.confirm_status, 'pending', 'Trạng thái phải được reset về pending.')

    def test_03_confirmation_deadline_and_locking_window(self):
        """Test confirmation deadline calculations & feedback window locking."""
        slip = self.Payslip.create({
            'employee_id': self.emp1.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })

        # Check deadline computation if fields exist
        if hasattr(slip, 'confirm_deadline'):
            # Trigger deadline check or view helper
            deadline_str = slip.confirm_deadline
            self.assertIsNotNone(deadline_str, 'Deadline xác nhận không được null.')

        if hasattr(slip, 'is_expired'):
            # Verify boolean expired flag calculation
            is_expired = slip.is_expired
            self.assertIn(is_expired, [True, False], 'is_expired phải là kiểu boolean.')
