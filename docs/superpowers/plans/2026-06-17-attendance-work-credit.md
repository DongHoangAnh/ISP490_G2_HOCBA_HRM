# Gói 1 — Tính công + phút trễ/về sớm/thiếu — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm tính "công" theo ngày (sáng/chiều), phút đi trễ / về sớm / thiếu trên mỗi bản ghi chấm công, và tổng hợp công tháng (trừ công thiếu, bỏ 2 ngày vi phạm đầu) — hiển thị trên các bảng lịch sử của SPA.

**Architecture:** Field tính sẵn (`compute` + `store`) trên `hocba.attendance`, đọc cấu hình từ `hocba.attendance.policy`. Tổng hợp tháng (tính chéo nhiều bản ghi) làm ở controller `hocba_hrm`. Frontend chỉ đọc thêm field từ JSON và render cột/thẻ mới.

**Tech Stack:** Odoo 19 (Python), test `odoo.tests.common.TransactionCase`; React (Vite) cho SPA `frontend/`.

**Spec:** [docs/superpowers/specs/2026-06-17-attendance-work-credit-design.md](../specs/2026-06-17-attendance-work-credit-design.md)

---

## File Structure

- `custom-addons/hocba_attendance/models/hocba_attendance_policy.py` — **Modify**: thêm 5 field cấu hình tính công.
- `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml` — **Modify**: hiện 5 field mới trên form.
- `custom-addons/hocba_attendance/models/hr_attendance.py` — **Modify**: thêm 7 field tính công + 1 compute; sửa `_compute_status` dùng `late_cutoff`.
- `custom-addons/hocba_attendance/tests/test_work_credit.py` — **Create**: test field tính công.
- `custom-addons/hocba_attendance/tests/test_status.py` — **Modify**: cập nhật mốc trễ 9:30.
- `custom-addons/hocba_hrm/controllers/main.py` — **Modify**: `_att_row` thêm field; bỏ `_late_minutes`; `_att_me_history` thêm tổng hợp công; `_att_day_table` thêm `counts.totalCredit`.
- `custom-addons/hocba_hrm/tests/test_attendance_api.py` — **Modify**: test tổng hợp công tháng.
- `frontend/src/features/attendance/util.js` — **Modify**: helper `fmtCredit`.
- `frontend/src/features/attendance/MyHistory.jsx` — **Modify**: thẻ + cột công.
- `frontend/src/features/attendance/AttendanceDrawer.jsx` — **Modify**: dòng chi tiết công.
- `frontend/src/features/attendance/AttendanceTable.jsx` — **Modify**: cột công.

**Lệnh chạy test backend** (Windows Git Bash — theo memory `running-odoo-tests`; `MSYS_NO_PATHCONV=1` bắt buộc, xác nhận số test in ra khác 0):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance \
  --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
```

Cho test controller `hocba_hrm` đổi `-u hocba_attendance` → `-u hocba_hrm` và `--test-tags /hocba_hrm` (lần đầu dùng `-i hocba_hrm` nếu chưa cài).

---

## Task 1: Thêm field cấu hình vào `hocba.attendance.policy`

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_attendance_policy.py:35` (sau `face_threshold`)
- Modify: `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml:38`
- Test: `custom-addons/hocba_attendance/tests/test_work_credit.py` (tạo ở bước này)

- [ ] **Step 1: Viết test thất bại — policy có field cấu hình mới với default đúng**

Tạo file `custom-addons/hocba_attendance/tests/test_work_credit.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestWorkCreditPolicy(TransactionCase):

    def test_policy_credit_defaults(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        self.assertEqual(policy.late_cutoff, 9.5)
        self.assertEqual(policy.morning_credit_cutoff, 10.0)
        self.assertEqual(policy.std_work_hours, 8.0)
        self.assertEqual(policy.afternoon_margin_hours, 2.0)
        self.assertEqual(policy.violation_free_days, 2)
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError`/`Invalid field 'late_cutoff'` (field chưa tồn tại).

- [ ] **Step 3: Thêm field vào model**

Trong `hocba_attendance_policy.py`, ngay sau dòng `face_threshold = fields.Float(...)` (dòng 35), thêm:

```python
    # --- Tính công (Gói 1): mốc trễ + công sáng/chiều + công thiếu ---
    late_cutoff = fields.Float(
        string='Mốc đi trễ (giờ)', default=9.5,
        help='Check-in sau giờ này (9.5 = 09:30) tính là đi trễ.')
    morning_credit_cutoff = fields.Float(
        string='Hạn công sáng (giờ)', default=10.0,
        help='Check-in sau giờ này mất công sáng (½ công).')
    std_work_hours = fields.Float(
        string='Giờ làm chuẩn/ngày', default=8.0,
        help='Mốc giờ ra mong đợi = check-in + số giờ này.')
    afternoon_margin_hours = fields.Float(
        string='Biên về sớm mất công chiều (giờ)', default=2.0,
        help='Check-out sớm hơn (giờ chuẩn − biên này) so mốc vào → mất công chiều.')
    violation_free_days = fields.Integer(
        string='Số ngày vi phạm miễn trừ/tháng', default=2,
        help='Số ngày vi phạm đầu tháng không tính vào công thiếu.')
```

- [ ] **Step 4: Hiện field mới trên form policy**

Trong `hocba_attendance_policy_views.xml`, sau group "Nhận diện khuôn mặt" (dòng 38-40), thêm group mới trước `</sheet>`:

```xml
                        <group string="Tính công">
                            <field name="late_cutoff"/>
                            <field name="morning_credit_cutoff"/>
                            <field name="std_work_hours"/>
                            <field name="afternoon_margin_hours"/>
                            <field name="violation_free_days"/>
                        </group>
```

- [ ] **Step 5: Chạy test để xác nhận PASS**

Run: (lệnh như Step 2)
Expected: PASS — `TestWorkCreditPolicy.test_policy_credit_defaults` xanh; tổng `0 failed, 0 error(s) of N tests` với N > 0.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance/models/hocba_attendance_policy.py custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml custom-addons/hocba_attendance/tests/test_work_credit.py
git commit -m "feat(attendance): thêm field cấu hình tính công vào policy"
```

---

## Task 2: Field tính công trên `hocba.attendance` + sửa mốc trễ

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py` (import, fields, compute, `_compute_status`)
- Test: `custom-addons/hocba_attendance/tests/test_work_credit.py` (thêm class)
- Modify: `custom-addons/hocba_attendance/tests/test_status.py` (mốc 9:30)

- [ ] **Step 1: Viết test thất bại cho field tính công**

Thêm vào cuối `custom-addons/hocba_attendance/tests/test_work_credit.py`:

```python
@tagged('post_install', '-at_install')
class TestWorkCreditFields(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'late_cutoff': 9.5, 'morning_credit_cutoff': 10.0,
            'std_work_hours': 8.0, 'afternoon_margin_hours': 2.0,
            'violation_free_days': 2,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Cong',
            'x_employment_status': 'official',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
        })

    def _rec(self, check_in, check_out=None):
        # Giờ truyền vào là UTC (chuỗi). tz context = Asia/Ho_Chi_Minh (+07).
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        vals = {'employee_id': self.emp.id, 'check_in': check_in}
        if check_out:
            vals['check_out'] = check_out
        return Att.create(vals)

    def test_full_day_one_credit(self):
        # 09:00–17:00 local = 02:00–10:00 UTC, đủ 8h
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 10:00:00')
        self.assertEqual(rec.work_credit, 1.0)
        self.assertEqual(rec.late_minutes, 0)
        self.assertEqual(rec.missing_minutes, 0)
        self.assertEqual(rec.early_leave_minutes, 0)
        self.assertEqual(rec.morning_credit, 0.5)
        self.assertEqual(rec.afternoon_credit, 0.5)

    def test_late_but_keeps_morning_credit(self):
        # check-in 09:45 local = 02:45 UTC -> trễ 15', vẫn trước 10:00
        rec = self._rec('2026-06-17 02:45:00', '2026-06-17 10:45:00')
        self.assertEqual(rec.late_minutes, 15)
        self.assertEqual(rec.morning_credit, 0.5)

    def test_after_ten_loses_morning_credit(self):
        # check-in 10:30 local = 03:30 UTC
        rec = self._rec('2026-06-17 03:30:00', '2026-06-17 11:30:00')
        self.assertEqual(rec.morning_credit, 0.0)
        self.assertEqual(rec.late_minutes, 60)
        self.assertEqual(rec.work_credit, 0.5)

    def test_early_checkout_loses_afternoon_credit(self):
        # 09:00 in (02:00 UTC), 14:00 out (07:00 UTC) = chỉ 5h, < check_in+6h
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 07:00:00')
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.missing_minutes, 180)
        self.assertEqual(rec.early_leave_minutes, 180)

    def test_no_checkout_no_missing(self):
        rec = self._rec('2026-06-17 02:00:00')
        self.assertEqual(rec.missing_minutes, 0)
        self.assertEqual(rec.early_leave_minutes, 0)
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.work_credit, 0.5)  # chỉ có công sáng
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run: (lệnh test `/hocba_attendance` như Task 1 Step 2)
Expected: FAIL — `Invalid field 'work_credit'` (field chưa tồn tại).

- [ ] **Step 3: Thêm import `timedelta`**

Trong `hr_attendance.py`, sửa dòng đầu `import json`/`import math` thành (thêm import datetime):

```python
import json
import math
from datetime import timedelta
```

- [ ] **Step 4: Khai báo 7 field tính công**

Trong `hr_attendance.py`, ngay sau field `working_hours = fields.Float(...)` (kết thúc dòng 61) và trước `active = fields.Boolean(...)` (dòng 62), thêm:

```python
    expected_check_out = fields.Datetime(
        string='Giờ ra mong đợi',
        compute='_compute_work_metrics', store=True)
    late_minutes = fields.Integer(
        string='Phút đi trễ',
        compute='_compute_work_metrics', store=True)
    early_leave_minutes = fields.Integer(
        string='Phút về sớm',
        compute='_compute_work_metrics', store=True)
    missing_minutes = fields.Integer(
        string='Phút thiếu',
        compute='_compute_work_metrics', store=True)
    morning_credit = fields.Float(
        string='Công sáng',
        compute='_compute_work_metrics', store=True)
    afternoon_credit = fields.Float(
        string='Công chiều',
        compute='_compute_work_metrics', store=True)
    work_credit = fields.Float(
        string='Công ngày',
        compute='_compute_work_metrics', store=True,
        help='0 / 0.5 / 1.0 = công sáng + công chiều.')
