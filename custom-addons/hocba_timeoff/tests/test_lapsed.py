# ============================================================
# Test Phase 12 — Đơn lỡ hạn duyệt + đối chiếu chấm công.
# Spec: docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Ngày test tính ĐỘNG từ date.today() (lỡ hạn phụ thuộc "hôm nay").
# Owner: Nhật Anh.
# ============================================================
from datetime import date, datetime, time, timedelta

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

    # ----- Helpers -----
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
            self.env, date.today() - timedelta(days=30), date.today())
        days, cur = [], date.today() - timedelta(days=1)
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
            vals.update({'request_unit_half': True,
                         'request_date_from_period': 'am'})
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
