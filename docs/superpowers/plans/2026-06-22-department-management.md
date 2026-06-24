# Quản lý Phòng ban — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm chức năng CRUD quản lý phòng ban (xem/tạo/sửa/lưu trữ) trong SPA `/hocba-hrm`, chỉ HR/Admin, dùng API thật + dữ liệu thật.

**Architecture:** Backend-first theo TDD. Model `hr.department` thêm ràng buộc chặn xóa cứng (còn nhân viên/phòng con). Controller `hocba_hrm` thêm helper cấp module (`_dept_*`) + routes `/hocba-hrm/api/departments*`, guard bằng `_is_hr`. SPA thêm api module + feature component, đăng ký vào nav/router. Mọi thứ mô phỏng pattern "account management" đã hoàn thành.

**Tech Stack:** Odoo 19 (Python), `hr.department`/`hr.employee`; React 18 + Vite 6 (không TypeScript); test `odoo.tests.common.TransactionCase`.

**Spec:** `docs/superpowers/specs/2026-06-22-department-management-design.md`

> **Lưu ý đính chính spec:** Mục 6 của spec ghi path FE cũ (`hrm-shell.jsx`, `hrm-app.jsx`, `hrm-departments.jsx`). Nguồn FE THẬT là `frontend/src/` (cấu trúc `api/`, `features/`, `app/`); plan này dùng path thật.

---

## File Structure

**Backend (module `hocba_employees`):**
- Modify: `custom-addons/hocba_employees/models/hr_department.py` — thêm ràng buộc `@api.ondelete` chặn xóa.

**Backend (module `hocba_hrm`):**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — thêm helper `_dept_payload/_dept_list/_dept_create/_dept_update/_dept_archive` (cấp module, cạnh `_account_*`) + 4 routes trong class `HocBaHRM`.
- Create: `custom-addons/hocba_hrm/tests/test_department.py` — test toàn bộ helper + ràng buộc model.
- Modify: `custom-addons/hocba_hrm/tests/__init__.py` — import test mới (kiểm tra trước, có thể đã tự gom).

**Frontend (`frontend/src/`):**
- Create: `frontend/src/api/departments.js` — hàm gọi API (hbGet/hbPost).
- Create: `frontend/src/features/departments/DepartmentForm.jsx` — modal tạo/sửa.
- Create: `frontend/src/features/departments/Departments.jsx` — màn danh sách + lưu trữ.
- Modify: `frontend/src/app/Shell.jsx` — thêm nav item + PAGE_META.
- Modify: `frontend/src/app/App.jsx` — import + route view `departments`.

Build SPA → `custom-addons/hocba_hrm/static/spa/` (commit artifact theo convention).

---

## Task 1: Model — chặn xóa cứng phòng ban còn nhân viên/phòng con

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_department.py`
- Test: `custom-addons/hocba_hrm/tests/test_department.py`

- [ ] **Step 1: Viết test thất bại** (tạo file test mới với 3 case xóa + đăng ký discovery)

> **Import:** Task 1 CHƯA có `_dept_*` (định nghĩa ở Task 2–5). Vì Python import lỗi sẽ làm vỡ CẢ module test, ở Task 1 KHÔNG import `_dept_*`. Task 2 sẽ bổ sung dòng import đó.

Tạo `custom-addons/hocba_hrm/tests/test_department.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError


@tagged('post_install', '-at_install')
class TestDepartment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV A', 'department_id': self.dept.id})

    def _env(self, user):
        return self.env(user=user)

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
```

Đăng ký discovery — thêm dòng cuối `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_department
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: `test_unlink_blocked_when_has_members` và `test_unlink_blocked_when_has_children` FAIL (xóa được, không raise `UserError`). `test_unlink_ok_when_empty` PASS.

- [ ] **Step 3: Thêm ràng buộc vào model**

Sửa `custom-addons/hocba_employees/models/hr_department.py` thành:

```python
from odoo import models, fields, api
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    x_function_desc = fields.Char(
        string='Chức năng phòng ban',
        help='Mô tả ngắn chức năng nghiệp vụ của phòng ban (theo Lookup 8.4 Lark).',
    )

    @api.ondelete(at_uninstall=False)
    def _prevent_delete_with_members_or_children(self):
        """Chặn xóa cứng phòng ban còn nhân viên hoặc còn phòng con.
        Người dùng nên LƯU TRỮ (active=False) thay vì xóa — giữ lịch sử."""
        for dept in self:
            if dept.member_ids:
                raise UserError(
                    "Phòng ban '%s' còn %d nhân viên. Vui lòng chuyển nhân viên "
                    "sang phòng khác trước, hoặc lưu trữ phòng ban."
                    % (dept.name, len(dept.member_ids)))
            if dept.child_ids:
                raise UserError(
                    "Phòng ban '%s' còn phòng ban con. Vui lòng xử lý phòng con "
                    "trước, hoặc lưu trữ phòng ban." % dept.name)
```

- [ ] **Step 4: Chạy test, xác nhận 3 test xóa PASS**

Run lệnh ở Step 2. Expected: 3 test `test_unlink_*` PASS.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_department.py custom-addons/hocba_hrm/tests/test_department.py
git commit -m "feat(department): chặn xóa cứng phòng ban còn nhân viên/phòng con

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: API helper `_dept_payload` + `_dept_list` + route GET

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm helper cạnh `_account_list`, ~dòng 1391; route cạnh `api_accounts`, ~dòng 2244)
- Test: `custom-addons/hocba_hrm/tests/test_department.py`

- [ ] **Step 1: Thêm test cho list + payload**

Bổ sung vào `TestDepartment`:

```python
    # ---- _dept_list / _dept_payload (Task 2) ----
    def test_list_forbidden_for_plain(self):
        with self.assertRaises(AccessError):
            _dept_list(self._env(self.plain))

    def test_list_returns_departments_and_employees(self):
        out = _dept_list(self._env(self.hr))
        names = [d['name'] for d in out['departments']]
        self.assertIn('Phòng A', names)
        self.assertTrue(any(e['id'] == self.emp.id for e in out['employees']))

    def test_payload_employee_count(self):
        out = _dept_list(self._env(self.hr))
        row = next(d for d in out['departments'] if d['id'] == self.dept.id)
        self.assertEqual(row['employeeCount'], 1)
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
```

Thêm dòng import (sau khối `from odoo.exceptions ...` đầu file `test_department.py`):

```python
from odoo.addons.hocba_hrm.controllers.main import (
    _dept_payload, _dept_list, _dept_create, _dept_update, _dept_archive)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run lệnh test (như Task 1 Step 2). Expected: ImportError `cannot import name '_dept_list'` — vì module test giờ import `_dept_*` nhưng helper chưa có. (Tất cả test_department lỗi import → đây là trạng thái đỏ mong đợi.)

- [ ] **Step 3: Thêm helper vào `main.py`** (ngay sau `_account_list`, trước dòng `_CHECK_ERR_STATUS`)

```python
def _dept_payload(dept):
    """Một dòng phòng ban cho SPA. employeeCount đếm trực tiếp member_ids
    (chắc chắn, không phụ thuộc tên field computed của Odoo)."""
    return {
        'id': dept.id,
        'name': dept.name,
        'functionDesc': dept.x_function_desc or '',
        'managerId': dept.manager_id.id or False,
        'managerName': dept.manager_id.name or '',
        'employeeCount': len(dept.member_ids),
        'active': dept.active,
    }


