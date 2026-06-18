# Đặc tả API domain — `timeoff` (Nghỉ phép)

> Theo khung `SPEC_API_TEMPLATE.md`. Quy ước chung: `QUY_UOC_FRONTEND.md`.
> Mẫu đối chiếu: **Employees** (`SPEC_HRM_SPA_API.md` §3).

**Domain:** `timeoff`
**Owner:** Nhật Anh · **Module backend:** `hocba_timeoff` · **Màn FE:** `features/timeoff/`
**Phiên bản:** 1.1 · **Ngày:** 15/06/2026 · **Trạng thái:** đã implement (chờ team review)

---

## 1. Phạm vi

Màn **Nghỉ phép** là self-service + duyệt đơn, gồm 5 tab:

- **Tổng quan** (mọi user): dashboard tự đổi view theo quyền —
  *Manager* thấy KPI toàn công ty (tổng đơn / chờ duyệt / đã duyệt / ngày phép /
  đang nghỉ hôm nay), biểu đồ theo loại nghỉ · phòng ban · top nhân viên, hàng chờ
  duyệt, có chọn năm + lọc phòng ban; *Nhân viên* thấy tổng phép còn lại, KPI cá
  nhân, số dư theo loại (thanh tiến độ đã dùng), đơn gần đây và nghỉ sắp tới.
- **Của tôi** (mọi user): xem **số dư phép** theo từng loại nghỉ (đã cấp / đã dùng /
  còn lại), danh sách **đơn nghỉ của chính mình** kèm trạng thái, **tạo đơn nghỉ mới**
  (chọn loại nghỉ, khoảng ngày, lý do, đính kèm chứng từ y tế nếu là nghỉ ốm), và
  **hủy** đơn còn ở trạng thái chờ duyệt.
- **Lịch** (mọi user): lịch nghỉ phép kiểu Odoo, toggle **Năm / Tháng**, tô màu ngày
  theo loại nghỉ + trạng thái (đã duyệt đặc / chờ duyệt viền / từ chối gạch ngang),
  lọc theo loại nghỉ, legend, danh sách **ngày bắt buộc / nghỉ lễ**; officer có thể
  chuyển phạm vi **Của tôi ↔ Cả đội**.
- **Chờ duyệt** (chỉ HR Officer / Manager — `hr_holidays.group_hr_holidays_user`):
  danh sách đơn đang chờ của cả đội, **duyệt / từ chối**, nhìn thấy cờ cảnh báo
  **xung đột lịch dạy** (BR-030) và **thiếu chứng từ y tế** (BR-011); khi duyệt có
  thể nhập **ghi chú bố trí thay thế** (BR-031) hoặc **override chứng từ** (chỉ HR Manager).

**KHÔNG làm ở SPA (để trong Odoo backend):**
- Cấu hình **chính sách nghỉ phép theo loại nhân viên** (`hb.timeoff.policy.rule`),
  kế hoạch tích lũy, ngày nghỉ bắt buộc — màn cấu hình của HR Admin.
- Phân bổ phép thủ công (`hr.leave.allocation`) — tự sinh bởi policy engine
  (`hr.employee._apply_leave_policy`), HR chỉnh trong Odoo.
- Dashboard phân tích / burnout (`hb.timeoff.leave.analysis`, report PDF).
- Quy trình duyệt 2 cấp phức tạp (`validate1`) vẫn dùng đúng cơ chế của
  `hr_holidays`; SPA chỉ gọi `action_approve` và để model quyết định bước kế.

## 2. Nguồn dữ liệu (model Odoo)

| Dữ liệu | Model | Ghi chú |
|---|---|---|
| Đơn nghỉ | `hr.leave` | core `hr_holidays`; `hocba_timeoff` mở rộng (khẩn cấp / y tế / xung đột lịch) |
| Số dư phép | `hr.leave.type` (ngữ cảnh `employee_id`) | `max_leaves`, `leaves_taken`, `virtual_remaining_leaves` |
| Phân bổ phép | `hr.leave.allocation` | chỉ đọc gián tiếp qua số dư; không thao tác ở SPA |
| Cờ khẩn cấp | `hr.leave.type.x_is_emergency_type` → `hr.leave.x_is_emergency` | fast-track 1 bước duyệt |
| Chứng từ y tế | `hr.leave.attachment_ids` + `x_has_medical_doc` / `x_medical_override` | BR-011, BR-012 (PDF/JPG/PNG ≤ 5MB) |
| Xung đột lịch dạy | `hr.leave.x_schedule_conflict` / `x_conflict_info` / `x_replacement_note` | BR-030/031 (dò bất đồng bộ qua cron) |
| Loại nhân viên | `hr.employee.x_hb_leave_emp_type` | hiển thị nhãn ở header tab "Của tôi" |

