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

**Vấn đề:** Đơn "nằm chết" không ai biết; khi tranh chấp không có vết.

### Backend
- **Thông báo in-app:** khi tạo đơn → báo người duyệt (trưởng phòng/HR); khi duyệt/từ chối → báo chủ đơn. Tái dùng `mail.thread`/`message_post` của `hr.leave` (đã là mail thread) hoặc model thông báo của `hocba_hrm` nếu SPA đã có chuông thông báo (**kiểm tra trước trong plan**).
- **Audit:** ghi `message_post` mốc tạo/duyệt/từ chối kèm người + ghi chú; expose `GET /request/<id>/history`.

### Test (BE)
- Tạo đơn sinh thông báo cho đúng người duyệt phạm vi; quyết định sinh thông báo cho chủ đơn; history trả đúng trình tự.

### Frontend
- Badge số đơn chờ trên tab "Chờ duyệt"; mục "Lịch sử xử lý" trong modal chi tiết (`ApprovedPanel`/`ApprovalPanel`).

### Acceptance
Người duyệt biết có đơn mới; nhân viên biết kết quả; mỗi đơn có dòng thời gian thao tác.

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

## Thứ tự đề xuất & phụ thuộc

| Phase | Tên | Phụ thuộc | Quy mô |
|---|---|---|---|
| 1 | Bảng Quỹ phép toàn NV | — | Vừa (BE phần lớn tái dùng) |
| 2 | Điều chỉnh quỹ + nhật ký | P1 (UI gắn vào bảng) | Vừa (model + 2 endpoint mới) |
| 3 | Cảnh báo phép tồn | P1 | Nhỏ (mở rộng /balances) |
| 4 | Coverage trùng lịch | — (độc lập) | Vừa |
| 5 | Thông báo & audit | — (độc lập) | Vừa–lớn (cần khảo sát kênh thông báo) |
| 6 | Nửa ngày + lễ | — (độc lập) | Nhỏ–vừa |

**Khuyến nghị code theo thứ tự 1 → 2 → 3** (một mạch "quỹ phép", dùng lại nhiều),
sau đó 4/6 (rẻ, độc lập), để 5 sau cùng (cần thống nhất hạ tầng thông báo với nhóm).

## Câu hỏi cần nhóm/khách chốt trước khi implement
1. **Quyền chỉnh quỹ (P2):** chỉ HR Manager, hay Trưởng phòng cũng được chỉnh phòng mình?
2. **Allocation âm (P2):** Odoo 19 cho phép `hr.leave.allocation` số ngày âm không? (quyết định cách "trừ phép" — cần thử nghiệm).
3. **Ngưỡng cảnh báo (P3/P4):** `AT_RISK_DAYS=5`, `OVERLAP_WARN=3`, `LOW_BALANCE_DAYS=2` — chốt con số.
4. **Carry-over (P3):** phép năm tồn có chuyển sang năm sau / hết hạn ngày nào? Có chính sách trong `hb.timeoff.policy.rule` chưa?
5. **Kênh thông báo (P5):** SPA `hocba_hrm` đã có hệ thống chuông/notification chung chưa, hay dùng `mail.thread` của `hr.leave`?
