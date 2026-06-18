# Gói 4A — Đăng ký & duyệt ca làm việc (lịch tuần) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho CTV/NV tự đăng ký ca làm việc (loại CTV/OT, hệ số tự gợi ý), manager duyệt/chỉnh/từ chối hoặc thêm ca hộ; hiển thị lịch tuần dạng lưới 7 cột; thay tab "Tăng ca (OT)" mock bằng lịch ca thật.

**Architecture:** Model riêng `hocba.work_shift` (state pending→approved/rejected, constraint giờ + chống trùng). Backend mở rộng `hocba_hrm/controllers/main.py` bằng helper module-level (`_shift_row/_shift_create/_shifts_week/_shift_decide/_shift_cancel`) + 5 endpoint, tái dùng `_to_utc/_dt_local/_user_can_manage/_emp_scope_domain/_emp_in_scope` của Gói 1-3. Frontend thêm `ShiftCalendar`/`ShiftForm`/`ShiftDrawer`.

**Tech Stack:** Odoo 19 (Python), TransactionCase tests; React/Vite SPA (build → `custom-addons/hocba_hrm/static/spa`).

**Spec:** [docs/superpowers/specs/2026-06-17-shift-registration-design.md](../specs/2026-06-17-shift-registration-design.md)

---

## Cấu trúc file (tạo/sửa)

**Backend (addon `hocba_attendance`)**
- Create: `custom-addons/hocba_attendance/models/hocba_work_shift.py` — model ca + constraint + `_default_rate`.
- Modify: `custom-addons/hocba_attendance/models/__init__.py` — đăng ký model.
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv` — 2 dòng ACL.

**Backend API (addon `hocba_hrm`)**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — 5 helper module-level + 5 endpoint trong class; thêm import `datetime` + `expression`.
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py` — test backend.
- Modify: `custom-addons/hocba_hrm/tests/__init__.py` — import file test mới.

**Frontend (`frontend/src/`)**
- Modify: `frontend/src/api/attendance.js` — 5 hàm gọi API.
- Create: `frontend/src/features/attendance/ShiftForm.jsx` — form đăng ký ca.
- Create: `frontend/src/features/attendance/ShiftDrawer.jsx` — chi tiết/duyệt/hủy ca.
- Create: `frontend/src/features/attendance/ShiftCalendar.jsx` — lưới tuần 7 cột + điều phối.
- Modify: `frontend/src/features/attendance/Attendance.jsx` — tab "Ca làm việc (CTV/OT)" render `ShiftCalendar`, bỏ `OtMock`.
- Modify/Delete: `frontend/src/features/attendance/mock.js` — bỏ `OT_LOG`; nếu rỗng thì xóa file + gỡ import `USE_MOCK`/`MockBanner`.

---

## Lệnh test & build (như Gói 1-3 — đọc kỹ)

Chạy trên Docker local (KHÔNG Neon). Docker Desktop phải bật. **`MSYS_NO_PATHCONV=1` BẮT BUỘC trên Git Bash Windows** — thiếu nó chạy 0 test mà vẫn báo "thành công". Luôn xác nhận `0 failed, 0 error(s) of N tests` với **N > 0**. Raise Bash timeout 480000ms cho lệnh test.

```bash
# Test hocba_hrm (controller + helper Gói 4A) — luôn -u cả hocba_attendance để sync schema model mới
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test

# Build SPA
cd frontend && npm install && npm run build   # output → custom-addons/hocba_hrm/static/spa
```
> Lần đầu nếu báo `of 0 tests` thì `-i hocba_hrm` (cài) trước rồi `-u` chạy lại. Bỏ qua các ERROR pre-existing không liên quan của `hb_timeoff_*`/`hr_holidays_modern` khi load module.

---

## Task 1: Model `hocba.work_shift` + ACL + `_default_rate` + constraints

**Files:**
- Create: `custom-addons/hocba_attendance/models/hocba_work_shift.py`
- Modify: `custom-addons/hocba_attendance/models/__init__.py`
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv`

- [ ] **Step 1: Tạo file model**

Create `custom-addons/hocba_attendance/models/hocba_work_shift.py`:

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WorkShift(models.Model):
    """Ca làm việc cho CTV/OT (Gói 4A). user đăng ký (state=pending) → manager
    duyệt (chỉnh giờ/loại/hệ số được) hoặc từ chối; manager có thể thêm ca hộ
    NV trong phạm vi (vào thẳng approved). Lịch hiển thị theo tuần."""
    _name = 'hocba.work_shift'
    _description = 'Ca làm việc'
    _order = 'start desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    start = fields.Datetime(string='Bắt đầu', required=True)
    end = fields.Datetime(string='Kết thúc', required=True)
    shift_type = fields.Selection(
        [('ctv', 'CTV'), ('ot', 'Tăng ca (OT)')],
        string='Loại ca', required=True)
    rate = fields.Float(string='Hệ số', default=1.0)
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reason = fields.Text(string='Lý do')
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True, readonly=True)

    @api.constrains('start', 'end')
    def _check_times(self):
        for rec in self:
            if rec.start and rec.end and rec.end <= rec.start:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu.')

    @api.constrains('start', 'end', 'employee_id', 'state')
    def _check_overlap(self):
        for rec in self:
            if rec.state not in ('pending', 'approved') or not (rec.start and rec.end):
                continue
            clash = self.search_count([
                ('id', '!=', rec.id),
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ('pending', 'approved')),
                ('start', '<', rec.end),
                ('end', '>', rec.start),
            ])
            if clash:
                raise ValidationError('Ca bị trùng giờ với ca khác.')

    @api.model
    def _default_rate(self, start_dt):
        """Hệ số gợi ý theo thứ trong tuần (local): T2–T6 = 1.5; T7/CN = 2.0.
        (Lễ/đêm + 30% để Gói 4C.) start_dt là Datetime UTC naive."""
        if not start_dt:
            return 1.0
        local = fields.Datetime.context_timestamp(self.env.user, start_dt)
        return 2.0 if local.weekday() >= 5 else 1.5
```

