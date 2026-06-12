# **FS — FUNC-PR-005**
# **Báo Cáo Thuế TNCN Định Dạng eTax**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-005 |
| **Function Name** | Báo Cáo Tờ Khai Khấu Trừ Thuế TNCN Hàng Tháng (eTax) |
| **Custom Module** | `hb_payroll_etax_report` |
| **GAP Reference** | CUS-PR-005 (Chapter 4) |
| **Phase** | Phase 1 — MVP go-live (Bắt buộc) |
| **Độ phức tạp** | Trung bình |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS cho function báo cáo thuế TNCN | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này **tự động sinh tờ khai khấu trừ thuế TNCN hàng tháng** ở định dạng tương thích cổng eTax của Tổng cục Thuế Việt Nam (theo mẫu **Tờ khai 05/KK-TNCN** — khấu trừ thuế TNCN hàng tháng). Báo cáo tổng hợp thu nhập tính thuế, các khoản giảm trừ, và số thuế TNCN đã khấu trừ của toàn bộ nhân viên trong tháng, export ra file XML hoặc Excel theo schema eTax.

Function này có **cross-validation quan trọng**: kiểm tra tính nhất quán giữa số người phụ thuộc đã đăng ký (từ Module Employee — `hr.dependent`) với số tiền giảm trừ đã áp dụng trong payslip — flag bất kỳ inconsistency nào.

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-08** Nhập tay eTax | Export trực tiếp file đúng định dạng eTax |
| **PP-PR-09** Khó quyết toán cuối năm | Dữ liệu hàng tháng được lưu chuẩn → quyết toán năm (FUNC-PR-006) dễ aggregate |
| **PP-PR-04** Audit trail | Lưu lịch sử submit + cross-validation log |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Payroll** | Đọc các dòng salary rule code = `PIT`, `INSURANCE_BASE`, `TAXABLE_INCOME`, `PERSONAL_DEDUCTION`, `DEPENDENT_DEDUCTION` |
| **Module Employee** | Đọc `x_pit_code` (Mã số thuế cá nhân), `hr.dependent` (danh sách người phụ thuộc) |
| **Chapter 5 (5.4.3 + 5.4.4)** | Tham chiếu biểu thuế 7 bậc + giảm trừ bản thân/người phụ thuộc |
| **FUNC-PR-006** | Cuối năm dùng lại dữ liệu monthly cho quyết toán |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **Finance (Payroll Accountant)** | Trigger sinh báo cáo + submit (`SEC-PR-04`) |
| **HR Manager** | View (`SEC-PR-03`) |

---

## **FUNCTION FLOW**

