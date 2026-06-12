# TÀI LIỆU HỆ THỐNG HỌC BÁ HRM (ISP490 — Nhóm 2)

Bộ tài liệu đặc tả & kiến trúc của hệ thống Quản lý Nhân sự cho Trung tâm Tiếng Trung Học Bá, xây trên **Odoo 19** (Docker, db `hocba_hrm`). **Quy trình làm việc của nhóm: viết/duyệt spec TRƯỚC khi code** — mọi chức năng mới phải có đặc tả trong thư mục này trước khi implement.

## Danh mục tài liệu

| Tài liệu | Nội dung | Trạng thái |
|---|---|---|
| [SPEC_EMPLOYEES_DAC_TA_v2.1.md](SPEC_EMPLOYEES_DAC_TA_v2.1.md) | **Đặc tả gốc phân hệ Employees** (DAC_TA v2.1, chốt sau họp khách hàng, 168 bản ghi Lark): phân loại 2 nhóm A/B, quy trình AS-IS/TO-BE, GAP, F-001→F-009, data dictionary + **Phụ lục C as-built** (khác biệt khi implement) | F-001..009 ĐÃ XONG, merged main |
| [SPEC_USERS_AUTH.md](SPEC_USERS_AUTH.md) | Đặc tả `hocba_users`: 4 role → quyền Odoo thật, luồng đăng nhập `/hocba/login`, khóa tài khoản, ma trận ACL/record rules | Đã implement & test |
| [SPEC_HRM_SPA_API.md](SPEC_HRM_SPA_API.md) | Đặc tả `hocba_hrm`: theme backend đỏ Học Bá, SPA React demo + hợp đồng JSON API | **SPA TẠM NGẮT 12/06** — test trên giao diện Odoo |
| [TEST_BACKEND_2026-06-12.md](TEST_BACKEND_2026-06-12.md) | Báo cáo test backend 132 ca (ORM + HTTP + phân quyền 4 role) + cách chạy lại + tài khoản test | 132/132 PASS |
| [MANUAL_TEST_GUIDE.md](MANUAL_TEST_GUIDE.md) | Kịch bản test tay trên giao diện Odoo: ~60 bước cho 11 nhóm (login/role/F-001..009/CRON) + checklist nghiệm thu | sẵn sàng dùng |
| [../HRM_DOC.md](../HRM_DOC.md) | Business Blueprint tổng (AnhDH) | tham khảo |
| [../HRM_SYSTEM_GUIDE.md](../HRM_SYSTEM_GUIDE.md) | Hướng dẫn user/auth ban đầu | tham khảo (đặc tả chuẩn xem SPEC_USERS_AUTH) |
| [../DOCKER_GUIDE.md](../DOCKER_GUIDE.md) | Hướng dẫn chạy Docker | tham khảo |

## Kiến trúc module (custom-addons)

```
hocba_employees   ← LÕI: mở rộng hr.employee (F-001..F-009), single source danh mục
   ↑ depends            hocba.employee.type; models: dependent, asset, promotion,
   |                    skill-cert; 2 CRON; sequence HB.xx
hocba_users       ← tài khoản HRM: hocba.user + 4 role (gán res.groups thật),
   |                    cổng /hocba/login, dashboard theo role
hocba_hrm         ← theme backend (đang dùng) + SPA demo & JSON API (tạm ngắt)
hocba_attendance  ← chấm công (AnhDH)
hr_holidays_modern← nghỉ phép (module ngoài)
```

## Phân quyền tổng quát (chi tiết: SPEC_USERS_AUTH §5)

| Role | Nhóm Odoo | Năng lực chính |
|---|---|---|
| Admin | base.group_system + hr manager | toàn quyền |
| HR Manager | hr.group_hr_manager | toàn bộ HR, thấy lương/MST/BHXH |
| Employee | base.group_user | dữ liệu cá nhân, không thấy field nhạy cảm |
| Contractor | base.group_user | như Employee, tối thiểu |

## Môi trường dev

- **Docker**: `docker compose up -d` → Odoo trên `http://[::1]:8069` (db `hocba_hrm`). ⚠️ Máy dev có Odoo native Windows chiếm `127.0.0.1:8069` (db `tan`) — luôn dùng `[::1]` để chắc chắn vào Docker.
- Đăng nhập backend: `/web/login` hoặc `/odoo`; tài khoản test xem TEST_BACKEND.
- Nâng cấp module: `docker compose exec -T odoo odoo -d hocba_hrm -u <module> --db_host=db --db_user=odoo --db_password=odoo_password --stop-after-init --no-http --addons-path=/mnt/extra-addons` rồi `docker compose restart odoo` (code Python cần restart; XML có `--dev=xml` tự nạp).
