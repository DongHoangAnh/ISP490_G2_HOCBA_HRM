# Tài khoản vai trò trưởng phòng (`x_is_role_account`) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tách "tài khoản vai trò trưởng phòng" khỏi hồ sơ nhân sự thật, để nó không còn lọt vào Nhận việc, danh sách Nhân viên và thống kê.

**Architecture:** Thêm cờ boolean `x_is_role_account` trên `hr.employee`. `_dept_new_manager` bật cờ khi tạo tài khoản quản lý. Lọc tại `_emp_scope_domain` — chỗ nghẽn duy nhất mà ~15 điểm liệt kê NV trong `hocba_hrm` cùng gọi. Màn Tài khoản cố tình **không** lọc. Migration gỡ `manager_id` của mọi phòng ban.

**Tech Stack:** Odoo 19 (Python), `custom-addons/hocba_employees` + `custom-addons/hocba_hrm`, test bằng `odoo --test-enable --test-tags`. Không đụng frontend.

**Spec:** [2026-08-27-tai-khoan-vai-tro-truong-phong-design.md](../specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md)

---

## Bối cảnh cho người thực thi

**Đọc trước khi bắt đầu:**

- `CLAUDE.md` ở gốc repo — gotcha Odoo 19 và quy trình test.
- Quyền "trưởng phòng" của cả hệ suy ra từ `hr.department.manager_id`, **không** từ group. Đó là lý do tài khoản quản lý buộc phải có một bản ghi `hr.employee`.
- `_managed_department_ids` (main.py:1591) chỉ `search` trên `hr.department`. Đã kiểm chứng: lọc `hr.employee` **không** làm tài khoản vai trò mất quyền.

**Lệnh test (chạy từ gốc repo, Git Bash):**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm:TestRoleAccount --stop-after-init --log-level=test
```

`MSYS_NO_PATHCONV=1` là **bắt buộc** — thiếu nó thì chạy 0 test mà vẫn báo OK. Kết quả cần thấy `0 failed, 0 error(s) of N tests` với **N > 0**.

Nếu `docker compose` báo lỗi bind cổng 5432: máy có Postgres native đang giữ cổng đó. Tắt nó, hoặc thêm `-f <override>.yml` với `db.ports = ["5434:5432"]`.

**Gotcha BR-010:** NV `official` trong test PHẢI có `identification_id` đúng 12 chữ số, mỗi NV một giá trị khác nhau, không thì `ValidationError` ngay `setUp`.

---

## File Structure

| File | Trách nhiệm | Trạng thái |
|---|---|---|
| `custom-addons/hocba_employees/models/hr_employee.py` | Định nghĩa cờ; `create()` bỏ qua mốc "Nhận việc" và gán quy trình cho tài khoản vai trò | Sửa |
| `custom-addons/hocba_employees/__manifest__.py` | Version `19.0.6.0.0` → `19.0.7.0.0` — **bump ở Task 6**, cùng commit với migration | Sửa |
| `custom-addons/hocba_employees/migrations/19.0.7.0.0/post-migrate.py` | Gỡ `manager_id` của mọi phòng ban | Tạo |
| `custom-addons/hocba_hrm/controllers/main.py` | `_dept_new_manager` bật cờ; `_emp_scope_domain` lọc; `_role_payload` trả `hasEmployee=False` | Sửa |
| `custom-addons/hocba_hrm/tests/test_role_account.py` | Toàn bộ 8 test của tính năng | Tạo |
| `docs/DB_TEST_DATA.md` | Bảng tài khoản + nhật ký sau khi gỡ `manager_id` | Sửa |

**Không đụng frontend.** `Shell.jsx` đã có sẵn `isRoleAccount(me)` ẩn "Hồ sơ của tôi" cho mọi tài khoản `isManager` — tài khoản vai trò là trưởng phòng nên đã bị ẩn từ trước. Thay đổi backend ở Task 5 chỉ để `hasEmployee` nói đúng sự thật.

---

### Task 1: Cờ `x_is_role_account` trên `hr.employee`

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py` (thêm field cạnh `x_employee_code`, dòng ~26-31)
- Test: `custom-addons/hocba_hrm/tests/test_role_account.py` (tạo mới)

