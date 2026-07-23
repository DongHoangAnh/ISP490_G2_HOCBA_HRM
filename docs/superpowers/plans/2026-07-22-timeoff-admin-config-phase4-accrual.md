# Trung tâm Cấu hình Time Off — Phase 4 (Kế hoạch tích lũy) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho Admin **tạo / sửa / xoá kế hoạch tích lũy phép năm** (`hr.leave.accrual.plan`) cùng các mốc (`hr.leave.accrual.plan.level`) trong khu "Cấu hình nghỉ phép" của SPA.

**Architecture:** Nối tiếp Phase 1-3. Thêm hàm cấp module + 3 endpoint vào `controllers/config.py` (`accrual-plans` GET, `accrual-plans/save` POST, `accrual-plans/delete` POST) gate `base.group_system` + ghi `sudo()`. Phơi ra **tập field cong lọc** (curated) đủ tái hiện 2 plan seed, tránh độ phức tạp của Odoo. Frontend bật tab "Tích lũy".

**Tech Stack:** Odoo 19, React 18 + Vite. Test backend Docker local theo CLAUDE.md.

**Tiền đề:** Phase 1 xong (`config.py` với `_guard`/`_is_admin`, `x_hb_managed`, shell `TimeoffConfig.jsx`). Phase 4 **không** thêm field DB, **không** migration, **không** bump version.

**Giới hạn phạm vi có chủ đích (no silent cap — ghi rõ):**
- Tần suất tích lũy (`frequency`) trong SPA chỉ hỗ trợ **`daily` (Hằng ngày)** và **`monthly` (Hàng tháng)** — hai giá trị này không cần field phụ (weekly cần `week_day`, bimonthly cần `first_day/second_day`, yearly cần `yearly_month/yearly_day`…). Muốn dùng tần suất khác → sửa ở backend Odoo. Seed Học Bá chỉ dùng `monthly`.
- Mỗi plan phơi field: `name`, `time_off_type_id`, `accrued_gain_time`, `can_be_carryover` (+ `carryover_month`/`carryover_day` khi bật).
- Mỗi level phơi field: `sequence`, `added_value`, `added_value_type`, `frequency`, `start_type`, `start_count`, `milestone_date`, `cap_accrued_time` (+ `maximum_leave`), `action_with_unused_accruals`, `carryover_options` (+ `postpone_max_days`).

**Field/selection (đã xác minh từ core `hr_leave_accrual_plan.py` / `_level.py`):**
- plan: `accrued_gain_time` `('start','end')` · `carryover_date` `('year_start','allocation','other')` (ta set `'other'` khi bật carryover) · `carryover_month` `('1'..'12')` · `carryover_day` selection ngày (dùng input số 1–31).
- level: `start_type` `('day','month','year')` · `milestone_date` `('creation','after')` · `frequency` (curated `daily/monthly`) · `added_value_type` `('day','hour')` · `action_with_unused_accruals` `('lost','all')` · `carryover_options` `('unlimited','limited')`.

---

## File Structure

**Backend (`custom-addons/hocba_timeoff/`):**
- Modify `controllers/config.py` — thêm `ACCRUAL_FREQUENCIES`, `_accrual_level_row`, `_accrual_plan_row`, `_accrual_field_options`, `_config_list_accrual_plans`, `_accrual_level_vals`, `_config_save_accrual_plan`, `_config_delete_accrual_plan`, và 3 route.
- Modify `tests/test_admin_config.py` — thêm class `TestAdminConfigAccrual`.

**Frontend (`frontend/`):**
- Modify `src/api/timeoffConfig.js` — thêm `fetchAccrualPlans`, `saveAccrualPlan`, `deleteAccrualPlan`.
- Create `src/features/timeoff-config/AccrualTab.jsx` — bảng plan + form plan/level.
- Modify `src/features/timeoff-config/TimeoffConfig.jsx` — bật tab `accrual`.

---

## Task 1: Backend — endpoint list/save/delete accrual plan + level

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/config.py`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`

- [ ] **Step 1: Viết test thất bại**

