# Tách màn chấm công OT/ca ra riêng — Thiết kế

- **Ngày**: 2026-06-19
- **Owner**: Hoàng Anh
- **Liên quan**: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md (Gói 4C)

## 1. Vấn đề

Hiện check-in/check-out cho OT **không hoạt động**, đặc biệt với NV `official`:

- Định tuyến check-in/out dựa trên `x_employment_status` (`custom-addons/hocba_hrm/controllers/main.py:1868`):
  nhánh `official` → `_assert_check_allowed` (chấm công ngày thường, **bỏ qua ca/OT**);
  nhánh non-official → `_assert_shift_check_allowed` (chấm theo ca).
- `hocba.attendance` chỉ có **1 bản ghi/người/ngày** (`hr_attendance.py:270`), không thể chứa
  vừa chấm công thường vừa chấm công OT, và một ngày có thể có **nhiều ca OT**.
- Kết quả: NV official có ca OT được duyệt không có đường nào để chấm công OT
  (đụng `already_checked_in` với bản ghi ngày thường).

FE: `CheckInPanel.jsx` gộp cả 2 luồng, rẽ nhánh theo `me.isOfficial`.

## 2. Mục tiêu

- Tách **chấm công theo ca** (cả `ctv` lẫn `ot`) sang một model + một màn riêng.
- `hocba.attendance` từ nay **chỉ phục vụ official ngày thường**.
- Mỗi ca được chấm độc lập (hỗ trợ nhiều ca/ngày), giờ công tính theo **giờ chấm thực tế**.
- Cập nhật cách tính "công" để cộng công ca/OT vào tổng công.

## 3. Phạm vi & phân vai

| | Màn **"Chấm công của tôi"** (giữ) | Màn **chấm công ca** (mới) |
|---|---|---|
| Đối tượng | NV `official` — ngày thường | Mọi NV có **ca approved** hôm nay (ctv + ot) |
| Nhãn tab | "Chấm công của tôi" | official → **"Chấm công OT"**; CTV → **"Chấm công"** |
| Lưu ở | `hocba.attendance` (1/người/ngày) — **không đổi** | `hocba.shift.attendance` (1/ca) — **model mới** |
| Luồng | Workday check-in (`_assert_check_allowed`) | Per-shift check-in, cửa sổ ±W quanh start/end từng ca |

Gỡ: nhánh non-official trong `CheckInPanel.jsx:96-129` và nhánh `else` (shift check) trong
`main.py:1870-1871`. Non-official thấy thông báo điều hướng sang tab chấm công ca.

## 4. Model mới `hocba.shift.attendance`

Một bản ghi cho mỗi ca được chấm công.

Trường:
- `shift_id` — m2o `hocba.work_shift`, `ondelete='cascade'`, **unique** (1 chấm công/ca).
- `employee_id` — related `shift_id.employee_id`, store.
- `check_in`, `check_out` — Datetime.
- `check_in_photo`, `check_out_photo` — ảnh base64.
- `check_in_lat`, `check_in_lng`, `check_out_lat`, `check_out_lng` — float.
- `check_in_face_score`, `check_out_face_score` — float.
- `face_suspect`, `out_of_zone`, `out_of_window` — boolean (cờ review).
- `worked_hours` — computed = `(check_out − check_in)` giờ; 0 nếu thiếu mốc.

ACL: nhân viên tự đọc/ghi bản ghi của mình (qua sudo trong controller như luồng attendance hiện tại);
manager đọc trong phạm vi.

### Tái dùng logic face/geo

Tách phần tính face_score / face_suspect / out_of_zone trong `hocba.attendance._do_check`
(`hr_attendance.py:233-254`) thành **helper dùng chung** (vd `_eval_face_geo(employee, payload)` trả
`{face_score, face_suspect, out_of_zone}`), để cả `hocba.attendance` và `hocba.shift.attendance` gọi,
tránh lặp. `out_of_window` tính riêng theo từng model.

## 5. Backend API

### 5.1 `GET /hocba-hrm/api/attendance/me` (sửa)
Bổ sung `shiftsToday: [...]` — mảng ca approved hôm nay của user, mỗi phần tử:
`{ id, start, end, shiftType, otLevel, rate, checkIn, checkOut,
   checkInOpen, checkOutOpen, faceSuspect, outOfZone, outOfWindow }`.
Thay cho `shiftToday` đơn lẻ. `checkInOpen`/`checkOutOpen` = đang trong cửa sổ ±W và chưa chấm xong.

### 5.2 Routes chấm công ca (mới)
- `POST /hocba-hrm/api/attendance/shift/<int:shift_id>/check-in`
- `POST /hocba-hrm/api/attendance/shift/<int:shift_id>/check-out`