- [ ] **Step 1: Viết test đỏ**

Tạo `custom-addons/hocba_hrm/tests/test_role_account.py`:

```python
"""Tài khoản vai trò trưởng phòng — không phải hồ sơ nhân sự.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Tài khoản tạo từ form "Thêm phòng ban" là tài khoản QUẢN LÝ (tài khoản thứ hai
của một người đã có hồ sơ nhân viên riêng). Nó phải biến mất khỏi Nhận việc,
danh sách Nhân viên và thống kê, nhưng VẪN giữ nguyên quyền duyệt phòng mình và
VẪN hiện ở màn Tài khoản để HR đổi mật khẩu / khoá.

DB test dùng chung nên mọi assert so theo bản ghi do test tự tạo, không so số
tuyệt đối.
"""
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _dept_create, _emp_scope_domain, _account_list)


@tagged('post_install', '-at_install')
class TestRoleAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        gu = self.env.ref('base.group_user').id
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Role', 'login': 'hrm_role_acc',
            'group_ids': [(6, 0, [gu,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def _mgr_block(self, login='tp_role_1', name='TP Vai Tro'):
        return {'name': name, 'login': login,
                'password': 'Hocba@2026', 'password_confirm': 'Hocba@2026'}

    def _create_dept(self, name='Phong Vai Tro', login='tp_role_1'):
        """Tạo phòng ban kèm tài khoản vai trò, trả về (dept, emp)."""
        env = self.env(user=self.hrm)
        _dept_create(env, {'name': name, 'manager': self._mgr_block(login=login)})
        dept = env['hr.department'].sudo().search(
            [('name', '=', name)], limit=1)
        return dept, dept.manager_id

    # ---- Task 1: cờ trên model ----
    def test_create_khong_ghi_moc_nhan_viec(self):
        """Tài khoản vai trò không sinh mốc thăng tiến 'join'."""
        emp = self.env['hr.employee'].create({
            'name': 'Chi La Tai Khoan', 'x_is_role_account': True})
        self.assertTrue(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertFalse(
            logs, 'Tài khoản vai trò không được có mốc "Nhận việc".')

    def test_nv_thuong_van_ghi_moc_nhan_viec(self):
        """Không làm hỏng đường đi của nhân viên thật."""
        emp = self.env['hr.employee'].create({'name': 'NV That Su'})
        self.assertFalse(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertTrue(logs, 'NV thật vẫn phải có mốc "Nhận việc".')
```

Model lịch sử thăng tiến là `hr.promotion.history`, khoá ngoại `employee_id` — đã
kiểm chứng khi soạn plan, không phải đoán.

- [ ] **Step 2: Chạy test, xác nhận ĐỎ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm:TestRoleAccount --stop-after-init --log-level=test
```

Kỳ vọng: FAIL với `Invalid field 'x_is_role_account' on model 'hr.employee'`.

- [ ] **Step 3: Thêm field**

Trong `custom-addons/hocba_employees/models/hr_employee.py`, ngay **sau** khối `x_employee_code` (kết thúc dòng ~31) và **trước** comment `# Trục 1 — Hình thức làm việc`:

```python
    # Tài khoản vai trò quản lý (trưởng phòng tạo từ form "Thêm phòng ban").
    # Bản ghi hr.employee tồn tại chỉ vì hr.department.manager_id đòi hỏi, chứ
    # đây KHÔNG phải hồ sơ nhân sự — spec 2026-08-27.
    x_is_role_account = fields.Boolean(
        string='Tài khoản vai trò',
        default=False,
        copy=False,
        index=True,
        help='Tài khoản quản lý (trưởng phòng) — không phải hồ sơ nhân sự. '
             'Không tham gia Nhận việc, danh sách nhân viên, thống kê.',
    )
```