- [ ] **Step 2: Đăng ký model**

Modify `custom-addons/hocba_attendance/models/__init__.py` — thêm dòng cuối:
```python
from . import hocba_work_shift
```

- [ ] **Step 3: Thêm ACL**

Modify `custom-addons/hocba_attendance/security/ir.model.access.csv` — thêm 2 dòng cuối:
```csv
access_hocba_work_shift_user,access.hocba.work_shift.user,model_hocba_work_shift,hr.group_hr_user,1,1,1,0
access_hocba_work_shift_manager,access.hocba.work_shift.manager,model_hocba_work_shift,hr.group_hr_manager,1,1,1,1
```

- [ ] **Step 4: Sync schema để xác nhận model load**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance --addons-path=/mnt/extra-addons --stop-after-init --log-level=warn
```
Expected: kết thúc không có traceback (không `KeyError model_hocba_work_shift`, không ParseError).

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_attendance/models/hocba_work_shift.py custom-addons/hocba_attendance/models/__init__.py custom-addons/hocba_attendance/security/ir.model.access.csv
git commit -m "feat(attendance): model hocba.work_shift + ACL + default rate (Gói 4A)"
```

---

## Task 2: Import bổ sung + helper `_shift_row`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py` (tạo mới)
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Bổ sung import module-level trong controller**

Modify `custom-addons/hocba_hrm/controllers/main.py`:
- Dòng `from datetime import date, timedelta` → đổi thành `from datetime import date, datetime, timedelta`.
- Thêm dòng import (cạnh các import odoo ở đầu file, sau `from odoo.tools import file_open`): `from odoo.osv import expression`.

- [ ] **Step 2: Đăng ký test module**

Modify `custom-addons/hocba_hrm/tests/__init__.py` — thêm dòng:
```python
from . import test_shift_api
```

- [ ] **Step 3: Viết test thất bại cho `_shift_row`**

Create `custom-addons/hocba_hrm/tests/test_shift_api.py`:
```python
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _shift_row


@tagged('post_install', '-at_install')
class TestShiftApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV A User', 'login': 'ctv_shift_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Shift', 'login': 'hrm_shift',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.hrm.tz = 'Asia/Ho_Chi_Minh'

    def _make_shift(self, **vals):
        base = {
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00',   # T2, 09:00 local
            'end': '2026-06-15 04:00:00',     # 11:00 local
            'shift_type': 'ctv', 'rate': 1.5, 'state': 'pending',
        }
        base.update(vals)
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create(base)

    def test_shift_row_shape(self):
        s = self._make_shift()
        row = _shift_row(s)
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['shiftType'], 'ctv')
        self.assertEqual(row['rate'], 1.5)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['start'], '2026-06-15T09:00:00')
        self.assertEqual(row['end'], '2026-06-15T11:00:00')
        self.assertIsNone(row['reviewer'])
```

- [ ] **Step 4: Chạy test — xác nhận FAIL**

Run (lệnh test ở đầu plan). Expected: FAIL — `ImportError: cannot import name '_shift_row'`. Xác nhận `of N tests` với N>0.

- [ ] **Step 5: Thêm helper `_shift_row`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm sau `_att_requests_pending` (helper Gói 3, trước `_to_utc`):
```python
def _shift_row(s):
    """Một ca làm việc cho SPA (wire format camelCase)."""
    emp = s.employee_id
    return {
        'id': s.id,
        'empId': emp.id,
        'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'start': _dt_local(s, s.start),
        'end': _dt_local(s, s.end),
        'shiftType': s.shift_type,
        'rate': s.rate,
        'state': s.state,
        'reason': s.reason or '',
        'reviewer': s.reviewer_id.name or None,
        'reviewNote': s.review_note or None,
        'decisionDate': _dt_local(s, s.decision_date),
    }
```

- [ ] **Step 6: Chạy test — `test_shift_row_shape` PASS**

Run lệnh test. Expected: `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 7: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(shift-api): import expression/datetime + helper _shift_row (Gói 4A)"
```

---

## Task 3: Helper `_shift_create` (đăng ký / manager thêm hộ)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py`

- [ ] **Step 1: Mở rộng import + viết test thất bại**

Trong `test_shift_api.py`: đổi import controller thành `from odoo.addons.hocba_hrm.controllers.main import _shift_row, _shift_create`. Thêm các test vào class:
```python
    def test_create_pins_employee_and_default_rate(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'reason': 'Trực sáng'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['rate'], 1.5)       # T2 -> 1.5
        s = env['hocba.work_shift'].browse(row['id'])
        self.assertEqual(str(s.start), '2026-06-15 02:00:00')   # 09:00+07 -> 02:00 UTC

    def test_create_weekend_rate(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-20T09:00', 'end': '2026-06-20T11:00',  # T7
            'shiftType': 'ot'})
        self.assertEqual(row['rate'], 2.0)

    def test_create_bad_type_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T09:00',
                                'end': '2026-06-15T11:00', 'shiftType': 'x'})

    def test_create_end_before_start_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T11:00',
                                'end': '2026-06-15T09:00', 'shiftType': 'ot'})

    def test_create_overlap_raises(self):
        env = self.env(user=self.user)
        _shift_create(env, {'start': '2026-06-15T09:00',
                            'end': '2026-06-15T11:00', 'shiftType': 'ctv'})
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-15T10:00',
                                'end': '2026-06-15T12:00', 'shiftType': 'ctv'})

    def test_create_no_employee_returns_none(self):
        u = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_shift'})
        self.assertIsNone(_shift_create(self.env(user=u), {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ot'}))

    def test_manager_add_for_employee_approved(self):
        env = self.env(user=self.hrm)
        row = _shift_create(env, {
            'empId': self.emp.id, 'start': '2026-06-16T09:00',
            'end': '2026-06-16T11:00', 'shiftType': 'ot'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['reviewer'], self.hrm.name)
```

