# Thiết kế — Gói 2: Tách tài khoản manager/user + khóa check-in/out + manager sửa/xóa

**Ngày:** 17/06/2026 · **Trạng thái:** chờ duyệt
**Phạm vi:** `hocba_hrm/controllers/main.py` (API chấm công), `hocba_attendance` (action check-in/out nếu cần), frontend `frontend/src/features/attendance/`.
**Spec liên quan:** [2026-06-13-attendance-spa-screen-design.md](2026-06-13-attendance-spa-screen-design.md), [2026-06-17-attendance-work-credit-design.md](2026-06-17-attendance-work-credit-design.md) (Gói 1).

---

## 0. Bối cảnh & lộ trình

Gói 2 của lộ trình nâng cấp chấm công (4 gói). Gói 1 (tính công) đã xong và merge. Gói 2 làm:
- Tách rõ **tài khoản manager** (chỉ quản lý, không check-in) ↔ **user** (tự chấm công).
- **Khóa** check-in/out: 1 lần/ngày, chỉ ngày làm việc; bấm xong khóa nút (enforce ở backend, không chỉ ẩn nút).
- **Manager sửa/xóa** bản ghi attendance của user trong phạm vi mình quản lý.

Gói 3 (luồng đơn user→manager) và Gói 4 (đăng ký ca CTV/OT + cửa sổ ±15') KHÔNG thuộc spec này.

### Quyết định đã chốt

- **Manager = mọi nhóm quản lý** (`canManage` trong `_role_payload`: Admin / HR Manager / HR officer / Giáo vụ / Trưởng phòng) → UI quản lý, **không** check-in/out.
- **User = NV thường + CTV** (không `canManage`) → UI tự chấm công.
- **Manager sửa** `check_in`/`check_out` + `notes` (công tự tính lại), **xóa** cả bản ghi; **theo phạm vi** `_emp_scope_domain` (trưởng phòng→phòng mình, giáo vụ→giáo viên, HR Manager/Admin→tất cả); xác nhận trước khi xóa.

### Hiện trạng (đã đọc code)

- `api_attendance_check` chỉ chặn `x_employment_status != 'official'` → manager (cũng là NV official) hiện vẫn check-in được; chưa khóa 1 lần/ngày; chưa chặn ngày nghỉ.
- `action_check_in`/`action_check_out` gắn employee = user hiện tại rồi gọi `_do_check` dưới `sudo`. `_do_check` giữ `check_in` gốc khi check-in lại và **ghi đè** `check_out` khi check-out lại.
- `_role_payload` đã có `canManage` + các cờ vai trò; `_emp_scope_domain`/`_emp_in_scope`/`_managed_department_ids` đã có (đang dùng cho danh sách NV & duyệt cổng).
- `_att_day_table` hiện chỉ phân biệt `hr.group_hr_user`/`hr.group_hr_manager` (tất cả) ↔ user thường (của mình) — **chưa** xử lý trưởng phòng/giáo vụ theo phạm vi.
- FE đã có `CheckInPanel`, `MyHistory`, `AttendanceTable`, `AttendanceDrawer`, `Attendance.jsx`, `api/attendance.js`.

---

## 1. Backend — chặn & khóa check-in/out

Model `_do_check` giữ nguyên (cơ chế face/geo). Enforce ở tầng action + controller:

1. **Chặn manager** — trong `api_attendance_check` (controller), nếu user `canManage` → `{"error":"manager_no_checkin"}` HTTP 403. (Kiểm bằng `_role_payload()['canManage']` hoặc gọi trực tiếp các `has_group`.)
2. **Chỉ ngày làm việc** — trong `action_check_in`/`action_check_out` (model `hocba.attendance`), tính `today_local` theo tz user; nếu `not policy.is_workday(today_local)` → `UserError`/trả lỗi `not_workday` (HTTP 403 ở controller).
3. **Một lần/ngày:**
   - check-in: nếu bản ghi hôm nay đã có `check_in` → lỗi `already_checked_in`.
   - check-out: nếu chưa có bản ghi/`check_in` hôm nay → lỗi `not_checked_in`; nếu đã có `check_out` → lỗi `already_checked_out`.

Cách hiện thực: `action_check_in`/`action_check_out` tìm bản ghi hôm nay (như `_do_check` đang làm), kiểm điều kiện, raise `UserError` với mã rõ ràng nếu vi phạm, rồi mới gọi `_do_check`. Controller `api_attendance_check` bắt `UserError`, map message→`error` code + HTTP 403, đồng thời chặn manager trước khi gọi action.

`_do_check` không đổi để các test gọi trực tiếp `_do_check` (vd `test_attendance_api._checkin`) không vỡ; ràng buộc 1-lần/ngày nằm ở action layer (đường đi thật của SPA).

4. **`_att_me_info`** trả thêm:
   - `canManage` (bool) — FE chọn UI.
   - `isWorkdayToday` (bool) — `policy.is_workday(today_local)`.
   (Giữ `enrolled`, `isOfficial`, `isHr`, `isHrManager`, `policy`, `today` như cũ. `today.checkIn`/`today.checkOut` dùng để khóa nút.)

### Mã lỗi (controller → FE)

| error | HTTP | Khi nào |
|---|---|---|
| `manager_no_checkin` | 403 | user `canManage` gọi check-in/out |
| `not_workday` | 403 | hôm nay không phải ngày làm việc |
| `already_checked_in` | 409 | đã check-in hôm nay |
| `not_checked_in` | 409 | check-out khi chưa check-in |
| `already_checked_out` | 409 | đã check-out hôm nay |
| `not_official` | 403 | (giữ) NV không chính thức |
| `no_employee` | 400 | (giữ) user chưa gắn hồ sơ |

---

## 2. Backend — manager sửa/xóa + phạm vi bảng ngày

### 2.1 `_att_day_table` theo phạm vi
Đổi logic phạm vi sang dùng `_emp_scope_domain()` (đang dùng cho `/api/employees`):
- HR/Admin → tất cả; trưởng phòng → phòng mình (+ phòng con); giáo vụ → giáo viên; user thường → chỉ của mình.
- Cụ thể: nếu `canManage` → domain = `_emp_scope_domain()` áp lên `employee_id`; ngược lại → `employee_id = user.employee_id`.
- Response thêm `canManage` (FE hiển thị nút sửa/xóa). Giữ `isHr`/`isHrManager`/`counts`/`rows`/`policy`. `counts.missing` chỉ tính cho HR/Admin (giữ như cũ; trưởng phòng có thể bỏ qua hoặc tính theo scope — giữ đơn giản: chỉ HR/Admin).

### 2.2 API sửa bản ghi
`POST /hocba-hrm/api/attendance/<int:rec_id>` (auth='user', csrf=False):
- Body: `{"checkIn": "2026-06-17T08:05", "checkOut": "2026-06-17T17:10" | null, "notes": "..."}` — datetime **local** ISO (không giây cũng được) hoặc null để xóa giờ ra.
- Kiểm quyền: phải `canManage` **và** `_emp_in_scope(rec.employee_id)`; nếu không → 403 (`forbidden`).
- Chuyển local→UTC theo `env.user.tz` (helper mới `_to_utc(env, s)`), `sudo().write({...})`. Bỏ qua key không gửi.
- Trả về row đã cập nhật (`_att_row`) — `work_credit`/`missing_minutes`/... tự tính lại do `@api.depends`.
- Không tồn tại → 404; lỗi ràng buộc (check_out < check_in) → 400 với message.

### 2.3 API xóa bản ghi
`POST /hocba-hrm/api/attendance/<int:rec_id>/delete` (auth='user', csrf=False):
- Cùng kiểm quyền (`canManage` + `_emp_in_scope`). → `sudo().unlink()` → `{"ok": true}`. Không tồn tại → 404; ngoài quyền → 403.

### 2.4 Helper datetime local→UTC
```python
from pytz import timezone, utc
def _to_utc(env, s):
    """Chuỗi datetime local ('YYYY-MM-DDTHH:MM[:SS]') -> Datetime UTC naive.
    None/'' -> False."""
    if not s:
        return False
    naive_local = fields.Datetime.to_datetime(s.replace('T', ' '))
    tz = timezone(env.user.tz or 'UTC')
    return tz.localize(naive_local).astimezone(utc).replace(tzinfo=None)
```

---

## 3. Frontend (`frontend/src/features/attendance/`)

### 3.1 `api/attendance.js`
Thêm:
- `editAttendance(id, body)` → `POST /api/attendance/<id>`.
- `deleteAttendance(id)` → `POST /api/attendance/<id>/delete`.

### 3.2 `Attendance.jsx` — tách UI theo `me.canManage`
- **Manager** (`me.canManage`): tabs `[['day','Bảng chấm công'],['forgot','Đơn quên chấm công'],['ot','Tăng ca (OT)']]`, mặc định `day`. Không render `CheckInPanel`/`MyHistory`.
- **User**: chỉ tab `me` → `CheckInPanel` + `MyHistory`.
- Thay `const isStaff = me.isHr || me.isHrManager;` → `const isManager = me.canManage;` và dựng tabs theo đó. (Tab mặc định: manager=`day`, user=`me`.)

### 3.3 `CheckInPanel.jsx` — khóa nút
- Đọc `me.isWorkdayToday`, `t = me.today`.
- `!isWorkdayToday` → thông báo "Hôm nay không phải ngày làm việc — không điểm danh", ẩn 2 nút.
- **Check-in** disable nếu: `busy || !ready || !isWorkdayToday || !!t?.checkIn`. Khi `t?.checkIn` → hiện "Đã check-in lúc {HH:MM}" thay nút.
- **Check-out** disable nếu: `busy || !ready || !t?.checkIn || !!t?.checkOut`. Khi `t?.checkOut` → hiện "Đã check-out lúc {HH:MM}".
- Bắt lỗi BE: map `manager_no_checkin`/`not_workday`/`already_checked_in`/`not_checked_in`/`already_checked_out` → thông điệp tiếng Việt thân thiện (không crash). Sau lỗi/clxong → `onChanged()` refetch.

### 3.4 `AttendanceTable.jsx` + `AttendanceDrawer.jsx` — manager sửa/xóa
- `AttendanceTable` truyền cờ `canManage` (từ `data.canManage`) + callback refetch xuống `AttendanceDrawer`.
- `AttendanceDrawer`: khi `canManage`, footer có **Sửa** & **Xóa**.
  - **Sửa**: chuyển drawer sang chế độ form với 3 input — `check_in` (`datetime-local`), `check_out` (`datetime-local`), `notes` (textarea); nút Lưu gọi `editAttendance(rec.id, {checkIn, checkOut, notes})` rồi đóng + refetch.
  - **Xóa**: xác nhận ("Xóa bản ghi chấm công ngày … của …?") → `deleteAttendance(rec.id)` → đóng + refetch.
  - Giá trị `datetime-local` lấy từ `rec.checkIn`/`rec.checkOut` (ISO local sẵn) cắt còn `YYYY-MM-DDTHH:MM`.
- User thường: drawer read-only như hiện tại (không có nút).

---

## 4. Kiểm thử

### Backend (`hocba_hrm/tests/test_attendance_api.py` mở rộng)
- **Chặn/khóa:** manager (user có `hr.group_hr_manager`) gọi check-in → `manager_no_checkin`/403. Ngày nghỉ → `not_workday`. check-in lần 2 cùng ngày → `already_checked_in`. check-out khi chưa check-in → `not_checked_in`. check-out lần 2 → `already_checked_out`. (Test ở tầng action/controller; dùng tz `Asia/Ho_Chi_Minh` + ngày là workday/không workday theo policy.)
- **`_att_me_info`:** trả `canManage` đúng (manager True, user False) + `isWorkdayToday`.
- **`_att_day_table` phạm vi:** trưởng phòng (department.manager_id, không group HR) chỉ thấy NV phòng mình; HR Manager thấy tất cả; user thường thấy của mình; response có `canManage`.
- **Sửa:** manager trong phạm vi sửa `check_in`/`check_out` → bản ghi cập nhật + `work_credit`/`missing_minutes` tính lại đúng; ngoài phạm vi → 403; user non-canManage → 403; record không tồn tại → 404.
- **Xóa:** trong phạm vi xóa OK (`ok:true`, bản ghi mất); ngoài phạm vi → 403.
- Fixture official cần `identification_id` 12 số (BR-010 — xem memory).

### Frontend (thủ công)
- Đăng nhập manager (trưởng phòng & HR Manager): thấy "Bảng chấm công" theo phạm vi, sửa/xóa hoạt động + refetch; không có panel check-in.
- Đăng nhập user official: panel khóa đúng (đã check-in → khóa check-in; chưa check-in → khóa check-out; ngày nghỉ → ẩn). CTV (không official): giữ nguyên thông báo hiện có "Chức năng điểm danh chỉ áp dụng cho nhân viên chính thức" — check-in CTV theo ca làm ở **Gói 4**, KHÔNG mở ở Gói 2.
- Build SPA sạch, không lỗi console.

---

## 5. Phạm vi

**Có làm:** chặn manager check-in (BE 403); chỉ ngày làm việc; khóa 1 lần/ngày (BE enforce ở action layer); `canManage`+`isWorkdayToday` trong `_att_me_info`; `_att_day_table` theo `_emp_scope_domain` + `canManage`; 2 API sửa/xóa attendance có kiểm phạm vi; helper `_to_utc`; tách UI manager/user trong `Attendance.jsx`; khóa nút trong `CheckInPanel`; sửa/xóa trong `AttendanceDrawer`/`AttendanceTable`; `editAttendance`/`deleteAttendance` ở api; test backend.

**KHÔNG làm (gói sau):** luồng đơn user→manager (Gói 3); đăng ký ca CTV/OT + cửa sổ check-in ±15' (Gói 4); manager **tạo** bản ghi thủ công; đổi 2 tab mock forgot/ot (giữ nguyên); đổi logic face/geo/window của `_do_check`; đổi payroll.
