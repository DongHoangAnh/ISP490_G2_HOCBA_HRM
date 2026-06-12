# ĐẶC TẢ MODULE `hocba_hrm` — THEME BACKEND, SPA DEMO & JSON API

**Phiên bản:** 1.1 · **Ngày:** 12/06/2026 · **Trạng thái SPA: ⛔ TẠM NGẮT** (test trên giao diện Odoo backend trước — quyết định 12/06/2026)

---

## 1. Vai trò của module

`hocba_hrm` gồm 3 phần độc lập:

1. **Theme backend Odoo** (đang dùng — định hướng UI chốt 11/06): SCSS đỏ Học Bá `#C8102E` + font Be Vietnam Pro nạp qua assets `web._assets_primary_variables` (`primary_variables.scss`) và `web.assets_backend` (`hocba_backend.scss`); font nhúng qua `views/webclient_templates.xml`.
2. **SPA React demo** tại `/hocba-hrm` (⛔ tạm ngắt): trang HTML nhúng React 18 UMD + Babel standalone, render các màn Dashboard/Employees/… từ `static/src/js/*.jsx`. Màn Employees đã nối API thật; các màn khác còn mock data. SPA là **bản đề xuất UI**, không phải giao diện vận hành.
3. **JSON API** phục vụ SPA (⛔ tạm ngắt cùng SPA): 2 endpoint đọc dữ liệu thật từ `hocba_employees`.

## 2. Cơ chế ngắt/mở SPA

- Cờ **`SPA_ENABLED`** (hằng số trong `controllers/main.py`). Khi `False`:
  - `GET /hocba-hrm` → redirect `/odoo` (vào backend Odoo).
  - 2 endpoint API → HTTP **410** `{"error": "spa_disabled"}`.
- Menu gốc "Học Bá HRM" (act_url → `/hocba-hrm`) được comment trong `views/menu.xml`.
- **Mở lại:** đặt `SPA_ENABLED = True`, bỏ comment menu, upgrade module `hocba_hrm` + restart. Theme backend KHÔNG bị ảnh hưởng khi ngắt SPA.

## 3. Đặc tả API (giữ nguyên hợp đồng để dùng lại khi mở SPA)

### 3.1. `GET /hocba-hrm/api/employees` (auth=user)
Trả về:
```json
{
  "isHr": bool,          // user thuộc hr.group_hr_user
  "isHrManager": bool,   // user thuộc hr.group_hr_manager
  "departments": [{"id", "name", "total", "official", "probation", "color"}],
  "employees":  [{"id", "code", "name", "dep", "depName", "jobTitle",
                   "status", "statusKey", "type", "posType", "posTypeKey",
                   "start", "email", "phone", "hasImg",
                   "wage"?  /* CHỈ khi isHrManager */ }]
}
```

### 3.2. `GET /hocba-hrm/api/employee/<id>` (auth=user)
- Không tồn tại → 404 `{"error": "not_found"}`.
- Khối dữ liệu trả về **theo quyền**:

| Khối | Điều kiện |
|---|---|
| Base (code/name/dep/job/status/…) | mọi user đăng nhập |
| `wage` | `hr.group_hr_manager` |
| Pháp lý F-002 (`bday`, `cccd`, `idIssue`, `idPlace`, `hi`, `hiPlace`, địa chỉ) + `dependents` (F-003) + `certs` (F-008/9) | `hr.group_hr_user` |
| `pit` (MST), `si` (BHXH) | `hr.group_hr_manager` |
| `probation` (timeline 2 cổng, F-004/5) | luôn trả (isGroupB = staff/manager + offline) |
| `trial` (thử giảng F-008) | chỉ khi nhân viên thuộc Nhóm A (online / parttime / ctv / advisor) |
| `assets` (F-006), `promotions` (F-007; from/to wage chỉ manager) | mọi user đăng nhập |

**Nguyên tắc bảo mật:** ORM gọi `sudo()` để đọc, nhưng việc ẩn/hiện field nhạy cảm quyết định bằng `has_group` ở tầng controller — đã có test HTTP xác nhận (API-1..12, xem `TEST_BACKEND_2026-06-12.md`).

## 4. Lý do tạm ngắt SPA (12/06/2026)
- Ưu tiên xây chắc backend + nghiệp vụ trên giao diện Odoo chuẩn (views `hocba_employees` đã polish theo wireframe F-001).
- SPA dùng Babel standalone compile JSX runtime — chỉ phù hợp demo, không production.
- Giảm 1 bề mặt phải test/regression mỗi lần đổi backend.

## 5. Nợ kỹ thuật khi mở lại SPA
- Chuyển JSX sang build tооl (bỏ Babel standalone), hoặc chuyển hẳn các màn SPA thành view Odoo theo theme.
- Các màn ngoài Employees vẫn mock — cần nối API như màn Employees hoặc cắt bỏ.
- API list trả toàn bộ nhân viên cho mọi user đăng nhập (ẩn field nhạy cảm nhưng vẫn thấy danh bạ) — xác nhận với khách mức lộ thông tin chấp nhận được cho role Employee/Contractor.
