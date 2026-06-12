# **FS — FUNC-PR-006**
# **Quyết Toán Thuế TNCN Cuối Năm (Mẫu 05/QTT-TNCN)**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-006 |
| **Function Name** | Quyết Toán Thuế TNCN Cuối Năm (Mẫu 05/QTT-TNCN) |
| **Custom Module** | `hb_payroll_year_end_pit` |
| **GAP Reference** | CUS-PR-006 (Chapter 4) |
| **Phase** | Phase 2 — **PHẢI XONG TRƯỚC THÁNG 12** |
| **Độ phức tạp** | Cao |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS quyết toán thuế cuối năm | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này **tự động tổng hợp 12 payslip hàng tháng** của mỗi nhân viên trong năm tài chính và sinh ra **Tờ khai Quyết toán Thuế TNCN (Mẫu 05/QTT-TNCN)** theo **Thông tư 80/2021/TT-BTC**. Function tính toán chính xác phần thuế cần khấu trừ thêm hoặc hoàn lại cho mỗi NV (settlement) — vốn hiện đang là cơn ác mộng cuối năm của HR (mất 3-5 ngày làm việc/tháng 1 để aggregate Excel thủ công).

Function này đặc biệt phức tạp vì phải xử lý:

- **NV vào giữa năm** (ví dụ vào tháng 5): chỉ tổng hợp từ tháng 5 → tháng 12
- **NV nghỉ giữa năm** (ví dụ nghỉ tháng 8): tổng hợp từ tháng 1 → tháng 8
- **NV vào và nghỉ giữa năm** (rare nhưng có): tổng hợp đoạn cụ thể
- **NV vừa cư trú vừa không cư trú trong năm** (chuyển status): phải tách rõ thuế phần nào
- **Thưởng tháng 13 / Tết**: include vào thu nhập cả năm theo BR-PR-032

Output là **Mẫu 05/QTT-TNCN** đúng định dạng eTax + phiếu quyết toán cá nhân cho từng NV (NV ký nhận = nghĩa vụ thuế đã hoàn thành).

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-09** Quyết toán cuối năm khó (3-5 ngày tay) | Tự động tổng hợp 12 payslips/NV → sinh báo cáo trong < 1 giờ |
| **PP-PR-04** Audit trail | Lưu vĩnh viễn settlement records |
| **PP-PR-03** Sai số khi tính tay | Dùng cùng salary rules đã tính → không có lỗi sao chép |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Payroll** | Đọc 12 payslips của mỗi NV trong năm tài chính |
| **Module Employee** | Đọc `x_pit_code`, `x_tax_residence_status`, lịch sử contract |
| **FUNC-PR-005** | Dùng cùng cấu trúc cross-validation NPT |
| **FUNC-PR-007** | Include thưởng tháng 13 vào tính tổng năm |
| **Chapter 5 (5.4.3 + 5.4.4)** | Reference biểu thuế + giảm trừ năm |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **HR Manager** | Trigger quyết toán + finalize (`SEC-PR-03`) |
| **Finance** | Submit lên eTax, đánh dấu submitted (`SEC-PR-04`) |
| **NV cá nhân** | Xem phiếu quyết toán của chính mình qua Portal |

---

## **FUNCTION FLOW**

