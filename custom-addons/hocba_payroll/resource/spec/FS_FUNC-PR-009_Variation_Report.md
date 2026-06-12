# **FS — FUNC-PR-009**
# **Báo Cáo Variation (So Sánh Tháng Này Vs Tháng Trước)**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-009 |
| **Function Name** | Báo Cáo Variation Lương (So Sánh Liên Kỳ) |
| **Custom Module** | `hb_payroll_variation_report` |
| **GAP Reference** | CUS-PR-009 (Chapter 4) |
| **Phase** | Phase 2 (Nice-to-have proactive quality) |
| **Độ phức tạp** | Trung bình |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS báo cáo variation | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này cung cấp một **dashboard so sánh payslip tháng hiện tại với tháng trước** để HR phát hiện các biến động bất thường **TRƯỚC** khi approve batch và chi lương. Hiện tại ở AS-IS, lỗi data chỉ được phát hiện sau khi NV đã nhận payslip và phàn nàn — gây bối rối cho cả HR và NV.

Báo cáo có **3 layer phân tích**:

1. **Summary level**: Tổng quan toàn batch (tổng Gross, tổng Net, tổng PIT) — biến động vs batch trước
2. **Employee level**: So sánh từng NV — Net giảm/tăng bao nhiêu, % thay đổi
3. **Salary-rule level**: Drill-down vào dòng cụ thể — TEACH_HOURS giảm 30% vì sao? BHXH tăng vì sao?

Mỗi level có **color-coded indicators**:
- 🟢 Xanh: Biến động < 10% (bình thường)
- 🟡 Vàng: Biến động 10-20% (cần để ý)
- 🔴 Đỏ: Biến động > 20% (cần investigate ngay)

Function này không cản trở chu trình bình thường — chỉ là **layer cảnh báo bổ sung**. HR vẫn có thể approve dù có warning, nhưng phải ghi nhận lý do (audit trail).

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-04** Không có audit trail biến động | Lưu vĩnh viễn các "anomalies" đã phát hiện + reasoning |
| **PP-PR-05** Lỗi data phát hiện trễ | Catch ngay tại bước review trước approve |
| **PP-PR-02** Lương GV phức tạp dễ sai | Drill-down rule-by-rule để debug |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Payroll** | Đọc 2 payslip batches liên tiếp + tất cả payslip lines |
| **FUNC-PR-001** | Drill-down TEACH_HOURS để xem chi tiết giờ dạy |
| **FUNC-PR-005** | Optional: liên kết với eTax variation |
| **Chapter 5** | Sử dụng cấu hình thresholds (10%, 20%, etc.) |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **HR Officer** | Xem báo cáo, không bypass được warnings (`SEC-PR-01/02`) |
| **HR Manager** | Xem báo cáo + bypass warnings với lý do (`SEC-PR-03`) |
| **Finance** | Read-only (`SEC-PR-04`) |

---

## **FUNCTION FLOW**

