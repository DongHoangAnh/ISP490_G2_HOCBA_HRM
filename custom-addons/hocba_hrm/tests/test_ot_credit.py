from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _ot_row, _ot_for_employee


@tagged('post_install', '-at_install')
class TestOtCredit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT E', 'x_employment_status': 'ctv'})
        self.env.user.tz = 'Asia/Ho_Chi_Minh'

    def _shift(self, level='150'):
        return self.env['hocba.work_shift'].create({
            'employee_id': self.emp.id,
            'start': '2026-06-15 01:00:00', 'end': '2026-06-15 09:00:00',
            'shift_type': 'ot', 'ot_level': level, 'state': 'approved'})

    def test_cong_ca_from_actual_hours(self):
        s = self._shift(level='150')   # rate 1.5
        self.env['hocba.shift.attendance'].create({
            'shift_id': s.id,
            'check_in': '2026-06-15 01:00:00',
            'check_out': '2026-06-15 09:00:00'})   # 8 giờ thực tế
        row = _ot_row(self.env, s)
        self.assertEqual(row['hours'], 8.0)
        self.assertTrue(row['counted'])
        self.assertEqual(row['congCa'], 1.5)        # 8/8 * 1.5

    def test_not_counted_without_checkin(self):
        s = self._shift()
        row = _ot_row(self.env, s)
        self.assertFalse(row['counted'])
        self.assertEqual(row['congCa'], 0.0)

    def test_employee_total_cong(self):
        s = self._shift(level='100')
        self.env['hocba.shift.attendance'].create({
            'shift_id': s.id,
            'check_in': '2026-06-15 01:00:00',
            'check_out': '2026-06-15 05:00:00'})   # 4 giờ
        res = _ot_for_employee(self.env, self.emp,
                               fields.Date.from_string('2026-06-01'),
                               fields.Date.from_string('2026-06-30'))
        self.assertEqual(res['otHours'], 4.0)
        self.assertEqual(res['otCong'], 0.5)        # 4/8 * 1.0
