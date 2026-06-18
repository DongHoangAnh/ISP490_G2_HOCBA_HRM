# Gói 4B — Check-in theo ca (cửa sổ ±15') Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Cho CTV/OT (non-official) check-in/out chỉ khi có ca `hocba.work_shift` approved hôm nay và trong cửa sổ ±15' quanh giờ ca; NV official giữ nguyên cơ chế workday Gói 2.

**Architecture:** Thêm `shift_window_minutes` vào policy; thêm `_todays_approved_shifts` + `_assert_shift_check_allowed` trên model `hocba.attendance`; phân nhánh `api_attendance_check` (official → `_assert_check_allowed`; non-official → `_assert_shift_check_allowed`) bỏ block `not_official`; lộ `shiftToday` qua `_att_me_info`; CheckInPanel xử lý CTV/OT.

**Tech Stack:** Odoo 19 (Python), TransactionCase; React/Vite SPA.

**Spec:** [docs/superpowers/specs/2026-06-18-shift-checkin-window-design.md](../specs/2026-06-18-shift-checkin-window-design.md)

---

## Lệnh test & build (như các gói trước)

`MSYS_NO_PATHCONV=1` BẮT BUỘC trên Git Bash Windows. Xác nhận `0 failed, 0 error(s) of N tests`, N>0. Bash timeout 480000ms.
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
# Build SPA: cd frontend && npm install && npm run build
```
Bỏ qua ERROR pre-existing `hb_timeoff_*`/`hr_holidays_modern`.

---

## Task 1: Policy — field `shift_window_minutes` + view

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`
- Modify: `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml`

- [ ] **Step 1: Thêm field.** Trong `hocba_attendance_policy.py`, sau field `violation_free_days` (cuối nhóm "Tính công Gói 1"), thêm:
```python
    shift_window_minutes = fields.Integer(
        string='Cửa sổ check-in ca (phút)', default=15,
        help='CTV/OT được check-in/out trong ±N phút quanh giờ ca đã duyệt.')
```

- [ ] **Step 2: Thêm vào view.** Đọc `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml`, tìm nơi đặt các field Gói 1 (`late_cutoff`, `std_work_hours`, `violation_free_days`...). Thêm `<field name="shift_window_minutes"/>` cạnh chúng (cùng group/page). Nếu không tìm thấy group phù hợp, thêm vào cùng `<group>` chứa `violation_free_days`.

- [ ] **Step 3: Sync schema.** Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance --addons-path=/mnt/extra-addons --stop-after-init --log-level=warn
```
Expected: load sạch (không ParseError ở view, không lỗi field).

- [ ] **Step 4: Commit.**
```bash
git add custom-addons/hocba_attendance/models/hocba_attendance_policy.py custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml
git commit -m "feat(attendance): policy.shift_window_minutes (mặc định 15) (Gói 4B)"
```

---

## Task 2: Model — `_todays_approved_shifts` + `_assert_shift_check_allowed` (TDD)

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_checkin.py` (tạo mới)
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Đăng ký test module.** Trong `custom-addons/hocba_hrm/tests/__init__.py` thêm dòng:
```python
from . import test_shift_checkin
```

- [ ] **Step 2: Viết test thất bại.** Create `custom-addons/hocba_hrm/tests/test_shift_checkin.py`:
```python
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestShiftCheckin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({'shift_window_minutes': 15,
                           'office_lat': 0.0, 'office_lng': 0.0})
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV Ca', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV Ca User', 'login': 'ctv_ca_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        self.Att = self.env['hocba.attendance']
        self.WS = self.env['hocba.work_shift']

    def _shift(self, start, end, state='approved'):
        return self.WS.sudo().create({
            'employee_id': self.emp.id, 'start': start, 'end': end,
            'shift_type': 'ot', 'state': state})

    def _att(self, **vals):
        v = {'employee_id': self.emp.id}
        v.update(vals)
        return self.Att.sudo().create(v)

    def test_todays_approved_shifts_filters(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=1))
        self._shift(now + timedelta(days=2), now + timedelta(days=2, hours=1))  # khác ngày
        today = fields.Datetime.context_timestamp(
            self.env(user=self.user).user, now).date()
        env = self.env(user=self.user)
        found = env['hocba.attendance']._todays_approved_shifts(self.emp, today)
        self.assertEqual(len(found), 1)

    def test_checkin_within_window_ok(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=2))
        env = self.env(user=self.user)
        # không raise
        env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')

    def test_no_shift_today_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'no_shift_today')

    def test_outside_window_raises(self):
        now = fields.Datetime.now()
        self._shift(now + timedelta(hours=3), now + timedelta(hours=5))
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'outside_shift_window')

    def test_pending_shift_not_counted(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=1), state='pending')
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'no_shift_today')

    def test_already_checked_in_raises(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=2))
        self._att(check_in=now)
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'in')
        self.assertEqual(str(e.exception), 'already_checked_in')

    def test_checkout_not_checked_in_raises(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(hours=2), now + timedelta(minutes=5))  # end gần now
        env = self.env(user=self.user)
        with self.assertRaises(UserError) as e:
            env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'out')
        self.assertEqual(str(e.exception), 'not_checked_in')

    def test_checkout_within_window_ok(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(hours=2), now + timedelta(minutes=5))
        self._att(check_in=now - timedelta(hours=2))
        env = self.env(user=self.user)
        env['hocba.attendance'].sudo()._assert_shift_check_allowed(self.emp, 'out')
```

