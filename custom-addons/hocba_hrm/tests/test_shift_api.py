from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _shift_row, _shift_create, _shifts_week, _shift_decide, _shift_cancel


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
            'shift_type': 'ctv', 'ot_level': '150', 'state': 'pending',
        }
        base.update(vals)
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create(base)

    def _make_future_shift(self, **vals):
        """Ca tương lai (start = now + 2h) — dùng cho test cần vượt qua deadline guard."""
        future = fields.Datetime.now() + timedelta(hours=2)
        base = {
            'employee_id': self.emp.id,
            'start': future,
            'end': future + timedelta(hours=2),
            'shift_type': 'ctv', 'ot_level': '150', 'state': 'pending',
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
        self.assertEqual(row['otLevel'], '150')
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['start'], '2026-06-15T09:00:00')
        self.assertEqual(row['end'], '2026-06-15T11:00:00')
        self.assertIsNone(row['reviewer'])

    def test_create_pins_employee_default_level_100(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'reason': 'Trực sáng'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['otLevel'], '100')
        self.assertEqual(row['rate'], 1.0)
        s = env['hocba.work_shift'].browse(row['id'])
        self.assertEqual(str(s.start), '2026-06-15 02:00:00')

    def test_create_with_level_300(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-20T09:00', 'end': '2026-06-20T11:00',
            'shiftType': 'ot', 'otLevel': '300'})
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)

    def test_create_bad_level_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-20T09:00',
                                'end': '2026-06-20T11:00',
                                'shiftType': 'ot', 'otLevel': '999'})

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

    def test_create_overlap_allowed(self):
        # Cho phép 1 người đăng ký nhiều ca OT/ngày kể cả khi giờ chồng nhau.
        env = self.env(user=self.user)
        _shift_create(env, {'start': '2026-06-15T09:00',
                            'end': '2026-06-15T11:00', 'shiftType': 'ctv'})
        row = _shift_create(env, {'start': '2026-06-15T10:00',
                                  'end': '2026-06-15T12:00', 'shiftType': 'ctv'})
        self.assertEqual(row['state'], 'pending')
        cnt = self.env['hocba.work_shift'].search_count(
            [('employee_id', '=', self.emp.id)])
        self.assertEqual(cnt, 2)

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

    def test_week_owner_sees_own_pending(self):
        self._make_shift()   # pending, 2026-06-15 (T2)
        data = _shifts_week(self.env(user=self.user), '2026-06-15')
        self.assertEqual(data['weekStart'], '2026-06-15')
        self.assertEqual(len(data['days']), 7)
        mon = data['days'][0]
        self.assertEqual(mon['date'], '2026-06-15')
        self.assertEqual(mon['weekday'], 'T2')
        self.assertEqual(len(mon['shifts']), 1)
        self.assertEqual(mon['shifts'][0]['empId'], self.emp.id)

    def test_week_other_sees_only_approved(self):
        self._make_shift()                       # pending
        self._make_shift(start='2026-06-16 02:00:00',
                         end='2026-06-16 04:00:00', state='approved')
        other_user = self.env['res.users'].create(
            {'name': 'Khac', 'login': 'khac_shift'})
        other_user.tz = 'Asia/Ho_Chi_Minh'
        other_emp = self.env['hr.employee'].create({
            'name': 'NV Khac', 'x_employment_status': 'official',
            'identification_id': '012345678991',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776'})
        other_emp.user_id = other_user
        data = _shifts_week(self.env(user=other_user), '2026-06-15')
        all_ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertNotIn(self.emp.id, all_ids)   # NV thường không thấy ca người khác

    def test_week_hr_manager_sees_approved_in_scope(self):
        self._make_shift(state='approved')
        data = _shifts_week(self.env(user=self.hrm), '2026-06-15')
        ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertIn(self.emp.id, ids)
        self.assertTrue(data['canManage'])

    def test_week_hr_manager_sees_pending_in_scope(self):
        # Bug: manager phải thấy ca PENDING của NV trong phạm vi để duyệt.
        # Dùng ngày tương lai để lazy auto-reject không loại ca này.
        from odoo.fields import Datetime
        from datetime import timedelta
        future = Datetime.now() + timedelta(days=14)
        future = future.replace(hour=2, minute=0, second=0, microsecond=0)
        monday = future.date() - timedelta(days=future.date().weekday())
        self._make_shift(start=future, end=future + timedelta(hours=2))
        data = _shifts_week(self.env(user=self.hrm), monday.strftime('%Y-%m-%d'))
        rows = [r for d in data['days'] for r in d['shifts']
                if r['empId'] == self.emp.id]
        self.assertTrue(rows, 'Manager phải thấy ca pending của NV để duyệt')
        self.assertEqual(rows[0]['state'], 'pending')

    def test_week_dept_head_sees_pending_in_scope(self):
        dept = self.env['hr.department'].create({'name': 'Phòng P'})
        in_emp = self.env['hr.employee'].create({
            'name': 'NV trong P', 'department_id': dept.id,
            'x_employment_status': 'ctv'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP P'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPP', 'login': 'tpp_shift'})
        mgr_user.tz = 'Asia/Ho_Chi_Minh'
        mgr_emp.user_id = mgr_user
        self.env['hocba.work_shift'].with_context(tz='Asia/Ho_Chi_Minh').create({
            'employee_id': in_emp.id, 'start': '2026-06-15 02:00:00',
            'end': '2026-06-15 04:00:00', 'shift_type': 'ot', 'state': 'pending'})
        data = _shifts_week(self.env(user=mgr_user), '2026-06-15')
        ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertIn(in_emp.id, ids)

    def test_week_dept_head_scope(self):
        dept = self.env['hr.department'].create({'name': 'Phòng S'})
        in_emp = self.env['hr.employee'].create({
            'name': 'NV trong S', 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': '012345678992',
            'x_pit_code': '3334445556', 'x_social_insurance_no': '6665554443'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP S'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPS', 'login': 'tps_shift'})
        mgr_user.tz = 'Asia/Ho_Chi_Minh'
        mgr_emp.user_id = mgr_user
        self.env['hocba.work_shift'].with_context(tz='Asia/Ho_Chi_Minh').create({
            'employee_id': in_emp.id, 'start': '2026-06-15 02:00:00',
            'end': '2026-06-15 04:00:00', 'shift_type': 'ot', 'state': 'approved'})
        self._make_shift(state='approved')   # self.emp ngoài Phòng S
        data = _shifts_week(self.env(user=mgr_user), '2026-06-15')
        ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertIn(in_emp.id, ids)
        self.assertNotIn(self.emp.id, ids)

    def test_week_defaults_to_monday(self):
        # truyền ngày giữa tuần (2026-06-17 là T4) -> chuẩn hóa về thứ 2 2026-06-15
        data = _shifts_week(self.env(user=self.user), '2026-06-17')
        self.assertEqual(data['weekStart'], '2026-06-15')

    def test_decide_approve_with_override(self):
        env = self.env(user=self.hrm)
        s = self._make_future_shift()
        # end override: now+4h expressed in hrm user's local tz (Asia/Ho_Chi_Minh)
        from pytz import timezone as _tz
        hrm_tz = _tz(self.hrm.tz or 'UTC')
        import datetime as _dt
        end_local = (fields.Datetime.now() + timedelta(hours=4)).replace(
            tzinfo=_dt.timezone.utc).astimezone(hrm_tz)
        end_override = end_local.strftime('%Y-%m-%dT%H:%M')
        row = _shift_decide(env, s.id, True, {'otLevel': '300',
                            'end': end_override})
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)
        self.assertEqual(row['reviewer'], self.hrm.name)

    def test_decide_bad_level_override_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_future_shift()
        with self.assertRaises(ValidationError):
            _shift_decide(env, s.id, True, {'otLevel': '999'})

    def test_decide_reject_sets_note(self):
        env = self.env(user=self.hrm)
        s = self._make_future_shift()
        row = _shift_decide(env, s.id, False, {'reviewNote': 'Không cần'})
        self.assertEqual(row['state'], 'rejected')
        self.assertEqual(row['reviewNote'], 'Không cần')

    def test_decide_bad_type_override_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_future_shift()
        with self.assertRaises(ValidationError):
            _shift_decide(env, s.id, True, {'shiftType': 'x'})

    def test_decide_out_of_scope_forbidden(self):
        dept = self.env['hr.department'].create({'name': 'Phòng Z'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP Z'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPZ', 'login': 'tpz_shift'})
        mgr_emp.user_id = mgr_user
        s = self._make_shift()   # self.emp ngoài Phòng Z
        with self.assertRaises(AccessError):
            _shift_decide(self.env(user=mgr_user), s.id, True, {})

    def test_decide_already_decided_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_future_shift(state='rejected')
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, True, {})

    def test_decide_missing_returns_none(self):
        self.assertIsNone(_shift_decide(self.env(user=self.hrm), 999999, True, {}))

    def test_cancel_owner_pending_ok(self):
        s = self._make_future_shift()
        res = _shift_cancel(self.env(user=self.user), s.id)
        self.assertEqual(res, {'ok': True})
        self.assertFalse(s.exists())

    def test_cancel_approved_rejected(self):
        s = self._make_shift(state='approved')
        with self.assertRaises(UserError):
            _shift_cancel(self.env(user=self.user), s.id)

    def test_cancel_other_user_forbidden(self):
        s = self._make_shift()
        u = self.env['res.users'].create({'name': 'Ke', 'login': 'ke_shift'})
        with self.assertRaises(AccessError):
            _shift_cancel(self.env(user=u), s.id)

    def test_cancel_missing_returns_none(self):
        self.assertIsNone(_shift_cancel(self.env(user=self.user), 999999))

    def test_cancel_manager_in_scope_ok(self):
        s = self._make_future_shift()
        res = _shift_cancel(self.env(user=self.hrm), s.id)
        self.assertEqual(res, {'ok': True})

    def test_ctv_forced_level_100(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'otLevel': '300', 'reason': 'x'})
        self.assertEqual(row['otLevel'], '100')
        self.assertEqual(row['rate'], 1.0)

    def test_set_level_blocked_for_ctv(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        s = self._make_future_shift(shift_type='ctv', state='approved', ot_level='100')
        env = self.env(user=self.hrm)
        with self.assertRaises(ValidationError):
            _shift_set_level(env, s.id, '150')
