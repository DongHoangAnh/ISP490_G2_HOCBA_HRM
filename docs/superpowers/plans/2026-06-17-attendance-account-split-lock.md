# Gói 2 — Tách tài khoản manager/user + khóa check-in/out + manager sửa/xóa — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phân biệt tài khoản manager (chỉ quản lý, không check-in) với user (tự chấm công), khóa check-in/out (1 lần/ngày, chỉ ngày làm việc) enforce ở backend, và cho manager sửa/xóa bản ghi attendance của user trong phạm vi quản lý.

**Architecture:** Backend enforce qua (a) module-level helper phạm vi/quyền trong `hocba_hrm/controllers/main.py`, (b) guard ở action layer `action_check_in`/`action_check_out` của model `hocba.attendance`, (c) 2 route mới sửa/xóa. Frontend đọc cờ `canManage`/`isWorkdayToday` để tách UI và khóa nút.

**Tech Stack:** Odoo 19 (Python, `TransactionCase`), React (Vite) SPA trong `frontend/`.

**Spec:** [docs/superpowers/specs/2026-06-17-attendance-account-split-lock-design.md](../specs/2026-06-17-attendance-account-split-lock-design.md)

---

## File Structure

- `custom-addons/hocba_hrm/controllers/main.py` — **Modify**: thêm module-level helpers (`_user_can_manage`, `_managed_department_ids`, `_emp_scope_domain`, `_emp_in_scope`, `_to_utc`, `_attendance_edit`, `_attendance_delete`); class methods cũ delegate; `api_attendance_check` chặn manager + map lỗi; `_att_me_info` thêm `canManage`/`isWorkdayToday`; `_att_day_table` scope theo `_emp_scope_domain`; 2 route mới sửa/xóa.
- `custom-addons/hocba_attendance/models/hr_attendance.py` — **Modify**: `_assert_check_allowed` + guard trong `action_check_in`/`action_check_out`.
- `custom-addons/hocba_attendance/tests/test_check_lock.py` — **Create**: test guard workday/once-per-day.
- `custom-addons/hocba_hrm/tests/test_attendance_api.py` — **Modify**: test scope helpers, me-info, day-table scope, edit/delete.
- `frontend/src/api/attendance.js` — **Modify**: `editAttendance`, `deleteAttendance`.
- `frontend/src/features/attendance/Attendance.jsx` — **Modify**: tách UI theo `canManage`.
- `frontend/src/features/attendance/CheckInPanel.jsx` — **Modify**: khóa nút + map lỗi.
- `frontend/src/features/attendance/AttendanceTable.jsx` — **Modify**: truyền `canManage` + refetch.
- `frontend/src/features/attendance/AttendanceDrawer.jsx` — **Modify**: form sửa + nút xóa cho manager.

**Lệnh test backend** (Windows Git Bash — `MSYS_NO_PATHCONV=1` BẮT BUỘC, xác nhận số test ≠ 0; nhân viên official trong fixture cần `identification_id` 12 số do BR-010):

```bash
# hocba_attendance
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
# hocba_hrm
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

---

## Task 1: Module-level helpers phạm vi/quyền (refactor giữ nguyên hành vi)

Trích logic phạm vi/quyền (đang là method của class `HocBaHRM`) ra hàm module-level nhận `env`, để các helper attendance dùng được; class method cũ gọi lại hàm mới (hành vi không đổi).

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_attendance_api.py`

- [ ] **Step 1: Viết test thất bại cho helper mới**

Thêm vào đầu file test (sau dòng import hiện có) import các helper mới sẽ tạo, và thêm test class. Trong `custom-addons/hocba_hrm/tests/test_attendance_api.py`, sửa dòng import:
```python
from odoo.addons.hocba_hrm.controllers.main import (
    _fmt_hm, _att_me_info, _att_day_table, _att_me_history,
)
```
thành:
```python
from odoo.addons.hocba_hrm.controllers.main import (
    _fmt_hm, _att_me_info, _att_day_table, _att_me_history,
    _user_can_manage, _emp_scope_domain, _emp_in_scope,
    _attendance_edit, _attendance_delete, _to_utc,
)
```

