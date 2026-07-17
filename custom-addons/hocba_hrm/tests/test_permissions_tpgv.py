from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.hocba_hrm.controllers.main import (
    HocBaHRM,
    _cap_edit_emp, _cap_see_salary, _cap_edit_salary, _cap_manage_account,
    _emp_in_scope,
)

MIN_LABELS = {'work_form': {}, 'status': {}, 'position': {}}


@tagged('post_install', '-at_install')
class TestDependentMeta(TransactionCase):
    """Bug #3: lựa chọn quan hệ NPT khả dụng cho NV thường (self-service)."""

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()
        self.emp_user = self.env['res.users'].create({
            'name': 'Plain', 'login': 'perm_plain',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

    def test_dependent_meta_available_to_plain_user(self):
        data = self.ctrl._dependent_meta(self.env(user=self.emp_user))
        rels = dict(data['relationship'])
        self.assertIn('child', rels)
        self.assertEqual(len(data['relationship']), 5)


@tagged('post_install', '-at_install')
class TestCapabilityFlags(TransactionCase):
    """Item 2: cờ năng lực đúng cho 5 vai trò."""

    def setUp(self):
        super().setUp()
        gu = self.env.ref('base.group_user').id
        self.dept = self.env['hr.department'].create({'name': 'QA Perm Dept'})
        # Trưởng phòng
        self.tp_user = self.env['res.users'].create({
            'name': 'TP', 'login': 'perm_tp', 'group_ids': [(6, 0, [gu])]})
        self.tp_emp = self.env['hr.employee'].create({
            'name': 'TP Emp', 'identification_id': '012000000001',
            'user_id': self.tp_user.id, 'department_id': self.dept.id})
        self.dept.manager_id = self.tp_emp.id
        # Giáo vụ
        self.gv_user = self.env['res.users'].create({
            'name': 'GV', 'login': 'perm_gv', 'group_ids': [(6, 0, [
                gu, self.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        # HR officer
        self.hr_user = self.env['res.users'].create({
            'name': 'HRU', 'login': 'perm_hru', 'group_ids': [(6, 0, [
                gu, self.env.ref('hr.group_hr_user').id])]})
        # HR manager
        self.mgr_user = self.env['res.users'].create({
            'name': 'HRM', 'login': 'perm_hrm', 'group_ids': [(6, 0, [
                gu, self.env.ref('hr.group_hr_manager').id])]})
        # NV thường
        self.nv_user = self.env['res.users'].create({
            'name': 'NV', 'login': 'perm_nv', 'group_ids': [(6, 0, [gu])]})

    def _e(self, u):
        return self.env(user=u)

    def test_can_edit_emp(self):
        for u in (self.tp_user, self.gv_user, self.hr_user, self.mgr_user):
            self.assertTrue(_cap_edit_emp(self._e(u)), u.login)
        self.assertFalse(_cap_edit_emp(self._e(self.nv_user)))

    def test_can_see_salary(self):
        for u in (self.tp_user, self.gv_user, self.mgr_user):
            self.assertTrue(_cap_see_salary(self._e(u)), u.login)
        for u in (self.hr_user, self.nv_user):
            self.assertFalse(_cap_see_salary(self._e(u)), u.login)

    def test_can_edit_salary(self):
        self.assertTrue(_cap_edit_salary(self._e(self.mgr_user)))
        for u in (self.tp_user, self.gv_user, self.hr_user, self.nv_user):
            self.assertFalse(_cap_edit_salary(self._e(u)), u.login)

    def test_can_manage_account(self):
        for u in (self.hr_user, self.mgr_user):
            self.assertTrue(_cap_manage_account(self._e(u)), u.login)
        for u in (self.tp_user, self.gv_user, self.nv_user):
            self.assertFalse(_cap_manage_account(self._e(u)), u.login)


@tagged('post_install', '-at_install')
class TestScopeEnforcement(TransactionCase):
    """Item 2: phạm vi ghi cho TP (phòng mình) và GV (giáo viên)."""

    def setUp(self):
        super().setUp()
        gu = self.env.ref('base.group_user').id
        self.dept = self.env['hr.department'].create({'name': 'Scope Dept'})
        self.other = self.env['hr.department'].create({'name': 'Scope Other'})
        self.tp_user = self.env['res.users'].create({
            'name': 'TP2', 'login': 'scope_tp', 'group_ids': [(6, 0, [gu])]})
        self.tp_emp = self.env['hr.employee'].create({
            'name': 'TP2 Emp', 'identification_id': '013000000001',
            'user_id': self.tp_user.id, 'department_id': self.dept.id})
        self.dept.manager_id = self.tp_emp.id
        self.in_emp = self.env['hr.employee'].create({
            'name': 'In Dept', 'identification_id': '013000000002',
            'department_id': self.dept.id})
        self.out_emp = self.env['hr.employee'].create({
            'name': 'Out Dept', 'identification_id': '013000000003',
            'department_id': self.other.id})
        # Giáo vụ + giáo viên
        self.gv_user = self.env['res.users'].create({
            'name': 'GV2', 'login': 'scope_gv', 'group_ids': [(6, 0, [
                gu, self.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        tt = self.env['hocba.employee.type'].search(
            [('code', '=', 'teacher')], limit=1)
        self.teacher = self.env['hr.employee'].create({
            'name': 'A Teacher', 'identification_id': '013000000004',
            'x_employee_type_id': tt.id if tt else False})

    def test_tp_scope(self):
        env = self.env(user=self.tp_user)
        self.assertTrue(_emp_in_scope(env, self.in_emp))
        self.assertFalse(_emp_in_scope(env, self.out_emp))

    def test_gv_scope_teacher_only(self):
        env = self.env(user=self.gv_user)
        self.assertTrue(_emp_in_scope(env, self.teacher))
        self.assertFalse(_emp_in_scope(env, self.out_emp))

    def test_emp_base_salary_visibility(self):
        ctrl = HocBaHRM()
        base_yes = ctrl._emp_base(self.in_emp, MIN_LABELS, True)
        base_no = ctrl._emp_base(self.in_emp, MIN_LABELS, False)
        self.assertIn('wage', base_yes)
        self.assertNotIn('wage', base_no)

    # Ghi chú: khối pháp lý/NPT/chứng chỉ vs tài khoản trong _employee_detail
    # phụ thuộc request context (_can_eval_emp/_can_eval_trial) nên không unit-test
    # trực tiếp — đã kiểm end-to-end trên preview (TP thấy cccd/dependents/certs/
    # wage, KHÔNG thấy account; ngoài phạm vi → 403).
