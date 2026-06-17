import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _fmt_hm, _att_me_info, _att_day_table, _att_me_history,
    _user_can_manage, _emp_scope_domain, _emp_in_scope,
    _attendance_edit, _attendance_delete, _to_utc,
)


@tagged('post_install', '-at_install')
class TestAttendanceApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
            'office_lat': 0.0, 'office_lng': 0.0,
            'std_work_hours': 8.0, 'violation_free_days': 2,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Chinh Thuc',
            'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })
        self.emp_user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'nv_att_user',
        })
        self.emp.user_id = self.emp_user
        self.hr_user = self.env['res.users'].create({
            'name': 'HR User', 'login': 'hr_att_user',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)],
        })
        if not self.hr_user.employee_id:
            self.env['hr.employee'].create({
                'name': 'HR Manager', 'user_id': self.hr_user.id,
            })

    def _checkin(self, emp):
        return self.env['hocba.attendance']._do_check({
            'employee_id': emp.id, 'photo': 'ZmFrZQ==',
            'descriptor': [0.0] * 128, 'latitude': 0.0, 'longitude': 0.0,
        }, 'in')

    def test_fmt_hm(self):
        self.assertEqual(_fmt_hm(8.0), '08:00')
        self.assertEqual(_fmt_hm(9.5), '09:30')
        self.assertEqual(_fmt_hm(8.25), '08:15')
        self.assertEqual(_fmt_hm(17.75), '17:45')

    def test_me_info_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_att'})
        self.assertIsNone(_att_me_info(self.env(user=user)))

    def test_me_info_basic(self):
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertEqual(info['employeeId'], self.emp.id)
        self.assertTrue(info['enrolled'])
        self.assertTrue(info['isOfficial'])
        self.assertEqual(info['policy']['checkInStart'], '08:00')
        self.assertIsNone(info['today'])

    def test_me_info_today_after_checkin(self):
        self._checkin(self.emp)
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertIsNotNone(info['today'])
        self.assertIn(info['today']['statusKey'], ('on_time', 'late'))

    def test_me_info_flags(self):
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertIn('canManage', info)
        self.assertIn('isWorkdayToday', info)
        self.assertFalse(info['canManage'])  # emp_user là NV thường

    def test_me_info_manager_can_manage(self):
        info = _att_me_info(self.env(user=self.hr_user))
        self.assertTrue(info['canManage'])

    def test_day_table_hr_sees_all(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.hr_user)
        data = _att_day_table(self.env(user=self.hr_user), str(today))
        self.assertTrue(data['isHrManager'])
        # HR sees the employee's record among all rows (don't assert an absolute
        # count — a shared dev DB may hold other check-ins for the same day).
        self.assertIn(self.emp.id, [r['empId'] for r in data['rows']])

    def test_day_table_employee_sees_only_own(self):
        other = self.env['hr.employee'].create({
            'name': 'Other', 'x_employment_status': 'official',
            'identification_id': '098765432109',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776',
        })
        self._checkin(self.emp)
        self._checkin(other)
        today = fields.Date.context_today(self.emp_user)
        data = _att_day_table(self.env(user=self.emp_user), str(today))
        self.assertFalse(data['isHr'])
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['empId'], self.emp.id)

    def test_day_table_no_employee_user_empty(self):
        from odoo import fields
        user = self.env['res.users'].create({'name': 'NoEmp3', 'login': 'noemp_att3'})
        self._checkin(self.emp)
        today = fields.Date.context_today(user)
        data = _att_day_table(self.env(user=user), str(today))
        self.assertFalse(data['isHr'])
        self.assertEqual(data['rows'], [])

    def test_history_filters_employee(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.emp_user)
        month = '%04d-%02d' % (today.year, today.month)
        data = _att_me_history(self.env(user=self.emp_user), month)
        self.assertEqual(data['month'], month)
        self.assertEqual(data['summary']['daysPresent'], 1)
        self.assertEqual(len(data['rows']), 1)

    def test_history_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp2', 'login': 'noemp_att2'})
        self.assertIsNone(_att_me_history(self.env(user=user), None))

    def test_history_credit_summary(self):
        # 4 ngày, mỗi ngày làm 6h (thiếu 120') -> 4 ngày vi phạm.
        # Bỏ 2 ngày đầu -> còn 2 ngày * 120' = 240' = 4h -> /8 = 0.5 công thiếu.
        # Mỗi ngày check-out đúng check_in+6h nên vẫn đủ công chiều -> work_credit=1.
        emp2 = self.env['hr.employee'].create({
            'name': 'NV Credit', 'x_employment_status': 'official',
            'x_pit_code': '5556667778', 'x_social_insurance_no': '4443332221',
            'identification_id': '012345678902',
        })
        u2 = self.env['res.users'].create({'name': 'U2', 'login': 'u2_credit'})
        emp2.user_id = u2
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        for day in (2, 3, 4, 5):
            Att.create({
                'employee_id': emp2.id,
                'check_in': '2026-06-%02d 02:00:00' % day,   # 09:00 local
                'check_out': '2026-06-%02d 08:00:00' % day,  # 15:00 local = 6h
            })
        data = _att_me_history(self.env(user=u2), '2026-06')
        s = data['summary']
        self.assertEqual(s['violationDays'], 4)
        self.assertEqual(s['totalCredit'], 4.0)
        self.assertEqual(s['deficitCredit'], 0.5)
        self.assertEqual(s['netCredit'], 3.5)

    def test_history_credit_under_free_days(self):
        # Chỉ 2 ngày vi phạm -> bỏ hết -> deficit 0.
        emp3 = self.env['hr.employee'].create({
            'name': 'NV Credit3', 'x_employment_status': 'official',
            'x_pit_code': '1212121212', 'x_social_insurance_no': '3434343434',
            'identification_id': '012345678903',
        })
        u3 = self.env['res.users'].create({'name': 'U3', 'login': 'u3_credit'})
        emp3.user_id = u3
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        for day in (10, 11):
            Att.create({
                'employee_id': emp3.id,
                'check_in': '2026-06-%02d 02:00:00' % day,
                'check_out': '2026-06-%02d 08:00:00' % day,
            })
        data = _att_me_history(self.env(user=u3), '2026-06')
        self.assertEqual(data['summary']['violationDays'], 2)
        self.assertEqual(data['summary']['deficitCredit'], 0.0)


