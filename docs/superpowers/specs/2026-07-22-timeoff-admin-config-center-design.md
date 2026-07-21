# Spec — Trung tâm Cấu hình Time Off (Admin)

- **Ngày:** 2026-07-22
- **Module:** `hocba_timeoff` (+ `hocba_hrm` SPA)
- **Owner:** NhatAnh (nhánh `NhatAnh/TimeOff`)
- **Trạng thái:** Đã duyệt thiết kế, chờ viết plan

## 1. Bối cảnh & vấn đề

Hiện tại tài khoản **Admin** (`test_admin@hocba.vn`, có `base.group_system` + `hr.group_hr_manager`) **hành xử y hệt HR Manager bên trong SPA "Học Bá"** — vì mọi kiểm tra quyền trong controller/SPA đều viết `group_system OR hr.group_hr_manager`. Khác biệt duy nhất là Admin vào được backend Odoo gốc, nhưng SPA không phản ánh điều đó.

Mục tiêu: cho Admin một **Trung tâm Cấu hình Time Off** ngay trong SPA để chỉnh các thông số kỹ thuật của nghiệp vụ nghỉ phép (loại nghỉ, chính sách, ngày lễ, tích lũy) — giống vai trò admin của Odoo nhưng gói gọn, tiếng Việt, không phải rời SPA. Đây cũng là điểm **phân biệt Admin với HR Manager**: HR Manager sẽ không thấy khu này.

## 2. Mục tiêu (Goals)

- Thêm khu **"Cấu hình"** trong SPA `/hocba-hrm`, **chỉ Admin** (`base.group_system`) thấy & truy cập.
- Quản lý 4 nhóm cấu hình: **Loại nghỉ · Chính sách theo loại NV · Ngày lễ · Kế hoạch tích lũy**.
- Không phá vỡ luồng nghỉ phép hiện có của nhân viên/HR/quản lý.

## 3. Ngoài phạm vi (Non-goals)

- Không đụng tới cron, trạng thái chấm công, hay các hằng số hard-code trong code (`SLA_DAYS`, `AT_RISK_DAYS`, `LOW_BALANCE_DAYS`, `OVERLAP_WARN`, `MAX_SIZE`) — muốn đổi vẫn sửa code.
- Không thêm màn cấu hình cho HR Manager.
- Không xoá cứng loại nghỉ (chỉ bật/tắt).

## 4. Quyết định thiết kế đã chốt

| Chủ đề | Quyết định |
|---|---|
| Quyền truy cập | Chỉ Admin (`base.group_system`) |
| Loại nghỉ | Sửa · Tạo mới · Bật/tắt (archive). **Không** xoá cứng |
| Chính sách theo loại NV | Chỉ **sửa 6 bản có sẵn** (ràng buộc `UNIQUE(employment_type)`) |
| Ngày lễ | Full CRUD theo năm; một thao tác ghi **cả 2 model** |
| Kế hoạch tích lũy | Full CRUD plan + level |

## 5. Kiến trúc — 5 đơn vị tách bạch

### 5.1. Cờ phân quyền `isAdmin` (BE → FE)

Thêm `isAdmin = user.has_group('base.group_system')` vào dict trả về của `_scope_for` (`hocba_timeoff/controllers/main.py:125-144`), tách bạch với `isHrManager`. SPA đọc cờ này để hiện/ẩn khu Cấu hình và để gate điều hướng.

- **Interface:** `scope['isAdmin'] -> bool`.
- **Phụ thuộc:** `res.users.has_group`.

### 5.2. Field DB `x_hb_managed` thay cho lọc cứng `xml_id`

Vấn đề: SPA đang lọc loại nghỉ **cứng** theo tuple `HB_LEAVE_TYPE_XMLIDS` (`controllers/main.py:26-31`). Nếu admin tạo loại nghỉ mới, nó không có trong tuple → không hiện.

