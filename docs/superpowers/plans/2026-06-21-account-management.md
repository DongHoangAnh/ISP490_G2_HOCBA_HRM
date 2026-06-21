# Account Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** HR/Admin cấp tài khoản đăng nhập (login + mật khẩu + xác nhận) cho nhân viên mới và cấp lại mật khẩu khi quên — nhân viên không tự đăng ký; hỗ trợ 2 loại tài khoản (thường / giáo vụ / trưởng phòng).

**Architecture:** Logic đặt trong hàm module-level (`_account_create`, `_account_reset`, `_account_list`, `_account_payload`) trong `custom-addons/hocba_hrm/controllers/main.py`, nhận `env`, raise `AccessError`/`ValidationError`/`UserError`; route HTTP mỏng gọi và map lỗi → status. Test qua `TransactionCase`. Liên kết NV↔user qua field Odoo chuẩn `hr.employee.user_id` (không thêm model). SPA gọi `/hocba-hrm/api/...`.

**Tech Stack:** Odoo 19 (`res.users.group_ids`, `hr.department.manager_id`, `group_hocba_giaovu`), React 18 + Vite 6 (no TS).

**Spec:** `docs/superpowers/specs/2026-06-21-account-management-design.md`

---

## File Structure

**Backend (`custom-addons/hocba_hrm/`):**
- Modify `controllers/main.py` — thêm hằng + 4 hàm module-level + khối `account` trong `_employee_detail` + 3 route.
- Create `tests/test_account.py` — test cho 4 hàm.
- Modify `tests/__init__.py` — đăng ký test module.

**Frontend (`frontend/src/`):**
- Modify `api/employees.js` — 3 hàm API.
- Create `features/employees/AccountForm.jsx` — modal tạo / cấp lại.
- Modify `features/employees/EmployeeDrawer.jsx` — tab "Tài khoản" (HR) + AccountTab.
- Create `features/accounts/Accounts.jsx` — trang danh sách TK.
- Modify `app/Shell.jsx` — nav item + gate `need: 'hr'` + PAGE_META.
- Modify `app/App.jsx` — route view `accounts`.

**Backend trước (Task 1–8, TDD), Frontend sau (Task 9–13, build + verify thủ công).**

---

### Task 1: `_account_payload` helper

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_user_can_manage`, quanh dòng 1280)
- Test: `custom-addons/hocba_hrm/tests/test_account.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Đăng ký test module**

Trong `custom-addons/hocba_hrm/tests/__init__.py` thêm dòng cuối:

```python
from . import test_account
```

- [ ] **Step 2: Viết test thất bại**

Tạo `custom-addons/hocba_hrm/tests/test_account.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError

from odoo.addons.hocba_hrm.controllers.main import (
    _account_create, _account_reset, _account_list, _account_payload)


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
```

- [ ] **Step 3: Chạy test, xác nhận FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm:TestAccount --stop-after-init --log-level=test
```
Expected: FAIL — `ImportError: cannot import name '_account_payload'`.

- [ ] **Step 4: Cài đặt tối thiểu**

Trong `controllers/main.py`, sau hàm `_user_can_manage` (~dòng 1280) thêm:

```python
# --- Quản lý tài khoản đăng nhập (account management) --------------------
ACCOUNT_ROLES = ('employee', 'giaovu', 'truongphong')
MIN_PASSWORD_LEN = 8


def _account_payload(emp):
    """Khối trạng thái tài khoản đăng nhập cho hồ sơ NV."""
    u = emp.user_id
    if not u:
        return {'hasAccount': False}
    return {'hasAccount': True, 'login': u.login, 'active': u.active}
```

- [ ] **Step 5: Chạy lại test, xác nhận PASS**

Run: (lệnh như Step 3) — Expected: `0 failed, 0 error(s) of 1 tests`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/
git commit -m "feat(account): _account_payload + khung test"
```

---

### Task 2: `_account_create` — nhân viên thường

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestAccount`:

```python
    def test_create_normal(self):
        out = _account_create(self._env(self.hr), self.emp.id, {
            'login': 'va', 'password': '12345678',
            'password_confirm': '12345678', 'role': 'employee'})
        self.assertEqual(out, {'hasAccount': True, 'login': 'va', 'active': True})
        self.assertEqual(self.emp.user_id.login, 'va')
        self.assertTrue(self.emp.user_id.has_group('base.group_user'))
        self.assertFalse(self.emp.user_id.has_group(
            'hocba_employees.group_hocba_giaovu'))
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: (lệnh Task 1 Step 3) — Expected: FAIL `cannot import name '_account_create'`.

