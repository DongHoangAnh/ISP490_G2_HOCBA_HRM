# **FS — FUNC-PR-004**
# **Báo Cáo Đóng BHXH Định Dạng iBHXH**

---

## **COVER**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-004 |
| **Function Name** | Báo Cáo Đóng BHXH Định Dạng iBHXH |
| **Custom Module** | `hb_payroll_bhxh_report` |
| **GAP Reference** | CUS-PR-004 (Chapter 4) |
| **Phase** | Phase 1 — MVP go-live (Bắt buộc) |
| **Độ phức tạp** | Trung bình |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS cho function báo cáo BHXH | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này **tự động sinh báo cáo đóng BHXH hàng tháng** ở định dạng tương thích với cổng iBHXH (Cơ quan Bảo hiểm Xã hội Việt Nam), tổng hợp các khoản đóng BHXH, BHYT, BHTN của toàn bộ nhân viên trong tháng. Báo cáo được export ra file XML hoặc Excel theo đúng schema mà cổng iBHXH yêu cầu, giúp Finance không phải nhập tay lại dữ liệu lên cổng — vốn hiện đang tốn 1 ngày làm việc/tháng và là nguồn lỗi sao chép thường xuyên.

Function này cũng giải quyết bài toán **validation trước khi nộp**: highlight các nhân viên thiếu Số Sổ BHXH (`x_social_insurance_number` từ G-07 Module Employee) hoặc mức đóng bất thường (vượt trần, dưới sàn).

### Business Requirement

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-08** Nhập tay iBHXH | Export trực tiếp file đúng định dạng iBHXH |
| **PP-PR-04** Không có audit trail | Lưu lịch sử mỗi lần submit + Chatter log |
| **PP-PR-03** Sai số khi tính BHXH | Đối chiếu với rule INSURANCE_BASE đã cấu hình ở Chapter 5 |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Payroll** | Đọc các dòng salary rule code = `BHXH`, `BHYT`, `BHTN` (cả employee + employer portion) trong các payslip ở state Done |
| **Module Employee** | Đọc `x_social_insurance_number` (Số Sổ BHXH), `x_health_insurance_number` (Mã thẻ BHYT) |
| **Chapter 5 (5.4.2)** | Tham chiếu các Salary Rule Parameters đã cấu hình (PARAM-PR-01 đến 09) |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **Finance (Payroll Accountant)** | Trigger sinh báo cáo + download + đánh dấu submitted (`SEC-PR-04`) |
| **HR Manager** | View báo cáo (`SEC-PR-03`) |

---

## **FUNCTION FLOW**

```
┌─────────────────────────────────────────────────────────┐
│  PRE: Payslip Batch tháng đã ở state 'done' + approved │
└─────────────────────┬───────────────────────────────────┘
                      ▼
       ┌───────────────────────────────────┐
       │ Finance vào BHXH Report menu      │
       │ Bấm "Tạo Báo Cáo Tháng"           │
       └────────────────┬──────────────────┘
                        ▼
       ┌───────────────────────────────────┐
       │ Wizard:                            │
       │ - Chọn kỳ (tháng/năm)              │
       │ - Chọn đơn vị BHXH (nếu nhiều CN)  │
       │ - Loại báo cáo: D02-TS / D01-TS    │
       └────────────────┬──────────────────┘
                        ▼
       ┌───────────────────────────────────┐
       │ Aggregate Engine                   │
       │ - Lặp qua payslips tháng           │
       │ - Group by employee                │
       │ - Tổng hợp BHXH+BHYT+BHTN          │
       └────────────────┬──────────────────┘
                        ▼
            ┌──────────────────────────┐
            │ Validation Gate          │
            │ NV thiếu Số sổ BHXH?     │
            └───┬─────────────────┬────┘
                │ Có               │ Không
                ▼                  ▼
       ┌─────────────────┐  ┌──────────────────────┐
       │ Warning Modal   │  │ Build XML / XLSX     │
       │ List NV thiếu   │  │ theo iBHXH schema    │
       │ → Sửa rồi quay  │  └──────────┬───────────┘
       │   lại           │             ▼
       └─────────────────┘  ┌──────────────────────┐
                            │ Save attachment +    │
                            │ create bhxh_report   │
                            │ record               │
                            └──────────┬───────────┘
                                       ▼
                            ┌──────────────────────┐
                            │ Download file        │
                            │ Finance upload lên   │
                            │ cổng iBHXH thủ công  │
                            └──────────┬───────────┘
                                       ▼
                            ┌──────────────────────┐
                            │ Finance đánh dấu     │
                            │ state = 'submitted'  │
                            │ + ghi mã hồ sơ iBHXH │
                            └──────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: BHXH Reports Menu (Danh sách báo cáo đã sinh)

**Vị trí**: Payroll → Reports → BHXH Contribution Reports

```
┌──────────────────────────────────────────────────────────────────┐
│  BHXH Contribution Reports                          [+ Tạo Mới]  │
├──────────────────────────────────────────────────────────────────┤
│  Filter: [Năm 2026 ▼] [Trạng thái ▼]                             │
├──────────────────────────────────────────────────────────────────┤
│  Kỳ      │ Loại    │ Số NV │ Tổng đóng       │ Trạng thái │ Mã  │
│  ────────┼─────────┼───────┼─────────────────┼────────────┼─── │
│  10/2026 │ D02-TS  │  68   │ 285,420,000 VND │ ✅ Submitted│#123│
│  09/2026 │ D02-TS  │  65   │ 274,180,000 VND │ ✅ Submitted│#117│
│  08/2026 │ D02-TS  │  63   │ 268,900,000 VND │ ⚠ Draft    │  - │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 2: Create BHXH Report Wizard

