# ============================================================
# Test Phase 12 — Đơn lỡ hạn duyệt + đối chiếu chấm công.
# Spec: docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Ngày test tính ĐỘNG từ date.today() (lỡ hạn phụ thuộc "hôm nay").
# Owner: Nhật Anh.
# ============================================================
from datetime import date, datetime, time, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _lapsed_info, _lapsed_table, _post_lapsed_decision_note,
    _public_holiday_dates_env,
)


@tagged('post_install', '-at_install')
class TestTimeoffLapsed(TransactionCase):

    def setUp(self):
        super().setUp()
        # Ép tz UTC cho mọi phép đổi giờ (work_credit dùng context tz;
        # hocba.attendance.date dùng tz user của NV) → test tất định.
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (lapsed)'})
        self.dept_b = Dept.create({'name': 'Khối B (lapsed)'})

        self.emp_mgr_a = self._mk_emp('TP A lapsed', '140000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A lapsed', '140000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV B lapsed', '140000000003', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('lapsed_mgr_a', self.emp_mgr_a)
        self.user_a = self._mk_user('lapsed_nv_a', self.emp_a)
        self.user_b = self._mk_user('lapsed_nv_b', self.emp_b)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR lapsed', 'login': 'lapsed_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self.teaching_off = self.env.ref(
            'hocba_timeoff.hb_leave_type_teaching_off')
        self._allocate(self.emp_a, 12)
        self._allocate(self.emp_b, 12)

        # Pin policy để ngưỡng công trong _mk_att tất định (get_policy trả bản
        # ghi có sẵn trong DB test — có thể đã bị sửa).
        self.env['hocba.attendance.policy'].get_policy().write({
            'morning_credit_cutoff': 10.0, 'std_work_hours': 8.0,
            'afternoon_margin_hours': 2.0})

    # ----- Helpers -----
    def _today(self):
        return fields.Date.context_today(self.env.user)

    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
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
            'name': 'Quỹ lapsed %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '%d-01-01' % year, 'date_to': '%d-12-31' % year,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _past_working_days(self, n):
        """n ngày LÀM VIỆC (T2–T6, trừ ngày lễ đã seed) gần nhất TRƯỚC hôm
        nay, trả về tăng dần. Dùng để đặt khoảng nghỉ đã-trôi-qua tất định."""
        holidays = _public_holiday_dates_env(
            self.env, self._today() - timedelta(days=n * 3 + 30), self._today())
        days, cur = [], self._today() - timedelta(days=1)
        while len(days) < n:
            if cur.weekday() < 5 and cur not in holidays:
                days.append(cur)
            cur -= timedelta(days=1)
        return list(reversed(days))

    def _mk_leave(self, emp, d_from, d_to, leave_type=None, half=False):
        vals = {
            'name': 'Nghỉ lapsed', 'employee_id': emp.id,
            'holiday_status_id': (leave_type or self.annual).id,
            'request_date_from': d_from, 'request_date_to': d_to,
        }
        if half:
            # Nửa ngày THẬT: cùng buổi sáng → _half_day_label trả 'Sáng'.
            vals.update({'request_unit_half': True,
                         'request_date_from_period': 'am',
                         'request_date_to_period': 'am'})
        else:
            # Nguyên ngày: am → pm (kể cả loại half_day-unit như Phép Năm,
            # sáng→chiều = trọn 1 ngày) → _half_day_label trả '' (không nửa ngày).
            vals.update({'request_date_from_period': 'am',
                         'request_date_to_period': 'pm'})
        return self.env['hr.leave'].create(vals)

    def _mk_att(self, emp, day, full=True):
        """Bản ghi chấm công ngày `day`: full → work_credit 1.0; không full
        → 0.5 (chỉ công sáng). 02:00 UTC vào ≤ cutoff 10.0; +9h ≥ +6h → đủ
        công chiều; +4h < +6h → mất công chiều."""
        ci = datetime.combine(day, time(2, 0))
        co = ci + timedelta(hours=9 if full else 4)
        return self.env['hocba.attendance'].create({
            'employee_id': emp.id, 'check_in': ci, 'check_out': co})

    # ----- Task 1: field + kind -----
    def test_lapsed_notified_field_default_false(self):
        days = self._past_working_days(1)
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        self.assertFalse(leave.x_lapsed_notified)

    def test_notification_kind_lapsed_accepted(self):
        days = self._past_working_days(1)
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        notif = self.env['hb.leave.notification'].sudo().create({
            'recipient_id': self.mgr_a_user.id, 'leave_id': leave.id,
            'kind': 'lapsed', 'title': 't', 'body': 'b'})
        self.assertEqual(notif.kind, 'lapsed')

    # ----- Task 2: _lapsed_info -----
    def test_not_lapsed_when_start_today_or_future(self):
        """BR-L01: chỉ lỡ hạn khi ngày BẮT ĐẦU < hôm nay."""
        today = self._today()
        leave_today = self._mk_leave(self.emp_a, today, today)
        self.assertIsNone(_lapsed_info(self.env, leave_today))
        future = today + timedelta(days=7)
        leave_future = self._mk_leave(self.emp_a, future, future)
        self.assertIsNone(_lapsed_info(self.env, leave_future))

    def test_not_lapsed_when_not_pending(self):
        """Đơn đã duyệt/từ chối không tính lỡ hạn dù ngày đã qua."""
        days = self._past_working_days(2)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        leave.sudo().action_refuse()
        self.assertIsNone(_lapsed_info(self.env, leave))

    def test_lapsed_no_attendance_suggests_approve(self):
        """BR-L03: nghỉ 2 ngày đã qua, không chấm công → gợi ý duyệt trễ."""
        days = self._past_working_days(2)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        self.assertEqual(info['checkedCount'], 2)
        self.assertEqual(info['workedCount'], 0)
        self.assertEqual(info['suggestion'], 'approve')
        self.assertFalse(info['exempt'])
        self.assertGreaterEqual(info['lapsedDays'], 2)

    def test_lapsed_all_worked_suggests_refuse(self):
        """BR-L03: đủ công mọi ngày nghỉ đã qua → gợi ý từ chối."""
        days = self._past_working_days(2)
        for d in days:
            self._mk_att(self.emp_a, d, full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 2)
        self.assertEqual(info['suggestion'], 'refuse')

    def test_lapsed_mixed_no_suggestion(self):
        """BR-L03: ngày làm ngày nghỉ → không gợi ý, người duyệt tự quyết."""
        days = self._past_working_days(2)
        self._mk_att(self.emp_a, days[0], full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 1)
        self.assertEqual(info['checkedCount'], 2)
        self.assertIsNone(info['suggestion'])

    def test_half_credit_counts_as_worked_for_full_day_leave(self):
        """BR-L02: đơn CẢ NGÀY — công 0.5 đã tính là 'vẫn đi làm'."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=False)     # 0.5 công
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 1)
        self.assertEqual(info['suggestion'], 'refuse')

    def test_half_day_leave_needs_full_credit(self):
        """BR-L02: đơn NỬA NGÀY — 0.5 công là khớp đơn (không mâu thuẫn);
        1.0 công mới là mâu thuẫn."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=False)     # 0.5 công
        leave = self._mk_leave(self.emp_a, days[0], days[0], half=True)
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 0)
        self.assertEqual(info['suggestion'], 'approve')

        days2 = self._past_working_days(2)
        self._mk_att(self.emp_b, days2[0], full=True)     # 1.0 công
        leave_b = self._mk_leave(self.emp_b, days2[0], days2[0], half=True)
        info_b = _lapsed_info(self.env, leave_b)
        self.assertEqual(info_b['workedCount'], 1)
        self.assertEqual(info_b['suggestion'], 'refuse')

    def test_teaching_off_exempt(self):
        """BR-L02: loại 'Nghỉ Buổi Dạy' miễn đối chiếu — chỉ cờ lỡ hạn."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[0],
                               leave_type=self.teaching_off)
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        self.assertTrue(info['exempt'])
        self.assertEqual(info['dayChecks'], [])
        self.assertIsNone(info['suggestion'])

    def test_future_days_not_checked(self):
        """Đơn đang-nghỉ-dở (qua ngày bắt đầu, chưa hết): chỉ đối chiếu
        các ngày ĐÃ QUA (đến hết hôm qua)."""
        days = self._past_working_days(1)
        end = self._today() + timedelta(days=3)
        leave = self._mk_leave(self.emp_a, days[0], end)
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        for c in info['dayChecks']:
            self.assertLess(c['date'], self._today().isoformat())
