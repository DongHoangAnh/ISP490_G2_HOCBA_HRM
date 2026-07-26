# Trung tâm Cấu hình Time Off — Phase 3 (Ngày lễ) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho Admin quản lý **ngày lễ theo năm** trong khu "Cấu hình nghỉ phép" (thêm/sửa/xoá). Một thao tác ghi đồng bộ **cả 2 model**: `hr.leave.mandatory.day` (hiển thị "ngày bắt buộc có mặt" trên lịch) và `resource.calendar.leaves` (ngày lễ toàn cục để **trừ khỏi thời lượng đơn nghỉ**).

**Architecture:** Nối tiếp Phase 1-2. Thêm hàm cấp module + 3 endpoint vào `controllers/config.py` (`holidays` GET theo năm, `holidays/save` POST, `holidays/delete` POST) gate `base.group_system` + ghi `sudo()`. `mandatory.day` là bản ghi CHÍNH (mang tên/ngày/màu); bản `calendar.leaves` "twin" khớp theo ngày bắt đầu. Frontend bật tab "Ngày lễ".

**Tech Stack:** Odoo 19, React 18 + Vite. Test backend Docker local theo CLAUDE.md.

**Tiền đề:** Phase 1 xong (controller `config.py` với `_guard`/`_is_admin`, shell `TimeoffConfig.jsx`). Phase 3 **không** thêm field DB, **không** migration, **không** bump version.

**Field model (đã xác minh từ core):**
- `hr.leave.mandatory.day`: `name` Char(req) · `start_date` Date(req) · `end_date` Date(req) · `color` Integer · `company_id` (default) · `resource_calendar_id`/`department_ids`/`job_ids` (không dùng, để trống).
- `resource.calendar.leaves`: `name` Char · `date_from` Datetime(req) · `date_to` Datetime(req) · `time_type` Selection `('leave','other')` · `calendar_id` M2O (**False = áp mọi lịch**) · `resource_id` M2O (**False = áp mọi NV**).
- Quy ước giờ (theo seed `resource_calendar_leaves_data.xml`): `date_from = 'YYYY-MM-DD 00:00:00'`, `date_to = 'YYYY-MM-DD 23:59:59'` (UTC) — luôn phủ cửa sổ giờ làm ICT.

---

## File Structure

**Backend (`custom-addons/hocba_timeoff/`):**
- Modify `controllers/config.py` — thêm `_holiday_row`, `_twin_calendar_leaves`, `_calendar_leave_vals`, `_validate_holiday_vals`, `_config_list_holidays`, `_config_save_holiday`, `_config_delete_holiday`, và 3 route.
- Modify `tests/test_admin_config.py` — thêm class `TestAdminConfigHolidays`.

**Frontend (`frontend/`):**
- Modify `src/api/timeoffConfig.js` — thêm `fetchHolidays`, `saveHoliday`, `deleteHoliday`.
- Create `src/features/timeoff-config/HolidaysTab.jsx` — chọn năm + bảng + form + xoá.
- Modify `src/features/timeoff-config/TimeoffConfig.jsx` — bật tab `holidays`.

---

## Task 1: Backend — endpoint list/save/delete ngày lễ (đồng bộ 2 model)

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/config.py`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`

- [ ] **Step 1: Viết test thất bại**

Thêm class mới vào cuối `custom-addons/hocba_timeoff/tests/test_admin_config.py`:

