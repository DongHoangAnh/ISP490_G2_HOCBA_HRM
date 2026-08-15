# Spec — Cấu hình khung giờ phỏng vấn

> Module: `hocba_recruitments` · Owner: Việt · Nhánh: `Viet/Recruitment`
> Ngày: 2026-08-11 · Trạng thái: **Đã duyệt (chốt miệng)**

---

## 1. Vấn đề

Khung giờ khai báo lịch rảnh phỏng vấn cứng ở **09:00–17:00, bước 30 phút**, và
cứng ở **hai nơi độc lập nhau**:

| Nơi | Ai dùng |
|---|---|
| `_HOUR_SLOTS` — [hb_interview_slot.py:11](../../../custom-addons/hocba_recruitments/models/hb_interview_slot.py) | Wizard khai slot trong backend Odoo (`fields.Selection`) |
| `HOUR_OPTIONS` — [SlotForm.jsx:15](../../../frontend/src/features/recruitment/SlotForm.jsx) | Form khai slot trên SPA |

Học Bá là trung tâm tiếng Trung, lớp và giáo viên chạy buổi tối. Trưởng bộ phận
**không khai được slot rảnh sau 17:00** để phỏng vấn ứng viên giáo viên — muốn đổi
phải sửa code ở cả hai chỗ rồi upgrade module.

Controller tạo slot (`api_recruitment_slots_create`) hiện **không kiểm giờ** — nhận
mọi số float. Nên giới hạn 9–17 thuần tuý là giới hạn của hai cái dropdown.

## 2. Phạm vi

Ba tham số `ir.config_parameter`, sửa trên tab mới của màn *Cấu hình tuyển dụng*:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `hocba_recruitments.slot_hour_open` | 9.0 | Giờ sớm nhất khai được |
| `hocba_recruitments.slot_hour_close` | 17.0 | Giờ muộn nhất khai được |
| `hocba_recruitments.slot_step_minutes` | 30 | Bước nhảy: 15 / 30 / 60 phút |

**Một nguồn sự thật duy nhất:** danh sách giờ do backend sinh; wizard Odoo và SPA
đều lấy từ đó. Xoá hẳn `HOUR_OPTIONS` tính tay bên JS.

### Ngoài phạm vi

- Khung giờ khác nhau theo thứ trong tuần, hay theo từng người phỏng vấn.
- Chặn khai slot trùng giờ nghỉ trưa.
- Slot đã tạo trước khi đổi cấu hình: **giữ nguyên**, xem §5.

## 3. Backend

### 3.1. Sinh danh sách giờ

Hàm `_hb_hour_slots()` trên `hb.interview.slot` (`@api.model`), trả
`[(float, 'HH:MM'), …]` từ `open` tới `close`, bước `step`.

`fields.Selection` của wizard chuyển sang **callable** (`selection='_hb_hour_selection'`)
để đọc cấu hình tại thời điểm mở form thay vì lúc load module.

### 3.2. Kiểm giờ khi tạo slot

`api_recruitment_slots_create` kiểm `open ≤ startHour < endHour ≤ close`, lệch thì
`400 {error:'rejected', message: …}`. Không kiểm bước nhảy — bước nhảy chỉ để dựng
dropdown, chặn cứng sẽ làm hỏng slot cũ khi admin đổi 30 → 60 phút.

### 3.3. API cấu hình

- `GET /hocba-hrm/api/recruitment/config` — thêm khối:
  ```json
  "slotHours": { "open": 9.0, "close": 17.0, "stepMinutes": 30,
                 "options": [[9.0, "09:00"], …] }
  ```
- `POST /hocba-hrm/api/recruitment/config/slot-hours` — body
  `{ open, close, stepMinutes }`. Quyền: `_can_config()` (Admin + HR Manager,
  đúng như các tab cấu hình hiện có).
- `GET /hocba-hrm/api/recruitment/interview-slots` — thêm `hourOptions` để form
  khai slot dựng dropdown mà không phải gọi API cấu hình (người khai slot là
  trưởng bộ phận, **không** có quyền vào màn cấu hình).

### 3.4. Ràng buộc

| Luật | Lỗi |
|---|---|
| `0 ≤ open < close ≤ 24` | "Giờ mở phải nhỏ hơn giờ đóng và nằm trong 0–24." |
| `stepMinutes ∈ {15, 30, 60}` | "Bước nhảy chỉ nhận 15, 30 hoặc 60 phút." |
| `close − open ≥ step/60` | "Khung giờ phải chứa ít nhất một mốc." |

## 4. Giao diện

Tab mới **"Khung giờ phỏng vấn"** trong `RecruitmentConfig.jsx`, sau *Quy trình &
hạn xử lý*: hai ô chọn giờ mở/đóng, một nhóm radio bước nhảy, kèm dòng xem trước
`09:00 · 09:30 · 10:00 … 17:00 (17 mốc)` để admin thấy ngay hệ quả.

`SlotForm.jsx` nhận `hourOptions` qua props từ `InterviewSlots.jsx` (lấy từ payload
`interview-slots`), bỏ hằng số tính tay.

## 5. Slot đã tạo trước khi đổi cấu hình

Slot lưu bằng `start_datetime`/`stop_datetime` (UTC) chứ không lưu mã giờ, nên thu
hẹp khung giờ **không làm hỏng** slot cũ: vẫn hiện, vẫn đặt lịch phỏng vấn được.
Chỉ là không khai **mới** ngoài khung được nữa. Đây là hành vi mong muốn — không
cần dọn dữ liệu.

## 6. Test

`custom-addons/hocba_recruitments/tests/test_slot_hours.py`

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `test_default_hours` | Không cấu hình → 9.0–17.0 bước 30, đúng 17 mốc |
| 2 | `test_custom_range_and_step` | 8.0–20.0 bước 60 → 13 mốc, mốc cuối 20:00 |
| 3 | `test_step_15` | Bước 15 → mốc 9.25 hiện "09:15" |
| 4 | `test_wizard_selection_follows_config` | Đổi cấu hình → Selection của wizard đổi theo (không cần restart) |
| 5 | `test_create_slot_outside_range_rejected` | POST slot 18:00 khi close=17 → 400 |
| 6 | `test_create_slot_inside_range_ok` | Nới close=20 rồi tạo lại slot 18:00 → 200 |
| 7 | `test_save_config_invalid_order` | open ≥ close → 400 |
| 8 | `test_save_config_bad_step` | step = 45 → 400 |
| 9 | `test_config_requires_permission` | Trưởng phòng gọi POST → 403 |
| 10 | `test_existing_slot_survives_narrowing` | Slot 18:00 đã có, thu khung về 17 → vẫn đọc/đặt lịch được |