> ⚠️ Không đọc dữ liệu domain khác. Tất cả endpoint nằm trong controller riêng của
> `hocba_timeoff` (`controllers/main.py`) nhưng dùng **chung prefix** `/hocba-hrm/api/timeoff/*`.

## 3. Endpoints

> Quy ước chung (mọi endpoint tuân theo):
> - Prefix `/hocba-hrm/api/timeoff/...`; `auth='user'`, `type='http'`, trả JSON.
> - JSON key **camelCase**; ngày ISO `YYYY-MM-DD`; số ngày phép = Float.
> - Ẩn/hiện theo `has_group` ở controller; FE chỉ đọc flag.
> - Lỗi: `{"error":"<code>"}` + HTTP status (400/401/403/404/500).
> - Cờ quyền dùng chung mọi response: `isOfficer` (`hr_holidays.group_hr_holidays_user`),
>   `isManager` (`hr_holidays.group_hr_holidays_manager`).

### 3.1. `GET /hocba-hrm/api/timeoff/overview`  (auth=user)

**Mục đích:** bootstrap tab "Của tôi" — danh tính, số dư phép, loại nghỉ có thể chọn,
đơn của chính mình.

**Response 200:**
```json
{
  "isOfficer": false,
  "isManager": false,
  "employee": { "id": 12, "name": "Trần Văn A", "empTypeKey": "teacher", "empType": "Giảng viên (Chính thức)" },
  "balances": [
    { "leaveTypeId": 1, "leaveType": "Phép năm", "kind": "blue",
      "allocated": 12.0, "taken": 3.0, "remaining": 9.0, "requiresAllocation": true }
  ],
  "leaveTypes": [
    { "id": 1, "name": "Phép năm", "requiresAllocation": true, "isEmergency": false,
      "supportDocument": false, "requestUnit": "day" },
    { "id": 5, "name": "Nghỉ ốm",  "requiresAllocation": false, "isEmergency": false,
      "supportDocument": true,  "requestUnit": "day" }
  ],
  "requests": [
    { "id": 88, "leaveTypeId": 1, "leaveType": "Phép năm",
      "from": "2026-06-20", "to": "2026-06-21", "days": 2.0,
      "state": "confirm", "stateLabel": "Chờ duyệt", "stateKind": "amber",
      "reason": "Việc gia đình", "isEmergency": false,
      "scheduleConflict": false, "supportDocument": false, "hasMedicalDoc": false,
      "canCancel": true }
  ]
}
```

**Lỗi:** `500 server_error` (không có employee gắn với user → `employee: null`, vẫn 200).

### 3.2. `GET /hocba-hrm/api/timeoff/approvals`  (auth=user, officer)

**Mục đích:** tab "Chờ duyệt" — đơn đang chờ (`confirm` / `validate1`) của đội.

**Response 200:**
```json
{
  "isOfficer": true,
  "isManager": false,
  "requests": [
    { "id": 91, "employeeId": 12, "employee": "Trần Văn A",
      "leaveType": "Nghỉ ốm", "from": "2026-06-18", "to": "2026-06-19", "days": 2.0,
      "state": "confirm", "stateLabel": "Chờ duyệt", "stateKind": "amber",
      "reason": "Sốt", "isEmergency": false,
      "scheduleConflict": true, "conflictInfo": "• 18/06/2026 — Toán 10A",
      "academicReviewRequired": true, "replacementNote": "",
      "supportDocument": true, "hasMedicalDoc": false }
  ]
}
```

**Lỗi:** `403 forbidden` (không thuộc nhóm officer).

### 3.3. `POST /hocba-hrm/api/timeoff/request`  (auth=user)

**Mục đích:** tạo đơn nghỉ cho **chính mình** (đơn vào thẳng trạng thái `confirm` —
chờ duyệt). Tự kích hoạt fast-track khẩn cấp / dò xung đột lịch (model lo).