```
┌─────────────────────────────────────────────────────────────┐
│  PRE: 12 Payslip Batches của năm đã ở state 'done'         │
│       + (optional) thưởng tháng 13 đã tính (FUNC-PR-007)    │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
       ┌──────────────────────────────────────┐
       │ HR Manager vào menu Year-End PIT     │
       │ Bấm "Quyết Toán Năm {N}"             │
       └────────────────┬─────────────────────┘
                        ▼
       ┌──────────────────────────────────────┐
       │ Wizard:                               │
       │ - Năm quyết toán (VD: 2026)           │
       │ - Filter NV (all/department/specific) │
       │ - Bao gồm thưởng tháng 13?            │
       │ - Loại tờ khai: chính thức/bổ sung    │
       └────────────────┬─────────────────────┘
                        ▼
       ┌──────────────────────────────────────┐
       │ Validate Pre-conditions:              │
       │ - Tất cả Payslip Batches T1-T12 done? │
       │ - eTax monthly reports (FUNC-PR-005)  │
       │   12 tháng đã submitted?              │
       └────┬──────────────────┬───────────────┘
            │ No                │ Yes
            ▼                   ▼
   ┌─────────────────┐  ┌──────────────────────────┐
   │ Block + list    │  │ Aggregate Engine          │
   │ những batch     │  │ - Loop từng NV:           │
   │ chưa done       │  │   • Sum 12 monthly        │
   └─────────────────┘  │   • Add 13th month bonus  │
                        │   • Compute annual PIT    │
                        │   • Compute settlement    │
                        │     (over/under-paid)     │
                        └──────────┬───────────────┘
                                   ▼
                        ┌────────────────────────┐
                        │ For NV vào/nghỉ giữa    │
                        │ năm:                     │
                        │ - Detect change dates    │
                        │ - Pro-rate deductions    │
                        │ - Handle residence change│
                        └──────────┬───────────────┘
                                   ▼
                        ┌────────────────────────┐
                        │ Cross-Validation        │
                        │ - Sum monthly PIT       │
                        │   khớp tổng PIT đã       │
                        │   khấu trừ trong năm     │
                        │ - List discrepancies     │
                        └──────────┬───────────────┘
                                   ▼
                        ┌────────────────────────┐
                        │ Build Mẫu 05/QTT-TNCN  │
                        │ - XML cho eTax         │
                        │ - PDF cho NV ký        │
                        └──────────┬───────────────┘
                                   ▼
                        ┌────────────────────────┐
                        │ Mỗi NV nhận:            │
                        │ - Phiếu quyết toán PDF  │
                        │   qua Employee Portal   │
                        │ - Email notification    │
                        └──────────┬───────────────┘
                                   ▼
                        ┌────────────────────────┐
                        │ Finance submit lên eTax │
                        │ Đánh dấu submitted +    │
                        │ ghi submission code     │
                        └────────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: Year-End PIT Menu

**Vị trí**: Payroll → Year-End → PIT Finalization (Quyết toán Thuế TNCN)

```
┌──────────────────────────────────────────────────────────────────┐
│  Quyết Toán Thuế TNCN Cuối Năm                  [+ Tạo Quyết Toán]│
├──────────────────────────────────────────────────────────────────┤
│  Năm  │ Số NV │ Tổng TN năm     │ Tổng PIT năm    │ Settlement   │
│  ─────┼───────┼────────────────┼─────────────────┼───────────  │
│  2026 │  68   │ 14,200,000,000 │  1,743,500,000  │ +12,3tr/-8tr │
│  2025 │  62   │ 12,800,000,000 │  1,520,100,000  │ +9,1tr/-5,8tr│
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Create Year-End PIT Wizard

```
┌──────────────────────────────────────────────────────────────────┐
│  Quyết Toán Thuế TNCN Năm 2026                              [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Năm tài chính (*)      : [2026 ▼]                               │
│                                                                    │
│  Phạm vi NV:                                                       │
│  ● Toàn bộ NV trong năm (68 người)                                │
│  ○ Theo phòng ban       : [Chọn... ▼]                            │
│  ○ Cá nhân cụ thể       : [Chọn NV... ▼]                         │
│                                                                    │
│  Bao gồm:                                                          │
│  ☑ Thu nhập từ payslip T1-T12                                     │
│  ☑ Thưởng tháng 13 / Tết (nếu đã tính ở FUNC-PR-007)              │
│  ☐ Thu nhập từ nguồn khác (NV tự kê khai)                         │
│                                                                    │
│  Loại tờ khai (*)       : ● Chính thức                            │
│                            ○ Bổ sung (nếu sửa cho năm đã quyết toán) │
│                                                                    │
│  Định dạng output (*)  : ● XML (cho eTax) + PDF cá nhân           │
│                          ○ Chỉ XLSX preview                       │
│                                                                    │
│  ⚠ Trước khi tạo:                                                  │
│  - Đảm bảo 12 Payslip Batches đã Done                             │
│  - Đảm bảo 12 eTax monthly reports đã Submitted                    │
│  - (Nếu có) Thưởng tháng 13 đã được approved                       │
│                                                                    │
│  [Hủy]                                  [Sinh Quyết Toán Preview]  │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 3: Year-End PIT Detail (Preview)

```
┌────────────────────────────────────────────────────────────────────┐
│  Quyết Toán TNCN Năm 2026 — Draft                            [×]   │
├────────────────────────────────────────────────────────────────────┤
│  ┌─── Tổng quan ──────────────────────────────────────────────┐   │
│  │  Đơn vị: TT Tiếng Trung Học Bá Education                    │   │
│  │  MST: 0123456789                                              │   │
│  │  Năm: 2026                                                    │   │
│  │  Tổng NV trong năm: 68                                        │   │
│  │  - NV làm đủ 12 tháng: 56                                    │   │
│  │  - NV vào giữa năm: 8                                        │   │
│  │  - NV nghỉ giữa năm: 4                                       │   │
│  │  Tổng TN cả năm: 14,200,000,000 VND                          │   │
│  │  Tổng PIT đã khấu trừ: 1,743,500,000 VND                     │   │
│  │  Tổng PIT phải nộp (tính lại): 1,747,800,000 VND             │   │
│  │  Chênh lệch tổng: +4,300,000 (nộp thêm)                      │   │
│  │  - Cá nhân nộp thêm: 32 NV - tổng 12,300,000                 │   │
│  │  - Cá nhân hoàn lại: 14 NV - tổng 8,000,000                  │   │
│  │  - Cân bằng: 22 NV (không chênh)                             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─── Chi tiết theo NV ────────────────────────────────────────┐   │
│  │ STT │ NV          │ Tháng làm │ TN năm   │ PIT khấu│ PIT năm│ Chênh│
│  │ ────┼────────────┼───────────┼──────────┼─────────┼────────┼──── │
│  │  1  │ Nguyễn A   │  12/12    │ 240tr    │ 28.5tr  │ 28.5tr │  0  │
│  │  2  │ Trần B     │   8/12 *  │ 152tr    │ 16.8tr  │ 17.2tr │+400k│
│  │  3  │ Lê C       │  12/12    │ 320tr    │ 42.3tr  │ 40.9tr │-1.4tr│
│  │ ... │            │            │          │         │        │     │
│  │ 68  │ Phạm Z     │  12/12    │ 180tr    │ 18.5tr  │ 18.5tr │  0  │
│  └─────────────────────────────────────────────────────────────────┘   │
│   * NV vào/nghỉ giữa năm                                              │
│                                                                       │
│  ⚠ Cross-Validation:                                                  │
│  - 2 NV thiếu MST → đã skip                                          │
│  - 3 NV có discrepancy giảm trừ NPT → đã ghi chú                     │
│  - PIT monthly aggregate khớp với 12 báo cáo eTax monthly ✅          │
│                                                                       │
│  [Quay lại] [Export XML eTax] [Gửi PDF cho NV] [Đánh dấu nộp]        │
└────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Individual Settlement Detail

