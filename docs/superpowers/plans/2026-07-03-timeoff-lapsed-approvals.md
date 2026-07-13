# Đơn lỡ hạn duyệt (Phase 12) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **⚠️ Quy ước commit của repo này:** KHÔNG thêm `Co-Authored-By: Claude` vào commit message. Trước MỖI bước commit phải DỪNG và hỏi user xác nhận (quy ước cá nhân của owner — không tự commit).

**Goal:** Gắn cờ đơn nghỉ "lỡ hạn duyệt" (qua ngày bắt đầu nghỉ mà vẫn chờ duyệt), đối chiếu chấm công `hocba.attendance` các ngày nghỉ đã qua để gợi ý duyệt trễ / từ chối (nút 1-chạm), báo chuông người duyệt 1 lần, và màn "Giám sát duyệt đơn" cho HR/quản lý.

**Spec:** `docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md` (BR-L01→L06)

**Architecture:** Tính "sống" khi đọc (phương án A): cờ lỡ hạn + đối chiếu chấm công là helper cấp module trong `controllers/main.py` (pattern Phase 8 — helper nhận `env` để test gọi trực tiếp). DB chỉ thêm 1 field `x_lapsed_notified` chống báo chuông lặp. Cron hàng ngày chỉ bắn thông báo. SPA thêm badge/nút gợi ý ở tab Chờ duyệt + panel mới.

**Tech Stack:** Odoo 19 (custom-addons/hocba_timeoff, đã depends hocba_attendance), React 18/Vite 6 (frontend/, không TypeScript), test bằng Docker Postgres local.

**Lệnh test** (macOS, chạy từ `/Users/nguyenanh/odoo19`):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestTimeoffLapsed --stop-after-init --log-level=test
```

Kết quả PHẢI thấy `0 failed, 0 error(s) of N tests` với **N > 0** (N = 0 nghĩa là test không chạy — coi như FAIL). Chạy full module ở Task 8 thì bỏ `:TestTimeoffLapsed`.

**Bối cảnh code có sẵn cần biết:**

- `controllers/main.py` (2490 dòng): helper cấp module nhận `env` ở đầu file (`_scope_for`, `_dept_domain`, `_leave_day_bounds`, `_half_day_label`, `_count_working_days_env`, `_public_holiday_dates_env`, `_teaching_off_type_id`, `_approver_users`, `_push_notification`, `_leave_span_label`, `_d`, `PENDING_STATES`, `STATE_LABEL`); class `HocBaTimeoff` bên dưới là lớp mỏng gọi xuống.
- `hocba.attendance` (module hocba_attendance): field `employee_id`, `date` (Date, computed stored từ check_in theo tz user của NV), `work_credit` (0/0.5/1.0, computed stored). Công sáng 0.5 nếu giờ vào (local) ≤ 10.0; công chiều 0.5 nếu check_out ≥ check_in + 6h (std 8h − margin 2h).
- `hr.leave` nửa ngày: `request_unit_half` (Boolean).
- Thông báo chuông: model `hb.leave.notification`; mở rộng `kind` bằng `selection_add` + `ondelete` (xem `models/hr_leave_withdraw.py:30-45`).
- Cron: model `hb.timeoff.cron` (`models/hb_timeoff_cron.py`), XML pattern `data/ir_cron_reminder_data.xml`. Odoo 19: `ir.cron` KHÔNG còn field `numbercall`.
- Test convention: `TransactionCase` + `@tagged('post_install', '-at_install')`, import helper cấp module từ `controllers.main`, NV official phải có `identification_id` 12 chữ số khác nhau (BR-010) — xem `tests/test_notifications.py`.

---

## File Structure

| File | Việc |
|---|---|
| `custom-addons/hocba_timeoff/models/hr_leave_lapsed.py` | **Tạo** — field `x_lapsed_notified` trên hr.leave + kind `lapsed` cho notification |
| `custom-addons/hocba_timeoff/models/__init__.py` | Sửa — import file mới |
| `custom-addons/hocba_timeoff/controllers/main.py` | Sửa — helpers `_working_dates_env`, `_lapsed_info`, `_lapsed_summary_label`, `_lapsed_table`, `_post_lapsed_decision_note`; wire vào `_approval_request`, `api_request_decision`; endpoint `api_lapsed_dashboard` |
| `custom-addons/hocba_timeoff/models/hb_timeoff_cron.py` | Sửa — method `_cron_notify_lapsed_approvals` |
| `custom-addons/hocba_timeoff/data/ir_cron_lapsed_data.xml` | **Tạo** — record ir.cron hàng ngày |
| `custom-addons/hocba_timeoff/__manifest__.py` | Sửa — thêm data XML |
| `custom-addons/hocba_timeoff/tests/test_lapsed.py` | **Tạo** — toàn bộ test backend |
| `custom-addons/hocba_timeoff/tests/__init__.py` | Sửa — import test mới |
| `frontend/src/api/timeoff.js` | Sửa — `fetchLapsedDashboard` |
| `frontend/src/features/timeoff/ApprovalPanel.jsx` | Sửa — badge Lỡ hạn, box đối chiếu + nút gợi ý trong DecisionModal |
| `frontend/src/features/timeoff/LapsedPanel.jsx` | **Tạo** — màn "Giám sát duyệt đơn" |
| `frontend/src/features/timeoff/TimeOff.jsx` | Sửa — tab mới |
| `frontend/src/components/NotificationBell.jsx` | Sửa — màu chấm kind `lapsed` |

---

### Task 1: Model — field `x_lapsed_notified` + kind `lapsed`

**Files:**
- Create: `custom-addons/hocba_timeoff/models/hr_leave_lapsed.py`
- Modify: `custom-addons/hocba_timeoff/models/__init__.py`
- Test: `custom-addons/hocba_timeoff/tests/test_lapsed.py` (tạo mới, khung setUp dùng cho mọi task sau)

- [ ] **Step 1: Viết test khung + test field/kind (failing)**

Tạo `custom-addons/hocba_timeoff/tests/test_lapsed.py`:

```python
# ============================================================
# Test Phase 12 — Đơn lỡ hạn duyệt + đối chiếu chấm công.
# Spec: docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
# Gọi thẳng helper cấp module của controllers.main theo quy ước repo.
# Ngày test tính ĐỘNG từ date.today() (lỡ hạn phụ thuộc "hôm nay").
# Owner: Nhật Anh.
# ============================================================
from datetime import date, datetime, time, timedelta

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _lapsed_info, _lapsed_table, _post_lapsed_decision_note,
    _public_holiday_dates_env,
)


