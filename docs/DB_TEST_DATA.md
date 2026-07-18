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
| `test_employee2@hocba.vn` | Nhân viên | (không) | NV Test 2 | Self-service phụ (2026-07-01), thuộc Phòng Test (QA) |

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
| **Neon** (`neondb`) | ✅ **Đã seed (7 TK)** — 2026-06-19 | ✅ **Đã seed dữ liệu demo vận hành** — 2026-06-27 (chấm công, OT, lương, đánh giá, tài sản…). **KHÔNG** có dữ liệu timeoff; **KHÔNG** thêm gì cho `test_employee`. |

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
| 2026-06-27 | Neon `neondb` | ✅ Seed **dữ liệu demo vận hành** (script `_demo_seed/seed_demo_data.py`, idempotent, đánh dấu `[DEMO]`): chấm công 51 bản ghi (đúng giờ/muộn/về sớm, có người đang làm hôm nay), 3 đơn sửa chấm công chờ duyệt, 4 ca OT (2 duyệt + 2 chờ), 8 hợp đồng + batch lương 06/2026 (8 payslip có số thật + thuế TNCN lũy tiến, state `verify`), 3 đánh giá thăng tiến (verdict 89/65/92%), 4 tài sản, 2 người phụ thuộc, 1 chứng chỉ sắp hết hạn. **KHÔNG seed timeoff** (theo yêu cầu — đồng thời tránh upgrade module). **KHÔNG thêm dữ liệu cho `test_employee@hocba.vn` (eid 21)** — giữ nguyên. ⚠️ **Fix bug payroll**: `payslip.py:793` gọi `safe_eval(..., nocopy=True)` — Odoo 19 đã bỏ `nocopy` → mọi rule code lỗi → payslip = 0. Đã bỏ `nocopy=True` (API mới tự `context.update`). Đã restart container để app live dùng code mới. | Claude |
| 2026-06-27 | Neon `neondb` | ℹ️ Lưu ý: cột `x_conflict_check_pending` (model `hr.leave`, module `hocba_timeoff`) **chưa tồn tại trên Neon** → mọi thao tác tạo/sửa `hr.leave` đang lỗi (cả app live). Cần `-u hocba_timeoff` qua **endpoint trực tiếp** (bỏ `-pooler`) để tạo cột. Lần seed này **đã bỏ qua timeoff** theo yêu cầu nên chưa xử lý. | Claude |
| 2026-06-23 | Neon `neondb` | ✅ Import **167 giáo viên từ CMS Mabble** (`cms.dangch.tech`, role ROLE_TEACHER) → 167 `hr.employee` (loại Giáo viên, status `parttime`) + 167 `res.users` self-service (internal, group_user), mật khẩu chung **`Hocba@2026`**. Idempotent theo `work_email`. Script sinh: `tools/cms/build_teacher_seed.py` → `_demo_seed/import_cms_teachers.py`. Chạy qua `docker compose exec odoo odoo shell` (lệnh `run` mới bị SSL EOF lúc boot — dùng container đang chạy). Verify: auth login `dta031@gmail.com` OK | Viet/Claude |
| 2026-07-01 | Neon `neondb` | ✅ Thêm 1 tài khoản nhân viên thường phụ: `test_employee2@hocba.vn` (mật khẩu `Hocba@2026`) → hồ sơ "NV Test 2" (`HB.QA.NV2`, CTV, Phòng Test (QA)), không nhóm HR. Script `_demo_seed/seed_employee2.py`, idempotent. Verify: login OK, hiện đúng màn self-service ("Hồ sơ của tôi") | Claude |
| 2026-07-10 | Local `hocba_hrm` | ✅ Seed **demo dashboard** (43 NV đang làm + 8 NV nghỉ việc, mã `HB.DEMO*`, phòng "Demo Dashboard"): tuổi 19–46, giới tính (đa số nữ), ngày vào 0–1 năm, 14 mốc `x_official_date` rải 10/2024–6/2026 — phục vụ verify trang Dashboard mới (KPI + 3 biểu đồ). Script scratchpad, idempotent theo mã `HB.DEMO%`. (Field `x_gender` từng thêm cho donut giới tính đã **bỏ** theo quyết định cùng ngày — cột `x_gender` sót trên local vô hại; Neon không bị ảnh hưởng.) Endpoint mới `/api/dashboard/stats` là Python thuần, **không đổi schema** → Neon chỉ cần `docker compose restart odoo` là dashboard mới chạy | Viet/Claude |
| 2026-07-11 | Local `hocba_hrm` | ✅ Seed **demo tab dashboard**: 40 ứng viên `Demo UV*` (24 pass CV / 15 PV / 9 pass / 6 nhận việc, nguồn TopCV/Facebook/Referral demo) + 1 phiếu tuyển `recruiting` (Demo Dashboard, qty 3) + 12 ca OT approved 4 tháng gần nhất (3 mức 100/150/300, `[DEMO] OT dashboard`) — phục vụ verify dashboard 5 tab. Idempotent theo `Demo UV%` | Viet/Claude |
| 2026-07-05 | Neon `neondb` | 🔁 **Test E2E offboarding** (preview trên Neon): `test_employee` nộp đơn `OFF/2026/0001` → `test_truongphong` duyệt cấp 1 → `test_hrmanager` duyệt cấp 2 + Hoàn tất (`done`). Verify luồng 2 cấp + phân quyền OK; khi `done` app archive cả `hr_employee(21)` **và** `res_users`/`res_partner` của `test_employee`. **Đã rollback sạch**: xoá đơn OFF/2026/0001, `active=True` lại cho employee+user+partner (eid 21 / uid 18). Net DB = 0. ⚠️ Lưu ý reviewer: hành vi `done` archive luôn tài khoản login là điểm cần rà (mong muốn?). | Claude |
| 2026-07-10 | Neon `neondb` | ✅ `-u hocba_timeoff` qua **endpoint trực tiếp** (bỏ `-pooler`, `--entrypoint bash` để qua mặt odoo.conf) — tạo bảng `hb_leave_notification` còn thiếu (chuông + duyệt/tạo đơn hết 500/rollback). Trong lúc kiểm chứng đã **duyệt đơn test #37** (Test Employee, Nghỉ Phép Năm 0.5 ngày 03/07) → badge Chờ duyệt của `hr.manager` 7→6. | Nhật Anh/Claude |
| 2026-07-10 | Neon `neondb` | ✅ Sau merge main (hệ thông báo hợp nhất): `-u hocba_timeoff` lần 2 qua endpoint trực tiếp → chạy migration `19.0.14.0.0` (chuyển `hb_leave_notification` → bảng `hb_notification` của module mới **`hocba_notify`**, module được cài kèm). Route chuông đổi `/hocba-hrm/api/timeoff/notifications` → **`/hocba-hrm/api/notifications`** (hợp nhất mọi module). Verify: login `hr.manager` → notifications 200 (trộn thông báo nhắc hạn chứng chỉ + nghỉ phép), approvals 200. | Nhật Anh/Claude |
| 2026-07-15 | Local `hocba_hrm` | ✅ Upgrade `hocba_employees` **19.0.2.0.0** — feature **quy trình nhận việc BƯỚC ĐỘNG** (spec 2026-07-15-onboarding-config): 2 bảng mới `hb_onboarding_template(+_step)` + `hb_onboarding_step`; seed 2 template mặc định ("Thử việc Giáo viên", "Thử việc Nhân viên văn phòng"); migration `post-migrate` map field cổng cũ (`x_eval_*`, thử giảng, thiết bị) → 20 step cho 5 NV có dữ liệu thử việc (idempotent; cột cũ GIỮ để đối chiếu). Cũng **cài `hocba_timeoff`** vào local (trước đó uninstalled → test `test_teaching_days` của hocba_hrm lỗi KeyError model). ⚠️ **Neon CHƯA upgrade** — khi deploy nhớ `-u hocba_employees,hocba_hrm` qua endpoint trực tiếp (bỏ `-pooler`). | Tân/Claude |
| 2026-07-18 | Local `hocba_hrm` | 🔧 Reset mật khẩu `test_hrmanager@hocba.vn` → `Hocba@2026` (pass local trước đó lệch tài liệu, không đăng nhập được). Lưu ý: SPA login hardcode `db: 'neondb'` (Login.jsx) → trên local phải đăng nhập qua `/web/login` rồi vào `/hocba-hrm`. Demo verify luồng onboarding (Không đạt → offboarding #373, NV eid 4; NV CTV demo + template demo) đều đã **rollback sạch**, net DB = 0 | Tân/Claude |
