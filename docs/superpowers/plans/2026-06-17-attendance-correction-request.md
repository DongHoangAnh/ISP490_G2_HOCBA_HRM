# Gói 3 — Luồng đơn chấm công (user gửi → manager duyệt & sửa) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thay tab mock "Đơn quên chấm công" bằng luồng thật: user gửi đơn xin sửa/tạo bản ghi chấm công cho 1 ngày; manager xem, chỉnh giờ rồi Duyệt (ghi/tạo bản ghi, công tự tính lại) hoặc Từ chối kèm lý do.

**Architecture:** Model gọn `hocba.attendance.request` trong addon `hocba_attendance` (không mail.thread). Backend mở rộng controller `hocba_hrm/controllers/main.py` bằng các helper module-level (`_req_row`, `_request_apply`, `_request_create`, `_request_decide`, `_att_requests_mine`, `_att_requests_pending`) + 5 endpoint, tái dùng helper phạm vi/UTC của Gói 1-2. Frontend thêm `RequestForm`/`RequestList`, tab "Đơn của tôi" (user) + nút gửi đơn trong drawer, tab "Đơn chấm công" thật (manager).

**Tech Stack:** Odoo 19 (Python), TransactionCase tests; React/Vite SPA (build → `custom-addons/hocba_hrm/static/spa`).

**Spec:** [docs/superpowers/specs/2026-06-17-attendance-correction-request-design.md](../specs/2026-06-17-attendance-correction-request-design.md)

---

## Cấu trúc file (tạo/sửa)

**Backend (addon `hocba_attendance`)**
- Create: `custom-addons/hocba_attendance/models/hocba_attendance_request.py` — model đơn.
- Modify: `custom-addons/hocba_attendance/models/__init__.py` — đăng ký model.
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv` — 2 dòng ACL.

**Backend API (addon `hocba_hrm`)**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — thêm 6 helper module-level + 5 endpoint trong class.
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py` — test backend (helper module-level).
- Modify: `custom-addons/hocba_hrm/tests/__init__.py` — import file test mới (kiểm tra có cần không).

**Frontend (`frontend/src/`)**
- Modify: `frontend/src/api/attendance.js` — 5 hàm gọi API.
- Create: `frontend/src/features/attendance/RequestForm.jsx` — form tạo đơn.
- Create: `frontend/src/features/attendance/RequestList.jsx` — danh sách đơn (user read-only / manager duyệt).
- Modify: `frontend/src/features/attendance/Attendance.jsx` — tab "Đơn của tôi" (user) + tab "Đơn chấm công" thật (manager), bỏ `ForgotMock`.
- Modify: `frontend/src/features/attendance/AttendanceDrawer.jsx` — nút "Gửi đơn sửa" cho user (non-manage).
- Modify: `frontend/src/features/attendance/mock.js` — bỏ `FORGOT_REQUESTS`.

---

## Lệnh test & build (handoff §5 — đọc kỹ)

Chạy trên Docker local (KHÔNG Neon). Docker Desktop phải bật. **`MSYS_NO_PATHCONV=1` BẮT BUỘC trên Git Bash Windows** — thiếu nó chạy 0 test mà vẫn báo "thành công". Luôn xác nhận dòng kết quả `0 failed, 0 error(s) of N tests` với **N > 0**.

```bash
# Test hocba_hrm (controller + helper Gói 3)
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test

# Build SPA
cd frontend && npm install && npm run build   # output → custom-addons/hocba_hrm/static/spa
```

> Vì Gói 3 thêm model trong `hocba_attendance` + dùng trong test của `hocba_hrm`, luôn `-u hocba_attendance,hocba_hrm,hocba_employees` để schema đồng bộ. Lần đầu nếu báo `of 0 tests` thì `-i hocba_hrm` (cài) trước, rồi `-u` chạy lại.

---

## Task 1: Model `hocba.attendance.request` + ACL

**Files:**
- Create: `custom-addons/hocba_attendance/models/hocba_attendance_request.py`
- Modify: `custom-addons/hocba_attendance/models/__init__.py`
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv`

- [ ] **Step 1: Tạo file model**

Create `custom-addons/hocba_attendance/models/hocba_attendance_request.py`:

```python
from odoo import models, fields


class AttendanceRequest(models.Model):
    """Đơn xin sửa/tạo bản ghi chấm công cho 1 ngày (Gói 3).
    user gửi (state=pending) → manager duyệt (chỉnh giờ được) hoặc từ chối.
    Duyệt thì áp vào hocba.attendance (sửa bản ghi có sẵn / tạo nếu ngày thiếu)."""
    _name = 'hocba.attendance.request'
    _description = 'Đơn chấm công'
    _order = 'create_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    request_date = fields.Date(string='Ngày công', required=True)
    attendance_id = fields.Many2one(
        'hocba.attendance', string='Bản ghi', ondelete='set null',
        help='Bản ghi cần sửa; rỗng = ngày thiếu (duyệt thì tạo mới).')
    proposed_check_in = fields.Datetime(string='Giờ vào đề xuất')
    proposed_check_out = fields.Datetime(string='Giờ ra đề xuất')
    reason = fields.Text(string='Lý do', required=True)
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True)
```

- [ ] **Step 2: Đăng ký model trong `__init__.py`**

Modify `custom-addons/hocba_attendance/models/__init__.py` — thêm dòng cuối:

```python
from . import hr_attendance_status
from . import hr_work_assignment
from . import hr_attendance
from . import hocba_attendance_policy
from . import hocba_attendance_request
```

- [ ] **Step 3: Thêm ACL**

Modify `custom-addons/hocba_attendance/security/ir.model.access.csv` — thêm 2 dòng cuối (HR user: read/write/create, không unlink; HR manager: full — giống `access_hocba_attendance_*`):

```csv
access_hocba_attendance_request_user,access.hocba.attendance.request.user,model_hocba_attendance_request,hr.group_hr_user,1,1,1,0
access_hocba_attendance_request_manager,access.hocba.attendance.request.manager,model_hocba_attendance_request,hr.group_hr_manager,1,1,1,1
```

- [ ] **Step 4: Đồng bộ schema để xác nhận model load được**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance --addons-path=/mnt/extra-addons --stop-after-init --log-level=warn
```
Expected: kết thúc không lỗi (không có traceback `ParseError`/`KeyError model_hocba_attendance_request`).

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/models/hocba_attendance_request.py \
        custom-addons/hocba_attendance/models/__init__.py \
        custom-addons/hocba_attendance/security/ir.model.access.csv
