# Thiết kế — Gói 3: Luồng đơn chấm công (user gửi → manager duyệt & sửa)

**Ngày:** 17/06/2026 · **Trạng thái:** chờ duyệt
**Phạm vi:** `hocba_attendance` (model + ACL mới), `hocba_hrm/controllers/main.py` (API), frontend `frontend/src/features/attendance/`.
**Spec liên quan:** Gói 1 [tính công](2026-06-17-attendance-work-credit-design.md), Gói 2 [tách tài khoản + khóa](2026-06-17-attendance-account-split-lock-design.md).

---

## 0. Bối cảnh & lộ trình

Gói 3/4 của lộ trình nâng cấp chấm công. Gói 1 (tính công) + Gói 2 (tách tài khoản manager/user, khóa check-in/out, manager sửa/xóa) đã xong & merge. Gói 3 làm **luồng đơn**: user gửi đơn xin sửa/tạo bản ghi chấm công cho 1 ngày; manager duyệt (có thể chỉnh giờ) → áp dụng vào bản ghi, hoặc từ chối. Thay tab mock "Đơn quên chấm công" bằng luồng thật.

Gói 4 (đăng ký ca CTV/OT + cửa sổ check-in ±15') KHÔNG thuộc spec này.

### Quyết định đã chốt
- **Đơn bao trùm 2 trường hợp:** (a) sửa bản ghi đã có; (b) ngày làm việc chưa có bản ghi (quên chấm cả ngày) → duyệt xong **tạo** bản ghi.
- **Luồng duyệt:** user nhập giờ đề xuất + lý do → manager xem, **chỉnh được giờ đề xuất** rồi Duyệt (ghi/tạo bản ghi, công tự tính lại) hoặc Từ chối kèm lý do.
- Model gọn, **không** mail.thread/chatter (SPA hiển thị danh sách pending là đủ).

### Tái dùng từ Gói 1-2 (không viết lại)
- `_to_utc(env, s)` — chuỗi datetime local → UTC naive.
- `_user_can_manage(env)`, `_emp_in_scope(env, emp)`, `_emp_scope_domain(env)` — phạm vi/quyền.
- `_att_row`, các field tính công store (`work_credit`, `missing_minutes`...) tự tính lại khi ghi `check_in`/`check_out`.
- Quyền & UI: manager = `canManage`; user = không `canManage`.

---

## 1. Model `hocba.attendance.request` (addon `hocba_attendance`)

File mới `custom-addons/hocba_attendance/models/hocba_attendance_request.py`, đăng ký trong `models/__init__.py`.

| Field | Kiểu | Ghi chú |
|---|---|---|
| `employee_id` | Many2one `hr.employee`, required, ondelete cascade, index | NV gửi đơn |
| `request_date` | Date, required | Ngày công cần sửa/tạo |
| `attendance_id` | Many2one `hocba.attendance`, ondelete='set null' | Bản ghi đính kèm; rỗng = ngày thiếu |
| `proposed_check_in` | Datetime | Giờ vào đề xuất (lưu UTC) |
| `proposed_check_out` | Datetime | Giờ ra đề xuất (lưu UTC) |
| `reason` | Text, required | Lý do user nêu |
| `state` | Selection `pending`/`approved`/`rejected`, default `pending`, index | |
| `reviewer_id` | Many2one `res.users`, readonly | Người duyệt |
| `review_note` | Text | Ghi chú khi duyệt/từ chối |
| `decision_date` | Datetime, readonly | Lúc quyết định |
| `department_id` | Many2one `hr.department`, related `employee_id.department_id`, store | Lọc/hiển thị |

- `_order = 'create_date desc'`.
- ACL `ir.model.access.csv`: `hr.group_hr_user` → read/write/create (no unlink); `hr.group_hr_manager` → full. (Giống `access_hocba_attendance_*`.) Phạm vi thực thi ở controller + ghi `sudo`.
- Không thêm constraint chéo check_in/out trên model đơn — ràng buộc thật áp khi ghi vào `hocba.attendance` (model đó đã có `_check_dates`).

---

## 2. Backend API (controller `hocba_hrm/controllers/main.py`)

### 2.1 Helper `_req_row(req)` — wire camelCase
```jsonc
{
  "id": 7, "empId": 12, "empName": "Nguyễn Văn A", "code": "NV010",
  "depName": "Hành chính", "requestDate": "2026-06-12",
  "attendanceId": 88,            // null nếu đơn cho ngày thiếu
  "checkIn": "2026-06-12T08:10:00",  // giờ đề xuất local ISO, null nếu không đề xuất
  "checkOut": null,
  "reason": "Điện thoại hết pin",
  "state": "pending",            // pending | approved | rejected
  "reviewer": "Trần Quản Lý" | null,
  "reviewNote": null,
  "decisionDate": null
}
```
Helper `_to_local_dt(rec, dt)` đã có (`_dt_local`); dùng cho `checkIn`/`checkOut`/`decisionDate`.

### 2.2 Helper module-level `_request_apply(env, req, check_in_utc, check_out_utc)`
Áp đơn đã duyệt vào bản ghi (dùng chung cho approve):
- Nếu `req.attendance_id`: `vals` = các giờ được cung cấp (không None bỏ qua) → `req.attendance_id.sudo().write(vals)`; trả bản ghi.
- Nếu không: tìm `hocba.attendance` cho (`employee_id`, `date = request_date`). Nếu có → write giờ. Nếu không → cần `check_in_utc` (bắt buộc để tạo) → `create({employee_id, check_in, check_out})`; thiếu `check_in_utc` → `ValidationError('Cần giờ check-in để tạo bản ghi.')`. Gán `req.attendance_id` = bản ghi.

### 2.3 Endpoints (`auth='user'`, type='http')
- `POST /hocba-hrm/api/attendance/requests` — **user tạo đơn**.
  - Body `{requestDate, attendanceId?, checkIn?, checkOut?, reason}`.
  - `employee = request.env.user.employee_id` (pin, chống giả mạo); thiếu hồ sơ → 400 `no_employee`; `reason` rỗng → 400 `rejected` ("Cần lý do").
  - Giờ local→UTC qua `_to_utc`. `attendance_id`: nếu gửi mà bản ghi không thuộc về employee của user → 400 `rejected`. `sudo().create(...)`. Trả `_req_row`.
- `GET /hocba-hrm/api/attendance/requests/mine` — đơn của chính user (mọi state), sort mới nhất.
- `GET /hocba-hrm/api/attendance/requests/pending` — **manager**: đơn `pending` trong phạm vi. `_emp_scope_domain(env)` áp lên `employee_id` (prefix như Gói 2). Non-canManage → trả `[]`.
- `POST /hocba-hrm/api/attendance/requests/<int:req_id>/approve` — body optional `{checkIn?, checkOut?, reviewNote?}`.
  - Kiểm `canManage` + `_emp_in_scope(req.employee_id)`; không → 403; không tồn tại → 404; state≠pending → 400 `already_decided`.
  - Giờ áp dụng = body override (nếu gửi) ELSE `req.proposed_*`. `_request_apply(...)`. Set `state='approved'`, `reviewer_id`, `decision_date=now`, `review_note`. Trả `_req_row`. Ràng buộc record (check_out<check_in) → 400 `rejected`+message.
- `POST /hocba-hrm/api/attendance/requests/<int:req_id>/reject` — body `{reviewNote?}`. Cùng kiểm. Set `state='rejected'` + reviewer + decision_date + review_note. Trả `_req_row`.

Route `<int:req_id>` không đụng route literal khác. Helper `_request_create/_request_decide` tách module-level để test trực tiếp (giống `_attendance_edit`).

---

## 3. Frontend (`frontend/src/features/attendance/`)

### 3.1 `api/attendance.js`
Thêm `createRequest(body)`, `fetchMyRequests()`, `fetchPendingRequests()`, `approveRequest(id, body)`, `rejectRequest(id, body)`.

### 3.2 Component mới
- `RequestForm.jsx` — form tạo đơn: chọn ngày (nếu không đính kèm bản ghi), giờ vào/ra (`datetime-local`, prefill nếu sửa bản ghi), lý do. Dùng cho cả "sửa bản ghi" (truyền `attendanceId`+`requestDate` cố định) và "quên chấm công" (user chọn ngày).
- `RequestList.jsx` — danh sách đơn; prop `canReview`:
  - `canReview=false` (user): hiện trạng thái + ghi chú duyệt (read-only).
  - `canReview=true` (manager): mỗi đơn cho sửa giờ đề xuất (`datetime-local`) + nút **Duyệt** / **Từ chối** (ô reviewNote) → gọi API → refetch.

### 3.3 `Attendance.jsx`
- **User**: tabs = `[['me','Chấm công của tôi'], ['requests','Đơn của tôi']]`.
  - Tab `requests`: nút "Gửi đơn quên chấm công" (mở `RequestForm` không đính kèm) + `RequestList` (mine, read-only) từ `fetchMyRequests`.
- **Manager**: tab `day`/`requests`/`ot`. Tab `requests` ("Đơn chấm công") = `RequestList` (canReview) từ `fetchPendingRequests`. Bỏ `ForgotMock`.

### 3.4 `AttendanceDrawer.jsx`
Khi **không** `canManage` (user xem bản ghi của mình): thêm nút **"Gửi đơn sửa"** → mở `RequestForm` với `attendanceId=rec.id`, `requestDate=rec.date`, prefill giờ từ `rec`. (Manager vẫn dùng Sửa/Xóa trực tiếp của Gói 2.)

### 3.5 `mock.js`
Bỏ `FORGOT_REQUESTS` (và import của nó). Giữ `OT_LOG` (Gói 4).

---

## 4. Kiểm thử

### Backend — `custom-addons/hocba_hrm/tests/test_attendance_request.py` (helper module-level, TransactionCase)
- Tạo đơn: `employee_id` pin = user; giờ local→UTC đúng; reason rỗng → lỗi.
- `mine`: chỉ đơn của user.
- `pending`: trưởng phòng chỉ thấy đơn NV phòng mình; HR Manager thấy tất cả; non-canManage → rỗng.
- Approve đơn **sửa bản ghi** (có `attendance_id`): bản ghi cập nhật giờ + `work_credit`/`missing_minutes` tính lại; `state=approved`, reviewer set.
- Approve đơn **ngày thiếu** (không record): tạo bản ghi mới cho (employee, request_date) + `attendance_id` được gán.
- Approve với giờ manager **chỉnh khác** giờ user đề xuất → áp giờ manager.
- Approve đơn ngày-thiếu **không có check_in** → `ValidationError`.
- Approve/Reject **ngoài phạm vi** → AccessError (403). Approve đơn đã quyết định → lỗi `already_decided`.
- Reject: `state=rejected` + review_note.
- Fixture NV official cần `identification_id` 12 số (BR-010 — xem memory).

### Frontend (thủ công)
- User: gửi đơn sửa từ drawer + đơn quên cả ngày từ tab; thấy trạng thái cập nhật sau khi manager xử lý.
- Manager: danh sách pending theo phạm vi; sửa giờ rồi Duyệt → bảng ngày phản ánh; Từ chối kèm ghi chú. Build SPA sạch.

---

## 5. Phạm vi

**Có làm:** model `hocba.attendance.request` + ACL; helper `_request_apply` + endpoint tạo/mine/pending/approve/reject với duyệt-thì-áp-dụng (sửa hoặc tạo bản ghi) + kiểm phạm vi; FE `RequestForm`/`RequestList`, tab "Đơn của tôi" (user) + nút gửi đơn trong drawer, tab "Đơn chấm công" thật (manager); bỏ `FORGOT_REQUESTS` mock; test backend.

**KHÔNG làm (Gói 4 / sau):** đăng ký ca CTV/OT + lịch tuần + cửa sổ check-in ±15' (Gói 4); tab OT (giữ `OT_LOG` mock); thông báo mail/activity cho manager; user tự sửa bản ghi trực tiếp (chỉ qua đơn); đổi logic face/geo/window; payroll.
