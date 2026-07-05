# Spec — Luồng xin nghỉ của giáo viên (xử lý xung đột lịch dạy)

- **Ngày**: 2026-06-25
- **Module**: `hocba_timeoff` (BE + API) · `frontend/` (FE) · phối hợp `hocba_attendance` (badge Lịch dạy)
- **Owner**: NhatAnh
- **Trạng thái**: Đã duyệt thiết kế — chờ viết plan (TDD)

---

## 1. Bối cảnh & mục tiêu

Giáo viên (GV) của Học Bá có **lịch dạy** (buổi/lớp). Khi GV xin nghỉ trùng vào buổi dạy, không thể tạo đơn "trơn" như nhân viên thường — phải xử lý buổi dạy bị ảnh hưởng trước.

**Mục tiêu**: khi GV xin nghỉ, hệ thống dò các buổi dạy trùng khoảng nghỉ và **bắt buộc** GV chọn cách xử lý cho **từng buổi**:
1. **Cả lớp cùng nghỉ** (hủy buổi), hoặc
2. **Đổi giáo viên dạy thay** (chọn GV khác; GV đó phải **đồng ý** mới chốt).

Chỉ khi **mọi buổi trùng đã được xử lý xong** thì đơn nghỉ mới được gửi; và đơn chỉ **được duyệt** khi **mọi yêu cầu dạy thay đã được GV thay đồng ý**.

### Quyết định nền tảng về dữ liệu

- Lịch dạy gốc nằm ở **CMS MySQL** (hệ thống của nhóm khác), Odoo hiện chỉ **đọc** (`cms_connector.get_sessions_for_tutor/week`). **Không ghi vào CMS.**
- **Neon là nguồn dữ liệu chính (source of truth)** cho lịch dạy trong phạm vi HRM. CMS chỉ dùng để **import 1 lần làm dữ liệu mẫu** vào Neon. Sau import, luồng nghỉ phép **không đọc CMS nữa** — mọi thao tác (dò xung đột, hủy buổi, đổi GV) đều thực hiện và **ghi thẳng vào Neon**.
- Lý do: sau khi hoàn thiện HRM, hai dự án sẽ **gộp về một DB chung**; model lịch dạy trong Neon sẽ trở thành bảng dùng chung, không phải đổi luồng.

---

## 2. Phạm vi

**Trong phạm vi:**
- Model lịch dạy chính trong Neon + lệnh import 1 lần từ CMS.
- Dò buổi dạy trùng đơn nghỉ (trên Neon).
- Cổng chặn tạo đơn: phải xử lý hết buổi trùng.
- Workflow "đổi GV dạy thay": yêu cầu → GV thay đồng ý/từ chối.
- Cổng chặn duyệt: mọi dòng dạy thay phải được đồng ý.
- Áp thay đổi lịch (hủy buổi / đổi GV) vào Neon **tại bước duyệt**; revert khi hủy đơn đã duyệt.
- FE: bước xử lý buổi trùng trong form tạo đơn; panel "Yêu cầu dạy thay"; badge nhắc trên màn Lịch dạy; chuông thông báo loại mới.

**Ngoài phạm vi (YAGNI):**
- Ghi ngược vào CMS MySQL.
- Cron đồng bộ định kỳ CMS → Neon (chỉ import thủ công 1 lần).
- Dò trùng lịch của GV thay (buổi GV thay cũng bận) — đánh dấu *optional*, có thể bổ sung sau.
- Phân quyền "Academic Manager" của code conflict cũ.

---

## 3. Data model (module `hocba_timeoff`)

### 3.1. `hocba.teaching.session` — bảng lịch dạy chính (Neon)

| field | kiểu | ràng buộc / ghi chú |
|---|---|---|
| `cms_session_id` | Char | unique, index — khóa buổi từ CMS (giữ để map khi gộp DB) |
| `employee_id` | M2O `hr.employee` | **GV đang phụ trách** (bị đổi khi dạy thay), index |
| `original_employee_id` | M2O `hr.employee` | GV gốc — để revert |
| `class_id` | Char | mã lớp |
| `class_name` | Char | tên lớp |
| `session_date` | Date | ngày dạy, index |
| `start_time` | Char | giờ bắt đầu "HH:MM" |
| `end_time` | Char | giờ kết thúc "HH:MM" |
| `state` | Selection | `planned` (mặc định) / `substituted` / `cancelled` |
| `source_leave_id` | M2O `hr.leave` | đơn nghỉ đã gây ra thay/hủy buổi |

- Constraint: `cms_session_id` unique → import idempotent (upsert theo khóa này).
- `name_get`/`display_name`: ví dụ `"<class_name> — <date> <start>-<end>"`.

### 3.2. `hocba.leave.session.resolution` — dòng xử lý mỗi buổi trùng