**Vị trí**: Click vào dòng NV trong Screen 3

```
┌────────────────────────────────────────────────────────────────────┐
│  Phiếu Quyết Toán: Trần Văn B (E-2026-015) — Năm 2026         [×]  │
├────────────────────────────────────────────────────────────────────┤
│  Thông tin cá nhân:                                                  │
│  - MST: 8123456790                                                   │
│  - CCCD: 0012345678901                                               │
│  - Trạng thái: Cư trú toàn năm                                       │
│  - Thời gian làm tại Cty: 01/05/2026 - 31/12/2026 (8 tháng)         │
│                                                                       │
│  ┌─── Thu nhập từng tháng ──────────────────────────────────────┐  │
│  │ Tháng │ TN chịu thuế │ Giảm trừ │ TN tính thuế │ PIT khấu trừ│  │
│  │ ──────┼─────────────┼──────────┼─────────────┼──────────── │  │
│  │  T5   │  18,000,000 │ 11,000,000│   7,000,000 │     350,000 │  │
│  │  T6   │  19,500,000 │ 11,000,000│   8,500,000 │     475,000 │  │
│  │  T7   │  19,500,000 │ 11,000,000│   8,500,000 │     475,000 │  │
│  │  ...  │             │           │             │             │  │
│  │  T12  │  21,000,000 │ 15,400,000│   5,600,000 │     280,000 │  │
│  │  +T13 │  19,500,000 │      -    │  19,500,000 │   2,925,000 │  │
│  │ ──────┼─────────────┼──────────┼─────────────┼──────────── │  │
│  │ Tổng  │ 175,000,000 │ 88,000,000│  87,000,000 │  16,800,000 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─── Tính lại theo năm ────────────────────────────────────────┐  │
│  │  Tổng TN chịu thuế năm     : 175,000,000 VND                   │  │
│  │  Giảm trừ bản thân (8 tháng × 11tr)  : -88,000,000             │  │
│  │  Giảm trừ NPT (1 NPT × 8 × 4.4tr)    : -35,200,000             │  │
│  │  TN tính thuế năm           : 51,800,000 VND                   │  │
│  │                                                                  │  │
│  │  PIT năm (theo biểu lũy tiến 7 bậc) : 17,200,000 VND            │  │
│  │  PIT đã khấu trừ trong năm           : 16,800,000 VND           │  │
│  │  ─────────────────────────────────────────                      │  │
│  │  Settlement: NỘP THÊM                : +400,000 VND             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Trạng thái: Draft                                                    │
│  [Quay lại] [In Phiếu Quyết Toán PDF] [Gửi cho NV qua Portal]        │
└────────────────────────────────────────────────────────────────────┘
```

### Screen 5: Employee Portal — Individual View

**Vị trí**: Portal → My Payroll → Year-End Settlement 2026

