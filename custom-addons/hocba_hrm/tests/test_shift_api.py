from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _shift_row, _shift_create


@tagged('post_install', '-at_install')
class TestShiftApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV A User', 'login': 'ctv_shift_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Shift', 'login': 'hrm_shift',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.hrm.tz = 'Asia/Ho_Chi_Minh'

    def _make_shift(self, **vals):
        base = {
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00',   # T2, 09:00 local
            'end': '2026-06-15 04:00:00',     # 11:00 local
            'shift_type': 'ctv', 'rate': 1.5, 'state': 'pending',
        }
        base.update(vals)
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create(base)

    def test_shift_row_shape(self):
        s = self._make_shift()
        row = _shift_row(s)
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['shiftType'], 'ctv')
        self.assertEqual(row['rate'], 1.5)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['start'], '2026-06-15T09:00:00')
        self.assertEqual(row['end'], '2026-06-15T11:00:00')
        self.assertIsNone(row['reviewer'])

    def test_create_pins_employee_and_default_rate(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'reason': 'Trực sáng'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['rate'], 1.5)       # T2 -> 1.5
        s = env['hocba.work_shift'].browse(row['id'])
        self.assertEqual(str(s.start), '2026-06-15 02:00:00')   # 09:00+07 -> 02:00 UTC

    def test_create_weekend_rate(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-20T09:00', 'end': '2026-06-20T11:00',  # T7
            'shiftType': 'ot'})
        self.assertEqual(row['rate'], 2.0)

    def test_create_bad_type_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T09:00',
                                'end': '2026-06-15T11:00', 'shiftType': 'x'})

    def test_create_end_before_start_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T11:00',
                                'end': '2026-06-15T09:00', 'shiftType': 'ot'})

    def test_create_overlap_raises(self):
        env = self.env(user=self.user)
        _shift_create(env, {'start': '2026-06-15T09:00',
                            'end': '2026-06-15T11:00', 'shiftType': 'ctv'})
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T10:00',
                                'end': '2026-06-15T12:00', 'shiftType': 'ctv'})

    def test_create_no_employee_returns_none(self):
        u = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_shift'})
        self.assertIsNone(_shift_create(self.env(user=u), {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ot'}))

    def test_manager_add_for_employee_approved(self):
        env = self.env(user=self.hrm)
        row = _shift_create(env, {
            'empId': self.emp.id, 'start': '2026-06-16T09:00',
            'end': '2026-06-16T11:00', 'shiftType': 'ot'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['reviewer'], self.hrm.name)