git commit -m "feat(attendance): model hocba.attendance.request + ACL (Gói 3)"
```

---

## Task 2: Helper `_req_row` (wire camelCase)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_att_me_history`, trước `_to_utc`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py` (tạo mới)
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Kiểm tra `tests/__init__.py` đã auto-import chưa**

Run: `cat custom-addons/hocba_hrm/tests/__init__.py`
- Nếu file dùng `from . import *` hoặc đã liệt kê từng file: thêm `from . import test_attendance_request` nếu cần (Odoo cần import rõ ràng từng module test). Nếu file rỗng/không có, tạo dòng:
```python
from . import test_attendance_request
```
(Giữ nguyên các dòng import test cũ; chỉ thêm dòng mới.)

- [ ] **Step 2: Viết test thất bại cho `_req_row`**

Create `custom-addons/hocba_hrm/tests/test_attendance_request.py`:

```python
import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import (
    _req_row, _request_apply, _request_create, _request_decide,
    _att_requests_mine, _att_requests_pending,
)


@tagged('post_install', '-at_install')
class TestAttendanceRequest(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
            'office_lat': 0.0, 'office_lng': 0.0,
            'std_work_hours': 8.0, 'violation_free_days': 2,
        })
        # NV gửi đơn + user của họ
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Don', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789',
        })
        self.user = self.env['res.users'].create({
            'name': 'NV Don User', 'login': 'nv_req_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        # HR Manager
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Req', 'login': 'hrm_req',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.hrm.tz = 'Asia/Ho_Chi_Minh'

    def _make_req(self, **vals):
        base = {
            'employee_id': self.emp.id, 'request_date': '2026-06-12',
            'reason': 'Quên bấm', 'state': 'pending',
        }
        base.update(vals)
        return self.env['hocba.attendance.request'].create(base)

    def test_req_row_shape(self):
        req = self._make_req()
        row = _req_row(req)
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['requestDate'], '2026-06-12')
        self.assertEqual(row['state'], 'pending')
        self.assertIsNone(row['attendanceId'])
        self.assertIsNone(row['reviewer'])
        self.assertEqual(row['reason'], 'Quên bấm')
```

- [ ] **Step 3: Chạy test — xác nhận FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: FAIL — `ImportError: cannot import name '_req_row'` (helper chưa tồn tại).

- [ ] **Step 4: Thêm helper `_req_row` vào controller**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau hàm `_att_me_history` (kết thúc dòng `return {'month': ...}`) và TRƯỚC `def _to_utc`:

```python
def _req_row(req):
    """Một đơn chấm công cho SPA (wire format camelCase)."""
    emp = req.employee_id
    return {
        'id': req.id,
        'empId': emp.id,
        'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'requestDate': _d(req.request_date),
        'attendanceId': req.attendance_id.id or None,
        'checkIn': _dt_local(req, req.proposed_check_in),
        'checkOut': _dt_local(req, req.proposed_check_out),
        'reason': req.reason or '',
        'state': req.state,
        'reviewer': req.reviewer_id.name or None,
        'reviewNote': req.review_note or None,
        'decisionDate': _dt_local(req, req.decision_date),
    }
```

- [ ] **Step 5: Chạy test — xác nhận `test_req_row_shape` PASS**

Run lệnh ở Step 3.
Expected: `0 failed, 0 error(s) of N tests` với N > 0; `test_req_row_shape` không nằm trong phần fail.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
        custom-addons/hocba_hrm/tests/test_attendance_request.py \
        custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance-api): helper _req_row cho đơn chấm công (Gói 3)"
```

---

## Task 3: Helper `_request_apply` (duyệt → ghi/tạo bản ghi)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_attendance_delete`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py`

- [ ] **Step 1: Viết test thất bại cho cả 2 nhánh (sửa bản ghi / tạo bản ghi)**

Thêm vào class `TestAttendanceRequest`:

```python
    def test_apply_updates_existing_record(self):
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': self.emp.id,
                          'check_in': '2026-06-12 02:00:00',    # 09:00 local
                          'check_out': '2026-06-12 07:00:00'})  # 5h -> thiếu 180
        self.assertEqual(rec.missing_minutes, 180)
        req = self._make_req(attendance_id=rec.id)
        # 09:00 -> 17:00 local = 8h đủ công. _to_utc nhận local ISO.
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        env = self.env(user=self.hrm)
        out = _request_apply(env, req.with_env(env), None,
                             _to_utc(env, '2026-06-12T17:00'))
        self.assertEqual(out, rec)
        self.assertEqual(rec.missing_minutes, 0)

    def test_apply_creates_record_for_missing_day(self):
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        req = self._make_req(request_date='2026-06-13')
        env = self.env(user=self.hrm)
        ci = _to_utc(env, '2026-06-13T09:00')
        co = _to_utc(env, '2026-06-13T17:00')
        rec = _request_apply(env, req.with_env(env), ci, co)
        self.assertTrue(rec.exists())
        self.assertEqual(rec.employee_id, self.emp)
        self.assertEqual(req.attendance_id, rec)

    def test_apply_missing_day_without_checkin_raises(self):
        req = self._make_req(request_date='2026-06-14')
        env = self.env(user=self.hrm)
        with self.assertRaises(ValidationError):
            _request_apply(env, req.with_env(env), None, None)
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Run lệnh test (như Task 2 Step 3).
Expected: FAIL — `ImportError: cannot import name '_request_apply'`.

- [ ] **Step 3: Thêm helper `_request_apply`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau hàm `_attendance_delete` (kết thúc `return {'ok': True}`):

```python
def _request_apply(env, req, check_in_utc, check_out_utc):
    """Áp đơn đã duyệt vào bản ghi chấm công (Gói 3). Trả bản ghi.
    check_in_utc/check_out_utc: Datetime UTC naive đã resolve (None = bỏ qua).
    - Có attendance_id (hoặc tìm thấy bản ghi cùng ngày): ghi các giờ != None.
    - Ngày thiếu: cần check_in_utc để tạo; thiếu -> ValidationError."""
    Att = env['hocba.attendance'].sudo()
    rec = req.attendance_id
    if not rec:
        rec = Att.search([
            ('employee_id', '=', req.employee_id.id),
            ('date', '=', req.request_date),
        ], limit=1)
    if rec:
        vals = {}
        if check_in_utc is not None:
            vals['check_in'] = check_in_utc
        if check_out_utc is not None:
            vals['check_out'] = check_out_utc
        if vals:
            rec.write(vals)
    else:
        if not check_in_utc:
            raise ValidationError('Cần giờ check-in để tạo bản ghi.')
        rec = Att.create({
            'employee_id': req.employee_id.id,
            'check_in': check_in_utc,
            'check_out': check_out_utc or False,
        })
    req.attendance_id = rec
    return rec
```

- [ ] **Step 4: Chạy test — xác nhận 3 test apply PASS**

Run lệnh test.
Expected: `0 failed, 0 error(s) of N tests`, N > 0; 3 test `test_apply_*` không fail.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
        custom-addons/hocba_hrm/tests/test_attendance_request.py
git commit -m "feat(attendance-api): _request_apply ghi/tạo bản ghi khi duyệt (Gói 3)"
```

---

## Task 4: Helper `_request_create` (user tạo đơn)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_request_apply`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào class `TestAttendanceRequest`:

```python
    def test_create_pins_employee_and_converts_utc(self):
        env = self.env(user=self.user)
        row = _request_create(env, {
            'requestDate': '2026-06-12',
            'checkIn': '2026-06-12T08:10',
            'reason': 'Điện thoại hết pin',
        })
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        req = env['hocba.attendance.request'].browse(row['id'])
        # 08:10 local (+07) -> 01:10 UTC stored
        self.assertEqual(str(req.proposed_check_in), '2026-06-12 01:10:00')

    def test_create_empty_reason_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'requestDate': '2026-06-12', 'reason': '  '})

    def test_create_no_employee_returns_none(self):
        u = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_req'})
        self.assertIsNone(_request_create(self.env(user=u),
                                          {'requestDate': '2026-06-12',
                                           'reason': 'x'}))

    def test_create_foreign_attendance_rejected(self):
        other = self.env['hr.employee'].create({
            'name': 'NV Khac', 'x_employment_status': 'official',
            'identification_id': '012345678902',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776'})
        rec = self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': other.id, 'check_in': '2026-06-12 02:00:00'})
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'requestDate': '2026-06-12',
                                  'attendanceId': rec.id, 'reason': 'x'})
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Expected: FAIL — `ImportError: cannot import name '_request_create'`.

- [ ] **Step 3: Thêm helper `_request_create`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_request_apply`:

```python
def _request_create(env, body):
    """User tạo đơn chấm công cho CHÍNH MÌNH (pin employee, chống giả mạo).
    Trả _req_row; None nếu user chưa có hồ sơ NV; ValidationError nếu thiếu lý
    do / bản ghi đính kèm không thuộc về user."""
    emp = env.user.employee_id
    if not emp:
        return None
    reason = (body.get('reason') or '').strip()
    if not reason:
        raise ValidationError('Cần lý do.')
    Att = env['hocba.attendance'].sudo()
    att_id = body.get('attendanceId')
    attendance = Att.browse(int(att_id)) if att_id else Att.browse()
    if att_id and (not attendance.exists() or attendance.employee_id != emp):
        raise ValidationError('Bản ghi không hợp lệ.')
    request_date = body.get('requestDate') or (attendance.date if att_id else False)
    req = env['hocba.attendance.request'].sudo().create({
        'employee_id': emp.id,
        'request_date': request_date,
        'attendance_id': attendance.id or False,
        'proposed_check_in': _to_utc(env, body.get('checkIn')),
        'proposed_check_out': _to_utc(env, body.get('checkOut')),
        'reason': reason,
    })
    return _req_row(req)
```

- [ ] **Step 4: Chạy test — xác nhận 4 test create PASS**

Expected: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
        custom-addons/hocba_hrm/tests/test_attendance_request.py
git commit -m "feat(attendance-api): _request_create — user gửi đơn (Gói 3)"
```

---

## Task 5: Helper `_request_decide` (manager duyệt/từ chối)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_request_create`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào class `TestAttendanceRequest`:

```python
    def test_decide_approve_applies_manager_override(self):
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': self.emp.id,
                          'check_in': '2026-06-12 02:00:00',
                          'check_out': '2026-06-12 07:00:00'})  # thiếu 180
        req = self._make_req(attendance_id=rec.id,
                             proposed_check_out=_to_utc(
                                 self.env(user=self.user), '2026-06-12T16:00'))
        env = self.env(user=self.hrm)
        # manager chỉnh khác giờ user đề xuất: 17:00
        row = _request_decide(env, req.id, True, {'checkOut': '2026-06-12T17:00'})
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['reviewer'], self.hrm.name)
        self.assertEqual(rec.missing_minutes, 0)  # 09:00->17:00 = 8h

    def test_decide_approve_creates_for_missing_day(self):
        from odoo.addons.hocba_hrm.controllers.main import _to_utc
        env = self.env(user=self.hrm)
        req = self._make_req(
            request_date='2026-06-13',
            proposed_check_in=_to_utc(self.env(user=self.user), '2026-06-13T09:00'),
            proposed_check_out=_to_utc(self.env(user=self.user), '2026-06-13T17:00'))
        row = _request_decide(env, req.id, True, {})
        self.assertEqual(row['state'], 'approved')
        self.assertIsNotNone(row['attendanceId'])

    def test_decide_approve_missing_day_no_checkin_raises(self):
        env = self.env(user=self.hrm)
        req = self._make_req(request_date='2026-06-14')  # không proposed giờ nào
        with self.assertRaises(ValidationError):
            _request_decide(env, req.id, True, {})

    def test_decide_reject_sets_state_and_note(self):
        env = self.env(user=self.hrm)
        req = self._make_req()
        row = _request_decide(env, req.id, False, {'reviewNote': 'Không hợp lệ'})
        self.assertEqual(row['state'], 'rejected')
        self.assertEqual(row['reviewNote'], 'Không hợp lệ')

    def test_decide_out_of_scope_forbidden(self):
        # NV ngoài phạm vi của 1 trưởng phòng (không HR)
        dept = self.env['hr.department'].create({'name': 'Phòng X'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP X'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPX', 'login': 'tpx_req'})
        mgr_emp.user_id = mgr_user
        req = self._make_req()  # emp KHÔNG thuộc Phòng X
        with self.assertRaises(AccessError):
            _request_decide(self.env(user=mgr_user), req.id, True, {})

    def test_decide_already_decided_raises(self):
        env = self.env(user=self.hrm)
        req = self._make_req(state='approved')
        with self.assertRaises(UserError):
            _request_decide(env, req.id, False, {})

    def test_decide_missing_returns_none(self):
        self.assertIsNone(_request_decide(self.env(user=self.hrm), 999999, False, {}))
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Expected: FAIL — `ImportError: cannot import name '_request_decide'`.

- [ ] **Step 3: Thêm helper `_request_decide`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_request_create`:

```python
def _request_decide(env, req_id, approve, body):
    """Manager duyệt/từ chối 1 đơn trong phạm vi (Gói 3).
    Trả _req_row; None nếu không tồn tại; AccessError nếu vượt quyền;
    UserError('already_decided') nếu đơn đã quyết định.
    Khi duyệt: giờ áp dụng = body override (nếu gửi) ELSE proposed_* của đơn."""
    req = env['hocba.attendance.request'].sudo().browse(req_id)
    if not req.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, req.employee_id)):
        raise AccessError('forbidden')
    if req.state != 'pending':
        raise UserError('already_decided')
    vals = {
        'reviewer_id': env.user.id,
        'decision_date': fields.Datetime.now(),
        'review_note': (body.get('reviewNote') or '').strip() or False,
    }
    if approve:
        ci = _to_utc(env, body['checkIn']) if 'checkIn' in body else req.proposed_check_in
        co = _to_utc(env, body['checkOut']) if 'checkOut' in body else req.proposed_check_out
        _request_apply(env, req, ci or None, co or None)
        vals['state'] = 'approved'
    else:
        vals['state'] = 'rejected'
    req.write(vals)
    return _req_row(req)
```

- [ ] **Step 4: Chạy test — xác nhận 7 test decide PASS**

Expected: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
        custom-addons/hocba_hrm/tests/test_attendance_request.py
git commit -m "feat(attendance-api): _request_decide — manager duyệt/từ chối (Gói 3)"
```

---

## Task 6: Helper danh sách `_att_requests_mine` + `_att_requests_pending`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm sau `_request_decide`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_request.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào class `TestAttendanceRequest`:

```python
    def test_mine_only_own(self):
        other = self.env['hr.employee'].create({
            'name': 'NV Khac2', 'x_employment_status': 'official',
            'identification_id': '012345678903',
            'x_pit_code': '2223334445', 'x_social_insurance_no': '5554443332'})
        self._make_req()
        self.env['hocba.attendance.request'].create({
            'employee_id': other.id, 'request_date': '2026-06-12',
            'reason': 'khac'})
        rows = _att_requests_mine(self.env(user=self.user))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['empId'], self.emp.id)

    def test_mine_no_employee_none(self):
        u = self.env['res.users'].create({'name': 'NoEmp2', 'login': 'noemp_req2'})
        self.assertIsNone(_att_requests_mine(self.env(user=u)))

    def test_pending_hr_manager_sees_all_pending(self):
        self._make_req()
        rows = _att_requests_pending(self.env(user=self.hrm))
        self.assertIn(self.emp.id, [r['empId'] for r in rows])

    def test_pending_non_manager_empty(self):
        self._make_req()
        rows = _att_requests_pending(self.env(user=self.user))
        self.assertEqual(rows, [])

    def test_pending_dept_head_scope(self):
        dept = self.env['hr.department'].create({'name': 'Phòng P'})
        in_emp = self.env['hr.employee'].create({
            'name': 'NV trong P', 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': '012345670099',
            'x_pit_code': '3334445556', 'x_social_insurance_no': '6665554443'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP P'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPP', 'login': 'tpp_req'})
        mgr_emp.user_id = mgr_user
        self.env['hocba.attendance.request'].create({
            'employee_id': in_emp.id, 'request_date': '2026-06-12', 'reason': 'a'})
        self._make_req()  # emp ngoài Phòng P
        rows = _att_requests_pending(self.env(user=mgr_user))
        emp_ids = [r['empId'] for r in rows]
        self.assertIn(in_emp.id, emp_ids)
        self.assertNotIn(self.emp.id, emp_ids)
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Expected: FAIL — `ImportError: cannot import name '_att_requests_mine'`.