- [ ] **Step 4: Bỏ mốc "Nhận việc" và gán quy trình cho tài khoản vai trò**

Trong cùng file, thay toàn bộ thân `create()` (dòng ~507-521) bằng:

```python
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_employee_code'):
                vals['x_employee_code'] = self.env['ir.sequence'].next_by_code(
                    'hocba.employee.code') or '/'
        employees = super().create(vals_list)
        # Tài khoản vai trò không phải hồ sơ nhân sự: không có "nhận việc" để
        # ghi mốc, không có quy trình onboarding để gán (spec 2026-08-27).
        real = employees.filtered(lambda e: not e.x_is_role_account)
        # Snapshot "nhận việc" cho lịch sử thăng tiến (khách họp #2)
        if not self.env.context.get('hocba_no_join_log'):
            today = fields.Date.context_today(self)
            for emp in real:
                emp._hocba_log_promotion('join', today, _('Nhận việc'))
        # NV thử việc có ngày bắt đầu → gán quy trình nhận việc bước động
        real._hocba_maybe_assign_onboarding()
        return employees
```

**KHÔNG nâng version module ở task này.** Bump version phải đi CÙNG commit với migration ở Task 6, nếu không: mỗi lần chạy test đều `-u hocba_employees` → DB ghi `latest_version = 19.0.7.0.0` → tới Task 6 Odoo thấy version không đổi và **bỏ qua post-migrate**. Đây đúng loại "migration vá trượt" dự án đã dính một lần ở `19.0.4.0.0`.

- [ ] **Step 5: Chạy test, xác nhận XANH**

Lệnh như Step 2. Kỳ vọng: `0 failed, 0 error(s) of 2 tests`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py custom-addons/hocba_hrm/tests/test_role_account.py
git commit -m "feat(employees): co x_is_role_account, bo moc Nhan viec cho tai khoan vai tro"
```

---

### Task 2: `_dept_new_manager` bật cờ

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — `_dept_new_manager`, khối `emp_vals` (~dòng 2467-2473)
- Test: `custom-addons/hocba_hrm/tests/test_role_account.py`

- [ ] **Step 1: Viết test đỏ**

Thêm vào cuối class `TestRoleAccount`:

```python
    # ---- Task 2: form phòng ban bật cờ ----
    def test_tao_phong_ban_sinh_tai_khoan_vai_tro(self):
        dept, emp = self._create_dept(login='tp_role_2')
        self.assertTrue(emp, 'Phòng ban mới phải có trưởng phòng.')
        self.assertTrue(
            emp.x_is_role_account,
            'Trưởng phòng tạo từ form phòng ban phải là tài khoản vai trò.')

    def test_tai_khoan_vai_tro_khong_o_trang_thai_thu_viec(self):
        _dept, emp = self._create_dept(name='Phong KTT', login='tp_role_3')
        self.assertFalse(
            emp.x_employment_status,
            'Tài khoản vai trò không có tình trạng làm việc — nó không đi làm.')
```

- [ ] **Step 2: Chạy test, xác nhận ĐỎ**

Lệnh như Task 1 Step 2. Kỳ vọng: FAIL — `x_is_role_account` là `False` và `x_employment_status` là `'probation'`.

- [ ] **Step 3: Sửa `_dept_new_manager`**

Thay khối `emp_vals` hiện tại:

```python
    emp_vals = {
        'name': name,
        'department_id': dept.id,
        'work_email': (m.get('email') or '').strip() or False,
        'work_phone': (m.get('phone') or '').strip() or False,
    }
```

bằng:

```python
    emp_vals = {
        'name': name,
        'department_id': dept.id,
        'work_email': (m.get('email') or '').strip() or False,
        'work_phone': (m.get('phone') or '').strip() or False,
        # Tài khoản QUẢN LÝ, không phải hồ sơ nhân sự (spec 2026-08-27). Phải
        # ghi rõ x_employment_status=False, nếu không nó rơi vào default
        # 'probation' của field và lọt thẳng vào hàng đợi Nhận việc.
        'x_is_role_account': True,
        'x_employment_status': False,
    }
