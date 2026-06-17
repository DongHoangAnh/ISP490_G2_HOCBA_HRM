import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _req_row


@tagged('post_install', '-at_install')
class TestAttendanceRequest(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
            'office_lat': 0.0, 'office_lng': 0.0,
            'std_work_hours': 8.0, 'violation_free_days': 2,
        })
        # NV gửi đơn + user của họ
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Don', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789',
        })
        self.user = self.env['res.users'].create({
            'name': 'NV Don User', 'login': 'nv_req_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        # HR Manager
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Req', 'login': 'hrm_req',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.hrm.tz = 'Asia/Ho_Chi_Minh'

    def _make_req(self, **vals):
        base = {
            'employee_id': self.emp.id, 'request_date': '2026-06-12',
            'reason': 'Quên bấm', 'state': 'pending',
        }
        base.update(vals)
        return self.env['hocba.attendance.request'].create(base)

    def test_req_row_shape(self):
        req = self._make_req()
        row = _req_row(req)
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['requestDate'], '2026-06-12')
        self.assertEqual(row['state'], 'pending')
        self.assertIsNone(row['attendanceId'])
        self.assertIsNone(row['reviewer'])
        self.assertEqual(row['reason'], 'Quên bấm')
