# **FS — FUNC-PR-002**
# **Tính Ngược Net-to-Gross (Wizard)**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-002 |
| **Function Name** | Tính Ngược Net-to-Gross (Wizard) |
| **Custom Module** | `hb_payroll_net_to_gross` |
| **GAP Reference** | CUS-PR-002 (Chapter 4) |
| **Phase** | Phase 2 (3-4 tháng sau go-live) |
| **Độ phức tạp** | Cao |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS cho function Net-to-Gross | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này cung cấp một **wizard tính ngược** từ Lương Net thoả thuận → Lương Gross tương ứng, giúp HR có thể xác định mức Gross chính xác cần ghi vào hợp đồng khi đàm phán với ứng viên theo Net. Đây là tình huống **rất phổ biến tại Học Bá** với:

- **Giáo viên ngoại** (giảng viên người Trung Quốc, Đài Loan): họ chỉ quan tâm số tiền thực nhận hàng tháng, không hiểu cơ chế thuế VN
- **Giáo viên cấp cao** (HSK 5-6, có chứng chỉ giảng dạy quốc tế): thường đàm phán theo Net để dễ so sánh với offer từ trung tâm khác
- **Quản lý cấp trung** (Trưởng phòng Đào tạo, Marketing Lead): offer thường theo Net cho dễ đo lường

Function dùng **iterative algorithm** (lặp xấp xỉ) vì biểu thuế TNCN 7 bậc của VN tạo ra quan hệ phi tuyến giữa Gross và Net — không có công thức đảo trực tiếp. Thuật toán hội tụ trong 3-5 vòng lặp với độ chính xác ±1 VND.

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-06** Không có công cụ Net-to-Gross | Wizard 1-click cho kết quả chính xác trong < 2 giây |
| **PP-PR-04** Audit trail thoả thuận lương | Lưu lịch sử tính toán + ghi rõ NV nào offer Net |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Employee** | Đọc `x_pit_code`, `x_tax_residence_status`, `hr.dependent` |
| **Module Payroll** | Áp dụng cùng logic Salary Rules đã cấu hình ở Chapter 5.4.2/5.4.3/5.4.4 |
| **Chapter 5 (Configuration)** | Reference các tham số PARAM-PR-01 đến 09 (BHXH), PARAM-PR-PIT-01 đến 07 (Thuế) |
| **FUNC-PR-001** | Nếu là giáo viên: dùng để tính ngược đơn giá giờ |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **HR Officer (C&B)** | Sử dụng wizard tính toán + lưu kết quả |
| **HR Manager** | Approve khi mức Gross vượt ngưỡng review |
| **Academic Manager** | Sử dụng cho giáo viên thuê mới (`SEC-PR-01` extended) |

---

## **FUNCTION FLOW**

