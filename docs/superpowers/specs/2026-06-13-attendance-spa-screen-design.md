# Thiết kế — Màn Chấm công (Attendance) cho SPA Học Bá HRM

**Ngày:** 13/06/2026 · **Owner FE:** Hoàng Anh · **Trạng thái:** chờ duyệt
**Phạm vi:** `frontend/src/features/attendance/`, `frontend/src/api/attendance.js`, controller HTTP `/hocba-hrm/api/attendance/*`, gỡ kiosk cũ.
**Quy ước nền:** [docs/QUY_UOC_FRONTEND.md](../../QUY_UOC_FRONTEND.md) · **Màn mẫu chuẩn:** Nhân viên (`features/employees/Employees.jsx`).

---

## 1. Mục tiêu & bối cảnh

Thay thế placeholder `ComingSoon` của view `attendance` trong SPA bằng màn Chấm công thật, nối API `/hocba-hrm/api/attendance/*`. Màn phục vụ **cả hai vai trò theo quyền**:

- **Nhân viên thường:** tự chấm công bằng khuôn mặt + GPS (camera máy tính sau khi đăng nhập), xem trạng thái hôm nay và **lịch sử chấm công của chính mình theo tháng** (chỉ xem).
- **HR/Manager:** ngoài phần cá nhân, xem **bảng chấm công toàn công ty theo ngày** + 2 tab nghiệp vụ tạm dùng dữ liệu mẫu (Đơn quên chấm công, Tăng ca).

Luồng check-in face/geo hiện nằm ở widget Odoo riêng (`hocba_attendance/static/src/js/attendance_kiosk.js`) gọi qua ORM `call_kw`. Quy ước FE §1 **cấm** `call_kw`; vì vậy luồng này được **tái hiện trong SPA** qua HTTP API mới, và **kiosk cũ bị gỡ bỏ**.

### Nguồn dữ liệu backend (đã có, không sửa logic nghiệp vụ)

- `hocba.attendance` — 1 bản ghi / nhân viên / ngày. Fields chính: `employee_id`, `check_in`, `check_out`, `date` (compute-store theo local tz), `working_hours`, `status_code` (`on_time`/`late`), cờ `face_suspect` / `out_of_zone` / `out_of_window` / `needs_review`, ảnh `check_in_photo` / `check_out_photo`, tọa độ, `check_in_map_url` / `check_out_map_url`.
- `hocba.attendance._do_check(payload, kind)` — lõi check-in/out (face matching + geofence + window). `action_check_in` / `action_check_out` gắn employee = user hiện tại rồi gọi `_do_check` dưới `sudo()`.
- `hocba.attendance.policy` — khung giờ (`morning_start/end`, `evening_start/end`), workdays, geofence (`office_lat/lng`, `office_radius_m`), `face_threshold`. `get_policy()` trả policy active.
- `hr.employee.get_self_attendance_info()` → `{employee_id, name, enrolled, is_official}`.
- `hr.employee.enroll_self_face(payload)` → lưu `x_face_image` + `x_face_descriptor`.
- Thư viện nhận diện: `hocba_employees/static/lib/face-api/` (face-api.min.js + models: tinyFaceDetector, faceLandmark68Net, faceRecognitionNet).

---

## 2. Kiến trúc & file layout

### Frontend (địa phận Hoàng Anh)

```
frontend/src/
├── api/attendance.js              # các hàm gọi /hocba-hrm/api/attendance/*
└── features/attendance/
    ├── Attendance.jsx             # màn chính + segment chuyển tab theo quyền
    ├── CheckInPanel.jsx           # camera lớn + enroll + check-in/out + trạng thái hôm nay
    ├── MyHistory.jsx              # lịch sử của tôi theo tháng (month picker + summary + bảng)
    ├── AttendanceTable.jsx        # bảng giám sát theo ngày (HR/manager)
    ├── AttendanceDrawer.jsx       # chi tiết 1 bản ghi: ảnh, bản đồ, cờ review (read-only)
    ├── useFaceApi.js              # hook nạp face-api.js + computeDescriptor(videoEl)
    └── mock.js                    # USE_MOCK + data cho tab Đơn quên chấm công & OT
```