- [ ] **Step 3: Cài đặt**

Trong `controllers/main.py`, ngay dưới `_account_payload` thêm:

```python
def _is_hr(env):
    return env.user.has_group('hr.group_hr_user')


def _validate_password(body):
    pw = body.get('password') or ''
    pw2 = body.get('password_confirm') or ''
    if len(pw) < MIN_PASSWORD_LEN:
        raise ValidationError(
            'Mật khẩu phải có ít nhất %d ký tự.' % MIN_PASSWORD_LEN)
    if pw != pw2:
        raise ValidationError('Xác nhận mật khẩu không khớp.')
    return pw


def _account_create(env, emp_id, body):
    """HR/Admin cấp tài khoản đăng nhập cho 1 nhân viên.
    AccessError nếu không phải HR; ValidationError nếu dữ liệu sai;
    UserError nếu trưởng phòng cần xác nhận ghi đè."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được cấp tài khoản.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists():
        raise ValidationError('Không tìm thấy nhân viên.')
    if emp.user_id:
        raise ValidationError('Nhân viên đã có tài khoản. Dùng cấp lại mật khẩu.')
    login = (body.get('login') or '').strip()
    if not login:
        raise ValidationError('Vui lòng nhập tên đăng nhập.')
    if env['res.users'].sudo().with_context(active_test=False).search_count(
            [('login', '=', login)]):
        raise ValidationError('Tên đăng nhập đã tồn tại.')
    password = _validate_password(body)
    role = body.get('role') or 'employee'
    if role not in ACCOUNT_ROLES:
        raise ValidationError('Loại tài khoản không hợp lệ.')

    group_ids = [env.ref('base.group_user').id]
    if role == 'giaovu':
        group_ids.append(env.ref('hocba_employees.group_hocba_giaovu').id)

    dept = None
    if role == 'truongphong':
        dept_id = body.get('department_id')
        if not dept_id:
            raise ValidationError('Trưởng phòng cần chọn phòng ban.')
        dept = env['hr.department'].sudo().browse(int(dept_id))
        if not dept.exists():
            raise ValidationError('Phòng ban không hợp lệ.')
        if (dept.manager_id and dept.manager_id != emp
                and not body.get('confirm_overwrite')):
            raise UserError(
                'Phòng "%s" đã có trưởng phòng (%s). Xác nhận để ghi đè.'
                % (dept.name, dept.manager_id.name))

    user = env['res.users'].sudo().create({
        'name': emp.name, 'login': login, 'password': password,
        'group_ids': [(6, 0, group_ids)],
    })
    emp.sudo().user_id = user.id
    if dept is not None:
        dept.manager_id = emp.id
    return _account_payload(emp)
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 2 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_account.py
git commit -m "feat(account): _account_create cho nhân viên thường"
```

---

### Task 3: `_account_create` — giáo vụ & trưởng phòng

**Files:**
- Test: `custom-addons/hocba_hrm/tests/test_account.py` (code Task 2 đã hỗ trợ đủ; chỉ thêm test)

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestAccount`:

```python
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
```

- [ ] **Step 2: Chạy test, xác nhận PASS**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 6 tests`. (Logic đã có ở Task 2; nếu fail, sửa Task 2.)

> Lưu ý Odoo: `ValidationError` kế thừa `UserError`. Trong route (Task 7) phải `except ValidationError` TRƯỚC `except UserError`. Test ở đây bắt riêng từng loại nên không bị ảnh hưởng.

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/tests/test_account.py
git commit -m "test(account): giáo vụ + trưởng phòng (manager_id, ghi đè)"
```

---

### Task 4: `_account_create` — chặn lỗi quyền & dữ liệu

**Files:**
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestAccount`:

```python
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
```

- [ ] **Step 2: Chạy test, xác nhận PASS**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 11 tests`. (Logic đã có ở Task 2.)

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/tests/test_account.py
git commit -m "test(account): chặn non-HR/login trùng/MK lệch/MK ngắn/đã có TK"
```

---

