# Attendance History Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tách `MyHistory` ra tab `'history'` riêng trong `Attendance.jsx`, thêm bộ lọc Thường/OT/Tất cả (chính thức) hoặc Công CTV (CTV), với API endpoint mới trả về dữ liệu gộp.

**Architecture:** Backend thêm hàm `_shift_history_row()` + `_att_me_history_full()` + route `/history-full`. Frontend thêm `AttendanceHistory.jsx` (filter tabs + bảng) và wire vào `Attendance.jsx` tab `'history'`. Tab `'me'` giữ nguyên — không xóa `MyHistory`.

**Tech Stack:** Python/Odoo 17, React 18 (JSX), CSS variables theo design system dự án.

## Global Constraints

- camelCase cho tất cả field JSON trả về từ API
- Giờ UTC stored → local qua `_dt_local(rec, dt)` (đã có)
- Dùng lại `_att_row`, `_ot_row`, `AttendanceDrawer`, `Badge`, `Icon`, `LoadingState`, `ErrorState`, `EmptyState` — không sửa các file đó
- `hocba.shift.attendance` không có `check_in_map_url`, `needs_review` → trả `None`
- Chỉ lấy ca có `state = 'approved'`
- `x_employment_status` của `hr.employee`: `'official'` = chính thức, `'ctv'` = CTV

---

## File Map

| File | Hành động | Trách nhiệm |
|---|---|---|
| `custom-addons/hocba_hrm/controllers/main.py` | Modify | Thêm `_shift_history_row()`, `_att_me_history_full()`, route `/history-full` |
| `frontend/src/api/attendance.js` | Modify | Thêm `fetchMyHistoryFull(month, type)` |
| `frontend/src/features/attendance/AttendanceHistory.jsx` | Create | Component mới: filter tabs + summary bar + bảng 9 cột |
| `frontend/src/features/attendance/Attendance.jsx` | Modify | Thêm tab `'history'`, import + render `AttendanceHistory` |

---

### Task 1: Backend — `_shift_history_row` + `_att_me_history_full` + route

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (sau dòng 282, trước `_att_me_history`)

**Interfaces:**
- Produces: `GET /hocba-hrm/api/attendance/me/history-full?month=YYYY-MM&type=all|regular|ot|ctv`
- Response shape:
  ```json
  {
    "month": "2026-06",
    "employmentStatus": "official",
    "rows": [
      {
        "id": 1, "date": "2026-06-19",
        "checkIn": "2026-06-19T08:00:00", "checkOut": "2026-06-19T17:00:00",
        "workingHours": 9.0, "lateMinutes": 0, "earlyLeaveMinutes": 0,
        "missingMinutes": 0, "workCredit": 1.0, "statusKey": "on_time",
        "rowType": "regular", "shiftLabel": null,
        "needsReview": false, "faceSuspect": false, "outOfZone": false,
        "outOfWindow": false, "hasImg": true, "hasCheckOutImg": false,
        "empId": 5, "name": "Nguyễn A", "code": "NV001", "depName": "IT"
      }
    ],
    "summary": {
      "daysPresent": 20, "totalCredit": 20.0,
      "deficitCredit": 0.5, "netCredit": 19.5,
      "onTime": 18, "late": 2, "needsReview": 1,
      "totalHours": 180.0,
      "otHours": 4.0, "congOt": 1.0,
      "ctvHours": 0.0, "congCtv": 0.0
    }
  }
  ```

