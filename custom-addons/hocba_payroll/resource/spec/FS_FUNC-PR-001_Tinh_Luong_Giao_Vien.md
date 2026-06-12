# **FS — FUNC-PR-001**
# **Tính Lương Giáo Viên Theo Giờ Dạy (TEACH_HOURS)**

---

## **COVER (Trang bìa)**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-001 |
| **Function Name** | Tính Lương Giáo Viên Theo Giờ Dạy (TEACH_HOURS) |
| **Custom Module** | `hb_payroll_teaching_hours` |
| **GAP Reference** | CUS-PR-001 (Chapter 4) |
| **Phase** | Phase 1 — MVP go-live (Bắt buộc) |
| **Độ phức tạp** | Cao |
| **Created by** | [Tên BA] |
| **Reviewed by** | [Reviewer] |
| **Approved by** | [Approver] |
| **Version** | 1.0 |
| **Created date** | DD/MM/YYYY |
| **Last update** | DD/MM/YYYY |

---

## **HISTORIES (Lịch sử phiên bản)**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — bản FS đầu tiên cho function tính lương GV theo giờ | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW (Tổng quan chức năng)**

### Mô tả

Chức năng này tự động tính lương cho giáo viên và trợ giảng (TA) tại Học Bá Education dựa trên **số giờ dạy đã xác thực** (validated teaching hours) từ Module Attendance, nhân với **đơn giá giờ** được cấu hình riêng cho từng giáo viên trong hợp đồng lao động. Đơn giá giờ có thể khác nhau theo từng cấp HSK (cơ bản, trung cấp, HSK4+) và theo loại lớp (thông thường, đặc biệt).

Function này thay thế hoàn toàn quy trình tính tay trên Excel hiện tại — vốn mất 3-5 ngày làm việc/tháng cho Phòng Đào tạo và 2-3 ngày cho Phòng Nhân sự, đồng thời gây ra trung bình 3-5 thắc mắc lương từ giáo viên mỗi tháng.

### Mục đích nghiệp vụ (Business Requirement)

Giải quyết Pain Points sau từ Chapter 2.5.4:

| Mã Pain Point | Mô tả | Cách giải quyết |
|---|---|---|
| **PP-PR-02** | Tính lương giáo viên phức tạp, dễ sai | Tự động hóa hoàn toàn, có Rule Trace cho mỗi dòng |
| **PP-PR-05** | Chu kỳ lương dài 8-10 ngày | Tính trong vài giây thay vì 2-3 ngày |
| **PP-PR-11** | Không có validation layer | Chặn payslip nếu Work Entry còn trạng thái draft/conflict |
| **PP-PR-12** | Bottleneck đối soát giờ dạy | Tận dụng Work Entry đã xác thực từ Module Attendance |
| **PP-PR-14** | Không phân biệt loại giờ làm | Phân biệt rõ WORK200 (Teaching) vs WORK110 (OT) qua Work Entry Type |

### Tham chiếu liên module

| Module liên quan | Tương tác |
|---|---|
| **Module Attendance** | Consume Work Entries loại WORK200 (Teaching Hours) đã ở trạng thái `validated` |
| **Module Employee** | Lấy danh sách giáo viên qua `employee_type = teacher/TA`, đọc trường HSK certification |
| **Module Time Off** | Loại trừ các ngày nghỉ phép đã duyệt khỏi giờ dạy |
| **Chapter 5 (Configuration)** | Tham chiếu Salary Structure `STR-PR-02` (Teacher Structure) |

### Đối tượng sử dụng

| Vai trò | Quyền tương tác |
|---|---|
| **HR Officer (C&B Specialist)** | Trigger compute payslip, review TEACH_HOURS line |
| **HR Manager** | Approve payslip cuối cùng |
| **Academic Manager** | Cấu hình đơn giá giờ trên hợp đồng (chỉ đọc payslip) |
| **Teacher/TA** | Xem payslip của chính mình qua Employee Portal |

---

## **FUNCTION FLOW (Luồng chức năng)**

### Sơ đồ tổng quát

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PRE-CONDITIONS                                                           │
│  ─ Hợp đồng GV có x_teaching_hourly_rate                                  │
│  ─ Work Entries WORK200 trong kỳ ở trạng thái 'validated'                 │
│  ─ Salary Structure STR-PR-02 đã được cấu hình                            │
└─────────────────────────────┬────────────────────────────────────────────┘
                              ▼
              ┌───────────────────────────────────┐
              │  HR tạo Payslip Batch tháng       │
              │  + assign Salary Structure        │
              │    STR-PR-02 (Teacher)            │
              └───────────────┬───────────────────┘
                              ▼
              ┌───────────────────────────────────┐
              │  Generate Payslips (Draft state)   │
              │  → 1 payslip / 1 giáo viên active  │
              └───────────────┬───────────────────┘
                              ▼
              ┌───────────────────────────────────┐
              │  Compute Sheet trigger             │
              │  → đọc Work Entries WORK200        │
              └───────────────┬───────────────────┘
                              ▼
                ┌─────────────────────────────┐
                │   Validation Gate          │
                │   Còn Work Entry draft?    │
                └────┬───────────────┬───────┘
                     │ Yes            │ No
                     ▼                ▼
            ┌────────────────┐  ┌────────────────────────┐
            │ Raise Error    │  │ Apply TEACH_HOURS rule  │
            │ (chặn compute) │  │ = Σ(hours) × hourly_rate│
            └────────────────┘  └─────────┬──────────────┘
                                          ▼
                              ┌─────────────────────────┐
                              │ Apply EXTRA_HOURS_BONUS │
                              │ (nếu vượt threshold)    │
                              └─────────┬───────────────┘
                                        ▼
                              ┌─────────────────────────┐
                              │ Apply HOLIDAY_OT (300%)  │
                              │ nếu có Work Entry        │
                              │ WORK110_OT_HOLIDAY       │
                              └─────────┬───────────────┘
                                        ▼
                              ┌─────────────────────────┐
                              │ Continue chuỗi Salary    │
                              │ Rules: + insurance + PIT │
                              │ → NET                    │
                              └─────────────────────────┘
