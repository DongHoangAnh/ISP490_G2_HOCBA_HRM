# BPMN Prompts cho các spec Payroll

Mỗi prompt dưới đây dùng để AI đọc và vẽ file `.bpmn` tương ứng.
Sau khi vẽ xong, bỏ file `.bpmn` vào Section 2 (FUNCTION FLOW) của từng spec.

---

## 1. FS-PAY-001 — Salary Structure & Rule Configuration

### Prompt 1.1: Main Flow 1 — Structure Management (HR Manager)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 1 — Structure Management

Actors / Lanes: HR Manager, Odoo System

[1] HR Manager navigates to: Payroll > Cấu hình > Cấu trúc lương

[2] System displays the salary structure list view (view_salary_structure_list) showing columns: name, code, rule_count, active

[3] HR Manager clicks "New" button

[4] System opens the salary structure form view (view_salary_structure_form) with an empty record

[5] HR Manager fills in name (h1 title field), code, active toggle, and optional note

[6] System validates fields: name and code are required. Code has UNIQUE SQL constraint (_code_uniq)

[7] HR Manager clicks Save

[8] System creates the hb.salary.structure record. rule_count is computed as 0

[9] HR Manager opens the "Quy tắc lương" notebook tab

[10] System displays an inline editable list of rule_ids with columns: sequence (handle widget), code, name, category_id, amount_type, appears_on_payslip, active

[11] HR Manager adds rules inline or navigates to standalone rule form (→ Flow 2)

[12] (Optional) HR Manager archives the structure by toggling active to False → System hides structure from default list views

Error / Exception Flow:
• Duplicate structure code → SQL UNIQUE constraint raises IntegrityError. Message: "Mã cấu trúc lương phải là duy nhất!"
• Delete structure with linked rules → PostgreSQL ondelete='cascade' deletes all associated rules
```

### Prompt 1.2: Main Flow 2 — Rule Configuration (HR Manager)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 2 — Rule Configuration

Actors / Lanes: HR Manager, Odoo System

[1] HR Manager opens a salary structure form and clicks "Add a line" in the rules list, or opens the standalone salary rule form (view_salary_rule_form)

[2] System displays the rule form with two main groups: "Thông tin" and "Tính toán"

[3] HR Manager fills in required fields: name, code, sequence, structure_id, category_id

[4] HR Manager selects amount_type

[5] System conditionally shows/hides fields:
    - amount_type='fixed': shows amount_fixed only
    - amount_type='percentage': shows amount_percentage and amount_percentage_base only
    - amount_type='formula': shows formula section with quick-insert buttons and help button
    - amount_type='code': shows Python code section only

[6a] (Gateway: amount_type) If 'fixed': HR Manager enters amount_fixed (Float 16,0)
[6b] If 'percentage': HR Manager enters amount_percentage and amount_percentage_base
[6c] If 'formula': HR Manager enters formula using Excel-like syntax (IF, SUM, MAX, MIN, ABS, ROUND)
[6d] If 'code': HR Manager enters Python code in the code widget

[7] (Optional) HR Manager sets condition_type to 'python' and enters condition_python

[8] HR Manager toggles appears_on_payslip

[9] HR Manager saves the record

[10] System creates/updates the hb.salary.rule record. Parent structure's rule_count is recomputed via _compute_rule_count

Error / Exception Flow:
• Missing required fields on API rule creation → REST returns { "success": false, "error": "Missing required field: <field>" } with HTTP 400
• Delete category with linked rules → ondelete='restrict' prevents deletion
• API salary rule not found (update/delete) → Returns HTTP 404
• API category not found (update/delete) → Returns HTTP 404
• API reorder with invalid IDs → Non-existent rule IDs silently skipped
```

### Prompt 1.3: Main Flow 3 — Formula Engine (HR Manager + System)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 3 — Formula Engine

Actors / Lanes: HR Manager, Odoo System, Computation Engine

[1] HR Manager selects amount_type='formula' on a salary rule