Validate (raise UserError mã lỗi → map HTTP, theo mẫu `_CHECK_ERR_STATUS`):
- `no_shift` / `forbidden` — ca không tồn tại hoặc không thuộc employee của user.
- ca phải `state == 'approved'`.
- `outside_shift_window` — ngoài cửa sổ ±W quanh start (check-in) / end (check-out).
- `already_checked_in` / `not_checked_in` / `already_checked_out` — theo bản ghi `hocba.shift.attendance` của ca.
- Body giống check thường: `{ photo, descriptor, latitude, longitude }`.

### 5.3 Hệ số theo loại ca
- `_shift_create` (`main.py:577-613`): nếu `shift_type == 'ctv'` thì ép `ot_level = '100'`
  (bỏ qua giá trị client gửi).
- `_shift_set_level` (`main.py:692-706`): chỉ cho đổi mức khi `shift.shift_type == 'ot'`;
  ca `ctv` raise ValidationError ("Ca CTV cố định 100%.").

## 6. Cách tính "công"

`_OT_RATE = {'100':1.0, '150':1.5, '300':3.0}` (giữ nguyên).

- **Giờ chấm thực tế** của ca = `check_out − check_in` từ `hocba.shift.attendance`
  (thay cho `end − start` kế hoạch). Ca chưa có đủ 2 mốc → giờ = 0.
- **Công của 1 ca** (dùng chung ctv & ot): `công_ca = giờ_chấm / 8 × hệ số`.
  - CTV: hệ số luôn 1.0 → `công = giờ_chấm / 8`.
  - OT: `công_ot = giờ_OT / 8 × hệ số`.
- **Công ngày thường (official)**: **giữ nguyên** cơ chế nửa-ngày `work_credit` ∈ {0, 0.5, 1.0}
  (`hr_attendance.py:127-157`).
- **Tổng công** = `Σ work_credit (ngày thường) + Σ công_ca`.
  - Official: ngày thường + công OT.
  - CTV: chỉ Σ công_ca (không có công ngày thường).

### Cập nhật tổng hợp
- `_ot_row` / `_ot_table` / `_ot_for_employee` (`main.py:247-323`): `counted` và giờ lấy từ
  `hocba.shift.attendance` (đã check-in/out) thay vì `hocba.attendance` theo ngày; thêm trường
  `congCa = giờ_chấm/8 × rate`. `_ot_table` gồm cả ca `ctv`.
- `_att_me_history` (`main.py:326-367`): `totalCredit` bao gồm Σ công_ca; thêm `congOt`
  (Σ công ca `ot`) cho official và Σ công_ca cho CTV.

## 7. Frontend

- **Component mới** `ShiftAttendance.jsx` (+ `OtCheckInPanel`): liệt kê `me.shiftsToday`,
  mỗi ca 1 thẻ với camera (tái dùng `useFaceApi`), nút check-in/out (bật theo `checkInOpen`/`checkOutOpen`),
  badge trạng thái + cửa sổ. Gọi `shiftCheckIn(shiftId, cap)` / `shiftCheckOut(shiftId, cap)`.
- **API** `frontend/src/api/attendance.js`: thêm `shiftCheckIn`, `shiftCheckOut`.
- **Tab** `Attendance.jsx:38-40`: thêm tab NV cho màn chấm công ca, nhãn động theo `me.isOfficial`
  ("Chấm công OT" / "Chấm công").
- **CheckInPanel.jsx**: chỉ còn luồng official; non-official hiển thị điều hướng sang tab chấm công ca.
- **ShiftForm.jsx**: ẩn ô "Mức hệ số" khi `shiftType === 'ctv'` (hiển thị cố định 100%).
- **MyHistory.jsx**: card "Giờ OT quy đổi" → **"Công OT"** (đơn vị công); "Tổng công" đã gồm công ca/OT.
- **OtTable.jsx**: cột "Giờ quy đổi" → **"Công"**; dropdown mức chỉ bật cho ca `ot`.
- **Build lại SPA** (`static/spa/assets`) sau khi sửa FE.

## 8. Test (TDD — viết test trước)

Backend (`custom-addons/hocba_*/tests`):
- Tạo model `hocba.shift.attendance`: ràng buộc unique theo `shift_id`, `worked_hours` đúng.
- Shift check-in/out: trong cửa sổ OK; ngoài cửa sổ → `outside_shift_window`; ca chưa approved → lỗi;
  nhiều ca/ngày chấm độc lập; không đụng `hocba.attendance` ngày thường của official.
- Hệ số: `_shift_create` ép `ot_level='100'` cho ctv; `_shift_set_level` chặn ca ctv.
- Công: `công_ca = giờ_chấm/8 × rate`; tổng công official = work_credit + công OT;
  tổng công CTV = Σ giờ_chấm/8.

## 9. Ngoài phạm vi (YAGNI)

- Không đổi cơ chế công nửa-ngày của official ngày thường.
- Không gộp `hocba.attendance` và `hocba.shift.attendance` thành một bảng.
- Không thêm loại ca mới ngoài `ctv`/`ot`.