```
┌──────────────────────────────────────────────────────────────────┐
│  Phiếu Quyết Toán Thuế TNCN Năm 2026                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Trần Văn B                                                        │
│  MST: 8123456790                                                   │
│  Phòng ban: Đào tạo                                                │
│                                                                    │
│  Tổng thu nhập năm: 175,000,000 VND                                │
│  PIT đã khấu trừ : 16,800,000 VND                                  │
│  PIT phải nộp     : 17,200,000 VND                                 │
│  ──────────────────────────────────────                            │
│  Bạn cần NỘP THÊM: 400,000 VND                                     │
│                                                                    │
│  Hạn nộp bổ sung: 30/04/2027                                       │
│  Hướng dẫn nộp: [Xem hướng dẫn]                                    │
│                                                                    │
│  [Tải PDF Phiếu Quyết Toán]   [Xác nhận đã đọc]                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Required | Mô tả |
|---|---|---|---|---|
| 1 | Năm tài chính | `wizard.fiscal_year` | Yes | VD: 2026 |
| 2 | Phạm vi NV | `wizard.scope` | Yes | all/department/specific |
| 3 | Loại tờ khai | `wizard.declaration_type` | Yes | official/supplementary |
| 4 | Include 13th-month | `wizard.include_13th_month` | Yes | True/False |
| 5 | Payslips 12 tháng | `hr.payslip` | Yes | state=done, date_from BETWEEN year_start AND year_end |
| 6 | 13th-month Payslip | `hr.payslip` | No | Nếu include và đã có |
| 7 | Active dependents trong năm | `hr.dependent` | Yes | với date_from <= year_end |
| 8 | NV info | `hr.employee` | Yes | x_pit_code, x_tax_residence_status, contract history |
| 9 | Contracts của NV trong năm | `hr.contract` | Yes | Để detect vào/nghỉ giữa năm |
| 10 | 12 eTax monthly reports | `hb.etax.report` | Yes | Đã submitted |

### Bảng Output Data

| No | Output | Định dạng |
|---|---|---|
| 1 | File XML | Mẫu 05/QTT-TNCN theo eTax schema |
| 2 | File PDF tổng (cho HR) | Toàn bộ NV trong 1 file |
| 3 | File PDF cá nhân (mỗi NV 1 file) | Phiếu quyết toán riêng |
| 4 | `hb.year.end.pit.report` record | Lưu vĩnh viễn |
| 5 | `hb.year.end.pit.line` records | Per-employee detail |
| 6 | Email notifications | Gửi qua Employee Portal |

### Pseudo-code

```
FUNCTION generate_year_end_pit(wizard):
    
    fiscal_year = wizard.fiscal_year
    year_start = DATE(fiscal_year, 1, 1)
    year_end = DATE(fiscal_year, 12, 31)
    
    # ── Step 1: Validate Pre-conditions ──────────────────────
    payslip_batches = SEARCH hr.payslip.run
        WHERE date_start BETWEEN year_start AND year_end
    
    incomplete_batches = [b FOR b IN payslip_batches IF b.state != 'done']
    IF incomplete_batches:
        RAISE ValidationError(f"Còn {LEN(incomplete_batches)} batch chưa Done")
    
    # ── Step 2: Get list of employees ────────────────────────
    employees = SEARCH hr.employee BASED ON wizard.scope
    
    # ── Step 3: For each employee, aggregate annual data ────
    settlement_lines = []
    
    FOR emp IN employees:
        # 3.1 Get all payslips of this employee in fiscal year
        emp_payslips = SEARCH hr.payslip
            WHERE employee_id = emp.id
              AND state = 'done'
              AND date_to BETWEEN year_start AND year_end
        
        IF NOT emp_payslips:
            CONTINUE  # NV không có payslip trong năm, skip
        
        # 3.2 Detect vào/nghỉ giữa năm
        first_payslip_month = MIN(p.date_to.month FOR p IN emp_payslips)
        last_payslip_month = MAX(p.date_to.month FOR p IN emp_payslips)
        months_worked = LEN(SET(p.date_to.month FOR p IN emp_payslips))
        
        # 3.3 Get contract history (detect residence status change)
        contracts = SEARCH hr.contract
            WHERE employee_id = emp.id
              AND (date_start <= year_end AND (date_end IS NULL OR date_end >= year_start))
        
        is_resident_full_year = ALL(c.x_tax_residence_status == 'resident' FOR c IN contracts)
        is_nonresident_full_year = ALL(c.x_tax_residence_status == 'non_resident' FOR c IN contracts)
        is_mixed_residence = NOT is_resident_full_year AND NOT is_nonresident_full_year
        
        # 3.4 Aggregate monthly data
        monthly_data = []
        FOR p IN emp_payslips ORDERED BY date_to:
            monthly_data.append({
                'month': p.date_to.month,
                'taxable_income_pre': p.line('GROSS_TAXABLE').amount,
                'personal_deduction': p.line('PERSONAL_DEDUCTION').amount,
                'dependent_deduction': p.line('DEPENDENT_DEDUCTION').amount,
                'dependent_count': ROUND(p.line('DEPENDENT_DEDUCTION').amount / 4400000),
                'taxable_income': p.line('TAXABLE_INCOME').amount,
                'pit_withheld': ABS(p.line('PIT').amount),
                'is_resident': (p.contract_id.x_tax_residence_status == 'resident'),
            })
        
        # 3.5 Include 13th-month bonus nếu có
        IF wizard.include_13th_month:
            bonus_payslip = SEARCH hr.payslip
                WHERE employee_id = emp.id
                  AND struct_id = STR_PR_BONUS_13TH
                  AND state = 'done'
                  AND date_to.year = fiscal_year
            
            IF bonus_payslip:
                monthly_data.append({
                    'month': 13,  # ký hiệu
                    'taxable_income_pre': bonus_payslip.line('GROSS_BONUS').amount,
                    'personal_deduction': 0,  # not applicable for bonus
                    'dependent_deduction': 0,
                    'pit_withheld': ABS(bonus_payslip.line('PIT').amount),
                    'is_resident': True,
                })
        
        # 3.6 Calculate annual totals
        annual_taxable_income_pre = SUM(m['taxable_income_pre'] FOR m IN monthly_data)
        annual_pit_withheld = SUM(m['pit_withheld'] FOR m IN monthly_data)
        
        IF is_resident_full_year:
            # Standard case
            
            # Tính giảm trừ năm: personal deduction × số tháng làm
            annual_personal_deduction = 11_000_000 × months_worked
            
            # Giảm trừ NPT: tính chính xác theo NPT đang hiệu lực mỗi tháng
            annual_dependent_deduction = 0
            FOR month IN range(first_payslip_month, last_payslip_month + 1):
                month_date = DATE(fiscal_year, month, 28)
                active_deps = SEARCH hr.dependent
                    WHERE employee_id = emp.id
                      AND date_from <= month_date
                      AND (date_to IS NULL OR date_to >= month_date)
                annual_dependent_deduction += LEN(active_deps) × 4_400_000
            
            # TN tính thuế năm
            annual_taxable_income = MAX(0, 
                annual_taxable_income_pre 
                - annual_personal_deduction 
                - annual_dependent_deduction
            )
            
            # PIT năm (theo biểu lũy tiến — nhưng tính dạng "tháng quy đổi")
            # Theo Thông tư 80/2021/TT-BTC: PIT năm = PIT_tháng_TB × 12
            # Trong đó PIT_tháng_TB tính trên TN_tính_thuế / months_worked
            monthly_avg_taxable = annual_taxable_income / months_worked
            monthly_pit = compute_pit_progressive(monthly_avg_taxable)
            annual_pit = monthly_pit × months_worked
            
        ELSE IF is_nonresident_full_year:
            # Non-resident: flat 20% on entire annual income
            annual_pit = annual_taxable_income_pre × 0.20
            annual_personal_deduction = 0
            annual_dependent_deduction = 0
            annual_taxable_income = annual_taxable_income_pre
            
        ELSE IF is_mixed_residence:
            # Phức tạp — tính riêng từng giai đoạn
            # Phase A: giai đoạn resident
            # Phase B: giai đoạn non-resident
            annual_pit = compute_mixed_residence_pit(emp, fiscal_year, monthly_data)
            # ... (logic phức tạp, tách riêng)
        
        # 3.7 Tính settlement
        settlement = annual_pit - annual_pit_withheld
        # settlement > 0: nộp thêm
        # settlement < 0: hoàn lại
        # settlement = 0: cân bằng
        
        settlement_lines.append({
            'employee': emp,
            'months_worked': months_worked,
            'monthly_data': monthly_data,
            'annual_taxable_income_pre': annual_taxable_income_pre,
            'annual_personal_deduction': annual_personal_deduction,
            'annual_dependent_deduction': annual_dependent_deduction,
            'annual_taxable_income': annual_taxable_income,
            'annual_pit': annual_pit,
            'annual_pit_withheld': annual_pit_withheld,
            'settlement': settlement,
            'settlement_type': 'pay_more' IF settlement > 0 
                              ELSE 'refund' IF settlement < 0 
                              ELSE 'balanced',
            'is_resident_full_year': is_resident_full_year,
            'is_nonresident_full_year': is_nonresident_full_year,
            'is_mixed_residence': is_mixed_residence,
        })
    
    # ── Step 4: Cross-Validation ─────────────────────────────
    warnings = []
    
    # 4.1 Check sum monthly khớp tổng năm
    total_pit_withheld_from_payslips = SUM(line.annual_pit_withheld FOR line IN settlement_lines)
    total_pit_from_etax_monthly = SUM(report.total_pit_amount 
                                       FOR report IN etax_monthly_reports_of_year)
    
    IF ABS(total_pit_withheld_from_payslips - total_pit_from_etax_monthly) > 1000:
        warnings.append({
            'type': 'pit_mismatch',
            'amount': total_pit_withheld_from_payslips - total_pit_from_etax_monthly,
        })
    
    # 4.2 Check NPT discrepancies (tương tự FUNC-PR-005)
    # ...
    
    # ── Step 5: Build files ──────────────────────────────────
    xml_file = build_xml_form_05_qtt_tncn(settlement_lines, fiscal_year, company)
    pdf_summary = build_pdf_summary(settlement_lines)
    
    # Per-employee PDFs
    individual_pdfs = []
    FOR line IN settlement_lines:
        individual_pdfs.append(
            build_pdf_individual_settlement(line)
        )
    
    # ── Step 6: Create records ───────────────────────────────
    year_end_report = CREATE hb.year.end.pit.report
        fiscal_year = fiscal_year
        declaration_type = wizard.declaration_type
        scope = wizard.scope
        line_count = LEN(settlement_lines)
        total_taxable_income = SUM(line.annual_taxable_income_pre)
        total_pit_year = SUM(line.annual_pit)
        total_pit_withheld = SUM(line.annual_pit_withheld)
        total_settlement_pay_more = SUM(line.settlement WHERE settlement > 0)
        total_settlement_refund = ABS(SUM(line.settlement WHERE settlement < 0))
        xml_attachment_id = create_attachment(xml_file)
        pdf_summary_attachment_id = create_attachment(pdf_summary)
        warnings_log = warnings  # JSON
        state = 'draft'
        generated_by = current_user
    
    FOR (line, pdf) IN ZIP(settlement_lines, individual_pdfs):
        line_record = CREATE hb.year.end.pit.line
            report_id = year_end_report.id
            employee_id = line.employee.id
            # ... all fields
            individual_pdf_attachment_id = create_attachment(pdf)
    
    # ── Step 7: Send to portal + email ───────────────────────
    FOR line_record IN year_end_report.line_ids:
        send_portal_notification(
            employee = line_record.employee_id,
            subject = f"Phiếu Quyết Toán TNCN Năm {fiscal_year}",
            attachment = line_record.individual_pdf_attachment_id,
        )
    
    RETURN year_end_report
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.year.end.pit.report`** (Master record per year)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "QTT-TNCN {year}" |
| `fiscal_year` | Integer | Yes | 2026 |
| `declaration_type` | Selection | Yes | official / supplementary |
| `scope` | Selection | Yes | all / department / specific |
| `line_count` | Integer | Yes | Số NV |
| `total_taxable_income` | Monetary | Yes | Tổng TN năm |
| `total_pit_year` | Monetary | Yes | Tổng PIT tính lại |
| `total_pit_withheld` | Monetary | Yes | Tổng PIT đã khấu trừ |
| `total_settlement_pay_more` | Monetary | Yes | Tổng phải nộp thêm |
| `total_settlement_refund` | Monetary | Yes | Tổng phải hoàn |
| `xml_attachment_id` | Many2one (ir.attachment) | Yes | XML eTax |
| `pdf_summary_attachment_id` | Many2one (ir.attachment) | Yes | PDF tổng |
| `warnings_log` | Text (JSON) | No | Cross-validation |
| `state` | Selection | Yes | draft/generated/submitted/accepted/rejected |
| `submission_code` | Char | No | Mã eTax |
| `submitted_date` | Date | No | - |
| `generated_by`, `generated_at` | (audit fields) | Yes | - |

**2. Model `hb.year.end.pit.line`** (Per-employee)

| Field | Type | Required | Description |
|---|---|---|---|
| `report_id` | Many2one | Yes | - |
| `employee_id` | Many2one (hr.employee) | Yes | - |
| `pit_code` | Char | No (Y nếu resident) | Snapshot |
| `passport_id` | Char | No (Y nếu non-resident) | Snapshot |
| `is_resident_full_year` | Boolean | Yes | - |
| `is_nonresident_full_year` | Boolean | Yes | - |
| `is_mixed_residence` | Boolean | Yes | - |
| `months_worked` | Integer | Yes | 1-12 |
| `first_month` | Integer | Yes | Tháng đầu (1-12) |
| `last_month` | Integer | Yes | Tháng cuối (1-12) |
| `annual_taxable_income_pre` | Monetary | Yes | Trước giảm trừ |
| `annual_personal_deduction` | Monetary | Yes | - |
| `annual_dependent_deduction` | Monetary | Yes | - |
| `annual_taxable_income` | Monetary | Yes | TN tính thuế |
| `annual_pit_year` | Monetary | Yes | PIT năm |
| `annual_pit_withheld` | Monetary | Yes | PIT đã khấu trừ |
| `settlement` | Monetary | Yes | + nộp thêm / - hoàn |
| `settlement_type` | Selection | Yes | pay_more/refund/balanced |
| `individual_pdf_attachment_id` | Many2one | No | PDF cá nhân |
| `monthly_breakdown_json` | Text | Yes | Chi tiết từng tháng |
| `acknowledgment_state` | Selection | No | pending/acknowledged |
| `acknowledged_date` | Date | No | NV xác nhận đã đọc |

---

## **VALIDATION RULES**

| No | Rule | Action |
|---|---|---|
| **VR-001** | 12 Payslip Batches của năm phải state `done` | Block + list batch chưa done |
| **VR-002** | 12 eTax monthly reports phải submitted | Warning (cho phép tiếp tục) |
| **VR-003** | NV phải có ít nhất 1 payslip trong năm | Skip NV không có |
| **VR-004** | NV resident phải có `x_pit_code` | Warning + cho skip |
| **VR-005** | Sum monthly PIT phải khớp với tổng từ eTax reports | Warning nếu chênh > 1000 VND |
| **VR-006** | Không tạo lại nếu đã submitted | Block (cần reset) |
| **VR-007** | `fiscal_year` không vượt năm hiện tại | Block |
| **VR-008** | NV có residence change phải có ghi chú đầy đủ | Warning |
| **VR-009** | Annual personal_deduction tính theo months_worked | Tự động pro-rate |
| **VR-010** | NPT phải có date_from / date_to chính xác | Warning nếu thiếu |

---

## **EXCEPTION FLOW**

### EX-001: Payslip Batches chưa hoàn thành
- Block + hiển thị list batch chưa done
- Cung cấp link đến Payroll Batches menu

### EX-002: Sum monthly PIT không khớp
- Warning modal với chi tiết chênh lệch
- Cho phép tiếp tục với ghi chú vào `warnings_log`
- HR Manager phải review trước khi submit

### EX-003: NV có nhiều contracts trong năm (residence change)
- Detect tự động, đánh dấu `is_mixed_residence = True`
- Apply logic tính riêng từng giai đoạn (`compute_mixed_residence_pit`)
- Log đầy đủ vào `monthly_breakdown_json`

### EX-004: NV vào/nghỉ giữa năm
- Detect bằng so sánh first_payslip_month vs last_payslip_month
- Pro-rate personal_deduction theo `months_worked`
- Đánh dấu trong báo cáo

### EX-005: Sinh lại sau khi đã submitted
- Block + yêu cầu reset (chỉ HR Manager)
- Bắt buộc nhập lý do
- Audit log đầy đủ

### EX-006: NV đã nghỉ — không truy cập Portal
- Gửi email với attachment PDF
- Log "not_delivered_via_portal"
- HR có thể export riêng để gửi tay

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-050** | Cùng cấu trúc data với FUNC-PR-005 (monthly eTax) | Để đối soát dễ dàng |
| **BR-PR-051** | Personal deduction × months_worked | Pro-rate cho NV vào/nghỉ giữa năm |
| **BR-PR-052** | NPT tính theo từng tháng, không lấy tổng năm | Vì NPT có thể thay đổi (sinh con, cha mẹ mất) trong năm |
| **BR-PR-053** | Thưởng tháng 13 include vào TN năm | Theo Thông tư 111/2013/TT-BTC |
| **BR-PR-054** | PIT năm = PIT_tháng_TB × months_worked (cho resident) | Theo Thông tư 80/2021/TT-BTC |
| **BR-PR-055** | Non-resident áp 20% flat trên TN năm | Không có giảm trừ |
| **BR-PR-056** | NV có residence change: tách giai đoạn | Phức tạp — tham khảo Thông tư 111 |
| **BR-PR-057** | Settlement positive = nộp thêm, negative = hoàn | Convention nhất quán |
| **BR-PR-058** | Hạn nộp bổ sung: 30/4 năm sau | Theo luật thuế VN |
| **BR-PR-059** | Hạn xin hoàn: trong vòng 3 năm | Theo Luật quản lý thuế |
| **BR-PR-060** | Mỗi NV nhận 1 phiếu quyết toán PDF riêng | Bảo mật + minh bạch |
| **BR-PR-061** | NV xác nhận đã đọc qua Portal | Audit + bảo vệ Cty |
| **BR-PR-062** | Audit log mọi thao tác | Generate, Reset, Submit |
| **BR-PR-063** | Submission code bắt buộc khi đánh dấu submitted | Truy xuất eTax |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| File XML Mẫu 05/QTT-TNCN | Theo schema eTax, upload lên cổng |
| File PDF tổng (cho HR) | Tất cả NV trong 1 file |
| File PDF cá nhân (per NV) | Gửi qua Portal + email |
| `hb.year.end.pit.report` record | Lưu vĩnh viễn |
| `hb.year.end.pit.line` records | Chi tiết per-employee |
| Portal notification | Mỗi NV nhận thông báo |
| Dashboard Year-End | Pivot/Chart cho HR Manager |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-006-01** | Wireframe Year-End List | Danh sách quyết toán các năm |
| **UI-PR-006-02** | Wireframe Create Wizard | Wizard tạo quyết toán |
| **UI-PR-006-03** | Wireframe Report Detail | Detail view với danh sách NV |
| **UI-PR-006-04** | Wireframe Individual Settlement | Phiếu quyết toán cá nhân |
| **UI-PR-006-05** | Wireframe Portal View | View của NV trên Employee Portal |
| **UI-PR-006-06** | Wireframe PDF Template | Template Mẫu 05/QTT-TNCN |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-006-001** | VN | Còn {N} Payslip Batch chưa Done. Vui lòng hoàn tất trước khi quyết toán. | On Validate |
| **MSG-PR-006-002** | VN | Còn {N} eTax monthly report chưa submitted. Có thể tiếp tục nhưng cần review kỹ. | On Validate (warning) |
| **MSG-PR-006-003** | VN | Quyết toán năm {year} đã hoàn thành: {N} NV, tổng PIT {amount} VND | On Generate Success |
| **MSG-PR-006-004** | VN | Phát hiện chênh lệch PIT giữa monthly aggregate và eTax reports: {amount} VND | On Cross-Validation |
| **MSG-PR-006-005** | VN | NV {name} có residence status thay đổi trong năm — đã áp dụng tính riêng từng giai đoạn | On Build Line (info) |
| **MSG-PR-006-006** | VN | NV {name} làm {N} tháng — đã pro-rate personal deduction | On Build Line (info) |
| **MSG-PR-006-007** | VN | Đã có quyết toán năm {year}. Vui lòng reset trước khi sinh mới. | On Duplicate |
| **MSG-PR-006-008** | VN | Đã gửi phiếu quyết toán đến {N} NV qua Portal | On Send Portal |
| **MSG-PR-006-009** | VN | Quyết toán đã được đánh dấu submitted với mã {code} | On Submit |
| **MSG-PR-006-010** | VN | Bạn cần nộp thêm {amount} VND. Hạn nộp: 30/04/{year+1} | On Portal Notification (pay more) |
| **MSG-PR-006-011** | VN | Bạn được hoàn lại {amount} VND. Vui lòng làm thủ tục theo hướng dẫn | On Portal Notification (refund) |
| **MSG-PR-006-012** | VN | Quyết toán của bạn đã cân bằng — không cần thao tác thêm | On Portal Notification (balanced) |
| **MSG-PR-006-013** | VN | Chỉ HR Manager mới có quyền reset quyết toán submitted | On Reset (security) |
| **MSG-PR-006-014** | VN | NV {name} đã xác nhận đã đọc phiếu quyết toán | On Acknowledge |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | 12 Payslip Batches của năm ở state `done` | Module Payroll |
| 2 | 12 eTax monthly reports đã submitted (khuyến nghị, không bắt buộc) | FUNC-PR-005 |
| 3 | (Optional) Thưởng tháng 13 đã được approve | FUNC-PR-007 |
| 4 | NV resident có `x_pit_code` | Module Employee (G-04) |
| 5 | NV có ít nhất 1 contract trong năm | Module Employee |
| 6 | Schema XML Mẫu 05/QTT-TNCN cập nhật | IT team |
| 7 | Module `hb_payroll_year_end_pit` cài đặt | Function này |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | File XML, PDF tổng, PDF cá nhân được tạo |
| 2 | `hb.year.end.pit.report` state = generated |
| 3 | Mỗi NV nhận phiếu quyết toán qua Portal + email |
| 4 | NV xác nhận đã đọc (acknowledgment) |
| 5 | Finance có thể submit lên eTax |
| 6 | Audit log đầy đủ |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Year-End Menu → "Quyết Toán Năm" | HR Manager (`SEC-PR-03`) |
| 2 | CRON auto-remind đầu tháng 1: "Đã đến lúc quyết toán năm trước" | Hệ thống |
| 3 | Smart button trên Payslip Batch tháng 12 → "Tiến hành Quyết Toán Năm" | HR Manager |