```python
@tagged('post_install', '-at_install')
class TestAdminConfigHolidays(TransactionCase):

    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin P3', 'login': 'cfg_admin_p3',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})

    def _env(self):
        return self.env(user=self.admin_user)

    def _count_twin(self, start):
        from odoo import fields
        return self.env['resource.calendar.leaves'].search_count([
            ('calendar_id', '=', False), ('resource_id', '=', False),
            ('time_type', '=', 'leave'),
            ('date_from', '>=', fields.Datetime.to_datetime('%s 00:00:00' % start)),
            ('date_from', '<=', fields.Datetime.to_datetime('%s 23:59:59' % start)),
        ])

    def test_create_writes_both_models(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_holiday
        row = _config_save_holiday(self._env(), {
            'name': 'Ngày lễ thử', 'startDate': '2027-05-19',
            'endDate': '2027-05-19', 'color': 3})
        mday = self.env['hr.leave.mandatory.day'].browse(row['id'])
        self.assertTrue(mday.exists())
        self.assertEqual(str(mday.start_date), '2027-05-19')
        self.assertEqual(self._count_twin('2027-05-19'), 1)

    def test_list_by_year_filters(self):
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_holiday, _config_list_holidays)
        env = self._env()
        _config_save_holiday(env, {'name': 'Lễ 2028', 'startDate': '2028-03-10',
                                    'endDate': '2028-03-10', 'color': 1})
        data = _config_list_holidays(env, 2028)
        names = [h['name'] for h in data['holidays']]
        self.assertIn('Lễ 2028', names)
        data_other = _config_list_holidays(env, 2029)
        self.assertNotIn('Lễ 2028', [h['name'] for h in data_other['holidays']])

    def test_update_syncs_both(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_holiday
        env = self._env()
        row = _config_save_holiday(env, {'name': 'Lễ cũ', 'startDate': '2027-07-01',
                                         'endDate': '2027-07-01', 'color': 2})
        row2 = _config_save_holiday(env, {'id': row['id'], 'name': 'Lễ mới',
                                          'startDate': '2027-07-02',
                                          'endDate': '2027-07-03', 'color': 5})
        mday = self.env['hr.leave.mandatory.day'].browse(row2['id'])
        self.assertEqual(mday.name, 'Lễ mới')
        self.assertEqual(str(mday.end_date), '2027-07-03')
        self.assertEqual(self._count_twin('2027-07-02'), 1)
        self.assertEqual(self._count_twin('2027-07-01'), 0)  # twin đã dời ngày

    def test_delete_removes_both(self):
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_holiday, _config_delete_holiday)
        env = self._env()
        row = _config_save_holiday(env, {'name': 'Lễ xoá', 'startDate': '2027-09-09',
                                         'endDate': '2027-09-09', 'color': 1})
        _config_delete_holiday(env, row['id'])
        self.assertFalse(self.env['hr.leave.mandatory.day'].browse(row['id']).exists())
        self.assertEqual(self._count_twin('2027-09-09'), 0)

    def test_end_before_start_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_holiday
        with self.assertRaises(ValidationError):
            _config_save_holiday(self._env(), {'name': 'x', 'startDate': '2027-05-10',
                                               'endDate': '2027-05-09'})

    def test_name_required_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_holiday
        with self.assertRaises(ValidationError):
            _config_save_holiday(self._env(), {'name': '  ', 'startDate': '2027-05-10',
                                               'endDate': '2027-05-10'})
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigHolidays --stop-after-init --log-level=test
```
Expected: FAIL — `ImportError` (hàm holiday chưa có).

- [ ] **Step 3: Thêm logic vào `config.py`**

Đảm bảo đầu file có `from odoo import fields, http` (Phase 1 chỉ import `http`; **sửa dòng import** thành):
```python
from odoo import fields, http
```

