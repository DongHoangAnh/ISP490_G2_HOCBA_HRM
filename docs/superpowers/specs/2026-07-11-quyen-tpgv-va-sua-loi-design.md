# Thiết kế: Quyền Trưởng phòng/Giáo vụ + sửa lỗi NPT & thu hồi tài sản

**Ngày:** 2026-07-11
**Nhánh:** `feature/quyen-tpgv-va-sua-loi`
**Nguồn:** phản hồi sau khi review kết quả test tay (`docs/KETQUA_TEST_TAY_2026-07-11.md`).

## Bối cảnh

Sau khi chạy test tay 3 module (Nhân viên / Nhận việc / Nghỉ việc), người dùng yêu cầu 4 điều chỉnh. Đã điều tra và xác nhận nguyên nhân gốc trên app đang chạy (Neon, tài khoản HR, NV mẫu Nguyễn Thị Thu Hà — id 6):

| # | Yêu cầu | Loại | Nguyên nhân gốc |
|---|---------|------|-----------------|
| 1 | Ghi rõ luồng duyệt nghỉ việc 2 cấp theo tên nút | Tài liệu | Nút hiện tại: **"Quản lý duyệt"** (cấp 1 = TP/Giáo vụ) → **"HR duyệt"** (cấp 2) → **"Hoàn tất"** |
| 2 | TP/Giáo vụ có quyền thêm/sửa/xoá như HR + xem Lương CB + cấp tài sản, giới hạn trong phạm vi; KHÔNG có quyền tài khoản/phòng ban | Code (BE+FE) | `isHr`/`isHrManager` là cờ kiểm nhóm HR thô → TP/GV hiện chỉ xem |
| 3 | Lỗi "Thêm người phụ thuộc" (NV tự thêm): dropdown Quan hệ trống | Bug (BE+FE) | `/hocba-hrm/api/form/meta` chặn non-HR (main.py:2563); `DependentForm` nuốt 403 → `relationship=[]` |
| 4 | "Cấp tài sản lỗi giao diện mất chữ thu hồi" | Bug (FE) | Ô thao tác AssetsTab (EmployeeDrawer.jsx:494) bị `.tbl td{max-width:0;overflow:hidden}` cắt: td 59px, nút cần 175px → "Thu hồi" bị cắt, "Chuyển" mất hẳn |

## Quyết định đã chốt với người dùng

- TP/GV: **tạo/sửa/xoá đầy đủ** hồ sơ NV + hồ sơ con (NPT, tài sản, chứng chỉ) **trong phạm vi**.
- **Thăng tiến (promotion) giữ nguyên HR-Manager-only**: bản ghi thăng tiến chứa `to_wage` (đổi lương) → nằm ngoài `canEditEmp` để tôn trọng "TP/GV chỉ xem lương".
- TP/GV: **chỉ XEM** Lương CB, **không sửa** mức lương.
- TP/GV: **được cấp/thu hồi/chuyển tài sản** trong phạm vi.
- TP/GV: **không** có tab Tài khoản, **không** có trang Phòng ban.
- **Phạm vi**: TP = phòng ban mình quản lý (`manager_id`, gồm phòng con); Giáo vụ = giáo viên (giữ nguyên định nghĩa hiện có).
- "Xoá": SPA không có nút xoá cứng nhân viên (NV rời qua offboarding — TP/GV vốn là người duyệt cấp 1). "Xoá" ở đây = xoá hồ sơ con (NPT/chứng chỉ) + luồng nghỉ việc sẵn có.
- HR officer (`group_hr_user`) **giữ nguyên**: sửa được, không thấy Lương, không sửa lương, có tab Tài khoản.

## Kiến trúc: cờ năng lực tách khỏi nhóm Odoo

Không thêm TP/GV vào `group_hr_user` (sẽ vô tình cấp quyền tài khoản/phòng ban + phạm vi toàn cục, phá mô hình bảo mật). Thay vào đó tính **cờ năng lực** ở server, enforce phạm vi bằng bộ máy sẵn có (`_emp_scope_domain`, `_emp_in_scope`).

