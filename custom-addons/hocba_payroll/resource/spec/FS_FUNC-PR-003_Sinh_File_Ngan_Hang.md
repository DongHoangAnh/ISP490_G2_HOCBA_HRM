# **FS — FUNC-PR-003**
# **Sinh File Thanh Toán Ngân Hàng VN (VCB / Techcombank)**

---

## **COVER (Trang bìa)**

| Trường | Giá trị |
|---|---|
| **Project** | Học Bá HRM — Triển khai Odoo 19 |
| **Module** | Payroll |
| **Function ID** | FUNC-PR-003 |
| **Function Name** | Sinh File Thanh Toán Ngân Hàng VN (VCB/TCB) |
| **Custom Module** | `hb_payroll_vn_bank_files` |
| **GAP Reference** | CUS-PR-003 (Chapter 4) |
| **Phase** | Phase 1 — MVP go-live (Bắt buộc) |
| **Độ phức tạp** | Trung bình |
| **Version** | 1.0 |

---

## **HISTORIES**

| No | Version | Description | Modified date | Modified by |
|---|---|---|---|---|
| 1 | 1.0 | Tạo mới — FS cho function sinh file ngân hàng VN | DD/MM/YYYY | [Tên BA] |

---

## **FUNCTION OVERVIEW**

### Mô tả

Chức năng này tự động sinh file thanh toán hàng loạt theo **định dạng riêng của từng ngân hàng Việt Nam** (Vietcombank và Techcombank trong Phase 1, có thể mở rộng sang BIDV, MB, ACB sau). File được tạo trực tiếp từ Payslip Batch sau khi đã được phê duyệt (Done state), giúp Finance không cần re-format dữ liệu trên Excel template thủ công mỗi chu kỳ.

Kiến trúc plugin: mỗi ngân hàng = 1 Python class formatter (`VCBFormatter`, `TCBFormatter`...), có bảng cấu hình per-bank lưu metadata (cột, format, encoding) → dễ thêm ngân hàng mới mà không sửa core logic.

### Business Requirement

Giải quyết các Pain Points sau từ Chapter 2.5.4:

| Pain Point | Cách giải quyết |
|---|---|
| **PP-PR-08** Khai báo & file ngân hàng thủ công | Sinh file 1-click với format chính xác từng ngân hàng |
| **PP-PR-05** Chu kỳ lương dài | Giảm 2h chuẩn bị file ngân hàng/tháng xuống còn < 5 phút |

### Tham chiếu liên module

| Module | Tương tác |
|---|---|
| **Module Employee** | Đọc `bank_account_id` của employee (cộng `x_bank_distribution` nếu Phase 3) |
| **Module Payroll** | Đọc `hr.payslip.run` ở state `done`, đọc `net_amount` của các payslips trong batch |
| **Accounting** | Reconcile với bank statement sau khi nhận file confirm từ ngân hàng |

### Đối tượng sử dụng

| Vai trò | Quyền |
|---|---|
| **Finance (Payroll Accountant)** | Trigger sinh file + download (`SEC-PR-04`) |
| **HR Manager** | Có thể trigger (`SEC-PR-03`) |

---

## **FUNCTION FLOW**

```
┌──────────────────────────────────────────────────────────┐
│  PRE: Payslip Batch ở state 'done' + đã approve         │
└──────────────────────┬───────────────────────────────────┘
                       ▼
       ┌────────────────────────────────────┐
       │ Finance mở Payslip Batch           │
       │ Bấm button "Generate Bank File"    │
       └────────────────┬───────────────────┘
                        ▼
       ┌────────────────────────────────────┐
       │ Wizard hiện lên:                   │
       │ - Chọn ngân hàng (VCB/TCB)         │
       │ - Chọn ngày chi (date_payment)     │
       │ - Chọn tài khoản công ty (from)    │
       └────────────────┬───────────────────┘
                        ▼
            ┌───────────────────────────┐
            │ Validation Gate           │
            │ Mọi payslip có bank account?│
            └────┬──────────────┬────────┘
                 │ No            │ Yes
                 ▼               ▼
       ┌─────────────────┐  ┌────────────────────┐
       │ Block + List NV │  │ Apply Formatter    │
       │ thiếu STK       │  │ (VCBFormatter/...) │
       └─────────────────┘  └────────┬───────────┘
                                     ▼
                       ┌────────────────────────┐
                       │ Generate file XLSX/CSV │
                       │ theo định dạng bank    │
                       └────────┬───────────────┘
                                ▼
                       ┌────────────────────────┐
                       │ Save attachment vào    │
                       │ payslip_batch.bank_file│
                       │ + log Chatter          │
                       └────────┬───────────────┘
                                ▼
                       ┌────────────────────────┐
                       │ Trả file download      │
                       └────────────────────────┘
```

