# Quyền TP/Giáo vụ + sửa lỗi NPT & thu hồi tài sản — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho Trưởng phòng/Giáo vụ quyền quản lý nhân sự như HR nhưng giới hạn trong phạm vi (xem lương, cấp tài sản; không quyền tài khoản/phòng ban), và sửa 2 lỗi giao diện (NPT dropdown trống, nút thu hồi tài sản bị cắt).

**Architecture:** Cờ năng lực (`canEditEmp`/`canSeeSalary`/`canEditSalary`/`canManageAccount`) tính ở server, tách khỏi nhóm Odoo thô; BE enforce phạm vi qua `_emp_in_scope` sẵn có + ghi bằng `.sudo()` sau khi kiểm quyền. FE chỉ hiển thị theo cờ.

**Tech Stack:** Odoo 19 (Python controller `hocba_hrm`), React/Vite SPA (`frontend/`), test `odoo --test-tags`.

**Spec:** `docs/superpowers/specs/2026-07-11-quyen-tpgv-va-sua-loi-design.md`

---

## File structure

| File | Trách nhiệm | Thay đổi |
|------|-------------|----------|
| `custom-addons/hocba_hrm/controllers/main.py` | API + cờ quyền | Thêm helper `_cap_*`; sửa gate + phạm vi các endpoint; lộ lương theo `canSeeSalary`; route `/api/dependent/meta` |
| `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py` | Test quyền TP/GV | **Tạo mới** |
| `custom-addons/hocba_hrm/tests/__init__.py` | Đăng ký test | Thêm import |
| `frontend/src/api/employees.js` | API client | Thêm `fetchDependentMeta` |
| `frontend/src/features/employees/DependentForm.jsx` | Form NPT | Đổi nguồn `relationship` |
| `frontend/src/features/employees/Employees.jsx` | Danh sách NV | Gate nút Thêm + cột Lương theo cờ mới |
| `frontend/src/features/employees/EmployeeDrawer.jsx` | Drawer hồ sơ | Tách `canEdit`/`canManageAccount`/`canSeeSalary`; sửa CSS ô thao tác |
| `docs/MANUAL_TEST_GUIDE.md` | Hướng dẫn test | §3 tên nút duyệt; §4/§5 kỳ vọng TP/GV |

**Quy ước test backend (mọi lệnh test):**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Cần thấy `0 failed, 0 error(s) of N tests` với N > 0.

---

## Task 1: Bug #4 — nút thao tác tài sản bị cắt (CSS)