Bốn cờ (server tính, trả trong payload; FE chỉ hiển thị — **BE luôn enforce**):

| Cờ | Đúng với | Ý nghĩa |
|----|----------|---------|
| `canEditEmp` | Admin \| HR \| HR-Mgr \| TP \| GV | Tạo/sửa/xoá NV + hồ sơ con, **trong phạm vi** |
| `canSeeSalary` | Admin \| HR-Mgr \| TP \| GV | **Xem** cột Lương CB + dòng lương trong hồ sơ |
| `canEditSalary` | Admin \| HR-Mgr | Sửa mức lương (tier `mgr`) — không đổi |
| `canManageAccount` | Admin \| HR \| HR-Mgr | Tab Tài khoản + trang Phòng ban — không đổi |

Helper mới trong `controllers/main.py` (đặt cạnh `_user_can_manage`):
```python
def _cap_edit_emp(env):      # Admin | HR user | HR mgr | TP | GV
def _cap_see_salary(env):    # Admin | HR mgr | TP | GV
def _cap_edit_salary(env):   # Admin | HR mgr
def _cap_manage_account(env):# Admin | HR user | HR mgr
```
TP = `_is_dept_manager(env, env.user.employee_id)`; GV = `has_group('hocba_employees.group_hocba_giaovu')`.

## Thành phần & thay đổi

### A. Backend — `custom-addons/hocba_hrm/controllers/main.py`

1. **Cờ trong payload**: `/api/me/roles` (`_role_payload`), `/api/employees`, `/api/employee/<id>`, `/api/form/meta` trả thêm `canEditEmp`, `canSeeSalary`, `canManageAccount` (giữ `isHr`/`isHrManager` để không phá chỗ khác).
2. **Ghi hồ sơ con** — đổi gate `if not is_hr` → `if not _cap_edit_emp(env) or not _emp_in_scope(env, e)`:
   - `api_dependent_create/update/delete` (giữ nhánh self-service `e == user.employee_id`).
   - `api_asset_create/return/transfer`.
   - `api_cert_*`.
   - `api_promotion_*` **giữ nguyên `is_mgr`** (HR-Manager-only, vì đổi lương).
3. **Tạo/sửa NV** (`api_employee_create`, `api_employee_update`):
   - Gate `canEditEmp`.
   - **Tạo**: validate phòng ban đích ∈ phạm vi TP (`_managed_department_ids`) hoặc NV là giáo viên (GV). Ngoài phạm vi → 403.
   - **Sửa**: `_emp_in_scope` với NV đích.
   - **Sudo sau khi kiểm phạm vi**: hiện `create/write` hr.employee KHÔNG sudo (dựa ACL Odoo mà TP/GV không có → AccessError). Đổi sang: gate `canEditEmp` + kiểm phạm vi ở tầng controller RỒI ghi bằng `.sudo()` (theo đúng pattern self-service của dự án). Ràng buộc nghiệp vụ (`@api.constrains`: CCCD, BR-010, gate) vẫn chạy dưới sudo nên không mất.
   - `_split_form_payload`: `wage` vẫn tier `mgr` → TP/GV gửi cũng bị bỏ (đảm bảo "chỉ xem").
4. **Lộ lương theo `canSeeSalary`**: chỗ nào đang dùng `is_mgr` để chèn `wage`/`pit`/`si`/bank vào detail (`_emp_base`, `_employee_detail`, cột Lương ở list) đổi sang `_cap_see_salary(env)`.
5. **Tài khoản/Phòng ban**: giữ gate `is_hr`/admin (không đổi).

### B. Backend — bug #3 (meta cho self-service)

Thêm route nhẹ `GET /hocba-hrm/api/dependent/meta` (`auth='user'`, không chặn HR) trả `{relationship: [...]}` (lấy từ selection của `hr.employee.dependent`). Không mở rộng `/api/form/meta` để tránh lộ danh sách nhạy cảm (employees/banks) cho non-HR.

