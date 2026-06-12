# Thiết kế: Điểm danh bằng khuôn mặt + vị trí (hocba_attendance)

- **Ngày:** 2026-06-11
- **Module:** `hocba_attendance` (Odoo 19), mở rộng `hocba_employees`
- **Trạng thái:** Đã chốt thiết kế, chờ lập kế hoạch triển khai

## 1. Mục tiêu

Bổ sung chức năng điểm danh cho **nhân viên chính thức** (`x_employment_status == 'official'`)
theo khung giờ cố định, yêu cầu:

1. Chụp ảnh khuôn mặt và lưu vào DB.
2. **Nhận diện / xác thực** khuôn mặt (so khớp với vector mẫu của nhân viên).
3. Lấy vị trí GPS hiện tại và kiểm tra nằm trong phạm vi văn phòng (geofencing).

Khung giờ mặc định (cấu hình được):
- Vào ca (check-in): **08:00 – 09:30**
- Kết thúc ca (check-out): **16:00 – 17:30**
- Ngày làm việc: **Thứ 2 – Thứ 6**

## 2. Quyết định thiết kế (chốt qua brainstorming)

| Hạng mục | Lựa chọn |
|----------|----------|
| Giao diện điểm danh | Trang self-service trong **Odoo backend** (OWL client action) |
| Engine nhận diện | **face-api.js** chạy trên trình duyệt (TensorFlow.js) |
| Đăng ký mẫu khuôn mặt | **Cả hai**: HR tải ảnh mẫu lên + nhân viên tự đăng ký lần đầu |
| Vị trí GPS | **Geofencing** — kiểm tra trong bán kính văn phòng |
| Xử lý vi phạm | **Cho phép tạo bản ghi nhưng đánh dấu cờ** để HR xem xét |

Lý do chọn face-api.js phía trình duyệt: tránh phụ thuộc native (dlib/cmake) khó build
trên Windows; server chỉ lưu & so khớp vector, không xử lý ảnh nặng.

## 3. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────┐
│  Backend self-service page (OWL client action)           │
│  • Bật camera → chụp ảnh khuôn mặt                        │
│  • face-api.js tính descriptor (128-d vector) trên client │
│  • navigator.geolocation lấy lat/long                     │
│  • Gọi RPC lên model Python                               │
└───────────────────────────┬─────────────────────────────┘
                            │ ORM RPC
