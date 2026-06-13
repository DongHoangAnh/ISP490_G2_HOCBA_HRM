# Màn Chấm công SPA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng màn Chấm công cho SPA Học Bá HRM: tự chấm công face/geo + lịch sử cá nhân theo tháng cho mọi nhân viên, bảng giám sát theo ngày cho HR/manager; gỡ kiosk Odoo cũ.

**Architecture:** Backend thêm 6 route HTTP `/hocba-hrm/api/attendance/*` trong `hocba_hrm/controllers/main.py`, tái dùng logic model có sẵn (`_do_check`, `enroll_self_face`, `get_self_attendance_info`). Phần serialize/query tách thành **hàm module thuần** để unit-test bằng `TransactionCase` (route chỉ là vỏ mỏng). Frontend là feature React độc lập trong `features/attendance/`, theo đúng mẫu màn Nhân viên (3 trạng thái loading/error/data, component chung, wire format camelCase).

**Tech Stack:** Odoo 19 (Python, `http.Controller`), React + Vite, face-api.js (đã vendor ở `hocba_employees/static/lib/face-api/`).

**Spec:** [docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md](../specs/2026-06-13-attendance-spa-screen-design.md)

---

## File Structure

**Backend (`custom-addons/hocba_hrm/`)**
- Modify `__manifest__.py` — thêm dependency `hocba_attendance`.
- Modify `__init__.py` — thêm `from . import tests`.
- Modify `controllers/main.py` — thêm helper functions + 6 route attendance.
- Create `tests/__init__.py`, `tests/test_attendance_api.py` — unit test helpers.

**Backend (`custom-addons/hocba_attendance/`) — gỡ kiosk**
- Modify `__manifest__.py` — bỏ 3 asset kiosk.
- Modify `views/menus.xml` — bỏ action+menu "My Attendance".
- Delete `static/src/js/attendance_kiosk.js`, `static/src/xml/attendance_kiosk.xml`, `static/src/scss/attendance_kiosk.scss`.

**Frontend (`frontend/`)**
- Modify `vite.config.js` `[CHUNG]` — proxy `/hocba_employees/static`.
- Modify `src/app/App.jsx` `[CHUNG]` — render `<Attendance>`.
- Create `src/api/attendance.js` — wrapper API.
- Create `src/features/attendance/util.js` — `fmtTime`, `attStatus`.
- Create `src/features/attendance/useFaceApi.js` — hook camera + face-api.
- Create `src/features/attendance/CheckInPanel.jsx`
- Create `src/features/attendance/MyHistory.jsx`
- Create `src/features/attendance/AttendanceTable.jsx`
- Create `src/features/attendance/AttendanceDrawer.jsx`
- Create `src/features/attendance/mock.js`
- Create `src/features/attendance/Attendance.jsx`

> **Lưu ý ownership:** `vite.config.js` và `App.jsx` là file `[CHUNG]` — cần FE-lead (Tân) review trong PR.

---

## PHASE A — Backend API & tests

### Task A1: Thêm dependency + scaffolding tests

**Files:**
- Modify: `custom-addons/hocba_hrm/__manifest__.py:13`
- Modify: `custom-addons/hocba_hrm/__init__.py`
- Create: `custom-addons/hocba_hrm/tests/__init__.py`

- [ ] **Step 1: Thêm `hocba_attendance` vào depends**

Trong `custom-addons/hocba_hrm/__manifest__.py`, sửa dòng `depends`:
```python
    'depends': ['base', 'hr', 'hocba_employees', 'hocba_attendance'],
```

- [ ] **Step 2: Wire tests vào module**

Trong `custom-addons/hocba_hrm/__init__.py`:
```python
from . import controllers
from . import tests
```

- [ ] **Step 3: Tạo package tests**

Tạo `custom-addons/hocba_hrm/tests/__init__.py`:
```python
from . import test_attendance_api
```

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_hrm/__manifest__.py custom-addons/hocba_hrm/__init__.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "chore(hocba_hrm): depend on hocba_attendance + tests scaffolding"
```

---

### Task A2: Helper functions serialize/query + tests (TDD)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Create: `custom-addons/hocba_hrm/tests/test_attendance_api.py`

- [ ] **Step 1: Viết test thất bại**

Tạo `custom-addons/hocba_hrm/tests/test_attendance_api.py`:
```python
import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _fmt_hm, _att_me_info, _att_day_table, _att_me_history,
)


@tagged('post_install', '-at_install')
class TestAttendanceApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
            'office_lat': 0.0, 'office_lng': 0.0,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Chinh Thuc',
            'x_employment_status': 'official',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })
        self.emp_user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'nv_att_user',
        })
        self.emp.user_id = self.emp_user
        self.hr_user = self.env['res.users'].create({
            'name': 'HR User', 'login': 'hr_att_user',
            'groups_id': [(4, self.env.ref('hr.group_hr_manager').id)],
        })

    def _checkin(self, emp):
        return self.env['hocba.attendance']._do_check({
            'employee_id': emp.id, 'photo': 'ZmFrZQ==',
            'descriptor': [0.0] * 128, 'latitude': 0.0, 'longitude': 0.0,
        }, 'in')

    def test_fmt_hm(self):
        self.assertEqual(_fmt_hm(8.0), '08:00')
        self.assertEqual(_fmt_hm(9.5), '09:30')

    def test_me_info_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_att'})
        self.assertIsNone(_att_me_info(self.env(user=user)))

    def test_me_info_basic(self):
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertEqual(info['employeeId'], self.emp.id)
        self.assertTrue(info['enrolled'])
        self.assertTrue(info['isOfficial'])
        self.assertEqual(info['policy']['checkInStart'], '08:00')
        self.assertIsNone(info['today'])

    def test_me_info_today_after_checkin(self):
        self._checkin(self.emp)
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertIsNotNone(info['today'])
        self.assertIn(info['today']['statusKey'], ('on_time', 'late'))

    def test_day_table_hr_sees_all(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.hr_user)
        data = _att_day_table(self.env(user=self.hr_user), str(today))
        self.assertTrue(data['isHrManager'])
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['empId'], self.emp.id)

    def test_day_table_employee_sees_only_own(self):
        other = self.env['hr.employee'].create({
            'name': 'Other', 'x_employment_status': 'official',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776',
        })
        self._checkin(self.emp)
        self._checkin(other)
        today = fields.Date.context_today(self.emp_user)
        data = _att_day_table(self.env(user=self.emp_user), str(today))
        self.assertFalse(data['isHr'])
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['empId'], self.emp.id)

    def test_history_filters_employee(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.emp_user)
        month = '%04d-%02d' % (today.year, today.month)
        data = _att_me_history(self.env(user=self.emp_user), month)
        self.assertEqual(data['month'], month)
        self.assertEqual(data['summary']['daysPresent'], 1)
        self.assertEqual(len(data['rows']), 1)

    def test_history_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp2', 'login': 'noemp_att2'})
        self.assertIsNone(_att_me_history(self.env(user=user), None))
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run (theo memory `running-odoo-tests`, Git Bash Windows cần `MSYS_NO_PATHCONV=1`):
```bash
MSYS_NO_PATHCONV=1 docker compose exec odoo odoo -d hocba_hrm \
  --test-enable --test-tags hocba_hrm --stop-after-init -u hocba_hrm
```
Expected: FAIL — `ImportError: cannot import name '_fmt_hm'` (helper chưa tồn tại).