Thêm test class mới ở cuối file:
```python
@tagged('post_install', '-at_install')
class TestScopeHelpers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.mgr_emp = self.env['hr.employee'].create({'name': 'Quản lý A'})
        self.dept.manager_id = self.mgr_emp
        self.mgr_user = self.env['res.users'].create(
            {'name': 'MgrA', 'login': 'mgra_scope'})
        self.mgr_user.tz = 'Asia/Ho_Chi_Minh'  # cho _to_utc test
        self.mgr_emp.user_id = self.mgr_user
        self.plain_user = self.env['res.users'].create(
            {'name': 'Plain', 'login': 'plain_scope'})

    def test_hr_manager_can_manage(self):
        u = self.env['res.users'].create({
            'name': 'HRM', 'login': 'hrm_scope',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.assertTrue(_user_can_manage(self.env(user=u)))

    def test_department_head_can_manage(self):
        self.assertTrue(_user_can_manage(self.env(user=self.mgr_user)))

    def test_plain_user_cannot_manage(self):
        self.assertFalse(_user_can_manage(self.env(user=self.plain_user)))

    def test_department_head_scope_is_own_department(self):
        dom = _emp_scope_domain(self.env(user=self.mgr_user))
        self.assertIn(('department_id', 'in', [self.dept.id]), dom)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (`ImportError: cannot import name '_user_can_manage'`). Lệnh `/hocba_hrm` như mục đầu.

- [ ] **Step 3: Thêm các hàm module-level**

Trong `main.py`, sau khối helper hiện có (vd sau `_att_me_history`, trước `class HocBaHRM`), thêm:

```python
def _managed_department_ids(env, emp):
    """Phòng ban (gồm phòng con) mà emp làm trưởng phòng (manager_id)."""
    if not emp:
        return []
    Dept = env['hr.department'].sudo()
    managed = Dept.search([('manager_id', '=', emp.id)])
    if not managed:
        return []
    result, frontier = set(managed.ids), managed
    while frontier:
        children = Dept.search([('parent_id', 'in', frontier.ids)])
        frontier = children.filtered(lambda d: d.id not in result)
        result.update(frontier.ids)
    return list(result)


