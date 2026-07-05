# Spec — Hệ thống thông báo hợp nhất (Unified Notifications)

- **Ngày:** 2026-07-05
- **Owner:** Vu/Tan (miền Employees) · phối hợp Nhật Anh (timeoff)
- **Trạng thái:** Đã duyệt thiết kế (brainstorm), chờ review spec → plan.

## 1. Mục tiêu & phạm vi

Một hệ thống thông báo **in-app (chuông SPA)** dùng chung cho toàn hệ thống Học
Bá HRM. Thay model thông báo riêng của timeoff (`hb.leave.notification`, FK cứng
tới `hr.leave`) bằng **một model tổng quát** `hb.notification` mà mọi module ghi
vào; chuông poll **một** endpoint duy nhất.

Nguồn thông báo cần có (đã chốt với user):
- **Offboarding (Nghỉ việc)** — sự kiện duyệt 2 cấp.
- **Onboarding / Thử việc (Nhận việc)** — mốc đánh giá & kết quả cổng thử việc.
- **Nhắc hạn hồ sơ** — kết thúc thử việc, hết hạn hợp đồng, hết hạn chứng chỉ/CCCD.
- **Timeoff (Nghỉ phép)** — migrate nguyên trạng sang model chung.

**Quyết định kiến trúc (Hướng 1):** hợp nhất thật về 1 model, gồm migrate
timeoff. Đã báo/ phối hợp Nhật Anh. Lý do chọn thay vì "gộp 2 nguồn": không có
module chung nào cả timeoff lẫn employees cùng `depends` (ngoài `hr` core), nên
cần một **module nền mới** làm nơi đặt model → tiện thể hợp nhất luôn.

### Ngoài phạm vi (YAGNI)
- Thông báo realtime (websocket/bus) — vẫn poll 60s như hiện tại.
- Thông báo qua email/SMS/push mobile.
- Nhắc sinh nhật/kỷ niệm (user đã loại).
- Trung tâm thông báo dạng trang riêng — chỉ dùng dropdown chuông sẵn có.

## 2. Kiến trúc

### 2.1. Module nền mới `hocba_notify`
`depends: ['base']` (chỉ cần `res.users`). Chứa:
1. Model `hb.notification`.
2. Helper `_notify(...)` (method model, chạy sudo được).
3. Controller API chung (route tự khai báo `/hocba-hrm/api/notifications*` — không
   cần depends `hocba_hrm`).
4. `security/ir.model.access.csv` + record rule.

Các module `hocba_timeoff`, `hocba_employees`, `hocba_hrm` thêm `hocba_notify`
vào `depends`.

### 2.2. Model `hb.notification`

| Field | Kiểu | Ghi chú |
|---|---|---|
| `recipient_id` | Many2one `res.users` | required, index, `ondelete='cascade'` |
| `category` | Selection | `timeoff` / `offboarding` / `onboarding` / `hr_reminder` |
| `kind` | Char | tag ngữ nghĩa (vd `pending`, `approved`, `refused`, `sub_request`, `probation_eval`, `cert_expiry`, `contract_end`) |
| `level` | Selection | `info` / `success` / `warning` / `danger` — điều khiển màu chấm |
| `title` | Char | required |
| `body` | Text | nullable |
| `target_view` | Char | view SPA cần mở (`timeoff`/`offboarding`/`onboarding`/`employees`) |
| `target_ref` | Integer | id bản ghi đích (nullable) |
| `target_tab` | Char | tab con (vd timeoff `sub_request`) — nullable |
| `dedup_key` | Char | index, nullable — chống trùng cho cron |
| `is_read` | Boolean | default False, index |

`_order = 'create_date desc, id desc'`, `_rec_name = 'title'`.

### 2.3. Helper `_notify`
```
@api.model
def _notify(self, recipient, category, kind, level, title,
            body=None, target_view=None, target_ref=None,
            target_tab=None, dedup_key=None):
    # recipient: res.users record | id | iterable → tạo 1 dòng cho mỗi người.
    # Nếu dedup_key: bỏ qua nếu đã tồn tại dòng CHƯA ĐỌC cùng (recipient, dedup_key).
    # Trả về records đã tạo.
```
- Bỏ qua recipient rỗng/không active (không tạo dòng "chết").
- Luôn gọi qua `sudo()` từ nơi phát; helper không tự kiểm quyền.

