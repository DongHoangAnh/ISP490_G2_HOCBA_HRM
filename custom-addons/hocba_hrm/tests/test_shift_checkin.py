from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestShiftCheckin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({'shift_window_minutes': 15,
                           'office_lat': 0.0, 'office_lng': 0.0})
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV Ca', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV Ca User', 'login': 'ctv_ca_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        self.Att = self.env['hocba.attendance']
        self.WS = self.env['hocba.work_shift']

    def _shift(self, start, end, state='approved'):
        return self.WS.sudo().create({
            'employee_id': self.emp.id, 'start': start, 'end': end,
            'shift_type': 'ot', 'state': state})

    def _att(self, **vals):
        v = {'employee_id': self.emp.id}
        v.update(vals)
        return self.Att.sudo().create(v)

    def test_todays_approved_shifts_filters(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=1))
        self._shift(now + timedelta(days=2), now + timedelta(days=2, hours=1))  # khác ngày
        today = fields.Datetime.context_timestamp(
            self.env(user=self.user).user, now).date()
        env = self.env(user=self.user)
        found = env['hocba.attendance']._todays_approved_shifts(self.emp, today)
        self.assertEqual(len(found), 1)

    def test_checkin_within_window_ok(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=2))
        env = self.env(user=self.user)
        env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')

    def test_no_shift_today_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'no_shift_today')

    def test_outside_window_raises(self):
        now = fields.Datetime.now()
        self._shift(now + timedelta(hours=3), now + timedelta(hours=5))
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'outside_shift_window')

    def test_pending_shift_not_counted(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=1), state='pending')
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'no_shift_today')

    def test_already_checked_in_raises(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=2))
        self._att(check_in=now)
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'already_checked_in')

    def test_checkout_not_checked_in_raises(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(hours=2), now + timedelta(minutes=5))
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'out')
        self.assertEqual(str(e.exception), 'not_checked_in')

    def test_checkout_within_window_ok(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(hours=2), now + timedelta(minutes=5))
        self._att(check_in=now - timedelta(hours=2))
        env = self.env(user=self.user)
        env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'out')

    def test_checkout_already_checked_out_raises(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(hours=2), now + timedelta(minutes=5))
        self._att(check_in=now - timedelta(hours=2), check_out=now - timedelta(minutes=1))
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'out')
        self.assertEqual(str(e.exception), 'already_checked_out')
