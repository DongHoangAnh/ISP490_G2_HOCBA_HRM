# Field "Ngân hàng nhận lương" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm field Số tài khoản + Ngân hàng nhận lương (dropdown chuẩn hoá từ list `hb.bank.format`) vào hồ sơ nhân viên, chỉ HR Manager xem/sửa.

**Architecture:** 2 field `Char` trên `hr.employee` (`x_bank_account_no`, `x_bank_code`) với `groups='hr.group_hr_manager'` (theo đúng pattern `x_pit_code`/`x_social_insurance_no`). Tầng controller `hocba_hrm` map field theo tier `mgr`, đổ dropdown từ `hb.bank.format` qua helper `_bank_options`. SPA hiển thị ở section "Lương & bảo hiểm (Quản lý)". Lưu **mã** ngân hàng (vd `VCB`) để đồng nhất. **Không** nối vào wizard sinh file (known gap).

**Tech Stack:** Odoo 19 (Python), React 18 + Vite (SPA, no TS), Docker local Postgres cho test.

Spec: `docs/superpowers/specs/2026-06-24-employee-bank-field-design.md`

---

## File Structure

- `custom-addons/hocba_employees/models/hr_employee.py` — thêm 2 field model.
- `custom-addons/hocba_hrm/controllers/main.py` — field map, helper `_bank_options`, meta, detail prefill.
- `custom-addons/hocba_hrm/tests/test_employee_bank.py` — **mới**, toàn bộ test backend.
- `custom-addons/hocba_hrm/tests/__init__.py` — import test mới.
- `frontend/src/features/employees/EmployeeForm.jsx` — form: initForm + dropdown + input.

**Lệnh test (Docker local — chạy từ Git Bash):**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_payroll --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Cần thấy: `0 failed, 0 error(s)` với N > 0. (Bắt buộc có `hocba_payroll` để model `hb.bank.format` tồn tại cho test meta.)

---

## Task 1: Model fields trên hr.employee

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py:96-98` (chèn sau `x_social_insurance_no`)
- Test: `custom-addons/hocba_hrm/tests/test_employee_bank.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Tạo file test với test model + đăng ký test**

Tạo `custom-addons/hocba_hrm/tests/test_employee_bank.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM, _bank_options


@tagged('post_install', '-at_install')
class TestEmployeeBankField(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()

    def test_model_stores_bank_fields(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Bank', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        self.assertEqual(emp.x_bank_code, 'VCB')
        self.assertEqual(emp.x_bank_account_no, '0123456789')
```

Thêm vào cuối `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_employee_bank
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run (lệnh test ở trên).
Expected: FAIL — `Invalid field 'x_bank_code' on model 'hr.employee'`.

- [ ] **Step 3: Thêm 2 field model**

Trong `custom-addons/hocba_employees/models/hr_employee.py`, ngay sau field `x_social_insurance_no` (kết thúc ở dòng 98), trước `x_health_insurance_no`:

```python
    x_bank_account_no = fields.Char(
        string='Số tài khoản nhận lương', groups='hr.group_hr_manager',
        help='Số tài khoản nhân viên nhận lương.')
    x_bank_code = fields.Char(
        string='Ngân hàng nhận lương', groups='hr.group_hr_manager',
        help='Mã ngân hàng chuẩn hoá (vd VCB), đồng bộ với danh sách cấu hình payroll (hb.bank.format).')
```

> `groups='hr.group_hr_manager'` theo đúng pattern field nhạy cảm liền kề (`x_pit_code`, `x_social_insurance_no`) — chặn ở cả tầng ORM, không chỉ controller.

- [ ] **Step 4: Chạy test để xác nhận PASS**

Run (lệnh test ở trên).
Expected: `test_model_stores_bank_fields` PASS.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py custom-addons/hocba_hrm/tests/test_employee_bank.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(employees): field x_bank_code + x_bank_account_no (mgr)"
```

---

## Task 2: Field map + lọc theo tier (`_split_form_payload`)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:43-44` (thêm vào `EMP_FORM_FIELDS`)
- Test: `custom-addons/hocba_hrm/tests/test_employee_bank.py`

- [ ] **Step 1: Thêm 2 test (mgr ghi được / non-mgr bị bỏ)**

Thêm vào class `TestEmployeeBankField`:

```python
    def test_form_payload_mgr_includes_bank(self):
        emp_vals, _ver = self.ctrl._split_form_payload(
            {'name': 'X', 'bankCode': 'VCB', 'bankAccountNo': '0123456789'},
            is_hr=True, is_mgr=True)
        self.assertEqual(emp_vals.get('x_bank_code'), 'VCB')
        self.assertEqual(emp_vals.get('x_bank_account_no'), '0123456789')

    def test_form_payload_non_mgr_excludes_bank(self):
        emp_vals, _ver = self.ctrl._split_form_payload(
            {'name': 'X', 'bankCode': 'VCB', 'bankAccountNo': '0123456789'},
            is_hr=True, is_mgr=False)
        self.assertNotIn('x_bank_code', emp_vals)
        self.assertNotIn('x_bank_account_no', emp_vals)
```

