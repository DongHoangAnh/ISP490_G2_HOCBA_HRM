# ============================================================
# Test Phase 4 — Cảnh báo trùng lịch nghỉ (coverage).
# Owner: Nhật Anh. Quy ước test repo: TransactionCase gọi thẳng các hàm cấp
# module của controller với self.env(user=...) (như test_balances).
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _coverage_table, _overlap_count, OVERLAP_WARN,
)


@tagged('post_install', '-at_install')
class TestTimeoffCoverage(TransactionCase):

    def setUp(self):
        super().setUp()
        Dept = self.env['hr.department']
        # Khối A (cha) → Tổ A1 (con) · Khối B (độc lập)
        self.dept_parent = Dept.create({'name': 'Khối A (cov)'})
        self.dept_child = Dept.create({'name': 'Tổ A1 (cov)',
                                       'parent_id': self.dept_parent.id})
        self.dept_other = Dept.create({'name': 'Khối B (cov)'})

        self.emp_mgr = self._mk_emp('TP Khối A', '120000000001', self.dept_parent)
        self.emp_a = self._mk_emp('NV A', '120000000002', self.dept_parent)
        self.emp_a2 = self._mk_emp('NV A2', '120000000003', self.dept_parent)
        self.emp_b = self._mk_emp('NV B', '120000000004', self.dept_other)

        self.dept_parent.manager_id = self.emp_mgr.id

        self.mgr_user = self.env['res.users'].create({
            'name': 'TP User', 'login': 'cov_mgr_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_mgr.user_id = self.mgr_user

        self.normal_user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'cov_normal_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_b.user_id = self.normal_user

        self.hr_user = self.env['res.users'].create({
            'name': 'HR User', 'login': 'cov_hr_user',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        # Dùng loại Nghỉ Không Lương (requires_allocation=False) — khỏi cấp quỹ.
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')

        # Lịch nghỉ đã duyệt (T2 15/06 .. T5 18/06/2026 đều là ngày làm việc):
        #   A : 15→17 (Khối A) · A2: 16→18 (Khối A) · B : 16→16 (Khối B)
        self._take(self.emp_a, '2026-06-15', '2026-06-17')
        self.leave_a2 = self._take(self.emp_a2, '2026-06-16', '2026-06-18')
        self._take(self.emp_b, '2026-06-16', '2026-06-16')

    # ----- helpers -----
    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name,
            'department_id': dept.id,
            'x_employment_status': 'official',
            'identification_id': cccd,
            'x_pit_code': cccd[2:],
            'x_social_insurance_no': cccd[:10],
        })

    def _take(self, emp, d_from, d_to):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ test',
            'holiday_status_id': self.unpaid.id,
            'employee_id': emp.id,
            'request_date_from': d_from,
            'request_date_to': d_to,
        })
        if leave.state != 'validate':
            leave.action_approve()
        if leave.state != 'validate':
            leave._action_validate()
        return leave

    def _day(self, data, iso):
        return next((d for d in data['days'] if d['date'] == iso), None)

    # ----- coverage table -----
    def test_hr_counts_all_departments(self):
        scope = _scope_for(self.env(user=self.hr_user))
        data = _coverage_table(self.env(user=self.hr_user), scope,
                               '2026-06-15', '2026-06-18')
        # 15: A · 16: A+A2+B · 17: A+A2 · 18: A2
        self.assertEqual(self._day(data, '2026-06-15')['count'], 1)
        self.assertEqual(self._day(data, '2026-06-16')['count'], 3)
        self.assertEqual(self._day(data, '2026-06-17')['count'], 2)
        self.assertEqual(self._day(data, '2026-06-18')['count'], 1)
        self.assertEqual(data['overlapWarn'], OVERLAP_WARN)
        # 16/06 có 3 người >= OVERLAP_WARN → 1 ngày quá tải.
        self.assertEqual(data['overloadedDays'], 1)

    def test_dept_manager_excludes_other_department(self):
        scope = _scope_for(self.env(user=self.mgr_user))
        data = _coverage_table(self.env(user=self.mgr_user), scope,
                               '2026-06-15', '2026-06-18')
        # Trưởng phòng Khối A: B (Khối B) không nằm trong phạm vi.
        day16 = self._day(data, '2026-06-16')
        self.assertEqual(day16['count'], 2)              # A + A2, KHÔNG có B
        emp_ids = {e['employeeId'] for d in data['days'] for e in d['employees']}
        self.assertNotIn(self.emp_b.id, emp_ids)
        self.assertEqual(data['overloadedDays'], 0)      # không ngày nào >= 3

    def test_dept_filter_narrows_to_one_department(self):
        scope = _scope_for(self.env(user=self.hr_user))
        data = _coverage_table(self.env(user=self.hr_user), scope,
                               '2026-06-15', '2026-06-18', dept_id=self.dept_other.id)
        # Chỉ Khối B → chỉ B nghỉ ngày 16.
        self.assertEqual(len(data['days']), 1)
        self.assertEqual(self._day(data, '2026-06-16')['count'], 1)

    def test_empty_days_are_omitted(self):
        scope = _scope_for(self.env(user=self.hr_user))
        data = _coverage_table(self.env(user=self.hr_user), scope,
                               '2026-06-19', '2026-06-21')
        self.assertEqual(data['days'], [])               # không ai nghỉ

    # ----- overlap count (badge modal duyệt) -----
    def test_overlap_count_same_dept_excludes_self(self):
        # Đơn A2 (16→18, Khối A) trùng với A (15→17, Khối A) → 1; B khác phòng.
        scope = _scope_for(self.env(user=self.hr_user))
        n = _overlap_count(self.env(user=self.hr_user), self.leave_a2)
        self.assertEqual(n, 1)
        self.assertTrue(scope['seeAll'])
