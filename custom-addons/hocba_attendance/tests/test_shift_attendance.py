from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from psycopg2 import IntegrityError
from odoo.tools import mute_logger
from odoo import fields
from datetime import timedelta
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestShiftAttendanceModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV B', 'x_employment_status': 'ctv'})
        self.shift = self.env['hocba.work_shift'].create({
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00', 'end': '2026-06-15 06:00:00',
            'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'})

    def test_worked_hours_and_employee_related(self):
        att = self.env['hocba.shift.attendance'].create({
            'shift_id': self.shift.id,
            'check_in': '2026-06-15 02:00:00',
            'check_out': '2026-06-15 06:00:00'})
        self.assertEqual(att.employee_id, self.emp)
        self.assertAlmostEqual(att.worked_hours, 4.0, places=2)

    def test_worked_hours_zero_without_checkout(self):
        att = self.env['hocba.shift.attendance'].create({
            'shift_id': self.shift.id, 'check_in': '2026-06-15 02:00:00'})
        self.assertEqual(att.worked_hours, 0.0)

    @mute_logger('odoo.sql_db')
    def test_one_record_per_shift(self):
        self.env['hocba.shift.attendance'].create({'shift_id': self.shift.id})
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['hocba.shift.attendance'].create({'shift_id': self.shift.id})


@tagged('post_install', '-at_install')
class TestShiftAttendanceCheck(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT C', 'x_employment_status': 'ctv',
            'x_face_descriptor': False})
        self.SA = self.env['hocba.shift.attendance']

    def _shift_now(self, **vals):
        now = fields.Datetime.now()
        base = {'employee_id': self.emp.id, 'start': now, 'end': now + timedelta(hours=2),
                'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'}
        base.update(vals)
        return self.env['hocba.work_shift'].create(base)

    def test_check_in_within_window_creates_record(self):
        s = self._shift_now()
        rec = self.SA._do_check(s, {'descriptor': [], 'latitude': 0, 'longitude': 0}, 'in')
        self.assertTrue(rec.check_in)
        self.assertEqual(rec.shift_id, s)

    def test_assert_outside_window_raises(self):
        s = self._shift_now(start=fields.Datetime.now() + timedelta(hours=5),
                            end=fields.Datetime.now() + timedelta(hours=7))
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'outside_shift_window')

    def test_assert_not_approved_raises(self):
        s = self._shift_now(state='pending')
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'shift_not_approved')

    def test_double_check_in_raises(self):
        s = self._shift_now()
        self.SA._do_check(s, {'descriptor': [], 'latitude': 0, 'longitude': 0}, 'in')
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'already_checked_in')

    def test_assert_not_checked_in_raises(self):
        # end within window (1 min ahead) so window check passes, exposing not_checked_in
        s = self._shift_now(end=fields.Datetime.now() + timedelta(minutes=1))
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'out')
        self.assertEqual(str(e.exception), 'not_checked_in')

    def test_assert_already_checked_out_raises(self):
        # end within window (1 min ahead) so window check passes, exposing already_checked_out
        s = self._shift_now(end=fields.Datetime.now() + timedelta(minutes=1))
        payload = {'descriptor': [], 'latitude': 0, 'longitude': 0}
        self.SA._do_check(s, payload, 'in')
        self.SA._do_check(s, payload, 'out')
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'out')
        self.assertEqual(str(e.exception), 'already_checked_out')