```
┌─────────────────────────────────────────────────────────┐
│  PRE: Payslip Batch tháng đã ở state 'done' + approved │
└─────────────────────┬───────────────────────────────────┘
                      ▼
       ┌───────────────────────────────────┐
       │ Finance vào eTax Report menu      │
       │ Bấm "Tạo Tờ Khai Tháng"           │
       └────────────────┬──────────────────┘
                        ▼
       ┌───────────────────────────────────┐
       │ Wizard:                            │
       │ - Chọn kỳ (tháng/năm)              │
       │ - Cơ quan thuế quản lý             │
       │ - Mã số thuế công ty               │
       │ - Loại tờ khai (05/KK-TNCN)        │
       └────────────────┬──────────────────┘
                        ▼
       ┌───────────────────────────────────┐
       │ Aggregate Engine                   │
       │ - Lặp qua payslips                 │
       │ - Tính thu nhập, giảm trừ, PIT     │
       │ - Phân theo cư trú / không cư trú  │
       └────────────────┬──────────────────┘
                        ▼
       ┌────────────────────────────────────┐
       │ Cross-Validation                   │
       │ 1. NV thiếu x_pit_code?            │
       │ 2. Dependent deduction khớp với    │
       │    số dependent đang hiệu lực?     │
       │ 3. PIT bracket áp dụng đúng?       │
       └────┬─────────────────┬─────────────┘
            │ Sai lệch         │ OK
            ▼                  ▼
   ┌─────────────────┐  ┌──────────────────────┐
   │ Show warnings + │  │ Build XML / XLSX     │
   │ list NV cần fix │  │ theo eTax schema     │
   └─────────────────┘  └──────────┬───────────┘
                                   ▼
                        ┌──────────────────────┐
                        │ Save attachment +    │
                        │ create etax_report   │
                        │ record               │
                        └──────────┬───────────┘
                                   ▼
                        ┌──────────────────────┐
                        │ Finance download +   │
                        │ upload lên cổng eTax │
                        │ thủ công             │
                        └──────────┬───────────┘
                                   ▼
                        ┌──────────────────────┐
                        │ Finance đánh dấu     │
                        │ state = 'submitted'  │
                        │ + nhập mã tờ khai    │
                        └──────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: eTax Reports Menu

**Vị trí**: Payroll → Reports → PIT Withholding Reports (Tờ khai TNCN)

```
┌──────────────────────────────────────────────────────────────────┐
│  Tờ Khai Khấu Trừ Thuế TNCN                       [+ Tạo Mới]   │
├──────────────────────────────────────────────────────────────────┤
│  Filter: [Năm 2026 ▼]  [Trạng thái ▼]                            │
├──────────────────────────────────────────────────────────────────┤
│  Kỳ      │ Số NV │ Tổng TN tính thuế │ Tổng PIT       │ Trạng thái│
│  ────────┼───────┼──────────────────┼─────────────────┼──────────  │
│  10/2026 │  62   │ 1,245,000,000    │ 152,300,000 VND │✅Submitted│
│  09/2026 │  60   │ 1,198,000,000    │ 145,750,000 VND │✅Submitted│
│  08/2026 │  58   │ 1,156,000,000    │ 138,420,000 VND │⚠ Draft   │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Create eTax Report Wizard

