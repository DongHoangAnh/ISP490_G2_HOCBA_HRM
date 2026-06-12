# **FS — FUNC-PR-007**
# **Lương Tháng 13 & Thưởng Tết Với Pro-rata**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-007 |
| **Function Name** | Lương Tháng 13 & Thưởng Tết Với Pro-rata Theo Năm |
| **Custom Module** | `hb_payroll_13th_month` |
| **GAP Reference** | CUS-PR-007 (Chapter 4) |
| **Phase** | Phase 2 — **PHẢI XONG TRƯỚC TẾT** |
| **Độ phức tạp** | Trung bình |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS thưởng tháng 13 | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này **tự động tính lương tháng 13 (thưởng Tết)** cho toàn bộ nhân viên Học Bá với logic **pro-rate theo số tháng làm việc thực tế trong năm**. Đây là chính sách thưởng phổ biến tại Việt Nam — NV làm đủ 12 tháng nhận 100%, NV vào giữa năm nhận theo tỷ lệ tháng đã làm.

Function xử lý các tình huống đặc thù tại Học Bá:

- **NV mới vào giữa năm**: VD vào tháng 5 → nhận 8/12 tháng
- **NV nghỉ giữa năm**: VD nghỉ tháng 8 → nhận 8/12 tháng (theo policy "có làm tới Tết mới được nhận" thì 0%)
- **NV chuyển từ thử việc lên chính thức**: tính theo tháng chính thức (thử việc không tính, hoặc tính 0.5 — config được)
- **NV ngắt quãng** (nghỉ rồi quay lại): tính tổng các đoạn làm trong năm
- **NV part-time / CTV**: chính sách riêng (thường KHÔNG được hưởng — config được)

Cuối cùng, payslip thưởng tháng 13 phải được **include vào tính thuế TNCN của tháng 12** (không tính riêng biệt) theo quy định VN. Function sẽ tạo `hr.payslip` riêng với salary structure `BONUS_13TH` để tracking dễ, đồng thời flag để quyết toán năm (FUNC-PR-006) tổng hợp đúng.

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-05** Tính tay 13th-month cho 50+ NV | Wizard 1 click cho toàn công ty |
| **PP-PR-02** Logic phức tạp theo từng nhóm NV | Cấu hình riêng theo loại (Office/Teacher/CTV) |
| **PP-PR-03** Xử lý thuế phức tạp | Auto-include vào TN tính thuế tháng 12 |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Payroll** | Tạo payslip mới với salary structure `BONUS_13TH` |
| **Module Employee** | Đọc danh sách NV, contract history (start_date, end_date) |
| **Module Time Off** | Xử lý các tháng NV nghỉ không lương (tùy policy có pro-rate không) |
| **Chapter 5 (5.4.1)** | Sử dụng cấu trúc lương BONUS_13TH (mới) |
| **FUNC-PR-006** | Quyết toán năm sẽ include bonus payslip này |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **HR Manager** | Cấu hình policy + trigger wizard (`SEC-PR-03`) |
| **HR Officer** | Review preview, không trigger được (`SEC-PR-01/02`) |
| **BGĐ** | Approve danh sách thưởng tháng 13 (`SEC-PR-05`) |

---

## **FUNCTION FLOW**

