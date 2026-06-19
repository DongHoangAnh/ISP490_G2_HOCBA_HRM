# Gói 4C — Công OT theo hệ số (3 mốc) + sửa nốt 4B — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quy đổi giờ ca OT đã duyệt × hệ số (3 mốc 100/150/300% chọn tay) thành giờ công OT gộp vào tổng hợp tháng, thêm màn quản lý OT cho manager, và sửa cờ `needs_review` nhiễu cho CTV check-in đúng cửa sổ (4B).

**Architecture:** Mốc hệ số lưu ở field `ot_level` (Selection) trên `hocba.work_shift`; `rate` (Float) computed-store suy ra từ `ot_level`. Backend gộp OT vào API qua helper module-level trong `hocba_hrm/controllers/main.py` (`_ot_row`, `_ot_for_employee`, `_ot_table`, `_shift_set_level`). Frontend React thêm select mốc + tab "Chấm công OT".

**Tech Stack:** Odoo 19 (Python), React/Vite SPA (build → `custom-addons/hocba_hrm/static/spa`), test Odoo `TransactionCase` chạy trên Docker.

## Global Constraints

- **Test trên Docker local, KHÔNG Neon.** `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` BẮT BUỘC (Git Bash Windows). Luôn `-u <module>,hocba_employees`. Xác nhận dòng `0 failed, 0 error(s) of N tests` với **N > 0**.
- **BR-010:** NV `official` trong test PHẢI có `identification_id` 12 chữ số (mỗi NV một giá trị khác). NV non-official (ctv) KHÔNG cần.
- Giờ lưu **UTC**; test dùng `.with_context(tz='Asia/Ho_Chi_Minh')` (+07): 09:00 local = 02:00 UTC.
- 3 mốc hệ số: `'100'→1.0`, `'150'→1.5`, `'300'→3.0`. Mặc định `'100'`.
- Giờ OT = giờ ca kế hoạch `(end−start)`; chỉ tính (counted) khi ngày local đó NV có bản ghi `hocba.attendance` đã check-in.
- Wire format API: camelCase.
- Quy ước commit: cuối message thêm `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## File Structure

**Backend**
- Modify `custom-addons/hocba_attendance/models/hocba_work_shift.py` — thêm `ot_level`, đổi `rate` thành computed-store, xóa `_default_rate`.
- Modify `custom-addons/hocba_attendance/models/hr_attendance.py` — `_do_check`: `out_of_window` theo cửa sổ ca cho non-official.
- Modify `custom-addons/hocba_hrm/controllers/main.py` — `_shift_row.otLevel`, `_shift_create`/`_shift_decide` theo `otLevel`, thêm `_ot_row`/`_ot_for_employee`/`_ot_table`/`_shift_set_level`, OT vào `_att_me_history`, 2 route mới.
- Create `custom-addons/hocba_attendance/tests/test_ot_shift.py` — test model (compute rate + 4B fix).
- Modify `custom-addons/hocba_attendance/tests/__init__.py` — đăng ký test mới.
- Create `custom-addons/hocba_hrm/tests/test_ot_payroll.py` — test API OT.
- Modify `custom-addons/hocba_hrm/tests/__init__.py` — đăng ký test mới.
- Modify `custom-addons/hocba_hrm/tests/test_shift_api.py` — cập nhật test cũ (bỏ auto-rate → otLevel).

**Frontend** (`frontend/src/`)
- Modify `api/attendance.js` — `fetchOtTable`, `setShiftLevel`.
- Modify `features/attendance/ShiftForm.jsx` — select mốc.
- Modify `features/attendance/ShiftDrawer.jsx` — override bằng select mốc.
- Modify `features/attendance/MyHistory.jsx` — 2 thẻ OT.
- Create `features/attendance/OtTable.jsx` — bảng OT tháng (manager).
- Modify `features/attendance/Attendance.jsx` — tab "Chấm công OT".

---

## Task 1: Model — `ot_level` + `rate` computed-store, xóa `_default_rate`

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_work_shift.py:21` (field `rate`), `:55-62` (`_default_rate`)
- Create: `custom-addons/hocba_attendance/tests/test_ot_shift.py`
- Modify: `custom-addons/hocba_attendance/tests/__init__.py`

**Interfaces:**
- Produces: `hocba.work_shift.ot_level` (Selection `'100'/'150'/'300'`, default `'100'`); `hocba.work_shift.rate` (Float, computed-store, depends `ot_level`, mapping `_OT_RATE`). `_default_rate` bị xóa.

- [ ] **Step 1: Viết test thất bại** — tạo `custom-addons/hocba_attendance/tests/test_ot_shift.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOtShift(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV OT', 'x_employment_status': 'ctv'})

    def _shift(self, **vals):
        base = {
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00', 'end': '2026-06-15 04:00:00',
            'shift_type': 'ot',
        }
        base.update(vals)
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create(base)

    def test_default_level_is_100(self):
        s = self._shift()
        self.assertEqual(s.ot_level, '100')
        self.assertEqual(s.rate, 1.0)

    def test_level_maps_to_rate(self):
        self.assertEqual(self._shift(ot_level='150').rate, 1.5)
        self.assertEqual(self._shift(ot_level='300',
                         start='2026-06-16 02:00:00',
                         end='2026-06-16 04:00:00').rate, 3.0)

    def test_changing_level_recomputes_rate(self):
        s = self._shift(ot_level='150')
        self.assertEqual(s.rate, 1.5)
        s.ot_level = '300'
        self.assertEqual(s.rate, 3.0)
```