```
┌──────────────────────────────────────────────────────────────────┐
│  Tạo Tờ Khai Khấu Trừ Thuế TNCN                            [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Kỳ tờ khai (*)        : [Tháng 10 ▼] [Năm 2026 ▼]              │
│  Mã số thuế Cty (*)    : 0123456789 (read-only từ company)        │
│  Cơ quan thuế (*)      : [Chi cục thuế Quận Cầu Giấy ▼]          │
│  Loại tờ khai (*)      : ● 05/KK-TNCN (Khấu trừ hàng tháng)       │
│                                                                    │
│  Loại NV bao gồm:                                                  │
│    ☑ Cá nhân cư trú (Resident)                                    │
│    ☑ Cá nhân không cư trú (Non-resident)                          │
│                                                                    │
│  Định dạng output (*)  : ● XML (theo schema eTax)                 │
│                          ○ XLSX (tham khảo)                       │
│                                                                    │
│  Cross-validation:                                                 │
│    ☑ Kiểm tra mã số thuế cá nhân                                  │
│    ☑ Kiểm tra giảm trừ người phụ thuộc                            │
│    ☑ Kiểm tra biểu thuế áp dụng đúng bậc                          │
│                                                                    │
│  [Hủy]                                  [Sinh Báo Cáo Preview]    │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 3: Report Detail (Preview)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Tờ Khai TNCN — Tháng 10/2026 — Draft                          [×]   │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─── Thông tin chung ──────────────────────────────────────────┐   │
│  │  Cty: TT Tiếng Trung Học Bá Education                         │   │
│  │  MST: 0123456789                                                │   │
│  │  Kỳ: 10/2026                                                    │   │
│  │  Cơ quan thuế: Chi cục thuế Quận Cầu Giấy                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─── Cá nhân CƯ TRÚ ─────────────────────────────────────────────┐   │
│  │  Số NV: 58                                                       │   │
│  │  Tổng thu nhập chịu thuế: 1,200,000,000 VND                    │   │
│  │  Tổng giảm trừ bản thân (11M × 58):  638,000,000 VND           │   │
│  │  Tổng giảm trừ người phụ thuộc (35 NPT × 4.4M): 154,000,000   │   │
│  │  Tổng thu nhập tính thuế: 408,000,000 VND                       │   │
│  │  Tổng thuế TNCN: 145,200,000 VND                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─── Cá nhân KHÔNG CƯ TRÚ ───────────────────────────────────────┐   │
│  │  Số NV: 4 (giáo viên ngoại)                                     │   │
│  │  Tổng thu nhập: 45,000,000 VND                                  │   │
│  │  Thuế suất: 20% (flat)                                           │   │
│  │  Tổng thuế: 9,000,000 VND                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ⚠ Cảnh báo:                                                            │
│  - 2 NV thiếu mã số thuế cá nhân                                       │
│  - 1 NV có giảm trừ người phụ thuộc không khớp danh sách đã đăng ký   │
│                                                                         │
│  [Quay lại] [Export XML] [Export XLSX] [Đánh dấu đã nộp]               │
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Cross-Validation Warning Modal

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚠ Cảnh báo Cross-Validation                                [×]   │
├──────────────────────────────────────────────────────────────────┤
│  Phát hiện sai lệch dữ liệu sau:                                  │
│                                                                    │
│  THIẾU MÃ SỐ THUẾ (2 NV):                                         │
│  • Nguyễn Văn X — chưa có x_pit_code                              │
│  • Lê Thị Y — mã thuế không đúng định dạng (chỉ 8 chữ số)         │
│                                                                    │
│  GIẢM TRỪ NGƯỜI PHỤ THUỘC KHÔNG KHỚP (1 NV):                      │
│  • Trần Văn Z (E-2026-018):                                        │
│    - Payslip giảm trừ: 8,800,000 VND (= 2 NPT)                    │
│    - Đăng ký NPT hiệu lực: 1 người (chênh 1 NPT)                  │
│    → Cần kiểm tra & cập nhật                                      │
│                                                                    │
│  [Đóng & Sửa NV]    [Xem Báo Cáo dù có sai lệch →]               │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Điều kiện |
|---|---|---|---|
| 1 | Kỳ | `wizard.month`, `wizard.year` | Required |
| 2 | Loại tờ khai | `wizard.declaration_type` | 05/KK-TNCN |
| 3 | Cơ quan thuế | `wizard.tax_office_id` | Required |
| 4 | Payslips trong kỳ | `hr.payslip` | state=done, date_to trong kỳ |
| 5 | Mã số thuế NV | `hr.employee.x_pit_code` | Required cho cá nhân cư trú |
| 6 | Loại cư trú | `hr.employee.x_tax_residence_status` | resident / non_resident |
| 7 | Thu nhập chịu thuế | `hr.payslip.line` code='TAXABLE_INCOME' | Per payslip |
| 8 | Giảm trừ bản thân | `hr.payslip.line` code='PERSONAL_DEDUCTION' | 11.000.000 |
| 9 | Giảm trừ người phụ thuộc | `hr.payslip.line` code='DEPENDENT_DEDUCTION' | Per dependent |
| 10 | Thuế TNCN | `hr.payslip.line` code='PIT' | Per payslip |
| 11 | Người phụ thuộc đang hiệu lực | `hr.dependent` | date_from <= period AND (date_to IS NULL OR date_to >= period) |
| 12 | Biểu thuế | `Salary Rule Parameters` PIT brackets | Tham chiếu 5.4.3 |

### Bảng Output Data

| No | Output | Định dạng |
|---|---|---|
| 1 | File XML | Theo eTax schema 05/KK-TNCN |
| 2 | File XLSX preview | Tham khảo / lưu trữ |
| 3 | `hb.etax.report` record | DB |
| 4 | Cross-validation log | List warnings |

### Cấu trúc XML eTax (Schema gợi ý)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<HSoTKhaiT>
  <HSoKhaiT>
    <TTinChung>
      <TTinTKhaiThue>
        <maToKhai>05/KK-TNCN</maToKhai>
        <KyKKhaiThue>10/2026</KyKKhaiThue>
        <loaiToKhai>Tờ khai chính thức</loaiToKhai>
        <ngayLapTKhai>2026-11-05</ngayLapTKhai>
      </TTinTKhaiThue>
      <TTinNNT>
        <mst>0123456789</mst>
        <tenNNT>Trung tâm Tiếng Trung Học Bá Education</tenNNT>
        <dchiNNT>...</dchiNNT>
      </TTinNNT>
      <TTinCQT>
        <maCQT>03003</maCQT>
        <tenCQT>Chi cục thuế Quận Cầu Giấy</tenCQT>
      </TTinCQT>
    </TTinChung>
    <NDKKhaiThue>
      <ToKhaiTNCN>
        <!-- Cá nhân cư trú -->
        <CNCuTru>
          <tongSoNV>58</tongSoNV>
          <tongTNCT>1200000000</tongTNCT>
          <tongGTKhauTru>638000000</tongGTKhauTru>
          <tongGTNPT>154000000</tongGTNPT>
          <tongTNTinhThue>408000000</tongTNTinhThue>
          <tongThueTNCN>145200000</tongThueTNCN>
          <DSachCN>
            <CN>
              <stt>1</stt>
              <maSoThue>8123456789</maSoThue>
              <hoTen>Nguyễn Thị A</hoTen>
              <tnChiuThue>15000000</tnChiuThue>
              <gtbThan>11000000</gtbThan>
              <gtNPT>4400000</gtNPT>
              <soNPT>1</soNPT>
              <tnTinhThue>3525000</tnTinhThue>
              <thueTNCN>176250</thueTNCN>
            </CN>
            <!-- ... -->
          </DSachCN>
        </CNCuTru>
        <!-- Cá nhân không cư trú -->
        <CNKCuTru>
          <tongSoNV>4</tongSoNV>
          <tongTNCT>45000000</tongTNCT>
          <tongThueTNCN>9000000</tongThueTNCN>
          <DSachCN>
            <CN>
              <stt>1</stt>
              <hoChieu>P12345678</hoChieu>
              <hoTen>John Smith</hoTen>
              <tnChiuThue>15000000</tnChiuThue>
              <thueTNCN>3000000</thueTNCN>
            </CN>
            <!-- ... -->
          </DSachCN>
        </CNKCuTru>
      </ToKhaiTNCN>
    </NDKKhaiThue>
  </HSoKhaiT>
</HSoTKhaiT>
```