| field | kiểu | ràng buộc / ghi chú |
|---|---|---|
| `leave_id` | M2O `hr.leave` | required, `ondelete='cascade'`, index |
| `session_id` | M2O `hocba.teaching.session` | required |
| `resolution` | Selection | `class_off` / `substitute` — required |
| `substitute_id` | M2O `hr.employee` | required khi `resolution='substitute'` |
| `state` | Selection | `pending` / `accepted` / `declined`; `class_off` mặc định `accepted` |
| `decided_at` | Datetime | mốc GV thay phản hồi |
| `decline_reason` | Char | lý do từ chối |

- Constraint: `substitute_id` bắt buộc và `!= leave_id.employee_id` khi `resolution='substitute'`.
- Constraint: không tạo 2 dòng cho cùng `(leave_id, session_id)`.

### 3.3. Mở rộng `hb.leave.notification`

Thêm vào field `kind` các giá trị:
- `sub_request` — gửi GV thay: "GV A xin bạn dạy thay buổi …".
- `sub_accepted` — báo GV xin nghỉ: "GV B đã đồng ý dạy thay".
- `sub_declined` — báo GV xin nghỉ: "GV B từ chối dạy thay".

### 3.4. Dọn dẹp

Gỡ file dead-code `models/hr_leave_schedule_conflict.py` (tham chiếu model ảo `teaching.session` + phụ thuộc module `hb_timeoff_policy` không cài được). Bỏ import trong `models/__init__.py`. Giữ **tên mới** `hocba.teaching.session` để không vô tình kích hoạt logic cũ.

---

## 4. Import dữ liệu mẫu (CMS → Neon, một lần)

- Method `hocba.teaching.session._import_from_cms(date_from, date_to)` (gọi qua script hoặc server-action HR-only):
  - Lặp ngày trong khoảng, gọi `cms_connector.get_sessions_for_week`/`get_sessions_for_tutor` cho từng GV có `x_cms_user_id`.
  - Map `tutor_id` (CMS) → `hr.employee` qua `x_cms_user_id`.
  - **Upsert** theo `cms_session_id`: tạo mới hoặc cập nhật; set `state='planned'`, `original_employee_id = employee_id`.
- Idempotent: chạy lại không tạo trùng.
- Sau import, **luồng nghỉ phép không gọi CMS** nữa.

---

## 5. Luồng nghiệp vụ

```
GV chọn loại nghỉ + khoảng ngày
   └─► BE dò buổi trùng TRÊN NEON
        domain: employee_id = GV, state='planned',
                session_date trong [dateFrom, dateTo]
        ├─ Không trùng → tạo đơn theo luồng hiện tại
        └─ Có trùng → form bắt chọn xử lý TỪNG buổi
   └─► Submit (CHẶN nếu còn buổi chưa chọn) → tạo hr.leave + resolution
        • class_off  → dòng state=accepted, CHƯA đụng session
        • substitute → dòng state=pending + chuông `sub_request` + badge cho GV thay
GV thay phản hồi:
   • Đồng ý  → resolution.state=accepted (+ chuông `sub_accepted` cho GV xin nghỉ)
   • Từ chối → resolution.state=declined (+ chuông `sub_declined`); GV xin nghỉ phải sửa lại buổi đó
Người quản lý DUYỆT đơn (action_approve):
   • CHẶN nếu còn dòng substitute có state != accepted
   • Khi duyệt thành công → GHI VÀO NEON:
        - class_off  → session.state='cancelled', source_leave_id = đơn
        - substitute → session.employee_id = substitute_id,
                       session.state='substituted', source_leave_id = đơn
Hủy đơn đã duyệt:
   • Revert mỗi session: employee_id = original_employee_id, state='planned', source_leave_id = False
```

**Quyết định**: áp thay đổi lịch tại bước **DUYỆT** (không phải lúc tạo đơn / lúc GV thay đồng ý) để đơn bị từ chối/hủy không làm hỏng lịch thật. GV thay "đồng ý" chỉ là **cam kết**; lịch chỉ đổi khi đơn được duyệt cuối cùng.

---

## 6. API (controller `hocba_timeoff`)

| Method | Route | Mô tả |
|---|---|---|
| POST | `/hocba-hrm/api/timeoff/teaching-conflicts` | body `{dateFrom,dateTo}` → dò buổi trùng **trên Neon**; trả `[{sessionId, className, date, startTime, endTime}]` + danh sách GV để chọn thay (`[{id,name}]`). Không gọi CMS. |
| POST | `/hocba-hrm/api/timeoff/request` (mở rộng) | nhận thêm `resolutions:[{sessionId, type:'class_off'\|'substitute', substituteId?}]`; validate đủ buổi trùng; tạo đơn + dòng resolution + thông báo dạy thay. |
| GET | `/hocba-hrm/api/timeoff/substitutions` | yêu cầu dạy thay gửi tới user đăng nhập (cho panel + badge): `[{id, requester, className, date, time, state}]`. |
| POST | `/hocba-hrm/api/timeoff/substitutions/<int:id>/decide` | body `{accept:bool, reason?}` → đặt resolution accepted/declined + thông báo lại GV xin nghỉ. |

