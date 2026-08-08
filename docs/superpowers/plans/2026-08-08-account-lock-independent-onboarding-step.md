# Khóa tài khoản + bước nhận việc không ràng buộc thứ tự — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** HR khóa/mở khóa tài khoản đăng nhập và lọc màn Tài khoản theo phòng ban + trạng thái; đồng thời một bước nhận việc có thể đánh dấu "không ràng buộc thứ tự" để làm bất cứ lúc nào ngoài chuỗi tuần tự.

**Architecture:** Khóa tài khoản dùng thẳng `res.users.active` (Odoo đã chặn đăng nhập theo field này, offboarding cũng đã ghi vào đó) — thêm 1 hàm + 1 route trong `hocba_hrm/controllers/main.py`, lọc làm client-side trong SPA. Bước độc lập là cờ `is_independent` trên `hb.onboarding.template.step` + `hb.onboarding.step`; máy trạng thái coi bước độc lập nằm ngoài chuỗi: mở ngay lúc gán, `_next_waiting`/`_advance` bỏ qua, và không bị `skipped` khi chuỗi kết thúc.

**Tech Stack:** Odoo 19 (Python, `TransactionCase`), React 18 + Vite 6 (JSX, không TypeScript), PostgreSQL.

**Spec:** `docs/superpowers/specs/2026-08-08-account-lock-independent-onboarding-step-design.md`

**Nhánh:** `feature/account-lock-independent-step` (đã tạo, spec đã commit).

**Lệnh test dùng xuyên suốt** (Docker local — `MSYS_NO_PATHCONV=1` là BẮT BUỘC trên Git Bash, thiếu nó chạy 0 test mà vẫn báo OK):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Đổi `--test-tags /hocba_hrm` thành `/hocba_employees` khi test module employees. Kết quả cần thấy: `0 failed, 0 error(s) of N tests` với N > 0.

---

## PHẦN A — Khóa tài khoản + bộ lọc

### Task 1: Hàm `_account_set_active` (backend)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm hàm sau `_account_reset`, dòng ~1591; sửa dòng import 9)
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Write the failing tests**

Sửa dòng import đầu file test để thêm `_account_set_active`:

```python
from odoo.addons.hocba_hrm.controllers.main import (
    _account_create, _account_reset, _account_list, _account_payload,
    _account_set_active)
```

Thêm 4 test vào cuối class `TestAccount` (sau `test_list_forbidden_non_hr`):

```python
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
        with self.assertRaises(ValidationError):
            _account_set_active(self._env(self.hr), me.id, False)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm:TestAccount --stop-after-init --log-level=test
```

Expected: FAIL — `ImportError: cannot import name '_account_set_active'`.

- [ ] **Step 3: Sửa import của controller**

Trong `custom-addons/hocba_hrm/controllers/main.py` dòng 9, đổi:

```python
from odoo import http, fields
```

thành:

```python
from odoo import http, fields, SUPERUSER_ID
```

- [ ] **Step 4: Viết hàm `_account_set_active`**

Chèn ngay sau hàm `_account_reset` (kết thúc ở dòng ~1591), trước `def _account_list`:

```python
def _account_set_active(env, emp_id, active):
    """HR/Admin khóa (active=False) / mở khóa tài khoản đăng nhập.

    Dùng thẳng res.users.active — Odoo tự chặn đăng nhập, và offboarding
    cũng ghi vào đúng field này khi hoàn tất nghỉ việc.
    active_test=False vì NV đã nghỉ bị archive nhưng vẫn phải rà được."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được khóa/mở tài khoản.')
    emp = env['hr.employee'].sudo().with_context(
        active_test=False).browse(emp_id)
    if not emp.exists() or not emp.user_id:
        raise ValidationError('Nhân viên chưa có tài khoản.')
    user = emp.user_id
    if user.id == env.user.id:
        raise ValidationError(
            'Không thể khóa tài khoản của chính bạn.')
    admin = env.ref('base.user_admin', raise_if_not_found=False)
    if user.id == SUPERUSER_ID or (admin and user.id == admin.id):
        raise ValidationError(
            'Không thể khóa tài khoản quản trị hệ thống.')
    user.sudo().write({'active': bool(active)})
    emp.sudo().message_post(body=(
        '🔓 Mở khóa tài khoản đăng nhập.' if active
        else '🔒 Khóa tài khoản đăng nhập.'))
    return _account_payload(emp)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm:TestAccount --stop-after-init --log-level=test
```

Expected: PASS — `0 failed, 0 error(s)`, số test tăng thêm 4 so với Step 2.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_account.py
git commit -m "feat(accounts): them _account_set_active de khoa/mo tai khoan"
```

---

### Task 2: `_account_list` gồm NV đã nghỉ + `depId`/`empActive`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:1594-1613`
- Test: `custom-addons/hocba_hrm/tests/test_account.py`

- [ ] **Step 1: Write the failing test**

Thêm vào cuối class `TestAccount`:

```python
    def test_list_includes_archived_employee_with_dep_fields(self):
        self._mk_account('arch1')
        self.emp.sudo().write({'active': False})   # như sau offboarding
        out = _account_list(self._env(self.hr))
        row = next((r for r in out['accounts'] if r['login'] == 'arch1'),
                   None)
        self.assertIsNotNone(row, 'NV đã archive phải còn trong danh sách')
        self.assertEqual(row['depId'], self.dept.id)
        self.assertFalse(row['empActive'])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm:TestAccount --stop-after-init --log-level=test
```

Expected: FAIL — `AssertionError: NV đã archive phải còn trong danh sách`.

