# Spec — Đánh dấu lịch dạy trên trang "Lịch" của giáo viên + dọn màu

- **Ngày:** 2026-06-26
- **Owner:** Nhật Anh (nhánh `NhatAnh/TimeOff`)
- **Module ảnh hưởng:** `hocba_attendance` (cms_connector), `hocba_hrm` (controller API), `frontend` (SPA — tab "Lịch")

## 1. Bối cảnh & vấn đề

Trang **Nghỉ phép → tab "Lịch"** (`frontend/src/features/timeoff/CalendarPanel.jsx`) hiển thị lịch năm/tháng tô màu theo **đơn nghỉ** + **ngày đi làm văn phòng** (Thứ 2–Thứ 6 chuẩn, Thứ 7 đi làm thêm tô xanh lá, cuối tuần tô xám).

Với **tài khoản giáo viên**, mô hình "ngày làm việc văn phòng" không đúng: lịch làm của giáo viên là **lịch dạy** lấy từ CMS, không liên quan ngày làm việc của nhân viên các phòng ban khác. Hiện giáo viên **không thấy** ngày nào mình có lịch dạy trên trang này.

Ngoài ra, cách tô màu hiện tại bị phản hồi là "chói" — đơn nghỉ đã duyệt tô đặc màu loại nghỉ + chữ trắng, lẫn với nền xám cuối tuần, nhiều tín hiệu màu cạnh tranh.

## 2. Mục tiêu

1. Tài khoản giáo viên: trang "Lịch" **đánh dấu những ngày có lịch dạy** (cả chế độ xem Năm và Tháng).
2. Với giáo viên: **ẩn** dấu hiệu "ngày làm việc văn phòng" (xanh lá Thứ 7, xám cuối tuần) vì không áp dụng.
3. **Dọn lại bảng màu** cho dịu, dễ đọc hơn — áp dụng cho mọi tài khoản.

Không nằm trong phạm vi (YAGNI): hiển thị chi tiết từng buổi dạy (giờ, lớp) trên ô lịch — đã có ở tab "Lịch tuần" của màn Chấm công; chỉ đánh dấu **ngày có/không có** lịch dạy + số buổi (tooltip).

## 3. Quy ước phân biệt giáo viên

Giáo viên = `hr.employee.x_cms_user_id` khác rỗng (đúng pattern hiện hành: `bool(emp.x_cms_user_id)`; xem `api_teaching_schedule`, `_overview_payload`). Frontend đã có `data.employee.isTeacher` trong payload overview.

Chỉ đánh dấu lịch dạy khi **người đăng nhập là giáo viên** và đang xem **phạm vi "Của tôi"** (`scope === 'me'`). Phạm vi "Cả đội" (officer) là tổng quan nghỉ của đội — không chèn lịch dạy.

## 4. Backend

> **Nguồn dữ liệu (chốt sau review):** lấy từ **Neon** — model `hocba.teaching.session`
> (module `hocba_timeoff`), KHÔNG đọc MySQL CMS. Model này đã được khai báo là
> "NGUỒN CHÍNH trong Neon" và sẽ thành bảng lịch dạy dùng chung khi gộp 2 dự án về
> 1 DB. Vì vậy không thêm hàm CMS nào; chỉ truy vấn ORM.

### 4.1 `hocba_hrm/controllers/main.py` — endpoint + helper

```
GET /hocba-hrm/api/teaching/days?from=YYYY-MM-DD&to=YYYY-MM-DD
```

Helper thuần `_teaching_days_payload(env, from_str, to_str)` → `(dict, status)`:
- Không có `employee_id`, hoặc không có `x_cms_user_id` → `({'isTeacher': False, 'days': []}, 200)`.
- Thiếu/sai định dạng `from`/`to` → `({'error': 'invalid_date'}, 400)`.
- `to < from` hoặc khoảng > 366 ngày → `({'error': 'invalid_range'}, 400)`.
- Hợp lệ → `search_read` trên `hocba.teaching.session` với domain
  `[employee_id = emp, state != 'cancelled', session_date in [from,to]]`, đếm số
  buổi theo `session_date`, trả `({'isTeacher': True, 'days': [{'date','count'}]}, 200)`.
  - `state='cancelled'` (cả lớp nghỉ) bị loại; buổi `substituted` tính cho GV đang
    phụ trách vì domain ghim `employee_id`.
  - Dùng `.sudo()` SAU khi ghim `employee_id` của chính user (user thường không có
    ACL trên model này — self-service an toàn).

`x_cms_user_id` vẫn là cờ phân biệt giáo viên (đồng nhất `isTeacher` ở payload overview).

## 5. Frontend

### 5.1 `api/attendance.js`
```js
export const fetchTeachingDays = (from, to) =>
  hbGet(`/hocba-hrm/api/teaching/days?from=${from}&to=${to}`);
```