def _emp_scope_domain(env):
    """Domain giới hạn NV theo vai trò: HR/Admin=tất cả; Giáo vụ=giáo viên;
    Trưởng phòng=phòng mình; còn lại=rỗng (id=0)."""
    user = env.user
    if (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager')):
        return []
    if user.has_group('hocba_employees.group_hocba_giaovu'):
        return [('x_employee_type_id.code', '=', 'teacher')]
    dept_ids = _managed_department_ids(env, user.employee_id)
    if dept_ids:
        return [('department_id', 'in', dept_ids)]
    return [('id', '=', 0)]


def _emp_in_scope(env, e):
    """User hiện tại có được xem/quản lý hồ sơ e không."""
    user = env.user
    if (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager')):
        return True
    if e == user.employee_id:
        return True
    return bool(env['hr.employee'].sudo().search_count(
        [('id', '=', e.id)] + _emp_scope_domain(env)))


def _user_can_manage(env):
    """True nếu user thuộc bất kỳ nhóm quản lý nào (Admin/HR Mgr/HR/Giáo vụ/
    Trưởng phòng) — dùng để tách UI manager↔user và chặn manager check-in."""
    user = env.user
    emp = user.employee_id
    is_manager = bool(emp) and (
        bool(emp.child_ids)
        or bool(env['hr.department'].sudo().search_count(
            [('manager_id', '=', emp.id)])))
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hocba_employees.group_hocba_giaovu')
            or is_manager)
```

- [ ] **Step 4: Cho class method cũ delegate (không đổi hành vi)**

Trong class `HocBaHRM`, thay thân 3 method để gọi hàm module-level:

```python
    def _managed_department_ids(self, emp):
        return _managed_department_ids(request.env, emp)

    def _emp_scope_domain(self):
        return _emp_scope_domain(request.env)

    def _emp_in_scope(self, e):
        return _emp_in_scope(request.env, e)
```

Trong `_role_payload`, đổi dòng tính `can_manage = (...)` thành:
```python
        can_manage = _user_can_manage(request.env)
```
(Giữ nguyên việc tính `is_manager` và các cờ `roles` phía trên — chỉ thay nguồn của `can_manage`.)

- [ ] **Step 5: Chạy test, xác nhận PASS** (lệnh `/hocba_hrm`). Expected: `TestScopeHelpers` (4 test) xanh + các test cũ vẫn xanh; `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "refactor(attendance-api): trích helper phạm vi/quyền ra module-level"
```

---

## Task 2: Guard khóa check-in/out ở action layer (model)

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py`
- Test (create): `custom-addons/hocba_attendance/tests/test_check_lock.py` + đăng ký trong `tests/__init__.py`

- [ ] **Step 1: Viết test thất bại**

Tạo `custom-addons/hocba_attendance/tests/test_check_lock.py`:
```python
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestCheckLock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        # Bật cả 7 ngày làm việc để test once-per-day không phụ thuộc hôm nay.
        self.policy.write({
            'workday_mon': True, 'workday_tue': True, 'workday_wed': True,
            'workday_thu': True, 'workday_fri': True, 'workday_sat': True,
            'workday_sun': True, 'office_lat': 0.0, 'office_lng': 0.0,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Lock', 'x_employment_status': 'official',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789',
            'identification_id': '012345670010',
        })
        self.user = self.env['res.users'].create(
            {'name': 'Lock User', 'login': 'lock_user'})
        self.emp.user_id = self.user

    def _att(self):
        return self.env['hocba.attendance'].with_user(self.user).with_context(
            tz='Asia/Ho_Chi_Minh')

    def _payload(self):
        return {'photo': 'ZmFrZQ==', 'descriptor': [], 'latitude': 0.0,
                'longitude': 0.0}

    def test_second_checkin_rejected(self):
        self._att().action_check_in(self._payload())
        with self.assertRaises(UserError) as cm:
            self._att().action_check_in(self._payload())
        self.assertEqual(str(cm.exception), 'already_checked_in')

    def test_checkout_without_checkin_rejected(self):
        with self.assertRaises(UserError) as cm:
            self._att().action_check_out(self._payload())
        self.assertEqual(str(cm.exception), 'not_checked_in')

    def test_second_checkout_rejected(self):
        self._att().action_check_in(self._payload())
        self._att().action_check_out(self._payload())
        with self.assertRaises(UserError) as cm:
            self._att().action_check_out(self._payload())
        self.assertEqual(str(cm.exception), 'already_checked_out')

    def test_non_workday_rejected(self):
        today = fields.Date.context_today(self.user)
        flag = ['workday_mon', 'workday_tue', 'workday_wed', 'workday_thu',
                'workday_fri', 'workday_sat', 'workday_sun'][today.weekday()]
        self.policy.write({flag: False})
        with self.assertRaises(UserError) as cm:
            self._att().action_check_in(self._payload())
        self.assertEqual(str(cm.exception), 'not_workday')
```

Đăng ký test trong `custom-addons/hocba_attendance/tests/__init__.py` — thêm dòng:
```python
from . import test_check_lock
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (lệnh `/hocba_attendance`). Expected: 4 test FAIL (chưa có guard → không raise / sai message).

- [ ] **Step 3: Thêm `_assert_check_allowed` + gọi trong action**

Trong `hr_attendance.py`, thêm method (đặt ngay trước `action_check_in`):
```python
    def _assert_check_allowed(self, employee, kind):
        """Chặn check-in/out sai luật: ngày nghỉ, đã check-in/out, chưa check-in.
        Raise UserError với mã lỗi làm message để controller map sang HTTP."""
        policy = self.env['hocba.attendance.policy'].get_policy()
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'),
            fields.Datetime.now()).replace(tzinfo=None)
        if not policy.is_workday(now_local):
            raise UserError('not_workday')
        rec = self.sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', now_local.date()),
        ], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')
```

Trong `action_check_in`, thêm dòng gọi guard ngay trước `return self.sudo()._do_check(payload, 'in')`:
```python
        self._assert_check_allowed(employee, 'in')
        return self.sudo()._do_check(payload, 'in')
```
Trong `action_check_out`, tương tự trước `return self.sudo()._do_check(payload, 'out')`:
```python
        self._assert_check_allowed(employee, 'out')
        return self.sudo()._do_check(payload, 'out')
```

- [ ] **Step 4: Chạy test, xác nhận PASS** (lệnh `/hocba_attendance`). Expected: 4 test `TestCheckLock` xanh; các test cũ vẫn xanh (chúng gọi `_do_check` trực tiếp, không qua action → không ảnh hưởng); `0 failed, 0 error(s) of N tests`.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py custom-addons/hocba_attendance/tests/test_check_lock.py custom-addons/hocba_attendance/tests/__init__.py
git commit -m "feat(attendance): khóa check-in/out 1 lần/ngày + chỉ ngày làm việc (action guard)"
```

---