- [ ] **Step 1: Thêm hàm `_shift_history_row` vào `main.py` (sau dòng 282)**

  Tìm dòng:
  ```python
  def _att_me_history(env, month_str):
  ```
  Chèn TRƯỚC dòng đó (sau `_ot_for_employee`):

  ```python
  def _shift_history_row(env, s, att, row_type):
      """Một dòng ca OT/CTV cho history-full (unified row format như _att_row).
      s = hocba.work_shift, att = hocba.shift.attendance (có thể None/empty)."""
      from math import floor
      emp = s.employee_id
      d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
      start_local = fields.Datetime.context_timestamp(s, s.start) if s.start else None
      end_local = fields.Datetime.context_timestamp(s, s.end) if s.end else None

      checked_in = bool(att and att.check_in)
      hours = att.worked_hours if att else 0.0
      worked_min = int(hours * 60)

      # Shift duration (minutes)
      shift_min = 0
      if s.start and s.end:
          shift_min = int((s.end - s.start).total_seconds() / 60)

      # Late = check_in vượt quá shift.start
      late_min = 0
      if checked_in and s.start:
          diff = (att.check_in - s.start).total_seconds()
          late_min = max(0, int(diff / 60))

      # Early leave = check_out trước shift.end
      early_min = 0
      if att and att.check_out and s.end:
          diff = (s.end - att.check_out).total_seconds()
          early_min = max(0, int(diff / 60))

      # Missing = shift duration - worked (nếu đã check in)
      missing_min = max(0, shift_min - worked_min) if checked_in else 0

      # workCredit = congCa
      cong_ca = round((hours / 8.0) * (s.rate or 1.0), 2) if checked_in else 0.0

      # statusKey
      if not checked_in:
          status_key = 'none'
      elif late_min > 0:
          status_key = 'late'
      else:
          status_key = 'on_time'

      # shiftLabel  e.g. "OT 150% · 08:00–12:00" hoặc "CTV · 08:00–12:00"
      t_start = start_local.strftime('%H:%M') if start_local else '?'
      t_end = end_local.strftime('%H:%M') if end_local else '?'
      if row_type == 'ot':
          level_label = '%s%%' % (int(float(s.ot_level or 100) * 100),) if s.ot_level else '100%'
          shift_label = 'OT %s · %s–%s' % (level_label, t_start, t_end)
      else:
          shift_label = 'CTV · %s–%s' % (t_start, t_end)

      return {
          'id': s.id,
          'empId': emp.id,
          'code': emp.x_employee_code or '—',
          'name': emp.name,
          'depName': emp.department_id.name or 'Chưa gán',
          'hasImg': bool(att and att.check_in_photo),
          'hasCheckOutImg': bool(att and att.check_out_photo),
          'date': _d(d) if d else None,
          'checkIn': _dt_local(att, att.check_in) if att and att.check_in else None,
          'checkOut': _dt_local(att, att.check_out) if att and att.check_out else None,
          'workingHours': round(hours, 2),
          'statusKey': status_key,
          'lateMinutes': late_min,
          'earlyLeaveMinutes': early_min,
          'missingMinutes': missing_min,
          'workCredit': cong_ca,
          'morningCredit': 0.0,
          'afternoonCredit': 0.0,
          'expectedCheckOut': _dt_local(s, s.end) if s.end else None,
          'faceSuspect': att.face_suspect if att else False,
          'outOfZone': att.out_of_zone if att else False,
          'outOfWindow': att.out_of_window if att else False,
          'needsReview': False,
          'checkInMapUrl': None,
          'checkOutMapUrl': None,
          'rowType': row_type,
          'shiftLabel': shift_label,
      }
  ```

