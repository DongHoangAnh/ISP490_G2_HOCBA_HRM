# Tách màn chấm công OT/ca — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tách chấm công theo ca (ctv + ot) sang model `hocba.shift.attendance` + màn riêng, để check-in/out OT hoạt động độc lập với chấm công ngày thường; cộng "công ca" vào tổng công.

**Architecture:** Model mới `hocba.shift.attendance` lưu 1 bản ghi/ca, validate theo cửa sổ quanh start/end của ca. `hocba.attendance` chỉ còn cho official ngày thường. Logic face/geo tách thành helper dùng chung. Controller thêm route per-shift; FE thêm màn chấm công ca với nhãn động.

**Tech Stack:** Odoo 19 (Python), React SPA (Vite), test bằng Odoo TransactionCase.

## Global Constraints

- Odoo 19: field nhóm trên `res.users` là `group_ids` (không phải `groups_id`).
- `_OT_RATE = {'100': 1.0, '150': 1.5, '300': 3.0}` — không đổi.
- Giờ chuẩn 1 công = 8 giờ.
- Công ngày thường official giữ nguyên cơ chế nửa-ngày (`work_credit` ∈ {0, 0.5, 1.0}).
- Test chạy LOCAL stack (không chạy trên Neon). Lệnh test ở cuối plan.
- Tiền tệ/đơn vị: "công" là số thực (float), làm tròn 2 chữ số ở tầng API.

---

### Task 1: Model `hocba.shift.attendance` + ACL + đăng ký

**Files:**
- Create: `custom-addons/hocba_attendance/models/hocba_shift_attendance.py`
- Modify: `custom-addons/hocba_attendance/models/__init__.py`
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv`
- Test: `custom-addons/hocba_attendance/tests/test_shift_attendance.py`

**Interfaces:**
- Produces: model `hocba.shift.attendance` với fields `shift_id` (m2o `hocba.work_shift`, unique),
  `employee_id` (related, store), `check_in`, `check_out`, `check_in_photo`, `check_out_photo`,
  `check_in_lat/lng`, `check_out_lat/lng`, `check_in_face_score`, `check_out_face_score`,
  `face_suspect`, `out_of_zone`, `out_of_window`, `worked_hours` (computed float, giờ).

- [ ] **Step 1: Viết test thất bại**

Tạo `custom-addons/hocba_attendance/tests/test_shift_attendance.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from psycopg2 import IntegrityError
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestShiftAttendanceModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV B', 'x_employment_status': 'ctv'})
        self.shift = self.env['hocba.work_shift'].create({
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00', 'end': '2026-06-15 06:00:00',
            'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'})

    def test_worked_hours_and_employee_related(self):
        att = self.env['hocba.shift.attendance'].create({
            'shift_id': self.shift.id,
            'check_in': '2026-06-15 02:00:00',
            'check_out': '2026-06-15 06:00:00'})
        self.assertEqual(att.employee_id, self.emp)
        self.assertAlmostEqual(att.worked_hours, 4.0, places=2)

    def test_worked_hours_zero_without_checkout(self):
        att = self.env['hocba.shift.attendance'].create({
            'shift_id': self.shift.id, 'check_in': '2026-06-15 02:00:00'})
        self.assertEqual(att.worked_hours, 0.0)

    @mute_logger('odoo.sql_db')
    def test_one_record_per_shift(self):
        self.env['hocba.shift.attendance'].create({'shift_id': self.shift.id})
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['hocba.shift.attendance'].create({'shift_id': self.shift.id})
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: lệnh test (cuối plan) với `--test-tags /hocba_attendance:TestShiftAttendanceModel`
Expected: FAIL — `KeyError: 'hocba.shift.attendance'` (model chưa tồn tại).

- [ ] **Step 3: Tạo model**

Tạo `custom-addons/hocba_attendance/models/hocba_shift_attendance.py`:

```python
from odoo import models, fields, api


class ShiftAttendance(models.Model):
    """Chấm công theo CA (ctv/ot) — 1 bản ghi/ca. Tách khỏi hocba.attendance
    (chỉ dùng cho official ngày thường). Giờ công lấy từ check_in/check_out thực tế."""
    _name = 'hocba.shift.attendance'
    _description = 'Chấm công theo ca'
    _order = 'check_in desc'

    shift_id = fields.Many2one(
        'hocba.work_shift', string='Ca', required=True,
        ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        related='shift_id.employee_id', store=True, index=True)
    check_in = fields.Datetime(string='Giờ vào')
    check_out = fields.Datetime(string='Giờ ra')
    check_in_photo = fields.Text(string='Ảnh vào')
    check_out_photo = fields.Text(string='Ảnh ra')
    check_in_lat = fields.Float(string='Lat vào', digits=(10, 7))
    check_in_lng = fields.Float(string='Lng vào', digits=(10, 7))
    check_out_lat = fields.Float(string='Lat ra', digits=(10, 7))
    check_out_lng = fields.Float(string='Lng ra', digits=(10, 7))
    check_in_face_score = fields.Float(string='Điểm khuôn mặt vào')
    check_out_face_score = fields.Float(string='Điểm khuôn mặt ra')
    face_suspect = fields.Boolean(string='Nghi ngờ khuôn mặt')
    out_of_zone = fields.Boolean(string='Ngoài vùng')
    out_of_window = fields.Boolean(string='Ngoài cửa sổ ca')
    worked_hours = fields.Float(
        string='Số giờ chấm', compute='_compute_worked_hours', store=True,
        help='check_out - check_in (giờ); 0 nếu thiếu mốc.')

    _sql_constraints = [
        ('shift_uniq', 'unique(shift_id)',
         'Mỗi ca chỉ có một bản ghi chấm công.'),
    ]

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.worked_hours = (rec.check_out - rec.check_in).total_seconds() / 3600.0
            else:
                rec.worked_hours = 0.0
```