*(Schema chính xác lấy từ tài liệu kỹ thuật cổng eTax tại thời điểm triển khai)*

### Pseudo-code

```
FUNCTION generate_etax_report(wizard):
    
    # Step 1: Validate kỳ
    payslips = SEARCH hr.payslip
        WHERE date_to.month = wizard.month
          AND date_to.year = wizard.year
          AND state = 'done'
    
    IF NOT payslips:
        RAISE ValidationError("Chưa có payslip Done nào trong kỳ")
    
    # Step 2: Tách resident vs non-resident
    resident_payslips = [p FOR p IN payslips IF p.employee.x_tax_residence_status == 'resident']
    nonresident_payslips = [p FOR p IN payslips IF p.employee.x_tax_residence_status == 'non_resident']
    
    # Step 3: Cross-Validation
    warnings = []
    
    # 3.1 Check x_pit_code cho resident
    FOR p IN resident_payslips:
        IF NOT p.employee.x_pit_code 
            OR NOT REGEX_MATCH(p.employee.x_pit_code, r'^\d{10}$'):
            warnings.append({
                'type': 'missing_pit_code',
                'employee': p.employee,
            })
    
    # 3.2 Check dependent deduction consistency
    FOR p IN resident_payslips:
        dep_deduction_amount = p.line('DEPENDENT_DEDUCTION').amount
        dep_count_from_payslip = ROUND(dep_deduction_amount / 4400000)
        
        active_dependents = SEARCH hr.dependent
            WHERE employee_id = p.employee.id
              AND date_from <= p.date_to
              AND (date_to IS NULL OR date_to >= p.date_from)
        
        IF dep_count_from_payslip != LEN(active_dependents):
            warnings.append({
                'type': 'dependent_mismatch',
                'employee': p.employee,
                'payslip_dep_count': dep_count_from_payslip,
                'registered_count': LEN(active_dependents),
            })
    
    # 3.3 Check PIT bracket áp dụng đúng
    # (Optional — re-compute và so sánh)
    
    IF warnings AND NOT wizard.skip_warnings:
        RAISE warning, show modal with `warnings`
    
    # Step 4: Build report data
    resident_lines = []
    FOR p IN resident_payslips:
        IF p.employee in [w.employee FOR w IN warnings IF w.type == 'missing_pit_code']:
            CONTINUE  # skip missing pit code
        
        resident_lines.append({
            'employee': p.employee,
            'pit_code': p.employee.x_pit_code,
            'taxable_income_pre_deduction': p.line('GROSS_TAXABLE').amount,
            'personal_deduction': p.line('PERSONAL_DEDUCTION').amount,
            'dependent_deduction': p.line('DEPENDENT_DEDUCTION').amount,
            'dependent_count': ROUND(p.line('DEPENDENT_DEDUCTION').amount / 4400000),
            'taxable_income': p.line('TAXABLE_INCOME').amount,
            'pit_amount': ABS(p.line('PIT').amount),
        })
    
    nonresident_lines = []
    FOR p IN nonresident_payslips:
        nonresident_lines.append({
            'employee': p.employee,
            'passport': p.employee.passport_id,
            'income': p.line('GROSS_TAXABLE').amount,
            'pit_amount': ABS(p.line('PIT').amount),  # flat 20%
        })
    
    # Step 5: Generate file
    IF wizard.output_format == 'xml':
        file_bytes = build_xml_etax_schema(
            company = wizard.company,
            tax_office = wizard.tax_office_id,
            period = (wizard.month, wizard.year),
            resident_lines = resident_lines,
            nonresident_lines = nonresident_lines,
        )
    ELSE:
        file_bytes = build_xlsx_preview(resident_lines, nonresident_lines)
    
    # Step 6: Create attachment + record
    attachment = CREATE ir.attachment(...)
    etax_report = CREATE hb.etax.report
        period = f"{wizard.year}-{wizard.month:02d}"
        declaration_type = '05/KK-TNCN'
        tax_office_id = wizard.tax_office_id
        resident_count = LEN(resident_lines)
        nonresident_count = LEN(nonresident_lines)
        total_taxable_income = SUM(resident_lines['taxable_income'])
        total_pit = SUM(resident_lines['pit_amount']) + SUM(nonresident_lines['pit_amount'])
        attachment_id = attachment.id
        state = 'draft'
        warnings_log = warnings  # JSON
        generated_by = current_user
    
    # Step 7: Log Chatter
    etax_report.message_post(body = "Đã sinh tờ khai...")
    
    RETURN etax_report
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.tax.office`** (Configuration - cơ quan thuế)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char | Yes | Tên cơ quan thuế |
| `code` | Char | Yes | Mã CQT do TCT cấp |
| `address` | Char | No | Địa chỉ |
| `province_id` | Many2one (res.country.state) | No | Tỉnh/TP |
| `company_id` | Many2one (res.company) | Yes | - |
| `active` | Boolean | No | True |