## Task 3: Controller chặn manager + map lỗi + me-info cờ mới

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`api_attendance_check`, `_att_me_info`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_api.py`

- [ ] **Step 1: Viết test thất bại cho me-info**

Thêm vào class `TestAttendanceApi` (file `test_attendance_api.py`):
```python
    def test_me_info_flags(self):
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertIn('canManage', info)
        self.assertIn('isWorkdayToday', info)
        self.assertFalse(info['canManage'])  # emp_user là NV thường

    def test_me_info_manager_can_manage(self):
        info = _att_me_info(self.env(user=self.hr_user))
        self.assertTrue(info['canManage'])
```
(`self.hr_user` trong setUp đã thuộc `hr.group_hr_manager`; `emp_user` là NV thường.)

- [ ] **Step 2: Chạy test, xác nhận FAIL** (`KeyError`/`assertIn` fail). Lệnh `/hocba_hrm`.

- [ ] **Step 3: Thêm cờ vào `_att_me_info`**

Trong `_att_me_info`, trong dict `info = {...}`, thêm 2 key (sau `'isHrManager': ...`):
```python
        'canManage': _user_can_manage(env),
        'isWorkdayToday': policy.is_workday(
            fields.Datetime.context_timestamp(
                env.user, fields.Datetime.now()).replace(tzinfo=None)),
