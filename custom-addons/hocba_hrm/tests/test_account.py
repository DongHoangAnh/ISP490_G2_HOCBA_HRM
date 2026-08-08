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

    def test_create_giaovu(self):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'gv', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'giaovu'})
        self.assertTrue(self.emp.user_id.has_group(
            'hocba_employees.group_hocba_giaovu'))

    def test_create_truongphong_sets_manager(self):
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'tp', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'truongphong',
            'department_id': self.dept.id})
        self.assertEqual(self.dept.manager_id, self.emp)

    def test_truongphong_requires_department(self):
        with self.assertRaises(ValidationError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'tp2', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'truongphong'})

    def test_truongphong_overwrite_needs_confirm(self):
        other = self.env['hr.employee'].create({
            'name': 'Other', 'x_employee_code': 'EMP-ACCT-2'})
        self.dept.manager_id = other.id
        with self.assertRaises(UserError):
            _account_create(self._env(self.hr), self.emp.id, {
                'login': 'tp3', 'password': '12345678',
                'password_confirm': '12345678', 'role': 'truongphong',
                'department_id': self.dept.id})
        _account_create(self._env(self.hr), self.emp.id, {
            'login': 'tp3', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'truongphong',
            'department_id': self.dept.id, 'confirm_overwrite': True})
        self.assertEqual(self.dept.manager_id, self.emp)

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
        out = _account_set_active(self._env(self.hr), self.emp.id, True)
        self.assertTrue(out['active'])
        self.assertTrue(self.emp.sudo().user_id.active)

    def test_set_active_forbidden_non_hr(self):
        self._mk_account('lock2')
        with self.assertRaises(AccessError):
            _account_set_active(self._env(self.plain), self.emp.id, False)

    def test_set_active_no_account(self):
        with self.assertRaises(ValidationError):
            _account_set_active(self._env(self.hr), self.emp.id, False)

    def test_set_active_cannot_lock_self(self):
        # NV gắn với chính user HR đang thao tác
        me = self.env['hr.employee'].create({
            'name': 'HR Self', 'x_employee_code': 'EMP-ACCT-SELF',
            'user_id': self.hr.id})
        with self.assertRaisesRegex(ValidationError, 'chính bạn'):
            _account_set_active(self._env(self.hr), me.id, False)

    def test_set_active_cannot_lock_system_admin(self):
        admin_user = self.env.ref('base.user_admin')
        # DB test đã có sẵn 1 hr.employee (archived) gắn với user_admin —
        # dùng lại nó thay vì tạo mới, để không vỡ unique constraint
        # hr_employee_user_uniq trên user_id.
        admin_emp = self.env['hr.employee'].sudo().with_context(
            active_test=False).search(
            [('user_id', '=', admin_user.id)], limit=1)
        if not admin_emp:
            admin_emp = self.env['hr.employee'].create({
                'name': 'Admin Emp', 'x_employee_code': 'EMP-ACCT-ADMIN',
                'user_id': admin_user.id})
        with self.assertRaisesRegex(ValidationError, 'quản trị hệ thống'):
            _account_set_active(self._env(self.hr), admin_emp.id, False)

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