[2] System shows the formula input section with text field, quick-insert buttons (IF, SUM, MAX, MIN, ABS, ROUND), and "Hướng dẫn hàm" button

[3] (Optional) HR Manager clicks a quick-insert button (e.g., "SUM( , )")

[4] System calls action_insert_formula_func() — reads formula_snippet from button context, appends to current amount_formula value, form reloads

[5] (Optional) HR Manager clicks "Hướng dẫn hàm" button

[6] System calls action_show_formula_help() — opens hb.formula.help.wizard transient model in dialog (target='new')

[7] Wizard's default_get() calls _build_help_html() — generates HTML table documenting 7 functions + supported operators

[8] HR Manager enters a formula, e.g., SUM(luong_thoi_gian, thuong_khac)

[9] Formula is stored as-is in amount_formula

[10] (At payslip computation time) Computation Engine calls _transpile_formula(formula, known_codes):
    - IF(c,a,b) → ((a) if (c) else (b))
    - SUM(a,b) → _range_sum('a','b')
    - ROUND(x,y) → _round_dir(x,y)
    - Known rule codes → rules.get('code',0)

[11] Resulting Python expression is executed via safe_eval

Error / Exception Flow:
• Invalid formula syntax at transpile time → _transpile_formula produces invalid Python → safe_eval raises exception during payslip computation
• Rule condition evaluates to falsy → Rule amount is set to 0, line may still appear if appears_on_payslip=True
• Duplicate category code → SQL UNIQUE constraint raises IntegrityError. Message: "Mã danh mục phải là duy nhất!"
```

---

## 2. FS-PAY-002 — Payslip Computation Engine

### Prompt 2.1: Main Flow — Salary Computation (action_compute_sheet)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow — Salary Computation (action_compute_sheet)

Actors / Lanes: HR Manager, Odoo System, Computation Engine

[1] HR Manager clicks "Tính lương" button on payslip form (or batch action triggers computation)

[2] System calls action_compute_sheet() — iterates payslips in self

[3] For each payslip: Computation Engine calls _ensure_draft_state()
    → Raises UserError if state is not 'draft' or 'verify'

[4] Computation Engine calls _resolve_contract():
    - If contract_id already set → use it
    - Else search hb.contract where employee matches, state='open', date overlaps
    - If found → assign to payslip
    - If not found → raise ValidationError with employee name and date range

[5] Computation Engine calls _resolve_structure(contract):
    Priority chain:
    - (1) payslip.structure_id if set
    - (2) contract.x_structure_id if set
    - (3) Auto-detect by employee.x_work_form: 'online' → STRUCT_ONLINE, else → STRUCT_OFFLINE
    - If none found → raise ValidationError

[6] System clears existing lines: slip.line_ids.unlink()

[7] Computation Engine calls _build_localdict(contract) — builds evaluation namespace with:
    payslip, employee, contract, worked_days (WorkedDaysProxy), inputs (InputsProxy),
    categories (CategoryTotals), rules (dict), _range_sum, _round_dir, result, result_qty, result_rate, builtins

[8] Computation Engine collects active rules: structure.rule_ids.filtered('active').sorted('sequence')

[9] Initialize warnings = []

[10] For each rule in sequence order:
    [10a] Evaluate condition: _evaluate_rule_condition(rule, localdict)
          - If condition_type != 'python' or condition_python empty → True
          - Else → bool(safe_eval(condition_python, localdict))
          - If False → skip rule (continue)

    [10b] Evaluate amount: _evaluate_rule_amount(rule, localdict) → returns (amount, qty, rate)
          Gateway by amount_type:
          - 'code': exec safe_eval(amount_python_compute) → read result/result_qty/result_rate
          - 'fixed': return (amount_fixed, 1.0, 0.0)
          - 'percentage': eval base via safe_eval, compute round(base * pct / 100)
          - 'formula': transpile formula → safe_eval → read result

    [10c] Store result: rules[rule.code] = amount; categories.accumulate(category_code, amount)

    [10d] If appears_on_payslip=True → create hb.payslip.line record

    [10e] Error handling: If exception in 10a/10b → log warning, append to warnings, produce (0.0, 1.0, 0.0)

[11] Finalize: write structure_id, set x_teaching_computed=True, store x_compute_warnings (or False if no warnings)

[12] Return True

Error / Exception Flow:
• State is not draft/verify → UserError raised at step 3
• No active contract found for employee in date range → ValidationError at step 4
• No salary structure found → ValidationError at step 5
• Rule evaluation exception → Warning logged, rule produces amount=0, computation continues
• Invalid formula → safe_eval exception caught per rule, warning appended
```