```

- [ ] **Step 4: Chặn manager + map lỗi trong `api_attendance_check`**

Thêm hằng số module-level (gần đầu file, cạnh các helper):
```python
_CHECK_ERR_STATUS = {
    'not_workday': 403,
    'already_checked_in': 409,
    'not_checked_in': 409,
    'already_checked_out': 409,
}
```

Thay thân `api_attendance_check` thành:
```python
    @http.route(['/hocba-hrm/api/attendance/check-in',
                 '/hocba-hrm/api/attendance/check-out'],
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_check(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if _user_can_manage(request.env):
            return request.make_json_response(
                {'error': 'manager_no_checkin'}, status=403)
        if emp.x_employment_status != 'official':
            return request.make_json_response({'error': 'not_official'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        method = 'action_check_out' if kind == 'out' else 'action_check_in'
        try:
            res = getattr(request.env['hocba.attendance'], method)({
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
            })
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

- [ ] **Step 5: Chạy test, xác nhận PASS** (lệnh `/hocba_hrm`). Expected: `test_me_info_flags` + `test_me_info_manager_can_manage` xanh; test cũ xanh.

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "feat(attendance-api): chặn manager check-in + map lỗi khóa + cờ me-info"
```

---

## Task 4: `_att_day_table` scope theo vai trò + `canManage`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`_att_day_table`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_api.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestScopeHelpers` (đã có `self.dept`, `self.mgr_user`, `self.mgr_emp`, `self.plain_user`):
```python
    def test_day_table_department_head_sees_only_dept(self):
        in_dept = self.env['hr.employee'].create({
            'name': 'NV trong phòng', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '1110002221',
            'x_social_insurance_no': '2220001112',
            'identification_id': '012345670021'})
        out_dept = self.env['hr.employee'].create({
            'name': 'NV ngoài phòng', 'x_employment_status': 'official',
            'x_pit_code': '3330004445', 'x_social_insurance_no': '4440003332',
            'identification_id': '012345670022'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        today = fields.Date.context_today(self.mgr_user)
        for e in (in_dept, out_dept):
            Att.create({'employee_id': e.id,
                        'check_in': '%s 02:00:00' % today})
        data = _att_day_table(self.env(user=self.mgr_user), str(today))
        self.assertTrue(data['canManage'])
        emp_ids = [r['empId'] for r in data['rows']]
        self.assertIn(in_dept.id, emp_ids)
        self.assertNotIn(out_dept.id, emp_ids)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (`KeyError: 'canManage'` hoặc thấy cả 2 NV). Lệnh `/hocba_hrm`.

- [ ] **Step 3: Sửa `_att_day_table`**

`_emp_scope_domain(env)` trả domain trên model `hr.employee` (term `department_id` / `x_employee_type_id.code` / `id`). Trên `hocba.attendance` phải prefix `employee_id.` (riêng term `('id','=',0)` "không thuộc nhóm nào" đổi sang `('employee_id','=',0)`). Thay thân hàm `_att_day_table` thành:
```python
def _att_day_table(env, date_str):
    """Bảng chấm công theo ngày. Phạm vi theo vai trò (giống danh sách NV):
    HR/Admin=tất cả; trưởng phòng=phòng mình; giáo vụ=giáo viên; NV thường=của mình."""
    is_hr = env.user.has_group('hr.group_hr_user')
    is_mgr = env.user.has_group('hr.group_hr_manager')
    can_manage = _user_can_manage(env)
    day = fields.Date.from_string(date_str) if date_str else fields.Date.context_today(env.user)
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    domain = [('date', '=', day)]
    if can_manage:
        for field, op, val in _emp_scope_domain(env):  # domain trên hr.employee
            if field == 'id':            # ('id','=',0): không thuộc nhóm nào
                domain.append(('employee_id', op, val))
            else:                         # department_id / x_employee_type_id.code
                domain.append(('employee_id.%s' % field, op, val))
    else:
        emp = env.user.employee_id
        domain.append(('employee_id', '=', emp.id if emp else -1))
    recs = env['hocba.attendance'].sudo().search(domain)
    rows = [_att_row(r, policy) for r in recs]
    counts = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'missing': 0,
        'totalCredit': round(sum(r['workCredit'] for r in rows), 2),
    }
    if (is_hr or is_mgr) and policy.is_workday(day):
        total = env['hr.employee'].sudo().search_count(
            [('x_employment_status', '=', 'official')])
        counts['missing'] = max(0, total - len(rows))
    return {
        'isHr': is_hr, 'isHrManager': is_mgr, 'canManage': can_manage,
        'date': _d(day),
        'policy': _policy_dict(policy),
        'counts': counts,
        'rows': rows,
    }
```

- [ ] **Step 4: Chạy test, xác nhận PASS** (lệnh `/hocba_hrm`). Expected: `test_day_table_department_head_sees_only_dept` xanh; test `test_day_table_hr_sees_all` / `test_day_table_employee_sees_only_own` cũ vẫn xanh.

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "feat(attendance-api): bảng ngày theo phạm vi vai trò + canManage"
```

---

## Task 5: API sửa/xóa bản ghi + helper `_to_utc`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_attendance_api.py`

- [ ] **Step 1: Viết test thất bại**

Thêm vào `TestScopeHelpers`:
```python
    def test_edit_recomputes_credit(self):
        e = self.env['hr.employee'].create({
            'name': 'NV Sửa', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '5550006661',
            'x_social_insurance_no': '6660005551',
            'identification_id': '012345670031'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00',
                          'check_out': '2026-06-17 07:00:00'})  # 5h -> thiếu 180
        self.assertEqual(rec.missing_minutes, 180)
        row = _attendance_edit(self.env(user=self.mgr_user), rec.id,
                               {'checkOut': '2026-06-17T17:00'})  # 09:00->17:00 = 8h
        self.assertEqual(row['missingMinutes'], 0)
        self.assertEqual(rec.missing_minutes, 0)

    def test_edit_out_of_scope_forbidden(self):
        from odoo.exceptions import AccessError
        out = self.env['hr.employee'].create({
            'name': 'NV ngoài', 'x_employment_status': 'official',
            'x_pit_code': '7770008881', 'x_social_insurance_no': '8880007771',
            'identification_id': '012345670032'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': out.id,
                          'check_in': '2026-06-17 02:00:00'})
        with self.assertRaises(AccessError):
            _attendance_edit(self.env(user=self.mgr_user), rec.id,
                             {'notes': 'x'})

    def test_edit_non_manager_forbidden(self):
        from odoo.exceptions import AccessError
        e = self.env['hr.employee'].create({
            'name': 'NV self', 'x_employment_status': 'official',
            'x_pit_code': '9990001112', 'x_social_insurance_no': '1110009992',
            'identification_id': '012345670033'})
        e.user_id = self.plain_user
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00'})
        with self.assertRaises(AccessError):
            _attendance_edit(self.env(user=self.plain_user), rec.id,
                             {'notes': 'x'})

    def test_delete_in_scope(self):
        e = self.env['hr.employee'].create({
            'name': 'NV Xóa', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'x_pit_code': '2223334445',
            'x_social_insurance_no': '5554443332',
            'identification_id': '012345670034'})
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({'employee_id': e.id,
                          'check_in': '2026-06-17 02:00:00'})
        res = _attendance_delete(self.env(user=self.mgr_user), rec.id)
        self.assertEqual(res, {'ok': True})
        self.assertFalse(rec.exists())

    def test_to_utc_roundtrip(self):
        # 17:00 local (+07, mgr_user.tz đặt ở setUp) -> 10:00 UTC
        dt = _to_utc(self.env(user=self.mgr_user), '2026-06-17T17:00')
        self.assertEqual(str(dt), '2026-06-17 10:00:00')
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (`ImportError`/`NameError` cho `_attendance_edit`/`_to_utc` — đã import ở Task 1 Step 1 nên sẽ là `ImportError` nếu chưa định nghĩa). Lệnh `/hocba_hrm`.

- [ ] **Step 3: Thêm import pytz + helper `_to_utc`/`_attendance_edit`/`_attendance_delete`**

Đầu `main.py`, thêm import:
```python
from pytz import timezone, utc
```

Thêm các hàm module-level (cạnh các helper attendance khác):
```python
def _to_utc(env, s):
    """Chuỗi datetime local ('YYYY-MM-DDTHH:MM[:SS]') -> Datetime UTC naive.
    None/'' -> False. Dùng tz của user."""
    if not s:
        return False
    s2 = s.replace('T', ' ')
    if len(s2) == 16:          # thiếu giây
        s2 += ':00'
    naive = fields.Datetime.to_datetime(s2)
    tz = timezone(env.user.tz or 'UTC')
    return tz.localize(naive).astimezone(utc).replace(tzinfo=None)


def _attendance_edit(env, rec_id, body):
    """Manager sửa check_in/check_out/notes của 1 bản ghi trong phạm vi.
    Trả row đã cập nhật; None nếu không tồn tại; raise AccessError nếu vượt quyền."""
    rec = env['hocba.attendance'].sudo().browse(rec_id)
    if not rec.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, rec.employee_id)):
        raise AccessError('forbidden')
    vals = {}
    if 'checkIn' in body:
        vals['check_in'] = _to_utc(env, body.get('checkIn'))
    if 'checkOut' in body:
        vals['check_out'] = _to_utc(env, body.get('checkOut'))
    if 'notes' in body:
        vals['notes'] = body.get('notes') or False
    rec.sudo().write(vals)
    return _att_row(rec, env['hocba.attendance.policy'].sudo().get_policy())


def _attendance_delete(env, rec_id):
    """Manager xóa 1 bản ghi trong phạm vi. {'ok':True}; None nếu không tồn tại;
    raise AccessError nếu vượt quyền."""
    rec = env['hocba.attendance'].sudo().browse(rec_id)
    if not rec.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, rec.employee_id)):
        raise AccessError('forbidden')
    rec.sudo().unlink()
    return {'ok': True}