```
┌──────────────────────────────────────────────────────────┐
│  HR tạo Payslip Batch tháng (state Draft → Waiting)      │
│  Đã compute payslips trong batch                          │
└──────────────────────┬───────────────────────────────────┘
                       ▼
       ┌─────────────────────────────────────┐
       │ HR bấm "Run Variation Analysis"     │
       │ trên Payslip Batch                  │
       └────────────────┬────────────────────┘
                        ▼
       ┌─────────────────────────────────────┐
       │ Engine tìm Payslip Batch trước đó:  │
       │ - Cùng salary structure type        │
       │ - Tháng liền kề                      │
       └────────────────┬────────────────────┘
                        ▼
            ┌─────────────────────────┐
            │ Có batch trước không?   │
            └───┬──────────────────┬──┘
                │ Không            │ Có
                ▼                  ▼
       ┌──────────────────┐  ┌──────────────────────────┐
       │ Báo: "Đây là     │  │ Compute Variations cho 3  │
       │  batch đầu tiên" │  │ levels: Summary / Emp /    │
       │ Skip analysis     │  │ Rule                       │
       └──────────────────┘  └──────────┬───────────────┘
                                        ▼
                            ┌──────────────────────────┐
                            │ Apply Color-coding       │
                            │ theo thresholds:         │
                            │ 🟢 < 10%                  │
                            │ 🟡 10-20%                 │
                            │ 🔴 > 20%                  │
                            └──────────┬───────────────┘
                                       ▼
                            ┌──────────────────────────┐
                            │ Render Dashboard:        │
                            │ - Summary cards          │
                            │ - Sortable table per NV   │
                            │ - Filter by severity     │
                            └──────────┬───────────────┘
                                       ▼
                            ┌──────────────────────────┐
                            │ HR review red items      │
                            │ Có 2 options:            │
                            │ 1. Drill-down: xem chi   │
                            │    tiết salary rule      │
                            │ 2. Fix: quay lại edit    │
                            │    inputs / recompute    │
                            └──────────┬───────────────┘
                                       ▼
                            ┌──────────────────────────┐
                            │ Nếu vẫn còn 🔴 mà HR     │
                            │ muốn proceed → bắt buộc  │
                            │ ghi lý do (justify)      │
                            │ vào audit log            │
                            └──────────┬───────────────┘
                                       ▼
                            ┌──────────────────────────┐
                            │ Save variation snapshot  │
                            │ vào `hb.variation.report`│
                            │ Batch có thể chuyển Done │
                            └──────────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: Run Variation Analysis Button

**Vị trí**: Payslip Batch Form — Khi batch ở state Waiting

```
┌──────────────────────────────────────────────────────────────────┐
│  Payslip Batch: BATCH/2026/10/001 — Lương Tháng 10/2026          │
│  State: [Waiting ▼]                                                │
├──────────────────────────────────────────────────────────────────┤
│  [Print Payslips]  [Generate Bank File]  [🔍 Variation Analysis] │
│                                          ─────────────────────── │
│                                          ↑ Highlighted button     │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Variation Dashboard — Summary Layer

**Vị trí**: Click "Variation Analysis" → mở dashboard

```
┌────────────────────────────────────────────────────────────────────┐
│  Variation Analysis: T10/2026 vs T9/2026                       [×] │
├────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─── Summary Cards ─────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌─ Tổng NV ─────┐  ┌─ Tổng Gross ──┐  ┌─ Tổng Net ────┐    │  │
│  │  │  64 (+2)      │  │ 1,250M (+3%)  │  │ 1,050M (+2.8%) │   │  │
│  │  │  vs 62 T9     │  │ 🟢 OK         │  │ 🟢 OK          │   │  │
│  │  └───────────────┘  └────────────────┘  └────────────────┘   │  │
│  │                                                                  │  │
│  │  ┌─ Tổng BHXH ───┐  ┌─ Tổng PIT ────┐  ┌─ Anomalies ─────┐   │  │
│  │  │ 95M (+3.1%)   │  │ 152M (-2.5%)  │  │ 🔴 3 | 🟡 7 | 🟢 54│  │
│  │  │ 🟢 OK         │  │ 🟡 Cần review │  │ Click để xem chi tiết│  │
│  │  └───────────────┘  └────────────────┘  └────────────────────┘   │  │
│  │                                                                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Filter Severity: [🔴 Red] [🟡 Yellow] [🟢 Green] [All]            │
│  Sort by:        [Severity ▼]   Showing: 10 items                   │
│                                                                       │
│  [Xem theo từng NV ↓]                                                │
└────────────────────────────────────────────────────────────────────┘
```

### Screen 3: Employee-Level Detail Table

