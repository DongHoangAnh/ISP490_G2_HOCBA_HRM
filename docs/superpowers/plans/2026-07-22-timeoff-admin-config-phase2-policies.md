# Trung tâm Cấu hình Time Off — Phase 2 (Chính sách theo loại NV) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho Admin sửa **6 chính sách nghỉ phép theo loại nhân viên** (`hb.timeoff.policy.rule`) trong khu "Cấu hình nghỉ phép" của SPA: loại nghỉ được phép, chế độ phân bổ, kế hoạch tích lũy, số ngày phép năm, tên & ghi chú.

**Architecture:** Nối tiếp Phase 1. Thêm hàm cấp module + endpoint vào `controllers/config.py` (`policies` GET, `policies/save` POST) gate `base.group_system` + ghi qua `sudo()`. Chỉ **sửa** 6 bản có sẵn (model có `UNIQUE(employment_type)` → không tạo/xoá; `employment_type` bất biến qua API). Frontend bật tab "Chính sách" trong `TimeoffConfig.jsx`.

**Tech Stack:** Odoo 19, React 18 + Vite. Test backend Docker local theo CLAUDE.md.

**Tiền đề:** Phase 1 đã xong (controller `config.py` với `_guard`/`_is_admin`, field `x_hb_managed`, khu SPA `timeoff-config`). Phase 2 **không** thêm field DB, **không** migration, **không** bump version (chỉ thêm controller + FE + test).

**Model `hb.timeoff.policy.rule` (đã xác minh — `models/hb_timeoff_policy_rule.py`):**
- `name` Char (required) · `notes` Text
- `employment_type` Selection (required, **UNIQUE**, bất biến qua API):
  `fulltime`=Nhân viên Toàn thời gian · `teacher`=Giảng viên (Chính thức) · `ta`=Trợ giảng · `parttime`=Nhân viên Bán thời gian · `visiting`=Giảng viên Thỉnh giảng · `ctv`=Cộng tác viên
- `leave_type_ids` Many2many → `hr.leave.type`
- `accrual_plan_id` Many2one → `hr.leave.accrual.plan`
- `allocation_mode` Selection `('accrual','fixed','none')` default `none` (required)
- `annual_days` Float (default 0)
- `employee_count` Integer (compute, read-only)

---

## File Structure

**Backend (`custom-addons/hocba_timeoff/`):**
- Modify `controllers/config.py` — thêm `ALLOCATION_MODES`, `_policy_row`, `_config_list_policies`, `_config_save_policy`, và 2 route trong class `HocBaTimeoffConfig`.
- Modify `tests/test_admin_config.py` — thêm class `TestAdminConfigPolicies`.

**Frontend (`frontend/`):**
- Modify `src/api/timeoffConfig.js` — thêm `fetchPolicies`, `savePolicy`.
- Create `src/features/timeoff-config/PoliciesTab.jsx` — bảng 6 chính sách + form sửa.
- Modify `src/features/timeoff-config/TimeoffConfig.jsx` — bật tab `policies`.

---

