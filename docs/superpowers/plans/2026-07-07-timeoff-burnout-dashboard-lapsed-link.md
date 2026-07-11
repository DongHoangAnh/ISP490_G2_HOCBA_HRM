# Tab "Sức khỏe NV" (Burnout) + Link nhanh Lapsed → Chờ duyệt — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lộ dữ liệu burnout (SQL view `hb.timeoff.burnout.line` đã có sẵn) ra tab SPA "Sức khỏe NV" cho officer, và biến chữ xám "xử lý ở tab Chờ duyệt" ở màn Giám sát duyệt thành link mở thẳng modal xử lý đơn.

**Architecture:** Backend theo đúng mẫu Phase 12: helper cấp module `_burnout_table(env, scope, dept_id)` trong `hocba_timeoff/controllers/main.py` (test import trực tiếp) + endpoint mỏng `GET /hocba-hrm/api/timeoff/burnout` gate bằng `canApprove`. Frontend: `BurnoutPanel.jsx` sao khung `LapsedPanel.jsx`; deep-link Lapsed→Approvals dùng pattern `focus` prop có sẵn trong `TimeOff.jsx`.

**Tech Stack:** Odoo 19 (custom-addons, KHÔNG sửa core), React 18 + Vite 6 (không TypeScript), Docker Postgres local để test.

**Spec:** `docs/superpowers/specs/2026-07-07-timeoff-burnout-dashboard-lapsed-link-design.md`

---

## Bối cảnh cho người không biết repo

- Controller Nghỉ phép: `custom-addons/hocba_timeoff/controllers/main.py`. Quy ước: logic nằm ở **hàm cấp module nhận `env`** (test gọi trực tiếp bằng `TransactionCase`), method trong class controller chỉ là lớp mỏng. Mẫu chuẩn để sao: `_lapsed_table` (dòng ~610) + `api_lapsed_dashboard` (dòng ~1912).
- Phân quyền: `_scope_for(env)` (dòng ~125) trả dict có `canApprove` (HR/Admin/HR User hoặc trưởng phòng), `seeAll`, `deptIds`. `_dept_domain(scope)` (dòng ~147) trả domain lọc phòng ban. Endpoint quản lý = sudo + lọc phòng ban tường minh.
- Model nguồn `hb.timeoff.burnout.line` (`models/hb_timeoff_burnout_line.py`) là SQL view `_auto=False`, `_order = 'burnout_risk desc, sick_leave_count_3m desc'`, đã có ACL trong `security/ir.model.access.csv` — **không sửa gì ở model/security**.
  - `risk_reason` chỉ trả 1 lý do chính, đúng 3 chuỗi: `'Nghỉ ốm thường xuyên (≥3 lần / 3 tháng)'`, `'Vắng nhiều (>10 ngày / 3 tháng)'`, `'Số dư nghỉ phép thấp (<2 ngày)'`.
- Test DB local có thể chứa dữ liệu demo → **không assert tổng tuyệt đối** trên bảng toàn cục; assert membership (NV X có/không có mặt) và KPI bằng `assertGreaterEqual`.
- Baseline test module hiện có **10 error pre-existing** ở `TestHandoverChain` (đã xác nhận từ Phase 12) — tiêu chí đạt là **không tăng số error/fail** so với baseline, và các test mới pass.
- Frontend không có test JS/eslint → verify tay. Build SPA: `cd frontend && npm run build` (output commit vào `custom-addons/hocba_hrm/static/spa/`).
- Commit: KHÔNG thêm `Co-Authored-By`. Giữ nguyên git identity.

## File Structure

