# ============================================================
# Test Phase 2 — Điều chỉnh quỹ phép thủ công + nhật ký.
# Gọi thẳng hàm cấp module (_apply_quota_adjustment / _adjustment_history /
# _scope_for) như quy ước test của repo. Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _apply_quota_adjustment, _adjustment_history,
)


@tagged('post_install', '-at_install')
class TestTimeoffAdjustment(TransactionCase):

    def setUp(self):
        super().setUp()
        Dept = self.env['hr.department']
        self.dept_parent = Dept.create({'name': 'Khối A (adj)'})
        self.dept_other = Dept.create({'name': 'Khối B (adj)'})

        self.emp_mgr = self._mk_emp('TP adj', '120000000001', self.dept_parent)
        self.emp_a = self._mk_emp('NV A adj', '120000000002', self.dept_parent)
        self.emp_b = self._mk_emp('NV B adj', '120000000003', self.dept_other)
        self.dept_parent.manager_id = self.emp_mgr.id

        self.mgr_user = self.env['res.users'].create({
            'name': 'TP adj user', 'login': 'adj_mgr_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_mgr.user_id = self.mgr_user
        self.normal_user = self.env['res.users'].create({
            'name': 'NV adj user', 'login': 'adj_normal_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_b.user_id = self.normal_user
        self.hr_user = self.env['res.users'].create({
            'name': 'HR adj user', 'login': 'adj_hr_user',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self._allocate(self.emp_a, 10)
        self._allocate(self.emp_b, 10)

    # ----- helpers -----
    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10]})

    def _allocate(self, emp, days):
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ test %s' % emp.name, 'holiday_status_id': self.annual.id,
            'employee_id': emp.id, 'number_of_days': days,
            'allocation_type': 'regular',
            'date_from': '2026-01-01', 'date_to': '2026-12-31'})
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _remaining(self, emp):
        lt = (self.env['hr.leave.type'].with_context(employee_id=emp.id)
              .browse(self.annual.id))
        return round(lt.virtual_remaining_leaves, 2)

    def _apply(self, emp, delta, reason='lý do test'):
        return _apply_quota_adjustment(self.env, emp, self.annual, delta, reason, 2026)

    # ----- phân quyền (gate ở endpoint = scope['isHrManager']) -----
    def test_only_hr_manager_flag_can_adjust(self):
        self.assertTrue(_scope_for(self.env(user=self.hr_user))['isHrManager'])
        # Trưởng phòng có quyền duyệt nhưng KHÔNG được chỉnh quỹ (open Q#1).
        self.assertTrue(_scope_for(self.env(user=self.mgr_user))['canApprove'])
        self.assertFalse(_scope_for(self.env(user=self.mgr_user))['isHrManager'])
        self.assertFalse(_scope_for(self.env(user=self.normal_user))['isHrManager'])

    # ----- cộng phép -----
    def test_increase_adds_remaining_and_logs(self):
        before = self._remaining(self.emp_a)            # 10
        self._apply(self.emp_a, 3, 'thưởng thâm niên')
        self.assertEqual(self._remaining(self.emp_a), round(before + 3, 2))
        logs = self.env['hb.leave.adjustment'].search([
            ('employee_id', '=', self.emp_a.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.delta_days, 3)
        self.assertEqual(logs.reason, 'thưởng thâm niên')
        self.assertTrue(logs.allocation_id)             # liên kết allocation mới
        self.assertEqual(logs.leave_type_id, self.annual)

    # ----- trừ phép -----
    def test_decrease_partial_reduces_remaining(self):
        self._apply(self.emp_a, -4, 'sửa nhầm')
        self.assertEqual(self._remaining(self.emp_a), 6.0)
        log = self.env['hb.leave.adjustment'].search([
            ('employee_id', '=', self.emp_a.id)], limit=1)
        self.assertEqual(log.delta_days, -4)
        self.assertTrue(log.allocation_id)

    def test_decrease_whole_zeroes_remaining(self):
        self._apply(self.emp_a, -10, 'thu hồi toàn bộ')
        self.assertEqual(self._remaining(self.emp_a), 0.0)

    def test_decrease_over_balance_rejected(self):
        with self.assertRaises(ValidationError):
            self._apply(self.emp_a, -100, 'trừ quá tay')
        # số dư không đổi sau khi bị từ chối
        self.assertEqual(self._remaining(self.emp_a), 10.0)

    # ----- validate đầu vào -----
    def test_zero_delta_rejected(self):
        with self.assertRaises(ValidationError):
            self._apply(self.emp_a, 0, 'không hợp lệ')

    def test_empty_reason_rejected(self):
        with self.assertRaises(ValidationError):
            self._apply(self.emp_a, 2, '   ')

    # ----- nhật ký + phạm vi -----
    def test_history_scoped_by_department(self):
        self._apply(self.emp_a, 1, 'A +1')      # Khối A (trong phạm vi TP)
        self._apply(self.emp_b, 1, 'B +1')      # Khối B (ngoài phạm vi TP)

        hr_scope = _scope_for(self.env(user=self.hr_user))
        hr_hist = _adjustment_history(self.env, hr_scope)
        hr_emp_ids = {h['employeeId'] for h in hr_hist}
        self.assertIn(self.emp_a.id, hr_emp_ids)
        self.assertIn(self.emp_b.id, hr_emp_ids)        # HR thấy cả hai

        mgr_scope = _scope_for(self.env(user=self.mgr_user))
        mgr_hist = _adjustment_history(self.env, mgr_scope)
        mgr_emp_ids = {h['employeeId'] for h in mgr_hist}
        self.assertIn(self.emp_a.id, mgr_emp_ids)
        self.assertNotIn(self.emp_b.id, mgr_emp_ids)    # TP không thấy Khối B

    def test_history_filter_by_employee(self):
        self._apply(self.emp_a, 1, 'A +1')
        self._apply(self.emp_b, 2, 'B +2')
        hr_scope = _scope_for(self.env(user=self.hr_user))
        only_a = _adjustment_history(self.env, hr_scope, employee_id=self.emp_a.id)
        self.assertTrue(only_a)
        self.assertTrue(all(h['employeeId'] == self.emp_a.id for h in only_a))