## Task 1: Backend — endpoint list/save chính sách

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/config.py`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào cuối `custom-addons/hocba_timeoff/tests/test_admin_config.py` một class mới:

```python
@tagged('post_install', '-at_install')
class TestAdminConfigPolicies(TransactionCase):

    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin P2', 'login': 'cfg_admin_p2',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})

    def _env(self):
        return self.env(user=self.admin_user)

    def test_list_returns_six_policies_with_choices(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_policies
        data = _config_list_policies(self._env())
        self.assertEqual(len(data['policies']), 6)
        ft = next(p for p in data['policies'] if p['employmentType'] == 'fulltime')
        self.assertEqual(ft['annualDays'], 12)
        self.assertEqual(ft['employmentLabel'], 'Nhân viên Toàn thời gian')
        # choices: loại nghỉ managed + accrual plan seed đều có mặt
        self.assertTrue(data['leaveTypeChoices'])
        annual_id = self.env.ref('hocba_timeoff.hb_leave_type_annual').id
        self.assertIn(annual_id, [c['id'] for c in data['leaveTypeChoices']])
        ft_plan = self.env.ref('hocba_timeoff.hb_accrual_plan_annual_fulltime').id
        self.assertIn(ft_plan, [c['id'] for c in data['accrualPlanChoices']])

    def test_update_policy_writes(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        env = self._env()
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        sick_id = self.env.ref('hocba_timeoff.hb_leave_type_sick').id
        row = _config_save_policy(env, {
            'id': rule.id, 'name': 'CS Toàn thời gian (sửa)',
            'allocationMode': 'fixed', 'annualDays': 15,
            'accrualPlanId': False, 'notes': 'ghi chú mới',
            'leaveTypeIds': [sick_id]})
        self.assertEqual(row['annualDays'], 15)
        self.assertEqual(row['allocationMode'], 'fixed')
        self.assertEqual(rule.name, 'CS Toàn thời gian (sửa)')
        self.assertEqual(rule.leave_type_ids.ids, [sick_id])

    def test_employment_type_immutable(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        env = self._env()
        rule = self.env.ref('hocba_timeoff.hb_policy_ta')
        _config_save_policy(env, {
            'id': rule.id, 'name': rule.name, 'employmentType': 'fulltime',
            'allocationMode': rule.allocation_mode, 'annualDays': rule.annual_days,
            'leaveTypeIds': rule.leave_type_ids.ids})
        self.assertEqual(rule.employment_type, 'ta')  # KHÔNG đổi

    def test_negative_annual_days_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': rule.id, 'name': 'x', 'allocationMode': 'none',
                'annualDays': -1, 'leaveTypeIds': []})

    def test_save_without_id_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'name': 'mới', 'allocationMode': 'none', 'annualDays': 0})

    def test_bad_allocation_mode_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': rule.id, 'name': 'x', 'allocationMode': 'weird',
                'annualDays': 0, 'leaveTypeIds': []})
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigPolicies --stop-after-init --log-level=test
```
Expected: FAIL — `ImportError` (`_config_list_policies`/`_config_save_policy` chưa có).

- [ ] **Step 3: Thêm logic vào `config.py`**

Trong `custom-addons/hocba_timeoff/controllers/config.py`, thêm hằng số cạnh `REQUEST_UNITS`:
```python
ALLOCATION_MODES = ('accrual', 'fixed', 'none')
```

Thêm các hàm cấp module (sau `_config_toggle_leave_type`):
```python
def _policy_row(env, rule):
    labels = dict(rule._fields['employment_type'].selection)
    return {
        'id': rule.id,
        'name': rule.name or '',
        'employmentType': rule.employment_type,
        'employmentLabel': labels.get(rule.employment_type, rule.employment_type),
        'leaveTypeIds': rule.leave_type_ids.ids,
        'allocationMode': rule.allocation_mode,
        'accrualPlanId': rule.accrual_plan_id.id or False,
        'annualDays': rule.annual_days,
        'notes': rule.notes or '',
        'employeeCount': rule.employee_count,
    }


def _config_list_policies(env):
    rules = env['hb.timeoff.policy.rule'].sudo().search([], order='employment_type')
    managed = (env['hr.leave.type'].sudo()
               .search([('x_hb_managed', '=', True)], order='id'))
    plans = env['hr.leave.accrual.plan'].sudo().search([], order='name')
    return {
        'policies': [_policy_row(env, r) for r in rules],
        'leaveTypeChoices': [{'id': t.id, 'name': t.name} for t in managed],
        'accrualPlanChoices': [{'id': p.id, 'name': p.name} for p in plans],
        'allocationModes': [
            {'value': 'accrual', 'label': 'Tích lũy tự động'},
            {'value': 'fixed', 'label': 'Phân bổ cố định'},
            {'value': 'none', 'label': 'Không phân bổ'},
        ],
    }


def _config_save_policy(env, vals):
    rec_id = vals.get('id')
    if not rec_id:
        raise ValidationError(
            'Thiếu id chính sách — chỉ được sửa 6 chính sách có sẵn.')
    rule = env['hb.timeoff.policy.rule'].sudo().browse(int(rec_id))
    if not rule.exists():
        raise ValidationError('Chính sách không tồn tại.')
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên chính sách không được để trống.')
    mode = vals.get('allocationMode') or 'none'
    if mode not in ALLOCATION_MODES:
        raise ValidationError('Chế độ phân bổ không hợp lệ.')
    try:
        annual = float(vals.get('annualDays') or 0)
    except (TypeError, ValueError):
        raise ValidationError('Số ngày phép năm không hợp lệ.')
    if annual < 0:
        raise ValidationError('Số ngày phép năm không được âm.')
    # Chỉ nhận loại nghỉ do Học Bá quản lý (lọc bỏ id lạ/không managed).
    req_ids = [int(x) for x in (vals.get('leaveTypeIds') or [])]
    managed_ids = set(env['hr.leave.type'].sudo()
                      .search([('x_hb_managed', '=', True), ('id', 'in', req_ids)]).ids)
    valid_ids = [i for i in req_ids if i in managed_ids]
    plan_id = vals.get('accrualPlanId')
    # employment_type CỐ Ý không cho sửa (khoá UNIQUE, ánh xạ loại NV).
    rule.write({
        'name': name,
        'allocation_mode': mode,
        'annual_days': annual,
        'notes': vals.get('notes') or False,
        'leave_type_ids': [(6, 0, valid_ids)],
        'accrual_plan_id': int(plan_id) if plan_id else False,
    })
    return _policy_row(env, rule)