### Prompt 2.2: Sub-Flow — PIT Calculation (_hocba_pit)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Sub-Flow — PIT Calculation (Personal Income Tax)

Actors / Lanes: Computation Engine

[1] Rule code invokes _hocba_pit(taxable_income)

[2] If taxable_income <= 0 → return 0.0

[3] Apply 7-bracket progressive tax:
    - Bracket 1: 0 – 5,000,000 VND → 5%
    - Bracket 2: 5,000,001 – 10,000,000 → 10%
    - Bracket 3: 10,000,001 – 18,000,000 → 15%
    - Bracket 4: 18,000,001 – 32,000,000 → 20%
    - Bracket 5: 32,000,001 – 52,000,000 → 25%
    - Bracket 6: 52,000,001 – 80,000,000 → 30%
    - Bracket 7: 80,000,001+ → 35%

[4] Sum tax from each bracket that taxable_income falls into

[5] Return round(total_tax)
```

---

## 3. FS-PAY-003 — Payslip Lifecycle & Batch Management

### Prompt 3.1: Main Flow 1 — Payslip Lifecycle State Machine

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 1 — Payslip Lifecycle State Machine

Actors / Lanes: HR Manager, Odoo System

[1] System creates a new payslip → state = 'draft'
    - Auto-generates number via ir.sequence 'hb.payslip' (format: SLIP/YYYY/MM/NNNN)
    - Auto-generates x_access_token (UUID v4)
    - Auto-computes name: "Lương {employee_name} -- {MM/YYYY}"

[2] HR Manager clicks "Tính lương" → System calls action_compute_sheet() (see FS-PAY-002)
    → Sets x_teaching_computed = True

[3] HR Manager clicks "Xác nhận" (verify):
    → System calls action_payslip_verify()
    → Guard: state must be 'draft', else UserError
    → State changes: draft → verify

[4] HR Manager clicks "Hoàn tất" (done):
    → System calls action_payslip_done()
    → Guard: state must be 'draft' or 'verify', else UserError
    → Guard: x_teaching_computed must be True, else UserError
    → State changes: draft/verify → done

[5] (Optional) HR Manager clicks "Huỷ":
    → System calls action_payslip_cancel()
    → No precondition — from any state
    → State changes: any → cancel

[6] (Optional, from 'done') HR Manager clicks "Reset về Nháp":
    → System calls action_reset_to_draft(reason)
    → Guard: state must be 'done'
    → Guard: current user must be HR Manager (hr.group_hr_manager)
    → Guard: reason string must be non-empty
    → State changes: done → draft
    → Clears x_teaching_computed = False
    → Posts chatter message with reason and user name

Error / Exception Flow:
• action_payslip_verify when state != 'draft' → UserError
• action_payslip_done when state != 'draft'/'verify' → UserError
• action_payslip_done when x_teaching_computed = False → UserError "Phải tính lương trước"
• action_reset_to_draft when state != 'done' → UserError
• action_reset_to_draft without HR Manager role → UserError
• action_reset_to_draft with empty reason → UserError
```

### Prompt 3.2: Main Flow 2 — Batch Management

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 2 — Batch Management (hb.payslip.run)

Actors / Lanes: HR Manager, Odoo System, SPA Frontend

[1] HR Manager creates a new batch (via SPA POST /payroll/batch or Odoo form):
    → Fills in: name, date_start, date_end
    → State = 'draft'

