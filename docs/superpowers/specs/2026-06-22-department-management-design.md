# Spec — Quản lý Phòng ban (Department Management)

- **Ngày**: 2026-06-22
- **Module**: `hocba_hrm` (controller/API + SPA) trên model `hr.department` (kế thừa ở `hocba_employees`)
- **Quy trình**: superpowers (brainstorming → writing-plans → TDD). Backend chắc trước, UI sau.

## 1. Mục tiêu & phạm vi

Thêm chức năng **CRUD quản lý phòng ban** trong SPA `/hocba-hrm`, dùng API thật + dữ liệu thật (không mock).

**Trong phạm vi**:
- Xem danh sách phòng ban (Tên, Chức năng, Trưởng phòng, Số nhân viên).
- Tạo / Sửa phòng ban.
- Lưu trữ (archive) / Khôi phục phòng ban; chặn xóa cứng khi còn nhân viên hoặc còn phòng con.

**Ngoài phạm vi** (YAGNI):
- Cây phân cấp phòng cha/con trong form (không hiển thị/sửa `parent_id`).
- Thêm field "mã phòng ban" mới.
- Phân quyền trưởng phòng được sửa phòng mình (chỉ HR/Admin CRUD).
- Sơ đồ tổ chức (org chart).

## 2. Quyết định đã chốt (từ brainstorming)

| Câu hỏi | Quyết định |
|---|---|
| Phạm vi | CRUD quản lý phòng ban (full-stack, API thật) |
| Ai được CRUD | **Chỉ HR/Admin** (`hr.group_hr_user` / `base.group_system`); người khác chỉ xem hoặc bị chặn |
| Xóa phòng còn NV/phòng con | **Chặn xóa cứng** + cho **archive** + báo "chuyển nhân viên trước" |
| Trường trong form | Tên + Chức năng (`x_function_desc`) + Trưởng phòng (`manager_id`) + Số NV (read-only) |
| Phòng cha (cây) | Không đưa vào form |
| Cách triển khai | Hướng A — full-stack backend-first theo TDD |

## 3. Kiến trúc

Bám pattern "account management" đã hoàn thành (`_account_*` trong `controllers/main.py`, `tests/test_account.py`):

- **Model**: `hr.department` — bổ sung ràng buộc chặn xóa (không thêm field mới).
- **API**: helper functions cấp module trong `hocba_hrm/controllers/main.py`, routes mỏng `/hocba-hrm/api/departments*`, guard bằng `_is_hr(env)`.
- **SPA**: màn mới "Phòng ban" trong NAV, file `hrm-departments.jsx`, gọi API qua `hbGet`/`hbPost`.
- **Test**: `hocba_hrm/tests/test_department.py` gọi helper trực tiếp.

## 4. Model & ràng buộc (`hr.department`)

Tận dụng field chuẩn Odoo 19: `name`, `manager_id` (M2o `hr.employee`), `active`, `total_employee` (đếm NV), `member_ids`, `child_ids`; field custom có sẵn `x_function_desc`.

**Ràng buộc chặn xóa** (`@api.ondelete(at_uninstall=False)` trên model inherit):
- Nếu phòng còn `member_ids` HOẶC có `child_ids` → raise `UserError`:
  > "Phòng ban '<tên>' còn N nhân viên / có phòng con. Vui lòng chuyển nhân viên sang phòng khác trước, hoặc lưu trữ phòng ban."

**Archive**: dùng field `active` chuẩn Odoo. `active=False` để lưu trữ (ẩn khỏi danh sách mặc định), `active=True` để khôi phục. Không xóa dữ liệu → giữ lịch sử phân công.

> Lưu ý xác minh khi implement: tên field đếm nhân viên của Odoo 19 (`total_employee`) — TDD sẽ phát hiện nếu sai.

## 5. API endpoints (`hocba_hrm/controllers/main.py`)

Tất cả guard bằng `_is_hr(env)` → ngoài HR/Admin trả `403 forbidden`. Ghi qua `.sudo()` sau khi đã check quyền (nhất quán với `_account_*`).