Thêm vào cuối `custom-addons/hocba_attendance/models/__init__.py`:

```python
from . import hocba_shift_attendance
```

Thêm 2 dòng vào cuối `custom-addons/hocba_attendance/security/ir.model.access.csv`:

```csv
access_hocba_shift_attendance_user,access.hocba.shift.attendance.user,model_hocba_shift_attendance,hr.group_hr_user,1,1,1,0
access_hocba_shift_attendance_manager,access.hocba.shift.attendance.manager,model_hocba_shift_attendance,hr.group_hr_manager,1,1,1,1
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: lệnh test với `--test-tags /hocba_attendance:TestShiftAttendanceModel`
Expected: `0 failed, 0 error(s) of 3 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/models/hocba_shift_attendance.py \
  custom-addons/hocba_attendance/models/__init__.py \
  custom-addons/hocba_attendance/security/ir.model.access.csv \
  custom-addons/hocba_attendance/tests/test_shift_attendance.py
git commit -m "feat(attendance): model hocba.shift.attendance (chấm công theo ca)"
```

---

### Task 2: Helper face/geo dùng chung + logic check-in/out trên model ca

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py` (tách helper `_eval_face_geo`, dùng lại trong `_do_check`)
- Modify: `custom-addons/hocba_attendance/models/hocba_shift_attendance.py` (thêm `_assert_allowed`, `_do_check`)
- Test: `custom-addons/hocba_attendance/tests/test_shift_attendance.py` (thêm)

**Interfaces:**
- Consumes: `hocba.attendance._face_distance`, `hocba.attendance._todays_approved_shifts`, `hocba.attendance.policy`.
- Produces:
  - `hocba.attendance._eval_face_geo(employee, payload, policy)` → `{face_score, face_suspect, out_of_zone}`.
  - `hocba.shift.attendance._assert_allowed(shift, kind)` — raise UserError mã:
    `no_shift`, `shift_not_approved`, `outside_shift_window`, `already_checked_in`,
    `not_checked_in`, `already_checked_out`.
  - `hocba.shift.attendance._do_check(shift, payload, kind)` → record (bản ghi shift.attendance).

- [ ] **Step 1: Viết test thất bại**

Thêm vào `test_shift_attendance.py`:

```python
from odoo import fields
from datetime import timedelta
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestShiftAttendanceCheck(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT C', 'x_employment_status': 'official',
            'x_face_descriptor': False})
        self.SA = self.env['hocba.shift.attendance']

    def _shift_now(self, **vals):
        now = fields.Datetime.now()
        base = {'employee_id': self.emp.id, 'start': now, 'end': now + timedelta(hours=2),
                'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'}
        base.update(vals)
        return self.env['hocba.work_shift'].create(base)

    def test_check_in_within_window_creates_record(self):
        s = self._shift_now()
        rec = self.SA._do_check(s, {'descriptor': [], 'latitude': 0, 'longitude': 0}, 'in')
        self.assertTrue(rec.check_in)
        self.assertEqual(rec.shift_id, s)

    def test_assert_outside_window_raises(self):
        s = self._shift_now(start=fields.Datetime.now() + timedelta(hours=5),
                            end=fields.Datetime.now() + timedelta(hours=7))
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'outside_shift_window')

    def test_assert_not_approved_raises(self):
        s = self._shift_now(state='pending')
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'shift_not_approved')

    def test_double_check_in_raises(self):
        s = self._shift_now()
        self.SA._do_check(s, {'descriptor': [], 'latitude': 0, 'longitude': 0}, 'in')
        with self.assertRaises(UserError) as e:
            self.SA._assert_allowed(s, 'in')
        self.assertEqual(str(e.exception), 'already_checked_in')
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `--test-tags /hocba_attendance:TestShiftAttendanceCheck`
Expected: FAIL — `_do_check` / `_assert_allowed` chưa có.

- [ ] **Step 3: Tách helper trong `hr_attendance.py`**

Trong `custom-addons/hocba_attendance/models/hr_attendance.py`, thêm method (đặt ngay trên `_do_check`, sau `_face_distance`):

```python
    @api.model
    def _eval_face_geo(self, employee, payload, policy):
        """Tính face_score/face_suspect/out_of_zone dùng chung cho chấm công
        ngày thường và chấm công ca."""
        face_score = None
        enrolled = []
        if employee.x_face_descriptor:
            try:
                enrolled = json.loads(employee.x_face_descriptor)
            except (ValueError, TypeError):
                enrolled = []
        dist = self._face_distance(payload.get('descriptor') or [], enrolled)
        if dist is None:
            face_suspect = True
        else:
            face_score = dist
            face_suspect = dist > policy.face_threshold
        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0
        if policy.office_lat and policy.office_lng:
            out_of_zone = not policy.is_within_office(lat, lng)
        else:
            out_of_zone = False
        return {'face_score': face_score, 'face_suspect': face_suspect,
                'out_of_zone': out_of_zone}
