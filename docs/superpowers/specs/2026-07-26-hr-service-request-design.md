# SPEC — Yêu cầu Dịch vụ Nhân sự & Góp ý (module `hocba_service`)

| | |
|---|---|
| **Mã** | SVC |
| **Ngày** | 2026-07-26 |
| **Owner** | Nhật Anh |
| **Nhánh** | `NhatAnh/Service` (fork từ `origin/main` @9518b36) |
| **Module mới** | `custom-addons/hocba_service` |
| **Trạng thái** | **P1 → P4 XONG** (2026-08-01) — model + ACL + seed + controller API + SPA hai phía (gửi & xử lý), `0 failed, 0 error(s) of 90 tests`. Kiểm tay trên DB local: §10.3 (P3), §10.4 (P4). Tiếp theo: P5 (thông báo + cron quá hạn + `StatsPanel`) |
| **Nguồn yêu cầu** | Giảng viên hướng dẫn — bổ sung cho phần self-service của tài khoản nhân viên |

---

## 1. Bối cảnh & phát biểu yêu cầu

Yêu cầu gốc từ GVHD:

> *"Chức năng gửi yêu cầu dịch vụ nhân sự — tạo 1 đơn gửi thư (đánh giá hoặc gửi yêu cầu, câu hỏi) cho HR hoặc trưởng phòng, có thể chọn ẩn danh hoặc không."*

Yêu cầu này gộp **2 nghiệp vụ khác bản chất**:

| | (A) Yêu cầu dịch vụ | (B) Đánh giá / góp ý / khiếu nại |
|---|---|---|
| Bản chất | Ticket có kết quả cụ thể (xin giấy xác nhận công tác, xác nhận thu nhập, sao y HĐ, hỏi lương/BHXH, cấp lại thẻ NV) | Feedback, không cần "kết quả vật chất" |
| Cần danh tính? | **Bắt buộc** — không biết ai thì không cấp được giấy tờ | Không cần |
| Ẩn danh | Phải **cấm** | Là tính năng cốt lõi |
| Đối thoại 2 chiều | Cần | Cần (đã chốt: **ẩn danh vẫn đối thoại 2 chiều**) |

**Quyết định kiến trúc:** dùng **một model chung** `hocba.hr.request` + **danh mục loại** `hocba.hr.request.type`, mỗi loại tự khai `allow_anonymous` / `default_recipient` / `sla_days`. Một màn hình, một bộ API, luật khác nhau theo loại — không tách 2 module. (Cách các HR tool thật làm: Zoho People Cases, Workday Help.)

### 1.1 Quyết định đã chốt với owner (2026-07-26)

1. **Ẩn danh mức 2** — ẩn danh ở *tầng dữ liệu*, không phải chỉ ẩn ở UI (§4).
2. **Module riêng** `hocba_service`, **nhánh mới** `NhatAnh/Service`.
3. **Phạm vi P1 → P6** (đầy đủ, gồm cả màn Cấu hình cho Admin).
4. **Đơn ẩn danh vẫn đối thoại 2 chiều** — HR/TP trả lời được, người gửi đọc được ở tab "Đơn của tôi", danh tính vẫn kín.
5. **Giới hạn 3 đơn ẩn danh / NV / ngày** (BR-SVC-12), cấu hình được qua `ir.config_parameter`.
6. **Ngưỡng phòng cho ẩn danh gửi TP = 5**, nhưng **DB test có phòng < 5 NV** ⇒ ngưỡng phải là `ir.config_parameter` để hạ xuống lúc demo mà không sửa code (§4.4, BR-SVC-03).
7. **SLA tính theo ngày dương lịch** (không dùng `resource.calendar`).
8. **HR Manager KHÔNG giám sát đơn của Trưởng phòng** — đơn `recipient_scope='manager'` chỉ TP của phòng đó đọc được; HR chỉ thấy nếu bản thân cũng là TP phòng đó. Không làm filter "Tất cả".
9. `Shell.jsx` / `App.jsx` / `hb_notification.py` — owner **đã thông báo nhóm**, được phép sửa trực tiếp.

### 1.2 Mục tiêu

- NV gửi được yêu cầu dịch vụ / câu hỏi / đánh giá tới **HR** hoặc **Trưởng phòng**, có tuỳ chọn **ẩn danh thật**.
- Người nhận có **hộp thư xử lý**: nhận việc (claim) → trả lời → đóng, có **SLA** và nhắc quá hạn.
- **Hội thoại 2 chiều** trên từng đơn, giữ được ẩn danh; có **ghi chú nội bộ** người gửi không thấy.
- Admin cấu hình được danh mục loại yêu cầu mà không sửa code.

### 1.3 Ngoài phạm vi (Non-goals)

- Không sinh file giấy tờ tự động (PDF xác nhận công tác…) — HR xử lý ngoài hệ thống, đính kèm kết quả nếu cần.
- Không gửi email ra ngoài; chỉ thông báo in-app qua `hb.notification`.
- Không có khảo sát định kỳ / eNPS / form động nhiều câu hỏi.
- Không chấm điểm KPI người xử lý.
- Không tích hợp `mail.thread` chatter (xem §4.3 — lý do bảo mật).

---

## 2. Nghiệp vụ

### 2.1 Danh mục loại yêu cầu (seed dữ liệu, `noupdate="0"` để nâng cấp được)

| xml_id | Tên | Người nhận mặc định | Ẩn danh | SLA (ngày) | Cho đính kèm |
|---|---|---|---|---|---|
| `type_confirm_work` | Xin giấy xác nhận công tác | HR | ✗ | 3 | ✓ |
| `type_confirm_income` | Xác nhận thu nhập / bảng lương | HR | ✗ | 3 | ✓ |
| `type_contract_copy` | Sao y hợp đồng | HR | ✗ | 5 | ✓ |
| `type_qna_payroll` | Hỏi đáp lương / BHXH / thuế | HR | ✗ | 2 | ✓ |
| `type_reissue_badge` | Cấp lại thẻ nhân viên | HR | ✗ | 5 | ✓ |
| `type_work_proposal` | Đề xuất / xin ý kiến công việc | Trưởng phòng | ✗ | 3 | ✓ |
| `type_feedback` | Đánh giá & góp ý | HR hoặc TP (người gửi chọn) | **✓** | 7 | ✗ |
| `type_complaint_mgr` | Khiếu nại về quản lý | **HR only — cứng** | **✓** | 5 | ✗ |
| `type_other` | Khác | HR | ✗ | 5 | ✓ |

**BR-SVC-01** — `type_complaint_mgr` **không bao giờ** route tới Trưởng phòng. Nếu không, đơn khiếu nại nằm trong tay chính người bị khiếu nại. Ràng buộc ở cả model (`_constrains`) và controller.

**BR-SVC-02** — Đơn ẩn danh **không cho đính kèm** (`ir.attachment.create_uid` làm lộ người gửi). Loại `allow_anonymous=True` đặt `allow_attachment=False`.

### 2.2 Định tuyến người nhận (`recipient_scope`)

| Giá trị | Ai đọc/xử lý được |
|---|---|
| `hr` | HR User + HR Manager + Admin |
| `manager` | Trưởng phòng của `target_department_id` (gồm phòng con, qua `_managed_department_ids`) |
| `both` | Cả hai |

- `target_department_id` = **snapshot** phòng của NV lúc gửi → tái cơ cấu phòng ban về sau không làm đổi phạm vi đọc.
- **BR-SVC-03** (sửa 2026-07-26 khi vào P1 — xem §2.2.1) — quy tắc `target_department_id` cho đơn ẩn danh:

| `is_anonymous` | `recipient_scope` | `target_department_id` | Ràng buộc thêm |
|---|---|---|---|
| False | `hr` | False | — |
| False | `manager` / `both` | phòng của NV (hoặc phòng chọn tường minh) | — |
| **True** | `hr` | **False** | — |
| **True** | `manager` | **BẮT BUỘC có** (cần để định tuyến) — nhưng **không bao giờ serialize** | Phòng phải có **≥ `min_anon_dept_size`** NV đang làm việc (`active=True` và `x_employment_status != 'resigned'`); không đạt → `anon_dept_too_small` |
| **True** | `both` | — | **Không cho phép** → `anon_scope_both` |

#### 2.2.1 Vì sao phải sửa BR-SVC-03

Bản nháp ghi *"đơn ẩn danh ⇒ `target_department_id = False`"* đồng thời vẫn cho gửi TP — **mâu thuẫn**: không lưu phòng thì `_inbox_domain` của TP (`target_department_id in deptIds`) không thể tìm ra đơn, TP sẽ không bao giờ nhận được.

Cách giải quyết và lý do nó **không** làm yếu ẩn danh:

1. TP nhận đơn thì **đã biết** đơn thuộc phòng mình — lưu `target_department_id` không cho họ thêm thông tin nào.
2. HR **không đọc được** đơn `recipient_scope='manager'` (BR-SVC-13) ⇒ phòng ban không rò sang HR.
3. Chặn `both` cho đơn ẩn danh (`anon_scope_both`) — đây chính là kịch bản duy nhất khiến HR thấy được `target_department_id` của đơn ẩn danh.
4. Ngưỡng `min_anon_dept_size` vẫn là lớp chống TP thu hẹp danh sách nghi vấn.

⇒ Ẩn danh vẫn nguyên vẹn; chỉ khác là phòng ban được lưu **để định tuyến**, và serializer (§4.2 L3) tuyệt đối không trả `department` ra ngoài.
- **BR-SVC-12** — Mỗi NV gửi tối đa **3 đơn ẩn danh / ngày** (tính theo `create_date` ngày dương lịch, đếm qua bảng `sender` bằng sudo). Vượt → `400 anon_daily_limit`. Chống spam/vu khống mà không cần lộ danh tính.
- **BR-SVC-04** — Người gửi không tự gửi đơn cho chính mình với vai trò TP (nếu người gửi *là* `manager_id` của `target_department_id` thì buộc `recipient_scope='hr'`).

**Hai tham số cấu hình** (`ir.config_parameter`, seed ở `data/`, sửa được ở P6):

| Key | Default | Ý nghĩa |
|---|---|---|
| `hocba_service.min_anon_dept_size` | `5` | Ngưỡng BR-SVC-03 |
| `hocba_service.anon_daily_limit` | `3` | Ngưỡng BR-SVC-12 |

⚠️ **DB test có phòng < 5 NV** (owner xác nhận 2026-07-26) ⇒ luồng "ẩn danh gửi TP" sẽ bị chặn khi demo nếu để mặc định. Trước khi demo: kiểm số NV thực tế của phòng đích rồi **hạ `min_anon_dept_size`** (vd `3`) qua màn Cấu hình P6 hoặc Odoo backend → **không sửa code, không sửa test**. Test tự tạo phòng riêng nên không phụ thuộc DB (§9.4).

### 2.3 Vòng đời (state machine)

```
                    ┌──────────── cancelled  (người gửi rút, chỉ khi state = new)
                    │
new ──claim──> in_progress ──answer──> answered ──close──> closed
 │                                        │
 └────────────── (HR có thể close trực tiếp từ new với loại feedback) ──────┘
```

| state | Nhãn | Ai chuyển | Ghi chú |
|---|---|---|---|
| `new` | Mới | (tạo) | Chưa ai nhận |
| `in_progress` | Đang xử lý | HR/TP trong phạm vi | Set `handler_id = uid` |
| `answered` | Đã trả lời | handler | Bắt buộc có ≥1 message của handler |
| `closed` | Đã đóng | handler **hoặc** người gửi | `closed_reason` optional |
| `cancelled` | Người gửi rút | người gửi | Chỉ từ `new` |

**BR-SVC-05** — Chỉ `handler_id` hoặc HR Manager mới chuyển được `answered`/`closed` sau khi đơn đã claim (tránh 2 người xử lý chồng).

**BR-SVC-06** — Đơn ở `answered` mà người gửi reply thêm → tự về `in_progress` (mở lại hội thoại).

### 2.4 SLA

- `deadline = create_date + type_id.sla_days` — **ngày dương lịch** (đã chốt 2026-07-26; **không** dùng `resource.calendar`/ngày làm việc).
- `is_overdue` = compute (không store): `state in ('new','in_progress') and now > deadline`.
- Cron nhắc: mỗi ngày, đơn quá hạn → `hb.notification` cho handler (hoặc toàn bộ người nhận nếu chưa claim), `dedup_key = 'svc_overdue_%s' % id`.

---

## 3. Mô hình dữ liệu

### 3.1 `hocba.hr.request` — đơn (KHÔNG chứa danh tính người gửi)

```python
_name = 'hocba.hr.request'
_order = 'create_date desc, id desc'

name                 Char      readonly, ir.sequence 'hocba.hr.request' → YCDV/2026/0001
type_id              M2O       hocba.hr.request.type, required, ondelete='restrict'
subject              Char      required
body                 Text      required
recipient_scope      Selection ('hr','manager','both'), required
target_department_id M2O       hr.department, snapshot; False khi ẩn danh (BR-SVC-03)
is_anonymous         Boolean   default False
rating               Selection ('1'..'5'), chỉ dùng khi type_id.has_rating
priority             Selection ('normal','urgent') default 'normal'
state                Selection xem §2.3, default 'new', required
handler_id           M2O       res.users, readonly
claimed_at           Datetime  readonly
answered_at          Datetime  readonly
closed_at            Datetime  readonly
closed_reason        Text
deadline             Datetime  compute store=True (depends type_id.sla_days, create_date)
is_overdue           Boolean   compute store=False, search='_search_is_overdue'
message_ids          O2M       hocba.hr.request.message
attachment_ids        M2M      ir.attachment (chỉ khi type_id.allow_attachment)
```

**Không có** `employee_id` / `user_id` trên model này. Đây là điểm cốt lõi của ẩn danh mức 2.

`_rec_name = 'name'`. `display_name` = `f'{name} — {subject}'`.

### 3.2 `hocba.hr.request.sender` — bảng danh tính TÁCH RIÊNG

```python
_name = 'hocba.hr.request.sender'
_description = 'Danh tính người gửi đơn dịch vụ — KHÔNG cấp ACL cho group nào'

request_id    M2O  hocba.hr.request, required, ondelete='cascade', index=True
employee_id   M2O  hr.employee, required, index=True
user_id       M2O  res.users, required, index=True
department_id M2O  hr.department  # phòng thực tế lúc gửi, phục vụ thống kê tổng hợp
_sql_constraints: uniq(request_id)
```

- **ACL: không dòng nào trong `ir.model.access.csv`** → không group nào đọc được, kể cả HR Manager, kể cả khi mở `/odoo` backend. Chỉ `.sudo()` trong controller truy cập.
- Không khai `ir.ui.view` / `ir.actions.act_window` cho model này.
- Tạo bằng `sudo().create()` trong cùng transaction với đơn.

### 3.3 `hocba.hr.request.message` — hội thoại

```python
_name = 'hocba.hr.request.message'
_order = 'create_date asc, id asc'

request_id   M2O       hocba.hr.request, required, ondelete='cascade', index=True
author_role  Selection ('sender','handler','system'), required
author_id    M2O       res.users  # chỉ hiển thị khi author_role='handler' HOẶC đơn không ẩn danh
body         Text      required
is_internal  Boolean   default False  # ghi chú nội bộ, người gửi KHÔNG thấy
```

**BR-SVC-07** — `is_internal=True` chỉ handler/HR tạo được; serializer phía người gửi phải lọc bỏ.
**BR-SVC-08** — Message của `author_role='sender'` trên đơn ẩn danh: `author_id` được ghi (để audit) nhưng **serializer không bao giờ trả ra** cho người xem khác.