- [ ] **Step 3: Thêm import + helper functions**

Trong `custom-addons/hocba_hrm/controllers/main.py`, đổi dòng import đầu:
```python
import calendar
from datetime import date

from odoo import http, fields
from odoo.http import request, Response
from odoo.tools import file_open
```

Ngay sau hàm `_d(v)` (khoảng dòng 20), thêm các helper:
```python
def _fmt_hm(hour_float):
    """8.5 -> '08:30' (giờ float local -> chuỗi HH:MM)."""
    h = int(hour_float)
    m = int(round((hour_float - h) * 60))
    return '%02d:%02d' % (h, m)


def _att_policy_dict(env):
    p = env['hocba.attendance.policy'].sudo().get_policy()
    return {
        'checkInStart': _fmt_hm(p.morning_start),
        'checkInEnd': _fmt_hm(p.morning_end),
        'checkOutStart': _fmt_hm(p.evening_start),
        'checkOutEnd': _fmt_hm(p.evening_end),
        'geofenceOn': bool(p.office_lat and p.office_lng),
    }


def _dt_local(rec, dt):
    """Datetime UTC (stored) -> chuỗi ISO theo local tz của context."""
    if not dt:
        return None
    local = fields.Datetime.context_timestamp(rec, dt)
    return local.replace(tzinfo=None).isoformat()


def _late_minutes(rec, policy):
    """Số phút đi muộn so với morning_start; 0 nếu đúng giờ."""
    if not rec.check_in or rec.status_code != 'late':
        return 0
    local = fields.Datetime.context_timestamp(rec, rec.check_in)
    hour = local.hour + local.minute / 60.0
    return max(0, int(round((hour - policy.morning_start) * 60)))


def _att_row(rec, policy):
    """Một dòng chấm công cho SPA (wire format camelCase)."""
    return {
        'id': rec.id,
        'empId': rec.employee_id.id,
        'code': rec.employee_id.x_employee_code or '—',
        'name': rec.employee_id.name,
        'depName': rec.employee_id.department_id.name or 'Chưa gán',
        'hasImg': bool(rec.check_in_photo),
        'date': _d(rec.date),
        'checkIn': _dt_local(rec, rec.check_in),
        'checkOut': _dt_local(rec, rec.check_out),
        'workingHours': round(rec.working_hours, 2),
        'statusKey': rec.status_code or 'none',
        'lateMinutes': _late_minutes(rec, policy),
        'faceSuspect': rec.face_suspect,
        'outOfZone': rec.out_of_zone,
        'outOfWindow': rec.out_of_window,
        'needsReview': rec.needs_review,
        'checkInMapUrl': rec.check_in_map_url or None,
        'checkOutMapUrl': rec.check_out_map_url or None,
    }


def _att_me_info(env):
    """Thông tin cá nhân để dựng panel check-in. None nếu user chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    today = fields.Date.context_today(env.user)
    rec = env['hocba.attendance'].sudo().search(
        [('employee_id', '=', emp.id), ('date', '=', today)], limit=1)
    info = {
        'employeeId': emp.id,
        'name': emp.name,
        'enrolled': bool(emp.x_face_descriptor),
        'isOfficial': emp.x_employment_status == 'official',
        'isHr': env.user.has_group('hr.group_hr_user'),
        'isHrManager': env.user.has_group('hr.group_hr_manager'),
        'policy': _att_policy_dict(env),
        'today': None,
    }
    if rec:
        info['today'] = {
            'checkIn': _dt_local(rec, rec.check_in),
            'checkOut': _dt_local(rec, rec.check_out),
            'workingHours': round(rec.working_hours, 2),
            'statusKey': rec.status_code or 'none',
            'lateMinutes': _late_minutes(rec, policy),
            'faceSuspect': rec.face_suspect,
            'outOfZone': rec.out_of_zone,
            'outOfWindow': rec.out_of_window,
        }
    return info


def _att_day_table(env, date_str):
    """Bảng chấm công theo ngày. HR/manager: tất cả; NV thường: chỉ của mình."""
    is_hr = env.user.has_group('hr.group_hr_user')
    is_mgr = env.user.has_group('hr.group_hr_manager')
    day = fields.Date.from_string(date_str) if date_str else fields.Date.context_today(env.user)
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    domain = [('date', '=', day)]
    if not (is_hr or is_mgr):
        emp = env.user.employee_id
        domain.append(('employee_id', '=', emp.id if emp else -1))
    recs = env['hocba.attendance'].sudo().search(domain)
    rows = [_att_row(r, policy) for r in recs]
    counts = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'missing': 0,
    }
    if is_hr or is_mgr:
        total = env['hr.employee'].sudo().search_count(
            [('x_employment_status', '=', 'official')])
        counts['missing'] = max(0, total - len(rows))
    return {
        'isHr': is_hr, 'isHrManager': is_mgr,
        'date': _d(day),
        'policy': _att_policy_dict(env),
        'counts': counts,
        'rows': rows,
    }


def _att_me_history(env, month_str):
    """Lịch sử chấm công của chính user theo tháng. None nếu chưa có hồ sơ NV."""
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
    recs = env['hocba.attendance'].sudo().search([
        ('employee_id', '=', emp.id),
        ('date', '>=', first), ('date', '<=', last),
    ], order='date desc')
    rows = [_att_row(r, policy) for r in recs]
    summary = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'daysPresent': len(rows),
        'totalHours': round(sum(r['workingHours'] for r in rows), 2),
    }
    return {'month': '%04d-%02d' % (y, m), 'summary': summary, 'rows': rows}
```

