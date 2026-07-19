# Tích hợp Nghỉ phép ↔ Chấm công (Task 1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Làm bảng chấm công phản ánh đúng nghỉ phép (chặn/sinh bản ghi/ghi công có–không lương) và nhận ngày làm bù `hb.work.day`, để Payroll đọc chấm công là ra công đúng.

**Architecture:** Toàn bộ logic đặt trong `hocba_timeoff` (đã `depends` `hocba_attendance`) bằng `_inherit` mở rộng `hocba.attendance.policy`, `hocba.attendance`, `hr.leave`. Ngoại lệ duy nhất chạm module attendance là badge trong `hr_attendance_views.xml` (đã được phép). Controller lỗi + thông báo FE nằm ở `hocba_hrm`/`frontend`.

**Tech Stack:** Odoo 19, Python, pytz; test `TransactionCase` tag `/hocba_timeoff`; SPA React (1 dòng map lỗi).

**Spec:** `docs/superpowers/specs/2026-07-13-timeoff-attendance-integration-design.md`

---

## Cấu trúc file

**Tạo mới (trong `custom-addons/hocba_timeoff/`):**
- `models/hocba_attendance_policy.py` — inherit `hocba.attendance.policy`, override `is_workday`.
- `models/hocba_attendance_leave.py` — inherit `hocba.attendance`: field mới + helper tra nghỉ + override `_assert_check_allowed`/`_assert_shift_check_allowed`/`_do_check`/`_compute_work_metrics`/`_compute_status` + `_generate_leave_attendance`/`_remove_leave_attendance`.
- `models/hr_leave_attendance_sync.py` — inherit `hr.leave`: override `_action_validate` (sinh), `action_refuse` (gỡ).
- `data/hocba_attendance_status_data.xml` — seed 2 trạng thái nghỉ.
- `tests/test_attendance_integration.py` — toàn bộ test.

**Sửa:**
- `custom-addons/hocba_timeoff/models/__init__.py` — import 3 file model mới.
- `custom-addons/hocba_timeoff/tests/__init__.py` — import test mới.
- `custom-addons/hocba_timeoff/__manifest__.py` — thêm data file, bump version → `19.0.15.0.0`.
- `custom-addons/hocba_hrm/controllers/main.py` — thêm `on_approved_leave` vào `_CHECK_ERR_STATUS`.
- `frontend/src/features/attendance/CheckInPanel.jsx` — thêm dòng message `on_approved_leave`.
- `custom-addons/hocba_attendance/views/hr_attendance_views.xml` — badge trạng thái nghỉ (đã được phép).

**Lệnh test dùng chung** (chạy từ repo root):
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```
Kết quả cần: `0 failed, 0 error(s) of N tests` với N tăng dần.

---

## Task 1: Nền móng — field mới + seed trạng thái + manifest

**Files:**
- Create: `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`
- Create: `custom-addons/hocba_timeoff/data/hocba_attendance_status_data.xml`
- Modify: `custom-addons/hocba_timeoff/models/__init__.py`
- Modify: `custom-addons/hocba_timeoff/__manifest__.py`
- Create/Modify test: `custom-addons/hocba_timeoff/tests/test_attendance_integration.py`, `tests/__init__.py`

- [ ] **Step 1: Viết test đỏ — field + trạng thái tồn tại**

Tạo `custom-addons/hocba_timeoff/tests/test_attendance_integration.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestAttendanceIntegrationBase(TransactionCase):

    def test_fields_and_statuses_exist(self):
        Att = self.env['hocba.attendance']
        for f in ('source', 'leave_id', 'leave_half', 'leave_is_paid'):
            self.assertIn(f, Att._fields, 'thiếu field %s' % f)
        Status = self.env['hocba.attendance.status']
        self.assertTrue(Status.search([('code', '=', 'on_leave_paid')]))
        self.assertTrue(Status.search([('code', '=', 'on_leave_unpaid')]))
```

Đăng ký test trong `custom-addons/hocba_timeoff/tests/__init__.py` (thêm dòng):
```python
from . import test_attendance_integration
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Chạy lệnh test dùng chung. Expected: FAIL (field/status chưa có).

- [ ] **Step 3: Tạo model field + computes rỗng (chưa logic nghỉ)**

Tạo `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`:

```python
# Task 1 — Tích hợp Nghỉ phép ↔ Chấm công. Mở rộng hocba.attendance:
#   - phân loại nguồn bản ghi (chấm công thật / sinh từ đơn nghỉ)
#   - chặn check-in ngày nghỉ cả ngày, sinh/gỡ bản ghi theo vòng đời đơn
#   - ép công + trạng thái cho ngày nghỉ (có/không lương)
import pytz
from datetime import datetime, time, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class HocbaAttendanceLeave(models.Model):
    _inherit = 'hocba.attendance'

    source = fields.Selection(
        [('checkin', 'Chấm công'), ('leave', 'Nghỉ phép')],
        string='Nguồn', default='checkin', required=True, index=True,
        help='checkin = NV chấm công thật; leave = bản ghi sinh từ đơn nghỉ cả ngày.')
    leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ', ondelete='set null', index=True)
    leave_half = fields.Selection(
        [('am', 'Sáng'), ('pm', 'Chiều')], string='Buổi nghỉ')
    leave_is_paid = fields.Boolean(
        string='Nghỉ có lương', help='Snapshot loại nghỉ có lương lúc sinh bản ghi.')
```

Thêm import vào `custom-addons/hocba_timeoff/models/__init__.py`:
```python
from . import hocba_attendance_leave
```

- [ ] **Step 4: Seed 2 trạng thái**

Tạo `custom-addons/hocba_timeoff/data/hocba_attendance_status_data.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="status_on_leave_paid" model="hocba.attendance.status">
            <field name="sequence">30</field>
            <field name="name">Nghỉ phép (có lương)</field>
            <field name="code">on_leave_paid</field>
            <field name="color_code">#17a2b8</field>
            <field name="description">Ngày nghỉ phép có lương — sinh từ đơn nghỉ đã duyệt.</field>
        </record>
        <record id="status_on_leave_unpaid" model="hocba.attendance.status">
            <field name="sequence">40</field>
            <field name="name">Nghỉ không lương</field>
            <field name="code">on_leave_unpaid</field>
            <field name="color_code">#6c757d</field>
            <field name="description">Ngày nghỉ không lương — sinh từ đơn nghỉ đã duyệt.</field>
        </record>
    </data>
</odoo>
```

Trong `custom-addons/hocba_timeoff/__manifest__.py`: bump `'version'` thành `'19.0.15.0.0'` và thêm vào list `'data'` (sau khối seed data khác):
```python
        'data/hocba_attendance_status_data.xml',
```

- [ ] **Step 5: Chạy test — xác nhận xanh**

Chạy lệnh test dùng chung. Expected: `test_fields_and_statuses_exist` PASS.

- [ ] **Step 6: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_leave.py \
  custom-addons/hocba_timeoff/models/__init__.py \
  custom-addons/hocba_timeoff/data/hocba_attendance_status_data.xml \
  custom-addons/hocba_timeoff/__manifest__.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py \
  custom-addons/hocba_timeoff/tests/__init__.py