### 3.4 `hocba.hr.request.type` — danh mục (P6 cho Admin cấu hình)

```python
_name = 'hocba.hr.request.type'
_order = 'sequence, id'

name              Char     required, translate=False
code              Char     required, unique
sequence          Integer  default 10
default_recipient Selection ('hr','manager','both'), required, default 'hr'
force_hr_only     Boolean  default False   # BR-SVC-01 cho type_complaint_mgr
allow_anonymous   Boolean  default False
allow_attachment  Boolean  default True
has_rating        Boolean  default False   # loại "Đánh giá" hiện 1..5 sao
sla_days          Integer  default 5, >0
active            Boolean  default True
description       Text                     # hướng dẫn hiện trên form SPA
```

**BR-SVC-09** — `_constrains`: `allow_anonymous=True` ⇒ `allow_attachment=False` (BR-SVC-02).

---

## 4. Ẩn danh mức 2 — thiết kế chi tiết

### 4.1 Vì sao "checkbox + ẩn ở UI" là ẩn danh giả

- `create_uid`/`write_uid` luôn ghi tác giả → ai đọc được record là truy ra được.
- Topbar SPA có nút **mở `/odoo` backend** ([Shell.jsx:155](../../frontend/src/app/Shell.jsx)) → HR/Admin vào list view thấy hết.
- `mail.message.author_id` lộ nếu dùng chatter.
- `ir.attachment.create_uid` lộ.

### 4.2 Bốn lớp bảo vệ

| Lớp | Biện pháp |
|---|---|
| **L1 — Schema** | Đơn không có field người gửi. Danh tính nằm ở `hocba.hr.request.sender`, **không ACL** ⇒ HR/TP không đọc được ở bất kỳ đâu (SPA, `/odoo`, XML-RPC). |
| **L2 — `create_uid`** | Đơn + message + sender tạo bằng `sudo()` ⇒ `create_uid = 1 (OdooBot)`, không phải NV. |
| **L3 — Serializer** | Controller là chốt cuối: `is_anonymous=True` và người xem ≠ người gửi ⇒ **không** đưa `employeeName` / `department` / `authorName` vào JSON. Viết 1 hàm `_serialize_request(req, viewer_is_sender)` dùng chung để không lệch giữa các route. |
| **L4 — Thông báo** | `hb.notification.title/body` **không chứa tên** khi ẩn danh. Đây là chỗ rò rỉ dễ bỏ sót nhất. |

### 4.3 Vì sao KHÔNG dùng `mail.thread`

`mail.message.author_id` không ẩn được (chatter render ở backend, ACL `mail.message` mở cho `base.group_user`), và SPA không render chatter. → dùng `hocba.hr.request.message` tự viết (§3.3).

### 4.4 Giới hạn được ghi nhận (nêu rõ trong báo cáo, không che)

- **DB superuser / người có quyền truy cập trực tiếp Postgres** vẫn đọc được bảng `hocba_hr_request_sender`. Đây là giới hạn không thể vượt trong mọi hệ thống lưu-để-đối-thoại; đánh đổi có ý thức để giữ (a) khả năng trả lời người gửi, (b) khả năng điều tra khi có khiếu nại nghiêm trọng.
- Nội dung do người gửi tự viết vẫn có thể tự tiết lộ danh tính. Form sẽ có nhắc nhở.
- `MIN_ANON_DEPT_SIZE=5` (BR-SVC-03) giảm nhưng không triệt tiêu rủi ro suy luận.

### 4.5 Cách người gửi vẫn theo dõi được đơn của mình

Không thể viết `ir.rule` tĩnh cho người gửi (danh tính ở bảng khác; domain `sender_ids.user_id` sẽ kích hoạt kiểm ACL trên model đã cố tình không cấp ACL). Vì vậy:

> **Toàn bộ phía người gửi đi qua `sudo()` trong controller SAU khi pin `uid`** — đúng gotcha "Self-service" của CLAUDE.md.

```python
def _my_request_ids(env):
    """Id các đơn do user hiện tại gửi. Pin uid trước, sudo sau."""
    rows = env['hocba.hr.request.sender'].sudo().search([('user_id', '=', env.user.id)])
    return rows.mapped('request_id').ids
```

⇒ `hocba.hr.request` **không cấp ACL cho `base.group_user`** (perm 0,0,0,0). NV thường không truy cập model này trực tiếp — chỉ qua API.

---

## 5. Phân quyền

Bám convention repo: **ACL theo group + scope trong controller** (`_scope_for`/`_dept_domain` của `hocba_timeoff`), rất ít `ir.rule`.

### 5.1 `security/ir.model.access.csv`

| model | group | R | W | C | D |
|---|---|---|---|---|---|
| `hocba.hr.request` | `hr.group_hr_user` | 1 | 1 | 0 | 0 |
| `hocba.hr.request` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `hocba.hr.request` | `base.group_user` | **0** | 0 | 0 | 0 (không khai dòng) |
| `hocba.hr.request.message` | `hr.group_hr_user` | 1 | 1 | 1 | 0 |
| `hocba.hr.request.message` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `hocba.hr.request.type` | `base.group_user` | 1 | 0 | 0 | 0 |
| `hocba.hr.request.type` | `hr.group_hr_manager` | 1 | 1 | 1 | 0 |
| `hocba.hr.request.type` | `base.group_system` | 1 | 1 | 1 | 1 |
| `hocba.hr.request.sender` | — | **không khai dòng nào** | | | |

> ⚠️ **Mỗi lần load module, Odoo log:** `WARNING ... The models ['hocba.hr.request.sender'] have no access rules in module hocba_service, consider adding some, like: ...`. **Đây là CỐ Ý, đừng "sửa".** Thêm một dòng ACL cho bảng này là phá thẳng lớp L1 của ẩn danh (§4.2). Test `test_no_acl_row_grants_sender_table` sẽ đỏ nếu ai đó làm vậy — và mutation test §9.5 đã chứng minh nó bắt được.

### 5.2 Scope trong controller

```python
def _svc_scope(env):
    """Vai trò + phạm vi đọc hộp thư dịch vụ."""
    user = env.user
    is_hr      = user.has_group('hr.group_hr_user') or user.has_group('hr.group_hr_manager')
    is_admin   = user.has_group('base.group_system')
    is_hr_mgr  = is_admin or user.has_group('hr.group_hr_manager')
    dept_ids   = _managed_department_ids(env, user.employee_id)   # dùng lại hocba_hrm
    return {
        'isHr': is_hr or is_admin, 'isHrManager': is_hr_mgr,
        'isDeptManager': bool(dept_ids), 'deptIds': dept_ids,
        'canHandle': is_hr or is_admin or bool(dept_ids),
    }
```

Domain hộp thư:

```python
def _inbox_domain(scope):
    if scope['isHr']:
        parts = [[('recipient_scope', 'in', ('hr', 'both'))]]
        if scope['deptIds']:   # HR kiêm TP
            parts.append([('recipient_scope', 'in', ('manager', 'both')),
                          ('target_department_id', 'in', scope['deptIds'])])
        return OR(parts)
    if scope['isDeptManager']:
        return [('recipient_scope', 'in', ('manager', 'both')),
                ('target_department_id', 'in', scope['deptIds']),
                ('type_id.force_hr_only', '=', False)]        # BR-SVC-01
    return [('id', '=', 0)]   # NV thường không có hộp thư
```

**BR-SVC-10** — Trưởng phòng `search()` trên đơn `force_hr_only` phải trả **0 record** (test bắt buộc, §9 case 9).