| File | Vai trò |
|---|---|
| `custom-addons/hocba_timeoff/controllers/main.py` | Modify: thêm helper `_burnout_table` (sau `_post_lapsed_decision_note`, ~dòng 676) + endpoint `api_burnout` (sau `api_lapsed_dashboard`, ~dòng 1931) |
| `custom-addons/hocba_timeoff/tests/test_burnout.py` | Create: test helper + scope |
| `custom-addons/hocba_timeoff/tests/__init__.py` | Modify: import test mới |
| `frontend/src/api/timeoff.js` | Modify: thêm `fetchBurnout` |
| `frontend/src/features/timeoff/BurnoutPanel.jsx` | Create: panel tab "Sức khỏe NV" |
| `frontend/src/features/timeoff/TimeOff.jsx` | Modify: tab `health` + state `approvalFocus` + wire props |
| `frontend/src/features/timeoff/LapsedPanel.jsx` | Modify: prop `onOpenApproval`, nút link |
| `frontend/src/features/timeoff/ApprovalPanel.jsx` | Modify: props `focusRequestId`/`onFocusConsumed`, effect mở modal |

---

### Task 1: Helper `_burnout_table` (TDD backend)

**Files:**
- Test: `custom-addons/hocba_timeoff/tests/test_burnout.py` (create)
- Modify: `custom-addons/hocba_timeoff/tests/__init__.py`
- Modify: `custom-addons/hocba_timeoff/controllers/main.py`

- [ ] **Step 1: Viết test (đỏ)**

Tạo `custom-addons/hocba_timeoff/tests/test_burnout.py`:

```python
# ============================================================
# Test tab "Sức khỏe NV" — cảnh báo burnout (Widget 5-6 / BR-040).
# Spec: docs/superpowers/specs/2026-07-07-timeoff-burnout-dashboard-lapsed-link-design.md
# Gọi thẳng helper cấp module _burnout_table theo quy ước repo.
# View tính theo CURRENT_DATE (90 ngày gần nhất) → ngày test đặt động.
# DB test có thể chứa demo data → chỉ assert membership + KPI >=.
# Owner: Nhật Anh.
# ============================================================
from datetime import date, timedelta

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _burnout_table, _public_holiday_dates_env,
)


@tagged('post_install', '-at_install')
class TestTimeoffBurnout(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (burnout)'})
        self.dept_b = Dept.create({'name': 'Khối B (burnout)'})

        self.emp_mgr_a = self._mk_emp('TP A burnout', '150000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A burnout', '150000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV B burnout', '150000000003', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('burnout_mgr_a', self.emp_mgr_a)
        self.user_a = self._mk_user('burnout_nv_a', self.emp_a)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR burnout', 'login': 'burnout_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.sick = self.env.ref('hocba_timeoff.hb_leave_type_sick')
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')

    # ----- Helpers (mẫu test_lapsed.py) -----
    def _mk_emp(self, name, cccd, dept):
        # BR-010: NV official cần CCCD 12 số duy nhất.
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10],
        })

    def _mk_user(self, login, emp):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'tz': 'UTC',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        emp.user_id = user
        return user

    def _past_working_days(self, n):
        """n ngày LÀM VIỆC (T2–T6, trừ lễ đã seed) gần nhất TRƯỚC hôm nay,
        tăng dần — nằm gọn trong cửa sổ 90 ngày của view."""
        holidays = _public_holiday_dates_env(
            self.env, date.today() - timedelta(days=n * 3 + 30), date.today())
        days, cur = [], date.today() - timedelta(days=1)
        while len(days) < n:
            if cur.weekday() < 5 and cur not in holidays:
                days.append(cur)
            cur -= timedelta(days=1)
        return list(reversed(days))

    def _approved_leave(self, emp, d_from, d_to, leave_type):
        """Đơn nghỉ đã duyệt (state='validate') — view chỉ đếm đơn validate.
        Mẫu approve: tests/test_balances.py."""
        leave = self.env['hr.leave'].create({
            'name': 'Burnout test', 'employee_id': emp.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': d_from, 'request_date_to': d_to,
            'request_date_from_period': 'am',
            'request_date_to_period': 'pm',
        })
        leave.action_approve()
        if leave.state != 'validate':
            leave._action_validate()
        return leave

    def _table(self, user, dept_id=False):
        # View SQL đọc thẳng bảng → flush ORM trước khi query.
        self.env.flush_all()
        env = self.env(user=user)
        return _burnout_table(env, _scope_for(env), dept_id)

    def _find(self, table, emp):
        return next((r for r in table['items']
                     if r['employeeId'] == emp.id), None)

    # ----- Tests -----
    def test_sick_frequency_flagged(self):
        """BR-040 criterion 1: >=3 lần nghỉ ốm / 90 ngày → cảnh báo nhóm ốm."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)
        table = self._table(self.hr_user)
        row = self._find(table, self.emp_a)
        self.assertIsNotNone(row, 'NV nghỉ ốm 3 lần phải có trong bảng')
        self.assertEqual(row['sickCount3m'], 3)
        self.assertTrue(row['riskReason'].startswith('Nghỉ ốm'))
        self.assertGreaterEqual(table['kpi']['sickFreq'], 1)
        self.assertGreaterEqual(table['kpi']['total'], 1)

    def test_high_absence_flagged(self):
        """BR-040 criterion 2: vắng >10 ngày / 90 ngày → nhóm 'Vắng nhiều'.
        Dùng Không Lương (requires_allocation=False) để không dính quỹ."""
        days = self._past_working_days(11)
        self._approved_leave(self.emp_b, days[0], days[-1], self.unpaid)
        table = self._table(self.hr_user)
        row = self._find(table, self.emp_b)
        self.assertIsNotNone(row, 'NV vắng 11 ngày phải có trong bảng')
        self.assertGreater(row['absenceDays3m'], 10)
        self.assertTrue(row['riskReason'].startswith('Vắng'))
        self.assertGreaterEqual(table['kpi']['highAbsence'], 1)

    def test_normal_employee_not_listed(self):
        """NV không có đơn nào → không nằm trong bảng cảnh báo."""
        table = self._table(self.hr_user)
        self.assertIsNone(self._find(table, self.emp_a))
        self.assertIsNone(self._find(table, self.emp_mgr_a))

    def test_scope_dept_manager_sees_own_dept_only(self):
        """Trưởng phòng A thấy NV phòng A, KHÔNG thấy NV phòng B."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)   # Khối A
            self._approved_leave(self.emp_b, d, d, self.sick)   # Khối B
        table_hr = self._table(self.hr_user)
        self.assertIsNotNone(self._find(table_hr, self.emp_a))
        self.assertIsNotNone(self._find(table_hr, self.emp_b))
        table_mgr = self._table(self.mgr_a_user)
        self.assertIsNotNone(self._find(table_mgr, self.emp_a))
        self.assertIsNone(self._find(table_mgr, self.emp_b))

    def test_dept_filter_for_hr(self):
        """HR lọc dept → chỉ còn phòng đó (dept truyền vào helper)."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)
            self._approved_leave(self.emp_b, d, d, self.sick)
        table = self._table(self.hr_user, dept_id=self.dept_a.id)
        self.assertIsNotNone(self._find(table, self.emp_a))
        self.assertIsNone(self._find(table, self.emp_b))

    def test_regular_user_has_no_approve_scope(self):
        """User thường: canApprove=False → endpoint /burnout trả 403
        (gate nằm trong api_burnout, y hệt api_lapsed_dashboard)."""
        env_nv = self.env(user=self.user_a)
        self.assertFalse(_scope_for(env_nv)['canApprove'])
```

Thêm import vào `custom-addons/hocba_timeoff/tests/__init__.py` (giữ thứ tự alphabet nếu file đang theo alphabet):

```python
from . import test_burnout
```

- [ ] **Step 2: Chạy test — phải ĐỎ (ImportError)**

```bash
cd /Users/nguyenanh/odoo19 && docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestTimeoffBurnout --stop-after-init --log-level=test
```

Expected: FAIL/ERROR — `ImportError: cannot import name '_burnout_table'`.

- [ ] **Step 3: Viết helper (xanh tối thiểu)**

Trong `custom-addons/hocba_timeoff/controllers/main.py`, chèn **ngay sau hàm `_post_lapsed_decision_note`** (kết thúc ~dòng 676, trước comment block "Nghỉ phép giáo viên"):