Giải pháp:
- Thêm field `x_hb_managed = fields.Boolean(default=True)` trên `hr.leave.type` (`models/hr_leave_type.py`). Ý nghĩa: "loại nghỉ do Học Bá quản lý, hiện trong SPA".
- **Migration** (post-migrate, version mới): set `x_hb_managed=True` cho đúng 8 loại seed hiện tại (theo `HB_LEAVE_TYPE_XMLIDS`), và `False` cho tất cả loại demo/bản địa hoá còn lại trong DB.
- Đổi `_hb_leave_type_ids` (`main.py:177-184`) từ vòng lặp `env.ref(xmlid)` sang domain `search([('x_hb_managed','=',True)])`. Loại tạo mới (default `True`) tự xuất hiện; loại tắt (`active=False`) tự biến mất khỏi SPA.
- `TEACHING_OFF_XMLID` (`main.py:35`) **giữ nguyên** — vẫn dùng `env.ref` để loại "Nghỉ Buổi Dạy" khỏi dropdown nghỉ dài ngày. (Loại này vẫn `x_hb_managed=True`.)

> Ghi chú: `HB_LEAVE_TYPE_XMLIDS` chỉ còn dùng trong migration để seed cờ; sau đó code runtime dùng domain.

### 5.3. Controller cấu hình (mới)

File mới `hocba_timeoff/controllers/config.py`, đăng ký trong `controllers/__init__.py`. Prefix `/hocba-hrm/api/timeoff/config/*`, `type='json'`, `auth='user'`.

- **Cổng quyền (bắt buộc mọi endpoint):** helper `_require_admin()` → nếu `not request.env.user.has_group('base.group_system')` thì trả `{'ok': False, 'error': 'forbidden'}` (HTTP 200, cờ lỗi) hoặc raise `AccessError`. Chọn 1 kiểu nhất quán với các controller JSON hiện có của module.
- **Ghi qua `.sudo()`** sau khi đã qua cổng quyền (theo gotcha self-service dự án — tránh lệ thuộc ACL của từng model).
- Trả JSON thống nhất `{'ok': bool, 'data'|'error': ...}`.

**Nhóm endpoint (dự kiến):**

*Loại nghỉ:*
- `GET  config/leave-types` — liệt kê (mặc định các loại `x_hb_managed`, cả active/inactive; kèm cờ đang được dùng ở đơn nào không để cảnh báo khi tắt).
- `POST config/leave-types/save` — tạo mới / cập nhật (payload có `id?` để phân biệt). Set `x_hb_managed=True` khi tạo.
- `POST config/leave-types/toggle-active` — bật/tắt (`active`).

*Chính sách:*
- `GET  config/policies` — 6 bản `hb.timeoff.policy.rule` + danh mục loại nghỉ và accrual plan để chọn.
- `POST config/policies/save` — cập nhật 1 bản (không tạo/xoá).

*Ngày lễ:*
- `GET  config/holidays?year=` — liệt kê ngày lễ theo năm (đọc từ `mandatory.day`, kèm tham chiếu cặp `calendar.leaves`).
- `POST config/holidays/save` — tạo/sửa (ghi đồng bộ 2 model).
- `POST config/holidays/delete` — xoá cặp.

*Tích lũy:*
- `GET  config/accrual-plans` — liệt kê plan + level lồng.
- `POST config/accrual-plans/save` — tạo/sửa plan và các level.
- `POST config/accrual-plans/delete` — xoá plan (chặn nếu đang gắn policy/allocation).

> Danh sách field cụ thể của từng payload chốt ở bước writing-plans.

### 5.4. Dịch vụ đồng bộ ngày lễ

Một "ngày lễ" (khái niệm admin) ánh xạ **1:1** tới một `hr.leave.mandatory.day` **và** một `resource.calendar.leaves` (twin) có cùng dải ngày & tên.

- **Tạo:** ghi cả hai bản ghi. `mandatory.day` set `name/start_date/end_date/color`; `calendar.leaves` set `name/date_from 00:00:00/date_to 23:59:59/time_type='leave'` (theo quy ước UTC hiện có trong `resource_calendar_leaves_data.xml`).
- **Sửa/Xoá:** khớp twin theo dải ngày (hoặc lưu liên kết) rồi cập nhật/xoá cả hai.
- **Interface:** helper `_holiday_upsert(vals)` / `_holiday_delete(id)` đóng trong controller hoặc model helper.
- **Phụ thuộc:** 2 model Odoo core.

### 5.5. Module Cấu hình trong SPA (React)

- Nav item **"Cấu hình"** (icon bánh răng) trong shell (`hocba_hrm/static/src/js/hrm-shell.jsx`), **chỉ render khi `isAdmin`**.
- 1 trang shell `TimeoffConfig` + 4 component tab: `LeaveTypesTab`, `PoliciesTab`, `HolidaysTab`, `AccrualTab`. Mỗi tab tự gọi endpoint của mình, có trạng thái loading/error, form sửa, toast kết quả.
- Build ra `custom-addons/hocba_hrm/static/spa/` như thường lệ (`npm run build`).