```
┌──────────────────────────────────────────────────────────────────┐
│  Tạo Báo Cáo BHXH Tháng                                    [×]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Kỳ báo cáo (*)        : [Tháng 10 ▼] [Năm 2026 ▼]              │
│  Đơn vị BHXH (*)       : [BHXH Quận Cầu Giấy - 01010 ▼]          │
│  Mã đơn vị tại BHXH    : [HG2024-0125] (read-only)                │
│  Loại báo cáo (*)      : ○ D02-TS (Tăng giảm BHXH)               │
│                          ● D01-TS (Khai báo hàng tháng)           │
│                                                                    │
│  Bao gồm:                                                          │
│    ☑ BHXH (Bảo hiểm xã hội)                                       │
│    ☑ BHYT (Bảo hiểm y tế)                                         │
│    ☑ BHTN (Bảo hiểm thất nghiệp)                                  │
│                                                                    │
│  Định dạng output (*)  : ● XML (theo schema iBHXH)                │
│                          ○ XLSX (tham khảo)                       │
│                                                                    │
│  ⚠ Đảm bảo Payslip Batch tháng đã được Done và Approved.         │
│                                                                    │
│  [Hủy]                              [Sinh Báo Cáo Preview]        │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 3: BHXH Report Detail (Preview trước khi export)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Báo Cáo BHXH — Tháng 10/2026 — Draft                         [×]   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─── Thông tin chung ─────────────────────────────────────────┐   │
│  │  Đơn vị: TT Tiếng Trung Học Bá Education                    │   │
│  │  Mã ĐV BHXH: HG2024-0125                                     │   │
│  │  Kỳ: 10/2026                                                  │   │
│  │  Tổng NV trong kỳ: 68                                         │   │
│  │  Tổng đóng (NV+ĐV): 285,420,000 VND                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─── Chi tiết theo NV ──────────────────────────────────────────┐   │
│  │ STT │ Họ tên           │ Số sổ BHXH │ Lương đóng│ BHXH NV    │   │
│  │ ────┼──────────────────┼────────────┼───────────┼─────────────  │   │
│  │  1  │ Nguyễn Thị A     │ 0123456789 │ 15,000,000│ 1,200,000  │   │
│  │  2  │ Trần Văn B       │ 0123456790 │ 12,000,000│   960,000  │   │
│  │  ...│                  │            │           │            │   │
│  │  68 │ Lê Thị C         │ 0123456856 │ 20,000,000│ 1,600,000  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ⚠ Cảnh báo: 3 NV thiếu Số sổ BHXH (xem chi tiết)                   │
│                                                                       │
│  [Quay lại]  [Export XML]  [Export XLSX]  [Đánh dấu đã nộp]         │
└─────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Missing Social Insurance Number Modal

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚠ Có 3 nhân viên thiếu Số Sổ BHXH                          [×]   │
├──────────────────────────────────────────────────────────────────┤
│  Các NV sau sẽ bị bỏ qua khi sinh báo cáo (hoặc cần điền trước): │
│                                                                    │
│  • Nguyễn Văn X (E-2026-045) — chưa cấu hình x_social_insurance  │
│  • Trần Thị Y (E-2026-052) — số không hợp lệ (chỉ 8 chữ số)      │
│  • Lê Văn Z (E-2026-068) — bỏ trống                               │
│                                                                    │
│  Bạn muốn:                                                         │
│  [Đóng & Sửa NV thiếu]    [Tiếp tục - bỏ qua các NV này →]       │
└──────────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn | Điều kiện |
|---|---|---|---|
| 1 | Kỳ báo cáo | `wizard.month`, `wizard.year` | Required |
| 2 | Loại báo cáo | `wizard.report_type` | D01-TS / D02-TS |
| 3 | Đơn vị BHXH | `wizard.bhxh_unit_id` | From `hb.bhxh.unit` |
| 4 | Payslips trong kỳ | `hr.payslip` | `state='done'` AND `date_to` trong kỳ |
| 5 | BHXH NV đóng | `hr.payslip.line` | code='BHXH', amount negative |
| 6 | BHXH Công ty đóng | `hr.payslip.line` | code='BHXH_ER' (Employer) |
| 7 | BHYT NV + Cty đóng | tương tự BHXH | code='BHYT', 'BHYT_ER' |
| 8 | BHTN NV + Cty đóng | tương tự | code='BHTN', 'BHTN_ER' |
| 9 | Số sổ BHXH | `hr.employee.x_social_insurance_number` | Required cho mỗi NV |
| 10 | Mã thẻ BHYT | `hr.employee.x_health_insurance_number` | Optional |
| 11 | Insurance Base | `hr.payslip.line.amount` (code='INSURANCE_BASE') | Per payslip |
| 12 | Ngày bắt đầu / kết thúc HĐ | `hr.contract.date_start`, `date_end` | Để xác định tăng/giảm |

### Bảng Output Data

| No | Output | Định dạng | Mục đích |
|---|---|---|---|
| 1 | File XML báo cáo | Schema iBHXH chuẩn | Upload lên cổng iBHXH |
| 2 | File XLSX preview | Tham khảo / lưu trữ | Internal audit |
| 3 | `hb.bhxh.report` record | DB | Lịch sử + Workflow |
| 4 | Chatter log | Text | Audit trail |

### Cấu trúc XML iBHXH (Schema gợi ý)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<HoSo>
  <DonVi>
    <MaDonVi>HG2024-0125</MaDonVi>
    <TenDonVi>Trung tâm Tiếng Trung Học Bá Education</TenDonVi>
    <MaSoThueDV>0123456789</MaSoThueDV>
    <DiaChi>...</DiaChi>
  </DonVi>
  <KyBaoCao>
    <Thang>10</Thang>
    <Nam>2026</Nam>
    <LoaiBaoCao>D02-TS</LoaiBaoCao>
  </KyBaoCao>
  <DanhSachLaoDong>
    <LaoDong>
      <STT>1</STT>
      <HoTen>Nguyễn Thị A</HoTen>
      <SoSoBHXH>0123456789</SoSoBHXH>
      <MaSoThue>8123456789</MaSoThue>
      <CCCD>012345678901</CCCD>
      <NgaySinh>1990-05-15</NgaySinh>
      <GioiTinh>Nu</GioiTinh>
      <LuongDong>15000000</LuongDong>
      <BHXH_NV>1200000</BHXH_NV>
      <BHXH_DV>2625000</BHXH_DV>
      <BHYT_NV>225000</BHYT_NV>
      <BHYT_DV>450000</BHYT_DV>
      <BHTN_NV>150000</BHTN_NV>
      <BHTN_DV>150000</BHTN_DV>
      <TongDong>4800000</TongDong>
    </LaoDong>
    <!-- ... lặp lại cho từng NV ... -->
  </DanhSachLaoDong>
  <TongHop>
    <TongLaoDong>68</TongLaoDong>
    <TongLuongDong>1500000000</TongLuongDong>
    <TongDong>285420000</TongDong>
  </TongHop>
</HoSo>
```

