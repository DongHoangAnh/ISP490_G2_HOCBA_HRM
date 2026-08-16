
## Change History (v1.1 Update)
- **Version 1.1 (2026-08-13)**:
  - Added MB Bank Formatter (`MBBankFormatter`) supporting MB Bank XLSX payment export specifications.
  - Formalized `BankFormatterRegistry` strategy pattern for dynamic bank format resolution (`VCBFormatter`, `TCBFormatter`, `MBBankFormatter`).
  - Documented transient wizard `hb.bank.file.wizard` for backend file generation.
  - Added REST APIs for `/hocba/payroll/api/bank-files/<id>/mark-uploaded` and `/hocba/payroll/api/bank-files/<id>/mark-confirmed`.

# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-004 |
| **Function Name** | Bank Payment File Generation |
| **Created Date** | 21/06/2026 |
| **Last Update Date** | 21/06/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP (Community / Enterprise) |
| **Reference** | `hb.bank.format`, `hb.bank.file`, `hb.bank.file.wizard`, `bank_formatter.py`, `bank_format_views.xml`, `bank_file_views.xml`, `BankFile.jsx`, `BankFileForm.jsx` -- module `hocba_payroll` |

| **Approver** | **Reviewer** | **Creator** |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

---

## CHANGE HISTORY

| No | Version | Change Description | Affected Sections | Date | Author |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial creation from bank payment BE/FE implementation | All | 21/06/2026 | Group G2 |
| 2 | 1.1 | Full rewrite with correct Function ID (FS-PAY-004), FS-PAY-001 format, detailed field specs, strategy pattern documentation, validation rules, and SPA component details derived from actual source code | All | 21/06/2026 | Group G2 |
| 3 | 1.2 | Fixed bank resolution fallback matching logic in `_resolve_bank_name()` and updated SPA `BankFile.jsx` modal to send `bank_codes: []` (ALL) when selecting all banks so employees are not filtered out when exporting. | Section 2, Section 4 | 08/08/2026 | Antigravity AI |
| 4 | 1.3 | Synchronized complete strategy pattern registry (`BankFormatterRegistry`): 7 registered bank formatters (`VCBFormatter`, `TCBFormatter`, `MBFormatter`, `BIDVFormatter`, `ACBFormatter`, `VietinBankFormatter`, `VPBankFormatter`) with custom XLSX column schemas. | 1, 2, 4 | 09/08/2026 | Antigravity AI |

---

## 1. FUNCTION OVERVIEW

| Item | Detail |
| --- | --- |
| **Function ID** | FS-PAY-004 |
| **Function Name** | Bank Payment File Generation |
| **Created Date** | 21/06/2026 |
| **Last Modified Date** | 09/08/2026 |

| Attribute | Value |
| --- | --- |
| **Processing Time** | On-demand |
| **Processing Type** | Interactive (Wizard) + REST API |
| **Function Type** | Transaction / Export |
| **Multilingual** | No |

### Business Requirement & Function Overview

**Overview:**
This function enables HR/Payroll operators to generate bank-specific XLSX payment files from confirmed payslip batches, track file lifecycle states, and manage bank format configurations. The architecture follows a Strategy pattern: each bank has a dedicated formatter class that produces the correct column layout, name transformations, and data formatting.

**Business Context:**
Hoc Ba Education pays employees through multiple banks (Vietcombank, Techcombank, etc.). Each bank requires a different Excel file format for bulk salary transfers. The system generates these files from finalized payslip data, validates employee bank account information, and tracks the file through its lifecycle (generated -> uploaded to bank portal -> confirmed by bank).

**Functional Scope:**
- CRUD operations on bank format configurations (`hb.bank.format`) with formatter class, encoding, file extension, and account validation regex.
- Bank payment file generation via wizard (`hb.bank.file.wizard`) with multi-step validation.
- XLSX file export using openpyxl with bank-specific column layouts and transformations.
- File lifecycle tracking (`hb.bank.file`) with state machine: `generated -> uploaded -> confirmed`.
- Strategy pattern: `BankFormatterRegistry` resolves concrete formatter classes (`VCBFormatter`, `TCBFormatter`) by bank code.
- Employee bank account resolution with fallback chain.
- Payroll Excel export (full summary with company header and signature blocks) via SPA.
- REST API endpoints for both bank format configuration and file generation/lifecycle.
- React SPA screens: `BankFile.jsx` (file list/management), `BankFileForm.jsx` (file creation form).