- [ ] **Step 2: Chạy test — xác nhận FAIL** (`ImportError: cannot import name '_shift_create'`). Run lệnh test.

- [ ] **Step 3: Thêm helper `_shift_create`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_shift_row`:
```python
def _shift_create(env, body):
    """Đăng ký ca. Mặc định pin về user (state=pending). Nếu người gọi là
    manager và gửi empId thuộc phạm vi → tạo hộ NV đó (state=approved).
    Trả _shift_row; None nếu user chưa có hồ sơ NV; ValidationError nếu dữ liệu sai."""
    Shift = env['hocba.work_shift'].sudo()
    emp_id = body.get('empId')
    as_manager = bool(emp_id) and _user_can_manage(env)
    if as_manager:
        emp = env['hr.employee'].sudo().browse(int(emp_id))
        if not emp.exists() or not _emp_in_scope(env, emp):
            raise ValidationError('Nhân viên ngoài phạm vi.')
    else:
        emp = env.user.employee_id
        if not emp:
            return None
    shift_type = body.get('shiftType')
    if shift_type not in ('ctv', 'ot'):
        raise ValidationError('Loại ca không hợp lệ.')
    start = _to_utc(env, body.get('start'))
    end = _to_utc(env, body.get('end'))
    if not start or not end:
        raise ValidationError('Cần giờ bắt đầu và kết thúc.')
    vals = {
        'employee_id': emp.id,
        'start': start, 'end': end,
        'shift_type': shift_type,
        'rate': Shift._default_rate(start),
        'reason': (body.get('reason') or '').strip() or False,
    }
    if as_manager:
        vals.update({'state': 'approved', 'reviewer_id': env.user.id,
                     'decision_date': fields.Datetime.now()})
    shift = Shift.create(vals)
    return _shift_row(shift)
```

- [ ] **Step 4: Chạy test — 7 test create PASS**. Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift-api): _shift_create — đăng ký / manager thêm hộ (Gói 4A)"
```

---

## Task 4: Helper `_shifts_week` (dữ liệu lịch tuần)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py`

- [ ] **Step 1: Mở rộng import + viết test thất bại**

Đổi import controller thành `from odoo.addons.hocba_hrm.controllers.main import _shift_row, _shift_create, _shifts_week`. Thêm test:
```python
    def test_week_owner_sees_own_pending(self):
        self._make_shift()   # pending, 2026-06-15 (T2)
        data = _shifts_week(self.env(user=self.user), '2026-06-15')
        self.assertEqual(data['weekStart'], '2026-06-15')
        self.assertEqual(len(data['days']), 7)
        mon = data['days'][0]
        self.assertEqual(mon['date'], '2026-06-15')
        self.assertEqual(mon['weekday'], 'T2')
        self.assertEqual(len(mon['shifts']), 1)
        self.assertEqual(mon['shifts'][0]['empId'], self.emp.id)

    def test_week_other_sees_only_approved(self):
        # ca pending của self.emp KHÔNG hiện cho NV khác; ca approved thì có.
        self._make_shift()                       # pending
        self._make_shift(start='2026-06-16 02:00:00',
                         end='2026-06-16 04:00:00', state='approved')
        other_user = self.env['res.users'].create(
            {'name': 'Khac', 'login': 'khac_shift'})
        other_user.tz = 'Asia/Ho_Chi_Minh'
        other_emp = self.env['hr.employee'].create({
            'name': 'NV Khac', 'x_employment_status': 'official',
            'identification_id': '012345678991',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776'})
        other_emp.user_id = other_user
        # other_user là NV thường, không quản lý -> chỉ thấy ca của chính mình
        data = _shifts_week(self.env(user=other_user), '2026-06-15')
        all_ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertNotIn(self.emp.id, all_ids)   # không thấy ca người khác

    def test_week_hr_manager_sees_approved_in_scope(self):
        self._make_shift(state='approved')
        data = _shifts_week(self.env(user=self.hrm), '2026-06-15')
        ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertIn(self.emp.id, ids)
        self.assertTrue(data['canManage'])

    def test_week_dept_head_scope(self):
        dept = self.env['hr.department'].create({'name': 'Phòng S'})
        in_emp = self.env['hr.employee'].create({
            'name': 'NV trong S', 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': '012345678992',
            'x_pit_code': '3334445556', 'x_social_insurance_no': '6665554443'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP S'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPS', 'login': 'tps_shift'})
        mgr_user.tz = 'Asia/Ho_Chi_Minh'
        mgr_emp.user_id = mgr_user
        self.env['hocba.work_shift'].with_context(tz='Asia/Ho_Chi_Minh').create({
            'employee_id': in_emp.id, 'start': '2026-06-15 02:00:00',
            'end': '2026-06-15 04:00:00', 'shift_type': 'ot', 'state': 'approved'})
        self._make_shift(state='approved')   # self.emp ngoài Phòng S
        data = _shifts_week(self.env(user=mgr_user), '2026-06-15')
        ids = [r['empId'] for d in data['days'] for r in d['shifts']]
        self.assertIn(in_emp.id, ids)
        self.assertNotIn(self.emp.id, ids)

    def test_week_defaults_to_monday(self):
        # truyền ngày giữa tuần -> chuẩn hóa về thứ 2 (2026-06-17 là T4)
        data = _shifts_week(self.env(user=self.user), '2026-06-17')
        self.assertEqual(data['weekStart'], '2026-06-15')
```

- [ ] **Step 2: Chạy test — xác nhận FAIL** (`ImportError: cannot import name '_shifts_week'`). Run lệnh test.