---

## **SCREEN LAYOUT**

### Screen 1: Payslip Batch Form — Button "Generate Bank File"

**Vị trí**: Payroll → Payslip Batches → [Chọn batch state=Done]

```
┌──────────────────────────────────────────────────────────────┐
│  Payslip Batch: BATCH/2026/10/001 — Lương Tháng 10/2026     │
│  State: [Done ✓]                                              │
├──────────────────────────────────────────────────────────────┤
│  [Print Payslips] [Generate Bank File] [Submit BHXH] [...]  │
├──────────────────────────────────────────────────────────────┤
│  ┌─── Bank Files đã sinh ─────────────────────────────────┐  │
│  │  Date          │ Bank   │ File              │ Status   │  │
│  │  ──────────────┼────────┼───────────────────┼────────   │  │
│  │  05/11/2026    │ VCB    │ VCB_T10_2026.xlsx │ ✅ OK    │  │
│  │  05/11/2026    │ TCB    │ TCB_T10_2026.xlsx │ ✅ OK    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Screen 2: Generate Bank File Wizard

```
┌──────────────────────────────────────────────────────────────┐
│  Tạo file thanh toán ngân hàng                         [×]   │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Payslip Batch    : BATCH/2026/10/001 (read-only)            │
│  Số payslip       : 47 (read-only)                            │
│  Tổng số tiền     : 1,250,000,000 VND (read-only)            │
│                                                                │
│  Ngân hàng (*)    : [Vietcombank ▼]                          │
│  TK công ty (*)   : [0123456789 - VCB Hà Nội ▼]              │
│  Ngày chi (*)     : [05/11/2026 📅]                          │
│  Mô tả giao dịch  : [Lương tháng 10/2026          ]          │
│                                                                │
│  ⚠ Lưu ý:                                                     │
│  - File sẽ chỉ chứa các payslips có NV đã có STK             │
│  - Số tiền sẽ làm tròn xuống đơn vị VND                       │
│                                                                │
│  [Hủy]                                    [Tạo file]          │
└──────────────────────────────────────────────────────────────┘
```

### Screen 3: Validation Error Modal (thiếu STK)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ Không thể tạo file                                   [×]   │
├──────────────────────────────────────────────────────────────┤
│  Có 3 nhân viên thiếu thông tin tài khoản ngân hàng:         │
│                                                                │
│  • Nguyễn Văn A (E-2026-001) — chưa có STK                   │
│  • Trần Thị B (E-2026-015) — STK rỗng                         │
│  • Lê Văn C (E-2026-022) — số tài khoản format sai            │
│                                                                │
│  Vui lòng cập nhật thông tin STK trước khi tạo file.         │
│                                                                │
│  [Đóng]              [Mở danh sách nhân viên thiếu STK →]    │
└──────────────────────────────────────────────────────────────┘
```

---

## **PROCESSING DESCRIPTION**

### Bảng Input Data

| No | Trường | Nguồn (Model.Field) | Điều kiện |
|---|---|---|---|
| 1 | Payslip Batch | `hr.payslip.run.id` | `state = 'done'` |
| 2 | Payslips trong batch | `hr.payslip` | `payslip_run_id = batch_id` AND `state = 'done'` |
| 3 | Net Amount mỗi payslip | `hr.payslip.net_amount` (line code='NET') | Required, > 0 |
| 4 | Bank Account NV | `hr.employee.bank_account_id` | Required, format hợp lệ |
| 5 | Ngân hàng được chọn | `hb.bank.format.id` | Từ wizard |
| 6 | TK công ty | `res.partner.bank.id` | Của company, currency=VND |
| 7 | Ngày chi | `wizard.payment_date` | Required, >= today |
| 8 | Mô tả giao dịch | `wizard.description` | Default = "Lương tháng MM/YYYY" |

### Bảng Output Data