### 2.4. API chung (controller trong `hocba_notify`)
| Route | Method | Trả về |
|---|---|---|
| `/hocba-hrm/api/notifications?limit=` | GET (`auth='user'`) | `{ items:[...], unread:int }` — lọc `recipient_id = uid`, sudo sau khi pin |
| `/hocba-hrm/api/notifications/<int:id>/read` | POST | list mới |
| `/hocba-hrm/api/notifications/read-all` | POST | list mới |

`items[]` JSON: `{ id, category, kind, level, title, body, targetView,
targetRef, targetTab, isRead, createdAt }`.

### 2.5. Bảo mật
- ACL `hb.notification`: tối thiểu; đọc/ghi thực tế qua `sudo()` trong controller
  **sau khi** đã lọc `recipient_id = uid`.
- Record rule: `recipient_id = user` (chỉ thấy của mình) — phòng thủ chiều sâu.

## 3. Producers

Mọi lệnh phát chạy `sudo` sau khi xác định recipient.

### 3.1. Offboarding (`hocba_employees/models/hocba_offboarding.py`)
Gọi `_notify` ngay trong các model action:

| Action | Recipient | kind / level | target |
|---|---|---|---|
| `action_submit` | `employee_id.parent_id.user_id` + trưởng phòng của phòng NV | `pending` / warning | offboarding, rec.id |
| `action_mgr_approve` | Users nhóm `hr.group_hr_manager` | `pending` / warning | offboarding, rec.id |
| `action_hr_approve` | `employee_id.user_id` | `approved` / info | offboarding, rec.id |
| `action_refuse` | `employee_id.user_id` | `refused` / danger | offboarding, rec.id |
| `action_done` | `employee_id.parent_id.user_id` (NV đã khoá login) | `info` / success | offboarding, rec.id |

- Recipient "trưởng phòng": lấy `employee_id.department_id.manager_id.user_id`
  (dedup với parent_id).
- `action_cancel`: không phát (giữ gọn); có thể thêm sau.

### 3.2. Onboarding / Thử việc (`hocba_employees/models/hr_employee.py`)
Không tạo model mới — hook vào luồng thử việc sẵn có:
- `_cron_probation_eval_reminders` (đã có): **thêm** `_notify` tới
  `emp.parent_id.user_id` (+ HR managers), category `onboarding`,
  `kind=probation_eval`, level `warning`,
  `dedup_key = f'probation_eval:{emp.id}:{milestone}:{due}'`.
  (Giữ nguyên `_hocba_gate_activity` hiện có — chỉ bổ sung chuông.)
- Kết quả cổng thử việc (pass→official / extend / fail→offboarding, trong các
  method gate): `_notify` `emp.parent_id.user_id` + `emp.user_id`, category
  `onboarding`, kind tương ứng (`probation_pass`/`probation_extend`/
  `probation_fail`), level success/warning/danger.

### 3.3. Nhắc hạn hồ sơ (category `hr_reminder`)
- `_cron_cert_expiry_alerts` (F-009, đã có): **thêm** `_notify` tới HR managers
  + `emp.user_id`, `kind=cert_expiry`, level `warning` (sắp hết) / `danger`
  (đã hết), `dedup_key = f'cert_expiry:{emp.id}:{skill_id}:{expiry}'`.
- **Kết thúc thử việc**: đã nằm trong 3.2 (mốc đánh giá) → không thêm cron.
- **Hết hạn hợp đồng**: cron **mới** `_cron_contract_end_alerts` quét ngày hết
  hạn HĐ. ⚠️ **Cần xác minh field khi viết plan**: Odoo 19 hợp đồng ở
  `hr.version` (field `contract_date_end`/tương đương) — có thể thuộc miền
  payroll (Hùng). Nếu field truy cập gọn → phát tới HR managers,
  `kind=contract_end`, dedup theo `emp:date_end`. Nếu vướng phụ thuộc/field
  chưa rõ → **tách Phase 5b làm sau**, không chặn 5a (cert).