- [ ] **Step 2: Thêm hàm `_att_me_history_full` vào `main.py` (sau `_att_me_history`)**

  Tìm dòng:
  ```python
  def _req_row(req):
  ```
  Chèn TRƯỚC dòng đó:

  ```python
  def _att_me_history_full(env, month_str, att_type):
      """Lịch sử chấm công đầy đủ (thường + OT + CTV) theo filter.
      att_type: 'all' | 'regular' | 'ot' | 'ctv'. None nếu chưa có hồ sơ NV."""
      emp = env.user.employee_id
      if not emp:
          return None
      policy = env['hocba.attendance.policy'].sudo().get_policy()
      if month_str:
          y, m = (int(x) for x in month_str.split('-'))
      else:
          today = fields.Date.context_today(env.user)
          y, m = today.year, today.month
      first = date(y, m, 1)
      last = date(y, m, calendar.monthrange(y, m)[1])

      # --- Regular rows ---
      regular_rows = []
      if att_type in ('regular', 'all'):
          recs = env['hocba.attendance'].sudo().search([
              ('employee_id', '=', emp.id),
              ('date', '>=', first), ('date', '<=', last),
          ], order='date desc')
          for r in recs:
              row = _att_row(r, policy)
              row['rowType'] = 'regular'
              row['shiftLabel'] = None
              regular_rows.append(row)

      # --- Shift rows (OT / CTV) ---
      ot_rows = []
      ctv_rows = []
      if att_type in ('ot', 'all'):
          shifts = env['hocba.work_shift'].sudo().search([
              ('employee_id', '=', emp.id),
              ('state', '=', 'approved'),
              ('shift_type', '=', 'ot'),
          ])
          for s in shifts:
              d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
              if d and first <= d <= last:
                  att = env['hocba.shift.attendance'].sudo().search(
                      [('shift_id', '=', s.id)], limit=1)
                  ot_rows.append(_shift_history_row(env, s, att or None, 'ot'))
      if att_type in ('ctv', 'all'):
          shifts = env['hocba.work_shift'].sudo().search([
              ('employee_id', '=', emp.id),
              ('state', '=', 'approved'),
              ('shift_type', '=', 'ctv'),
          ])
          for s in shifts:
              d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
              if d and first <= d <= last:
                  att = env['hocba.shift.attendance'].sudo().search(
                      [('shift_id', '=', s.id)], limit=1)
                  ctv_rows.append(_shift_history_row(env, s, att or None, 'ctv'))

      all_rows = sorted(
          regular_rows + ot_rows + ctv_rows,
          key=lambda r: r['date'] or '', reverse=True)

      # --- Summary ---
      total_credit = sum(r['workCredit'] for r in regular_rows)
      violations = sorted(
          [r for r in regular_rows if r['missingMinutes'] > 0],
          key=lambda r: r['date'])
      counted = violations[policy.violation_free_days:]
      std = policy.std_work_hours or 8.0
      deficit_credit = round(
          (sum(r['missingMinutes'] for r in counted) / 60.0) / std, 2)
      ot_hours = round(sum(r['workingHours'] for r in ot_rows if r['statusKey'] != 'none'), 2)
      cong_ot = round(sum(r['workCredit'] for r in ot_rows), 2)
      ctv_hours = round(sum(r['workingHours'] for r in ctv_rows if r['statusKey'] != 'none'), 2)
      cong_ctv = round(sum(r['workCredit'] for r in ctv_rows), 2)

      summary = {
          'daysPresent': len(regular_rows),
          'totalHours': round(sum(r['workingHours'] for r in regular_rows), 2),
          'totalCredit': round(total_credit, 2),
          'deficitCredit': deficit_credit,
          'netCredit': round(total_credit - deficit_credit, 2),
          'onTime': sum(1 for r in regular_rows if r['statusKey'] == 'on_time'),
          'late': sum(1 for r in regular_rows if r['statusKey'] == 'late'),
          'needsReview': sum(1 for r in regular_rows if r['needsReview']),
          'otHours': ot_hours,
          'congOt': cong_ot,
          'ctvHours': ctv_hours,
          'congCtv': cong_ctv,
      }
      return {
          'month': '%04d-%02d' % (y, m),
          'employmentStatus': emp.x_employment_status or 'official',
          'summary': summary,
          'rows': all_rows,
      }
  ```

- [ ] **Step 3: Thêm route `/history-full` vào class controller (ngay sau route `/history`)**

  Tìm:
  ```python
      @http.route('/hocba-hrm/api/attendance/enroll', auth='user',
  ```
  Chèn TRƯỚC:
  ```python
      @http.route('/hocba-hrm/api/attendance/me/history-full', auth='user',
                  type='http', methods=['GET'])
      def api_attendance_history_full(self, month=None, type=None, **kw):
          att_type = type if type in ('regular', 'ot', 'ctv', 'all') else 'all'
          data = _att_me_history_full(request.env, month, att_type)
          if data is None:
              return request.make_json_response({'error': 'no_employee'}, status=400)
          return request.make_json_response(data)
  ```