**Users:**
- **HR Manager** (`hr.group_hr_manager`): Full CRUD on bank format and bank file models. Can generate files, mark uploaded, confirm. Access to configuration menu.
- **HR User** (`hr.group_hr_user`): Read-only access on bank format and bank file models.

---

## 2. FUNCTION FLOW

### Main Flow 1 -- File Generation via Wizard (Odoo Backend)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Opens a closed batch (`hb.payslip.run` with `state='close'`) and clicks "Tao file Ngan hang" | System opens the `hb.bank.file.wizard` dialog. `payslip_batch_id` is pre-filled from context. Computed fields `payslip_count` and `total_net` show summary of done payslips. |
| 2 | HR Manager | Selects `bank_format_id`, `company_bank_id`, `payment_date`, and optionally edits `description` | `bank_format_id` domain filters to active formats only. `payment_date` defaults to tomorrow. `description` defaults to `Luong T{month}/{year}`. |
| 3 | HR Manager | Clicks "Tao file" | Wizard calls `action_generate()`. |
| 4 | System | Runs validation (`_validate()`) | VR-001: Batch must be in `close` state. VR-005: `payment_date >= today`. VR-002: All done employees must have bank account. VR-003: Account numbers must match format regex (if set). |
| 5 | System | Loads formatter via `BankFormatterRegistry.get(bank_format.code)` | Resolves concrete class (e.g., `VCBFormatter`). Raises `ValidationError` if code not registered. |
| 6 | System | Calls `formatter.build_rows(done_slips, description, account_regex)` | Iterates done payslips. For each: reads net amount (line code `thuc_lanh`), resolves employee bank account, builds row dict via `build_row()`. Skips payslips with net <= 0 (with warning). |
| 7 | System | Validates rows result | VR-006: If rows list is empty (all net=0), raises `UserError`. |
| 8 | System | Calls `formatter.export_xlsx(rows)` | Generates XLSX binary using openpyxl: bold headers, `#,##0` number format, right-aligned numerics, auto-width columns (max 40). |
| 9 | System | Creates `ir.attachment` and `hb.bank.file` record | Attachment linked to batch (`res_model='hb.payslip.run'`). Bank file stores metadata: total_amount, record_count, generated_by, generated_at. State defaults to `generated`. |
| 10 | System | Posts chatter message on batch | Message: "Da sinh file {filename}: {count} dong, tong {amount} VND". |
| 11 | System | Returns download action | `ir.actions.act_url` pointing to `/web/content/{attachment_id}?download=true`. Browser downloads the XLSX file. |

### Main Flow 2 -- File Generation via REST API (SPA)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In SPA `BankFile.jsx`, clicks "Tao file" | Opens `BankFileForm.jsx` modal with batch and format dropdowns. |
| 2 | HR Manager | Selects batch and bank format, clicks "Tao file" | FE calls `POST /bank-file/generate` with `{ batch_id, bank_format_id }`. |
| 3 | Backend | Creates wizard and calls `action_generate()` | Same validation and generation flow as Main Flow 1. |
| 4 | Backend | Returns bank file API dict | Includes `download_url` built from `attachment_id`. |

### Main Flow 3 -- File Lifecycle (Upload -> Confirm)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | After uploading XLSX to bank portal, clicks "Danh dau Uploaded" on bank file form | `action_mark_uploaded()` transitions state from `generated` to `uploaded`. Raises `UserError` if not in `generated` state. |
| 2 | HR Manager | After bank confirms payment, clicks "Xac nhan NH" | `action_mark_confirmed()` transitions state from `uploaded` to `confirmed`. Raises `UserError` if not in `uploaded` state. |

**REST API (File Lifecycle):**
- `POST /hocba-hrm/api/payroll/bank-file/<id>/upload` -- Mark as uploaded.
- `POST /hocba-hrm/api/payroll/bank-file/<id>/confirm` -- Mark as confirmed.

### Main Flow 4 -- Payroll Excel Export (SPA)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In `BankFile.jsx`, clicks "Xuat Excel" for a bank file | FE fetches employee payroll data for the batch's month/year via `fetchEmployeePayroll({month, year})`. |
| 2 | FE | Builds formatted Excel | Company header (name, address, MST), title "BANG LUONG THANG MM/YYYY", employee rows with all salary rule columns, total row with sums, and 3 signature blocks (Nguoi lap bieu, Ke toan truong, Giam doc). |
| 3 | FE | Downloads generated file | Uses `xlsx` library client-side. Bold Times New Roman 10pt, blue headers, `#,##0` number format, adaptive column widths. |

