import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _req_row, _request_apply, _request_create


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

    def test_apply_updates_existing_record(self):
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': self.emp.id,
                          'check_in': '2026-06-12 02:00:00',    # 09:00 local
                          'check_out': '2026-06-12 07:00:00'})  # 5h -> thiếu 180
        self.assertEqual(rec.missing_minutes, 180)
        req = self._make_req(attendance_id=rec.id)
        # 09:00 -> 17:00 local = 8h đủ công. _to_utc nhận local ISO.
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        env = self.env(user=self.hrm)
        out = _request_apply(env, req.with_env(env), None,
                             _to_utc(env, '2026-06-12T17:00'))
        self.assertEqual(out, rec)
        self.assertEqual(rec.missing_minutes, 0)

    def test_apply_creates_record_for_missing_day(self):
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        req = self._make_req(request_date='2026-06-13')
        env = self.env(user=self.hrm)
        ci = _to_utc(env, '2026-06-13T09:00')
        co = _to_utc(env, '2026-06-13T17:00')
        rec = _request_apply(env, req.with_env(env), ci, co)
        self.assertTrue(rec.exists())
        self.assertEqual(rec.employee_id, self.emp)
        self.assertEqual(req.attendance_id, rec)
        self.assertEqual(rec.check_in, ci)
        self.assertEqual(rec.check_out, co)

    def test_apply_missing_day_without_checkin_raises(self):
        req = self._make_req(request_date='2026-06-14')
        env = self.env(user=self.hrm)
        with self.assertRaises(ValidationError):
            _request_apply(env, req.with_env(env), None, None)

    def test_create_pins_employee_and_converts_utc(self):
        env = self.env(user=self.user)
        row = _request_create(env, {
            'requestDate': '2026-06-12',
            'checkIn': '2026-06-12T08:10',
            'reason': 'Điện thoại hết pin',
        })
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        req = env['hocba.attendance.request'].browse(row['id'])
        # 08:10 local (+07) -> 01:10 UTC stored
        self.assertEqual(str(req.proposed_check_in), '2026-06-12 01:10:00')

    def test_create_empty_reason_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'requestDate': '2026-06-12', 'reason': '  '})

    def test_create_no_employee_returns_none(self):
        u = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_req'})
        self.assertIsNone(_request_create(self.env(user=u),
                                          {'requestDate': '2026-06-12',
                                           'reason': 'x'}))

    def test_create_foreign_attendance_rejected(self):
        other = self.env['hr.employee'].create({
            'name': 'NV Khac', 'x_employment_status': 'official',
            'identification_id': '012345678902',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776'})
        rec = self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': other.id, 'check_in': '2026-06-12 02:00:00'})
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'requestDate': '2026-06-12',
                                  'attendanceId': rec.id, 'reason': 'x'})

    def test_create_derives_date_from_attendance(self):
        # Đính kèm bản ghi của chính mình, KHÔNG gửi requestDate -> lấy theo
        # ngày của bản ghi (attendance.date).
        rec = self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'check_in': '2026-06-12 02:00:00'})
        env = self.env(user=self.user)
        row = _request_create(env, {'attendanceId': rec.id, 'reason': 'Sửa giờ'})
        self.assertEqual(row['attendanceId'], rec.id)
        req = env['hocba.attendance.request'].browse(row['id'])
        self.assertEqual(req.request_date, rec.date)