@tagged('post_install', '-at_install')
class TestTimeoffLapsed(TransactionCase):

    def setUp(self):
        super().setUp()
        # Ép tz UTC cho mọi phép đổi giờ (work_credit dùng context tz;
        # hocba.attendance.date dùng tz user của NV) → test tất định.
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (lapsed)'})
        self.dept_b = Dept.create({'name': 'Khối B (lapsed)'})

        self.emp_mgr_a = self._mk_emp('TP A lapsed', '140000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A lapsed', '140000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV B lapsed', '140000000003', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('lapsed_mgr_a', self.emp_mgr_a)
        self.user_a = self._mk_user('lapsed_nv_a', self.emp_a)
        self.user_b = self._mk_user('lapsed_nv_b', self.emp_b)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR lapsed', 'login': 'lapsed_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self.teaching_off = self.env.ref(
            'hocba_timeoff.hb_leave_type_teaching_off')
        self._allocate(self.emp_a, 12)
        self._allocate(self.emp_b, 12)

    # ----- Helpers -----
    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10],
        })

    def _mk_user(self, login, emp):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'tz': 'UTC',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        emp.user_id = user
        return user

    def _allocate(self, emp, days):
        year = date.today().year
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ lapsed %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '%d-01-01' % year, 'date_to': '%d-12-31' % year,
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _past_working_days(self, n):
        """n ngày LÀM VIỆC (T2–T6, trừ ngày lễ đã seed) gần nhất TRƯỚC hôm
        nay, trả về tăng dần. Dùng để đặt khoảng nghỉ đã-trôi-qua tất định."""
        holidays = _public_holiday_dates_env(
            self.env, date.today() - timedelta(days=30), date.today())
        days, cur = [], date.today() - timedelta(days=1)
        while len(days) < n:
            if cur.weekday() < 5 and cur not in holidays:
                days.append(cur)
            cur -= timedelta(days=1)
        return list(reversed(days))

    def _mk_leave(self, emp, d_from, d_to, leave_type=None, half=False):
        vals = {
            'name': 'Nghỉ lapsed', 'employee_id': emp.id,
            'holiday_status_id': (leave_type or self.annual).id,
            'request_date_from': d_from, 'request_date_to': d_to,
        }
        if half:
            vals.update({'request_unit_half': True,
                         'request_date_from_period': 'am'})
        return self.env['hr.leave'].create(vals)

    def _mk_att(self, emp, day, full=True):
        """Bản ghi chấm công ngày `day`: full → work_credit 1.0; không full
        → 0.5 (chỉ công sáng). 02:00 UTC vào ≤ cutoff 10.0; +9h ≥ +6h → đủ
        công chiều; +4h < +6h → mất công chiều."""
        ci = datetime.combine(day, time(2, 0))
        co = ci + timedelta(hours=9 if full else 4)
        return self.env['hocba.attendance'].create({
            'employee_id': emp.id, 'check_in': ci, 'check_out': co})

    # ----- Task 1: field + kind -----
    def test_lapsed_notified_field_default_false(self):
        days = self._past_working_days(1)
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        self.assertFalse(leave.x_lapsed_notified)

    def test_notification_kind_lapsed_accepted(self):
        days = self._past_working_days(1)
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        notif = self.env['hb.leave.notification'].sudo().create({
            'recipient_id': self.mgr_a_user.id, 'leave_id': leave.id,
            'kind': 'lapsed', 'title': 't', 'body': 'b'})
        self.assertEqual(notif.kind, 'lapsed')
```

Thêm vào `custom-addons/hocba_timeoff/tests/__init__.py`:

```python
from . import test_lapsed
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Chạy lệnh test ở đầu plan. Expected: **ImportError** (`_lapsed_info` chưa tồn tại) hoặc lỗi field `x_lapsed_notified`/kind `lapsed`. Để qua được import ở bước này chưa cần — cứ ghi nhận fail đúng lý do.

- [ ] **Step 3: Tạo model**

Tạo `custom-addons/hocba_timeoff/models/hr_leave_lapsed.py`:

```python
# ============================================================
# Phase 12 — Đơn lỡ hạn duyệt (qua ngày bắt đầu nghỉ mà vẫn chờ duyệt).
# Cờ lỡ hạn + đối chiếu chấm công TÍNH SỐNG trong controller (không lưu DB)
# — xem _lapsed_info ở controllers/main.py. DB chỉ giữ 1 field chống báo
# chuông lặp cho cron CRON-TO-002. Owner: Nhật Anh.
# ============================================================
from odoo import fields, models


class HrLeaveLapsed(models.Model):
    _inherit = 'hr.leave'

    x_lapsed_notified = fields.Boolean(
        string='Đã báo lỡ hạn duyệt', default=False,
        help='Cron đã bắn chuông "đơn lỡ hạn" cho người duyệt (chỉ báo 1 lần).',
    )


class HbLeaveNotification(models.Model):
    """Mở rộng selection 'kind' của chuông cho sự kiện đơn lỡ hạn duyệt."""
    _inherit = 'hb.leave.notification'

    kind = fields.Selection(
        selection_add=[('lapsed', 'Lỡ hạn duyệt')],
        ondelete={'lapsed': 'cascade'},
    )
```

Trong `custom-addons/hocba_timeoff/models/__init__.py` thêm (theo thứ tự alphabet cạnh các import hr_leave_* khác):

```python
from . import hr_leave_lapsed
```

- [ ] **Step 4: Stub các helper để import test không gãy**

Cuối phần helper Phase 8 trong `custom-addons/hocba_timeoff/controllers/main.py` (sau `_request_age_working_days`, trước phần "Nghỉ phép giáo viên"), thêm stub tạm — Task 2/3/5 sẽ thay bằng code thật:

```python
# ---------------------------------------------------------------------------
# Phase 12 — Đơn lỡ hạn duyệt. Spec:
# docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
# ---------------------------------------------------------------------------
def _lapsed_info(env, leave):
    raise NotImplementedError


def _lapsed_table(env, scope, dept_id=False):
    raise NotImplementedError


def _post_lapsed_decision_note(env, leave, action, info):
    raise NotImplementedError
```

- [ ] **Step 5: Chạy test, xác nhận PASS**

Chạy lệnh test. Expected: 2 test PASS (`0 failed, 0 error(s) of 2 tests`).