```

Thêm 2 route vào class `HocBaTimeoffConfig` (sau route `leave_type_toggle`):
```python
    @http.route('/hocba-hrm/api/timeoff/config/policies',
                auth='user', type='http', methods=['GET'])
    def policies(self, **kw):
        block = self._guard()
        if block:
            return block
        return request.make_json_response(_config_list_policies(request.env))

    @http.route('/hocba-hrm/api/timeoff/config/policies/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def policy_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_policy(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'policy': row})
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: cả 6 test của `TestAdminConfigPolicies` PASS.

- [ ] **Step 5: Regression toàn module**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/config.py \
  custom-addons/hocba_timeoff/tests/test_admin_config.py
git commit -m "feat(timeoff): endpoint cấu hình admin — sửa 6 chính sách theo loại NV"
```

---

## Task 2: Frontend — tab "Chính sách"

**Files:**
- Modify: `frontend/src/api/timeoffConfig.js`
- Create: `frontend/src/features/timeoff-config/PoliciesTab.jsx`
- Modify: `frontend/src/features/timeoff-config/TimeoffConfig.jsx`

- [ ] **Step 1: API wrapper**

Thêm vào cuối `frontend/src/api/timeoffConfig.js`:
```javascript
/* Chính sách theo loại NV (6 bản, chỉ sửa). → { policies, leaveTypeChoices, accrualPlanChoices, allocationModes } */
export const fetchPolicies = () => hbGet(`${BASE}/policies`);

/* Cập nhật 1 chính sách. → { policy: {...} }
   payload: { id, name, leaveTypeIds:[...], allocationMode, accrualPlanId, annualDays, notes } */
export const savePolicy = (payload) => hbPost(`${BASE}/policies/save`, payload);
```

- [ ] **Step 2: Component PoliciesTab**

Tạo `frontend/src/features/timeoff-config/PoliciesTab.jsx`:
```javascript
/* Khu Cấu hình → tab "Chính sách": sửa 6 chính sách nghỉ phép theo loại NV.
   Không tạo/xoá (mỗi loại NV đúng 1 chính sách). Chỉ Admin. */
import { useEffect, useState } from 'react';
import { fetchPolicies, savePolicy } from '../../api/timeoffConfig';
import { LoadingState, ErrorState } from '../../components/states';

export default function PoliciesTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null);
    fetchPolicies().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const toggleLeaveType = (id) => {
    const has = editing.leaveTypeIds.includes(id);
    setEditing({
      ...editing,
      leaveTypeIds: has
        ? editing.leaveTypeIds.filter((x) => x !== id)
        : [...editing.leaveTypeIds, id],
    });
  };

  const onSave = async () => {
    setSaving(true);
    try {
      await savePolicy(editing);
      setEditing(null);
      load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải chính sách…" />;

  const modeLabel = (v) =>
    (data.allocationModes.find((m) => m.value === v) || {}).label || v;

  return (
    <div className="to-config-policies">
      <h3>Chính sách theo loại nhân viên ({data.policies.length})</h3>
      <table className="hb-table">
        <thead>
          <tr>
            <th>Loại nhân viên</th><th>Tên chính sách</th>
            <th>Phân bổ</th><th>Ngày phép năm</th>
            <th>Số loại nghỉ</th><th>NV áp dụng</th><th></th>
          </tr>
        </thead>
        <tbody>
          {data.policies.map((p) => (
            <tr key={p.id}>
              <td>{p.employmentLabel}</td>
              <td>{p.name}</td>
              <td>{modeLabel(p.allocationMode)}</td>
              <td>{p.annualDays}</td>
              <td>{p.leaveTypeIds.length}</td>
              <td>{p.employeeCount}</td>
              <td><button className="btn btn-sm" onClick={() => setEditing({ ...p })}>Sửa</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing && (
        <div className="hb-modal-backdrop" onClick={() => !saving && setEditing(null)}>
          <div className="hb-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Sửa chính sách — {editing.employmentLabel}</h3>
            <label>Tên chính sách
              <input value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </label>
            <label>Chế độ phân bổ phép năm
              <select value={editing.allocationMode}
                onChange={(e) => setEditing({ ...editing, allocationMode: e.target.value })}>
                {data.allocationModes.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </label>
            <label>Kế hoạch tích lũy
              <select value={editing.accrualPlanId || ''}
                onChange={(e) => setEditing({ ...editing, accrualPlanId: e.target.value ? Number(e.target.value) : false })}>
                <option value="">— Không —</option>
                {data.accrualPlanChoices.map((pl) => (
                  <option key={pl.id} value={pl.id}>{pl.name}</option>
                ))}
              </select>
            </label>
            <label>Số ngày phép năm
              <input type="number" min="0" step="0.5" value={editing.annualDays}
                onChange={(e) => setEditing({ ...editing, annualDays: Number(e.target.value) })} />
            </label>
            <fieldset style={{ marginTop: 8 }}>
              <legend>Loại nghỉ được phép</legend>
              {data.leaveTypeChoices.map((t) => (
                <label key={t.id} style={{ display: 'block' }}>
                  <input type="checkbox"
                    checked={editing.leaveTypeIds.includes(t.id)}
                    onChange={() => toggleLeaveType(t.id)} /> {t.name}
                </label>
              ))}
            </fieldset>
            <label>Ghi chú
              <textarea rows="3" value={editing.notes}
                onChange={(e) => setEditing({ ...editing, notes: e.target.value })} />
            </label>
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" disabled={saving} onClick={onSave}>
                {saving ? 'Đang lưu…' : 'Lưu'}
              </button>
              <button className="btn" disabled={saving} onClick={() => setEditing(null)}>Huỷ</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Bật tab trong TimeoffConfig**

Trong `frontend/src/features/timeoff-config/TimeoffConfig.jsx`:

(a) Thêm import:
```javascript
import PoliciesTab from './PoliciesTab';
```

(b) Bỏ `disabled: true` ở entry `policies` trong `TABS`:
```javascript
const TABS = [
  { id: 'types', label: 'Loại nghỉ' },
  { id: 'policies', label: 'Chính sách' },
  { id: 'holidays', label: 'Ngày lễ', disabled: true },
  { id: 'accrual', label: 'Tích lũy', disabled: true },
];
```

(c) Thêm render sau `{tab === 'types' && <LeaveTypesTab />}`:
```javascript
      {tab === 'policies' && <PoliciesTab />}
```

- [ ] **Step 4: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công, không lỗi.

- [ ] **Step 5: Verify qua Browser pane**

1. `preview_start`, đăng nhập `test_admin@hocba.vn` / `Hocba@2026`.
2. Vào "Cấu hình nghỉ phép" → tab **"Chính sách"** → thấy bảng 6 chính sách (Toàn thời gian 12 ngày, Trợ giảng 6 ngày, CTV 0…).
3. Sửa 1 chính sách (đổi số ngày / tick loại nghỉ) → Lưu → bảng cập nhật; `read_network_requests` thấy `policies/save` trả 200.
4. Nhập số ngày âm → Lưu → hiện lỗi "không được âm" (BE trả 400).
5. Chụp screenshot tab Chính sách cho user.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/timeoffConfig.js \
  frontend/src/features/timeoff-config/PoliciesTab.jsx \
  frontend/src/features/timeoff-config/TimeoffConfig.jsx \
  custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-spa): tab Chính sách — sửa 6 chính sách nghỉ phép theo loại NV"
```

---

## Self-Review (đã rà)

- **Spec coverage (Phase 2):** sửa 6 policy rule ✓ (Task 1); loại nghỉ được phép / chế độ phân bổ / accrual plan / số ngày / tên / ghi chú ✓; `employment_type` bất biến ✓ (test `test_employment_type_immutable`); gate group_system tái dùng `_guard` ✓; validate annual_days≥0 + mode hợp lệ + phải có id ✓; UI tab Chính sách ✓.
- **Placeholder scan:** không có TBD; mọi bước có code/lệnh cụ thể.
- **Type consistency:** field keys FE↔BE khớp (`id/name/employmentType/employmentLabel/leaveTypeIds/allocationMode/accrualPlanId/annualDays/notes/employeeCount`); `allocationModes`/`leaveTypeChoices`/`accrualPlanChoices` dùng cùng shape ở list-endpoint và FE; tên hàm `_config_list_policies`/`_config_save_policy`/`_policy_row` nhất quán; endpoint path `config/policies` + `config/policies/save` khớp `timeoffConfig.js` ↔ `config.py`.
- **Phụ thuộc Phase 1:** dùng lại `_guard`, `_is_admin`, `x_hb_managed`, shell `TimeoffConfig.jsx` — phải hoàn tất Phase 1 trước.