**Validate khi tạo đơn (mở rộng `api_request_create`):**
- Chỉ chạy nhánh xung đột nếu `emp.x_cms_user_id` (là GV).
- Dò buổi trùng trên Neon; tập `sessionId` trong `resolutions` phải **phủ hết** tập buổi trùng — thiếu → `error: 'unresolved_sessions'` (400).
- Mỗi `substitute` phải có `substituteId` hợp lệ, khác chính GV → lỗi nếu sai.

---

## 7. Phân quyền & ràng buộc

- Chỉ tài khoản **giáo viên** (có `x_cms_user_id`) chạy nhánh dò xung đột; NV thường giữ luồng cũ.
- Self-service: đọc/ghi `hocba.teaching.session` qua `.sudo()` **sau khi đã pin** đúng employee/phạm vi (NV thường không có ACL).
- GV thay phải khác GV xin nghỉ.
- `action_approve` (override trên `hr.leave`): chặn khi còn dòng `substitute` chưa `accepted`; thông báo lỗi tiếng Việt rõ ràng.

---

## 8. Frontend (`frontend/`)

- **`LeaveForm.jsx`**: sau khi chọn khoảng ngày (và là GV) → gọi `teaching-conflicts`. Nếu có buổi trùng:
  - Hiện danh sách buổi: tên lớp, ngày, giờ.
  - Mỗi buổi: radio `Cả lớp nghỉ` / `Đổi GV dạy thay`; nếu chọn dạy thay → dropdown GV.
  - Nút **Gửi đơn** disabled cho tới khi mọi buổi đã chọn (và dạy thay đã chọn GV).
  - Submit kèm `resolutions`.
- **Panel "Yêu cầu dạy thay"** (màn Nghỉ phép): list yêu cầu gửi tới mình + nút **Đồng ý** / **Từ chối** (kèm lý do).
- **Badge trên Lịch dạy** (màn Chấm công, `hocba_attendance`): buổi có yêu cầu dạy thay hiện nhãn "GV A xin dạy thay" + link sang panel. (Phối hợp owner `hocba_attendance`.)
- **Chuông**: hiển thị `kind` mới (`sub_request`/`sub_accepted`/`sub_declined`).

---

## 9. Edge cases

- GV thay **từ chối** sau khi đã có dòng → đơn không duyệt được tới khi GV xin nghỉ sửa lại buổi đó (đổi GV khác hoặc chuyển sang "cả lớp nghỉ").
- Đơn bị **từ chối/hủy khi chưa duyệt** → resolution cascade xóa; nếu có dòng dạy thay đã `accepted` → gửi chuông báo GV thay "buổi không còn cần thay".
- Đơn **đã duyệt rồi bị hủy** → revert session (`original_employee_id`, `state='planned'`).
- Buổi trùng nhưng `state != 'planned'` (đã bị hủy/đổi bởi đơn khác) → không tính là xung đột mới (tránh đụng độ kép).
- (Optional) GV thay cũng có buổi `planned` trùng giờ → cảnh báo khi chọn.

---

## 10. Testing (TDD — backend trước)

Chạy theo CLAUDE.md: `-u hocba_timeoff,hocba_employees --test-enable --test-tags /hocba_timeoff`. **Mock `cms_connector`** để test không phụ thuộc MySQL thật.

1. **Import**: upsert idempotent theo `cms_session_id`; map `x_cms_user_id` → employee; set `original_employee_id`, `state='planned'`.
2. **Dò xung đột**: tạo session Neon → xin nghỉ trùng → trả đúng tập buổi; bỏ qua buổi `state != 'planned'`.
3. **Gate tạo đơn**: thiếu resolution cho buổi trùng → reject (`unresolved_sessions`); đủ → tạo đơn + đúng số dòng.
4. **Workflow dạy thay**: dòng `substitute` `pending` → `action_approve` bị chặn; GV thay accept → approve được; decline → vẫn chặn.
5. **Áp ghi lúc duyệt**: duyệt đơn → `class_off` ⇒ session `cancelled`; `substitute` ⇒ session.employee_id = GV thay, `substituted`, `source_leave_id` đúng.
6. **Revert lúc hủy**: hủy đơn đã duyệt → session về `original_employee_id`/`planned`.
7. **Phân quyền**: GV thay phải khác GV nghỉ; NV thường không kích hoạt nhánh xung đột.

---

## 11. Thứ tự triển khai (BE chắc trước, UI sau)

1. Model `hocba.teaching.session` + `_import_from_cms` + test import.
2. Model `hocba.leave.session.resolution` + ràng buộc + test.
3. Mở rộng API `teaching-conflicts` + `request` (gate tạo đơn) + test.
4. Override `action_approve` (gate duyệt) + áp ghi session + revert + test.
5. Workflow GV thay: `substitutions` + `decide` + chuông `kind` mới + test.
6. FE: LeaveForm bước xung đột → panel dạy thay → badge Lịch dạy → chuông.
7. Gỡ dead-code `hr_leave_schedule_conflict.py`.