### Error/Exception Flow

| Error Scenario | System Behavior |
| --- | --- |
| Batch not in `close` state | `UserError` raised by VR-001 |
| Payment date in the past | `ValidationError` raised by VR-005 |
| Employee missing bank account | `ValidationError` listing employees by name and code (VR-002) |
| Account number fails regex | `ValidationError` listing invalid accounts (VR-003) |
| All payslips have net = 0 | `UserError` raised by VR-006 |
| Formatter class not registered | `ValidationError` from `BankFormatterRegistry.get()` |
| Mark uploaded from wrong state | `UserError`: must be in `generated` state |
| Mark confirmed from wrong state | `UserError`: must be in `uploaded` state |
| Missing required API fields | 400 error: "Missing required field: {field}" |

---

## 3. SCREEN LAYOUT

### Screen 1: Bank Format List (`hb_bank_format_tree`)

**View type:** List
**XML ID:** `hocba_payroll.hb_bank_format_tree`
**Model:** `hb.bank.format`

| Column | Field | Widget | Notes |
| --- | --- | --- | --- |
| (drag handle) | `sequence` | `handle` | Allows drag-reorder |
| Ten | `name` | (default Char) | Bank display name |
| Ma | `code` | (default Char) | Bank code |
| Formatter | `formatter_class` | (default Char) | Python class name |
| Encoding | `encoding` | (default Selection) | File encoding |
| Dinh dang | `file_extension` | (default Selection) | Output format |
| Active | `active` | (default Boolean) | Archive toggle |

**Action:** `action_hb_bank_format`
- Menu path: Payroll > Cau hinh > Cau hinh Ngan hang
- Access group: `hr.group_hr_manager`

### Screen 2: Bank Format Form (`hb_bank_format_form`)

**View type:** Form
**XML ID:** `hocba_payroll.hb_bank_format_form`
**Model:** `hb.bank.format`

**Layout:**

```
<sheet>
  <group>
    <group>
      name, code, sequence, active
    </group>
    <group>
      formatter_class, encoding, file_extension
    </group>
  </group>
  <group>
    account_format_regex, max_records_per_file, description_template
  </group>
</sheet>
```

### Screen 3: Bank File List (`hb_bank_file_tree`)

**View type:** List
**XML ID:** `hocba_payroll.hb_bank_file_tree`
**Model:** `hb.bank.file`

| Column | Field | Widget | Decoration | Notes |
| --- | --- | --- | --- | --- |
| Ten file | `name` | (default Char) | -- | Generated filename |
| Ky luong | `batch_id` | (default Many2one) | -- | Parent batch |
| Ngan hang | `bank_format_id` | (default Many2one) | -- | Bank format |
| Ngay thanh toan | `payment_date` | (default Date) | -- | Payment execution date |
| Tong tien | `total_amount` | monetary | -- | Sum of net amounts |
| So dong | `record_count` | (default Integer) | -- | Data row count |
| Trang thai | `state` | badge | `decoration-info`=generated, `decoration-warning`=uploaded, `decoration-success`=confirmed | Lifecycle state |
| Ngay tao | `generated_at` | (default Datetime) | -- | File creation timestamp |

**Action:** `action_hb_bank_file`
- Menu path: Payroll > File Ngan hang

### Screen 4: Bank File Form (`hb_bank_file_form`)

**View type:** Form
**XML ID:** `hocba_payroll.hb_bank_file_form`
**Model:** `hb.bank.file`

**Layout:**

```
<header>
  <button name="action_mark_uploaded" string="Danh dau Uploaded"
          invisible="state != 'generated'" class="btn-primary"/>
  <button name="action_mark_confirmed" string="Xac nhan NH"
          invisible="state != 'uploaded'" class="btn-success"/>
  <field name="state" widget="statusbar"
         statusbar_visible="generated,uploaded,confirmed"/>
</header>
<sheet>
  <group>
    <group>
      name, batch_id, bank_format_id, payment_date
    </group>
    <group>
      total_amount (monetary), record_count,
      generated_by, generated_at
    </group>
  </group>
  attachment_id
</sheet>
<chatter/>
```