Thêm class mới vào cuối `custom-addons/hocba_timeoff/tests/test_admin_config.py`:

```python
@tagged('post_install', '-at_install')
class TestAdminConfigAccrual(TransactionCase):

    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin P4', 'login': 'cfg_admin_p4',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})
        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')

    def _env(self):
        return self.env(user=self.admin_user)

    def _level(self, **kw):
        base = {'sequence': 10, 'addedValue': 1, 'addedValueType': 'day',
                'frequency': 'monthly', 'startType': 'day', 'startCount': 0,
                'milestoneDate': 'creation', 'capAccruedTime': True,
                'maximumLeave': 12, 'actionWithUnusedAccruals': 'all',
                'carryoverOptions': 'limited', 'postponeMaxDays': 5}
        base.update(kw)
        return base

    def test_list_returns_seeded_plans(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_accrual_plans
        data = _config_list_accrual_plans(self._env())
        names = [p['name'] for p in data['plans']]
        self.assertIn('Phép Năm — Nhân Viên Toàn Thời Gian', names)
        self.assertTrue(data['leaveTypeChoices'])

    def test_field_options_frequency_curated(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_accrual_plans
        data = self._config = _config_list_accrual_plans(self._env())
        freq_vals = {o['value'] for o in data['fieldOptions']['frequency']}
        self.assertEqual(freq_vals, {'daily', 'monthly'})

    def test_create_plan_with_level(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_accrual_plan
        row = _config_save_accrual_plan(self._env(), {
            'name': 'Plan Thử', 'timeOffTypeId': self.annual.id,
            'accruedGainTime': 'start', 'canBeCarryover': True,
            'carryoverMonth': '3', 'carryoverDay': '31',
            'levels': [self._level(addedValue=0.5, maximumLeave=6)]})
        plan = self.env['hr.leave.accrual.plan'].browse(row['id'])
        self.assertEqual(len(plan.level_ids), 1)
        self.assertEqual(plan.level_ids.added_value, 0.5)
        self.assertEqual(plan.level_ids.frequency, 'monthly')

    def test_update_replaces_levels(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_accrual_plan
        env = self._env()
        row = _config_save_accrual_plan(env, {
            'name': 'Plan Sửa', 'timeOffTypeId': self.annual.id,
            'accruedGainTime': 'start', 'canBeCarryover': False,
            'levels': [self._level(addedValue=1)]})
        row2 = _config_save_accrual_plan(env, {
            'id': row['id'], 'name': 'Plan Sửa', 'timeOffTypeId': self.annual.id,
            'accruedGainTime': 'start', 'canBeCarryover': False,
            'levels': [self._level(addedValue=2), self._level(sequence=20, addedValue=3)]})
        plan = self.env['hr.leave.accrual.plan'].browse(row2['id'])
        self.assertEqual(len(plan.level_ids), 2)
        self.assertEqual(sorted(plan.level_ids.mapped('added_value')), [2.0, 3.0])

    def test_delete_used_plan_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_delete_accrual_plan
        used = self.env.ref('hocba_timeoff.hb_accrual_plan_annual_fulltime')
        with self.assertRaises(ValidationError):
            _config_delete_accrual_plan(self._env(), used.id)

    def test_delete_unused_plan_ok(self):
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_accrual_plan, _config_delete_accrual_plan)
        env = self._env()
        row = _config_save_accrual_plan(env, {
            'name': 'Plan Bỏ', 'timeOffTypeId': self.annual.id,
            'accruedGainTime': 'start', 'canBeCarryover': False,
            'levels': [self._level()]})
        _config_delete_accrual_plan(env, row['id'])
        self.assertFalse(self.env['hr.leave.accrual.plan'].browse(row['id']).exists())

    def test_bad_frequency_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_accrual_plan
        with self.assertRaises(ValidationError):
            _config_save_accrual_plan(self._env(), {
                'name': 'x', 'timeOffTypeId': self.annual.id,
                'accruedGainTime': 'start', 'canBeCarryover': False,
                'levels': [self._level(frequency='weekly')]})

    def test_non_positive_added_value_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_accrual_plan
        with self.assertRaises(ValidationError):
            _config_save_accrual_plan(self._env(), {
                'name': 'x', 'timeOffTypeId': self.annual.id,
                'accruedGainTime': 'start', 'canBeCarryover': False,
                'levels': [self._level(addedValue=0)]})
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigAccrual --stop-after-init --log-level=test
```
Expected: FAIL — `ImportError` (hàm accrual chưa có).

