from datetime import date
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _ot_row, _ot_for_employee, _att_me_history, _ot_table)


@tagged('post_install', '-at_install')
class TestOtPayroll(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV P', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV P User', 'login': 'ctv_ot_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user

    def _shift(self, day, level='150', state='approved'):
        # day='2026-06-15' -> 09:00-11:00 local (02:00-04:00 UTC), 2 giờ
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'shift_type': 'ot',
                'ot_level': level, 'state': state,
                'start': day + ' 02:00:00', 'end': day + ' 04:00:00'})

    def _shift_att(self, shift, ci=None, co=None):
        return self.env['hocba.shift.attendance'].sudo().create({
            'shift_id': shift.id,
            'check_in': ci or shift.start,
            'check_out': co or shift.end})

    def test_ot_row_counted(self):
        s = self._shift('2026-06-15', level='150')
        self._shift_att(s)
        row = _ot_row(self.env, s)
        self.assertEqual(row['hours'], 2.0)
        self.assertTrue(row['counted'])
        # 2h shift: congCa = round(2/8 * 1.5, 2) = 0.38
        self.assertEqual(row['congCa'], 0.38)
        self.assertEqual(row['otLevel'], '150')

    def test_ot_row_not_counted_when_no_attendance(self):
        s = self._shift('2026-06-15')
        row = _ot_row(self.env, s)
        self.assertFalse(row['counted'])
        self.assertEqual(row['congCa'], 0.0)

    def test_for_employee_sums_counted_only(self):
        s1 = self._shift('2026-06-15', level='150')
        self._shift_att(s1)
        self._shift('2026-06-16', level='300')  # không có shift_att -> bỏ
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otHours'], 2.0)
        # congCa của ca counted: round(2/8 * 1.5, 2) = 0.38
        self.assertEqual(res['otCong'], 0.38)

    def test_for_employee_excludes_pending_and_other_month(self):
        s1 = self._shift('2026-06-15', state='pending')
        self._shift_att(s1)
        s2 = self._shift('2026-05-15', level='300')
        self._shift_att(s2)
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otCong'], 0.0)

    def test_me_history_summary_has_ot(self):
        s = self._shift('2026-06-15', level='300')
        self._shift_att(s)
        data = _att_me_history(self.env(user=self.user), '2026-06')
        self.assertEqual(data['summary']['otHours'], 2.0)
        # congCa: round(2/8 * 3.0, 2) = 0.75
        self.assertEqual(data['summary']['congOt'], 0.75)

    def test_ot_table_scope_and_totals(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        s1 = self._shift('2026-06-15', level='150')
        self._shift_att(s1)
        self._shift('2026-06-16', level='300')   # không shift_att -> counted False
        # Tạo manager có phạm vi chỉ trong phòng ban chứa self.emp
        dept = self.env['hr.department'].create({'name': 'Phòng OT Test'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP OT'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({
            'name': 'TPO OT', 'login': 'tpo_ot_test'})
        mgr_user.tz = 'Asia/Ho_Chi_Minh'
        mgr_emp.user_id = mgr_user
        # Đưa self.emp vào phòng ban
        self.emp.department_id = dept.id
        data = _ot_table(self.env(user=mgr_user), '2026-06')
        self.assertTrue(data['canManage'])
        self.assertEqual(len(data['rows']), 2)            # cả 2 ca approved trong phòng
        self.assertEqual(data['totals']['otHours'], 2.0)   # chỉ ca counted
        # otCong: congCa của ca 150% counted = round(2/8 * 1.5, 2) = 0.38
        self.assertEqual(data['totals']['otCong'], 0.38)
        self.assertEqual(data['totals']['count'], 2)
        self.assertEqual(data['totals']['countedCount'], 1)

    def test_ot_table_user_sees_only_own(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        s = self._shift('2026-06-15')
        self._shift_att(s)
        data = _ot_table(self.env(user=self.user), '2026-06')
        self.assertFalse(data['canManage'])
        self.assertTrue(all(r['empId'] == self.emp.id for r in data['rows']))

    def test_set_level_manager_in_scope(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        s = self._shift('2026-06-15', level='150')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL', 'login': 'hrm_sl',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        row = _shift_set_level(self.env(user=hrm), s.id, '300')
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)

    def test_set_level_bad_value_raises(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import ValidationError
        s = self._shift('2026-06-15')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL2', 'login': 'hrm_sl2',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        with self.assertRaises(ValidationError):
            _shift_set_level(self.env(user=hrm), s.id, '999')

    def test_set_level_pending_raises(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import ValidationError
        s = self._shift('2026-06-15', state='pending')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL3', 'login': 'hrm_sl3',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        with self.assertRaises(ValidationError):
            _shift_set_level(self.env(user=hrm), s.id, '300')

    def test_set_level_out_of_scope_forbidden(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import AccessError
        dept = self.env['hr.department'].create({'name': 'Phòng Q'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP Q'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPQ', 'login': 'tpq_ot'})
        mgr_emp.user_id = mgr_user
        s = self._shift('2026-06-15')   # self.emp ngoài Phòng Q
        with self.assertRaises(AccessError):
            _shift_set_level(self.env(user=mgr_user), s.id, '300')

    def test_set_level_missing_returns_none(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        hrm = self.env['res.users'].create({
            'name': 'HRM SL4', 'login': 'hrm_sl4',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.assertIsNone(_shift_set_level(self.env(user=hrm), 999999, '300'))
