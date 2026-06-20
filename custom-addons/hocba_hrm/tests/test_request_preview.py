from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _request_create, _request_preview


@tagged('post_install', '-at_install')
class TestRequestPreview(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'NV B', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789'})
        self.user = self.env['res.users'].create({
            'name': 'NV B', 'login': 'nvb_prev',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp.user_id = self.user
        self.mgr = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_prev',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.att = self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'check_in': '2026-06-17 02:00:00'})

    def test_create_requires_attendance_id(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'reason': 'quên', 'requestDate': '2026-06-17'})

    def test_create_with_record_ok(self):
        env = self.env(user=self.user)
        row = _request_create(env, {'attendanceId': self.att.id, 'reason': 'quên ra',
                                    'checkOut': '2026-06-17T17:00'})
        self.assertEqual(row['attendanceId'], self.att.id)

    def test_preview_recomputes_full_day(self):
        env = self.env(user=self.user)
        row = _request_create(env, {'attendanceId': self.att.id, 'reason': 'quên ra'})
        req = self.env['hocba.attendance.request'].browse(row['id'])
        # 09:00-17:00 local = 02:00-10:00 UTC = du 8h, du cong
        out = _request_preview(self.env(user=self.mgr), req.id,
                               {'checkIn': '2026-06-17T09:00', 'checkOut': '2026-06-17T17:00'})
        self.assertEqual(out['workCredit'], 1.0)
        self.assertEqual(out['missingMinutes'], 0)
        self.assertFalse(out['needsReview'])