*(Schema chính xác sẽ được lấy từ tài liệu kỹ thuật của Cơ quan BHXH Việt Nam tại thời điểm triển khai — vì BHXH có thể update schema)*

### Pseudo-code

```
FUNCTION generate_bhxh_report(wizard):
    
    # Step 1: Validate kỳ
    payslip_batch = SEARCH hr.payslip.run
        WHERE date_start.month = wizard.month 
          AND date_start.year = wizard.year
    
    IF payslip_batch.state != 'done':
        RAISE ValidationError("Payslip Batch tháng chưa Done")
    
    # Step 2: Load payslips trong kỳ
    payslips = SEARCH hr.payslip
        WHERE payslip_run_id = payslip_batch.id
          AND state = 'done'
    
    # Step 3: Check missing social insurance numbers
    missing = []
    FOR payslip IN payslips:
        emp = payslip.employee
        IF NOT emp.x_social_insurance_number 
            OR NOT REGEX_MATCH(emp.x_social_insurance_number, r'^\d{10}$'):
            missing.append(emp)
    
    IF missing AND NOT wizard.skip_missing:
        RAISE warning, show modal with `missing` list
    
    # Step 4: Build report data
    report_lines = []
    FOR payslip IN payslips:
        IF payslip.employee IN missing:
            CONTINUE
        
        bhxh_nv = ABS(payslip.line('BHXH').amount)
        bhxh_er = payslip.line('BHXH_ER').amount
        bhyt_nv = ABS(payslip.line('BHYT').amount)
        bhyt_er = payslip.line('BHYT_ER').amount
        bhtn_nv = ABS(payslip.line('BHTN').amount)
        bhtn_er = payslip.line('BHTN_ER').amount
        insurance_base = payslip.line('INSURANCE_BASE').amount
        
        report_lines.append({
            'employee': payslip.employee,
            'social_insurance_number': payslip.employee.x_social_insurance_number,
            'salary_base': insurance_base,
            'bhxh_nv': bhxh_nv, 'bhxh_er': bhxh_er,
            'bhyt_nv': bhyt_nv, 'bhyt_er': bhyt_er,
            'bhtn_nv': bhtn_nv, 'bhtn_er': bhtn_er,
            'total': SUM_ALL(...)
        })
    
    # Step 5: Generate file
    IF wizard.output_format == 'xml':
        file_bytes = build_xml_ibhxh_schema(report_lines)
    ELSE:
        file_bytes = build_xlsx_preview(report_lines)
    
    # Step 6: Create attachment + record
    attachment = CREATE ir.attachment(...)
    
    bhxh_report = CREATE hb.bhxh.report
        period = f"{wizard.year}-{wizard.month:02d}"
        report_type = wizard.report_type
        unit_id = wizard.bhxh_unit_id
        line_count = LEN(report_lines)
        total_contribution = SUM(line['total'] FOR line IN report_lines)
        attachment_id = attachment.id
        state = 'draft'
        generated_by = current_user
    
    # Step 7: Log
    bhxh_report.message_post(body = "Đã sinh báo cáo BHXH {period}: {N} NV, tổng {amount}")
    
    RETURN bhxh_report
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.bhxh.unit`** (Configuration - đơn vị BHXH quản lý)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char | Yes | Tên đơn vị BHXH (VD: "BHXH Quận Cầu Giấy") |
| `code` | Char | Yes | Mã đơn vị cấp bởi BHXH |
| `company_bhxh_code` | Char | Yes | Mã đơn vị của công ty tại BHXH (VD: HG2024-0125) |
| `company_id` | Many2one (res.company) | Yes | - |
| `active` | Boolean | No | True |