**Body:**
```json
{
  "leaveTypeId": 5,
  "dateFrom": "2026-06-18",
  "dateTo": "2026-06-19",
  "reason": "Sốt cao",
  "attachment": { "filename": "giay-kham.pdf", "mimetype": "application/pdf", "data": "<base64>" }
}
```
- `attachment` **tùy chọn** (chỉ dùng cho loại nghỉ cần chứng từ). Controller validate
  mime ∈ {pdf, jpeg, png} và size ≤ 5MB trước khi tạo; model re-validate ở bước duyệt.

**Response 200:** trả lại nguyên payload `GET /overview` (đã refresh số dư + đơn).

**Lỗi:** `400 bad_request` (thiếu/ sai field, ngày to < from, file sai loại/quá lớn),
`403 forbidden` (không được phép tạo cho employee đó), `404 leave_type_not_found`.

### 3.4. `POST /hocba-hrm/api/timeoff/request/<id>/cancel`  (auth=user)

**Mục đích:** chủ đơn hủy đơn của mình khi còn chờ duyệt.

**Body:** `{}` · **Response 200:** payload `GET /overview`.
**Lỗi:** `404 not_found`, `403 forbidden` (không phải chủ đơn / không hủy được trạng thái này).

### 3.5. `POST /hocba-hrm/api/timeoff/request/<id>/decision`  (auth=user, officer)

**Mục đích:** duyệt / từ chối đơn. Gọi `action_approve` / `action_refuse` **không sudo**
để model áp đủ ràng buộc (BR-011 chứng từ, BR-031 ghi chú thay thế, quyền duyệt).

**Body:**
```json
{ "action": "approve",
  "replacementNote": "Cô B dạy thay buổi 18/06",
  "medicalOverride": false, "medicalOverrideReason": "" }
```
- `action`: `"approve"` | `"refuse"`.
- `replacementNote`: ghi vào `x_replacement_note` trước khi duyệt (khi có xung đột lịch).
- `medicalOverride` + `medicalOverrideReason`: chỉ HR Manager — bỏ qua yêu cầu chứng từ.

**Response 200:** payload `GET /approvals` (đã refresh).
**Lỗi:** `400 bad_request`, `403 rejected` (model chặn — kèm `message` mô tả lý do
do người dùng đọc, vd "Đơn nghỉ ốm phải đính kèm chứng từ y tế"), `404 not_found`.

### 3.6. `GET /hocba-hrm/api/timeoff/dashboard`  (auth=user)

**Mục đích:** dữ liệu tab "Tổng quan". Tự đổi view theo quyền (`isManager`).

**Query params:** `?year=2026` · `&dept=<id>` (chỉ Manager dùng để lọc phòng ban).

**Response 200 (Manager):**
```json
{ "isManager": true, "isOfficer": true, "year": 2026,
  "kpi": { "total": 5, "pending": 4, "approved": 1, "approvedDays": 1.0, "onLeaveToday": 0 },
  "byType": [ { "id": 88, "name": "Nghỉ Khẩn Cấp", "days": 1.0, "count": 1, "pct": 100, "color": "#ef4444" } ],
  "byDept": [ ... ], "topEmployees": [ ... ],
  "pending": [ { "id": 91, "employee": "...", "department": "...", "leaveType": "...",
                 "from": "2026-06-18", "to": "2026-06-19", "days": 2.0, "isEmergency": false } ],
  "departments": [ { "id": 1, "name": "..." } ] }
```

**Response 200 (Nhân viên):**
```json
{ "isManager": false, "isOfficer": false, "year": 2026,
  "empMissing": false, "employee": { "id": 12, "name": "..." },
  "balances": [ { "id": 1, "name": "Phép năm", "allocated": 12, "taken": 3, "remaining": 9,
                  "pct": 25, "low": false, "color": "#3b82f6" } ],
  "totalRemaining": 9.0,
  "empKpi": { "pending": 0, "approved": 1, "approvedDays": 2.0 },
  "myRequests": [ { "id": 88, "leaveType": "...", "from": "...", "to": "...", "days": 2.0,
                    "state": "confirm", "stateLabel": "Chờ duyệt", "stateKind": "amber" } ],
  "upcoming": [ { "id": 88, "leaveType": "...", "from": "...", "to": "...", "days": 2.0 } ] }
```

### 3.7. `GET /hocba-hrm/api/timeoff/calendar`  (auth=user)

**Mục đích:** dữ liệu tab "Lịch" cho 1 năm.

**Query params:** `?year=2026` · `&scope=me|all` (`all` chỉ officer; mặc định `me`).