```python
def _burnout_table(env, scope, dept_id=False):
    """Bảng cảnh báo burnout (Widget 5-6, BR-040): KPI theo nhóm lý do
    + bảng NV có cờ + đếm theo phòng. Đọc SQL view hb.timeoff.burnout.line
    (đã sắp burnout desc, sick desc). sudo + lọc phòng ban tường minh."""
    domain = [('burnout_risk', '=', True)] + _dept_domain(scope)
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    lines = env['hb.timeoff.burnout.line'].sudo().search(domain)

    items, by_dept = [], {}
    n_sick = n_absence = n_balance = 0
    for line in lines:
        reason = line.risk_reason or ''
        # view trả đúng 1 lý do chính/NV → 3 nhóm cộng lại = total
        if reason.startswith('Nghỉ ốm'):
            n_sick += 1
        elif reason.startswith('Vắng'):
            n_absence += 1
        else:
            n_balance += 1
        dept = line.department_id
        row = by_dept.setdefault(dept.id or 0, {
            'id': dept.id or False, 'name': dept.name or '—', 'count': 0})
        row['count'] += 1
        items.append({
            'employeeId': line.employee_id.id,
            'employee': line.employee_id.name,
            'departmentId': dept.id or False,
            'department': dept.name or '—',
            'sickCount3m': line.sick_leave_count_3m,
            'absenceDays3m': round(line.total_absence_days_3m, 2),
            'remainingBalance': round(line.remaining_leave_balance, 2),
            'riskReason': reason,
        })
    return {
        'kpi': {'total': len(items), 'sickFreq': n_sick,
                'highAbsence': n_absence, 'lowBalance': n_balance},
        'items': items,
        'byDepartment': sorted(by_dept.values(),
                               key=lambda r: r['count'], reverse=True),
    }
```

- [ ] **Step 4: Chạy lại test — phải XANH**

Cùng lệnh Step 2. Expected: `0 failed, 0 error(s) of 6 tests` (đúng 6 test của TestTimeoffBurnout).

- [ ] **Step 5: Commit**

```bash
cd /Users/nguyenanh/odoo19
git add custom-addons/hocba_timeoff/tests/test_burnout.py \
        custom-addons/hocba_timeoff/tests/__init__.py \
        custom-addons/hocba_timeoff/controllers/main.py
git commit -m "feat(timeoff): _burnout_table — dữ liệu tab 'Sức khỏe NV' (BR-040)"
```

---