- [ ] **Step 3: Chạy test — FAIL** (`AttributeError: ... _assert_shift_check_allowed` hoặc `_todays_approved_shifts`). Run lệnh test. Confirm N>0.

- [ ] **Step 4: Implement.** Trong `custom-addons/hocba_attendance/models/hr_attendance.py`, thêm 2 method ngay SAU `_assert_check_allowed` (kết thúc trước `action_check_in`):
```python
    def _todays_approved_shifts(self, employee, today):
        """Ca approved của employee có start rơi vào ngày local `today`."""
        shifts = self.env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'approved')])
        return shifts.filtered(
            lambda s: fields.Datetime.context_timestamp(s, s.start).date() == today)

    def _assert_shift_check_allowed(self, employee, kind):
        """CTV/OT (non-official): check-in/out theo ca approved + cửa sổ ±W phút.
        Raise UserError mã lỗi: no_shift_today / outside_shift_window /
        already_checked_in / not_checked_in / already_checked_out."""
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        window = policy.shift_window_minutes or 15
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'),
            fields.Datetime.now()).replace(tzinfo=None)
        today = now_local.date()
        shifts = self._todays_approved_shifts(employee, today)
        if not shifts:
            raise UserError('no_shift_today')
        in_window = False
        for s in shifts:
            anchor_utc = s.start if kind == 'in' else s.end
            anchor = fields.Datetime.context_timestamp(
                s, anchor_utc).replace(tzinfo=None)
            if abs((now_local - anchor).total_seconds()) <= window * 60:
                in_window = True
                break
        if not in_window:
            raise UserError('outside_shift_window')
        rec = self.sudo().search([
            ('employee_id', '=', employee.id), ('date', '=', today)], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')
```
`fields`, `UserError`, `timedelta` đã import sẵn ở đầu `hr_attendance.py`. `hocba.work_shift` truy cập qua `self.env[...]`. Đừng sửa `_assert_check_allowed`/`_do_check`.

- [ ] **Step 5: Chạy test — 8 test PASS.** Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 6: Commit.**
```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py custom-addons/hocba_hrm/tests/test_shift_checkin.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance): _assert_shift_check_allowed — check-in cửa sổ ca (Gói 4B)"
```

---

## Task 3: Controller — phân nhánh `api_attendance_check` + map lỗi

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

> Wiring; xác nhận bằng chạy lại toàn bộ suite không vỡ.

- [ ] **Step 1: Thêm mã lỗi.** Trong `custom-addons/hocba_hrm/controllers/main.py`, tìm dict `_CHECK_ERR_STATUS` (module-level) và thêm 2 mục:
```python
_CHECK_ERR_STATUS = {
    'not_workday': 403,
    'already_checked_in': 409,
    'not_checked_in': 409,
    'already_checked_out': 409,
    'no_shift_today': 403,
    'outside_shift_window': 403,
}
```
(Giữ các mục cũ; chỉ thêm 2 dòng `no_shift_today`/`outside_shift_window`.)

- [ ] **Step 2: Phân nhánh `api_attendance_check`.** Tìm method `api_attendance_check` trong class `HocBaHRM`. Thay TOÀN BỘ thân method (từ `emp = request.env.user.employee_id` đến hết) bằng:
```python
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if _user_can_manage(request.env):
            return request.make_json_response(
                {'error': 'manager_no_checkin'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        Att = request.env['hocba.attendance'].sudo()
        try:
            if emp.x_employment_status == 'official':
                Att._assert_check_allowed(emp, kind)
            else:
                Att._assert_shift_check_allowed(emp, kind)
            res = Att._do_check({
                'employee_id': emp.id,
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
            }, kind)
        except UserError as ex:
            code = str(ex)
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': code}, status=_CHECK_ERR_STATUS.get(code, 400))
        return request.make_json_response({
            'recordId': res['record_id'], 'kind': res['kind'],
            'faceSuspect': res['face_suspect'], 'outOfZone': res['out_of_zone'],
            'outOfWindow': res['out_of_window'], 'faceScore': res['face_score'],
        })
```
Đây thay nhánh `if emp.x_employment_status != 'official': return not_official` bằng phân luồng official↔non-official, và gọi trực tiếp `_assert_* + _do_check` (thay vì `action_check_in/out`) để phân luồng mà không nhân đôi logic. `UserError` đã import sẵn. KHÔNG đụng các method khác.