**2. Model `hb.bhxh.report`** (Lịch sử báo cáo)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char (computed) | Yes | Auto: "BHXH {period}" |
| `period` | Char | Yes | Format YYYY-MM |
| `report_type` | Selection | Yes | D01-TS / D02-TS |
| `bhxh_unit_id` | Many2one (hb.bhxh.unit) | Yes | - |
| `line_count` | Integer | Yes | Số NV trong báo cáo |
| `total_contribution` | Monetary | Yes | Tổng đóng (NV+ĐV) |
| `attachment_id` | Many2one (ir.attachment) | Yes | File XML/XLSX |
| `submission_code` | Char | No | Mã hồ sơ trả về từ iBHXH (Finance nhập sau) |
| `state` | Selection | Yes | draft / generated / submitted / accepted / rejected |
| `submitted_date` | Date | No | Ngày Finance đánh dấu đã nộp |
| `generated_by` | Many2one (res.users) | Yes | - |
| `generated_at` | Datetime | Yes | - |
| `notes` | Text | No | Ghi chú thêm |

**3. Model `hb.bhxh.report.line`** (Dòng chi tiết - lazy load)

| Field | Type | Required |
|---|---|---|
| `report_id` | Many2one (hb.bhxh.report) | Yes |
| `employee_id` | Many2one (hr.employee) | Yes |
| `social_insurance_number` | Char | Yes |
| `salary_base` | Monetary | Yes |
| `bhxh_employee` | Monetary | Yes |
| `bhxh_employer` | Monetary | Yes |
| `bhyt_employee` | Monetary | Yes |
| `bhyt_employer` | Monetary | Yes |
| `bhtn_employee` | Monetary | Yes |
| `bhtn_employer` | Monetary | Yes |
| `total` | Monetary (computed) | Yes |

