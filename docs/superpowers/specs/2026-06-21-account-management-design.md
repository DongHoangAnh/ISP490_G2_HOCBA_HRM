# Spec — Quản lý tài khoản đăng nhập (Account Management)

- **Ngày:** 2026-06-21
- **Module:** `hocba_hrm` (controller + SPA), liên kết `hr.employee` ↔ `res.users`
- **Nhánh:** `feature/account-management` (nhánh từ `Tan/Employee`)
- **Trạng thái:** Đã duyệt thiết kế, chờ review spec → writing-plans

## 1. Mục tiêu & logic cốt lõi

> **Logic quan trọng nhất:** HR/Admin (manager) **cung cấp tài khoản** (nhập login, mật khẩu, xác nhận mật khẩu) khi có nhân viên mới. Nhân viên **không thể tự đăng ký** tài khoản. Khi quên mật khẩu, **HR/Admin cấp lại** mật khẩu.

Tạo lớp quản lý tài khoản đăng nhập gắn với hồ sơ nhân viên, do HR/Admin thao tác hoàn toàn trong SPA. Hỗ trợ **2 loại tài khoản**: thường và quản lý (giáo vụ / trưởng phòng).

## 2. Quyết định đã chốt

| Vấn đề | Chốt |
|---|---|
| Ai cấp/cấp lại TK | **Chỉ HR/Admin** (`is_hr` trong controller) |
| Login | HR **tự nhập** (email hoặc username), duy nhất |
| Cấp lại mật khẩu | HR **nhập mật khẩu mới trực tiếp** (+ xác nhận) |
| Vị trí UI | **Cả hai**: khu TK trong hồ sơ NV + trang danh sách TK |
| Loại TK | Thường / Quản lý |
| Map quyền QL | **Giáo vụ** = gán `group_hocba_giaovu`; **Trưởng phòng** = đặt `manager_id` của phòng được chọn |
| Tự đăng ký | **Không** — không có luồng self-signup |

## 3. Dữ liệu & quan hệ

- Dùng sẵn `hr.employee.user_id` (Odoo chuẩn) liên kết NV ↔ `res.users`. **Không thêm model mới.**
- "Có tài khoản" = `employee.user_id` tồn tại. Login = `user_id.login`. Trạng thái = `user_id.active`.

## 4. API endpoints (controller `hocba_hrm`)

| Method | Route | Việc |
|---|---|---|
| POST | `/hocba-hrm/api/employee/<id>/account` | Tạo TK: `{login, password, password_confirm, role, department_id?}` |
| POST | `/hocba-hrm/api/employee/<id>/account/reset` | Cấp lại MK: `{password, password_confirm}` |
| GET | `/hocba-hrm/api/accounts` | Danh sách TK cho trang tổng |

- Cả 3 endpoint kiểm `is_hr` (HR/Admin); không phải → `403 forbidden`.
- Tạo/ghi `res.users` qua `.sudo()` **sau khi** đã kiểm quyền.
- Payload `_employee_detail` bổ sung khối: `account: {hasAccount, login, active, roleLabel}`.

`role` nhận một trong: `employee` | `giaovu` | `truongphong`.

## 5. Logic tạo tài khoản

- Tạo `res.users` (sudo): `login`, `password`, `name` = tên NV, **`group_ids` gồm `base.group_user`** (internal user → mới truy cập được SPA `auth='user'`).
- Theo `role`:
  - `employee` → chỉ `base.group_user`.
  - `giaovu` → thêm `group_hocba_giaovu`.
  - `truongphong` → bắt buộc `department_id`; đặt `department.manager_id` = nhân viên này. Nếu phòng đã có trưởng phòng khác → trả cảnh báo, yêu cầu xác nhận ghi đè (FE gửi lại với cờ xác nhận).
- Gán `employee.user_id = new_user`.

## 6. Logic cấp lại mật khẩu

- Yêu cầu NV **đã có** `user_id`; chưa có → `400`.
- Ghi `user_id.sudo().password = password` sau khi validate.

## 7. Validation

- `login` không rỗng, **duy nhất** (trùng → `400` "Login đã tồn tại").
- `password == password_confirm`; độ dài **≥ 8 ký tự**.
- Tạo TK chỉ khi NV **chưa có** `user_id`; đã có → `400` (phải dùng reset).
- `role = truongphong` mà thiếu `department_id` → `400`.

## 8. Frontend (SPA)

- **Trong hồ sơ NV (EmployeeDrawer):** khu "Tài khoản đăng nhập".
  - Chưa có TK → nút **Tạo tài khoản** → modal: login, mật khẩu, xác nhận mật khẩu, chọn loại (thường/giáo vụ/trưởng phòng), chọn phòng nếu trưởng phòng.
  - Đã có TK → hiện login + trạng thái + nút **Cấp lại mật khẩu** (modal: MK mới + xác nhận).
- **Trang "Tài khoản" (menu mới, chỉ HR/Admin):** bảng NV — login — loại — trạng thái — nút Tạo/Cấp lại.

## 9. Test (TDD, backend trước)

- Tạo TK: thường / giáo vụ (kiểm `group_hocba_giaovu`) / trưởng phòng (kiểm `department.manager_id`).
- Chặn: không phải HR (`403`), login trùng, MK lệch, MK < 8 ký tự, tạo khi đã có TK, trưởng phòng thiếu phòng.
- Reset: đổi được MK; chặn non-HR; chặn khi chưa có TK.
- Payload `account` trong `_employee_detail` phản ánh đúng trạng thái.

## 10. Ngoài phạm vi (để sau)

- Khóa/vô hiệu hóa tài khoản khi nhân viên nghỉ việc.
- Đổi vai trò sau khi đã tạo tài khoản.
- Cấp lại mật khẩu qua email.

## 11. Lưu ý kỹ thuật

- Odoo 19: `res.users` dùng `group_ids` (không phải `groups_id`).
- SPA `auth='user'` → tài khoản phải là internal user (`base.group_user`) mới truy cập được `/hocba-hrm`.
- Không có self-signup: đảm bảo Odoo không bật `auth_signup` cho phép đăng ký công khai.