- [ ] **Step 3: Thêm logic vào `config.py`**

Thêm hằng số (cạnh `ALLOCATION_MODES`):
```python
ACCRUAL_FREQUENCIES = ('daily', 'monthly')  # SPA chỉ hỗ trợ 2 tần suất này
```

Thêm các hàm cấp module (sau nhóm holiday của Phase 3):
```python
def _accrual_level_row(lv):
    return {
        'id': lv.id,
        'sequence': lv.sequence,
        'addedValue': lv.added_value,
        'addedValueType': lv.added_value_type,
        'frequency': lv.frequency,
        'startType': lv.start_type,
        'startCount': lv.start_count,
        'milestoneDate': lv.milestone_date,
        'capAccruedTime': bool(lv.cap_accrued_time),
        'maximumLeave': lv.maximum_leave,
        'actionWithUnusedAccruals': lv.action_with_unused_accruals,
        'carryoverOptions': lv.carryover_options,
        'postponeMaxDays': lv.postpone_max_days,
    }


def _accrual_plan_row(env, plan):
    return {
        'id': plan.id,
        'name': plan.name or '',
        'active': bool(plan.active),
        'timeOffTypeId': plan.time_off_type_id.id or False,
        'timeOffTypeName': plan.time_off_type_id.name or '',
        'accruedGainTime': plan.accrued_gain_time,
        'canBeCarryover': bool(plan.can_be_carryover),
        'carryoverMonth': plan.carryover_month or '',
        'carryoverDay': plan.carryover_day or '',
        'employeesCount': plan.employees_count,
        'levels': [_accrual_level_row(l) for l in plan.level_ids.sorted('sequence')],
    }


def _accrual_field_options(env):
    Plan = env['hr.leave.accrual.plan']
    Level = env['hr.leave.accrual.plan.level']

    def opts(model, fname, only=None):
        sel = dict(model._fields[fname].selection)
        return [{'value': k, 'label': v} for k, v in sel.items()
                if only is None or k in only]

    return {
        'accruedGainTime': opts(Plan, 'accrued_gain_time'),
        'frequency': opts(Level, 'frequency', only=ACCRUAL_FREQUENCIES),
        'startType': opts(Level, 'start_type'),
        'milestoneDate': opts(Level, 'milestone_date'),
        'addedValueType': opts(Level, 'added_value_type'),
        'carryoverMonth': opts(Plan, 'carryover_month'),
        'actionWithUnusedAccruals': opts(Level, 'action_with_unused_accruals'),
        'carryoverOptions': opts(Level, 'carryover_options'),
    }


def _config_list_accrual_plans(env):
    plans = env['hr.leave.accrual.plan'].sudo().search([], order='name')
    managed = env['hr.leave.type'].sudo().search(
        [('x_hb_managed', '=', True)], order='id')
    return {
        'plans': [_accrual_plan_row(env, p) for p in plans],
        'leaveTypeChoices': [{'id': t.id, 'name': t.name} for t in managed],
        'fieldOptions': _accrual_field_options(env),
    }


def _accrual_level_vals(lv):
    freq = lv.get('frequency') or 'monthly'
    if freq not in ACCRUAL_FREQUENCIES:
        raise ValidationError(
            'Tần suất tích lũy không hỗ trợ trong SPA (chỉ Hằng ngày / Hàng '
            'tháng). Dùng backend Odoo cho tần suất khác.')
    try:
        added = float(lv.get('addedValue') or 0)
    except (TypeError, ValueError):
        raise ValidationError('Giá trị tích lũy không hợp lệ.')
    if added <= 0:
        raise ValidationError('Giá trị tích lũy phải lớn hơn 0.')
    vals = {
        'sequence': int(lv.get('sequence') or 10),
        'added_value': added,
        'added_value_type': lv.get('addedValueType') or 'day',
        'frequency': freq,
        'start_type': lv.get('startType') or 'day',
        'start_count': int(lv.get('startCount') or 0),
        'milestone_date': lv.get('milestoneDate') or 'creation',
        'cap_accrued_time': bool(lv.get('capAccruedTime')),
        'action_with_unused_accruals': lv.get('actionWithUnusedAccruals') or 'lost',
        'carryover_options': lv.get('carryoverOptions') or 'unlimited',
    }
    if vals['cap_accrued_time']:
        vals['maximum_leave'] = float(lv.get('maximumLeave') or 0)
    if vals['carryover_options'] == 'limited':
        vals['postpone_max_days'] = int(lv.get('postponeMaxDays') or 0)
    return vals


def _config_save_accrual_plan(env, vals):
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên kế hoạch không được để trống.')
    type_id = vals.get('timeOffTypeId')
    plan_vals = {
        'name': name,
        'time_off_type_id': int(type_id) if type_id else False,
        'accrued_gain_time': vals.get('accruedGainTime') or 'start',
        'can_be_carryover': bool(vals.get('canBeCarryover')),
    }
    if plan_vals['can_be_carryover']:
        plan_vals['carryover_date'] = 'other'
        if vals.get('carryoverMonth'):
            plan_vals['carryover_month'] = str(vals['carryoverMonth'])
        if vals.get('carryoverDay'):
            plan_vals['carryover_day'] = str(vals['carryoverDay'])
    # Thay TOÀN BỘ level: xoá cũ rồi tạo mới theo payload.
    level_cmds = [(5, 0, 0)]
    for lv in (vals.get('levels') or []):
        level_cmds.append((0, 0, _accrual_level_vals(lv)))
    plan_vals['level_ids'] = level_cmds
    Plan = env['hr.leave.accrual.plan'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        plan = Plan.browse(int(rec_id))
        if not plan.exists():
            raise ValidationError('Kế hoạch không tồn tại.')
        plan.write(plan_vals)
    else:
        plan = Plan.create(plan_vals)
    return _accrual_plan_row(env, plan)


def _config_delete_accrual_plan(env, rec_id):
    plan = env['hr.leave.accrual.plan'].sudo().browse(int(rec_id))
    if not plan.exists():
        raise ValidationError('Kế hoạch không tồn tại.')
    if plan.allocation_ids:
        raise ValidationError(
            'Không thể xoá: kế hoạch đang gắn với allocation của nhân viên.')
    if env['hb.timeoff.policy.rule'].sudo().search_count(
            [('accrual_plan_id', '=', plan.id)]):
        raise ValidationError(
            'Không thể xoá: kế hoạch đang gắn với chính sách nghỉ phép.')
    plan.unlink()
    return {'ok': True, 'id': int(rec_id)}
```