```

Trong `_do_check` của `hocba.attendance`, thay khối tính face/geo (đoạn từ `# Face matching`
tới hết tính `out_of_zone`, hiện ~dòng 233-254) bằng:

```python
        fg = self._eval_face_geo(employee, payload, policy)
        face_score = fg['face_score']
        face_suspect = fg['face_suspect']
        out_of_zone = fg['out_of_zone']
```

(Giữ nguyên phần `out_of_window` và phần ghi record phía dưới.)

- [ ] **Step 4: Thêm logic check trên model ca**

Trong `custom-addons/hocba_attendance/models/hocba_shift_attendance.py`, thêm:

```python
    @api.model
    def _assert_allowed(self, shift, kind):
        """Validate chấm công 1 ca. Raise UserError mã lỗi để controller map HTTP."""
        if not shift or not shift.exists():
            raise UserError('no_shift')
        if shift.state != 'approved':
            raise UserError('shift_not_approved')
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        window = policy.shift_window_minutes or 15
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'),
            fields.Datetime.now()).replace(tzinfo=None)
        anchor_utc = shift.start if kind == 'in' else shift.end
        anchor = fields.Datetime.context_timestamp(
            shift, anchor_utc).replace(tzinfo=None)
        if abs((now_local - anchor).total_seconds()) > window * 60:
            raise UserError('outside_shift_window')
        rec = self.sudo().search([('shift_id', '=', shift.id)], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')

    @api.model
    def _do_check(self, shift, payload, kind):
        """Ghi chấm công cho ca. Tái dùng face/geo của hocba.attendance.
        out_of_window: ngoài cửa sổ ±W quanh start (in) / end (out)."""
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        employee = shift.employee_id
        fg = self.env['hocba.attendance']._eval_face_geo(employee, payload, policy)
        now = fields.Datetime.now()
        window = policy.shift_window_minutes or 15
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'), now).replace(tzinfo=None)
        anchor = fields.Datetime.context_timestamp(
            shift, shift.start if kind == 'in' else shift.end).replace(tzinfo=None)
        out_of_window = abs((now_local - anchor).total_seconds()) > window * 60
        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        rec = self.sudo().search([('shift_id', '=', shift.id)], limit=1)
        if kind == 'in':
            vals = {'check_in': now, 'check_in_photo': payload.get('photo'),
                    'check_in_lat': lat, 'check_in_lng': lng}
            if fg['face_score'] is not None:
                vals['check_in_face_score'] = fg['face_score']
        else:
            vals = {'check_out': now, 'check_out_photo': payload.get('photo'),
                    'check_out_lat': lat, 'check_out_lng': lng}
            if fg['face_score'] is not None:
                vals['check_out_face_score'] = fg['face_score']
        vals.update({'face_suspect': fg['face_suspect'],
                     'out_of_zone': fg['out_of_zone'], 'out_of_window': out_of_window})
        if rec:
            rec.write(vals)
        else:
            vals['shift_id'] = shift.id
            rec = self.create(vals)
        return rec
```

- [ ] **Step 5: Chạy test — phải PASS (cả TestShiftAttendanceCheck và bộ test attendance cũ)**

Run: `--test-tags /hocba_attendance`
Expected: `0 failed, 0 error(s) of N tests` (N > số test cũ; bao gồm 4 test mới).

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py \
  custom-addons/hocba_attendance/models/hocba_shift_attendance.py \
  custom-addons/hocba_attendance/tests/test_shift_attendance.py
git commit -m "feat(attendance): logic check-in/out theo ca + helper face/geo dùng chung"
```

---

### Task 3: Controller route chấm công ca + `shiftsToday` trong `/me`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_shift_attendance_api.py` (create)

**Interfaces:**
- Consumes: `hocba.shift.attendance._assert_allowed`, `._do_check`; `_att_me_info`.
- Produces:
  - `_shift_today_rows(env, emp)` → list dict (camelCase) cho `me.shiftsToday`.
  - `_shift_check(env, shift_id, kind, payload)` → dict `{recordId, kind, faceSuspect, outOfZone, outOfWindow, faceScore}`; raise UserError mã / AccessError.
  - Routes `POST /hocba-hrm/api/attendance/shift/<int:shift_id>/check-in` và `.../check-out`.
  - `_att_me_info` trả thêm `shiftsToday: [...]`.

- [ ] **Step 1: Viết test thất bại**

Tạo `custom-addons/hocba_hrm/tests/test_shift_attendance_api.py`:

```python
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError, AccessError

from odoo.addons.hocba_hrm.controllers.main import _shift_check, _shift_today_rows


@tagged('post_install', '-at_install')
class TestShiftAttendanceApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT D', 'x_employment_status': 'official'})
        self.user = self.env['res.users'].create({
            'name': 'OT D User', 'login': 'ot_d_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user

    def _shift_now(self, **vals):
        now = fields.Datetime.now()
        base = {'employee_id': self.emp.id, 'start': now, 'end': now + timedelta(hours=2),
                'shift_type': 'ot', 'ot_level': '150', 'state': 'approved'}
        base.update(vals)
        return self.env['hocba.work_shift'].create(base)

    def test_shift_today_rows_shape(self):
        s = self._shift_now()
        env = self.env(user=self.user)
        rows = _shift_today_rows(env, self.emp)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], s.id)
        self.assertTrue(rows[0]['checkInOpen'])
        self.assertFalse(rows[0]['checkIn'])

    def test_shift_check_in_then_out(self):
        s = self._shift_now()
        env = self.env(user=self.user)
        res = _shift_check(env, s.id, 'in', {'descriptor': [], 'latitude': 0, 'longitude': 0})
        self.assertEqual(res['kind'], 'in')
        att = env['hocba.shift.attendance'].search([('shift_id', '=', s.id)])
        self.assertTrue(att.check_in)

    def test_shift_check_other_employee_forbidden(self):
        other = self.env['hr.employee'].create({'name': 'X', 'x_employment_status': 'official'})
        s = self._shift_now(employee_id=other.id)
        env = self.env(user=self.user)
        with self.assertRaises(AccessError):
            _shift_check(env, s.id, 'in', {'descriptor': [], 'latitude': 0, 'longitude': 0})
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `--test-tags /hocba_hrm:TestShiftAttendanceApi`
Expected: FAIL — `ImportError: cannot import name '_shift_check'`.

> Nếu lần đầu test `hocba_hrm` trên local: dùng `-i hocba_hrm` thay `-u` (xem ghi chú cuối plan).

- [ ] **Step 3: Thêm helper + route trong `main.py`**

Thêm gần nhóm hàm OT (sau `_ot_table`, trước phần routes). Lưu ý dùng `_dt_local`, `_user_can_manage`, `_emp_in_scope` đã có sẵn:

```python
def _shift_today_rows(env, emp):
    """Ca approved hôm nay của emp (local) + trạng thái chấm cho màn chấm công ca."""
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    window = policy.shift_window_minutes or 15
    now_local = fields.Datetime.context_timestamp(
        env.user, fields.Datetime.now()).replace(tzinfo=None)
    today = now_local.date()
    shifts = env['hocba.attendance']._todays_approved_shifts(emp, today)
    rows = []
    for s in shifts:
        att = env['hocba.shift.attendance'].sudo().search(
            [('shift_id', '=', s.id)], limit=1)
        ci_anchor = fields.Datetime.context_timestamp(s, s.start).replace(tzinfo=None)
        co_anchor = fields.Datetime.context_timestamp(s, s.end).replace(tzinfo=None)
        has_in = bool(att and att.check_in)
        has_out = bool(att and att.check_out)
        rows.append({
            'id': s.id,
            'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
            'shiftType': s.shift_type, 'otLevel': s.ot_level, 'rate': s.rate,
            'checkIn': _dt_local(att, att.check_in) if has_in else None,
            'checkOut': _dt_local(att, att.check_out) if has_out else None,
            'checkInOpen': (not has_in) and abs((now_local - ci_anchor).total_seconds()) <= window * 60,
            'checkOutOpen': has_in and (not has_out) and abs((now_local - co_anchor).total_seconds()) <= window * 60,
            'faceSuspect': att.face_suspect if att else False,
            'outOfZone': att.out_of_zone if att else False,
            'outOfWindow': att.out_of_window if att else False,
        })
    return rows


def _shift_check(env, shift_id, kind, payload):
    """Chấm công 1 ca cho user hiện tại. Raise AccessError nếu ca không thuộc user."""
    emp = env.user.employee_id
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists() or not emp or shift.employee_id.id != emp.id:
        raise AccessError('forbidden')
    SA = env['hocba.shift.attendance'].sudo()
    SA._assert_allowed(shift, kind)
    rec = SA._do_check(shift, payload, kind)
    return {
        'recordId': rec.id, 'kind': kind,
        'faceSuspect': rec.face_suspect, 'outOfZone': rec.out_of_zone,
        'outOfWindow': rec.out_of_window,
        'faceScore': (rec.check_in_face_score if kind == 'in'
                      else rec.check_out_face_score),
    }