[2] HR Manager clicks "Tạo phiếu lương" (Generate payslips):
    → SPA calls POST /payroll/batch/{id}/generate
    → System searches all active employees with open contracts
    → For each employee with valid contract: creates hb.payslip linked to batch
    → Employees without matching contract → added to 'skipped' list
    → Response: { created: N, skipped: [...] }

[3] HR Manager computes salary for payslips:
    → SPA calls POST /payroll/payslip/{id}/compute for each payslip
    → System calls action_compute_sheet() (see FS-PAY-002)

[4] HR Manager clicks "Xác nhận" batch (verify):
    → System calls action_verify()
    → Guard: state must be 'draft', else UserError
    → State changes: draft → verify

[5] HR Manager clicks "Đóng batch" (close):
    → System calls action_close()
    → Guard: state must not be 'close'
    → Cascade: iterates all child payslips in state 'draft' or 'verify', calls action_payslip_done() on each
    → Guard per payslip: x_teaching_computed must be True (else UserError)
    → Sets batch state to 'close'
    → Posts chatter message with total payslip count

[6] (Alternative) HR Manager uses "Lưu lịch sử" in SPA (close by period):
    → SPA calls POST /payroll/batch/close-by-period with { month, year }
    → System finds all non-cancelled payslips in that period
    → Guard: every payslip must have x_employee_confirm == 'confirmed'
    → If any unconfirmed → returns error listing up to 5 employee names
    → If all confirmed → calls action_close() on all related batches

[7] (Optional) HR Manager clicks "Reset Nháp":
    → System calls action_reset_draft()
    → No precondition
    → State changes: any → draft

Error / Exception Flow:
• action_verify when state != 'draft' → UserError
• action_close when state == 'close' → UserError
• Batch close cascade when child payslip has x_teaching_computed = False → UserError
• close-by-period when unconfirmed payslips exist → error listing employee names
```

---

## 4. FS-PAY-004 — Bank Payment File Generation

### Prompt 4.1: Main Flow — Bank File Generation (HR Manager)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow — Bank Payment File Generation

Actors / Lanes: HR Manager, Odoo System, Formatter Engine, SPA Frontend

[1] HR Manager opens a payslip batch in state 'close' (Done)

[2] HR Manager clicks "Tạo file Ngân hàng" (from Odoo form) or uses SPA POST /bank-file/generate

[3] System opens the hb.bank.file.wizard form:
    - payslip_batch_id (readonly, from context)
    - payslip_count (computed: count of 'done' payslips)
    - total_net (computed: sum of net amounts from line code 'thuc_lanh')
    - bank_format_id (select from active bank formats)
    - company_bank_id (company bank account)
    - payment_date (default: tomorrow)
    - description (default: "Lương T{month}/{year}")

[4] HR Manager selects bank_format_id, company_bank_id, payment_date, description

[5] HR Manager clicks "Tạo file"

[6] System runs validation (_validate):
    - VR-001: Batch must be in state 'close' → else UserError
    - VR-002: Every employee with 'done' payslip must have bank account → else ValidationError listing missing accounts
    - VR-003: If account_format_regex set, validate all account numbers → else ValidationError listing invalid accounts
    - VR-005: payment_date >= today → else ValidationError
    (Any validation fails → show error, stop)

[7] Formatter Engine loads formatter via BankFormatterRegistry.get(bank_format_code):
    Gateway by bank code:
    - 'VCB' → VCBFormatter: uppercase name without diacritics (NFKD), columns: STT, Số tài khoản, Tên người nhận, Số tiền, Nội dung
    - 'TCB' → TCBFormatter: uppercase name with diacritics, currency="VND", description max 100 chars, columns: Account Number, Beneficiary Name, Amount, Currency, Remark, Bank Code

[8] Formatter Engine calls build_rows():
    - Iterates done payslips, reads net amount from line code 'thuc_lanh'
    - Resolves employee bank account (fallback chain: bank_account_id → address_home_id.bank_ids → work_contact_id.bank_ids)
    - Payslips with net <= 0 are skipped with warning

[9] VR-006: If rows result is empty (all net=0) → UserError, stop

[10] System generates XLSX file via openpyxl:
    - Bold header row, #,##0 number format for amounts, right-aligned numeric cells
    - Auto-adjusted column widths (max 40 chars)
    - Filename: {bank_code}_T{MM}_{YYYY}.xlsx

[11] System creates ir.attachment linked to batch

[12] System creates hb.bank.file record:
    - name, batch_id, bank_format_id, attachment_id, payment_date
    - total_amount, record_count, generated_by, generated_at
    - state = 'generated'

[13] System posts chatter message on batch: file name, row count, total amount

[14] System returns download URL action

Error / Exception Flow:
• Batch not in 'close' state → UserError at VR-001
• Employee missing bank account → ValidationError listing employee names at VR-002
• Invalid bank account format → ValidationError listing invalid accounts at VR-003
• Payment date in past → ValidationError at VR-005
• All payslips have net=0 → UserError at VR-006
• Bank format code not found in registry → error
```