```
┌──────────────────────────────────────────────────────────┐
│  HR đàm phán xong với ứng viên — chốt mức NET            │
│  (VD: 25 triệu Net/tháng)                                 │
└──────────────────────┬───────────────────────────────────┘
                       ▼
       ┌────────────────────────────────────┐
       │ HR mở wizard: Net-to-Gross         │
       │ Vị trí: HR Menu / Employee Form    │
       └────────────────┬───────────────────┘
                        ▼
       ┌────────────────────────────────────┐
       │ Wizard Input:                       │
       │ - Net target (VD: 25,000,000)       │
       │ - Số người phụ thuộc                │
       │ - Insurance base eligibility        │
       │ - Cư trú / Không cư trú             │
       │ - Thử việc / Chính thức             │
       └────────────────┬───────────────────┘
                        ▼
       ┌────────────────────────────────────┐
       │ Bước 1: Quick Estimate              │
       │ - Nếu Net dưới ngưỡng thuế:         │
       │   Gross = Net/(1 - 10.5%) (đơn giản)│
       │ - Nếu trên: estimate ban đầu        │
       │   Gross ≈ Net × 1.30                │
       └────────────────┬───────────────────┘
                        ▼
       ┌────────────────────────────────────┐
       │ Bước 2: Iterative Forward Compute   │
       │ Loop tối đa 10 vòng:                │
       │   - Apply BHXH/BHYT/BHTN            │
       │   - Apply giảm trừ bản thân + NPT   │
       │   - Apply biểu thuế 7 bậc           │
       │   - So sánh Net_computed vs Net_tgt │
       │   - Điều chỉnh Gross (Newton-like)  │
       │   - Tolerance: |diff| < 1 VND       │
       └────────────────┬───────────────────┘
                        ▼
                ┌────────────────────────┐
                │ Đã hội tụ?             │
                └────┬───────────────┬───┘
                     │ Có             │ Không (sau 10 vòng)
                     ▼                ▼
       ┌─────────────────────┐  ┌──────────────────────┐
       │ Hiển thị Breakdown  │  │ Báo lỗi không hội tụ  │
       │ - Gross             │  │ + recommend gọi IT     │
       │ - BHXH/BHYT/BHTN    │  └──────────────────────┘
       │ - PIT               │
       │ - Net (verify =     │
       │   Net_target)       │
       └─────────┬───────────┘
                 ▼
       ┌─────────────────────┐
       │ HR review            │
       │ Có lưu vào employee  │
       │ contract?            │
       └──────┬──────────────┘
              ▼
       ┌─────────────────────────────┐
       │ Save → tạo contract draft   │
       │ với:                         │
       │ - wage = Gross               │
       │ - x_negotiated_in_net = True │
       │ - x_net_target = Net         │
       └─────────────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: Net-to-Gross Wizard

**Vị trí**: HR → Payroll Tools → Net-to-Gross Calculator
**HOẶC**: Từ Employee Form / Contract Form → button "Compute Gross from Net"

```
┌──────────────────────────────────────────────────────────────────┐
│  Tính ngược Lương Gross từ Net                              [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─── Input ──────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  Lương NET thỏa thuận (*) : [____________] VND/tháng        │  │
│  │                              VD: 25,000,000                   │  │
│  │                                                                │  │
│  │  Số người phụ thuộc       : [___] (0-10)                     │  │
│  │  Trạng thái cư trú        : ● Cư trú  ○ Không cư trú         │  │
│  │  Loại hợp đồng            : ● Chính thức  ○ Thử việc (85%)   │  │
│  │                                                                │  │
│  │  ☑ Có đóng BHXH/BHYT/BHTN                                    │  │
│  │  ☐ Có phụ cấp không đóng BH (ăn trưa, đi lại...)             │  │
│  │     └─ Tổng phụ cấp không đóng BH: [_______] VND             │  │
│  │                                                                │  │
│  │  Liên kết NV (optional):  [Chọn nhân viên ▼]                 │  │
│  │  (Nếu chọn, sẽ tự lấy số NPT và cư trú từ profile)           │  │
│  │                                                                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  [Hủy]                                              [Tính toán]    │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Result Breakdown

```
┌────────────────────────────────────────────────────────────────────┐
│  Kết quả: Lương Net 25,000,000 ↔ Lương Gross ???        [×]        │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✅ Đã hội tụ sau 4 vòng lặp (tolerance < 1 VND)                    │
│                                                                      │
│  ┌─── Breakdown chi tiết ───────────────────────────────────────┐  │
│  │                                                                │  │
│  │  Lương GROSS                          : 33,728,500 VND        │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  (-) BHXH NV đóng (8%)                : -2,698,280            │  │
│  │  (-) BHYT NV đóng (1.5%)              :   -505,928            │  │
│  │  (-) BHTN NV đóng (1%)                :   -337,285            │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  Thu nhập trước thuế                   : 30,187,007 VND        │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  (-) Giảm trừ bản thân                 : -11,000,000          │  │
│  │  (-) Giảm trừ người phụ thuộc (1 NPT)  :  -4,400,000          │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  Thu nhập tính thuế                    : 14,787,007 VND        │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  Thuế TNCN (theo biểu lũy tiến 7 bậc) :  -1,187,051           │  │
│  │     • Bậc 1 (5tr × 5%)         :   250,000                    │  │
│  │     • Bậc 2 (5tr × 10%)        :   500,000                    │  │
│  │     • Bậc 3 (4.79tr × 15%)     :   718,051                    │  │
│  │     ─────────────────────────────                              │  │
│  │     Tổng PIT                   : 1,468,051                    │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │  Chi phí Cty đóng BH (17.5%+3%+1%):  +7,757,555               │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │                                                                  │  │
│  │  Lương NET (verify)                    : 25,000,000 VND ✓     │  │
│  │  Tổng chi phí Cty                      : 41,486,055 VND       │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ⚠ Khuyến nghị: Mức này hợp lý, không cần HR Manager approve          │
│                                                                       │
│  Action:                                                               │
│  [Hủy]  [In Breakdown]  [Lưu lịch sử]  [Tạo Contract Draft →]        │
└────────────────────────────────────────────────────────────────────┘
```

### Screen 3: Save to Contract Confirmation

```
┌──────────────────────────────────────────────────────────────────┐
│  Lưu mức lương vào Contract                                [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Bạn muốn lưu kết quả này vào:                                    │
│                                                                    │
│  ○ Tạo Contract DRAFT mới                                         │
│    └─ Cho nhân viên: [Chọn nhân viên ▼]                          │
│                                                                    │
│  ● Cập nhật Contract đang DRAFT                                    │
│    └─ Contract: [HD-2026-T-045 (Draft) ▼]                        │
│                                                                    │
│  ○ Chỉ lưu vào lịch sử (`hb.net.to.gross.history`)                │
│                                                                    │
│  Contract sau khi lưu sẽ có:                                       │
│  - wage = 33,728,500 VND                                          │
│  - x_negotiated_in_net = TRUE                                     │
│  - x_net_target = 25,000,000 VND                                  │
│  - Ghi chú: "Đàm phán theo Net" (chatter)                         │
│                                                                    │
│  [Hủy]                                              [Xác nhận]    │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 4: History List

**Vị trí**: HR → Reports → Net-to-Gross History

```
┌──────────────────────────────────────────────────────────────────┐
│  Lịch sử Net-to-Gross Calculations            [+ Tạo Mới]        │
├──────────────────────────────────────────────────────────────────┤
│  Ngày      │ NV (nếu có) │ Net    │ Gross    │ NPT │ Người tính │
│  ──────────┼────────────┼────────┼──────────┼─────┼──────────  │
│  03/12/2026│ Cô Wang Yu │ 25.0tr │ 33.7tr   │  1  │ Chị Hằng   │
│  02/12/2026│ (chưa lưu) │ 30.0tr │ 41.5tr   │  2  │ Chị Hằng   │
│  28/11/2026│ Anh Trần A │ 18.0tr │ 22.8tr   │  0  │ Anh Tuấn   │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Required | Mô tả |
|---|---|---|---|---|
| 1 | `net_target` | Wizard input | Yes | Net thỏa thuận (VND) |
| 2 | `dependent_count` | Wizard input hoặc từ `hr.dependent` | Yes | Số NPT |
| 3 | `is_resident` | Wizard input | Yes | Cá nhân cư trú? |
| 4 | `is_probation` | Wizard input | Yes | Đang thử việc? |
| 5 | `has_insurance` | Wizard input | Yes | Có đóng BH bắt buộc? |
| 6 | `non_insurance_allowances` | Wizard input | No | Tổng phụ cấp không đóng BH |
| 7 | `employee_id` (optional) | Wizard input | No | Liên kết NV để auto-fill |
| 8 | BHXH/BHYT/BHTN rates | `Salary Rule Parameters` | Yes | Từ Chapter 5.4.2 |
| 9 | PIT brackets | `Salary Rule Parameters` | Yes | Từ Chapter 5.4.3 |
| 10 | Personal/Dependent deduction | `Salary Rule Parameters` | Yes | Từ Chapter 5.4.4 |
| 11 | Insurance caps | `Salary Rule Parameters` | Yes | 20× base salary |

### Bảng Output Data

| No | Output | Mô tả |
|---|---|---|
| 1 | `gross_amount` | Lương Gross đã tính |
| 2 | `bhxh_employee`, `bhxh_employer` | BHXH NV + Cty đóng |
| 3 | `bhyt_employee`, `bhyt_employer` | BHYT NV + Cty đóng |
| 4 | `bhtn_employee`, `bhtn_employer` | BHTN NV + Cty đóng |
| 5 | `taxable_income_before_deduction` | TN trước giảm trừ |
| 6 | `personal_deduction`, `dependent_deduction` | Giảm trừ |
| 7 | `taxable_income` | TN tính thuế |
| 8 | `pit_amount` | Thuế TNCN |
| 9 | `pit_breakdown` | Chi tiết từng bậc thuế |
| 10 | `net_verified` | Net được verify (phải = net_target) |
| 11 | `iterations_count` | Số vòng lặp đã chạy |
| 12 | `total_company_cost` | Tổng chi phí Cty (Gross + BH Cty) |

### Pseudo-code thuật toán

```
FUNCTION compute_net_to_gross(inputs):
    
    # ── Bước 1: Quick estimate ban đầu ──────────────────────────
    IF NOT inputs.has_insurance:
        # Đơn giản: chỉ có thuế
        estimated_gross = inputs.net_target × 1.1  # rough estimate
    ELSE:
        # Có cả BH và thuế
        IF inputs.net_target < 11_000_000:
            # Dưới ngưỡng thuế (NV chỉ trừ BH 10.5%)
            estimated_gross = inputs.net_target / (1 - 0.105)
        ELSE:
            estimated_gross = inputs.net_target × 1.30  # heuristic
    
    # ── Bước 2: Iterative forward compute ───────────────────────
    MAX_ITERATIONS = 10
    TOLERANCE = 1  # VND
    gross = estimated_gross
    
    FOR iteration IN range(MAX_ITERATIONS):
        
        # 2.1 Apply probation rate (nếu thử việc)
        effective_gross = gross × 0.85 IF inputs.is_probation ELSE gross
        
        # 2.2 Tính BH NV đóng
        IF inputs.has_insurance:
            insurance_base = MIN(effective_gross, PARAM_BHXH_BASE_CAP)
            insurance_base_bhtn = MIN(effective_gross, PARAM_BHTN_BASE_CAP)
            
            bhxh_nv = insurance_base × 0.08
            bhyt_nv = insurance_base × 0.015
            bhtn_nv = insurance_base_bhtn × 0.01
        ELSE:
            bhxh_nv = bhyt_nv = bhtn_nv = 0
        
        # 2.3 Tính thu nhập tính thuế
        IF inputs.is_resident:
            # Resident: dùng biểu lũy tiến 7 bậc
            taxable_income_pre = effective_gross 
                               - (bhxh_nv + bhyt_nv + bhtn_nv)
                               - inputs.non_insurance_allowances_taxable
            
            personal_deduction = 11_000_000
            dependent_deduction = inputs.dependent_count × 4_400_000
            
            taxable_income = MAX(0, 
                taxable_income_pre - personal_deduction - dependent_deduction
            )
            
            # Apply 7-bracket progressive tax
            pit = compute_pit_progressive(taxable_income)
        ELSE:
            # Non-resident: flat 20% on entire taxable income
            taxable_income = effective_gross
            pit = effective_gross × 0.20
            personal_deduction = 0
            dependent_deduction = 0
        
        # 2.4 Tính NET computed
        net_computed = effective_gross 
                     - (bhxh_nv + bhyt_nv + bhtn_nv) 
                     - pit
        
        # 2.5 So sánh với target
        diff = inputs.net_target - net_computed
        
        IF ABS(diff) < TOLERANCE:
            # Đã hội tụ
            BREAK
        
        # 2.6 Newton-like adjustment
        # Marginal rate: bao nhiêu Net tăng khi Gross tăng 1 đơn vị
        marginal_rate = compute_marginal_rate(
            current_gross=gross,
            inputs=inputs
        )
        # marginal_rate là tỷ lệ Net/Gross tại điểm hiện tại (thường 0.6-0.85)
        
        gross_adjustment = diff / marginal_rate
        gross = gross + gross_adjustment
    
    # ── Bước 3: Validate hội tụ ─────────────────────────────────
    IF iteration == MAX_ITERATIONS - 1 AND ABS(diff) >= TOLERANCE:
        RAISE ValidationError(
            "Không hội tụ sau {MAX_ITERATIONS} vòng. "
            "Có thể do input bất thường. Liên hệ IT."
        )
    
    # ── Bước 4: Tính các giá trị output ─────────────────────────
    bhxh_er = insurance_base × 0.175  # Employer
    bhyt_er = insurance_base × 0.03
    bhtn_er = insurance_base_bhtn × 0.01
    
    pit_breakdown = compute_pit_breakdown(taxable_income)  # for each bracket
    
    total_company_cost = gross + bhxh_er + bhyt_er + bhtn_er
    
    RETURN {
        'gross_amount': gross,
        'bhxh_employee': bhxh_nv,
        'bhxh_employer': bhxh_er,
        'bhyt_employee': bhyt_nv,
        'bhyt_employer': bhyt_er,
        'bhtn_employee': bhtn_nv,
        'bhtn_employer': bhtn_er,
        'taxable_income_before_deduction': taxable_income_pre,
        'personal_deduction': personal_deduction,
        'dependent_deduction': dependent_deduction,
        'taxable_income': taxable_income,
        'pit_amount': pit,
        'pit_breakdown': pit_breakdown,
        'net_verified': net_computed,
        'iterations_count': iteration + 1,
        'total_company_cost': total_company_cost,
        'is_converged': ABS(diff) < TOLERANCE,
    }


FUNCTION compute_pit_progressive(taxable_income):
    # 7-bracket progressive tax theo Nghị quyết 954/2020/UBTVQH14
    brackets = [
        (5_000_000, 0.05),
        (10_000_000, 0.10),
        (18_000_000, 0.15),
        (32_000_000, 0.20),
        (52_000_000, 0.25),
        (80_000_000, 0.30),
        (FLOAT_INF, 0.35),
    ]
    
    total_pit = 0
    previous_threshold = 0
    
    FOR (threshold, rate) IN brackets:
        IF taxable_income <= threshold:
            total_pit += (taxable_income - previous_threshold) × rate
            BREAK
        ELSE:
            total_pit += (threshold - previous_threshold) × rate
            previous_threshold = threshold
    
    RETURN total_pit


FUNCTION compute_marginal_rate(current_gross, inputs):
    # Tính tỷ lệ Net/Gross tại điểm này
    # Bằng cách compute forward 2 lần: current_gross và current_gross + delta
    delta = 1_000_000
    net1 = forward_compute_net(current_gross, inputs)
    net2 = forward_compute_net(current_gross + delta, inputs)
    RETURN (net2 - net1) / delta
```

### Ví dụ minh hoạ (matching Screen 2)

**Input**: Net target = 25.000.000, NPT = 1, Cư trú, Chính thức, Có đóng BH

**Trace iteration:**

| Vòng | Gross thử | Net computed | Diff | Marginal | Adjust | Gross mới |
|---|---|---|---|---|---|---|
| 1 | 32.500.000 (estimate) | 23.940.000 | +1.060.000 | 0.74 | +1.432.432 | 33.932.432 |
| 2 | 33.932.432 | 25.124.500 | -124.500 | 0.74 | -168.243 | 33.764.189 |
| 3 | 33.764.189 | 25.012.300 | -12.300 | 0.74 | -16.621 | 33.747.568 |
| 4 | 33.747.568 | 25.000.105 | -105 | 0.74 | -142 | 33.747.426 |
| 5 | 33.747.426 | 25.000.000 | 0 | - | (hội tụ) | **33.747.426** |

→ **Gross final: 33.747.426 VND** (hội tụ sau 5 vòng, tolerance < 1 VND).

(Số trên Screen 2 là 33,728,500 — chỉ là ví dụ minh hoạ, không cần khớp pixel-perfect với pseudo-code).

---

## **SCREEN DEFINITION**

### Custom Models / Wizards

**1. Model Wizard `hb.payroll.net.to.gross.wizard` (Transient)**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `net_target` | Monetary | Yes | - | Net thoả thuận |
| `dependent_count` | Integer | Yes | 0 | Số NPT |
| `is_resident` | Boolean | Yes | True | Cư trú? |
| `is_probation` | Boolean | Yes | False | Thử việc? |
| `has_insurance` | Boolean | Yes | True | Có BH? |
| `non_insurance_allowances` | Monetary | No | 0 | Phụ cấp không đóng BH |
| `employee_id` | Many2one (hr.employee) | No | - | Liên kết NV (optional) |
| `result_gross` | Monetary (computed) | - | - | Gross output |
| `result_pit` | Monetary (computed) | - | - | PIT output |
| `result_company_cost` | Monetary (computed) | - | - | Chi phí Cty |
| `result_iterations` | Integer (computed) | - | - | Số vòng lặp |
| `result_converged` | Boolean (computed) | - | - | Có hội tụ? |
| `result_breakdown_json` | Text (computed) | - | - | JSON chi tiết breakdown |

**2. Model `hb.net.to.gross.history` (Lưu lịch sử)**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "N2G {date} - {employee}" |
| `compute_date` | Datetime | Yes | Default = now |
| `employee_id` | Many2one (hr.employee) | No | NV liên kết (nếu có) |
| `contract_id` | Many2one (hr.contract) | No | Contract đã lưu vào (nếu có) |
| `net_target` | Monetary | Yes | - |
| `gross_result` | Monetary | Yes | - |
| `dependent_count` | Integer | Yes | - |
| `is_resident` | Boolean | Yes | - |
| `is_probation` | Boolean | Yes | - |
| `iterations` | Integer | Yes | - |
| `breakdown_json` | Text | Yes | Full breakdown |
| `computed_by` | Many2one (res.users) | Yes | Người tính |
| `notes` | Text | No | - |

**3. Extend `hr.contract`**

| Field | Type | Required | Description |
|---|---|---|---|
| `x_negotiated_in_net` | Boolean | No (default False) | Hợp đồng thoả thuận theo Net |
| `x_net_target` | Monetary | No | Net thoả thuận (nếu x_negotiated_in_net=True) |

---

## **VALIDATION RULES**

| No | Rule | Trigger | Action |
|---|---|---|---|
| **VR-001** | `net_target` > 0 | On Wizard Compute | Block, error message |
| **VR-002** | `net_target` <= 1.000.000.000 (sanity cap) | On Wizard Compute | Warning + cho phép |
| **VR-003** | `dependent_count` trong khoảng 0-10 | On Wizard Save | Block nếu out of range |
| **VR-004** | Phải hội tụ trong 10 vòng | On Compute | Raise error nếu không hội tụ |
| **VR-005** | Marginal rate phải > 0.1 (tránh loop vô hạn) | On Each Iteration | Raise error nếu detect đứng yên |
| **VR-006** | Gross result phải >= Net target | Post-compute sanity | Sanity check (luôn đúng nếu logic OK) |
| **VR-007** | Khi non-resident: bỏ qua giảm trừ | On Compute | Tự động, không block |
| **VR-008** | Khi `has_insurance = False`: BHXH = BHYT = BHTN = 0 | On Compute | Tự động |
| **VR-009** | Khi save vào Contract: Contract phải state = Draft | On Save | Block nếu Contract đã Open |
| **VR-010** | Gross > 200tr/tháng → cần HR Manager review | On Save Result | Warning + flag for review |

---

## **EXCEPTION FLOW**

### EX-001: Không hội tụ sau 10 vòng
- Raise error: "Thuật toán không hội tụ. Có thể do input bất thường."
- Log đầy đủ vào system log: input + trace 10 vòng
- Notify IT team qua email
- HR có thể thử lại với input đơn giản hơn

### EX-002: Marginal rate = 0 (loop vô hạn)
- Detect khi 2 vòng liên tiếp có Gross adjustment = 0 nhưng diff > tolerance
- Raise error "Không thể điều chỉnh thêm. Có thể input ở mức bất thường."
- Log + báo IT

### EX-003: Net target quá thấp (< minimum wage)
- Warning: "Net thoả thuận thấp hơn lương tối thiểu vùng"
- Cho phép tiếp tục (để dùng cho CTV / part-time)

### EX-004: Net target quá cao (> 200tr/tháng)
- Warning: "Mức lương cao. Cần HR Manager review."
- Flag history record với `needs_review = True`

### EX-005: Lỗi parameter chưa cấu hình
- Nếu Chapter 5 chưa cấu hình PIT brackets / BH parameters
- Raise error: "Chưa cấu hình tham số. Vui lòng hoàn thành Chapter 5 Configuration."
- Cung cấp link đến menu Configuration

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-038** | Iterative algorithm tolerance: ±1 VND | Vì Gross/Net là số nguyên VND |
| **BR-PR-039** | MAX_ITERATIONS = 10 | Đủ cho mọi case thực tế (thường hội tụ 3-5 vòng) |
| **BR-PR-040** | Resident dùng biểu lũy tiến 7 bậc | Theo Nghị quyết 954/2020/UBTVQH14 |
| **BR-PR-041** | Non-resident áp 20% flat | Theo Thông tư 111/2013/TT-BTC |
| **BR-PR-042** | Probation áp 85% tại bước Effective Gross | Theo Chapter 5.4.5 (CFG-PR-005) |
| **BR-PR-043** | NPT lấy snapshot tại thời điểm tính | Không phụ thuộc thời gian — tính dạng "if has NPT thì áp giảm trừ" |
| **BR-PR-044** | Trần BHXH/BHYT = 20× lương cơ sở, BHTN = 20× lương tối thiểu vùng | Theo Chapter 5.4.2 (PARAM-PR-09) |
| **BR-PR-045** | Lưu lịch sử tính mọi lần, kể cả không lưu vào contract | Phục vụ audit + tham khảo |
| **BR-PR-046** | Khi save vào contract: tự bật `x_negotiated_in_net = True` | Để future payslip có thể recompute nếu params đổi |
| **BR-PR-047** | Gross result làm tròn xuống đơn vị 1.000 VND | Để dễ ghi vào contract (không có lẻ) |
| **BR-PR-048** | Audit log: mọi save vào contract đều ghi Chatter | Để biết ai đề xuất mức Gross này |
| **BR-PR-049** | Người tính (`computed_by`) phải có quyền `SEC-PR-01` hoặc cao hơn | Security |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| Breakdown chi tiết on-screen | Hiển thị trong Wizard result step |
| `hb.net.to.gross.history` record | Lưu lịch sử mọi lần tính |
| Contract field `wage` được cập nhật (nếu HR save) | Sẵn sàng cho payslip computation |
| Contract field `x_negotiated_in_net` = True | Flag cho future payslip |
| PDF breakdown (optional print) | Để HR đưa cho ứng viên xem (transparency) |
| Chatter log trên Contract | Audit ai đã set wage = bao nhiêu, từ Net = bao nhiêu |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-002-01** | Wireframe Wizard Input | Screen 1 — form nhập Net target |
| **UI-PR-002-02** | Wireframe Result Breakdown | Screen 2 — bảng breakdown chi tiết |
| **UI-PR-002-03** | Wireframe Save Confirmation | Screen 3 — chọn cách lưu |
| **UI-PR-002-04** | Wireframe History List | Screen 4 — danh sách lịch sử |
| **UI-PR-002-05** | Wireframe PDF Breakdown | Template PDF để in cho ứng viên |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-002-001** | VN | Net thoả thuận phải lớn hơn 0 | On Validate |
| **MSG-PR-002-002** | VN | Số người phụ thuộc phải trong khoảng 0-10 | On Validate |
| **MSG-PR-002-003** | VN | Đã tính thành công: Net {net} ↔ Gross {gross} ({iterations} vòng) | On Compute Success |
| **MSG-PR-002-004** | VN | Thuật toán không hội tụ sau 10 vòng. Vui lòng kiểm tra input hoặc liên hệ IT. | On Compute Fail |
| **MSG-PR-002-005** | VN | Mức Gross {gross} vượt 200 triệu/tháng — cần HR Manager phê duyệt | On Save (warning) |
| **MSG-PR-002-006** | VN | Net thoả thuận thấp hơn lương tối thiểu vùng — vui lòng xem lại | On Validate (warning) |
| **MSG-PR-002-007** | VN | Đã lưu mức Gross vào Contract {contract_ref} | On Save Success |
| **MSG-PR-002-008** | VN | Contract đã ở state Open — không thể sửa wage. Vui lòng tạo Contract mới. | On Save (block) |
| **MSG-PR-002-009** | VN | Đã lưu lịch sử Net-to-Gross #{history_id} | On Save History |
| **MSG-PR-002-010** | VN | Chưa cấu hình tham số thuế. Vui lòng hoàn thành Chapter 5 Configuration. | On Compute (error) |
| **MSG-PR-002-011** | VN | Cá nhân không cư trú áp thuế 20% flat — không có giảm trừ bản thân/NPT | On Compute (info) |
| **MSG-PR-002-012** | VN | Vui lòng nhập Net thoả thuận trước khi tính | On Compute (validate) |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | Các Salary Rule Parameters BHXH/BHYT/BHTN đã cấu hình | Chapter 5.4.2 |
| 2 | Các Salary Rule Parameters PIT 7 brackets đã cấu hình | Chapter 5.4.3 |
| 3 | Personal/Dependent Deduction parameters đã cấu hình | Chapter 5.4.4 |
| 4 | HR user có quyền `SEC-PR-01` hoặc cao hơn | Chapter 5.4.11 |
| 5 | Module `hb_payroll_net_to_gross` đã được cài | Function này |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | History record được tạo trong `hb.net.to.gross.history` |
| 2 | (Optional) Contract.wage được cập nhật + `x_negotiated_in_net = True` |
| 3 | (Optional) Chatter log trên Contract ghi ai đã set, từ Net nào |
| 4 | HR có Breakdown chi tiết để giải thích với ứng viên |
| 5 | Future payslip có thể recompute nếu parameters thay đổi (qua flag `x_negotiated_in_net`) |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | HR Menu → Payroll Tools → "Net-to-Gross Calculator" | HR Officer (`SEC-PR-01+`) |
| 2 | Button "Compute Gross from Net" trên Contract Form | HR Officer / Academic Manager |
| 3 | Button "Compute Gross from Net" trên Employee Form (cho NV mới) | HR Officer |
| 4 | API call (Phase 3 — integration với recruitment) | Recruitment module |