### Task 5: `_account_reset` — cấp lại mật khẩu

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestAccount`:

```python
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
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: (lệnh Task 1 Step 3) — Expected: FAIL `cannot import name '_account_reset'`.

- [ ] **Step 3: Cài đặt**

Trong `controllers/main.py`, sau `_account_create` thêm:

```python
def _account_reset(env, emp_id, body):
    """HR/Admin cấp lại mật khẩu cho nhân viên đã có tài khoản."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được cấp lại mật khẩu.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists() or not emp.user_id:
        raise ValidationError('Nhân viên chưa có tài khoản.')
    password = _validate_password(body)
    emp.user_id.sudo().write({'password': password})
    return _account_payload(emp)
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 14 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_account.py
git commit -m "feat(account): _account_reset cấp lại mật khẩu"
```

---

### Task 6: `_account_list` — danh sách tài khoản

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestAccount`:

```python
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
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: (lệnh Task 1 Step 3) — Expected: FAIL `cannot import name '_account_list'`.

- [ ] **Step 3: Cài đặt**

Trong `controllers/main.py`, sau `_account_reset` thêm:

```python
def _account_list(env):
    """Danh sách NV đã có tài khoản + danh mục phòng ban (cho form). Chỉ HR."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được xem danh sách tài khoản.')
    Dept = env['hr.department'].sudo()
    emps = env['hr.employee'].sudo().search(
        [('user_id', '!=', False)], order='x_employee_code, id')
    rows = []
    for e in emps:
        u = e.user_id
        is_tp = bool(Dept.search_count([('manager_id', '=', e.id)]))
        is_gv = u.has_group('hocba_employees.group_hocba_giaovu')
        role = 'truongphong' if is_tp else ('giaovu' if is_gv else 'employee')
        rows.append({
            'employeeId': e.id, 'name': e.name,
            'code': e.x_employee_code or '', 'depName': e.department_id.name or '',
            'login': u.login, 'active': u.active, 'role': role,
        })
    depts = [{'id': d.id, 'name': d.name} for d in Dept.search([], order='name')]
    return {'accounts': rows, 'departments': depts}
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 16 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_account.py
git commit -m "feat(account): _account_list danh sách TK + phòng ban"
```

---

### Task 7: Route HTTP + khối `account` trong hồ sơ chi tiết

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm vào `_employee_detail` ~dòng 1545, thêm 3 route gần các route khác)

- [ ] **Step 1: Thêm khối `account` vào `_employee_detail`**

Trong `_employee_detail`, ngay trước `return data` (~dòng 1546) thêm:

```python
        if is_hr:
            data['account'] = _account_payload(e)
```

- [ ] **Step 2: Thêm 3 route**

Sau `api_employee_update` (~dòng 2075) thêm:

```python
    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_account_create(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_create(request.env, emp_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'needs_confirm', 'message': str(ex)}, status=409)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account/reset',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_account_reset(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_reset(request.env, emp_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/accounts', auth='user', type='http',
                methods=['GET'])
    def api_accounts(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_list(request.env)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        return request.make_json_response(data)
```

> `ValidationError` kế thừa `UserError` → BẮT BUỘC `except ValidationError` trước `except UserError`, nếu không ghi đè-confirm sẽ bị nuốt thành 400.

- [ ] **Step 3: Chạy lại toàn bộ test module, xác nhận không vỡ**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 16 tests`.

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(account): route tạo/reset/list + khối account trong hồ sơ"
```

---

### Task 8: API client FE

**Files:**
- Modify: `frontend/src/api/employees.js`

- [ ] **Step 1: Thêm 3 hàm API**

Cuối file `frontend/src/api/employees.js` thêm:

```js
/* Tài khoản đăng nhập (chỉ HR/Admin). createAccount/resetAccountPassword trả
   khối account đã cập nhật; fetchAccounts trả { accounts, departments }. */
export const createAccount = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account`, payload);
export const resetAccountPassword = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account/reset`, payload);
export const fetchAccounts = () => hbGet('/hocba-hrm/api/accounts');
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/employees.js
git commit -m "feat(account): hàm API FE create/reset/list"
```

---

### Task 9: AccountForm (modal tạo / cấp lại)

**Files:**
- Create: `frontend/src/features/employees/AccountForm.jsx`

- [ ] **Step 1: Tạo component**

