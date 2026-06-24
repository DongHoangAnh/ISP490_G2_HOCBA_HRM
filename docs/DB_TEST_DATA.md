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
| **Neon** (`neondb`) | ✅ **Đã seed (7 TK)** — 2026-06-19 | ❌ Chưa (chấm công demo) |

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

**Trên Neon** (base compose tự dùng creds `.env` + `sslmode=require`):
```bash
docker compose -f docker-compose.yml run --rm --no-deps -T odoo \
  odoo shell -d neondb --addons-path=/mnt/extra-addons --no-http \
  < _demo_seed/seed_test_accounts.py
```
> ✅ **Đã thông (2026-06-19):** Neon cổng **5432** kết nối lại được; đã seed thành
> công 7 TK lên `neondb` bằng lệnh trên. (Lần trước 2026-06-17 bị mạng chặn
> outbound 5432 — nay đã hết.) Khi chạy gặp ERROR `hb_timeoff_*`/`hr_holidays_modern`
> "not loaded" là tồn đọng đã biết (module timeoff cũ đã gộp/đổi tên) — vô hại với seed.

> Lưu ý Odoo 19: `res.users` dùng field **`group_ids`** (không phải `groups_id`);
> `res.groups` **không còn `category_id`**.

---

## 4. Nhật ký thay đổi DB

| Ngày | DB | Thay đổi | Người |
|---|---|---|---|
| 2026-06-17 | Local `hocba_hrm` | Seed 7 tài khoản test + phòng "Phòng Test (QA)" + NV test (script `seed_test_accounts.py`) | Vu/Claude |
| 2026-06-17 | Local `hocba_hrm` | Seed 5 bản ghi chấm công hôm nay (3 đúng giờ, 2 muộn) — script `_demo_seed/seed_attendance_demo.py` | Vu/Claude |
| 2026-06-17 | Neon `neondb` | **CHƯA seed** — máy hiện tại chặn TCP cổng 5432 tới Neon (host + container đều timeout). Chờ mạng/VPN cho phép 5432 | — |
| 2026-06-19 | Neon `neondb` | ✅ Seed 7 tài khoản test + phòng "Phòng Test (QA)" + NV test (cổng 5432 đã thông; `seed_test_accounts.py`). Verify: 7/7 TK tồn tại, link hồ sơ đúng | Vu/Claude |
| 2026-06-19 | Neon `neondb` | ✅ Cài/upgrade `hocba_payroll` (62 modules loaded OK). **Phải dùng endpoint Neon TRỰC TIẾP** (`ep-...neon.tech`, bỏ `-pooler`) cho upgrade — pooler rớt SSL giữa transaction DDL dài. Verify SPA: API `/api/payroll/batch` 200, màn Bảng lương render | Vu/Claude |
| 2026-06-23 | Neon `neondb` | ✅ Import **167 giáo viên từ CMS Mabble** (`cms.dangch.tech`, role ROLE_TEACHER) → 167 `hr.employee` (loại Giáo viên, status `parttime`) + 167 `res.users` self-service (internal, group_user), mật khẩu chung **`Hocba@2026`**. Idempotent theo `work_email`. Script sinh: `tools/cms/build_teacher_seed.py` → `_demo_seed/import_cms_teachers.py`. Chạy qua `docker compose exec odoo odoo shell` (lệnh `run` mới bị SSL EOF lúc boot — dùng container đang chạy). Verify: auth login `dta031@gmail.com` OK | Viet/Claude |