```

- [ ] **Step 4: Thêm 2 route trong class `HocBaHRM`**

Thêm (cạnh các route attendance khác):
```python
    @http.route('/hocba-hrm/api/attendance/<int:rec_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_edit(self, rec_id, **kw):
        try:
            row = _attendance_edit(request.env, rec_id,
                                   request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/<int:rec_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_delete(self, rec_id, **kw):
        try:
            res = _attendance_delete(request.env, rec_id)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        if res is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(res)
```
(`AccessError`, `ValidationError`, `UserError` đã import sẵn ở đầu file.)

- [ ] **Step 5: Chạy test, xác nhận PASS** (lệnh `/hocba_hrm`). Expected: 4 test edit/delete + `test_to_utc_roundtrip` xanh.

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "feat(attendance-api): API manager sửa/xóa bản ghi + helper local->UTC"
```

---

## Task 6: Frontend — tách UI user/manager + khóa nút

**Files:**
- Modify: `frontend/src/api/attendance.js`, `frontend/src/features/attendance/Attendance.jsx`, `frontend/src/features/attendance/CheckInPanel.jsx`

- [ ] **Step 1: Thêm hàm API sửa/xóa**

Cuối `frontend/src/api/attendance.js`, thêm:
```javascript
export const editAttendance = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/${id}`, body);
export const deleteAttendance = (id) =>
  hbPost(`/hocba-hrm/api/attendance/${id}/delete`, {});
```

- [ ] **Step 2: Tách UI theo `canManage` trong `Attendance.jsx`**

Thay đoạn dựng tabs + render. Đổi:
```javascript
  const isStaff = me.isHr || me.isHrManager;
  const tabs = [['me', 'Chấm công của tôi']];
  if (isStaff) tabs.push(['day', 'Bảng chấm công'], ['forgot', 'Đơn quên chấm công'], ['ot', 'Tăng ca (OT)']);
```
thành:
```javascript
  const isManager = me.canManage;
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['forgot', 'Đơn quên chấm công'], ['ot', 'Tăng ca (OT)']]
    : [['me', 'Chấm công của tôi']];
```
Và đổi state khởi tạo tab cho đúng mặc định — đổi:
```javascript
  const [tab, setTab] = useState('me');