**2. Model `hb.etax.report`** (Lịch sử tờ khai)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "PIT {period}" |
| `period` | Char | Yes | YYYY-MM |
| `declaration_type` | Selection | Yes | 05/KK-TNCN |
| `tax_office_id` | Many2one | Yes | - |
| `resident_count` | Integer | Yes | Số NV cư trú |
| `nonresident_count` | Integer | Yes | Số NV không cư trú |
| `total_taxable_income` | Monetary | Yes | Tổng TN tính thuế |
| `total_personal_deduction` | Monetary | Yes | Tổng GT bản thân |
| `total_dependent_deduction` | Monetary | Yes | Tổng GT NPT |
| `total_pit_amount` | Monetary | Yes | Tổng thuế TNCN |
| `attachment_id` | Many2one (ir.attachment) | Yes | File XML/XLSX |
| `submission_code` | Char | No | Mã tờ khai trả từ eTax |
| `state` | Selection | Yes | draft / generated / submitted / accepted / rejected |
| `submitted_date` | Date | No | - |
| `warnings_log` | Text (JSON) | No | Cross-validation warnings |
| `notes` | Text | No | - |

**3. Model `hb.etax.report.line`** (Dòng chi tiết)

| Field | Type | Required |
|---|---|---|
| `report_id` | Many2one (hb.etax.report) | Yes |
| `employee_id` | Many2one (hr.employee) | Yes |
| `is_resident` | Boolean | Yes |
| `pit_code` | Char | No (Yes nếu resident) |
| `passport_id` | Char | No (Yes nếu non-resident) |
| `taxable_income_pre` | Monetary | Yes |
| `personal_deduction` | Monetary | Yes (chỉ resident) |
| `dependent_deduction` | Monetary | Yes (chỉ resident) |
| `dependent_count` | Integer | Yes (chỉ resident) |
| `taxable_income` | Monetary | Yes |
| `pit_amount` | Monetary | Yes |

