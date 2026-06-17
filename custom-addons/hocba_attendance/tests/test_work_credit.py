from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestWorkCreditPolicy(TransactionCase):

    def test_policy_credit_defaults(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        self.assertEqual(policy.late_cutoff, 9.5)
        self.assertEqual(policy.morning_credit_cutoff, 10.0)
        self.assertEqual(policy.std_work_hours, 8.0)
        self.assertEqual(policy.afternoon_margin_hours, 2.0)
        self.assertEqual(policy.violation_free_days, 2)


@tagged('post_install', '-at_install')
class TestWorkCreditFields(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'late_cutoff': 9.5, 'morning_credit_cutoff': 10.0,
            'std_work_hours': 8.0, 'afternoon_margin_hours': 2.0,
            'violation_free_days': 2,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Cong',
            'x_employment_status': 'official',
            # BR-010: official employees must declare CCCD (12 digits) + MST + BHXH
            'identification_id': '012345678901',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
        })

    def _rec(self, check_in, check_out=None):
        # Giờ truyền vào là UTC (chuỗi). tz context = Asia/Ho_Chi_Minh (+07).
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        vals = {'employee_id': self.emp.id, 'check_in': check_in}
        if check_out:
            vals['check_out'] = check_out
        return Att.create(vals)

    def test_full_day_one_credit(self):
        # 09:00–17:00 local = 02:00–10:00 UTC, đủ 8h
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 10:00:00')
        self.assertEqual(rec.work_credit, 1.0)
        self.assertEqual(rec.late_minutes, 0)
        self.assertEqual(rec.missing_minutes, 0)
        self.assertEqual(rec.early_leave_minutes, 0)
        self.assertEqual(rec.morning_credit, 0.5)
        self.assertEqual(rec.afternoon_credit, 0.5)

    def test_late_but_keeps_morning_credit(self):
        # check-in 09:45 local = 02:45 UTC -> trễ 15', vẫn trước 10:00
        rec = self._rec('2026-06-17 02:45:00', '2026-06-17 10:45:00')
        self.assertEqual(rec.late_minutes, 15)
        self.assertEqual(rec.morning_credit, 0.5)

    def test_after_ten_loses_morning_credit(self):
        # check-in 10:30 local = 03:30 UTC
        rec = self._rec('2026-06-17 03:30:00', '2026-06-17 11:30:00')
        self.assertEqual(rec.morning_credit, 0.0)
        self.assertEqual(rec.late_minutes, 60)
        self.assertEqual(rec.work_credit, 0.5)

    def test_early_checkout_loses_afternoon_credit(self):
        # 09:00 in (02:00 UTC), 14:00 out (07:00 UTC) = chỉ 5h, < check_in+6h
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 07:00:00')
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.missing_minutes, 180)
        self.assertEqual(rec.early_leave_minutes, 180)

    def test_no_checkout_no_missing(self):
        rec = self._rec('2026-06-17 02:00:00')
        self.assertEqual(rec.missing_minutes, 0)
        self.assertEqual(rec.early_leave_minutes, 0)
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.work_credit, 0.5)  # chỉ có công sáng