```

- [ ] **Step 5: Viết compute `_compute_work_metrics`**

Trong `hr_attendance.py`, ngay sau method `_compute_working_hours` (kết thúc dòng 102), thêm:

```python
    @api.depends('check_in', 'check_out')
    def _compute_work_metrics(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        std = policy.std_work_hours or 8.0
        late_cut = policy.late_cutoff or 9.5
        morn_cut = policy.morning_credit_cutoff or 10.0
        aft_margin = policy.afternoon_margin_hours or 2.0
        for rec in self:
            ci, co = rec.check_in, rec.check_out
            rec.expected_check_out = (ci + timedelta(hours=std)) if ci else False
            if ci:
                local_in = fields.Datetime.context_timestamp(rec, ci)
                in_hour = (local_in.hour + local_in.minute / 60.0
                           + local_in.second / 3600.0)
                rec.late_minutes = max(0, int(round((in_hour - late_cut) * 60)))
                rec.morning_credit = 0.5 if in_hour <= morn_cut else 0.0
            else:
                rec.late_minutes = 0
                rec.morning_credit = 0.0
            if ci and co:
                worked_min = (co - ci).total_seconds() / 60.0
                rec.missing_minutes = max(0, int(round(std * 60 - worked_min)))
                expected = ci + timedelta(hours=std)
                rec.early_leave_minutes = max(
                    0, int(round((expected - co).total_seconds() / 60.0)))
                aft_threshold = ci + timedelta(hours=std - aft_margin)
                rec.afternoon_credit = 0.5 if co >= aft_threshold else 0.0
            else:
                rec.missing_minutes = 0
                rec.early_leave_minutes = 0
                rec.afternoon_credit = 0.0
            rec.work_credit = rec.morning_credit + rec.afternoon_credit
```

- [ ] **Step 6: Sửa `_compute_status` dùng `late_cutoff`**

Trong `hr_attendance.py`, trong method `_compute_status`, đổi dòng:

```python
        cutoff = policy.morning_start
```
thành:
```python
        cutoff = policy.late_cutoff
```

- [ ] **Step 7: Cập nhật `test_status.py` cho mốc 9:30**

Trong `custom-addons/hocba_attendance/tests/test_status.py`:

Trong `setUp`, đổi dòng `self.policy.write({'morning_start': 8.0, 'morning_end': 9.5})` thành:
```python
        self.policy.write({'morning_start': 8.0, 'morning_end': 9.5,
                           'late_cutoff': 9.5})
```

Đổi `test_checkin_before_cutoff_is_on_time` — dùng 09:20 local (02:20 UTC) cho rõ là trước 9:30:
```python
    def test_checkin_before_cutoff_is_on_time(self):
        """Status dùng LOCAL time. 02:20 UTC = 09:20 +07 -> trước 09:30 -> on_time."""
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({
            'employee_id': self.employee.id,
            'check_in': '2026-06-11 02:20:00',  # 09:20 local, trước 09:30
        })
        self.assertEqual(rec.status_code, 'on_time')
```

Đổi `test_checkin_after_cutoff_is_late` — dùng 09:40 local (02:40 UTC):
```python
    def test_checkin_after_cutoff_is_late(self):
        """02:40 UTC = 09:40 +07 -> sau mốc 09:30 -> late."""
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        rec = Att.create({
            'employee_id': self.employee.id,
            'check_in': '2026-06-11 02:40:00',  # 09:40 local, sau 09:30
        })
        self.assertEqual(rec.status_code, 'late')
```

- [ ] **Step 8: Chạy test để xác nhận PASS**

Run: (lệnh test `/hocba_attendance` như Task 1 Step 2)
Expected: PASS — `TestWorkCreditFields` (5 test) + `TestAttendanceStatus` (đã sửa) xanh; `0 failed, 0 error(s)`.

- [ ] **Step 9: Commit**

```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py custom-addons/hocba_attendance/tests/test_work_credit.py custom-addons/hocba_attendance/tests/test_status.py
git commit -m "feat(attendance): field tính công + mốc trễ 9:30 trên hocba.attendance"
```

---

## Task 3: Mở rộng `_att_row` (wire thêm field công) trong controller

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (xóa `_late_minutes`, sửa `_att_row`)

- [ ] **Step 1: Xóa helper `_late_minutes` (không còn cần — dùng field store)**

Trong `main.py`, xóa toàn bộ hàm `_late_minutes` (dòng ~126-132):

```python
def _late_minutes(rec, policy):
    """Số phút đi muộn so với morning_start; 0 nếu đúng giờ."""
    if not rec.check_in or rec.status_code != 'late':
        return 0
    local = fields.Datetime.context_timestamp(rec, rec.check_in)
    hour = local.hour + local.minute / 60.0
    return max(0, int(round((hour - policy.morning_start) * 60)))
```

- [ ] **Step 2: Thêm field công vào `_att_row`**

Trong `main.py`, trong `_att_row`, đổi dòng:
```python
        'lateMinutes': _late_minutes(rec, policy),
```
thành:
```python
        'lateMinutes': rec.late_minutes,
        'earlyLeaveMinutes': rec.early_leave_minutes,
        'missingMinutes': rec.missing_minutes,
        'workCredit': rec.work_credit,
        'morningCredit': rec.morning_credit,
        'afternoonCredit': rec.afternoon_credit,
        'expectedCheckOut': _dt_local(rec, rec.expected_check_out),
```

(`_att_row` vẫn nhận tham số `policy` — giữ chữ ký, các caller không đổi.)

- [ ] **Step 3: Chạy test hiện có của controller để xác nhận không vỡ**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: PASS — bộ test `TestAttendanceApi` cũ vẫn xanh (lần đầu nếu `of 0 tests` thì cài `-i hocba_hrm` rồi chạy lại).

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(attendance-api): wire field tính công vào _att_row"
```

---

## Task 4: Tổng hợp công tháng trong `_att_me_history` + `counts.totalCredit`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (`_att_me_history`, `_att_day_table`)
- Test: `custom-addons/hocba_hrm/tests/test_attendance_api.py` (thêm test)

- [ ] **Step 1: Viết test thất bại cho tổng hợp công tháng**

Thêm vào cuối class `TestAttendanceApi` trong `custom-addons/hocba_hrm/tests/test_attendance_api.py`:

```python
    def test_history_credit_summary(self):
        # 4 ngày, mỗi ngày làm 6h (thiếu 120') -> 4 ngày vi phạm.
        # Bỏ 2 ngày đầu -> còn 2 ngày * 120' = 240' = 4h -> /8 = 0.5 công thiếu.
        # Mỗi ngày check-out đúng check_in+6h nên vẫn đủ công chiều -> work_credit=1.
        emp2 = self.env['hr.employee'].create({
            'name': 'NV Credit', 'x_employment_status': 'official',
            'x_pit_code': '5556667778', 'x_social_insurance_no': '4443332221',
        })
        u2 = self.env['res.users'].create({'name': 'U2', 'login': 'u2_credit'})
        emp2.user_id = u2
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        for day in (2, 3, 4, 5):
            Att.create({
                'employee_id': emp2.id,
                'check_in': '2026-06-%02d 02:00:00' % day,   # 09:00 local
                'check_out': '2026-06-%02d 08:00:00' % day,  # 15:00 local = 6h
            })
        data = _att_me_history(self.env(user=u2), '2026-06')
        s = data['summary']
        self.assertEqual(s['violationDays'], 4)
        self.assertEqual(s['totalCredit'], 4.0)
        self.assertEqual(s['deficitCredit'], 0.5)
        self.assertEqual(s['netCredit'], 3.5)

    def test_history_credit_under_free_days(self):
        # Chỉ 2 ngày vi phạm -> bỏ hết -> deficit 0.
        emp3 = self.env['hr.employee'].create({
            'name': 'NV Credit3', 'x_employment_status': 'official',
            'x_pit_code': '1212121212', 'x_social_insurance_no': '3434343434',
        })
        u3 = self.env['res.users'].create({'name': 'U3', 'login': 'u3_credit'})
        emp3.user_id = u3
        Att = self.env['hocba.attendance'].with_context(tz='Asia/Ho_Chi_Minh')
        for day in (10, 11):
            Att.create({
                'employee_id': emp3.id,
                'check_in': '2026-06-%02d 02:00:00' % day,
                'check_out': '2026-06-%02d 08:00:00' % day,
            })
        data = _att_me_history(self.env(user=u3), '2026-06')
        self.assertEqual(data['summary']['violationDays'], 2)
        self.assertEqual(data['summary']['deficitCredit'], 0.0)
```

- [ ] **Step 2: Chạy test để xác nhận FAIL**

Run: (lệnh `/hocba_hrm` như Task 3 Step 3)
Expected: FAIL — `KeyError: 'violationDays'` (summary chưa có key).

- [ ] **Step 3: Thêm tổng hợp công vào `_att_me_history`**

Trong `main.py`, trong `_att_me_history`, sau khi tạo `rows` và trước `summary = {...}`, thêm logic; rồi bổ sung key vào dict `summary`. Đổi block:

```python
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

thành:

```python
    rows = [_att_row(r, policy) for r in recs]
    total_credit = sum(r['workCredit'] for r in rows)
    violations = sorted(
        [r for r in rows if r['missingMinutes'] > 0], key=lambda r: r['date'])
    counted = violations[policy.violation_free_days:]
    std = policy.std_work_hours or 8.0
    deficit_credit = round(
        (sum(r['missingMinutes'] for r in counted) / 60.0) / std, 2)
    summary = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'daysPresent': len(rows),
        'totalHours': round(sum(r['workingHours'] for r in rows), 2),
        'totalCredit': round(total_credit, 2),
        'deficitCredit': deficit_credit,
        'netCredit': round(total_credit - deficit_credit, 2),
        'violationDays': len(violations),
    }
    return {'month': '%04d-%02d' % (y, m), 'summary': summary, 'rows': rows}