```

Thêm route (cạnh `api_attendance_check`, dùng `_CHECK_ERR_STATUS` đã có; bổ sung mã mới vào dict đó):

```python
    @http.route(['/hocba-hrm/api/attendance/shift/<int:shift_id>/check-in',
                 '/hocba-hrm/api/attendance/shift/<int:shift_id>/check-out'],
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_shift_attendance_check(self, shift_id, **kw):
        if not request.env.user.employee_id:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if _user_can_manage(request.env):
            return request.make_json_response({'error': 'manager_no_checkin'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        try:
            res = _shift_check(request.env, shift_id, kind, {
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
            })
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except UserError as ex:
            code = str(ex)
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': code}, status=_CHECK_ERR_STATUS.get(code, 400))
        return request.make_json_response(res)
```

Bổ sung mã lỗi mới vào `_CHECK_ERR_STATUS` (tìm dict này trong main.py, thêm key thiếu):

```python
    'no_shift': 404,
    'shift_not_approved': 409,
```

(`outside_shift_window`, `already_checked_in`, `not_checked_in`, `already_checked_out` đã có sẵn.)

Trong `_att_me_info` (sau khi set `info['shiftToday']`), thêm:

```python
    info['shiftsToday'] = _shift_today_rows(env, emp)
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `--test-tags /hocba_hrm:TestShiftAttendanceApi`
Expected: `0 failed, 0 error(s) of 3 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
  custom-addons/hocba_hrm/tests/test_shift_attendance_api.py
git commit -m "feat(attendance-api): route chấm công ca + shiftsToday trong /me"
```

---

### Task 4: Hệ số theo loại ca (CTV cố định 100%)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`_shift_create`, `_shift_set_level`)
- Test: `custom-addons/hocba_hrm/tests/test_shift_api.py` (thêm)

**Interfaces:**
- Consumes: `_shift_create`, `_shift_set_level` (đã có).
- Produces: hành vi — `_shift_create` ép `ot_level='100'` khi `shiftType=='ctv'`;
  `_shift_set_level` raise ValidationError khi `shift.shift_type=='ctv'`.

- [ ] **Step 1: Viết test thất bại**

Thêm vào `custom-addons/hocba_hrm/tests/test_shift_api.py` (class `TestShiftApi`):

```python
    def test_ctv_forced_level_100(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'otLevel': '300', 'reason': 'x'})
        self.assertEqual(row['otLevel'], '100')
        self.assertEqual(row['rate'], 1.0)

    def test_set_level_blocked_for_ctv(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        s = self._make_shift(shift_type='ctv', state='approved', ot_level='100')
        env = self.env(user=self.hrm)
        with self.assertRaises(ValidationError):
            _shift_set_level(env, s.id, '150')
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `--test-tags /hocba_hrm:TestShiftApi.test_ctv_forced_level_100,/hocba_hrm:TestShiftApi.test_set_level_blocked_for_ctv`
(hoặc chạy cả `--test-tags /hocba_hrm`)
Expected: FAIL — CTV vẫn nhận level 300; `_shift_set_level` không chặn.

- [ ] **Step 3: Sửa `_shift_create` và `_shift_set_level`**

Trong `_shift_create` (main.py ~577-613), sau khi xác định `shift_type` và `level`, thêm:

```python
        if shift_type == 'ctv':
            level = '100'   # CTV cố định 100%, bỏ qua giá trị client gửi
```

(đặt ngay sau dòng `level = body.get('otLevel') or '100'` và sau khi validate `level in (...)`.)

Trong `_shift_set_level` (main.py ~692-706), sau khi browse shift và kiểm tra tồn tại/quyền,
thêm trước `shift.write`:

```python
        if shift.shift_type == 'ctv':
            raise ValidationError('Ca CTV cố định hệ số 100%.')
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `--test-tags /hocba_hrm:TestShiftApi`
Expected: `0 failed, 0 error(s)` — gồm 2 test mới và các test cũ vẫn xanh.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift): CTV cố định hệ số 100% (backend ép + chặn override)"
```

---

### Task 5: Tính "công ca" + cộng vào tổng công

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`_ot_row`, `_ot_for_employee`, `_ot_table`, `_att_me_history`)
- Test: `custom-addons/hocba_hrm/tests/test_ot_credit.py` (create)

**Interfaces:**
- Consumes: `hocba.shift.attendance`.
- Produces:
  - `_ot_row` trả thêm `congCa` (= `round(hours/8*rate,2)` nếu counted, else 0); `hours` = giờ chấm thực tế, `counted` = có check_in trên shift.attendance.
  - `_ot_for_employee` trả `{otHours, otCong}` (giờ OT thực tế + công OT).
  - `_ot_table.totals` trả `otHours`, `otCong`, `count`, `countedCount`.
  - `_att_me_history.summary`: `totalCredit` gồm `Σ congCa`; thêm `congOt = Σ congCa`.

- [ ] **Step 1: Viết test thất bại**

Tạo `custom-addons/hocba_hrm/tests/test_ot_credit.py`:

```python
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _ot_row, _ot_for_employee


@tagged('post_install', '-at_install')
class TestOtCredit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'OT E', 'x_employment_status': 'official'})
        self.env.user.tz = 'Asia/Ho_Chi_Minh'

    def _shift(self, level='150'):
        return self.env['hocba.work_shift'].create({
            'employee_id': self.emp.id,
            'start': '2026-06-15 01:00:00', 'end': '2026-06-15 09:00:00',
            'shift_type': 'ot', 'ot_level': level, 'state': 'approved'})

    def test_cong_ca_from_actual_hours(self):
        s = self._shift(level='150')   # rate 1.5
        self.env['hocba.shift.attendance'].create({
            'shift_id': s.id,
            'check_in': '2026-06-15 01:00:00',
            'check_out': '2026-06-15 09:00:00'})   # 8 giờ thực tế
        row = _ot_row(self.env, s)
        self.assertEqual(row['hours'], 8.0)
        self.assertTrue(row['counted'])
        self.assertEqual(row['congCa'], 1.5)        # 8/8 * 1.5

    def test_not_counted_without_checkin(self):
        s = self._shift()
        row = _ot_row(self.env, s)
        self.assertFalse(row['counted'])
        self.assertEqual(row['congCa'], 0.0)

    def test_employee_total_cong(self):
        s = self._shift(level='100')
        self.env['hocba.shift.attendance'].create({
            'shift_id': s.id,
            'check_in': '2026-06-15 01:00:00',
            'check_out': '2026-06-15 05:00:00'})   # 4 giờ
        res = _ot_for_employee(self.env, self.emp,
                               fields.Date.from_string('2026-06-01'),
                               fields.Date.from_string('2026-06-30'))
        self.assertEqual(res['otHours'], 4.0)
        self.assertEqual(res['otCong'], 0.5)        # 4/8 * 1.0
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `--test-tags /hocba_hrm:TestOtCredit`
Expected: FAIL — `_ot_row` chưa có `congCa`; `_ot_for_employee` trả `otCreditHours` chứ không `otCong`.