- [ ] **Step 2: Đăng ký test** — thêm vào `custom-addons/hocba_attendance/tests/__init__.py`:

```python
from . import test_ot_shift
```

- [ ] **Step 3: Chạy test, xác nhận FAIL**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance:TestOtShift --stop-after-init --log-level=test
```
Expected: FAIL — `ot_level` chưa tồn tại (Invalid field / ValueError).

- [ ] **Step 4: Sửa model** — trong `hocba_work_shift.py` thay field `rate` (dòng 21) bằng:

```python
    ot_level = fields.Selection(
        [('100', '100%'), ('150', '150%'), ('300', '300%')],
        string='Mức hệ số', default='100', required=True,
        help='Mức quy đổi công OT do người dùng chọn; manager đổi được.')
    rate = fields.Float(
        string='Hệ số', compute='_compute_rate', store=True,
        help='Suy từ mức: 100%→1.0, 150%→1.5, 300%→3.0.')
```

Thêm hằng + compute (đặt cạnh các `@api.constrains`, ví dụ ngay trước `_check_times`):

```python
    _OT_RATE = {'100': 1.0, '150': 1.5, '300': 3.0}

    @api.depends('ot_level')
    def _compute_rate(self):
        for rec in self:
            rec.rate = self._OT_RATE.get(rec.ot_level, 1.0)
```

Xóa hẳn method `_default_rate` (dòng 55-62).

- [ ] **Step 5: Chạy test, xác nhận PASS** (cùng lệnh Step 3). Expected: `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance/models/hocba_work_shift.py custom-addons/hocba_attendance/tests/test_ot_shift.py custom-addons/hocba_attendance/tests/__init__.py
git commit -m "feat(attendance): ot_level 3 mốc + rate computed-store, bỏ _default_rate (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Model — `_do_check` `out_of_window` theo cửa sổ ca cho non-official (sửa nốt 4B)

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py:255`
- Modify: `custom-addons/hocba_attendance/tests/test_ot_shift.py` (thêm test)

**Interfaces:**
- Consumes: `_todays_approved_shifts(employee, today)` (đã có), `policy.shift_window_minutes`.
- Produces: `_do_check` set `out_of_window=False` cho non-official check-in/out trong cửa sổ ±W; official giữ `policy.is_within_window`.

- [ ] **Step 1: Viết test thất bại** — thêm vào `TestOtShift` trong `test_ot_shift.py`:

```python
    def test_do_check_non_official_in_window_not_flagged(self):
        from odoo import fields as f
        from datetime import timedelta
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        now = f.Datetime.now()
        # ca approved quanh thời điểm hiện tại (start = now)
        self.env['hocba.work_shift'].create({
            'employee_id': self.emp.id, 'state': 'approved', 'shift_type': 'ot',
            'ot_level': '150',
            'start': now, 'end': now + timedelta(hours=2)})
        res = Att.sudo()._do_check({
            'employee_id': self.emp.id, 'descriptor': [], 'photo': False,
            'latitude': 0.0, 'longitude': 0.0}, 'in')
        self.assertFalse(res['out_of_window'])
        rec = Att.browse(res['record_id'])
        self.assertFalse(rec.needs_review)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance:TestOtShift.test_do_check_non_official_in_window_not_flagged --stop-after-init --log-level=test
```
Expected: FAIL — `out_of_window` đang `True` (assertFalse fails).

- [ ] **Step 3: Sửa `_do_check`** — trong `hr_attendance.py`, thay dòng:

```python
        out_of_window = not policy.is_within_window(now_local, kind)
```
bằng:

```python
        if employee.x_employment_status == 'official':
            out_of_window = not policy.is_within_window(now_local, kind)
        else:
            # non-official (CTV/OT): cờ theo cửa sổ ±W quanh giờ ca approved
            window = policy.shift_window_minutes or 15
            in_win = False
            for s in self._todays_approved_shifts(employee, today):
                anchor = fields.Datetime.context_timestamp(
                    s, s.start if kind == 'in' else s.end).replace(tzinfo=None)
                if abs((now_local - anchor).total_seconds()) <= window * 60:
                    in_win = True
                    break
            out_of_window = not in_win