Thêm các hàm cấp module (sau nhóm policy của Phase 2):
```python
def _holiday_row(mday):
    return {
        'id': mday.id,
        'name': mday.name or '',
        'startDate': str(mday.start_date),
        'endDate': str(mday.end_date),
        'color': mday.color or 0,
    }


def _twin_calendar_leaves(env, start_date):
    """Bản resource.calendar.leaves 'twin' của ngày lễ — khớp theo NGÀY bắt đầu
    (ngày lễ Học Bá không chồng lấn nên đủ định danh). start_date: date."""
    day_start = fields.Datetime.to_datetime('%s 00:00:00' % start_date)
    day_end = fields.Datetime.to_datetime('%s 23:59:59' % start_date)
    return env['resource.calendar.leaves'].sudo().search([
        ('calendar_id', '=', False),
        ('resource_id', '=', False),
        ('time_type', '=', 'leave'),
        ('date_from', '>=', day_start),
        ('date_from', '<=', day_end),
    ])


def _calendar_leave_vals(name, start_date, end_date):
    return {
        'name': name,
        'date_from': fields.Datetime.to_datetime('%s 00:00:00' % start_date),
        'date_to': fields.Datetime.to_datetime('%s 23:59:59' % end_date),
        'time_type': 'leave',
        'calendar_id': False,
        'resource_id': False,
    }


def _validate_holiday_vals(vals):
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên ngày lễ không được để trống.')
    try:
        start = fields.Date.to_date(vals.get('startDate'))
        end = fields.Date.to_date(vals.get('endDate'))
    except (ValueError, TypeError):
        raise ValidationError('Ngày không hợp lệ.')
    if not start or not end:
        raise ValidationError('Thiếu ngày bắt đầu/kết thúc.')
    if end < start:
        raise ValidationError('Ngày kết thúc phải >= ngày bắt đầu.')
    return name, start, end


def _config_list_holidays(env, year):
    year = int(year)
    MDay = env['hr.leave.mandatory.day'].sudo()
    days = MDay.search([
        ('start_date', '>=', '%d-01-01' % year),
        ('start_date', '<=', '%d-12-31' % year),
    ], order='start_date')
    years = sorted({d.start_date.year for d in MDay.search([]) if d.start_date})
    return {
        'year': year,
        'holidays': [_holiday_row(d) for d in days],
        'years': years,
    }


def _config_save_holiday(env, vals):
    name, start, end = _validate_holiday_vals(vals)
    color = int(vals.get('color') or 1)
    MDay = env['hr.leave.mandatory.day'].sudo()
    Cal = env['resource.calendar.leaves'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        mday = MDay.browse(int(rec_id))
        if not mday.exists():
            raise ValidationError('Ngày lễ không tồn tại.')
        twin = _twin_calendar_leaves(env, mday.start_date)  # theo ngày CŨ
        mday.write({'name': name, 'start_date': start,
                    'end_date': end, 'color': color})
        if twin:
            twin.write(_calendar_leave_vals(name, start, end))
        else:
            Cal.create(_calendar_leave_vals(name, start, end))
    else:
        mday = MDay.create({'name': name, 'start_date': start,
                            'end_date': end, 'color': color})
        Cal.create(_calendar_leave_vals(name, start, end))
    return _holiday_row(mday)


def _config_delete_holiday(env, rec_id):
    MDay = env['hr.leave.mandatory.day'].sudo()
    mday = MDay.browse(int(rec_id))
    if not mday.exists():
        raise ValidationError('Ngày lễ không tồn tại.')
    _twin_calendar_leaves(env, mday.start_date).unlink()
    mday.unlink()
    return {'ok': True, 'id': int(rec_id)}
```

Thêm 3 route vào class `HocBaTimeoffConfig`:
```python
    @http.route('/hocba-hrm/api/timeoff/config/holidays',
                auth='user', type='http', methods=['GET'])
    def holidays(self, **kw):
        block = self._guard()
        if block:
            return block
        try:
            year = int(kw.get('year') or fields.Date.today().year)
        except (TypeError, ValueError):
            year = fields.Date.today().year
        return request.make_json_response(
            _config_list_holidays(request.env, year))

    @http.route('/hocba-hrm/api/timeoff/config/holidays/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def holiday_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_holiday(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'holiday': row})

    @http.route('/hocba-hrm/api/timeoff/config/holidays/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def holiday_delete(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            _config_delete_holiday(request.env, payload.get('id'))
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'ok': True})
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: 6 test `TestAdminConfigHolidays` PASS.

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
git commit -m "feat(timeoff): endpoint cấu hình admin — CRUD ngày lễ đồng bộ 2 model"
```