```
┌──────────────────────────────────────────────────────────────┐
│  PRE: Cuối năm âm lịch / dương lịch                          │
│       BGĐ quyết định mức thưởng tháng 13                     │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
       ┌──────────────────────────────────────┐
       │ HR Manager mở wizard:                 │
       │ "Tạo Thưởng Tháng 13 Năm {year}"     │
       └────────────────┬─────────────────────┘
                        ▼
       ┌──────────────────────────────────────┐
       │ Wizard Setup:                         │
       │ - Năm tính (2026)                     │
       │ - Loại lịch: Dương / Âm               │
       │ - Tháng trả: tháng 12 / Tết / khác    │
       │ - Tỷ lệ mặc định: 100% lương cơ bản   │
       │ - Policy:                              │
       │   • NV nghỉ trước Tết: 0% / pro-rate  │
       │   • Thử việc: 0% / 50% / 100%         │
       │   • CTV: 0% / có nhận                 │
       └────────────────┬─────────────────────┘
                        ▼
       ┌──────────────────────────────────────┐
       │ Wizard Generate Preview:              │
       │ Hệ thống tính cho từng NV:            │
       │ - Months worked (1-12)                │
       │ - Pro-rate factor                     │
       │ - Bonus amount = base × factor        │
       └────────────────┬─────────────────────┘
                        ▼
       ┌──────────────────────────────────────┐
       │ HR Review List:                       │
       │ - Sort by department                  │
       │ - Highlight pro-rate < 100%           │
       │ - Có thể adjust manual (per NV)       │
       │ - Tổng tiền + impact ngân sách        │
       └────────────────┬─────────────────────┘
                        ▼
              ┌──────────────────────┐
              │ Gửi BGĐ duyệt?       │
              └────┬─────────────┬───┘
                   │ No           │ Yes
                   ▼              ▼
       ┌──────────────────┐  ┌──────────────────────┐
       │ HR Manager       │  │ Send to BGĐ          │
       │ self-approve     │  │ Email notification    │
       │ (nếu < threshold)│  │ Wait approval         │
       └────────┬─────────┘  └──────────┬───────────┘
                ▼                       ▼
                └───────────┬───────────┘
                            ▼
              ┌────────────────────────┐
              │ Approved → Generate     │
              │ Bonus Payslips         │
              │ - Salary Struct: BONUS_13TH│
              │ - 1 payslip / NV       │
              │ - Date: payment_date   │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ Compute Sheet auto:    │
              │ - BONUS_GROSS = amount │
              │ - PIT tính ngay        │
              │   (vì include trong TN │
              │   tháng 12)            │
              │ - NET = Gross - PIT    │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ Bonus Payslips state:  │
              │ Done → bao gồm trong:  │
              │ - FUNC-PR-003 Bank File │
              │ - FUNC-PR-006 Year-end  │
              │ - Accounting move      │
              └────────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: 13th-month Bonus Menu

**Vị trí**: Payroll → Year-End → 13th-Month Bonus

```
┌──────────────────────────────────────────────────────────────────┐
│  Thưởng Tháng 13 / Tết                          [+ Tạo Mới]      │
├──────────────────────────────────────────────────────────────────┤
│  Năm  │ Loại lịch │ Số NV │ Tổng thưởng    │ Trạng thái          │
│  ─────┼───────────┼───────┼────────────────┼─────────────────── │
│  2026 │ Tết Âm    │  64   │ 1,580,000,000  │ ✅ Approved & Done │
│  2025 │ Tết Âm    │  60   │ 1,420,000,000  │ ✅ Approved & Done │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Create 13th-Month Wizard — Step 1: Setup Policy