- [ ] **Step 3: Sửa các hàm tính công**

Thay `_ot_row` (main.py ~247-266):

```python
def _ot_row(env, s):
    """Một ca cho SPA + công ca theo giờ chấm THỰC TẾ (hocba.shift.attendance).
    counted = ca đã check-in; congCa = giờ_chấm/8 × hệ số (0 nếu chưa chấm)."""
    att = env['hocba.shift.attendance'].sudo().search([('shift_id', '=', s.id)], limit=1)
    hours = att.worked_hours if att else 0.0
    counted = bool(att and att.check_in)
    d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
    emp = s.employee_id
    return {
        'id': s.id, 'empId': emp.id, 'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'date': _d(d) if d else None,
        'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
        'shiftType': s.shift_type, 'otLevel': s.ot_level, 'rate': s.rate,
        'hours': round(hours, 2), 'counted': counted,
        'congCa': round((hours / 8.0) * s.rate, 2) if counted else 0.0,
        'state': s.state,
    }
```

Thay `_ot_for_employee` (main.py ~269-282) phần return:

```python
    return {
        'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
        'otCong': round(sum(r['congCa'] for r in rows), 2),
    }
```

Thay `_ot_table.totals` (main.py ~317-321):

```python
        'totals': {
            'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
            'otCong': round(sum(r['congCa'] for r in rows), 2),
            'count': len(rows),
            'countedCount': sum(1 for r in rows if r['counted']),
        },
```

Trong `_att_me_history` (main.py ~326-367): tìm chỗ gọi `_ot_for_employee` (đang lấy
`otHours`/`otCreditHours`) và `total_credit`. Sửa summary:

```python
    ot = _ot_for_employee(env, emp, first, last)
    summary = {
        # ... các field cũ giữ nguyên (daysPresent, deficitCredit, netCredit ...) ...
        'totalCredit': round(total_credit + ot['otCong'], 2),
        'congOt': ot['otCong'],
        'otHours': ot['otHours'],
    }
```

Lưu ý: `netCredit` hiện = `total_credit - deficit_credit`. Đổi để cũng gồm công ca:
`'netCredit': round(total_credit + ot['otCong'] - deficit_credit, 2)`.
Bỏ field `otCreditHours` cũ (FE sẽ dùng `congOt`).

- [ ] **Step 4: Chạy test — phải PASS**

Run: `--test-tags /hocba_hrm:TestOtCredit`
Expected: `0 failed, 0 error(s) of 3 tests`. Chạy thêm `--test-tags /hocba_hrm` để chắc không vỡ test cũ (sửa test cũ nào còn tham chiếu `otCreditHours`/`creditHours` nếu có).

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_ot_credit.py
git commit -m "feat(ot): công ca theo giờ chấm thực tế (giờ/8×hệ số) + cộng vào tổng công"
```

---

### Task 6: Frontend — API + màn chấm công ca + nhãn động

**Files:**
- Modify: `frontend/src/api/attendance.js`
- Create: `frontend/src/features/attendance/ShiftAttendance.jsx`
- Modify: `frontend/src/features/attendance/Attendance.jsx`
- Modify: `frontend/src/features/attendance/CheckInPanel.jsx`
- Modify: `frontend/src/features/attendance/ShiftForm.jsx`

**Interfaces:**
- Consumes: `me.shiftsToday` (Task 3), routes `shift/<id>/check-in|out`, `useFaceApi`, `fmtTime`.
- Produces: component `ShiftAttendance` (default export) nhận `{ me, onChanged }`.

- [ ] **Step 1: Thêm API**

Thêm vào cuối `frontend/src/api/attendance.js`:

```javascript
export const shiftCheckIn = (shiftId, payload) =>
  hbPost(`/hocba-hrm/api/attendance/shift/${shiftId}/check-in`, payload);
export const shiftCheckOut = (shiftId, payload) =>
  hbPost(`/hocba-hrm/api/attendance/shift/${shiftId}/check-out`, payload);