```
┌──────────────────────────────────────────────────────────────────────┐
│  Variation per Employee (Filter: 🔴 Red)                        [×]   │
├──────────────────────────────────────────────────────────────────────┤
│ NV         │ Phòng     │ Net T9   │ Net T10  │ Delta      │ Severity │
│ ───────────┼───────────┼──────────┼──────────┼────────────┼──────── │
│ Cô Hương   │ Đào tạo   │ 18.5tr   │ 12.0tr   │ -6.5tr(-35%)│ 🔴      │
│ Anh Tuấn   │ Sales     │ 22.0tr   │ 28.5tr   │ +6.5tr(+30%)│ 🔴      │
│ Chị Linh   │ Marketing │ 15.0tr   │ 11.5tr   │ -3.5tr(-23%)│ 🔴      │
├──────────────────────────────────────────────────────────────────────┤
│  ⚠ 3 NV có biến động > 20% — vui lòng investigate                    │
│                                                                        │
│  Click vào dòng để drill-down salary rules                             │
│                                                                        │
│  Nếu đã review xong và muốn proceed:                                  │
│  [Justify & Approve →]    [Quay lại Fix Issues ↩]                    │
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Drill-down Rule Comparison

**Vị trí**: Click vào 1 dòng NV (VD: Cô Hương)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Drill-down: Cô Hương — T9 vs T10                              [×]   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Rule          │ T9/2026   │ T10/2026  │ Delta        │ Note          │
│  ──────────────┼───────────┼───────────┼──────────────┼────────────── │
│  TEACH_HOURS   │ 18,750k   │ 12,500k   │ -6,250k(-33%)│ 🔴 Giờ dạy giảm│
│                │ (75h)     │ (50h)     │ (-25h)        │ -25 giờ        │
│                │           │           │               │ [Xem WE T9/T10]│
│  HSK_PREMIUM   │  1,400k   │     0     │ -1,400k      │ 🔴 Không có lớp│
│                │           │           │               │ HSK4+ trong T10│
│  EXTRA_HOURS   │  3,750k   │     0     │ -3,750k      │ Liên quan: ↑   │
│  HOLIDAY_OT    │  1,500k   │     0     │ -1,500k      │ T10 không có lễ│
│  GROSS_TEACHING│ 25,400k   │ 12,500k   │ -12,900k(-51%)│ 🔴             │
│  BHXH (8%)     │ -2,032k   │ -1,000k   │ +1,032k       │ Theo Gross     │
│  ...           │           │           │               │                │
│  NET           │ 18,500k   │ 12,000k   │ -6,500k(-35%) │ 🔴             │
│                                                                         │
│  ┌─ Root Cause Analysis (auto) ─────────────────────────────────────┐ │
│  │  Nguyên nhân chính giảm Net của Cô Hương:                         │ │
│  │  1. Số giờ dạy WORK200 giảm từ 75h → 50h (-25h)                  │ │
│  │  2. Không có lớp HSK4+ trong T10 (T9 có 20h HSK4+)                │ │
│  │  3. Không có dạy ngày lễ (T9 có 2h dạy ngày 02/9)                │ │
│  │                                                                    │ │
│  │  Action gợi ý:                                                     │ │
│  │  • Verify giờ dạy T10 với Phòng Đào tạo                            │ │
│  │  • Nếu giờ ít thật → biến động hợp lý → justify & proceed         │ │
│  │  • Nếu data missing → fix Work Entry rồi recompute payslip         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  [Xem Work Entries T10 →]  [Recompute Payslip ↻]  [Mark as Reviewed ✓]│
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 5: Justification Modal (Khi vẫn còn Red mà muốn approve)

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚠ Justify Outstanding Variations                           [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Còn 3 NV có biến động 🔴 chưa được resolve:                       │
│  • Cô Hương: Net -35%                                              │
│  • Anh Tuấn: Net +30%                                              │
│  • Chị Linh: Net -23%                                              │
│                                                                    │
│  Bạn xác nhận đã review và muốn approve batch?                     │
│                                                                    │
│  Lý do justify (bắt buộc):                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Cô Hương: giảm giờ dạy do nghỉ phép T10 (đã verify).      │  │
│  │ Anh Tuấn: có hoa hồng đặc biệt từ chiến dịch tháng 10.    │  │
│  │ Chị Linh: probation→official chuyển đổi giữa tháng.       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ☑ Tôi xác nhận đã investigate từng case                           │
│  ☑ Tôi xác nhận dữ liệu chính xác và proceed approve              │
│                                                                    │
│  [Hủy]                                       [Justify & Continue]  │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 6: Variation Reports History List

**Vị trí**: Payroll → Reports → Variation Reports

```
┌──────────────────────────────────────────────────────────────────┐
│  Lịch sử Variation Reports                                        │
├──────────────────────────────────────────────────────────────────┤
│  Kỳ      │ Tổng NV │ Red │ Yellow │ Green │ Justified │ Run by   │
│  ────────┼─────────┼─────┼────────┼───────┼───────────┼──────── │
│  10/2026 │   64    │  3  │   7    │  54   │ Yes (3)   │ Chị Hằng │
│  09/2026 │   62    │  1  │   4    │  57   │ Yes (1)   │ Chị Hằng │
│  08/2026 │   60    │  0  │   2    │  58   │ -         │ Chị Hằng │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Required | Mô tả |
|---|---|---|---|---|
| 1 | Current batch | `hr.payslip.run` | Yes | Batch đang phân tích |
| 2 | Previous batch | `hr.payslip.run` (auto-detect) | Yes | Tháng trước cùng struct |
| 3 | Payslips của 2 batches | `hr.payslip` | Yes | Tất cả lines |
| 4 | Salary rule lines | `hr.payslip.line` | Yes | Để compare per-rule |
| 5 | Thresholds | Configuration | Yes | 10%, 20% (cấu hình được) |
| 6 | Employee mapping | `hr.employee` | Yes | Liên kết payslip T9 với T10 |
| 7 | Work Entries | `hr.work.entry` | Yes | Drill-down WORK200 etc. |

