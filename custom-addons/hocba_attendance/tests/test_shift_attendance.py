from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from psycopg2 import IntegrityError
from odoo.tools import mute_logger


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
