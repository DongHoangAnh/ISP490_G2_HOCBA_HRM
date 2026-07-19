# Tích hợp Nghỉ phép ↔ Chấm công (Task 1) — Thiết kế

**Ngày:** 2026-07-13
**Owner:** Nhật Anh (module `hocba_timeoff`)
**Trạng thái:** Spec chờ duyệt

---

## Mục tiêu

Nối `hocba_timeoff` với `hocba_attendance` để **Chấm công phản ánh đúng thực tế nghỉ phép**, đồng thời làm Chấm công nhận các "ngày công ty đi làm bù" (Thứ 7) mà HR đã khai bên Nghỉ phép. Sau Task 1, bảng chấm công là **nguồn sự thật duy nhất** về công của mỗi nhân viên/ngày — kể cả ngày nghỉ — để Payroll (đang đọc chấm công) tính lương đúng mà không cần nối trực tiếp với Nghỉ phép.

## Kiến trúc (nguyên tắc nền)

- **Toàn bộ code tích hợp đặt trong `hocba_timeoff`**, vì `hocba_timeoff` đã `depends` `hocba_attendance` (chiều ngược lại sẽ tạo phụ thuộc vòng). Cụ thể `hocba_timeoff` sẽ `_inherit`:
  - `hocba.attendance.policy` — mở rộng `is_workday()` để cộng thêm `hb.work.day`.
  - `hocba.attendance` — thêm field phân loại nguồn + chỉnh cách tính công cho bản ghi nghỉ.
  - `hr.leave` — hook vòng đời duyệt/từ chối/rút để sinh/gỡ bản ghi chấm công.
- **Gần như không sửa `hocba_attendance`** (module của DongHoangAnh): mọi model/logic đặt ở `hocba_timeoff` qua `_inherit`. **Ngoại lệ duy nhất** (theo quyết định Q2=b): thêm badge "Nghỉ phép" vào `views/hr_attendance_views.xml` của attendance — 1 file view, cần xin phép owner. Toàn bộ còn lại không chạm module người khác.
- **Một nguồn, lưu chung:** bản ghi ngày nghỉ nằm chung bảng `hocba.attendance`, phân biệt bằng field `source` (+ `leave_id`) và một **trạng thái chấm công riêng** (`status_code = on_leave_paid` / `on_leave_unpaid`) để nhìn vào DB/view biết ngay "ngày này NV nghỉ phép (có/không lương)" mà vẫn là một dòng chấm công.

## Tech stack

Odoo 19, Python. Không đụng SPA/React trong Task 1 (thuần backend + test). Test: `TransactionCase`, chạy qua Docker local `-u hocba_timeoff,hocba_employees --test-tags /hocba_timeoff`.

---

## Bối cảnh & hiện trạng (đã khảo sát code)