**4. Extend `hr.employee`**

| Field | Type | Required | Description |
|---|---|---|---|
| `x_tax_residence_status` | Selection | Yes | resident / non_resident |

---

## **VALIDATION RULES**

| No | Rule | Action |
|---|---|---|
| **VR-001** | Payslip Batch tháng phải state `done` | Block |
| **VR-002** | NV cư trú phải có `x_pit_code` 10 digits | Warning + cho skip |
| **VR-003** | NV không cư trú phải có `passport_id` | Warning + cho skip |
| **VR-004** | Dependent deduction phải khớp số NPT đăng ký | Warning + show diff |
| **VR-005** | Không sinh lại tờ khai đã submitted | Block (cần reset) |
| **VR-006** | `tax_office_id` phải active | Block |
| **VR-007** | Mã số thuế cty phải đầy đủ | Block |
| **VR-008** | Mỗi kỳ chỉ 1 tờ khai active | Block duplicate |
| **VR-009** | `submission_code` từ eTax phải nhập khi đánh dấu submitted | Required |
| **VR-010** | Resident vs non-resident phải có ít nhất 1 NV | Warning nếu cả 2 đều 0 |

---

## **EXCEPTION FLOW**

### EX-001: NV thiếu mã số thuế
- Cross-validation modal
- Cho phép: Sửa NV / Skip & continue
- Skip → log warning

### EX-002: Dependent deduction không khớp
- Modal cảnh báo chi tiết (số đăng ký vs số trên payslip)
- Cho phép: Đi sửa Dependent / Recompute payslip / Tiếp tục
- Log đầy đủ vào `warnings_log` JSON

### EX-003: Lỗi schema XML
- Catch exception, hiển thị lỗi
- Không tạo record

### EX-004: NV không cư trú thiếu hộ chiếu
- Warning (vì cá nhân không cư trú phải có hộ chiếu để khai thuế)
- Cho phép skip với warning rõ ràng