- [ ] **Step 3: Thêm helper `_shifts_week`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_shift_create`:
```python
def _shifts_week(env, monday_str):
    """Dữ liệu lịch tuần (T2→CN của tuần chứa monday_str; rỗng = tuần hiện tại).
    Owner thấy ca của mình mọi state; người khác chỉ thấy ca approved trong
    phạm vi vai trò (HR=tất cả, trưởng phòng=phòng mình, NV thường=của mình)."""
    user = env.user
    d = fields.Date.from_string(monday_str) if monday_str else fields.Date.context_today(user)
    monday = d - timedelta(days=d.weekday())
    tz = timezone(user.tz or 'UTC')
    start_local = tz.localize(datetime(monday.year, monday.month, monday.day))
    end_local = start_local + timedelta(days=7)
    start_utc = start_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(utc).replace(tzinfo=None)
    approved = [('state', '=', 'approved')]
    for field, op, val in _emp_scope_domain(env):
        if field == 'id':
            approved.append(('employee_id', op, val))
        else:
            approved.append(('employee_id.%s' % field, op, val))
    me = user.employee_id
    if me:
        visible = expression.OR([[('employee_id', '=', me.id)], approved])
    else:
        visible = approved
    domain = [('start', '>=', start_utc), ('start', '<', end_utc)] + visible
    recs = env['hocba.work_shift'].sudo().search(domain)
    by_day = {}
    for s in recs:
        local = fields.Datetime.context_timestamp(s, s.start)
        by_day.setdefault(local.date(), []).append(_shift_row(s))
    weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
    days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        days.append({'date': _d(day), 'weekday': weekdays[i],
                     'shifts': by_day.get(day, [])})
    return {'weekStart': _d(monday), 'canManage': _user_can_manage(env), 'days': days}
```

- [ ] **Step 4: Chạy test — 5 test week PASS**. Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift-api): _shifts_week — lịch tuần theo phạm vi (Gói 4A)"
```

---

## Task 5: Helper `_shift_decide` (manager duyệt/từ chối)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py`

- [ ] **Step 1: Mở rộng import + viết test thất bại**

Đổi import controller thành `... import _shift_row, _shift_create, _shifts_week, _shift_decide`. Thêm test:
```python
    def test_decide_approve_with_override(self):
        env = self.env(user=self.hrm)
        s = self._make_shift()
        row = _shift_decide(env, s.id, True, {'rate': 3.0,
                            'end': '2026-06-15T12:00'})
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['rate'], 3.0)
        self.assertEqual(row['end'], '2026-06-15T12:00:00')
        self.assertEqual(row['reviewer'], self.hrm.name)

    def test_decide_reject_sets_note(self):
        env = self.env(user=self.hrm)
        s = self._make_shift()
        row = _shift_decide(env, s.id, False, {'reviewNote': 'Không cần'})
        self.assertEqual(row['state'], 'rejected')
        self.assertEqual(row['reviewNote'], 'Không cần')

    def test_decide_bad_type_override_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_shift()
        with self.assertRaises(ValidationError):
            _shift_decide(env, s.id, True, {'shiftType': 'x'})

    def test_decide_out_of_scope_forbidden(self):
        dept = self.env['hr.department'].create({'name': 'Phòng Z'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP Z'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPZ', 'login': 'tpz_shift'})
        mgr_emp.user_id = mgr_user
        s = self._make_shift()   # self.emp ngoài Phòng Z
        with self.assertRaises(AccessError):
            _shift_decide(self.env(user=mgr_user), s.id, True, {})

    def test_decide_already_decided_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_shift(state='approved')
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, False, {})

    def test_decide_missing_returns_none(self):
        self.assertIsNone(_shift_decide(self.env(user=self.hrm), 999999, True, {}))
```

- [ ] **Step 2: Chạy test — xác nhận FAIL** (`ImportError: cannot import name '_shift_decide'`). Run lệnh test.

- [ ] **Step 3: Thêm helper `_shift_decide`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_shifts_week`:
```python
def _shift_decide(env, shift_id, approve, body):
    """Manager duyệt/từ chối 1 ca trong phạm vi (Gói 4A). Khi duyệt: override
    được start/end/shiftType/rate (nếu body gửi). Trả _shift_row; None nếu không
    tồn tại; AccessError nếu vượt quyền; UserError('already_decided') nếu đã quyết định."""
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)):
        raise AccessError('forbidden')
    if shift.state != 'pending':
        raise UserError('already_decided')
    vals = {
        'reviewer_id': env.user.id,
        'decision_date': fields.Datetime.now(),
        'review_note': (body.get('reviewNote') or '').strip() or False,
    }
    if approve:
        if 'start' in body:
            vals['start'] = _to_utc(env, body['start'])
        if 'end' in body:
            vals['end'] = _to_utc(env, body['end'])
        if 'shiftType' in body:
            if body['shiftType'] not in ('ctv', 'ot'):
                raise ValidationError('Loại ca không hợp lệ.')
            vals['shift_type'] = body['shiftType']
        if 'rate' in body:
            vals['rate'] = float(body['rate'])
        vals['state'] = 'approved'
    else:
        vals['state'] = 'rejected'
    shift.write(vals)
    return _shift_row(shift)
```

- [ ] **Step 4: Chạy test — 6 test decide PASS**. Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift-api): _shift_decide — manager duyệt/từ chối/override (Gói 4A)"
```

---

## Task 6: Helper `_shift_cancel` (hủy ca pending)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py`

- [ ] **Step 1: Mở rộng import + viết test thất bại**