- [ ] **Step 3: Thêm 2 helper danh sách**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau `_request_decide`:

```python
def _att_requests_mine(env):
    """Đơn chấm công của chính user (mọi state), mới nhất trước.
    None nếu user chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    reqs = env['hocba.attendance.request'].sudo().search(
        [('employee_id', '=', emp.id)])
    return [_req_row(r) for r in reqs]


def _att_requests_pending(env):
    """Đơn đang chờ duyệt trong phạm vi vai trò của manager. [] nếu không phải
    manager. Áp _emp_scope_domain lên employee_id (prefix như bảng ngày Gói 2)."""
    if not _user_can_manage(env):
        return []
    domain = [('state', '=', 'pending')]
    for field, op, val in _emp_scope_domain(env):
        if field == 'id':
            domain.append(('employee_id', op, val))
        else:
            domain.append(('employee_id.%s' % field, op, val))
    reqs = env['hocba.attendance.request'].sudo().search(domain)
    return [_req_row(r) for r in reqs]
```

- [ ] **Step 4: Chạy test — xác nhận 5 test list PASS**

Expected: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
        custom-addons/hocba_hrm/tests/test_attendance_request.py
git commit -m "feat(attendance-api): danh sách đơn mine/pending theo phạm vi (Gói 3)"
```

---

## Task 7: 5 endpoint HTTP cho luồng đơn

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm trong class `HocBaHRM`, sau `api_attendance_delete`)

> Không viết test HTTP riêng (test ở tầng helper đã đủ — giống Gói 2). Đây là wiring mỏng; xác nhận bằng build + chạy lại toàn bộ test suite không vỡ.

- [ ] **Step 1: Thêm 5 endpoint + helper `_decide`**

Modify `custom-addons/hocba_hrm/controllers/main.py` — thêm ngay sau method `api_attendance_delete` (cuối class, trước khi hết file):

```python
    # ------------------------------------------------------------------
    # Đơn chấm công (Gói 3): user gửi đơn sửa/tạo bản ghi → manager duyệt
    # (chỉnh giờ được) & áp dụng, hoặc từ chối. Spec:
    # docs/superpowers/specs/2026-06-17-attendance-correction-request-design.md
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/attendance/requests', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_request_create(self, **kw):
        try:
            row = _request_create(request.env, request.get_json_data() or {})
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/requests/mine', auth='user',
                type='http', methods=['GET'])
    def api_attendance_requests_mine(self, **kw):
        rows = _att_requests_mine(request.env)
        if rows is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response({'rows': rows})

    @http.route('/hocba-hrm/api/attendance/requests/pending', auth='user',
                type='http', methods=['GET'])
    def api_attendance_requests_pending(self, **kw):
        return request.make_json_response(
            {'rows': _att_requests_pending(request.env)})

    def _decide_request(self, req_id, approve):
        try:
            row = _request_decide(request.env, req_id, approve,
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

    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/approve',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_approve(self, req_id, **kw):
        return self._decide_request(req_id, True)

    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/reject',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_reject(self, req_id, **kw):
        return self._decide_request(req_id, False)
```

> **Lưu ý thứ tự except:** `ValidationError` là lớp con của `UserError` nên PHẢI bắt `ValidationError` trước `UserError`. Khối `_decide_request` đã đúng thứ tự: AccessError → ValidationError (rejected + message) → UserError (`already_decided`). Route `requests`/`requests/mine`/`requests/pending` (literal) không đụng `<int:req_id>` vì 'requests' không phải số.

- [ ] **Step 2: Chạy lại TOÀN BỘ test suite — không vỡ**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests`, N > 0 (gồm cả `test_attendance_api` cũ + `test_attendance_request` mới).

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(attendance-api): 5 endpoint đơn chấm công (tạo/mine/pending/duyệt/từ chối) (Gói 3)"
```

---

## Task 8: Frontend — hàm gọi API

**Files:**
- Modify: `frontend/src/api/attendance.js`

- [ ] **Step 1: Thêm 5 hàm API**

Modify `frontend/src/api/attendance.js` — thêm vào cuối file (sau `deleteAttendance`):

```javascript
export const createRequest = (body) =>
  hbPost('/hocba-hrm/api/attendance/requests', body);
export const fetchMyRequests = () =>
  hbGet('/hocba-hrm/api/attendance/requests/mine');
export const fetchPendingRequests = () =>
  hbGet('/hocba-hrm/api/attendance/requests/pending');
export const approveRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/approve`, body);
export const rejectRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/reject`, body);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/attendance.js
git commit -m "feat(attendance-ui): hàm API đơn chấm công (Gói 3)"
```

---

## Task 9: Frontend — `RequestForm.jsx` (form tạo đơn)

**Files:**
- Create: `frontend/src/features/attendance/RequestForm.jsx`

- [ ] **Step 1: Tạo component form**

Create `frontend/src/features/attendance/RequestForm.jsx`:

```jsx
/* Form gửi đơn chấm công (Gói 3). Dùng 2 trường hợp:
   - Sửa bản ghi có sẵn: truyền attendanceId + requestDate cố định (prefill giờ).
   - Quên cả ngày: không attendanceId, user tự chọn ngày. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createRequest } from '../../api/attendance';

export default function RequestForm({ attendanceId, requestDate, checkIn, checkOut, onClose, onSaved }) {
  const fixedDate = !!attendanceId;
  const [form, setForm] = useState({
    requestDate: requestDate || '',
    checkIn: checkIn ? checkIn.slice(0, 16) : '',
    checkOut: checkOut ? checkOut.slice(0, 16) : '',
    reason: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function submit() {
    if (!form.requestDate) { setErr('Vui lòng chọn ngày.'); return; }
    if (!form.reason.trim()) { setErr('Vui lòng nhập lý do.'); return; }
    setBusy(true); setErr(null);
    try {
      await createRequest({
        attendanceId: attendanceId || undefined,
        requestDate: form.requestDate,
        checkIn: form.checkIn || null,
        checkOut: form.checkOut || null,
        reason: form.reason.trim(),
      });
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Gửi đơn thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>
          {fixedDate ? 'Gửi đơn sửa chấm công' : 'Gửi đơn quên chấm công'}
        </h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <label style={{ fontSize: 12.5 }}>Ngày công
          <input type="date" className="sel" value={form.requestDate} disabled={fixedDate}
            onChange={(e) => setForm({ ...form, requestDate: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Giờ vào đề xuất
          <input type="datetime-local" className="sel" value={form.checkIn}
            onChange={(e) => setForm({ ...form, checkIn: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Giờ ra đề xuất
          <input type="datetime-local" className="sel" value={form.checkOut}
            onChange={(e) => setForm({ ...form, checkOut: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Lý do
          <textarea className="sel" rows={3} value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}>Gửi đơn</button>
          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={onClose}>Hủy</button>
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/attendance/RequestForm.jsx
git commit -m "feat(attendance-ui): RequestForm gửi đơn chấm công (Gói 3)"
```

---

## Task 10: Frontend — `RequestList.jsx` (danh sách đơn / duyệt)

**Files:**
- Create: `frontend/src/features/attendance/RequestList.jsx`

- [ ] **Step 1: Tạo component danh sách**

Create `frontend/src/features/attendance/RequestList.jsx`:

```jsx
/* Danh sách đơn chấm công (Gói 3).
   - canReview=false (user): xem trạng thái + ghi chú duyệt (read-only).
   - canReview=true (manager): chỉnh giờ đề xuất + Duyệt / Từ chối. */