```

- [ ] **Step 4: Chạy lại cả lớp, xác nhận PASS**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance:TestOtShift --stop-after-init --log-level=test
```
Expected: PASS, N>0.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py custom-addons/hocba_attendance/tests/test_ot_shift.py
git commit -m "fix(attendance): _do_check out_of_window theo cửa sổ ca cho CTV/OT (sửa nốt 4B)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: API — `_shift_row.otLevel` + `_shift_create`/`_shift_decide` theo `otLevel` (+ cập nhật test cũ)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — `_shift_row` (~484), `_shift_create` (~509-520), `_shift_decide` (~593-594)
- Modify: `custom-addons/hocba_hrm/tests/test_shift_api.py` — cập nhật test phụ thuộc auto-rate cũ

**Interfaces:**
- Consumes: `hocba.work_shift.ot_level` (Task 1).
- Produces: `_shift_row(s)` trả thêm `'otLevel': s.ot_level`. `_shift_create` đọc `body['otLevel']` (default `'100'`, validate). `_shift_decide` override bằng `body['otLevel']`.

- [ ] **Step 1: Cập nhật test cũ + thêm test mới** trong `test_shift_api.py`:

Sửa `_make_shift` (dòng 30): bỏ `'rate': 1.5`, đổi thành `'ot_level': '150'`:
```python
            'shift_type': 'ctv', 'ot_level': '150', 'state': 'pending',
```
`test_shift_row_shape` (dòng 41): giữ `self.assertEqual(row['rate'], 1.5)` (ot_level 150 → 1.5) và thêm `self.assertEqual(row['otLevel'], '150')`.

Thay `test_create_pins_employee_and_default_rate` (dòng 47-56) bằng:
```python
    def test_create_pins_employee_default_level_100(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-15T09:00', 'end': '2026-06-15T11:00',
            'shiftType': 'ctv', 'reason': 'Trực sáng'})
        self.assertEqual(row['empId'], self.emp.id)
        self.assertEqual(row['state'], 'pending')
        self.assertEqual(row['otLevel'], '100')
        self.assertEqual(row['rate'], 1.0)
        s = env['hocba.work_shift'].browse(row['id'])
        self.assertEqual(str(s.start), '2026-06-15 02:00:00')
```

Thay `test_create_weekend_rate` (dòng 58-63) bằng:
```python
    def test_create_with_level_300(self):
        env = self.env(user=self.user)
        row = _shift_create(env, {
            'start': '2026-06-20T09:00', 'end': '2026-06-20T11:00',
            'shiftType': 'ot', 'otLevel': '300'})
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)

    def test_create_bad_level_raises(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _shift_create(env, {'start': '2026-06-20T09:00',
                                'end': '2026-06-20T11:00',
                                'shiftType': 'ot', 'otLevel': '999'})
```

Thay `test_decide_approve_with_override` (dòng 159-167) bằng:
```python
    def test_decide_approve_with_override(self):
        env = self.env(user=self.hrm)
        s = self._make_shift()
        row = _shift_decide(env, s.id, True, {'otLevel': '300',
                            'end': '2026-06-15T12:00'})
        self.assertEqual(row['state'], 'approved')
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)
        self.assertEqual(row['end'], '2026-06-15T12:00:00')
        self.assertEqual(row['reviewer'], self.hrm.name)

    def test_decide_bad_level_override_raises(self):
        env = self.env(user=self.hrm)
        s = self._make_shift()
        with self.assertRaises(ValidationError):
            _shift_decide(env, s.id, True, {'otLevel': '999'})
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm:TestShiftApi --stop-after-init --log-level=test
```
Expected: FAIL — `otLevel` chưa có trong `_shift_row`; `_shift_create`/`_shift_decide` chưa xử lý `otLevel`.

- [ ] **Step 3: Sửa `main.py`**

`_shift_row` — thêm sau `'shiftType': s.shift_type,`:
```python
        'otLevel': s.ot_level,
```
(giữ `'rate': s.rate,`.)

`_shift_create` — thay khối tạo `vals` (đoạn `shift_type` … `'rate': Shift._default_rate(start),`):
```python
    shift_type = body.get('shiftType')
    if shift_type not in ('ctv', 'ot'):
        raise ValidationError('Loại ca không hợp lệ.')
    level = body.get('otLevel') or '100'
    if level not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    start = _to_utc(env, body.get('start'))
    end = _to_utc(env, body.get('end'))
    if not start or not end:
        raise ValidationError('Cần giờ bắt đầu và kết thúc.')
    vals = {
        'employee_id': emp.id,
        'start': start, 'end': end,
        'shift_type': shift_type,
        'ot_level': level,
        'reason': (body.get('reason') or '').strip() or False,
    }
```

`_shift_decide` — thay nhánh `if 'rate' in body:`:
```python
        if 'otLevel' in body:
            if body['otLevel'] not in ('100', '150', '300'):
                raise ValidationError('Mức hệ số không hợp lệ.')
            vals['ot_level'] = body['otLevel']
```