```

- [ ] **Step 4: Thêm `counts.totalCredit` vào `_att_day_table`**

Trong `main.py`, trong `_att_day_table`, trong dict `counts = {...}`, thêm key `totalCredit` (tính sau khi có `rows`). Đổi:

```python
    counts = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'missing': 0,
    }
```
thành:
```python
    counts = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'missing': 0,
        'totalCredit': round(sum(r['workCredit'] for r in rows), 2),
    }
```

- [ ] **Step 5: Chạy test để xác nhận PASS**

Run: (lệnh `/hocba_hrm` như Task 3 Step 3)
Expected: PASS — `test_history_credit_summary` + `test_history_credit_under_free_days` xanh; `0 failed, 0 error(s)`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_attendance_api.py
git commit -m "feat(attendance-api): tổng hợp công tháng (totalCredit/deficitCredit/netCredit)"
```

---

## Task 5: Helper `fmtCredit` (frontend)

**Files:**
- Modify: `frontend/src/features/attendance/util.js`

- [ ] **Step 1: Thêm helper `fmtCredit`**

Cuối `util.js`, thêm:

```javascript
/* Công ngày: 1.0 -> '1 công', 0.5 -> '½ công', 0/null -> '—'. */
export function fmtCredit(v) {
  if (v >= 1) return '1 công';
  if (v >= 0.5) return '½ công';
  return '—';
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/attendance/util.js
git commit -m "feat(attendance-ui): helper fmtCredit"
```