- [ ] **Step 4: Test thủ công API**

  Restart Odoo (hoặc dùng `--dev=reload`), rồi dùng browser/curl:
  ```
  GET /hocba-hrm/api/attendance/me/history-full?month=2026-06&type=all
  ```
  Kỳ vọng: JSON có `month`, `employmentStatus`, `rows`, `summary`. Không có lỗi 500.

  ```
  GET /hocba-hrm/api/attendance/me/history-full?type=ot
  ```
  Kỳ vọng: rows chỉ có `rowType: "ot"`.

- [ ] **Step 5: Commit**

  ```bash
  git add custom-addons/hocba_hrm/controllers/main.py
  git commit -m "feat(attendance): thêm API /history-full với filter regular/ot/ctv"
  ```

---

### Task 2: Frontend API — `fetchMyHistoryFull`

**Files:**
- Modify: `frontend/src/api/attendance.js`

**Interfaces:**
- Produces: `fetchMyHistoryFull(month: string, type: string): Promise<HistoryFullResponse>`
  - `month`: `'YYYY-MM'` hoặc `''` (backend dùng tháng hiện tại)
  - `type`: `'all' | 'regular' | 'ot' | 'ctv'`

- [ ] **Step 1: Thêm export vào `attendance.js`**

  Tìm dòng:
  ```javascript
  export const fetchMyHistory = (month) =>
  ```
  Chèn SAU dòng đó (sau dấu `;`):
  ```javascript
  export const fetchMyHistoryFull = (month, type) =>
    hbGet(`/hocba-hrm/api/attendance/me/history-full?month=${month}&type=${type}`);
  ```

- [ ] **Step 2: Verify không lỗi syntax**

  ```bash
  cd frontend && node --input-type=module < /dev/null || npx eslint src/api/attendance.js
  ```
  Kỳ vọng: không có error.

- [ ] **Step 3: Commit**

  ```bash
  git add frontend/src/api/attendance.js
  git commit -m "feat(attendance-api): thêm fetchMyHistoryFull"
  ```

---

### Task 3: Frontend Component — `AttendanceHistory.jsx`

**Files:**
- Create: `frontend/src/features/attendance/AttendanceHistory.jsx`

**Interfaces:**
- Consumes: `fetchMyHistoryFull(month, type)` từ Task 2
- Consumes: `AttendanceDrawer` (import sẵn, không sửa)
- Consumes: `fmtDate` từ `../../utils/format`, `fmtTime`, `attStatus`, `currentMonth`, `fmtCredit` từ `./util`
- Consumes: `Badge`, `Icon`, `LoadingState`, `ErrorState`, `EmptyState` từ `../../components/`
- Props: `me` (object từ `/api/attendance/me` — dùng `me.isOfficial` hoặc so sánh `employmentStatus` trong response)