### Bảng Output Data

| No | Output | Mô tả |
|---|---|---|
| 1 | `hb.variation.report` master record | Lưu snapshot |
| 2 | `hb.variation.report.line` per NV | Detail variation |
| 3 | `hb.variation.report.rule` per rule | Rule-level comparison |
| 4 | Dashboard rendering | UI hiển thị real-time |
| 5 | Justification log | Lý do approve dù còn red |
| 6 | Export Excel (optional) | Cho Finance review offline |

### Pseudo-code

```
FUNCTION run_variation_analysis(current_batch):
    
    # ── Step 1: Find previous batch ──────────────────────────
    previous_batch = SEARCH hr.payslip.run
        WHERE date_to < current_batch.date_from
          AND state = 'done'
          AND struct_type_filter SIMILAR TO current_batch
        ORDER BY date_to DESC LIMIT 1
    
    IF NOT previous_batch:
        RETURN {'status': 'no_baseline', 
                'message': 'Đây là batch đầu tiên — không có baseline để so sánh'}
    
    # ── Step 2: Compute Summary-level variations ─────────────
    summary = {}
    
    summary['employee_count'] = {
        'current': LEN(current_batch.slip_ids),
        'previous': LEN(previous_batch.slip_ids),
        'delta': LEN(current_batch.slip_ids) - LEN(previous_batch.slip_ids),
        'delta_pct': calc_pct(...)
    }
    
    FOR aggregate IN ['gross_amount', 'net_amount', 'total_bhxh', 'total_pit']:
        current_val = SUM(p[aggregate] FOR p IN current_batch.slip_ids)
        previous_val = SUM(p[aggregate] FOR p IN previous_batch.slip_ids)
        summary[aggregate] = {
            'current': current_val,
            'previous': previous_val,
            'delta': current_val - previous_val,
            'delta_pct': calc_pct(previous_val, current_val),
            'severity': classify_severity(delta_pct)
        }
    
    # ── Step 3: Compute Employee-level variations ────────────
    employee_variations = []
    
    # Map employees in both batches
    current_emp_payslips = {p.employee_id: p FOR p IN current_batch.slip_ids}
    previous_emp_payslips = {p.employee_id: p FOR p IN previous_batch.slip_ids}
    
    all_employees = SET(current_emp_payslips.keys()) | SET(previous_emp_payslips.keys())
    
    FOR emp_id IN all_employees:
        current_p = current_emp_payslips.get(emp_id)
        previous_p = previous_emp_payslips.get(emp_id)
        
        IF NOT current_p:
            # NV đã nghỉ
            employee_variations.append({
                'employee_id': emp_id,
                'status': 'left',
                'previous_net': previous_p.net_amount,
                'current_net': 0,
                'delta': -previous_p.net_amount,
                'severity': 'left',  # special
            })
            CONTINUE
        
        IF NOT previous_p:
            # NV mới
            employee_variations.append({
                'employee_id': emp_id,
                'status': 'new',
                'previous_net': 0,
                'current_net': current_p.net_amount,
                'delta': current_p.net_amount,
                'severity': 'new',  # special
            })
            CONTINUE
        
        # Normal case — compute delta
        delta = current_p.net_amount - previous_p.net_amount
        delta_pct = calc_pct(previous_p.net_amount, current_p.net_amount)
        
        employee_variations.append({
            'employee_id': emp_id,
            'status': 'continuing',
            'previous_net': previous_p.net_amount,
            'current_net': current_p.net_amount,
            'delta': delta,
            'delta_pct': delta_pct,
            'severity': classify_severity(delta_pct),  # green/yellow/red
        })
    
    # ── Step 4: Compute Rule-level variations (for red items) ─
    rule_variations = []
    
    FOR emp_var IN employee_variations:
        IF emp_var['severity'] != 'red':
            CONTINUE
        
        current_p = current_emp_payslips[emp_var['employee_id']]
        previous_p = previous_emp_payslips.get(emp_var['employee_id'])
        
        IF NOT previous_p:
            CONTINUE  # skip new/left
        
        # Compare each salary rule
        current_rules = {l.code: l.amount FOR l in current_p.line_ids}
        previous_rules = {l.code: l.amount FOR l in previous_p.line_ids}
        
        all_rules = SET(current_rules.keys()) | SET(previous_rules.keys())
        
        FOR rule_code IN all_rules:
            current_amt = current_rules.get(rule_code, 0)
            previous_amt = previous_rules.get(rule_code, 0)
            delta = current_amt - previous_amt
            
            IF delta == 0:
                CONTINUE  # skip identical
            
            rule_variations.append({
                'employee_id': emp_var['employee_id'],
                'rule_code': rule_code,
                'current': current_amt,
                'previous': previous_amt,
                'delta': delta,
                'delta_pct': calc_pct(previous_amt, current_amt) if previous_amt else None,
                'auto_explanation': generate_auto_explanation(rule_code, emp_id, current_p, previous_p)
            })
    
    # ── Step 5: Generate Root Cause Analysis ─────────────────
    FOR emp_var IN [v FOR v in employee_variations if v['severity'] == 'red']:
        emp_var['root_causes'] = analyze_root_causes(
            emp_id=emp_var['employee_id'],
            rule_vars=[r FOR r IN rule_variations if r['employee_id'] == emp_var['employee_id']]
        )
    
    # ── Step 6: Save snapshot ────────────────────────────────
    variation_report = CREATE hb.variation.report
        current_batch_id = current_batch.id
        previous_batch_id = previous_batch.id
        period_current = current_batch.date_to
        period_previous = previous_batch.date_to
        red_count = COUNT(employee_variations WHERE severity == 'red')
        yellow_count = COUNT(employee_variations WHERE severity == 'yellow')
        green_count = COUNT(employee_variations WHERE severity == 'green')
        new_count = COUNT(employee_variations WHERE status == 'new')
        left_count = COUNT(employee_variations WHERE status == 'left')
        summary_json = JSON_SERIALIZE(summary)
        run_by = current_user
        state = 'open'  # not yet justified
    
    FOR emp_var IN employee_variations:
        CREATE hb.variation.report.line (...)
    
    FOR rule_var IN rule_variations:
        CREATE hb.variation.report.rule (...)
    
    RETURN variation_report


FUNCTION classify_severity(delta_pct):
    IF delta_pct IS NULL:
        RETURN 'green'  # nothing to compare
    
    abs_pct = ABS(delta_pct)
    
    IF abs_pct < 10:
        RETURN 'green'
    ELIF abs_pct < 20:
        RETURN 'yellow'
    ELSE:
        RETURN 'red'


FUNCTION generate_auto_explanation(rule_code, emp_id, current_p, previous_p):
    # Auto-generated explanation based on rule code
    
    IF rule_code == 'TEACH_HOURS':
        # Compare work entries
        current_hours = current_p.work_entries_total_hours_WORK200
        previous_hours = previous_p.work_entries_total_hours_WORK200
        return f"Giờ dạy: {previous_hours}h → {current_hours}h ({current_hours - previous_hours:+}h)"
    
    ELIF rule_code == 'COMMISSION':
        return f"Hoa hồng từ input line"
    
    ELIF rule_code == 'BHXH':
        return f"Đóng BH theo Gross (tự động)"
    
    # ... etc
    return None
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.variation.report`** (Master)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "Variation {period}" |
| `current_batch_id` | Many2one (hr.payslip.run) | Yes | - |
| `previous_batch_id` | Many2one (hr.payslip.run) | Yes | - |
| `period_current` | Date | Yes | - |
| `period_previous` | Date | Yes | - |
| `red_count` | Integer | Yes | NV biến động > 20% |
| `yellow_count` | Integer | Yes | NV biến động 10-20% |
| `green_count` | Integer | Yes | NV biến động < 10% |
| `new_count` | Integer | Yes | NV mới |
| `left_count` | Integer | Yes | NV đã nghỉ |
| `summary_json` | Text | Yes | Summary aggregates JSON |
| `state` | Selection | Yes | open / justified / closed |
| `run_by` | Many2one (res.users) | Yes | - |
| `run_at` | Datetime | Yes | - |
| `justification` | Text | No | Lý do approve dù còn red |
| `justified_by` | Many2one (res.users) | No | - |
| `justified_at` | Datetime | No | - |