**BR-SVC-13** — HR/HR Manager **không** đọc được đơn `recipient_scope='manager'` (đã chốt: không giám sát TP xử lý). Nhánh `parts.append(...)` ở trên chỉ áp dụng khi HR **đồng thời** là TP của phòng đó (`deptIds` không rỗng) — tức họ đọc với tư cách TP, không phải tư cách HR. Không làm filter "Tất cả".

### 5.3 Giáo vụ

Không liên quan nghiệp vụ dịch vụ ⇒ **không cấp**. Giáo vụ chỉ là NV gửi đơn như người thường.

---

## 6. API (`/hocba-hrm/api/service/*`)

Đăng ký route từ `hocba_service/controllers/main.py` — tiền lệ `hocba_timeoff` đăng ký `/hocba-hrm/api/timeoff/*` từ module riêng ([main.py:1336](../../custom-addons/hocba_timeoff/controllers/main.py)). Tất cả `auth='user'`, `type='http'`, trả JSON qua helper chung của repo.

| Method | Route | Mô tả |
|---|---|---|
| GET | `/service/meta` | Danh mục loại (id, name, allowAnonymous, allowAttachment, hasRating, slaDays, defaultRecipient, forceHrOnly, description) + cờ vai trò từ `_svc_scope` + danh sách phòng gửi được (khi `recipient_scope='manager'`) |
| POST | `/service/request` | Gửi đơn. Body: `typeId, subject, body, recipientScope, targetDepartmentId?, isAnonymous, rating?, priority?, attachmentIds?` |
| GET | `/service/my-requests` | `?state=&year=` — đơn của tôi (qua `_my_request_ids`) |
| GET | `/service/inbox` | `?state=&scope=&overdue=&typeId=&q=` — hộp thư HR/TP |
| GET | `/service/request/<int:rid>` | Chi tiết + thread (lọc `is_internal` theo vai trò; ẩn danh tính theo §4.2 L3) |
| POST | `/service/request/<int:rid>/reply` | Body: `body, isInternal?` |
| POST | `/service/request/<int:rid>/claim` | `new → in_progress`, set `handler_id` |
| POST | `/service/request/<int:rid>/answer` | `in_progress → answered` (yêu cầu ≥1 message handler) |
| POST | `/service/request/<int:rid>/close` | `→ closed`, body: `closedReason?` |
| POST | `/service/request/<int:rid>/cancel` | người gửi rút, chỉ từ `new` |
| GET | `/service/stats` | KPI: tổng / đang mở / quá hạn / thời gian xử lý TB (giờ) / điểm đánh giá TB / phân bố theo loại |
| GET | `/service/attachment/<int:att_id>` | Tải file, kiểm phạm vi trước — copy pattern `/timeoff/attachment/<id>` |
| GET | `/service/config/types` · POST `/service/config/types/save` · POST `/service/config/types/toggle-active` | P6, Admin/HR Manager |

**Quy ước lỗi:** `403` ngoài phạm vi · `400` vi phạm BR (kèm `code` để SPA hiện đúng thông điệp, vd `anon_dept_too_small`, `anon_not_allowed`, `attachment_not_allowed`).

### 6.1 Đính kèm: KHÔNG nhận `attachmentIds` (sửa bản nháp, 2026-07-31)

Bảng trên viết body của `POST /service/request` có `attachmentIds?`. **Bỏ.** Cho client tự chọn id `ir.attachment` là lỗ hổng: gắn id file của người khác vào đơn của mình rồi tải về hợp lệ qua `GET /service/attachment/<id>` (route đó chỉ kiểm "attachment này thuộc đơn nào" — mà chính người gửi vừa tạo liên kết đó).

Thay bằng **nội dung base64 trong payload** (đúng cách `hocba_timeoff` nhận chứng từ y tế): `attachments: [{name, mimetype, data}]`, controller tự `create` record. Giới hạn: **PDF/JPG/PNG, ≤5MB/tệp, ≤3 tệp** (`ALLOWED_MIME`, `MAX_SIZE_BYTES`, `MAX_FILES`) → mã lỗi `bad_mimetype`, `file_too_large`, `too_many_files`, `bad_attachment`. Test `test_create_ignores_client_supplied_attachment_ids` khoá hồi quy: gửi `attachmentIds` thì đơn ra **không có** đính kèm nào.

### 6.2 Vì sao mọi route phải chạy trong savepoint

Controller **bắt** `SvcError` và trả `400` → với Odoo, request đó *thành công*, nên transaction **vẫn commit**. Không có savepoint thì mọi ghi trước chỗ lỗi bị commit mồ côi — cụ thể: `ir.attachment` vừa tạo cho một đơn bị `create_request()` bác. Vì vậy `_guarded()` bọc toàn bộ `build()` trong `request.env.cr.savepoint()`; lỗi → rollback tới savepoint + `cr.clear()` (Odoo `_FlushingSavepoint` tự làm). Test `test_attachment_rolled_back_when_request_refused` kiểm đúng hợp đồng này.

Thứ tự `except` cũng quan trọng: `SvcError` **kế thừa** `ValidationError` ⇒ phải bắt `SvcError` TRƯỚC, không thì mã lỗi nghiệp vụ bị nuốt thành `invalid` và SPA mất thông điệp riêng.

### 6.3 `meta` trả thêm dữ liệu để form tự chặn

`GET /service/meta` trả kèm `minAnonDeptSize`, `anonDailyLimit`, `anonUsedToday`, `myDepartment{id,name,headcount,hasManager,iAmManager}` — để form thực hiện được §7.3 (chặn tại chỗ, gợi ý gửi HR) thay vì để người dùng viết xong đơn mới ăn `400 anon_dept_too_small`. `iAmManager` báo trước BR-SVC-04 (TP gửi cho phòng mình sẽ bị đổi hướng về HR).

---

## 7. SPA

### 7.1 Điều hướng — file CHUNG (đã được nhóm đồng ý sửa)

[`frontend/src/app/Shell.jsx`](../../frontend/src/app/Shell.jsx) ghi ở dòng 1: *"file CHUNG, sửa phải qua review"*. Owner **đã thông báo nhóm 2026-07-26** ⇒ sửa trực tiếp. Vẫn giữ commit cho file chung **tách riêng, nhỏ**, chỉ thêm dòng — để ai merge sau nhìn diff là hiểu ngay, giảm rủi ro conflict.

Thêm view `service` vào **cả 2 mục** (đúng pattern `timeoff` — tài khoản vai trò không thấy item `need:'self'`):

```js
// mục 'Quản lý nhân sự'
{ id: 'service', label: 'Yêu cầu dịch vụ', icon: 'mail', need: 'manage' },
// mục 'Cá nhân'
{ id: 'service', label: 'Yêu cầu & Góp ý', icon: 'mail', need: 'self' },
```

`PAGE_META.service = { t: 'Yêu cầu dịch vụ nhân sự', c: 'Cá nhân / Self-service' }`.
`App.jsx`: `{view === 'service' && <Service search={search} focus={focus} />}`.
`openNotification`: cho `targetView === 'service'` truyền `focus` để mở đúng đơn (mở rộng nhánh `if (view === 'timeoff')` hiện tại).

Icon `mail` **đã có** trong `components/Icon.jsx` → không cần sửa file icon.

### 7.2 Cấu trúc component

```
frontend/src/api/service.js
frontend/src/features/service/
  Service.jsx        # tabs: Đơn của tôi | Hộp thư cần xử lý | Thống kê
  RequestForm.jsx    # gửi đơn
  RequestThread.jsx  # hội thoại 2 chiều + ghi chú nội bộ
  MyRequestsPanel.jsx
  InboxPanel.jsx     # bảng + filter state/loại/quá hạn + badge SLA
  StatsPanel.jsx
```

Tab hiện theo `meta.canHandle` (giống `TimeOff` bật tab theo `isOfficer`).

### 7.3 Yêu cầu UX của form (bảo vệ ẩn danh)

