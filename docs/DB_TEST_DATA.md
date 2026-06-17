# Dữ liệu test & thay đổi DB (cho cả nhóm)

> **Quy ước:** mỗi khi seed/thay đổi dữ liệu trên DB (tài khoản, dữ liệu mẫu, đổi
> manager phòng ban…) → **cập nhật file này** (bảng tài khoản + mục Nhật ký) để
> thành viên khác test được. Mật khẩu chung các tài khoản test: **`Hocba@2026`**.

---

## 1. Bộ tài khoản test theo vai trò

| Login | Vai trò | Nhóm quyền Odoo | Hồ sơ NV | Test gì |
|---|---|---|---|---|
| `test_admin@hocba.vn` | Admin | `base.group_system` (+HR) | — | Toàn quyền, mọi phòng ban |
| `test_hrmanager@hocba.vn` | HR Manager | `hr.group_hr_manager` | — | Quản lý NV + xem lương + duyệt cổng mọi NV |
| `test_hr@hocba.vn` | HR officer | `hr.group_hr_user` | — | Xem/sửa hồ sơ, **không** thấy lương |
| `test_giaovu@hocba.vn` | Giáo vụ | `hocba_employees.group_hocba_giaovu` | Test Giáo Vụ | **Chỉ thấy giáo viên** |
| `test_truongphong@hocba.vn` | Trưởng phòng | (không nhóm HR) | Test Trưởng Phòng | **Chỉ NV phòng mình**; duyệt cổng dù không có quyền HR |
| `test_employee@hocba.vn` | Nhân viên | (không) | NV Test (Nhân viên) | Self-service: Hồ sơ của tôi, NPT, ảnh |
| `test_ctv@hocba.vn` | Nhân viên (CTV) | (không) | — | Ca "user chưa gắn hồ sơ" |

> `admin` / `admin` là superuser hệ thống có sẵn (không thuộc bộ test).
> Trưởng phòng = officer phân theo phòng ban; với SPA (sudo sau kiểm phạm vi) thì
> tài khoản thường vẫn duyệt được cổng NV trong phòng mình.

**Dữ liệu kèm theo (do seed tạo):**
- Phòng ban **"Phòng Test (QA)"** — `Test Trưởng Phòng` làm trưởng phòng.
- NV trong QA: Test Trưởng Phòng, Test Giáo Vụ, NV Test, **NV Thử Việc QA** (thử việc Nhóm B để test duyệt cổng), 2 giáo viên (GV Tiếng Trung A/B).

---

## 2. Trạng thái theo từng DB

| DB | Tài khoản test | Dữ liệu mẫu khác |
|---|---|---|
| **Local** (Docker `hocba_hrm`) | ✅ Đã seed (7 TK) | ✅ Chấm công hôm nay (5 bản ghi) |
| **Neon** (`neondb`) | ❌ **CHƯA seed** | ❌ Chưa |

---

## 3. Cách tạo lại (idempotent — chạy nhiều lần không nhân đôi)

Script: `_demo_seed/seed_test_accounts.py` (thư mục `_demo_seed/` bị `.gitignore`
→ giữ local; nội dung tài khoản đã liệt kê ở mục 1 để tái dựng nếu mất).

**Trên DB local (Docker):**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T odoo \
  odoo shell -d hocba_hrm --db_host=db --db_port=5432 --db_user=odoo \
  --db_password=odoo_password --addons-path=/mnt/extra-addons --no-http \
  < _demo_seed/seed_test_accounts.py
```

**Trên Neon** (lấy creds từ `.env`; cần `--db_sslmode=require`): _chưa chạy được do
container local-override không egress tới Neon — dùng base compose hoặc máy có
psql nối Neon._

> Lưu ý Odoo 19: `res.users` dùng field **`group_ids`** (không phải `groups_id`);
> `res.groups` **không còn `category_id`**.

---

## 4. Nhật ký thay đổi DB

| Ngày | DB | Thay đổi | Người |
|---|---|---|---|
| 2026-06-17 | Local `hocba_hrm` | Seed 7 tài khoản test + phòng "Phòng Test (QA)" + NV test (script `seed_test_accounts.py`) | Vu/Claude |
| 2026-06-17 | Local `hocba_hrm` | Seed 5 bản ghi chấm công hôm nay (3 đúng giờ, 2 muộn) — script `_demo_seed/seed_attendance_demo.py` | Vu/Claude |
| 2026-06-17 | Neon `neondb` | _CHƯA seed tài khoản test (đang chờ)_ | — |
