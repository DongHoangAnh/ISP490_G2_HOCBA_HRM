# Thiết kế — Gói 4B: Check-in theo ca (cửa sổ ±15') cho CTV/OT

**Ngày:** 18/06/2026 · **Trạng thái:** chốt (tự quyết theo tiêu chí khuyến nghị — goal autonomous)
**Phạm vi:** `hocba_attendance` (policy + model attendance), `hocba_hrm/controllers/main.py` (API), frontend `frontend/src/features/attendance/`.
**Spec liên quan:** Gói 2 [khóa check-in](2026-06-17-attendance-account-split-lock-design.md), Gói 4A [đăng ký ca](2026-06-17-shift-registration-design.md).

---

## 0. Bối cảnh & quyết định

Gói 4A đã có model `hocba.work_shift` (ca CTV/OT, state pending/approved/rejected) + lịch tuần + duyệt. Gói 4B mở **check-in cho CTV/OT theo ca đã duyệt**, trong cửa sổ **±15'** quanh giờ ca.

Hiện trạng: `api_attendance_check` chặn cứng `emp.x_employment_status != 'official'` → `not_official`; NV official dùng cơ chế khóa Gói 2 (`_assert_check_allowed`: is_workday + 1 lần/ngày). Mô hình **1 bản ghi `hocba.attendance`/NV/ngày**.

### Quyết định đã chốt (tiêu chí khuyến nghị)
- **Cơ chế cửa sổ chỉ cho non-official** (`x_employment_status != 'official'` — CTV/parttime/advisor): check-in/out **chỉ khi** có ca `hocba.work_shift` **approved** hôm nay **và** thời điểm nằm trong **±W phút** quanh `start` (check-in) / `end` (check-out). Thay thế block `not_official`.
- **NV official: GIỮ NGUYÊN** cơ chế workday Gói 2. Ca OT của official phục vụ tính lương (Gói 4C), **không** tạo check-in lần 2 trong ngày (giữ mô hình 1 record/ngày, tránh phá vỡ Gói 1/2). → tránh xung đột "chấm công ngày thường + ca OT tối" cùng 1 record.
- **W = `shift_window_minutes`** trên policy (default 15) — cấu hình được.
- Vẫn áp **1 bản ghi/ngày** cho non-official: đã check-in → `already_checked_in`; check-out cần đã check-in (`not_checked_in`); đã check-out → `already_checked_out`. Mặt face/geo (`_do_check`) giữ nguyên.

### Tái dùng (không viết lại)
- `_do_check` (face/geo + tạo/ghi record), `_assert_check_allowed` (official — Gói 2), `_CHECK_ERR_STATUS` (map lỗi→HTTP), `_att_me_info`, `fields.Datetime.context_timestamp`.

### KHÔNG làm (4C / sau)
- Quy đổi công/lương OT theo hệ số (4C). Nhiều ca/ngày cho 1 NV (nhiều record/ngày). Check-in lần 2 cho official làm OT. Luật lễ/đêm.

---

## 1. Policy — thêm cửa sổ ca (`hocba_attendance`)

File `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`:
- Thêm field `shift_window_minutes = fields.Integer(string='Cửa sổ check-in ca (phút)', default=15, help='CTV/OT được check-in/out trong ±N phút quanh giờ ca đã duyệt.')`.
- Thêm field này vào view `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml` (cạnh các field tính công Gói 1).

---

## 2. Model `hocba.attendance` — guard cửa sổ ca (`hocba_attendance`)

File `custom-addons/hocba_attendance/models/hr_attendance.py`. Thêm method (cạnh `_assert_check_allowed`):

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
        anchor = fields.Datetime.context_timestamp(s, anchor_utc).replace(tzinfo=None)
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

- `action_check_in`/`action_check_out` (RPC entry) **không đổi** — chúng vẫn gọi `_assert_check_allowed`. Việc phân nhánh official↔non-official làm ở **controller** (§3) để giữ logic phạm vi/HTTP một chỗ. (RPC entry chỉ dùng nội bộ; controller là đường vào SPA.)
- `_assert_shift_check_allowed` là method trên model (gọi được từ controller qua `request.env['hocba.attendance']`).

---

## 3. Controller `api_attendance_check` — phân nhánh (`hocba_hrm`)

File `custom-addons/hocba_hrm/controllers/main.py`, method `api_attendance_check`. Hiện tại:
```python
if _user_can_manage(request.env):
    return manager_no_checkin 403
if emp.x_employment_status != 'official':
    return not_official 403
... self._assert_check_allowed → _do_check
```
Đổi nhánh chặn non-official thành phân luồng:
```python
emp = request.env.user.employee_id
if not emp: return no_employee 400
if _user_can_manage(request.env):
    return manager_no_checkin 403
kind = 'out' if path endswith 'check-out' else 'in'
Att = request.env['hocba.attendance']
try:
    if emp.x_employment_status == 'official':
        Att.sudo()._assert_check_allowed(emp, kind)       # Gói 2 (workday)
    else:
        Att.sudo()._assert_shift_check_allowed(emp, kind)  # Gói 4B (ca + cửa sổ)
    res = Att.sudo()._do_check({...payload..., 'employee_id': emp.id}, kind)
except UserError as ex:
    code = str(ex); rollback
    return {'error': code} status=_CHECK_ERR_STATUS.get(code, 400)
return {...res...}
```
- Bỏ hẳn nhánh `not_official`.
- Thêm vào `_CHECK_ERR_STATUS`: `'no_shift_today': 403`, `'outside_shift_window': 403`.
- Lưu ý: hiện controller gọi `action_check_in/out` (RPC) — đổi sang gọi trực tiếp `_assert_*` + `_do_check` để phân luồng official↔non-official mà không nhân đôi logic ở RPC entry. `_do_check` đã tự pin `employee_id` từ payload.