### EX-005: Sinh lại tờ khai đã submitted
- Block + yêu cầu reset (chỉ HR Manager)
- Log lý do reset

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-029** | Phân biệt rõ resident vs non-resident | Resident dùng biểu lũy tiến, non-resident áp 20% flat |
| **BR-PR-030** | Mã số thuế chỉ áp dụng cho resident | Non-resident dùng hộ chiếu |
| **BR-PR-031** | Dependent deduction tính theo số NPT đang hiệu lực trong kỳ | Snapshot theo period_end |
| **BR-PR-032** | Tổng thuế TNCN khớp với salary rule PIT đã tính ở Chapter 5 | Không tính lại — chỉ aggregate |
| **BR-PR-033** | Mỗi kỳ chỉ 1 tờ khai active | Reset cũ trước khi sinh mới |
| **BR-PR-034** | Submission code bắt buộc khi state = submitted | Tra cứu lại từ eTax |
| **BR-PR-035** | Audit log đầy đủ | Generate, Reset, Submit, Reject |
| **BR-PR-036** | Cross-validation log lưu vĩnh viễn | Phục vụ audit |
| **BR-PR-037** | Data hàng tháng dùng cho quyết toán năm (FUNC-PR-006) | Lưu cấu trúc giống nhau |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| File XML | Theo eTax schema, upload lên cổng |
| File XLSX preview | Internal review |
| `hb.etax.report` record | Lưu trữ vĩnh viễn |
| Smart button "Xem tờ khai" trên Payslip Batch | Quick access |
| Dashboard PIT trends | 12 tháng PIT (smart chart) |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-005-01** | Wireframe eTax List | Danh sách tờ khai |
| **UI-PR-005-02** | Wireframe Create Wizard | Wizard tạo tờ khai |
| **UI-PR-005-03** | Wireframe Report Detail | Detail resident + non-resident |
| **UI-PR-005-04** | Wireframe Validation Warnings | Modal cross-validation |
| **UI-PR-005-05** | Wireframe Tax Office Config | Configuration cho `hb.tax.office` |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-005-001** | VN | Chưa có payslip Done nào trong kỳ {month}/{year} | On Validate |
| **MSG-PR-005-002** | VN | Có {N} NV thiếu mã số thuế cá nhân. Bạn muốn sửa hay bỏ qua? | On Cross-Validation |
| **MSG-PR-005-003** | VN | Có {N} NV có giảm trừ người phụ thuộc không khớp đăng ký | On Cross-Validation |
| **MSG-PR-005-004** | VN | Tờ khai TNCN tháng {month}/{year} sinh thành công: {N} NV, tổng thuế {amount} VND | On Generate Success |
| **MSG-PR-005-005** | VN | Đã có tờ khai TNCN {period}. Reset cũ trước khi sinh mới. | On Duplicate |
| **MSG-PR-005-006** | VN | Mã số thuế "{code}" của NV {name} không đúng định dạng (cần 10 chữ số) | On Validate |
| **MSG-PR-005-007** | VN | NV {name} là cá nhân không cư trú nhưng thiếu thông tin hộ chiếu | On Validate |
| **MSG-PR-005-008** | VN | Đã đánh dấu submitted với mã tờ khai {code} | On Submit |
| **MSG-PR-005-009** | VN | Lỗi sinh XML: {error}. Kiểm tra cấu hình schema. | On Generate Error |
| **MSG-PR-005-010** | VN | Chỉ HR Manager mới có quyền reset tờ khai submitted | On Reset (security) |
| **MSG-PR-005-011** | VN | Tờ khai đã được Cơ quan thuế từ chối với lý do: {reason} | On Mark Rejected |
| **MSG-PR-005-012** | VN | Giảm trừ NPT của {name}: payslip = {N} người, đăng ký = {M} người. Chênh lệch! | On Cross-Validation |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | Payslip Batch tháng state = `done` | Module Payroll |
| 2 | NV cư trú có `x_pit_code` 10 digits | Module Employee (G-04) |
| 3 | NV có `x_tax_residence_status` (resident/non-resident) | Module Employee |
| 4 | Người phụ thuộc đã đăng ký trong `hr.dependent` (FUNC-EMP-003) | Module Employee (G-12) |
| 5 | `hb.tax.office` đã có ít nhất 1 record | Function này |
| 6 | Salary rules PIT/PERSONAL_DEDUCTION/DEPENDENT_DEDUCTION đã cấu hình | Chapter 5.4.3 + 5.4.4 |
| 7 | Schema XML eTax (version mới nhất) đã cập nhật | IT team |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | File XML/XLSX tạo và lưu attachment |
| 2 | `hb.etax.report` state = `generated` |
| 3 | Cross-validation log đầy đủ trong `warnings_log` |
| 4 | Finance download file để upload lên cổng eTax |
| 5 | Sau khi nộp, đánh dấu submitted + nhập submission_code |
| 6 | Audit log đầy đủ |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Bấm "Tạo Tờ Khai Tháng" từ eTax menu | Finance (`SEC-PR-04`) |
| 2 | Smart button trên Payslip Batch | Finance |
| 3 | Auto reminder CRON khi qua ngày 20 hàng tháng mà chưa nộp | Hệ thống |