**Header Buttons:**

| Button Label | Type | Method | Visibility | Class |
| --- | --- | --- | --- | --- |
| Danh dau Uploaded | `object` | `action_mark_uploaded` | `state == 'generated'` | `btn-primary` |
| Xac nhan NH | `object` | `action_mark_confirmed` | `state == 'uploaded'` | `btn-success` |

### Screen 5: Bank File Wizard (`hb_bank_file_wizard_form`)

**View type:** Form (dialog, `target='new'`)
**XML ID:** `hocba_payroll.hb_bank_file_wizard_form`
**Model:** `hb.bank.file.wizard` (TransientModel)
**Title:** "Tao file thanh toan ngan hang"

**Layout:**

```
<group>
  <group>
    payslip_batch_id (readonly)
    payslip_count (readonly)
    total_net (monetary, readonly)
  </group>
  <group>
    bank_format_id
    company_bank_id
    payment_date
    description
  </group>
</group>
<footer>
  <button name="action_generate" string="Tao file"
          type="object" class="btn-primary"/>
  <button string="Huy" special="cancel"/>
</footer>
```

### Screen 6: REST API Endpoints

**Base path:** `/hocba-hrm/api/payroll/`

All endpoints use `type='http'`, `auth='user'`, `csrf=False`.

**Bank Format (Configuration):**

| Method | Endpoint | Description | Request Body | Response (`data`) |
| --- | --- | --- | --- | --- |
| GET | `/bank-format` | List active formats | -- | Array: `{ id, name, code, sequence, formatter_class, encoding, file_extension, account_format_regex, max_records_per_file, description_template }` |
| POST | `/bank-format` | Create format | `{ name*, code*, formatter_class*, sequence?, encoding?, file_extension?, account_format_regex?, max_records_per_file?, description_template? }` | `{ id, name, code }` |
| POST | `/bank-format/<id>` | Update format | Partial object | `{ id, name, code }` |
| POST | `/bank-format/<id>/delete` | Archive format | -- | `{ message }` |

**Bank File (Generation & Lifecycle):**

| Method | Endpoint | Description | Request Body | Response (`data`) |
| --- | --- | --- | --- | --- |
| POST | `/bank-file/generate` | Generate file | `{ batch_id*, bank_format_id*, company_bank_id?, payment_date?, description? }` | `hb.bank.file._to_api_dict()` |
| GET | `/bank-file` | List files | Query: `batch_id?`, `limit?` (default 50) | Array of `_to_api_dict()` |
| POST | `/bank-file/<id>/upload` | Mark uploaded | -- | `{ state: 'uploaded' }` |
| POST | `/bank-file/<id>/confirm` | Mark confirmed | -- | `{ state: 'confirmed' }` |

**Bank File API Serialization (`_to_api_dict()`):**

```json
{
  "id": 1,
  "name": "VCB_T06_2026.xlsx",
  "batch_id": 5,
  "batch_name": "Luong T06/2026",
  "batch_month": "06",
  "batch_year": "2026",
  "bank_code": "VCB",
  "bank_name": "Vietcombank",
  "format_name": "Vietcombank",
  "payment_date": "2026-06-22",
  "total_amount": 125000000,
  "record_count": 10,
  "state": "generated",
  "generated_by": "Admin",
  "generated_at": "2026-06-21T10:30:00",
  "download_url": "/web/content/42"
}
```

### Screen 7: React SPA -- BankFile.jsx

**File:** `frontend/src/features/payroll/BankFile.jsx`
**Component:** `BankFile` (default export)
**Used by:** Payroll module as a sub-tab.

**Features:**
- Lists generated bank files with state badges (gray=generated, blue=uploaded, green=confirmed).
- Filter by batch via dropdown.
- Per-file action buttons: "Tai len" (upload state transition), "Xac nhan" (confirm transition), "Xuat Excel" (download).
- "Tao file" button opens `BankFileForm` modal.
- Excel export: builds full payroll summary with company header, salary columns, totals, and signature blocks.

### Screen 8: React SPA -- BankFileForm.jsx

**File:** `frontend/src/features/payroll/BankFileForm.jsx`
**Component:** `BankFileForm` (default export)

**Form Fields:**
- "Dot luong" (required, select dropdown from batches).
- "Dinh dang ngan hang" (required, select dropdown from active bank formats).

