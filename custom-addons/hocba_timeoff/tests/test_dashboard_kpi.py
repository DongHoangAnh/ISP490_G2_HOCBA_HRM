# ============================================================
# Test KPI dashboard "Tổng quan" — ô "Đã từ chối" (_refused_domain) và số
# đơn cần duyệt dùng cho badge cạnh "Nghỉ phép" ở thanh menu.
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Owner: Nhật Anh.
# ============================================================
from datetime import date, timedelta

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _approvals_domain, _refused_domain, _scope_for,
)


@tagged('post_install', '-at_install')
class TestDashboardKpi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (kpi)'})
        self.dept_b = Dept.create({'name': 'Khối B (kpi)'})

        self.emp_mgr_a = self._mk_emp('TP A kpi', '160000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A kpi', '160000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV B kpi', '160000000003', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('kpi_mgr_a', self.emp_mgr_a)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR kpi', 'login': 'kpi_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        for emp in (self.emp_a, self.emp_b):
            self._allocate(emp, 12)

        self.year = date.today().year
        self.bounds = ('%d-01-01 00:00:00' % self.year,
                       '%d-12-31 23:59:59' % self.year)

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
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ kpi %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '%d-01-01' % date.today().year,
            'date_to': '%d-12-31' % date.today().year,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _future_workday(self, offset=7):
        cur = date.today() + timedelta(days=offset)
        while cur.weekday() >= 5:
            cur += timedelta(days=1)
        return cur

    def _mk_leave(self, emp, day):
        return self.env['hr.leave'].create({
            'name': 'Nghỉ kpi', 'employee_id': emp.id,
            'holiday_status_id': self.annual.id,
            'request_date_from': day, 'request_date_to': day,
            'request_date_from_period': 'am', 'request_date_to_period': 'pm',
        })

    def _refused_count(self, scope, dept_id=False):
        return self.env['hr.leave'].sudo().search_count(
            _refused_domain(scope, dept_id, *self.bounds))

    # ----- Tests: KPI "Đã từ chối" -----
    def test_counts_refused_requests(self):
        """Đơn bị từ chối trong năm được đếm; đơn chờ duyệt/đã duyệt thì không."""
        scope = _scope_for(self.env(user=self.hr_user))
        before = self._refused_count(scope)

        self._mk_leave(self.emp_a, self._future_workday(7))          # chờ duyệt
        self._mk_leave(self.emp_a, self._future_workday(14)).sudo().action_approve()
        self._mk_leave(self.emp_a, self._future_workday(21)).sudo().action_refuse()

        self.assertEqual(self._refused_count(scope), before + 1)

    def test_scoped_by_department_for_manager(self):
        """Trưởng phòng A chỉ đếm đơn từ chối của phòng A."""
        self._mk_leave(self.emp_a, self._future_workday(7)).sudo().action_refuse()
        self._mk_leave(self.emp_b, self._future_workday(7)).sudo().action_refuse()

        mgr_scope = _scope_for(self.env(user=self.mgr_a_user))
        hr_scope = _scope_for(self.env(user=self.hr_user))
        self.assertFalse(mgr_scope['seeAll'])
        self.assertEqual(self._refused_count(mgr_scope), 1)
        self.assertGreaterEqual(self._refused_count(hr_scope), 2)

    def test_dept_filter_narrows_hr_view(self):
        """HR lọc 1 phòng ban → chỉ đếm đơn từ chối của phòng đó."""
        self._mk_leave(self.emp_a, self._future_workday(7)).sudo().action_refuse()
        self._mk_leave(self.emp_b, self._future_workday(7)).sudo().action_refuse()

        scope = _scope_for(self.env(user=self.hr_user))
        self.assertEqual(self._refused_count(scope, self.dept_b.id), 1)

    def test_other_year_excluded(self):
        """KPI theo năm: đơn từ chối của năm khác không lọt vào."""
        scope = _scope_for(self.env(user=self.hr_user))
        self._mk_leave(self.emp_a, self._future_workday(7)).sudo().action_refuse()
        other = ('%d-01-01 00:00:00' % (self.year - 1),
                 '%d-12-31 23:59:59' % (self.year - 1))
        self.assertEqual(
            self.env['hr.leave'].sudo().search_count(
                _refused_domain(scope, False, *other)),
            0)

    def test_withdrawn_request_counted_as_refused(self):
        """Đơn đã duyệt bị RÚT (duyệt yêu cầu rút) về state 'refuse' → phải
        nằm trong "tổng số đơn đã bị từ chối"."""
        scope = _scope_for(self.env(user=self.hr_user))
        before = self._refused_count(scope)
        leave = self._mk_leave(self.emp_a, self._future_workday(7))
        leave.sudo().action_approve()
        leave.sudo().write({'x_withdraw_state': 'pending'})
        leave.sudo().action_refuse()          # duyệt rút = từ chối + hoàn quỹ
        self.assertEqual(self._refused_count(scope), before + 1)

    # ----- Tests: badge "Nghỉ phép" ở thanh menu -----
    def test_pending_count_matches_approvals_list(self):
        """Badge sidebar dùng search_count trên CÙNG _approvals_domain với tab
        "Đơn chờ duyệt" → 2 con số không được lệch nhau."""
        self._mk_leave(self.emp_a, self._future_workday(7))
        withdrawn = self._mk_leave(self.emp_a, self._future_workday(14))
        withdrawn.sudo().action_approve()
        withdrawn.sudo().write({'x_withdraw_state': 'pending'})
        self._mk_leave(self.emp_b, self._future_workday(7))   # ngoài phòng A

        Leave = self.env['hr.leave'].sudo()
        for scope in (_scope_for(self.env(user=self.hr_user)),
                      _scope_for(self.env(user=self.mgr_a_user))):
            dom = _approvals_domain(scope)
            self.assertEqual(Leave.search_count(dom), len(Leave.search(dom)))

    def test_pending_count_scoped_for_manager(self):
        """Trưởng phòng A không đếm đơn chờ duyệt của phòng B."""
        self._mk_leave(self.emp_a, self._future_workday(7))
        self._mk_leave(self.emp_b, self._future_workday(7))
        mgr_scope = _scope_for(self.env(user=self.mgr_a_user))
        found = self.env['hr.leave'].sudo().search(_approvals_domain(mgr_scope))
        self.assertEqual(found.employee_id, self.emp_a)