- [ ] **Step 6: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/models/hr_leave_lapsed.py \
        custom-addons/hocba_timeoff/models/__init__.py \
        custom-addons/hocba_timeoff/controllers/main.py \
        custom-addons/hocba_timeoff/tests/test_lapsed.py \
        custom-addons/hocba_timeoff/tests/__init__.py
git commit -m "feat(timeoff): field x_lapsed_notified + kind 'lapsed' (Phase 12)"
```

---

### Task 2: Helper `_lapsed_info` — phát hiện lỡ hạn + đối chiếu chấm công

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py` (thay stub `_lapsed_info`)
- Test: `custom-addons/hocba_timeoff/tests/test_lapsed.py`

- [ ] **Step 1: Viết các test failing**

Thêm vào class `TestTimeoffLapsed`:

```python
    # ----- Task 2: _lapsed_info -----
    def test_not_lapsed_when_start_today_or_future(self):
        """BR-L01: chỉ lỡ hạn khi ngày BẮT ĐẦU < hôm nay."""
        today = date.today()
        leave_today = self._mk_leave(self.emp_a, today, today)
        self.assertIsNone(_lapsed_info(self.env, leave_today))
        future = today + timedelta(days=7)
        leave_future = self._mk_leave(self.emp_a, future, future)
        self.assertIsNone(_lapsed_info(self.env, leave_future))

    def test_not_lapsed_when_not_pending(self):
        """Đơn đã duyệt/từ chối không tính lỡ hạn dù ngày đã qua."""
        days = self._past_working_days(2)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        leave.sudo().action_refuse()
        self.assertIsNone(_lapsed_info(self.env, leave))

    def test_lapsed_no_attendance_suggests_approve(self):
        """BR-L03: nghỉ 2 ngày đã qua, không chấm công → gợi ý duyệt trễ."""
        days = self._past_working_days(2)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        self.assertEqual(info['checkedCount'], 2)
        self.assertEqual(info['workedCount'], 0)
        self.assertEqual(info['suggestion'], 'approve')
        self.assertFalse(info['exempt'])
        self.assertGreaterEqual(info['lapsedDays'], 2)

    def test_lapsed_all_worked_suggests_refuse(self):
        """BR-L03: đủ công mọi ngày nghỉ đã qua → gợi ý từ chối."""
        days = self._past_working_days(2)
        for d in days:
            self._mk_att(self.emp_a, d, full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 2)
        self.assertEqual(info['suggestion'], 'refuse')

    def test_lapsed_mixed_no_suggestion(self):
        """BR-L03: ngày làm ngày nghỉ → không gợi ý, người duyệt tự quyết."""
        days = self._past_working_days(2)
        self._mk_att(self.emp_a, days[0], full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 1)
        self.assertEqual(info['checkedCount'], 2)
        self.assertIsNone(info['suggestion'])

    def test_half_credit_counts_as_worked_for_full_day_leave(self):
        """BR-L02: đơn CẢ NGÀY — công 0.5 đã tính là 'vẫn đi làm'."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=False)     # 0.5 công
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 1)
        self.assertEqual(info['suggestion'], 'refuse')

    def test_half_day_leave_needs_full_credit(self):
        """BR-L02: đơn NỬA NGÀY — 0.5 công là khớp đơn (không mâu thuẫn);
        1.0 công mới là mâu thuẫn."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=False)     # 0.5 công
        leave = self._mk_leave(self.emp_a, days[0], days[0], half=True)
        info = _lapsed_info(self.env, leave)
        self.assertEqual(info['workedCount'], 0)
        self.assertEqual(info['suggestion'], 'approve')

        days2 = self._past_working_days(2)
        self._mk_att(self.emp_b, days2[0], full=True)     # 1.0 công
        leave_b = self._mk_leave(self.emp_b, days2[0], days2[0], half=True)
        info_b = _lapsed_info(self.env, leave_b)
        self.assertEqual(info_b['workedCount'], 1)
        self.assertEqual(info_b['suggestion'], 'refuse')

    def test_teaching_off_exempt(self):
        """BR-L02: loại 'Nghỉ Buổi Dạy' miễn đối chiếu — chỉ cờ lỡ hạn."""
        days = self._past_working_days(1)
        self._mk_att(self.emp_a, days[0], full=True)
        leave = self._mk_leave(self.emp_a, days[0], days[0],
                               leave_type=self.teaching_off)
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        self.assertTrue(info['exempt'])
        self.assertEqual(info['dayChecks'], [])
        self.assertIsNone(info['suggestion'])

    def test_future_days_not_checked(self):
        """Đơn đang-nghỉ-dở (qua ngày bắt đầu, chưa hết): chỉ đối chiếu
        các ngày ĐÃ QUA (đến hết hôm qua)."""
        days = self._past_working_days(1)
        end = date.today() + timedelta(days=3)
        leave = self._mk_leave(self.emp_a, days[0], end)
        info = _lapsed_info(self.env, leave)
        self.assertTrue(info['isLapsed'])
        # Chỉ ngày đã qua được kiểm — không ngày nào ≥ hôm nay.
        for c in info['dayChecks']:
            self.assertLess(c['date'], date.today().isoformat())
```

Lưu ý khi chạy: nếu `hr.leave` seed của dự án chặn tạo đơn ngày quá khứ (ValidationError ngay `create`), tạo đơn với ngày tương lai rồi `leave.sudo().write({'request_date_from': ..., 'request_date_to': ...})` — cập nhật helper `_mk_leave` một lần, các test giữ nguyên.

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Expected: các test mới FAIL với `NotImplementedError`.

- [ ] **Step 3: Cài đặt `_lapsed_info`**

Thay stub trong `controllers/main.py` bằng:

```python
def _working_dates_env(env, start, end):
    """Danh sách NGÀY LÀM VIỆC (T2–T6 + workday HR, trừ lễ) trong [start, end]."""
    if not start or not end or end < start:
        return []
    work_extra = set(env['hb.work.day'].sudo().search([
        ('date', '>=', start), ('date', '<=', end)]).mapped('date'))
    holidays = _public_holiday_dates_env(env, start, end)
    days, cur = [], start
    while cur <= end:
        if (cur.weekday() < 5 or cur in work_extra) and cur not in holidays:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def _lapsed_info(env, leave):
    """Thông tin 'lỡ hạn duyệt' của 1 đơn (BR-L01→L03) — None nếu chưa lỡ hạn.

    Lỡ hạn = còn chờ duyệt mà ngày BẮT ĐẦU nghỉ đã qua. Đối chiếu
    hocba.attendance từng ngày nghỉ ĐÃ QUA (đến hết hôm qua): tổng work_credit
    trong ngày >= 0.5 là 'vẫn đi làm'; đơn NỬA NGÀY cần >= 1.0 mới tính (nửa
    làm + nửa nghỉ là khớp đơn). Loại 'Nghỉ Buổi Dạy' miễn đối chiếu — GV có
    thể vẫn chấm công ở trung tâm dù nghỉ 1 buổi dạy. Attendance đọc qua sudo:
    người duyệt không có ACL hocba.attendance; quyền phạm vi kiểm ở tầng gọi."""
    if leave.state not in PENDING_STATES:
        return None
    d0, d1 = _leave_day_bounds(leave)
    today = fields.Date.context_today(env.user)
    if not d0 or d0 >= today:
        return None

    yesterday = today - timedelta(days=1)
    lapsed_days = _count_working_days_env(env, d0, yesterday)
    exempt = leave.holiday_status_id.id == _teaching_off_type_id(env)

    day_checks, worked = [], 0
    if not exempt:
        dates = _working_dates_env(env, d0, min(d1 or yesterday, yesterday))
        if dates:
            atts = env['hocba.attendance'].sudo().search([
                ('employee_id', '=', leave.employee_id.id),
                ('date', 'in', dates)])
            credit_by_day = {}
            for a in atts:
                credit_by_day[a.date] = credit_by_day.get(a.date, 0.0) + a.work_credit
            threshold = 1.0 if leave.request_unit_half else 0.5
            for d in dates:
                credit = credit_by_day.get(d, 0.0)
                is_worked = credit >= threshold
                worked += 1 if is_worked else 0
                day_checks.append({'date': _d(d), 'worked': is_worked,
                                   'workCredit': round(credit, 1)})

    checked = len(day_checks)
    suggestion = None
    if checked:
        if worked == 0:
            suggestion = 'approve'
        elif worked == checked:
            suggestion = 'refuse'
    return {
        'isLapsed': True,
        'lapsedDays': lapsed_days,
        'dayChecks': day_checks,
        'workedCount': worked,
        'checkedCount': checked,
        'suggestion': suggestion,
        'exempt': exempt,
    }
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Expected: toàn bộ test trong `TestTimeoffLapsed` PASS.

- [ ] **Step 5: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/controllers/main.py \
        custom-addons/hocba_timeoff/tests/test_lapsed.py
git commit -m "feat(timeoff): _lapsed_info — phát hiện đơn lỡ hạn + đối chiếu chấm công"
```

---

### Task 3: Helper `_lapsed_table` — dữ liệu màn giám sát (KPI, bảng, theo phòng)

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py` (thay stub `_lapsed_table`, thêm `_lapsed_summary_label`)
- Test: `custom-addons/hocba_timeoff/tests/test_lapsed.py`

- [ ] **Step 1: Viết test failing**

```python
    # ----- Task 3: _lapsed_table -----
    def test_lapsed_table_hr_sees_all_manager_sees_own_dept(self):
        """BR-L06: HR thấy mọi phòng; trưởng phòng chỉ thấy phòng mình."""
        days = self._past_working_days(2)
        self._mk_leave(self.emp_a, days[0], days[1])          # Khối A
        self._mk_att(self.emp_b, days[0], full=True)
        self._mk_att(self.emp_b, days[1], full=True)
        self._mk_leave(self.emp_b, days[0], days[1])          # Khối B

        env_hr = self.env(user=self.hr_user)
        table_hr = _lapsed_table(env_hr, _scope_for(env_hr))
        self.assertEqual(table_hr['kpi']['total'], 2)
        self.assertEqual(table_hr['kpi']['suggestApprove'], 1)
        self.assertEqual(table_hr['kpi']['suggestRefuse'], 1)
        self.assertEqual(
            sorted(r['count'] for r in table_hr['byDepartment']), [1, 1])

        env_mgr = self.env(user=self.mgr_a_user)
        table_mgr = _lapsed_table(env_mgr, _scope_for(env_mgr))
        self.assertEqual(table_mgr['kpi']['total'], 1)
        self.assertEqual(table_mgr['items'][0]['employee'], self.emp_a.name)

    def test_lapsed_table_items_have_summary_and_suggestion(self):
        days = self._past_working_days(1)
        self._mk_leave(self.emp_a, days[0], days[0])
        env_hr = self.env(user=self.hr_user)
        table = _lapsed_table(env_hr, _scope_for(env_hr))
        row = table['items'][0]
        self.assertEqual(row['suggestion'], 'approve')
        self.assertIn('0/1', row['summary'])
        self.assertEqual(row['state'], 'confirm')
        self.assertGreaterEqual(row['lapsedDays'], 1)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (NotImplementedError)

- [ ] **Step 3: Cài đặt**

Thay stub `_lapsed_table` bằng:

```python
def _lapsed_summary_label(info):
    """Chuỗi tóm tắt đối chiếu (dùng cả trong chatter và bảng giám sát FE)."""
    if info['exempt']:
        return 'nghỉ buổi dạy — không đối chiếu chấm công'
    if not info['checkedCount']:
        return 'chưa có ngày nghỉ nào qua để đối chiếu'
    return 'đi làm %d/%d ngày nghỉ đã qua' % (
        info['workedCount'], info['checkedCount'])


def _lapsed_table(env, scope, dept_id=False):
    """Dữ liệu màn 'Giám sát duyệt đơn' (BR-L06): KPI + bảng đơn lỡ hạn
    + đếm theo phòng. sudo + lọc phòng ban tường minh theo scope."""
    today = fields.Date.context_today(env.user)
    domain = [('state', 'in', list(PENDING_STATES)),
              ('request_date_from', '<', today)] + _dept_domain(scope)
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    leaves = env['hr.leave'].sudo().search(domain, order='request_date_from, id')

    items, by_dept = [], {}
    n_approve = n_refuse = n_review = oldest = 0
    for leave in leaves:
        info = _lapsed_info(env, leave)
        if not info:
            continue
        if info['suggestion'] == 'approve':
            n_approve += 1
        elif info['suggestion'] == 'refuse':
            n_refuse += 1
        else:
            n_review += 1
        oldest = max(oldest, info['lapsedDays'])
        dept = leave.department_id or leave.employee_id.department_id
        row = by_dept.setdefault(dept.id or 0, {
            'id': dept.id or False, 'name': dept.name or '—', 'count': 0})
        row['count'] += 1
        items.append({
            'requestId': leave.id,
            'employee': leave.employee_id.name,
            'department': dept.name or '—',
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'days': round(leave.number_of_days, 2),
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'lapsedDays': info['lapsedDays'],
            'summary': _lapsed_summary_label(info),
            'suggestion': info['suggestion'],
            'workedCount': info['workedCount'],
            'checkedCount': info['checkedCount'],
            'exempt': info['exempt'],
        })
    items.sort(key=lambda r: r['lapsedDays'], reverse=True)
    return {
        'kpi': {'total': len(items), 'suggestApprove': n_approve,
                'suggestRefuse': n_refuse, 'needsReview': n_review,
                'oldestLapsedDays': oldest},
        'items': items,
        'byDepartment': sorted(by_dept.values(),
                               key=lambda r: r['count'], reverse=True),
    }
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

- [ ] **Step 5: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/controllers/main.py \
        custom-addons/hocba_timeoff/tests/test_lapsed.py
git commit -m "feat(timeoff): _lapsed_table — dữ liệu màn giám sát duyệt đơn"
```