- [ ] **Step 4: Chạy test, xác nhận PASS** (cùng lệnh Step 2). Expected: PASS, N>0.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_api.py
git commit -m "feat(shift-api): _shift_row.otLevel + create/decide theo otLevel (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: API — helper OT (`_ot_row`, `_ot_for_employee`) + gộp vào `_att_me_history`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — thêm `_ot_row`/`_ot_for_employee` (cạnh `_att_me_history`), sửa `_att_me_history`
- Create: `custom-addons/hocba_hrm/tests/test_ot_payroll.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: `_d`, `_dt_local` (đã có), `hocba.work_shift`, `hocba.attendance`.
- Produces:
  - `_ot_row(env, s)` → dict: `{id, empId, empName, code, depName, date, start, end, otLevel, rate, hours, counted, creditHours, state}`. `hours=(end−start)/3600`; `counted`=có attendance check-in ngày local của `start`; `creditHours=round(hours*rate,2) if counted else 0.0`.
  - `_ot_for_employee(env, emp, first, last)` → `{otHours, otCreditHours}` (chỉ ca approved có start trong [first,last]; `otHours`=Σ hours ca counted; `otCreditHours`=Σ creditHours).
  - `_att_me_history(...).summary` thêm `otHours`, `otCreditHours`.

- [ ] **Step 1: Viết test thất bại** — tạo `custom-addons/hocba_hrm/tests/test_ot_payroll.py`:

```python
from datetime import date
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _ot_row, _ot_for_employee, _att_me_history)