git commit -m "feat(timeoff): field source/leave_id + seed trạng thái nghỉ cho chấm công (Task 1.1)"
```

---

## Task 2: `is_workday()` nhận ngày làm bù `hb.work.day`

**Files:**
- Create: `custom-addons/hocba_timeoff/models/hocba_attendance_policy.py`
- Modify: `custom-addons/hocba_timeoff/models/__init__.py`
- Test: `tests/test_attendance_integration.py`

- [ ] **Step 1: Viết test đỏ**

Thêm class vào `test_attendance_integration.py`:
```python
from datetime import date, datetime


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestIsWorkdayExtra(TransactionCase):

    def test_extra_workday_counts_as_workday(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        # 2026-07-18 là Thứ 7 (cuối tuần) -> mặc định không phải ngày làm
        sat = datetime(2026, 7, 18, 8, 0, 0)
        self.assertFalse(policy.is_workday(sat))
        self.env['hb.work.day'].create({'date': date(2026, 7, 18), 'name': 'Làm bù'})
        self.assertTrue(policy.is_workday(sat))
        # Thứ 7 khác chưa đánh dấu vẫn False
        self.assertFalse(policy.is_workday(datetime(2026, 7, 25, 8, 0, 0)))
```

- [ ] **Step 2: Chạy test — đỏ** (Expected: assertion thứ 2 FAIL vì chưa cộng hb.work.day).

- [ ] **Step 3: Override is_workday**

Tạo `custom-addons/hocba_timeoff/models/hocba_attendance_policy.py`:
```python
# Task 1 — Chấm công nhận thêm "ngày công ty đi làm bù" (hb.work.day) mà HR
# khai bên Nghỉ phép, ngoài 7 cờ workday_mon..sun sẵn có.
from odoo import models


class HocbaAttendancePolicy(models.Model):
    _inherit = 'hocba.attendance.policy'

    def is_workday(self, dt_local):
        if super().is_workday(dt_local):
            return True
        return bool(self.env['hb.work.day'].sudo().search_count(
            [('date', '=', dt_local.date())]))
```

Thêm vào `models/__init__.py` (TRƯỚC `hocba_attendance_leave` để rõ thứ tự, không bắt buộc):
```python
from . import hocba_attendance_policy
```

- [ ] **Step 4: Chạy test — xanh.**

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_policy.py \
  custom-addons/hocba_timeoff/models/__init__.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py
git commit -m "feat(timeoff): is_workday() cộng thêm hb.work.day (Task 1.2)"
```

---

## Task 3: Chặn check-in khi nghỉ CẢ NGÀY đã duyệt

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`
- Test: `tests/test_attendance_integration.py`

Thêm helper dựng dữ liệu vào đầu file test (dùng chung cho Task 3–6). Đặt trong một mixin:

```python
class _LeaveAttMixin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Att = cls.env['hocba.attendance']
        cls.Leave = cls.env['hr.leave']
        cls.annual = cls.env.ref('hocba_timeoff.hb_leave_type_annual')
        cls.unpaid = cls.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        cls.emp = cls.env['hr.employee'].create({
            'name': 'NV Tích Hợp', 'x_employment_status': 'official',
            'identification_id': '190000000001',
        })

    def _mk_leave(self, ltype, d_from, d_to, half=None, validate=True):
        vals = {
            'name': 'Nghỉ', 'employee_id': self.emp.id,
            'holiday_status_id': ltype.id,
            'request_date_from': d_from, 'request_date_to': d_to,
        }
        if half:
            vals.update({'request_unit_half': True,
                         'request_date_from_period': half,
                         'request_date_to_period': half})
        lv = self.Leave.sudo().create(vals)
        if validate:
            lv.sudo().action_approve()
        return lv
```

> Ghi chú BR-010: `identification_id` phải là 12 số, mỗi NV một giá trị (đổi số nếu trùng test khác).

- [ ] **Step 1: Viết test đỏ**
```python
from datetime import date
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestFullDayBlock(_LeaveAttMixin):

    def test_block_check_in_on_full_day_leave(self):
        today = fields.Date.context_today(self.Att)
        self._mk_leave(self.annual, today, today)
        with self.assertRaises(UserError) as ctx:
            self.Att._assert_check_allowed(self.emp, 'in')
        self.assertEqual(str(ctx.exception), 'on_approved_leave')

    def test_no_block_without_leave(self):
        # Không có đơn nghỉ -> không raise on_approved_leave (có thể raise
        # not_workday nếu hôm nay cuối tuần; test chỉ khẳng định KHÔNG phải mã nghỉ)
        try:
            self.Att._assert_check_allowed(self.emp, 'in')
        except UserError as ex:
            self.assertNotEqual(str(ex), 'on_approved_leave')
```

- [ ] **Step 2: Chạy test — đỏ.**

- [ ] **Step 3: Thêm helper + override assert**

Thêm vào class `HocbaAttendanceLeave` trong `hocba_attendance_leave.py`:
```python
    # ---- Tra đơn nghỉ ------------------------------------------------------
    def _leave_day_bounds(self, leave):
        d0 = leave.request_date_from or (leave.date_from and leave.date_from.date())
        d1 = leave.request_date_to or (leave.date_to and leave.date_to.date())
        return d0, d1

    def _leave_is_half_day(self, leave):
        """Nửa ngày = đơn 1 ngày, cùng buổi sáng/chiều. Đơn nhiều ngày -> cả ngày."""
        return bool(leave.request_unit_half
                    and leave.request_date_from_period
                    and leave.request_date_from_period == leave.request_date_to_period)

    def _approved_full_day_leave(self, employee, day):
        """Đơn nghỉ CẢ NGÀY đã duyệt phủ `day` (hoặc False)."""
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'validate')])
        for lv in leaves:
            d0, d1 = self._leave_day_bounds(lv)
            if d0 and d1 and d0 <= day <= d1 and not self._leave_is_half_day(lv):
                return lv
        return False

    def _assert_not_on_full_day_leave(self, employee):
        tz = employee.user_id.tz or self.env.user.tz or 'UTC'
        today = fields.Datetime.context_timestamp(
            self.with_context(tz=tz), fields.Datetime.now()).date()
        if self._approved_full_day_leave(employee, today):
            raise UserError('on_approved_leave')

    def _assert_check_allowed(self, employee, kind):
        self._assert_not_on_full_day_leave(employee)   # nghỉ trước, rồi luật cũ
        return super()._assert_check_allowed(employee, kind)

    def _assert_shift_check_allowed(self, employee, kind):
        self._assert_not_on_full_day_leave(employee)
        return super()._assert_shift_check_allowed(employee, kind)
