# Đặc tả thiết kế — Nâng cấp module Nghỉ phép cho HR (quản lý quỹ phép)

> Theo khung `SPEC_API_TIMEOFF.md` + quy ước `QUY_UOC_FRONTEND.md`.
> Quy trình: spec (file này) → `writing-plans` (plan TDD) → code đỏ→xanh→commit.

**Domain:** `timeoff` · **Owner:** Nhật Anh
**Module BE:** `hocba_timeoff` (controller chung prefix `/hocba-hrm/api/timeoff/*`)
**Màn FE:** `frontend/src/features/timeoff/`
**Phiên bản:** 0.1 (draft, chờ duyệt) · **Ngày:** 21/06/2026

---

## 0. Bối cảnh & mục tiêu

Module Nghỉ phép hiện đã có: tự tạo/hủy đơn, duyệt 1–2 cấp, dashboard, lịch, tab
"Đơn đã duyệt" (kèm **sort bar** + **xuất Excel** vừa thêm — `utils/xlsx.js`,
`features/timeoff/SortBar.jsx`). Phần còn thiếu, dưới góc nhìn **HR vận hành**, là
bộ công cụ quản lý **quỹ phép** và **điều phối nhân sự khi nghỉ**.

Spec này gom các tính năng đó thành **6 phase độc lập, mỗi phase ship được**, ưu tiên
Phase 1–3 (chủ đề "quỹ phép" — giá trị HR cao nhất, backend phần lớn đã có sẵn).

> **Ngoài phạm vi (để trống chờ dữ liệu trung tâm):** logic nghỉ phép **riêng cho
> giáo viên** (quỹ theo lịch dạy, bù tiết, conflict lịch lớp nâng cao). Khi trung tâm
> đưa dữ liệu sẽ bổ sung phase riêng. Các phase dưới đây dùng quỹ phép chuẩn, áp
> dụng cho mọi nhân viên — không chặn việc gắn thêm logic giáo viên sau.

### Nguyên tắc kỹ thuật chung (áp cho mọi phase)
- Backend chắc trước: **model + security (`ir.model.access.csv`/record rule) + API + test** xanh rồi mới làm UI.
- Phân quyền tái dùng `_scope()` / `_dept_domain()` / `_scoped_departments()` / `_managed_department_ids()` đã có trong `controllers/main.py`. **Không** tự chế cơ chế quyền mới.
- Endpoint quản lý: `sudo()` + lọc phòng ban tường minh (role mới không gán group `hr_holidays`). Ghi dữ liệu nhạy cảm: kiểm `scope` **trước**, trả `403 {'error':'forbidden'}` nếu thiếu quyền.
- Chỉ làm việc với **7 loại nghỉ Học Bá** qua `_hb_leave_type_ids()` (DB có ~88 loại demo).
- FE: tái dùng `SortBar` + `sortRows`, `downloadXlsx`, `Badge`, `states`, `Modal`, `fmtDate`; không format tay (quy ước §5c).
- Test BE: chạy theo CLAUDE.md (`MSYS_NO_PATHCONV=1 … -u hocba_timeoff,hocba_employees --test-tags /hocba_timeoff`), cần thấy `0 failed, 0 error(s) of N tests` với N > 0. NV `official` phải có `identification_id` 12 số (BR-010).

---

## PHASE 1 — Bảng "Quỹ phép" toàn nhân viên (HR/Trưởng phòng)

**Vấn đề:** Số dư phép hiện chỉ xem được của chính mình (tab *Của tôi*). HR không có
chỗ trả lời "nhân viên X còn mấy ngày phép?".