```

### Diễn giải luồng

1. **Bước 1 — Tiền điều kiện**: Trước khi tính, hệ thống phải có (a) hợp đồng GV với đơn giá giờ, (b) Work Entries đã được xác thực bởi Module Attendance, (c) Salary Structure Teacher đã được cấu hình.

2. **Bước 2 — Tạo Batch**: HR Officer tạo Payslip Batch cho tháng (ví dụ "Lương GV Tháng 10/2026"), assign Salary Structure `STR-PR-02`.

3. **Bước 3 — Generate Payslips**: Hệ thống tự sinh 1 payslip cho mỗi giáo viên đang active có hợp đồng hợp lệ trong kỳ.

4. **Bước 4 — Validation Gate**: TRƯỚC khi compute, kiểm tra mọi Work Entry WORK200 trong kỳ phải ở trạng thái `validated`. Nếu có entry `draft` hoặc `conflict` → raise ValidationError, không cho compute.

5. **Bước 5 — Apply TEACH_HOURS Rule**: Tính `teach_hours_amount = Σ(work_entries.worked_hours WHERE type=WORK200) × contract.x_teaching_hourly_rate`.

6. **Bước 6 — Apply EXTRA_HOURS_BONUS**: Nếu tổng giờ vượt `x_standard_threshold` của hợp đồng → tính bonus = (hours - threshold) × extra_rate.

7. **Bước 7 — Apply HOLIDAY_OT**: Nếu trong kỳ có Work Entries WORK110_OT_HOLIDAY (dạy ngày lễ) → áp multiplier 3× theo CFG-PR-006.

8. **Bước 8 — Continue Salary Pipeline**: Sau khi có teaching salary, tiếp tục chuỗi rules còn lại: BHXH/BHYT/BHTN → PIT → NET (đã định nghĩa trong STR-PR-02).

---

## **SCREEN LAYOUT (Bố cục màn hình)**

Function này không tạo màn hình mới — sử dụng các màn hình **chuẩn của Odoo Payroll** với một số trường custom được thêm. Có **3 màn hình** chính liên quan:

### Screen 1: Contract Form — Tab "Salary Information" (Cấu hình đơn giá giờ)

**Mục đích**: Academic Manager hoặc HR cấu hình đơn giá giờ cho giáo viên trên hợp đồng.

**Vị trí trong Odoo**: Employees → Contracts → [Chọn contract của Teacher] → Salary Information Tab

**Layout**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Hợp đồng: HD-2026-T-001 — Cô Nguyễn Thị Hương                │
├─────────────────────────────────────────────────────────────────┤
│  [Salary Information] [Work Information] [HR Settings] [...]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Salary Structure Type: [Teacher Structure ▼]   (read-only)    │
│                                                                  │
│  ┌─── Thông tin Lương theo Giờ ─────────────────────────────┐   │
│  │                                                            │   │
│  │  Đơn giá giờ cơ bản (*)         : [_____________] VND/h  │   │
│  │  Đơn giá giờ HSK4+              : [_____________] VND/h  │   │
│  │  Đơn giá giờ lớp đặc biệt       : [_____________] VND/h  │   │
│  │  Ngưỡng giờ chuẩn/tháng         : [_____________] giờ    │   │
│  │  Đơn giá giờ vượt ngưỡng        : [_____________] VND/h  │   │
│  │  ☐ Có lương cố định base (FIXED_BASE)                    │   │
│  │     └─ Lương cố định           : [_____________] VND/th  │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─── Thông tin Lương Khác ─────────────────────────────────┐   │
│  │  Wage (lương danh nghĩa cho BH)  : [_____________] VND   │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [Save] [Discard]                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Screen 2: Payslip Form — Tab "Salary Computation" (Xem kết quả tính)

**Mục đích**: HR Officer xem dòng TEACH_HOURS đã tính cho từng giáo viên.

**Vị trí trong Odoo**: Payroll → Payslips → [Chọn payslip của Teacher] → Salary Computation Tab

**Layout**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Payslip: SLIP/2026/10/0042 — Cô Nguyễn Thị Hương                  │
│  Period: 01/10/2026 — 31/10/2026          State: [Waiting ▼]       │
├──────────────────────────────────────────────────────────────────────┤
│  [Worked Days & Inputs] [Salary Computation] [Accounting] [Other]   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─── Bảng tính lương chi tiết ──────────────────────────────────┐   │
│  │  Code     │ Name                  │ Quantity │ Rate │ Total   │   │
│  │  ─────────┼───────────────────────┼──────────┼──────┼─────────  │   │
│  │  TEACH_HOURS│ Lương theo giờ dạy  │   72.5h │ 250k│ 18,125k │   │
│  │  EXTRA_HOURS│ Bonus giờ vượt ngưỡng│   12.5h │ 300k│  3,750k │   │
│  │  HOLIDAY_OT │ OT ngày lễ (300%)   │    3.0h │ 750k│  2,250k │   │
│  │  ─────────┼───────────────────────┼──────────┼──────┼─────────  │   │
│  │  GROSS    │ Tổng lương Gross      │         │      │ 24,125k │   │
│  │  BHXH     │ BHXH NV đóng (8%)     │         │      │ -2,000k │   │
│  │  BHYT     │ BHYT NV đóng (1.5%)   │         │      │   -375k │   │
│  │  ...      │                       │         │      │         │   │
│  │  NET      │ Thực lĩnh             │         │      │ 19,500k │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  [Rule Trace ▼]   [Recompute Sheet]   [Refuse]   [Confirm]          │
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 3: Payslip Form — Tab "Worked Days & Inputs" (Xem chi tiết giờ dạy)

**Mục đích**: Drill-down để xem cụ thể giờ dạy đến từ những buổi nào.

**Layout**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Worked Days & Inputs] [Salary Computation] [...]                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─── Work Entries trong kỳ (read-only) ─────────────────────────┐   │
│  │  Date       │ Class Code         │ Type    │ Hours │ Status   │   │
│  │  ───────────┼────────────────────┼─────────┼───────┼────────    │   │
│  │  03/10/2026 │ G-HSK4-T10-Tối4    │ WORK200 │  1.5h │ ✅ Valid │   │
│  │  05/10/2026 │ G-HSK3-T10-Sáng2   │ WORK200 │  2.0h │ ✅ Valid │   │
│  │  10/10/2026 │ G-HSK4-T10-Tối4    │ WORK200 │  1.5h │ ✅ Valid │   │
│  │  30/04/2026 │ G-HSK4-Special     │ WORK110_OT_HOLIDAY│ 1.0h │✅│   │
│  │  ...        │                    │         │       │          │   │
│  │  ───────────┼────────────────────┼─────────┼───────┼────────    │   │
│  │  TOTAL      │                    │ WORK200 │ 72.5h │          │   │
│  │             │                    │ HOLIDAY │  3.0h │          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ⚠ Nếu có entry nào ở trạng thái 'draft' hoặc 'conflict':           │
│     [Recompute Sheet] sẽ bị disable, hiển thị warning popup.        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION (Logic xử lý)**

### Bảng Input Data

| No | Tên trường | Nguồn (Model.Field) | Điều kiện lọc |
|---|---|---|---|
| 1 | Employee | `hr.employee.id` | `employee_type IN ('teacher', 'tutor')` AND `active = True` |
| 2 | Contract đang hoạt động | `hr.contract` | `state = 'open'` AND `date_start <= period_end` AND `(date_end IS NULL OR date_end >= period_start)` |
| 3 | Đơn giá giờ cơ bản | `hr.contract.x_teaching_hourly_rate` | Required, > 0 |
| 4 | Đơn giá giờ HSK4+ | `hr.contract.x_rate_hsk_class` | Optional (NULL → dùng base rate) |
| 5 | Đơn giá giờ lớp đặc biệt | `hr.contract.x_rate_advanced_class` | Optional |
| 6 | Ngưỡng giờ chuẩn | `hr.contract.x_standard_threshold` | Default = 60 (giờ/tháng) |
| 7 | Đơn giá vượt ngưỡng | `hr.contract.x_extra_rate` | Optional (NULL → = base × 1.25) |
| 8 | Lương cố định base | `hr.contract.x_fixed_base` | Optional (NULL hoặc 0 → không áp dụng) |
| 9 | Work Entries giờ dạy | `hr.work.entry` | `work_entry_type.code = 'WORK200'` AND `state = 'validated'` AND date_start trong kỳ |
| 10 | Work Entries OT ngày lễ | `hr.work.entry` | `work_entry_type.code = 'WORK110_OT_HOLIDAY'` AND `state = 'validated'` |
| 11 | Public Holidays | `resource.calendar.leaves` | global = True, trong kỳ |
| 12 | Period (kỳ tính lương) | `hr.payslip.date_from`, `date_to` | Required |

### Bảng Output Data

| No | Salary Rule Code | Cách tính | Mô tả output |
|---|---|---|---|
| 1 | **TEACH_HOURS** | `Σ(work_entry.worked_hours) × contract.x_teaching_hourly_rate` (chỉ tính WORK200) | Lương cơ bản theo giờ dạy |
| 2 | **HSK_HOURS_PREMIUM** | Nếu work_entry có class_level = 'HSK4+' và `x_rate_hsk_class > x_teaching_hourly_rate`: tính phần chênh × hours | Premium cho lớp HSK cao |
| 3 | **EXTRA_HOURS_BONUS** | `IF total_hours > x_standard_threshold THEN (total_hours - threshold) × x_extra_rate ELSE 0` | Bonus giờ vượt ngưỡng |
| 4 | **HOLIDAY_OT** | `Σ(work_entries WHERE type=WORK110_OT_HOLIDAY) × hourly_rate × 3.0` | OT ngày lễ 300% |
| 5 | **FIXED_BASE** | `IF x_fixed_base > 0 THEN x_fixed_base ELSE 0` (pro-rated nếu vào/nghỉ giữa kỳ) | Lương cố định (nếu hợp đồng có) |
| 6 | **GROSS_TEACHING** | `TEACH_HOURS + HSK_HOURS_PREMIUM + EXTRA_HOURS_BONUS + HOLIDAY_OT + FIXED_BASE` | Gross teaching salary |
| 7 | (tiếp tục chuỗi rules chuẩn) | BHXH → BHYT → BHTN → PIT → NET | Đã định nghĩa trong STR-PR-02 |

### Thuật toán chính (Pseudo-code BA-level)

```
FUNCTION compute_teaching_salary(payslip):
    
    # ── Step 1: Validation Gate ──────────────────────────
    pending_entries = SEARCH hr.work.entry
        WHERE employee = payslip.employee
          AND date BETWEEN payslip.date_from AND payslip.date_to
          AND state IN ('draft', 'conflict')
    
    IF pending_entries.count > 0:
        RAISE ValidationError(
            "Còn {N} Work Entry chưa được xác thực. "
            "Vui lòng xử lý trước khi tính lương."
        )
        RETURN
    
    # ── Step 2: Đọc cấu hình contract ────────────────────
    contract = payslip.employee.active_contract
    
    IF contract.x_teaching_hourly_rate IS NULL OR <= 0:
        RAISE ValidationError(
            "Hợp đồng chưa cấu hình đơn giá giờ. "
            "Vui lòng liên hệ Academic Manager."
        )
        RETURN
    
    # ── Step 3: Lấy giờ dạy đã xác thực ──────────────────
    teaching_entries = SEARCH hr.work.entry
        WHERE employee = payslip.employee
          AND work_entry_type.code = 'WORK200'
          AND state = 'validated'
          AND date BETWEEN payslip.date_from AND payslip.date_to
    
    total_hours = SUM(teaching_entries.worked_hours)
    
    # ── Step 4: Tính TEACH_HOURS cơ bản ──────────────────
    teach_amount = total_hours × contract.x_teaching_hourly_rate
    
    # ── Step 5: Tính premium HSK4+ (nếu có) ──────────────
    hsk_premium = 0
    IF contract.x_rate_hsk_class IS NOT NULL:
        hsk_entries = teaching_entries WHERE class_level = 'HSK4+'
        hsk_hours = SUM(hsk_entries.worked_hours)
        rate_diff = contract.x_rate_hsk_class - contract.x_teaching_hourly_rate
        IF rate_diff > 0:
            hsk_premium = hsk_hours × rate_diff
    
    # ── Step 6: Tính EXTRA_HOURS_BONUS ───────────────────
    extra_bonus = 0
    IF total_hours > contract.x_standard_threshold:
        excess_hours = total_hours - contract.x_standard_threshold
        extra_rate = contract.x_extra_rate OR (contract.x_teaching_hourly_rate × 1.25)
        extra_bonus = excess_hours × extra_rate
    
    # ── Step 7: Tính HOLIDAY_OT (300%) ───────────────────
    holiday_entries = SEARCH hr.work.entry
        WHERE employee = payslip.employee
          AND work_entry_type.code = 'WORK110_OT_HOLIDAY'
          AND state = 'validated'
          AND date BETWEEN payslip.date_from AND payslip.date_to
    
    holiday_hours = SUM(holiday_entries.worked_hours)
    holiday_amount = holiday_hours × contract.x_teaching_hourly_rate × 3.0
    
    # ── Step 8: Tính FIXED_BASE (nếu hợp đồng có) ───────
    fixed_base = 0
    IF contract.x_fixed_base > 0:
        # Pro-rate nếu vào/nghỉ giữa kỳ
        worked_days = payslip.worked_days_total
        standard_days = payslip.period.working_days_count
        fixed_base = contract.x_fixed_base × (worked_days / standard_days)
    
    # ── Step 9: Tổng hợp Gross Teaching ──────────────────
    gross_teaching = teach_amount + hsk_premium + extra_bonus 
                    + holiday_amount + fixed_base
    
    # ── Step 10: Tiếp tục Salary Pipeline ────────────────
    # (Insurance, PIT, NET — đã định nghĩa trong STR-PR-02)
    RETURN gross_teaching
