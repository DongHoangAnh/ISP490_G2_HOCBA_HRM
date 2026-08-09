# ============================================================
# Test đơn "xin nghỉ bù" (x_is_makeup): NV nộp đơn cho ngày nghỉ ĐÃ QUA và tự
# khai là nộp bù → không tính vào "quá hạn duyệt" (bảng Kiểm duyệt phát sinh,
# KPI dashboard, tag ở tab Chờ duyệt, chuông CRON-TO-002).
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Owner: Nhật Anh.
# ============================================================
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _lapsed_info, _lapsed_table, _public_holiday_dates_env,
)


@tagged('post_install', '-at_install')
class TestTimeoffMakeup(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.tz = 'UTC'

        self.dept = self.env['hr.department'].create({'name': 'Khối M (makeup)'})
        self.emp_mgr = self._mk_emp('TP M makeup', '170000000001')
        self.emp = self._mk_emp('NV M makeup', '170000000002')
        self.dept.manager_id = self.emp_mgr.id

        self.mgr_user = self._mk_user('makeup_mgr', self.emp_mgr)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR makeup', 'login': 'makeup_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self._allocate(self.emp, 12)

    # ----- Helpers -----
    def _today(self):
        return fields.Date.context_today(self.env.user)

    def _mk_emp(self, name, cccd):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': self.dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10],
        })

    def _mk_user(self, login, emp):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'tz': 'UTC',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        emp.user_id = user
        return user

    def _allocate(self, emp, days):
        year = date.today().year
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ makeup %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '%d-01-01' % year, 'date_to': '%d-12-31' % year,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _past_working_days(self, n):
        holidays = _public_holiday_dates_env(
            self.env, self._today() - timedelta(days=n * 3 + 30), self._today())
        days, cur = [], self._today() - timedelta(days=1)
        while len(days) < n:
            if cur.weekday() < 5 and cur not in holidays:
                days.append(cur)
            cur -= timedelta(days=1)
        return list(reversed(days))

    def _mk_leave(self, d_from, d_to, makeup=False):
        return self.env['hr.leave'].create({
            'name': 'Nghỉ makeup', 'employee_id': self.emp.id,
            'holiday_status_id': self.annual.id,
            'request_date_from': d_from, 'request_date_to': d_to,
            'request_date_from_period': 'am', 'request_date_to_period': 'pm',
            'x_is_makeup': makeup,
        })

    # ----- Field + ràng buộc -----
    def test_makeup_defaults_false(self):
        days = self._past_working_days(1)
        self.assertFalse(self._mk_leave(days[0], days[0]).x_is_makeup)

    def test_makeup_allowed_for_past_leave(self):
        """Nghỉ rồi mới nộp đơn: vẫn tạo được và giữ cờ nghỉ bù."""
        days = self._past_working_days(2)
        leave = self._mk_leave(days[0], days[1], makeup=True)
        self.assertTrue(leave.x_is_makeup)

    def test_makeup_rejected_for_today_or_future(self):
        """Cờ nghỉ bù chỉ dành cho ngày đã qua — nếu không nó thành lối thoát
        khỏi thống kê quá hạn cho mọi đơn."""
        today = self._today()
        with self.assertRaises(ValidationError):
            self._mk_leave(today, today, makeup=True)
        future = today + timedelta(days=7)
        with self.assertRaises(ValidationError):
            self._mk_leave(future, future, makeup=True)

    # ----- Không tính quá hạn duyệt -----
    def test_makeup_not_lapsed(self):
        days = self._past_working_days(2)
        leave = self._mk_leave(days[0], days[1], makeup=True)
        self.assertIsNone(
            _lapsed_info(self.env, leave),
            'đơn nghỉ bù không được coi là quá hạn duyệt')

    def test_same_leave_without_flag_is_lapsed(self):
        """Đối chứng: cùng khoảng ngày, không tick nghỉ bù → vẫn quá hạn."""
        days = self._past_working_days(2)
        leave = self._mk_leave(days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertIsNotNone(info)
        self.assertTrue(info['isLapsed'])

    def test_makeup_excluded_from_lapsed_table(self):
        """Bảng "Kiểm duyệt phát sinh" + KPI/bảng quá hạn ở Tổng quan đều lấy
        từ _lapsed_table → đơn nghỉ bù phải biến mất khỏi cả hai."""
        days = self._past_working_days(3)
        makeup = self._mk_leave(days[0], days[0], makeup=True)
        normal = self._mk_leave(days[2], days[2])

        env_hr = self.env(user=self.hr_user)
        data = _lapsed_table(env_hr, _scope_for(env_hr))
        ids = [r['requestId'] for r in data['items']]
        self.assertIn(normal.id, ids)
        self.assertNotIn(makeup.id, ids)
        self.assertEqual(data['kpi']['total'], len(ids))

    def test_cron_skips_makeup(self):
        """CRON-TO-002 không bắn chuông "quá hạn" cho đơn nghỉ bù."""
        days = self._past_working_days(1)
        makeup = self._mk_leave(days[0], days[0], makeup=True)

        self.env['hb.timeoff.cron']._cron_notify_lapsed_approvals()

        self.assertFalse(makeup.x_lapsed_notified)
        self.assertFalse(self.env['hb.notification'].sudo().search([
            ('target_ref', '=', makeup.id), ('kind', '=', 'lapsed')]))