```
thành:
```javascript
  const [tab, setTab] = useState(null);
```
rồi thêm, ngay sau `if (!me) return ...`:
```javascript
  const activeTab = tab || (me.canManage ? 'day' : 'me');
```
và thay mọi `tab === 'xxx'` trong phần render bằng `activeTab === 'xxx'`, và `className={'tab' + (tab === id ...)}` thành `(activeTab === id ...)`. (Manager không có tab `me` → khối `activeTab === 'me'` sẽ không render cho manager.)

- [ ] **Step 3: Khóa nút trong `CheckInPanel.jsx`**

(a) Map lỗi BE: trong `doCheck`, thay khối `catch (e)`:
```javascript
    } catch (e) {
      setMsg({ kind: 'err', text: 'Điểm danh thất bại (' + e.message + ').' });
    } finally { setBusy(false); }
```
bằng:
```javascript
    } catch (e) {
      const M = {
        manager_no_checkin: 'Tài khoản quản lý không điểm danh.',
        not_workday: 'Hôm nay không phải ngày làm việc.',
        already_checked_in: 'Bạn đã check-in hôm nay rồi.',
        not_checked_in: 'Bạn chưa check-in nên không thể check-out.',
        already_checked_out: 'Bạn đã check-out hôm nay rồi.',
      };
      setMsg({ kind: 'err', text: M[e.code] || ('Điểm danh thất bại (' + e.message + ').') });
    } finally { setBusy(false); }
```

(b) Khóa nút theo trạng thái. Thay khối nút (từ `) : (` ứng với `enrolled` tới hết cụm 2 nút) bằng:
```javascript
        ) : !me.isWorkdayToday ? (
          <div className="empty">Hôm nay không phải ngày làm việc — không điểm danh.</div>
        ) : (
          <div style={{ display: 'flex', gap: 10, flexDirection: 'column' }}>
            <div style={{ display: 'flex', gap: 10 }}>
              {t && t.checkIn ? (
                <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                  <Icon name="checkCircle" size={15} /> Đã check-in lúc {fmtTime(t.checkIn)}
                </div>
              ) : (
                <button className="btn btn-primary" disabled={busy || !ready} onClick={() => doCheck('in')}>
                  <Icon name="checkCircle" size={16} />Check-in
                </button>
              )}
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              {t && t.checkOut ? (
                <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                  <Icon name="logout" size={15} /> Đã check-out lúc {fmtTime(t.checkOut)}
                </div>
              ) : (
                <button className="btn btn-ghost" disabled={busy || !ready || !(t && t.checkIn)} onClick={() => doCheck('out')}>
                  <Icon name="logout" size={16} />Check-out
                </button>
              )}
            </div>
          </div>
        )}
```
(Cụm `!me.isOfficial` và `!enrolled` phía trên giữ nguyên thứ tự: official? → enrolled? → workday? → nút.)

- [ ] **Step 4: Build & kiểm tra**
```bash
cd frontend && npm run build
```
Expected: build OK. Đăng nhập user official: nếu đã check-in → nút check-in thay bằng "Đã check-in lúc…"; chưa check-in → nút check-out disable; ngày nghỉ → thông báo. Manager: vào thẳng tab "Bảng chấm công", không có panel.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/api/attendance.js frontend/src/features/attendance/Attendance.jsx frontend/src/features/attendance/CheckInPanel.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): tách UI manager/user + khóa nút check-in/out"
```

---

## Task 7: Frontend — manager sửa/xóa trong drawer/table

**Files:**
- Modify: `frontend/src/features/attendance/AttendanceTable.jsx`, `frontend/src/features/attendance/AttendanceDrawer.jsx`

- [ ] **Step 1: Truyền `canManage` + callback refetch từ `AttendanceTable`**

Trong `AttendanceTable.jsx`, đổi nơi render drawer:
```javascript
      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
```
thành:
```javascript
      {sel && <AttendanceDrawer rec={sel} canManage={data.canManage}
        onClose={() => setSel(null)} onChanged={() => { setSel(null); load(); }} />}
```

- [ ] **Step 2: Thêm form sửa + nút xóa trong `AttendanceDrawer.jsx`**

Đầu file, đổi imports:
```javascript
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus } from './util';
```
thành:
```javascript
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus } from './util';
import { editAttendance, deleteAttendance } from '../../api/attendance';
```