---

## **VALIDATION RULES**

| No | Rule | Action |
|---|---|---|
| **VR-001** | Payslip Batch của kỳ phải ở state `done` | Block + hiện thông báo |
| **VR-002** | Mọi NV phải có `x_social_insurance_number` hợp lệ (10 digits) | Warning + cho phép skip |
| **VR-003** | Không sinh lại báo cáo nếu đã ở state `submitted` | Block (chỉ cho phép nếu reset về draft với lý do) |
| **VR-004** | `bhxh_unit_id` phải active | Block |
| **VR-005** | `company_bhxh_code` phải có | Block |
| **VR-006** | Mỗi NV phải có ít nhất 1 dòng BHXH/BHYT/BHTN trong payslip | Warning |
| **VR-007** | Mức đóng không vượt trần (PARAM-PR-07/08 × PARAM-PR-09) | Auto-cap (đã handle ở Chapter 5) |
| **VR-008** | Mức đóng không dưới sàn (lương tối thiểu vùng) | Warning |
| **VR-009** | Báo cáo `submitted` không thể xóa | Read-only sau khi submit |
| **VR-010** | Khi đánh dấu submitted, phải nhập `submission_code` từ iBHXH | Required field |

---

## **EXCEPTION FLOW**

### EX-001: NV thiếu Số Sổ BHXH
- Hiển thị modal với danh sách NV thiếu
- Cho phép user chọn: Sửa NV thiếu / Skip & continue
- Nếu skip → log warning vào Chatter

### EX-002: Lỗi schema XML
- Catch exception khi build XML
- Hiển thị "Lỗi sinh XML, vui lòng liên hệ IT"
- Không tạo report record

### EX-003: Sinh lại báo cáo đã submitted
- Block + yêu cầu reset về draft với lý do
- Chỉ HR Manager có quyền reset
- Log audit trail đầy đủ

### EX-004: iBHXH từ chối hồ sơ
- Finance đánh dấu state = `rejected`
- Nhập lý do từ chối
- Cho phép sinh lại báo cáo sau khi sửa