- Chọn loại → mô tả loại hiện ra; checkbox **Ẩn danh** tự `disabled` khi `!allowAnonymous`.
- Tick ẩn danh → banner: *"HR/Trưởng phòng sẽ không thấy tên và phòng ban của bạn. Bạn vẫn theo dõi và trả lời được đơn ở tab Đơn của tôi. Lưu ý: đừng viết thông tin có thể nhận ra bạn trong nội dung."*
- Tick ẩn danh → khối đính kèm **ẩn hoàn toàn** (BR-SVC-02).
- Chọn "gửi Trưởng phòng" + ẩn danh + phòng < 5 người → chặn tại chỗ, gợi ý gửi HR (`anon_dept_too_small`).
- Loại "Khiếu nại về quản lý" → ô người nhận khoá ở HR, kèm giải thích.
- Loại `hasRating` → hiện 1..5 sao.

---

## 8. Thông báo & Cron

### 8.1 `hb.notification` — sửa file dùng chung (đã được nhóm đồng ý)

Thêm `('service', 'Dịch vụ nhân sự')` vào `CATEGORY_SEL` của [`hocba_notify/models/hb_notification.py`](../../custom-addons/hocba_notify/models/hb_notification.py) — chỉ thêm 1 dòng selection, không breaking. `hocba_service` phải khai `depends: ['hocba_notify']` để `-u hocba_service` kéo theo cập nhật selection.

| kind | Ai nhận | Khi nào |
|---|---|---|
| `service_new` | Người nhận theo `recipient_scope` | Gửi đơn |
| `service_claimed` | Người gửi | Có người nhận xử lý |
| `service_reply` | Bên còn lại | Có message mới, `is_internal=False` |
| `service_answered` | Người gửi | `→ answered` |
| `service_closed` | Người gửi | `→ closed` |
| `service_overdue` | handler (hoặc mọi người nhận nếu chưa claim) | Cron |

`target_view='service'`, `target_ref=request.id`, `target_tab='mine'|'inbox'`.

**BR-SVC-11** — Với đơn ẩn danh, `title`/`body` chỉ được chứa `name` + `type_id.name` + `subject`. Cấm tên/phòng ban.

### 8.2 Cron nhắc quá hạn

`ir.cron` chạy hằng ngày, quét `state in ('new','in_progress') and deadline < now`, `dedup_key='svc_overdue_%s'`. Pattern: `hocba_timeoff/models/hb_timeoff_cron.py`.
⚠️ Odoo 19: `ir.cron` **không còn** `numbercall`/`nextcall tz` — khai theo mẫu đang chạy trong `hocba_timeoff`.

---

## 9. Test bắt buộc

`--test-tags /hocba_service`. `TransactionCase` + `@tagged('post_install', '-at_install')`, gọi thẳng hàm cấp module (`_svc_scope`, `_inbox_domain`, `_my_request_ids`) theo quy ước repo.

### 9.1 Ẩn danh (`test_anonymity.py`) — nhóm quan trọng nhất

| # | Case | Kỳ vọng |
|---|---|---|
1 | NV gửi đơn ẩn danh, HR đọc qua API | JSON **không** có `employeeName`/`department` |
2 | HR đọc trực tiếp: `env['hocba.hr.request'].with_user(hr).browse(id).read()` | không tồn tại field người gửi |
3 | `env['hocba.hr.request.sender'].with_user(hr).search([])` | `AccessError` |
4 | `create_uid` của đơn ẩn danh | `= 1` (OdooBot), không phải NV |
5 | `hb.notification` sinh ra từ đơn ẩn danh | `title`+`body` không chứa tên NV |
6 | Message của người gửi trên đơn ẩn danh, HR đọc | `authorName` = "Người gửi (ẩn danh)" |
7 | Người gửi đọc `my-requests` | thấy đúng đơn ẩn danh của mình, không thấy của người khác |

### 9.2 Phân quyền (`test_acl.py`)

| # | Case | Kỳ vọng |
|---|---|---|
8 | TP đọc đơn `recipient_scope='manager'` của **phòng khác** | ngoài `_inbox_domain`, API `403` |
9 | TP `search` đơn `type_complaint_mgr` của **chính phòng mình** | **0 record** (BR-SVC-01/10) |
10 | NV thường gọi `/service/inbox` | rỗng |
11 | NV thường `with_user(nv).search` trên `hocba.hr.request` | `AccessError` (không cấp ACL) |
12 | TP thấy đơn `both` của phòng mình | ✓ |
12b | **HR Manager** (không phải TP phòng đó) đọc đơn `recipient_scope='manager'` | ngoài `_inbox_domain`, API `403` (BR-SVC-13) |
12c | HR Manager **đồng thời là TP** phòng đó đọc đơn `manager` của phòng mình | ✓ (đọc với tư cách TP) |

### 9.3 Nghiệp vụ (`test_request_flow.py`)

| # | Case | Kỳ vọng |
|---|---|---|
13 | Ẩn danh với loại `allow_anonymous=False` | `ValidationError` |
14 | Đính kèm trên đơn ẩn danh | `400 attachment_not_allowed` (BR-SVC-02) |
15 | Ẩn danh + `manager` + phòng 3 người (`min_anon_dept_size=5`) | `400 anon_dept_too_small` (BR-SVC-03) |
15b | Cùng case 15 nhưng hạ `min_anon_dept_size=3` | gửi được → chứng minh tham số cấu hình có tác dụng |
15c | Gửi đơn ẩn danh thứ **4** trong cùng ngày (`anon_daily_limit=3`) | `400 anon_daily_limit` (BR-SVC-12) |
15d | Đơn ẩn danh thứ 4 nhưng là đơn **không ẩn danh** | gửi được (giới hạn chỉ áp cho ẩn danh) |
15e | Ẩn danh + `recipient_scope='both'` | `anon_scope_both` (BR-SVC-03, §2.2.1) |
15f | Ẩn danh + `manager` + phòng ≥ ngưỡng | gửi được; TP của phòng đó **tìm thấy** đơn trong `_inbox_domain` (chứng minh định tuyến còn hoạt động sau khi sửa BR-SVC-03) |
15g | Cùng đơn 15f, serializer cho TP | payload **không** có `department`/`departmentName` |
16 | Người gửi *là* TP của phòng đích | buộc `recipient_scope='hr'` (BR-SVC-04) |
17 | `answer` khi chưa có message handler | `400` |
18 | Người thứ 2 `answer` đơn đã claim bởi người khác | `403` (BR-SVC-05) |
19 | Người gửi reply đơn `answered` | về `in_progress` (BR-SVC-06) |
20 | `cancel` khi `state != new` | `400` |
21 | Ghi chú `is_internal` trong payload của người gửi | bị lọc bỏ (BR-SVC-07) |
22 | `deadline` theo `sla_days`; `is_overdue` bật đúng | ✓ |
23 | `name` sinh theo `ir.sequence` `YCDV/2026/0001` | ✓ |
24 | `type` với `allow_anonymous=True, allow_attachment=True` | `ValidationError` (BR-SVC-09) |

### 9.4 Gotcha khi viết test

- **Không phụ thuộc DB**: `setUp` **tự tạo** phòng ban + NV, và **set tường minh** cả 2 `ir.config_parameter` (`min_anon_dept_size`, `anon_daily_limit`). DB test hiện có phòng < 5 NV (§2.2) ⇒ test nào đọc ngưỡng từ DB sẽ đỏ/xanh ngẫu nhiên theo môi trường.
- Luồng "ẩn danh gửi TP" happy-path cần phòng **≥ 5 NV đang làm việc** → tạo đủ 5 NV trong `setUp`, mỗi NV một CCCD khác nhau (xem gạch đầu dòng dưới).
- **BR-010**: NV `official` trong test **phải** có `identification_id` **đúng 12 chữ số**, mỗi NV một giá trị khác nhau, không thì `ValidationError` ngay `setUp`.
- Odoo 19: `res.users` dùng `group_ids` (không phải `groups_id`); `identification_id` nằm trên `hr.version`.
- `.sudo()` **giữ nguyên** `env.user` ⇒ `has_group()` vẫn đọc quyền user gốc. Muốn bỏ qua phải `with_user(SUPERUSER_ID)`. Test dưới admin dễ false-positive → mọi case ACL phải `with_user(<user thật>)`.