import { useState } from 'react';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { approveRequest, rejectRequest } from '../../api/attendance';

const STATE_LABEL = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối' };
const STATE_KIND = { pending: 'amber', approved: 'green', rejected: 'red' };

export default function RequestList({ rows, loading, error, onReload, canReview }) {
  if (loading) return <LoadingState label="Đang tải đơn…" />;
  if (error) return <ErrorState message={error} onRetry={onReload} />;
  if (!rows || rows.length === 0) return <EmptyState label="Chưa có đơn nào." />;
  return (
    <div className="card">
      <div className="card-head"><h3>{canReview ? 'Đơn chấm công chờ duyệt' : 'Đơn của tôi'}</h3></div>
      <div style={{ padding: '4px 12px 8px' }}>
        {rows.map((r) => (
          <RequestRow key={r.id} r={r} canReview={canReview} onReload={onReload} />
        ))}
      </div>
    </div>
  );
}

function RequestRow({ r, canReview, onReload }) {
  const [ci, setCi] = useState(r.checkIn ? r.checkIn.slice(0, 16) : '');
  const [co, setCo] = useState(r.checkOut ? r.checkOut.slice(0, 16) : '');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function act(approve) {
    setBusy(true); setErr(null);
    try {
      const body = approve
        ? { checkIn: ci || null, checkOut: co || null, reviewNote: note }
        : { reviewNote: note };
      await (approve ? approveRequest(r.id, body) : rejectRequest(r.id, body));
      onReload && onReload();
    } catch (e) { setErr('Thao tác thất bại (' + e.message + ').'); }
    finally { setBusy(false); }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '12px 4px', borderBottom: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Avatar emp={{ id: r.empId, name: r.empName, hasImg: false }} size={40} />
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.empName}</div>
          <div className="muted" style={{ fontSize: 12 }}>{r.code} · {r.depName}</div>
        </div>
        <div style={{ flex: 1 }}>
          <span className="mono" style={{ fontWeight: 600, fontSize: 13 }}>
            {fmtDate(r.requestDate)}
          </span>
          <span className="muted" style={{ fontSize: 12.5, marginLeft: 8 }}>
            {r.attendanceId ? 'Sửa bản ghi' : 'Ngày thiếu'} · vào {fmtTime(r.checkIn)} / ra {fmtTime(r.checkOut)}
          </span>
          <div className="muted" style={{ fontSize: 12.5 }}>"{r.reason}"</div>
        </div>
        <Badge kind={STATE_KIND[r.state]} dot>{STATE_LABEL[r.state]}</Badge>
      </div>

      {!canReview && r.state !== 'pending' && r.reviewNote && (
        <div className="muted" style={{ fontSize: 12.5, paddingLeft: 54 }}>
          Ghi chú duyệt: {r.reviewNote}
        </div>
      )}

      {canReview && r.state === 'pending' && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end', paddingLeft: 54 }}>
          <label style={{ fontSize: 12 }}>Giờ vào
            <input type="datetime-local" className="sel" value={ci} onChange={(e) => setCi(e.target.value)} />
          </label>
          <label style={{ fontSize: 12 }}>Giờ ra
            <input type="datetime-local" className="sel" value={co} onChange={(e) => setCo(e.target.value)} />
          </label>
          <label style={{ fontSize: 12, flex: 1, minWidth: 140 }}>Ghi chú
            <input className="sel" value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => act(true)}>Duyệt</button>
          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={() => act(false)}>Từ chối</button>
        </div>
      )}
      {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5, paddingLeft: 54 }}>{err}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Xác nhận `EmptyState` tồn tại trong `components/states`**