Mỗi unit một nhiệm vụ rõ: `useFaceApi` cô lập toàn bộ phụ thuộc face-api + camera; `CheckInPanel` lo hành vi chấm công; `AttendanceTable`/`MyHistory` chỉ render dữ liệu; `Attendance.jsx` điều phối tab + quyền.

### Backend

- **Controller HTTP mới**: thêm các route `/hocba-hrm/api/attendance/*` (đặt trong `hocba_hrm/controllers/main.py`, cùng class `HocBaHRM`, hoặc tách `attendance_api.py` import vào controllers — quyết định ở plan). Controller **tái dùng** `_do_check` / `enroll_self_face` / `get_self_attendance_info` / `get_policy`, **không viết lại** logic face/geo.
- **Gỡ kiosk**: xóa widget kiosk + template + action/menu trỏ tới (`attendance_kiosk.js`, `static/src/xml/attendance_kiosk.xml`, khai báo trong `__manifest__.py`, action/menu liên quan). Danh sách chính xác chốt ở bước plan. Thư viện face-api ở `hocba_employees` **giữ nguyên**.

### File `[CHUNG]` cần FE-lead (Tân) review

- `frontend/vite.config.js`: thêm proxy `/hocba_employees/static` → Odoo (để dev nạp được face-api.js + models + ảnh enroll).
- `frontend/src/app/App.jsx`: thay `<ComingSoon ... view="attendance">` bằng `<Attendance search={search} />`.

---

## 3. API contract (spec-first, wire format camelCase)

Mọi response JSON key `camelCase`. Ngày trên dây ISO `YYYY-MM-DD`; datetime ISO. FE hiển thị qua `fmtDate` / helper chung. Lỗi: `{"error":"<code>"}` + HTTP status đúng nghĩa. Tất cả route `auth='user'`. BE là nguồn chân lý về quyền (nhân viên thường chỉ thấy dữ liệu của mình).

### a) `GET /hocba-hrm/api/attendance/me`
Thông tin cá nhân để dựng panel check-in.
```jsonc
{
  "employeeId": 12, "name": "Nguyễn Văn A",
  "enrolled": true,            // đã đăng ký khuôn mặt chưa
  "isOfficial": true,          // chỉ NV chính thức mới được điểm danh
  "isHr": false, "isHrManager": false,
  "policy": { "checkInStart": "08:00", "checkInEnd": "09:30",
              "checkOutStart": "16:00", "checkOutEnd": "17:30",
              "geofenceOn": true },
  "today": {                   // bản ghi hôm nay của chính mình; null nếu chưa có
    "checkIn": "2026-06-13T08:05:00", "checkOut": null,
    "workingHours": 0, "statusKey": "late", "lateMinutes": 35,
    "faceSuspect": false, "outOfZone": false, "outOfWindow": false
  }
}
```
- `error: "no_employee"` (HTTP 400) nếu user chưa gắn hồ sơ nhân viên.

### b) `POST /hocba-hrm/api/attendance/enroll`
Body `{ "photo": "<base64>", "descriptor": [128 floats] }` → `{ "ok": true }`.
- Gọi `hr.employee.enroll_self_face`. `error: "no_employee"` (400) nếu chưa gắn hồ sơ.

### c) `POST /hocba-hrm/api/attendance/check-in` và `POST /hocba-hrm/api/attendance/check-out`
Body `{ "photo": "<base64>", "descriptor": [..], "latitude": 21.01, "longitude": 105.84 }`.
```jsonc
{ "recordId": 88, "kind": "in", "faceSuspect": false,
  "outOfZone": false, "outOfWindow": false, "faceScore": 0.42 }
```
- Gọi `action_check_in` / `action_check_out` (đã tự gắn employee = user, chạy `sudo`).
- `error: "no_employee"` (400) nếu chưa gắn hồ sơ; `error: "not_official"` (403) nếu NV không chính thức.