- [ ] **Step 2: Chạy 2 test mới để xác nhận FAIL**

Run (lệnh test ở trên).
Expected: `test_form_payload_mgr_includes_bank` FAIL (`None != 'VCB'`) vì field chưa được map.

- [ ] **Step 3: Thêm 2 dòng vào EMP_FORM_FIELDS**

Trong `custom-addons/hocba_hrm/controllers/main.py`, trong dict `EMP_FORM_FIELDS`, ngay sau dòng `'si': ('x_social_insurance_no', 'mgr'),` (dòng 44):

```python
    'bankAccountNo': ('x_bank_account_no', 'mgr'),
    'bankCode': ('x_bank_code', 'mgr'),
```

- [ ] **Step 4: Chạy 2 test để xác nhận PASS**

Run (lệnh test ở trên).
Expected: cả 2 test PASS.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_employee_bank.py
git commit -m "feat(hrm): map bank fields trong form payload (tier mgr)"
```

---

## Task 3: Helper `_bank_options` + đổ vào `form/meta`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm helper module-level gần `_d`; sửa `api_form_meta:1973`)
- Test: `custom-addons/hocba_hrm/tests/test_employee_bank.py`

- [ ] **Step 1: Thêm test list ngân hàng**

Thêm vào class `TestEmployeeBankField`:

```python
    def test_bank_options_lists_active_formats(self):
        if 'hb.bank.format' not in self.env:
            self.skipTest('hocba_payroll chưa cài')
        self.env['hb.bank.format'].create({
            'name': 'Test Bank', 'code': 'TSTBANK',
            'formatter_class': 'VCBFormatter'})
        opts = _bank_options(self.env)
        self.assertIn(
            {'code': 'TSTBANK', 'name': 'Test Bank'},
            [{'code': o['code'], 'name': o['name']} for o in opts])
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run (lệnh test ở trên).
Expected: FAIL — `ImportError`/`cannot import name '_bank_options'` (hàm chưa tồn tại).

- [ ] **Step 3: Thêm helper module-level**

Trong `custom-addons/hocba_hrm/controllers/main.py`, ngay sau hàm `def _d(v):` (dòng 94 và phần thân của nó), thêm:

```python
def _bank_options(env):
    """Danh sách ngân hàng cho dropdown form NV — đọc từ cấu hình payroll
    (hb.bank.format). Trả [] nếu module payroll chưa cài (loose coupling)."""
    if 'hb.bank.format' not in env:
        return []
    return [{'code': b.code, 'name': b.name}
            for b in env['hb.bank.format'].sudo().search(
                [('active', '=', True)], order='sequence, name')]
```

> Lưu ý: kiểm tra phần thân thực tế của `_d` để chèn **sau** khi nó kết thúc, không cắt giữa hàm.

- [ ] **Step 4: Đổ `banks` vào dict trả về của `api_form_meta`**

Trong `api_form_meta` (`make_json_response({...})` bắt đầu ~dòng 1973), thêm 1 key vào dict — đặt ngay sau `'canManager': is_mgr,`:

```python
            'banks': _bank_options(env),
```

- [ ] **Step 5: Chạy test để xác nhận PASS**

Run (lệnh test ở trên).
Expected: `test_bank_options_lists_active_formats` PASS.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_employee_bank.py
git commit -m "feat(hrm): form/meta trả danh sách ngân hàng từ hb.bank.format"
```

---

## Task 4: Prefill bank trong `_employee_detail`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:1460-1464` (block `if is_mgr:`)
- Test: `custom-addons/hocba_hrm/tests/test_employee_bank.py`

- [ ] **Step 1: Thêm test prefill (mgr thấy / non-mgr không)**

Thêm vào class `TestEmployeeBankField`:

```python
    _LABELS = {'status': {}, 'work_form': {}, 'position': {},
               'asset_state': {}, 'relationship': {}}

    def test_detail_includes_bank_for_mgr(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Detail', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        data = self.ctrl._employee_detail(emp, self._LABELS, is_hr=True, is_mgr=True)
        self.assertEqual(data.get('bankCode'), 'VCB')
        self.assertEqual(data.get('bankAccountNo'), '0123456789')

    def test_detail_hides_bank_for_non_mgr(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Detail2', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        data = self.ctrl._employee_detail(emp, self._LABELS, is_hr=True, is_mgr=False)
        self.assertNotIn('bankCode', data)
        self.assertNotIn('bankAccountNo', data)
```

- [ ] **Step 2: Chạy 2 test để xác nhận FAIL**