Run: `grep -n "EmptyState\|LoadingState\|ErrorState" frontend/src/components/states.jsx`
- Nếu `EmptyState` KHÔNG tồn tại: thay dòng `if (!rows || rows.length === 0) return <EmptyState label="Chưa có đơn nào." />;` bằng:
```jsx
  if (!rows || rows.length === 0) return <div className="muted" style={{ padding: 16, fontSize: 13 }}>Chưa có đơn nào.</div>;
```
và bỏ `EmptyState` khỏi dòng import.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/RequestList.jsx
git commit -m "feat(attendance-ui): RequestList xem/duyệt đơn (Gói 3)"
```

---

## Task 11: Frontend — nối vào `Attendance.jsx`

**Files:**
- Modify: `frontend/src/features/attendance/Attendance.jsx`

- [ ] **Step 1: Sửa import**

Modify `frontend/src/features/attendance/Attendance.jsx` — dòng 13:

Thay:
```jsx
import { USE_MOCK, FORGOT_REQUESTS, OT_LOG } from './mock';
```
bằng:
```jsx
import { USE_MOCK, OT_LOG } from './mock';
import { fetchMyRequests, fetchPendingRequests } from '../../api/attendance';
import RequestForm from './RequestForm';
import RequestList from './RequestList';
```

- [ ] **Step 2: Thêm state + loader đơn vào component `Attendance`**

Trong `export default function Attendance({ search })`, sau dòng `const [tab, setTab] = useState(null);` thêm:

```jsx
  const [reqs, setReqs] = useState({ rows: null, loading: false, error: null });
  const [showForm, setShowForm] = useState(false);

  const loadReqs = (manager) => {
    setReqs({ rows: null, loading: true, error: null });
    const fn = manager ? fetchPendingRequests : fetchMyRequests;
    fn().then((d) => setReqs({ rows: d.rows, loading: false, error: null }))
      .catch((e) => setReqs({ rows: null, loading: false, error: e.message }));
  };
