from datetime import date, datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestAttendanceIntegrationBase(TransactionCase):

    def test_fields_and_statuses_exist(self):
        Att = self.env['hocba.attendance']
        for f in ('source', 'leave_id', 'leave_half', 'leave_is_paid'):
            self.assertIn(f, Att._fields, 'thiếu field %s' % f)
        Status = self.env['hocba.attendance.status']
        self.assertTrue(Status.search([('code', '=', 'on_leave_paid')]))
        self.assertTrue(Status.search([('code', '=', 'on_leave_unpaid')]))


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestIsWorkdayExtra(TransactionCase):

    def test_extra_workday_counts_as_workday(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        # 2026-07-18 là Thứ 7 (cuối tuần) -> mặc định không phải ngày làm
        sat = datetime(2026, 7, 18, 8, 0, 0)
        self.assertFalse(policy.is_workday(sat))
        self.env['hb.work.day'].create({'date': date(2026, 7, 18), 'name': 'Làm bù'})
        self.assertTrue(policy.is_workday(sat))
        # Thứ 7 khác chưa đánh dấu vẫn False
        self.assertFalse(policy.is_workday(datetime(2026, 7, 25, 8, 0, 0)))