---

## 4. `_att_me_info` — lộ trạng thái ca cho FE (`hocba_hrm`)

File `controllers/main.py`, helper `_att_me_info`. Với **non-official**, thêm key `shiftToday` để FE dựng panel:
```python
# sau khi build info, nếu không official:
if not info['isOfficial']:
    policy = ... ; window = policy.shift_window_minutes or 15
    now_local = context_timestamp(env.user, now).replace(tzinfo=None)
    today = now_local.date()
    shifts = env['hocba.attendance']._todays_approved_shifts(emp, today)
    s = shifts[:1]
    if s:
        ci_anchor = context_timestamp(s, s.start).replace(tzinfo=None)
        co_anchor = context_timestamp(s, s.end).replace(tzinfo=None)
        info['shiftToday'] = {
            'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
            'shiftType': s.shift_type, 'rate': s.rate,
            'checkInOpen': abs((now_local - ci_anchor).total_seconds()) <= window*60,
            'checkOutOpen': abs((now_local - co_anchor).total_seconds()) <= window*60,
        }
    else:
        info['shiftToday'] = None
```
(official: không thêm `shiftToday`, hoặc để `None` — FE chỉ đọc khi `!isOfficial`.) Helper `_todays_approved_shifts` dùng lại từ model (§2).

---

## 5. Frontend — CheckInPanel cho CTV/OT (`frontend/src/features/attendance/`)

File `CheckInPanel.jsx`. Hiện dòng 92-93 chặn cứng `!me.isOfficial` → "chỉ áp dụng cho nhân viên chính thức". Thay bằng nhánh non-official:
- **non-official** (`!me.isOfficial`):
  - Nếu **chưa enroll khuôn mặt** → nút "Đăng ký khuôn mặt" (như official).
  - Nếu `me.shiftToday == null` → thông báo "Chưa có ca làm việc được duyệt hôm nay."
  - Nếu có ca: hiện giờ ca (`start–end`, loại, ×hệ số) + nút Check-in (disable khi `!shiftToday.checkInOpen` hoặc đã check-in) / Check-out (disable khi `!shiftToday.checkOutOpen` hoặc chưa check-in/đã check-out). Dùng lại `doCheck('in'/'out')`.
  - Nhãn khung giờ đổi: thay vì policy window, hiện "Cửa sổ check-in: quanh giờ ca ±15'".
- **official**: giữ nguyên logic hiện có.
- Map thêm mã lỗi trong `doCheck` catch `M`: `no_shift_today: 'Chưa có ca được duyệt hôm nay.'`, `outside_shift_window: 'Ngoài cửa sổ check-in của ca (±15 phút).'`.
- Build SPA.

---

## 6. Kiểm thử

### Backend — `custom-addons/hocba_hrm/tests/test_shift_checkin.py` (TransactionCase)
Test method model `_assert_shift_check_allowed` + `_todays_approved_shifts` (gọi trực tiếp; dựng now bằng cách tạo ca quanh thời điểm test — dùng `freeze`/`patch` hoặc tạo ca có start = now ± nhỏ). Cách thực dụng: tạo ca approved với `start`/`end` tính từ `fields.Datetime.now()` để now nằm trong/ngoài cửa sổ.
- **CTV có ca approved, now trong cửa sổ check-in** → không raise; sau đó check-out trong cửa sổ end → không raise.
- **CTV không có ca hôm nay** → `no_shift_today`.
- **CTV có ca nhưng now ngoài ±15'** → `outside_shift_window`.
- **CTV đã check-in** (tạo record) rồi check-in lại → `already_checked_in`; check-out khi chưa check-in → `not_checked_in`; đã check-out → `already_checked_out`.
- **Ca pending/rejected không tính** → `no_shift_today`.
- **Official KHÔNG dùng cơ chế ca**: `_assert_check_allowed` vẫn hoạt động (regression — official có thể bị `not_workday` ngoài ngày làm; đây là Gói 2, chỉ cần xác nhận controller phân nhánh đúng — test ở tầng controller helper nếu khả thi, hoặc khẳng định bằng test riêng cho `_assert_shift_check_allowed` chỉ áp non-official).
- Fixture official cần CCCD 12 số (BR-010); CTV không cần.
- Giờ UTC; test set tz context.

### Frontend (thủ công)
- CTV có ca duyệt hôm nay (quanh giờ hiện tại): panel hiện nút check-in mở; bấm → chấm công. Ngoài cửa sổ → nút khóa / báo "ngoài cửa sổ". Không có ca → báo "chưa có ca".
- Official: không đổi.
- Build SPA sạch.

---

## 7. Phạm vi

**Có làm (4B):** `shift_window_minutes` (policy + view); `_todays_approved_shifts` + `_assert_shift_check_allowed` (model); phân nhánh `api_attendance_check` (official↔non-official) + bỏ `not_official` + map lỗi mới; `_att_me_info.shiftToday`; FE CheckInPanel cho CTV/OT + map lỗi; test backend.

**KHÔNG làm (4C / sau):** tính công/lương OT theo hệ số (4C); nhiều ca/ngày; check-in lần 2 cho official OT; luật lễ/đêm.