### Task 2: Endpoint `GET /hocba-hrm/api/timeoff/burnout`

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py` (trong class controller, sau `api_lapsed_dashboard` ~dòng 1931)

- [ ] **Step 1: Thêm endpoint** (sao 1:1 gate/parse của `api_lapsed_dashboard` ngay phía trên):

```python
    # ------------------------------------------------------------------
    # 3.6c. GET /burnout — tab "Sức khỏe NV" (Widget 5-6, BR-040).
    # Chỉ officer; HR/Admin mọi phòng, Trưởng phòng phòng mình.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/burnout', auth='user',
                type='http', methods=['GET'])
    def api_burnout(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        data = _burnout_table(request.env, scope, dept_id)
        data.update({
            **self._scope_flags(scope),
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
        })
        return request.make_json_response(data)
```

- [ ] **Step 2: Chạy toàn bộ test burnout (regression nhanh)**

Cùng lệnh Task 1 Step 2. Expected: `0 failed, 0 error(s) of 6 tests`.

- [ ] **Step 3: Commit**

```bash
cd /Users/nguyenanh/odoo19
git add custom-addons/hocba_timeoff/controllers/main.py
git commit -m "feat(timeoff): API GET /burnout — tab 'Sức khỏe NV'"
```

---

### Task 3: SPA — `fetchBurnout` + `BurnoutPanel` + tab "Sức khỏe NV"

**Files:**
- Modify: `frontend/src/api/timeoff.js` (thêm cạnh `fetchLapsedDashboard`, ~dòng 191)
- Create: `frontend/src/features/timeoff/BurnoutPanel.jsx`
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`

- [ ] **Step 1: Thêm API client** — trong `frontend/src/api/timeoff.js`, ngay sau `fetchLapsedDashboard`:

```js
export const fetchBurnout = (dept) => {
  const p = new URLSearchParams();
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/burnout' + (q ? '?' + q : ''));
};
```

- [ ] **Step 2: Tạo `frontend/src/features/timeoff/BurnoutPanel.jsx`** (khung sao LapsedPanel):

```jsx
/* Tab "Sức khỏe NV" — cảnh báo burnout (Widget 5-6, BR-040). Chỉ officer
   (HR/Admin mọi phòng, Trưởng phòng phòng mình). Dữ liệu 90 ngày gần nhất.
   Spec: docs/superpowers/specs/2026-07-07-timeoff-burnout-dashboard-lapsed-link-design.md
   Owner: Nhật Anh. */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchBurnout } from '../../api/timeoff';

function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px', color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}

/* Màu badge theo nhóm lý do (khớp 3 chuỗi risk_reason của SQL view). */
const reasonKind = (reason) => (
  reason.startsWith('Nghỉ ốm') ? 'red'
    : reason.startsWith('Vắng') ? 'amber' : 'gray'
);

export default function BurnoutPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchBurnout(dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải cảnh báo sức khỏe nhân viên…" />;

  const k = data.kpi;
  const maxDept = Math.max(...data.byDepartment.map((r) => r.count), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {data.seeAll && (
        <div className="filterbar">
          <div style={{ marginLeft: 'auto' }}>
            <select className="sel" value={dept} onChange={(e) => setDept(e.target.value)}>
              <option value="">Mọi phòng ban</option>
              {data.allDepartments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        </div>
      )}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Tổng cảnh báo" value={k.total}
          color={k.total > 0 ? 'var(--red-600)' : 'var(--ink)'}
          sub="nhân viên trong diện theo dõi" />
        <Kpi label="Nghỉ ốm thường xuyên" value={k.sickFreq} color="var(--red-600)"
          sub="≥3 lần / 3 tháng" />
        <Kpi label="Vắng nhiều" value={k.highAbsence} color="var(--amber)"
          sub=">10 ngày / 3 tháng" />
        <Kpi label="Sắp cạn phép" value={k.lowBalance}
          sub="số dư < 2 ngày" />
      </div>

      {data.byDepartment.length > 0 && (
        <div className="card">
          <div className="card-head"><h3>Cảnh báo theo phòng ban</h3></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 13, padding: 16 }}>
            {data.byDepartment.map((r) => (
              <div key={r.id || r.name}>
                <div className="between" style={{ marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</span>
                  <span className="muted mono" style={{ fontSize: 12 }}>{r.count} NV</span>
                </div>
                <div className="bar">
                  <span style={{ width: (r.count / maxDept) * 100 + '%', background: 'var(--red-600)' }}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-head">
          <h3>Nhân viên trong diện cảnh báo</h3>
          <span className="sub">{data.items.length} nhân viên — dữ liệu 90 ngày gần nhất (BR-040)</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th>
              <th className="tbl-num">Nghỉ ốm (3 tháng)</th>
              <th className="tbl-num">Ngày vắng (3 tháng)</th>
              <th className="tbl-num">Số dư phép</th>
              <th>Lý do cảnh báo</th>
            </tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.employeeId}>
                  <td style={{ fontWeight: 600 }}>{r.employee}</td>
                  <td className="muted">{r.department}</td>
                  <td className="tbl-num mono">{r.sickCount3m} lần</td>
                  <td className="tbl-num mono">{r.absenceDays3m} ngày</td>
                  <td className="tbl-num mono">{r.remainingBalance} ngày</td>
                  <td style={{ overflow: 'visible', maxWidth: 'none', whiteSpace: 'nowrap' }}>
                    <Badge kind={reasonKind(r.riskReason)}>{r.riskReason}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.items.length === 0 && (
          <EmptyState>Không có nhân viên nào trong diện cảnh báo. 🎉</EmptyState>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Nối tab vào `frontend/src/features/timeoff/TimeOff.jsx`**

3a. Thêm import (cạnh `import LapsedPanel...`):

```js
import BurnoutPanel from './BurnoutPanel';
```

3b. Trong khối `if (data.isOfficer) { tabs.push(...) }` — thêm `['health', 'Sức khỏe NV']` ngay sau `['lapsed', 'Giám sát duyệt']`:

```js
    tabs.push(['overview', 'Tổng quan'], ['calendar', 'Lịch'],
              ['approvals', 'Chờ duyệt'], ['lapsed', 'Giám sát duyệt'],
              ['health', 'Sức khỏe NV'],
              ['approved', 'Đơn đã duyệt'],
              ['balances', 'Quỹ phép']);
```

3c. Thêm render ngay sau dòng `{activeTab === 'lapsed' && ...}`:

```jsx
      {activeTab === 'health' && data.isOfficer && <BurnoutPanel />}
```

- [ ] **Step 4: Build SPA**

```bash
cd /Users/nguyenanh/odoo19/frontend && npm run build
```

Expected: `✓ built in ...` không lỗi; output ghi vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 5: Commit**

```bash
cd /Users/nguyenanh/odoo19
git add frontend/src/api/timeoff.js frontend/src/features/timeoff/BurnoutPanel.jsx \
        frontend/src/features/timeoff/TimeOff.jsx custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-ui): tab 'Sức khỏe NV' — cảnh báo burnout (Widget 5-6)"