```

- [ ] **Step 3: Thay khối tabs + render tab**

Thay đoạn từ `const isManager = me.canManage;` đến hết `{activeTab === 'ot' && <OtMock />}` bằng:

```jsx
  const isManager = me.canManage;
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Tăng ca (OT)']]
    : [['me', 'Chấm công của tôi'], ['requests', 'Đơn của tôi']];
  const activeTab = tab || (isManager ? 'day' : 'me');

  const goTab = (id) => {
    setTab(id);
    if (id === 'requests') loadReqs(isManager);
  };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Chấm công</h1>
          <p>Tự điểm danh bằng khuôn mặt &amp; vị trí · dữ liệu trực tiếp từ Odoo</p>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(([id, l]) => (
          <button key={id} className={'tab' + (activeTab === id ? ' active' : '')} onClick={() => goTab(id)}>{l}</button>
        ))}
      </div>

      {activeTab === 'me' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <CheckInPanel me={me} onChanged={load} />
          <MyHistory />
        </div>
      )}
      {activeTab === 'day' && <AttendanceTable search={search} />}
      {activeTab === 'requests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!isManager && (
            <div>
              <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
                Gửi đơn quên chấm công
              </button>
            </div>
          )}
          <RequestList rows={reqs.rows} loading={reqs.loading} error={reqs.error}
            onReload={() => loadReqs(isManager)} canReview={isManager} />
        </div>
      )}
      {activeTab === 'ot' && <OtMock />}

      {showForm && (
        <RequestForm onClose={() => setShowForm(false)} onSaved={() => loadReqs(false)} />
      )}
    </div>
  );