---

## Task 2: Frontend — tab "Ngày lễ"

**Files:**
- Modify: `frontend/src/api/timeoffConfig.js`
- Create: `frontend/src/features/timeoff-config/HolidaysTab.jsx`
- Modify: `frontend/src/features/timeoff-config/TimeoffConfig.jsx`

- [ ] **Step 1: API wrapper**

Thêm vào cuối `frontend/src/api/timeoffConfig.js`:
```javascript
/* Ngày lễ theo năm. → { year, holidays:[{id,name,startDate,endDate,color}], years:[...] } */
export const fetchHolidays = (year) =>
  hbGet(`${BASE}/holidays${year ? `?year=${year}` : ''}`);

/* Tạo/sửa ngày lễ (ghi đồng bộ 2 model). → { holiday: {...} }
   payload: { id?, name, startDate, endDate, color } */
export const saveHoliday = (payload) => hbPost(`${BASE}/holidays/save`, payload);

/* Xoá ngày lễ (cả 2 model). → { ok: true } */
export const deleteHoliday = (id) => hbPost(`${BASE}/holidays/delete`, { id });
```

- [ ] **Step 2: Component HolidaysTab**

Tạo `frontend/src/features/timeoff-config/HolidaysTab.jsx`:
```javascript
/* Khu Cấu hình → tab "Ngày lễ": chọn năm, thêm/sửa/xoá ngày lễ.
   Mỗi thao tác đồng bộ mandatory.day + calendar.leaves ở backend. Chỉ Admin. */
import { useEffect, useState } from 'react';
import { fetchHolidays, saveHoliday, deleteHoliday } from '../../api/timeoffConfig';
import { LoadingState, ErrorState } from '../../components/states';

const THIS_YEAR = new Date().getFullYear();
const EMPTY = { id: null, name: '', startDate: '', endDate: '', color: 1 };

export default function HolidaysTab() {
  const [year, setYear] = useState(THIS_YEAR);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = (y) => {
    setErr(null);
    fetchHolidays(y).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(() => load(year), [year]);

  const onSave = async () => {
    setSaving(true);
    try {
      await saveHoliday(editing);
      setEditing(null);
      load(year);
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (row) => {
    if (!window.confirm(`Xoá ngày lễ "${row.name}"?`)) return;
    try {
      await deleteHoliday(row.id);
      load(year);
    } catch (e) {
      setErr(e.message);
    }
  };

  if (err) return <ErrorState message={err} onRetry={() => load(year)} />;
  if (!data) return <LoadingState label="Đang tải ngày lễ…" />;

  const yearOptions = Array.from(
    new Set([...(data.years || []), THIS_YEAR, THIS_YEAR + 1, year]),
  ).sort((a, b) => a - b);

  return (
    <div className="to-config-holidays">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <label>Năm{' '}
          <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {yearOptions.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
        <button className="btn btn-primary"
          onClick={() => setEditing({ ...EMPTY, startDate: `${year}-01-01`, endDate: `${year}-01-01` })}>
          + Thêm ngày lễ
        </button>
      </div>
      <table className="hb-table">
        <thead>
          <tr><th>Tên</th><th>Bắt đầu</th><th>Kết thúc</th><th></th></tr>
        </thead>
        <tbody>
          {data.holidays.length === 0 && (
            <tr><td colSpan="4">Chưa có ngày lễ nào cho năm {year}.</td></tr>
          )}
          {data.holidays.map((h) => (
            <tr key={h.id}>
              <td>{h.name}</td>
              <td>{h.startDate}</td>
              <td>{h.endDate}</td>
              <td>
                <button className="btn btn-sm" onClick={() => setEditing({ ...h })}>Sửa</button>
                <button className="btn btn-sm" onClick={() => onDelete(h)}>Xoá</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing && (
        <div className="hb-modal-backdrop" onClick={() => !saving && setEditing(null)}>
          <div className="hb-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.id ? 'Sửa ngày lễ' : 'Thêm ngày lễ'}</h3>
            <label>Tên
              <input value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </label>
            <label>Ngày bắt đầu
              <input type="date" value={editing.startDate}
                onChange={(e) => setEditing({ ...editing, startDate: e.target.value })} />
            </label>
            <label>Ngày kết thúc
              <input type="date" value={editing.endDate}
                onChange={(e) => setEditing({ ...editing, endDate: e.target.value })} />
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
import HolidaysTab from './HolidaysTab';
```