┌───────────────────────────▼─────────────────────────────┐
│  hocba.attendance (Python)                                │
│  • So khớp descriptor vs vector mẫu của nhân viên        │
│  • Kiểm tra geofence (Haversine vs toạ độ văn phòng)     │
│  • Kiểm tra khung giờ + ngày làm việc                     │
│  • Lưu ảnh, toạ độ, điểm khớp, gắn cờ bất thường         │
└──────────────────────────────────────────────────────────┘
```

## 4. Thay đổi dữ liệu (models)

### 4.1. `hr.employee` — mở rộng trong `hocba_employees`
- `x_face_image` (Binary) — ảnh chân dung mẫu (HR upload).
- `x_face_descriptor` (Text) — vector 128 chiều dạng JSON, dùng để so khớp.
- `x_face_enrolled` (Boolean, computed) — đã có mẫu hay chưa (`bool(x_face_descriptor)`).

Khi HR upload `x_face_image`: cần tính descriptor. Vì face-api.js chạy ở trình duyệt,
descriptor được tính ở form view (OWL widget nhỏ trên field ảnh) hoặc tại bước đăng ký
self-service. **Quyết định:** descriptor luôn được tính ở client; khi HR upload ảnh trong
form nhân viên, một widget nhỏ tính descriptor và ghi vào `x_face_descriptor` cùng lúc.

### 4.2. `hocba.attendance` — thêm field
- `check_in_photo` / `check_out_photo` (Binary) — ảnh chụp lúc điểm danh.
- `check_in_lat` / `check_in_lng` / `check_out_lat` / `check_out_lng` (Float, digits cao).
- `check_in_face_score` / `check_out_face_score` (Float) — khoảng cách euclid descriptor (nhỏ = khớp).
- `face_suspect` (Boolean) — khuôn mặt nghi ngờ không khớp (score > threshold).
- `out_of_zone` (Boolean) — ngoài bán kính văn phòng.
- `out_of_window` (Boolean) — ngoài khung giờ / sai ngày làm việc.
- `needs_review` (Boolean, computed, store) — `face_suspect OR out_of_zone OR out_of_window`.

### 4.3. `hocba.attendance.policy` — model cấu hình mới (singleton)
- `morning_start` (Float, default 8.0), `morning_end` (Float, default 9.5)
- `evening_start` (Float, default 16.0), `evening_end` (Float, default 17.5)
- Ngày làm việc: `workday_mon`..`workday_sun` (Boolean), mặc định T2–T6 = True.
- `office_lat` (Float), `office_lng` (Float), `office_radius_m` (Float, default 150).
- `face_threshold` (Float, default 0.6) — ngưỡng khoảng cách euclid; lớn hơn = không khớp.
- Helper `get_policy()` trả về bản ghi cấu hình hiện hành (tạo mặc định nếu chưa có).

## 5. Luồng nghiệp vụ

### 5.1. Check-in
1. Nhân viên mở trang **My Attendance**; hệ thống xác định `hr.employee` từ `res.users`.
2. Nếu `x_employment_status != 'official'` → thông báo không áp dụng (vẫn cho xem lịch sử).
3. Nếu chưa có `x_face_descriptor` → bước **đăng ký khuôn mặt** trước (chụp, tính descriptor, lưu vào employee).
4. Nếu đã có mẫu → bật camera + xin quyền vị trí.
5. Bấm "Check In": chụp ảnh → tính descriptor → lấy GPS → gửi RPC `action_check_in(payload)`.
6. Server tính:
   - khoảng cách descriptor vs mẫu → `check_in_face_score`; nếu `> face_threshold` → `face_suspect = True`.
   - khoảng cách Haversine GPS vs văn phòng → nếu `> office_radius_m` → `out_of_zone = True`.
   - thời điểm hiện tại nằm trong `[morning_start, morning_end]` và đúng ngày làm việc → nếu không → `out_of_window = True`.
7. **Luôn tạo bản ghi** trong ngày (nếu chưa có), lưu ảnh + toạ độ + score + cờ.

### 5.2. Check-out
- Tương tự, dùng khung giờ chiều `[evening_start, evening_end]`.
- Cập nhật bản ghi điểm danh **cùng ngày** của nhân viên (set `check_out`, các field `check_out_*`).
- Nếu chưa có bản ghi check-in trong ngày → tạo mới rồi set check-out (đánh cờ `out_of_window` nếu cần).

### 5.3. Quy tắc 1 bản ghi / ngày
- Mỗi nhân viên tối đa 1 bản ghi điểm danh / ngày. Check-in lần 2 trong ngày → cập nhật, không tạo trùng.

## 6. Giao diện HR (xem xét)
- List view bổ sung cột cờ (`face_suspect`, `out_of_zone`, `out_of_window`).
- Bộ lọc **"Cần xem xét"** (`needs_review = True`).
- Form hiển thị ảnh check-in/out, link Google Maps từ toạ độ, điểm khớp khuôn mặt.

## 7. Frontend & thư viện
- face-api.js + model weights lưu **tĩnh trong module** (`static/lib/face-api.min.js`,
  `static/models/`) — không phụ thuộc CDN, chạy offline.
- OWL component đăng ký làm `client action`, gắn vào menu **"My Attendance"**.
- Component xử lý: khởi tạo model → mở camera → chụp → tính descriptor → GPS → RPC.

## 8. Bảo mật & quyền
- Method `action_check_in` / `action_check_out` dùng `@api.model`, tự suy ra employee từ
  `self.env.user`; nhân viên thường chỉ tạo/sửa bản ghi của chính mình.
- Quyền HR (`hr.group_hr_user` / `hr.group_hr_manager`) giữ nguyên như hiện tại để xem/duyệt.

## 9. Kiểm thử
- **Unit test Python** (không cần camera):
  - Haversine: điểm trong/ngoài bán kính.
  - Khung giờ: trong/ngoài khoảng, đúng/sai ngày làm việc.
  - Ngưỡng khuôn mặt: score < / > threshold → cờ `face_suspect`.
  - `needs_review` computed đúng.
  - Quy tắc 1 bản ghi / ngày (check-in rồi check-out cập nhật cùng record).
- **Test thủ công frontend:** camera + GPS (yêu cầu `https://` hoặc `localhost`).

## 10. Ràng buộc đã biết
- Camera + GPS chỉ hoạt động trên `https://` hoặc `localhost` (giới hạn trình duyệt).
- face-api.js cần tải model weights (~vài MB) lần đầu — đóng gói tĩnh trong module.
- Nhận diện phía client mang tính xác thực mức cơ bản (không chống giả mạo ảnh tĩnh /
  liveness). Phù hợp phạm vi đồ án; nếu cần chống giả mạo phải bổ sung sau (ngoài phạm vi).

## 11. Ngoài phạm vi (YAGNI)
- Chống giả mạo / liveness detection.
- Điểm danh cho nhân viên không chính thức (thử việc, part-time, CTV...).
- Tính công / bảng lương từ dữ liệu điểm danh.
- Báo cáo nâng cao / dashboard.