```

> Kiểm nghỉ TRƯỚC super() để không bị super báo `already_checked_in` do bản ghi nghỉ tự sinh đã chiếm slot ngày.

- [ ] **Step 4: Chạy test — xanh.**

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_leave.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py
git commit -m "feat(timeoff): chặn check-in khi nghỉ cả ngày đã duyệt (Task 1.3)"
```

---

## Task 4: Sinh bản ghi chấm công khi duyệt nghỉ cả ngày + ép công/trạng thái

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`
- Create: `custom-addons/hocba_timeoff/models/hr_leave_attendance_sync.py`
- Modify: `custom-addons/hocba_timeoff/models/__init__.py`
- Test: `tests/test_attendance_integration.py`

- [ ] **Step 1: Viết test đỏ**
```python
@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestGenerateFullDay(_LeaveAttMixin):

    def _records_for(self, leave):
        return self.Att.sudo().search([('leave_id', '=', leave.id), ('source', '=', 'leave')])

    def test_generate_paid_full_day(self):
        d = date(2026, 7, 15)  # Thứ 4
        lv = self._mk_leave(self.annual, d, d)
        recs = self._records_for(lv)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs.work_credit, 1.0)
        self.assertTrue(recs.leave_is_paid)
        self.assertEqual(recs.status_id.code, 'on_leave_paid')
        self.assertEqual(recs.date, d)

    def test_generate_unpaid_full_day(self):
        d = date(2026, 7, 16)  # Thứ 5
        lv = self._mk_leave(self.unpaid, d, d)
        recs = self._records_for(lv)
        self.assertEqual(recs.work_credit, 0.0)
        self.assertFalse(recs.leave_is_paid)
        self.assertEqual(recs.status_id.code, 'on_leave_unpaid')

    def test_multiday_skips_weekend(self):
        # 2026-07-17 (T6) -> 2026-07-20 (T2): bỏ T7 18, CN 19
        lv = self._mk_leave(self.annual, date(2026, 7, 17), date(2026, 7, 20))
        days = self._records_for(lv).mapped('date')
        self.assertEqual(sorted(days), [date(2026, 7, 17), date(2026, 7, 20)])

    def test_retroactive_conflict_keeps_checkin(self):
        d = date(2026, 7, 22)  # Thứ 4
        # bản ghi chấm công thật có sẵn
        real = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 22, 1, 0, 0)})  # ~8h VN
        lv = self._mk_leave(self.annual, d, d)
        self.assertEqual(real.source, 'checkin')          # không bị ghi đè
        self.assertFalse(self._records_for(lv))           # không sinh thêm
        self.assertIn('rà soát', (real.notes or '').lower())