- [ ] **Step 3: Chạy lại toàn bộ suite — không vỡ.** Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 4: Commit.**
```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(attendance-api): check-in phân nhánh official/ca CTV-OT, bỏ not_official (Gói 4B)"
```

---

## Task 4: `_att_me_info.shiftToday` (TDD)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_checkin.py`

- [ ] **Step 1: Viết test thất bại.** Thêm vào class `TestShiftCheckin` (import `_att_me_info` ở đầu file: thêm `from odoo.addons.hocba_hrm.controllers.main import _att_me_info`):
```python
    def test_me_info_shift_today_for_ctv(self):
        now = fields.Datetime.now()
        self._shift(now - timedelta(minutes=5), now + timedelta(hours=2))
        info = _att_me_info(self.env(user=self.user))
        self.assertFalse(info['isOfficial'])
        self.assertIsNotNone(info['shiftToday'])
        self.assertTrue(info['shiftToday']['checkInOpen'])
        self.assertEqual(info['shiftToday']['shiftType'], 'ot')

    def test_me_info_shift_today_none_when_no_shift(self):
        info = _att_me_info(self.env(user=self.user))
        self.assertIsNone(info['shiftToday'])
```

- [ ] **Step 2: Chạy test — FAIL** (`KeyError: 'shiftToday'`). Run lệnh test.

- [ ] **Step 3: Implement.** Trong `_att_me_info(env)` (controller), TRƯỚC `return info`, thêm:
```python
    info['shiftToday'] = None
    if not info['isOfficial']:
        window = policy.shift_window_minutes or 15
        now_local = fields.Datetime.context_timestamp(
            env.user, fields.Datetime.now()).replace(tzinfo=None)
        shifts = env['hocba.attendance']._todays_approved_shifts(
            emp, now_local.date())
        if shifts:
            s = shifts[0]
            ci = fields.Datetime.context_timestamp(s, s.start).replace(tzinfo=None)
            co = fields.Datetime.context_timestamp(s, s.end).replace(tzinfo=None)
            info['shiftToday'] = {
                'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
                'shiftType': s.shift_type, 'rate': s.rate,
                'checkInOpen': abs((now_local - ci).total_seconds()) <= window * 60,
                'checkOutOpen': abs((now_local - co).total_seconds()) <= window * 60,
            }
```
`policy` và `emp` đã có sẵn trong `_att_me_info` (đọc lại hàm để chắc tên biến: `emp = env.user.employee_id`, `policy = env['hocba.attendance.policy'].sudo().get_policy()`). `_dt_local`/`_todays_approved_shifts` tái dùng. KHÔNG đổi phần còn lại của info.

- [ ] **Step 4: Chạy test — 2 test PASS + suite xanh.** Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 5: Commit.**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_checkin.py
git commit -m "feat(attendance-api): _att_me_info.shiftToday cho CTV/OT (Gói 4B)"
```

---

## Task 5: Frontend — CheckInPanel cho CTV/OT + build

**Files:**
- Modify: `frontend/src/features/attendance/CheckInPanel.jsx`

- [ ] **Step 1: READ** `frontend/src/features/attendance/CheckInPanel.jsx` đầy đủ.

- [ ] **Step 2: Map mã lỗi mới.** Trong hàm `doCheck`, dict `M` (map mã lỗi → message) thêm 2 dòng:
```javascript
        no_shift_today: 'Chưa có ca được duyệt hôm nay.',
        outside_shift_window: 'Ngoài cửa sổ check-in của ca (±15 phút).',
