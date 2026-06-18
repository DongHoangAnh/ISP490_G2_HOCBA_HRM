from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _shift_row


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