(b) Bỏ `disabled: true` ở entry `holidays` trong `TABS`:
```javascript
  { id: 'holidays', label: 'Ngày lễ' },
```

(c) Thêm render sau `{tab === 'policies' && <PoliciesTab />}`:
```javascript
      {tab === 'holidays' && <HolidaysTab />}
```

- [ ] **Step 4: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 5: Verify qua Browser pane**

1. `preview_start`, đăng nhập `test_admin@hocba.vn` / `Hocba@2026`.
2. Vào "Cấu hình nghỉ phép" → tab **"Ngày lễ"** → chọn năm 2026 → thấy các ngày lễ seed (Tết, 30/4, 2/9…).
3. Thêm 1 ngày lễ thử (năm 2027) → xuất hiện; đổi năm sang 2027 để thấy; `read_network_requests` `holidays/save` 200.
4. Sửa và Xoá ngày lễ thử → bảng cập nhật đúng.
5. (tuỳ chọn) Xác nhận đồng bộ: tạo đơn nghỉ vắt qua ngày lễ mới không bị tính ngày lễ vào quỹ — hoặc kiểm ở backend Odoo `resource.calendar.leaves` có bản ghi tương ứng.
6. Chụp screenshot tab Ngày lễ cho user.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/timeoffConfig.js \
  frontend/src/features/timeoff-config/HolidaysTab.jsx \
  frontend/src/features/timeoff-config/TimeoffConfig.jsx \
  custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-spa): tab Ngày lễ — CRUD theo năm, đồng bộ 2 model"
```

---

## Ghi chú vận hành

- Dịch vụ đồng bộ chỉ đảm bảo khi thao tác **qua SPA**. Nếu ai đó sửa tay `resource.calendar.leaves` hoặc `hr.leave.mandatory.day` ở backend, 2 model có thể lệch (twin khớp theo ngày bắt đầu). Ghi rõ cho HR trong tài liệu vận hành.
- Ngày lễ nhiều ngày (vd Tết 5 ngày) lưu 1 bản twin `calendar.leaves` với `date_from..date_to` phủ trọn dải — Odoo trừ đúng cả dải.

## Self-Review (đã rà)

- **Spec coverage (Phase 3):** full CRUD theo năm ✓; ghi đồng bộ 2 model ✓ (test `test_create_writes_both_models`, `test_delete_removes_both`, `test_update_syncs_both`); validate tên + end≥start ✓; gate group_system tái dùng `_guard` ✓; UI chọn năm + bảng + form ✓.
- **Placeholder scan:** không có TBD; mọi bước có code/lệnh cụ thể.
- **Type consistency:** field keys FE↔BE khớp (`id/name/startDate/endDate/color`, list trả `year/holidays/years`); tên hàm `_config_list_holidays`/`_config_save_holiday`/`_config_delete_holiday`/`_twin_calendar_leaves`/`_calendar_leave_vals` nhất quán; endpoint path `config/holidays(/save|/delete)` khớp `timeoffConfig.js` ↔ `config.py`.
- **Lưu ý import:** Phase 3 dùng `fields` → phải đảm bảo dòng import ở đầu `config.py` là `from odoo import fields, http` (Step 3 đã ghi rõ).
- **Phụ thuộc Phase 1:** dùng lại `_guard`/`_is_admin`/shell `TimeoffConfig.jsx`.