Đổi import controller thành `... import _shift_row, _shift_create, _shifts_week, _shift_decide, _shift_cancel`. Thêm test:
```python
    def test_cancel_owner_pending_ok(self):
        s = self._make_shift()
        res = _shift_cancel(self.env(user=self.user), s.id)
        self.assertEqual(res, {'ok': True})
        self.assertFalse(s.exists())

    def test_cancel_approved_rejected(self):
        s = self._make_shift(state='approved')
        with self.assertRaises(UserError):
            _shift_cancel(self.env(user=self.user), s.id)

    def test_cancel_other_user_forbidden(self):
        s = self._make_shift()
        u = self.env['res.users'].create({'name': 'Ke', 'login': 'ke_shift'})
        with self.assertRaises(AccessError):
            _shift_cancel(self.env(user=u), s.id)

    def test_cancel_missing_returns_none(self):
        self.assertIsNone(_shift_cancel(self.env(user=self.user), 999999))

    def test_cancel_manager_in_scope_ok(self):
        s = self._make_shift()
        res = _shift_cancel(self.env(user=self.hrm), s.id)
        self.assertEqual(res, {'ok': True})
```

- [ ] **Step 2: Chạy test — xác nhận FAIL** (`ImportError: cannot import name '_shift_cancel'`). Run lệnh test.

- [ ] **Step 3: Thêm helper `_shift_cancel`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_shift_decide`:
```python
def _shift_cancel(env, shift_id):
    """Hủy ca PENDING. Quyền: owner của ca hoặc manager trong phạm vi.
    Trả {'ok':True}; None nếu không tồn tại; AccessError nếu vượt quyền;
    UserError('only_pending') nếu ca không còn pending."""
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    me = env.user.employee_id
    is_owner = bool(me) and shift.employee_id == me
    if not (is_owner or (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id))):
        raise AccessError('forbidden')
    if shift.state != 'pending':
        raise UserError('only_pending')
    shift.unlink()
    return {'ok': True}
```

- [ ] **Step 4: Chạy test — 5 test cancel PASS**. Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift-api): _shift_cancel — hủy ca pending (Gói 4A)"
```

---

## Task 7: 5 endpoint HTTP cho ca làm việc

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

> Wiring mỏng (không test helper riêng); xác nhận bằng chạy lại toàn bộ suite không vỡ.

- [ ] **Step 1: Thêm 5 endpoint + helper `_decide_shift` vào class `HocBaHRM`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm sau method `api_attendance_request_reject` (cuối class, các endpoint Gói 3):
```python
    # ------------------------------------------------------------------
    # Ca làm việc CTV/OT (Gói 4A): user đăng ký ca → manager duyệt/chỉnh/từ chối
    # hoặc thêm ca hộ; lịch hiển thị theo tuần. Spec:
    # docs/superpowers/specs/2026-06-17-shift-registration-design.md
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/shifts', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_shift_create(self, **kw):
        try:
            row = _shift_create(request.env, request.get_json_data() or {})
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/shifts/week', auth='user', type='http', methods=['GET'])
    def api_shifts_week(self, monday=None, **kw):
        return request.make_json_response(_shifts_week(request.env, monday))

    def _decide_shift(self, shift_id, approve):
        try:
            row = _shift_decide(request.env, shift_id, approve,
                                request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/approve', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_approve(self, shift_id, **kw):
        return self._decide_shift(shift_id, True)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/reject', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_reject(self, shift_id, **kw):
        return self._decide_shift(shift_id, False)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/cancel', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_cancel(self, shift_id, **kw):
        try:
            res = _shift_cancel(request.env, shift_id)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': str(ex)}, status=400)
        if res is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(res)
```
> Except-ordering trong `_decide_shift`: AccessError → ValidationError → UserError (ValidationError là lớp con của UserError). Route literal `shifts`/`shifts/week` không đụng `<int:shift_id>`.

- [ ] **Step 2: Chạy lại TOÀN BỘ suite — không vỡ**

Run lệnh test. Expected `0 failed, 0 error(s) of N tests`, N>0 (gồm test_attendance_api + test_attendance_request + test_shift_api).

- [ ] **Step 3: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(shift-api): 5 endpoint ca (đăng ký/tuần/duyệt/từ chối/hủy) (Gói 4A)"
```

---

## Task 8: Frontend — hàm gọi API

**Files:**
- Modify: `frontend/src/api/attendance.js`

- [ ] **Step 1: Thêm 5 hàm**

Modify `frontend/src/api/attendance.js` — thêm cuối file:
```javascript
export const fetchWeekShifts = (monday) =>
  hbGet(`/hocba-hrm/api/shifts/week?monday=${monday}`);
export const createShift = (body) =>
  hbPost('/hocba-hrm/api/shifts', body);
export const approveShift = (id, body) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/approve`, body);
export const rejectShift = (id, body) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/reject`, body);
export const cancelShift = (id) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/cancel`, {});
```

- [ ] **Step 2: Commit**
```bash
git add frontend/src/api/attendance.js
git commit -m "feat(shift-ui): hàm API ca làm việc (Gói 4A)"
```

---

## Task 9: Frontend — `ShiftForm.jsx`

**Files:**
- Create: `frontend/src/features/attendance/ShiftForm.jsx`

- [ ] **Step 1: Tạo component**

