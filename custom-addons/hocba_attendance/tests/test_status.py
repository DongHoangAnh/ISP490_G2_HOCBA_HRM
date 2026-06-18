import json

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAttendanceStatus(TransactionCase):

    def setUp(self):
        super().setUp()
        # Default policy has morning_start = 8.0 (08:00 local is the late cutoff)
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({'morning_start': 8.0, 'morning_end': 9.5,
                           'late_cutoff': 9.5})
        self.employee = self.env['hr.employee'].create({
            'name': 'Nguyen Van A',
            'x_employment_status': 'official',
            # BR-010: official employees must declare CCCD (12 digits) + MST + BHXH
            'identification_id': '012345678901',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
        })

    def test_status_records_are_seeded(self):
        """Bug #1: on_time / late statuses must exist out of the box."""
        Status = self.env['hocba.attendance.status']
        self.assertTrue(Status.search([('code', '=', 'on_time')], limit=1))
        self.assertTrue(Status.search([('code', '=', 'late')], limit=1))

    def test_checkin_before_cutoff_is_on_time(self):
        """Status dùng LOCAL time. 02:20 UTC = 09:20 +07 -> trước 09:30 -> on_time."""
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({
            'employee_id': self.employee.id,
            'check_in': '2026-06-11 02:20:00',  # 09:20 local, trước 09:30
        })
        self.assertEqual(rec.status_code, 'on_time')

    def test_checkin_after_cutoff_is_late(self):
        """02:40 UTC = 09:40 +07 -> sau mốc 09:30 -> late."""
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({
            'employee_id': self.employee.id,
            'check_in': '2026-06-11 02:40:00',  # 09:40 local, sau 09:30
        })
        self.assertEqual(rec.status_code, 'late')