Tạo `frontend/src/features/employees/AccountForm.jsx`:

```jsx
/* Form tạo / cấp lại tài khoản đăng nhập — chỉ HR/Admin. Owner: Tân.
   mode='create' | 'reset'. onDone(accountPayload) nhận khối account mới. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import { createAccount, resetAccountPassword } from '../../api/employees';

const ROLE_OPTS = [
  ['employee', 'Nhân viên thường'],
  ['giaovu', 'Giáo vụ'],
  ['truongphong', 'Trưởng phòng'],
];

export default function AccountForm({ emp, mode = 'create', departments = [], onClose, onDone }) {
  const reset = mode === 'reset';
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [role, setRole] = useState('employee');
  const [deptId, setDeptId] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (overwrite = false) => {
    setErr(null); setBusy(true);
    try {
      let res;
      if (reset) {
        res = await resetAccountPassword(emp.id, { password, password_confirm: confirm });
      } else {
        res = await createAccount(emp.id, {
          login, password, password_confirm: confirm, role,
          department_id: role === 'truongphong' ? Number(deptId) || 0 : undefined,
          confirm_overwrite: overwrite,
        });
      }
      onDone(res);
    } catch (e) {
      if (e.code === 'needs_confirm' && window.confirm(e.message)) {
        setBusy(false);
        return submit(true);
      }
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div style={{ padding: 24, minWidth: 380 }}>
        <h3 style={{ marginTop: 0 }}>
          {reset ? 'Cấp lại mật khẩu' : 'Tạo tài khoản'} — {emp.name}
        </h3>
        {!reset && (
          <label className="fld">
            <span>Tên đăng nhập</span>
            <input value={login} onChange={(e) => setLogin(e.target.value)}
              placeholder="email hoặc username" autoComplete="off" />
          </label>
        )}
        <label className="fld">
          <span>{reset ? 'Mật khẩu mới' : 'Mật khẩu'}</span>
          <input type="password" value={password} autoComplete="new-password"
            onChange={(e) => setPassword(e.target.value)} />
        </label>
        <label className="fld">
          <span>Xác nhận mật khẩu</span>
          <input type="password" value={confirm} autoComplete="new-password"
            onChange={(e) => setConfirm(e.target.value)} />
        </label>
        {!reset && (
          <label className="fld">
            <span>Loại tài khoản</span>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLE_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
        )}
        {!reset && role === 'truongphong' && (
          <label className="fld">
            <span>Phòng ban</span>
            <select value={deptId} onChange={(e) => setDeptId(e.target.value)}>
              <option value="">— Chọn phòng —</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </label>
        )}
        {err && <div style={{ color: 'var(--red-600)', marginTop: 8, fontSize: 13 }}>{err}</div>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Hủy</button>
          <button className="btn btn-primary" onClick={() => submit(false)} disabled={busy}>
            {busy ? 'Đang lưu…' : (reset ? 'Cấp lại' : 'Tạo tài khoản')}
          </button>
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/employees/AccountForm.jsx
git commit -m "feat(account): AccountForm modal tạo/cấp lại"
```

---

### Task 10: Tab "Tài khoản" trong EmployeeDrawer

**Files:**
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx`

- [ ] **Step 1: Thêm import**

Sửa dòng 4 (`import { fetchEmployee, ... }`) thành — thêm `fetchAccounts`:

```jsx
import { fetchEmployee, postGate, postTrial, deleteDependent, verifyCert, deleteCert, fetchAccounts } from '../../api/employees';
```

Thêm sau dòng `import CertForm from './CertForm';` (dòng 13):

```jsx
import AccountForm from './AccountForm';
```

- [ ] **Step 2: Thêm tab cho HR**

Sau khai báo `const tabs = [...]` (kết thúc ~dòng 31) thêm:

```jsx
  if (isHr) tabs.push(['account', 'Tài khoản']);
```

- [ ] **Step 3: Render AccountTab**

Sau dòng render tab `promo` (tìm `tab === 'promo'` trong vùng render ~dòng 70-80) thêm dòng:

```jsx
        {det && tab === 'account' && isHr && <AccountTab det={det} emp={emp} onUpdated={setDet} />}