@tagged('post_install', '-at_install')
class TestOtPayroll(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV P', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV P User', 'login': 'ctv_ot_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user

    def _shift(self, day, level='150', state='approved'):
        # day='2026-06-15' -> 09:00-11:00 local (02:00-04:00 UTC), 2 giờ
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'shift_type': 'ot',
                'ot_level': level, 'state': state,
                'start': day + ' 02:00:00', 'end': day + ' 04:00:00'})

    def _attendance(self, day):
        # check-in lúc 02:00 UTC ngày day -> date local = day
        return self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').sudo().create({
                'employee_id': self.emp.id, 'check_in': day + ' 02:00:00'})

    def test_ot_row_counted(self):
        s = self._shift('2026-06-15', level='150')
        self._attendance('2026-06-15')
        row = _ot_row(self.env, s)
        self.assertEqual(row['hours'], 2.0)
        self.assertTrue(row['counted'])
        self.assertEqual(row['creditHours'], 3.0)   # 2h * 1.5
        self.assertEqual(row['otLevel'], '150')

    def test_ot_row_not_counted_when_no_attendance(self):
        s = self._shift('2026-06-15')
        row = _ot_row(self.env, s)
        self.assertFalse(row['counted'])
        self.assertEqual(row['creditHours'], 0.0)

    def test_for_employee_sums_counted_only(self):
        self._shift('2026-06-15', level='150'); self._attendance('2026-06-15')
        self._shift('2026-06-16', level='300')  # không có attendance -> bỏ
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otHours'], 2.0)
        self.assertEqual(res['otCreditHours'], 3.0)

    def test_for_employee_excludes_pending_and_other_month(self):
        self._shift('2026-06-15', state='pending'); self._attendance('2026-06-15')
        self._shift('2026-05-15', level='300'); self._attendance('2026-05-15')
        res = _ot_for_employee(self.env, self.emp, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(res['otCreditHours'], 0.0)

    def test_me_history_summary_has_ot(self):
        self._shift('2026-06-15', level='300'); self._attendance('2026-06-15')
        data = _att_me_history(self.env(user=self.user), '2026-06')
        self.assertEqual(data['summary']['otHours'], 2.0)
        self.assertEqual(data['summary']['otCreditHours'], 6.0)   # 2h * 3.0
```

- [ ] **Step 2: Đăng ký test** — thêm vào `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_ot_payroll
```

- [ ] **Step 3: Chạy test, xác nhận FAIL**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm:TestOtPayroll --stop-after-init --log-level=test
```
Expected: FAIL — `_ot_row` chưa định nghĩa (ImportError).

- [ ] **Step 4: Thêm helper + sửa `_att_me_history`** trong `main.py` (đặt `_ot_row`/`_ot_for_employee` ngay trên `_att_me_history`):

```python
def _ot_row(env, s):
    """Một ca OT cho SPA (camelCase) + cờ counted / giờ quy đổi.
    counted = ngày local của start có bản ghi attendance đã check-in."""
    hours = ((s.end - s.start).total_seconds() / 3600.0) if (s.start and s.end) else 0.0
    d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
    counted = bool(d and env['hocba.attendance'].sudo().search_count([
        ('employee_id', '=', s.employee_id.id), ('date', '=', d),
        ('check_in', '!=', False)]))
    emp = s.employee_id
    return {
        'id': s.id, 'empId': emp.id, 'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'date': _d(d) if d else None,
        'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
        'otLevel': s.ot_level, 'rate': s.rate,
        'hours': round(hours, 2), 'counted': counted,
        'creditHours': round(hours * s.rate, 2) if counted else 0.0,
        'state': s.state,
    }


def _ot_for_employee(env, emp, first, last):
    """Tổng OT của 1 NV trong [first,last] (ca approved, start trong tháng,
    chỉ cộng ca counted). Trả {otHours, otCreditHours}."""
    shifts = env['hocba.work_shift'].sudo().search([
        ('employee_id', '=', emp.id), ('state', '=', 'approved')])
    rows = []
    for s in shifts:
        d = fields.Datetime.context_timestamp(s, s.start).date()
        if first <= d <= last:
            rows.append(_ot_row(env, s))
    return {
        'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
        'otCreditHours': round(sum(r['creditHours'] for r in rows), 2),
    }
```

Trong `_att_me_history`, trước dòng `return {'month': ...}`, thêm:
```python
    ot = _ot_for_employee(env, emp, first, last)
    summary['otHours'] = ot['otHours']
    summary['otCreditHours'] = ot['otCreditHours']
```

- [ ] **Step 5: Chạy test, xác nhận PASS** (cùng lệnh Step 3). Expected: PASS, N>0.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_ot_payroll.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(ot-api): _ot_row/_ot_for_employee + OT vào _att_me_history (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: API — `_ot_table` + route `GET /api/shifts/ot`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — thêm `_ot_table` (cạnh `_ot_for_employee`) + route trong class controller (cạnh `api_shifts_week`)
- Modify: `custom-addons/hocba_hrm/tests/test_ot_payroll.py` (thêm test)

**Interfaces:**
- Consumes: `_ot_row` (Task 4), `_emp_scope_domain`, `_user_can_manage`, `expression`, `timezone/datetime/utc/timedelta` (đã import ở đầu file cho `_shifts_week`).
- Produces: `_ot_table(env, month_str)` → `{month, canManage, rows, totals}` với `totals={otHours, otCreditHours, count, countedCount}`. `rows`=mọi ca approved trong tháng theo phạm vi (mỗi ca qua `_ot_row`). Route `GET /hocba-hrm/api/shifts/ot?month=`.

- [ ] **Step 1: Viết test thất bại** — thêm vào `TestOtPayroll`:

```python
    def test_ot_table_scope_and_totals(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        self._shift('2026-06-15', level='150'); self._attendance('2026-06-15')
        self._shift('2026-06-16', level='300')   # không attendance -> counted False
        hrm = self.env['res.users'].create({
            'name': 'HRM OT', 'login': 'hrm_ot',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        hrm.tz = 'Asia/Ho_Chi_Minh'
        data = _ot_table(self.env(user=hrm), '2026-06')
        self.assertTrue(data['canManage'])
        self.assertEqual(len(data['rows']), 2)            # cả 2 ca approved
        self.assertEqual(data['totals']['otHours'], 2.0)   # chỉ ca counted
        self.assertEqual(data['totals']['otCreditHours'], 3.0)
        self.assertEqual(data['totals']['count'], 2)
        self.assertEqual(data['totals']['countedCount'], 1)

    def test_ot_table_user_sees_only_own(self):
        from odoo.addons.hocba_hrm.controllers.main import _ot_table
        self._shift('2026-06-15'); self._attendance('2026-06-15')
        data = _ot_table(self.env(user=self.user), '2026-06')
        self.assertFalse(data['canManage'])
        self.assertTrue(all(r['empId'] == self.emp.id for r in data['rows']))
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (cùng lệnh Task 4 Step 3). Expected: FAIL — `_ot_table` chưa định nghĩa.

- [ ] **Step 3: Thêm `_ot_table`** trong `main.py` (sau `_ot_for_employee`):

```python
def _ot_table(env, month_str):
    """Bảng ca OT approved theo tháng + phạm vi vai trò (giống _att_day_table).
    rows=mọi ca approved trong tháng; totals cộng ca counted. canManage."""
    user = env.user
    if month_str:
        y, m = (int(x) for x in month_str.split('-'))
    else:
        today = fields.Date.context_today(user)
        y, m = today.year, today.month
    tz = timezone(user.tz or 'UTC')
    start_local = tz.localize(datetime(y, m, 1))
    end_local = (tz.localize(datetime(y + 1, 1, 1)) if m == 12
                 else tz.localize(datetime(y, m + 1, 1)))
    start_utc = start_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(utc).replace(tzinfo=None)
    domain = [('state', '=', 'approved'),
              ('start', '>=', start_utc), ('start', '<', end_utc)]
    if _user_can_manage(env):
        for field, op, val in _emp_scope_domain(env):
            if field == 'id':
                domain.append(('employee_id', op, val))
            else:
                domain.append(('employee_id.%s' % field, op, val))
    else:
        emp = user.employee_id
        domain.append(('employee_id', '=', emp.id if emp else -1))
    recs = env['hocba.work_shift'].sudo().search(domain, order='start')
    rows = [_ot_row(env, s) for s in recs]
    return {
        'month': '%04d-%02d' % (y, m),
        'canManage': _user_can_manage(env),
        'rows': rows,
        'totals': {
            'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
            'otCreditHours': round(sum(r['creditHours'] for r in rows), 2),
            'count': len(rows),
            'countedCount': sum(1 for r in rows if r['counted']),
        },
    }
```

**Lưu ý import:** dùng `datetime`, `timezone`, `utc` (đã import sẵn đầu `main.py` cho `_shifts_week`) — KHÔNG cần `relativedelta`. Tháng kế tính tay (`m == 12` → năm sau).

- [ ] **Step 4: Thêm route** trong class controller (cạnh `api_shifts_week`, ~dòng 1888):

```python
    @http.route('/hocba-hrm/api/shifts/ot', auth='user', type='http', methods=['GET'])
    def api_shifts_ot(self, month=None, **kw):
        return request.make_json_response(_ot_table(request.env, month))
```

- [ ] **Step 5: Chạy test, xác nhận PASS** (cùng lệnh Task 4 Step 3). Expected: PASS, N>0.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_ot_payroll.py
git commit -m "feat(ot-api): _ot_table + route GET /api/shifts/ot (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: API — `_shift_set_level` + route `POST /api/shifts/<id>/level`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — thêm `_shift_set_level` (cạnh `_shift_decide`) + route (cạnh `api_shift_cancel`)
- Modify: `custom-addons/hocba_hrm/tests/test_ot_payroll.py` (thêm test)

**Interfaces:**
- Consumes: `_user_can_manage`, `_emp_in_scope`, `_shift_row`.
- Produces: `_shift_set_level(env, shift_id, level)` → `_shift_row`; `None` nếu không tồn tại; `AccessError` ngoài quyền; `ValidationError` nếu level sai hoặc ca không `approved`. Route `POST /hocba-hrm/api/shifts/<int:shift_id>/level` body `{otLevel}`.

- [ ] **Step 1: Viết test thất bại** — thêm vào `TestOtPayroll`:

```python
    def test_set_level_manager_in_scope(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        s = self._shift('2026-06-15', level='150')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL', 'login': 'hrm_sl',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        row = _shift_set_level(self.env(user=hrm), s.id, '300')
        self.assertEqual(row['otLevel'], '300')
        self.assertEqual(row['rate'], 3.0)

    def test_set_level_bad_value_raises(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import ValidationError
        s = self._shift('2026-06-15')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL2', 'login': 'hrm_sl2',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        with self.assertRaises(ValidationError):
            _shift_set_level(self.env(user=hrm), s.id, '999')

    def test_set_level_pending_raises(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import ValidationError
        s = self._shift('2026-06-15', state='pending')
        hrm = self.env['res.users'].create({
            'name': 'HRM SL3', 'login': 'hrm_sl3',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        with self.assertRaises(ValidationError):
            _shift_set_level(self.env(user=hrm), s.id, '300')

    def test_set_level_out_of_scope_forbidden(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        from odoo.exceptions import AccessError
        dept = self.env['hr.department'].create({'name': 'Phòng Q'})
        mgr_emp = self.env['hr.employee'].create({'name': 'TP Q'})
        dept.manager_id = mgr_emp
        mgr_user = self.env['res.users'].create({'name': 'TPQ', 'login': 'tpq_ot'})
        mgr_emp.user_id = mgr_user
        s = self._shift('2026-06-15')   # self.emp ngoài Phòng Q
        with self.assertRaises(AccessError):
            _shift_set_level(self.env(user=mgr_user), s.id, '300')

    def test_set_level_missing_returns_none(self):
        from odoo.addons.hocba_hrm.controllers.main import _shift_set_level
        hrm = self.env['res.users'].create({
            'name': 'HRM SL4', 'login': 'hrm_sl4',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})
        self.assertIsNone(_shift_set_level(self.env(user=hrm), 999999, '300'))
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (cùng lệnh Task 4 Step 3). Expected: FAIL — `_shift_set_level` chưa định nghĩa.

- [ ] **Step 3: Thêm `_shift_set_level`** trong `main.py` (sau `_shift_decide`):

```python
def _shift_set_level(env, shift_id, level):
    """Manager (trong phạm vi) đổi mốc hệ số 1 ca approved (màn Chấm công OT).
    Trả _shift_row; None nếu không tồn tại; AccessError nếu vượt quyền;
    ValidationError nếu mốc sai / ca không ở trạng thái approved."""
    if level not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)):
        raise AccessError('forbidden')
    if shift.state != 'approved':
        raise ValidationError('Chỉ đổi mức cho ca đã duyệt.')
    shift.write({'ot_level': level})
    return _shift_row(shift)
```

- [ ] **Step 4: Thêm route** trong class controller (cạnh `api_shift_cancel`, ~dòng 1920):

```python
    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/level', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_set_level(self, shift_id, **kw):
        try:
            row = _shift_set_level(request.env, shift_id,
                                   (request.get_json_data() or {}).get('otLevel'))
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)
```

- [ ] **Step 5: Chạy test, xác nhận PASS** (cùng lệnh Task 4 Step 3). Expected: PASS, N>0.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_ot_payroll.py
git commit -m "feat(ot-api): _shift_set_level + route POST /api/shifts/<id>/level (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: FE — api client + ShiftForm (chọn mốc) + ShiftDrawer (override mốc)

**Files:**
- Modify: `frontend/src/api/attendance.js`
- Modify: `frontend/src/features/attendance/ShiftForm.jsx`
- Modify: `frontend/src/features/attendance/ShiftDrawer.jsx`

**Interfaces:**
- Consumes: route `GET /api/shifts/ot`, `POST /api/shifts/<id>/level` (Task 5, 6); `_shift_row.otLevel`.
- Produces: `fetchOtTable(month)`, `setShiftLevel(id, otLevel)`. ShiftForm gửi `otLevel` qua `createShift`; ShiftDrawer gửi `otLevel` qua `approveShift`.

- [ ] **Step 1: api/attendance.js** — thêm cuối file:

```js
export const fetchOtTable = (month) =>
  hbGet(`/hocba-hrm/api/shifts/ot?month=${month}`);
export const setShiftLevel = (id, otLevel) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/level`, { otLevel });
```

- [ ] **Step 2: ShiftForm.jsx** — thêm `otLevel` vào state (dòng 9):

```jsx
  const [form, setForm] = useState({ start: '', end: '', shiftType: 'ot', otLevel: '100', reason: '' });
```

Trong `createShift` (dòng 17-20) thêm `otLevel`:
```jsx
      await createShift({
        start: form.start, end: form.end,
        shiftType: form.shiftType, otLevel: form.otLevel,
        reason: form.reason.trim(),
      });
```

Thêm select "Mức hệ số" ngay sau khối `Loại ca` (sau dòng 41):
```jsx
        <label style={{ fontSize: 12.5 }}>Mức hệ số
          <select className="sel" value={form.otLevel}
            onChange={(e) => setForm({ ...form, otLevel: e.target.value })}>
            <option value="100">100%</option>
            <option value="150">150%</option>
            <option value="300">300%</option>
          </select>
        </label>
```

- [ ] **Step 3: ShiftDrawer.jsx** — thay state `rate` (dòng 19) bằng `level`:

```jsx
  const [level, setLevel] = useState(shift.otLevel);
```

Trong `decide` (dòng 27-29), body duyệt đổi `rate: Number(rate)` thành `otLevel: level`:
```jsx
      const body = approve
        ? { start: start || null, end: end || null, shiftType: stype, otLevel: level, reviewNote: note }
        : { reviewNote: note };
```

Thay ô override `Hệ số` (dòng 87-89) bằng select:
```jsx
            <label style={{ fontSize: 12 }}>Mức hệ số
              <select className="sel" value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="100">100%</option>
                <option value="150">150%</option>
                <option value="300">300%</option>
              </select>
            </label>
```
(Giữ nguyên dòng hiển thị "Hệ số ×{shift.rate}" ở phần kv.)

- [ ] **Step 4: Build SPA, xác nhận sạch**

```bash
cd frontend && npm run build
```
Expected: build thành công, không lỗi; bundle ghi vào `custom-addons/hocba_hrm/static/spa`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/attendance.js frontend/src/features/attendance/ShiftForm.jsx frontend/src/features/attendance/ShiftDrawer.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(shift-ui): chọn/override mốc hệ số 100/150/300% + api OT (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: FE — MyHistory 2 thẻ tổng OT

**Files:**
- Modify: `frontend/src/features/attendance/MyHistory.jsx`

**Interfaces:**
- Consumes: `summary.otHours`, `summary.otCreditHours` (Task 4).

- [ ] **Step 1: MyHistory.jsx** — đổi lưới summary (dòng 44) sang 6 cột và thêm 2 thẻ:

```jsx
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(6,1fr)', marginBottom: 16 }}>
            <Sum val={data.summary.daysPresent} lbl="Ngày có mặt" />
            <Sum val={data.summary.totalCredit} lbl="Tổng công" />
            <Sum val={data.summary.deficitCredit} lbl="Công thiếu" col={data.summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
            <Sum val={data.summary.netCredit} lbl="Công thực" col="var(--green)" />
            <Sum val={data.summary.otHours} lbl="Giờ OT" />
            <Sum val={data.summary.otCreditHours} lbl="Giờ OT quy đổi" col="var(--green)" />
          </div>
```

- [ ] **Step 2: Build SPA, xác nhận sạch**

```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/attendance/MyHistory.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): MyHistory thêm 2 thẻ Giờ OT / Giờ OT quy đổi (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: FE — `OtTable.jsx` + tab "Chấm công OT" (manager)

**Files:**
- Create: `frontend/src/features/attendance/OtTable.jsx`
- Modify: `frontend/src/features/attendance/Attendance.jsx`

**Interfaces:**
- Consumes: `fetchOtTable(month)`, `setShiftLevel(id, otLevel)` (Task 7); `currentMonth`, `fmtTime` (util.js); `fmtDate` (utils/format); `LoadingState`/`ErrorState`/`EmptyState` (components/states).

- [ ] **Step 1: Tạo `OtTable.jsx`**:

```jsx
/* Bảng quản lý chấm công OT theo tháng (Gói 4C, manager). Liệt kê ca OT
   approved trong phạm vi; manager đổi mốc hệ số inline. */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchOtTable, setShiftLevel } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, currentMonth } from './util';

const LEVELS = ['100', '150', '300'];

export default function OtTable() {
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchOtTable(month).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month]);

  async function changeLevel(id, level) {
    setBusyId(id);
    try { await setShiftLevel(id, level); load(); }
    catch (e) { setErr(e.message); }
    finally { setBusyId(null); }
  }

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="between" style={{ marginBottom: 14 }}>
        <h3 style={{ margin: 0 }}>Chấm công OT</h3>
        <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải dữ liệu OT…" />}

      {data && (
        <>
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 16 }}>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1 }}>{data.totals.otHours}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Tổng giờ OT</div>
            </div>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: 'var(--green)' }}>{data.totals.otCreditHours}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Giờ OT quy đổi</div>
            </div>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1 }}>{data.totals.countedCount}/{data.totals.count}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Ca đã chấm / tổng</div>
            </div>
          </div>

          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Nhân viên</th><th>Phòng</th><th>Ngày</th><th>Giờ ca</th>
                <th className="tbl-num">Số giờ</th><th>Mức</th>
                <th className="tbl-num">Giờ quy đổi</th><th>Đã chấm</th>
              </tr></thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.id} style={{ opacity: r.counted ? 1 : 0.55 }}>
                    <td>{r.empName}<div className="muted" style={{ fontSize: 11 }}>{r.code}</div></td>
                    <td>{r.depName}</td>
                    <td className="mono">{fmtDate(r.date)}</td>
                    <td className="mono">{fmtTime(r.start)}–{fmtTime(r.end)}</td>
                    <td className="tbl-num mono">{r.hours}</td>
                    <td>
                      {data.canManage ? (
                        <select className="sel" value={r.otLevel} disabled={busyId === r.id}
                          onChange={(e) => changeLevel(r.id, e.target.value)}>
                          {LEVELS.map((l) => <option key={l} value={l}>{l}%</option>)}
                        </select>
                      ) : `${r.otLevel}%`}
                    </td>
                    <td className="tbl-num mono" style={{ fontWeight: 600, color: r.counted ? 'var(--green)' : undefined }}>{r.creditHours}</td>
                    <td>{r.counted ? <Badge kind="green" dot>Đã chấm</Badge> : <Badge kind="gray">Chưa</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.rows.length === 0 && <EmptyState>Không có ca OT đã duyệt trong tháng này.</EmptyState>}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Attendance.jsx** — thêm import (cạnh import ShiftCalendar, dòng 9):

```jsx
import OtTable from './OtTable';
```

Thêm tab vào nhánh manager (dòng 37-39):
```jsx
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Ca làm việc (CTV/OT)'], ['otpay', 'Chấm công OT']]
    : [['me', 'Chấm công của tôi'], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
```

Thêm render (sau dòng 82 `{activeTab === 'ot' && ...}`):
```jsx
      {activeTab === 'otpay' && <OtTable />}
```

- [ ] **Step 3: Build SPA, xác nhận sạch**

```bash
cd frontend && npm run build
```
Expected: build thành công.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/OtTable.jsx frontend/src/features/attendance/Attendance.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(ot-ui): tab Chấm công OT + bảng OT tháng cho manager (Gói 4C)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Hồi quy + cập nhật handoff

**Files:**
- Modify: `docs/superpowers/HANDOFF-attendance-upgrade.md`

- [ ] **Step 1: Chạy full suite cả 2 module, xác nhận xanh**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: cả 2 đều `0 failed, 0 error(s) of N tests`, N>0.

- [ ] **Step 2: Cập nhật bảng trạng thái + ghi chú** trong `HANDOFF-attendance-upgrade.md`: đánh dấu Gói 4B `✅ XONG (đã merge main, đã sửa needs_review)`, Gói 4C `✅ XONG` với tóm tắt; ghi rõ **migration caveat** (ca cũ rate về 1.0 theo ot_level mặc định) và kiểm thử thủ công SPA còn lại.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/HANDOFF-attendance-upgrade.md
git commit -m "docs(attendance): Gói 4C hoàn tất + sửa nốt 4B (handoff)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review (đã chạy)

**Spec coverage:** A→Task 2 ✅; B→Task 1 ✅; C→Task 3 (otLevel) + Task 4 (`_att_me_history`, `_ot_row`/`_ot_for_employee`) + Task 5 (`_ot_table`) + Task 6 (`_shift_set_level`) ✅; D→Task 7/8/9 ✅; E→test rải Task 1-6 ✅. Cập nhật test cũ phụ thuộc auto-rate: Task 3 ✅.

**Placeholder scan:** không có TBD/TODO; mọi step có code/lệnh cụ thể.

**Type consistency:** `ot_level` (str '100'/'150'/'300'), `rate` (float), `_OT_RATE` map — nhất quán Task 1→6. `_ot_row` keys (`hours/counted/creditHours/otLevel`) khớp giữa Task 4/5 và FE Task 9. `otHours/otCreditHours` khớp Task 4 (summary) ↔ Task 8 (FE). Route `otLevel` body khớp Task 6 ↔ Task 7 `setShiftLevel`.
