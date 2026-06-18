# Thiết kế — Gói 1: Tính công + phút trễ/về sớm/thiếu (Chấm công Học Bá)

**Ngày:** 17/06/2026 · **Trạng thái:** chờ duyệt
**Phạm vi:** `hocba_attendance` (model `hocba.attendance`, `hocba.attendance.policy`), controller `hocba_hrm/controllers/main.py` (API chấm công), frontend `frontend/src/features/attendance/`.
**Quy ước nền:** [docs/QUY_UOC_FRONTEND.md](../../QUY_UOC_FRONTEND.md) · **Spec trước:** [2026-06-13-attendance-spa-screen-design.md](2026-06-13-attendance-spa-screen-design.md).

---

## 0. Bối cảnh & vị trí trong lộ trình

Yêu cầu tổng (nâng cấp chấm công) được chia thành **4 gói phụ thuộc**, làm tuần tự:

1. **Gói 1 (spec này):** Tính công (công sáng/chiều, lương theo ngày) + phút trễ / về sớm / phút thiếu + tổng hợp công tháng (trừ công thiếu) + chuẩn hóa mốc trễ trong policy. Đây là nền tảng các gói sau dùng lại.
2. **Gói 2:** Khóa nút check-in/out (1 lần/ngày, ngày làm việc) + tách UI tài khoản manager (chỉ quản lý) ↔ user (tự chấm công).
3. **Gói 3:** Luồng "đơn" — user đính đơn vào 1 bản ghi → manager duyệt & sửa thông tin bản ghi.
4. **Gói 4:** Đăng ký ca CTV/OT — lịch tuần tự đăng ký, manager thêm/duyệt ca, check-in theo cửa sổ ±15' quanh giờ ca.

Spec này **chỉ** đặc tả Gói 1.

### Mô hình vai trò (đã có sẵn trong code — không đổi ở Gói 1)

- **Master-manager** = `hr.group_hr_manager` (quản lý toàn bộ).
- **Manager** = trưởng phòng (`hr.department.manager_id`), phạm vi suy ra qua `_managed_department_ids` / `_emp_scope_domain`.
- **User** = nhân viên thường; **CTV** = `x_employment_status == 'ctv'`.

### Nguồn dữ liệu đã có (không viết lại logic face/geo)

- `hocba.attendance` — 1 bản ghi / nhân viên / ngày. Fields: `employee_id`, `check_in`, `check_out`, `date` (compute-store local tz), `working_hours` (= `check_out − check_in`, giờ), `status_code` (`on_time`/`late`), cờ face/geo, `needs_review`.
- `hocba.attendance.policy` — `get_policy()` trả policy active; có window/workdays/geofence/face.
- Controller `hocba_hrm` đã có `_att_row`, `_att_me_info`, `_att_day_table`, `_att_me_history`, `_late_minutes` và 6 route `/hocba-hrm/api/attendance/*`.
- Frontend đã build: `frontend/src/features/attendance/{Attendance,CheckInPanel,MyHistory,AttendanceTable,AttendanceDrawer,useFaceApi,util,mock}.{jsx,js}` + `frontend/src/api/attendance.js`.

---

## 1. Quy tắc nghiệp vụ (đã chốt)

Tất cả tính theo **giờ local** (BE quy đổi từ UTC qua `fields.Datetime.context_timestamp`).

- **Giờ làm** = `check_out − check_in` (8h **tổng**, KHÔNG trừ nghỉ trưa).
- **Mốc ra mong đợi** = `check_in + std_work_hours` (mặc định 8h).
- **Đi trễ:** phút sau **09:30** cố định (`late_cutoff`). `late_minutes = max(0, (giờ_checkin − 09:30)·60)`.
- **Công sáng (½):** mất nếu check-in **sau 10:00** cố định (`morning_credit_cutoff`); ngược lại = 0.5.
- **Về sớm:** phút trước mốc ra. `early_leave_minutes = max(0, (expected_check_out − check_out)·60)`.
- **Công chiều (½):** mất nếu check-out **trước** `check_in + (std_work_hours − afternoon_margin_hours)` (mặc định `check_in + 6h`) **hoặc** chưa check-out; ngược lại = 0.5.
- **Công ngày** = công sáng + công chiều → **0 / 0.5 / 1.0**.
- **Phút thiếu** = `max(0, (std_work_hours − giờ làm)·60)`; chỉ tính khi có **cả** check-in & check-out, ngược lại = 0.
- **Lương theo ngày, không theo giờ:** đơn vị là "công"; Gói 1 chỉ tính & hiển thị công, KHÔNG đụng payroll.

### Tổng hợp công tháng