- [ ] **Step 3: Sửa `_account_list`**

Trong `_account_list`, đổi lệnh search và dict row. Thay:

```python
    emps = env['hr.employee'].sudo().search(
        [('user_id', '!=', False)], order='x_employee_code, id')
```

thành:

```python
    # active_test=False: NV đã nghỉ bị archive nhưng tài khoản của họ vẫn
    # phải rà soát được (nhóm bị khóa đông nhất).
    emps = env['hr.employee'].sudo().with_context(active_test=False).search(
        [('user_id', '!=', False)], order='x_employee_code, id')
```

Và thay dict row:

```python
        rows.append({
            'employeeId': e.id, 'name': e.name,
            'code': e.x_employee_code or '', 'depName': e.department_id.name or '',
            'login': u.login, 'active': u.active, 'role': role,
        })
```

thành:

```python
        rows.append({
            'employeeId': e.id, 'name': e.name,
            'code': e.x_employee_code or '',
            'depId': e.department_id.id or 0,
            'depName': e.department_id.name or '',
            'login': u.login, 'active': u.active, 'role': role,
            'empActive': e.active,
        })
```

Lưu ý: `u = e.user_id` trong vòng lặp cũng cần đọc được user đã archive — many2one đã lưu vẫn browse ra bình thường, không cần sửa.

- [ ] **Step 4: Run test to verify it passes**

Lệnh như Step 2. Expected: PASS, `0 failed, 0 error(s)`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_account.py
git commit -m "feat(accounts): _account_list gom NV da nghi, tra depId/empActive"
```

---

### Task 3: Route `POST /account/active`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm route sau `api_account_reset`, dòng ~3396)

Không có test tự động cho tầng route (repo này chưa có HttpCase cho account) — logic đã phủ ở Task 1; route chỉ là lớp vỏ, kiểm bằng tay ở Task 5.

- [ ] **Step 1: Thêm route**

Chèn ngay sau `api_account_reset` (kết thúc ở dòng ~3396), trước `api_accounts`:

```python
    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account/active',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_account_active(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            body = request.get_json_data()
            data = _account_set_active(
                request.env, emp_id, bool(body.get('active')))
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)
```

- [ ] **Step 2: Chạy lại toàn bộ test module để chắc không vỡ gì**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(accounts): route POST /account/active"
```

---

### Task 4: SPA — API client + bộ lọc + nút khóa

**Files:**
- Modify: `frontend/src/api/employees.js:60`
- Modify: `frontend/src/features/accounts/Accounts.jsx` (viết lại toàn bộ)

- [ ] **Step 1: Thêm API client**

Trong `frontend/src/api/employees.js`, ngay sau dòng `export const fetchAccounts = ...` (dòng 60), thêm:

```javascript
export const setAccountActive = (empId, active) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account/active`, { active });
```

- [ ] **Step 2: Viết lại `Accounts.jsx`**

Thay toàn bộ nội dung `frontend/src/features/accounts/Accounts.jsx` bằng:

```jsx
/* ============================================================
   Trang danh sách tài khoản đăng nhập (HR/Admin) — liệt kê NV đã có tài
   khoản (gồm cả NV đã nghỉ), lọc theo phòng ban / trạng thái, khóa-mở
   khóa + cấp lại mật khẩu. Tạo tài khoản làm ở drawer NV. Owner: Tân.
   Spec: docs/superpowers/specs/2026-08-08-account-lock-independent-onboarding-step-design.md
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchAccounts, setAccountActive } from '../../api/employees';
import AccountForm from '../employees/AccountForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const ROLE_LABEL = { employee: 'Nhân viên', giaovu: 'Giáo vụ', truongphong: 'Trưởng phòng' };

const sel = {
  padding: '6px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', fontFamily: 'inherit',
};
const nowrap = { width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' };

export default function Accounts({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [reset, setReset] = useState(null);  // { id, name } | null
  const [lock, setLock] = useState(null);    // { id, name, active } | null
  const [depId, setDepId] = useState('');    // '' = mọi phòng ban
  const [status, setStatus] = useState('');  // '' | 'active' | 'locked'

  const load = () => {
    setErr(null); setData(null);
    fetchAccounts().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tài khoản…" />;

  const { accounts, departments } = data;
  const q = search.trim().toLowerCase();
  const rows = accounts.filter((r) => {
    if (depId && String(r.depId) !== depId) return false;
    if (status === 'active' && !r.active) return false;
    if (status === 'locked' && r.active) return false;
    return !q
      || r.name.toLowerCase().includes(q)
      || (r.login || '').toLowerCase().includes(q)
      || (r.code || '').toLowerCase().includes(q);
  });
  const lockedCount = accounts.filter((r) => !r.active).length;

  const doToggleLock = () => setAccountActive(lock.id, !lock.active)
    .then(() => { setLock(null); load(); });

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tài khoản</h1>
          <p>{accounts.length} tài khoản đăng nhập · {lockedCount} đang khóa · {departments.length} phòng ban</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Danh sách tài khoản</h3>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
            <select style={sel} value={depId} onChange={(e) => setDepId(e.target.value)}>
              <option value="">Tất cả phòng ban</option>
              {departments.map((d) => (
                <option key={d.id} value={String(d.id)}>{d.name}</option>
              ))}
            </select>
            <select style={sel} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Mọi trạng thái</option>
              <option value="active">Đang sử dụng</option>
              <option value="locked">Đang khóa</option>
            </select>
            <span className="sub">{rows.length} người</span>
          </span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Mã</th><th>Phòng ban</th>
              {/* width:1% + nowrap: các cột phải co sát nội dung, dồn khoảng trống cho
                  cột Đăng nhập → nút thao tác kéo về gần cột Trạng thái, không bị đẩy khỏi khung. */}
              <th>Đăng nhập</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Loại</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.employeeId}>
                  <td><div className="nm">{r.name}</div></td>
                  <td className="muted mono">{r.code}</td>
                  <td>{r.depName}</td>
                  <td className="mono">{r.login}</td>
                  <td style={nowrap}>{ROLE_LABEL[r.role] || r.role}</td>
                  <td style={nowrap}>
                    <span style={{ display: 'inline-flex', gap: 5 }}>
                      <Badge kind={r.active ? 'green' : 'gray'} dot>
                        {r.active ? 'Hoạt động' : 'Khóa'}
                      </Badge>
                      {r.empActive === false && <Badge kind="gray">Đã nghỉ</Badge>}
                    </span>
                  </td>
                  <td style={nowrap}>
                    {/* NV đã nghỉ: tài khoản do offboarding khóa, mở lại ở đây sẽ
                        tạo user đăng nhập được trong khi hồ sơ NV vẫn archived
                        (env.user.employee_id rỗng) → BE chặn, FE ẩn luôn nút. */}
                    {(r.active || r.empActive !== false) && (
                      <button className="btn btn-ghost btn-sm"
                        onClick={() => setLock({ id: r.employeeId, name: r.name, active: r.active })}>
                        <Icon name={r.active ? 'lock' : 'unlock'} size={14} />
                        {r.active ? 'Khóa' : 'Mở khóa'}
                      </button>
                    )}
                    <button className="btn btn-ghost btn-sm" onClick={() => setReset({ id: r.employeeId, name: r.name })}>
                      <Icon name="rotateCcw" size={14} />Cấp lại MK</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Không có tài khoản khớp bộ lọc.</EmptyState>}
      </div>

      {reset && (
        <AccountForm emp={reset} mode="reset"
          onClose={() => setReset(null)}
          onDone={() => { setReset(null); load(); }} />
      )}

      {lock && (
        <ConfirmModal
          title={lock.active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
          message={lock.active
            ? `Khóa tài khoản của ${lock.name}? Người này sẽ không đăng nhập được cho tới khi được mở khóa.`
            : `Mở khóa tài khoản của ${lock.name}? Người này đăng nhập lại được ngay.`}
          confirmLabel={lock.active ? 'Khóa' : 'Mở khóa'}
          onConfirm={doToggleLock}
          onClose={() => setLock(null)} />
      )}
    </div>
  );
}
```

- [ ] **Step 3: Kiểm tra icon `lock` / `unlock` có tồn tại**

```bash
grep -n "lock\|unlock" frontend/src/components/Icon.jsx | head
```

Nếu **không** có key `lock`/`unlock`: đổi 2 chỗ dùng icon trong nút thành `<Icon name={r.active ? 'x' : 'checkCircle'} size={14} />` (2 key này chắc chắn có — đang dùng ở `OnboardingStepsPanel.jsx`). Không tự thêm icon mới.

- [ ] **Step 4: Build SPA và xác nhận build sạch**

```bash
cd frontend && npm run build
```

Expected: build thành công, không lỗi; output ghi vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 5: Kiểm bằng tay trên preview**

Mở app tại `/hocba-hrm` (preview qua proxy 8169 theo `CLAUDE.md`), đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026`, vào màn **Tài khoản**. Xác nhận:
1. Hai dropdown lọc hiện ra; chọn một phòng ban → danh sách co lại đúng.
2. Chọn "Đang khóa" → chỉ còn dòng badge xám.
3. Bấm **Khóa** một tài khoản thường → modal xác nhận → sau khi xác nhận, badge đổi thành "Khóa" và nút đổi thành "Mở khóa".
4. Bấm **Khóa** trên chính tài khoản đang đăng nhập → modal hiện lỗi "Không thể khóa tài khoản của chính bạn."

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/employees.js frontend/src/features/accounts/Accounts.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(accounts): SPA khoa/mo tai khoan + loc phong ban va trang thai"
```

---

## PHẦN B — Bước "không ràng buộc thứ tự"

### Task 5: Field `is_independent` + ràng buộc trên template step

**Files:**
- Modify: `custom-addons/hocba_employees/models/hb_onboarding_template.py:133-185`
- Modify: `custom-addons/hocba_employees/models/hb_onboarding_step.py:26-37`
- Test: `custom-addons/hocba_employees/tests/test_onboarding_template.py`

- [ ] **Step 1: Write the failing tests**

Thêm class mới vào cuối `custom-addons/hocba_employees/tests/test_onboarding_template.py`:

```python
@tagged('post_install', '-at_install')
class TestIndependentStepFlags(TransactionCase):
    """Cờ 'Không ràng buộc thứ tự' — spec 2026-08-08."""

    def _tpl(self, step_vals):
        return self.env['hb.onboarding.template'].create({
            'name': 'TPL Indep', 'sequence': 1,
            'apply_position_types': 'ctv',
            'step_ids': [(0, 0, step_vals)]})

    def test_independent_task_ok(self):
        tpl = self._tpl({'name': 'Cấp thiết bị', 'step_type': 'task',
                         'sequence': 1, 'is_independent': True})
        self.assertTrue(tpl.step_ids.is_independent)

    def test_independent_rejected_on_evaluation(self):
        with self.assertRaises(ValidationError):
            self._tpl({'name': 'ĐG', 'step_type': 'evaluation',
                       'sequence': 1, 'is_independent': True})

    def test_independent_rejected_with_auto_action(self):
        with self.assertRaises(ValidationError):
            self._tpl({'name': 'Cấp TB', 'step_type': 'task', 'sequence': 1,
                       'is_independent': True,
                       'auto_action': 'grant_assets'})

    def test_independent_rejected_with_is_extension(self):
        # is_extension chỉ hợp lệ trên evaluation, mà independent lại chỉ
        # hợp lệ trên task → hai cờ không bao giờ đi cùng nhau
        with self.assertRaises(ValidationError):
            self._tpl({'name': 'X', 'step_type': 'evaluation',
                       'sequence': 1, 'is_independent': True,
                       'is_extension': True})