```
┌──────────────────────────────────────────────────────────────────┐
│  Tạo Thưởng Tháng 13 — Step 1/3: Cấu hình Policy          [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Năm tính (*)              : [2026 ▼]                            │
│  Loại lịch (*)             : ○ Dương lịch (T12/2026)              │
│                              ● Âm lịch (Tết 2027 — payment T1/2027)│
│                                                                    │
│  Ngày trả thưởng (*)       : [25/01/2027 📅]                     │
│                                                                    │
│  ┌─── Mức thưởng cơ bản ───────────────────────────────────────┐ │
│  │  Cơ sở tính: ● Lương cơ bản (BASE) tháng gần nhất            │ │
│  │              ○ Lương Gross trung bình 12 tháng                │ │
│  │              ○ Số tiền cố định: [___________] VND             │ │
│  │                                                                 │ │
│  │  Tỷ lệ (cho NV làm đủ năm): [100] %                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─── Pro-rate Policy ─────────────────────────────────────────┐ │
│  │  NV vào giữa năm:                                              │ │
│  │    ● Pro-rate theo tháng làm (months_worked / 12)             │ │
│  │    ○ Phải làm đủ 12 tháng mới nhận                            │ │
│  │    ○ Tỷ lệ tuỳ chỉnh: [_____] (nếu làm >= [_] tháng)         │ │
│  │                                                                 │ │
│  │  NV nghỉ trước ngày trả thưởng:                                │ │
│  │    ○ Không nhận (chính sách phổ biến)                         │ │
│  │    ● Pro-rate theo tháng đã làm                               │ │
│  │    ○ Nhận đủ                                                  │ │
│  │                                                                 │ │
│  │  Thời gian thử việc:                                           │ │
│  │    ○ Không tính (0)                                            │ │
│  │    ● Tính 50%                                                  │ │
│  │    ○ Tính 100%                                                │ │
│  │                                                                 │ │
│  │  Tháng có nghỉ không lương:                                    │ │
│  │    ☑ Trừ pro-rate (nếu nghỉ >= 15 ngày/tháng → coi như 0)     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─── Phạm vi NV ──────────────────────────────────────────────┐ │
│  │  ☑ Office Staff (Khối Văn phòng)                             │ │
│  │  ☑ Teachers & Tutors (Khối Giáo viên)                        │ │
│  │  ☐ Collaborators (CTV) — thường không có 13th-month          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  [Hủy]                                          [Tiếp theo →]     │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 3: Wizard Step 2 — Preview & Adjustment

```
┌────────────────────────────────────────────────────────────────────┐
│  Tạo Thưởng Tháng 13 — Step 2/3: Preview & Điều chỉnh        [×]   │
├────────────────────────────────────────────────────────────────────┤
│  Tổng NV: 64 | Tổng thưởng dự kiến: 1,580,000,000 VND              │
│  Filter: [Tất cả ▼] [Pro-rate < 100% ▼]                            │
├────────────────────────────────────────────────────────────────────┤
│ STT │ NV         │ Loại     │ Tháng │ Cơ sở   │ Pro-rate│ Thưởng  │
│ ────┼────────────┼──────────┼───────┼─────────┼─────────┼──────── │
│  1  │ Nguyễn A   │ Office   │ 12/12 │  20.0tr │ 100%    │  20.0tr │
│  2  │ Trần B     │ Teacher  │  8/12 │  18.0tr │  66.7%  │  12.0tr │
│  3  │ Lê C       │ Office   │ 12/12 │  25.0tr │ 100%    │  25.0tr │
│  4  │ Phạm D     │ Teacher  │  3/12 │  18.0tr │  25.0%  │   4.5tr │
│     │            │ (thử việc)│      │         │ (×50%)  │  2.25tr │
│ ... │            │          │       │         │         │         │
│ 64  │ Wang Z     │ Teacher  │  5/12 │  22.0tr │  41.7%  │   9.2tr │
├────────────────────────────────────────────────────────────────────┤
│  ⚠ Cảnh báo:                                                        │
│  - 3 NV đã nghỉ trước ngày trả (đã loại theo policy)                │
│  - 5 NV pro-rate < 50% — cần review                                 │
│  - Có thể manual adjust mức thưởng từng NV bằng cách click vào dòng│
│                                                                       │
│  [← Quay lại]                       [Tiếp theo: Gửi duyệt →]        │
└────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Wizard Step 3 — Approval & Submit

```
┌──────────────────────────────────────────────────────────────────┐
│  Tạo Thưởng Tháng 13 — Step 3/3: Phê duyệt                 [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Tổng kết:                                                         │
│  - Tổng số NV được nhận: 61 (loại 3 NV đã nghỉ)                  │
│  - Tổng tiền thưởng:    1,580,000,000 VND                        │
│  - Tổng PIT dự kiến:      189,600,000 VND (12%)                  │
│  - Tổng Net dự kiến:    1,390,400,000 VND                        │
│  - Impact ngân sách Tết: ~1.58 tỷ                                 │
│                                                                    │
│  ⚠ Mức tổng > 1 tỷ → cần BGĐ approve                              │
│                                                                    │
│  Bước phê duyệt:                                                   │
│  ○ HR Manager tự duyệt (chỉ áp dụng nếu < 1 tỷ)                   │
│  ● Gửi BGĐ duyệt qua workflow                                     │
│                                                                    │
│  Ghi chú gửi BGĐ:                                                  │
│  [Thưởng Tết Âm 2027 theo policy đã được BGĐ thống nhất tại    ]  │
│  [cuộc họp ngày 15/12/2026                                       ]  │
│                                                                    │
│  ☑ Tôi xác nhận đã review toàn bộ danh sách                        │
│  ☑ Tôi đồng ý với policy đã chọn                                   │
│                                                                    │
│  [← Quay lại]                          [Submit → Chờ duyệt]        │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 5: BGĐ Approval Screen

**Vị trí**: Email link → trỏ vào Bonus Run record

```
┌──────────────────────────────────────────────────────────────────┐
│  Phê duyệt: Thưởng Tháng 13 Năm 2026 — Tết 2027                  │
├──────────────────────────────────────────────────────────────────┤
│  Trình bởi: HR Manager - Hằng                                      │
│  Ngày trình: 18/01/2027                                            │
│                                                                    │
│  ┌─── Tổng quan ───────────────────────────────────────────────┐ │
│  │  Tổng NV: 61                                                  │ │
│  │  Tổng thưởng: 1,580,000,000 VND                              │ │
│  │  So với năm 2025 (1.42 tỷ): +11.3%                            │ │
│  │  Phân bố:                                                     │ │
│  │  - Office: 22 NV — 540tr                                      │ │
│  │  - Teacher: 39 NV — 1,040tr                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  [Xem chi tiết từng NV]                                            │
│                                                                    │
│  Quyết định:                                                       │
│  ○ Duyệt                                                          │
│  ○ Duyệt với điều chỉnh (mức tối đa: [_____] VND)                 │
│  ○ Từ chối                                                        │
│                                                                    │
│  Ghi chú/Lý do:                                                    │
│  [______________________________________________________]        │
│                                                                    │
│  [Submit Quyết định]                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Required | Mô tả |
|---|---|---|---|---|
| 1 | `fiscal_year` | wizard | Yes | Năm tính (2026) |
| 2 | `calendar_type` | wizard | Yes | solar / lunar |
| 3 | `payment_date` | wizard | Yes | Ngày trả thưởng |
| 4 | `base_method` | wizard | Yes | basic_salary / avg_gross / fixed |
| 5 | `bonus_rate` | wizard | Yes | Default 100% |
| 6 | `prorate_policy_new_hire` | wizard | Yes | full_prorate / require_full_year / custom |
| 7 | `prorate_policy_left_employee` | wizard | Yes | no_bonus / prorate / full |
| 8 | `probation_treatment` | wizard | Yes | 0 / 50 / 100 |
| 9 | `unpaid_leave_treatment` | wizard | Yes | deduct / ignore |
| 10 | `eligible_employee_types` | wizard | Yes | Multi-select |
| 11 | NV contracts trong năm | `hr.contract` | - | Để tính months_worked |
| 12 | NV payslips trong năm | `hr.payslip` | - | Để lấy base salary + leave |