| Method | Route | Helper | Mô tả |
|---|---|---|---|
| GET | `/hocba-hrm/api/departments` | `_dept_list(env, archived=False)` | Danh sách phòng ban + danh mục NV (cho dropdown trưởng phòng). `?archived=1` → gồm phòng đã lưu trữ |
| POST | `/hocba-hrm/api/department` | `_dept_create(env, body)` | Tạo phòng ban mới |
| POST | `/hocba-hrm/api/department/<int:id>` | `_dept_update(env, id, body)` | Sửa tên / chức năng / trưởng phòng |
| POST | `/hocba-hrm/api/department/<int:id>/archive` | `_dept_archive(env, id, body)` | Lưu trữ (`active=False`) / khôi phục (`active=True`) |

**Payload mỗi phòng** (`_dept_payload(dept)`):
```json
{ "id": 1, "name": "Marketing", "functionDesc": "...",
  "managerId": 5, "managerName": "Nguyễn Văn A",
  "employeeCount": 8, "active": true }
```

**Body tạo/sửa**: `{ "name": "...", "functionDesc": "...", "managerId": 5 }`
- `name` bắt buộc, không trống.
- `managerId` có thể rỗng (`false`/null) → không gán trưởng phòng.

**`_dept_list` trả về**:
```json
{ "departments": [ <payload>, ... ],
  "employees": [ { "id": 5, "name": "...", "code": "..." }, ... ] }
```

**Quy ước lỗi** (giống account management):
- `403 forbidden` — không phải HR/Admin (`AccessError`).
- `400 rejected` — `ValidationError` (tên trống / trùng) kèm `message`.
- `400 rejected` / `409` — `UserError` khi archive/xóa phòng còn NV, kèm message hướng dẫn.

## 6. Màn SPA "Phòng ban"

- **NAV** (`hrm-shell.jsx`): thêm `{ id:'departments', label:'Phòng ban', icon:'building' }` vào nhóm "Quản lý nhân sự". Chỉ hiển thị khi `role.isHrUser || role.isAdmin` (đọc từ `/api/me/roles`).
- **File mới** `static/src/js/hrm-departments.jsx`, đăng ký entry trong `hrm-app.jsx` (và cấu hình build Vite nếu cần):
  - *Danh sách*: bảng/card mỗi phòng — Tên, Chức năng, Trưởng phòng, Số NV; nút **Sửa**, **Lưu trữ/Khôi phục**; toggle "Hiện phòng đã lưu trữ".
  - *Form tạo/sửa* (modal): Tên (bắt buộc), Chức năng, Trưởng phòng (dropdown NV từ `employees`). Số NV read-only.
  - Helper mới `hbPost(url, body)` (POST JSON, `credentials:'same-origin'`) cạnh `hbGet`.
  - Trạng thái loading / error; hiển thị `message` lỗi từ API (vd chặn xóa khi còn NV).

## 7. Kiểm thử (`hocba_hrm/tests/test_department.py`)

TDD đỏ→xanh, `TransactionCase`, gọi helper trực tiếp (mô phỏng `test_account.py`). Setup: tạo user HR + user thường + 1 phòng + vài NV.

Các case:
- **Quyền**: user thường gọi `_dept_list` / `_dept_create` / `_dept_update` / `_dept_archive` → `AccessError`.
- **Tạo**: tên hợp lệ → tạo OK, payload đúng các field; tên trống → `ValidationError`.
- **Sửa**: đổi tên / chức năng / gán `managerId` → ghi đúng; gỡ trưởng phòng (managerId rỗng) → OK.
- **Chặn xóa**: `dept.unlink()` khi còn `member_ids` → `UserError`; khi có `child_ids` → `UserError`.
- **Archive**: phòng rỗng `_dept_archive(active=False)` → `active=False`; khôi phục → `active=True`.
- **employeeCount**: payload phản ánh đúng số nhân viên của phòng.

**Lệnh test** (theo CLAUDE.md, Git Bash + Docker local):
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Kết quả cần thấy: `0 failed, 0 error(s) of N tests` với N > 0.

## 8. Thứ tự thực hiện (TDD, backend trước)

1. Model: ràng buộc `@api.ondelete` chặn xóa → test xóa (đỏ→xanh).
2. API helpers `_dept_payload` / `_dept_list` / `_dept_create` / `_dept_update` / `_dept_archive` + routes → test quyền/CRUD/archive (đỏ→xanh).
3. SPA: NAV + `hrm-departments.jsx` + `hbPost` → build SPA, verify trên preview.
4. `requesting-code-review` → `verification-before-completion` → cập nhật `docs/DB_TEST_DATA.md` nếu có seed → `finishing-a-development-branch`.

Làm trên nhánh `feature/department-management` (không code thẳng `main`).