### Backend
- **Endpoint mới:** `GET /hocba-hrm/api/timeoff/balances?year=&dept=&type=`
  - Chỉ `scope.canApprove` (HR/Admin = mọi phòng; Trưởng phòng = phòng được giao). Khác → `403`.
  - Duyệt tập nhân viên trong phạm vi (`hr.employee` lọc theo `_dept_domain`/`deptIds`), với mỗi NV tính số dư theo 7 loại HB — **tái dùng đúng cách `_balances()`**: `hr.leave.type.with_context(employee_id=…)` đọc `max_leaves`, `leaves_taken`, `virtual_remaining_leaves`.
  - Trả về:
    ```json
    {
      "isOfficer": true, "isHrManager": true, "year": 2026,
      "rows": [{
        "employeeId": 12, "employee": "Nguyễn Văn A", "department": "Giáo vụ",
        "balances": [{"leaveTypeId":3,"leaveType":"Phép năm","allocated":12,"taken":4,"remaining":8,"kind":"teal"}],
        "totalRemaining": 8.0, "totalAllocated": 12.0, "totalTaken": 4.0
      }],
      "leaveTypes": [{"id":3,"name":"Phép năm"}],
      "allDepartments": [{"id":1,"name":"Giáo vụ"}],
      "kpi": {"employees": 25, "totalRemaining": 180.5, "lowBalance": 3}
    }
    ```
  - `kpi.lowBalance` = số NV có `totalRemaining <= 2` (ngưỡng cảnh báo, hằng số `LOW_BALANCE_DAYS = 2`).
- **Hiệu năng:** tránh N+1 — gom `hr.leave.type` 1 lần, lặp NV với context; nếu chậm với >200 NV thì cân nhắc `_read_group` trên allocation/leave (ghi chú trong plan, chưa tối ưu sớm).

### Test (BE)
- HR thấy mọi phòng; Trưởng phòng chỉ thấy NV phòng mình (+ phòng con); NV thường → `403`.
- `totalRemaining`/`kpi` cộng đúng; chỉ trả 7 loại HB.

### Frontend
- Tab mới **"Quỹ phép"** trong nhánh officer (`TimeOff.jsx`, cạnh "Đơn đã duyệt").
- `BalancesPanel.jsx`: filter năm + phòng ban (mẫu `ApprovedPanel`), KPI (Tổng NV / Tổng ngày còn lại / Số NV sắp hết phép), bảng mỗi NV 1 dòng (cột: NV, phòng ban, các loại "còn/đã cấp", tổng còn lại) + **SortBar** + **Xuất Excel** (`downloadXlsx`).
- Dòng `totalRemaining <= 2` tô badge đỏ/amber (`_balance_kind`).

### Acceptance
HR mở tab "Quỹ phép" → thấy số dư mọi NV, lọc/sắp xếp/xuất Excel; Trưởng phòng chỉ thấy phòng mình; NV thường không thấy tab.

---

## PHASE 2 — Điều chỉnh quỹ phép thủ công + nhật ký

**Vấn đề:** Không có cách cộng/trừ phép (thưởng, thâm niên, sửa nhầm) ngoài việc sửa
thẳng DB; không lưu vết ai chỉnh.

### Backend
- **Model nhật ký mới:** `hb.leave.adjustment`
  | field | kiểu | ghi chú |
  |---|---|---|
  | `employee_id` | M2O `hr.employee` | required, index |
  | `leave_type_id` | M2O `hr.leave.type` | required (trong 7 loại HB) |
  | `delta_days` | Float | required, ≠ 0 (dương = cấp thêm, âm = trừ) |
  | `reason` | Text | required |
  | `allocation_id` | M2O `hr.leave.allocation` | allocation được tạo/sửa |
  | `applied_by` | M2O `hr.employee` | mặc định người đăng nhập |
  | `applied_date` | Datetime | default now |
  - `_order = 'applied_date desc'`. (Mẫu có sẵn: `hb.leave.policy.log`.)
- **Cách áp delta:** tạo 1 `hr.leave.allocation` mới (state `validate`, `holiday_status_id`, `number_of_days = delta_days`, `allocation_type='regular'`, **không** đặt `x_from_policy` để policy engine không expire). Trừ phép = allocation âm nếu Odoo 19 cho phép; nếu không, dùng cơ chế giảm allocation hiện có — **xác nhận trong plan** (rủi ro: Odoo có thể chặn allocation âm → fallback: chỉnh `number_of_days` của allocation thủ công gần nhất). → liên kết `allocation_id`.
- **Endpoints:**
  - `POST /hocba-hrm/api/timeoff/balances/adjust` — body `{employeeId, leaveTypeId, deltaDays, reason}`. **Chỉ `scope.isHrManager`** (HR Manager/Admin; Trưởng phòng **không** được chỉnh quỹ → quyết định này cần team xác nhận). Validate: NV trong phạm vi, loại ∈ HB, `deltaDays ≠ 0`, `reason` không rỗng, không cho `remaining` âm khi trừ (trả lỗi rõ ràng). Trả về dòng balance mới của NV.
  - `GET /hocba-hrm/api/timeoff/balances/history?employeeId=&leaveTypeId=` — danh sách điều chỉnh (HR/Trưởng phòng phạm vi liên quan được xem).