def _dept_list(env, archived=False):
    """Danh sách phòng ban + danh mục NV (cho dropdown trưởng phòng). Chỉ HR.
    archived=True → gồm cả phòng đã lưu trữ (active=False)."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được xem danh sách phòng ban.')
    Dept = env['hr.department'].sudo().with_context(active_test=not archived)
    depts = Dept.search([], order='name')
    employees = env['hr.employee'].sudo().search(
        [], order='x_employee_code, name')
    return {
        'departments': [_dept_payload(d) for d in depts],
        'employees': [{'id': e.id, 'name': e.name, 'code': e.x_employee_code or ''}
                      for e in employees],
    }
```

- [ ] **Step 4: Thêm route GET** (trong class `HocBaHRM`, ngay sau `api_accounts`)

```python
    @http.route('/hocba-hrm/api/departments', auth='user', type='http',
                methods=['GET'])
    def api_departments(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        archived = kw.get('archived') in ('1', 'true', 'True')
        try:
            data = _dept_list(request.env, archived=archived)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        return request.make_json_response(data)
```

- [ ] **Step 5: Chạy test, xác nhận PASS**

Run lệnh test. Expected: 5 test mới + 3 test Task 1 PASS.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_department.py
git commit -m "feat(department): API GET danh sách phòng ban (_dept_list)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: API helper `_dept_create` + route POST

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_department.py`

- [ ] **Step 1: Thêm test create**

```python
    # ---- _dept_create (Task 3) ----
    def test_create_ok(self):
        out = _dept_create(self._env(self.hr), {
            'name': 'Phòng Mới', 'functionDesc': 'Mô tả', 'managerId': self.emp.id})
        self.assertEqual(out['name'], 'Phòng Mới')
        self.assertEqual(out['functionDesc'], 'Mô tả')
        self.assertEqual(out['managerId'], self.emp.id)
        self.assertTrue(out['active'])

    def test_create_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_create(self._env(self.hr), {'name': '   '})

    def test_create_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_create(self._env(self.plain), {'name': 'X'})
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (NameError `_dept_create`)

- [ ] **Step 3: Thêm helper** (sau `_dept_list`)

```python
def _dept_create(env, body):
    """HR/Admin tạo phòng ban mới."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được tạo phòng ban.')
    name = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('Vui lòng nhập tên phòng ban.')
    vals = {'name': name,
            'x_function_desc': (body.get('functionDesc') or '').strip()}
    manager_id = body.get('managerId')
    if manager_id:
        vals['manager_id'] = int(manager_id)
    dept = env['hr.department'].sudo().create(vals)
    return _dept_payload(dept)
