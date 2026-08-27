"""
Unit tests for Role Allowance Matrix & Bulk Bonus Penalty Wizard API.

Spec reference: docs/specs/payroll/FS-PAY-007_Role_Based_Allowances_And_Bulk_Bonus_Penalty_v1_0.md
"""
import json
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestRoleAllowanceBulk(HttpCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Job = self.env['hr.job'].sudo()
        self.Batch = self.env['hb.payslip.run'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()
        self.RoleCfg = self.env['hb.role.allowance.config'].sudo()

        self.mgr_job = self.Job.create({'name': 'Trưởng phòng Kinh doanh'})

        self.emp = self.Employee.create({
            'name': 'Trưởng phòng Test Bulk',
            'work_email': 'tp_test_bulk@hocba.edu.vn',
            'job_id': self.mgr_job.id,
        })

    def test_01_role_allowance_auto_computation(self):
        """Test matching role allowance automatically added to payslip."""
        self.RoleCfg.create({
            'name': 'Phụ cấp Trách nhiệm Trưởng phòng',
            'job_id': self.mgr_job.id,
            'allowance_type': 'responsibility',
            'amount': 3000000.0,
        })

        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        slip.action_compute_sheet()

        self.assertEqual(slip.x_role_allowance_amount, 3000000.0, 'Phụ cấp trách nhiệm trưởng phòng phải bằng 3,000,000 VND.')

    def test_02_bulk_bonus_penalty_api(self):
        """Test POST /hocba-hrm/api/payroll/batch/<id>/bulk-bonus-penalty endpoint."""
        batch = self.Batch.create({
            'name': 'Đợt Test Bulk Bonus',
            'date_start': '2026-08-01',
            'date_end': '2026-08-31',
        })
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        })

        self.authenticate('admin', 'admin')
        payload = json.dumps({
            'payslipIds': [slip.id],
            'bonusAmount': 1000000.0,
            'bonusReason': 'Thưởng hiệu suất vượt trội',
            'penaltyAmount': 200000.0,
            'penaltyReason': 'Vi phạm nội quy đi trễ',
        })

        res = self.url_open(
            f'/hocba-hrm/api/payroll/batch/{batch.id}/bulk-bonus-penalty',
            data=payload,
            headers={'Content-Type': 'application/json'},
        )

        self.assertIn(res.status_code, [200, 201])
        slip.invalidate_recordset()
        self.assertEqual(slip.x_bonus_extra, 1000000.0)
        self.assertEqual(slip.x_penalty_amount, 200000.0)
        self.assertEqual(
            slip.line_ids.filtered(lambda line: line.code == 'bonus_extra').amount,
            1000000.0,
        )
        self.assertEqual(
            slip.line_ids.filtered(lambda line: line.code == 'penalty_amount').amount,
            200000.0,
        )