```

Kiểm tra đầu file test đã có `from odoo.tests import tagged`, `from odoo.tests.common import TransactionCase` và `from odoo.exceptions import ValidationError`; thiếu cái nào thì thêm.

- [ ] **Step 2: Run tests to verify they fail**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees:TestIndependentStepFlags --stop-after-init --log-level=test
```

Expected: FAIL — `ValueError: Invalid field 'is_independent' on model 'hb.onboarding.template.step'`.

- [ ] **Step 3: Thêm field vào template step**

Trong `hb_onboarding_template.py`, class `HbOnboardingTemplateStep`, ngay sau field `is_extension` (dòng ~152-155), thêm:

```python
    is_independent = fields.Boolean(
        string='Không ràng buộc thứ tự',
        help='Chỉ bước Việc cần làm: bước mở ngay từ lúc gán quy trình, làm '
             'lúc nào cũng được, không chặn và không bị chặn bởi chuỗi.')
```

- [ ] **Step 4: Thêm field vào step instance (snapshot)**

Trong `hb_onboarding_step.py`, ngay sau field `is_extension` (dòng 33), thêm:

```python
    is_independent = fields.Boolean(string='Không ràng buộc thứ tự')
```

- [ ] **Step 5: Thêm ràng buộc**

Trong `hb_onboarding_template.py`, sửa decorator của `_check_step_flags` (dòng 163-164) để thêm `is_independent`:

```python
    @api.constrains('step_type', 'pass_completes', 'is_extension',
                    'is_independent', 'auto_action', 'due_days', 'sequence')
```

Và thêm 2 nhánh kiểm tra vào đầu vòng `for step in self:` (ngay sau `if step.due_days < 0: ...`):

```python
            if step.is_independent and step.step_type != 'task':
                raise ValidationError(_(
                    'Cờ "Không ràng buộc thứ tự" chỉ dùng cho bước Việc '
                    'cần làm — các bước Đánh giá phải chạy tuần tự.'))
            if step.is_independent and step.auto_action != 'none':
                raise ValidationError(_(
                    'Bước "không ràng buộc thứ tự" mở ngay từ đầu nên không '
                    'được đặt Automation — nếu không nó sẽ tự chạy ngày đầu.'))
```

- [ ] **Step 6: Run tests to verify they pass**

Lệnh như Step 2. Expected: PASS, 4 test mới đều xanh.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_employees/models/hb_onboarding_template.py custom-addons/hocba_employees/models/hb_onboarding_step.py custom-addons/hocba_employees/tests/test_onboarding_template.py
git commit -m "feat(onboarding): field is_independent + rang buoc tren buoc mau"
```

---

### Task 6: Gán quy trình — copy cờ và mở bước độc lập ngay

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py:746-763`
- Test: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Write the failing test**

Thêm class mới vào cuối `custom-addons/hocba_employees/tests/test_onboarding_step.py`:

```python
@tagged('post_install', '-at_install')
class TestOnboardingIndependentStep(TransactionCase):
    """Bước 'không ràng buộc thứ tự' nằm ngoài chuỗi — spec 2026-08-08."""

    def setUp(self):
        super().setUp()
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL Indep Engine', 'apply_position_types': 'staff',
            'apply_work_form': 'offline', 'sequence': 1,
            'step_ids': [
                (0, 0, {'name': 'ĐG tuần-2', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 14}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2, 'is_independent': True}),
                (0, 0, {'name': 'ĐG tháng-1', 'step_type': 'evaluation',
                        'sequence': 3, 'due_days': 30,
                        'pass_completes': True}),
                (0, 0, {'name': 'ĐG tháng-2', 'step_type': 'evaluation',
                        'sequence': 4, 'due_days': 60,
                        'is_extension': True, 'pass_completes': True}),
            ]})
        # BR-010: NV lên official phải đủ CCCD 12 số / MST / BHXH
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Indep', 'x_position_type': 'staff',
            'x_work_form': 'offline',
            'identification_id': '017788990201',
            'x_pit_code': '8017788992',
            'x_social_insurance_no': '0117788992',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today() - timedelta(days=10)})

    def _steps(self):
        return self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def test_independent_open_at_assign_alongside_first_step(self):
        s = self._steps()
        self.assertTrue(s[1].is_independent)
        self.assertEqual(s.mapped('state'),
                         ['open', 'open', 'waiting', 'waiting'])
```

Kiểm tra đầu file đã có `from datetime import timedelta`, `from odoo import fields` — đã có sẵn (dòng 1-3).