- `hocba.attendance.policy.is_workday(dt_local)` chỉ xét 7 cờ `workday_mon…workday_sun` — không biết `hb.work.day` (ngày làm bù). ([hocba_attendance_policy.py:86](../../custom-addons/hocba_attendance/models/hocba_attendance_policy.py#L86))
- `hocba.attendance._assert_check_allowed()` chỉ chặn: không phải ngày làm việc / đã check-in / chưa check-in. **Không** tra `hr.leave`. → NV đã duyệt nghỉ vẫn chấm công được. ([hr_attendance.py:334](../../custom-addons/hocba_attendance/models/hr_attendance.py#L334))
- `hocba.attendance` chỉ có **1 bản ghi/NV/ngày**; `work_credit = morning_credit + afternoon_credit` (0 / 0.5 / 1.0), đều `compute='_compute_work_metrics', store=True` suy từ giờ check-in/out. `check_in` là `required=True`. ([hr_attendance.py:130](../../custom-addons/hocba_attendance/models/hr_attendance.py#L130))
- `hr.leave` (đã duyệt = `state='validate'`): khoảng ngày ở `request_date_from`/`request_date_to` (fallback `date_from`/`date_to`); nửa ngày = `request_unit_half=True` + `request_date_from_period`/`request_date_to_period` ∈ `am`/`pm`. Loại nghỉ có/không lương ở `holiday_status_id.unpaid` (chỉ "Nghỉ Không Lương" `unpaid=True`). Helper `_half_day_label`, `_leave_day_bounds` đã có sẵn trong controller.
- Vòng đời đơn: duyệt qua `action_approve()` → `_action_validate()`; **rút đơn đã duyệt** (Phase 7) khi được chấp nhận sẽ gọi `leave.action_refuse()` (xem `hr_leave_withdraw.py`).
- Payroll đọc đúng 1 nguồn `hocba.attendance` qua whitelist `LOOKUP_SOURCES` ([payslip.py:39](../../custom-addons/hocba_payroll/models/payslip.py#L39)); `work_credit` là field payroll dùng để tính công.

---

## Phạm vi

**Trong phạm vi (Task 1):**
1. `is_workday()` cộng thêm `hb.work.day`.
2. Chặn check-in khi có đơn nghỉ **cả ngày** đã duyệt.
3. Tự sinh bản ghi `hocba.attendance` cho ngày nghỉ (cả ngày & nửa ngày), mang công + cờ có/không lương + note.
4. Đồng bộ ngược: đơn bị từ chối/rút → gỡ bản ghi chấm công đã sinh.
5. Test backend đầy đủ cho 1–4.

**Ngoài phạm vi (để Task 2 hoặc sau):**
- Lương **giáo viên** (tính theo giờ dạy `hb.work.entry`, không theo `work_credit`) — nghỉ ảnh hưởng lương GV xử lý riêng.
- Chỉnh rule lương Payroll (chỉ *kiểm* rule phân biệt đúng công; nếu cần sửa là phần đuôi nhỏ, không thuộc Task 1).
- Thay đổi UI/SPA.

---

## Thay đổi data model

Thêm vào `hocba.attendance` (khai báo từ `hocba_timeoff` qua `_inherit`):

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `source` | Selection `[('checkin','Chấm công'),('leave','Nghỉ phép')]`, default `'checkin'`, index | Phân biệt bản ghi công thật vs sinh từ đơn nghỉ. |
| `leave_id` | Many2one `hr.leave`, `ondelete='set null'`, index | Đơn nghỉ nguồn (chỉ set cho bản ghi liên quan nghỉ). |
| `leave_half` | Selection `[('am','Sáng'),('pm','Chiều')]` | Buổi được nghỉ (chỉ dùng cho nửa ngày). Rỗng = cả ngày / không liên quan. |
| `leave_is_paid` | Boolean | Snapshot loại nghỉ có lương tại thời điểm sinh (tránh lệ thuộc `holiday_status_id.unpaid` đổi về sau). |

**Trạng thái chấm công mới** (seed từ `hocba_timeoff/data/`, model `hocba.attendance.status`):

| xml_id | `code` | `name` | `color_code` |
|---|---|---|---|
| `status_on_leave_paid` | `on_leave_paid` | Nghỉ phép (có lương) | `#17a2b8` |
| `status_on_leave_unpaid` | `on_leave_unpaid` | Nghỉ không lương | `#6c757d` |

> Không thêm bảng mới. Không sửa `required=True` của `check_in` — bản ghi nghỉ cả ngày dùng **check-in quy ước** = `policy.morning_start` (chỉ để thoả ràng buộc + suy ra `date`; không mang nghĩa "NV đến lúc đó"). Dấu hiệu nhận biết ngày nghỉ = `source='leave'` + `status_code` mới + `leave_is_paid`.

---

## Hành vi chi tiết

### A. `is_workday()` nhận ngày làm bù

Override `hocba.attendance.policy.is_workday(dt_local)` trong `hocba_timeoff`:

```
kết quả = super().is_workday(dt_local)  OR  (tồn tại hb.work.day có date == dt_local.date())
```

- Tra `self.env['hb.work.day'].sudo().search_count([('date','=', dt_local.date())]) > 0`.
- Hệ quả: ngày HR đánh dấu làm bù (VD Thứ 7) → Chấm công mở cửa sổ check-in/out. Cửa sổ giờ (`morning_start`…`evening_end`) giữ nguyên.

### B. Chặn check-in khi nghỉ CẢ NGÀY đã duyệt

Override `hocba.attendance._assert_check_allowed(employee, kind)` (super() trước, rồi bổ sung):

- Nếu tồn tại `hr.leave` với `employee_id == employee`, `state == 'validate'`, khoảng ngày phủ `today`, và **là nghỉ cả ngày** (không `request_unit_half`, hoặc nửa-ngày kéo dài nhiều ngày) → `raise UserError('on_approved_leave')`.
- Áp cho **cả hai** nhánh check chính thức (`_assert_check_allowed`) và ca CTV/OT (`_assert_shift_check_allowed`) — dùng chung 1 helper `_approved_full_day_leave(employee, day)`.

### C. Nghỉ NỬA NGÀY đã duyệt → cho chấm công + note + công đúng

- **Không chặn.** NV chấm công buổi còn lại như thường (bản ghi thật, `source='checkin'`, `leave_id` set, `leave_half=am|pm`).
- **Ghi note** vào `notes`: `"Nghỉ phép nửa buổi sáng"` / `"…nửa buổi chiều"`.
- **Miễn phạt & bù công đúng buổi nghỉ** (mức hoàn chỉnh) — chỉnh `_compute_work_metrics` (override, super() rồi hiệu chỉnh khi `leave_id` set và `leave_half`):
  - Nghỉ **sáng** (`am`): không tính `late_minutes`; coi buổi sáng như "đã có" — nếu nghỉ **có lương** thì `morning_credit = 0.5` (bù), nếu **không lương** thì `morning_credit = 0`.
  - Nghỉ **chiều** (`pm`): không tính `early_leave_minutes`/`missing_minutes` cho buổi chiều; `afternoon_credit = 0.5` nếu **có lương**, `0` nếu **không lương**.
  - `work_credit = morning_credit + afternoon_credit` (giữ công thức gốc, chỉ điều chỉnh từng nửa).

### D. Tự sinh bản ghi cho nghỉ CẢ NGÀY + đồng bộ ngược

**Sinh khi duyệt** — hook `_action_validate()` (override, gọi `super()` trước) trên `hr.leave`:

Cho mỗi **ngày làm việc** trong khoảng đơn (dùng logic ngày làm việc: T2–T6 + `hb.work.day`, trừ lễ — tái dùng khái niệm `_count_working_days`), nếu đơn là **nghỉ cả ngày**:
- Nếu **đã có** bản ghi `source='checkin'` (NV lỡ chấm công thật ngày đó) → **không** ghi đè; ghi `notes` cảnh báo xung đột + để nguyên cho HR xử lý (xem Edge case).
- Ngược lại `create` bản ghi `hocba.attendance`:
  - `source='leave'`, `leave_id=leave.id`, `leave_is_paid = not holiday_status_id.unpaid`.
  - `check_in` = quy ước: `<ngày> + policy.morning_start`; **không** set `check_out`.
  - `work_credit`: **1.0** nếu có lương, **0.0** nếu không lương — ép trong `_compute_work_metrics` khi `source='leave'` (bỏ qua giờ quy ước, không tính late/early/missing).
  - `status_id`: ép về `on_leave_paid` / `on_leave_unpaid` (override `_compute_status` cho `source='leave'`) — đây là dấu hiệu "nhìn phát biết ngay" ở DB/view.
  - `notes`: tên loại nghỉ (VD "Nghỉ phép năm" / "Nghỉ không lương").

> Nửa ngày **không** sinh bản ghi ở D (bản ghi đến từ lần NV chấm công thật ở C). Nếu NV nghỉ nửa ngày mà **không** đến chấm công → không có bản ghi (đúng: buổi làm việc đó thực sự vắng); phần công buổi nghỉ có/không lương chấp nhận bỏ ngỏ ở Task 1, xử lý ở Task 2 nếu cần.

**Gỡ khi từ chối/rút** — hook `action_refuse()` (override, gọi `super()`) trên `hr.leave`:
- `unlink` mọi `hocba.attendance` có `source='leave'` và `leave_id == self.id`.
- Với bản ghi nửa ngày (`source='checkin'`, `leave_id` set): **không xoá** (là công thật) — chỉ gỡ liên kết: set `leave_id=False`, `leave_half=False`, xoá note nghỉ, để `_compute_work_metrics` tự tính lại thuần theo giờ.

---

## Ánh xạ công có/không lương (tóm tắt)

| Trường hợp (đơn đã duyệt) | Bản ghi | `work_credit` | Nguồn |
|---|---|---|---|
| Cả ngày, có lương | Tự sinh (D) | 1.0 | `leave` |
| Cả ngày, không lương | Tự sinh (D) | 0.0 | `leave` |
| Nửa ngày có lương, NV chấm buổi còn lại | NV tạo (C) | 1.0 (0.5 làm + 0.5 bù) | `checkin` |
| Nửa ngày không lương, NV chấm buổi còn lại | NV tạo (C) | 0.5 | `checkin` |
| Nửa ngày, NV **không** chấm | (không có) | — | — |
| Không có đơn | NV tạo | theo giờ | `checkin` |

Payroll đọc `SUM(work_credit)` như hiện tại → ra công đúng cho mọi trường hợp trên (trừ dòng "nửa ngày không chấm").

---

## Xử lý lỗi & thông báo

- Thêm mã `'on_approved_leave'` vào bảng map lỗi controller `_CHECK_ERR_STATUS` ([main.py:1619](../../custom-addons/hocba_hrm/controllers/main.py#L1619)) → HTTP **403**, message tiếng Việt: *"Bạn đang trong kỳ nghỉ phép đã được duyệt — không thể chấm công ngày này."*
- Các mã lỗi cũ giữ nguyên.

## Hiển thị (view — quyết định Q2=b)

- Thêm badge màu theo `status_id.color_code` cho dòng `status_code ∈ {on_leave_paid, on_leave_unpaid}` trong `hocba_attendance/views/hr_attendance_views.xml`.
- **Đây là file duy nhất thuộc `hocba_attendance`** bị chạm → cần xin phép DongHoangAnh trước khi sửa; nếu chưa được thì tách bước view ra khỏi luồng và làm sau (dữ liệu + status vẫn đúng, chỉ chưa có badge).

---

## Edge cases (bắt buộc có test hoặc quyết định)

1. **NV đã chấm công thật rồi đơn cả-ngày mới được duyệt (retroactive):** D không ghi đè bản ghi `checkin`; ghi note cảnh báo *"Có đơn nghỉ cả ngày đã duyệt trùng ngày đã chấm công — cần HR rà soát."* → HR quyết thủ công. Không tự xoá công thật.
2. **Đơn nhiều ngày:** sinh 1 bản ghi cho **mỗi** ngày làm việc trong khoảng; bỏ qua T7/CN thường, ngày lễ; **giữ** ngày `hb.work.day`.
3. **Rút đơn (Phase 7):** `action_refuse` do luồng rút gọi → gỡ bản ghi như mục D. Test riêng luồng rút vì đây là điểm dễ để lệch lương.
4. **Nửa ngày kéo dài nhiều ngày** (`request_date_from_period != request_date_to_period`): coi như **cả ngày** cho từng ngày ở giữa (theo `_half_day_label` trả '' khi sáng→chiều).
5. **Loại nghỉ đổi `unpaid` sau khi đã sinh bản ghi:** dùng snapshot `leave_is_paid` — không tính lại theo loại nghỉ hiện tại.
6. **NV thường không có ACL** trên `hr.leave`/`hocba.attendance`: mọi truy vấn/tạo/xoá trong hook + `_assert_check_allowed` dùng `.sudo()` sau khi đã ghim `employee`.

---

## Ảnh hưởng tới Payroll (Task 2 thu nhỏ)

- Payroll **không cần** nối trực tiếp `hr.leave`. Chuỗi trở thành **Nghỉ phép → Chấm công → Lương** một nguồn.
- Việc còn lại (nếu có) chỉ là **kiểm** rule lương đang cộng `work_credit` đúng cho công có lương và không cộng cho công 0 — không còn là một "Task 2" độc lập lớn. Ghi nhận là phần rà soát nhỏ sau Task 1.

---

## Chiến lược test (TDD)

Tất cả trong `custom-addons/hocba_timeoff/tests/` (tag `/hocba_timeoff`), theo quy ước sẵn có (CCCD 12 số cho NV official — BR-010, dùng `.sudo()`):

- `test_is_workday_extra`: `hb.work.day` bật → `policy.is_workday` True cho ngày T7 đó; ngày T7 khác vẫn False.
- `test_block_full_day_leave`: đơn cả ngày `validate` phủ hôm nay → `_assert_check_allowed('in')` raise `on_approved_leave`; không đơn → không raise.
- `test_generate_full_day_paid`: duyệt đơn cả ngày có lương → sinh bản ghi `source='leave'`, `work_credit==1.0`, đúng số bản ghi = số ngày làm việc.
- `test_generate_full_day_unpaid`: tương tự nhưng `work_credit==0.0`.
- `test_half_day_paid_note_credit`: nửa ngày sáng có lương + chấm công buổi chiều → `notes` chứa "nửa buổi sáng", `work_credit==1.0`, `late_minutes==0`.
- `test_half_day_unpaid_credit`: nửa ngày không lương → `work_credit==0.5`.
- `test_refuse_removes_generated`: duyệt rồi `action_refuse` → bản ghi `source='leave'` bị xoá; bản ghi `checkin` (nếu có) giữ nguyên, `leave_id` gỡ.
- `test_withdraw_removes_generated`: luồng rút Phase 7 → như trên.
- `test_retroactive_conflict`: đã có `checkin` rồi duyệt đơn cả ngày → không ghi đè, có note cảnh báo.
- `test_multiday_skips_weekend`: đơn phủ T6→T2 → chỉ sinh cho T6 + T2 (bỏ T7/CN), trừ khi có `hb.work.day`.
- `test_leave_status_code`: bản ghi sinh từ nghỉ có lương → `status_code == 'on_leave_paid'`; không lương → `'on_leave_unpaid'`; `check_in` == ngày đó lúc `morning_start`.

---

## Quyết định đã chốt (từ trao đổi)

1. Nghỉ nửa ngày: **mức hoàn chỉnh** (miễn phạt + bù công đúng buổi).
2. Nghỉ cả ngày: **chặn hẳn** check-in (phương án A) + tự sinh bản ghi.
3. Nửa ngày: **cho chấm công** + note "nghỉ phép nửa buổi sáng/chiều".
4. Lưu **chung** `hocba.attendance` + field `source`/`leave_id` để lọc.
5. Toàn bộ code trong `hocba_timeoff`; ngoại lệ duy nhất chạm `hocba_attendance` là badge trong `hr_attendance_views.xml` (Q2=b).
6. **(Q1)** Bản ghi nghỉ cả ngày: `check_in = morning_start` (giá trị quy ước) + đánh dấu bằng `status_code` mới (`on_leave_paid`/`on_leave_unpaid`) và `source='leave'` — vẫn ghi nhận như một dòng chấm công nhưng biết rõ hôm đó nghỉ phép có/không lương.
7. **(Q2=b)** Thêm badge "Nghỉ phép" vào view chấm công → cần xin phép DongHoangAnh (file `hr_attendance_views.xml`).

## Điểm cần phối hợp trước khi implement

- **Xin phép DongHoangAnh** sửa 1 file `hocba_attendance/views/hr_attendance_views.xml` (badge). Nếu chưa được → tách bước view làm sau, phần backend không phụ thuộc.
- Thống nhất *hành vi* chặn check-in với owner Chấm công (dù không sửa code của họ, hành vi thay đổi).