### Prompt 4.2: Sub-Flow — Bank File Lifecycle

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Sub-Flow — Bank File Lifecycle (hb.bank.file state machine)

Actors / Lanes: HR Manager, Odoo System

[1] File is created with state = 'generated'

[2] HR Manager uploads file to bank portal, then clicks "Đánh dấu Uploaded":
    → System calls action_mark_uploaded()
    → Guard: state must be 'generated', else UserError
    → State changes: generated → uploaded

[3] Bank confirms payment, HR Manager clicks "Xác nhận NH":
    → System calls action_mark_confirmed()
    → Guard: state must be 'uploaded', else UserError
    → State changes: uploaded → confirmed

Error / Exception Flow:
• action_mark_uploaded when state != 'generated' → UserError
• action_mark_confirmed when state != 'uploaded' → UserError
```

---

## 5. FS-PAY-005 — Employee Payslip Confirmation & Email

### Prompt 5.1: Main Flow 1 — Send Payslip Email (HR Manager)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 1 — Send Payslip Email

Actors / Lanes: HR Manager, SPA Frontend, Odoo System, Mail Server

[1] HR Manager selects payslips in BatchList.jsx (checkbox column)

[2] HR Manager clicks "Gửi mail (N)" button (blue, disabled when checkedCount=0)

[3] SPA Frontend calls POST /hocba-hrm/api/payroll/payslip/send-mail with { payslip_ids: [...] }

[4] Odoo System iterates each payslip:
    For each payslip:
    [4a] Read employee work_email (fallback to email field)
    [4b] If no email found → add to 'skipped' list with reason "Không có email", continue to next

    [4c] Read email templates from ir.config_parameter:
         - Key 'hocba_payroll.mail_subject' → fallback to default: "Bảng lương tháng {month}/{year} — {employee_name}"
         - Key 'hocba_payroll.mail_body' → fallback to _default_mail_body()

    [4d] Build template variables:
         - employee_name, month, year, gross (formatted), net (formatted)
         - view_url = {web.base.url}/payslip/view/{x_access_token}
         - If x_access_token is empty → generate new UUID, save to payslip

    [4e] Render templates: _render_mail_tpl(tpl, variables) — calls tpl.format(**variables) with error suppression

    [4f] Create mail.mail record with auto_delete=True

    [4g] Mail Server sends email

    [4h] Update payslip: x_email_sent=True, x_email_sent_date=now

[5] System returns response: { sent: N, skipped: [...] }

[6] SPA shows alert with sent/skipped counts

Error / Exception Flow:
• payslip_ids is missing or empty → HTTP 400
• No valid payslips found → HTTP 404
• Employee has no email → silently skipped, added to skipped list
• Mail send exception per payslip → skipped with error message as reason
• Template rendering error (bad placeholder) → returns raw template unchanged
```

### Prompt 5.2: Main Flow 2 — Employee Confirms/Rejects Payslip (Public)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Main Flow 2 — Employee Payslip Confirmation (Public Page)

Actors / Lanes: Employee, Public Controller, Odoo System

[1] Employee receives email with link: /payslip/view/{token}