**Submit:** Calls `generateBankFile({ batch_id, bank_format_id })`. Shows error text on failure, closes modal on success.

---

## 4. FIELD SPECIFICATION

### 4.1 Model: `hb.bank.format`

**Python class:** `HbBankFormat`
**`_name`:** `hb.bank.format`
**`_description`:** `Bank Format Configuration`
**`_order`:** `sequence, name`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | -- | Ten ngan hang | Bank display name (e.g., "Vietcombank"). |
| 2 | `code` | `Char` | Yes | No | -- | SQL UNIQUE (`_code_unique`: `UNIQUE(code)`, message: "Ma ngan hang phai la duy nhat!") | Ma | Short bank code (e.g., "VCB"). |
| 3 | `sequence` | `Integer` | No | No | `10` | -- | Thu tu | Ordering in list views. |
| 4 | `formatter_class` | `Char` | Yes | No | -- | -- | Formatter class | Python class name (e.g., "VCBFormatter"). Must be registered in `BankFormatterRegistry`. |
| 5 | `encoding` | `Selection` | Yes | No | `'utf-8'` | Options: `('utf-8','UTF-8')`, `('utf-8-sig','UTF-8 BOM')`, `('cp1252','Windows-1252')` | Encoding | File encoding for export. |
| 6 | `file_extension` | `Selection` | Yes | No | `'xlsx'` | Options: `('xlsx','XLSX')`, `('csv','CSV')`, `('txt','TXT')` | Dinh dang file | Output file format. |
| 7 | `account_format_regex` | `Char` | No | No | -- | -- | Regex tai khoan | Regex to validate employee bank account numbers (e.g., `^\d{10,14}$`). |
| 8 | `max_records_per_file` | `Integer` | No | No | `0` | -- | So dong toi da | Maximum rows per file. 0 = unlimited. |
| 9 | `description_template` | `Char` | No | No | `'Luong T{month}/{year}'` | -- | Mau mo ta | Transaction description template with `{month}`, `{year}`, `{employee_code}` placeholders. |
| 10 | `active` | `Boolean` | No | No | `True` | -- | (default) | Soft-delete / archive flag. |

### 4.2 Model: `hb.bank.file`

**Python class:** `HbBankFile`
**`_name`:** `hb.bank.file`
**`_description`:** `Bank Payment File`
**`_order`:** `generated_at desc`
**`_inherit`:** `['mail.thread']`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | `readonly=True` | Ten file | Generated filename (e.g., "VCB_T06_2026.xlsx"). |
| 2 | `batch_id` | `Many2one` | Yes | No | -- | Comodel: `hb.payslip.run`, `ondelete='restrict'`, `readonly=True` | Ky luong | Parent batch. Cannot delete batch while files exist. |
| 3 | `bank_format_id` | `Many2one` | Yes | No | -- | Comodel: `hb.bank.format`, `ondelete='restrict'`, `readonly=True` | Ngan hang | Bank format used. |
| 4 | `attachment_id` | `Many2one` | No | No | -- | Comodel: `ir.attachment`, `ondelete='set null'`, `readonly=True` | File dinh kem | Attached XLSX file. |
| 5 | `payment_date` | `Date` | Yes | No | -- | `readonly=True` | Ngay thanh toan | Payment execution date. |
| 6 | `total_amount` | `Float` | No | No | -- | `digits=(16,0)`, `readonly=True` | Tong tien | Sum of net amounts in file. |
| 7 | `record_count` | `Integer` | No | No | -- | `readonly=True` | So dong | Number of data rows generated. |
| 8 | `generated_by` | `Many2one` | Yes | No | current user | Comodel: `res.users`, `readonly=True` | Nguoi tao | User who generated the file. |
| 9 | `generated_at` | `Datetime` | Yes | No | `fields.Datetime.now` | `readonly=True` | Ngay tao | File creation timestamp. |
| 10 | `state` | `Selection` | No | No | `'generated'` | Options: `('generated','Da tao')`, `('uploaded','Da tai len')`, `('confirmed','Da xac nhan')`. `tracking=True` | Trang thai | File lifecycle state. |

**Key Methods:**

| Method | Description |
| --- | --- |
| `action_mark_uploaded` | Validates `state == 'generated'`, transitions to `uploaded`. Raises `UserError` on invalid state. |
| `action_mark_confirmed` | Validates `state == 'uploaded'`, transitions to `confirmed`. Raises `UserError` on invalid state. |
| `_to_api_dict` | Returns dict for API response including `download_url` from `attachment_id` (`/web/content/{id}`). |