```

---

### Task 4: Link nhanh Lapsed → Chờ duyệt (mở thẳng modal)

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`
- Modify: `frontend/src/features/timeoff/LapsedPanel.jsx`
- Modify: `frontend/src/features/timeoff/ApprovalPanel.jsx`

- [ ] **Step 1: `TimeOff.jsx` — state + wire props**

1a. Thêm state (cạnh `const [historyReq, setHistoryReq] = useState(null);`):

```js
  const [approvalFocus, setApprovalFocus] = useState(null); // requestId từ tab Giám sát duyệt → mở modal ở tab Chờ duyệt
```

1b. Sửa render `ApprovalPanel` (hiện là `<ApprovalPanel isHrManager={data.isHrManager} />`):

```jsx
      {activeTab === 'approvals' && data.isOfficer && (
        <ApprovalPanel isHrManager={data.isHrManager}
          focusRequestId={approvalFocus}
          onFocusConsumed={() => setApprovalFocus(null)} />
      )}
```

1c. Sửa render `LapsedPanel` (hiện là `<LapsedPanel />`):

```jsx
      {activeTab === 'lapsed' && data.isOfficer && (
        <LapsedPanel onOpenApproval={(id) => { setApprovalFocus(id); setTab('approvals'); }} />
      )}
```

- [ ] **Step 2: `LapsedPanel.jsx` — prop + nút link**

2a. Đổi chữ ký component:

```js
export default function LapsedPanel({ onOpenApproval }) {
```

2b. Trong bảng chi tiết, thay nhánh không có đề xuất — hiện là:

```jsx
                    ) : (
                      <span className="muted" style={{ fontSize: 12 }}>xử lý ở tab Chờ duyệt</span>
                    )}
```

bằng:

```jsx
                    ) : (
                      <button className="btn btn-ghost btn-sm"
                        onClick={() => onOpenApproval && onOpenApproval(r.requestId)}>
                        Xử lý ở tab Chờ duyệt →
                      </button>
                    )}
```

- [ ] **Step 3: `ApprovalPanel.jsx` — nhận focus, tự mở modal**

3a. Đổi chữ ký component (hiện là `export default function ApprovalPanel({ isHrManager }) {`):

```js
export default function ApprovalPanel({ isHrManager, focusRequestId, onFocusConsumed }) {
```

3b. Thêm effect ngay sau `useEffect(load, []);`:

```jsx
  // Deep-link từ tab "Giám sát duyệt": mở thẳng modal xử lý của đơn được trỏ.
  // Tiêu thụ 1 lần (onFocusConsumed) — user đóng modal thì không tự mở lại;
  // đơn không còn trong danh sách (vừa được xử lý) → chỉ hiện tab, không modal.
  useEffect(() => {
    if (!data || !focusRequestId) return;
    const row = data.requests.find((r) => r.id === focusRequestId);
    if (row) {
      if (row.withdrawState === 'pending') setWithdrawDecision(row);
      else setDecision(row);
    }
    onFocusConsumed && onFocusConsumed();
  }, [data, focusRequestId]);
```

