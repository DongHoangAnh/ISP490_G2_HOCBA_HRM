# ============================================================
# Test Phase 1 — Bảng "Quỹ phép" toàn nhân viên (GET /balances).
# Owner: Nhật Anh. Theo quy ước test repo: TransactionCase gọi thẳng các hàm
# cấp module của controller với self.env(user=...) (như test_attendance_api).
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _balances_table, _hb_leave_type_ids,
    LOW_BALANCE_DAYS, AT_RISK_DAYS,
)


@tagged('post_install', '-at_install')
class TestTimeoffBalances(TransactionCase):

    def setUp(self):
        super().setUp()
        Emp = self.env['hr.employee']
        Dept = self.env['hr.department']

        # --- Cây phòng ban: Khối A (cha) → Tổ A1 (con) · Khối B (độc lập) ---
        self.dept_parent = Dept.create({'name': 'Khối A (test)'})
        self.dept_child = Dept.create({'name': 'Tổ A1 (test)',
                                       'parent_id': self.dept_parent.id})
        self.dept_other = Dept.create({'name': 'Khối B (test)'})

        # --- Nhân viên (CCCD 12 số, mỗi NV một giá trị — BR-010) ---
        self.emp_mgr = self._mk_emp('TP Khối A', '110000000001', self.dept_parent)
        self.emp_a = self._mk_emp('NV Khối A', '110000000002', self.dept_parent)
        self.emp_a1 = self._mk_emp('NV Tổ A1', '110000000003', self.dept_child)
        self.emp_b = self._mk_emp('NV Khối B', '110000000004', self.dept_other)

        # Trưởng phòng quản lý Khối A (gồm Tổ A1 nhờ parent_id).
        self.dept_parent.manager_id = self.emp_mgr.id

        # --- Users ---
        self.mgr_user = self.env['res.users'].create({
            'name': 'TP User', 'login': 'to_mgr_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_mgr.user_id = self.mgr_user

        self.normal_user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'to_normal_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_b.user_id = self.normal_user

        self.hr_user = self.env['res.users'].create({
            'name': 'HR User', 'login': 'to_hr_user',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        # --- Loại nghỉ Phép Năm + cấp 12 ngày cho NV Khối A, nghỉ vài ngày ---
        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self._allocate(self.emp_a, 12)
        self.taken_days = self._take_leave(self.emp_a, '2026-06-15', '2026-06-18')

    # ----- helpers -----
    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name,
            'department_id': dept.id,
            'x_employment_status': 'official',
            'identification_id': cccd,
            'x_pit_code': cccd[2:],          # 10 số, đủ định dạng MST test
            'x_social_insurance_no': cccd[:10],
        })

    def _allocate(self, emp, days):
        # Mẫu trong hocba_timeoff/models/hr_employee.py: create → _action_validate().
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ phép test %s' % emp.name,
            'holiday_status_id': self.annual.id,
            'employee_id': emp.id,
            'number_of_days': days,
            'allocation_type': 'regular',
            'date_from': '%d-01-01' % 2026,
            'date_to': '%d-12-31' % 2026,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _take_leave(self, emp, d_from, d_to):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ test',
            'holiday_status_id': self.annual.id,
            'employee_id': emp.id,
            'request_date_from': d_from,
            'request_date_to': d_to,
        })
        if leave.state != 'validate':
            leave.action_approve()
        if leave.state != 'validate':
            leave._action_validate()
        return leave.number_of_days

    def _mgr_scope(self):
        return _scope_for(self.env(user=self.mgr_user))

    # ----- scope -----
    def test_scope_normal_user_cannot_approve(self):
        scope = _scope_for(self.env(user=self.normal_user))
        self.assertFalse(scope['canApprove'])   # → endpoint trả 403
        self.assertTrue(scope['isEmployee'])
        self.assertFalse(scope['seeAll'])

    def test_scope_hr_sees_all(self):
        scope = _scope_for(self.env(user=self.hr_user))
        self.assertTrue(scope['seeAll'])
        self.assertTrue(scope['canApprove'])
        self.assertTrue(scope['isHrManager'])

    def test_scope_dept_manager_includes_child_dept(self):
        scope = self._mgr_scope()
        self.assertTrue(scope['canApprove'])
        self.assertFalse(scope['seeAll'])
        self.assertIn(self.dept_parent.id, scope['deptIds'])
        self.assertIn(self.dept_child.id, scope['deptIds'])      # phòng con
        self.assertNotIn(self.dept_other.id, scope['deptIds'])

    # ----- bảng số dư -----
    def test_dept_manager_table_scoped_to_managed_depts(self):
        scope = self._mgr_scope()
        data = _balances_table(self.env(user=self.mgr_user), scope, 2026)
        ids = {r['employeeId'] for r in data['rows']}
        self.assertIn(self.emp_a.id, ids)
        self.assertIn(self.emp_a1.id, ids)       # NV phòng con
        self.assertIn(self.emp_mgr.id, ids)
        self.assertNotIn(self.emp_b.id, ids)     # ngoài phạm vi → không thấy

    def test_hr_table_sees_other_department(self):
        scope = _scope_for(self.env(user=self.hr_user))
        data = _balances_table(self.env(user=self.hr_user), scope, 2026)
        ids = {r['employeeId'] for r in data['rows']}
        self.assertIn(self.emp_b.id, ids)        # HR thấy cả Khối B

    def test_only_hb_allocation_leave_types(self):
        scope = _scope_for(self.env(user=self.hr_user))
        data = _balances_table(self.env(user=self.hr_user), scope, 2026)
        # Chỉ Phép Năm (loại HB duy nhất requires_allocation), bỏ ~88 loại demo.
        self.assertEqual(len(data['leaveTypes']), 1)
        self.assertEqual(data['leaveTypes'][0]['id'], self.annual.id)
        self.assertIn(self.annual.id, _hb_leave_type_ids(self.env))

    def test_balance_values_and_kpi(self):
        scope = self._mgr_scope()
        data = _balances_table(self.env(user=self.mgr_user), scope, 2026)
        by_id = {r['employeeId']: r for r in data['rows']}

        # NV Khối A: cấp 12, đã nghỉ taken_days, còn lại = 12 - taken.
        row_a = by_id[self.emp_a.id]
        self.assertEqual(len(row_a['balances']), 1)
        bal = row_a['balances'][0]
        self.assertEqual(bal['allocated'], 12.0)
        self.assertGreater(self.taken_days, 0)
        self.assertEqual(bal['taken'], round(self.taken_days, 2))
        self.assertEqual(bal['remaining'], round(12 - self.taken_days, 2))
        self.assertEqual(row_a['totalRemaining'], round(12 - self.taken_days, 2))
        self.assertEqual(bal['kind'], 'teal')    # còn > 2 ngày

        # NV Tổ A1: không cấp phép → còn 0, nằm trong nhóm "sắp hết phép".
        row_a1 = by_id[self.emp_a1.id]
        self.assertEqual(row_a1['totalRemaining'], 0.0)
        self.assertLessEqual(row_a1['totalRemaining'], LOW_BALANCE_DAYS)

        # KPI: 3 NV trong phạm vi (TP + NV A + NV A1); 2 NV sắp hết (TP, A1).
        self.assertEqual(data['kpi']['employees'], 3)
        self.assertEqual(data['kpi']['employees'], len(data['rows']))
        self.assertEqual(data['kpi']['lowBalance'], 2)
        expect_total = round(sum(r['totalRemaining'] for r in data['rows']), 1)
        self.assertEqual(data['kpi']['totalRemaining'], expect_total)

    # ----- Phase 3: cảnh báo phép tồn -----
    def test_at_risk_flag_and_expire_date(self):
        scope = self._mgr_scope()
        data = _balances_table(self.env(user=self.mgr_user), scope, 2026)
        by_id = {r['employeeId']: r for r in data['rows']}
        # emp_a: cấp 12, nghỉ ~4 → còn >= 5 ngày Phép Năm ⇒ at-risk.
        self.assertGreaterEqual(12 - self.taken_days, AT_RISK_DAYS)
        self.assertTrue(by_id[self.emp_a.id]['atRisk'])
        self.assertEqual(by_id[self.emp_a.id]['expireDate'], '2026-12-31')
        # emp_a1: không có Phép Năm ⇒ không at-risk.
        self.assertFalse(by_id[self.emp_a1.id]['atRisk'])
        # KPI đếm số NV at-risk trên toàn phạm vi.
        self.assertEqual(data['atRiskDays'], AT_RISK_DAYS)
        self.assertGreaterEqual(data['kpi']['atRisk'], 1)

    def test_expiring_filter_returns_only_at_risk(self):
        scope = self._mgr_scope()
        full = _balances_table(self.env(user=self.mgr_user), scope, 2026)
        data = _balances_table(self.env(user=self.mgr_user), scope, 2026,
                               filter_mode='expiring')
        ids = {r['employeeId'] for r in data['rows']}
        self.assertIn(self.emp_a.id, ids)            # at-risk → giữ lại
        self.assertNotIn(self.emp_a1.id, ids)        # không at-risk → bị lọc
        self.assertNotIn(self.emp_mgr.id, ids)
        self.assertTrue(all(r['atRisk'] for r in data['rows']))
        # KPI vẫn tính trên TOÀN phạm vi (không đổi theo filter).
        self.assertEqual(data['kpi']['employees'], full['kpi']['employees'])
        self.assertEqual(data['kpi']['atRisk'], full['kpi']['atRisk'])