Run (lệnh test ở trên).
Expected: `test_detail_includes_bank_for_mgr` FAIL (`None != 'VCB'`).

- [ ] **Step 3: Thêm prefill vào block is_mgr**

Trong `_employee_detail`, sửa block `if is_mgr:` (dòng 1460-1464) thành:

```python
        if is_mgr:
            data.update({
                'pit': e.x_pit_code or '',
                'si': e.x_social_insurance_no or '',
                'bankCode': e.x_bank_code or '',
                'bankAccountNo': e.x_bank_account_no or '',
            })
```

- [ ] **Step 4: Chạy 2 test để xác nhận PASS**

Run (lệnh test ở trên).
Expected: cả 2 test PASS.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_employee_bank.py
git commit -m "feat(hrm): prefill bank fields trong employee detail (mgr)"
```

---

## Task 5: SPA — dropdown ngân hàng + ô số tài khoản

**Files:**
- Modify: `frontend/src/features/employees/EmployeeForm.jsx:36-47` (initForm), `:146-155` (section mgr)

> Không có unit test FE (dự án không có test FE). Verify bằng build + preview ở Task 6.

- [ ] **Step 1: Thêm 2 key vào `initForm`**

Trong `initForm(emp)` (dòng 36-47), thêm vào object trả về (sau dòng `pit: ..., si: ..., wage: ...`):

```js
    bankAccountNo: emp?.bankAccountNo || '', bankCode: emp?.bankCode || '',
```

- [ ] **Step 2: Thêm 2 Field vào section "Lương & bảo hiểm (Quản lý)"**

Trong block `{isMgr && (<Section title="Lương & bảo hiểm (Quản lý)">...`(dòng 146-155), thêm sau Field "Số sổ BHXH (10 số)":

```jsx
                <Field label="Ngân hàng nhận lương">
                  <select style={inp} value={f.bankCode} onChange={set('bankCode')}>
                    <option value="">— Chọn —</option>
                    {(meta.banks || []).map((b) => <option key={b.code} value={b.code}>{b.name}</option>)}
                  </select></Field>
                <Field label="Số tài khoản nhận lương">
                  <input style={inp} value={f.bankAccountNo} onChange={set('bankAccountNo')} placeholder="VD: 0123456789" /></Field>
```

- [ ] **Step 3: Build SPA**

```bash
cd frontend && npm run build
```
Expected: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/employees/EmployeeForm.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(spa): form NV thêm ngân hàng nhận lương + số tài khoản (mgr)"
```

---

## Task 6: Verify toàn bộ + preview

- [ ] **Step 1: Chạy full test suite hocba_hrm**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_payroll --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests`, N > 0; 6 test mới đều chạy (test meta không bị skip vì payroll đã `-u`).

- [ ] **Step 2: Preview thủ công (tài khoản HR Manager)**

Đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026` tại `/hocba-hrm`. Mở **Nhân viên → Sửa** một NV → section "Lương & bảo hiểm (Quản lý)" phải có dropdown "Ngân hàng nhận lương" (đổ VCB/TCB từ cấu hình payroll) + ô "Số tài khoản nhận lương". Chọn + lưu → mở lại thấy giá trị prefill đúng.

- [ ] **Step 3: Preview với tài khoản HR thường (không phải Manager)**

Đăng nhập `test_giaovu@hocba.vn` hoặc 1 HR non-manager → form **không** hiển thị 2 field bank (section Quản lý ẩn). Xác nhận đúng phân quyền.

- [ ] **Step 4 (tuỳ chọn): Cập nhật DB_TEST_DATA.md**

Nếu có seed giá trị ngân hàng cho NV demo, cập nhật `docs/DB_TEST_DATA.md` (nhật ký).

---

## Self-Review

- **Spec coverage:** §4.1 model → Task 1 · §4.2a map → Task 2 · §4.2b meta/banks → Task 3 · §4.2c detail → Task 4 · §4.3 SPA → Task 5 · §6 test (ghi đúng/chặn tier/meta) → Task 1-4 · §7 tiêu chí (build, preview, phân quyền) → Task 5-6. Out-of-scope (wizard) giữ nguyên — không có task, đúng chủ đích.
- **Refinement so với spec:** thêm `groups='hr.group_hr_manager'` trên field model (spec §4.1 chỉ ghi Char) — strengthening đúng intent tier mgr, theo pattern field liền kề.
- **Type consistency:** key payload `bankCode`/`bankAccountNo` ↔ field `x_bank_code`/`x_bank_account_no` ↔ detail `bankCode`/`bankAccountNo` ↔ initForm `bankCode`/`bankAccountNo` — đồng nhất xuyên suốt. Helper `_bank_options(env)` ký hiệu khớp ở Task 3 (định nghĩa) và test.
- **Placeholder scan:** không có TBD/TODO; mọi step có code/lệnh cụ thể.