**2. Model `hb.variation.report.line`** (Per-employee)

| Field | Type | Required | Description |
|---|---|---|---|
| `report_id` | Many2one | Yes | - |
| `employee_id` | Many2one (hr.employee) | Yes | - |
| `status` | Selection | Yes | continuing / new / left |
| `previous_net` | Monetary | Yes | - |
| `current_net` | Monetary | Yes | - |
| `delta` | Monetary | Yes | - |
| `delta_pct` | Float | No | - |
| `severity` | Selection | Yes | green / yellow / red / new / left |
| `root_causes` | Text | No | Auto-generated analysis |
| `reviewed` | Boolean | No | HR đã review chưa |
| `review_note` | Text | No | Note của HR |

**3. Model `hb.variation.report.rule`** (Per-employee + per-rule)

| Field | Type | Required | Description |
|---|---|---|---|
| `report_id` | Many2one | Yes | - |
| `employee_id` | Many2one | Yes | - |
| `rule_code` | Char | Yes | TEACH_HOURS, BHXH, PIT... |
| `current_amount` | Monetary | Yes | - |
| `previous_amount` | Monetary | Yes | - |
| `delta` | Monetary | Yes | - |
| `delta_pct` | Float | No | - |
| `auto_explanation` | Text | No | Auto-generated |

