# SPEC — Dashboard tổng quan nhân sự (theo mẫu Lark Base)

**Người yêu cầu:** Việt · **Ngày:** 2026-07-10 · **Trạng thái:** implement ngay theo ảnh mẫu người dùng cung cấp (dashboard Lark "HRM_Hồ sơ nhân sự_Công lương Học Bá", tab 6.1 Tổng quan tình hình).

## Mục tiêu

Thay trang Dashboard demo hiện tại (`frontend/src/features/dashboard/Dashboard.jsx`)
bằng dashboard giống bảng Lark, dữ liệu THẬT từ Odoo:

1. **5 thẻ KPI**: Số nhân sự tính đến hiện tại · Onboard · Offboard · Độ tuổi trung bình · Thâm niên trung bình.
2. **Line chart** — Biến động nhân sự chính thức theo từng thời gian (số NV lên chính thức theo tháng, từ `x_official_date`).
3. **Bar chart** — Số nhân sự theo độ tuổi (histogram từng tuổi, từ `birthday`).
4. **Bar chart ngang** — Số nhân sự theo thâm niên (số năm tròn từ ngày vào làm).

> **Bỏ biểu đồ giới tính** (có trong ảnh Lark): Odoo 19 đã bỏ field `gender`
> chuẩn; người yêu cầu quyết định (2026-07-10) KHÔNG thêm field riêng —
> dashboard không có donut giới tính.

Giữ lại widget "Chứng chỉ cần gia hạn" (F-009) ở cuối trang (chỉ HR thấy).
Bỏ các khối demo: "Phân bổ theo phòng ban", "Mới vào gần đây", "Phân hệ khác".

## Định nghĩa số liệu

- **Nguồn NV**: `hr.employee` với `active_test=False` (NV nghỉ việc bị archive vẫn tính),
  lọc theo phạm vi vai trò `_emp_scope_domain` (HR/Admin = tất cả; Trưởng phòng = phòng mình;
  Giáo vụ = giáo viên; user thường = mình).
- **Số nhân sự tính đến hiện tại** = tổng mọi hồ sơ trong phạm vi (kể cả đã nghỉ).
- **Onboard** = đang làm việc (`active=True` và `x_employment_status != 'resigned'`).
- **Offboard** = đã nghỉ (`x_employment_status = 'resigned'`).
- **Độ tuổi trung bình** = trung bình tuổi (năm tròn) của NV đang làm có `birthday`.
- **Thâm niên trung bình** = trung bình số năm tròn từ ngày vào làm
  (`x_probation_start`, fallback `create_date`) của NV đang làm.
- Biểu đồ tuổi/thâm niên: chỉ NV đang làm; tháng chính thức tính trên mọi hồ sơ có `x_official_date`.

## API

`GET /hocba-hrm/api/dashboard/stats` (auth='user') →

```json
{
  "kpi": {"total": 183, "onboard": 85, "offboard": 97, "avgAge": 26, "avgSeniority": 0},
  "officialByMonth": [{"label": "1/2025", "count": 4}],
  "byAge": [{"age": 23, "count": 33}],
  "bySeniority": [{"years": 0, "count": 44}]
}
```

Helper module-level `_dashboard_stats(env)` trong `hocba_hrm/controllers/main.py`
(test trực tiếp bằng `TransactionCase` như `_employee_search`).

## UI

- recharts (đã có sẵn): `LineChart`, `BarChart` (dọc + `layout="vertical"`).
- Hàng KPI 5 cột (style `.stat` hiện có); card biểu đồ dùng `.card`/`.card-head`.
- Màu: xanh dương `#3370ff` (giống Lark) cho cột/đường.

## Mở rộng 2026-07-11 — Dashboard theo TAB (gợi ý của Việt)

5 tab, hiển thị theo quyền (cờ `tabs` trả trong `/api/dashboard/stats`):

| Tab | Ai thấy | Nội dung |
|---|---|---|
| Tổng quan | mọi user (theo scope) | KPI cũ + **Tỷ lệ nghỉ việc theo tháng** (line %, tử = đơn offboarding `done` có `actual_leave_date` trong tháng, mẫu = headcount cuối tháng ≈ đã vào − đã nghỉ lũy kế) + **Phân bổ phòng ban** (bar ngang, NV đang làm) + 3 biểu đồ cũ |
| Tuyển dụng | HR/Admin | **Phễu**: Nộp CV → Pass lọc CV (`cv_filter_result=pass`) → Tham gia PV (`attendance_status=present`) → Pass PV (`interview_result=pass`) → Nhận việc (stage `hired_stage`); **Time-to-hire** = TB(start_date − date_received) của UV đã tuyển; **Nguồn CV** (donut, `source_id`, fallback CTV/Khác); **Vị trí đang mở theo phòng ban** (phiếu `hb.recruitment.request` state `recruiting`, đếm + tổng `qty_expected`) |
| Chấm công | HR + trưởng phòng/giáo vụ (scope NV) | **% đi muộn / % về sớm theo tháng** (12 tháng, từ `hocba.attendance.late_minutes/early_leave_minutes>0` trên tổng bản ghi); **Top đi muộn** (3 tháng gần nhất, top 7 NV theo số lần); **Giờ OT theo tháng** (stacked theo `ot_level` 100/150/300, `hocba.work_shift` approved) |
| Nghỉ phép | như Chấm công | **Pie lý do nghỉ** (`hr.leave` validate 12 tháng, theo loại); **Xu hướng ngày nghỉ theo tháng** (area); KPI **Quỹ phép tồn** = Σ allocation validate − Σ ngày nghỉ validate |
| Lương | HR Manager | **Quỹ lương theo tháng** (line net+gross, `hb.payslip` ≠ cancel, 12 tháng); **Chi phí theo phòng ban** (bar ngang, kỳ lương gần nhất); **Lương TB theo phân cấp** (wage hợp đồng NV đang làm, nhóm `x_seniority_level`) |

Điều chỉnh so với gợi ý gốc: (1) bỏ chiều **giới tính** trong "Cơ cấu tuổi & giới tính"
(đã quyết không dùng field giới tính) — giữ histogram tuổi; (2) "Phân bổ phòng ban"
dùng bar ngang thay pie (nhiều phòng, pie khó đọc); (3) treemap chi phí → bar ngang
(recharts treemap đọc kém với ít phòng ban).

Màu (đã chạy validator dataviz, nền trắng, ΔE CVD 24.2 PASS):
- Series đơn/brand: `#3370ff`; ramp thứ tự (phễu, OT stacked): `#86b6ef → #5598e7 → #3987e5 → #256abf → #184f95`.
- Categorical (pie/donut, thứ tự cố định): `#3370ff, #1baf7a, #eda100, #008300, #4a3aa7, #e34948, #e87ba4, #eb6834` — 3 slot dưới 3:1 → luôn kèm nhãn trực tiếp trên lát.

API mới (đều `auth='user'`, trả 403 khi thiếu quyền):
`/api/dashboard/recruitment` · `/api/dashboard/attendance` · `/api/dashboard/timeoff` · `/api/dashboard/payroll`.

## Test

`custom-addons/hocba_hrm/tests/test_dashboard_stats.py`:
- HR manager thấy đủ KPI, đếm đúng onboard/offboard (tạo 1 NV đang làm + 1 NV resigned+archived).
- Tuổi/thâm niên trung bình tính đúng với birthday/ngày vào cho trước.
- User thường: scope rỗng → số 0, không lỗi.
- NV thiếu birthday/ngày vào không làm vỡ số liệu (bị loại khỏi trung bình).