---

### Task 4: Chatter note khi xử lý đơn lỡ hạn (BR-L04)

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py` (thay stub `_post_lapsed_decision_note` + wire vào `api_request_decision`)
- Test: `custom-addons/hocba_timeoff/tests/test_lapsed.py`

- [ ] **Step 1: Viết test failing**

```python
    # ----- Task 4: chatter note duyệt trễ / từ chối -----
    def test_lapsed_decision_note_posted(self):
        days = self._past_working_days(2)
        leave = self._mk_leave(self.emp_a, days[0], days[1])
        info = _lapsed_info(self.env, leave)
        n_before = len(leave.sudo().message_ids)
        _post_lapsed_decision_note(self.env, leave, 'approve', info)
        msgs = leave.sudo().message_ids
        self.assertEqual(len(msgs), n_before + 1)
        self.assertIn('Duyệt trễ', msgs[0].body)
        self.assertIn('0/2', msgs[0].body)

        _post_lapsed_decision_note(self.env, leave, 'refuse', info)
        self.assertIn('Từ chối', leave.sudo().message_ids[0].body)

    def test_no_note_when_not_lapsed(self):
        """Đơn thường (không lỡ hạn) → không ghi note."""
        future = date.today() + timedelta(days=7)
        leave = self._mk_leave(self.emp_a, future, future)
        n_before = len(leave.sudo().message_ids)
        _post_lapsed_decision_note(
            self.env, leave, 'approve', _lapsed_info(self.env, leave))
        self.assertEqual(len(leave.sudo().message_ids), n_before)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (NotImplementedError)

- [ ] **Step 3: Cài đặt helper + wire vào endpoint**

Thay stub bằng:

```python
def _post_lapsed_decision_note(env, leave, action, info):
    """BR-L04: ghi vết 'duyệt trễ / từ chối đơn lỡ hạn' vào chatter.
    `info` phải lấy TRƯỚC khi duyệt (sau khi duyệt state đổi → hết lỡ hạn)."""
    if not info or not info.get('isLapsed'):
        return
    head = 'Duyệt trễ' if action == 'approve' else 'Từ chối đơn lỡ hạn'
    leave.sudo().message_post(
        body='%s — đơn lỡ hạn %d ngày làm việc. Đối chiếu chấm công: %s.' % (
            head, info['lapsedDays'], _lapsed_summary_label(info)),
        subtype_xmlid='mail.mt_note',
    )
```

Trong `api_request_decision` (controllers/main.py, ~dòng 1554): NGAY TRƯỚC `try:` thêm:

```python
        # Phase 12: chụp trạng thái lỡ hạn TRƯỚC khi duyệt (duyệt xong state
        # đổi → _lapsed_info trả None) để ghi vết "duyệt trễ" chính xác.
        lapsed_before = _lapsed_info(request.env, leave)
```

và NGAY SAU dòng `_notify_decision(request.env, leave, action)` thêm:

```python
            _post_lapsed_decision_note(request.env, leave, action, lapsed_before)
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

- [ ] **Step 5: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/controllers/main.py \
        custom-addons/hocba_timeoff/tests/test_lapsed.py
git commit -m "feat(timeoff): ghi chatter 'duyệt trễ/từ chối' khi xử lý đơn lỡ hạn"
```

---

### Task 5: Cron báo chuông 1 lần (BR-L05)

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hb_timeoff_cron.py`
- Create: `custom-addons/hocba_timeoff/data/ir_cron_lapsed_data.xml`
- Modify: `custom-addons/hocba_timeoff/__manifest__.py`
- Test: `custom-addons/hocba_timeoff/tests/test_lapsed.py`

- [ ] **Step 1: Viết test failing**

```python
    # ----- Task 5: cron báo chuông 1 lần -----
    def _notifs_of(self, user, kind=None):
        domain = [('recipient_id', '=', user.id)]
        if kind:
            domain.append(('kind', '=', kind))
        return self.env['hb.leave.notification'].sudo().search(domain)

    def test_cron_notifies_approvers_once(self):
        """BR-L05: đơn lỡ hạn → chuông cho trưởng phòng + HR đúng 1 LẦN."""
        days = self._past_working_days(1)
        leave = self._mk_leave(self.emp_a, days[0], days[0])
        future = date.today() + timedelta(days=7)
        leave_ok = self._mk_leave(self.emp_b, future, future)

        Cron = self.env['hb.timeoff.cron']
        Cron._cron_notify_lapsed_approvals()

        mgr_notifs = self._notifs_of(self.mgr_a_user, kind='lapsed')
        self.assertEqual(len(mgr_notifs), 1)
        self.assertEqual(mgr_notifs.leave_id.id, leave.id)
        self.assertTrue(self._notifs_of(self.hr_user, kind='lapsed'))
        self.assertTrue(leave.x_lapsed_notified)
        # Đơn chưa lỡ hạn: không báo, không set cờ.
        self.assertFalse(leave_ok.x_lapsed_notified)

        # Chạy lần 2 → không báo thêm.
        Cron._cron_notify_lapsed_approvals()
        self.assertEqual(len(self._notifs_of(self.mgr_a_user, kind='lapsed')), 1)
