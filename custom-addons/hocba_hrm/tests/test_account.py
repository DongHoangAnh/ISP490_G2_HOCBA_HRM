from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError

from odoo.addons.hocba_hrm.controllers.main import (
    _account_create, _account_reset, _account_list, _account_payload,
    _account_set_active)


@tagged('post_install', '-at_install')
class TestAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng Test'})
        self.emp = self.env['hr.employee'].create({
            'name': 'Nguyen Van A', 'x_employee_code': 'EMP-ACCT-1',
            'department_id': self.dept.id})

    def _env(self, user):
        return self.env(user=user)

    def test_payload_empty(self):
        self.assertEqual(_account_payload(self.emp), {'hasAccount': False})

    def test_create_normal(self):
        out = _account_create(self._env(self.hr), self.emp.id, {
            'login': 'va', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})
        self.assertEqual(out, {'hasAccount': True, 'login': 'va', 'active': True})
        self.assertEqual(self.emp.user_id.login, 'va')
        self.assertTrue(self.emp.user_id.has_group('base.group_user'))
        self.assertFalse(self.emp.user_id.has_group(
            'hocba_employees.group_hocba_giaovu'))

    # Từ 2026-08-27 màn này CHỈ cấp tài khoản nhân viên thường. Trưởng phòng và
    # giáo vụ là tài khoản vai trò riêng, tạo ở form phòng ban — cấp ở đây là
    # đeo quyền quản lý vào tài khoản cá nhân của một NV có thật, đúng mô hình
    # kiêm nhiệm mà migration 19.0.7.0.0 / 19.0.8.0.0 đã dọn.
    def test_create_giaovu_bi_tu_choi(self):
        with self.assertRaisesRegex(ValidationError, 'nhân viên thường'):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'gv', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'giaovu'})
        self.assertFalse(self.emp.user_id)

    def test_create_truongphong_bi_tu_choi(self):
        with self.assertRaisesRegex(ValidationError, 'nhân viên thường'):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'tp', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'truongphong',
                'department_id': self.dept.id})
        # Quan trọng hơn cả việc ném lỗi: KHÔNG được để lại dấu vết nào —
        # không tài khoản, không manager_id.
        self.assertFalse(self.emp.user_id)
        self.assertFalse(self.dept.manager_id)

    def test_create_forbidden_non_hr(self):
        with self.assertRaises(AccessError):
            _account_create(self._env(self.plain), self.emp.id, {
                'login': 'x', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'employee'})

    def test_create_duplicate_login(self):
        with self.assertRaises(ValidationError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'hr_acct', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'employee'})

    def test_create_password_mismatch(self):
        with self.assertRaises(ValidationError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'y', 'password': '12345678',
                'password_confirm': '99999999', 'role': 'employee'})

    def test_create_password_too_short(self):
        with self.assertRaises(ValidationError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'z', 'password': '123', 'password_confirm': '123',
                'role': 'employee'})

    def test_create_already_has_account(self):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'first', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})
        with self.assertRaises(ValidationError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'second', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'employee'})

    def test_reset_changes_password(self):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'rst', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})
        out = _account_reset(self._env(self.hr), self.emp.id, {
            'password': 'newpass99', 'password_confirm': 'newpass99'})
        self.assertEqual(out['login'], 'rst')

    def test_reset_forbidden_non_hr(self):
        with self.assertRaises(AccessError):
            _account_reset(self._env(self.plain), self.emp.id, {
                'password': 'newpass99', 'password_confirm': 'newpass99'})

    def test_reset_no_account(self):
        with self.assertRaises(ValidationError):
            _account_reset(self._env(self.hr), self.emp.id, {
                'password': 'newpass99', 'password_confirm': 'newpass99'})

    def test_list_hr(self):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'lst', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})
        out = _account_list(self._env(self.hr))
        logins = [r['login'] for r in out['accounts']]
        self.assertIn('lst', logins)
        self.assertTrue(any(d['id'] == self.dept.id for d in out['departments']))

    def test_list_flags_system_admin_row(self):
        # FE ẩn nút khóa cho tài khoản quản trị hệ thống dựa vào cờ này.
        self._mk_account('sysflag')
        sysadmin = self.env['res.users'].create({
            'name': 'Sys List', 'login': 'sys_list_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('base.group_system').id])]})
        sys_emp = self.env['hr.employee'].create({
            'name': 'Sys List Emp', 'x_employee_code': 'EMP-ACCT-SYSL',
            'user_id': sysadmin.id})
        rows = {r['employeeId']: r for r in _account_list(
            self._env(self.hr))['accounts']}
        self.assertTrue(rows[sys_emp.id]['isSystem'])
        self.assertFalse(rows[self.emp.id]['isSystem'])

    def test_list_forbidden_non_hr(self):
        with self.assertRaises(AccessError):
            _account_list(self._env(self.plain))

    def _mk_account(self, login='lockme'):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': login, 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})

    def test_set_active_lock_then_unlock(self):
        self._mk_account('lock1')
        out = _account_set_active(self._env(self.hr), self.emp.id, False)
        self.assertEqual(out, {'hasAccount': True, 'login': 'lock1',
                               'active': False})
        self.assertFalse(self.emp.sudo().user_id.active)
        # Audit log phải nêu tên người thao tác (spec §4.1), không được
        # ghi vô danh.
        msg = self.emp.sudo().message_ids[0]
        self.assertIn(self.hr.name, msg.body)
        msg_count = len(self.emp.sudo().message_ids)

        out = _account_set_active(self._env(self.hr), self.emp.id, True)
        self.assertTrue(out['active'])
        self.assertTrue(self.emp.sudo().user_id.active)

        # No-op: khóa một tài khoản đã khóa lại không được ghi thêm chatter.
        _account_set_active(self._env(self.hr), self.emp.id, True)
        self.assertEqual(len(self.emp.sudo().message_ids), msg_count + 1)

    def test_set_active_forbidden_non_hr(self):
        self._mk_account('lock2')
        with self.assertRaises(AccessError):
            _account_set_active(self._env(self.plain), self.emp.id, False)

    def test_set_active_no_account(self):
        with self.assertRaisesRegex(ValidationError, 'chưa có tài khoản'):
            _account_set_active(self._env(self.hr), self.emp.id, False)

    def test_set_active_employee_not_found(self):
        with self.assertRaisesRegex(ValidationError, 'Không tìm thấy nhân viên'):
            _account_set_active(self._env(self.hr), 999999, False)

    def test_set_active_cannot_lock_self(self):
        # NV gắn với chính user HR đang thao tác
        me = self.env['hr.employee'].create({
            'name': 'HR Self', 'x_employee_code': 'EMP-ACCT-SELF',
            'user_id': self.hr.id})
        with self.assertRaisesRegex(ValidationError, 'chính bạn'):
            _account_set_active(self._env(self.hr), me.id, False)

    def test_set_active_cannot_lock_system_admin(self):
        sysadmin = self.env['res.users'].create({
            'name': 'Sys', 'login': 'sys_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('base.group_system').id])]})
        emp = self.env['hr.employee'].create({
            'name': 'Sys Emp', 'x_employee_code': 'EMP-ACCT-SYS',
            'user_id': sysadmin.id})
        with self.assertRaisesRegex(ValidationError, 'quản trị hệ thống'):
            _account_set_active(self._env(self.hr), emp.id, False)

    def test_set_active_locks_archived_employee(self):
        # NV đã nghỉ (archived) vẫn phải khóa được — đó là lý do màn Tài
        # khoản liệt kê cả họ.
        self._mk_account('arch_lock')
        self.emp.sudo().write({'active': False})
        out = _account_set_active(self._env(self.hr), self.emp.id, False)
        self.assertFalse(out['active'])

    def test_set_active_cannot_unlock_resigned(self):
        self._mk_account('arch_unlock')
        self.emp.sudo().user_id.write({'active': False})
        self.emp.sudo().write({'active': False})
        with self.assertRaisesRegex(ValidationError, 'đã nghỉ việc'):
            _account_set_active(self._env(self.hr), self.emp.id, True)

    def test_list_includes_archived_employee_with_dep_fields(self):
        self._mk_account('arch1')
        self.emp.sudo().write({'active': False})   # như sau offboarding
        out = _account_list(self._env(self.hr))
        row = next((r for r in out['accounts'] if r['login'] == 'arch1'),
                   None)
        self.assertIsNotNone(row, 'NV đã archive phải còn trong danh sách')
        self.assertEqual(row['depId'], self.dept.id)
        self.assertFalse(row['empActive'])
        # Chỉ hồ sơ NV bị archive, tài khoản đăng nhập vẫn còn active —
        # hai khái niệm khác nhau, không được trộn.
        self.assertTrue(row['active'])

    def test_list_role_ignores_archived_department(self):
        # NV làm trưởng một phòng ban ĐÃ ARCHIVE thì không được gắn nhãn
        # truongphong — bảo toàn ngữ nghĩa cũ của Dept.search_count (chỉ
        # đếm phòng ban active) sau khi bỏ N+1 search_count.
        self._mk_account('arch_dept')
        self.dept.sudo().write({'manager_id': self.emp.id, 'active': False})
        out = _account_list(self._env(self.hr))
        row = next(r for r in out['accounts'] if r['login'] == 'arch_dept')
        self.assertEqual(row['role'], 'employee')

    def test_list_includes_fully_offboarded_employee(self):
        self._mk_account('offb1')
        # Trạng thái thật sau offboarding: archive CẢ hồ sơ NV lẫn tài khoản
        self.emp.sudo().user_id.sudo().write({'active': False})
        self.emp.sudo().write({'active': False})
        out = _account_list(self._env(self.hr))
        row = next((r for r in out['accounts'] if r['login'] == 'offb1'), None)
        self.assertIsNotNone(row)
        self.assertFalse(row['active'])
        self.assertFalse(row['empActive'])