@tagged('post_install', '-at_install')
class TestScopeHelpers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.mgr_emp = self.env['hr.employee'].create({'name': 'Quản lý A'})
        self.dept.manager_id = self.mgr_emp
        self.mgr_user = self.env['res.users'].create(
            {'name': 'MgrA', 'login': 'mgra_scope'})
        self.mgr_user.tz = 'Asia/Ho_Chi_Minh'
        self.mgr_emp.user_id = self.mgr_user
        self.plain_user = self.env['res.users'].create(
            {'name': 'Plain', 'login': 'plain_scope'})

    def test_hr_manager_can_manage(self):
        u = self.env['res.users'].create({
            'name': 'HRM', 'login': 'hrm_scope',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.assertTrue(_user_can_manage(self.env(user=u)))

    def test_department_head_can_manage(self):
        self.assertTrue(_user_can_manage(self.env(user=self.mgr_user)))

    def test_plain_user_cannot_manage(self):
        self.assertFalse(_user_can_manage(self.env(user=self.plain_user)))

    def test_department_head_scope_is_own_department(self):
        dom = _emp_scope_domain(self.env(user=self.mgr_user))
        self.assertIn(('department_id', 'in', [self.dept.id]), dom)

    def test_day_table_department_head_sees_only_dept(self):
        in_dept = self.env['hr.employee'].create({
            'name': 'NV trong phòng', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '1110002221',
            'x_social_insurance_no': '2220001112',
            'identification_id': '012345670021'})
        out_dept = self.env['hr.employee'].create({
            'name': 'NV ngoài phòng', 'x_employment_status': 'official',
            'x_pit_code': '3330004445', 'x_social_insurance_no': '4440003332',
            'identification_id': '012345670022'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        today = fields.Date.context_today(self.mgr_user)
        for e in (in_dept, out_dept):
            Att.create({'employee_id': e.id,
                        'check_in': '%s 02:00:00' % today})
        data = _att_day_table(self.env(user=self.mgr_user), str(today))
        self.assertTrue(data['canManage'])
        emp_ids = [r['empId'] for r in data['rows']]
        self.assertIn(in_dept.id, emp_ids)
        self.assertNotIn(out_dept.id, emp_ids)

    def test_edit_recomputes_credit(self):
        e = self.env['hr.employee'].create({
            'name': 'NV Sửa', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '5550006661',
            'x_social_insurance_no': '6660005551',
            'identification_id': '012345670031'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00',
                          'check_out': '2026-06-17 07:00:00'})  # 5h -> thiếu 180
        self.assertEqual(rec.missing_minutes, 180)
        row = _attendance_edit(self.env(user=self.mgr_user), rec.id,
                               {'checkOut': '2026-06-17T17:00'})  # 09:00->17:00 = 8h
        self.assertEqual(row['missingMinutes'], 0)
        self.assertEqual(rec.missing_minutes, 0)

    def test_edit_out_of_scope_forbidden(self):
        from odoo.exceptions import AccessError
        out = self.env['hr.employee'].create({
            'name': 'NV ngoài', 'x_employment_status': 'official',
            'x_pit_code': '7770008881', 'x_social_insurance_no': '8880007771',
            'identification_id': '012345670032'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': out.id,
                          'check_in': '2026-06-17 02:00:00'})
        with self.assertRaises(AccessError):
            _attendance_edit(self.env(user=self.mgr_user), rec.id, {'notes': 'x'})

    def test_edit_non_manager_forbidden(self):
        from odoo.exceptions import AccessError
        e = self.env['hr.employee'].create({
            'name': 'NV self', 'x_employment_status': 'official',
            'x_pit_code': '9990001112', 'x_social_insurance_no': '1110009992',
            'identification_id': '012345670033'})
        e.user_id = self.plain_user
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00'})
        with self.assertRaises(AccessError):
            _attendance_edit(self.env(user=self.plain_user), rec.id, {'notes': 'x'})

    def test_delete_in_scope(self):
        e = self.env['hr.employee'].create({
            'name': 'NV Xóa', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '2223334445',
            'x_social_insurance_no': '5554443332',
            'identification_id': '012345670034'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00'})
        res = _attendance_delete(self.env(user=self.mgr_user), rec.id)
        self.assertEqual(res, {'ok': True})
        self.assertFalse(rec.exists())

    def test_to_utc_roundtrip(self):
        # 17:00 local (+07, mgr_user.tz đặt ở setUp) -> 10:00 UTC
        dt = _to_utc(self.env(user=self.mgr_user), '2026-06-17T17:00')
        self.assertEqual(str(dt), '2026-06-17 10:00:00')