- **Security:** thêm dòng `ir.model.access.csv` cho `hb.leave.adjustment` (HR Manager CRUD; HR User/Trưởng phòng read).

### Test (BE)
- Chỉ HR Manager `adjust` được; Trưởng phòng/NV → `403`.
- `delta_days = +3` → `virtual_remaining_leaves` tăng 3; tạo đúng 1 bản ghi log liên kết allocation.
- Trừ vượt số dư → `ValidationError`/400 có thông điệp; `deltaDays = 0` hoặc `reason` rỗng → 400.

### Frontend
- Từ `BalancesPanel`: nút "Điều chỉnh" trên mỗi dòng (chỉ `isHrManager`) → `AdjustQuotaModal` (chọn loại nghỉ, nhập +/− ngày, lý do bắt buộc).
- Modal "Lịch sử" xem `history` của NV (ngày, loại, delta, lý do, người chỉnh).

### Acceptance
HR Manager cộng/trừ phép có lý do; số dư cập nhật ngay; có nhật ký truy vết; vai trò khác không thấy/không gọi được.

---

## PHASE 3 — Cảnh báo phép tồn cuối năm

**Vấn đề:** Cuối năm HR cần biết ai còn nhiều phép chưa dùng (để nhắc xài / xử lý
carry-over / mất phép).

### Backend
- Mở rộng `GET /balances` (Phase 1) thêm `?filter=expiring` và field mỗi dòng:
  `atRisk` (bool, `remaining >= AT_RISK_DAYS`, mặc định `AT_RISK_DAYS = 5`, chỉ tính
  **Phép năm** `hb_leave_type_annual`), `expireDate` (cuối năm hiện tại, hoặc theo
  chính sách carry-over nếu có cấu hình trong `hb.timeoff.policy.rule`).
- (Tùy chọn) tái dùng cron có sẵn `ir_cron_reminder_data.xml` để gửi nhắc — chỉ làm nếu kênh thông báo Phase 5 đã có; nếu không, để cảnh báo dạng hiển thị.

### Test (BE)
- NV còn ≥ 5 ngày Phép năm → `atRisk=true`; lọc `filter=expiring` chỉ trả NV at-risk.

### Frontend
- Trong `BalancesPanel`: chip lọc **"Sắp mất phép"** + KPI "N nhân viên còn ≥ 5 ngày phép năm"; dòng at-risk tô amber, có nhãn ngày hết hạn.

### Acceptance
HR lọc nhanh danh sách NV còn nhiều phép chưa dùng kèm ngày hết hạn; xuất Excel để gửi nhắc.

---

## PHASE 4 — Cảnh báo trùng lịch nghỉ (coverage)

**Vấn đề:** Duyệt đơn mà không thấy "ngày đó phòng đã có mấy người nghỉ" → dễ làm
trống phòng.

### Backend
- `GET /hocba-hrm/api/timeoff/coverage?from=&to=&dept=` → mỗi ngày trong khoảng:
  `{date, count, employees:[...]}` (đơn `state='validate'` chồng lấp, lọc phòng ban theo scope).
- Helper dùng lại trong endpoint duyệt: khi mở 1 đơn, trả `overlapCount` = số người **cùng phòng** nghỉ trùng khoảng ngày của đơn.

### Test (BE)
- 2 đơn cùng phòng trùng ngày → `count=2`; lọc phòng ban đúng scope.

