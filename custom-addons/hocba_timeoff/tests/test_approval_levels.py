# ============================================================
# Bậc duyệt theo LOẠI NGHỈ (hr.leave.type.leave_validation_type):
#   'hr'      → chỉ HR Manager/Admin
#   'manager' → chỉ Trưởng phòng của nhân viên
#   'both'    → HR Manager HOẶC Trưởng phòng (một trong hai là đủ)
# Test gọi thẳng _can_decide_leave/_scope_for cấp module với env(user=...)
# theo quy ước test của repo. Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _can_decide_leave,
)


@tagged('post_install', '-at_install')
class TestTimeoffApprovalLevels(TransactionCase):

    def setUp(self):
        super().setUp()
        Dept = self.env['hr.department']
        # Khối A có trưởng phòng; Khối C CỐ Ý bỏ trống manager_id để kiểm
        # đường lui "phòng chưa có trưởng phòng thì HR Manager duyệt thay".
        self.dept_a = Dept.create({'name': 'Khối A (bậc duyệt)'})
        self.dept_b = Dept.create({'name': 'Khối B (bậc duyệt)'})
        self.dept_c = Dept.create({'name': 'Khối C (không TP)'})

        self.emp_head = self._mk_emp('TP Khối A', '120000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV Khối A', '120000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV Khối B', '120000000003', self.dept_b)
        self.emp_c = self._mk_emp('NV Khối C', '120000000004', self.dept_c)
        self.dept_a.manager_id = self.emp_head.id

        self.head_user = self.env['res.users'].create({
            'name': 'TP User', 'login': 'lvl_head_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp_head.user_id = self.head_user

        self.hr_manager = self.env['res.users'].create({
            'name': 'HR Manager', 'login': 'lvl_hr_manager',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.hr_view_user = self.env['res.users'].create({
            'name': 'HR Nhan Vien', 'login': 'lvl_hr_user',
            'group_ids': [(4, self.env.ref('hr.group_hr_user').id)]})

        self.type_hr = self._mk_type('Nghỉ - HR duyệt', 'hr')
        self.type_mgr = self._mk_type('Nghỉ - TP duyệt', 'manager')
        self.type_both = self._mk_type('Nghỉ - HR/TP duyệt', 'both')

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

    def _mk_type(self, name, validation):
        return self.env['hr.leave.type'].create({
            'name': name,
            'requires_allocation': False,
            'leave_validation_type': validation,
            'request_unit': 'day',
            'x_hb_managed': True,
        })

    def _mk_leave(self, emp, leave_type, week=0):
        """week: dịch khoảng nghỉ sang tuần khác — Odoo cấm 1 NV có 2 đơn trùng
        ngày, nên test tạo nhiều đơn cho cùng NV phải tách tuần."""
        day = 7 + week * 7
        return self.env['hr.leave'].create({
            'name': 'Nghỉ test %s' % leave_type.name,
            'holiday_status_id': leave_type.id,
            'employee_id': emp.id,
            'request_date_from': '2026-09-%02d' % day,
            'request_date_to': '2026-09-%02d' % (day + 1),
        })

    def _can(self, user, leave):
        return _can_decide_leave(_scope_for(self.env(user=user)), leave)[0]

    # ----- 'hr': chỉ HR Manager -----
    def test_hr_type_only_hr_manager_decides(self):
        leave = self._mk_leave(self.emp_a, self.type_hr)
        self.assertTrue(self._can(self.hr_manager, leave))
        # Trưởng phòng vẫn thấy đơn của phòng mình nhưng KHÔNG được duyệt.
        self.assertFalse(self._can(self.head_user, leave))

    def test_hr_type_message_explains_role(self):
        leave = self._mk_leave(self.emp_a, self.type_hr)
        scope = _scope_for(self.env(user=self.head_user))
        ok, why = _can_decide_leave(scope, leave)
        self.assertFalse(ok)
        self.assertIn('HR Manager', why)

    # ----- 'manager': chỉ Trưởng phòng -----
    def test_manager_type_only_dept_head_decides(self):
        leave = self._mk_leave(self.emp_a, self.type_mgr)
        self.assertTrue(self._can(self.head_user, leave))
        # HR Manager thấy mọi phòng ban nhưng loại này để trưởng phòng quyết.
        self.assertFalse(self._can(self.hr_manager, leave))

    def test_manager_type_falls_back_to_hr_when_no_dept_head(self):
        """Phòng ban chưa gán trưởng phòng → đơn sẽ kẹt vĩnh viễn, nên HR
        Manager được đứng ra duyệt thay."""
        self.assertFalse(self.dept_c.manager_id)
        leave = self._mk_leave(self.emp_c, self.type_mgr)
        self.assertTrue(self._can(self.hr_manager, leave))

    def test_hr_manager_who_is_also_dept_head_decides_manager_type(self):
        """Một người vừa là HR Manager vừa là trưởng phòng: managedDeptIds phải
        được tính cả khi seeAll=True, nếu không sẽ mất quyền trưởng phòng."""
        self.dept_b.manager_id = self.env['hr.employee'].create({
            'name': 'HR kiêm TP', 'department_id': self.dept_b.id,
            'x_employment_status': 'official',
            'identification_id': '120000000009',
            'x_pit_code': '0000000009', 'x_social_insurance_no': '1200000000',
            'user_id': self.hr_manager.id,
        }).id
        leave = self._mk_leave(self.emp_b, self.type_mgr)
        scope = _scope_for(self.env(user=self.hr_manager))
        self.assertIn(self.dept_b.id, scope['managedDeptIds'])
        self.assertTrue(_can_decide_leave(scope, leave)[0])

    # ----- 'both': một trong hai -----
    def test_both_type_either_role_decides(self):
        leave = self._mk_leave(self.emp_a, self.type_both)
        self.assertTrue(self._can(self.hr_manager, leave))
        self.assertTrue(self._can(self.head_user, leave))

    # ----- phạm vi & vai trò chỉ xem vẫn giữ nguyên -----
    def test_dept_head_cannot_decide_other_department(self):
        leave = self._mk_leave(self.emp_b, self.type_both)
        self.assertFalse(self._can(self.head_user, leave))

    def test_hr_user_never_decides_any_type(self):
        for week, lt in enumerate((self.type_hr, self.type_mgr, self.type_both)):
            leave = self._mk_leave(self.emp_a, lt, week=week)
            self.assertFalse(self._can(self.hr_view_user, leave),
                             'HR User không được duyệt loại %s' % lt.name)