```

- [ ] **Step 4: Chạy test, xác nhận XANH**

Lệnh như Task 1 Step 2. Kỳ vọng: `0 failed, 0 error(s) of 4 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_role_account.py
git commit -m "feat(departments): tai khoan truong phong duoc danh dau la tai khoan vai tro"
```

---

### Task 3: Lọc khỏi danh sách NV, Nhận việc, thống kê

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:1607-1620` (`_emp_scope_domain`)
- Test: `custom-addons/hocba_hrm/tests/test_role_account.py`

- [ ] **Step 1: Viết test đỏ**

Thêm vào cuối class:

```python
    # ---- Task 3: biến mất khỏi các màn nhân sự ----
    def test_khong_nam_trong_danh_sach_nhan_vien(self):
        _dept, emp = self._create_dept(name='Phong DS', login='tp_role_4')
        env = self.env(user=self.hrm)
        found = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertNotIn(
            emp, found, 'Tài khoản vai trò không được nằm trong danh sách NV.')

    def test_khong_nam_trong_hang_doi_nhan_viec(self):
        """api_onboarding lọc probation + _emp_scope_domain."""
        _dept, emp = self._create_dept(name='Phong NV', login='tp_role_5')
        env = self.env(user=self.hrm)
        queue = env['hr.employee'].sudo().search(
            [('x_employment_status', '=', 'probation')]
            + _emp_scope_domain(env))
        self.assertNotIn(
            emp, queue, 'Tài khoản vai trò không được vào hàng đợi Nhận việc.')

    def test_nv_that_van_nam_trong_danh_sach(self):
        """Bộ lọc không được vơ đũa cả nắm."""
        env = self.env(user=self.hrm)
        that = env['hr.employee'].sudo().create({'name': 'NV That Trong DS'})
        found = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertIn(that, found)

    def test_tai_khoan_vai_tro_van_duyet_duoc_phong_minh(self):
        """Quyền đến từ _managed_department_ids (search trên hr.department),
        không từ việc bản thân nằm trong danh sách NV."""
        dept, emp = self._create_dept(name='Phong Quyen', login='tp_role_6')
        nv = self.env['hr.employee'].sudo().create({
            'name': 'NV Duoi Quyen', 'department_id': dept.id})
        env = self.env(user=emp.user_id)
        thay_duoc = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertIn(
            nv, thay_duoc,
            'Tài khoản vai trò phải vẫn thấy NV phòng mình.')
```

- [ ] **Step 2: Chạy test, xác nhận ĐỎ**

Lệnh như Task 1 Step 2. Kỳ vọng: 3 test đầu FAIL (tài khoản vai trò vẫn nằm trong kết quả), test cuối PASS sẵn.

- [ ] **Step 3: Lọc trong `_emp_scope_domain`**

Thay toàn bộ hàm:

```python
def _emp_scope_domain(env):
    """Domain giới hạn NV theo vai trò: HR/Admin=tất cả; Giáo vụ=giáo viên;
    Trưởng phòng=phòng mình; còn lại=rỗng (id=0).

    Tài khoản vai trò (x_is_role_account) bị loại ở MỌI nhánh — nó là tài khoản
    quản lý, không phải hồ sơ nhân sự (spec 2026-08-27). Điều này KHÔNG làm nó
    mất quyền: quyền suy ra từ _managed_department_ids, hàm đó chỉ search trên
    hr.department.
    """
    user = env.user
    base = [('x_is_role_account', '=', False)]
    if (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager')):
        return base
    if user.has_group('hocba_employees.group_hocba_giaovu'):
        return base + [('x_employee_type_id.code', '=', 'teacher')]
    dept_ids = _managed_department_ids(env, user.employee_id)
    if dept_ids:
        return base + [('department_id', 'in', dept_ids)]
    return [('id', '=', 0)]
```