```

- [ ] **Step 4: Thêm component AccountTab cuối file**

Cuối `EmployeeDrawer.jsx` thêm:

```jsx
function AccountTab({ det, emp, onUpdated }) {
  const acc = det.account || { hasAccount: false };
  const [mode, setMode] = useState(null);     // 'create' | 'reset' | null
  const [depts, setDepts] = useState([]);
  useEffect(() => {
    fetchAccounts().then((d) => setDepts(d.departments || [])).catch(() => {});
  }, []);
  const done = (accountPayload) => { onUpdated({ ...det, account: accountPayload }); setMode(null); };
  return (
    <div>
      {acc.hasAccount ? (
        <div className="card" style={{ padding: 16 }}>
          <div><b>Đăng nhập:</b> {acc.login}</div>
          <div style={{ marginTop: 4 }}><b>Trạng thái:</b> {acc.active ? 'Hoạt động' : 'Khóa'}</div>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 12 }}
            onClick={() => setMode('reset')}>
            <Icon name="rotateCcw" size={14} />Cấp lại mật khẩu</button>
        </div>
      ) : (
        <div className="card" style={{ padding: 16 }}>
          <div className="muted">Nhân viên chưa có tài khoản đăng nhập.</div>
          <button className="btn btn-primary btn-sm" style={{ marginTop: 12 }}
            onClick={() => setMode('create')}>
            <Icon name="shield" size={14} />Tạo tài khoản</button>
        </div>
      )}
      {mode && <AccountForm emp={emp} mode={mode} departments={depts}
        onClose={() => setMode(null)} onDone={done} />}
    </div>
  );
}
```

- [ ] **Step 5: Build SPA**

Run: `cd frontend && npm run build`
Expected: build thành công, không lỗi.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/employees/EmployeeDrawer.jsx custom-addons/hocba_hrm/static/spa/
git commit -m "feat(account): tab Tài khoản trong hồ sơ NV"
```

---

### Task 11: Trang "Tài khoản" (danh sách)

**Files:**
- Create: `frontend/src/features/accounts/Accounts.jsx`

- [ ] **Step 1: Tạo trang**

Tạo `frontend/src/features/accounts/Accounts.jsx`:

```jsx
/* Trang danh sách tài khoản đăng nhập (HR/Admin) — list + cấp lại MK. Owner: Tân. */
import { useState, useEffect } from 'react';
import { fetchAccounts } from '../../api/employees';
import AccountForm from '../employees/AccountForm';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const ROLE_LABEL = { employee: 'Nhân viên', giaovu: 'Giáo vụ', truongphong: 'Trưởng phòng' };

export default function Accounts({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [reset, setReset] = useState(null);   // { id, name } | null
  const load = () => { setErr(null); fetchAccounts().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);
  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tài khoản…" />;
  const q = search.trim().toLowerCase();
  const rows = data.accounts.filter((r) => !q
    || r.name.toLowerCase().includes(q)
    || (r.login || '').toLowerCase().includes(q)
    || (r.code || '').toLowerCase().includes(q));
  return (
    <div className="card">
      <table className="tbl">
        <thead><tr>
          <th>Nhân viên</th><th>Mã</th><th>Phòng ban</th>
          <th>Đăng nhập</th><th>Loại</th><th>Trạng thái</th><th></th>
        </tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.employeeId}>
              <td>{r.name}</td><td>{r.code}</td><td>{r.depName}</td>
              <td>{r.login}</td><td>{ROLE_LABEL[r.role] || r.role}</td>
              <td>{r.active ? 'Hoạt động' : 'Khóa'}</td>
              <td><button className="btn btn-ghost btn-sm"
                onClick={() => setReset({ id: r.employeeId, name: r.name })}>
                <Icon name="rotateCcw" size={14} />Cấp lại MK</button></td>
            </tr>
          ))}
          {!rows.length && (
            <tr><td colSpan={7}><EmptyState>Chưa có tài khoản.</EmptyState></td></tr>
          )}
        </tbody>
      </table>
      {reset && <AccountForm emp={reset} mode="reset"
        onClose={() => setReset(null)} onDone={() => { setReset(null); load(); }} />}
    </div>
  );
}
```