### 4.3 Model: `hb.bank.file.wizard` (TransientModel)

**Python class:** `HbBankFileWizard`
**`_name`:** `hb.bank.file.wizard`
**`_description`:** `Bank File Generation Wizard`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `payslip_batch_id` | `Many2one` | Yes | No | -- | Comodel: `hb.payslip.run`, `readonly=True` | Ky luong | Set from caller context. |
| 2 | `bank_format_id` | `Many2one` | Yes | No | -- | Comodel: `hb.bank.format`, domain: `[('active','=',True)]` | Ngan hang | Selected bank format. |
| 3 | `company_bank_id` | `Many2one` | Yes | No | -- | Comodel: `res.partner.bank` | TK cong ty | Company bank account for transfer. |
| 4 | `payment_date` | `Date` | Yes | No | `fields.Date.today() + 1` | -- | Ngay thanh toan | Must be >= today (validated). |
| 5 | `description` | `Char` | Yes | No | `'Luong T{month}/{year}'` | -- | Noi dung | Transaction description template. |
| 6 | `payslip_count` | `Integer` | No | No | -- | Computed: `_compute_summary`, depends on `payslip_batch_id` | So phieu | Count of done payslips in batch. Read-only. |
| 7 | `total_net` | `Float` | No | No | -- | `digits=(16,0)`, computed: `_compute_summary` | Tong thuc linh | Sum of net amounts (line code `thuc_lanh`). Read-only. |

**Key Methods:**

| Method | Description |
| --- | --- |
| `_compute_summary` | `@api.depends('payslip_batch_id')`. Counts done payslips and sums their net amounts. |
| `_validate` | Runs VR-001 through VR-006 validation rules. |
| `action_generate` | Validates, loads formatter, builds rows, exports XLSX, creates attachment + bank file, posts chatter, returns download URL action. |

---

## 5. BUSINESS RULES

### BR-PAY-050: Unique Code Constraint on Bank Format

**Rule:** The `code` field on `hb.bank.format` has a SQL UNIQUE constraint.
**Implementation:** `_code_unique = models.Constraint('unique (code)', 'Ma ngan hang phai la duy nhat!')`
**Behavior:** Duplicate codes raise database integrity error.

### BR-PAY-051: Strategy Pattern for File Generation

**Rule:** Each `hb.bank.format.formatter_class` maps to a concrete Python class that extends `BaseBankFormatter`. The `BankFormatterRegistry` resolves the class by code.
**Implementation:**
```
BaseBankFormatter (abstract)
  +-- VCBFormatter (code='VCB')
  +-- TCBFormatter (code='TCB')

BankFormatterRegistry
  .get(code) -> BaseBankFormatter instance
  .register(code, cls) -> void
  .available_codes() -> list[str]
```
**Extensibility:** New banks are added by creating a new formatter class extending `BaseBankFormatter` and registering it in `BankFormatterRegistry._formatters`.

### BR-PAY-052: VCB Formatter Output

**Rule:** `VCBFormatter` converts employee name to uppercase without diacritics (Unicode NFKD normalization via `_to_uppercase_no_diacritics()`).
**Output columns:**

| # | Header | Key | Transformation |
| --- | --- | --- | --- |
| 1 | STT | `stt` | Sequential row number (1-indexed) |
| 2 | So tai khoan | `acc_number` | Stripped bank account number |
| 3 | Ten nguoi nhan | `emp_name` | Uppercase, no diacritics |
| 4 | So tien | `amount` | Integer net amount |
| 5 | Noi dung | `description` | Formatted from template |

### BR-PAY-053: TCB Formatter Output

**Rule:** `TCBFormatter` converts employee name to uppercase while preserving Vietnamese diacritics, appends currency `VND`, and truncates description to 100 characters.
**Output columns:**

| # | Header | Key | Transformation |
| --- | --- | --- | --- |
| 1 | Account Number | `acc_number` | Stripped account number |
| 2 | Beneficiary Name | `emp_name` | Uppercase, diacritics preserved |
| 3 | Amount | `amount` | Integer net amount |
| 4 | Currency | `currency` | Hardcoded `VND` |
| 5 | Remark | `description` | Truncated to 100 characters |
| 6 | Bank Code | `bank_code` | Empty string (reserved) |