```

- [ ] **Step 3: Thay nhánh chặn non-official.** Khối hiện tại bắt đầu bằng `{!me.isOfficial ? (<div className="empty">Chức năng điểm danh chỉ áp dụng cho nhân viên chính thức.</div>) : !enrolled ? (...) : !me.isWorkdayToday ? (...) : (...check-in/out official...)}`.

Thay nhánh `{!me.isOfficial ? (` (chỉ phần hiển thị khi non-official) bằng một nhánh render check-in theo ca. Cấu trúc mới (giữ nguyên các nhánh official phía sau):
```jsx
        {!me.isOfficial ? (
          !enrolled ? (
            <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
              <Icon name="user" size={16} />Đăng ký khuôn mặt
            </button>
          ) : !me.shiftToday ? (
            <div className="empty">Chưa có ca làm việc được duyệt hôm nay.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="muted" style={{ fontSize: 12.5 }}>
                Ca: <b className="mono">{fmtTime(me.shiftToday.start)}–{fmtTime(me.shiftToday.end)}</b>
                {' '}· {me.shiftToday.shiftType === 'ctv' ? 'CTV' : 'OT'} ×{me.shiftToday.rate}
                {' '}· cửa sổ ±15'
              </div>
              {t && t.checkIn ? (
                <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                  <Icon name="checkCircle" size={15} /> Đã check-in lúc {fmtTime(t.checkIn)}
                </div>
              ) : (
                <button className="btn btn-primary" disabled={busy || !ready || !me.shiftToday.checkInOpen} onClick={() => doCheck('in')}>
                  <Icon name="checkCircle" size={16} />Check-in
                </button>
              )}
              {t && t.checkOut ? (
                <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                  <Icon name="logout" size={15} /> Đã check-out lúc {fmtTime(t.checkOut)}
                </div>
              ) : (
                <button className="btn btn-ghost" disabled={busy || !ready || !(t && t.checkIn) || !me.shiftToday.checkOutOpen} onClick={() => doCheck('out')}>
                  <Icon name="logout" size={16} />Check-out
                </button>
              )}
            </div>
          )
        ) : !enrolled ? (
```
Tức là: nhánh `!me.isOfficial` giờ render block trên; phần `: !enrolled ? (` còn lại GIỮ NGUYÊN cho official (nó nối tiếp ternary). Đảm bảo cấu trúc ternary lồng vẫn hợp lệ: `{!me.isOfficial ? ( <CTV block> ) : !enrolled ? ( <enroll official> ) : !me.isWorkdayToday ? ( <empty> ) : ( <official check-in/out> )}`.

- [ ] **Step 4: Build SPA.** Run:
```bash
cd frontend && npm install && npm run build
```
Expected: build thành công, output → `custom-addons/hocba_hrm/static/spa`. Nếu lỗi JSX/ternary, sửa cho cân bằng dấu ngoặc rồi build lại.

- [ ] **Step 5: Commit (gồm build).**
```bash
git add frontend/src/features/attendance/CheckInPanel.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(shift-ui): CheckInPanel check-in theo ca cho CTV/OT + build (Gói 4B)"
```

---

## Task 6: Kiểm thử cuối + handoff + merge

- [ ] **Step 1: Chạy lại toàn bộ test backend — xanh, N>0.** Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0 (gồm test_shift_checkin + các suite cũ).

- [ ] **Step 2: Kiểm thử thủ công SPA (spec §6).** CTV có ca duyệt quanh giờ hiện tại → panel hiện nút check-in mở; ngoài cửa sổ → khóa/báo lỗi; không có ca → "chưa có ca". Official không đổi.

- [ ] **Step 3: Cập nhật handoff.** Modify `docs/superpowers/HANDOFF-attendance-upgrade.md`: bảng §1 đổi Gói 4B → ✅ XONG; thêm spec/plan 4B vào §6 (hoặc mục tham chiếu). Commit:
```bash
git add docs/superpowers/HANDOFF-attendance-upgrade.md
git commit -m "docs(attendance): Gói 4B hoàn tất — check-in cửa sổ ca (handoff)"
```

- [ ] **Step 4: Merge về `main`** (skill `superpowers:finishing-a-development-branch`). Trước merge: fetch + merge `origin/main` mới nhất (có thể có commit của thành viên khác), chạy lại test + build xác nhận xanh, rồi push.

---

## Self-Review (đối chiếu spec)
- §1 Policy field + view: Task 1. ✅
- §2 Model `_todays_approved_shifts` + `_assert_shift_check_allowed`: Task 2 (8 test phủ window/no-shift/outside/pending/already-checked-in/checkout-not-checked-in/checkout-ok/filter). ✅
- §3 Controller phân nhánh + bỏ not_official + map lỗi: Task 3. ✅
- §4 `_att_me_info.shiftToday`: Task 4 (2 test). ✅
- §5 FE CheckInPanel + map lỗi + build: Task 5. ✅
- §6 Test + thủ công: Task 2/4/6. ✅
- §7 Phạm vi: không đụng 4C/nhiều-ca-ngày/official-OT. ✅

**Type consistency:** `_assert_shift_check_allowed(employee, kind)` + `_todays_approved_shifts(employee, today)` nhất quán model↔controller↔test. Mã lỗi `no_shift_today`/`outside_shift_window` khớp `_CHECK_ERR_STATUS`↔model raise↔FE map. `shiftToday` keys (`start/end/shiftType/rate/checkInOpen/checkOutOpen`) khớp `_att_me_info`↔CheckInPanel.