- `totalCredit` = Σ `work_credit` các ngày trong tháng.
- **Ngày vi phạm** = ngày có `missing_minutes > 0`, sắp xếp theo `date` tăng dần.
- Bỏ qua **2 ngày vi phạm đầu tiên** (`violation_free_days`).
- `deficitCredit` (công thiếu) = (Σ `missing_minutes` của các ngày vi phạm **còn lại** ÷ 60) ÷ `std_work_hours`.
- `netCredit` (công thực) = `totalCredit − deficitCredit`.

---

## 2. Thay đổi model

### 2.1 `hocba.attendance.policy` — thêm field cấu hình

Giữ nguyên toàn bộ field window/geofence/face hiện có. Thêm:

| Field | Kiểu | Default | Ý nghĩa |
|---|---|---|---|
| `late_cutoff` | Float | 9.5 | Sau giờ này → tính đi trễ (giờ local float, 9.5 = 09:30) |
| `morning_credit_cutoff` | Float | 10.0 | Check-in sau giờ này → mất công sáng |
| `std_work_hours` | Float | 8.0 | Số giờ chuẩn/ngày; mốc ra = check_in + giá trị này |
| `afternoon_margin_hours` | Float | 2.0 | Check-out sớm hơn (std − margin) so mốc vào → mất công chiều |
| `violation_free_days` | Integer | 2 | Số ngày vi phạm đầu tháng miễn khỏi công thiếu |

### 2.2 `hocba.attendance` — thêm field tính công

Tất cả `compute` + `store=True`, `@api.depends('check_in', 'check_out')`, đọc policy qua `get_policy()` trong compute. Tính theo giờ local.

| Field | Kiểu | Công thức |
|---|---|---|
| `expected_check_out` | Datetime | `check_in + std_work_hours` (None nếu chưa check-in) |
| `late_minutes` | Integer | `max(0, (giờ_checkin_local − late_cutoff)·60)` |
| `early_leave_minutes` | Integer | `max(0, (expected_check_out − check_out) phút)`; 0 nếu chưa check-out |
| `missing_minutes` | Integer | `max(0, (std_work_hours·60 − (check_out−check_in) phút))`; 0 nếu thiếu check_in/out |
| `morning_credit` | Float | 0.5 nếu check-in ≤ `morning_credit_cutoff`, ngược lại 0.0 (0.0 nếu chưa check-in) |
| `afternoon_credit` | Float | 0.5 nếu đã check-out & check-out ≥ `check_in + (std − margin)`, ngược lại 0.0 |
| `work_credit` | Float | `morning_credit + afternoon_credit` (0 / 0.5 / 1.0) |

**Lưu ý staleness:** field store đọc policy lúc compute; đổi policy KHÔNG tự tính lại bản ghi cũ. Gói 1 chấp nhận điều này (bản ghi mới luôn đúng); nút "tính lại tháng" để gói sau.

Sửa `_compute_status`: thay `cutoff = policy.morning_start` bằng `cutoff = policy.late_cutoff` (đang dùng 8.0 — sai so với mốc 9:30 đã chốt).

---

## 3. API contract (controller `hocba_hrm/controllers/main.py`)

Wire format `camelCase`. Không thêm/đổi route ở Gói 1 — chỉ mở rộng payload.

### 3.1 `_att_row(rec, policy)` — thêm field

```jsonc
{
  // ...field cũ giữ nguyên (id, empId, name, checkIn, checkOut, workingHours,
  //    statusKey, lateMinutes, faceSuspect, ... , needsReview, mapUrl)...
  "workCredit": 1.0,          // 0 | 0.5 | 1.0
  "morningCredit": 0.5,
  "afternoonCredit": 0.5,
  "earlyLeaveMinutes": 0,
  "missingMinutes": 0,
  "expectedCheckOut": "2026-06-17T17:00:00"  // null nếu chưa check-in
}
```

`_late_minutes(rec, policy)` đổi mốc từ `policy.morning_start` → `policy.late_cutoff`.

### 3.2 `_att_me_history(env, month)` — mở rộng `summary`

Giữ field cũ, thêm:

```jsonc
"summary": {
  "onTime": 12, "late": 3, "needsReview": 1,
  "daysPresent": 15, "totalHours": 120.5,   // (cũ)
  "totalCredit": 14.5,        // Σ work_credit
  "deficitCredit": 0.5,       // công thiếu (đã bỏ 2 ngày vi phạm đầu)
  "netCredit": 14.0,          // totalCredit − deficitCredit
  "violationDays": 4          // số ngày missing_minutes > 0
}
```