**4. Configuration `hb.variation.config`** (Global thresholds)

| Field | Type | Default | Description |
|---|---|---|---|
| `yellow_threshold_pct` | Float | 10 | % để chuyển từ green → yellow |
| `red_threshold_pct` | Float | 20 | % để chuyển từ yellow → red |
| `require_justification_for_red` | Boolean | True | Bắt buộc ghi lý do khi approve còn red |

---

## **VALIDATION RULES**

| No | Rule | Action |
|---|---|---|
| **VR-001** | Current batch phải compute xong (Waiting state hoặc cao hơn) | Block nếu Draft |
| **VR-002** | Có previous batch để so sánh | Skip với info nếu không có |
| **VR-003** | Variation state = `open` không cho approve batch | Bắt buộc justify hoặc fix |
| **VR-004** | Justification bắt buộc khi còn `red_count > 0` | Block approve |
| **VR-005** | Chỉ HR Manager mới được justify | Security |
| **VR-006** | Justification phải >= 20 ký tự | Quality control |
| **VR-007** | Không sửa variation report sau khi state = closed | Read-only |
| **VR-008** | Threshold % phải >= 5 và <= 100 | Validation config |
| **VR-009** | Re-run variation analysis sẽ tạo report mới (không overwrite) | Audit trail |
| **VR-010** | NV mới (new) không tính vào red_count | Logic |