### 3.4. Timeoff — migrate (`hocba_timeoff`, phối hợp Nhật Anh)
- Sửa `_push_notification` (controllers/main.py) ghi vào `hb.notification`:
  map kind cũ → `(category='timeoff', kind=<cũ>, level=<map>, target_view=
  'timeoff', target_ref=leave.id, target_tab=<'sub' nếu sub_*>)`.
  - Map level: `pending`/`withdraw_pending`/`sub_request`/`sub_returned` →
    warning; `approved`/`sub_accepted` → success; `refused`/`sub_declined`/
    `sub_cancelled` → danger.
- Gỡ 3 route `/api/timeoff/notifications*` + model `hb.leave.notification`.
- **Migration** (`hocba_timeoff/migrations/.../post-migrate.py`): copy mọi dòng
  `hb.leave.notification` → `hb.notification` (map field như trên), giữ
  `is_read`, `create_date`. Sau đó model cũ bị gỡ (bảng drop theo Odoo).

## 4. Frontend

- **`frontend/src/api/notifications.js`** (mới): `fetchNotifications(limit)`,
  `markNotificationRead(id)`, `markAllNotificationsRead()` → `/api/notifications*`.
- **`NotificationBell.jsx`**: đổi import sang api mới; bỏ map kind→màu cứng, thay
  bằng `level`→màu (`info`=lam, `success`=lục, `warning`=hổ phách, `danger`=đỏ);
  (tuỳ chọn) hiện nhãn `category` nhỏ. Prop đổi `onOpenRequest` → `onOpenNotification(n)`.
- **`app/App.jsx`**: `onOpenNotification(n)` điều hướng theo `n.targetView`
  (`timeoff`/`offboarding`/`onboarding`/`employees`), truyền `targetRef`/
  `targetTab` cho component đích (giữ tương thích hành vi timeoff `sub_request`).
- Rebuild SPA sau khi sửa.

## 5. Test (TDD, đỏ→xanh)

- **hocba_notify**: `_notify` tạo dòng đúng field; recipient rỗng/inactive bị bỏ;
  `dedup_key` chặn trùng khi chưa đọc; API `/api/notifications` chỉ trả của uid;
  read đánh dấu 1 dòng; read-all đánh dấu hết; unread đếm đúng.
- **offboarding**: mỗi transition (`submit`/`mgr_approve`/`hr_approve`/`refuse`/
  `done`) tạo đúng số notification tới đúng recipient (mở rộng
  `hocba_hrm/tests/test_offboarding_api.py` hoặc test model trong hocba_employees).
- **onboarding/thử việc**: cron eval reminder tạo notification tới manager; chạy
  2 lần không nhân bản (dedup).
- **reminder**: seed chứng chỉ gần hết hạn → cron tạo notification HR+NV; dedup.
- **timeoff**: push helper giờ ghi `hb.notification` (sửa test hiện có nếu có);
  migration script copy đúng.

## 6. Phân phase (giao tăng dần, mỗi phase 1 vòng đỏ→xanh→commit)

1. **`hocba_notify`** — module nền: model + helper + API + security + test. Nền
   tảng, chưa đụng ai.
2. **Migrate timeoff** — rewire `_push_notification`, migration data, gỡ model/API
   cũ; refactor FE (api + bell + App) sang endpoint chung; verify chuông timeoff
   vẫn chạy. (Phối hợp Nhật Anh.)
3. **Offboarding** producers + test.
4. **Onboarding / thử việc** producers + test.
5. **Nhắc hạn**: 5a cert (hook cron sẵn có) · 5b hợp đồng (cron mới, nếu field HĐ
   truy cập gọn — nếu không, tách làm sau).

**Điểm phụ thuộc/rủi ro:**
- Phase 2 đụng `hocba_timeoff` (Nhật Anh) + cần migration cẩn thận (Neon: upgrade
  qua endpoint TRỰC TIẾP, bỏ `-pooler`).
- Phase 5b phụ thuộc field hợp đồng ở `hr.version`/payroll (Hùng) — xác minh
  trước, tách nếu vướng.
- `NotificationBell.jsx` + `App.jsx` + `Shell.jsx` là **file CHUNG** → sửa phải
  qua review (quy ước §2).