```

- [ ] **Step 4: Xóa hàm `ForgotMock`**

Xóa toàn bộ định nghĩa `function ForgotMock() { ... }` (không còn dùng). Giữ `MockBanner` và `OtMock`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/attendance/Attendance.jsx
git commit -m "feat(attendance-ui): tab Đơn chấm công thật (user + manager), bỏ ForgotMock (Gói 3)"
```

---

## Task 12: Frontend — nút "Gửi đơn sửa" trong `AttendanceDrawer.jsx`

**Files:**
- Modify: `frontend/src/features/attendance/AttendanceDrawer.jsx`

- [ ] **Step 1: Thêm import + state form**

Modify `frontend/src/features/attendance/AttendanceDrawer.jsx`:

Thêm vào cụm import (sau dòng `import { editAttendance, deleteAttendance } from '../../api/attendance';`):
```jsx
import RequestForm from './RequestForm';
```

Sau dòng `const [err, setErr] = useState(null);` (trong component) thêm:
```jsx
  const [reqForm, setReqForm] = useState(false);
```

- [ ] **Step 2: Thêm nút cho user (non-manage) + render form**

Sau khối `{canManage && editing && ( ... )}` (ngay trước `</Modal>`), thêm:

```jsx
        {!canManage && (
          <div style={{ display: 'flex', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setReqForm(true)}>Gửi đơn sửa</button>
          </div>
        )}
        {reqForm && (
          <RequestForm attendanceId={rec.id} requestDate={rec.date}
            checkIn={rec.checkIn} checkOut={rec.checkOut}
            onClose={() => setReqForm(false)}
            onSaved={() => { setReqForm(false); onChanged && onChanged(); }} />
        )}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/AttendanceDrawer.jsx
git commit -m "feat(attendance-ui): nút Gửi đơn sửa trong drawer cho user (Gói 3)"
```

---

## Task 13: Frontend — dọn mock + build

**Files:**
- Modify: `frontend/src/features/attendance/mock.js`

- [ ] **Step 1: Bỏ `FORGOT_REQUESTS`**