```

- [ ] **Step 2: Chạy test, xác nhận FAIL** (AttributeError: `_cron_notify_lapsed_approvals`)

- [ ] **Step 3: Cài đặt cron**

Trong `custom-addons/hocba_timeoff/models/hb_timeoff_cron.py`, sửa dòng import odoo thành:

```python
from odoo import models, fields, api, _
```

và thêm method vào class `HbTimeoffCron`:

```python
    @api.model
    def _cron_notify_lapsed_approvals(self):
        """CRON-TO-002 (Phase 12): báo chuông 1 LẦN cho người duyệt khi đơn
        lỡ hạn — còn chờ duyệt mà ngày bắt đầu nghỉ đã qua (BR-L05).
        Chống lặp bằng x_lapsed_notified. Không escalate, không email."""
        # Import trong hàm: controllers nạp SAU models khi Odoo khởi động.
        from odoo.addons.hocba_timeoff.controllers.main import (
            PENDING_STATES, _approver_users, _push_notification,
            _leave_span_label)
        today = fields.Date.context_today(self.env.user)
        leaves = self.env['hr.leave'].sudo().search([
            ('state', 'in', list(PENDING_STATES)),
            ('request_date_from', '<', today),
            ('x_lapsed_notified', '=', False),
        ])
        for leave in leaves:
            title = 'Đơn nghỉ lỡ hạn duyệt'
            body = '%s — %s (%s) đã qua ngày nghỉ mà chưa được duyệt.' % (
                leave.employee_id.name, leave.holiday_status_id.name,
                _leave_span_label(leave))
            for user in _approver_users(self.env, leave):
                _push_notification(self.env, user, leave, 'lapsed', title, body)
            leave.x_lapsed_notified = True
        _logger.info('CRON-TO-002: đã báo %d đơn lỡ hạn duyệt.', len(leaves))
        return len(leaves)
```

Tạo `custom-addons/hocba_timeoff/data/ir_cron_lapsed_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- CRON-TO-002 (Phase 12): quét đơn lỡ hạn duyệt, báo chuông người duyệt
         1 lần/đơn. Chạy hàng ngày 00:30 UTC (07:30 Asia/Ho_Chi_Minh) — sau
         CRON-TO-001. Odoo 19: ir.cron không còn numbercall. -->
    <record id="ir_cron_lapsed_approval_notify" model="ir.cron">
        <field name="name">HB: Báo đơn nghỉ lỡ hạn duyệt (CRON-TO-002)</field>
        <field name="model_id" ref="model_hb_timeoff_cron"/>
        <field name="state">code</field>
        <field name="code">model._cron_notify_lapsed_approvals()</field>
        <field name="interval_number">1</field>
        <field name="interval_type">days</field>
        <field name="active" eval="True"/>
        <field name="nextcall">2026-07-04 00:30:00</field>
    </record>
</odoo>
```

Trong `custom-addons/hocba_timeoff/__manifest__.py`, sau dòng `'data/ir_cron_reminder_data.xml',` thêm:

```python
        'data/ir_cron_lapsed_data.xml',
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

- [ ] **Step 5: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/models/hb_timeoff_cron.py \
        custom-addons/hocba_timeoff/data/ir_cron_lapsed_data.xml \
        custom-addons/hocba_timeoff/__manifest__.py \
        custom-addons/hocba_timeoff/tests/test_lapsed.py
git commit -m "feat(timeoff): cron CRON-TO-002 báo chuông đơn lỡ hạn duyệt (1 lần)"
```

---

### Task 6: Wire controller — key `lapsed` trong /approvals + endpoint /lapsed-dashboard

Lớp mỏng dùng lại helper đã test ở Task 2/3 — không unit test riêng (quy ước repo: test helper cấp module; endpoint kiểm tay ở Task 9).

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py`

- [ ] **Step 1: Thêm key `lapsed` vào `_approval_request`**

Trong method `_approval_request` (~dòng 1079), thêm vào dict trả về, sau dòng `'submittedAt': ...`:

```python
            # Phase 12 — đơn lỡ hạn duyệt + đối chiếu chấm công (None nếu chưa).
            'lapsed': _lapsed_info(request.env, leave),
```

- [ ] **Step 2: Thêm endpoint `api_lapsed_dashboard`**

Đặt ngay sau method `api_dashboard`/`_dashboard_employee` (cuối nhóm dashboard, ~dòng 1900):

```python
    # ------------------------------------------------------------------
    # 3.6b. GET /lapsed-dashboard — màn "Giám sát duyệt đơn" (Phase 12).
    # Chỉ officer; HR/Admin mọi phòng, Trưởng phòng phòng mình (BR-L06).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/lapsed-dashboard', auth='user',
                type='http', methods=['GET'])
    def api_lapsed_dashboard(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        data = _lapsed_table(request.env, scope, dept_id)
        data.update({
            **self._scope_flags(scope),
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
        })
        return request.make_json_response(data)
```

- [ ] **Step 3: Chạy lại toàn bộ test class để chắc không vỡ gì**

Chạy lệnh test. Expected: toàn bộ PASS (wire không đổi hành vi helper).

- [ ] **Step 4: Commit** *(DỪNG — hỏi user trước)*

```bash
git add custom-addons/hocba_timeoff/controllers/main.py
git commit -m "feat(timeoff): API /lapsed-dashboard + key lapsed trong /approvals"
```

---

### Task 7: SPA — badge + gợi ý 1-chạm ở tab Chờ duyệt

**Files:**
- Modify: `frontend/src/api/timeoff.js`
- Modify: `frontend/src/features/timeoff/ApprovalPanel.jsx`
- Modify: `frontend/src/components/NotificationBell.jsx`

- [ ] **Step 1: Thêm API client**

Cuối `frontend/src/api/timeoff.js`:

```js
/* Phase 12 — màn "Giám sát duyệt đơn": đơn lỡ hạn (qua ngày bắt đầu nghỉ mà
   vẫn chờ duyệt) + đối chiếu chấm công + KPI. Chỉ officer; dept: lọc 1 phòng. */
export const fetchLapsedDashboard = (dept) => {
  const p = new URLSearchParams();
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/lapsed-dashboard' + (q ? '?' + q : ''));
};
```

- [ ] **Step 2: Màu chấm chuông cho kind `lapsed`**

Trong `frontend/src/components/NotificationBell.jsx`, map `KIND_DOT` (dòng 13–17) thêm:

```js
  lapsed: 'var(--red-600,#dc2626)',
```

- [ ] **Step 3: Badge "Lỡ hạn" trên bảng Chờ duyệt**

Trong `frontend/src/features/timeoff/ApprovalPanel.jsx`, cột Cảnh báo (khối `<div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>`, sau badge `r.overdue`):