### 5.2 `features/timeoff/TimeOff.jsx`
Truyền cờ giáo viên xuống panel lịch:
```jsx
{activeTab === 'calendar' &&
  <CalendarPanel isOfficer={data.isOfficer}
                 isTeacher={!!(data.employee && data.employee.isTeacher)} />}
```

### 5.3 `features/timeoff/CalendarPanel.jsx`

**Dữ liệu lịch dạy**
- Nhận thêm prop `isTeacher`.
- State `teaching` = `Map<dateStr, count>`.
- `useEffect` phụ thuộc `[isTeacher, scope, year]`: khi `isTeacher && scope === 'me'` → `fetchTeachingDays(`${year}-01-01`, `${year}-12-31`)`, dựng Map từ `resp.days`. Ngược lại đặt Map rỗng. Lỗi gọi API lịch dạy **không** chặn render lịch nghỉ (chỉ bỏ qua đánh dấu dạy).
- Truyền `teaching` + cờ `teacherView = isTeacher && scope === 'me'` xuống `MonthGrid`.

**Tô màu ô ngày (`cellStyle` + `MonthGrid`)** — bảng màu mới:

| Trạng thái | Hiện tại | Mới |
|---|---|---|
| Nghỉ đã duyệt (`validate`) | nền đặc `info.color` + chữ trắng | nền `info.color + '22'` + viền `inset 0 0 0 1px info.color` + chữ `--ink`, đậm |
| Nghỉ chờ duyệt | nền `color+'26'` + viền 1.5px | nền trắng + viền `inset 0 0 0 1.5px info.color` + chữ `info.color` |
| Nghỉ từ chối (`refuse`) | gạch ngang, muted | giữ nguyên |
| Ngày có lịch dạy (chỉ `teacherView`) | — | nền `--blue-bg` (khi ô chưa có nền nghỉ) + vạch trái `--blue` (3px, bo nhẹ); tooltip "N buổi dạy" |
| Cuối tuần | nền xám `--surface-2` | **không** với `teacherView` (số cuối tuần chỉ `--faint`); tài khoản khác giữ xám |
| Thứ 7 đi làm | nền xanh lá + viền | **không** với `teacherView`; tài khoản khác giữ nguyên |
| Ngày bắt buộc/nghỉ lễ | chấm đỏ góc trên-phải | giữ nguyên |
| Trùng lịch ≥3 người (officer, "Cả đội") | viền amber + badge | giữ nguyên |

**Chồng lấn dạy + nghỉ:** nếu ô vừa có lịch dạy vừa có đơn nghỉ → giữ nền/viền của nghỉ, **vẫn** vẽ vạch trái xanh để báo "ngày này có buổi dạy". Tooltip ghép cả hai.

**Cột phải (legend & thông tin)**
- `teacherView`:
  - Legend: thêm dòng "Ngày có lịch dạy" (mẫu nền xanh + vạch); **bỏ** dòng "Ngày đi làm (Thứ 7)".
  - Thay card "Lịch làm việc" (văn phòng: "Chuẩn Thứ 2–Thứ 6…") bằng card "Lịch dạy": ghi chú "Ngày có lịch dạy lấy từ hệ thống CMS." + tổng số ngày dạy / số buổi trong năm.
- Tài khoản khác: giữ nguyên legend & card "Lịch làm việc" như hiện tại.

## 6. Kiểm thử

**Backend** (`hocba_hrm/tests/test_teaching_days.py`): helper `_teaching_days_payload`
- NV không có `x_cms_user_id` / user không có hồ sơ → `{isTeacher:false, days:[]}`.
- `from`/`to` thiếu hoặc sai định dạng → HTTP 400 `invalid_date`.
- `to < from` hoặc khoảng > 366 ngày → HTTP 400 `invalid_range`.
- GV có buổi dạy: đếm đúng số buổi/ngày; loại buổi `cancelled`, buổi ngoài khoảng,
  buổi của GV khác; buổi `substituted` của chính GV vẫn tính.
- Tất cả chạy được ở local (dữ liệu là bản ghi `hocba.teaching.session`, không cần CMS).

**Frontend:** không có test framework → kiểm tra bằng `npm run build` + preview với tài khoản giáo viên: thấy ngày dạy tô xanh ở cả Năm/Tháng, đơn nghỉ màu dịu hơn, không còn xám cuối tuần / xanh lá Thứ 7.

## 7. Rủi ro & lưu ý

- **Dữ liệu Neon:** chỉ đánh dấu các buổi đã có trong `hocba.teaching.session`. Trước
  khi import/gộp đủ dữ liệu, lịch có thể thưa — đúng theo dữ liệu hiện có, không phải lỗi.
- **Tải:** một truy vấn ORM/năm khi đổi năm ở phạm vi "Của tôi"; có chặn khoảng > 366 ngày.
- **GV kiêm officer:** chỉ đánh dấu dạy ở phạm vi "Của tôi"; sang "Cả đội" hành xử như officer thường.