### Bảng Output Data

| No | Output | Mô tả |
|---|---|---|
| 1 | Bonus Run record | `hb.13th.month.run` master record |
| 2 | Bonus Run lines | Per-employee detail trong `hb.13th.month.line` |
| 3 | Bonus Payslips | Tạo `hr.payslip` với struct = BONUS_13TH |
| 4 | Workflow record | Approval workflow (HR → BGĐ) |
| 5 | Email notifications | Gửi NV thông báo nhận thưởng |
| 6 | Accounting moves | Auto-post khi payslip Done |

### Pseudo-code

```
FUNCTION compute_13th_month_bonus(wizard):
    
    fiscal_year = wizard.fiscal_year
    year_start = DATE(fiscal_year, 1, 1)
    year_end = DATE(fiscal_year, 12, 31)
    payment_date = wizard.payment_date
    
    # ── Step 1: Get eligible employees ──────────────────────
    employees = SEARCH hr.employee
        WHERE employee_type IN wizard.eligible_employee_types
          AND (active = True OR (
              -- NV đã nghỉ nhưng tuỳ policy có nhận hay không
              departure_date BETWEEN year_start AND year_end
              AND wizard.prorate_policy_left_employee != 'no_bonus'
          ))
    
    bonus_lines = []
    
    FOR emp IN employees:
        # ── Step 2: Detect months_worked ────────────────────
        # Get all contracts of this emp in fiscal_year
        contracts = SEARCH hr.contract
            WHERE employee_id = emp.id
              AND (date_start <= year_end AND (date_end IS NULL OR date_end >= year_start))
        
        IF NOT contracts:
            CONTINUE  # NV không có contract trong năm
        
        # Calculate actual months worked
        months_worked = 0
        probation_months = 0
        official_months = 0
        unpaid_leave_months = []
        
        FOR month IN range(1, 13):  # 1 to 12
            month_start = DATE(fiscal_year, month, 1)
            month_end = LAST_DAY_OF_MONTH(month_start)
            
            # Check if any contract active in this month
            active_in_month = ANY(c FOR c IN contracts
                                  IF c.date_start <= month_end
                                  AND (c.date_end IS NULL OR c.date_end >= month_start))
            
            IF NOT active_in_month:
                CONTINUE
            
            # Check if probation in this month
            is_probation_this_month = ANY(c.is_probation FOR c IN contracts 
                                          IF c.date_start <= month_end 
                                          AND (c.date_end IS NULL OR c.date_end >= month_start))
            
            # Check unpaid leave > 15 days in this month
            payslip_this_month = SEARCH hr.payslip
                WHERE employee_id = emp.id
                  AND date_from <= month_end
                  AND date_to >= month_start
            
            unpaid_leave_days = SUM(
                we.duration FOR we IN payslip_this_month.work_entries
                IF we.work_entry_type.code == 'LEAVE120'  # unpaid leave
            )
            
            IF unpaid_leave_days >= 15 AND wizard.unpaid_leave_treatment == 'deduct':
                unpaid_leave_months.append(month)
                CONTINUE  # skip month
            
            # Count this month
            months_worked += 1
            IF is_probation_this_month:
                probation_months += 1
            ELSE:
                official_months += 1
        
        # ── Step 3: Calculate base salary ────────────────────
        IF wizard.base_method == 'basic_salary':
            # Get BASE từ payslip tháng gần nhất
            latest_payslip = SEARCH hr.payslip
                WHERE employee_id = emp.id
                  AND state = 'done'
                  AND date_to <= year_end
                ORDER BY date_to DESC LIMIT 1
            base_salary = latest_payslip.line('BASE').amount
        
        ELSE IF wizard.base_method == 'avg_gross':
            # Trung bình Gross 12 tháng
            year_payslips = SEARCH hr.payslip
                WHERE employee_id = emp.id
                  AND state = 'done'
                  AND date_to BETWEEN year_start AND year_end
            
            base_salary = AVG(p.gross_amount FOR p IN year_payslips)
        
        ELSE:  # 'fixed'
            base_salary = wizard.fixed_amount
        
        # ── Step 4: Apply pro-rate ───────────────────────────
        # Effective months = official + probation × probation_factor
        probation_factor = wizard.probation_treatment / 100  # 0 / 0.5 / 1
        effective_months = official_months + probation_months × probation_factor
        
        # Check eligibility
        IF wizard.prorate_policy_new_hire == 'require_full_year' AND months_worked < 12:
            bonus_amount = 0
            eligibility_reason = "Không đủ điều kiện (chưa làm đủ 12 tháng)"
        
        ELSE IF emp.departure_date AND emp.departure_date < payment_date 
                 AND wizard.prorate_policy_left_employee == 'no_bonus':
            bonus_amount = 0
            eligibility_reason = "Đã nghỉ trước ngày trả thưởng"
        
        ELSE:
            # Standard pro-rate
            prorate_factor = effective_months / 12
            bonus_amount = base_salary × wizard.bonus_rate / 100 × prorate_factor
            eligibility_reason = "OK"
        
        # ── Step 5: Round + Apply manual adjustment (if any) ─
        bonus_amount = ROUND_DOWN(bonus_amount, 1000)  # round to 1000 VND
        
        # If HR manually adjusted this NV in Step 2 of wizard
        IF emp.id IN wizard.manual_adjustments:
            bonus_amount = wizard.manual_adjustments[emp.id]
            manual_note = wizard.manual_adjustment_notes[emp.id]
        
        bonus_lines.append({
            'employee': emp,
            'base_salary': base_salary,
            'months_worked': months_worked,
            'official_months': official_months,
            'probation_months': probation_months,
            'unpaid_leave_months': unpaid_leave_months,
            'prorate_factor': prorate_factor IF bonus_amount > 0 ELSE 0,
            'bonus_amount': bonus_amount,
            'eligibility_reason': eligibility_reason,
            'manual_adjusted': (emp.id IN wizard.manual_adjustments),
        })
    
    # ── Step 6: Create Bonus Run record (draft) ──────────────
    bonus_run = CREATE hb.13th.month.run
        fiscal_year = fiscal_year
        calendar_type = wizard.calendar_type
        payment_date = payment_date
        total_employees = LEN([l FOR l IN bonus_lines IF l.bonus_amount > 0])
        total_amount = SUM(l.bonus_amount FOR l IN bonus_lines)
        policy_config = SERIALIZE(wizard)  # JSON
        state = 'draft'
        created_by = current_user
    
    FOR l IN bonus_lines:
        CREATE hb.13th.month.line
            run_id = bonus_run.id
            # ... all fields
    
    # ── Step 7: Approval Workflow ─────────────────────────────
    IF total_amount > APPROVAL_THRESHOLD or wizard.send_to_bod:
        # Trigger BGĐ approval workflow
        bonus_run.state = 'pending_bod_approval'
        send_email_to_bod(bonus_run)
    ELSE:
        # HR Manager self-approve
        bonus_run.state = 'approved'
        bonus_run.approved_by = current_user
    
    RETURN bonus_run


FUNCTION generate_bonus_payslips(bonus_run):
    # Called after approval
    
    payslip_batch = CREATE hr.payslip.run
        name = f"Thưởng tháng 13 - {bonus_run.fiscal_year}"
        date_start = bonus_run.payment_date
        date_end = bonus_run.payment_date
    
    FOR line IN bonus_run.line_ids:
        IF line.bonus_amount <= 0:
            CONTINUE
        
        payslip = CREATE hr.payslip
            employee_id = line.employee_id
            contract_id = line.employee.active_contract.id
            struct_id = STR_PR_BONUS_13TH  # Salary Structure đặc biệt
            payslip_run_id = payslip_batch.id
            date_from = bonus_run.payment_date
            date_to = bonus_run.payment_date
            state = 'draft'
        
        # Set BONUS_GROSS input
        CREATE hr.payslip.input
            payslip_id = payslip.id
            code = 'BONUS_13TH'
            amount = line.bonus_amount
            name = "Thưởng tháng 13"
        
        # Compute payslip — will apply BONUS_13TH + PIT
        payslip.compute_sheet()
        
        # Link bonus_line to payslip
        line.payslip_id = payslip.id
    
    bonus_run.state = 'done'
    bonus_run.payslip_batch_id = payslip_batch.id
    
    RETURN payslip_batch
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.13th.month.run`** (Master record)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "Thưởng T13 {year}" |
| `fiscal_year` | Integer | Yes | 2026 |
| `calendar_type` | Selection | Yes | solar / lunar |
| `payment_date` | Date | Yes | Ngày trả thưởng |
| `policy_config` | Text (JSON) | Yes | Snapshot toàn bộ policy đã chọn |
| `total_employees` | Integer | Yes | Số NV được nhận |
| `total_amount` | Monetary | Yes | Tổng tiền thưởng |
| `total_pit_estimate` | Monetary | No | PIT dự kiến |
| `state` | Selection | Yes | draft / pending_bod_approval / approved / rejected / generating / done / cancelled |
| `payslip_batch_id` | Many2one (hr.payslip.run) | No | Liên kết với batch payslip thưởng |
| `created_by`, `created_at` | (audit) | Yes | - |
| `approved_by`, `approved_at` | (audit) | No | BGĐ hoặc HR Manager |
| `bod_notes` | Text | No | Ghi chú từ BGĐ |
| `cancellation_reason` | Text | No | Nếu bị huỷ |