### 9.5 Kiểm chứng test không "rỗng" (mutation test 2026-07-30)

49 test xanh ngay lần chạy đầu ⇒ phải chứng minh chúng thật sự bắt lỗi. Cố ý phá 2 cơ chế rồi chạy lại:

| Phá gì | Kết quả |
|---|---|
| `with_user(SUPERUSER_ID).create()` → `.sudo().create()` | ❌ `test_anon_create_uid_is_odoobot`: `AssertionError: 19066 != 1` |
| Thêm 1 dòng ACL `hocba.hr.request.sender` cho `hr.group_hr_manager` | ❌ `test_no_acl_row_grants_sender_table` + `test_sender_table_unreadable_even_for_hr_manager` (`AccessError not raised`) |

`3 failed of 49` — đúng 3 test, đúng chỗ. Hoàn nguyên → `0 failed, 0 error(s) of 49 tests`. Lặp lại 2 phép phá này mỗi khi sửa cơ chế ẩn danh.

**Vòng 2 — lớp API (2026-07-31, 38 test mới).** Phá 3 cơ chế của controller:

| Phá gì | Kết quả |
|---|---|
| `domain += [...tìm kiếm...]` → `domain = [...]` (mất AND phạm vi khi có từ khoá) | ❌ `test_inbox_keyword_search_keeps_scope`: `311 unexpectedly found in [311]` |
| `_create_from_payload` nhận `payload['attachmentIds']` của client | ❌ `test_create_ignores_client_supplied_attachment_ids`: `ir.attachment(306041,) is not false` |
| `_stats_payload` dùng `search([])` thay `_inbox_domain(scope)` | ❌ `test_stats_respects_br_svc_13`: `1 != 0` |

`3 failed of 87` — đúng 3 test, đúng chỗ. Hoàn nguyên → `0 failed, 0 error(s) of 87 tests`.

### 9.6 Test route mà không có `HttpCase`

Repo **không dùng `HttpCase` ở đâu cả** (18 file test của `hocba_timeoff` đều gọi thẳng helper cấp module của `controllers.main`). `test_api.py` giữ đúng quy ước đó: gọi `_meta_payload` / `_create_from_payload` / `_inbox_payload` / `_detail_payload` / `_stats_payload` / `_visible_request` với `self.env(user=...)`.

Đổi lại, phần *khai báo* route không được kiểm → thêm `test_all_spec_routes_registered`: soi `original_routing` của từng method trong `HocBaService`, khẳng định đủ **12 đường dẫn**, đúng `auth='user'`, `type='http'`, đúng `methods`, và POST phải `csrf=False` (SPA gọi bằng `fetch`, không có token CSRF). Lỗi đánh máy đường dẫn hoặc thiếu `csrf=False` sẽ đỏ ngay thay vì chỉ phát hiện lúc bấm thử trên UI.