---

## Task 6: Thẻ + cột công trong `MyHistory.jsx`

**Files:**
- Modify: `frontend/src/features/attendance/MyHistory.jsx`

- [ ] **Step 1: Import `fmtCredit`**

Đổi dòng import util:
```javascript
import { fmtTime, attStatus, currentMonth } from './util';
```
thành:
```javascript
import { fmtTime, attStatus, currentMonth, fmtCredit } from './util';
```

- [ ] **Step 2: Thêm 3 thẻ tổng hợp công**

Trong khối `stat-grid`, đổi `gridTemplateColumns: 'repeat(5,1fr)'` thành `'repeat(4,1fr)'` và thay 5 thẻ hiện tại bằng cụm dưới (gom: bỏ "Cần xem lại" khỏi hàng chính, ưu tiên công):

```jsx
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
            <Sum val={data.summary.daysPresent} lbl="Ngày có mặt" />
            <Sum val={data.summary.totalCredit} lbl="Tổng công" />
            <Sum val={data.summary.deficitCredit} lbl="Công thiếu" col={data.summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
            <Sum val={data.summary.netCredit} lbl="Công thực" col="var(--green)" />
          </div>
```

- [ ] **Step 3: Thêm cột Ngày công / Về sớm / Thiếu vào bảng**

Đổi `<thead>`:
```jsx
              <thead><tr>
                <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th>
                <th className="tbl-num">Về sớm</th><th className="tbl-num">Thiếu</th>
                <th className="tbl-num">Ngày công</th><th>Trạng thái</th><th></th>
              </tr></thead>
```

Trong `<tbody>`, sau ô "Đi trễ" (`<td className="tbl-num mono">{r.lateMinutes...}</td>`), thêm 3 ô trước ô Trạng thái:
```jsx
                      <td className="tbl-num mono">{r.earlyLeaveMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>-{r.earlyLeaveMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono">{r.missingMinutes > 0 ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono" style={{ fontWeight: 600 }}>{fmtCredit(r.workCredit)}</td>
```

