# Thiết kế — Gói 4A: Đăng ký & duyệt ca làm việc (lịch tuần)

**Ngày:** 17/06/2026 · **Trạng thái:** chờ duyệt
**Phạm vi:** `hocba_attendance` (model + ACL mới), `hocba_hrm/controllers/main.py` (API), frontend `frontend/src/features/attendance/`.
**Spec liên quan:** Gói 1 [tính công](2026-06-17-attendance-work-credit-design.md), Gói 2 [tách tài khoản + khóa](2026-06-17-attendance-account-split-lock-design.md), Gói 3 [đơn chấm công](2026-06-17-attendance-correction-request-design.md).

---

## 0. Bối cảnh & lộ trình

Gói 4 (cuối của lộ trình nâng cấp chấm công) làm cơ chế **ca làm việc cho CTV/OT**. Yêu cầu gốc từ khách: CTV và NV làm OT tự đăng ký ca, hiển thị **lịch theo tuần**; manager thêm/duyệt ca; ca chỉ hiển thị (cho người khác) sau khi duyệt; check-in trong **cửa sổ ±15'** quanh giờ ca; OT có **hệ số** (150/200/300%) tính công/lương.

Vì lớn, Gói 4 tách thành 3 gói con phụ thuộc:
- **4A (spec này)** — Đăng ký & duyệt ca + lịch tuần.
- **4B** — Check-in theo ca (cửa sổ ±15') cho CTV/OT. Phụ thuộc 4A.
- **4C** — Tính công/lương OT theo hệ số + luật lễ/đêm, gộp vào tổng hợp tháng. Phụ thuộc 4A.

### Quyết định đã chốt (qua brainstorming)
- **Model ca riêng** `hocba.work_shift` (không nhồi vào `hocba.attendance.request`). Câu "vẫn dùng luồng đơn Gói 3" = đơn *sửa chấm công* cho ngày có ca vẫn đi qua Gói 3; đăng ký ca là model riêng.
- **Loại ca chọn tay** khi đăng ký: `ctv` | `ot`.
- **Hệ số auto theo luật** (4A: T2–T6 = 1.5, T7/CN = 2.0; lễ/đêm để 4C), **manager sửa được** khi duyệt.
- **Lịch tuần dạng lưới 7 cột** (T2→CN), ca là chip trong cột ngày.
- **Hiển thị:** owner thấy ca của mình **mọi state**; người khác/đồng nghiệp chỉ thấy ca **approved** trong phạm vi vai trò.
- **Manager thêm ca hộ** NV trong phạm vi → vào **thẳng `approved`**.

### Tái dùng từ Gói 1-3 (không viết lại)
- `_to_utc(env, s)` (local ISO → UTC), `_dt_local(rec, dt)` (UTC → local ISO).
- `_user_can_manage(env)`, `_emp_scope_domain(env)`, `_emp_in_scope(env, emp)` — phạm vi/quyền.
- Pattern endpoint + map lỗi của Gói 3 (`forbidden`/403, `not_found`/404, `rejected`+message/400, `already_decided`/400, `no_employee`/400).

---

## 1. Model `hocba.work_shift` (addon `hocba_attendance`)

File mới `custom-addons/hocba_attendance/models/hocba_work_shift.py`, đăng ký trong `models/__init__.py`.

| Field | Kiểu | Ghi chú |
|---|---|---|
| `employee_id` | Many2one `hr.employee`, required, ondelete cascade, index | NV của ca |
| `start` | Datetime, required | Giờ bắt đầu ca (lưu UTC) |
| `end` | Datetime, required | Giờ kết thúc ca (lưu UTC) |
| `shift_type` | Selection `ctv`/`ot`, required | Chọn tay khi đăng ký |
| `rate` | Float, default 1.0 | Hệ số (1.0/1.5/2.0/3.0). Khi tạo: gợi ý từ `_default_rate(start)`; manager sửa được. |
| `state` | Selection `pending`/`approved`/`rejected`, default `pending`, index | |
| `reason` | Text | Lý do/ghi chú người đăng ký |
| `reviewer_id` | Many2one `res.users`, readonly | Người duyệt |
| `review_note` | Text | Ghi chú duyệt/từ chối |
| `decision_date` | Datetime, readonly | Lúc quyết định |
| `department_id` | Many2one `hr.department`, related `employee_id.department_id`, store, readonly | Lọc theo phạm vi |

- `_order = 'start desc'`.
- **Constraint `_check_times`** (`@api.constrains('start','end')`): `end > start` → nếu sai raise `ValidationError('Giờ kết thúc phải sau giờ bắt đầu.')`.
- **Constraint chống trùng giờ** `_check_overlap` (`@api.constrains('start','end','employee_id','state')`): với ca cùng `employee_id`, state ∈ {pending, approved}, khoảng `[start,end)` không được giao nhau với ca khác (id != self) cùng NV & state ∈ {pending, approved}. Vi phạm → raise `ValidationError('Ca bị trùng giờ với ca khác.')`. (Logic giao nhau: `other.start < self.end and other.end > self.start`.)
- ACL `ir.model.access.csv`: `hr.group_hr_user` → read/write/create (no unlink); `hr.group_hr_manager` → full. Phạm vi thực thi ở controller + ghi `sudo`.
- **Method `_default_rate(self, start_dt)`** (model, `@api.model`): trả Float hệ số gợi ý theo thứ trong tuần của `start_dt` (đã là datetime UTC; lấy weekday theo local tz của context để đúng ngày VN): thứ 2–6 → 1.5; thứ 7/CN → 2.0. (Lễ/đêm: 4C.)

---

## 2. Backend API (controller `hocba_hrm/controllers/main.py`)

### 2.1 Helper `_shift_row(s)` — wire camelCase
```jsonc
{
  "id": 12, "empId": 7, "empName": "Trần Thị B", "code": "GV002",
  "depName": "Tiếng Trung",
  "start": "2026-06-15T18:00:00",   // local ISO
  "end": "2026-06-15T20:30:00",
  "shiftType": "ot",                // ctv | ot
  "rate": 1.5,
  "state": "pending",               // pending | approved | rejected
  "reason": "Dạy bù lớp tối",
  "reviewer": "Trần Quản Lý" | null,
  "reviewNote": null,
  "decisionDate": null
}
```
Dùng `_dt_local(s, s.start/s.end/s.decision_date)` cho các datetime.

### 2.2 Helper `_shift_create(env, body)` — user đăng ký / manager thêm hộ
- `body`: `{start, end, shiftType, reason?, empId?}`.
- Xác định NV mục tiêu:
  - Mặc định pin về `env.user.employee_id` (chống giả mạo). Thiếu hồ sơ NV → trả `None` (controller map `no_employee`).
  - Nếu `empId` được gửi **và** người gọi `_user_can_manage(env)` **và** `_emp_in_scope(env, emp)` → tạo hộ cho NV đó, `state='approved'`, `reviewer_id=env.user.id`, `decision_date=now`. Ngược lại bỏ qua `empId`, pin về chính mình, `state='pending'`.
- `shiftType` không thuộc {ctv, ot} → `ValidationError('Loại ca không hợp lệ.')`.
- Giờ local→UTC qua `_to_utc`. `start`/`end` rỗng → `ValidationError`.
- `rate = env['hocba.work_shift']._default_rate(start_utc)`.
- `sudo().create(...)` (constraint `_check_times`/`_check_overlap` của model tự áp; ValidationError sẽ propagate). Trả `_shift_row`.

### 2.3 Helper `_shifts_week(env, monday_str)` — dữ liệu lịch tuần
- Xác định tuần: nếu `monday_str` rỗng → tuần chứa hôm nay; chuẩn hóa về **thứ 2** của tuần đó (theo local). 7 ngày T2→CN.
- Khoảng UTC: `[monday 00:00 local, monday+7d 00:00 local)` → đổi sang UTC để lọc `start`.
- Domain:
  - Ca của **chính mình** (mọi state): `('employee_id','=',my_emp.id)`.
  - Ca **approved** trong phạm vi vai trò: `('state','=','approved')` + `_emp_scope_domain` prefix `employee_id.` (như Gói 2/3). Non-canManage & không có emp → chỉ ca của mình.
  - Hợp 2 domain bằng OR (`expression.OR`) — owner luôn thấy ca mình; người quản lý thấy thêm ca approved trong phạm vi.
- Gom theo ngày local. Trả:
```jsonc
{ "weekStart": "2026-06-15", "canManage": true,
  "days": [ {"date":"2026-06-15","weekday":"T2","shifts":[ _shift_row... ]}, ... 7 phần tử ] }
```

### 2.4 Helper `_shift_decide(env, shift_id, approve, body)` — manager duyệt/từ chối
- `sudo().browse(shift_id)`; không tồn tại → `None`.
- Kiểm `_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)`; sai → `AccessError('forbidden')`.
- `state != 'pending'` → `UserError('already_decided')`.
- `vals = {reviewer_id, decision_date=now, review_note}`.
- Nếu approve: override nếu body có key — `start`/`end` (qua `_to_utc`), `shiftType` (validate), `rate` (float); rồi `state='approved'`. (Đổi giờ → constraint overlap/time tự áp.)
- Nếu reject: `state='rejected'`.
- `write(vals)`; trả `_shift_row`.

### 2.5 Helper `_shift_cancel(env, shift_id)` — hủy ca pending
- `sudo().browse`; không tồn tại → `None`.
- Quyền hủy: owner (`shift.employee_id == env.user.employee_id`) **hoặc** (`_user_can_manage` và `_emp_in_scope`). Sai → `AccessError('forbidden')`.
- `state != 'pending'` → `UserError('only_pending')` (chỉ hủy ca chờ duyệt).
- `unlink()`; trả `{'ok': True}`.

### 2.6 Endpoints (`auth='user'`, type='http'; POST có csrf=False)
- `POST /hocba-hrm/api/shifts` → `_shift_create`. None → `no_employee` 400; ValidationError → `rejected`+message 400 (gồm overlap/giờ sai/loại sai).
- `GET /hocba-hrm/api/shifts/week?monday=YYYY-MM-DD` → `{...}` của `_shifts_week`.
- `POST /hocba-hrm/api/shifts/<int:shift_id>/approve` → `_shift_decide(...,True)`.
- `POST /hocba-hrm/api/shifts/<int:shift_id>/reject` → `_shift_decide(...,False)`.
- `POST /hocba-hrm/api/shifts/<int:shift_id>/cancel` → `_shift_cancel`.
- Map lỗi (thứ tự except: AccessError → ValidationError → UserError, vì ValidationError là lớp con UserError): `forbidden`/403, `not_found`/404, `rejected`+message/400, `already_decided`/400, `only_pending`/400.
- Route literal `shifts`/`shifts/week` không đụng `<int:shift_id>` (không phải số).

---

## 3. Frontend (`frontend/src/features/attendance/`)

### 3.1 `api/attendance.js`
Thêm: `fetchWeekShifts(monday)` (GET), `createShift(body)`, `approveShift(id, body)`, `rejectShift(id, body)`, `cancelShift(id)`.

### 3.2 Component mới
- **`ShiftCalendar.jsx`** — lưới 7 cột (T2→CN). Header: nút **‹ / ›** chuyển tuần + nhãn khoảng ngày tuần. Mỗi cột ngày: liệt kê chip ca (giờ `start–end`, badge loại CTV/OT + hệ số `×1.5`, màu theo state: amber=pending, green=approved, red=rejected). Click chip → mở `ShiftDrawer`. State tuần hiện tại (Monday) + loading/error; refetch khi đổi tuần.
- **`ShiftForm.jsx`** — form đăng ký ca: ngày + giờ vào/ra (`datetime-local`), loại ca (select CTV/OT), lý do. Gửi qua `createShift`; lỗi hiện message; onSaved → refetch tuần + đóng.
- **`ShiftDrawer.jsx`** — chi tiết 1 ca. Owner (`!canManage` hoặc ca của mình): xem trạng thái + ghi chú duyệt; nếu pending → nút **Hủy** (`cancelShift`). Manager (`canManage` + ca pending): input override giờ/loại/hệ số + **Duyệt** / **Từ chối** (ô note). Sau thao tác → refetch + đóng.

### 3.3 `Attendance.jsx`
- Tab `ot`: đổi nhãn → **"Ca làm việc (CTV/OT)"**, render `ShiftCalendar` thay `OtMock`. Có nút **"Đăng ký ca"** mở `ShiftForm` (cho mọi vai trò — manager đăng ký ca của chính mình; thêm hộ NV làm ở 4A sau qua API, FE 4A chỉ cần đăng ký cho mình + duyệt).
- Tab này hiện cho **cả user lẫn manager** (user: xem lịch + đăng ký ca mình; manager: thêm xem ca approved trong phạm vi + duyệt qua drawer).

### 3.4 `mock.js`
Bỏ `OT_LOG` (và `OtMock` trong `Attendance.jsx`). Sau Gói 4A, `mock.js` không còn dữ liệu mock nào → xóa file `mock.js` và gỡ import `USE_MOCK`/`MockBanner` nếu không còn nơi dùng. (Kiểm tra `grep` trước khi xóa.)

---

## 4. Kiểm thử

### Backend — `custom-addons/hocba_hrm/tests/test_shift_api.py` (helper module-level, TransactionCase)
- **Tạo ca:** pin `employee_id` = user; `start`/`end` local→UTC đúng; `state=pending`; `rate` default đúng (ngày T2–6 → 1.5, T7/CN → 2.0 — chọn ngày cố định để test).
- **end ≤ start** → ValidationError. **Overlap** cùng NV (pending/approved) → ValidationError.
- **Lịch tuần:** owner thấy ca pending của mình; NV khác chỉ thấy ca approved; trưởng phòng thấy ca approved của phòng mình, không thấy ngoài phòng; HR Manager thấy tất cả approved. 7 ngày trả đúng, gom theo ngày local.
- **Manager thêm ca hộ** NV trong phạm vi (`empId`) → `state=approved`, reviewer set. Ngoài phạm vi `empId` → bị bỏ qua, pin về chính người gọi (hoặc, nếu người gọi không là manager, luôn pin về mình).
- **Approve** (override hệ số/giờ) → `state=approved`, reviewer, rate mới áp. **Reject** + note. Ngoài phạm vi → AccessError. already_decided.
- **Cancel:** owner hủy ca pending của mình → ok, ca biến mất. Hủy ca approved → `only_pending`. Ngoài phạm vi → AccessError.
- Fixture NV official cần `identification_id` 12 số (BR-010 — xem memory `br010-official-employee-cccd`).
- Giờ lưu UTC; test truyền UTC với `.with_context(tz='Asia/Ho_Chi_Minh')`.

### Frontend (thủ công)
- User: đăng ký ca → chip amber trong lịch tuần; chuyển tuần trước/sau; hủy ca pending.
- Manager: thấy ca approved trong phạm vi; mở drawer ca pending → chỉnh hệ số/giờ → Duyệt (chip green) / Từ chối (chip red, note). Thêm ca hộ NV (qua API) vào thẳng approved.
- Build SPA sạch.

---

## 5. Phạm vi

**Có làm (4A):** model `hocba.work_shift` + ACL + constraint (time/overlap) + `_default_rate`; helper `_shift_row/_shift_create/_shifts_week/_shift_decide/_shift_cancel` + 5 endpoint với kiểm phạm vi & duyệt-thì-áp-dụng; FE `ShiftCalendar`/`ShiftForm`/`ShiftDrawer`, tab "Ca làm việc (CTV/OT)" thật thay `OtMock`; bỏ `OT_LOG` mock; test backend.

**KHÔNG làm (4B / 4C / sau):**
- Check-in cửa sổ ±15' quanh giờ ca cho CTV/OT (4B) — mở `api_attendance_check` cho CTV/OT theo ca approved + cửa sổ; khác cơ chế ngày-làm-việc của NV official (Gói 2).
- Quy đổi công/lương OT theo hệ số vào tổng hợp tháng + luật lễ/đêm/+30% đêm (4C).
- Lịch lặp (recurring shift), thông báo mail/activity, payroll thật.
- Đơn sửa chấm công cho ngày có ca vẫn dùng luồng Gói 3 (không làm lại ở đây).
