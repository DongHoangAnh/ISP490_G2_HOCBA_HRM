import time
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestBatchComputePayroll(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Contract = self.env['hb.contract'].sudo()
        self.Batch = self.env['hb.payslip.run'].sudo()
        self.Slip = self.env['hb.payslip'].sudo()
        self.Rule = self.env['hb.salary.rule'].sudo()

    def test_01_batch_compute_performance_and_correctness(self):
        """Test batch calculation performance & correctness for multiple employees."""
        # 1. Create batch
        batch = self.Batch.create({
            'name': 'Batch Test Performance',
            'date_start': '2026-08-01',
            'date_end': '2026-08-31',
        })

        # 2. Create 20 test employees & contracts
        emps = []
        for i in range(20):
            emp = self.Employee.create({
                'name': f'Test Emp Batch {i+1}',
                'work_email': f'test_batch_{i+1}@hocba.edu.vn',
            })
            self.Contract.create({
                'employee_id': emp.id,
                'name': f'HD Test {i+1}',
                'state': 'open',
                'date_start': '2026-01-01',
                'wage': 10000000 + i * 500000,
            })
            emps.append(emp)

        # 3. Create payslips
        slips = self.Slip.create([{
            'employee_id': emp.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        } for emp in emps])

        # 4. Measure action_compute_batch execution time
        rules = self.Rule.search([('active', '=', True)], order='sequence, id')
        t0 = time.time()
        res = slips.action_compute_batch(prefetched_rules=rules)
        t1 = time.time()
        elapsed = t1 - t0

        # Assertions
        self.assertEqual(res['computed'], 20, 'Tất cả 20 phiếu phải được tính toán thành công.')
        self.assertEqual(len(res['errors']), 0, 'Không được có lỗi trong quá trình tính toán.')

        for slip in slips:
            self.assertTrue(slip.x_teaching_computed, 'Phiếu phải được đánh dấu x_teaching_computed = True')
            self.assertGreater(len(slip.line_ids), 0, 'Phiếu phải sinh ra các dòng lương (payslip lines)')

        print(f'\n[PERFORMANCE] Computed {len(slips)} payslips in {elapsed:.4f}s ({elapsed/len(slips)*1000:.2f}ms/slip)')
        self.assertLess(elapsed, 2.0, f'Thời gian tính 20 phiếu phải dưới 2s (Thực tế: {elapsed:.3f}s)')