```jsx
                    {r.lapsed && (
                      <Badge kind="red">
                        Lỡ hạn{r.lapsed.lapsedDays > 0 ? ` ${r.lapsed.lapsedDays} ngày` : ''}
                      </Badge>
                    )}
```

- [ ] **Step 4: Box đối chiếu + nút "theo đề xuất" trong DecisionModal**

Trong `DecisionModal` (cùng file), thêm block sau `{req.reason && ...}` (trước block `{req.overlapCount > 0 && ...}`):

```jsx
        {req.lapsed && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, fontSize: 12.5, color: 'var(--red-700)' }}>
            <b>Đơn lỡ hạn duyệt{req.lapsed.lapsedDays > 0 ? ` ${req.lapsed.lapsedDays} ngày làm việc` : ''}</b>
            {' '}— đã qua ngày bắt đầu nghỉ mà chưa được duyệt.
            <div style={{ marginTop: 6, color: 'var(--ink)' }}>
              {req.lapsed.exempt
                ? 'Nghỉ buổi dạy — không đối chiếu chấm công.'
                : req.lapsed.checkedCount === 0
                  ? 'Chưa có ngày nghỉ nào qua để đối chiếu chấm công.'
                  : `Đối chiếu chấm công: đi làm ${req.lapsed.workedCount}/${req.lapsed.checkedCount} ngày nghỉ đã qua.`}
              {req.lapsed.suggestion === 'approve' && <b> Nhân viên nghỉ thật — đề xuất duyệt trễ.</b>}
              {req.lapsed.suggestion === 'refuse' && <b> Nhân viên vẫn đi làm — đề xuất từ chối (hoàn quỹ).</b>}
            </div>
            {req.lapsed.dayChecks.length > 0 && (
              <div style={{ marginTop: 6, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {req.lapsed.dayChecks.map((d) => (
                  <Badge key={d.date} kind={d.worked ? 'amber' : 'green'}>
                    {fmtDate(d.date)}: {d.worked ? `đi làm (${d.workCredit} công)` : 'nghỉ'}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}
```

Trong footer của `DecisionModal` (khối nút Đóng/Từ chối/Duyệt), thêm TRƯỚC nút "Từ chối":

```jsx
        {req.lapsed && req.lapsed.suggestion && (
          <button className="btn btn-soft" disabled={busy}
            style={{ marginRight: 'auto', borderColor: 'var(--red-600)', color: 'var(--red-700)' }}
            onClick={() => {
              const label = req.lapsed.suggestion === 'approve'
                ? 'Duyệt trễ' : 'Từ chối (nhân viên vẫn đi làm)';
              if (window.confirm(label + ' đơn này theo đề xuất đối chiếu chấm công?')) {
                decide(req.lapsed.suggestion);
              }
            }}>
            <Icon name="alertCircle" size={16} />
            {req.lapsed.suggestion === 'approve' ? 'Duyệt trễ theo đề xuất' : 'Từ chối theo đề xuất'}
          </button>
        )}
```

- [ ] **Step 5: Build SPA, xác nhận không lỗi**

```bash
cd /Users/nguyenanh/odoo19/frontend && npm run build
```

Expected: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 6: Commit** *(DỪNG — hỏi user trước)*

```bash
git add frontend/src/api/timeoff.js frontend/src/features/timeoff/ApprovalPanel.jsx \
        frontend/src/components/NotificationBell.jsx custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-ui): badge lỡ hạn + đề xuất xử lý 1-chạm ở tab Chờ duyệt"
```

---

### Task 8: SPA — màn "Giám sát duyệt đơn" (LapsedPanel) + tab mới

**Files:**
- Create: `frontend/src/features/timeoff/LapsedPanel.jsx`
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`

- [ ] **Step 1: Tạo `LapsedPanel.jsx`**

```jsx
/* Tab "Giám sát duyệt đơn" (Phase 12) — đơn lỡ hạn duyệt + đối chiếu chấm
   công + KPI. Chỉ officer (HR/Admin mọi phòng, Trưởng phòng phòng mình).
   Spec: docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
   Owner: Nhật Anh. */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchLapsedDashboard, decideRequest } from '../../api/timeoff';

function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px', color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}