---

## **EXCEPTION FLOW**

### EX-001: Không có previous batch
- Hiển thị info "Đây là batch đầu tiên — không có baseline"
- Skip analysis, không tạo variation report
- Cho phép approve batch bình thường

### EX-002: Previous batch khác struct type
- VD: T9 là batch GV, T10 là batch GV — OK
- Nhưng T9 batch GV, T10 batch Office staff — không so sánh được
- Báo lỗi: "Không tìm thấy baseline cùng loại"

### EX-003: NV mới (chưa có previous)
- Đánh dấu `status = 'new'`, `severity = 'new'`
- Hiển thị màu xanh dương (không phải red)
- Không yêu cầu justify

### EX-004: NV đã nghỉ (chỉ có previous)
- Đánh dấu `status = 'left'`, `severity = 'left'`
- Hiển thị xám
- Không yêu cầu justify nhưng cần ghi nhận

### EX-005: HR muốn skip variation analysis hoàn toàn
- Chỉ HR Manager có quyền skip
- Phải ghi lý do skip vào audit log
- Variation Report state = `skipped`

### EX-006: Tất cả NV đều red (data corruption?)
- Cảnh báo: "Tất cả NV đều có biến động > 20% — có thể có vấn đề data"
- Đề xuất: kiểm tra recompute payslip / verify input
- Vẫn cho phép proceed nếu HR confirm

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-078** | Thresholds cấu hình được (10%, 20% default) | Cho phép tinh chỉnh theo nhu cầu Học Bá |
| **BR-PR-079** | NV mới / đã nghỉ không tính red | Vì là expected variation |
| **BR-PR-080** | Justification bắt buộc cho red items | Audit + transparency |
| **BR-PR-081** | Justification phải >= 20 ký tự, có nội dung thực sự | Tránh "OK" generic |
| **BR-PR-082** | Tự động auto-explanation cho common rules | TEACH_HOURS, BHXH, PIT... |
| **BR-PR-083** | Root cause analysis link đến drill-down screens | Để HR investigate nhanh |
| **BR-PR-084** | Variation report lưu vĩnh viễn | Phục vụ audit + trend analysis |
| **BR-PR-085** | Mỗi lần re-run tạo report mới (không overwrite) | Audit trail |
| **BR-PR-086** | HR Officer review nhưng không justify được | Bảo vệ proper review chain |
| **BR-PR-087** | HR Manager justify với note bắt buộc | Authority + traceability |
| **BR-PR-088** | Smart link đến drill-down: Work Entries, Salary Rules, Inputs | UX |
| **BR-PR-089** | Export Excel/PDF cho Finance review offline | Convenience |
| **BR-PR-090** | Variation report visible trên Payslip Batch (smart button) | Discoverability |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| `hb.variation.report` record | Master tracking |
| `hb.variation.report.line` (per-employee) | Detail variations |
| `hb.variation.report.rule` (per-rule) | Drill-down |
| Dashboard UI | Real-time hiển thị |
| Justification log | Trên Chatter của batch + report |
| Excel export (optional) | Cho Finance |
| Email digest (optional) | Cho HR Manager mỗi batch |
| Smart button "Variation" trên Payslip Batch | Quick access |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-009-01** | Wireframe Run Button | Button trên Payslip Batch |
| **UI-PR-009-02** | Wireframe Summary Dashboard | Cards tổng quan |
| **UI-PR-009-03** | Wireframe Employee Table | Bảng per NV với severity |
| **UI-PR-009-04** | Wireframe Drill-down | Rule-by-rule comparison |
| **UI-PR-009-05** | Wireframe Justification Modal | Modal nhập lý do |
| **UI-PR-009-06** | Wireframe History List | Lịch sử các variation reports |
| **UI-PR-009-07** | Wireframe Config Page | Cấu hình thresholds |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-009-001** | VN | Đây là batch payroll đầu tiên — không có baseline để so sánh | On Run (no previous) |
| **MSG-PR-009-002** | VN | Phân tích hoàn tất: 🔴 {red} | 🟡 {yellow} | 🟢 {green} | On Run Success |
| **MSG-PR-009-003** | VN | Còn {N} NV có biến động > 20% — vui lòng review hoặc justify | On Approve (block) |
| **MSG-PR-009-004** | VN | Justification phải có ít nhất 20 ký tự — vui lòng mô tả rõ ràng | On Justify (validate) |
| **MSG-PR-009-005** | VN | Chỉ HR Manager mới có quyền justify red items | On Justify (security) |
| **MSG-PR-009-006** | VN | Đã ghi nhận justification cho {N} items. Batch sẵn sàng approve. | On Justify Success |
| **MSG-PR-009-007** | VN | NV {name}: Net {previous} → {current} ({delta:+}, {delta_pct:+.1f}%) | Per row in table |
| **MSG-PR-009-008** | VN | Tất cả NV đều có biến động > 20% — kiểm tra dữ liệu nguồn? | On High Anomaly Rate |
| **MSG-PR-009-009** | VN | NV {name} có giờ dạy giảm từ {prev}h → {curr}h | Auto-explanation |
| **MSG-PR-009-010** | VN | Skip variation analysis cho batch này — lý do: {reason} | On Skip (audit log) |
| **MSG-PR-009-011** | VN | Đã export Excel variation report cho batch {batch_ref} | On Export |
| **MSG-PR-009-012** | VN | Re-run variation tạo bản mới (#{N}) — bản cũ vẫn được lưu | On Re-run |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | Current Payslip Batch state >= Waiting (đã compute) | Module Payroll |
| 2 | Có Payslip Batch trước đó cùng loại (cho first analysis) | Module Payroll |
| 3 | `hb.variation.config` thresholds đã cấu hình | Function này |
| 4 | Module `hb_payroll_variation_report` đã cài | Function này |
| 5 | HR user có quyền truy cập Payroll | Chapter 5.4.11 |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | `hb.variation.report` được tạo (state = open) |
| 2 | Dashboard hiển thị real-time |
| 3 | HR có thể drill-down để investigate |
| 4 | Sau khi justify: state = justified, batch có thể approve |
| 5 | Audit log đầy đủ |
| 6 | Report lưu vĩnh viễn, dùng cho trend analysis |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Click "🔍 Variation Analysis" trên Payslip Batch | HR Officer / Manager |
| 2 | Auto-trigger sau khi Compute Sheet xong (optional config) | Hệ thống |
| 3 | Yêu cầu re-run sau khi recompute payslip | HR Officer |
| 4 | Pre-approval gate (block approve nếu chưa run analysis) | Hệ thống (optional) |