### Frontend
- `CalendarPanel`: ngày có ≥ `OVERLAP_WARN` (mặc định 3) người nghỉ tô đậm/cảnh báo.
- `ApprovalPanel` (modal duyệt): badge "Cùng phòng đang nghỉ ngày này: N người" để người duyệt cân nhắc.

### Acceptance
Người duyệt thấy mức độ trùng trước khi bấm Duyệt; lịch nổi bật ngày quá tải.

---

## PHASE 5 — Thông báo & nhật ký thao tác đơn (audit)

**Vấn đề:** Đơn "nằm chết" không ai biết; khi tranh chấp không có vết. SPA **chưa có**
chuông thông báo riêng → nhân viên/người duyệt không biết có việc cần xử lý.

> **Quyết định (chốt câu hỏi #5):** SPA `hocba_hrm` **chưa** có hệ thống chuông chung →
> Phase 5 **tự dựng chuông thông báo riêng cho TimeOff** ở **góc phải header** (kiểu Odoo).
> **Không** dùng `mail.message` needaction làm nguồn chuông: trong Odoo 19
> `res.users.notification_type` là field computed/stored, **mặc định `'email'`** (chỉ user
> thuộc group `mail.group_mail_notification_type_inbox` mới là `'inbox'`), nên đa số tài
> khoản SPA sẽ có inbox needaction rỗng → chuông trống. Thay vào đó dùng **model riêng**
> `hb.leave.notification` (giống pattern `hb.leave.adjustment`) để chủ động, robust, test
> tất định. Audit/lịch sử thao tác đơn **vẫn** dùng `message_post` (chatter) của `hr.leave`.

### Backend
- **Model thông báo mới:** `hb.leave.notification` — `recipient_id` (M2O `res.users`,
  index, cascade), `leave_id` (M2O `hr.leave`, index, cascade), `kind`
  (`pending`/`approved`/`refused`), `title` (Char), `body` (Char), `is_read` (Bool).
  ACL: `base.group_user` read, `hr.group_hr_manager` CRUD (mọi thao tác qua controller
  chạy `sudo()` sau khi pin `recipient_id = uid`).
- **Sinh thông báo (helper cấp module, controller gọi):**
  - Tạo đơn → `_notify_request_created`: báo người duyệt phạm vi (`_approver_users` =
    trưởng phòng theo chuỗi phòng ban của NV gồm phòng cha + toàn bộ HR Manager, trừ
    chính chủ đơn), `kind='pending'`; + `message_post` ghi chú audit.
  - Duyệt/từ chối → `_notify_decision`: báo **chủ đơn** (`leave.employee_id.user_id`),
    `kind='approved'`/`'refused'`; + `message_post` ghi chú audit kèm người duyệt.
- **Endpoint cho chuông** (lọc `recipient_id = uid`, `sudo()` sau khi pin):
  - `GET /hocba-hrm/api/timeoff/notifications?limit=&onlyUnread=` → `{items:[{id,
    requestId, title, body, kind, isRead, createdAt}], unread: N}` (badge = `unread`).
  - `POST /hocba-hrm/api/timeoff/notifications/<id>/read` — đánh dấu 1 tin đã đọc; chỉ
    tin của chính mình (khác → `403`).
  - `POST /hocba-hrm/api/timeoff/notifications/read-all` — đánh dấu tất cả đã đọc.
- **Audit:** `GET /hocba-hrm/api/timeoff/request/<id>/history` trả dòng thời gian các
  `message_post` (tạo/duyệt/từ chối, kèm người + ghi chú) theo thứ tự tăng dần; xem được
  nếu là chủ đơn hoặc người duyệt trong phạm vi (`404` nếu không tồn tại, `403` nếu ngoài
  phạm vi).

### Test (BE) — ✅ đã xanh (6 test, `tests/test_notifications.py`)
- Tạo đơn → sinh thông báo cho **đúng** trưởng phòng của NV + HR (không lọt sang trưởng
  phòng phòng khác, không tự báo cho chủ đơn); duyệt/từ chối → thông báo cho chủ đơn với
  `kind` tương ứng.
- `_list_notifications` chỉ trả tin của user gọi, `unread` đếm đúng (+ filter `onlyUnread`);
  `/read` set 1 tin về đã đọc (unread giảm 1); `/read-all` đưa unread về 0; đánh dấu tin
  người khác → `False` (403), không đổi.
- `_request_history` trả đúng trình tự create → approve; chủ đơn xem được; ngoài phạm vi
  (trưởng phòng khác / NV thường) → `False` (403); đơn không tồn tại → `None` (404).

### Frontend
- **Chuông thông báo ở góc phải header SPA** (component mới `NotificationBell.jsx`,
  đặt trong layout chung của `/hocba-hrm` cạnh tên user): icon chuông + **badge số chưa
  đọc**; click mở dropdown danh sách (mới nhất trước), mỗi dòng: tiêu đề, mô tả ngắn,
  thời gian (`fmtDate`), trạng thái đọc; click 1 dòng → gọi `/read` + điều hướng tới
  đơn liên quan (mở tab/đơn `requestId`); nút **"Đánh dấu tất cả đã đọc"**.
  - Poll `GET /notifications?onlyUnread` định kỳ (vd 60s) hoặc refetch khi đổi tab để
    cập nhật badge — **chốt cơ chế trong plan** (không cần realtime/websocket).
  - Tái dùng `Badge`, `Modal`/dropdown sẵn có, `fmtDate`; không format tay.
- Badge số đơn chờ trên tab "Chờ duyệt"; mục **"Lịch sử xử lý"** (timeline) trong modal
  chi tiết đơn (`ApprovedPanel`/`ApprovalPanel`) đọc từ `/request/<id>/history`.

### Acceptance
Người duyệt thấy **chuông sáng** khi có đơn mới; nhân viên thấy chuông khi đơn được
duyệt/từ chối; click vào thông báo mở đúng đơn và tự đánh dấu đã đọc; mỗi đơn có dòng
thời gian thao tác đầy đủ.

---

## PHASE 6 — Tinh chỉnh tính ngày (nửa ngày + loại trừ lễ/cuối tuần)

**Vấn đề:** Chỉ nghỉ nguyên ngày; nghỉ qua dịp lễ vẫn bị trừ phép.

### Backend
- **Nửa ngày:** dùng `request_unit='half_day'`/`request_date_from_period` của `hr.leave` (Odoo hỗ trợ sẵn theo `hr.leave.type.request_unit`). Mở `request_unit` cho loại HB phù hợp + nhận `period` (morning/afternoon) ở `POST /request`.
- **Loại trừ lễ/cuối tuần:** đảm bảo `number_of_days` tính theo `resource.calendar` (working days) — kiểm tra lịch làm việc chuẩn + `hr.leave.mandatory.day`/`hb.work.day` đã seed; bổ sung nếu cần.

### Test (BE)
- Đơn nửa ngày → `number_of_days = 0.5`; đơn vắt qua T7/CN hoặc ngày lễ → không tính ngày nghỉ vào đó.

### Frontend
- `LeaveForm`: chọn "Cả ngày / Sáng / Chiều" khi loại nghỉ cho phép; hiển thị số ngày thực trừ.

### Acceptance
Nhân viên xin nửa ngày; số ngày trừ đúng, bỏ qua cuối tuần/lễ.

---

## PHASE 7 — Rút / hủy đơn đã duyệt (có phê duyệt lại)

**Vấn đề:** Hiện chỉ hủy được đơn khi đang **chờ duyệt**. Đơn đã duyệt
(`state='validate'`) mà nhân viên muốn rút (đổi kế hoạch, ốm bất ngờ không nghỉ
nữa…) thì phải nhờ HR sửa thẳng DB → quỹ phép lệch, không có vết.

### Backend
- **Luồng:** nhân viên gửi **yêu cầu rút** trên đơn đã duyệt → đơn chuyển trạng thái
  "chờ duyệt rút" → người duyệt ban đầu (trưởng phòng/HR theo `_scope()`) **duyệt** thì
  đơn về `cancel`/`refuse` và **hoàn trả số ngày** vào quỹ; **từ chối** thì đơn giữ
  nguyên `validate`. Không cho rút đơn có ngày nghỉ **đã trôi qua** (chỉ rút phần
  tương lai — xác nhận cách xử lý đơn vắt ngang hôm nay trong plan).
- **Cơ chế Odoo:** tái dùng `action_refuse` / cơ chế cancel của `hr.leave` để nhả
  `number_of_days` về `virtual_remaining_leaves` (kiểm tra Odoo 19 có tự hoàn allocation
  khi refuse đơn validate không — **xác nhận trong plan**; nếu không, hoàn thủ công như
  cơ chế Phase 2). Trạng thái trung gian "chờ duyệt rút" lưu bằng field bổ sung trên
  `hr.leave` (vd `x_withdraw_state`) hoặc field sẵn có phù hợp — **chốt trong plan**.
- **Endpoints:**
  - `POST /hocba-hrm/api/timeoff/request/<id>/withdraw` — chủ đơn gửi yêu cầu rút,
    body `{reason}` (lý do bắt buộc). Validate: là chủ đơn, đơn đang `validate`, còn
    ngày nghỉ trong tương lai. Sai phạm vi → `403`.
  - `POST /hocba-hrm/api/timeoff/request/<id>/withdraw/decide` — người duyệt
    `{approve: bool, note}`. Chỉ `scope.canApprove` đúng phòng. `approve=true` →
    hủy đơn + hoàn quỹ; `approve=false` → trả đơn về `validate`.
- **Audit:** `message_post` mốc gửi-rút / duyệt-rút / từ-chối-rút kèm người + lý do
  (nối tiếp lịch sử Phase 5).

### Test (BE)
- Chủ đơn rút đơn `validate` → trạng thái "chờ duyệt rút"; người ngoài phạm vi → `403`.
- Duyệt rút → đơn `cancel`, `virtual_remaining_leaves` **tăng lại** đúng `number_of_days`.
- Từ chối rút → đơn về `validate`, quỹ không đổi.
- Rút đơn có ngày đã qua hoàn toàn → `400`/`ValidationError`.

### Frontend
- Nút **"Rút đơn"** trên đơn đã duyệt của chính mình (tab *Của tôi* / `ApprovedPanel`),
  mở modal nhập lý do.
- Tab "Chờ duyệt" của người duyệt hiện thêm mục **"Yêu cầu rút"** (badge riêng) với nút
  Duyệt/Từ chối; tái dùng `Modal`, `states`, `Badge`.

### Acceptance
Nhân viên rút được đơn đã duyệt qua một vòng phê duyệt; khi được duyệt rút thì quỹ phép
hoàn lại đúng và có nhật ký; vai trò/phạm vi sai không thao tác được.

---

## PHASE 8 — SLA duyệt đơn (KPI đơn quá hạn)

**Vấn đề:** Đơn chờ duyệt "nằm chết" nhiều ngày không ai biết; thiếu chỉ số để HR/quản
lý theo dõi tốc độ xử lý.

### Backend
- **Khái niệm:** "tuổi đơn" = số ngày làm việc (hoặc ngày lịch — **chốt trong plan**)
  kể từ khi đơn vào trạng thái chờ duyệt (`confirm`/`validate1`) đến nay. Đơn `overdue`
  khi tuổi > `SLA_DAYS` (mặc định **3**, hằng số cạnh `LOW_BALANCE_DAYS`).
- **Mở rộng dashboard:** bổ sung vào endpoint dashboard hiện có (hoặc
  `GET /hocba-hrm/api/timeoff/sla?dept=`) các KPI **theo phạm vi `_scope()`**:
  `{pending, overdue, avgAgeDays, oldestAgeDays}` + danh sách đơn quá hạn
  `[{requestId, employee, department, leaveType, ageDays, submittedAt}]`.
  HR/Admin = mọi phòng; Trưởng phòng = phòng được giao; NV thường không thấy KPI duyệt.
- Không tạo cron/thông báo mới ở phase này (nhắc quá hạn có thể gắn vào kênh Phase 5 sau);
  chỉ tính **on-the-fly** khi gọi API.

### Test (BE)
- Đơn chờ duyệt tạo cách đây > `SLA_DAYS` → `overdue=true`; ≤ ngưỡng → không.
- KPI `pending`/`overdue` đếm đúng theo phạm vi; Trưởng phòng chỉ thấy phòng mình; NV
  thường gọi → `403` (hoặc rỗng theo quy ước dashboard).
- `avgAgeDays`/`oldestAgeDays` tính đúng trên tập đơn chờ.

### Frontend
- Dashboard officer: thẻ KPI **"Đơn quá hạn (> N ngày)"** + "Tuổi đơn cũ nhất";
  bảng "Đơn quá hạn" (tái dùng `SortBar`/`downloadXlsx`), dòng quá hạn tô amber/đỏ.
- Tab "Chờ duyệt": badge tuổi đơn (vd "4 ngày") cho đơn vượt SLA.

### Acceptance
HR/quản lý thấy ngay số đơn quá hạn và đơn chờ lâu nhất theo phạm vi; lọc/sắp xếp/xuất
được; không phát sinh quyền mới.

---

## Thứ tự đề xuất & phụ thuộc

| Phase | Tên | Phụ thuộc | Quy mô |
|---|---|---|---|
| 1 | Bảng Quỹ phép toàn NV | — | Vừa (BE phần lớn tái dùng) |
| 2 | Điều chỉnh quỹ + nhật ký | P1 (UI gắn vào bảng) | Vừa (model + 2 endpoint mới) |
| 3 | Cảnh báo phép tồn | P1 | Nhỏ (mở rộng /balances) |
| 4 | Coverage trùng lịch | — (độc lập) | Vừa |
| 5 | Thông báo & audit | — (độc lập) | Vừa–lớn (cần khảo sát kênh thông báo) |
| 6 | Nửa ngày + lễ | — (độc lập) | Nhỏ–vừa |
| 7 | Rút/hủy đơn đã duyệt | P5 (dùng chung nhật ký) | Vừa (luồng + hoàn quỹ) |
| 8 | SLA đơn quá hạn | — (độc lập) | Nhỏ (mở rộng dashboard) |

**Khuyến nghị code theo thứ tự 1 → 2 → 3** (một mạch "quỹ phép", dùng lại nhiều),
sau đó 4/6/8 (rẻ, độc lập), rồi 5 và 7 (7 dùng chung nhật ký/thông báo với 5, nên làm
sau hoặc cùng đợt 5).

## Câu hỏi cần nhóm/khách chốt trước khi implement
1. **Quyền chỉnh quỹ (P2):** chỉ HR Manager, hay Trưởng phòng cũng được chỉnh phòng mình?
2. **Allocation âm (P2):** Odoo 19 cho phép `hr.leave.allocation` số ngày âm không? (quyết định cách "trừ phép" — cần thử nghiệm).
3. **Ngưỡng cảnh báo (P3/P4):** `AT_RISK_DAYS=5`, `OVERLAP_WARN=3`, `LOW_BALANCE_DAYS=2` — chốt con số.
4. **Carry-over (P3):** phép năm tồn có chuyển sang năm sau / hết hạn ngày nào? Có chính sách trong `hb.timeoff.policy.rule` chưa?
5. **Kênh thông báo (P5):** ~~SPA có chuông chung chưa?~~ → **ĐÃ CHỐT & implement:** SPA chưa có → tự dựng **chuông riêng góc phải header**; nguồn dữ liệu là **model riêng `hb.leave.notification`** (KHÔNG dùng `mail.message` needaction vì Odoo 19 mặc định `notification_type='email'` → inbox rỗng). Audit/history dùng `message_post` chatter. Badge cập nhật bằng poll ~60s.
6. **Rút đơn đã trôi qua (P7):** đơn vắt ngang hôm nay (một phần ngày đã nghỉ) thì cho rút phần còn lại hay chặn hẳn? Khi duyệt rút, Odoo 19 có tự hoàn `number_of_days` về quỹ khi `action_refuse` đơn `validate` không (cần thử nghiệm)?
7. **Đơn vị tuổi đơn (P8):** đếm SLA theo **ngày lịch** hay **ngày làm việc**? `SLA_DAYS=3` — chốt con số.
