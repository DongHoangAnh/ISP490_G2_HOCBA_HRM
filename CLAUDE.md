# CLAUDE.md — Học Bá HRM (ISP490_G2)

Hệ thống HR cho trung tâm tiếng Trung **Học Bá Education**, xây trên **Odoo 19** (custom-addons) + **SPA React/Vite** nhúng trong Odoo. Đồ án nhóm ISP490 (FPT).

## Kiến trúc

- **Backend**: Odoo 19, chỉ làm trong `custom-addons/` (KHÔNG sửa core Odoo). Module chính:
  - `hocba_employees` — Hồ sơ & vòng đời nhân sự (owner: Vu/Tan, nhánh `Tan/Employee`)
  - `hocba_attendance` — Chấm công, ca làm việc/OT (owner: DongHoangAnh)
  - `hocba_payroll` — Lương, ngân hàng, BHXH, thuế TNCN (owner: Hùng)
  - `hocba_recruitments` — Tuyển dụng (owner: Việt)
  - `hocba_timeoff` — Nghỉ phép (owner: NhatAnh)
  - `hocba_users` — Vai trò/phân quyền · `hocba_hrm` — **controller API + phục vụ SPA**
  - *Legacy/đang dọn:* `hb_timeoff_*`, `hr_holidays_modern`, `hocba_tuyen_dung` (lỗi "not loaded"/"inconsistent states" khi load là **tồn đọng đã biết, vô hại**).
- **Frontend**: `frontend/` (Vite 6 + React 18, **không** TypeScript, **không** eslint/prettier). Build ra `custom-addons/hocba_hrm/static/spa/`, Odoo phục vụ SPA tại route **`/hocba-hrm`**. API: `/hocba-hrm/api/*` (controller trong `hocba_hrm/controllers/main.py`).
- **DB**: mặc định **Neon PostgreSQL cloud** (`neondb`); có stack Docker Postgres local (`hocba_hrm`) để dev/test nhanh.

## Lệnh hay dùng

```bash
# Build SPA (output → custom-addons/hocba_hrm/static/spa)
cd frontend && npm run build
# (Có hook tự build SPA khi sửa frontend/src — xem .claude/settings.local.json)

# Test backend Odoo (Docker local). MSYS_NO_PATHCONV=1 BẮT BUỘC trên Git Bash,
# thiếu nó → chạy 0 test mà vẫn báo OK. Luôn -u <module>,hocba_employees để đồng bộ schema.
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u <module>,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /<module> --stop-after-init --log-level=test
# Kết quả cần thấy: "0 failed, 0 error(s) of N tests" với N > 0.

# Chạy app: stack Neon (mặc định) hoặc local
docker compose -f docker-compose.yml up -d odoo                                  # Neon
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d           # local
```

## Preview (xem app chạy)

- Odoo bind cổng 8069. Trên máy này có thể có **2 Odoo cùng 8069** (native IPv4 vs Docker `[::1]` IPv6) → preview dùng **TCP proxy 8169 → `[::1]:8069`** (script `%TEMP%\hb_tcp_proxy.py`, config `.claude/launch.json`). Nếu script bị xoá → tái tạo rồi `preview_start`.
- Route `/` là trang Website mặc định của Odoo → **vào thẳng `/hocba-hrm`** (app) hoặc `/web/login`.
- Tài khoản test: mật khẩu chung `Hocba@2026` (vd `test_hrmanager@hocba.vn`, `test_giaovu@hocba.vn`, `test_truongphong@hocba.vn`, `test_employee@hocba.vn`). Chi tiết: `docs/DB_TEST_DATA.md`.

## Quy trình làm việc (BẮT BUỘC)

- **Spec trước code**: mọi feature mới phải có spec (file md) được duyệt rồi mới implement. Backend chắc (model/security/API + test) trước, UI sau.
- Áp dụng plugin **superpowers** cho mỗi feature: `brainstorming` (spec) → `writing-plans` (plan TDD) → code đỏ→xanh→commit → `requesting-code-review` → `verification-before-completion` → `finishing-a-development-branch`.
- Làm trên nhánh **`feature/...`** (hoặc nhánh cá nhân `Tên/Module`), **KHÔNG code thẳng `main`**. Commit nhỏ. Merge về main bằng fast-forward khi nhánh đã chứa `origin/main`.
- Spec/plan để ở `docs/superpowers/specs/` + `plans/`. Đặc tả Employees: `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md` (header v2.2).

## Gotcha quan trọng

- **Odoo 19**: `res.users` dùng `group_ids` (không phải `groups_id`); `res.groups` bỏ `category_id`; CCCD `identification_id` nằm trên `hr.version` (không phải `hr.employee`).
- **BR-010**: NV `official` trong test PHẢI có `identification_id` (CCCD) **đúng 12 chữ số**, mỗi NV một giá trị, không thì `ValidationError` ngay setUp.
- **Neon DDL/upgrade**: cài/upgrade module nặng lên Neon phải dùng **endpoint TRỰC TIẾP** (bỏ `-pooler` trong host) — pooler (pgbouncer) rớt SSL giữa transaction DDL dài. Override `HOST` khi chạy compose. Serving (query ngắn) thì pooler OK.
- **Self-service**: user thường không có ACL trên policy/attendance → đọc/ghi qua `.sudo()` SAU khi đã kiểm phạm vi/pin employee.
- **SPA build artifacts** (`static/spa/`) được commit → hay xung đột khi merge; giải bằng **build lại** từ source đã gộp, đừng merge tay bundle.
- Mỗi lần seed/đổi DB → cập nhật `docs/DB_TEST_DATA.md` (bảng tài khoản + nhật ký) cho cả nhóm.

## Phân quyền (tóm tắt)

HR/Admin = tất cả; Trưởng phòng (`hr.department.manager_id`) = phòng mình (gồm phòng con, `_managed_department_ids`); Giáo vụ (`group_hocba_giaovu`) = chỉ giáo viên; user thường = của mình. `canManage` = thuộc bất kỳ nhóm quản lý nào. Màn quản lý (tài khoản vai trò HR/Admin/Giáo vụ) **không** hiển thị "Hồ sơ của tôi".