Create `frontend/src/features/attendance/ShiftForm.jsx`:
```jsx
/* Form đăng ký ca làm việc (Gói 4A). User chọn giờ vào/ra (datetime-local),
   loại ca (CTV/OT), lý do. Hệ số do backend tự tính theo ngày. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createShift } from '../../api/attendance';

export default function ShiftForm({ onClose, onSaved }) {
  const [form, setForm] = useState({ start: '', end: '', shiftType: 'ot', reason: '' });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function submit() {
    if (!form.start || !form.end) { setErr('Vui lòng chọn giờ bắt đầu và kết thúc.'); return; }
    setBusy(true); setErr(null);
    try {
      await createShift({
        start: form.start, end: form.end,
        shiftType: form.shiftType, reason: form.reason.trim(),
      });
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Đăng ký ca thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>Đăng ký ca làm việc</h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <label style={{ fontSize: 12.5 }}>Loại ca
          <select className="sel" value={form.shiftType}
            onChange={(e) => setForm({ ...form, shiftType: e.target.value })}>
            <option value="ot">Tăng ca (OT)</option>
            <option value="ctv">CTV</option>
          </select>
        </label>
        <label style={{ fontSize: 12.5 }}>Bắt đầu
          <input type="datetime-local" className="sel" value={form.start}
            onChange={(e) => setForm({ ...form, start: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Kết thúc
          <input type="datetime-local" className="sel" value={form.end}
            onChange={(e) => setForm({ ...form, end: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Lý do
          <textarea className="sel" rows={2} value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}>Đăng ký ca</button>
          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={onClose}>Hủy</button>
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Xác nhận `Modal`/`Icon` import giống `RequestForm.jsx`/`AttendanceDrawer.jsx` (default export). No build (Task 13 builds).**

- [ ] **Step 3: Commit**
```bash
git add frontend/src/features/attendance/ShiftForm.jsx
git commit -m "feat(shift-ui): ShiftForm đăng ký ca (Gói 4A)"
```

---

## Task 10: Frontend — `ShiftDrawer.jsx`

**Files:**
- Create: `frontend/src/features/attendance/ShiftDrawer.jsx`

- [ ] **Step 1: Tạo component**

Create `frontend/src/features/attendance/ShiftDrawer.jsx`:
```jsx
/* Chi tiết 1 ca (Gói 4A). Manager + ca pending: override giờ/loại/hệ số +
   Duyệt/Từ chối. Owner + ca pending: nút Hủy. Còn lại: xem trạng thái. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { approveShift, rejectShift, cancelShift } from '../../api/attendance';

const STATE_LABEL = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối' };
const STATE_KIND = { pending: 'amber', approved: 'green', rejected: 'red' };

export default function ShiftDrawer({ shift, canManage, onClose, onChanged }) {
  const isPending = shift.state === 'pending';
  const [start, setStart] = useState(shift.start ? shift.start.slice(0, 16) : '');
  const [end, setEnd] = useState(shift.end ? shift.end.slice(0, 16) : '');
  const [stype, setStype] = useState(shift.shiftType);
  const [rate, setRate] = useState(shift.rate);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function decide(approve) {
    setBusy(true); setErr(null);
    try {
      const body = approve
        ? { start: start || null, end: end || null, shiftType: stype, rate: Number(rate), reviewNote: note }
        : { reviewNote: note };
      await (approve ? approveShift(shift.id, body) : rejectShift(shift.id, body));
      onChanged && onChanged();
    } catch (e) { setErr('Thao tác thất bại (' + e.message + ').'); onChanged && onChanged(); }
    finally { setBusy(false); }
  }

  async function cancel() {
    setBusy(true); setErr(null);
    try {
      await cancelShift(shift.id);
      onChanged && onChanged();
    } catch (e) { setErr('Hủy thất bại (' + e.message + ').'); onChanged && onChanged(); }
    finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{shift.empName}</h2>
            <Badge kind={STATE_KIND[shift.state]} dot>{STATE_LABEL[shift.state]}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
            {shift.code} · {shift.depName}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div className="grid-2" style={{ rowGap: 14 }}>
          <div className="kv"><div className="k">Bắt đầu</div><div className="v mono">{fmtDate(shift.start.slice(0, 10))} {fmtTime(shift.start)}</div></div>
          <div className="kv"><div className="k">Kết thúc</div><div className="v mono">{fmtTime(shift.end)}</div></div>
          <div className="kv"><div className="k">Loại ca</div><div className="v">{shift.shiftType === 'ctv' ? 'CTV' : 'Tăng ca (OT)'}</div></div>
          <div className="kv"><div className="k">Hệ số</div><div className="v mono" style={{ fontWeight: 600 }}>×{shift.rate}</div></div>
        </div>
        {shift.reason && <div className="muted" style={{ fontSize: 12.5, marginTop: 12 }}>Lý do: "{shift.reason}"</div>}
        {!canManage && !isPending && shift.reviewNote && (
          <div className="muted" style={{ fontSize: 12.5, marginTop: 8 }}>Ghi chú duyệt: {shift.reviewNote}</div>
        )}
      </div>

      {canManage && isPending && (
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <label style={{ fontSize: 12 }}>Bắt đầu
              <input type="datetime-local" className="sel" value={start} onChange={(e) => setStart(e.target.value)} />
            </label>
            <label style={{ fontSize: 12 }}>Kết thúc
              <input type="datetime-local" className="sel" value={end} onChange={(e) => setEnd(e.target.value)} />
            </label>
            <label style={{ fontSize: 12 }}>Loại
              <select className="sel" value={stype} onChange={(e) => setStype(e.target.value)}>
                <option value="ot">OT</option><option value="ctv">CTV</option>
              </select>
            </label>
            <label style={{ fontSize: 12 }}>Hệ số
              <input type="number" step="0.5" className="sel" style={{ width: 80 }} value={rate} onChange={(e) => setRate(e.target.value)} />
            </label>
          </div>
          <input className="sel" placeholder="Ghi chú duyệt" value={note} onChange={(e) => setNote(e.target.value)} />
          {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => decide(true)}>Duyệt</button>
            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={() => decide(false)}>Từ chối</button>
          </div>
        </div>
      )}
      {!canManage && isPending && (
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
          {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5, marginBottom: 8 }}>{err}</div>}
          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={cancel}>Hủy ca</button>
        </div>
      )}
    </Modal>
  );
}
```

- [ ] **Step 2: Xác nhận imports (Modal/Icon/Badge default; fmtDate từ utils/format; fmtTime từ ./util; approveShift/rejectShift/cancelShift từ api) khớp interface thật. No build.**

- [ ] **Step 3: Commit**
```bash
git add frontend/src/features/attendance/ShiftDrawer.jsx
git commit -m "feat(shift-ui): ShiftDrawer xem/duyệt/hủy ca (Gói 4A)"
```

---

## Task 11: Frontend — `ShiftCalendar.jsx` (lưới tuần)

**Files:**
- Create: `frontend/src/features/attendance/ShiftCalendar.jsx`

- [ ] **Step 1: Tạo component**

Create `frontend/src/features/attendance/ShiftCalendar.jsx`:
```jsx
/* Lịch ca theo tuần — lưới 7 cột (T2→CN) (Gói 4A). Điều phối: tải tuần, đăng ký
   ca (ShiftForm), xem/duyệt/hủy 1 ca (ShiftDrawer), chuyển tuần trước/sau. */
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { fetchWeekShifts } from '../../api/attendance';
import ShiftForm from './ShiftForm';
import ShiftDrawer from './ShiftDrawer';