Modify `frontend/src/features/attendance/mock.js` — xóa toàn bộ block `export const FORGOT_REQUESTS = [ ... ];` (giữ `USE_MOCK` và `OT_LOG` cho Gói 4). Cập nhật comment đầu file:

```javascript
/* Dữ liệu mẫu cho tab chưa có backend (Tăng ca — Gói 4).
   Quy ước §7: có cờ USE_MOCK; xóa khi backend sẵn sàng. */
export const USE_MOCK = true;

export const OT_LOG = [
  { id: 1, name: 'Phạm Thị D', code: 'GV005', depName: 'Luyện thi',
    date: '2026-06-10', hours: 2.5, rate: 150, reason: 'Dạy bù lớp tối' },
  { id: 2, name: 'Hoàng Văn E', code: 'NV021', depName: 'Marketing',
    date: '2026-06-08', hours: 3, rate: 100, reason: 'Chạy chiến dịch tuyển sinh' },
];
```

- [ ] **Step 2: Xác nhận không còn import `FORGOT_REQUESTS`**

Run: `grep -rn "FORGOT_REQUESTS" frontend/src`
Expected: không có kết quả.

- [ ] **Step 3: Build SPA — xác nhận biên dịch sạch**

Run:
```bash
cd frontend && npm install && npm run build
```
Expected: build thành công, không lỗi import/JSX; output ghi vào `custom-addons/hocba_hrm/static/spa` (file `assets/index-*.js` mới + `index.html` cập nhật hash).

- [ ] **Step 4: Commit (gồm cả bản build SPA)**

```bash
git add frontend/src/features/attendance/mock.js \
        custom-addons/hocba_hrm/static/spa
git commit -m "chore(attendance-ui): bỏ FORGOT_REQUESTS + build SPA (Gói 3)"
```

---

## Task 14: Kiểm thử cuối + bàn giao

- [ ] **Step 1: Chạy lại toàn bộ test backend — xanh, N > 0**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 2: Kiểm thử thủ công SPA (handoff §4 spec)**

- User: mở drawer 1 bản ghi của mình → "Gửi đơn sửa" → điền → gửi; tab "Đơn của tôi" thấy đơn `Chờ duyệt`. Nút "Gửi đơn quên chấm công" → chọn ngày + giờ → gửi.
- Manager: tab "Đơn chấm công" thấy đơn pending theo phạm vi; chỉnh giờ → Duyệt → bảng ngày phản ánh giờ/công mới; Từ chối kèm ghi chú → user thấy trạng thái cập nhật.

- [ ] **Step 3: Cập nhật handoff — đánh dấu Gói 3 XONG**

Modify `docs/superpowers/HANDOFF-attendance-upgrade.md`:
- Bảng §1: đổi trạng thái Gói 3 thành `✅ XONG (đã merge main)`.
- §2: ghi nhận đã thay mock `FORGOT_REQUESTS` bằng luồng thật; cập nhật §6 (thêm plan Gói 3 vào danh sách Plans).

```bash
git add docs/superpowers/HANDOFF-attendance-upgrade.md
git commit -m "docs(attendance): Gói 3 hoàn tất — luồng đơn chấm công (handoff)"
```

- [ ] **Step 4: Merge về `main`**

Dùng skill `superpowers:finishing-a-development-branch`. Trước khi merge: rebase/merge `origin/main` mới nhất, chạy lại test (Step 1) + build (Task 13 Step 3) xác nhận xanh.

---

## Self-Review (đã đối chiếu spec)

- **§1 Model:** Task 1 — đủ field/kiểu/`_order`/ACL theo bảng spec; related `department_id` store; không constraint chéo (ràng buộc thật ở `hocba.attendance._check_dates`). ✅
- **§2.1 `_req_row`:** Task 2 — đủ key camelCase; `attendanceId`/`reviewer`/`reviewNote`/`decisionDate` null-safe; dùng `_dt_local` cho giờ. ✅
- **§2.2 `_request_apply`:** Task 3 — sửa bản ghi / tìm theo (emp, date) / tạo khi thiếu; thiếu check_in → ValidationError. ✅
- **§2.3 Endpoints:** Task 4 (create), Task 6 (mine/pending), Task 5 (approve/reject decide), Task 7 (HTTP wiring) — pin employee, `no_employee`/`rejected`, manager override giờ, kiểm phạm vi 403, `already_decided` 400, 404. ✅
- **§3 Frontend:** Task 8 (api), 9 (RequestForm 2 chế độ), 10 (RequestList user/manager), 11 (tab "Đơn của tôi"+"Đơn chấm công", bỏ ForgotMock), 12 (nút trong drawer), 13 (bỏ FORGOT_REQUESTS, giữ OT_LOG). ✅
- **§4 Test:** Task 2-6 phủ create (pin/utc/reason/foreign), mine, pending (HR/dept-head/non-manager), approve (sửa/tạo/override/thiếu-checkin), reject, ngoài phạm vi, already_decided; fixture official có `identification_id` 12 số (BR-010). ✅
- **§5 Phạm vi:** KHÔNG đụng OT/ca CTV (Gói 4), mail/activity, payroll, logic face/geo. ✅

**Type consistency:** `_request_decide(env, req_id, approve, body)` đồng nhất; controller gọi `_request_decide(...)` qua `_decide_request`. `_req_row` key dùng nhất quán ở FE (`empName`, `code`, `depName`, `requestDate`, `attendanceId`, `checkIn`, `checkOut`, `reason`, `state`, `reviewNote`). API `createRequest/fetchMyRequests/fetchPendingRequests/approveRequest/rejectRequest` khớp giữa `api/attendance.js` và component. `mine`/`pending` trả `{rows: [...]}` → FE đọc `d.rows`. ✅
