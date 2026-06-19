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

    def _attendance(self, day):
        # check-in lúc 02:00 UTC ngày day -> date local = day
        return self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').sudo().create({
                'employee_id': self.emp.id, 'check_in': day + ' 02:00:00'})

    def test_ot_row_counted(self):
        s = self._shift('2026-06-15', level='150')
        self._attendance('2026-06-15')
        row = _ot_row(self.env, s)
        self.assertEqual(row['hours'], 2.0)
        self.assertTrue(row['counted'])
        self.assertEqual(row['creditHours'], 3.0)   # 2h * 1.5
        self.assertEqual(row['otLevel'], '150')

    def test_ot_row_not_counted_when_no_attendance(self):
        s = self._shift('2026-06-15')
        row = _ot_row(self.env, s)
        self.assertFalse(row['counted'])
        self.assertEqual(row['creditHours'], 0.0)

    def test_for_employee_sums_counted_only(self):
        self._shift('2026-06-15', level='150'); self._attendance('2026-06-15')
        self._shift('2026-06-16', level='300')  # không có attendance -> bỏ
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otHours'], 2.0)
        self.assertEqual(res['otCreditHours'], 3.0)

    def test_for_employee_excludes_pending_and_other_month(self):
        self._shift('2026-06-15', state='pending'); self._attendance('2026-06-15')
        self._shift('2026-05-15', level='300'); self._attendance('2026-05-15')
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otCreditHours'], 0.0)

    def test_me_history_summary_has_ot(self):
        self._shift('2026-06-15', level='300'); self._attendance('2026-06-15')
        data = _att_me_history(self.env(user=self.user), '2026-06')
        self.assertEqual(data['summary']['otHours'], 2.0)
        self.assertEqual(data['summary']['otCreditHours'], 6.0)   # 2h * 3.0

    def test_ot_table_scope_and_totals(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        self._shift('2026-06-15', level='150'); self._attendance('2026-06-15')
        self._shift('2026-06-16', level='300')   # không attendance -> counted False
        hrm = self.env['res.users'].create({
            'name': 'HRM OT', 'login': 'hrm_ot',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        hrm.tz = 'Asia/Ho_Chi_Minh'
        data = _ot_table(self.env(user=hrm), '2026-06')
        self.assertTrue(data['canManage'])
        self.assertEqual(len(data['rows']), 2)            # cả 2 ca approved
        self.assertEqual(data['totals']['otHours'], 2.0)   # chỉ ca counted
        self.assertEqual(data['totals']['otCreditHours'], 3.0)
        self.assertEqual(data['totals']['count'], 2)
        self.assertEqual(data['totals']['countedCount'], 1)

    def test_ot_table_user_sees_only_own(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        self._shift('2026-06-15'); self._attendance('2026-06-15')
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