- [ ] **Step 4: Chạy test để xác nhận PASS**

Run:
```bash
MSYS_NO_PATHCONV=1 docker compose exec odoo odoo -d hocba_hrm \
  --test-enable --test-tags hocba_hrm --stop-after-init -u hocba_hrm
```
Expected: PASS — 8 test trong `TestAttendanceApi` xanh, không lỗi.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "feat(hocba_hrm): serializer/query helpers cho API attendance + test"
```

---

### Task A3: 6 route HTTP (vỏ mỏng)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (cuối class `HocBaHRM`)

- [ ] **Step 1: Thêm các route attendance**

Trong `custom-addons/hocba_hrm/controllers/main.py`, thêm vào **cuối class `HocBaHRM`** (sau `api_employee_detail`):
```python
    # ------------------------------------------------------------------
    # JSON API Chấm công (Attendance) — owner FE: Hoàng Anh.
    # Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md
    # Logic face/geo tái dùng hocba.attendance._do_check / enroll_self_face.
    # ------------------------------------------------------------------

    @http.route('/hocba-hrm/api/attendance/me', auth='user',
                type='http', methods=['GET'])
    def api_attendance_me(self, **kw):
        info = _att_me_info(request.env)
        if info is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(info)

    @http.route('/hocba-hrm/api/attendance', auth='user',
                type='http', methods=['GET'])
    def api_attendance_day(self, date=None, **kw):
        return request.make_json_response(_att_day_table(request.env, date))

    @http.route('/hocba-hrm/api/attendance/me/history', auth='user',
                type='http', methods=['GET'])
    def api_attendance_history(self, month=None, **kw):
        data = _att_me_history(request.env, month)
        if data is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/attendance/enroll', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_enroll(self, **kw):
        if not request.env.user.employee_id:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        payload = request.get_json_data()
        request.env['hr.employee'].enroll_self_face({
            'photo': payload.get('photo'),
            'descriptor': payload.get('descriptor') or [],
        })
        return request.make_json_response({'ok': True})

    @http.route(['/hocba-hrm/api/attendance/check-in',
                 '/hocba-hrm/api/attendance/check-out'],
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_check(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if emp.x_employment_status != 'official':
            return request.make_json_response({'error': 'not_official'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        method = 'action_check_out' if kind == 'out' else 'action_check_in'
        res = getattr(request.env['hocba.attendance'], method)({
            'photo': payload.get('photo'),
            'descriptor': payload.get('descriptor') or [],
            'latitude': payload.get('latitude') or 0.0,
            'longitude': payload.get('longitude') or 0.0,
        })
        return request.make_json_response({
            'recordId': res['record_id'], 'kind': res['kind'],
            'faceSuspect': res['face_suspect'], 'outOfZone': res['out_of_zone'],
            'outOfWindow': res['out_of_window'], 'faceScore': res['face_score'],
        })
```

- [ ] **Step 2: Khởi động lại Odoo + kiểm tra route bằng tay**

Run:
```bash
MSYS_NO_PATHCONV=1 docker compose restart odoo
```
Sau khi Odoo lên, đăng nhập web rồi mở trong trình duyệt (giữ session):
`http://localhost:8069/hocba-hrm/api/attendance/me`
Expected: JSON có `employeeId`, `enrolled`, `policy`, `today`. (Nếu user không gắn NV → `{"error":"no_employee"}` status 400.)

- [ ] **Step 3: Chạy lại test suite để chắc không vỡ gì**

Run:
```bash
MSYS_NO_PATHCONV=1 docker compose exec odoo odoo -d hocba_hrm \
  --test-enable --test-tags hocba_hrm --stop-after-init -u hocba_hrm
```
Expected: PASS toàn bộ.

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(hocba_hrm): 6 route /hocba-hrm/api/attendance/* (me, day, history, enroll, check-in/out)"
```

---

## PHASE B — Gỡ kiosk Odoo cũ

### Task B1: Xóa kiosk + asset + menu

**Files:**
- Modify: `custom-addons/hocba_attendance/__manifest__.py:18-24`
- Modify: `custom-addons/hocba_attendance/views/menus.xml:21-28`
- Delete: `custom-addons/hocba_attendance/static/src/js/attendance_kiosk.js`
- Delete: `custom-addons/hocba_attendance/static/src/xml/attendance_kiosk.xml`
- Delete: `custom-addons/hocba_attendance/static/src/scss/attendance_kiosk.scss`

- [ ] **Step 1: Bỏ block assets kiosk khỏi manifest**

Trong `custom-addons/hocba_attendance/__manifest__.py`, xóa toàn bộ key `'assets'` (vì chỉ chứa 3 file kiosk):
```python
    'data': [
        'security/ir.model.access.csv',
        'data/hocba_attendance_status_data.xml',
        'data/hocba_attendance_policy_data.xml',
        'views/hr_attendance_status_views.xml',
        'views/hr_work_assignment_views.xml',
        'views/hr_attendance_views.xml',
        'views/hocba_attendance_policy_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}
```
(Xóa các dòng từ `'assets': {` đến `},` ngay trước `'installable'`.)

- [ ] **Step 2: Bỏ action + menu "My Attendance" trong menus.xml**

Trong `custom-addons/hocba_attendance/views/menus.xml`, xóa khối:
```xml
        <!-- My Attendance (kiosk client action: face + geo check-in) -->
        <record id="hocba_my_attendance_action" model="ir.actions.client">
            <field name="name">My Attendance</field>
            <field name="tag">hocba_attendance_kiosk</field>
        </record>
        <menuitem name="My Attendance" id="hocba_my_attendance_menu"
                  parent="hocba_attendance_menu_root"
                  action="hocba_my_attendance_action" sequence="5"/>
```

- [ ] **Step 3: Xóa 3 file kiosk**

Run:
```bash
git rm custom-addons/hocba_attendance/static/src/js/attendance_kiosk.js \
       custom-addons/hocba_attendance/static/src/xml/attendance_kiosk.xml \
       custom-addons/hocba_attendance/static/src/scss/attendance_kiosk.scss
```

- [ ] **Step 4: Upgrade + verify module load + test**

Run:
```bash
MSYS_NO_PATHCONV=1 docker compose exec odoo odoo -d hocba_hrm \
  --stop-after-init -u hocba_attendance,hocba_hrm
```
Expected: không lỗi load (không còn tham chiếu `hocba_attendance_kiosk`, không còn asset thiếu file). Sau đó chạy lại test suite:
```bash
MSYS_NO_PATHCONV=1 docker compose exec odoo odoo -d hocba_hrm \
  --test-enable --test-tags hocba_hrm --stop-after-init
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/__manifest__.py custom-addons/hocba_attendance/views/menus.xml
git commit -m "refactor(hocba_attendance): gỡ kiosk Odoo cũ (chuyển check-in sang SPA)"
```

---

## PHASE C — Frontend

> FE không có test JS tự động trong repo; mỗi task kết thúc bằng `cd frontend && npm run build` để đảm bảo build sạch, kiểm thử thủ công ở task cuối (Definition of Done §9). Cần Odoo Docker chạy + đăng nhập user test.

### Task C1: Proxy Vite + lớp API + util

**Files:**
- Modify: `frontend/vite.config.js:14-16` `[CHUNG]`
- Create: `frontend/src/api/attendance.js`
- Create: `frontend/src/features/attendance/util.js`

- [ ] **Step 1: Thêm proxy `/hocba_employees/static` (để dev nạp face-api.js + ảnh)**

Trong `frontend/vite.config.js`, thêm vào object `proxy`:
```js
    proxy: {
      '/hocba-hrm/api': { target: 'http://[::1]:8069', changeOrigin: false },
      '/hocba_employees/static': { target: 'http://[::1]:8069', changeOrigin: false },
      '/web': { target: 'http://[::1]:8069', changeOrigin: false },
      '/odoo': { target: 'http://[::1]:8069', changeOrigin: false },
    },
```

- [ ] **Step 2: Tạo lớp API attendance**

Tạo `frontend/src/api/attendance.js`:
```js
/* API domain Attendance — Hoàng Anh.
   Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { hbGet, hbPost } from './client';

export const fetchMyAttendance = () => hbGet('/hocba-hrm/api/attendance/me');
export const fetchAttendanceDay = (date) =>
  hbGet(`/hocba-hrm/api/attendance?date=${date}`);
export const fetchMyHistory = (month) =>
  hbGet(`/hocba-hrm/api/attendance/me/history?month=${month}`);
export const enrollFace = (photo, descriptor) =>
  hbPost('/hocba-hrm/api/attendance/enroll', { photo, descriptor });
export const checkIn = (payload) =>
  hbPost('/hocba-hrm/api/attendance/check-in', payload);
export const checkOut = (payload) =>
  hbPost('/hocba-hrm/api/attendance/check-out', payload);
```

- [ ] **Step 3: Tạo util feature-local**

Tạo `frontend/src/features/attendance/util.js`:
```js
/* Helper riêng feature attendance (feature-local theo quy ước §4). */

/* ISO datetime -> 'HH:MM' (giờ local đã do BE quy đổi). */
export function fmtTime(iso) {
  if (!iso) return '—';
  const t = (iso.split('T')[1] || '').slice(0, 5);
  return t || '—';
}

/* statusKey -> [nhãn, kind badge] (kind theo bộ chuẩn quy ước §6). */
export function attStatus(key) {
  return ({
    on_time: ['Đúng giờ', 'green'],
    late: ['Đi muộn', 'amber'],
    none: ['Chưa chấm', 'gray'],
  })[key] || ['—', 'gray'];
}

/* Tháng hiện tại dạng 'YYYY-MM' cho input month mặc định. */
export function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/* Hôm nay dạng 'YYYY-MM-DD' cho input date mặc định. */
export function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
```

- [ ] **Step 4: Build kiểm tra**

Run:
```bash
cd frontend && npm install && npm run build
```
Expected: build thành công, không lỗi import.

- [ ] **Step 5: Commit**

```bash
git add frontend/vite.config.js frontend/src/api/attendance.js frontend/src/features/attendance/util.js
git commit -m "feat(frontend): proxy face-api + lớp API + util cho attendance"
```

---

### Task C2: Hook useFaceApi (camera + face-api.js)

**Files:**
- Create: `frontend/src/features/attendance/useFaceApi.js`

- [ ] **Step 1: Tạo hook**

Tạo `frontend/src/features/attendance/useFaceApi.js`:
```js
/* Nạp face-api.js (đã vendor ở hocba_employees) + camera + GPS.
   Tách riêng để CheckInPanel không phải biết chi tiết thư viện. */
import { useEffect, useRef, useState } from 'react';

const LIB = '/hocba_employees/static/lib/face-api/face-api.min.js';
const MODELS = '/hocba_employees/static/lib/face-api/models';

let _libPromise = null;
function loadFaceApi() {
  if (window.faceapi && window.faceapi.nets.faceRecognitionNet.params) {
    return Promise.resolve(window.faceapi);
  }
  if (_libPromise) return _libPromise;
  _libPromise = new Promise((resolve, reject) => {
    if (window.faceapi) return resolve();
    const s = document.createElement('script');
    s.src = LIB; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  }).then(async () => {
    const f = window.faceapi;
    await f.nets.tinyFaceDetector.loadFromUri(MODELS);
    await f.nets.faceLandmark68Net.loadFromUri(MODELS);
    await f.nets.faceRecognitionNet.loadFromUri(MODELS);
    return f;
  });
  return _libPromise;
}

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ lat: 0, lng: 0 });
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => resolve({ lat: 0, lng: 0 }),
      { enableHighAccuracy: true, timeout: 8000 });
  });
}