Đổi chữ ký component:
```javascript
export default function AttendanceDrawer({ rec, onClose }) {
```
thành:
```javascript
export default function AttendanceDrawer({ rec, onClose, canManage, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const dtLocal = (iso) => (iso ? iso.slice(0, 16) : '');
  const [form, setForm] = useState({
    checkIn: dtLocal(rec.checkIn), checkOut: dtLocal(rec.checkOut),
    notes: rec.notes || '',
  });

  async function save() {
    setBusy(true); setErr(null);
    try {
      await editAttendance(rec.id, {
        checkIn: form.checkIn || null,
        checkOut: form.checkOut || null,
        notes: form.notes,
      });
      onChanged && onChanged();
    } catch (e) { setErr('Lưu thất bại (' + e.message + ').'); }
    finally { setBusy(false); }
  }

  async function remove() {
    if (!window.confirm('Xóa bản ghi chấm công ngày ' + fmtDate(rec.date) + ' của ' + rec.name + '?')) return;
    setBusy(true); setErr(null);
    try {
      await deleteAttendance(rec.id);
      onChanged && onChanged();
    } catch (e) { setErr('Xóa thất bại (' + e.message + ').'); }
    finally { setBusy(false); }
  }
```

Ngay TRƯỚC thẻ đóng `</Modal>` ở cuối component, thêm khối form + footer (sau `</div>` của vùng nội dung cuộn):
```javascript
        {canManage && !editing && (
          <div style={{ display: 'flex', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}><Icon name="pencil" size={15} />Sửa</button>
            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={remove}><Icon name="trash" size={15} />Xóa</button>
          </div>
        )}
        {canManage && editing && (
          <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <label style={{ fontSize: 12.5 }}>Check-in
              <input type="datetime-local" className="sel" value={form.checkIn}
                onChange={(e) => setForm({ ...form, checkIn: e.target.value })} />
            </label>
            <label style={{ fontSize: 12.5 }}>Check-out
              <input type="datetime-local" className="sel" value={form.checkOut}
                onChange={(e) => setForm({ ...form, checkOut: e.target.value })} />
            </label>
            <label style={{ fontSize: 12.5 }}>Ghi chú
              <textarea className="sel" rows={2} value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </label>
            {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary btn-sm" disabled={busy} onClick={save}>Lưu</button>
              <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => setEditing(false)}>Hủy</button>
            </div>
          </div>
        )}
```
(Nếu icon `pencil`/`trash` không tồn tại trong bộ Icon, dùng `edit`/`x` — kiểm `frontend/src/components/Icon.jsx` và chọn tên hợp lệ; nếu không có tên phù hợp, bỏ thuộc tính `name` icon, chỉ để chữ.)

- [ ] **Step 3: Build & kiểm tra**
```bash
cd frontend && npm run build
```
Expected: build OK. Manager mở 1 dòng bảng ngày → có nút Sửa/Xóa; Sửa giờ → Lưu → bảng refetch, giờ + công cập nhật; Xóa (xác nhận) → bản ghi biến mất. User thường: drawer không có nút (lịch sử của tôi vẫn read-only).

- [ ] **Step 4: Commit**
```bash
git add frontend/src/features/attendance/AttendanceTable.jsx frontend/src/features/attendance/AttendanceDrawer.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): manager sửa/xóa bản ghi trong drawer"
```

---

## Task 8: Verify toàn bộ (test backend + build)

- [ ] **Step 1: Test `hocba_attendance`** — lệnh `/hocba_attendance` (mục đầu). Expected: `0 failed, 0 error(s) of N tests`, N>0.
- [ ] **Step 2: Test `hocba_hrm`** — lệnh `/hocba_hrm`. Expected: `0 failed, 0 error(s) of N tests`, N>0.
- [ ] **Step 3: Build frontend** — `cd frontend && npm run build`. Expected: build OK, không lỗi.

---

## Notes cho người thực thi
- Giờ trong test là **UTC**; tz context `Asia/Ho_Chi_Minh` (+07). 09:00 local = 02:00 UTC.
- NV `official` trong test phải có `identification_id` 12 số (BR-010) — dùng giá trị khác nhau mỗi NV.
- `_assert_check_allowed` raise `UserError(<mã>)`; controller map `<mã>`→HTTP. Đừng đổi message thành tiếng Việt ở model (FE map mã sang tiếng Việt).
- Không đổi route check-in/out cũ ngoài việc thêm chặn manager + try/except; không đổi logic face/geo của `_do_check`.
- Route `/api/attendance/<int:rec_id>` chỉ khớp số nguyên → không đụng `/check-in`, `/me`, `/me/history`.