**2. Model `hb.13th.month.line`** (Per-employee detail)

| Field | Type | Required | Description |
|---|---|---|---|
| `run_id` | Many2one | Yes | - |
| `employee_id` | Many2one (hr.employee) | Yes | - |
| `employee_type` | Selection (snapshot) | Yes | office / teacher / collaborator |
| `base_salary` | Monetary | Yes | Cơ sở tính |
| `months_worked` | Integer | Yes | 0-12 |
| `official_months` | Integer | Yes | - |
| `probation_months` | Integer | Yes | - |
| `unpaid_leave_months` | Char | No | "8,11" — tháng có nghỉ |
| `prorate_factor` | Float | Yes | 0.0 - 1.0 |
| `bonus_amount_calculated` | Monetary | Yes | Tính tự động |
| `bonus_amount_final` | Monetary | Yes | Sau manual adjust |
| `manual_adjusted` | Boolean | Yes | Default False |
| `manual_adjustment_note` | Text | No | Lý do điều chỉnh |
| `eligibility_status` | Selection | Yes | eligible / not_eligible / left_before_payment |
| `eligibility_reason` | Text | No | - |
| `payslip_id` | Many2one (hr.payslip) | No | Sau khi generate |

**3. Salary Structure mới `STR_PR_BONUS_13TH`**