```

- [ ] **Step 2: Tạo `ShiftAttendance.jsx`**

```jsx
/* Màn chấm công theo ca (ctv/ot). Nhãn do Attendance.jsx quyết định.
   Mỗi ca approved hôm nay là 1 thẻ camera + nút check-in/out. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useFaceApi } from './useFaceApi';
import { enrollFace, shiftCheckIn, shiftCheckOut } from '../../api/attendance';
import { fmtTime } from './util';

const ERR = {
  no_shift: 'Không tìm thấy ca.',
  shift_not_approved: 'Ca chưa được duyệt.',
  outside_shift_window: 'Ngoài cửa sổ chấm công của ca (±15 phút).',
  already_checked_in: 'Ca này đã check-in rồi.',
  not_checked_in: 'Chưa check-in nên không thể check-out.',
  already_checked_out: 'Ca này đã check-out rồi.',
  forbidden: 'Ca không thuộc về bạn.',
  manager_no_checkin: 'Tài khoản quản lý không điểm danh.',
};

export default function ShiftAttendance({ me, onChanged }) {
  const { videoRef, ready, camError, capture } = useFaceApi();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [enrolled, setEnrolled] = useState(me.enrolled);
  const shifts = me.shiftsToday || [];

  async function doEnroll() {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không thấy khuôn mặt. Thử lại.' }); return; }
      await enrollFace(cap.photo, cap.descriptor);
      setEnrolled(true);
      setMsg({ kind: 'ok', text: 'Đăng ký khuôn mặt thành công.' });
    } catch (e) { setMsg({ kind: 'err', text: 'Đăng ký thất bại (' + e.message + ').' }); }
    finally { setBusy(false); }
  }

  async function doCheck(shiftId, kind) {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không thấy khuôn mặt. Thử lại.' }); return; }
      const res = await (kind === 'in' ? shiftCheckIn(shiftId, cap) : shiftCheckOut(shiftId, cap));
      const flags = [];
      if (res.faceSuspect) flags.push('khuôn mặt nghi ngờ');
      if (res.outOfZone) flags.push('ngoài vùng văn phòng');
      setMsg({ kind: flags.length ? 'warn' : 'ok',
        text: (kind === 'in' ? 'Đã check-in' : 'Đã check-out') + (flags.length ? ' ⚠ ' + flags.join(', ') : ' thành công') });
      onChanged && onChanged();
    } catch (e) { setMsg({ kind: 'err', text: ERR[e.code] || ('Chấm công thất bại (' + e.message + ').') }); }
    finally { setBusy(false); }
  }

  return (
    <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start' }}>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', display: 'block', background: '#000', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        {camError && <div className="empty" style={{ color: 'var(--red-600)' }}>{camError}</div>}
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{me.name}</div>
        <div className="divider" style={{ margin: '14px 0' }}></div>

        {!enrolled ? (
          <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
            <Icon name="user" size={16} />Đăng ký khuôn mặt
          </button>
        ) : shifts.length === 0 ? (
          <div className="empty">Chưa có ca được duyệt hôm nay.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {shifts.map((s) => (
              <div key={s.id} style={{ borderTop: '1px solid var(--line)', paddingTop: 12 }}>
                <div className="muted" style={{ fontSize: 12.5, marginBottom: 8 }}>
                  Ca <b className="mono">{fmtTime(s.start)}–{fmtTime(s.end)}</b>
                  {' '}· {s.shiftType === 'ctv' ? 'CTV' : 'OT'} ×{s.rate} · ±15'
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  {s.checkIn ? (
                    <Badge kind="green" dot>Vào {fmtTime(s.checkIn)}</Badge>
                  ) : (
                    <button className="btn btn-primary btn-sm" disabled={busy || !ready || !s.checkInOpen}
                      onClick={() => doCheck(s.id, 'in')}>
                      <Icon name="checkCircle" size={15} />Check-in
                    </button>
                  )}
                  {s.checkOut ? (
                    <Badge kind="gray" dot>Ra {fmtTime(s.checkOut)}</Badge>
                  ) : (
                    <button className="btn btn-ghost btn-sm" disabled={busy || !ready || !s.checkOutOpen}
                      onClick={() => doCheck(s.id, 'out')}>
                      <Icon name="logout" size={15} />Check-out
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {!ready && !camError && <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>Đang khởi tạo camera…</div>}
        {msg && (
          <div style={{ marginTop: 12, fontSize: 13, fontWeight: 600,
            color: msg.kind === 'ok' ? 'var(--green)' : msg.kind === 'warn' ? 'var(--amber)' : 'var(--red-600)' }}>
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Sửa `Attendance.jsx` — thêm tab + nhãn động**

Thêm import:

```jsx
import ShiftAttendance from './ShiftAttendance';
```

Sửa danh sách tabs NV (dòng ~39-40) — nhãn động theo `me.isOfficial`:

```jsx
  const shiftTabLabel = me.isOfficial ? 'Chấm công OT' : 'Chấm công';
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Ca làm việc (CTV/OT)'], ['otpay', 'Chấm công OT']]
    : [['me', 'Chấm công của tôi'], ['shift', shiftTabLabel], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
```

Thêm render khối tab `shift` (cạnh khối `me`):

```jsx
      {activeTab === 'shift' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <ShiftAttendance me={me} onChanged={load} />
        </div>
      )}
```

- [ ] **Step 4: Sửa `CheckInPanel.jsx` — bỏ nhánh non-official**

Thay toàn bộ block điều kiện `{!me.isOfficial ? (...) : !enrolled ? (...)}` (dòng 96-157) bằng:
chỉ giữ luồng official. Cho non-official hiện điều hướng. Tức thay đoạn `{!me.isOfficial ? (` ... đến trước `) : !enrolled ? (` bằng:

```jsx
        {!me.isOfficial ? (
          <div className="empty">Bạn chấm công theo ca ở tab “Chấm công”.</div>
        ) : !enrolled ? (
```

(giữ nguyên phần official từ `!enrolled ? (...)` trở đi). Cũng có thể đơn giản: vì tab `shift`
đã tách, official vẫn dùng panel này cho ngày thường; non-official chỉ thấy thông báo.

- [ ] **Step 5: Sửa `ShiftForm.jsx` — ẩn ô hệ số khi CTV**

Bọc khối `<label>Mức hệ số ...</label>` bằng điều kiện:

```jsx
        {form.shiftType === 'ot' && (
          <label style={{ fontSize: 12.5 }}>Mức hệ số
            <select className="sel" value={form.otLevel}
              onChange={(e) => setForm({ ...form, otLevel: e.target.value })}>
              <option value="100">100%</option>
              <option value="150">150%</option>
              <option value="300">300%</option>
            </select>
          </label>
        )}
```

Khi `shiftType === 'ctv'`, đảm bảo gửi `otLevel: '100'` (backend cũng ép — Task 4). Trong handler
đổi loại ca, set lại `otLevel: '100'` khi chọn ctv:

```jsx
            onChange={(e) => setForm({ ...form, shiftType: e.target.value,
              otLevel: e.target.value === 'ctv' ? '100' : form.otLevel })}
```

- [ ] **Step 6: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công, tạo `frontend/dist` → copy vào `static/spa` (theo quy trình build hiện có của dự án — kiểm tra script `build` trong `frontend/package.json` xem có tự copy không; nếu không, copy `dist/*` sang `custom-addons/hocba_hrm/static/spa/`).

- [ ] **Step 7: Commit**

```bash
git add frontend/src custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): màn chấm công ca riêng + nhãn động + ẩn hệ số CTV"
```

---

### Task 7: Cập nhật nhãn MyHistory & OtTable

**Files:**
- Modify: `frontend/src/features/attendance/MyHistory.jsx`
- Modify: `frontend/src/features/attendance/OtTable.jsx`

**Interfaces:**
- Consumes: `summary.congOt`, `summary.totalCredit` (Task 5); `row.congCa`, `totals.otCong`.

- [ ] **Step 1: Sửa MyHistory.jsx**

Đổi card "Giờ OT quy đổi" → "Công OT" dùng `data.summary.congOt`:

```jsx
        <Sum val={data.summary.otHours} lbl="Giờ OT" />
        <Sum val={data.summary.congOt} lbl="Công OT" col="var(--green)" />
```

(Bỏ tham chiếu `otCreditHours` cũ.)

- [ ] **Step 2: Sửa OtTable.jsx**

- Card "Giờ OT quy đổi" → "Công" dùng `data.totals.otCong`:

```jsx
          {data.totals.otCong}
          ...
          <div className="stat-lbl" style={{ marginTop: 4 }}>Tổng công ca</div>
```

- Header cột "Giờ quy đổi" → "Công"; ô dữ liệu dùng `r.congCa`:

```jsx
          <th className="tbl-num">Công</th>
          ...
          <td className="tbl-num mono" style={{ fontWeight: 600, color: r.counted ? 'var(--green)' : undefined }}>
            {r.congCa}
          </td>
```

- Dropdown mức chỉ bật cho ca `ot` (CTV cố định 100%):

```jsx
                {data.canManage && r.shiftType === 'ot' ? (
                  <select className="sel" value={r.otLevel} disabled={busyId === r.id}
                    onChange={(e) => changeLevel(r.id, e.target.value)}>
                    {LEVELS.map((l) => <option key={l} value={l}>{l}%</option>)}
                  </select>
                ) : `${r.otLevel}%`}
```

- [ ] **Step 3: Build SPA**

Run: `cd frontend && npm run build` (rồi copy sang static/spa như Task 6 Step 6).

- [ ] **Step 4: Commit**

```bash
git add frontend/src custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): MyHistory/OtTable hiển thị Công ca thay Giờ quy đổi"
```

---

### Task 8: Verify end-to-end thủ công

**Files:** none (kiểm thử)

- [ ] **Step 1: Chạy toàn bộ test backend**

Run: `--test-tags /hocba_attendance` và `--test-tags /hocba_hrm`
Expected: cả hai `0 failed, 0 error(s) of N tests` (N > 0).

- [ ] **Step 2: Deploy local & thử tay**

- Upgrade module local: `-u hocba_attendance,hocba_hrm`.
- Đăng nhập NV official có ca OT approved hôm nay → tab "Chấm công OT" hiện ca, check-in/out trong cửa sổ hoạt động; tab "Chấm công của tôi" vẫn chấm ngày thường độc lập.
- Đăng nhập CTV → tab "Chấm công" hiện ca, hệ số ẩn (cố định 100%) khi đăng ký.
- MyHistory: "Công OT" và "Tổng công" gồm công ca. OtTable (manager): cột "Công", dropdown chỉ ở ca OT.

- [ ] **Step 3: Commit cuối (nếu có chỉnh)**

```bash
git add -A && git commit -m "chore(attendance): hoàn tất tách màn chấm công OT/ca"
```

---

## Ghi chú chạy test (local stack)

Lệnh (Windows Git Bash — bắt buộc prefix MSYS để tag `/...` không bị mangle):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_hrm \
  --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
```

- `--addons-path=/mnt/extra-addons` BẮT BUỘC trên dòng lệnh.
- Đổi `--test-tags` theo task (vd `/hocba_hrm:TestShiftAttendanceApi`).
- Tìm dòng `0 failed, 0 error(s) of N tests` với N > 0 (`of 0 tests` = không thu được test).
- **Lần đầu test `hocba_hrm` trên local**: module có thể chưa cài → dùng `-i hocba_hrm` (thay `-u`) một lần; sau đó `-u` dùng bình thường.

## Self-Review (đã rà)

- Spec coverage: model mới (T1), check logic + helper (T2), routes + shiftsToday (T3), hệ số CTV (T4), công ca + tổng công (T5), FE màn/nhãn/form (T6), MyHistory/OtTable (T7), verify (T8). Đủ.
- Type consistency: `congCa` (row), `otCong` (totals/summary), `congOt` (history summary), `shiftsToday[]` (me) — dùng nhất quán giữa BE và FE.
- Placeholder: không có TODO/“tương tự task N”; code đầy đủ.