[2] Employee clicks the link

[3] Public Controller receives GET /payslip/view/{token} (auth='public', csrf=False)

[4] Controller calls _get_payslip_by_token(token):
    - Searches hb.payslip with sudo() by x_access_token == token, limit=1
    - If not found → render payslip_public_not_found (404 page)

[5] Controller renders payslip_public_view template with context:
    - slip, employee, lines (sorted by sequence), month, year, gross, net, token
    - Lines with code containing 'thuc_lanh' receive CSS class 'line-net' (green)

[6] Employee views payslip details on public page:
    - Header: "Phiếu lương tháng {month}/{year}", employee name, job title
    - Info bar: employee ID, department, confirmation status badge
    - Salary lines with formatted amounts
    - Total bar: "Thực lĩnh" with net amount

[7] Gateway: slip.x_employee_confirm status?
    - If 'confirmed' → show green message "Bạn đã xác nhận phiếu lương này" → END
    - If 'rejected' → show red message with feedback → END
    - If 'pending' → show action buttons (continue to step 8)

[8a] Employee clicks "Xác nhận" button:
    → POST /payslip/view/{token}/confirm
    → Controller checks x_employee_confirm == 'pending'
    → If not pending → redirect with ?msg=already_actioned
    → Write x_employee_confirm='confirmed', x_confirmed_date=now
    → Redirect with ?msg=confirmed
    → Page shows green success message

[8b] Employee clicks "Từ chối" button:
    → JavaScript toggles reject form visibility (classList.toggle('show'))
    → Employee enters rejection reason in textarea (required)
    → Employee clicks "Gửi phản hồi"
    → POST /payslip/view/{token}/reject with feedback parameter
    → Controller checks x_employee_confirm == 'pending'
    → If not pending → redirect with ?msg=already_actioned
    → If feedback is empty/whitespace → redirect with ?msg=feedback_required
    → Write x_employee_confirm='rejected', x_employee_feedback=feedback, x_confirmed_date=now
    → Redirect with ?msg=rejected
    → Page shows red rejection message

Error / Exception Flow:
• Invalid/expired token → render 404 page (payslip_public_not_found)
• Payslip already confirmed or rejected → redirect with ?msg=already_actioned
• Reject without feedback text → redirect with ?msg=feedback_required
• Token not found on confirm/reject POST → HTTP 404 response
```

### Prompt 5.3: Sub-Flow — Email Template Management (ConfigView)

```
tạo file .bpmn cho tôi về phần này đầy đủ các lane cho tôi:
Sub-Flow — Email Template Management

Actors / Lanes: HR Manager, SPA Frontend, Odoo System

[1] HR Manager navigates to Payroll > Cấu hình tab > "Mẫu email" sub-tab in SPA

[2] SPA Frontend calls GET /hocba-hrm/api/payroll/mail-template

[3] Odoo System reads ir.config_parameter keys:
    - hocba_payroll.mail_subject → fallback to default
    - hocba_payroll.mail_body → fallback to default

[4] SPA displays email template editor:
    - Placeholder guide box listing: {employee_name}, {month}, {year}, {gross}, {net}, {view_url}
    - Subject input field
    - Body textarea (monospace, HTML)

[5] HR Manager edits subject and/or body content

[6] (Optional) HR Manager clicks "Xem trước" → SPA opens preview Modal:
    - Substitutes placeholders with sample values (Nguyễn Văn A, 06, 2026, 15,000,000, 12,500,000)
    - Renders HTML body via dangerouslySetInnerHTML

[7] HR Manager clicks "Lưu mẫu email"

[8] SPA Frontend calls POST /hocba-hrm/api/payroll/mail-template with { subject, body }

[9] Odoo System writes to ir.config_parameter via sudo():
    - set_param('hocba_payroll.mail_subject', subject)
    - set_param('hocba_payroll.mail_body', body)

[10] SPA shows success message "Đã lưu thành công!"

Error / Exception Flow:
• Save fails → SPA shows error message "Lỗi: {error}"
```