export default function LapsedPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dept, setDept] = useState('');
  const [busy, setBusy] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchLapsedDashboard(dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải giám sát duyệt đơn…" />;

  const k = data.kpi;
  const maxDept = Math.max(...data.byDepartment.map((r) => r.count), 1);

  // Nút 1-chạm: gọi thẳng flow duyệt hiện có với action theo đề xuất (BR-L04).
  const quickDecide = (row) => {
    const label = row.suggestion === 'approve'
      ? 'Duyệt trễ' : 'Từ chối (nhân viên vẫn đi làm)';
    if (!window.confirm(`${label} đơn của ${row.employee}?`)) return;
    setBusy(row.requestId);
    decideRequest(row.requestId, { action: row.suggestion })
      .then(() => setTick((t) => t + 1))
      .catch((e) => alert('Không xử lý được đơn: ' + e.message))
      .finally(() => setBusy(null));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {data.seeAll && (
        <div className="filterbar">
          <div style={{ marginLeft: 'auto' }}>
            <select className="sel" value={dept} onChange={(e) => setDept(e.target.value)}>
              <option value="">Mọi phòng ban</option>
              {data.allDepartments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        </div>
      )}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Đơn lỡ hạn duyệt" value={k.total}
          color={k.total > 0 ? 'var(--red-600)' : 'var(--ink)'}
          sub="qua ngày nghỉ, chưa duyệt" />
        <Kpi label="Đề xuất duyệt trễ" value={k.suggestApprove} color="var(--green)"
          sub="nhân viên nghỉ thật" />
        <Kpi label="Mâu thuẫn chấm công" value={k.suggestRefuse} color="var(--amber)"
          sub="xin nghỉ nhưng vẫn đi làm" />
        <Kpi label="Cần xem tay" value={k.needsReview} sub="lẫn lộn / chưa đủ dữ liệu" />
        <Kpi label="Lỡ hạn lâu nhất" value={k.oldestLapsedDays} sub="ngày làm việc" />
      </div>

      {data.byDepartment.length > 0 && (
        <div className="card">
          <div className="card-head"><h3>Đơn lỡ hạn theo phòng ban</h3></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 13, padding: 16 }}>
            {data.byDepartment.map((r) => (
              <div key={r.id || r.name}>
                <div className="between" style={{ marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</span>
                  <span className="muted mono" style={{ fontSize: 12 }}>{r.count} đơn</span>
                </div>
                <div className="bar">
                  <span style={{ width: (r.count / maxDept) * 100 + '%', background: 'var(--red-600)' }}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-head">
          <h3>Chi tiết đơn lỡ hạn</h3>
          <span className="sub">{data.items.length} đơn — đối chiếu bảng chấm công các ngày nghỉ đã qua</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Loại nghỉ</th>
              <th>Từ</th><th>Đến</th><th className="tbl-num">Lỡ hạn</th>
              <th>Đối chiếu chấm công</th><th>Đề xuất</th><th></th>
            </tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.requestId}>
                  <td style={{ fontWeight: 600 }}>{r.employee}</td>
                  <td className="muted">{r.department}</td>
                  <td>{r.leaveType}</td>
                  <td className="mono muted">{fmtDate(r.from)}</td>
                  <td className="mono muted">{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 700, color: 'var(--red-700)' }}>
                    {r.lapsedDays} ngày</td>
                  <td className="muted" style={{ fontSize: 12.5 }}>{r.summary}</td>
                  <td>
                    {r.suggestion === 'approve' && <Badge kind="green">Duyệt trễ</Badge>}
                    {r.suggestion === 'refuse' && <Badge kind="amber">Từ chối</Badge>}
                    {!r.suggestion && <Badge kind="gray">Xem tay</Badge>}
                  </td>
                  <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                    {r.suggestion ? (
                      <button className="btn btn-primary btn-sm"
                        disabled={busy === r.requestId} onClick={() => quickDecide(r)}>
                        {busy === r.requestId ? 'Đang xử lý…' : 'Xử lý theo đề xuất'}
                      </button>
                    ) : (
                      <span className="muted" style={{ fontSize: 12 }}>xử lý ở tab Chờ duyệt</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.items.length === 0 && (
          <EmptyState>Không có đơn nào lỡ hạn duyệt. 🎉</EmptyState>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Đăng ký tab trong `TimeOff.jsx`**

Thêm import (cạnh import `ApprovalPanel`):

```jsx
import LapsedPanel from './LapsedPanel';
```

Trong khối `if (data.isOfficer) { tabs.push(...) }` sửa thành (thêm `lapsed` sau `approvals`):

```jsx
    tabs.push(['overview', 'Tổng quan'], ['calendar', 'Lịch'],
              ['approvals', 'Chờ duyệt'], ['lapsed', 'Giám sát duyệt'],
              ['approved', 'Đơn đã duyệt'], ['balances', 'Quỹ phép']);
```

Thêm render (sau dòng render ApprovalPanel):

```jsx
      {activeTab === 'lapsed' && data.isOfficer && <LapsedPanel />}
```

- [ ] **Step 3: Build SPA**

```bash
cd /Users/nguyenanh/odoo19/frontend && npm run build
```

Expected: build OK.

- [ ] **Step 4: Commit** *(DỪNG — hỏi user trước)*

```bash
git add frontend/src/features/timeoff/LapsedPanel.jsx \
        frontend/src/features/timeoff/TimeOff.jsx \
        custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-ui): màn 'Giám sát duyệt đơn' — KPI + bảng đơn lỡ hạn"
```

---

### Task 9: Kiểm thử tổng + verify tay

- [ ] **Step 1: Chạy FULL test module hocba_timeoff**

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```

Expected: `0 failed, 0 error(s) of N tests` với N > 0 (mọi test cũ + mới).

- [ ] **Step 2: Verify tay trên app (Neon stack đang chạy)**

Upgrade module lên DB đang serve (lưu ý gotcha Neon: nếu upgrade trên Neon phải dùng endpoint TRỰC TIẾP không `-pooler`), restart `odoo19-odoo-1`, rồi kiểm bằng preview (route `/hocba-hrm`):

1. Đăng nhập `hr.manager` (pw `hocba@123`) → màn Nghỉ phép có tab "Giám sát duyệt"; KPI + bảng hiện đơn lỡ hạn (nếu DB chưa có, tạo 1 đơn ngày quá khứ bằng `nv.test` trước).
2. Tab Chờ duyệt: đơn lỡ hạn có badge đỏ "Lỡ hạn N ngày"; mở modal Xử lý thấy box đối chiếu + nút "theo đề xuất"; bấm nút → đơn được duyệt/từ chối, chatter (endpoint history) có note "Duyệt trễ…".
3. Đăng nhập `nv.test` → KHÔNG thấy tab Giám sát duyệt; gọi thẳng `GET /hocba-hrm/api/timeoff/lapsed-dashboard` trả 403.
4. Chuông thông báo của `hr.manager` có tin "Đơn nghỉ lỡ hạn duyệt" sau khi chạy tay cron: Settings → Technical → Scheduled Actions → "HB: Báo đơn nghỉ lỡ hạn duyệt (CRON-TO-002)" → Run Manually.

- [ ] **Step 3: Cập nhật docs nếu có seed/đổi DB test**

Nếu bước verify tạo dữ liệu test mới trên DB chung → cập nhật `docs/DB_TEST_DATA.md` (bảng tài khoản + nhật ký) theo quy ước repo.

- [ ] **Step 4: Commit cuối (nếu có thay đổi docs)** *(DỪNG — hỏi user trước)*

```bash
git add docs/DB_TEST_DATA.md
git commit -m "docs: nhật ký dữ liệu test Phase 12 (đơn lỡ hạn duyệt)"
```

---

## Self-Review đã chạy

- **Spec coverage:** BR-L01/L02/L03 → Task 2; BR-L04 → Task 4 + nút 1-chạm Task 7/8; BR-L05 → Task 5; BR-L06 → Task 3 (scope) + Task 6 (endpoint 403); dashboard riêng → Task 8; badge tab Chờ duyệt → Task 7; test hoàn quỹ khi từ chối đi qua flow chuẩn `action_refuse` của Odoo (đã có test `test_adjustment.py` cover hoàn quỹ) — không lặp lại.
- **Type consistency:** `_lapsed_info` trả `isLapsed/lapsedDays/dayChecks/workedCount/checkedCount/suggestion/exempt` — FE dùng đúng các key này; `_lapsed_table` items dùng `requestId/summary/suggestion/lapsedDays` — LapsedPanel khớp.
- **Placeholder:** không còn TBD/TODO; mọi bước code có code đầy đủ.
