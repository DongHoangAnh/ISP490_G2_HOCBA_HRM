# ============================================================
# Test _approvals_domain — domain tab "Chờ duyệt" dùng chung.
# Bug gốc: refresh của POST /request/<id>/decision dùng domain riêng
# (chỉ PENDING_STATES) → sau khi duyệt một đơn thường, payload mất các
# đơn validate đang chờ duyệt rút → bảng + badge FE sai đến khi F5.
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Owner: Nhật Anh.
# ============================================================
from datetime import date, timedelta

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _approvals_domain, _dept_domain, _scope_for, PENDING_STATES,
)


@tagged('post_install', '-at_install')
class TestApprovalsDomain(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (appr-dom)'})
        self.dept_b = Dept.create({'name': 'Khối B (appr-dom)'})

        self.emp_mgr_a = self._mk_emp('TP A appr-dom', '150000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A appr-dom', '150000000002', self.dept_a)
        self.emp_a2 = self._mk_emp('NV A2 appr-dom', '150000000003', self.dept_a)
        self.emp_b = self._mk_emp('NV B appr-dom', '150000000004', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('apprdom_mgr_a', self.emp_mgr_a)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR appr-dom', 'login': 'apprdom_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        for emp in (self.emp_a, self.emp_a2, self.emp_b):
            self._allocate(emp, 12)

        # 3 đơn dựng sẵn cho mọi test:
        #  - pending  : đơn mới chờ duyệt (NV A)
        #  - withdraw : đơn ĐÃ duyệt có yêu cầu rút đang chờ (NV A2)
        #  - plain_ok : đơn đã duyệt bình thường, KHÔNG được xuất hiện (NV B)
        d = self._future_workday()
        self.leave_pending = self._mk_leave(self.emp_a, d)
        self.leave_withdraw = self._mk_leave(self.emp_a2, d + timedelta(days=7))
        self.leave_withdraw.sudo().action_approve()
        self.leave_withdraw.sudo().write({'x_withdraw_state': 'pending'})
        self.leave_plain_ok = self._mk_leave(self.emp_b, d + timedelta(days=14))
        self.leave_plain_ok.sudo().action_approve()

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
            'name': 'Quỹ appr-dom %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '%d-01-01' % year, 'date_to': '%d-12-31' % year,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _future_workday(self):
        """Ngày làm việc (T2–T6) đầu tiên sau hôm nay + 7 ngày — tránh lệch
        cuối tuần làm đơn 0 ngày."""
        cur = date.today() + timedelta(days=7)
        while cur.weekday() >= 5:
            cur += timedelta(days=1)
        return cur

    def _mk_leave(self, emp, day):
        return self.env['hr.leave'].create({
            'name': 'Nghỉ appr-dom', 'employee_id': emp.id,
            'holiday_status_id': self.annual.id,
            'request_date_from': day, 'request_date_to': day,
            'request_date_from_period': 'am', 'request_date_to_period': 'pm',
        })

    def _search(self, scope):
        return self.env['hr.leave'].sudo().search(_approvals_domain(scope))

    # ----- Tests -----
    def test_domain_includes_pending_and_withdraw_pending(self):
        """Domain hợp nhất phải gồm đơn chờ duyệt MỚI + đơn chờ duyệt RÚT,
        và loại đơn đã duyệt bình thường."""
        found = self._search(_scope_for(self.env(user=self.hr_user)))
        self.assertIn(self.leave_pending, found)
        self.assertIn(self.leave_withdraw, found)
        self.assertNotIn(self.leave_plain_ok, found)

    def test_domain_scoped_by_department_for_manager(self):
        """Trưởng phòng A chỉ thấy đơn phòng A (gồm cả yêu cầu rút phòng A),
        không thấy đơn phòng B."""
        scope = _scope_for(self.env(user=self.mgr_a_user))
        self.assertFalse(scope['seeAll'])
        found = self._search(scope)
        self.assertIn(self.leave_pending, found)
        self.assertIn(self.leave_withdraw, found)
        self.assertNotIn(self.leave_plain_ok, found)

    def test_decision_refresh_keeps_withdraw_rows(self):
        """Kịch bản bug gốc: duyệt đơn thường xong, tìm lại bằng domain
        refresh (nay là _approvals_domain) vẫn phải còn dòng yêu cầu rút.
        Trước fix, domain refresh chỉ có PENDING_STATES → mất dòng này."""
        scope = _scope_for(self.env(user=self.hr_user))
        # Trước khi duyệt: cả 2 dòng cùng có mặt (như GET /approvals).
        self.assertEqual(
            self._search(scope) & (self.leave_pending | self.leave_withdraw),
            self.leave_pending | self.leave_withdraw)
        # Duyệt đơn thường (chính là bước làm payload refresh bị lệch trước đây).
        self.leave_pending.sudo().action_approve()
        found = self._search(scope)
        self.assertNotIn(self.leave_pending, found,
                         'Đơn vừa duyệt không còn chờ duyệt')
        self.assertIn(self.leave_withdraw, found,
                      'Yêu cầu rút đang chờ phải còn trong payload refresh')

    def test_domain_composes_dept_domain(self):
        """_approvals_domain = domain trạng thái + _dept_domain (không lệch
        phạm vi giữa GET /approvals và refresh)."""
        scope = _scope_for(self.env(user=self.mgr_a_user))
        self.assertEqual(_approvals_domain(scope)[-len(_dept_domain(scope)):],
                         _dept_domain(scope))
        # PENDING_STATES vẫn là nguồn sự thật cho nhánh "đơn mới".
        self.assertIn(('state', 'in', list(PENDING_STATES)),
                      _approvals_domain(scope))