| No | Output | Định dạng | Vị trí lưu |
|---|---|---|---|
| 1 | File ngân hàng | XLSX (VCB) hoặc XLSX (TCB) | `ir.attachment` link to `hr.payslip.run` |
| 2 | Log entry | Text | Chatter của Payslip Batch |
| 3 | Bank File Record | `hb.bank.file` (model mới) | DB |

### Định dạng file theo từng ngân hàng

**VCB Format (Vietcombank Bulk Payment):**

| Cột | Tên cột | Kiểu dữ liệu | Bắt buộc | Format |
|---|---|---|---|---|
| A | STT | Number | Yes | 1, 2, 3... |
| B | Số tài khoản người nhận | Text | Yes | 10-14 digits |
| C | Tên người nhận | Text | Yes | UPPERCASE, không dấu |
| D | Số tiền | Number | Yes | Integer VND |
| E | Nội dung | Text | Yes | "Luong T{MM}/{YYYY} - {Employee Code}" |

Encoding: **UTF-8 with BOM**, file extension `.xlsx`.

**TCB Format (Techcombank Bulk Payment):**

| Cột | Tên cột | Kiểu dữ liệu | Bắt buộc | Format |
|---|---|---|---|---|
| A | Account Number | Text | Yes | 14 digits |
| B | Beneficiary Name | Text | Yes | UPPERCASE, có thể có dấu |
| C | Amount | Number | Yes | Decimal (2) |
| D | Currency | Text | Yes | VND (fixed) |
| E | Remark | Text | Yes | Max 100 chars |
| F | Bank Code (nếu khác TCB) | Text | No | (rỗng nếu cùng TCB) |

Encoding: **UTF-8**, file extension `.xlsx`.

### Pseudo-code

```
FUNCTION generate_bank_file(payslip_batch, wizard):
    
    # Step 1: Validate
    payslips_no_bank = SEARCH hr.payslip
        WHERE payslip_run_id = payslip_batch.id
          AND employee.bank_account_id IS NULL
    
    IF payslips_no_bank.count > 0:
        RAISE ValidationError("Có {N} NV thiếu STK: ...")
    
    # Step 2: Load formatter theo bank
    formatter = LOAD_FORMATTER(wizard.bank_format_id.code)
    # Formatter là 1 class Python: VCBFormatter, TCBFormatter...
    
    # Step 3: Lặp qua payslips, build data rows
    rows = []
    stt = 1
    FOR payslip IN payslip_batch.slip_ids:
        IF payslip.net_amount <= 0:
            CONTINUE  # skip 0 hoặc âm
        
        row = formatter.build_row(
            stt = stt,
            account = payslip.employee.bank_account_id.acc_number,
            name = payslip.employee.name,
            amount = INT(payslip.net_amount),  # round down
            description = wizard.description.format(
                month = payslip.date_to.strftime('%m'),
                year = payslip.date_to.strftime('%Y'),
                employee_code = payslip.employee.employee_code
            )
        )
        rows.append(row)
        stt += 1
    
    # Step 4: Generate XLSX
    file_bytes = formatter.export_xlsx(rows, header=True)
    
    # Step 5: Save as attachment
    attachment = CREATE ir.attachment
        name = f"{formatter.code}_{period}.xlsx"
        res_model = 'hr.payslip.run'
        res_id = payslip_batch.id
        datas = file_bytes
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Step 6: Create bank_file record
    CREATE hb.bank.file
        batch_id = payslip_batch.id
        bank_format_id = wizard.bank_format_id
        attachment_id = attachment.id
        payment_date = wizard.payment_date
        total_amount = SUM(row.amount FOR row IN rows)
        record_count = LEN(rows)
        generated_by = current_user
    
    # Step 7: Log to Chatter
    payslip_batch.message_post(
        body = f"Đã sinh file {formatter.name}: {LEN(rows)} dòng, "
               f"tổng {format_money(total_amount)} VND"
    )
    
    RETURN attachment
```

---

## **SCREEN DEFINITION**

### Custom Models mới

**1. Model `hb.bank.format`** (Configuration - định nghĩa format từng bank)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | Char | Yes | - | Tên ngân hàng (VD: "Vietcombank") |
| `code` | Char | Yes | - | Mã ngắn (VD: "VCB", "TCB") |
| `formatter_class` | Char | Yes | - | Tên Python class (VD: "VCBFormatter") |
| `encoding` | Selection | Yes | utf-8 | utf-8 / utf-8-bom / ansi |
| `file_extension` | Selection | Yes | xlsx | xlsx / csv / txt |
| `account_format_regex` | Char | No | - | Regex validate STK (VD: `^\d{10,14}$`) |
| `max_records_per_file` | Integer | No | 0 | 0 = không giới hạn |
| `description_template` | Char | No | "Luong T{month}/{year}" | Template mô tả giao dịch |
| `active` | Boolean | No | True | - |

