# ĐẶC TẢ MODULE `hocba_users` — XÁC THỰC & PHÂN QUYỀN

**Phiên bản:** 1.0 (as-built) · **Ngày:** 12/06/2026 · **Trạng thái:** Đã implement & test (xem `TEST_BACKEND_2026-06-12.md`)

> Tài liệu này đặc tả hệ thống tài khoản – vai trò – phân quyền của Học Bá HRM. Nguyên tắc cốt lõi: **role không phải là nhãn trang trí — gán role là gán quyền Odoo thật** (commit `f9b7288`).

---

## 1. Mục tiêu & phạm vi

- Quản lý tài khoản người dùng HRM tách khỏi `res.users` thuần (thêm vòng đời: role, khóa/mở, last login, liên kết hồ sơ nhân viên).
- 4 vai trò chuẩn, mỗi vai trò ánh xạ sang một tập `res.groups` của Odoo.
- Cổng đăng nhập riêng `/hocba/login` (kiểm tra thêm điều kiện tài khoản HRM) bên cạnh `/web/login` chuẩn.
- Dashboard điều hướng theo vai trò tại `/hocba/dashboard`.

Ngoài phạm vi: SSO/OAuth, 2FA, self-service đổi mật khẩu (dùng cơ chế Odoo chuẩn).

## 2. Mô hình dữ liệu

### 2.1. `hocba.user.role` — Vai trò
| Field | Kiểu | Ghi chú |
|---|---|---|
| `name` | Char, required | Tên hiển thị |
| `code` | Char, required, **unique** | `admin` / `hr_manager` / `employee` / `contractor` |
| `group_ids` | M2M → `res.groups` | **Tập quyền Odoo thật của role** |
| `sequence`, `description`, `permissions`, `active`, `color_code` | | Phụ trợ hiển thị |

**Seed 4 role chuẩn** (data `hocba_user_role_data.xml`, noupdate):

| Role | Code | Nhóm Odoo được gán |
|---|---|---|
| Admin | `admin` | `base.group_system` + `hr.group_hr_manager` |
| HR Manager | `hr_manager` | `hr.group_hr_manager` |
| Employee | `employee` | `base.group_user` |
| Contractor | `contractor` | `base.group_user` |

### 2.2. `hocba.user` — Tài khoản HRM
| Field | Kiểu | Ghi chú |
|---|---|---|
| `user_id` | M2O → `res.users`, required, **unique**, cascade | 1 res.users ↔ tối đa 1 hocba.user |
| `role_id` | M2O → `hocba.user.role`, required, restrict | |
| `role_code`, `email`, `department_id` | related, stored | |
| `employee_id` | M2O → `hr.employee`, set null | Liên kết hồ sơ nhân viên |
| `employee_type_id` | related qua `employee_id.x_employee_type_id` | Single source tại `hocba_employees` |
| `is_active` | Boolean | Khóa/mở — đồng bộ sang `res.users.active` |
| `last_login`, `created_at`, `updated_at` | Datetime | `last_login` chỉ ghi sau khi xác thực thành công |

### 2.3. Model phụ
- `hocba.access.control` — quyền truy cập chi tiết theo user (one2many từ hocba.user).
- `hocba.department.manager` — gán user quản lý phòng ban.

## 3. Business rules

| Mã | Quy tắc | Cài đặt |
|---|---|---|
| BR-U01 | Gán role khi tạo `hocba.user` → user nhận ngay các `res.groups` của role | `create()` → `_sync_role_groups()` |
| BR-U02 | Đổi role → **gỡ nhóm của role cũ**, thêm nhóm role mới (nhóm implied Odoo tự tính lại) | `write()` lưu old_roles trước super |
| BR-U03 | Khóa (`is_active=False`) → set `res.users.active=False` → chặn đăng nhập ở **mọi** cổng (cả `/web/login`) | `write()` đồng bộ |
| BR-U04 | 1 `res.users` chỉ có 1 `hocba.user` | `models.Constraint` unique |
| BR-U05 | Không nhập tên → tự lấy tên từ `res.users` | `create()/write()` |
| BR-U06 | `updated_at` tự cập nhật mỗi lần ghi (merge vào vals, KHÔNG gán trong loop sau super — tránh đệ quy) | `write()` |

## 4. Luồng xác thực

### 4.1. `/hocba/login` (GET, public) → render form đăng nhập custom.