```

- [ ] **Step 4: Thêm route POST** (sau `api_departments`)

```python
    @http.route('/hocba-hrm/api/department', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_department_create(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_create(request.env, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)
```

- [ ] **Step 5: Chạy test, xác nhận PASS**

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_department.py
git commit -m "feat(department): API tạo phòng ban (_dept_create)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: API helper `_dept_update` + route POST

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_department.py`

- [ ] **Step 1: Thêm test update**

```python
    # ---- _dept_update (Task 4) ----
    def test_update_changes_fields(self):
        out = _dept_update(self._env(self.hr), self.dept.id, {
            'name': 'Phòng A2', 'functionDesc': 'Mới', 'managerId': self.emp.id})
        self.assertEqual(out['name'], 'Phòng A2')
        self.assertEqual(out['functionDesc'], 'Mới')
        self.assertEqual(self.dept.manager_id, self.emp)

    def test_update_clears_manager(self):
        self.dept.manager_id = self.emp.id
        out = _dept_update(self._env(self.hr), self.dept.id, {
            'name': 'Phòng A', 'managerId': False})
        self.assertFalse(out['managerId'])
        self.assertFalse(self.dept.manager_id)

    def test_update_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_update(self._env(self.hr), self.dept.id, {'name': ''})

    def test_update_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_update(self._env(self.plain), self.dept.id, {'name': 'X'})
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (NameError `_dept_update`)

- [ ] **Step 3: Thêm helper** (sau `_dept_create`)

```python
def _dept_update(env, dept_id, body):
    """HR/Admin sửa tên / chức năng / trưởng phòng. managerId rỗng → gỡ trưởng phòng."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được sửa phòng ban.')
    dept = env['hr.department'].sudo().with_context(
        active_test=False).browse(dept_id)
    if not dept.exists():
        raise ValidationError('Không tìm thấy phòng ban.')
    name = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('Vui lòng nhập tên phòng ban.')
    manager_id = body.get('managerId')
    dept.write({
        'name': name,
        'x_function_desc': (body.get('functionDesc') or '').strip(),
        'manager_id': int(manager_id) if manager_id else False,
    })
    return _dept_payload(dept)
```

- [ ] **Step 4: Thêm route POST** (sau `api_department_create`)

```python
    @http.route('/hocba-hrm/api/department/<int:dept_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_department_update(self, dept_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_update(request.env, dept_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)
```

- [ ] **Step 5: Chạy test, xác nhận PASS**

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_department.py
git commit -m "feat(department): API sửa phòng ban (_dept_update)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: API helper `_dept_archive` + route POST

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_department.py`

> **Quyết định thiết kế:** Nút "Lưu trữ" trên SPA luôn gọi archive (active=False) — đây là đường an toàn thay cho xóa cứng. Ràng buộc model (Task 1) mới là lớp chặn xóa cứng + báo "chuyển nhân viên trước". `_dept_archive` chỉ toggle `active`, không chặn theo nhân viên (để HR có thể ẩn phòng không dùng).

- [ ] **Step 1: Thêm test archive**

```python
    # ---- _dept_archive (Task 5) ----
    def test_archive_sets_inactive(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        out = _dept_archive(self._env(self.hr), empty.id, {'active': False})
        self.assertFalse(out['active'])
        self.assertFalse(empty.active)

    def test_archive_restore(self):
        self.dept.active = False
        out = _dept_archive(self._env(self.hr), self.dept.id, {'active': True})
        self.assertTrue(out['active'])
        self.assertTrue(self.dept.active)

    def test_archive_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_archive(self._env(self.plain), self.dept.id, {'active': False})
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (NameError `_dept_archive`)

- [ ] **Step 3: Thêm helper** (sau `_dept_update`)

```python
def _dept_archive(env, dept_id, body):
    """HR/Admin lưu trữ (active=False) / khôi phục (active=True) phòng ban.
    Đây là đường thay cho xóa cứng — xóa cứng bị chặn bởi ràng buộc model."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được lưu trữ phòng ban.')
    dept = env['hr.department'].sudo().with_context(
        active_test=False).browse(dept_id)
    if not dept.exists():
        raise ValidationError('Không tìm thấy phòng ban.')
    dept.write({'active': bool(body.get('active'))})
    return _dept_payload(dept)
```

- [ ] **Step 4: Thêm route POST** (sau `api_department_update`)

```python
    @http.route('/hocba-hrm/api/department/<int:dept_id>/archive', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_department_archive(self, dept_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_archive(request.env, dept_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)
```

- [ ] **Step 5: Chạy test, xác nhận TOÀN BỘ test_department PASS**

Run lệnh test. Expected: `0 failed, 0 error(s)`, tất cả test `TestDepartment` xanh.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_department.py
git commit -m "feat(department): API lưu trữ/khôi phục phòng ban (_dept_archive)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Frontend — API module `departments.js`

**Files:**
- Create: `frontend/src/api/departments.js`

- [ ] **Step 1: Tạo file**

```javascript
/* API domain Phòng ban (chỉ HR/Admin) — Owner: Tân.
   Spec: docs/superpowers/specs/2026-06-22-department-management-design.md */
import { hbGet, hbPost } from './client';

export const fetchDepartments = (archived = false) =>
  hbGet(`/hocba-hrm/api/departments${archived ? '?archived=1' : ''}`);
export const createDepartment = (payload) =>
  hbPost('/hocba-hrm/api/department', payload);
export const updateDepartment = (id, payload) =>
  hbPost(`/hocba-hrm/api/department/${id}`, payload);
export const archiveDepartment = (id, active) =>
  hbPost(`/hocba-hrm/api/department/${id}/archive`, { active });
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/departments.js
git commit -m "feat(department): FE api module departments.js

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Frontend — modal `DepartmentForm.jsx`

**Files:**
- Create: `frontend/src/features/departments/DepartmentForm.jsx`

- [ ] **Step 1: Tạo modal tạo/sửa** (mô phỏng `features/employees/AccountForm.jsx`)

```javascript
/* ============================================================
   Form tạo / sửa phòng ban — chỉ HR/Admin. Owner: Tân.
   mode='create' | 'edit'. employees = danh mục NV cho dropdown trưởng phòng.
   onDone(deptPayload) nhận phòng ban đã lưu.
   ============================================================ */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createDepartment, updateDepartment } from '../../api/departments';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

export default function DepartmentForm({ dept, employees = [], onClose, onDone }) {
  const edit = !!dept;
  const [name, setName] = useState(dept ? dept.name : '');
  const [functionDesc, setFunctionDesc] = useState(dept ? dept.functionDesc : '');
  const [managerId, setManagerId] = useState(dept && dept.managerId ? String(dept.managerId) : '');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setErr(null); setBusy(true);
    try {
      const payload = { name, functionDesc, managerId: managerId ? Number(managerId) : false };
      const res = edit
        ? await updateDepartment(dept.id, payload)
        : await createDepartment(payload);
      onDone(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={edit ? 'edit' : 'plus'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{edit ? 'Sửa phòng ban' : 'Thêm phòng ban'}</h2>
          {edit && <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{dept.employeeCount} nhân viên</div>}
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên phòng ban *" full>
            <input style={inp} value={name} onChange={(e) => setName(e.target.value)}
              placeholder="VD: Marketing" autoComplete="off" />
          </Field>
          <Field label="Chức năng phòng ban" full>
            <input style={inp} value={functionDesc} onChange={(e) => setFunctionDesc(e.target.value)}
              placeholder="Mô tả ngắn nghiệp vụ" autoComplete="off" />
          </Field>
          <Field label="Trưởng phòng" full>
            <select style={inp} value={managerId} onChange={(e) => setManagerId(e.target.value)}>
              <option value="">— Không gán —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>{e.name}{e.code ? ` (${e.code})` : ''}</option>
              ))}
            </select>
          </Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : (edit ? 'Lưu' : 'Thêm phòng ban')}
        </button>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/departments/DepartmentForm.jsx
git commit -m "feat(department): FE modal tạo/sửa phòng ban

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Frontend — màn danh sách `Departments.jsx`

**Files:**
- Create: `frontend/src/features/departments/Departments.jsx`

- [ ] **Step 1: Tạo màn danh sách** (mô phỏng `features/accounts/Accounts.jsx`)

```javascript
/* ============================================================
   Trang quản lý Phòng ban (HR/Admin) — danh sách + tạo/sửa + lưu trữ.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchDepartments, archiveDepartment } from '../../api/departments';
import DepartmentForm from './DepartmentForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

export default function Departments({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [form, setForm] = useState(null); // { dept } | { dept: null } | null

  const load = () => {
    setErr(null); setData(null);
    fetchDepartments(showArchived).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [showArchived]); // eslint-disable-line react-hooks/exhaustive-deps

  const onArchive = async (d) => {
    const next = !d.active;
    if (next === false && d.employeeCount > 0
        && !window.confirm(`Phòng "${d.name}" còn ${d.employeeCount} nhân viên. Vẫn lưu trữ?`)) return;
    try {
      await archiveDepartment(d.id, next);
      load();
    } catch (e) { window.alert(e.message); }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phòng ban…" />;

  const { departments, employees } = data;
  const q = search.trim().toLowerCase();
  const rows = departments.filter((d) => !q
    || d.name.toLowerCase().includes(q)
    || (d.functionDesc || '').toLowerCase().includes(q)
    || (d.managerName || '').toLowerCase().includes(q));

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Phòng ban</h1>
          <p>{departments.length} phòng ban</p>
        </div>
        <button className="btn btn-primary" onClick={() => setForm({ dept: null })}>
          <Icon name="plus" size={16} />Thêm phòng ban
        </button>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Danh sách phòng ban</h3>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, cursor: 'pointer' }}>
            <input type="checkbox" checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)} />
            Hiện phòng đã lưu trữ
          </label>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Phòng ban</th><th>Chức năng</th><th>Trưởng phòng</th>
              <th>Số NV</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map((d) => (
                <tr key={d.id}>
                  <td><div className="nm">{d.name}</div></td>
                  <td className="muted">{d.functionDesc || '—'}</td>
                  <td>{d.managerName || '—'}</td>
                  <td className="mono">{d.employeeCount}</td>
                  <td><Badge kind={d.active ? 'green' : 'gray'} dot>{d.active ? 'Hoạt động' : 'Lưu trữ'}</Badge></td>
                  <td style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => setForm({ dept: d })}>
                      <Icon name="edit" size={14} />Sửa</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onArchive(d)}>
                      <Icon name={d.active ? 'trash' : 'rotateCcw'} size={14} />
                      {d.active ? 'Lưu trữ' : 'Khôi phục'}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có phòng ban.</EmptyState>}
      </div>

      {form && (
        <DepartmentForm dept={form.dept} employees={employees}
          onClose={() => setForm(null)}
          onDone={() => { setForm(null); load(); }} />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/departments/Departments.jsx
git commit -m "feat(department): FE màn danh sách phòng ban + lưu trữ

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Frontend — đăng ký nav + router

**Files:**
- Modify: `frontend/src/app/Shell.jsx` (NAV ~dòng 20, PAGE_META ~dòng 68)
- Modify: `frontend/src/app/App.jsx` (import + route ~dòng 50)

- [ ] **Step 1: Thêm nav item vào `Shell.jsx`**

Trong mảng `NAV`, nhóm "Quản lý nhân sự", thêm dòng ngay sau item `accounts` (dòng 20):

```javascript
    { id: 'accounts', label: 'Tài khoản', icon: 'idcard', need: 'hr' },
    { id: 'departments', label: 'Phòng ban', icon: 'building', need: 'hr' },
```

- [ ] **Step 2: Thêm PAGE_META** (trong object `PAGE_META`, sau dòng `accounts`):

```javascript
  accounts: { t: 'Tài khoản', c: 'Quản lý nhân sự / Tài khoản' },
  departments: { t: 'Phòng ban', c: 'Quản lý nhân sự / Phòng ban' },
```

- [ ] **Step 3: Đăng ký route trong `App.jsx`**

Thêm import (sau dòng import `Accounts`):

```javascript
import Accounts from '../features/accounts/Accounts';
import Departments from '../features/departments/Departments';
```

Thêm dòng render (sau dòng `accounts`):

```javascript
        {view === 'accounts' && canManage && me.isHrUser && <Accounts search={search} />}
        {view === 'departments' && canManage && me.isHrUser && <Departments search={search} />}
```

- [ ] **Step 4: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 5: Commit (gồm cả artifact build)**

```bash
git add frontend/src/app/Shell.jsx frontend/src/app/App.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(department): đăng ký nav + route màn Phòng ban; build SPA

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Verify end-to-end trên preview

**Files:** (không sửa code — chỉ kiểm thử thủ công qua preview)

- [ ] **Step 1: Khởi động preview** (theo CLAUDE.md: TCP proxy 8169 → `[::1]:8069`)

Dùng `preview_start`. Nếu Odoo local chưa chạy, khởi động stack local + upgrade module:
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```
(Module đã được `-u hocba_hrm,hocba_employees` qua các lần chạy test ở trên.)

- [ ] **Step 2: Đăng nhập HR và vào màn Phòng ban**

Vào `/hocba-hrm`, đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026`. Xác nhận nav có "Phòng ban", mở ra thấy 6 phòng ban seed.

- [ ] **Step 3: Kiểm tra CRUD**

Tạo phòng mới → thấy trong danh sách. Sửa tên/trưởng phòng → cập nhật. Lưu trữ phòng rỗng → biến mất (bật "Hiện phòng đã lưu trữ" thấy lại) → Khôi phục. Thử lưu trữ phòng còn NV → hiện confirm.

- [ ] **Step 4: Kiểm tra phân quyền**

Đăng nhập `test_employee@hocba.vn` → KHÔNG thấy nav "Phòng ban". (Tùy chọn) gọi trực tiếp `GET /hocba-hrm/api/departments` → 403.

- [ ] **Step 5: Chụp màn hình bằng chứng**

Dùng `preview_screenshot` cho màn danh sách phòng ban (vai trò HR).

---

## Hoàn tất

- [ ] Chạy lại toàn bộ test backend, xác nhận `0 failed, 0 error(s) of N tests` (N > 0).
- [ ] `superpowers:requesting-code-review` → xử lý feedback.
- [ ] `superpowers:verification-before-completion`.
- [ ] `superpowers:finishing-a-development-branch` — merge `feature/department-management` về `main` (fast-forward khi đã chứa `origin/main`).
- [ ] Nếu có seed/đổi DB → cập nhật `docs/DB_TEST_DATA.md`. (Tính năng này không seed dữ liệu mới nên thường bỏ qua.)
