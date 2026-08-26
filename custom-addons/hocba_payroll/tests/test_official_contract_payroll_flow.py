"""Integration: probation -> official -> contract -> attendance -> payroll."""
from datetime import date, datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll', 'contract_payroll_flow')
class TestOfficialContractPayrollFlow(TransactionCase):

    def test_official_employee_is_paid_through_auto_contract(self):
        employee = self.env['hr.employee'].sudo().create({
            'name': 'E2E Hợp đồng đến tính lương',
            'x_employee_code': 'E2E-HD-PAY-001',
            'identification_id': '090000009901',
            'x_pit_code': '8123459901',
            'x_social_insurance_no': '3199999901',
            'x_employment_status': 'probation',
            'x_work_form': 'offline',
        })
        employee.version_id.sudo().write({'wage': 20_000_000})

        employee.write({
            'x_employment_status': 'official',
            'x_official_date': date(2026, 8, 1),
        })

        contract = self.env['hb.contract'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'open'),
        ])
        self.assertEqual(len(contract), 1)
        self.assertEqual(contract.date_start, date(2026, 8, 1))
        self.assertEqual(contract.wage, 20_000_000)

        Attendance = self.env['hocba.attendance'].sudo()
        for day in range(1, 26):
            check_in = datetime(2026, 8, day, 1, 0, 0)  # 08:00 Asia/Ho_Chi_Minh
            Attendance.create({
                'employee_id': employee.id,
                'check_in': check_in,
                'check_out': check_in + timedelta(hours=8),
            })
        self.assertEqual(sum(Attendance.search([
            ('employee_id', '=', employee.id),
        ]).mapped('work_credit')), 25)

        batch = self.env['hb.payslip.run'].sudo().create({
            'name': 'E2E Hợp đồng - Lương 08/2026',
            'date_start': date(2026, 8, 1),
            'date_end': date(2026, 8, 31),
        })
        slip = self.env['hb.payslip'].sudo().create({
            'employee_id': employee.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        })
        slip.action_compute_batch()

        self.assertTrue(slip.x_teaching_computed)
        self.assertEqual(slip.contract_id, contract)
        self.assertTrue(slip.line_ids)
        self.assertEqual(slip.line_ids.filtered(
            lambda line: line.code == 'luong_co_ban').amount, 20_000_000)
        self.assertEqual(slip.line_ids.filtered(
            lambda line: line.code == 'nctt').amount, 25)
        self.assertGreater(slip.gross_amount, 0)
        self.assertGreater(slip.net_amount, 0)
        self.assertLessEqual(slip.net_amount, slip.gross_amount)
