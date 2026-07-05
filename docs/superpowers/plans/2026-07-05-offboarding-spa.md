# Offboarding SPA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Giao diện SPA cho offboarding — NV nộp đơn nghỉ việc, officer duyệt 2 cấp — trên API đã có, mirror màn Nghỉ phép.

**Architecture:** Backend chỉ enrich JSON controller (`stateLabel/stateKind` + cờ `can*` + list `mine/managed` với scope gồm parent_id). FE thêm 1 nav item, 1 api client, 2 component (`Offboarding.jsx` tab theo `isOfficer`, `OffboardingForm.jsx` modal). Spec: `docs/superpowers/specs/2026-07-05-offboarding-spa-design.md`.

**Tech Stack:** Odoo 19 controller (Python) + React 18/Vite 6 (không TS, không test runner JS — verify bằng build + preview).

**Test env:** DB chung `hocba_hrm` hỏng bởi bug payroll (ngoài phạm vi). Backend test chạy DB `off_hrm`:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d off_hrm -u hocba_hrm --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm:TestOffboardingScope,/hocba_hrm:TestOffboardingApiJson --stop-after-init --log-level=test
```

---

## Task 1: API enrichment — `_offb_json` + list mine/managed + scope parent_id

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (block offboarding, ~dòng 2185-2262)
- Test: `custom-addons/hocba_hrm/tests/test_offboarding_api.py`

- [ ] **Step 1: Test đỏ** — thêm class vào `test_offboarding_api.py`:

```python
@tagged('post_install', '-at_install')
class TestOffboardingApiJson(TransactionCase):
    """Enrichment JSON + scope managed (gồm parent_id) cho SPA."""
    def setUp(self):
        super().setUp()
        from odoo.addons.hocba_hrm.controllers.main import HocBaHRM
        self.ctrl = HocBaHRM()
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Json', 'login': 'offj_hr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.mgr_user = self.env['res.users'].create({
            'name': 'ParentMgr', 'login': 'offj_pmgr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'ParentMgr Emp', 'identification_id': '015555550001',
            'user_id': self.mgr_user.id})
        self.staff_user = self.env['res.users'].create({
            'name': 'StaffJson', 'login': 'offj_staff',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.staff = self.env['hr.employee'].create({
            'name': 'StaffJson Emp', 'identification_id': '015555550002',
            'parent_id': self.mgr_emp.id, 'user_id': self.staff_user.id})
        self.rec = self.env['hocba.offboarding'].with_user(self.staff_user).create({
            'employee_id': self.staff.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        self.rec.action_submit()

    def _json(self, user):
        return self.ctrl._offb_json(self.rec.with_user(user).env['hocba.offboarding']
                                    .browse(self.rec.id))

    def test_json_state_label_and_flags_parent_mgr(self):
        d = self._json(self.mgr_user)
        self.assertEqual(d['stateLabel'], 'Chờ quản lý duyệt')
        self.assertEqual(d['stateKind'], 'amber')
        self.assertTrue(d['canMgrApprove'])
        self.assertFalse(d['canHrApprove'])
        self.assertTrue(d['canRefuse'])
        self.assertFalse(d['canCancel'])

    def test_json_flags_staff_own(self):
        d = self._json(self.staff_user)
        self.assertFalse(d['canMgrApprove'])
        self.assertTrue(d['canCancel'])  # submitted + own

    def test_json_flags_hr(self):
        self.rec.sudo().action_mgr_approve()
        d = self._json(self.hr_user)
        self.assertEqual(d['stateKind'], 'blue')
        self.assertTrue(d['canHrApprove'])
        self.assertTrue(d['canRefuse'])
        self.assertFalse(d['canMgrApprove'])

    def test_managed_scope_includes_parent_reports(self):
        ids = self.ctrl._offb_managed_employee_ids(
            self.env(user=self.mgr_user))
        self.assertIn(self.staff.id, ids)
        self.assertNotIn(self.mgr_emp.id, ids)
```
Lưu ý: `_offb_json` hiện nhận record; test gọi trực tiếp method của controller instance với record ở env của từng user (không cần HTTP request vì method chỉ đọc record + env.user của record.env).
**QUAN TRỌNG:** `_offb_json` mới phải lấy user từ `rec.env.user` (không phải `request.env`) để test được và để route dùng chung — trong route, record đã browse dưới `request.env` nên `rec.env.user` chính là user hiện tại.

- [ ] **Step 2: Chạy đỏ** — lệnh test ở header. Expected: FAIL (`stateLabel` KeyError / `_offb_managed_employee_ids` không tồn tại).

- [ ] **Step 3: Implement** — trong `main.py`, THAY `_offb_json` bằng bản enrich + thêm helper + sửa `api_offboarding_list`:

```python
    OFFB_STATE_UI = {
        'draft': ('Nháp', 'gray'),
        'submitted': ('Chờ quản lý duyệt', 'amber'),
        'mgr_approved': ('Chờ HR duyệt', 'blue'),
        'hr_approved': ('Chờ hoàn tất', 'violet'),
        'done': ('Đã nghỉ', 'gray'),
        'refused': ('Từ chối', 'red'),
        'cancelled': ('Đã huỷ', 'gray'),
    }

    def _offb_json(self, rec):
        user = rec.env.user
        is_hr_mgr = rec.env.su or user.has_group('hr.group_hr_manager')
        try:
            rec._ensure_manages()
            manages = True
        except AccessError:
            manages = False
        own = rec.employee_id == user.employee_id
        label, kind = self.OFFB_STATE_UI.get(rec.state, (rec.state, 'gray'))
        return {
            'id': rec.id, 'name': rec.name,
            'employeeId': rec.employee_id.id,
            'employeeName': rec.employee_id.name,
            'source': rec.source, 'reasonType': rec.reason_type,
            'reason': rec.reason or '',
            'requestDate': rec.request_date and str(rec.request_date) or '',
            'expectedLeaveDate': rec.expected_leave_date
                and str(rec.expected_leave_date) or '',
            'state': rec.state, 'stateLabel': label, 'stateKind': kind,
            'assetPending': rec.asset_pending_count,
            'mgrApprovedBy': rec.mgr_approved_by.name or '',
            'hrApprovedBy': rec.hr_approved_by.name or '',
            'canMgrApprove': rec.state == 'submitted' and manages,
            'canHrApprove': rec.state == 'mgr_approved' and is_hr_mgr,
            'canDone': rec.state == 'hr_approved' and is_hr_mgr,
            'canRefuse': (rec.state == 'submitted' and manages)
                or (rec.state == 'mgr_approved' and is_hr_mgr),
            'canCancel': rec.state in ('draft', 'submitted')
                and (own or is_hr_mgr),
        }

    def _offb_managed_employee_ids(self, env):
        """Phạm vi NV mà user hiện tại được xử lý đơn nghỉ việc — KHỚP quyền
        duyệt của model (_ensure_manages): HR=tất cả; trưởng phòng=phòng mình;
        quản lý trực tiếp=cấp dưới parent_id; giáo vụ=giáo viên.
        Không dùng _emp_scope_domain (helper chung, thiếu parent_id)."""
        user = env.user
        Emp = env['hr.employee'].sudo()
        if (user.has_group('base.group_system')
                or user.has_group('hr.group_hr_user')
                or user.has_group('hr.group_hr_manager')):
            return Emp.search([]).ids
        ids = set()
        emp = user.employee_id
        dept_ids = _managed_department_ids(env, emp)
        if dept_ids:
            ids.update(Emp.search([('department_id', 'in', dept_ids)]).ids)
        if emp:
            ids.update(Emp.search([('parent_id', '=', emp.id)]).ids)
        if user.has_group('hocba_employees.group_hocba_giaovu'):
            ids.update(Emp.search(
                [('x_employee_type_id.code', '=', 'teacher')]).ids)
        ids.discard(emp.id if emp else -1)
        return list(ids)
```
Và THAY `api_offboarding_list` bằng:
```python
    @http.route('/hocba-hrm/api/offboarding/list', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_offboarding_list(self, **kw):
        env = request.env
        Off = env['hocba.offboarding'].sudo()
        is_officer = _user_can_manage(env)
        emp = env.user.employee_id
        mine = Off.search([('employee_id', '=', emp.id if emp else -1)])
        managed = Off.browse()
        if is_officer:
            managed = Off.search([
                ('employee_id', 'in', self._offb_managed_employee_ids(env))])
        # _offb_json đọc quyền từ rec.env.user → re-browse dưới env user thật
        to_user = lambda recs: env['hocba.offboarding'].sudo(False).browse(recs.ids)
        return request.make_json_response({
            'isOfficer': is_officer,
            'isEmployee': bool(emp) and not is_officer,
            'mine': [self._offb_json(r) for r in to_user(mine)],
            'managed': [self._offb_json(r) for r in to_user(managed)],
        })
```
Ghi chú: `sudo(False)` đưa record về user thật để cờ can* tính đúng; record rule vẫn cho đọc vì mine=của mình, managed=phạm vi rule (dept/parent/teacher/HR) — nếu 1 bản ghi managed nằm ngoài record rule của user (không xảy ra vì scope đã khớp rule), `_offb_json` đọc field sẽ AccessError → coi đó là bug scope, phải sửa scope chứ không sudo.

- [ ] **Step 4: Chạy xanh** — lệnh test header. Expected: `0 failed, 0 error(s)` cho 2 class TestOffboarding*.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_offboarding_api.py
git commit -m "feat(offboarding): enrich API JSON (stateLabel/can*) + list mine/managed gồm parent_id"
```

## Task 2: FE — api client + nav + route

**Files:**
- Create: `frontend/src/api/offboarding.js`
- Modify: `frontend/src/app/Shell.jsx` (NAV + PAGE_META)
- Modify: `frontend/src/app/App.jsx` (import + route)

- [ ] **Step 1: api client** — tạo `frontend/src/api/offboarding.js`:
```javascript
/* API domain Nghỉ việc (offboarding) — Vu/Tan.
   Spec: docs/superpowers/specs/2026-07-05-offboarding-spa-design.md */
import { hbGet, hbPost } from './client';

/* { isOfficer, isEmployee, mine:[...], managed:[...] } */
export const fetchOffboarding = () => hbGet('/hocba-hrm/api/offboarding/list');

/* NV tự nộp đơn. payload: { reasonType, reason, expectedLeaveDate } */
export const submitOffboarding = (payload) =>
  hbPost('/hocba-hrm/api/offboarding/submit', payload);

/* action ∈ mgr_approve | hr_approve | done | refuse | cancel */
export const offboardingAction = (id, action) =>
  hbPost('/hocba-hrm/api/offboarding/action', { id, action });
```

- [ ] **Step 2: Shell.jsx** — thêm vào NAV nhóm "Quản lý nhân sự" (sau dòng timeoff `need:'manage'`... thực tế nhóm manage: sau item `timeoff`):
```javascript
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'manage' },
```
và nhóm "Cá nhân" (sau item timeoff `need:'self'`):
```javascript
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'self' },
```
PAGE_META thêm:
```javascript
  offboarding: { t: 'Nghỉ việc', c: 'Nhân sự / Offboarding' },
```

- [ ] **Step 3: App.jsx** — import `Offboarding from '../features/offboarding/Offboarding'` và route sau dòng timeoff:
```javascript
        {view === 'offboarding' && <Offboarding search={search} />}
```
(Component tạo ở Task 3 — build sẽ fail tới khi Task 3 xong; làm Task 2+3 rồi build 1 lần.)

## Task 3: FE — Offboarding.jsx + OffboardingForm.jsx + build

**Files:**
- Create: `frontend/src/features/offboarding/Offboarding.jsx`
- Create: `frontend/src/features/offboarding/OffboardingForm.jsx`

- [ ] **Step 1: Offboarding.jsx** (component chính — tab theo isOfficer, bảng + thao tác):
```javascript
/* ============================================================
   Màn Nghỉ việc (Offboarding) — self-service + duyệt 2 cấp.
   Owner: Vu/Tan. Spec: docs/superpowers/specs/2026-07-05-offboarding-spa-design.md
   Mirror cấu trúc màn Nghỉ phép (timeoff).
   ============================================================ */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchOffboarding, offboardingAction } from '../../api/offboarding';
import OffboardingForm from './OffboardingForm';

const REASON_LABEL = {
  voluntary: 'Tự nguyện', performance: 'Không đạt',
  contract_end: 'Hết hạn HĐ', other: 'Khác',
};

export default function Offboarding({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null); // id đơn đang thao tác
  const [detail, setDetail] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchOffboarding().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nghỉ việc…" />;

  const act = (row, action, confirmMsg) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    setBusy(row.id);
    offboardingAction(row.id, action)
      .then(load)
      .catch((e) => alert('Không thực hiện được: ' + e.message))
      .finally(() => setBusy(null));
  };

  const q = (search || '').toLowerCase();
  const match = (r) => !q || (r.employeeName || '').toLowerCase().includes(q)
    || (r.name || '').toLowerCase().includes(q)
    || (r.reason || '').toLowerCase().includes(q);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nghỉ việc</h1>
          <p>Đơn thôi việc &amp; phê duyệt 2 cấp · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          {data.isEmployee && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Nộp đơn nghỉ</button>
          )}
        </div>
      </div>

      {data.isOfficer
        ? <ManagedTable rows={data.managed.filter(match)} busy={busy} act={act} />
        : <MineTable rows={data.mine.filter(match)} busy={busy} act={act}
            onOpen={setDetail} />}

      {creating && (
        <OffboardingForm onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
      {detail && <DetailModal row={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

/* ---- Tab officer: mọi đơn trong phạm vi, thao tác theo cờ can* ---- */
function ManagedTable({ rows, busy, act }) {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc — chờ xử lý</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Mã đơn</th><th>Nhân viên</th><th>Loại lý do</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</th>
            <th className="tbl-num" style={{ width: '1%', whiteSpace: 'nowrap' }}>Tài sản</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => <ManagedRow key={r.id} r={r} busy={busy} act={act} />)}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <EmptyState>Không có đơn nghỉ việc nào trong phạm vi của bạn.</EmptyState>}
    </div>
  );
}

function ManagedRow({ r, busy, act }) {
  const b = busy === r.id;
  const doneBlocked = r.canDone && r.assetPending > 0;
  return (
    <tr>
      <td className="mono" style={{ fontWeight: 600 }}>{r.name}</td>
      <td style={{ fontWeight: 600 }}>{r.employeeName}</td>
      <td>{REASON_LABEL[r.reasonType] || r.reasonType}</td>
      <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.requestDate)}</td>
      <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.expectedLeaveDate)}</td>
      <td className="tbl-num mono" style={{ fontWeight: 600 }}>
        {r.assetPending > 0
          ? <Badge kind="amber">{r.assetPending} chưa thu</Badge> : '0'}
      </td>
      <td style={{ whiteSpace: 'nowrap' }}><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
      <td style={{ whiteSpace: 'nowrap' }}>
        {r.canMgrApprove && (
          <button className="btn btn-primary btn-sm" disabled={b}
            onClick={() => act(r, 'mgr_approve')}>Quản lý duyệt</button>
        )}
        {r.canHrApprove && (
          <button className="btn btn-primary btn-sm" disabled={b}
            onClick={() => act(r, 'hr_approve')}>HR duyệt</button>
        )}
        {r.canDone && (
          <button className="btn btn-primary btn-sm" disabled={b || doneBlocked}
            title={doneBlocked ? `Còn ${r.assetPending} tài sản chưa thu hồi` : undefined}
            onClick={() => act(r, 'done',
              'Hoàn tất nghỉ việc? Hồ sơ sẽ lưu trữ và khoá tài khoản đăng nhập.')}>
            Hoàn tất</button>
        )}
        {r.canRefuse && (
          <button className="btn btn-ghost btn-sm" disabled={b}
            onClick={() => act(r, 'refuse', 'Từ chối đơn nghỉ việc này?')}>Từ chối</button>
        )}
      </td>
    </tr>
  );
}

/* ---- Tab nhân viên: đơn của tôi ---- */
function MineTable({ rows, busy, act, onOpen }) {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc của tôi</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Mã đơn</th><th>Loại lý do</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} onClick={() => onOpen(r)} style={{ cursor: 'pointer' }}>
                <td className="mono" style={{ fontWeight: 600 }}>{r.name}</td>
                <td>{REASON_LABEL[r.reasonType] || r.reasonType}</td>
                <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.requestDate)}</td>
                <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.expectedLeaveDate)}</td>
                <td style={{ whiteSpace: 'nowrap' }}><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  {r.canCancel && (
                    <button className="btn btn-ghost btn-sm" disabled={busy === r.id}
                      onClick={(e) => { e.stopPropagation(); act(r, 'cancel', 'Huỷ đơn nghỉ việc này?'); }}>
                      {busy === r.id ? 'Đang huỷ…' : 'Huỷ'}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <EmptyState>Chưa có đơn nghỉ việc nào.</EmptyState>}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      <span style={{ fontSize: 13.5, color: 'var(--ink)', whiteSpace: 'pre-wrap' }}>{value}</span>
    </div>
  );
}

function DetailModal({ row, onClose }) {
  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="logout" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{row.name}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Chi tiết đơn nghỉ việc</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '18px 24px', display: 'grid', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="muted" style={{ fontSize: 12.5 }}>Trạng thái</span>
          <Badge kind={row.stateKind} dot>{row.stateLabel}</Badge>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
          <Field label="Loại lý do" value={REASON_LABEL[row.reasonType] || row.reasonType} />
          <Field label="Ngày nộp đơn" value={fmtDate(row.requestDate)} />
          <Field label="Ngày nghỉ dự kiến" value={fmtDate(row.expectedLeaveDate)} />
          <Field label="Quản lý duyệt" value={row.mgrApprovedBy || '—'} />
          <Field label="HR duyệt" value={row.hrApprovedBy || '—'} />
        </div>
        <Field label="Lý do chi tiết" value={row.reason || '—'} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: OffboardingForm.jsx** (modal nộp đơn — pattern WithdrawModal):
```javascript
/* Modal nộp đơn nghỉ việc (self-service). */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { submitOffboarding } from '../../api/offboarding';

const REASONS = [
  ['voluntary', 'Tự nguyện'],
  ['contract_end', 'Hết hạn hợp đồng'],
  ['other', 'Khác'],
];

const plus30 = () => {
  const d = new Date(); d.setDate(d.getDate() + 30);
  return d.toISOString().slice(0, 10);
};

const inputStyle = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function L({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

export default function OffboardingForm({ onClose, onSaved }) {
  const [reasonType, setReasonType] = useState('voluntary');
  const [reason, setReason] = useState('');
  const [leaveDate, setLeaveDate] = useState(plus30);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = () => {
    const r = reason.trim();
    if (!r) { setErr('Vui lòng nhập lý do chi tiết.'); return; }
    if (!leaveDate) { setErr('Vui lòng chọn ngày nghỉ dự kiến.'); return; }
    setBusy(true); setErr(null);
    submitOffboarding({ reasonType, reason: r, expectedLeaveDate: leaveDate })
      .then(onSaved)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="logout" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Nộp đơn nghỉ việc</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            Đơn sẽ qua 2 cấp duyệt: quản lý trực tiếp → HR
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <L label="Loại lý do *">
          <select style={inputStyle} value={reasonType}
            onChange={(e) => setReasonType(e.target.value)}>
            {REASONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </L>
        <L label="Lý do chi tiết *">
          <textarea rows={3} style={{ ...inputStyle, resize: 'vertical' }}
            value={reason} onChange={(e) => setReason(e.target.value)}
            placeholder="VD: Chuyển nơi ở, định hướng nghề nghiệp mới…" />
        </L>
        <L label="Ngày nghỉ dự kiến *">
          <input type="date" style={inputStyle} value={leaveDate}
            onChange={(e) => setLeaveDate(e.target.value)} />
        </L>
        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Đang gửi…' : 'Nộp đơn'}
        </button>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 3: Build**
Run: `cd frontend && npm run build`
Expected: build OK, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 4: Commit (source + artifacts)**
```bash
git add frontend/src custom-addons/hocba_hrm/static/spa
git commit -m "feat(offboarding): SPA màn Nghỉ việc — nộp đơn + duyệt 2 cấp (mirror timeoff)"
```

## Task 4: Verify E2E (preview) + finish

- [ ] **Step 1:** Khởi động Odoo DB `off_hrm` (compose run --service-ports) + preview proxy 8169.
- [ ] **Step 2:** Kịch bản: tạo user NV thường + gắn employee (RPC); đăng nhập SPA `/hocba-hrm` → "Nghỉ việc" → nộp đơn; đăng nhập admin/officer → duyệt QL → duyệt HR → Hoàn tất; xác nhận list cập nhật + NV resigned. Chụp screenshot làm bằng chứng.
- [ ] **Step 3:** Chạy lại test backend cả 2 module (off_test + off_hrm TestOffboarding*) — `0 failed`.
- [ ] **Step 4:** finishing-a-development-branch → merge FF về main (nhánh đã chứa main), gỡ chip follow-up parent_id (đã fix trong Task 1).

## Self-review
- Spec §2 → Task 1; §3 → Task 2; §4 → Task 3; §5 → Task 3 Step 3-4 + Task 4. Đủ.
- Naming nhất quán: `_offb_managed_employee_ids`, `fetchOffboarding/submitOffboarding/offboardingAction`, cờ can* trùng giữa BE/FE.
- `fmtDate` + `Badge`/`Modal`/`states` là component sẵn có (đã thấy dùng trong TimeOff.jsx).