> Tạo TK cho NV mới làm trong tab "Tài khoản" của hồ sơ NV (Task 10). Trang này tập trung liệt kê + cấp lại MK (đúng phạm vi spec).

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/accounts/Accounts.jsx
git commit -m "feat(account): trang danh sách tài khoản"
```

---

### Task 12: Nav + routing

**Files:**
- Modify: `frontend/src/app/Shell.jsx`
- Modify: `frontend/src/app/App.jsx`

- [ ] **Step 1: Thêm nav item (Shell.jsx)**

Trong mảng `NAV`, section `'Quản lý nhân sự'`, sau dòng `recruitment` thêm:

```jsx
    { id: 'accounts', label: 'Tài khoản', icon: 'idcard', need: 'hr' },
```

- [ ] **Step 2: Thêm gate `need: 'hr'` (Shell.jsx)**

Trong hàm `allow`, trước `if (need === 'self')` thêm:

```jsx
  if (need === 'hr') return !!(me && (me.isHrUser || me.isHrManager || me.isAdmin));
```

- [ ] **Step 3: Thêm PAGE_META (Shell.jsx)**

Trong `PAGE_META`, sau dòng `recruitment:` thêm:

```jsx
  accounts: { t: 'Tài khoản', c: 'Quản lý nhân sự / Tài khoản' },
```

- [ ] **Step 4: Route view (App.jsx)**

Thêm import sau dòng `import Payroll ...` (dòng 11):

```jsx
import Accounts from '../features/accounts/Accounts';
```

Thêm sau dòng render `recruitment` (dòng 49):

```jsx
        {view === 'accounts' && canManage && me.isHrUser && <Accounts search={search} />}
```

- [ ] **Step 5: Build SPA**

Run: `cd frontend && npm run build`
Expected: build thành công.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/Shell.jsx frontend/src/app/App.jsx custom-addons/hocba_hrm/static/spa/
git commit -m "feat(account): nav + route trang Tài khoản (HR/Admin)"
```

---

### Task 13: Verify end-to-end + docs

**Files:**
- Modify: `docs/DB_TEST_DATA.md` (nếu seed tài khoản mới khi test thủ công)

- [ ] **Step 1: Chạy lại toàn bộ test backend module**

Run: (lệnh Task 1 Step 3) — Expected: `0 failed, 0 error(s) of 16 tests`.

- [ ] **Step 2: Verify SPA trong preview**

Dùng `preview_start` rồi đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026`:
1. Vào **Nhân viên** → mở 1 NV chưa có TK → tab **Tài khoản** → **Tạo tài khoản** (login + MK + xác nhận + loại) → lưu thành công, khối hiện login.
2. Mở lại NV đó → **Cấp lại mật khẩu** → đổi MK thành công.
3. Vào menu **Tài khoản** → thấy NV vừa tạo trong danh sách; nút **Cấp lại MK** hoạt động.
4. Đăng nhập `test_employee@hocba.vn` → KHÔNG thấy menu **Tài khoản**.

- [ ] **Step 3: Cập nhật docs (nếu có seed)**

Nếu tạo tài khoản test mới, ghi vào bảng + nhật ký `docs/DB_TEST_DATA.md`.

- [ ] **Step 4: Commit (nếu có thay đổi docs)**

```bash
git add docs/DB_TEST_DATA.md
git commit -m "docs(account): cập nhật DB_TEST_DATA sau khi test tài khoản"
```

---

## Self-Review (đã rà)

- **Spec coverage:** ai cấp TK (Task 2,4 — `_is_hr`), login tự nhập + duy nhất (Task 2,4), MK+xác nhận ≥8 (Task 2,4 — `_validate_password`), reset (Task 5), 2 loại TK: giáo vụ=group / trưởng phòng=manager_id (Task 3), khối account trong hồ sơ (Task 7), UI cả hai chỗ (Task 10,11), nav HR-only (Task 12), không self-signup (không thêm route đăng ký nào — mặc định). ✓
- **Placeholder scan:** không có TBD/TODO; mọi step có code/lệnh cụ thể. ✓
- **Type consistency:** `_account_payload` trả `{hasAccount, login, active}` — dùng nhất quán ở create/reset/detail/FE. `_account_list` trả `{accounts, departments}` — FE `fetchAccounts` đọc đúng `.accounts`/`.departments`. `role` ∈ `employee|giaovu|truongphong` đồng bộ BE↔FE. `needs_confirm` (409) ↔ FE `e.code === 'needs_confirm'`. ✓
- **Thứ tự except:** `ValidationError` trước `UserError` trong route create (đã ghi chú). ✓