```

### Trace logic minh họa (Ví dụ thực tế)

**Cô Nguyễn Thị Hương — Tháng 10/2026:**

| Bước | Tính toán | Kết quả |
|---|---|---|
| Tổng giờ WORK200 đã validated | 48 buổi dạy × 1.5h = 72h + 0.5h lẻ | 72.5h |
| Trong đó có 20 giờ lớp HSK4+ | | |
| Ngưỡng chuẩn của Cô Hương | (cấu hình trong hợp đồng) | 60h |
| Đơn giá cơ bản | (cấu hình) | 250.000 VND/h |
| Đơn giá HSK4+ | (cấu hình) | 320.000 VND/h |
| Đơn giá vượt ngưỡng | (cấu hình) | 300.000 VND/h |
| **TEACH_HOURS** | 72.5 × 250.000 | **18.125.000** |
| **HSK_HOURS_PREMIUM** | 20 × (320.000 - 250.000) | **1.400.000** |
| **EXTRA_HOURS_BONUS** | (72.5 - 60) × 300.000 | **3.750.000** |
| Giờ dạy ngày lễ 30/4 | 1 buổi × 2h | 2h |
| **HOLIDAY_OT** | 2 × 250.000 × 3.0 | **1.500.000** |
| **GROSS_TEACHING** | Tổng các khoản trên | **24.775.000** |
| Tiếp tục: BHXH/BHYT/BHTN | (theo chuỗi rules STR-PR-02) | -2.475.000 |
| Tiếp tục: PIT | (theo biểu 7 bậc) | -1.840.000 |
| **NET** | Thực lĩnh | **20.460.000** |

---

## **SCREEN DEFINITION (Định nghĩa kỹ thuật field)**

### Bảng định nghĩa các trường custom thêm vào `hr.contract`

| No | Field Name | Type | I/O | Multi/Single | Data Type | Length/Precision | Required | Default | Format | Align | Search Help (F4) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `x_teaching_hourly_rate` | Field | I/O | Single | Float | (12, 0) | Yes (cho contract teacher) | NULL | #,##0 | Right | No |
| 2 | `x_rate_hsk_class` | Field | I/O | Single | Float | (12, 0) | No | NULL | #,##0 | Right | No |
| 3 | `x_rate_advanced_class` | Field | I/O | Single | Float | (12, 0) | No | NULL | #,##0 | Right | No |
| 4 | `x_standard_threshold` | Field | I/O | Single | Float | (6, 2) | No | 60.0 | #,##0.0 | Right | No |
| 5 | `x_extra_rate` | Field | I/O | Single | Float | (12, 0) | No | NULL | #,##0 | Right | No |
| 6 | `x_fixed_base` | Field | I/O | Single | Float | (12, 0) | No | 0 | #,##0 | Right | No |
| 7 | `x_has_fixed_base` | Field | I/O | Single | Boolean | - | No | False | Checkbox | Left | No |

### Bảng định nghĩa Salary Rules mới

| No | Rule Code | Category | Sequence | Condition | Computation Type | Quantity | Amount Formula |
|---|---|---|---|---|---|---|---|
| 1 | TEACH_HOURS | Allowance | 10 | `contract.x_teaching_hourly_rate > 0` | Python | hours_worked | `inputs.WORK200_HOURS × contract.x_teaching_hourly_rate` |
| 2 | HSK_HOURS_PREMIUM | Allowance | 11 | `contract.x_rate_hsk_class is not None` | Python | hsk_hours | (xem pseudocode bước 5) |
| 3 | EXTRA_HOURS_BONUS | Allowance | 12 | `total_hours > threshold` | Python | excess_hours | (xem pseudocode bước 6) |
| 4 | HOLIDAY_OT | Allowance | 13 | có WORK110_OT_HOLIDAY | Python | holiday_hours | `hours × rate × 3.0` |
| 5 | FIXED_BASE | Allowance | 5 | `contract.x_fixed_base > 0` | Python | 1 | `x_fixed_base × pro_rate` |
| 6 | GROSS_TEACHING | Gross | 20 | always | Code | 1 | Σ(rules 1-5) |

### Bảng định nghĩa View XML cần extend

| No | View Reference | Inherit From | Action |
|---|---|---|---|
| 1 | `view_hr_contract_form_inherit_teaching` | `hr_contract.hr_contract_view_form` | Thêm 7 fields vào Tab Salary Information |
| 2 | `view_hr_payslip_form_inherit_teaching` | `hr_payroll.view_hr_payslip_form` | Highlight TEACH_HOURS rules trong bảng Computation |
| 3 | `view_hr_employee_form_teacher_filter` | `hr.view_employee_form` | Thêm domain filter `employee_type IN ('teacher', 'tutor')` |

---

## **VALIDATION RULES (Quy tắc kiểm tra)**

| No | Quy tắc | Khi nào trigger | Hành động khi vi phạm |
|---|---|---|---|
| **VR-001** | `x_teaching_hourly_rate` phải > 0 nếu nhân viên là teacher | On Save Contract | Block save, hiển thị error "Đơn giá giờ phải lớn hơn 0" |
| **VR-002** | `x_rate_hsk_class` phải > `x_teaching_hourly_rate` (nếu có) | On Save Contract | Warning (cho phép save nhưng cảnh báo) |
| **VR-003** | `x_standard_threshold` phải trong khoảng 0-200h/tháng | On Save Contract | Block save nếu ngoài range |
| **VR-004** | Mọi Work Entry WORK200 trong kỳ phải ở state `validated` | On Compute Payslip | Block compute, raise ValidationError |
| **VR-005** | Nhân viên phải có active contract trong kỳ tính lương | On Generate Payslip | Skip nhân viên đó, log warning |
| **VR-006** | Salary Structure phải là `STR-PR-02` (Teacher Structure) | On Compute Payslip | Block compute, hiển thị error |
| **VR-007** | Nếu `x_has_fixed_base = True` thì `x_fixed_base` phải > 0 | On Save Contract | Block save |
| **VR-008** | Worked hours không được âm | On Read Work Entry | Skip entry đó, log warning |
| **VR-009** | Đơn giá giờ không được vượt 1.000.000 VND/h | On Save Contract | Warning (cho phép save nhưng cảnh báo HR Manager) |
| **VR-010** | Tổng giờ dạy/tháng không vượt 250h (giới hạn vật lý) | On Compute Payslip | Warning, đánh dấu payslip màu vàng (cần review) |

---

## **EXCEPTION FLOW (Luồng ngoại lệ)**

### EX-001: Còn Work Entry chưa xác thực

**Trigger**: Khi HR bấm "Compute Sheet" mà còn có WORK200 entry ở state `draft` hoặc `conflict`.

**Luồng xử lý**:

1. Hệ thống raise `ValidationError`
2. Hiển thị popup với danh sách Work Entries chưa xác thực
3. Cung cấp link "Xử lý Work Entries" → chuyển sang Module Attendance
4. Payslip giữ nguyên trạng thái Draft
5. Log warning vào Chatter

### EX-002: Hợp đồng thiếu đơn giá giờ

**Trigger**: Khi compute mà hợp đồng GV không có `x_teaching_hourly_rate`.

**Luồng xử lý**:

1. Raise `ValidationError`: "Hợp đồng [contract_ref] của [employee_name] chưa cấu hình đơn giá giờ"
2. Nút "Mở hợp đồng" → chuyển sang form contract
3. Payslip không tính được TEACH_HOURS, các rule khác cũng không tính

### EX-003: Giáo viên đổi đơn giá giữa kỳ

**Trigger**: Hợp đồng được sửa `x_teaching_hourly_rate` sau khi đã có một số Work Entries trong kỳ.

**Luồng xử lý**:

1. Hệ thống đọc đơn giá tại **thời điểm tính payslip** (snapshot), không phải tại thời điểm Work Entry
2. Nếu HR muốn áp dụng đơn giá cũ cho 1 phần kỳ + đơn giá mới cho phần còn lại → phải tạo **2 hợp đồng** riêng (cũ + mới với ngày hiệu lực khác nhau)
3. Log warning vào Chatter: "Đơn giá đã thay đổi trong kỳ — vui lòng review payslip"

### EX-004: Work Entry có duration > 24h (data error)

**Trigger**: Phát hiện work_entry.worked_hours > 24h cho 1 entry (lỗi nhập liệu).

**Luồng xử lý**:

1. Skip entry đó, không tính vào TEACH_HOURS
2. Log error vào Chatter và system log
3. Đánh dấu payslip màu đỏ (Blocked)
4. Notify HR Manager qua email

### EX-005: Recompute sau khi đã ở state Done

**Trigger**: HR Manager reset payslip từ Done → Draft sau khi đã có thanh toán.

**Luồng xử lý**:

1. Đòi hỏi quyền `SEC-PR-03` (HR Manager)
2. Bắt buộc nhập lý do reset (textarea)
3. Unlock Work Entries (chuyển state từ `payslip_included` về `validated`)
4. Reset payslip về Draft
5. Log đầy đủ vào Chatter (user, time, reason, IP)
6. Notify Finance để đảo bút toán nếu cần

---

## **BUSINESS RULES (Quy tắc nghiệp vụ)**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-001** | Chỉ tính giờ dạy đã xác thực | Work Entry phải ở state `validated`, không tính `draft`, `conflict`, `cancelled` |
| **BR-PR-002** | Đơn giá theo hợp đồng tại thời điểm tính lương | Snapshot rate tại payslip compute, không dùng rate hiện tại của contract |
| **BR-PR-003** | HSK Premium chỉ áp dụng cho lớp cấp HSK4+ | Class level được lấy từ `academic.session.level` (Module Academic) |
| **BR-PR-004** | EXTRA_HOURS_BONUS chỉ tính phần vượt ngưỡng | Không double-count giờ chuẩn |
| **BR-PR-005** | HOLIDAY_OT = đơn giá × 3.0 | Theo Điều 98 Bộ luật Lao động 2019, không tính cộng dồn với EXTRA_HOURS |
| **BR-PR-006** | FIXED_BASE được pro-rate khi vào/nghỉ giữa kỳ | Dựa trên worked_days / standard_days |
| **BR-PR-007** | Giờ dạy ngày Chủ nhật/Thứ 7 vẫn tính WORK200 (không cộng dồn OT cuối tuần) | Vì giáo viên ở Học Bá thường dạy cuối tuần — coi như giờ chuẩn |
| **BR-PR-008** | Audit trail bắt buộc khi reset payslip Done → Draft | Log user, time, reason vào Chatter |
| **BR-PR-009** | Payslip GV không được Done khi còn Work Entry pending | Gate ở Bước 4 của Function Flow |
| **BR-PR-010** | Đơn giá vượt 1tr/giờ cần HR Manager approve | VR-009 — warning, cần ghi chú lý do |
| **BR-PR-011** | Báo cáo TEACH_HOURS phải truy xuất được đến từng buổi dạy | Drill-down từ Payslip → Work Entries (Screen 3) |
| **BR-PR-012** | Khi reset payslip, Work Entries được unlock tự động | Để recompute lại với data có thể đã thay đổi |

---

## **OUTPUT (Kết quả đầu ra)**

### 1. Dữ liệu hệ thống

| Đối tượng | Tạo/Cập nhật | Trường được set |
|---|---|---|
| `hr.payslip.line` | Tạo mới | Lines mới: TEACH_HOURS, HSK_HOURS_PREMIUM, EXTRA_HOURS_BONUS, HOLIDAY_OT, FIXED_BASE |
| `hr.work.entry` | Cập nhật state | `payslip_included` (khi payslip Done) hoặc unlock về `validated` (khi reset) |
| `hr.payslip` | Cập nhật trường | `gross_amount`, `net_amount`, `state` |
| `mail.message` (Chatter) | Tạo mới | Audit log cho mọi state transition và adjustment |

### 2. Báo cáo người dùng nhận được

| Người nhận | Tài liệu | Khi nào |
|---|---|---|
| Giáo viên | Payslip PDF qua email | Khi payslip chuyển sang state Paid |
| HR Officer | Bảng tổng hợp payslip batch | Khi review trước approval |
| HR Manager | Variation Report (so sánh tháng trước) | Khi approval |
| Finance | Bút toán Accounting Move (draft) | Khi payslip Done |

### 3. Indicators trên Payslip Card

- 🟢 Xanh: Compute sạch, sẵn sàng approve
- 🟡 Vàng: Biến động > 20% so tháng trước, hoặc tổng giờ > 200h
- 🔴 Đỏ: Còn Work Entry pending hoặc lỗi data

---

## **UI REFERENCE (Tham chiếu giao diện)**

| ID | Wireframe / Reference | Mô tả |
|---|---|---|
| **UI-PR-001-01** | Wireframe Contract Salary Tab | Screen 1 — Tab "Salary Information" mở rộng |
| **UI-PR-001-02** | Wireframe Payslip Computation | Screen 2 — Tab "Salary Computation" với highlight TEACH_HOURS |
| **UI-PR-001-03** | Wireframe Payslip Worked Days | Screen 3 — Tab "Worked Days & Inputs" — drill-down giờ dạy |
| **UI-PR-001-04** | Wireframe Rule Trace Popup | Popup hiển thị chi tiết công thức của 1 dòng salary rule |
| **UI-PR-001-05** | Wireframe Validation Error Modal | Modal khi gặp Work Entry pending — kèm link xử lý |

*(Các wireframe SVG sẽ được tạo riêng và đặt trong thư mục `/wireframes/payroll/`)*

---

## **MESSAGE DEFINITION (Định nghĩa thông báo)**

| Message ID | Language | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-001-001** | VN | Hợp đồng [contract_ref] chưa cấu hình đơn giá giờ. Vui lòng liên hệ Academic Manager. | On Compute Payslip |
| MSG-PR-001-001 | EN | Contract [contract_ref] has not configured hourly rate. Please contact Academic Manager. | On Compute Payslip |
| **MSG-PR-001-002** | VN | Còn {N} Work Entry chưa được xác thực. Vui lòng xử lý trước khi tính lương. | On Compute Payslip |
| MSG-PR-001-002 | EN | {N} Work Entries are still pending validation. Please resolve before computing payslip. | On Compute Payslip |
| **MSG-PR-001-003** | VN | Đơn giá giờ phải lớn hơn 0 | On Save Contract |
| MSG-PR-001-003 | EN | Hourly rate must be greater than 0 | On Save Contract |
| **MSG-PR-001-004** | VN | Đơn giá giờ vượt 1.000.000 VND/giờ — cần HR Manager phê duyệt | On Save Contract (warning) |
| MSG-PR-001-004 | EN | Hourly rate exceeds 1,000,000 VND/h — requires HR Manager approval | On Save Contract (warning) |
| **MSG-PR-001-005** | VN | Đơn giá giờ HSK nên cao hơn đơn giá cơ bản | On Save Contract (info) |
| MSG-PR-001-005 | EN | HSK class rate should be higher than base rate | On Save Contract (info) |
| **MSG-PR-001-006** | VN | Tổng giờ dạy vượt 200h/tháng — payslip cần review thêm | On Compute Payslip (warning) |
| MSG-PR-001-006 | EN | Total teaching hours exceeds 200h/month — payslip needs additional review | On Compute Payslip (warning) |
| **MSG-PR-001-007** | VN | Work Entry có giờ làm âm hoặc quá 24h — data có thể bị sai | System log + Chatter |
| MSG-PR-001-007 | EN | Work Entry has negative or > 24h duration — possible data error | System log + Chatter |
| **MSG-PR-001-008** | VN | Payslip đã được reset về Draft. Lý do: {reason}. Bởi: {user} | On Reset (Chatter audit log) |
| MSG-PR-001-008 | EN | Payslip has been reset to Draft. Reason: {reason}. By: {user} | On Reset (Chatter audit log) |
| **MSG-PR-001-009** | VN | Đã tính TEACH_HOURS thành công: {total_hours}h × {rate}đ = {amount}đ | On Compute (success info) |
| MSG-PR-001-009 | EN | TEACH_HOURS computed successfully: {total_hours}h × {rate} = {amount} | On Compute (success info) |
| **MSG-PR-001-010** | VN | Đơn giá đã thay đổi trong kỳ — vui lòng review payslip | On Compute (warning) |
| MSG-PR-001-010 | EN | Hourly rate has changed during the period — please review the payslip | On Compute (warning) |

---

## **PRECONDITIONS (Tiền điều kiện)**

Trước khi function này hoạt động, các điều kiện sau phải được đáp ứng:

| No | Tiền điều kiện | Module phụ trách | Kiểm tra ở đâu |
|---|---|---|---|
| 1 | Salary Structure `STR-PR-02` đã được tạo | Chapter 5 (5.4.1) | Configuration → Salary Structures |
| 2 | 7 trường custom `x_*` đã được thêm vào `hr.contract` | Function này | Database schema |
| 3 | Work Entry Type `WORK200` đã tồn tại | Module Attendance (CFG-PR-006 / 5.4.6) | Configuration → Work Entry Types |
| 4 | Work Entry Type `WORK110_OT_HOLIDAY` đã tồn tại | Module Attendance | Configuration → Work Entry Types |
| 5 | Public Holidays VN đã được cấu hình | Module Time Off (5.4.9) | Time Off → Public Holidays |
| 6 | Mỗi giáo viên có 1 active contract | Module Employee | Employees → Contracts |
| 7 | Mỗi hợp đồng GV có `x_teaching_hourly_rate > 0` | Function này (VR-001) | Contract Form |
| 8 | Work Entries trong kỳ đã ở state `validated` | Module Attendance (Function ATT-F-001/002) | Payroll → Work Entries |

---

## **POSTCONDITIONS (Hậu điều kiện)**

Sau khi function thực thi thành công:

| No | Kết quả | Trạng thái hệ thống |
|---|---|---|
| 1 | Payslip có dòng TEACH_HOURS với số tiền chính xác | `hr.payslip.line` được tạo |
| 2 | Payslip có thể chuyển sang state Done | State transition cho phép |
| 3 | Work Entries WORK200 trong kỳ ở state `payslip_included` (khi Done) | Lock — không sửa được nữa |
| 4 | Audit log đầy đủ trong Chatter | Mọi action có user + timestamp |
| 5 | Variation Report có dữ liệu so sánh với tháng trước | Function FUNC-PR-009 sử dụng |

---

## **TRIGGER (Khởi tạo function)**

| No | Trigger | Người thực hiện | Tần suất |
|---|---|---|---|
| 1 | HR Officer bấm "Compute Sheet" trên Payslip | HR Officer (`SEC-PR-01/02`) | Hàng tháng, sau khi Work Entries đã được validate |
| 2 | HR bấm "Generate Payslips" trên Payslip Batch | HR Officer | Hàng tháng, vào ngày bắt đầu chu kỳ |
| 3 | HR Manager bấm "Refresh Computation" sau khi sửa input | HR Manager (`SEC-PR-03`) | Khi cần |
| 4 | Automated: Salary Structure được apply lên payslip mới tạo | Hệ thống | Khi Generate Payslips |

---

## **GHI CHÚ TRIỂN KHAI**

### Dependencies (Phụ thuộc)

Function này **phụ thuộc trực tiếp** vào:

1. **ATT-F-001 / ATT-F-002** (Module Attendance) — phải go-live trước để có Work Entries
2. **FUNC-EMP-003** (Module Employee — Dependents) — cho việc tính PIT về sau
3. **Chapter 5.4.1 — STR-PR-02** — Salary Structure phải được tạo trước

### Test Cases gợi ý

1. **TC-001**: GV chỉ có giờ WORK200, không có HSK4+, không vượt ngưỡng → chỉ có TEACH_HOURS
2. **TC-002**: GV có giờ HSK4+ → có thêm HSK_HOURS_PREMIUM
3. **TC-003**: GV vượt ngưỡng → có EXTRA_HOURS_BONUS
4. **TC-004**: GV có dạy ngày lễ → có HOLIDAY_OT (300%)
5. **TC-005**: GV có hợp đồng có FIXED_BASE → có thêm dòng FIXED_BASE pro-rated
6. **TC-006**: GV vào giữa kỳ → FIXED_BASE pro-rated, TEACH_HOURS không pro-rate
7. **TC-007**: GV có Work Entry pending → compute bị block
8. **TC-008**: Hợp đồng không có hourly_rate → compute bị block
9. **TC-009**: Reset payslip Done → Draft → Work Entries unlock
10. **TC-010**: 2 hợp đồng nối tiếp trong kỳ (đơn giá khác) → tính đúng đoạn từng hợp đồng

### Phụ lục Custom Fields tóm tắt

| Field | Model | Type | Mục đích |
|---|---|---|---|
| `x_teaching_hourly_rate` | hr.contract | Float | Đơn giá giờ cơ bản |
| `x_rate_hsk_class` | hr.contract | Float | Đơn giá giờ lớp HSK4+ |
| `x_rate_advanced_class` | hr.contract | Float | Đơn giá giờ lớp đặc biệt |
| `x_standard_threshold` | hr.contract | Float | Ngưỡng giờ chuẩn/tháng |
| `x_extra_rate` | hr.contract | Float | Đơn giá vượt ngưỡng |
| `x_fixed_base` | hr.contract | Float | Lương cố định (nếu có) |
| `x_has_fixed_base` | hr.contract | Boolean | Cờ bật/tắt FIXED_BASE |