- [ ] **Step 2: Run test to verify it fails**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees:TestOnboardingIndependentStep --stop-after-init --log-level=test
```

Expected: FAIL — `AssertionError: ['open', 'waiting', 'waiting', 'waiting'] != ['open', 'open', 'waiting', 'waiting']`.

- [ ] **Step 3: Copy cờ khi tạo snapshot**

Trong `hr_employee.py`, hàm `_hocba_assign_onboarding`, thêm `is_independent` vào dict `Step.create(...)` (sau dòng `'is_extension': ts.is_extension,`, dòng 753):

```python
            'is_independent': ts.is_independent,
```

- [ ] **Step 4: Mở mọi bước độc lập + bước thường đầu tiên**

Trong cùng hàm, thay khối cuối (dòng 761-763):

```python
        if steps:
            steps.sorted(lambda s: (s.sequence, s.id))[0]._open()
        return steps
```

bằng:

```python
        # Bước độc lập nằm ngoài chuỗi → mở hết ngay. Chuỗi tuần tự vẫn
        # chỉ mở bước KHÔNG độc lập đầu tiên.
        ordered = steps.sorted(lambda s: (s.sequence, s.id))
        for step in ordered.filtered('is_independent'):
            step._open()
        chain = ordered.filtered(lambda s: not s.is_independent)
        if chain:
            chain[0]._open()
        return steps