```

- [ ] **Step 2: Chạy test — đỏ.**

- [ ] **Step 3: Thêm sinh bản ghi + computes ép công/trạng thái**

Thêm vào class `HocbaAttendanceLeave`:
```python
    # ---- Sinh bản ghi cho nghỉ cả ngày ------------------------------------
    def _is_working_day(self, day, policy):
        dt = datetime.combine(day, time(0))
        return policy.is_workday(dt)

    def _leave_checkin_utc(self, employee, day, policy):
        """check_in quy ước = day tại morning_start (giờ local NV) -> UTC naive."""
        tz = pytz.timezone(employee.user_id.tz or self.env.user.tz or 'UTC')
        hours = policy.morning_start or 8.0
        local = tz.localize(datetime.combine(day, time(0)) + timedelta(hours=hours))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _generate_leave_attendance(self, leave):
        if self._leave_is_half_day(leave):
            return  # nửa ngày: bản ghi đến từ NV chấm công thật (Task 5)
        d0, d1 = self._leave_day_bounds(leave)
        if not d0 or not d1:
            return
        Att = self.env['hocba.attendance'].sudo()
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        is_paid = not leave.holiday_status_id.unpaid
        emp = leave.employee_id
        cur = d0
        while cur <= d1:
            if self._is_working_day(cur, policy):
                exist = Att.search([('employee_id', '=', emp.id), ('date', '=', cur)], limit=1)
                if exist:
                    if exist.source == 'checkin':
                        exist.write({'notes': (exist.notes or '')
                            + '\n[Cảnh báo] Có đơn nghỉ cả ngày đã duyệt trùng ngày đã chấm công — cần HR rà soát.'})
                else:
                    Att.create({
                        'employee_id': emp.id,
                        'check_in': self._leave_checkin_utc(emp, cur, policy),
                        'source': 'leave', 'leave_id': leave.id,
                        'leave_is_paid': is_paid,
                        'notes': leave.holiday_status_id.name,
                    })
            cur += timedelta(days=1)

    # ---- Ép công + trạng thái cho bản ghi nghỉ ----------------------------
    @api.depends('source', 'leave_id', 'leave_is_paid', 'leave_half')
    def _compute_work_metrics(self):
        super()._compute_work_metrics()
        for rec in self:
            if rec.source == 'leave':
                rec.late_minutes = 0
                rec.early_leave_minutes = 0
                rec.missing_minutes = 0
                rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.afternoon_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.work_credit = rec.morning_credit + rec.afternoon_credit
            elif rec.leave_id and rec.leave_half:      # nửa ngày, có chấm công thật
                if rec.leave_half == 'am':
                    rec.late_minutes = 0
                    rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                else:
                    rec.early_leave_minutes = 0
                    rec.missing_minutes = 0
                    rec.afternoon_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.work_credit = rec.morning_credit + rec.afternoon_credit

    @api.depends('source', 'leave_is_paid')
    def _compute_status(self):
        super()._compute_status()
        Status = self.env['hocba.attendance.status']
        paid = Status.search([('code', '=', 'on_leave_paid')], limit=1)
        unpaid = Status.search([('code', '=', 'on_leave_unpaid')], limit=1)
        for rec in self:
            if rec.source == 'leave':
                rec.status_id = paid if rec.leave_is_paid else unpaid
```

Tạo hook duyệt `custom-addons/hocba_timeoff/models/hr_leave_attendance_sync.py`:
```python
# Task 1 — Nối vòng đời đơn nghỉ với bảng chấm công:
#   duyệt (state -> validate) sinh bản ghi; từ chối/rút gỡ bản ghi.
from odoo import models


class HrLeaveAttendanceSync(models.Model):
    _inherit = 'hr.leave'

    def _action_validate(self):
        res = super()._action_validate()
        Att = self.env['hocba.attendance']
        for leave in self.filtered(lambda l: l.state == 'validate'):
            Att._generate_leave_attendance(leave)
        return res
```

Thêm vào `models/__init__.py`:
```python
from . import hr_leave_attendance_sync
```

- [ ] **Step 4: Chạy test — xanh.** (Nếu `_action_validate` không phải điểm vào khi `action_approve` một cấp, kiểm tra state sau approve; điều chỉnh hook sang override `action_approve` gọi super rồi sinh cho bản ghi `state=='validate'`.)

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_leave.py \
  custom-addons/hocba_timeoff/models/hr_leave_attendance_sync.py \
  custom-addons/hocba_timeoff/models/__init__.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py
git commit -m "feat(timeoff): sinh bản ghi chấm công + ép công/trạng thái khi duyệt nghỉ cả ngày (Task 1.4)"
```

---