- [ ] **Step 4: Build & kiểm tra trực quan**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công (không lỗi). Mở `/hocba-hrm` đăng nhập user thường → tab "Chấm công của tôi" → bảng lịch sử có cột Về sớm/Thiếu/Ngày công, 3 thẻ Tổng công/Công thiếu/Công thực hiển thị số.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/attendance/MyHistory.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): cột & thẻ công trong MyHistory"
```

---

## Task 7: Chi tiết công trong `AttendanceDrawer.jsx`

**Files:**
- Modify: `frontend/src/features/attendance/AttendanceDrawer.jsx`

- [ ] **Step 1: Import `fmtCredit`**

Đổi:
```javascript
import { fmtTime, attStatus } from './util';
```
thành:
```javascript
import { fmtTime, attStatus, fmtCredit } from './util';
```

- [ ] **Step 2: Thêm 4 ô chi tiết**

Trong `<div className="grid-2" ...>`, sau ô "Giờ công" (`<div className="kv"><div className="k">Giờ công</div>...</div>`), thêm:

```jsx
          <div className="kv"><div className="k">Ngày công</div><div className="v mono" style={{ fontWeight: 600 }}>{fmtCredit(rec.workCredit)}</div></div>
          <div className="kv"><div className="k">Giờ ra mong đợi</div><div className="v mono">{fmtTime(rec.expectedCheckOut)}</div></div>
          <div className="kv"><div className="k">Về sớm</div><div className="v mono">{rec.earlyLeaveMinutes > 0 ? `${rec.earlyLeaveMinutes}'` : '—'}</div></div>
          <div className="kv"><div className="k">Phút thiếu</div><div className="v mono">{rec.missingMinutes > 0 ? `${rec.missingMinutes}'` : '—'}</div></div>
```

- [ ] **Step 3: Build & kiểm tra trực quan**

Run: `cd frontend && npm run build`
Expected: build OK; click 1 dòng lịch sử → drawer hiện Ngày công, Giờ ra mong đợi, Về sớm, Phút thiếu.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/AttendanceDrawer.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): chi tiết công trong AttendanceDrawer"
```

---

## Task 8: Cột công trong `AttendanceTable.jsx` (bảng theo ngày — manager)

**Files:**
- Modify: `frontend/src/features/attendance/AttendanceTable.jsx`

- [ ] **Step 1: Import `fmtCredit`**

Đổi:
```javascript
import { fmtTime, attStatus, today as todayStr } from './util';
```
thành:
```javascript
import { fmtTime, attStatus, today as todayStr, fmtCredit } from './util';
```

- [ ] **Step 2: Thêm cột Ngày công + Thiếu vào bảng**

Đổi `<thead>`:
```jsx
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Check-in</th><th>Check-out</th>
              <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th>
              <th className="tbl-num">Thiếu</th><th className="tbl-num">Ngày công</th>
              <th>Trạng thái</th><th></th>
            </tr></thead>
```

Trong `<tbody>`, sau ô "Đi trễ", thêm 2 ô trước ô Trạng thái:
```jsx
                    <td className="tbl-num mono">{r.missingMinutes > 0 ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span> : <span className="faint">—</span>}</td>
                    <td className="tbl-num mono" style={{ fontWeight: 600 }}>{fmtCredit(r.workCredit)}</td>
```

- [ ] **Step 3: Build & kiểm tra trực quan**

Run: `cd frontend && npm run build`
Expected: build OK; đăng nhập HR/manager → tab "Bảng chấm công" → có cột Thiếu + Ngày công.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/AttendanceTable.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(attendance-ui): cột công trong AttendanceTable"
```

---

## Task 9: Chạy toàn bộ test backend (xác nhận xanh end-to-end)

- [ ] **Step 1: Test module `hocba_attendance`**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests` với N > 0.

- [ ] **Step 2: Test module `hocba_hrm`**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests` với N > 0.

- [ ] **Step 3: Build frontend lần cuối**

Run: `cd frontend && npm run build`
Expected: build OK, không lỗi đỏ.

---

## Notes cho người thực thi

- **Giờ trong test là UTC**; tz context `Asia/Ho_Chi_Minh` (+07). Vd 09:00 local = 02:00 UTC.
- **Staleness**: đổi field policy KHÔNG tự tính lại bản ghi cũ (field store đọc policy lúc compute). Bản ghi mới luôn đúng. Nút "tính lại tháng" để Gói sau — không làm ở đây.
- **Không** đổi route API, không đổi logic face/geo/window.
- Nếu `npm run build` báo thiếu dependency, chạy `cd frontend && npm install` trước (theo docs/QUY_UOC_FRONTEND.md §8).