```

- [ ] **Step 5: Run test to verify it passes**

Lệnh như Step 2. Expected: PASS.

- [ ] **Step 6: Chạy toàn bộ test onboarding để chắc không vỡ hành vi cũ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s)`. Đặc biệt `TestOnboardingAssign.test_auto_assign_on_create` (kỳ vọng `['open', 'waiting', 'waiting', 'waiting']`) phải vẫn xanh — template của nó không có bước độc lập.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py custom-addons/hocba_employees/tests/test_onboarding_step.py
git commit -m "feat(onboarding): buoc doc lap mo ngay luc gan quy trinh"
```

---

### Task 7: Máy trạng thái bỏ qua bước độc lập

**Files:**
- Modify: `custom-addons/hocba_employees/models/hb_onboarding_step.py:60-68` (`_next_waiting`), `:91-111` (`_advance`), `:202-215` (`action_evaluate` nhánh fail/pass)
- Test: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Write the failing tests**

Thêm 4 test vào class `TestOnboardingIndependentStep` (tạo ở Task 6):

```python
    def test_completing_independent_does_not_advance_chain(self):
        s = self._steps()
        s[1].action_complete()
        s = self._steps()
        self.assertEqual(s[1].state, 'done')
        self.assertEqual(s[0].state, 'open')     # chuỗi đứng yên
        self.assertEqual(s[2].state, 'waiting')
        # và KHÔNG được bắn chuông "hoàn tất quy trình" — chuỗi còn dở
        notif = self.env['hb.notification'].sudo().search([
            ('kind', '=', 'onboarding_chain_done'),
            ('target_ref', '=', self.emp.id)])
        self.assertFalse(notif)

    def test_chain_pass_skips_independent_step(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        s = self._steps()
        self.assertEqual(s[1].state, 'open')     # vẫn mở, không bị nuốt lượt
        self.assertEqual(s[2].state, 'open')     # chuỗi nhảy thẳng tháng-1

    def test_official_leaves_independent_open(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('pass')  # pass_completes
        self.assertEqual(self.emp.x_employment_status, 'official')
        s = self._steps()
        self.assertEqual(s[1].state, 'open')      # cấp thiết bị vẫn còn việc
        self.assertEqual(s[3].state, 'skipped')   # bước chuỗi thì bị bỏ

    def test_fail_leaves_independent_open(self):
        s = self._steps()
        s[0].action_evaluate('fail', note='Không đáp ứng')
        s = self._steps()
        self.assertEqual(s[1].state, 'open')
        self.assertEqual(s[2].state, 'skipped')
        self.assertEqual(s[3].state, 'skipped')
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees:TestOnboardingIndependentStep --stop-after-init --log-level=test
```

Expected: FAIL. `test_official_leaves_independent_open` và `test_fail_leaves_independent_open` báo `'skipped' != 'open'`; `test_completing_independent_does_not_advance_chain` báo bước tháng-1 bị mở sai.

- [ ] **Step 3: `_next_waiting` bỏ qua bước độc lập**

Trong `hb_onboarding_step.py`, thay hàm `_next_waiting` (dòng 60-68):

```python
    def _next_waiting(self):
        """Bước 'waiting' đứng sau self gần nhất (rỗng nếu hết)."""
        self.ensure_one()
        chain = list(self._chain())
        idx = chain.index(self)
        for step in chain[idx + 1:]:
            if step.state == 'waiting':
                return step
        return self.browse()
```

bằng:

```python
    def _next_waiting(self):
        """Bước 'waiting' trong CHUỖI đứng sau self gần nhất (rỗng nếu hết).

        Bước is_independent nằm ngoài chuỗi: không bao giờ được mở hay bỏ
        qua bởi điều hướng — HR làm nó lúc nào cũng được."""
        self.ensure_one()
        chain = [s for s in self._chain() if not s.is_independent]
        if self.is_independent:
            return self.browse()
        idx = chain.index(self)
        for step in chain[idx + 1:]:
            if step.state == 'waiting':
                return step
        return self.browse()
```

- [ ] **Step 4: `_advance` thoát sớm với bước độc lập**

Bước độc lập không điều hướng chuỗi. Nếu để nguyên, hoàn thành nó sẽ chạy
`_advance` → `_next_waiting()` trả rỗng (vì self độc lập) → hiểu nhầm là hết
chuỗi và bắn chuông "Hoàn tất quy trình nhận việc" sai.

Trong `_advance` (dòng 91-111), thêm ngay sau `self.ensure_one()`:

```python
        if self.is_independent:
            # Bước ngoài chuỗi: xong thì thôi, không mở bước nào và không
            # được coi là "hết chuỗi".
            return
```

- [ ] **Step 5: `pass_completes` và `fail` không skip bước độc lập**

Trong `action_evaluate`, nhánh `fail` (dòng 202-205), thay:

```python
        if result == 'fail':
            self._chain().filtered(
                lambda s: s.state in ('waiting', 'open')).sudo().write(
                    {'state': 'skipped'})
```

bằng:

```python
        if result == 'fail':
            self._chain().filtered(
                lambda s: s.state in ('waiting', 'open')
                and not s.is_independent).sudo().write({'state': 'skipped'})
```

Và nhánh `pass` + `pass_completes` (dòng 210-213), thay:

```python
        if self.pass_completes and not self._skip_auto():
            self._chain().filtered(
                lambda s: s.state == 'waiting').sudo().write(
                    {'state': 'skipped'})
```

bằng:

```python
        if self.pass_completes and not self._skip_auto():
            self._chain().filtered(
                lambda s: s.state == 'waiting'
                and not s.is_independent).sudo().write({'state': 'skipped'})
```

- [ ] **Step 6: Run tests to verify they pass**

Lệnh như Step 2. Expected: PASS — cả 5 test của class đều xanh.

- [ ] **Step 7: Chạy toàn bộ test module employees**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s) of N tests`, N > 0.

Lưu ý: theo memory `hocba_local_env_issues`, môi trường local có thể sẵn có 2 error ở `test_teaching_days` do `hocba_timeoff` không cài được — đó **không** phải regression của task này. Nếu thấy đúng 2 error đó và chúng đã tồn tại trước khi bắt đầu, ghi nhận rồi đi tiếp; error khác thì phải sửa.

- [ ] **Step 8: Commit**

```bash
git add custom-addons/hocba_employees/models/hb_onboarding_step.py custom-addons/hocba_employees/tests/test_onboarding_step.py
git commit -m "feat(onboarding): may trang thai bo qua buoc doc lap"
```

---

### Task 8: Seed data + migration cho DB sẵn có

**Files:**
- Modify: `custom-addons/hocba_employees/data/hb_onboarding_template_data.xml:37-43`
- Modify: `custom-addons/hocba_employees/__manifest__.py:3`
- Create: `custom-addons/hocba_employees/migrations/19.0.4.0.0/post-migrate.py`

- [ ] **Step 1: Sửa seed data cho DB cài mới**

Trong `hb_onboarding_template_data.xml`, thay record `onb_tpl_vp_step2` (dòng 37-43):

```xml
  <record id="onb_tpl_vp_step2" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">2</field>
    <field name="name">Cấp thiết bị làm việc</field>
    <field name="step_type">task</field>
    <field name="auto_action">grant_assets</field>
  </record>
```

bằng:

```xml
  <!-- Khách 2026-08-07: cấp thiết bị là luồng riêng, làm lúc nào cũng được.
       Bỏ auto_action vì bước độc lập mở ngay từ đầu — để automation thì nó
       tự cấp tài sản ngày đầu, HR mất quyền chọn thời điểm. -->
  <record id="onb_tpl_vp_step2" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">2</field>
    <field name="name">Cấp thiết bị làm việc</field>
    <field name="step_type">task</field>
    <field name="is_independent" eval="True"/>
  </record>
```

- [ ] **Step 2: Nâng version module**

Trong `custom-addons/hocba_employees/__manifest__.py` dòng 3, đổi:

```python
    'version': '19.0.3.0.0',
```

thành:

```python
    'version': '19.0.4.0.0',
```

- [ ] **Step 3: Viết migration**

Tạo `custom-addons/hocba_employees/migrations/19.0.4.0.0/post-migrate.py`:

```python
# Migration 19.0.4.0.0 — bước "Cấp thiết bị làm việc" thành bước không ràng
# buộc thứ tự (khách 2026-08-07). Seed template khai noupdate="1" nên upgrade
# KHÔNG đè, phải sửa tay ở đây; và NV đang chạy dở cũng cần mở bước ra.
# Spec: docs/superpowers/specs/2026-08-08-account-lock-independent-onboarding-step-design.md
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

XMLID = 'hocba_employees.onb_tpl_vp_step2'


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    tpl_step = env.ref(XMLID, raise_if_not_found=False)
    if not tpl_step:
        # DB seed khác đi (admin đã xoá/dựng lại quy trình) — không có gì
        # để sửa, thoát êm chứ không chặn upgrade.
        _logger.info('19.0.4.0.0: không thấy %s, bỏ qua.', XMLID)
        return
    tpl_step.write({'is_independent': True, 'auto_action': 'none'})

    steps = env['hb.onboarding.step'].with_context(
        active_test=False).search([
            ('template_id', '=', tpl_step.template_id.id),
            ('name', '=', tpl_step.name)])
    if not steps:
        _logger.info('19.0.4.0.0: không có bước NV nào cần chuyển.')
        return
    steps.write({'is_independent': True, 'auto_action': 'none'})
    # Bước đang chờ tới lượt → mở ngay để HR cấp thiết bị được.
    # done/skipped giữ nguyên: đó là lịch sử.
    waiting = steps.filtered(lambda s: s.state == 'waiting')
    waiting.write({'state': 'open'})
    _logger.info(
        '19.0.4.0.0: %s bước "Cấp thiết bị" thành độc lập, mở %s bước.',
        len(steps), len(waiting))
```

- [ ] **Step 4: Chạy upgrade để migration thực sự thực thi**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --stop-after-init --log-level=info
```

Expected: trong log thấy dòng `19.0.4.0.0: ... bước "Cấp thiết bị" thành độc lập, mở ... bước.` (hoặc dòng "không thấy/không có bước" nếu DB local không có seed đó — cả hai đều là kết quả hợp lệ, miễn không có traceback).

- [ ] **Step 5: Chạy lại test employees**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s)`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_employees/data/hb_onboarding_template_data.xml custom-addons/hocba_employees/__manifest__.py custom-addons/hocba_employees/migrations/19.0.4.0.0/post-migrate.py
git commit -m "feat(onboarding): seed + migration cho buoc cap thiet bi doc lap"
```

---

### Task 9: Payload controller cho SPA

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:2413-2426` (`_onb_emp_item`), `:2550-2556` (`_onb_tpl_json`), `:2562-2571` (`_onb_step_vals`)

- [ ] **Step 1: Thêm `isIndependent` vào payload bước của NV**

Trong `_onb_emp_item`, thêm khóa vào dict `item` (sau `'isExtension': s.is_extension,`, dòng 2421):

```python
                'isIndependent': s.is_independent,
```

- [ ] **Step 2: `current` ưu tiên bước trong chuỗi**

Trong cùng hàm, thay (dòng 2424-2425):

```python
            if s.state == 'open' and current is None:
                current = item
```

bằng:

```python
            # "Bước hiện tại" là bước của CHUỖI — bước độc lập luôn mở nên
            # nếu tính cả nó thì header lúc nào cũng hiện "Cấp thiết bị".
            if (s.state == 'open' and not s.is_independent
                    and current is None):
                current = item
```

- [ ] **Step 3: Thêm `isIndependent` vào payload template**

Trong `_onb_tpl_json`, thêm vào dict bước (sau `'isExtension': s.is_extension,`, dòng 2554):

```python
                'isIndependent': s.is_independent,
```

- [ ] **Step 4: Nhận `isIndependent` khi lưu template**

Trong `_onb_step_vals`, thêm vào dict (sau `'is_extension': bool(s.get('isExtension')),`, dòng 2568):

```python
            'is_independent': bool(s.get('isIndependent')),
```

- [ ] **Step 5: Chạy test hocba_hrm để chắc không vỡ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s)`. Chú ý `test_onboarding_api.py` — nếu nó khẳng định `current` theo cách cũ trên template có bước độc lập thì phải cập nhật kỳ vọng; template test hiện tại không có bước độc lập nên phải xanh nguyên.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(onboarding): payload isIndependent + current bo qua buoc doc lap"
```

---

### Task 10: SPA — cấu hình cờ + badge trên timeline

**Files:**
- Modify: `frontend/src/features/onboarding/OnboardingConfig.jsx:24-25, 104-111, 262-271, 394-398`
- Modify: `frontend/src/features/employees/OnboardingStepsPanel.jsx:279-287`

- [ ] **Step 1: Thêm `isIndependent` vào state rỗng của bước**

Trong `OnboardingConfig.jsx`, sửa `EMPTY_STEP` (dòng 24-25):

```javascript
  name: '', stepType: 'task', dueDays: 0,
  passCompletes: false, isExtension: false, autoAction: 'none', note: '',
```

thành:

```javascript
  name: '', stepType: 'task', dueDays: 0,
  passCompletes: false, isExtension: false, isIndependent: false,
  autoAction: 'none', note: '',
```

- [ ] **Step 2: Gửi cờ lên API khi lưu**

Trong cùng file, sửa `payload.steps` (dòng 104-111). Thay:

```javascript
        isExtension: s.stepType === 'evaluation' && !!s.isExtension,
        autoAction: s.stepType === 'task' ? (s.autoAction || 'none') : 'none',
```

bằng:

```javascript
        isExtension: s.stepType === 'evaluation' && !!s.isExtension,
        isIndependent: s.stepType === 'task' && !!s.isIndependent,
        // Ràng buộc BE: bước độc lập không được có automation.
        autoAction: (s.stepType === 'task' && !s.isIndependent)
          ? (s.autoAction || 'none') : 'none',
```

- [ ] **Step 3: Thêm checkbox vào form bước**

Trong cùng file, thay nhánh `task` (dòng 262-271):

```jsx
                ) : (
                  <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    Automation:
                    <select style={{ ...inp, padding: '5px 8px' }} value={s.autoAction || 'none'}
                      onChange={(e) => setStep(i, 'autoAction', e.target.value)}>
                      <option value="none">Không</option>
                      <option value="grant_assets">Tự cấp tài sản mặc định</option>
                    </select>
                  </label>
                )}
```

bằng:

```jsx
                ) : (
                  <>
                    <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}
                      title="Bước mở ngay từ lúc gán quy trình, làm lúc nào cũng được">
                      <input type="checkbox" checked={!!s.isIndependent}
                        onChange={(e) => setStep(i, 'isIndependent', e.target.checked)} />
                      Không ràng buộc thứ tự
                    </label>
                    <label style={{ display: 'flex', gap: 6, alignItems: 'center',
                      opacity: s.isIndependent ? 0.45 : 1 }}>
                      Automation:
                      <select style={{ ...inp, padding: '5px 8px' }} value={s.autoAction || 'none'}
                        disabled={!!s.isIndependent}
                        onChange={(e) => setStep(i, 'autoAction', e.target.value)}>
                        <option value="none">Không</option>
                        <option value="grant_assets">Tự cấp tài sản mặc định</option>
                      </select>
                    </label>
                  </>
                )}
```

- [ ] **Step 4: Thêm hậu tố vào dòng tóm tắt bước**

Trong cùng file, dòng tóm tắt (dòng 394-398), thêm một dòng sau `{s.isExtension ? ' · ↻gia hạn' : ''}`:

```jsx
              {s.isIndependent ? ' · ↗độc lập' : ''}
```

- [ ] **Step 5: Badge trên timeline bước của NV**

Trong `frontend/src/features/employees/OnboardingStepsPanel.jsx`, thay khối nhãn loại bước (dòng 279-285):

```jsx
                    <span style={{ fontWeight: 700, fontSize: 13.5 }}>
                      {s.name}
                      <span className="faint" style={{ fontWeight: 500, fontSize: 11.5, marginLeft: 8 }}>
                        {s.stepType === 'evaluation' ? 'Đánh giá' : 'Việc cần làm'}
                        {s.extendCount > 0 ? ` · đã gia hạn ×${s.extendCount}` : ''}
                      </span>
                    </span>
```

bằng:

```jsx
                    <span style={{ fontWeight: 700, fontSize: 13.5 }}>
                      {s.name}
                      <span className="faint" style={{ fontWeight: 500, fontSize: 11.5, marginLeft: 8 }}>
                        {s.stepType === 'evaluation' ? 'Đánh giá' : 'Việc cần làm'}
                        {s.extendCount > 0 ? ` · đã gia hạn ×${s.extendCount}` : ''}
                      </span>
                      {s.isIndependent && (
                        <Badge kind="teal" style={{ marginLeft: 8 }}>Không ràng buộc</Badge>
                      )}
                    </span>
```

`Badge` đã được import sẵn ở dòng 12. Nếu `Badge` không nhận prop `style`, bọc nó trong `<span style={{ marginLeft: 8 }}>…</span>` thay vì truyền `style`.

- [ ] **Step 6: Build SPA**

```bash
cd frontend && npm run build
```

Expected: build thành công, không lỗi.

- [ ] **Step 7: Kiểm bằng tay trên preview**

Đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026`:
1. Vào **Cấu hình nhận việc** → mở quy trình "Thử việc Nhân viên văn phòng" → bước "Cấp thiết bị làm việc" có checkbox "Không ràng buộc thứ tự" đã tick, ô Automation bị vô hiệu hóa.
2. Vào **Nhận việc** → mở một NV đang thử việc → bước "Cấp thiết bị làm việc" có badge "Không ràng buộc", trạng thái "Đang chờ" và bấm **Hoàn thành** được ngay dù Đánh giá tuần-2 chưa xong.
3. Bấm Hoàn thành bước đó → chuỗi không nhảy bước, Đánh giá tuần-2 vẫn là bước đang chờ.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/onboarding/OnboardingConfig.jsx frontend/src/features/employees/OnboardingStepsPanel.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(onboarding): SPA cau hinh + badge buoc khong rang buoc thu tu"
```

---

### Task 11: Chạy kiểm chứng cuối + cập nhật tài liệu

**Files:**
- Modify: `docs/DB_TEST_DATA.md`

- [ ] **Step 1: Chạy trọn bộ test cả hai module**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm,/hocba_employees --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s) of N tests` với N > 0. Chép nguyên dòng kết quả vào phần mô tả PR/báo cáo — không được khẳng định "đã pass" nếu chưa nhìn thấy dòng này.

- [ ] **Step 2: Ghi nhật ký đổi DB**

Thêm một mục vào phần nhật ký của `docs/DB_TEST_DATA.md`:

```markdown
- **2026-08-08** — Nâng `hocba_employees` lên `19.0.4.0.0`. Migration đặt bước
  "Cấp thiết bị làm việc" của quy trình "Thử việc Nhân viên văn phòng" thành
  *không ràng buộc thứ tự*, bỏ automation `grant_assets`, và mở các bước đang
  `waiting` của NV thử việc dở. Neon chưa chạy upgrade — khi chạy phải dùng
  endpoint TRỰC TIẾP (bỏ `-pooler`).
