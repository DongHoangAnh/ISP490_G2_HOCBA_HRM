# BÁO CÁO TEST BACKEND — 12/06/2026

**Kết quả: 132/132 PASS** (sau khi sửa 1 bug 403 ở `/hocba/dashboard`). Môi trường: Docker `odoo:19` + PostgreSQL 15, db `hocba_hrm`, truy cập host qua `http://[::1]:8069`.

## 1. Phạm vi & cách chạy

| Bộ test | Số ca | Công cụ | Script |
|---|---|---|---|
| Nâng cấp 4 module sạch | 1 | `odoo -u ... --stop-after-init` | — |
| ORM: F-001→F-009, hocba_users, ACL | 104 | `odoo shell` (savepoint + **rollback toàn bộ**, không để rác DB) | `%TEMP%\hocba_test\test_orm.py` |
| HTTP: login + phân quyền 4 role | 27 | `python3 + requests` trong container | `%TEMP%\hocba_test\test_http.py` |
| Khóa/mở tài khoản + last_login | 4 | odoo shell + HTTP | `%TEMP%\hocba_test\test_lock.py` |

Chạy lại bộ ORM:
```powershell
docker cp $env:TEMP\hocba_test\test_orm.py isp490_g2_hocba_hrm-odoo-1:/tmp/test_orm.py
docker cp $env:TEMP\hocba_test\runner.py  isp490_g2_hocba_hrm-odoo-1:/tmp/runner.py
docker compose exec -T odoo bash -c "odoo shell -d hocba_hrm --db_host=db --db_user=odoo --db_password=odoo_password --no-http --addons-path=/mnt/extra-addons < /tmp/runner.py"
```
Bộ HTTP: `docker compose exec -T odoo python3 /tmp/test_http.py <emp_id HB.TEST>`.
Tạo lại user test nếu reset db: `setup_users.py` (idempotent).

## 2. Kết quả theo nhóm

| Nhóm | Ca | Kết quả | Điểm đáng chú ý |
|---|---|---|---|
| F-001 Định danh | 5 | ✅ | Mã `HB.xx` tự sinh, unique enforce qua `models.Constraint` |
| F-002 Pháp lý VN | 12 | ✅ | MST 10/13 số, BHXH 10 số, CCCD 12 số (constraint trên `hr.version`), hộ chiếu bypass, BR-010 |
| F-003 Người phụ thuộc | 5 | ✅ | Chỉ đếm NPT trong hiệu lực |
| F-004 Thử việc 2 cổng | 8 | ✅ | Hạn +14/+60, khoảng sửa [7–21]/[30–120], thứ tự cổng |
| F-005 Automation + quyền | 16 | ✅ | AUT-001/002, fail→exiting, skip flag, CRON nhắc hạn, quyền TBP/HR Manager |
| F-006 Tài sản | 11 | ✅ | Unique mã đang giữ, chặn xóa/archive, chuyển giao tạo bản ghi mới |
| F-007 Thăng tiến | 10 | ✅ | Auto áp job/dept, audit không xóa, BR-060 24h |
| F-008 Thử giảng | 8 | ✅ | Thang điểm 1–10, fail cần nhận xét, activity ký HĐ |
| F-009 Chứng chỉ + CRON | 9 | ✅ | Status valid/expiring/expired, chỉ cert đã xác minh được cảnh báo |
| hocba_users role sync | 7 | ✅ | Gán/đổi role = thêm/gỡ `res.groups` thật; khóa đồng bộ `res.users.active` |
| ACL/record rules | 13 | ✅ | Employee không đọc được MST/lương; HR Officer chỉ thấy hocba.user của mình |
| HTTP login + API | 27 | ✅ | 4 role login 2 cổng; wage/cccd/pit/si ẩn-hiện đúng nhóm; API chưa đăng nhập → redirect |
| Khóa tài khoản | 4 | ✅ | `is_active=False` chặn cả `/web/login` lẫn `/hocba/do_login` |

## 3. Bug tìm thấy & đã sửa

| # | Mô tả | Fix |
|---|---|---|
| 1 | `/hocba/dashboard` trả **403** với role Employee/Contractor: controller search `hocba.user` không `sudo()` trong khi user thường không có ACL | Thêm `sudo()` (domain vẫn khóa `user_id = request.uid`) — `hocba_users/controllers/dashboard.py` |

## 4. Phát hiện khác (chưa sửa trong nhánh này)

1. **`hocba_attendance`**: field `hocba.attendance.status.code` dùng `unique=True` — Odoo 19 không hỗ trợ tham số này, **uniqueness không được enforce** (warning mỗi lần upgrade). Cần đổi sang `models.Constraint` (đã giao task riêng).
2. **BR-010 chặn AUT-002** (hành vi chủ đích, cần đào tạo HR): phải nhập MST/BHXH trước khi chấm Đạt cổng tháng-2, nếu không sẽ gặp ValidationError.
3. Đăng nhập custom theo **email**: nếu 2 res.users trùng email, login lấy user đầu tiên — nên thêm ràng buộc (ghi ở mục nợ kỹ thuật SPEC_USERS_AUTH).
4. User thường truy vấn `hr.employee` bị Odoo ủy quyền qua `hr.employee.public` → **mọi field custom `x_` bị ẩn/chặn search** với role Employee/Contractor (đúng chủ đích — chi tiết SPEC_USERS_AUTH §5.4).

## 6. Phụ lục: verify ngắt SPA (12/06, sau khi gắn cờ `SPA_ENABLED=False`)

11/11 PASS: `/hocba-hrm` redirect `/odoo`; 2 API trả 410 `spa_disabled`; menu gốc SPA đã gỡ khỏi DB; backend `/odoo` 200; 4 role vẫn login và đọc dữ liệu đúng quyền qua RPC chuẩn (admin/hr_manager thấy MST, employee/ctv bị chặn field `x_`). Script: `%TEMP%\hocba_test\test_spa_off.py`.

## 5. Tài khoản test (đã commit vào db)

Mật khẩu chung **`Hocba@2026`**: `test_admin@hocba.vn` · `test_hrmanager@hocba.vn` · `test_employee@hocba.vn` (gắn NV `HB.TEST` — Nguyễn Văn Test, đủ CCCD/MST/BHXH để test ẩn-hiện) · `test_ctv@hocba.vn`.