Lệnh chạy (Docker local):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -i hocba_service -u hocba_service,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_service --stop-after-init --log-level=test
```

Cần thấy `0 failed, 0 error(s) of N tests` với **N > 0**. Lần đầu dùng `-i` (module chưa cài thì `-u` báo "0 of 0 tests").

---

## 10. Phân pha & tiêu chí hoàn thành

| Pha | Nội dung | Done khi |
|---|---|---|
| **P0** | Spec này | Owner + GVHD duyệt |
| **P1** ✅ | 4 model + ACL + seed danh mục + `ir.sequence` + 2 config param + **test §9.1 + §9.2 + §9.3** | ✅ 2026-07-30: `0 failed, 0 error(s) of 49 tests`. Nghiệp vụ đặt ở **model** (`create_request`, `action_*`, `post_message`, `serialize`) chứ không ở controller — xem §10.1 |
| **P2** ✅ | Controller `/service/*` (trừ config) + serializer chung + **BR-SVC-12 (giới hạn 3 đơn ẩn danh/ngày)** + test route | ✅ 2026-07-31: `0 failed, 0 error(s) of 87 tests` (38 test API mới). 12 route + 8 helper cấp module; xem §6.1, §6.2, §10.2 |
| **P3** ✅ | SPA phía NV: `Service.jsx`, `RequestForm`, `MyRequestsPanel`, `RequestThread` (+ `svcMeta.js`) + sửa `Shell.jsx`/`App.jsx` | ✅ 2026-08-01: gửi được đơn thường + ẩn danh, đính kèm round-trip, hội thoại 2 chiều trên đơn ẩn danh, 4 chốt §7.3 chặn tại chỗ. Kiểm tay: §10.3 |
| **P4** ✅ | SPA phía xử lý: `InboxPanel` (claim/answer/close, filter, badge SLA), ghi chú nội bộ | ✅ 2026-08-01: `0 failed, 0 error(s) of 90 tests` (thêm guard `dept_no_manager` + 3 test). HR và TP xử lý trọn vòng đời; TP chỉ thấy đơn phòng mình. Kiểm tay: §10.4 |
| **P5** | `hb.notification` producers + cron quá hạn + `StatsPanel` (KPI) | Chuông nhận đủ 6 kind, bấm nhảy đúng đơn; test §9.1 case 5 xanh |
| **P6** | Màn Cấu hình loại yêu cầu (Admin/HR Manager) — `/service/config/types*` + sửa 2 `ir.config_parameter` (`min_anon_dept_size`, `anon_daily_limit`) | Admin thêm/sửa/ẩn loại + đổi 2 ngưỡng không cần sửa code; BR-SVC-09 chặn được |

**Thứ tự bắt buộc:** backend chắc (model → security → API → test) trước, UI sau — theo CLAUDE.md.

### 10.1 Hai điều chỉnh so với bản spec khi thực thi P1

**(a) Nghiệp vụ đặt ở model, không ở controller.** Repo có tiền lệ đặt logic ở hàm cấp module của controller (`hocba_timeoff._apply_quota_adjustment`) và test gọi thẳng hàm đó. Ở đây làm khác: `create_request` / `action_claim|answer|close|cancel` / `post_message` / `serialize` nằm trên model `hocba.hr.request`. Lý do: P1 phải test được **toàn bộ 13 BR** khi chưa có API; nếu logic nằm ở controller thì P1 chỉ test được model rỗng và mọi rule phải chờ P2. Controller P2 vì vậy rất mỏng — parse JSON, gọi model, `except SvcError as e → 400 + e.code`. Riêng `_svc_scope` / `_inbox_domain` / `_my_request_ids` vẫn là **hàm cấp module** đúng convention để test gọi trực tiếp.

**(b) `.sudo()` KHÔNG đủ cho lớp L2 — phải `with_user(SUPERUSER_ID)`.** Odoo 19: `.sudo()` chỉ bật cờ `su`, **`env.uid` không đổi** ⇒ `X.sudo().create(...)` vẫn ghi `create_uid` = nhân viên. Đo bằng mutation test: đổi về `.sudo()` thì `create_uid = 19066` (id user NV) thay vì `1`. Điều này áp cho cả `write()` — người gửi ẩn danh tự rút đơn bằng `.sudo()` sẽ để lại `write_uid` chỉ đúng họ.

⇒ Quy tắc trong module: ghi do **người gửi** kích hoạt (tạo đơn, tạo sender row, tạo message, rút/đóng đơn, mở lại hội thoại theo BR-SVC-06) dùng `_as_system()` = `with_user(SUPERUSER_ID)`; ghi do **người xử lý** kích hoạt dùng `.sudo()` để `write_uid` còn vết audit của handler. Test `test_anon_create_uid_is_odoobot` + `test_anon_sender_cancel_does_not_leak_write_uid` khoá hồi quy chỗ này.

### 10.2 Ba điều chỉnh khi thực thi P2

**(a) Bỏ `attachmentIds` khỏi body `POST /service/request`** — lý do bảo mật, xem §6.1.

**(b) Mọi route chạy trong `cr.savepoint()`** — vì bắt lỗi rồi trả 400 vẫn commit transaction, xem §6.2.

**(c) Helper cấp module dùng `env._()` chứ không `_()`.** Odoo 19 suy ngôn ngữ dịch từ frame locals: tìm `context`, `kwargs['context']`, `self.env`, rồi `http.request`, rồi `cr`+`uid`. Hàm cấp module chỉ có tham số `env` (không có `self`, không có `uid`) ⇒ ngoài request context (tức khi **test** gọi trực tiếp) `_()` không suy được lang và log `WARNING ... no translation language detected` **kèm cả stack trace** cho mỗi lần raise. Dùng `env._(...)` (API Odoo 19, `Environment._`) lấy lang thẳng từ env → log test sạch, hành vi trong request không đổi.

Ngoài ra, thêm `@api.depends('state', 'deadline')` cho `_compute_is_overdue`: field non-stored không khai depends thì Odoo **không** invalidate cache khi `deadline` đổi, nên chỗ nào đọc `is_overdue` sau khi `write({'deadline': ...})` phải tự `invalidate_recordset` — một cái bẫy im lặng cho `_stats_payload`.

### 10.3 P3 — kiểm tay + 3 điều chỉnh

**Cách kiểm.** SPA không có test tự động trong repo (không eslint/vitest), nên P3 kiểm tay trên **DB local `hocba_hrm`** bằng một container Odoo thứ hai ở cổng **8079** (`docker compose … run --rm -d -p 8079:8069 --name hb_preview_local odoo odoo -d hocba_hrm -u hocba_service …`) để **không đụng** stack Neon đang chạy ở 8069. Tài khoản demo đã seed: xem `docs/DB_TEST_DATA.md`.

Đã kiểm, mỗi mục là một nhánh render riêng:

| Kiểm | Kết quả |
|---|---|
| Gửi đơn ẩn danh (Đánh giá & góp ý, 4★) → `YCDV/2026/0430` | Người gửi thấy “Bạn (ẩn danh)”, **không** có dòng phòng ban |
| HR đọc chính đơn đó qua `/inbox` + `/request/<id>` | `senderName='Người gửi (ẩn danh)'`, `departmentName=null`, tác giả tin nhắn cũng ẩn danh, chuỗi tên NV/phòng **không** xuất hiện ở bất kỳ đâu trong payload — lớp L3 đứng vững trên HTTP thật, không chỉ trong test |
| Hội thoại 2 chiều trên đơn ẩn danh | Người gửi reply được, bong bóng ghi “Bạn (ẩn danh)” |
| Đính kèm PDF (đơn thường) | Tạo `ir.attachment` từ base64 → `GET /service/attachment/<id>` trả đúng `application/pdf` + `content-disposition` + nội dung |
| Ẩn danh + gửi TP, phòng 3 NV (ngưỡng 5) | Chặn tại form, nút “Gửi đơn” `disabled`, thông điệp gợi ý gửi HR — **không** phát sinh request nào |
| Ẩn danh bật | Khối đính kèm **biến mất** (0 `input[type=file]`), option “HR và Trưởng phòng” **bị loại khỏi** select (BR-SVC-12 chặn từ gốc) |
| TP của chính phòng đó chọn “gửi Trưởng phòng” | Hiện cảnh báo BR-SVC-04 “đơn sẽ được chuyển về HR” |
| Loại “Khiếu nại về quản lý” | Ô người nhận khoá (icon ổ khoá, “HR (bắt buộc)”) + giải thích BR-SVC-01 |
| Console browser | Không có lỗi |

**(a) `PAGE_META.service.c` = `'Nhân sự / Yêu cầu & Góp ý'`, không phải `'Cá nhân / Self-service'` như §7.1.** View `service` nằm ở **cả hai** mục nav nhưng `PAGE_META` lại theo view ⇒ crumb “Cá nhân” sai khi HR mở màn này. Dùng chuỗi trung tính đúng cho cả hai. (`timeoff` đang mắc đúng lỗi này — không sửa kèm ở đây để giữ commit nhỏ.)

**(b) `MyRequestsPanel` dùng `tbl-wrap tbl-scroll`.** `table.tbl td` mặc định `white-space: nowrap; max-width: 0; overflow: hidden` ⇒ badge đặt sau tiêu đề **bị cắt mất hoàn toàn** — mà “Ẩn danh” là nhãn quan trọng nhất của màn này. Modifier `tbl-scroll` (đã có, `hocba_recruitments` dùng) bỏ giới hạn đó; ô tiêu đề tự cắt bằng `div` bên trong `max-width: 320px`.

**(c) `fmtDateTime` phải ép UTC (`svcMeta.js`).** `serialize()` trả `fields.Datetime.to_string()` = chuỗi UTC **không hậu tố** (`'2026-08-01 00:35:00'`); `new Date(s)` của JS hiểu chuỗi đó là **giờ máy** ⇒ lệch 7 tiếng ở VN. Phải `s.replace(' ','T') + 'Z'` rồi mới để browser đổi về giờ địa phương. ⚠️ `hocba_timeoff/HistoryTimeline.jsx` đang mắc đúng lỗi này (hiện giờ UTC) — việc riêng, không sửa kèm.

**Chưa làm ở P3 (đúng phạm vi):** tab “Cần xử lý” hiện **khối placeholder ghi rõ “Đang làm — P4”** cho tài khoản `canHandle`. Lý do bày cả 2 item nav ngay ở P3 (thay vì thêm item `need:'manage'` ở P4): file chung `Shell.jsx` chỉ sửa **một lần**, giảm rủi ro conflict như §11 yêu cầu.

### 10.4 P4 — kiểm tay + 4 điều chỉnh

Môi trường kiểm: container Odoo **thứ hai** cổng 8079 trên DB local `hocba_hrm` (stack Neon 8069 của nhóm không bị chạm), tài khoản demo `svc.hr` / `svc.tp` / `svc.nv` / `svc.nvnho` (mật khẩu `hocba@123`, xem `docs/DB_TEST_DATA.md`).

| Kiểm | Kết quả |
|---|---|
| HR mở tab “Cần xử lý” | 6 đơn thuộc phạm vi HR; đơn `recipient_scope='manager'` (`YCDV/2026/0585`) **không** xuất hiện kể cả khi chọn filter “Tất cả” — BR-SVC-13 đứng vững ở UI |
| Trưởng phòng (`svc.tp`) mở tab “Cần xử lý” | Đúng **1 đơn** của phòng mình; không thấy đơn nào của HR, không thấy đơn “Khiếu nại về quản lý” (BR-SVC-01) |
| TP nhận xử lý → trả lời → chốt | Chạy trọn, không lỗi quyền — TP **không có ACL** trên `hocba.hr.request`, toàn bộ đi qua `.sudo()` sau khi lọc bằng `_inbox_domain` |
| Vòng đời đầy đủ (HR, `YCDV/2026/0588`) | `Mới` → nhận xử lý (`Đang xử lý`, hiện tên người xử lý) → ghi chú nội bộ → trả lời công khai → `Đã trả lời` (hiện “Trả lời lúc”) → đóng kèm lý do (`Đã đóng`, ô trả lời biến mất vì `canReply=false`) |
| BR-SVC-05 ở UI | Sau khi CHỈ có ghi chú nội bộ: nút “Chốt đã trả lời” `disabled` + hiện dòng nhắc; sau khi có 1 tin công khai: nút mở, dòng nhắc biến mất |
| BR-SVC-07 phía người gửi | Người xử lý thấy 2 tin, người gửi (`svc.nvnho`) chỉ thấy **1** — nội dung ghi chú nội bộ và badge “Ghi chú nội bộ” **không** có trong payload người gửi |
| Filter trạng thái / loại / “chỉ đơn trễ hạn” | Trễ hạn → đúng 1 đơn quá hạn; loại “Đánh giá & góp ý” + trạng thái `Đang mở` → lọc đúng; `Đã đóng` → đúng đơn vừa đóng |
| Tìm kiếm (ô search ở topbar, debounce 350ms) | Từ khoá **chỉ nằm trong nội dung đơn** (“ngân hàng”) vẫn tìm ra ⇒ `q` chạy ở BE thật, không phải lọc bảng ở client; không khớp → empty state đúng |
| Badge SLA | `Còn N ngày` (xanh), `Hạn hôm nay`/≤1 ngày (hổ phách), `Trễ hạn` (đỏ); đơn đã kết thúc **không** hiện badge |
| Guard `dept_no_manager` qua HTTP | Bỏ trưởng phòng của phòng đích → `POST /service/request` với `recipientScope='manager'` **và** `'both'` đều trả `400 dept_no_manager`; `'hr'` vẫn `200`. Form cũng chặn tại chỗ, nút `disabled` |
| Console browser | Không có lỗi |

**(a) Thêm guard `dept_no_manager` ở model (việc backend duy nhất của P4).** `create_request()` trước đây nhận `recipient_scope='manager'` khi phòng đích **chưa có** `manager_id` ⇒ `_inbox_domain()` không khớp hộp thư nào ⇒ **đơn mồ côi, không ai đọc**. Form P3 đã chặn nhưng gọi API trực tiếp thì vẫn tạo được. Nay chặn ở model, **kể cả `scope='both'`**: im lặng hạ về HR là đổi người đọc đơn sau lưng người gửi — khác bản chất với BR-SVC-04 (ở đó phương án còn lại là tự xử đơn của chính mình, bất khả). 3 test mới trong `test_request_flow.py`.

**(b) 3 test `/stats` chuyển sang đo BIẾN THIÊN thay vì số tuyệt đối.** `test_stats_counts_and_averages` / `test_stats_respects_br_svc_13` / `test_stats_empty_inbox_has_no_division_by_zero` khẳng định `total == 0` ở đầu bài ⇒ **đỏ trên mọi DB có đơn tồn đọng** (kể cả DB local sau khi seed demo). Nay: chụp `before` rồi so delta; trung bình cộng suy kỳ vọng từ `before` (`(old_avg*old_n + 5)/(old_n+1)`) nên vẫn kiểm được chính xác; bài “không chia cho 0” đổi sang dùng TP của phòng do `setUp` tự tạo — hộp thư chắc chắn rỗng ở mọi DB. Cùng tinh thần với `common.py` (không phụ thuộc dữ liệu DB).

**(c) Bảng hộp thư 6 cột, không phải 9.** Đo thật ở viewport 1500px: 9 cột = **1394px** trong khung **1194px** ⇒ trạng thái và nút “Xử lý” nằm ngoài khung, phải cuộn ngang mới thao tác được. Rút gọn: bỏ cột “Gửi lúc” (giờ gửi xem trong `RequestThread`; với người xử lý thì **hạn** mới là con số phải nhìn — SLA tính theo ngày nên hạn chỉ hiện ngày), “Loại” xuống dòng phụ dưới tiêu đề, “Người xử lý” gộp vào ô trạng thái. Chữ dài tự cắt bằng `span` có `maxWidth` + `title` (vì `.tbl-scroll` đã bỏ ellipsis mặc định của `td`).

**(d) `setData(null)` chuyển vào trong `load()` (`InboxPanel` **và** `MyRequestsPanel`).** Đặt ở `onChange` của select là bẫy: nếu giá trị **không đổi thật**, `load` giữ nguyên identity ⇒ `useEffect` không chạy lại ⇒ **skeleton treo vĩnh viễn** (gặp thật khi kiểm tay). Đặt trong `load` thì mỗi lần filter đổi vẫn có skeleton, mà chọn lại giá trị cũ thì bảng đứng yên thay vì trắng.

**Ghi nhận thêm (không sửa ở P4):** `base.css` không có rule `.btn:disabled` ⇒ mọi nút `disabled` toàn SPA vẫn trông bấm được. `RequestThread` tạm dim tại chỗ bằng inline style; sửa gốc là 1 rule CSS ở file chung, tách thành việc riêng cho cả nhóm.

---

## 11. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Rò rỉ danh tính qua đường chưa lường (notification, attachment, log) | **Cao** | 4 lớp §4.2 + 7 test §9.1; serializer **một hàm duy nhất** dùng chung mọi route |
| Suy luận danh tính từ phòng ban / nội dung | Trung bình | BR-SVC-03 (`min_anon_dept_size`) + không lưu `target_department_id` + banner nhắc người gửi |
| **DB test có phòng < 5 NV ⇒ demo luồng "ẩn danh gửi TP" bị chặn** | **Cao (demo)** | Ngưỡng là `ir.config_parameter`, hạ xuống 3 lúc demo không cần sửa code; test tự tạo phòng riêng (§9.4). Kiểm headcount phòng đích **trước** buổi demo |
| Conflict `Shell.jsx` / `App.jsx` / `hb_notification.py` (file chung, 5 người) | Thấp (đã thông báo nhóm) | Commit riêng, nhỏ, chỉ thêm dòng; làm sớm ở P3 |
| Lạm dụng ẩn danh (spam, vu khống) | Thấp | BR-SVC-12 giới hạn 3 đơn ẩn danh/NV/ngày (làm ở **P2**, không hoãn tới P5); danh tính vẫn có ở bảng `sender` cho điều tra chính thức |
| Không đủ thời gian tới P6 | Trung bình | P1–P4 đã là bản demo trọn vẹn; P5/P6 cắt được mà không hỏng luồng |

---

## 12. Câu hỏi mở

**Không còn câu hỏi mở chặn triển khai.** 4 câu hỏi của bản nháp đã được owner chốt 2026-07-26 → xem §1.1 mục 5–8:

| Câu hỏi | Chốt |
|---|---|
| Giới hạn đơn ẩn danh/NV/ngày | **3**, cấu hình được (BR-SVC-12) |
| Ngưỡng phòng cho ẩn danh gửi TP | **5**, cấu hình được; **DB test có phòng < 5 NV** → hạ ngưỡng lúc demo |
| SLA ngày dương lịch vs ngày làm việc | **Ngày dương lịch** |
| HR Manager giám sát TP xử lý | **Không** (BR-SVC-13) |

Việc cần làm trước demo (không chặn code): kiểm headcount các phòng trong DB đang dùng, chọn giá trị `min_anon_dept_size` phù hợp.

---

## 13. Tham chiếu

- Convention phân quyền: [`hocba_timeoff/controllers/main.py:125`](../../custom-addons/hocba_timeoff/controllers/main.py) `_scope_for`
- Helper phòng ban: [`hocba_hrm/controllers/main.py:1364`](../../custom-addons/hocba_hrm/controllers/main.py) `_managed_department_ids`
- Thông báo in-app: [`hocba_notify/models/hb_notification.py`](../../custom-addons/hocba_notify/models/hb_notification.py) `_notify()`
- Mẫu đơn có state machine: [`hocba_employees/models/hocba_offboarding.py`](../../custom-addons/hocba_employees/models/hocba_offboarding.py)
- Mẫu `ir.sequence`: `hocba_employees/data/hocba_offboarding_data.xml`
- Quy ước frontend: `docs/superpowers/specs/QUY_UOC_FRONTEND.md`
- Tài khoản test: `docs/DB_TEST_DATA.md`