- [ ] **Step 4: Build SPA**

```bash
cd /Users/nguyenanh/odoo19/frontend && npm run build
```

Expected: build xanh.

- [ ] **Step 5: Commit**

```bash
cd /Users/nguyenanh/odoo19
git add frontend/src/features/timeoff/TimeOff.jsx \
        frontend/src/features/timeoff/LapsedPanel.jsx \
        frontend/src/features/timeoff/ApprovalPanel.jsx \
        custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-ui): link 'Xử lý ở tab Chờ duyệt' mở thẳng modal xử lý đơn"
```

---

### Task 5: Regression toàn module + upgrade Neon + verify tay

- [ ] **Step 1: Full test module (local Docker)**

```bash
cd /Users/nguyenanh/odoo19 && docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```

Expected: `0 failed, 10 error(s) of ~94 tests` — **đúng 10 error pre-existing của TestHandoverChain, KHÔNG tăng**; 6 test TestTimeoffBurnout pass.

- [ ] **Step 2: Upgrade module trên Neon (endpoint TRỰC TIẾP, bỏ `-pooler` trong HOST)**

```bash
cd /Users/nguyenanh/odoo19
# Lấy HOST hiện tại từ docker-compose.yml/.env, bỏ hậu tố -pooler rồi:
HOST=<neon-host-không-pooler> docker compose run --rm odoo \
  odoo -d neondb -u hocba_timeoff --addons-path=/mnt/extra-addons --stop-after-init
docker restart odoo19-odoo-1
```

Expected: log `Module hocba_timeoff loaded` không traceback (ERROR "Some modules are not loaded" của `hb_timeoff_*`/`hr_holidays_modern` legacy là vô hại đã biết).

- [ ] **Step 3: Verify tay trên app (tài khoản `hr.manager` / mật khẩu `hocba@123`, route `/hocba-hrm`)**

1. Tab **Sức khỏe NV** hiện sau "Giám sát duyệt": 4 KPI, bar phòng ban, bảng NV có badge lý do đúng màu (đỏ=ốm, amber=vắng, gray=dư thấp); lọc phòng ban hoạt động.
2. Đăng nhập trưởng phòng (`test_truongphong@hocba.vn` / `Hocba@2026`): tab chỉ hiện NV phòng mình, KHÔNG có dropdown lọc phòng.
3. Tài khoản NV thường (`nv.test`): không thấy tab (không phải officer).
4. Tab **Giám sát duyệt**: dòng "Xem tay" có nút "Xử lý ở tab Chờ duyệt →"; bấm → sang tab Chờ duyệt + DecisionModal mở đúng đơn (tên NV + khoảng ngày khớp).
5. Đóng modal → không tự mở lại; qua lại tab → không tự mở lại.
6. Dòng có đề xuất giữ nguyên nút "Xử lý theo đề xuất".

- [ ] **Step 4: Cập nhật docs nếu có seed dữ liệu test mới** (chỉ khi seed — cập nhật `docs/DB_TEST_DATA.md`).

---

## Self-review (đã chạy)

- **Spec coverage:** §2.2 helper+endpoint → Task 1-2; §2.3 FE → Task 3; §2.4 test (5 ý → 6 test, tách thêm dept-filter) → Task 1; §3 → Task 4; §5 triển khai → Task 5. Đủ.
- **Placeholder:** không còn TBD/TODO; mọi step có code/lệnh thật.
- **Type consistency:** `_burnout_table(env, scope, dept_id=False)` thống nhất Task 1/2; keys `sickCount3m/absenceDays3m/remainingBalance/riskReason` thống nhất helper↔test↔BurnoutPanel; `onOpenApproval`/`focusRequestId`/`onFocusConsumed` thống nhất 3 file Task 4; `r.requestId` (lapsed) vs `r.id` (approvals) dùng đúng chỗ.