**Response 200:**
```json
{ "isOfficer": true, "isManager": true, "year": 2026, "scope": "all",
  "leaveTypes": [ { "id": 75, "name": "Nghỉ Ốm", "color": "#ef4444" } ],
  "leaves": [ { "id": 91, "employee": "...", "leaveTypeId": 75, "leaveType": "Nghỉ Ốm",
                "color": "#ef4444", "from": "2026-06-18", "to": "2026-06-19",
                "state": "confirm", "stateKind": "amber", "isEmergency": false } ],
  "mandatoryDays": [ { "name": "Tết Dương Lịch", "from": "2026-01-01", "to": "2026-01-01", "color": "#ef4444" } ] }
```
- `color` là mã hex suy ra từ color index của leave type (BE gửi sẵn để FE khỏi map).
- FE tự dựng lưới ngày từ khoảng `from`/`to`; ngày trùng nhiều đơn lấy trạng thái "mạnh nhất"
  (đã duyệt > chờ duyệt > từ chối). `mandatoryDays` đã khử trùng lặp ở BE.

## 4. Ma trận phân quyền

| Khối dữ liệu / thao tác | Điều kiện (nhóm) |
|---|---|
| Số dư phép + đơn của chính mình (`/overview`) | mọi user đăng nhập |
| Dashboard view Nhân viên (`/dashboard`) | mọi user đăng nhập |
| Dashboard view Manager (KPI toàn công ty, lọc phòng ban) | `hr_holidays.group_hr_holidays_manager` |
| Lịch của mình (`/calendar?scope=me`) | mọi user đăng nhập |
| Lịch cả đội (`/calendar?scope=all`) | `hr_holidays.group_hr_holidays_user` |
| Tạo / hủy đơn của chính mình | mọi user (model áp domain employee của user) |
| Tab "Chờ duyệt" (`/approvals`) | `hr_holidays.group_hr_holidays_user` |
| Duyệt / từ chối (`/decision`) | model tự kiểm (officer / manager / leave_manager) |
| Override chứng từ y tế | `hr_holidays.group_hr_holidays_manager` |
| Phê duyệt khi xung đột lịch dạy | `hocba_timeoff.group_academic_manager` (hoặc HR Manager) |

> Flag FE: `isOfficer` quyết định có hiện tab "Chờ duyệt"; `isManager` quyết định có
> hiện ô "override chứng từ". Mọi thao tác ghi đều gọi **không sudo** → AccessError /
> ValidationError của model là nguồn chân lý, FE chỉ hiển thị `message`.

## 5. Ghi chú test

- [ ] User thường (không nhóm HR): thấy số dư + đơn của mình; tạo/hủy đơn OK;
      KHÔNG thấy tab "Chờ duyệt"; gọi `/approvals` → 403.
- [ ] HR Officer: thấy tab "Chờ duyệt"; duyệt đơn thường OK.
- [ ] Nghỉ ốm không kèm chứng từ → duyệt báo 403 `rejected` (BR-011); HR Manager
      bật override + nhập lý do → duyệt OK (BR-012).
- [ ] Giảng viên nghỉ trùng buổi dạy → đơn có `scheduleConflict=true`; duyệt khi
      chưa nhập `replacementNote` → 403 `rejected` (BR-031).
- [ ] Loại nghỉ khẩn cấp (`x_is_emergency_type`) → tạo xong HR + manager nhận thông báo.
- [ ] Edge: `leaveTypeId` không tồn tại → 404; `dateTo < dateFrom` → 400;
      file `.exe` hoặc > 5MB → 400; hủy đơn người khác → 403.

## 6. Câu hỏi mở / phụ thuộc

- **Đơn vị theo giờ / nửa ngày:** v1 chỉ hỗ trợ tạo theo **ngày** (`requestUnit='day'`).
  Loại nghỉ cấu hình theo giờ vẫn hiển thị số dư nhưng form tạo tạm khóa — cần chốt UI.
- **Dò xung đột lịch dạy** chạy bất đồng bộ qua `ir.cron` (`teaching.session` hiện chưa
  cài ở mọi DB) → `scheduleConflict` có thể còn `false` ngay sau khi tạo, cập nhật sau
  vài giây. FE không chặn theo cờ này, chỉ hiển thị ở tab duyệt.
- **Đính kèm chứng từ** đi qua body JSON base64 (ngoại lệ có kiểm soát so với
  QUY_UOC §1) — nếu team muốn dùng multipart riêng, chỉnh ở mục 3.3.