### BR-PAY-054: Skip Payslips with Net <= 0

**Rule:** The `build_rows()` method iterates payslips and reads net amount from payslip line with code `thuc_lanh`. Payslips with net <= 0 are skipped and a warning is logged.
**Warning format:** "Payslip {number} co Net = 0 hoac am -- da bo qua."

### BR-PAY-055: Employee Bank Account Fallback Chain

**Rule:** Employee bank account resolution follows a 3-step fallback:
1. `employee.bank_account_id` if present (Enterprise field).
2. First bank account from `employee.address_home_id.bank_ids`.
3. First bank account from `employee.work_contact_id.bank_ids`.
**Behavior:** Returns `None` if all three sources are empty.

### BR-PAY-056: XLSX Formatting Standards

**Rule:** Generated XLSX files use openpyxl with: bold header row (row 1), `#,##0` number format for amount columns, right alignment for numeric cells, and auto-adjusted column widths capped at 40 characters.
**Worksheet name:** Bank code (e.g., "VCB", "TCB").

### BR-PAY-057: Generated Filename Pattern

**Rule:** Filename follows the pattern `{bank_code}_T{MM}_{YYYY}.xlsx` derived from `batch.date_start`.
**Example:** `VCB_T06_2026.xlsx`

### BR-PAY-058: Post-Generation Actions

**Rule:** Upon successful file generation, the wizard:
1. Creates an `ir.attachment` (base64-encoded) linked to the batch.
2. Creates an `hb.bank.file` record with `total_amount` (sum of row amounts), `record_count` (len of rows), and `state='generated'`.
3. Posts a chatter message on the batch: "Da sinh file {filename}: {count} dong, tong {amount} VND".

### BR-PAY-059: Bank File State Machine

**Rule:** `hb.bank.file` state machine is linear: `generated -> uploaded -> confirmed`. Each transition is guarded.
**Implementation:**
- `action_mark_uploaded()` requires `state == 'generated'`. Raises `UserError` otherwise.
- `action_mark_confirmed()` requires `state == 'uploaded'`. Raises `UserError` otherwise.
- No backward transitions are supported.

---

## 6. STANDARD vs CUSTOM MATRIX

| # | Component | Type | Standard / Custom | Notes |
| --- | --- | --- | --- | --- |
| 1 | `hb.bank.format` | Model | Custom (new model) | Bank format configuration. |
| 2 | `hb.bank.file` | Model | Custom (new model) | File lifecycle tracking. Inherits `mail.thread`. |
| 3 | `hb.bank.file.wizard` | TransientModel | Custom (new model) | Generation wizard with validation. |
| 4 | `BaseBankFormatter` | Python class | Custom | Abstract base class for formatter strategy. |
| 5 | `VCBFormatter` | Python class | Custom | Vietcombank-specific formatter. |
| 6 | `TCBFormatter` | Python class | Custom | Techcombank-specific formatter. |
| 7 | `BankFormatterRegistry` | Python class | Custom | Strategy registry resolving formatters by code. |
| 8 | `_remove_diacritics()` / `_to_uppercase_no_diacritics()` | Helper functions | Custom | Unicode NFKD normalization helpers. |
| 9 | `hb_bank_format_form` / `hb_bank_format_tree` | Odoo Views | Custom | Format configuration UI. |
| 10 | `hb_bank_file_form` / `hb_bank_file_tree` | Odoo Views | Custom | File lifecycle UI with statusbar and chatter. |
| 11 | `hb_bank_file_wizard_form` | Odoo View | Custom | Wizard dialog form. |
| 12 | `action_hb_bank_format` / `action_hb_bank_file` | Odoo Actions | Custom | Navigation actions. |
| 13 | `/hocba-hrm/api/payroll/bank-format*` | REST API | Custom | Format CRUD endpoints. |
| 14 | `/hocba-hrm/api/payroll/bank-file*` | REST API | Custom | File generate/list/upload/confirm endpoints. |
| 15 | `BankFile.jsx` | React component | Custom | File list and management UI. |
| 16 | `BankFileForm.jsx` | React component | Custom | File creation modal form. |
| 17 | `ir.attachment` | Model | Standard Odoo | Used to store generated XLSX binary. |
| 18 | `mail.thread` | Mixin | Standard Odoo | Chatter support on `hb.bank.file`. |
| 19 | `openpyxl` | Python library | Standard (pip) | XLSX generation library. |
| 20 | `hr.group_hr_manager` / `hr.group_hr_user` | Security Groups | Standard Odoo | Access control groups. |