Thêm 3 route vào class `HocBaTimeoffConfig`:
```python
    @http.route('/hocba-hrm/api/timeoff/config/accrual-plans',
                auth='user', type='http', methods=['GET'])
    def accrual_plans(self, **kw):
        block = self._guard()
        if block:
            return block
        return request.make_json_response(
            _config_list_accrual_plans(request.env))

    @http.route('/hocba-hrm/api/timeoff/config/accrual-plans/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def accrual_plan_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_accrual_plan(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'plan': row})

    @http.route('/hocba-hrm/api/timeoff/config/accrual-plans/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def accrual_plan_delete(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            _config_delete_accrual_plan(request.env, payload.get('id'))
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'ok': True})
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: 8 test `TestAdminConfigAccrual` PASS.

> Nếu `test_create_plan_with_level` báo lỗi ràng buộc level (vd field phụ), kiểm lại `_accrual_level_vals` — với `frequency='monthly'`/`'daily'` không cần field ngày-trong-tuần/tháng; đảm bảo không truyền field thừa.

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
git commit -m "feat(timeoff): endpoint cấu hình admin — CRUD kế hoạch tích lũy + level"
```

---

## Task 2: Frontend — tab "Tích lũy"

**Files:**
- Modify: `frontend/src/api/timeoffConfig.js`
- Create: `frontend/src/features/timeoff-config/AccrualTab.jsx`
- Modify: `frontend/src/features/timeoff-config/TimeoffConfig.jsx`