const CHIP_BG = { pending: 'var(--amber-bg)', approved: '#ecfdf5', rejected: 'var(--red-50)' };

function ymd(d) {
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}
function mondayOf(date) {
  const d = new Date(date);
  const wd = (d.getDay() + 6) % 7;   // 0=Th2
  d.setDate(d.getDate() - wd);
  d.setHours(0, 0, 0, 0);
  return d;
}

export default function ShiftCalendar({ canManage }) {
  const [monday, setMonday] = useState(() => mondayOf(new Date()));
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchWeekShifts(ymd(monday)).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [monday]);

  const moveWeek = (n) => {
    const d = new Date(monday); d.setDate(d.getDate() + n); setMonday(d);
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải lịch ca…" />;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(-7)}>‹ Tuần trước</button>
        <div style={{ fontWeight: 600, fontSize: 13.5 }}>
          Tuần {fmtDate(data.days[0].date)} – {fmtDate(data.days[6].date)}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(7)}>Tuần sau ›</button>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>Đăng ký ca</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 8 }}>
        {data.days.map((day) => (
          <div key={day.date} className="card" style={{ padding: 8, minHeight: 120 }}>
            <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 6 }}>
              {day.weekday}<span className="muted" style={{ fontWeight: 400, marginLeft: 4 }}>{fmtDate(day.date).slice(0, 5)}</span>
            </div>
            {day.shifts.length === 0 && <div className="faint" style={{ fontSize: 11 }}>—</div>}
            {day.shifts.map((s) => (
              <button key={s.id} onClick={() => setSel(s)}
                style={{ display: 'block', width: '100%', textAlign: 'left', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 8px', marginBottom: 6, background: CHIP_BG[s.state], cursor: 'pointer' }}>
                <div className="mono" style={{ fontSize: 12, fontWeight: 600 }}>{fmtTime(s.start)}–{fmtTime(s.end)}</div>
                <div style={{ fontSize: 11 }}>{s.shiftType === 'ctv' ? 'CTV' : 'OT'} ×{s.rate}</div>
              </button>
            ))}
          </div>
        ))}
      </div>

      {showForm && <ShiftForm onClose={() => setShowForm(false)} onSaved={load} />}
      {sel && <ShiftDrawer shift={sel} canManage={canManage}
        onClose={() => setSel(null)} onChanged={() => { setSel(null); load(); }} />}
    </div>
  );
}
```

- [ ] **Step 2: Xác nhận imports (states/format/util/api) khớp interface thật (giống RequestList.jsx). No build.**

- [ ] **Step 3: Commit**
```bash
git add frontend/src/features/attendance/ShiftCalendar.jsx
git commit -m "feat(shift-ui): ShiftCalendar lưới tuần 7 cột (Gói 4A)"
```

---

## Task 12: Frontend — nối `Attendance.jsx` + bỏ OtMock/OT_LOG + build

**Files:**
- Modify: `frontend/src/features/attendance/Attendance.jsx`
- Modify/Delete: `frontend/src/features/attendance/mock.js`

- [ ] **Step 1: READ `Attendance.jsx` đầy đủ** trước khi sửa.

- [ ] **Step 2: Sửa import.**

Trong `Attendance.jsx`:
- Dòng `import { USE_MOCK, OT_LOG } from './mock';` → **xóa** (mock.js sẽ bị bỏ). Thêm:
```jsx
import ShiftCalendar from './ShiftCalendar';
```
(Giữ các import khác như `Avatar`, `Badge`, `fmtDate`, `Icon` TẠM THỜI — sẽ dọn ở Step 5 sau khi xóa OtMock/MockBanner.)

- [ ] **Step 3: Đổi nhãn tab + render ShiftCalendar.**

Trong mảng `tabs` của manager: đổi `['ot', 'Tăng ca (OT)']` → `['ot', 'Ca làm việc (CTV/OT)']`.
Trong mảng `tabs` của user: thêm `['ot', 'Ca làm việc (CTV/OT)']` vào cuối (user cũng có tab ca):
```jsx
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Ca làm việc (CTV/OT)']]
    : [['me', 'Chấm công của tôi'], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
```
Đổi dòng render `{activeTab === 'ot' && <OtMock />}` thành:
```jsx
      {activeTab === 'ot' && <ShiftCalendar canManage={isManager} />}
```

- [ ] **Step 4: Xóa `OtMock` và `MockBanner`.**

Xóa định nghĩa `function OtMock() { ... }` và `function MockBanner() { ... }` (không còn dùng — Gói 3 đã bỏ ForgotMock; giờ bỏ nốt OtMock). Xóa luôn dòng render OtMock cũ nếu còn sót.

- [ ] **Step 5: Dọn import thừa trong `Attendance.jsx`.**

Sau khi xóa OtMock/MockBanner, chạy:
```bash
grep -n "Avatar\|Badge\|fmtDate\|USE_MOCK\|Icon\b" frontend/src/features/attendance/Attendance.jsx
```
Với mỗi import giờ không còn nơi dùng (`Avatar`, `Badge`, `fmtDate`, `Icon`, và import từ `./mock`), **xóa** dòng import đó. (Các symbol này trước chỉ phục vụ OtMock/MockBanner.) Giữ lại những gì vẫn còn dùng (CheckInPanel, MyHistory, AttendanceTable, states, RequestForm, RequestList, fetch* …).

- [ ] **Step 6: Xử lý `mock.js`.**

Run `grep -rn "from './mock'\|from \"./mock\"\|OT_LOG\|USE_MOCK\|FORGOT_REQUESTS" frontend/src`.
- Nếu KHÔNG còn file nào import từ `./mock` → **xóa** `frontend/src/features/attendance/mock.js`.
- Nếu còn nơi dùng → chỉ xóa `OT_LOG` khỏi mock.js, giữ phần còn lại.
Xác nhận lại bằng grep: không còn tham chiếu `OT_LOG`/`OtMock`/`MockBanner` trong toàn `frontend/src`.

- [ ] **Step 7: Build SPA.**

Run:
```bash
cd frontend && npm install && npm run build
```
Expected: build thành công, không lỗi import/JSX; output ghi `custom-addons/hocba_hrm/static/spa` (assets/index-*.js mới + index.html cập nhật hash).

- [ ] **Step 8: Commit (gồm bản build SPA)**
```bash
git add frontend/src/features/attendance/Attendance.jsx frontend/src/features/attendance/mock.js custom-addons/hocba_hrm/static/spa
git commit -m "feat(shift-ui): tab Ca làm việc thật thay OtMock + build (Gói 4A)"
```
> Nếu đã xóa `mock.js`: `git add -A frontend/src/features/attendance/` để ghi nhận việc xóa file.

---

## Task 13: Kiểm thử cuối + cập nhật handoff

- [ ] **Step 1: Chạy lại toàn bộ test backend — xanh, N>0.**

Run lệnh test (đầu plan). Expected `0 failed, 0 error(s) of N tests`, N>0 (gồm test_attendance_api + test_attendance_request + test_shift_api).

- [ ] **Step 2: Kiểm thử thủ công SPA (spec §4).**

- User: tab "Ca làm việc (CTV/OT)" → "Đăng ký ca" (OT/CTV, giờ vào/ra) → chip amber trong cột ngày; chuyển tuần trước/sau; mở chip pending → "Hủy ca".
- Manager: thấy ca approved trong phạm vi; mở chip pending → chỉnh hệ số/giờ → Duyệt (chip green) / Từ chối (chip red + note).

- [ ] **Step 3: Cập nhật handoff — đánh dấu 4A xong.**

Modify `docs/superpowers/HANDOFF-attendance-upgrade.md`:
- Bảng §1: tách dòng Gói 4 thành 4A/4B/4C; đánh dấu **4A ✅ XONG (đã merge main)**, 4B/4C 🔴 chưa.
- §6: thêm spec `2026-06-17-shift-registration-design.md` + plan `2026-06-17-shift-registration.md` vào danh sách.
```bash
git add docs/superpowers/HANDOFF-attendance-upgrade.md
git commit -m "docs(attendance): Gói 4A hoàn tất — đăng ký & duyệt ca (handoff)"
```

- [ ] **Step 4: Merge về `main`.**

Dùng skill `superpowers:finishing-a-development-branch`. Trước merge: rebase/merge `origin/main` mới nhất, chạy lại test (Step 1) + build (Task 12 Step 7) xác nhận xanh.

---

## Self-Review (đã đối chiếu spec)

- **§1 Model:** Task 1 — đủ field/kiểu/`_order`/ACL; constraint `_check_times` + `_check_overlap`; `_default_rate`. ✅
- **§2.1 `_shift_row`:** Task 2 — đủ key camelCase, dùng `_dt_local`. ✅
- **§2.2 `_shift_create`:** Task 3 — pin employee / manager thêm hộ approved / validate type+giờ / default rate / overlap (qua constraint). ✅
- **§2.3 `_shifts_week`:** Task 4 — chuẩn hóa Monday, khoảng local→UTC, OR(owner, approved-in-scope), gom 7 ngày. ✅
- **§2.4 `_shift_decide`:** Task 5 — scope 403, already_decided, override start/end/type/rate. ✅
- **§2.5 `_shift_cancel`:** Task 6 — owner/manager, only_pending, unlink. ✅
- **§2.6 Endpoints:** Task 7 — 5 endpoint + map lỗi đúng thứ tự except. ✅
- **§3 Frontend:** Task 8 (api), 9 (ShiftForm), 10 (ShiftDrawer), 11 (ShiftCalendar lưới 7 cột), 12 (tab + bỏ OtMock/OT_LOG + build). ✅
- **§4 Test:** Task 2-6 phủ row/create(pin/rate/type/overlap/manager-add)/week(owner/other/HR/dept-head/monday)/decide(override/reject/scope/already)/cancel(owner/approved/scope/manager). BR-010 fixture official có CCCD. ✅
- **§5 Phạm vi:** KHÔNG đụng check-in cửa sổ (4B), tính công OT (4C), lịch lặp, payroll. ✅

**Type consistency:** helper tên `_shift_row/_shift_create/_shifts_week/_shift_decide/_shift_cancel` nhất quán controller↔test↔endpoint. Wire field (`empId/empName/code/depName/start/end/shiftType/rate/state/reason/reviewer/reviewNote/decisionDate`) khớp FE. API `fetchWeekShifts/createShift/approveShift/rejectShift/cancelShift` khớp `api/attendance.js`↔component. `_shifts_week` trả `{weekStart, canManage, days:[{date,weekday,shifts}]}` khớp `ShiftCalendar`. ✅