## Task 5: Nghỉ nửa ngày — cho chấm công + note + bù công đúng buổi

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`
- Test: `tests/test_attendance_integration.py`

Cơ chế: khi NV check-in ngày có đơn **nửa ngày** đã duyệt, override `_do_check` gắn `leave_id`/`leave_half`/`leave_is_paid` + note vào bản ghi vừa tạo; `_compute_work_metrics` (Task 4) tự bù/miễn phạt.

- [ ] **Step 1: Viết test đỏ**
```python
@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestHalfDay(_LeaveAttMixin):

    def _checkin(self, when_utc):
        # tạo bản ghi qua _do_check để đi qua logic gắn nửa ngày
        return self.Att.sudo()._do_check({
            'employee_id': self.emp.id, 'photo': None, 'descriptor': [],
            'latitude': 0.0, 'longitude': 0.0}, 'in')

    def test_half_day_paid_note_and_credit(self):
        d = date(2026, 7, 15)
        self._mk_leave(self.annual, d, d, half='am')
        # giả lập NV chấm công buổi chiều ngày d (freeze time không có -> set check_in tay)
        rec = self.Att.sudo().create({'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 15, 7, 0, 0)})  # ~14h VN
        self.Att._stamp_half_day_leave(rec)   # helper idempotent, gọi trong _do_check
        self.assertEqual(rec.leave_half, 'am')
        self.assertIn('nửa buổi sáng', (rec.notes or '').lower())
        self.assertEqual(rec.work_credit, 1.0)
        self.assertEqual(rec.late_minutes, 0)

    def test_half_day_unpaid_credit(self):
        d = date(2026, 7, 16)
        self._mk_leave(self.unpaid, d, d, half='pm')
        rec = self.Att.sudo().create({'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 16, 1, 0, 0)})  # ~8h VN sáng
        self.Att._stamp_half_day_leave(rec)
        self.assertEqual(rec.leave_half, 'pm')
        self.assertEqual(rec.work_credit, 0.5)
```

- [ ] **Step 2: Chạy test — đỏ.**

- [ ] **Step 3: Thêm `_stamp_half_day_leave` + gọi trong `_do_check`**

Thêm vào class `HocbaAttendanceLeave`:
```python
    _HALF_LABEL = {'am': 'Nghỉ phép nửa buổi sáng', 'pm': 'Nghỉ phép nửa buổi chiều'}

    def _approved_half_day_leave(self, employee, day):
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'validate')])
        for lv in leaves:
            d0, d1 = self._leave_day_bounds(lv)
            if d0 and d1 and d0 <= day <= d1 and self._leave_is_half_day(lv):
                return lv
        return False

    def _stamp_half_day_leave(self, record):
        """Gắn thông tin nghỉ nửa ngày vào bản ghi chấm công thật (idempotent)."""
        if not record.date or record.source == 'leave':
            return
        lv = self._approved_half_day_leave(record.employee_id, record.date)
        if not lv:
            return
        half = lv.request_date_from_period
        note = self._HALF_LABEL.get(half, '')
        vals = {'leave_id': lv.id, 'leave_half': half,
                'leave_is_paid': not lv.holiday_status_id.unpaid}
        if note and note not in (record.notes or ''):
            vals['notes'] = ((record.notes + '\n') if record.notes else '') + note
        record.write(vals)

    def _do_check(self, payload, kind):
        res = super()._do_check(payload, kind)
        rec = self.browse(res['record_id'])
        rec._stamp_half_day_leave(rec)
        return res
```

- [ ] **Step 4: Chạy test — xanh.**

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_leave.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py
git commit -m "feat(timeoff): nghỉ nửa ngày — note + bù/miễn phạt công đúng buổi (Task 1.5)"
```

---

## Task 6: Đồng bộ ngược — từ chối/rút đơn thì gỡ bản ghi

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hocba_attendance_leave.py`
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_attendance_sync.py`
- Test: `tests/test_attendance_integration.py`

- [ ] **Step 1: Viết test đỏ**
```python
@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestReverseSync(_LeaveAttMixin):

    def _leave_recs(self, lv):
        return self.Att.sudo().search([('leave_id', '=', lv.id), ('source', '=', 'leave')])

    def test_refuse_removes_generated(self):
        d = date(2026, 7, 15)
        lv = self._mk_leave(self.annual, d, d)
        self.assertTrue(self._leave_recs(lv))
        lv.sudo().action_refuse()
        self.assertFalse(self._leave_recs(lv))

    def test_refuse_keeps_real_checkin_unlinks(self):
        d = date(2026, 7, 16)
        lv = self._mk_leave(self.annual, d, d, half='pm')
        real = self.Att.sudo().create({'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 16, 1, 0, 0)})
        self.Att._stamp_half_day_leave(real)
        self.assertEqual(real.leave_id, lv)
        lv.sudo().action_refuse()
        self.assertTrue(real.exists())            # công thật giữ nguyên
        self.assertFalse(real.leave_id)           # chỉ gỡ liên kết
        self.assertFalse(real.leave_half)
```

- [ ] **Step 2: Chạy test — đỏ.**

- [ ] **Step 3: Thêm `_remove_leave_attendance` + hook `action_refuse`**

Thêm vào class `HocbaAttendanceLeave`:
```python
    def _remove_leave_attendance(self, leave):
        recs = self.env['hocba.attendance'].sudo().search([('leave_id', '=', leave.id)])
        gen = recs.filtered(lambda r: r.source == 'leave')
        real = recs - gen
        gen.unlink()                              # bản ghi tự sinh -> xoá
        if real:
            real.write({'leave_id': False, 'leave_half': False,
                        'leave_is_paid': False})  # công thật -> gỡ liên kết + note
            for r in real:
                if r.notes:
                    for lab in self._HALF_LABEL.values():
                        r.notes = r.notes.replace(lab, '').strip('\n')
```

Thêm vào `HrLeaveAttendanceSync` (`hr_leave_attendance_sync.py`):
```python
    def action_refuse(self):
        res = super().action_refuse()
        Att = self.env['hocba.attendance']
        for leave in self:
            Att._remove_leave_attendance(leave)
        return res
```

- [ ] **Step 4: Chạy test — xanh.** (Luồng **rút đơn** Phase 7 gọi `action_refuse` → được phủ bởi cùng hook; nếu muốn test riêng, gọi qua controller rút, nhưng unit test action_refuse là đủ tương đương.)

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_timeoff/models/hocba_attendance_leave.py \
  custom-addons/hocba_timeoff/models/hr_leave_attendance_sync.py \
  custom-addons/hocba_timeoff/tests/test_attendance_integration.py
git commit -m "feat(timeoff): gỡ bản ghi chấm công khi từ chối/rút đơn nghỉ (Task 1.6)"
```

---

## Task 7: Controller lỗi + thông báo FE cho `on_approved_leave`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:1619`
- Modify: `frontend/src/features/attendance/CheckInPanel.jsx:51`

- [ ] **Step 1: Thêm mã lỗi vào `_CHECK_ERR_STATUS`**

Sửa dict tại [main.py:1619](../../custom-addons/hocba_hrm/controllers/main.py#L1619), thêm dòng:
```python
    'on_approved_leave': 403,
```

- [ ] **Step 2: Thêm message tiếng Việt ở SPA**

Trong `frontend/src/features/attendance/CheckInPanel.jsx`, thêm vào object `M` (sau dòng `outside_shift_window`):
```javascript
        on_approved_leave: 'Bạn đang trong kỳ nghỉ phép đã duyệt — không thể chấm công hôm nay.',
```

- [ ] **Step 3: Build SPA**

Run: `cd frontend && npm run build`
Expected: `✓ built`. (Hook tự build có thể đã chạy — vẫn build tay để chắc bundle cập nhật.)

- [ ] **Step 4: Kiểm chứng thủ công (preview)**

Với NV có đơn nghỉ cả ngày hôm nay: gọi `POST /hocba-hrm/api/attendance/check-in` → HTTP 403 body `{"error":"on_approved_leave"}`; SPA hiện đúng câu thông báo. (Xem verification cuối.)

- [ ] **Step 5: Commit**
```bash
git add custom-addons/hocba_hrm/controllers/main.py \
  frontend/src/features/attendance/CheckInPanel.jsx \
  custom-addons/hocba_hrm/static/spa
git commit -m "feat(hrm): map lỗi on_approved_leave (403) + thông báo SPA (Task 1.7)"
```

---

## Task 8: Badge trạng thái nghỉ trên view chấm công (đã được phép)

**Files:**
- Modify: `custom-addons/hocba_attendance/views/hr_attendance_views.xml`

- [ ] **Step 1: Xác định chỗ hiển thị status**

Mở `custom-addons/hocba_attendance/views/hr_attendance_views.xml`, tìm cột/field `status_id` (hoặc `status_code`) trong list/form. Ghi lại tên view + vị trí field.

- [ ] **Step 2: Thêm decoration badge theo status_code**

Với list view, đảm bảo hiển thị `status_id` dạng badge và thêm màu theo mã nghỉ. Ví dụ (điều chỉnh theo cấu trúc thật của file):
```xml
<field name="status_code" invisible="1"/>
<field name="status_id" widget="badge"
       decoration-info="status_code == 'on_leave_paid'"
       decoration-muted="status_code == 'on_leave_unpaid'"/>
```
Nếu form/list đã render `status_id` khác kiểu, chỉ bổ sung `decoration-*` cho 2 mã mới, giữ nguyên phần cũ.

- [ ] **Step 3: Upgrade + kiểm view**

Chạy `-u hocba_timeoff,hocba_attendance` (local) rồi mở view chấm công trong Odoo backend (hoặc SPA nếu có bảng) xác nhận dòng nghỉ có badge màu xanh (có lương) / xám (không lương).

- [ ] **Step 4: Commit**
```bash
git add custom-addons/hocba_attendance/views/hr_attendance_views.xml
git commit -m "feat(attendance): badge trạng thái nghỉ phép trên view chấm công (Task 1.8)"
```

---

## Task 9: Kiểm chứng cuối + upgrade

**Files:** (không sửa code; chạy & xác minh)

- [ ] **Step 1: Chạy toàn bộ test timeoff**

Chạy lệnh test dùng chung. Expected: `0 failed, 0 error(s) of N tests`, N gồm toàn bộ test cũ + ~11 test mới của Task 1.

- [ ] **Step 2: Upgrade local + smoke test luồng chấm công**

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```
Rồi `-u hocba_timeoff,hocba_attendance` để tạo cột + seed status. Preview `/hocba-hrm`, đăng nhập một NV official:
- Có đơn nghỉ cả ngày hôm nay → check-in bị chặn, hiện thông báo nghỉ phép.
- Không có đơn → check-in bình thường.

- [ ] **Step 3: (Neon) Ghi chú upgrade production**

Khi deploy Neon: `-u hocba_timeoff` qua **endpoint trực tiếp** (bỏ `-pooler`, `--entrypoint bash`) vì có DDL (cột mới) — theo memory [Neon direct upgrade]. Cập nhật `docs/DB_TEST_DATA.md` (nhật ký) sau khi upgrade.

- [ ] **Step 4: Review tổng thể**

Dispatch final code reviewer cho toàn bộ diff Task 1 (superpowers:requesting-code-review). Sửa các vấn đề Important nếu có, re-review.

- [ ] **Step 5: Dừng chờ user** — KHÔNG tự merge/push. Báo cáo kết quả, chờ user quyết commit/push/merge (theo memory no-auto-commit).

---

## Rủi ro & lưu ý

- **Điểm vào hook duyệt:** nếu `_action_validate` không phủ hết đường duyệt (VD approve một cấp), chuyển hook sang `action_approve` + lọc `state=='validate'`. Test Task 4 sẽ bắt lỗi này.
- **Timezone `check_in` quy ước:** phải qua pytz để `_compute_date` ra đúng ngày; test `test_generate_paid_full_day` khẳng định `recs.date == d`.
- **Override compute (`_compute_work_metrics`/`_compute_status`):** phải gọi `super()` trước rồi hiệu chỉnh; `@api.depends` bổ sung field nghỉ để recompute đúng khi đổi loại đơn.
- **`.sudo()`:** NV thường không có ACL trên `hr.leave`/`hocba.attendance` — mọi truy vấn/tạo/xoá trong hook + assert đã sudo sau khi ghim employee.
- **View Task 8:** cấu trúc `hr_attendance_views.xml` cần đọc thực tế; đoạn XML ví dụ chỉ minh hoạ decoration, phải khớp field/kiểu thật.
```