- [ ] **Step 1: API wrapper**

Thêm vào cuối `frontend/src/api/timeoffConfig.js`:
```javascript
/* Kế hoạch tích lũy. → { plans:[...], leaveTypeChoices:[...], fieldOptions:{...} } */
export const fetchAccrualPlans = () => hbGet(`${BASE}/accrual-plans`);

/* Tạo/sửa plan + level (thay toàn bộ level). → { plan: {...} }
   payload: { id?, name, timeOffTypeId, accruedGainTime, canBeCarryover,
              carryoverMonth?, carryoverDay?, levels:[{...}] } */
export const saveAccrualPlan = (payload) =>
  hbPost(`${BASE}/accrual-plans/save`, payload);

/* Xoá plan (chặn nếu đang dùng). → { ok: true } */
export const deleteAccrualPlan = (id) =>
  hbPost(`${BASE}/accrual-plans/delete`, { id });
```

- [ ] **Step 2: Component AccrualTab**

Tạo `frontend/src/features/timeoff-config/AccrualTab.jsx`:
```javascript
/* Khu Cấu hình → tab "Tích lũy": CRUD kế hoạch tích lũy phép năm + các mốc.
   SPA chỉ hỗ trợ tần suất Hằng ngày / Hàng tháng (khác → sửa backend). Chỉ Admin. */
import { useEffect, useState } from 'react';
import { fetchAccrualPlans, saveAccrualPlan, deleteAccrualPlan } from '../../api/timeoffConfig';
import { LoadingState, ErrorState } from '../../components/states';

const EMPTY_LEVEL = {
  sequence: 10, addedValue: 1, addedValueType: 'day', frequency: 'monthly',
  startType: 'day', startCount: 0, milestoneDate: 'creation',
  capAccruedTime: true, maximumLeave: 12,
  actionWithUnusedAccruals: 'all', carryoverOptions: 'limited', postponeMaxDays: 5,
};
const EMPTY_PLAN = {
  id: null, name: '', timeOffTypeId: false, accruedGainTime: 'start',
  canBeCarryover: true, carryoverMonth: '3', carryoverDay: '31',
  levels: [{ ...EMPTY_LEVEL }],
};

export default function AccrualTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null);
    fetchAccrualPlans().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const opt = (key) => (data ? data.fieldOptions[key] || [] : []);

  const setLevel = (idx, patch) => {
    const levels = editing.levels.map((l, i) => (i === idx ? { ...l, ...patch } : l));
    setEditing({ ...editing, levels });
  };
  const addLevel = () =>
    setEditing({ ...editing, levels: [...editing.levels, { ...EMPTY_LEVEL, sequence: (editing.levels.length + 1) * 10 }] });
  const removeLevel = (idx) =>
    setEditing({ ...editing, levels: editing.levels.filter((_, i) => i !== idx) });

  const onSave = async () => {
    setSaving(true);
    try {
      await saveAccrualPlan(editing);
      setEditing(null);
      load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (p) => {
    if (!window.confirm(`Xoá kế hoạch "${p.name}"?`)) return;
    try {
      await deleteAccrualPlan(p.id);
      load();
    } catch (e) {
      setErr(e.message);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải kế hoạch tích lũy…" />;

  const Select = ({ value, onChange, options }) => (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );

  return (
    <div className="to-config-accrual">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <h3>Kế hoạch tích lũy ({data.plans.length})</h3>
        <button className="btn btn-primary" onClick={() => setEditing({ ...EMPTY_PLAN, levels: [{ ...EMPTY_LEVEL }] })}>
          + Thêm kế hoạch
        </button>
      </div>
      <table className="hb-table">
        <thead>
          <tr><th>Tên</th><th>Loại nghỉ</th><th>Số mốc</th><th>NV áp dụng</th><th></th></tr>
        </thead>
        <tbody>
          {data.plans.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.timeOffTypeName || '—'}</td>
              <td>{p.levels.length}</td>
              <td>{p.employeesCount}</td>
              <td>
                <button className="btn btn-sm" onClick={() => setEditing({ ...p, levels: p.levels.map((l) => ({ ...l })) })}>Sửa</button>
                <button className="btn btn-sm" onClick={() => onDelete(p)}>Xoá</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing && (
        <div className="hb-modal-backdrop" onClick={() => !saving && setEditing(null)}>
          <div className="hb-modal hb-modal-lg" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.id ? 'Sửa kế hoạch tích lũy' : 'Thêm kế hoạch tích lũy'}</h3>
            <label>Tên
              <input value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </label>
            <label>Loại nghỉ áp dụng
              <select value={editing.timeOffTypeId || ''}
                onChange={(e) => setEditing({ ...editing, timeOffTypeId: e.target.value ? Number(e.target.value) : false })}>
                <option value="">— Chọn —</option>
                {data.leaveTypeChoices.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </label>
            <label>Thời điểm cộng dồn
              <Select value={editing.accruedGainTime}
                onChange={(v) => setEditing({ ...editing, accruedGainTime: v })}
                options={opt('accruedGainTime')} />
            </label>
            <label><input type="checkbox" checked={editing.canBeCarryover}
              onChange={(e) => setEditing({ ...editing, canBeCarryover: e.target.checked })} /> Cho phép chuyển năm (carry-over)</label>
            {editing.canBeCarryover && (
              <div style={{ display: 'flex', gap: 8 }}>
                <label>Tháng hết hạn
                  <Select value={editing.carryoverMonth}
                    onChange={(v) => setEditing({ ...editing, carryoverMonth: v })}
                    options={opt('carryoverMonth')} />
                </label>
                <label>Ngày
                  <input type="number" min="1" max="31" value={editing.carryoverDay}
                    onChange={(e) => setEditing({ ...editing, carryoverDay: e.target.value })} />
                </label>
              </div>
            )}

            <h4 style={{ marginTop: 16 }}>Các mốc tích lũy</h4>
            {editing.levels.map((lv, idx) => (
              <div key={idx} className="hb-card" style={{ padding: 8, marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <label>Cộng
                    <input type="number" step="0.5" min="0" value={lv.addedValue}
                      onChange={(e) => setLevel(idx, { addedValue: Number(e.target.value) })} />
                  </label>
                  <label>Đơn vị
                    <Select value={lv.addedValueType}
                      onChange={(v) => setLevel(idx, { addedValueType: v })}
                      options={opt('addedValueType')} />
                  </label>
                  <label>Tần suất
                    <Select value={lv.frequency}
                      onChange={(v) => setLevel(idx, { frequency: v })}
                      options={opt('frequency')} />
                  </label>
                  <label><input type="checkbox" checked={lv.capAccruedTime}
                    onChange={(e) => setLevel(idx, { capAccruedTime: e.target.checked })} /> Trần tích lũy</label>
                  {lv.capAccruedTime && (
                    <label>Tối đa
                      <input type="number" step="0.5" min="0" value={lv.maximumLeave}
                        onChange={(e) => setLevel(idx, { maximumLeave: Number(e.target.value) })} />
                    </label>
                  )}
                  <label>Khi hết hạn
                    <Select value={lv.actionWithUnusedAccruals}
                      onChange={(v) => setLevel(idx, { actionWithUnusedAccruals: v })}
                      options={opt('actionWithUnusedAccruals')} />
                  </label>
                  <label>Carry-over
                    <Select value={lv.carryoverOptions}
                      onChange={(v) => setLevel(idx, { carryoverOptions: v })}
                      options={opt('carryoverOptions')} />
                  </label>
                  {lv.carryoverOptions === 'limited' && (
                    <label>Tối đa chuyển
                      <input type="number" min="0" value={lv.postponeMaxDays}
                        onChange={(e) => setLevel(idx, { postponeMaxDays: Number(e.target.value) })} />
                    </label>
                  )}
                  <button className="btn btn-sm" onClick={() => removeLevel(idx)}>Xoá mốc</button>
                </div>
              </div>
            ))}
            <button className="btn btn-sm" onClick={addLevel}>+ Thêm mốc</button>

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
import AccrualTab from './AccrualTab';
```