Salary Rules trong structure:
- **BONUS_13TH** (input from `hr.payslip.input`)
- **TAXABLE_INCOME_BONUS** = BONUS_13TH (toàn bộ thưởng tính thuế)
- **PIT_BONUS** = áp biểu lũy tiến 7 bậc trên tổng (TN_tháng_12 + BONUS) - PIT_tháng_12_đã_tính
- **NET_BONUS** = BONUS_13TH - PIT_BONUS

(Lưu ý: Logic này phức tạp vì PIT của thưởng cần tính chung với TN tháng 12 — sẽ làm chi tiết ở Implementation)

---

## **VALIDATION RULES**

| No | Rule | Action |
|---|---|---|
| **VR-001** | Tổng amount > 1 tỷ → bắt buộc BGĐ approve | Auto-route workflow |
| **VR-002** | `fiscal_year` không vượt năm hiện tại | Block |
| **VR-003** | `payment_date` không trong quá khứ > 30 ngày | Warning |
| **VR-004** | Mọi NV trong scope phải có active contract | Skip NV không có |
| **VR-005** | Không tạo lại Bonus Run nếu năm đó đã `done` | Block (cần cancel cũ trước) |
| **VR-006** | Manual adjustment phải <= 200% mức tính tự động | Warning + cần lý do |
| **VR-007** | Manual adjustment <= 0 cần lý do bắt buộc | Block nếu không có |
| **VR-008** | BGĐ approval cần ít nhất 1 person trong role `SEC-PR-05` | Workflow |
| **VR-009** | Sau khi `done`, không sửa được bonus_amount | Read-only sau Done |
| **VR-010** | Bonus payslip phải compute đồng thời với PIT tháng 12 | Logic constraint |