**2. Model `hb.bank.file`** (History - log mỗi lần sinh file)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | Char | Yes | Auto: `{bank_code}_{period}` |
| `batch_id` | Many2one (hr.payslip.run) | Yes | Batch nguồn |
| `bank_format_id` | Many2one (hb.bank.format) | Yes | Ngân hàng |
| `attachment_id` | Many2one (ir.attachment) | Yes | File đã sinh |
| `payment_date` | Date | Yes | Ngày dự kiến chi |
| `total_amount` | Monetary | Yes | Tổng số tiền |
| `record_count` | Integer | Yes | Số dòng trong file |
| `generated_by` | Many2one (res.users) | Yes | Người sinh file |
| `generated_at` | Datetime | Yes | Timestamp |
| `state` | Selection | Yes | draft / generated / uploaded / confirmed |

**3. Wizard `hb.bank.file.wizard`**

| Field | Type | Required | Description |
|---|---|---|---|
| `payslip_batch_id` | Many2one | Yes | Auto fill từ context |
| `bank_format_id` | Many2one (hb.bank.format) | Yes | NH được chọn |
| `company_bank_id` | Many2one (res.partner.bank) | Yes | TK công ty |
| `payment_date` | Date | Yes | Default = today + 1 |
| `description` | Char | Yes | Default theo template |

---

## **VALIDATION RULES**

| No | Rule | Trigger | Action |
|---|---|---|---|
| **VR-001** | Payslip Batch phải ở state `done` | On Click "Generate Bank File" | Hide button nếu state != done |
| **VR-002** | Mọi NV trong batch phải có `bank_account_id` | On Wizard Submit | Block + list NV thiếu |
| **VR-003** | STK phải match `bank_format.account_format_regex` | On Wizard Submit | Block + list STK invalid |
| **VR-004** | `net_amount` > 0 | On Build Row | Skip row, log warning |
| **VR-005** | `payment_date` >= today | On Wizard Save | Block save |
| **VR-006** | TK công ty phải cùng currency VND | On Wizard Submit | Block |
| **VR-007** | `bank_format.formatter_class` phải import được | On Generate | Raise error nếu class không tồn tại |
| **VR-008** | Tên NV viết hoa, không dấu cho VCB | On VCB Build Row | Auto-transform |
| **VR-009** | Nội dung giao dịch <= 100 chars | On TCB Build Row | Truncate + log warning |
| **VR-010** | Không sinh file 2 lần cho cùng (batch, bank) | On Generate | Show confirm dialog "File đã tồn tại, ghi đè?" |

---

## **EXCEPTION FLOW**

### EX-001: NV thiếu STK
- Block sinh file
- Modal hiển thị danh sách NV thiếu
- Cung cấp link "Mở danh sách" → list view employees filter

### EX-002: STK sai định dạng
- Block sinh file
- Modal hiển thị NV nào + STK nào không match regex
- Đề xuất sửa trực tiếp (link đến employee form)

### EX-003: Lỗi khi sinh XLSX (memory/disk)
- Catch exception, log đầy đủ traceback
- Hiển thị "Lỗi sinh file. Liên hệ IT." kèm error code
- Không tạo `hb.bank.file` record

### EX-004: Người dùng cancel giữa chừng
- Rollback transaction
- Không tạo attachment, không log

### EX-005: Ghi đè file đã có
- Confirm dialog: "File {bank}_{period} đã tồn tại. Bạn có muốn ghi đè?"
- Nếu Yes: archive file cũ + tạo file mới
- Nếu No: hủy thao tác

---

## **BUSINESS RULES**