(b) Bỏ `disabled: true` ở entry `accrual` trong `TABS`:
```javascript
  { id: 'accrual', label: 'Tích lũy' },
```

(c) Thêm render sau `{tab === 'holidays' && <HolidaysTab />}`:
```javascript
      {tab === 'accrual' && <AccrualTab />}
```

- [ ] **Step 4: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 5: Verify qua Browser pane**

1. `preview_start`, đăng nhập `test_admin@hocba.vn` / `Hocba@2026`.
2. Vào "Cấu hình nghỉ phép" → tab **"Tích lũy"** → thấy 2 plan seed (Toàn Thời Gian, Trợ Giảng) với số mốc.
3. Tạo 1 plan thử (loại nghỉ = Phép Năm, 1 mốc: cộng 1 ngày/tháng, trần 12) → Lưu → xuất hiện; `read_network_requests` `accrual-plans/save` 200.
4. Sửa plan thử: thêm mốc thứ 2 → Lưu → số mốc = 2.
5. Xoá plan thử → biến mất. Thử xoá plan seed "Toàn Thời Gian" (đang gắn chính sách) → hiện lỗi "đang gắn với chính sách" (BE 400).
6. Chụp screenshot tab Tích lũy cho user.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/timeoffConfig.js \
  frontend/src/features/timeoff-config/AccrualTab.jsx \
  frontend/src/features/timeoff-config/TimeoffConfig.jsx \
  custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-spa): tab Tích lũy — CRUD kế hoạch tích lũy + mốc (daily/monthly)"