### 4.2. `/hocba/do_login` (POST, public)
1. Thiếu email/password → render lại form + lỗi.
2. Tìm `res.users` theo **email**; không thấy → lỗi chung "Invalid credentials" (không lộ user tồn tại hay không).
3. Tìm `hocba.user` của user đó; **không có hồ sơ HRM hoặc `is_active=False` → từ chối** (kể cả mật khẩu đúng).
4. `request.session.authenticate(env, {'login', 'password', 'type': 'password'})` (chữ ký Odoo 19); sai mật khẩu → AccessDenied → lỗi chung.
5. Thành công → ghi `last_login` → redirect `/web`.

### 4.3. `/hocba/logout` → đăng xuất, quay về `/hocba/login`.

### 4.4. `/hocba/dashboard` (auth=user)
Đọc `hocba.user` của user hiện tại bằng **sudo** (user thường không có ACL trên `hocba.user`; domain khóa theo `request.uid` nên không lộ dữ liệu) → render template theo `role_code`: `admin_dashboard` / `hr_manager_dashboard` / `employee_dashboard` (mặc định).

## 5. Ma trận phân quyền

### 5.1. ACL (`ir.model.access.csv`)
| Model | `hr.group_hr_user` (HR Officer) | `hr.group_hr_manager` |
|---|---|---|
| hocba.user.role | đọc | full |
| hocba.user | đọc | full |
| hocba.access.control | đọc | full |
| hocba.department.manager | đọc | full |

User thường (`base.group_user`, role Employee/Contractor) **không có ACL** → mọi truy cập ORM trực tiếp vào các model trên bị chặn.

### 5.2. Record rules (`security_rules.xml`)
| Rule | Nhóm | Hiệu lực |
|---|---|---|
| Own Record Only | hr.group_hr_user | Chỉ thấy `hocba.user` có `user_id = chính mình` (read-only) |
| All for Managers | hr.group_hr_manager | Thấy/sửa tất cả |
| Access Control self/manager | tương tự | theo `user_id.user_id` |

### 5.3. Hệ quả thực tế theo role (đã test 12/06/2026)
| Hành vi | Employee/CTV | HR Officer | HR Manager | Admin |
|---|---|---|---|---|
| Đăng nhập `/web` + `/hocba/login` | ✅ | ✅ | ✅ | ✅ |
| Đọc danh sách hocba.user | ❌ AccessError | chỉ bản ghi của mình | tất cả | tất cả |
| Sửa hr.employee | ❌ | ✅ (trừ field manager-only) | ✅ | ✅ |
| Đọc `x_pit_code`/`x_social_insurance_no` | ❌ | ❌ (field groups) | ✅ | ✅ |
| Điền kết quả 2 cổng thử việc | ❌ | chỉ khi là quản lý trực tiếp | ✅ | ✅ |
| Tạo/sửa role, gán role | ❌ | ❌ | ✅ | ✅ |
| Settings hệ thống | ❌ | ❌ | ❌ | ✅ (`base.group_system`) |

## 6. Tài khoản test (db `hocba_hrm`)
Mật khẩu chung `Hocba@2026`: `test_admin@hocba.vn` (Admin), `test_hrmanager@hocba.vn` (HR Manager), `test_employee@hocba.vn` (Employee — gắn nhân viên `HB.TEST`), `test_ctv@hocba.vn` (Contractor).

### 5.4. Lưu ý Odoo 19: user thường và `hr.employee.public`
User không thuộc nhóm HR khi truy vấn `hr.employee` sẽ bị Odoo tự ủy quyền qua **`hr.employee.public`** (chỉ chứa field công khai chuẩn). Hệ quả (đã verify 12/06/2026): đọc field thường (`name`, `work_email`, `department_id`) → OK; search/đọc **mọi field custom `x_`** → bị chặn (`Invalid field hr.employee.public.x_...`). Tức field nghiệp vụ Học Bá mặc định chỉ hiện với nhóm HR trở lên — đúng chủ đích bảo mật, cần nhớ khi sau này làm màn self-service cho nhân viên (sẽ phải expose có kiểm soát).

## 7. Vấn đề đã biết / nợ kỹ thuật
- `hocba.access.control` và `hocba.department.manager` mới ở mức khung dữ liệu — chưa có nghiệp vụ đọc các bảng này khi kiểm tra quyền (quyền thật hiện dựa hoàn toàn vào `res.groups`).
- Dashboard template còn sơ khai; sẽ thay bằng giao diện Odoo backend đã theme (xem định hướng UI 11/06).
- Đăng nhập bằng **email** tại `/hocba/do_login` yêu cầu email duy nhất giữa các user — Odoo không ràng buộc; cân nhắc thêm constraint hoặc chuyển sang login.