**Files:**
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx:494`

Lỗi: ô `<td>` thao tác trong `AssetsTab` bị quy tắc `.tbl td{max-width:0;overflow:hidden}` cắt còn ~59px (nút cần 175px) → "Thu hồi" cụt, "Chuyển" mất. Cùng lớp lỗi đã fix ở `Offboarding.jsx`.

- [ ] **Step 1: Sửa style ô thao tác AssetsTab**

Tìm (dòng ~493-494):
```jsx
                {canAct && (
                  <td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>
```
Thay bằng:
```jsx
                {canAct && (
                  <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
```

- [ ] **Step 2: Sửa ô thao tác NPT (cùng lỗi tiềm ẩn)**

Tìm (dòng ~153-154):
```jsx
                    {depEditable && (
                      <td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>
```
Thay bằng:
```jsx
                    {depEditable && (
                      <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
```

- [ ] **Step 3: Sửa ô thao tác chứng chỉ (cùng lỗi tiềm ẩn)**

Trong khối `det.certs.map(...)`, tìm ô `<td>` chứa nút Sửa/Xoá chứng chỉ (khối `{editable && (<td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>`), thêm `width:'1%', overflow:'visible', maxWidth:'none'` giống Step 1. Nếu không có ô như vậy thì bỏ qua step này.

- [ ] **Step 4: Commit**
```bash
git add frontend/src/features/employees/EmployeeDrawer.jsx
git commit -m "fix(employees): nút thu hồi/chuyển tài sản bị .tbl td cắt (bug #4)"
```

Kiểm trực quan để ở Task 10 (sau khi build SPA).

---

## Task 2: Bug #3 (BE) — meta người phụ thuộc cho self-service

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm helper + route gần `api_form_meta`, ~dòng 2559)
- Test: `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

Nguyên nhân: `/api/form/meta` chặn non-HR (dòng 2563) nhưng `DependentForm` gọi nó để lấy `relationship`. NV thường → 403 → dropdown trống.

- [ ] **Step 1: Đăng ký file test**

Trong `custom-addons/hocba_hrm/tests/__init__.py` thêm dòng:
```python
from . import test_permissions_tpgv
```

- [ ] **Step 2: Viết test đỏ — helper meta khả dụng cho NV thường**

Tạo `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py`:
```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.hocba_hrm.controllers.main import (
    HocBaHRM,
    _cap_edit_emp, _cap_see_salary, _cap_edit_salary, _cap_manage_account,
    _emp_in_scope,
)


@tagged('post_install', '-at_install')
class TestDependentMeta(TransactionCase):
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
```

- [ ] **Step 3: Chạy test — xác nhận FAIL**

Chạy lệnh test chuẩn (mục trên). Kỳ vọng: FAIL `AttributeError: 'HocBaHRM' object has no attribute '_dependent_meta'` (và import `_cap_*` lỗi — sẽ có ở Task 4; tạm thời có thể lỗi import). Nếu import chặn cả file, tạm bỏ import `_cap_*`/`_emp_in_scope` khỏi dòng import ở Step 2 rồi thêm lại ở Task 4.

- [ ] **Step 4: Thêm helper + route**

Trong `controllers/main.py`, ngay TRƯỚC `def api_form_meta` (dòng ~2559, giữ nguyên `api_form_meta`), thêm:
```python
    def _dependent_meta(self, env):
        """Lựa chọn cho form Người phụ thuộc — khả dụng cho MỌI user đăng nhập
        (self-service NV tự khai NPT của mình). Chỉ trả selection, không lộ
        danh sách nhạy cảm như /api/form/meta."""
        return {'relationship': list(
            env['hr.employee.dependent']._fields['relationship']
            ._description_selection(env))}

    @http.route('/hocba-hrm/api/dependent/meta', auth='user',
                type='http', methods=['GET'])
    def api_dependent_meta(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        return request.make_json_response(self._dependent_meta(request.env))
```

- [ ] **Step 5: Chạy test — xác nhận PASS**

Chạy lệnh test. Kỳ vọng: `test_dependent_meta_available_to_plain_user` PASS.

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_permissions_tpgv.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "fix(employees): route /api/dependent/meta cho self-service NPT (bug #3 BE)"
```

---

## Task 3: Bug #3 (FE) — DependentForm dùng meta mới

**Files:**
- Modify: `frontend/src/api/employees.js`
- Modify: `frontend/src/features/employees/DependentForm.jsx`

- [ ] **Step 1: Thêm API client**

Trong `frontend/src/api/employees.js`, ngay dưới dòng `export const fetchFormMeta = () => hbGet('/hocba-hrm/api/form/meta');` thêm:
```js
export const fetchDependentMeta = () => hbGet('/hocba-hrm/api/dependent/meta');
```

- [ ] **Step 2: Đổi nguồn relationship trong DependentForm**

Trong `frontend/src/features/employees/DependentForm.jsx`:

Dòng import (dòng 6):
```js
import { fetchFormMeta, createDependent, updateDependent } from '../../api/employees';
```
→
```js
import { fetchDependentMeta, createDependent, updateDependent } from '../../api/employees';
```

Dòng useEffect (dòng 36):
```js
  useEffect(() => { fetchFormMeta().then((m) => setRels(m.relationship || [])).catch(() => {}); }, []);
```
→
```js
  useEffect(() => { fetchDependentMeta().then((m) => setRels(m.relationship || [])).catch(() => {}); }, []);
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/api/employees.js frontend/src/features/employees/DependentForm.jsx
git commit -m "fix(employees): DependentForm lấy relationship từ /dependent/meta (bug #3 FE)"
```

Kiểm trực quan để ở Task 10.

---

## Task 4: Cờ năng lực (BE) + test

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_user_can_manage`, ~dòng 1425)
- Test: `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py`

- [ ] **Step 1: Viết test đỏ — cờ đúng theo vai trò**

Thêm class vào `test_permissions_tpgv.py`:
```python
@tagged('post_install', '-at_install')
class TestCapabilityFlags(TransactionCase):
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
```

- [ ] **Step 2: Chạy test — xác nhận FAIL** (ImportError `_cap_edit_emp`).

- [ ] **Step 3: Thêm helper cờ năng lực**

Trong `controllers/main.py`, ngay SAU hàm `_user_can_manage` (kết thúc ~dòng 1425), thêm:
```python
def _cap_edit_emp(env):
    """Được tạo/sửa/xoá hồ sơ NV + hồ sơ con (trong phạm vi). = tập quản lý:
    Admin | HR | HR-Mgr | Giáo vụ | Trưởng phòng."""
    return _user_can_manage(env)


def _cap_see_salary(env):
    """Được XEM lương cơ bản: Admin | HR-Mgr | Giáo vụ | Trưởng phòng.
    (HR officer KHÔNG xem lương — giữ nguyên.)"""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager')
            or user.has_group('hocba_employees.group_hocba_giaovu')
            or _is_dept_manager(env, user.employee_id))


def _cap_edit_salary(env):
    """Được SỬA mức lương: Admin | HR-Mgr."""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager'))


def _cap_manage_account(env):
    """Quản lý tài khoản đăng nhập + phòng ban: Admin | HR | HR-Mgr."""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager'))
```

- [ ] **Step 4: Chạy test — xác nhận PASS** (4 test cờ).

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_permissions_tpgv.py
git commit -m "feat(employees): cờ năng lực _cap_edit_emp/see_salary/edit_salary/manage_account"
```

---

## Task 5: Enforce phạm vi ghi hồ sơ con (dependent/asset/cert)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

Đổi gate `is_hr` → `_cap_edit_emp + _emp_in_scope` cho dependent/asset/cert. Giữ nhánh self-service của dependent. Promotion **không đổi** (giữ `is_mgr`).

- [ ] **Step 1: Helper gate dùng chung**

Trong class `HocBaHRM`, cạnh `_emp_in_scope` (dòng ~1671), thêm:
```python
    def _can_edit_emp_record(self, e):
        """Được sửa hồ sơ (con) của NV e: có quyền quản lý VÀ e trong phạm vi."""
        return _cap_edit_emp(request.env) and self._emp_in_scope(e)
```

- [ ] **Step 2: Dependent create** — dòng ~2052-2055:
```python
        is_hr, _ = self._hr_flags()
        # Họp #2: cho chính chủ tự thêm NPT của mình (không cần HR duyệt).
        if not (is_hr or e == request.env.user.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
```
→
```python
        # Cho chính chủ tự thêm NPT của mình; hoặc người quản lý trong phạm vi.
        if not (e == request.env.user.employee_id or self._can_edit_emp_record(e)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
```
(Giữ biến `is_hr` phía dưới cho `_dep_response`; nay = quyền quản lý.)

- [ ] **Step 3: Dependent update** — dòng ~2072-2074:
```python
        is_hr, _ = self._hr_flags()
        if not (is_hr or d.employee_id == request.env.user.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
```
→
```python
        if not (d.employee_id == request.env.user.employee_id
                or self._can_edit_emp_record(d.employee_id)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
```

- [ ] **Step 4: Dependent delete** — dòng ~2089-2091: sửa y hệt Step 3 (biến `d`):
```python
        if not (d.employee_id == request.env.user.employee_id
                or self._can_edit_emp_record(d.employee_id)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
```

- [ ] **Step 5: Asset create/return/transfer** — mỗi hàm có `is_hr, _ = self._hr_flags(); if not is_hr:`. Với **asset_create** (browse `e` từ `emp_id`), đổi thành kiểm phạm vi trên `e`; với **return/transfer** (thao tác trên `asset`), kiểm trên `asset.employee_id`.

asset_create (dòng ~2111-2113): sau khi có `e` (browse emp_id), đổi:
```python
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
```
→
```python
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
```

asset_return (dòng ~2135-2137) và asset_transfer (dòng ~2159-2161): mỗi hàm browse `a`/asset từ `asset_id`. Đổi khối:
```python
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
```
thành (đặt SAU khi đã browse asset record, đổi tên biến cho khớp code hiện có):
```python
        a = request.env['hr.employee.asset'].sudo().browse(asset_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(a.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
```
> Lưu ý: đọc lại code gốc từng hàm để đặt kiểm quyền đúng chỗ (sau browse, trước write). Nếu hàm đã browse sẵn biến khác (vd `asset`), dùng lại biến đó thay vì browse lần nữa.

- [ ] **Step 6: Cert create/update/verify/delete** (dòng ~2470-2532): mỗi hàm `is_hr, _ = self._hr_flags(); if not is_hr:`. Đổi sang kiểm phạm vi trên NV chủ của chứng chỉ:
  - `api_cert_create(emp_id)`: browse `e` từ emp_id (sudo), rồi `if not self._can_edit_emp_record(e): 403`.
  - `api_cert_update/verify/delete(cert_id)`: browse cert (sudo), rồi `if not self._can_edit_emp_record(cert.employee_id): 403`.
  Giữ nguyên phần thân xử lý.

- [ ] **Step 7: Chạy toàn bộ test hocba_hrm — xác nhận không vỡ** (chưa có test riêng cho các endpoint này; đảm bảo không lỗi import/khởi tạo).

- [ ] **Step 8: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(employees): TP/GV quản lý NPT/tài sản/chứng chỉ trong phạm vi"
```

---

## Task 6: Tạo/sửa NV theo phạm vi + sudo + test

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`api_employee_create` ~2621, `api_employee_update` ~2652)
- Test: `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py`

- [ ] **Step 1: Viết test đỏ — `_emp_in_scope` cho TP/GV**

Thêm class:
```python
@tagged('post_install', '-at_install')
class TestScopeEnforcement(TransactionCase):
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
        # Giáo vụ + giáo viên / non-teacher
        self.gv_user = self.env['res.users'].create({
            'name': 'GV2', 'login': 'scope_gv', 'group_ids': [(6, 0, [
                gu, self.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        tt = self.env['hocba.employee.type'].search([('code', '=', 'teacher')], limit=1)
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
```

- [ ] **Step 2: Chạy test — xác nhận PASS ngay** (`_emp_in_scope` đã tồn tại). Đây là test hồi quy khẳng định bộ máy phạm vi đúng cho TP/GV trước khi cắm vào create/update. Nếu FAIL, dừng và xem lại `_managed_department_ids`/`_emp_scope_domain`.

- [ ] **Step 3: Sửa `api_employee_create`** (dòng ~2626-2648):

Đổi:
```python
        is_hr, is_mgr = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        if not (emp_vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập họ tên.'}, status=400)
        try:
            e = request.env['hr.employee'].create(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
```
thành:
```python
        _, is_mgr = self._hr_flags()
        if not _cap_edit_emp(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        if not (emp_vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập họ tên.'}, status=400)
        try:
            # Ghi sudo sau khi đã kiểm quyền (TP/GV không có ACL Odoo trên hr.employee).
            e = request.env['hr.employee'].sudo().create(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
            # NV mới phải nằm trong phạm vi người tạo (TP: phòng mình; GV: giáo viên).
            if not self._emp_in_scope(e):
                request.env.cr.rollback()
                return request.make_json_response(
                    {'error': 'forbidden',
                     'message': 'Ngoài phạm vi quản lý của bạn.'}, status=403)
```
> Ghi chú: `_split_form_payload` với `is_hr=_cap_edit_emp` mở tier `hr`; tier `mgr` (lương) vẫn theo `is_mgr` thật → TP/GV không set được lương.

- [ ] **Step 4: Sửa `api_employee_update`** (dòng ~2657-2669):

Đổi:
```python
        is_hr, is_mgr = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        try:
            if emp_vals:
                e.write(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
```
thành:
```python
        _, is_mgr = self._hr_flags()
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        try:
            if emp_vals:
                e.sudo().write(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
```

- [ ] **Step 5: Chạy test — xác nhận PASS** (test scope + không vỡ test cũ).

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_permissions_tpgv.py
git commit -m "feat(employees): TP/GV tạo/sửa NV trong phạm vi (sudo sau kiểm quyền)"
```

---

## Task 7: Cắm cờ vào payload + lộ lương theo canSeeSalary

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

- [ ] **Step 1: `_emp_base` — lương theo canSeeSalary**

Dòng 1714 đổi chữ ký + dòng 1738:
```python
    def _emp_base(self, e, labels, is_mgr):
```
→
```python
    def _emp_base(self, e, labels, see_salary):
```
Dòng 1738:
```python
        if is_mgr:
```
→
```python
        if see_salary:
```

- [ ] **Step 2: `api_employees` — truyền canSeeSalary + trả cờ**

Dòng ~1747:
```python
        is_hr, is_mgr = self._hr_flags()
```
→
```python
        is_hr, is_mgr = self._hr_flags()
        see_salary = _cap_see_salary(request.env)
```
Dòng ~1762:
```python
            rows.append(self._emp_base(e, labels, is_mgr))
```
→
```python
            rows.append(self._emp_base(e, labels, see_salary))
```
Khối return (dòng ~1771-1776) đổi:
```python
        return request.make_json_response({
            'isHr': is_hr,
            'isHrManager': is_mgr,
            'departments': list(deps.values()),
            'employees': rows,
        })
```
→
```python
        return request.make_json_response({
            'isHr': is_hr,
            'isHrManager': is_mgr,
            'canEditEmp': _cap_edit_emp(request.env),
            'canSeeSalary': see_salary,
            'canManageAccount': _cap_manage_account(request.env),
            'departments': list(deps.values()),
            'employees': rows,
        })
```

- [ ] **Step 3: `_employee_detail` — lương theo canSeeSalary**

Dòng 1778-1781:
```python
    def _employee_detail(self, e, labels, is_hr, is_mgr):
        """..."""
        data = self._emp_base(e, labels, is_mgr)
```
→
```python
    def _employee_detail(self, e, labels, is_hr, is_mgr, see_salary=None):
        """..."""
        if see_salary is None:
            see_salary = is_mgr
        data = self._emp_base(e, labels, see_salary)
```
Trong thân `_employee_detail`, các chỗ `if is_mgr:` dùng để chèn dòng lương/MST/BHXH/bank (dòng ~1811) và promotion wage (dòng ~1892) đổi `is_mgr` → `see_salary`.

- [ ] **Step 4: Endpoint detail truyền see_salary**

`api_employee` (GET detail, dòng ~1924-1932) và `/api/employee/<id>` GET (dòng ~1979-1981): nơi gọi `self._employee_detail(e, labels, is_hr, is_mgr)` thêm `see_salary=_cap_see_salary(request.env)`:
```python
            self._employee_detail(e, labels, is_hr, is_mgr, _cap_see_salary(request.env)))
```
Với create/update (Task 6, dòng ~2648/2680) đổi tương tự:
```python
            self._employee_detail(e.sudo(), self._labels(), is_hr, is_mgr, _cap_see_salary(request.env)))
```
`/api/me` (`_me_payload`, self-view) giữ nguyên (`is_mgr=True` → see_salary mặc định True: NV tự xem lương mình).

- [ ] **Step 5: `_role_payload` trả cờ mới** (dòng ~2846-2858): thêm 3 khoá vào dict return:
```python
            'canEditEmp': _cap_edit_emp(request.env),
            'canSeeSalary': _cap_see_salary(request.env),
            'canManageAccount': _cap_manage_account(request.env),
```

- [ ] **Step 6: Viết test lộ lương**

Thêm vào `TestScopeEnforcement` (dùng ctrl):
```python
    def test_emp_base_salary_visibility(self):
        ctrl = HocBaHRM()
        labels = ctrl._labels() if hasattr(ctrl, '_labels') else {'work_form': {}, 'status': {}, 'position': {}}
        base_mgr = ctrl._emp_base(self.in_emp, ctrl._labels(), True)
        base_no = ctrl._emp_base(self.in_emp, ctrl._labels(), False)
        self.assertIn('wage', base_mgr)
        self.assertNotIn('wage', base_no)
```
> Nếu `_labels()` cần `request` → thay bằng labels tối thiểu: `{'work_form': {}, 'status': {}, 'position': {}}` trực tiếp trong lời gọi `_emp_base`.

- [ ] **Step 7: Chạy test — PASS.** Commit:
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_permissions_tpgv.py
git commit -m "feat(employees): trả cờ canEdit/canSeeSalary/canManageAccount + lộ lương theo canSeeSalary"
```

---

## Task 8: Frontend — Employees.jsx theo cờ mới

**Files:**
- Modify: `frontend/src/features/employees/Employees.jsx`

- [ ] **Step 1: Nút Thêm nhân viên** — dòng 75:
```jsx
          {data.isHr && (
```
→
```jsx
          {data.canEditEmp && (
```

- [ ] **Step 2: Cột Lương CB (header + cell)** — dòng 118 và 140: đổi cả hai `data.isHrManager` → `data.canSeeSalary`:
```jsx
                {data.canSeeSalary && <th className="tbl-num">Lương CB</th>}
```
```jsx
                    {data.canSeeSalary && <td className="tbl-num mono" style={{ fontWeight: 600 }}>{e.wage ? hbVND(e.wage) : '—'}</td>}
```

- [ ] **Step 3: Truyền cờ xuống drawer + form** — dòng 176-184:
```jsx
      {sel && <EmployeeDrawer emp={sel}
        onClose={() => { setSel(null); if (dirtyRef.current) { dirtyRef.current = false; reloadQuiet(); } }}
        onChanged={() => { dirtyRef.current = true; }}
        isHr={data.isHr} isMgr={data.isHrManager} />}
      {creating && (
        <EmployeeForm emp={null} isMgr={data.isHrManager}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
```
→
```jsx
      {sel && <EmployeeDrawer emp={sel}
        onClose={() => { setSel(null); if (dirtyRef.current) { dirtyRef.current = false; reloadQuiet(); } }}
        onChanged={() => { dirtyRef.current = true; }}
        canEdit={data.canEditEmp} canManageAccount={data.canManageAccount}
        isMgr={data.isHrManager} canSeeSalary={data.canSeeSalary} />}
      {creating && (
        <EmployeeForm emp={null} isMgr={data.isHrManager}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
```

- [ ] **Step 4: Commit**
```bash
git add frontend/src/features/employees/Employees.jsx
git commit -m "feat(employees): Employees.jsx dùng canEditEmp/canSeeSalary/canManageAccount"
```

---

## Task 9: Frontend — EmployeeDrawer.jsx theo cờ mới

**Files:**
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx`

Drawer nhận props mới `canEdit`, `canManageAccount`, `canSeeSalary` (thay `isHr`). Self-view (`Profile.jsx`) truyền `isHr isMgr depEditable` — giữ tương thích bằng cách map.

- [ ] **Step 1: Chữ ký component chính** — tìm dòng `export default function EmployeeDrawer({ ... })` (đầu file, ~dòng 15-27). Thêm props mới với mặc định suy ra từ prop cũ để tương thích cả 2 nơi gọi:
```jsx
export default function EmployeeDrawer({ emp, onClose, onChanged,
  isHr, isMgr, canEdit = isHr, canManageAccount = isHr, canSeeSalary = isMgr }) {
```
> Nếu chữ ký hiện tại khác, giữ các prop cũ và bổ sung 3 prop mới với mặc định như trên (đọc lại đầu file để khớp).

- [ ] **Step 2: Tab Tài khoản** — dòng 38:
```jsx
    if (isHr) tabs.push(['account', 'Tài khoản']);
```
→
```jsx
    if (canManageAccount) tabs.push(['account', 'Tài khoản']);
```

- [ ] **Step 3: Nút Chỉnh sửa + các tab** — dòng ~56 và ~75-79:
```jsx
          {isHr && det && (
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
```
→
```jsx
          {canEdit && det && (
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
```
Dòng 75-79:
```jsx
        {det && tab === 'info' && <InfoTab det={det} isHr={isHr} isMgr={isMgr} editable={isHr} onUpdated={update} />}
        {det && tab === 'probation' && <ProbationTab det={det} isHr={isHr} isMgr={isMgr} onUpdated={update} />}
        {det && tab === 'assets' && <AssetsTab det={det} editable={isHr} onUpdated={update} />}
        {det && tab === 'promo' && <PromoTab det={det} isMgr={isMgr} editable={isMgr} onUpdated={update} />}
        {det && tab === 'account' && isHr && <AccountTab det={det} emp={emp} onUpdated={update} />}
```
→
```jsx
        {det && tab === 'info' && <InfoTab det={det} isHr={canEdit} isMgr={canSeeSalary} editable={canEdit} onUpdated={update} />}
        {det && tab === 'probation' && <ProbationTab det={det} isHr={canEdit} isMgr={isMgr} onUpdated={update} />}
        {det && tab === 'assets' && <AssetsTab det={det} editable={canEdit} onUpdated={update} />}
        {det && tab === 'promo' && <PromoTab det={det} isMgr={isMgr} editable={isMgr} onUpdated={update} />}
        {det && tab === 'account' && canManageAccount && <AccountTab det={det} emp={emp} onUpdated={update} />}
```
> Giải thích: `InfoTab` dùng `isMgr` để hiện dòng lương → truyền `canSeeSalary`. `editable`/`isHr` (sửa hồ sơ, NPT, chứng chỉ) → `canEdit`. `PromoTab editable={isMgr}` giữ HR-Mgr-only (thăng tiến đổi lương). `EmployeeForm` (sửa) mở qua `editing`, ô lương của nó theo `isMgr` (dòng ~83) → giữ nguyên `isMgr`.

- [ ] **Step 4: Commit**
```bash
git add frontend/src/features/employees/EmployeeDrawer.jsx
git commit -m "feat(employees): EmployeeDrawer tách canEdit/canManageAccount/canSeeSalary"
```

---

## Task 10: Build SPA + verify trực quan (preview)

**Files:** không sửa code (trừ khi phát hiện lỗi).

- [ ] **Step 1: Build SPA**
```bash
cd frontend && npm run build
```
Kỳ vọng: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 2: Verify bug #3 (self-service NPT)** — đăng nhập `test_employee@hocba.vn`, vào "Hồ sơ của tôi" → tab Thông tin → "Thêm NPT" → xác nhận dropdown **Quan hệ có 5 lựa chọn** (Vợ/Chồng, Con, Cha/Mẹ, Anh/Chị/Em, Khác) và thêm được.

- [ ] **Step 3: Verify bug #4 (thu hồi)** — đăng nhập `test_hrmanager@hocba.vn` → Nhân viên → mở Nguyễn Thị Thu Hà → tab Tài sản → xác nhận nút **"Thu hồi"** và **"Chuyển"** hiển thị đầy đủ, không bị cắt (đo `td scrollWidth <= clientWidth` hoặc ảnh chụp).

- [ ] **Step 4: Verify TP/GV** — đăng nhập `test_truongphong@hocba.vn` → Nhân viên: **có** nút "Thêm nhân viên", **thấy** cột "Lương CB", mở 1 NV trong phòng → có nút "Chỉnh sửa", tab Tài sản có "Cấp phát", **không** có tab "Tài khoản". Tương tự `test_giaovu@hocba.vn` với phạm vi giáo viên.

- [ ] **Step 5: Commit build artifacts**
```bash
git add custom-addons/hocba_hrm/static/spa
git commit -m "build(spa): rebuild sau thay đổi quyền TP/GV + fix NPT/tài sản"
```

---

## Task 11: Cập nhật hướng dẫn test

**Files:**
- Modify: `docs/MANUAL_TEST_GUIDE.md`

- [ ] **Step 1: §3 Nghỉ việc — tên nút 2 cấp**

Bổ sung/nêu rõ: đơn nghỉ việc duyệt 2 cấp — cấp 1 **Trưởng phòng/Giáo vụ** bấm nút **"Quản lý duyệt"** (đơn chuyển "Chờ HR duyệt"); cấp 2 **HR/Admin** bấm **"HR duyệt"** (chuyển "Chờ hoàn tất"); cuối cùng HR bấm **"Hoàn tất"** (lưu trữ hồ sơ + khoá đăng nhập). Nút "Từ chối" có ở cả hai cấp.

- [ ] **Step 2: §4 Trưởng phòng / §5 Giáo vụ — cập nhật kỳ vọng**

Đổi kỳ vọng: TP/GV nay **có** nút "Thêm nhân viên", **thấy** cột "Lương CB" (chỉ xem, không sửa mức lương), **sửa** hồ sơ + **cấp/thu hồi/chuyển tài sản** + quản lý NPT/chứng chỉ — tất cả **trong phạm vi** (TP: phòng mình gồm phòng con; GV: giáo viên). **Không** có tab "Tài khoản", **không** vào trang "Phòng ban". Thử ngoài phạm vi phải bị chặn.

- [ ] **Step 3: Commit**
```bash
git add docs/MANUAL_TEST_GUIDE.md
git commit -m "docs(test-guide): luồng duyệt nghỉ việc 2 cấp + quyền TP/GV mới"
```

---

## Task 12: Chạy full test backend + tái tạo kết quả

- [ ] **Step 1: Chạy full test hocba_hrm**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Kỳ vọng: `0 failed, 0 error(s) of N tests`, N tăng so với trước (thêm test permissions).

- [ ] **Step 2: Chạy lại runner test tay các case vai trò + 2 bug** (dùng harness `scratchpad/e2e` đã có; cập nhật kỳ vọng TP/GV: nay có nút Thêm, có cột Lương). Regenerate `docs/KETQUA_TEST_TAY_2026-07-11.md` + bản HTML kèm ảnh.

- [ ] **Step 3: Commit kết quả**
```bash
git add docs/KETQUA_TEST_TAY_2026-07-11.md
git commit -m "test: cập nhật kết quả test tay sau thay đổi quyền TP/GV + 2 bug"
```

---

## Task 13: Kết thúc nhánh

- [ ] Dùng skill `superpowers:finishing-a-development-branch`: review tổng, đảm bảo test xanh, rồi hợp nhất về `main` bằng fast-forward (nhánh đã chứa `origin/main`). Cập nhật memory nếu cần.

---

## Self-review (đã kiểm khi viết plan)

- **Spec coverage:** item 1 (Task 11), item 2 (Task 4-9), bug #3 (Task 2-3), bug #4 (Task 1); tài liệu + kết quả (Task 11-12). ✔
- **Type consistency:** cờ dùng nhất quán `canEditEmp`/`canSeeSalary`/`canManageAccount`; `_emp_base(e, labels, see_salary)`; `_can_edit_emp_record(e)`. ✔
- **Điểm rủi ro cần chú ý khi thực thi:** đọc lại code gốc từng endpoint asset/cert trước khi sửa (tên biến browse khác nhau); `_labels()` có thể cần request context (test dùng labels tối thiểu nếu cần); build SPA có hook tự chạy — vẫn build tay để chắc.