### EX-005: Lương đóng vượt trần
- Đã được handle ở Chapter 5 (auto-cap trong INSURANCE_BASE rule)
- Function này chỉ đọc kết quả đã được cap, không cần xử lý thêm

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-021** | Chỉ tính NV có payslip Done trong kỳ | Không include payslip Draft/Waiting |
| **BR-PR-022** | NV không có Số sổ BHXH bị loại khỏi báo cáo | Phải sửa trước hoặc skip explicit |
| **BR-PR-023** | Salary base lấy từ rule INSURANCE_BASE (đã cap trần) | Theo Chapter 5.4.2 |
| **BR-PR-024** | Tổng đóng = BHXH+BHYT+BHTN (cả NV và ĐV) | Phải khớp với rule tính ở Chapter 5 |
| **BR-PR-025** | Mỗi kỳ chỉ có 1 báo cáo active (draft hoặc submitted) | Không cho sinh 2 báo cáo cùng kỳ |
| **BR-PR-026** | Báo cáo submitted không sửa được | Chỉ HR Manager reset → draft mới sửa |
| **BR-PR-027** | Audit log mọi thao tác | Generate, Reset, Submit, Reject |
| **BR-PR-028** | Schema XML phải tuân thủ iBHXH version hiện tại | Cấu hình schema_version trong `hb.bhxh.unit` |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| File XML | Theo schema iBHXH, sẵn sàng upload lên cổng |
| File XLSX preview | Để Finance review trước khi submit |
| `hb.bhxh.report` record | Lưu trữ vĩnh viễn cho audit |
| Bảng tổng hợp dashboard | Hiển thị BHXH 12 tháng (smart kanban) |
| Chatter log | Audit trail |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-004-01** | Wireframe BHXH List | Danh sách báo cáo theo tháng |
| **UI-PR-004-02** | Wireframe Create Wizard | Wizard tạo báo cáo |
| **UI-PR-004-03** | Wireframe Report Detail | Detail view với danh sách NV |
| **UI-PR-004-04** | Wireframe Missing NV Modal | Modal cảnh báo NV thiếu Số Sổ |
| **UI-PR-004-05** | Wireframe Submission Confirmation | Form xác nhận đã nộp + nhập submission_code |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-004-001** | VN | Payslip Batch tháng {month}/{year} chưa Done. Vui lòng Done payslip trước. | On Validate |
| **MSG-PR-004-002** | VN | Có {N} nhân viên thiếu Số Sổ BHXH. Bạn muốn sửa hay bỏ qua? | On Validate |
| **MSG-PR-004-003** | VN | Báo cáo BHXH tháng {month}/{year} đã được sinh — {N} NV — Tổng đóng {amount} VND | On Generate Success |
| **MSG-PR-004-004** | VN | Đã có báo cáo BHXH {period}. Vui lòng reset báo cáo cũ trước khi sinh mới. | On Duplicate |
| **MSG-PR-004-005** | VN | Báo cáo đã được đánh dấu submitted với mã hồ sơ {code} | On Submit |
| **MSG-PR-004-006** | VN | Chỉ HR Manager mới có quyền reset báo cáo submitted | On Reset (security) |
| **MSG-PR-004-007** | VN | Lỗi sinh XML: {error}. Vui lòng kiểm tra cấu hình schema. | On Generate Error |
| **MSG-PR-004-008** | VN | Số Sổ BHXH "{number}" của NV {name} không đúng định dạng (cần 10 chữ số) | On Validate |
| **MSG-PR-004-009** | VN | NV {name} có lương đóng BH dưới mức tối thiểu vùng. Vui lòng kiểm tra. | On Build Line (warning) |
| **MSG-PR-004-010** | VN | Báo cáo đã được iBHXH từ chối với lý do: {reason} | On Mark Rejected |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Phụ trách |
|---|---|---|
| 1 | Payslip Batch tháng ở state `done` | Module Payroll |
| 2 | Mọi NV có `x_social_insurance_number` (10 digits) | Module Employee (G-07) |
| 3 | `hb.bhxh.unit` đã được tạo ít nhất 1 record | Function này (Configuration) |
| 4 | Salary Rules BHXH/BHYT/BHTN đã được cấu hình | Chapter 5.4.2 |
| 5 | Schema XML iBHXH (version mới nhất) đã được cập nhật | IT team (Implementation) |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | File XML/XLSX được tạo và lưu attachment |
| 2 | `hb.bhxh.report` record state = `generated` |
| 3 | Finance có thể download file để upload lên cổng iBHXH |
| 4 | Sau khi nộp thành công, Finance đánh dấu submitted + nhập mã |
| 5 | Audit log đầy đủ |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Finance vào menu → bấm "Tạo Báo Cáo Tháng" | Finance (`SEC-PR-04`) |
| 2 | Smart button trên Payslip Batch → "Xem Báo Cáo BHXH" | Finance |
| 3 | Automated reminder (CRON) khi qua ngày 10 hàng tháng mà chưa có báo cáo | Hệ thống tự gửi activity |