## 6. Luồng dữ liệu

```
Admin mở "Cấu hình"
  → SPA kiểm scope.isAdmin (ẩn nav nếu false)
  → GET config/<khu>            → controller _require_admin → sudo read → JSON
  → Admin sửa → POST .../save   → controller _require_admin → validate → sudo write
                                 → trả bản ghi mới → SPA cập nhật + toast
```

Non-admin gọi thẳng endpoint (bỏ qua UI) → `_require_admin` chặn.

## 7. Xử lý lỗi

- Bắt `ValidationError` / `UserError` từ ORM, dịch sang thông báo tiếng Việt trong `{'ok': False, 'error': ...}`.
- Trường hợp cụ thể:
  - Tắt/xoá loại nghỉ đang có đơn → cảnh báo, chặn xoá cứng (loại nghỉ chỉ archive nên an toàn; nhưng cảnh báo khi tắt loại đang dùng).
  - `annual_days < 0` ở chính sách → chặn.
  - Ngày lễ: `end_date < start_date`, hoặc trùng dải với ngày lễ khác cùng năm → cảnh báo.
  - Xoá accrual plan đang gắn policy/allocation → chặn với thông báo rõ.

## 8. Bảo mật

- Mọi endpoint cấu hình gate `base.group_system`. HR Manager (chỉ `hr.group_hr_manager`) **không** qua được.
- Ghi bằng `.sudo()` sau cổng quyền.
- Không thêm ACL rộng; không mở record rule mới cho user thường.

## 9. Kiểm thử (TDD — backend trước, UI sau)

Đặt trong `hocba_timeoff/tests/test_admin_config.py`. Đỏ → xanh → commit từng phase.

1. **Cổng quyền:** user non-admin (HR Manager, nhân viên) gọi mỗi endpoint → bị chặn; admin → OK.
2. **Loại nghỉ:** tạo loại mới → `x_hb_managed=True` và **xuất hiện trong `_hb_leave_type_ids`**; tắt loại → biến mất; sửa thuộc tính lưu đúng.
3. **Migration cờ:** sau migrate, đúng 8 loại seed có `x_hb_managed=True`, loại demo khác `False`.
4. **Chính sách:** sửa 6 rule lưu đúng; `annual_days<0` bị chặn.
5. **Ngày lễ:** tạo → **cả `mandatory.day` lẫn `calendar.leaves`** có bản ghi khớp dải ngày; sửa/xoá đồng bộ cả hai.
6. **Tích lũy:** CRUD plan + level; xoá plan đang dùng bị chặn.

Tiêu chí: `0 failed, 0 error(s) of N tests` với `N>0`, chạy Docker local `-u hocba_timeoff,hocba_employees` (theo CLAUDE.md).

## 10. Triển khai theo giai đoạn (mỗi phase ship độc lập)

1. **Phase 1** — Cờ `isAdmin` (BE+FE) + nav shell "Cấu hình" + khu **Loại nghỉ** (gồm field `x_hb_managed` + migration + đổi `_hb_leave_type_ids`).
2. **Phase 2** — Khu **Chính sách** (6 rule).
3. **Phase 3** — Khu **Ngày lễ** (đồng bộ 2 model).
4. **Phase 4** — Khu **Tích lũy** (accrual plan/level).

## 11. Rủi ro & lưu ý

- Đổi `_hb_leave_type_ids` sang domain là thay đổi có thể ảnh hưởng mọi màn nghỉ phép → Phase 1 phải có test hồi quy: 8 loại vẫn hiện đúng như trước migration.
- Accrual plan/level là cấu trúc Odoo phức tạp (nhiều field lồng); UI Phase 4 cần giới hạn ở các field thực sự dùng (frequency, added_value, cap/maximum_leave, carryover) để tránh rối.
- Ngày lễ 2 model dễ lệch nếu sửa tay ở backend — dịch vụ đồng bộ chỉ đảm bảo khi thao tác qua SPA; ghi rõ trong tài liệu vận hành.
- Neon: nếu migration nặng, cài/upgrade dùng endpoint trực tiếp (bỏ `-pooler`) theo gotcha dự án.