```

---

## Ghi chú vận hành

- SPA cố ý chỉ mở tần suất **Hằng ngày / Hàng tháng**. Plan seed có tần suất khác (không có) hoặc field nâng cao vẫn sửa được ở backend Odoo; SPA hiển thị được nhưng khi lưu sẽ chuẩn hoá theo tập field curated.
- Xoá plan bị chặn khi còn allocation hoặc chính sách tham chiếu — tránh mồ côi dữ liệu.

## Self-Review (đã rà)

- **Spec coverage (Phase 4):** full CRUD plan + level ✓ (Task 1); guard xoá khi đang dùng ✓ (`test_delete_used_plan_raises`); validate tên/added_value>0/tần suất hỗ trợ ✓; gate group_system tái dùng `_guard` ✓; UI plan + trình sửa level ✓.
- **Placeholder scan:** không có TBD; mọi bước có code/lệnh cụ thể. Giới hạn tần suất được ghi rõ (no silent cap).
- **Type consistency:** field keys FE↔BE khớp (plan: `id/name/timeOffTypeId/timeOffTypeName/accruedGainTime/canBeCarryover/carryoverMonth/carryoverDay/employeesCount/levels`; level: `sequence/addedValue/addedValueType/frequency/startType/startCount/milestoneDate/capAccruedTime/maximumLeave/actionWithUnusedAccruals/carryoverOptions/postponeMaxDays`); `fieldOptions` keys dùng chung BE↔FE (`opt(...)`); tên hàm `_config_list_accrual_plans`/`_config_save_accrual_plan`/`_config_delete_accrual_plan`/`_accrual_level_vals` nhất quán; endpoint path `config/accrual-plans(/save|/delete)` khớp `timeoffConfig.js` ↔ `config.py`.
- **Phụ thuộc:** Phase 1 (`_guard`/`x_hb_managed`/shell). CSS `hb-modal-lg` là gợi ý — nếu chưa có, dùng `hb-modal` sẵn có (modal vẫn hoạt động, chỉ hẹp hơn).