### d) `GET /hocba-hrm/api/attendance?date=YYYY-MM-DD`
Bảng chấm công theo ngày (mặc định hôm nay nếu thiếu `date`).
```jsonc
{
  "isHr": true, "isHrManager": false, "date": "2026-06-13",
  "policy": { "checkInStart": "08:00", "checkInEnd": "09:30",
              "checkOutStart": "16:00", "checkOutEnd": "17:30", "geofenceOn": true },
  "counts": { "onTime": 18, "late": 4, "needsReview": 2, "missing": 6 },
  "rows": [{
    "id": 88, "empId": 12, "code": "GV001", "name": "Nguyễn Văn A",
    "depName": "Toán", "hasImg": true,
    "checkIn": "2026-06-13T08:05:00", "checkOut": "2026-06-13T17:10:00",
    "workingHours": 8.2, "statusKey": "late", "lateMinutes": 35,
    "faceSuspect": false, "outOfZone": true, "outOfWindow": false,
    "needsReview": true,
    "checkInMapUrl": "https://www.google.com/maps?q=...", "checkOutMapUrl": null
  }]
}
```
- **Quyền:** HR/Manager (`hr.group_hr_user` / `hr.group_hr_manager`) → tất cả nhân viên. Nhân viên thường → chỉ `rows` của chính mình. `counts.missing` = số NV (chính thức) không có bản ghi trong ngày (chỉ tính khi là HR/Manager).
- `statusKey`: `on_time` | `late` | `none` (chưa check-in). `lateMinutes` suy từ giờ check-in local so với `policy.morning_start` (0 nếu đúng giờ).

### e) `GET /hocba-hrm/api/attendance/me/history?month=YYYY-MM`
Lịch sử chấm công của **chính mình** theo tháng (mặc định tháng hiện tại nếu thiếu `month`).
```jsonc
{
  "month": "2026-06",
  "summary": { "onTime": 12, "late": 3, "needsReview": 1,
               "daysPresent": 15, "totalHours": 120.5 },
  "rows": [{
    "date": "2026-06-13",
    "checkIn": "2026-06-13T08:05:00", "checkOut": "2026-06-13T17:10:00",
    "workingHours": 8.2, "statusKey": "late", "lateMinutes": 35,
    "faceSuspect": false, "outOfZone": true, "outOfWindow": false,
    "needsReview": true
  }]
}
```
- Luôn lọc `employee_id` = NV của user đang đăng nhập. Query theo khoảng `date` trong tháng (field `date` đã store theo local tz). **Không đổi model.**
- `error: "no_employee"` (400) nếu chưa gắn hồ sơ.

### Ảnh điểm danh
Hiển thị qua `/web/image/hocba.attendance/<id>/check_in_photo` (và `check_out_photo`) — read-only, là ngoại lệ được phép ở quy ước §1.

---

## 4. UI/UX

Giữ design system Học Bá (token `styles/tokens.css`, đỏ `#C8102E`, font Be Vietnam Pro). Dùng component chung từ `components/` (Avatar, Badge, Icon, Modal, EmptyState, states). Badge trạng thái dùng mapping `kind` sẵn có. Mọi fetch xử lý đủ **3 trạng thái**: Loading / Error (nút "Thử lại") / Data.

### Cấu trúc màn

Page-head: tiêu đề "Chấm công" + segment chuyển tab. Tab hiển thị theo quyền (`isHr`/`isHrManager` từ API):

| Tab | Ai thấy | Nội dung |
|---|---|---|
| **Chấm công của tôi** | Mọi người (mặc định) | `CheckInPanel` (trên) + `MyHistory` (dưới) |
| **Bảng chấm công** | HR/Manager | `AttendanceTable` theo ngày |
| **Đơn quên chấm công** | HR/Manager | Mock (`USE_MOCK`), nhãn "Dữ liệu mẫu — chờ backend" |
| **Tăng ca (OT)** | HR/Manager | Mock (`USE_MOCK`), nhãn "Dữ liệu mẫu — chờ backend" |

### Tab "Chấm công của tôi"

1. **CheckInPanel (trọng tâm, kiosk-style):**
   - Trái: video camera lớn (`getUserMedia`).
   - Phải: tên NV, badge trạng thái hôm nay (đúng giờ/đi muộn + giờ check-in), khung giờ policy, 2 nút lớn **Check-in / Check-out**.
   - Chưa enroll → thay nút check-in bằng **Đăng ký khuôn mặt**.
   - Không phải NV chính thức → thông báo "Chức năng điểm danh chỉ áp dụng cho nhân viên chính thức", ẩn nút.
   - Sau khi chấm: toast kết quả; nếu có cờ (face nghi ngờ / ngoài vùng / ngoài giờ) → badge cảnh báo amber; refetch `/me` để cập nhật `today`.
   - Lỗi camera/face/GPS: thông báo thân thiện, không crash (không có camera, không bắt được mặt, từ chối GPS → gửi lat/lng = 0).

