from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestCheckLock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        # Bật cả 7 ngày làm việc để test once-per-day không phụ thuộc hôm nay.
        self.policy.write({
            'workday_mon': True, 'workday_tue': True, 'workday_wed': True,
            'workday_thu': True, 'workday_fri': True, 'workday_sat': True,
            'workday_sun': True, 'office_lat': 0.0, 'office_lng': 0.0,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Lock', 'x_employment_status': 'official',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789',
            'identification_id': '012345670010',
        })
        self.user = self.env['res.users'].create(
            {'name': 'Lock User', 'login': 'lock_user'})
        self.emp.user_id = self.user

    def _att(self):
        return self.env['hocba.attendance'].with_user(self.user).with_context(
            tz='Asia/Ho_Chi_Minh')

    def _payload(self):
        return {'photo': 'ZmFrZQ==', 'descriptor': [], 'latitude': 0.0,
                'longitude': 0.0}

    def test_second_checkin_rejected(self):
        self._att().action_check_in(self._payload())
        with self.assertRaises(UserError) as cm:
            self._att().action_check_in(self._payload())
        self.assertEqual(str(cm.exception), 'already_checked_in')

    def test_checkout_without_checkin_rejected(self):
        with self.assertRaises(UserError) as cm:
            self._att().action_check_out(self._payload())
        self.assertEqual(str(cm.exception), 'not_checked_in')

    def test_second_checkout_rejected(self):
        self._att().action_check_in(self._payload())
        self._att().action_check_out(self._payload())
        with self.assertRaises(UserError) as cm:
            self._att().action_check_out(self._payload())
        self.assertEqual(str(cm.exception), 'already_checked_out')

    def test_non_workday_rejected(self):
        today = fields.Date.context_today(self.user)
        flag = ['workday_mon', 'workday_tue', 'workday_wed', 'workday_thu',
                'workday_fri', 'workday_sat', 'workday_sun'][today.weekday()]
        self.policy.write({flag: False})
        with self.assertRaises(UserError) as cm:
            self._att().action_check_in(self._payload())
        self.assertEqual(str(cm.exception), 'not_workday')