- [ ] **Step 1: Tạo file `AttendanceHistory.jsx`**

  ```jsx
  /* Lịch sử chấm công đầy đủ — tab riêng với filter Thường / OT / Tất cả (chính thức)
     hoặc Công CTV (CTV). Spec: docs/superpowers/specs/2026-06-19-attendance-history-screen-design.md */
  import { useState, useEffect } from 'react';
  import Badge from '../../components/Badge';
  import Icon from '../../components/Icon';
  import { LoadingState, ErrorState, EmptyState } from '../../components/states';
  import { fetchMyHistoryFull } from '../../api/attendance';
  import { fmtDate } from '../../utils/format';
  import { fmtTime, attStatus, currentMonth, fmtCredit } from './util';
  import AttendanceDrawer from './AttendanceDrawer';

  function Sum({ val, lbl, col }) {
    return (
      <div className="stat" style={{ padding: '14px 16px' }}>
        <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: col || 'inherit' }}>{val}</div>
        <div className="stat-lbl" style={{ marginTop: 4 }}>{lbl}</div>
      </div>
    );
  }

  function SummaryBar({ summary, filter }) {
    if (filter === 'regular') return (
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
        <Sum val={summary.daysPresent} lbl="Ngày có mặt" />
        <Sum val={summary.totalCredit} lbl="Tổng công" />
        <Sum val={summary.deficitCredit} lbl="Công thiếu" col={summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
        <Sum val={summary.netCredit} lbl="Công thực" col="var(--green)" />
      </div>
    );
    if (filter === 'ot') return (
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 16 }}>
        <Sum val={summary.otHours} lbl="Giờ OT" />
        <Sum val={summary.congOt} lbl="Công OT" col="var(--green)" />
      </div>
    );
    if (filter === 'ctv') return (
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 16 }}>
        <Sum val={summary.ctvHours} lbl="Giờ CTV" />
        <Sum val={summary.congCtv} lbl="Công CTV" col="var(--green)" />
      </div>
    );
    // all
    return (
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(6,1fr)', marginBottom: 16 }}>
        <Sum val={summary.daysPresent} lbl="Ngày có mặt" />
        <Sum val={summary.totalCredit} lbl="Tổng công thường" />
        <Sum val={summary.deficitCredit} lbl="Công thiếu" col={summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
        <Sum val={summary.netCredit} lbl="Công thực" col="var(--green)" />
        <Sum val={summary.otHours} lbl="Giờ OT" />
        <Sum val={summary.congOt} lbl="Công OT" col="var(--green)" />
      </div>
    );
  }

  const ROW_TYPE_LABEL = { regular: 'Thường', ot: 'OT', ctv: 'CTV' };
  const ROW_TYPE_COLOR = { regular: 'gray', ot: 'amber', ctv: 'blue' };

  export default function AttendanceHistory({ me }) {
    const isCtv = me && !me.isOfficial;

    // filter: 'all' | 'regular' | 'ot' (chính thức) | 'ctv' (CTV)
    const defaultFilter = isCtv ? 'ctv' : 'all';
    const [filter, setFilter] = useState(defaultFilter);
    const [month, setMonth] = useState(currentMonth());
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);
    const [sel, setSel] = useState(null);

    const load = () => {
      setErr(null); setData(null);
      fetchMyHistoryFull(month, filter).then(setData).catch((e) => setErr(e.message));
    };
    useEffect(load, [month, filter]);

    const FILTERS = isCtv
      ? [['ctv', 'Công CTV']]
      : [['all', 'Tất cả'], ['regular', 'Thường'], ['ot', 'OT']];

    return (
      <div className="card" style={{ padding: 18 }}>
        <div className="between" style={{ marginBottom: 14 }}>
          <h3 style={{ margin: 0 }}>Lịch sử chấm công của tôi</h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
          </div>
        </div>

        {/* Filter tabs */}
        {FILTERS.length > 1 && (
          <div className="tabs" style={{ marginBottom: 14 }}>
            {FILTERS.map(([id, lbl]) => (
              <button key={id} className={'tab' + (filter === id ? ' active' : '')} onClick={() => setFilter(id)}>{lbl}</button>
            ))}
          </div>
        )}

        {err && <ErrorState message={err} onRetry={load} />}
        {!data && !err && <LoadingState label="Đang tải lịch sử…" />}

        {data && (
          <>
            <SummaryBar summary={data.summary} filter={filter} />

            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr>
                  <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                  <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th>
                  <th className="tbl-num">Về sớm</th><th className="tbl-num">Thiếu</th>
                  <th className="tbl-num">Ngày công</th><th>Trạng thái</th><th></th>
                </tr></thead>
                <tbody>
                  {data.rows.map((r) => {
                    const [lbl, kind] = attStatus(r.statusKey);
                    const showTypeBadge = filter === 'all' && r.rowType !== 'regular';
                    return (
                      <tr key={r.rowType + '-' + r.id} onClick={() => setSel(r)}>
                        <td className="mono">
                          <span title={r.shiftLabel || undefined}>{fmtDate(r.date)}</span>
                          {showTypeBadge && (
                            <Badge kind={ROW_TYPE_COLOR[r.rowType] || 'gray'} style={{ marginLeft: 6, fontSize: 10 }}>
                              {ROW_TYPE_LABEL[r.rowType]}
                            </Badge>
                          )}
                        </td>
                        <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                        <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                        <td className="tbl-num mono">{r.workingHours || '—'}</td>
                        <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
                        <td className="tbl-num mono">{r.earlyLeaveMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>-{r.earlyLeaveMinutes}'</span> : <span className="faint">—</span>}</td>
                        <td className="tbl-num mono">{r.missingMinutes > 0 ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span> : <span className="faint">—</span>}</td>
                        <td className="tbl-num mono" style={{ fontWeight: 600 }}>{fmtCredit(r.workCredit)}</td>
                        <td><span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                          <Badge kind={kind} dot>{lbl}</Badge>
                          {r.needsReview && <Badge kind="amber">!</Badge>}
                        </span></td>
                        <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {data.rows.length === 0 && <EmptyState>Chưa có bản ghi trong tháng này.</EmptyState>}
          </>
        )}

        {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify không lỗi import**

  Kiểm tra các import tồn tại:
  ```bash
  ls frontend/src/components/Badge.jsx frontend/src/components/Icon.jsx
  ls frontend/src/features/attendance/AttendanceDrawer.jsx
  ls frontend/src/features/attendance/util.js
  ```
  Kỳ vọng: tất cả tồn tại.

- [ ] **Step 3: Commit**

  ```bash
  git add frontend/src/features/attendance/AttendanceHistory.jsx
  git commit -m "feat(attendance-ui): thêm component AttendanceHistory với filter tabs"
  ```

---

### Task 4: Frontend Wiring — Tab `'history'` trong `Attendance.jsx`

**Files:**
- Modify: `frontend/src/features/attendance/Attendance.jsx`

**Interfaces:**
- Consumes: `AttendanceHistory` từ Task 3 — `<AttendanceHistory me={me} />`
- `me.isOfficial` — đã có trong response `/api/attendance/me`

- [ ] **Step 1: Thêm import `AttendanceHistory`**

  Tìm trong `Attendance.jsx`:
  ```javascript
  import ShiftAttendance from './ShiftAttendance';
  ```
  Thêm dòng sau:
  ```javascript
  import AttendanceHistory from './AttendanceHistory';
  ```

- [ ] **Step 2: Thêm tab `'history'` vào danh sách tabs**

  Tìm:
  ```javascript
  : [['me', 'Chấm công của tôi'], ['shift', shiftTabLabel], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
  ```
  Thay bằng:
  ```javascript
  : [['me', 'Chấm công của tôi'], ['history', 'Lịch sử chấm công'], ['shift', shiftTabLabel], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
  ```

- [ ] **Step 3: Thêm render tab `'history'`**

  Tìm:
  ```jsx
      {activeTab === 'shift' && (
  ```
  Chèn TRƯỚC dòng đó:
  ```jsx
        {activeTab === 'history' && <AttendanceHistory me={me} />}
  ```

- [ ] **Step 4: Kiểm tra trong trình duyệt**

  Khởi động dev server:
  ```bash
  cd frontend && npm run dev
  ```
  Mở trình duyệt → đăng nhập → vào Chấm công → kiểm tra:
  1. Tab "Lịch sử chấm công" xuất hiện giữa "Chấm công của tôi" và "Chấm công OT"
  2. Nhân viên chính thức: thấy 3 filter tab Tất cả / Thường / OT
  3. CTV: thấy 1 tab Công CTV
  4. Đổi tháng → bảng reload
  5. Đổi filter → bảng reload đúng loại
  6. Click dòng → `AttendanceDrawer` mở
  7. Tab "Chấm công của tôi" giữ nguyên (vẫn có `CheckInPanel` + `MyHistory`)

- [ ] **Step 5: Commit**

  ```bash
  git add frontend/src/features/attendance/Attendance.jsx
  git commit -m "feat(attendance-ui): thêm tab Lịch sử chấm công với AttendanceHistory"
  ```
