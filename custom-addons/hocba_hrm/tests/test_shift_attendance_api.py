from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError, AccessError

from odoo.addons.hocba_hrm.controllers.main import _shift_check, _shift_today_rows


@tagged('post_install', '-at_install')
class TestShiftAttendanceApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT D', 'x_employment_status': 'official',
            'identification_id': '123456789012',
            'x_pit_code': '1234567890', 'x_social_insurance_no': '1111111111'})
        self.user = self.env['res.users'].create({
            'name': 'OT D User', 'login': 'ot_d_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user

    def _shift_now(self, **vals):
        now = fields.Datetime.now()
        base = {'employee_id': self.emp.id, 'start': now, 'end': now + timedelta(hours=2),
                'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'}
        base.update(vals)
        return self.env['hocba.work_shift'].create(base)

    def test_shift_today_rows_shape(self):
        s = self._shift_now()
        env = self.env(user=self.user)
        rows = _shift_today_rows(env, self.emp)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], s.id)
        self.assertTrue(rows[0]['checkInOpen'])
        self.assertFalse(rows[0]['checkIn'])
        self.assertFalse(rows[0]['checkOutOpen'])

    def test_shift_check_in_then_out(self):
        now = fields.Datetime.now()
        s = self._shift_now(end=now + timedelta(minutes=1))
        env = self.env(user=self.user)
        res = _shift_check(env, s.id, 'in', {'descriptor': [], 'latitude': 0, 'longitude': 0})
        self.assertEqual(res['kind'], 'in')
        att = env['hocba.shift.attendance'].sudo().search([('shift_id', '=', s.id)])
        self.assertTrue(att.check_in)
        res2 = _shift_check(env, s.id, 'out', {'descriptor': [], 'latitude': 0, 'longitude': 0})
        self.assertEqual(res2['kind'], 'out')
        att = env['hocba.shift.attendance'].sudo().search([('shift_id', '=', s.id)])
        self.assertTrue(att.check_out)

    def test_shift_check_other_employee_forbidden(self):
        other = self.env['hr.employee'].create({
            'name': 'X', 'x_employment_status': 'official',
            'identification_id': '999888777666',
            'x_pit_code': '9876543210', 'x_social_insurance_no': '2222222222'})
        s = self._shift_now(employee_id=other.id)
        env = self.env(user=self.user)
        with self.assertRaises(AccessError):
            _shift_check(env, s.id, 'in', {'descriptor': [], 'latitude': 0, 'longitude': 0})

    def test_shift_check_nonexistent_raises_no_shift(self):
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            _shift_check(env, 999999, 'in', {'descriptor': [], 'latitude': 0, 'longitude': 0})
        self.assertEqual(str(e.exception), 'no_shift')