2. **MyHistory (dưới):** month picker (mặc định tháng hiện tại) + 4 thẻ tổng hợp (Đúng giờ / Đi muộn / Cần xem lại / Tổng giờ công) + bảng các bản ghi trong tháng (ngày, check-in, check-out, giờ công, đi trễ, trạng thái, cờ review). Click 1 dòng → `AttendanceDrawer` (read-only).

### Tab "Bảng chấm công" (HR/Manager)

- Date picker (mặc định hôm nay) + 4 metric card (Đúng giờ / Đi muộn / Cần duyệt / Chưa chấm) từ `counts`.
- Bảng theo mẫu màn Nhân viên: Nhân viên (Avatar + tên + mã), Phòng ban, Check-in, Check-out, Giờ công, Đi trễ, Trạng thái, cờ review. Có search (lọc theo tên/mã trên `search` từ Topbar).
- Click dòng → `AttendanceDrawer`: ảnh check-in/out (`/web/image/...`), link bản đồ (`checkInMapUrl`/`checkOutMapUrl`), các cờ `faceSuspect`/`outOfZone`/`outOfWindow`. `needsReview` **chỉ hiển thị** (backend chưa có luồng duyệt → không có nút duyệt).

### useFaceApi (hook)

- Nạp `/hocba_employees/static/lib/face-api/face-api.min.js` + 3 model một lần (idempotent), expose trạng thái `ready` + `computeDescriptor(videoEl)` (trả mảng 128 float hoặc `null` nếu không thấy mặt).
- Camera qua `getUserMedia`, GPS qua `navigator.geolocation` (lat/lng = 0 nếu từ chối). **Yêu cầu HTTPS/localhost** mới mở được camera — ghi chú rõ cho người chạy demo.

---

## 5. Quyền & bảo mật

- FE ẩn/hiện tab theo `isHr`/`isHrManager` do API trả; **không tự suy luận quyền**.
- BE chặn thật: `/api/attendance` cho NV thường chỉ trả bản ghi của chính họ; `/me/history` luôn pin theo NV của user.
- Check-in/out/enroll luôn gắn employee = `request.env.user.employee_id` (không nhận `employee_id` từ client) → chống giả mạo. Logic write chạy `sudo` như RPC hiện tại.

---

## 6. Kiểm thử

- **Backend (Odoo test, theo memory `running-odoo-tests`)** — thêm test cho controller mới:
  - `/me`: trả đúng `enrolled`/`isOfficial`/`today`; `no_employee` khi user không có hồ sơ.
  - check-in: tạo bản ghi mới + cập nhật bản ghi cùng ngày; trả cờ face/geo; `not_official` 403.
  - enroll: lưu `x_face_descriptor`.
  - list theo ngày: HR thấy tất cả; NV thường chỉ thấy của mình; `counts` đúng.
  - `/me/history`: lọc đúng tháng + đúng NV; `summary` đúng.
- **Frontend (thủ công, theo Definition of Done §9)**: chạy với cả 4 user role test; đủ 3 trạng thái loading/error/data; không lỗi đỏ console; ẩn/hiện tab đúng quyền; camera/GPS hoạt động trên localhost.

---

## 7. Phạm vi

**Có làm:** panel check-in face/geo + enroll; lịch sử cá nhân theo tháng (read-only); bảng giám sát theo ngày + drawer; 2 tab mock (Đơn quên chấm công, OT); 6 route API (`/me`, `/enroll`, `/check-in`, `/check-out`, list theo ngày, `/me/history`) + test backend; gỡ kiosk cũ; proxy Vite + đăng ký view trong App.

**Không làm (lần này):** luồng duyệt `needs_review`; NV tự sửa/ghi chú bản ghi; xem theo tháng cho HR / báo cáo xuất file; model thật cho Đơn quên chấm công & OT; sửa logic face/geo của model.
