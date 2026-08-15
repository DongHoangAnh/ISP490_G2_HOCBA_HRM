from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.addons.hocba_hrm.controllers.main import _dept_payload, _dept_list, _dept_create, _dept_update, _dept_archive


@tagged('post_install', '-at_install')
class TestDepartment(TransactionCase):

    def setUp(self):
        super().setUp()
        # HR officer: CHỈ được xem phòng ban (chốt 2026-08-15 — xem _cap_edit_dept).
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        # HR Manager: được thêm/sửa/lưu trữ.
        self.hrm = self.env['res.users'].create({
            'name': 'HR Manager', 'login': 'hrm_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        # Admin "thuần" — base.group_system, KHÔNG kèm nhóm HR nào. Tài khoản
        # test_admin@hocba.vn trong DB thật đúng dạng này.
        self.admin = self.env['res.users'].create({
            'name': 'Admin', 'login': 'admin_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('base.group_system').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV A', 'department_id': self.dept.id})
        # NV đã có tài khoản → hợp lệ để gán làm trưởng phòng (_dept_update).
        self.emp_user = self.env['hr.employee'].create({
            'name': 'NV Có TK', 'department_id': self.dept.id,
            'user_id': self.env['res.users'].create({
                'name': 'NV Có TK', 'login': 'nv_co_tk',
                'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
            }).id})

    def _env(self, user):
        return self.env(user=user)

    def _mgr_block(self, login='tp_moi', name='TP Mới'):
        """Khối 'manager' bắt buộc khi tạo phòng ban (trưởng phòng mới)."""
        return {'name': name, 'login': login,
                'password': 'Hocba@2026', 'password_confirm': 'Hocba@2026'}

    # ---- Ràng buộc xóa (Task 1) ----
    def test_unlink_blocked_when_has_members(self):
        with self.assertRaises(UserError):
            self.dept.unlink()

    def test_unlink_blocked_when_has_children(self):
        parent = self.env['hr.department'].create({'name': 'Cha'})
        self.env['hr.department'].create({'name': 'Con', 'parent_id': parent.id})
        with self.assertRaises(UserError):
            parent.unlink()

    def test_unlink_ok_when_empty(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        empty.unlink()
        self.assertFalse(empty.exists())

    # ---- _dept_list / _dept_payload (Task 2) ----
    def test_list_forbidden_for_plain(self):
        with self.assertRaises(AccessError):
            _dept_list(self._env(self.plain))

    def test_list_returns_departments_and_employees(self):
        out = _dept_list(self._env(self.hr))
        names = [d['name'] for d in out['departments']]
        self.assertIn('Phòng A', names)
        self.assertTrue(any(e['id'] == self.emp_user.id for e in out['employees']))

    def test_payload_employee_count(self):
        out = _dept_list(self._env(self.hr))
        row = next(d for d in out['departments'] if d['id'] == self.dept.id)
        self.assertEqual(row['employeeCount'], 2)
        self.assertTrue(row['active'])

    def test_list_excludes_archived_by_default(self):
        self.dept.active = False
        names = [d['name'] for d in _dept_list(self._env(self.hr))['departments']]
        self.assertNotIn('Phòng A', names)

    def test_list_includes_archived_when_requested(self):
        self.dept.active = False
        names = [d['name'] for d in
                 _dept_list(self._env(self.hr), archived=True)['departments']]
        self.assertIn('Phòng A', names)

    # ---- Cờ canEdit: FE ẩn nút Thêm/Sửa/Lưu trữ theo cờ này ----
    def test_list_can_edit_false_for_hr_officer(self):
        self.assertFalse(_dept_list(self._env(self.hr))['canEdit'])

    def test_list_can_edit_true_for_hr_manager(self):
        self.assertTrue(_dept_list(self._env(self.hrm))['canEdit'])

    def test_list_allowed_for_admin_without_hr_group(self):
        """Admin thuần (base.group_system) phải xem được — nav vẫn bày menu
        Phòng ban cho Admin, chặn ở đây là 403 giữa mặt."""
        out = _dept_list(self._env(self.admin))
        self.assertIn('Phòng A', [d['name'] for d in out['departments']])
        self.assertTrue(out['canEdit'])

    # ---- _dept_create (Task 3) ----
    def test_create_ok(self):
        out = _dept_create(self._env(self.hrm), {
            'name': 'Phòng Mới', 'functionDesc': 'Mô tả',
            'manager': self._mgr_block()})
        self.assertEqual(out['name'], 'Phòng Mới')
        self.assertEqual(out['functionDesc'], 'Mô tả')
        self.assertEqual(out['managerName'], 'TP Mới')
        self.assertTrue(out['active'])

    def test_create_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_create(self._env(self.hrm), {'name': '   '})

    def test_create_without_manager_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_create(self._env(self.hrm), {'name': 'Phòng Thiếu TP'})

    def test_create_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_create(self._env(self.plain), {'name': 'X'})

    def test_create_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_create(self._env(self.hr), {
                'name': 'Phòng HR tạo', 'manager': self._mgr_block()})

    # ---- _dept_update (Task 4) ----
    def test_update_changes_fields(self):
        out = _dept_update(self._env(self.hrm), self.dept.id, {
            'name': 'Phòng A2', 'functionDesc': 'Mới',
            'managerId': self.emp_user.id})
        self.assertEqual(out['name'], 'Phòng A2')
        self.assertEqual(out['functionDesc'], 'Mới')
        self.assertEqual(self.dept.manager_id, self.emp_user)

    def test_update_clears_manager(self):
        self.dept.manager_id = self.emp_user.id
        out = _dept_update(self._env(self.hrm), self.dept.id, {
            'name': 'Phòng A', 'managerId': False})
        self.assertFalse(out['managerId'])
        self.assertFalse(self.dept.manager_id)

    def test_update_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_update(self._env(self.hrm), self.dept.id, {'name': ''})

    def test_update_manager_without_account_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_update(self._env(self.hrm), self.dept.id, {
                'name': 'Phòng A', 'managerId': self.emp.id})

    def test_update_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_update(self._env(self.plain), self.dept.id, {'name': 'X'})

    def test_update_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_update(self._env(self.hr), self.dept.id, {'name': 'X'})

    # ---- _dept_archive (Task 5) ----
    def test_archive_sets_inactive(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        out = _dept_archive(self._env(self.hrm), empty.id, {'active': False})
        self.assertFalse(out['active'])
        self.assertFalse(empty.active)

    def test_archive_restore(self):
        self.dept.active = False
        out = _dept_archive(self._env(self.hrm), self.dept.id, {'active': True})
        self.assertTrue(out['active'])
        self.assertTrue(self.dept.active)

    def test_archive_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_archive(self._env(self.plain), self.dept.id, {'active': False})

    def test_archive_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_archive(self._env(self.hr), self.dept.id, {'active': False})