```

- [ ] **Step 3: Commit**

```bash
git add docs/DB_TEST_DATA.md
git commit -m "docs: nhat ky DB cho migration 19.0.4.0.0"
```

- [ ] **Step 4: Code review**

Dùng skill `superpowers:requesting-code-review` trên toàn bộ diff của nhánh so với `main`, rồi `superpowers:verification-before-completion` trước khi báo hoàn thành.

---

## Ghi chú rủi ro (đọc trước khi bắt đầu)

- **BR-010**: NV `official` phải có `identification_id` đúng 12 chữ số, mỗi NV một giá trị khác nhau, nếu không `ValidationError` ngay `setUp`. Test ở Task 6/7 đẩy NV lên Chính thức nên dùng đúng giá trị `'017788990201'` đã cấp — đừng copy CCCD từ test khác.
- **`MSYS_NO_PATHCONV=1`**: thiếu là chạy 0 test mà vẫn báo OK. Luôn kiểm dòng `of N tests` có N > 0.
- **SPA build artifacts** (`custom-addons/hocba_hrm/static/spa/`) được commit nên hay xung đột khi merge — giải bằng build lại từ source đã gộp, không merge tay bundle.
- **Neon**: nếu upgrade lên Neon, phải dùng endpoint trực tiếp (bỏ `-pooler` trong host), pooler rớt SSL giữa transaction DDL dài.