---

## **EXCEPTION FLOW**

### EX-001: NV không có contract trong năm
- Skip với log "Không có contract — không tính"
- Hiển thị trong "Skipped Employees" tab

### EX-002: NV nghỉ giữa năm với policy "no_bonus"
- `bonus_amount = 0`, `eligibility_status = 'left_before_payment'`
- Vẫn hiển thị trong danh sách (transparency)

### EX-003: NV có residence change → tax tricky
- Detect tự động
- Apply tax theo phần đang resident
- Log warning

### EX-004: BGĐ từ chối
- `state = 'rejected'`
- Email notify HR Manager
- HR có thể tạo lại với policy điều chỉnh

### EX-005: Lỗi khi generate payslips (NV thiếu contract / structure không có)
- Rollback bonus_run state về `approved`
- Hiển thị lỗi chi tiết
- Cho phép retry sau khi sửa

### EX-006: HR muốn cancel sau khi đã generate payslips
- Yêu cầu xác nhận: "Sẽ huỷ {N} payslips đã tạo"
- Chỉ HR Manager có quyền
- Bắt buộc nhập lý do
- Audit log đầy đủ

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-064** | Pro-rate theo months_worked / 12 | Logic chuẩn nhất |
| **BR-PR-065** | Probation months được tính với factor cấu hình | Default 50% |
| **BR-PR-066** | Tháng có unpaid leave >= 15 ngày → không tính | Theo policy phổ biến |
| **BR-PR-067** | NV đã nghỉ trước payment_date → tuỳ policy | Default: không nhận |
| **BR-PR-068** | Bonus tính thuế cùng tháng 12 (không tính riêng) | Theo Thông tư 111/2013/TT-BTC |
| **BR-PR-069** | CTV không được nhận 13th-month (default) | Có thể bật nếu có policy đặc biệt |
| **BR-PR-070** | Manual adjustment cần lý do nếu vượt 200% hoặc giảm về 0 | Audit + transparency |
| **BR-PR-071** | Bonus Run trên 1 tỷ cần BGĐ approve | Threshold cấu hình được |
| **BR-PR-072** | Audit log đầy đủ mọi action | Tạo, sửa, approve, reject, cancel |
| **BR-PR-073** | Round down to 1000 VND | Tránh số lẻ |
| **BR-PR-074** | Khi NV ngắt quãng (nghỉ rồi quay lại) → tính tổng các đoạn | Tính chính xác |
| **BR-PR-075** | Bonus payslip dùng structure riêng STR_PR_BONUS_13TH | Tách biệt với payslip thường |
| **BR-PR-076** | Email notification cho mỗi NV nhận bonus | Trước ngày trả 3-5 ngày |
| **BR-PR-077** | Include bonus payslip vào FUNC-PR-006 quyết toán năm | Tính đúng tổng TN năm |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| `hb.13th.month.run` record | Master tracking |
| `hb.13th.month.line` records | Per-employee detail |
| Bonus Payslips (`hr.payslip` với struct BONUS_13TH) | 1 payslip / NV |
| Payslip Batch riêng cho bonus | Để generate bank file riêng (FUNC-PR-003) |
| Approval workflow | HR → BGĐ → Done |
| Email notifications | Cho NV biết được nhận bao nhiêu |
| Accounting moves | Tự post khi Done |
| Dashboard YoY comparison | So sánh với năm trước |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-007-01** | Wireframe Bonus Run List | Danh sách qua các năm |
| **UI-PR-007-02** | Wireframe Wizard Step 1 (Policy) | Setup policy |
| **UI-PR-007-03** | Wireframe Wizard Step 2 (Preview) | Review per-NV |
| **UI-PR-007-04** | Wireframe Wizard Step 3 (Approval) | Submit to BGĐ |
| **UI-PR-007-05** | Wireframe BGĐ Approval Email | Email + link |
| **UI-PR-007-06** | Wireframe BGĐ Approval Screen | Approve/Reject UI |
| **UI-PR-007-07** | Wireframe Bonus Payslip | Payslip riêng cho bonus |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-007-001** | VN | Đã có Bonus Run năm {year}. Vui lòng cancel cũ trước. | On Duplicate |
| **MSG-PR-007-002** | VN | Tổng thưởng {amount} VND vượt ngưỡng 1 tỷ — cần BGĐ approve | On Submit |
| **MSG-PR-007-003** | VN | Đã gửi BGĐ duyệt — chờ phản hồi qua email | On Submit (workflow) |
| **MSG-PR-007-004** | VN | BGĐ đã duyệt — bạn có thể generate payslips ngay | On BGĐ Approve |
| **MSG-PR-007-005** | VN | BGĐ từ chối với lý do: {reason}. Vui lòng điều chỉnh và submit lại. | On BGĐ Reject |
| **MSG-PR-007-006** | VN | NV {name} đã nghỉ trước ngày trả thưởng — đã loại theo policy | On Build Line (info) |
| **MSG-PR-007-007** | VN | NV {name} chỉ làm {N} tháng — pro-rate {factor}% | On Build Line (info) |
| **MSG-PR-007-008** | VN | NV {name} có nghỉ không lương >= 15 ngày trong tháng {month} — đã skip tháng đó | On Build Line (info) |
| **MSG-PR-007-009** | VN | Manual adjustment cho NV {name}: {original} → {adjusted}. Lý do: {reason} | On Manual Adjust |
| **MSG-PR-007-010** | VN | Manual adjustment vượt 200% — cần HR Manager phê duyệt riêng | On Manual Adjust (warning) |
| **MSG-PR-007-011** | VN | Đã tạo thành công {N} bonus payslips trong batch {batch_ref} | On Generate Success |
| **MSG-PR-007-012** | VN | Lỗi generate payslip cho {name}: {error}. Rollback tự động. | On Generate Error |
| **MSG-PR-007-013** | VN | Đã gửi email thông báo cho {N} NV | On Send Notifications |
| **MSG-PR-007-014** | VN | Cancel bonus run này sẽ huỷ {N} payslips đã tạo. Bạn có chắc? | On Cancel (confirm) |
| **MSG-PR-007-015** | VN | Bonus của bạn năm {year}: {amount} VND (đã trừ thuế). Sẽ chuyển khoản vào {date}. | Email to Employee |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | Salary Structure `STR_PR_BONUS_13TH` đã cấu hình | Chapter 5.4.1 (cần extend) |
| 2 | Hầu hết Payslip Batches trong năm đã Done | Module Payroll |
| 3 | NV có active contract hoặc đã có contract trong năm | Module Employee |
| 4 | Policy threshold cho BGĐ approval đã cấu hình | Function này |
| 5 | Module `hb_payroll_13th_month` đã cài | Function này |
| 6 | (Nếu áp dụng) Time Off module hoạt động để check unpaid leave | Module Time Off |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | `hb.13th.month.run` ở state `done` |
| 2 | `hb.13th.month.line` records cho từng NV |
| 3 | Bonus payslips (`hr.payslip`) tạo và `state = done` |
| 4 | Payslip Batch riêng cho bonus được link |
| 5 | Email notifications gửi đến từng NV |
| 6 | Accounting moves auto-post |
| 7 | Sẵn sàng include vào Year-End PIT (FUNC-PR-006) |
| 8 | Audit log đầy đủ |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Year-End Menu → "Tạo Thưởng Tháng 13" | HR Manager (`SEC-PR-03`) |
| 2 | CRON auto-remind tháng 12: "Đã đến lúc tính thưởng Tết" | Hệ thống |
| 3 | BGĐ workflow trigger sau khi HR submit | Hệ thống |