**Vì sao nhánh cuối giữ nguyên `[('id', '=', 0)]`:** đó là domain "không thấy gì cả", thêm điều kiện nữa là thừa.

**Cạm bẫy đã kiểm chứng:** khoảng 5 điểm gọi dịch domain này sang tiền tố `employee_id.` bằng vòng lặp `for field, op, val in _emp_scope_domain(env)` với nhánh `if field == 'id'` (main.py:411, 487, 578, 1310, 1345). Tuple mới sinh ra `('employee_id.x_is_role_account', '=', False)` — hợp lệ và đúng ý. Không cần sửa các điểm đó.

- [ ] **Step 4: Chạy test, xác nhận XANH**

Lệnh như Task 1 Step 2. Kỳ vọng: `0 failed, 0 error(s) of 8 tests`.

- [ ] **Step 5: Chạy TOÀN BỘ test hai module để bắt hồi quy**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm,/hocba_employees --stop-after-init --log-level=test
```

Kỳ vọng: `0 failed, 0 error(s)`. Đây là bước dễ vỡ nhất của cả plan — `_emp_scope_domain` dùng chung ~15 chỗ. Nếu có test đỏ, đọc kỹ: nhiều khả năng một fixture cũ tạo NV rồi gán làm `manager_id` và nay bị lọc mất.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_role_account.py
git commit -m "feat(employees): loai tai khoan vai tro khoi danh sach NV va Nhan viec"
```

---

### Task 4: Màn Tài khoản KHÔNG bị lọc (test chốt chặn)

Task này **không sửa code** — nó khoá hành vi cố ý để lần refactor sau không vô tình lọc mất.

**Files:**
- Test: `custom-addons/hocba_hrm/tests/test_role_account.py`

- [ ] **Step 1: Viết test**

```python
    # ---- Task 4: màn Tài khoản cố tình KHÔNG lọc ----
    def test_van_hien_o_man_tai_khoan(self):
        """Đây là chỗ duy nhất HR đổi mật khẩu / khoá tài khoản vai trò.
        Lọc nó ở đây là biến tài khoản thành vô hình, không quản được."""
        _dept, emp = self._create_dept(name='Phong TK', login='tp_role_7')
        data = _account_list(self.env(user=self.hrm))
        ids = [r['employeeId'] for r in data['accounts']]
        self.assertIn(
            emp.id, ids,
            'Tài khoản vai trò phải hiện ở màn Tài khoản để HR quản lý.')
```

`_account_list` trả về `{'accounts': rows, 'departments': depts}` — đã kiểm chứng
khi soạn plan.

- [ ] **Step 2: Chạy test, xác nhận XANH ngay**