| Mã | Rule | Mô tả |
|---|---|---|
| **BR-PR-013** | Mỗi (batch, ngân hàng) có thể tạo nhiều file, file mới ghi đè file cũ | File cũ được archive, không xóa hoàn toàn |
| **BR-PR-014** | Số tiền làm tròn xuống đơn vị VND | Không có decimal trong file ngân hàng |
| **BR-PR-015** | Tên NV trong VCB phải viết hoa không dấu | Đảm bảo tương thích hệ thống VCB |
| **BR-PR-016** | Tên NV trong TCB giữ nguyên dấu tiếng Việt | TCB hỗ trợ Unicode |
| **BR-PR-017** | NV có nhiều STK (Phase 3) → sinh nhiều dòng | 1 NV có thể xuất hiện 2-3 lần trong file |
| **BR-PR-018** | Mô tả giao dịch chuẩn hóa | `Luong T{MM}/{YYYY} - {employee_code}` (max 100 chars) |
| **BR-PR-019** | File được lưu vào DB, không xóa | Phục vụ audit + tra cứu lịch sử |
| **BR-PR-020** | Audit log đầy đủ | Mọi lần sinh file + ai sinh + thời gian |

---

## **OUTPUT**

| Output | Mô tả |
|---|---|
| File XLSX | Tải về máy Finance để upload lên VCB Internet Banking / TCB Business Banking |
| `hb.bank.file` record | Log lịch sử trên Odoo, drill-down xem được payslips trong file |
| Chatter log | Audit trail trên Payslip Batch |
| Smart button "Bank Files" | Trên Payslip Batch form, hiển thị các file đã sinh cho batch này |

---

## **UI REFERENCE**

| ID | Reference | Mô tả |
|---|---|---|
| **UI-PR-003-01** | Wireframe Bank File Button | Button trên Payslip Batch |
| **UI-PR-003-02** | Wireframe Generate Wizard | Wizard chọn bank + date |
| **UI-PR-003-03** | Wireframe Validation Modal | Modal khi thiếu STK |
| **UI-PR-003-04** | Wireframe Bank File List | List các file đã sinh |
| **UI-PR-003-05** | Wireframe Bank Format Config | Configuration screen cho `hb.bank.format` |

---

## **MESSAGE DEFINITION**

| Message ID | Lang | Message | Output Timing |
|---|---|---|---|
| **MSG-PR-003-001** | VN | Có {N} nhân viên thiếu tài khoản ngân hàng. Vui lòng cập nhật trước khi tạo file. | On Validate |
| MSG-PR-003-001 | EN | {N} employees missing bank account. Please update before generating file. | On Validate |
| **MSG-PR-003-002** | VN | Số tài khoản "{acc}" không đúng định dạng yêu cầu của {bank} | On Validate |
| **MSG-PR-003-003** | VN | File {filename} đã tồn tại. Bạn có muốn ghi đè? | On Generate (confirm) |
| **MSG-PR-003-004** | VN | Đã sinh thành công file {filename}: {N} dòng, tổng {amount} VND | On Generate (success) |
| **MSG-PR-003-005** | VN | Payslip {ref} có Net = 0 hoặc âm — đã bỏ qua | On Build Row (warning) |
| **MSG-PR-003-006** | VN | Lỗi sinh file: {error_msg}. Vui lòng liên hệ IT. | On Generate (error) |
| **MSG-PR-003-007** | VN | Ngày chi phải lớn hơn hoặc bằng hôm nay | On Wizard Save |
| **MSG-PR-003-008** | VN | Tài khoản công ty phải có loại tiền VND | On Wizard Submit |

---

## **PRECONDITIONS**

| No | Tiền điều kiện | Module phụ trách |
|---|---|---|
| 1 | Payslip Batch ở state `done` | Module Payroll (core) |
| 2 | Mọi NV có `bank_account_id` hợp lệ | Module Employee |
| 3 | `hb.bank.format` đã có ít nhất 1 bản ghi cho VCB & TCB | Function này (Configuration) |
| 4 | Company có ít nhất 1 `res.partner.bank` VND | Accounting setup |
| 5 | Python classes `VCBFormatter`, `TCBFormatter` đã được code | Function này |

---

## **POSTCONDITIONS**

| No | Kết quả |
|---|---|
| 1 | File XLSX được tạo và sẵn sàng download |
| 2 | `hb.bank.file` record được tạo với state = `generated` |
| 3 | Attachment được link với Payslip Batch |
| 4 | Chatter log đầy đủ |
| 5 | Finance có thể upload file lên ngân hàng |

---

## **TRIGGER**

| No | Trigger | Người thực hiện |
|---|---|---|
| 1 | Bấm button "Generate Bank File" trên Payslip Batch | Finance (`SEC-PR-04`) |
| 2 | Bấm "Regenerate" trên `hb.bank.file` record cũ | Finance hoặc HR Manager |