Logic công thiếu (Python, trong controller — vì chéo nhiều bản ghi):
1. Lấy các row có `missingMinutes > 0`, sort theo `date` tăng dần.
2. Bỏ `policy.violation_free_days` row đầu.
3. `deficitCredit = (sum(missingMinutes của phần còn lại) / 60) / policy.std_work_hours`, làm tròn 2 chữ số.
4. `netCredit = round(totalCredit − deficitCredit, 2)`.

### 3.3 `_att_day_table(env, date_str)`

Rows tự có field mới qua `_att_row`. Thêm (tùy chọn) `counts.totalCredit` = Σ `workCredit` trong bảng ngày để manager thấy tổng công ngày.

---

## 4. Frontend (`frontend/src/features/attendance/`)

Giữ design system Học Bá. Mọi fetch giữ 3 trạng thái loading/error/data (đã có).

### 4.1 `util.js`
Thêm `fmtCredit(v)`: `1.0 → '1 công'`, `0.5 → '½ công'`, `0/null → '—'`.

### 4.2 `MyHistory.jsx`
- **Thẻ tổng hợp:** thêm **Tổng công** (`summary.totalCredit`), **Công thiếu** (`summary.deficitCredit`, màu amber/đỏ nếu > 0), **Công thực** (`summary.netCredit`, đậm). Sắp lại `stat-grid` cho gọn (gom ~6 thẻ, có thể bỏ "Cần xem lại" xuống hàng phụ nếu chật — quyết định ở plan).
- **Bảng:** thêm cột **Ngày công** (`fmtCredit(r.workCredit)`), **Về sớm** (`r.earlyLeaveMinutes`, hiển thị `-n'` nếu > 0), **Thiếu** (`r.missingMinutes`, `n'` nếu > 0). Giữ cột Đi trễ.

### 4.3 `AttendanceDrawer.jsx`
Thêm vào lưới chi tiết: **Ngày công** (`fmtCredit`), **Về sớm** (`earlyLeaveMinutes`), **Phút thiếu** (`missingMinutes`), **Giờ ra mong đợi** (`fmtTime(expectedCheckOut)`).

### 4.4 `AttendanceTable.jsx` (bảng theo ngày — manager)
Thêm cột **Ngày công** + **Thiếu**. (Cột khác giữ nguyên.)

### 4.5 `api/attendance.js`
Không đổi — chỉ đọc thêm field từ response.

---

## 5. Kiểm thử

### Backend (Odoo test — theo memory `running-odoo-tests`)
File mới `custom-addons/hocba_attendance/tests/test_work_credit.py`:

- check-in 09:00 / out 17:00 → `work_credit=1.0`, `late_minutes=0`, `missing_minutes=0`, `early_leave_minutes=0`.
- check-in 09:45 → `late_minutes=15`, vẫn `morning_credit=0.5` (trước 10:00).
- check-in 10:30 → `morning_credit=0.0` (mất công sáng), `late_minutes` đúng.
- check-out trước `check_in + 6h` → `afternoon_credit=0.0`.
- làm < 8h → `missing_minutes` đúng; làm ≥ 8h → `missing_minutes=0`.
- chưa check-out → `missing_minutes=0`, `early_leave_minutes=0`, không là ngày vi phạm.
- `_att_me_history`: 5 ngày thiếu → bỏ 2 ngày đầu → `deficitCredit`/`netCredit` đúng; ≤ 2 ngày thiếu → `deficitCredit=0`.
- `status_code`: check-in 09:20 → `on_time`; 09:40 → `late` (mốc 9:30 mới).

### Frontend (thủ công — Definition of Done §9)
3 trạng thái loading/error/data; thẻ & cột mới hiển thị đúng (user test thường); không lỗi đỏ console.

---

## 6. Phạm vi

**Có làm:** 5 field policy mới; 7 field tính công trên `hocba.attendance`; sửa mốc trễ → `late_cutoff` (9:30); mở rộng `_att_row` + tổng hợp tháng (`totalCredit`/`deficitCredit`/`netCredit`) + `counts.totalCredit`; cập nhật `MyHistory`/`AttendanceDrawer`/`AttendanceTable`/`util`; test backend `test_work_credit.py`.

**KHÔNG làm (gói sau):**
- Khóa nút check-in/out theo ngày & tách UI manager/user → **Gói 2**.
- Luồng đơn (user đính đơn → manager duyệt/sửa) → **Gói 3**.
- Đăng ký ca CTV/OT + lịch tuần + cửa sổ check-in ±15' → **Gói 4**.
- Nút "tính lại tháng" khi đổi policy (chấp nhận staleness ở Gói 1).
- Đổi lương/payroll, đổi logic face/geo/window của model.