Lệnh như Task 1 Step 2. Kỳ vọng: `0 failed, 0 error(s) of 9 tests`. Test này xanh ngay từ đầu là **đúng** — nó là chốt chặn hồi quy, không phải TDD đỏ→xanh.

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/tests/test_role_account.py
git commit -m "test(accounts): chot chan man Tai khoan van liet ke tai khoan vai tro"
```

---

### Task 5: `hasEmployee = False` cho tài khoản vai trò

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — `_role_payload` (~dòng 4871-4872) và `api_me` (~dòng 4829-4831)
- Test: `custom-addons/hocba_hrm/tests/test_role_account.py`

**Bối cảnh:** `Shell.jsx` đã ẩn "Hồ sơ của tôi" cho mọi `isManager`, nên UI vốn đã đúng. Task này làm backend nói đúng sự thật, và làm `Attendance.jsx` (dùng `hasEmployee`) hiển thị đúng nhánh quản lý.

- [ ] **Step 1: Viết test đỏ**

`_role_payload` đọc `request`, thứ chỉ tồn tại trong ngữ cảnh HTTP, nên test khoá ở
mức helper thuần — chính điều kiện mà `_role_payload` và `api_me` sẽ gọi. Hành vi
HTTP do bước kiểm chứng thủ công ở Task 7 phủ.

```python
    # ---- Task 5: không có "Hồ sơ của tôi" ----
    def test_dieu_kien_an_ho_so_ca_nhan(self):
        """hasEmployee phải False cho tài khoản vai trò. Test ở mức điều kiện
        vì _role_payload cần request; hành vi HTTP do test thủ công phủ."""
        from odoo.addons.hocba_hrm.controllers.main import _has_self_profile
        _dept, emp = self._create_dept(name='Phong Me', login='tp_role_8')
        self.assertFalse(_has_self_profile(emp.user_id))
        nv_user = self.env['res.users'].create({
            'name': 'NV Co Ho So', 'login': 'nv_co_ho_so',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.env['hr.employee'].sudo().create({
            'name': 'NV Co Ho So', 'user_id': nv_user.id})
        self.assertTrue(_has_self_profile(nv_user))
```

- [ ] **Step 2: Chạy test, xác nhận ĐỎ**

Lệnh như Task 1 Step 2. Kỳ vọng: FAIL với `ImportError: cannot import name '_has_self_profile'`.

- [ ] **Step 3: Thêm helper**

Trong `custom-addons/hocba_hrm/controllers/main.py`, đặt ngay **sau** `_emp_in_scope` (kết thúc ~dòng 1634):

```python
def _has_self_profile(user):
    """User này có hồ sơ nhân sự của chính mình để xem không?

    Tài khoản vai trò (trưởng phòng) có gắn hr.employee, nhưng đó là bản ghi kỹ
    thuật để mang manager_id chứ không phải hồ sơ nhân sự — không có gì để bày
    ở "Hồ sơ của tôi" (spec 2026-08-27).
    """
    emp = user.employee_id
    return bool(emp) and not emp.x_is_role_account
```

- [ ] **Step 4: Dùng helper trong `_role_payload`**

Trong `_role_payload`, thay dòng:

```python
            'hasEmployee': bool(emp),
```

bằng:

```python
            'hasEmployee': _has_self_profile(user),
```

**Giữ nguyên** `'employeeId': emp.id if emp else False` — nhiều luồng quản lý ở FE dùng id này.

- [ ] **Step 5: Chặn luôn ở `api_me`**

Trong `api_me`, thay:

```python
        e = request.env.user.employee_id
        if not e:
            return request.make_json_response({'hasEmployee': False})
```

bằng:

```python
        e = request.env.user.employee_id
        if not _has_self_profile(request.env.user):
            return request.make_json_response({'hasEmployee': False})
```

- [ ] **Step 6: Chạy test, xác nhận XANH**

Lệnh như Task 1 Step 2. Kỳ vọng: `0 failed, 0 error(s) of 10 tests`.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_role_account.py
git commit -m "feat(me): tai khoan vai tro khong co Ho so cua toi"
```

---

### Task 6: Migration gỡ `manager_id`

**Files:**
- Create: `custom-addons/hocba_employees/migrations/19.0.7.0.0/post-migrate.py`

- [ ] **Step 1: Viết migration**

```python
"""Gỡ manager_id của mọi phòng ban — chuẩn bị cho tài khoản vai trò.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Trước bản này, trưởng phòng là một NV THẬT kiêm nhiệm, nên tài khoản cá nhân của
người đó mang luôn quyền quản lý phòng. Chốt với khách 2026-08-27: quyền quản lý
phải nằm ở một tài khoản vai trò riêng, HR tạo lại qua form "Thêm phòng ban".

CỐ TÌNH không đánh dấu x_is_role_account cho bản ghi cũ: không heuristic nào
phân biệt được "NV thật kiêm trưởng phòng" với "tài khoản vai trò" mà không có
nguy cơ bắt nhầm một NV thật rồi làm họ biến mất khỏi lương và chấm công.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("UPDATE hr_department SET manager_id = NULL "
               "WHERE manager_id IS NOT NULL")
```

**`if not version: return`** là bắt buộc — bỏ nó thì migration chạy cả khi cài mới từ đầu.

- [ ] **Step 2: Nâng version module — PHẢI cùng commit với migration**

`custom-addons/hocba_employees/__manifest__.py` dòng 3: `'version': '19.0.6.0.0'` → `'version': '19.0.7.0.0'`.

Thứ tự này là bắt buộc: Odoo chỉ chạy `migrations/19.0.7.0.0/` khi thấy version trong manifest CAO HƠN `latest_version` đang ghi trong `ir_module_module`. Bump sớm ở task trước = migration không bao giờ chạy.

- [ ] **Step 3: Chạy upgrade trên DB local**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees,hocba_hrm --addons-path=/mnt/extra-addons --stop-after-init --log-level=info
```

- [ ] **Step 4: Xác minh bằng SQL**

```bash
docker exec isp490_g2_hocba_hrm-db-1 psql -U odoo -d hocba_hrm -c "select count(*) as con_truong_phong from hr_department where manager_id is not null;"
```

Kỳ vọng: `con_truong_phong = 0`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/migrations/19.0.7.0.0/post-migrate.py custom-addons/hocba_employees/__manifest__.py
git commit -m "chore(migration): go manager_id moi phong ban (19.0.7.0.0)"
```

---

### Task 7: Cập nhật `docs/DB_TEST_DATA.md` + xác minh cuối

**Files:**
- Modify: `docs/DB_TEST_DATA.md`

- [ ] **Step 1: Đọc file để nắm khuôn bảng và nhật ký**

```bash
head -60 docs/DB_TEST_DATA.md && echo "..." && tail -30 docs/DB_TEST_DATA.md
```

- [ ] **Step 2: Cập nhật bảng tài khoản**

Sửa dòng của `test_truongphong@hocba.vn`: nó **không còn** là trưởng phòng sau migration. Ghi rõ trạng thái mới (nhân viên thường, HB.06 Trần Quốc Việt) và cách lấy lại vai trò: HR vào màn Phòng ban → Thêm phòng ban → tạo tài khoản vai trò mới.

- [ ] **Step 3: Thêm mục nhật ký**

Theo khuôn nhật ký sẵn có trong file, thêm mục ngày **2026-08-27**: đã chạy migration `19.0.7.0.0` trên DB local `hocba_hrm`, gỡ `manager_id` của toàn bộ 7 phòng ban; Neon **chưa** chạy, chờ báo nhóm.

- [ ] **Step 4: Chạy lại toàn bộ test hai module**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm,/hocba_employees --stop-after-init --log-level=test
```

Kỳ vọng: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 5: Kiểm chứng thủ công trên app**

Khởi động lại Odoo (`docker restart isp490_g2_hocba_hrm-odoo-1`), đăng nhập `test_hrmanager@hocba.vn`, rồi kiểm:

1. Màn **Phòng ban** → Thêm phòng ban → tạo tài khoản trưởng phòng mới.
2. Màn **Nhân viên**: tài khoản vừa tạo **không** xuất hiện.
3. Màn **Nhận việc**: **không** xuất hiện.
4. Màn **Tài khoản**: **có** xuất hiện, vai trò "Trưởng phòng".
5. Đăng nhập bằng tài khoản vừa tạo: **không** có mục "Hồ sơ của tôi", nhưng **thấy** NV phòng mình.

- [ ] **Step 6: Commit**

```bash
git add docs/DB_TEST_DATA.md
git commit -m "docs(db): nhat ky go manager_id + trang thai moi cua test_truongphong"
```

---

## Sau khi xong

- **Không tự đẩy lên Neon.** Migration gỡ `manager_id` sẽ làm cả nhóm mất quyền trưởng phòng. Chờ user báo nhóm và cho phép.
- Nhánh `feature/dept-bo-loai-nhan-su`; gộp về `main` bằng fast-forward khi nhánh đã chứa `origin/main`.
- Bản ghi rác cũ (`test123` → NV #33107) vẫn kẹt trong Nhận việc: migration chỉ gỡ `manager_id`, không đánh cờ. Dọn tay nếu vướng mắt.