### C. Frontend

- `api/employees.js`: thêm `fetchDependentMeta = () => hbGet('/hocba-hrm/api/dependent/meta')`.
- `DependentForm.jsx`: đổi `fetchFormMeta()` → `fetchDependentMeta()` để lấy `relationship` (khả dụng cho cả HR lẫn self-service). **[bug #3]**
- `Employees.jsx`: nút "Thêm nhân viên" gate `data.canEditEmp`; cột "Lương CB" gate `data.canSeeSalary`; truyền `canEdit`/`canSeeSalary`/`canManageAccount` xuống drawer.
- `EmployeeDrawer.jsx`: tách prop `isHr` → `canEdit` (nút Chỉnh sửa, InfoTab editable, AssetsTab, NPT, chứng chỉ) và `canManageAccount` (tab Tài khoản); dòng lương trong InfoTab theo `canSeeSalary`; ô lương trong `EmployeeForm` giữ theo `isMgr`.
- `EmployeeDrawer.jsx:494` (AssetsTab) + các ô thao tác NPT/chứng chỉ: thêm `width:'1%', whiteSpace:'nowrap', overflow:'visible', maxWidth:'none'`. **[bug #4]**

### D. Tài liệu

- `docs/MANUAL_TEST_GUIDE.md`:
  - §3 Nghỉ việc: nêu rõ tên nút — TP/GV bấm **"Quản lý duyệt"** (cấp 1) → HR bấm **"HR duyệt"** (cấp 2) → **"Hoàn tất"**. **[item 1]**
  - §4/§5: TP/GV nay kỳ vọng **có** nút Thêm nhân viên, **thấy** cột Lương CB (chỉ xem), sửa hồ sơ + cấp tài sản trong phạm vi; **không** có tab Tài khoản/trang Phòng ban.
- Sau khi code xong: chạy lại các case vai trò TP/GV + 2 bug, cập nhật `docs/KETQUA_TEST_TAY_2026-07-11.md` và bản HTML kèm ảnh.

## Kiểm thử (TDD — backend trước)

Test Odoo (`custom-addons/hocba_hrm/tests/` hoặc `hocba_employees/tests/`):

1. **Bug NPT (model)**: NV thường tạo NPT của mình OK; dropdown meta khả dụng — test route `/api/dependent/meta` trả relationship cho user thường (403 hiện tại → 200 sau fix). *(Kiểm mức controller/route.)*
2. **Cờ năng lực**: `_cap_*` đúng cho 5 vai trò (Admin/HR/HR-Mgr/TP/GV/NV).
3. **Enforce phạm vi ghi**:
   - TP sửa NV **trong** phòng mình OK; NV **ngoài** phòng → 403.
   - GV sửa giáo viên OK; NV non-teacher → 403.
   - TP/GV **tạo** NV trong phạm vi OK; ngoài phạm vi → 403.
   - TP/GV cấp/thu hồi tài sản trong phạm vi OK.
4. **Lương**: TP/GV thấy `wage` trong detail (`canSeeSalary`) nhưng gửi `wage` khi sửa **không** ghi (tier mgr). HR officer **không** thấy `wage`.
5. **Tài khoản**: TP/GV gọi endpoint tài khoản → 403 (không đổi).

Bug #4 (thuần CSS) kiểm bằng verify trực quan trên preview (đo ô thao tác không còn bị cắt), không cần unit test.

Lưu ý test Odoo: `MSYS_NO_PATHCONV=1`, `-u hocba_hrm,hocba_employees`, NV official cần CCCD 12 số/MST/BHXH (BR-010).

## Ngoài phạm vi (YAGNI)

- Không xoá cứng nhân viên trên SPA.
- Không đổi phạm vi Giáo vụ (giữ "giáo viên").
- Không đổi quyền HR officer.
- Không refactor mô hình nhóm Odoo.