---

### Appendix A: Validation Rules

| Rule ID | Field / Scope | Rule | Error Type |
| --- | --- | --- | --- |
| VR-001 | `payslip_batch_id.state` | Batch must be in state `close`. | `UserError` |
| VR-002 | Employee bank accounts | Every employee with a `done` payslip must have a non-empty bank account number. Missing accounts are listed by name and employee code. | `ValidationError` |
| VR-003 | Account number format | If `bank_format_id.account_format_regex` is set, every employee bank account must match the regex. Invalid accounts are listed by name and account number. | `ValidationError` |
| VR-005 | `payment_date` | Payment date must be >= `fields.Date.today()`. | `ValidationError` |
| VR-006 | Rows result | After building rows, if result is empty (all payslips had net = 0), wizard raises error. | `UserError` |

### Appendix B: Seed Data -- Bank Formats (`noupdate=1`)

| XML ID | Code | Name | Formatter Class | Encoding | Extension | Account Regex | Description Template |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `bank_format_vcb` | VCB | Vietcombank | VCBFormatter | utf-8-sig | xlsx | `^\d{10,14}$` | `Luong T{month}/{year} - {employee_code}` |
| `bank_format_tcb` | TCB | Techcombank | TCBFormatter | utf-8 | xlsx | `^\d{14}$` | `Luong T{month}/{year} - {employee_code}` |

### Appendix C: Security Access Control List

| ACL ID | Model | Group | Read | Write | Create | Delete |
| --- | --- | --- | --- | --- | --- | --- |
| `access_hb_bank_format_user` | `hb.bank.format` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_bank_format_manager` | `hb.bank.format` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_bank_file_user` | `hb.bank.file` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_bank_file_manager` | `hb.bank.file` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_bank_file_wizard_manager` | `hb.bank.file.wizard` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |

### Appendix D: Frontend API Functions (`payroll.js`)

| Function | HTTP | Endpoint | Parameters |
| --- | --- | --- | --- |
| `fetchBankFormats` | GET | `/hocba-hrm/api/payroll/bank-format` | -- |
| `createBankFormat(payload)` | POST | `/hocba-hrm/api/payroll/bank-format` | `{ name, code, formatter_class, ... }` |
| `updateBankFormat(id, payload)` | POST | `/hocba-hrm/api/payroll/bank-format/{id}` | partial object |
| `deleteBankFormat(id)` | POST | `/hocba-hrm/api/payroll/bank-format/{id}/delete` | -- |
| `fetchBankFiles(params)` | GET | `/hocba-hrm/api/payroll/bank-file` | `{ batch_id?, limit? }` |
| `generateBankFile(payload)` | POST | `/hocba-hrm/api/payroll/bank-file/generate` | `{ batch_id, bank_format_id }` |
| `markBankFileUploaded(id)` | POST | `/hocba-hrm/api/payroll/bank-file/{id}/upload` | -- |
| `markBankFileConfirmed(id)` | POST | `/hocba-hrm/api/payroll/bank-file/{id}/confirm` | -- |

### Appendix E: Source Files

| File | Purpose |
| --- | --- |
| `models/bank_format.py` | `hb.bank.format` Odoo model |
| `models/bank_file.py` | `hb.bank.file` Odoo model and methods |
| `models/bank_formatter.py` | Strategy classes and registry (plain Python) |
| `wizards/bank_file_wizard.py` | `hb.bank.file.wizard` TransientModel |
| `views/bank_format_views.xml` | Form, list, and action for `hb.bank.format` |
| `views/bank_file_views.xml` | Form, list, and action for `hb.bank.file` |
| `wizards/bank_file_wizard_views.xml` | Wizard form view and action |
| `data/bank_format_data.xml` | Seed data for VCB and TCB formats |
| `controllers/payroll_api.py` | REST API endpoints for bank-format and bank-file |
| `frontend/src/features/payroll/BankFile.jsx` | Bank file list and management UI |
| `frontend/src/features/payroll/BankFileForm.jsx` | Bank file creation form component |
| `frontend/src/api/payroll.js` | Frontend API client methods |