export function useFaceApi() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [camError, setCamError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadFaceApi()
      .then(() => navigator.mediaDevices.getUserMedia({ video: true }))
      .then((stream) => {
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setReady(true);
      })
      .catch(() => setCamError(
        'Không mở được camera hoặc thư viện nhận diện. Cần HTTPS/localhost và cấp quyền camera.'));
    return () => {
      cancelled = true;
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  /* Trả {descriptor, photo, latitude, longitude} hoặc {error:'no_face'} / null. */
  async function capture() {
    const faceapi = window.faceapi;
    const video = videoRef.current;
    if (!faceapi || !video || !streamRef.current) return null;
    const det = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor();
    if (!det) return { error: 'no_face' };
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const photo = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
    const loc = await getLocation();
    return {
      descriptor: Array.from(det.descriptor), photo,
      latitude: loc.lat, longitude: loc.lng,
    };
  }

  return { videoRef, ready, camError, capture };
}
```

- [ ] **Step 2: Build kiểm tra**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/useFaceApi.js
git commit -m "feat(frontend): hook useFaceApi (camera + face-api.js + GPS)"
```

---

### Task C3: CheckInPanel (trọng tâm)

**Files:**
- Create: `frontend/src/features/attendance/CheckInPanel.jsx`

- [ ] **Step 1: Tạo component**

Tạo `frontend/src/features/attendance/CheckInPanel.jsx`:
```jsx
/* Panel tự chấm công face/geo (thay kiosk). Nhận `me` (từ /api/attendance/me)
   và onChanged() để refetch sau khi chấm. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useFaceApi } from './useFaceApi';
import { enrollFace, checkIn, checkOut } from '../../api/attendance';
import { fmtTime, attStatus } from './util';

export default function CheckInPanel({ me, onChanged }) {
  const { videoRef, ready, camError, capture } = useFaceApi();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null); // {kind:'ok'|'warn'|'err', text}
  const [enrolled, setEnrolled] = useState(me.enrolled);

  const p = me.policy;
  const t = me.today;

  async function doEnroll() {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không phát hiện khuôn mặt. Thử lại.' }); return; }
      await enrollFace(cap.photo, cap.descriptor);
      setEnrolled(true);
      setMsg({ kind: 'ok', text: 'Đăng ký khuôn mặt thành công.' });
    } catch (e) {
      setMsg({ kind: 'err', text: 'Đăng ký thất bại (' + e.message + ').' });
    } finally { setBusy(false); }
  }

  async function doCheck(kind) {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không phát hiện khuôn mặt. Thử lại.' }); return; }
      const res = await (kind === 'in' ? checkIn(cap) : checkOut(cap));
      const flags = [];
      if (res.faceSuspect) flags.push('khuôn mặt nghi ngờ');
      if (res.outOfZone) flags.push('ngoài vùng văn phòng');
      if (res.outOfWindow) flags.push('ngoài khung giờ');
      setMsg({
        kind: flags.length ? 'warn' : 'ok',
        text: (kind === 'in' ? 'Đã check-in' : 'Đã check-out')
          + (flags.length ? ' ⚠ ' + flags.join(', ') : ' thành công'),
      });
      onChanged && onChanged();
    } catch (e) {
      setMsg({ kind: 'err', text: 'Điểm danh thất bại (' + e.message + ').' });
    } finally { setBusy(false); }
  }

  const [stLabel, stKind] = attStatus(t ? t.statusKey : 'none');

  return (
    <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start' }}>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', display: 'block', background: '#000', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        {camError && <div className="empty" style={{ color: 'var(--red-600)' }}>{camError}</div>}
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{me.name}</div>
        <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
          Khung giờ: check-in {p.checkInStart}–{p.checkInEnd} · check-out {p.checkOutStart}–{p.checkOutEnd}
        </div>

        <div className="divider" style={{ margin: '14px 0' }}></div>

        <div className="between" style={{ marginBottom: 6 }}>
          <span className="muted" style={{ fontSize: 13 }}>Hôm nay</span>
          <Badge kind={stKind} dot>{stLabel}</Badge>
        </div>
        <div style={{ display: 'flex', gap: 18, fontSize: 13 }}>
          <div><span className="muted">Check-in: </span><b className="mono">{fmtTime(t && t.checkIn)}</b>
            {t && t.lateMinutes > 0 && <span style={{ color: 'var(--amber)', fontWeight: 600 }}> +{t.lateMinutes}'</span>}</div>
          <div><span className="muted">Check-out: </span><b className="mono">{fmtTime(t && t.checkOut)}</b></div>
        </div>

        <div className="divider" style={{ margin: '14px 0' }}></div>

        {!me.isOfficial ? (
          <div className="empty">Chức năng điểm danh chỉ áp dụng cho nhân viên chính thức.</div>
        ) : !enrolled ? (
          <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
            <Icon name="user" size={16} />Đăng ký khuôn mặt
          </button>
        ) : (
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" disabled={busy || !ready} onClick={() => doCheck('in')}>
              <Icon name="checkCircle" size={16} />Check-in
            </button>
            <button className="btn btn-ghost" disabled={busy || !ready} onClick={() => doCheck('out')}>
              <Icon name="logout" size={16} />Check-out
            </button>
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

- [ ] **Step 2: Build kiểm tra**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/CheckInPanel.jsx
git commit -m "feat(frontend): CheckInPanel — tự chấm công face/geo trong SPA"
```

---

### Task C4: AttendanceDrawer + AttendanceTable

**Files:**
- Create: `frontend/src/features/attendance/AttendanceDrawer.jsx`
- Create: `frontend/src/features/attendance/AttendanceTable.jsx`

- [ ] **Step 1: Tạo AttendanceDrawer (read-only)**

Tạo `frontend/src/features/attendance/AttendanceDrawer.jsx`:
```jsx
/* Chi tiết 1 bản ghi chấm công (read-only): ảnh, bản đồ, cờ review. */
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus } from './util';

export default function AttendanceDrawer({ rec, onClose }) {
  const [stLabel, stKind] = attStatus(rec.statusKey);
  const img = (field) => `/web/image/hocba.attendance/${rec.id}/${field}`;
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>{rec.name}</h2>
            <Badge kind={stKind} dot>{stLabel}</Badge>
            {rec.needsReview && <Badge kind="amber" dot>Cần xem lại</Badge>}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
            {rec.code} · {rec.depName} · {fmtDate(rec.date)}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        <div className="grid-2" style={{ rowGap: 16 }}>
          <div className="kv"><div className="k">Check-in</div><div className="v mono">{fmtTime(rec.checkIn)}{rec.lateMinutes > 0 && <span style={{ color: 'var(--amber)' }}> (+{rec.lateMinutes}')</span>}</div></div>
          <div className="kv"><div className="k">Check-out</div><div className="v mono">{fmtTime(rec.checkOut)}</div></div>
          <div className="kv"><div className="k">Giờ công</div><div className="v mono">{rec.workingHours} giờ</div></div>
          <div className="kv"><div className="k">Cờ kiểm tra</div><div className="v" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {rec.faceSuspect && <Badge kind="red">Khuôn mặt nghi ngờ</Badge>}
            {rec.outOfZone && <Badge kind="red">Ngoài vùng VP</Badge>}
            {rec.outOfWindow && <Badge kind="amber">Ngoài khung giờ</Badge>}
            {!rec.faceSuspect && !rec.outOfZone && !rec.outOfWindow && <span className="faint">Không có</span>}
          </div></div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginTop: 20, flexWrap: 'wrap' }}>
          {rec.hasImg && (
            <figure style={{ margin: 0 }}>
              <img src={img('check_in_photo')} alt="check-in" style={{ width: 200, borderRadius: 10, display: 'block' }} />
              <figcaption className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Ảnh check-in {rec.checkInMapUrl && <a href={rec.checkInMapUrl} target="_blank" rel="noreferrer"><Icon name="pin" size={13} /> bản đồ</a>}
              </figcaption>
            </figure>
          )}
          {rec.checkOut && (
            <figure style={{ margin: 0 }}>
              <img src={img('check_out_photo')} alt="check-out" style={{ width: 200, borderRadius: 10, display: 'block' }} />
              <figcaption className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Ảnh check-out {rec.checkOutMapUrl && <a href={rec.checkOutMapUrl} target="_blank" rel="noreferrer"><Icon name="pin" size={13} /> bản đồ</a>}
              </figcaption>
            </figure>
          )}
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Tạo AttendanceTable (HR/manager, theo ngày)**

Tạo `frontend/src/features/attendance/AttendanceTable.jsx`:
```jsx
/* Bảng chấm công theo ngày cho HR/manager. */
import { useState, useEffect } from 'react';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchAttendanceDay } from '../../api/attendance';
import { fmtTime, attStatus, today as todayStr } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Metric({ ico, col, bg, val, lbl }) {
  return (
    <div className="stat" style={{ padding: '15px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{ width: 38, height: 38, borderRadius: 11, background: bg, color: col, display: 'grid', placeItems: 'center' }}>
          <Icon name={ico} size={19} /></div>
        <div>
          <div style={{ fontSize: 24, fontWeight: 800, lineHeight: 1 }}>{val}</div>
          <div className="stat-lbl" style={{ marginTop: 3 }}>{lbl}</div>
        </div>
      </div>
    </div>
  );
}

export default function AttendanceTable({ search }) {
  const [date, setDate] = useState(todayStr());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchAttendanceDay(date).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [date]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải bảng chấm công…" />;

  const rows = data.rows.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (r.name || '').toLowerCase().includes(q) || (r.code || '').toLowerCase().includes(q);
  });

  return (
    <div>
      <div className="filterbar">
        <input type="date" className="sel" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
        <Metric ico="checkCircle" col="var(--green)" bg="var(--green-bg)" val={data.counts.onTime} lbl="Đúng giờ" />
        <Metric ico="clock" col="var(--amber)" bg="var(--amber-bg)" val={data.counts.late} lbl="Đi muộn" />
        <Metric ico="shield" col="var(--red-600)" bg="var(--red-50)" val={data.counts.needsReview} lbl="Cần xem lại" />
        <Metric ico="x" col="var(--text-3)" bg="var(--surface-2)" val={data.counts.missing} lbl="Chưa chấm" />
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Check-in</th><th>Check-out</th>
              <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => {
                const [lbl, kind] = attStatus(r.statusKey);
                return (
                  <tr key={r.id} onClick={() => setSel(r)}>
                    <td><div className="cell-emp">
                      <Avatar emp={{ id: r.empId, name: r.name, hasImg: false }} />
                      <div><div className="nm">{r.name}</div><div className="id">{r.code}</div></div>
                    </div></td>
                    <td className="muted">{r.depName}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                    <td className="tbl-num mono">{r.workingHours || '—'}</td>
                    <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
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
        {rows.length === 0 && <EmptyState>Không có bản ghi chấm công cho ngày này.</EmptyState>}
      </div>

      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
    </div>
  );
}
```

- [ ] **Step 3: Build kiểm tra**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/AttendanceDrawer.jsx frontend/src/features/attendance/AttendanceTable.jsx
git commit -m "feat(frontend): AttendanceTable theo ngày + AttendanceDrawer (HR/manager)"
```

---

### Task C5: MyHistory (lịch sử cá nhân theo tháng)

**Files:**
- Create: `frontend/src/features/attendance/MyHistory.jsx`

- [ ] **Step 1: Tạo component**

Tạo `frontend/src/features/attendance/MyHistory.jsx`:
```jsx
/* Lịch sử chấm công của chính mình theo tháng (read-only). */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMyHistory } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus, currentMonth } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Sum({ val, lbl, col }) {
  return (
    <div className="stat" style={{ padding: '14px 16px' }}>
      <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: col || 'inherit' }}>{val}</div>
      <div className="stat-lbl" style={{ marginTop: 4 }}>{lbl}</div>
    </div>
  );
}

export default function MyHistory() {
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchMyHistory(month).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month]);

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="between" style={{ marginBottom: 14 }}>
        <h3 style={{ margin: 0 }}>Lịch sử chấm công của tôi</h3>
        <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải lịch sử…" />}

      {data && (
        <>
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
            <Sum val={data.summary.onTime} lbl="Đúng giờ" col="var(--green)" />
            <Sum val={data.summary.late} lbl="Đi muộn" col="var(--amber)" />
            <Sum val={data.summary.needsReview} lbl="Cần xem lại" col="var(--red-600)" />
            <Sum val={data.summary.totalHours} lbl="Tổng giờ công" />
          </div>

          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th><th>Trạng thái</th><th></th>
              </tr></thead>
              <tbody>
                {data.rows.map((r) => {
                  const [lbl, kind] = attStatus(r.statusKey);
                  return (
                    <tr key={r.id} onClick={() => setSel(r)}>
                      <td className="mono">{fmtDate(r.date)}</td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                      <td className="tbl-num mono">{r.workingHours || '—'}</td>
                      <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
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
          {data.rows.length === 0 && <EmptyState>Chưa có bản ghi chấm công trong tháng này.</EmptyState>}
        </>
      )}

      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
    </div>
  );
}
```

- [ ] **Step 2: Build kiểm tra**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/MyHistory.jsx
git commit -m "feat(frontend): MyHistory — lịch sử chấm công cá nhân theo tháng"
```

---

### Task C6: mock.js + Attendance.jsx + wire App.jsx

**Files:**
- Create: `frontend/src/features/attendance/mock.js`
- Create: `frontend/src/features/attendance/Attendance.jsx`
- Modify: `frontend/src/app/App.jsx:4-23` `[CHUNG]`

- [ ] **Step 1: Tạo mock cho 2 tab chưa có backend**

Tạo `frontend/src/features/attendance/mock.js`:
```js
/* Dữ liệu mẫu cho 2 tab chưa có backend (Đơn quên chấm công, Tăng ca).
   Quy ước §7: có cờ USE_MOCK; xóa khi backend sẵn sàng. */
export const USE_MOCK = true;

export const FORGOT_REQUESTS = [
  { id: 1, name: 'Trần Thị B', code: 'GV002', depName: 'Tiếng Trung',
    missType: 'Quên check-out', date: '2026-06-11', proposed: '17:30',
    reason: 'Quên bấm khi ra về', state: 'Chờ duyệt' },
  { id: 2, name: 'Lê Văn C', code: 'NV010', depName: 'Hành chính',
    missType: 'Quên check-in', date: '2026-06-12', proposed: '08:10',
    reason: 'Điện thoại hết pin', state: 'Chờ duyệt' },
];

export const OT_LOG = [
  { id: 1, name: 'Phạm Thị D', code: 'GV005', depName: 'Luyện thi',
    date: '2026-06-10', hours: 2.5, rate: 150, reason: 'Dạy bù lớp tối' },
  { id: 2, name: 'Hoàng Văn E', code: 'NV021', depName: 'Marketing',
    date: '2026-06-08', hours: 3, rate: 100, reason: 'Chạy chiến dịch tuyển sinh' },
];
```

- [ ] **Step 2: Tạo màn chính Attendance.jsx**

Tạo `frontend/src/features/attendance/Attendance.jsx`:
```jsx
/* Màn Chấm công — điều phối tab theo quyền (mẫu chuẩn: màn Nhân viên).
   Owner: Hoàng Anh. Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchMyAttendance } from '../../api/attendance';
import CheckInPanel from './CheckInPanel';
import MyHistory from './MyHistory';
import AttendanceTable from './AttendanceTable';
import { USE_MOCK, FORGOT_REQUESTS, OT_LOG } from './mock';

export default function Attendance({ search }) {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState('me');

  const load = () => {
    setErr(null); setMe(null);
    fetchMyAttendance().then(setMe).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!me) return <LoadingState label="Đang tải dữ liệu chấm công…" />;

  const isStaff = me.isHr || me.isHrManager;
  const tabs = [['me', 'Chấm công của tôi']];
  if (isStaff) tabs.push(['day', 'Bảng chấm công'], ['forgot', 'Đơn quên chấm công'], ['ot', 'Tăng ca (OT)']);

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
          <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => setTab(id)}>{l}</button>
        ))}
      </div>

      {tab === 'me' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <CheckInPanel me={me} onChanged={load} />
          <MyHistory />
        </div>
      )}
      {tab === 'day' && <AttendanceTable search={search} />}
      {tab === 'forgot' && <ForgotMock />}
      {tab === 'ot' && <OtMock />}
    </div>
  );
}

function MockBanner() {
  return USE_MOCK ? (
    <div style={{ padding: '8px 12px', background: 'var(--amber-bg)', color: 'var(--amber)', borderRadius: 9, fontSize: 12.5, marginBottom: 12, fontWeight: 600 }}>
      Dữ liệu mẫu — chờ backend
    </div>
  ) : null;
}

function ForgotMock() {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn quên chấm công</h3></div>
      <div style={{ padding: '8px 12px' }}>
        <MockBanner />
        {FORGOT_REQUESTS.map((f) => (
          <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 4px', borderBottom: '1px solid var(--border)' }}>
            <Avatar emp={{ id: f.id, name: f.name, hasImg: false }} size={40} />
            <div style={{ minWidth: 200 }}>
              <div style={{ fontWeight: 600, fontSize: 13.5 }}>{f.name}</div>
              <div className="muted" style={{ fontSize: 12 }}>{f.code} · {f.depName}</div>
            </div>
            <div style={{ flex: 1 }}>
              <Badge kind="red">{f.missType}</Badge>
              <span className="mono" style={{ fontWeight: 600, fontSize: 13, marginLeft: 8 }}>{fmtDate(f.date)} · {f.proposed}</span>
              <div className="muted" style={{ fontSize: 12.5 }}>“{f.reason}”</div>
            </div>
            <Badge kind="amber" dot>{f.state}</Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

function OtMock() {
  return (
    <div className="card">
      <div className="card-head"><h3>Đăng ký tăng ca</h3></div>
      <div style={{ padding: '0 12px 8px' }}><MockBanner /></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr><th>Nhân viên</th><th>Ngày</th><th className="tbl-num">Số giờ</th><th>Hệ số</th><th>Lý do</th></tr></thead>
          <tbody>
            {OT_LOG.map((o) => (
              <tr key={o.id} style={{ cursor: 'default' }}>
                <td><div className="cell-emp"><Avatar emp={{ id: o.id, name: o.name, hasImg: false }} /><div><div className="nm">{o.name}</div><div className="id">{o.code}</div></div></div></td>
                <td className="mono muted">{fmtDate(o.date)}</td>
                <td className="tbl-num mono" style={{ fontWeight: 600 }}>{o.hours} giờ</td>
                <td><Badge kind={o.rate === 300 ? 'red' : o.rate === 150 ? 'amber' : 'gray'}>{o.rate}%</Badge></td>
                <td className="muted">{o.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire vào App.jsx (file `[CHUNG]` — cần Tân review)**

Trong `frontend/src/app/App.jsx`, thêm import và thay dòng `attendance`:
```jsx
import { useState, useEffect } from 'react';
import { Sidebar, Topbar } from './Shell';
import Dashboard from '../features/dashboard/Dashboard';
import Employees from '../features/employees/Employees';
import Attendance from '../features/attendance/Attendance';
import ComingSoon from '../components/ComingSoon';

export default function App() {
  const [view, setView] = useState(() => localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');

  useEffect(() => { localStorage.setItem('hocba_view', view); setSearch(''); }, [view]);

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} />
        {view === 'dashboard' && <Dashboard setView={setView} />}
        {view === 'employees' && <Employees search={search} />}
        {view === 'attendance' && <Attendance search={search} />}
        {view === 'timeoff' && <ComingSoon title="Nghỉ phép" owner="Nhật Anh" api="/hocba-hrm/api/timeoff/*" />}
        {view === 'payroll' && <ComingSoon title="Bảng lương" owner="Hùng" api="/hocba-hrm/api/payroll/*" />}
        {view === 'recruitment' && <ComingSoon title="Tuyển dụng" owner="Việt" api="/hocba-hrm/api/recruitment/*" />}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Build kiểm tra**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công, không lỗi import; output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/attendance/mock.js frontend/src/features/attendance/Attendance.jsx frontend/src/app/App.jsx
git commit -m "feat(frontend): màn Chấm công — điều phối tab theo quyền + mock Đơn/OT + wire App"
```

---

### Task C7: Kiểm thử thủ công + commit bản build

**Files:**
- Modify: `custom-addons/hocba_hrm/static/spa/**` (output build, commit theo quy ước §8)

- [ ] **Step 1: Chạy dev và kiểm thử thủ công với 4 user role**

Run:
```bash
cd frontend && npm run dev
```
Mở `http://localhost:5173/hocba_hrm/static/spa/`, đăng nhập lần lượt 4 user test, kiểm tra (Definition of Done §9):
- NV thường: chỉ thấy tab "Chấm công của tôi"; camera mở; enroll (nếu chưa) → check-in → trạng thái hôm nay cập nhật; lịch sử tháng hiển thị đúng; KHÔNG thấy tab bảng/đơn/OT.
- HR/manager: thấy đủ 4 tab; bảng theo ngày đổi `date` reload đúng; metric đúng; drawer hiện ảnh + bản đồ + cờ; tab Đơn/OT hiện banner "Dữ liệu mẫu".
- Đủ 3 trạng thái loading/error (rút mạng → nút "Thử lại")/data; không lỗi đỏ console.

- [ ] **Step 2: Build production và commit bản build**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công.

```bash
git add custom-addons/hocba_hrm/static/spa
git commit -m "build(frontend): bản build SPA kèm màn Chấm công"
```

- [ ] **Step 3: (tuỳ chọn) hoàn tất nhánh**

Dùng skill `superpowers:finishing-a-development-branch` để quyết định merge/PR.

---

## Self-Review

**Spec coverage:**
- §3a `/me` → Task A2 (`_att_me_info`) + A3 route ✔
- §3b `/enroll` → A3 route ✔
- §3c `/check-in` `/check-out` → A3 route (gồm chặn `not_official`) ✔
- §3d list theo ngày + quyền + counts → A2 (`_att_day_table`) + A3 ✔
- §3e `/me/history` theo tháng → A2 (`_att_me_history`) + A3 ✔
- §4 CheckInPanel/MyHistory/AttendanceTable/Drawer/useFaceApi → Task C2–C6 ✔
- §4 ảnh qua `/web/image` → AttendanceDrawer ✔
- §5 quyền (ẩn tab + BE chặn) → Attendance.jsx + `_att_day_table` ✔
- §6 test backend → Task A2; FE thủ công → C7 ✔
- §2 gỡ kiosk → Phase B ✔
- §2 proxy Vite + App.jsx → C1, C6 ✔

**Placeholder scan:** không còn TODO/TBD; mọi step có code/command cụ thể.

**Type consistency:** wire keys camelCase khớp giữa BE (`_att_row`) và FE (`fmtTime`/`attStatus`/Table/History/Drawer dùng `r.statusKey`, `r.checkIn`, `r.lateMinutes`, `r.needsReview`, `r.checkInMapUrl`...). `me.policy.checkInStart` khớp `_att_policy_dict`. Hàm `today()`/`currentMonth()` trong util dùng nhất quán ở Table/History.

**Lưu ý phụ thuộc thực thi:** `_att_day_table` test "HR thấy tất cả" dùng user gắn `hr.group_hr_manager` tường minh (không dựa vào admin có sẵn group). Route `check-in/check-out` phân biệt qua `request.httprequest.path` (1 handler, 2 path).
