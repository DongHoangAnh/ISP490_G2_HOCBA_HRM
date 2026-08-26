# ĐẶC TẢ MODULE `hocba_hrm` — SPA FRONTEND, THEME BACKEND & JSON API

**Phiên bản:** 2.1 · **Ngày:** 24/08/2026 · **Trạng thái SPA: ✅ FRONTEND CHÍNH THỨC**

> Đây là spec API của domain **Employees** (Tân) + vai trò module `hocba_hrm`.
> Domain khác: copy `SPEC_API_TEMPLATE.md`. Quy ước FE: `QUY_UOC_FRONTEND.md`.

---

## 1. Vai trò của module

`hocba_hrm` gồm 3 phần:

1. **SPA React (frontend chính thức)** tại `/hocba-hrm`: build từ thư mục `frontend/` (Vite + React 18) → `static/spa/`. Route serve bản build; dev chạy `npm run dev` (Vite :5173, proxy API về Odoo). Đây là **giao diện vận hành chính**, nối backend chỉ qua JSON API.
2. **Theme backend Odoo** (vai trò admin/nhập liệu): SCSS đỏ Học Bá `#C8102E` + font Be Vietnam Pro nạp qua `web._assets_primary_variables` (`primary_variables.scss`) và `web.assets_backend` (`hocba_backend.scss`); font nhúng qua `views/webclient_templates.xml`. Form phức tạp (face enrollment, cấu hình policy…) ở lại backend, không xây lại trong SPA.
3. **JSON API** phục vụ SPA: hiện có 2 endpoint Employees (§3); mỗi domain khác tự thêm endpoint trong module của mình theo `SPEC_API_TEMPLATE.md`.

## 2. Cơ chế serve SPA

- Cờ **`SPA_ENABLED = True`** (hằng số trong `controllers/main.py`).
  - `GET /hocba-hrm` → đọc `static/spa/index.html` (bản build). Chưa build → trang nhắc chạy `npm run build`.
  - Chưa đăng nhập → redirect `/web/login?redirect=/hocba-hrm` (auth=user).
- Menu gốc "Học Bá HRM" (act_url → `/hocba-hrm`) bật trong `views/menu.xml`.
- **Build:** `cd frontend && npm run build` → xuất `static/spa/` (đã commit để demo không cần Node). Sau khi build, upgrade `hocba_hrm` nếu cần (`-u hocba_hrm`).

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

## 4. Trạng thái triển khai (13/06/2026)
- ✅ Babel standalone đã bỏ — chuyển sang Vite build (`frontend/`, G1 xong).
- ✅ Màn Employees nối API thật, đã verify đăng nhập + phân quyền.
- ⏳ 4 màn còn lại (attendance/timeoff/payroll/recruitment) là stub `ComingSoon` — chờ từng owner viết spec (G2) + nối API (G3).

## 5. Nợ kỹ thuật / điểm cần chốt
- API list trả toàn bộ nhân viên cho mọi user đăng nhập (ẩn field nhạy cảm nhưng vẫn thấy danh bạ) — xác nhận với khách mức lộ thông tin chấp nhận được cho role Employee/Contractor.
- Dashboard tổng hợp (`features/dashboard/`) hiện chỉ điều hướng — hoàn thiện ở G4 khi API các domain sẵn sàng.

## 6. Hợp đồng lao động trong hồ sơ nhân viên (v2.1)

- `GET /hocba-hrm/api/employee/<id>` SHALL trả `contracts`, `contractOptions`,
  `canEditContract`, `canEditWage` khi người dùng được xem dữ liệu lương.
- `POST /hocba-hrm/api/employee/<id>/contract` SHALL tạo hợp đồng; hợp đồng hiệu
  lực bắt buộc có `dateStart`.
- WHERE nhân viên đã có hợp đồng `open`, API SHALL từ chối tạo thêm hợp đồng
  `open` thông thường để tránh payroll chọn sai hợp đồng.
- WHEN tái ký với `renewFromId`, hệ thống SHALL tạo hợp đồng mới và đóng hợp
  đồng cũ trong cùng transaction; ngày kết thúc bản cũ là một ngày trước ngày
  bắt đầu bản mới.
- `POST /hocba-hrm/api/contract/<id>` SHALL cập nhật và
  `POST /hocba-hrm/api/contract/<id>/delete` SHALL xoá nếu chưa có phiếu lương
  tham chiếu.
- Chỉ HR Manager/Admin được thay đổi lương; vai trò quản lý trong phạm vi chỉ
  được sửa các điều khoản không phải lương.

**Changelog 2.1 (24/08/2026):** bổ sung tab/API hợp đồng, tự đồng bộ lương và
quy tắc tái ký bảo đảm tối đa một hợp đồng đang hiệu lực qua SPA.
