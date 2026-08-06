# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-003 |
| **Function Name** | Payslip Lifecycle & Batch Management |
| **Created Date** | 21/06/2026 |
| **Last Update Date** | 21/06/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP (Community / Enterprise) |
| **Reference** | `hb.payslip`, `hb.payslip.run`, `hb.payslip.line`, `hb.payslip.worked_days`, `hb.payslip.input`, `payroll_api.py`, `payslip_views.xml`, `BatchList.jsx`, `BatchDrawer.jsx`, `PayslipDrawer.jsx` -- module `hocba_payroll` |

| **Approver** | **Reviewer** | **Creator** |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

---

## CHANGE HISTORY

| No | Version | Change Description | Affected Sections | Date | Author |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial formatted version from payroll BE/FE implementation | All | 21/06/2026 | Group G2 |
| 2 | 1.1 | Full rewrite with detailed field specs, screen layouts, API endpoints, SPA component documentation, and business rules derived from actual source code | All | 21/06/2026 | Group G2 |

---

## 1. FUNCTION OVERVIEW

| Item | Detail |
| --- | --- |
| **Function ID** | FS-PAY-003 |
| **Function Name** | Payslip Lifecycle & Batch Management |
| **Created Date** | 21/06/2026 |
| **Last Modified Date** | 21/06/2026 |

| Attribute | Value |
| --- | --- |
| **Processing Time** | On-demand |
| **Processing Type** | Interactive + REST API |
| **Function Type** | Transaction / Workflow |
| **Multilingual** | No |

### Business Requirement & Function Overview

**Overview:**
This function manages the full lifecycle of payslip batches and individual payslips: create batch, generate payslips, compute salary, verify/finalize, and close period. It is the central workflow module that orchestrates payslip creation and state transitions, connecting the computation engine (FS-PAY-002), bank payment file generation (FS-PAY-004), and employee confirmation flow (FS-PAY-005).

**Business Context:**
Hoc Ba Education processes payroll monthly. Each month, the HR Manager creates a payslip batch (period), generates payslips for all active employees, computes salary using data-driven rules, verifies results, and closes the batch. Individual payslips follow a state machine (`draft -> verify -> done`) while batches follow a parallel state machine (`draft -> verify -> close`). The system supports both Odoo backend UI and a React SPA frontend.

**Core State Machines:**
- `hb.payslip.run` (Batch): `draft -> verify -> close` (with `action_reset_draft` back to draft)
- `hb.payslip` (Payslip): `draft -> verify -> done` (with `cancel` from draft/verify, and `action_reset_to_draft` from done by HR Manager only)

**Functional Scope:**
- CRUD operations on payslip batches (`hb.payslip.run`) with period dates.
- Batch-level payslip generation for all active employees with open contracts.
- Individual payslip state transitions: compute, verify, finalize, cancel, reset.
- Batch-level state transitions: verify, close (finalizes all child payslips), reset.
- Close-by-period workflow: verifies all employees confirmed before locking the month.
- Employee payroll summary endpoint with dynamic salary rule columns.
- Odoo backend form/list views for both models.
- React SPA screens: `BatchList.jsx` (payroll dashboard), `BatchDrawer.jsx` (batch detail), `BatchForm.jsx` (create batch), `PayslipDrawer.jsx` (payslip detail).

**Users:**
- **HR Manager** (`hr.group_hr_manager`): Full CRUD on all payroll models. Can reset finalized payslips (requires reason). Can close batches and periods.
- **HR User** (`hr.group_hr_user`): Read-only access on payslip, batch, and line models. Cannot modify payslip state or reset done payslips.

---

## 2. FUNCTION FLOW

### Main Flow 1 -- Batch Creation & Payslip Generation

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Creates a batch via SPA `BatchForm.jsx` or Odoo backend | `POST /batch` creates `hb.payslip.run` with `name`, `date_start`, `date_end`. State defaults to `draft`. |
| 2 | HR Manager | Clicks "Tao phieu luong" (Generate Payslips) in batch detail | `POST /batch/<id>/generate` searches all active employees (`hr.employee`) with an open contract (`hb.contract`, `state='open'`) overlapping the batch period. Creates one `hb.payslip` per matched employee. Employees without a matching contract are collected in a `skipped` list. Auto-assigns `structure_id` from `contract.x_structure_id` if present. |
| 3 | System | Returns generation summary | Response includes `created` count and `skipped` employee names. |

**REST API (Batch CRUD):**
- `POST /hocba-hrm/api/payroll/batch` -- Create batch. Required: `name`, `date_start`, `date_end`. Returns `{ id, name, state }`.
- `GET /hocba-hrm/api/payroll/batch` -- List batches ordered by `date_start desc`. Optional: `limit` (default 50). Returns array of `{ id, name, date_start, date_end, state, payslip_count }`.
- `GET /hocba-hrm/api/payroll/batch/<id>` -- Get batch detail with nested payslip list.
- `POST /hocba-hrm/api/payroll/batch/<id>/generate` -- Generate payslips for batch.

**React SPA -- BatchForm.jsx:**
Modal form with fields: "Ten ky luong" (auto-filled `Luong T{month}/{year}`), "Tu ngay" (first of month), "Den ngay" (last of month). Changing `date_start` auto-updates `name` and `date_end`. Calls `createBatch(form)` on submit.

### Main Flow 2 -- Payslip Lifecycle (Compute -> Verify -> Done)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Opens a payslip and clicks "Tinh luong" (Compute) | `action_compute_sheet()` is called. Requires state `draft` or `verify`. Resolves contract and salary structure, evaluates all active rules in sequence order, creates payslip lines (`hb.payslip.line`), sets `x_teaching_computed=True`, stores any warnings in `x_compute_warnings`. See FS-PAY-002 for computation engine details. |
| 2 | HR Manager | Clicks "Gui xac nhan" (Send for Verification) | `action_payslip_verify()` transitions state from `draft` to `verify`. Raises `UserError` if state is not `draft`. |
| 3 | HR Manager | Clicks "Hoan tat" (Finalize) | `action_payslip_done()` transitions state to `done`. Requires state `draft` or `verify` AND `x_teaching_computed=True`. Raises `UserError` if salary has not been computed. |
| 4 | HR Manager | Clicks "Huy" (Cancel) | `action_payslip_cancel()` transitions state to `cancel` from `draft` or `verify` only. |
| 5 | HR Manager | (Done payslip) Clicks "Reset ve nhap" | `action_reset_to_draft(reason)` requires state `done`, `hr.group_hr_manager` group, and a non-empty `reason` string. Raises `UserError` otherwise. Transitions back to `draft`. |

**REST API (Payslip):**
- `GET /hocba-hrm/api/payroll/payslip` -- List payslips. Filters: `batch_id`, `employee_id`, `state`, `year`, `month`, `limit` (default 500).
- `GET /hocba-hrm/api/payroll/payslip/<id>` -- Get payslip detail with lines, worked days, inputs.
- `POST /hocba-hrm/api/payroll/payslip/<id>/compute` -- Compute payslip salary.
- `POST /hocba-hrm/api/payroll/payslip/<id>/confirm` -- Finalize payslip (calls `action_payslip_done()`).
- `POST /hocba-hrm/api/payroll/payslip/<id>/reset` -- Reset to draft. Required body: `{ reason }`.

**React SPA -- PayslipDrawer.jsx:**
Slide-over drawer with tabs: "Chi tiet luong" (salary lines grouped by category), "Ngay cong" (worked days), "Dau vao" (inputs). Action buttons change by state: "Tinh luong" (draft), "Xac nhan" (draft with lines), "Reset ve nhap" (done, shows reason input). Header shows red gradient with employee name, payslip number, structure, and state badge.

### Main Flow 3 -- Batch Lifecycle (Verify -> Close)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Clicks "Xac nhan" on batch | `action_verify()` transitions batch state from `draft` to `verify`. Raises `UserError` if not in `draft`. |
| 2 | HR Manager | Clicks "Dong batch" on batch | `action_close()` iterates all child payslips in `draft` or `verify` state, calls `action_payslip_done()` on each, then transitions batch state to `close`. Posts chatter message: "Batch da duoc dong. X payslips hoan tat." |
| 3 | HR Manager | (Optional) Clicks "Reset Nhap" | `action_reset_draft()` transitions batch back to `draft` state. |
| 4 | HR Manager | (Close state) Clicks "Tao file Ngan hang" | `action_open_bank_file_wizard()` opens the bank file generation wizard. See FS-PAY-004. |

**REST API:**
- `POST /hocba-hrm/api/payroll/batch/<id>/close` -- Close batch and finalize all child payslips.

### Main Flow 4 -- Save Payroll History by Period (Close-by-Period)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In `BatchList.jsx`, clicks "Luu lich su" button | FE validates that all employees in the period have `employee_confirm == 'confirmed'`. Button is disabled (gray) if any employee is not confirmed. |
| 2 | HR Manager | Confirms the action in browser dialog | FE calls `POST /batch/close-by-period` with `{ month, year }`. |
| 3 | Backend | Searches all payslips in the given month/year where `state != 'cancel'` | Validates every payslip has `x_employee_confirm == 'confirmed'`. |
| 4 | Backend | If any unconfirmed employees | Returns error listing up to 5 unconfirmed employee names: "Con X nhan vien chua xac nhan: [names]..." |
| 5 | Backend | If all confirmed | Calls `action_close()` on all related batches in the period. Returns list of closed batches and total payslip count. |

**REST API:**
- `POST /hocba-hrm/api/payroll/batch/close-by-period` -- Required: `{ month, year }`. Returns `{ closed_batches, payslip_count }`.

### Main Flow 5 -- Employee Payroll Summary

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR User/Manager | Opens `BatchList.jsx` (SPA payroll dashboard) | FE calls `GET /employee-payroll?month=M&year=Y` to load the summary table. |
| 2 | System | Collects salary rule columns | Reads active salary rules where `appears_on_payslip=True`, returns as dynamic columns with `id`, `code`, `name`, `sequence`. |
| 3 | System | Collects employee payroll data | For each active employee, finds the latest payslip in the period, extracts `amounts` dict keyed by rule code, plus `employee_confirm`, `email_sent`, `employee_feedback` status. |

**REST API:**
- `GET /hocba-hrm/api/payroll/employee-payroll` -- Query: `month` (1-12, defaults to current), `year` (defaults to current). Returns `{ month, year, columns, employees }`.

### Main Flow 6 -- Batch Compute All (SPA)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Opens batch detail in SPA `BatchDrawer.jsx` and clicks "Tinh luong tat ca" | FE iterates through all draft payslips in the batch sequentially. |
| 2 | FE | For each draft payslip | Calls `POST /payslip/<id>/compute`. Shows progress: "Dang tinh {i}/{n}..." |
| 3 | FE | If any computation fails | Stops processing and displays the error. Remaining payslips are not computed. |
| 4 | FE | On completion | Reloads batch detail to show updated states and amounts. |

### Error/Exception Flow

| Error Scenario | System Behavior |
| --- | --- |
| Verify batch not in `draft` | `UserError`: batch must be in draft state to verify |
| Close batch with un-computed payslips | `action_close()` calls `action_payslip_done()` which raises `UserError` if `x_teaching_computed=False` |
| Finalize payslip not computed | `UserError`: salary must be computed before finalizing |
| Finalize payslip in wrong state | `UserError`: payslip must be in draft or verify state |
| Cancel payslip in done state | Not allowed; cancel only from draft/verify |
| Reset payslip without reason | `UserError`: reason is required |
| Reset payslip by non-manager | `UserError`: only HR Manager can reset |
| Close-by-period with unconfirmed employees | 400 error with list of up to 5 unconfirmed names |
| Generate payslips for employee without contract | Employee added to `skipped` list; no payslip created |
| Compute payslip without active contract | `ValidationError` naming the employee and date range |
| Compute payslip without salary structure | `ValidationError` if no structure found at any priority level |
| Rule evaluation error during computation | Warning logged, rule defaults to amount=0; computation continues (see FS-PAY-002) |

---

## 3. SCREEN LAYOUT

### Screen 1: Payslip Batch List (`hb_payslip_run_tree`)

**View type:** List
**XML ID:** `hocba_payroll.hb_payslip_run_tree`
**Model:** `hb.payslip.run`

| Column | Field | Widget | Decoration | Notes |
| --- | --- | --- | --- | --- |
| Ten | `name` | (default Char) | -- | Batch name |
| Tu ngay | `date_start` | (default Date) | -- | Period start |
| Den ngay | `date_end` | (default Date) | -- | Period end |
| So phieu luong | `payslip_count` | (default Integer) | -- | Computed count |
| Trang thai | `state` | badge | `decoration-info`=draft, `decoration-warning`=verify, `decoration-success`=close | State badge |

**Action:** `action_hb_payslip_run` (xml_id: `hocba_payroll.action_hb_payslip_run`)
- `res_model`: `hb.payslip.run`
- `view_mode`: `list,form`

### Screen 2: Payslip Batch Form (`hb_payslip_run_form`)

**View type:** Form
**XML ID:** `hocba_payroll.hb_payslip_run_form`
**Model:** `hb.payslip.run`

**Layout:**

```
<header>
  <button name="action_verify" string="Xac nhan"
          invisible="state != 'draft'"/>
  <button name="action_close" string="Dong batch"
          invisible="state != 'verify'" class="btn-success"/>
  <button name="action_reset_draft" string="Reset Nhap"
          invisible="state == 'draft'"/>
  <button name="action_open_bank_file_wizard"
          string="Tao file Ngan hang"
          invisible="state != 'close'" class="btn-warning"/>
  <field name="state" widget="statusbar"
         statusbar_visible="draft,verify,close"/>
</header>
<sheet>
  <div class="oe_button_box">
    <button name="action_open_payslips" class="oe_stat_button"
            icon="fa-file-text-o">
      <field name="payslip_count" string="Phieu luong"/>
    </button>
  </div>
  <group>
    <group>
      name, date_start, date_end
    </group>
  </group>
  <notebook>
    <page string="Phieu luong" name="payslips">
      slip_ids -> inline list (editable="bottom"):
        number, employee_id, structure_id,
        gross_amount (monetary), net_amount (monetary), state (badge)
    </page>
  </notebook>
</sheet>
<chatter/>
```

**Header Buttons:**

| Button Label | Type | Method / Action | Visibility | Class |
| --- | --- | --- | --- | --- |
| Xac nhan | `object` | `action_verify` | `state == 'draft'` | -- |
| Dong batch | `object` | `action_close` | `state == 'verify'` | `btn-success` |
| Reset Nhap | `object` | `action_reset_draft` | `state != 'draft'` | -- |
| Tao file Ngan hang | `object` | `action_open_bank_file_wizard` | `state == 'close'` | `btn-warning` |

### Screen 3: Payslip List (`hb_payslip_tree`)

**View type:** List
**XML ID:** `hocba_payroll.hb_payslip_tree`
**Model:** `hb.payslip`

| Column | Field | Widget | Decoration | Notes |
| --- | --- | --- | --- | --- |
| Ma phieu | `number` | (default Char) | -- | Auto-generated |
| Nhan vien | `employee_id` | (default Many2one) | -- | |
| Cau truc | `structure_id` | (default Many2one) | -- | |
| Tu ngay | `date_from` | (default Date) | -- | |
| Den ngay | `date_to` | (default Date) | -- | |
| Tong thu nhap | `gross_amount` | monetary | -- | |
| Thuc linh | `net_amount` | monetary | -- | |
| Trang thai | `state` | badge | `decoration-info`=draft, `decoration-warning`=verify, `decoration-success`=done | |

**Search View Filters:** employee_id, number, structure_id. Groupby: employee_id, payslip_run_id, structure_id. Filters: draft, done states.

### Screen 4: Payslip Form (`hb_payslip_form`)

**View type:** Form
**XML ID:** `hocba_payroll.hb_payslip_form`
**Model:** `hb.payslip`

**Layout:**

```
<header>
  <button name="action_compute_sheet" string="Tinh luong"
          invisible="state not in ('draft','verify')"/>
  <button name="action_payslip_verify" string="Gui xac nhan"
          invisible="state != 'draft'"/>
  <button name="action_payslip_done" string="Hoan tat"
          invisible="state not in ('draft','verify')" class="btn-success"/>
  <button name="action_payslip_cancel" string="Huy"
          invisible="state not in ('draft','verify')"/>
  <field name="state" widget="statusbar"
         statusbar_visible="draft,verify,done"/>
</header>
<sheet>
  <group>
    <group string="Thong tin">
      employee_id, contract_id, structure_id, payslip_run_id
    </group>
    <group string="Thoi gian">
      date_from, date_to
    </group>
  </group>
  <group string="Ket qua">
    gross_amount (monetary), net_amount (monetary)
  </group>
  <!-- Warning area -->
  <field name="x_compute_warnings"
         invisible="not x_compute_warnings"
         class="alert alert-warning"/>
  <notebook>
    <page string="Chi tiet luong" name="lines">
      line_ids -> inline list (editable="bottom"):
        sequence, code, name, category_id,
        quantity, rate (monetary), amount (monetary)
    </page>
    <page string="Ngay cong" name="worked_days">
      worked_days_ids -> inline list (editable="bottom"):
        sequence, code, name, number_of_days, number_of_hours
    </page>
    <page string="Dau vao" name="inputs">
      input_ids -> inline list (editable="bottom"):
        sequence, code, name, amount
    </page>
  </notebook>
</sheet>
<chatter/>
```

**Header Buttons:**

| Button Label | Type | Method / Action | Visibility | Class |
| --- | --- | --- | --- | --- |
| Tinh luong | `object` | `action_compute_sheet` | `state in ('draft','verify')` | -- |
| Gui xac nhan | `object` | `action_payslip_verify` | `state == 'draft'` | -- |
| Hoan tat | `object` | `action_payslip_done` | `state in ('draft','verify')` | `btn-success` |
| Huy | `object` | `action_payslip_cancel` | `state in ('draft','verify')` | -- |

### Screen 5: REST API Endpoints

**Base path:** `/hocba-hrm/api/payroll/`

All endpoints use `type='http'`, `auth='user'`, `csrf=False`. Standard response envelope: `{ "success": true/false, "data": ..., "message": ..., "error": ... }`.

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/batch` | Create batch. Required: `name`, `date_start`, `date_end`. |
| GET | `/batch` | List batches. Query: `limit` (default 50). Ordered by `date_start desc`. |
| GET | `/batch/<id>` | Get batch detail with nested payslip list. |
| POST | `/batch/<id>/generate` | Generate payslips for active employees with open contracts. |
| POST | `/batch/<id>/close` | Close batch and finalize all child payslips. |
| POST | `/batch/close-by-period` | Close all batches for month/year. Required: `{ month, year }`. |
| GET | `/payslip` | List payslips. Filters: `batch_id`, `employee_id`, `state`, `year`, `month`, `limit`. |
| GET | `/payslip/<id>` | Get payslip detail with lines, worked days, inputs. |
| POST | `/payslip/<id>/compute` | Compute payslip salary via `action_compute_sheet()`. |
| POST | `/payslip/<id>/confirm` | Finalize payslip via `action_payslip_done()`. |
| POST | `/payslip/<id>/reset` | Reset to draft. Required body: `{ reason }`. HR Manager only. |
| GET | `/employee-payroll` | Employee payroll summary. Query: `month`, `year`. Dynamic salary rule columns. |

**Payslip API Serialization (`_to_api_dict()`):**

```json
{
  "id": 1,
  "name": "Luong Nguyen Van A -- 06/2026",
  "number": "SLIP/2026/0001",
  "employee_id": 10,
  "employee_name": "Nguyen Van A",
  "contract_id": 5,
  "structure_id": 1,
  "structure_code": "struct_offline",
  "date_from": "2026-06-01",
  "date_to": "2026-06-30",
  "state": "done",
  "teaching_computed": true,
  "compute_warnings": null,
  "gross_amount": 15000000,
  "net_amount": 12500000,
  "employee_confirm": "confirmed",
  "employee_feedback": "",
  "email_sent": true,
  "worked_days": [{"code": "WORK100", "name": "Normal Working Days", "number_of_days": 22, "number_of_hours": 176}],
  "inputs": [{"code": "ADVANCE", "name": "Advance Payment", "amount": 500000}],
  "lines": [{"id": 1, "code": "an_ca", "name": "An ca", "sequence": 10, "quantity": 1, "rate": 0, "amount": 1100000, "category_code": "phu_cap"}]
}
```

### Screen 6: React SPA -- BatchList.jsx (Payroll Dashboard)

**File:** `frontend/src/features/payroll/BatchList.jsx`
**Component:** `BatchList` (default export)
**Used by:** `Payroll.jsx` as the main payroll tab.

**Key State:**
- `data`: `{ month, year, columns, employees }` from `/employee-payroll` endpoint.
- `cfg`: Column configuration (frozen, visible, order) persisted in `localStorage`.
- `colWidths`: Column widths persisted in `localStorage`.
- `checked`: `{ [payslip_id]: bool }` for bulk mail selection.

**Toolbar Buttons:**

| Button | Label | Color | Condition | Action |
| --- | --- | --- | --- | --- |
| Send Mail | "Gui mail (N)" | Blue `#2563eb` | `checkedCount > 0` | `sendPayslipMail(checkedIds)` |
| Save History | "Luu lich su" | Green `#16a34a` when enabled, gray `#9ca3af` when disabled | All employees have `employee_confirm === 'confirmed'` | `closeBatchByPeriod(month, year)` |

**Table Structure:**
- Fixed columns: STT, Code, Name (employee), Job Title, Department.
- Variable columns: Dynamic salary rule columns from API.
- Final column: "NV xac nhan" -- confirmation status badge (see FS-PAY-005).
- Sticky header and footer row for column totals.
- Checkbox column for bulk mail selection.

**Additional Features:**
- Column configuration modal (`CfgModal`): freeze columns, show/hide, drag-to-reorder.
- Column resize via mouse drag on header dividers.
- Local search by name, code, department, job_title (case-insensitive substring).
- Salary detail modal (`SalaryDetail`): opens on employee name click, receipt-style layout with net amount highlight.
- Metrics display: employee count, payslip count, total net, average net.
- Row background tinting by confirmation status: confirmed `#f0fdf4`, rejected `#fef2f2`, pending white.

### Screen 7: React SPA -- BatchDrawer.jsx (Batch Detail)

**File:** `frontend/src/features/payroll/BatchDrawer.jsx`
**Component:** `BatchDrawer` (default export)

**Actions by Batch State:**

| Action | Label | Condition | API Call |
| --- | --- | --- | --- |
| Generate | "Tao phieu luong" | Draft, no payslips | `generatePayslips(batch.id)` |
| Compute All | "Tinh luong tat ca" | Draft, has draft payslips | Sequential `computePayslip()` per payslip with progress |
| Close | "Dong batch" | Draft/computed, has payslips | `closeBatch(batch.id)` |

**Payslip Table Columns:** Ma phieu, Nhan vien, Gross, Net, Trang thai. Click row to open `PayslipDrawer`.

### Screen 8: React SPA -- PayslipDrawer.jsx (Payslip Detail)

**File:** `frontend/src/features/payroll/PayslipDrawer.jsx`
**Component:** `PayslipDrawer` (default export)

**Tabs:**

| Tab | Label | Content |
| --- | --- | --- |
| 1 | Chi tiet luong | Salary lines grouped by category. Highlights: `tong_thu_nhap` and `thuc_lanh` in red. Negative amounts in red. Muted `bh_phan_cong_ty` at 55% opacity. |
| 2 | Ngay cong | Worked days: Code, Name, Days, Hours. |
| 3 | Dau vao | Inputs: Code, Name, Amount. |

**Action Buttons by State:**

| Button | Label | State | Notes |
| --- | --- | --- | --- |
| Compute | "Tinh luong" | `draft` | Calls `computePayslip(slip.id)` |
| Confirm | "Xac nhan" | `draft` with lines | Calls `confirmPayslip(slip.id)` |
| Reset | "Reset ve nhap" | `done` | Shows reason input, calls `resetPayslip(slip.id, reason)` |

---

## 4. FIELD SPECIFICATION

### 4.1 Model: `hb.payslip.run`

**Python class:** `HbPayslipRun`
**`_name`:** `hb.payslip.run`
**`_description`:** `Payslip Batch`
**`_order`:** `date_start desc, id desc`
**`_inherit`:** `['mail.thread']`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | -- | Ten | Batch name (e.g., "Luong T06/2026"). |
| 2 | `date_start` | `Date` | Yes | No | -- | -- | Tu ngay | Period start date. |
| 3 | `date_end` | `Date` | Yes | No | -- | -- | Den ngay | Period end date. |
| 4 | `state` | `Selection` | No | No | `'draft'` | Options: `('draft','Nhap')`, `('verify','Xac nhan')`, `('close','Dong')` | Trang thai | Batch lifecycle state. |
| 5 | `slip_ids` | `One2many` | No | No | -- | Comodel: `hb.payslip`, inverse: `payslip_run_id` | Phieu luong | All child payslips in this batch. |
| 6 | `payslip_count` | `Integer` | No | No | -- | Computed by `_compute_payslip_count`, depends on `slip_ids` | So phieu luong | Count of payslips in batch. Read-only. |

**Key Methods:**

| Method | Signature | Description |
| --- | --- | --- |
| `action_verify` | `action_verify(self)` | Validates `state == 'draft'`, transitions to `verify`. Raises `UserError` on invalid state. |
| `action_close` | `action_close(self)` | Iterates `slip_ids` in `draft`/`verify`, calls `action_payslip_done()` on each. Transitions batch to `close`. Posts chatter message. |
| `action_reset_draft` | `action_reset_draft(self)` | Transitions batch back to `draft`. |
| `action_open_payslips` | `action_open_payslips(self)` | Returns `ir.actions.act_window` to list child payslips. |
| `action_open_bank_file_wizard` | `action_open_bank_file_wizard(self)` | Opens `hb.bank.file.wizard` with `payslip_batch_id` context. |

### 4.2 Model: `hb.payslip`

**Python class:** `HbPayslip`
**`_name`:** `hb.payslip`
**`_description`:** `Payslip`
**`_order`:** `number desc, id desc`
**`_inherit`:** `['mail.thread']`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | No | No | -- | Computed: `_compute_name`, depends on `employee_id`, `date_from`, `date_to` | Ten | Auto-computed: "Luong {emp_name} -- {month/year}". |
| 2 | `number` | `Char` | No | No | `'Moi'` | Auto-generated via sequence `hb.payslip` on create | Ma phieu | Payslip reference number. |
| 3 | `employee_id` | `Many2one` | Yes | Yes | -- | Comodel: `hr.employee` | Nhan vien | The employee. |
| 4 | `contract_id` | `Many2one` | No | No | -- | Comodel: `hb.contract` | Hop dong | Resolved during computation (see `_resolve_contract`). |
| 5 | `structure_id` | `Many2one` | No | No | -- | Comodel: `hb.salary.structure` | Cau truc luong | Set during computation (see `_resolve_structure`). |
| 6 | `payslip_run_id` | `Many2one` | No | Yes | -- | Comodel: `hb.payslip.run`, `ondelete='cascade'` | Ky luong | Parent batch. Cascade-deletes payslip with batch. |
| 7 | `date_from` | `Date` | Yes | No | -- | -- | Tu ngay | Period start. |
| 8 | `date_to` | `Date` | Yes | No | -- | -- | Den ngay | Period end. |
| 9 | `state` | `Selection` | No | No | `'draft'` | Options: `('draft','Nhap')`, `('verify','Cho duyet')`, `('done','Hoan tat')`, `('cancel','Huy')` | Trang thai | Payslip lifecycle state. |
| 10 | `company_id` | `Many2one` | No | No | current company | Comodel: `res.company` | Cong ty | Company reference. |
| 11 | `line_ids` | `One2many` | No | No | -- | Comodel: `hb.payslip.line`, inverse: `payslip_id` | Chi tiet luong | Computed salary lines. |
| 12 | `worked_days_ids` | `One2many` | No | No | -- | Comodel: `hb.payslip.worked_days`, inverse: `payslip_id` | Ngay cong | Work-entry data. |
| 13 | `input_ids` | `One2many` | No | No | -- | Comodel: `hb.payslip.input`, inverse: `payslip_id` | Dau vao | Ad-hoc monetary inputs. |
| 14 | `gross_amount` | `Float` | No | No | -- | `digits=(16,0)`, computed/stored: reads `tong_thu_nhap` line | Tong thu nhap | Stored compute from line code `tong_thu_nhap`. |
| 15 | `net_amount` | `Float` | No | No | -- | `digits=(16,0)`, computed/stored: reads `thuc_lanh` line | Thuc linh | Stored compute from line code `thuc_lanh`. |
| 16 | `x_teaching_computed` | `Boolean` | No | No | `False` | -- | Da tinh luong | Set to `True` after successful `action_compute_sheet()`. Required before `action_payslip_done()`. |
| 17 | `x_compute_warnings` | `Text` | No | No | -- | -- | Canh bao tinh luong | Newline-joined warning messages from rule evaluation errors. |
| 18 | `x_access_token` | `Char` | No | Yes | `str(uuid.uuid4())` | `copy=False`. Generated on `create()`. | Token truy cap | Unique public access token for employee confirmation page (see FS-PAY-005). |
| 19 | `x_employee_confirm` | `Selection` | No | No | `'pending'` | Options: `('pending','Cho xac nhan')`, `('confirmed','Da xac nhan')`, `('rejected','Tu choi')`. `tracking=True` | NV xac nhan | Employee confirmation status (see FS-PAY-005). |
| 20 | `x_employee_feedback` | `Text` | No | No | -- | -- | Phan hoi NV | Employee rejection reason (see FS-PAY-005). |
| 21 | `x_email_sent` | `Boolean` | No | No | `False` | -- | Da gui email | Set `True` after `action_send_payslip_mail()` (see FS-PAY-005). |
| 22 | `x_email_sent_date` | `Datetime` | No | No | -- | -- | Ngay gui email | Timestamp of last email dispatch. |
| 23 | `x_confirmed_date` | `Datetime` | No | No | -- | -- | Ngay xac nhan | Timestamp when employee confirmed or rejected. |

**Key Methods:**

| Method | Signature | Description |
| --- | --- | --- |
| `create` | `create(self, vals_list)` | Overrides to auto-generate `number` from sequence `hb.payslip` if default, and `x_access_token` from `uuid.uuid4()`. |
| `_compute_name` | `_compute_name(self)` | Depends on `employee_id`, `date_from`, `date_to`. Format: "Luong {emp_name} -- {month/year}". |
| `_compute_amounts` | `_compute_amounts(self)` | Depends on `line_ids`. Reads `tong_thu_nhap` line -> `gross_amount`, `thuc_lanh` line -> `net_amount`. |
| `action_compute_sheet` | `action_compute_sheet(self)` | Main computation entry point. See FS-PAY-002 for engine details. |
| `action_payslip_verify` | `action_payslip_verify(self)` | Requires `state == 'draft'`. Transitions to `verify`. |
| `action_payslip_done` | `action_payslip_done(self)` | Requires `state in ('draft','verify')` AND `x_teaching_computed == True`. Transitions to `done`. |
| `action_payslip_cancel` | `action_payslip_cancel(self)` | Transitions to `cancel` from `draft` or `verify`. |
| `action_reset_to_draft` | `action_reset_to_draft(self, reason)` | Requires `state == 'done'`, `hr.group_hr_manager`, non-empty `reason`. Transitions to `draft`. |
| `_to_api_dict` | `_to_api_dict(self)` | Serializes payslip for REST API response (see Screen 5). |

### 4.3 Model: `hb.payslip.line`

**Python class:** `HbPayslipLine`
**`_name`:** `hb.payslip.line`
**`_description`:** `Payslip Line`
**`_order`:** `sequence, id`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `payslip_id` | `Many2one` | Yes | Yes | -- | Comodel: `hb.payslip`, `ondelete='cascade'` | Phieu luong | Parent payslip. Cascade-deletes with payslip. |
| 2 | `rule_id` | `Many2one` | No | No | -- | Comodel: `hb.salary.rule`, `ondelete='set null'` | Quy tac | Source salary rule. |
| 3 | `category_id` | `Many2one` | No | No | -- | Comodel: `hb.salary.rule.category`, `ondelete='set null'` | Danh muc | Category from source rule. |
| 4 | `code` | `Char` | Yes | Yes | -- | -- | Ma | Rule code copied at creation. |
| 5 | `name` | `Char` | Yes | No | -- | -- | Ten | Rule name copied at creation. |
| 6 | `sequence` | `Integer` | No | No | `10` | -- | Thu tu | Display order copied from rule. |
| 7 | `quantity` | `Float` | No | No | `1.0` | `digits=(10,2)` | So luong | Quantity from rule evaluation. |
| 8 | `rate` | `Float` | No | No | -- | `digits=(16,0)` | Don gia | Rate from rule evaluation. |
| 9 | `amount` | `Float` | No | No | -- | `digits=(16,0)` | So tien | `round(amount)` -- primary computed monetary value. Always integer (no decimals). |

### 4.4 Model: `hb.payslip.worked_days`

**Python class:** `HbPayslipWorkedDays`
**`_name`:** `hb.payslip.worked_days`
**`_description`:** `Payslip Worked Days`
**`_order`:** `sequence, id`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `payslip_id` | `Many2one` | Yes | No | -- | Comodel: `hb.payslip`, `ondelete='cascade'` | Phieu luong | Parent payslip. |
| 2 | `name` | `Char` | Yes | No | -- | -- | Mo ta | Descriptive label (e.g., "Normal Working Days"). |
| 3 | `code` | `Char` | Yes | No | -- | -- | Ma | Lookup code (e.g., `WORK100`). |
| 4 | `sequence` | `Integer` | No | No | `10` | -- | Thu tu | Display order. |
| 5 | `number_of_days` | `Float` | No | No | -- | `digits=(8,2)` | So ngay | Number of worked days. |
| 6 | `number_of_hours` | `Float` | No | No | -- | `digits=(8,2)` | So gio | Number of worked hours. |

### 4.5 Model: `hb.payslip.input`

**Python class:** `HbPayslipInput`
**`_name`:** `hb.payslip.input`
**`_description`:** `Payslip Input`
**`_order`:** `sequence, id`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `payslip_id` | `Many2one` | Yes | No | -- | Comodel: `hb.payslip`, `ondelete='cascade'` | Phieu luong | Parent payslip. |
| 2 | `name` | `Char` | Yes | No | -- | -- | Mo ta | Descriptive label (e.g., "Advance Payment"). |
| 3 | `code` | `Char` | Yes | No | -- | -- | Ma | Lookup code (e.g., `ADVANCE`, `XANG_XE`). |
| 4 | `sequence` | `Integer` | No | No | `10` | -- | Thu tu | Display order. |
| 5 | `amount` | `Float` | No | No | -- | `digits=(16,0)` | So tien | Monetary value of the input. |

---

## 5. BUSINESS RULES

### BR-PAY-040: Payslip Number Auto-Generation

**Rule:** Payslip `number` is auto-generated by the Odoo sequence `hb.payslip` when the value is the default `Moi`.
**Implementation:** In `create()` override, if `vals.get('number')` equals `'Moi'` or is falsy, calls `self.env['ir.sequence'].next_by_code('hb.payslip')`.

### BR-PAY-041: Payslip Verify Requires Draft State

**Rule:** `action_payslip_verify()` only accepts payslips in `state == 'draft'`.
**Implementation:** Raises `UserError("Phieu luong phai o trang thai Nhap de gui xac nhan.")` if precondition fails.

### BR-PAY-042: Payslip Done Requires Draft/Verify and Computed

**Rule:** `action_payslip_done()` requires `state in ('draft', 'verify')` AND `x_teaching_computed == True`.
**Implementation:** Raises `UserError` if state is invalid. Raises `UserError("Phai tinh luong truoc khi hoan tat phieu luong.")` if salary has not been computed.

### BR-PAY-043: Payslip Cancel from Draft/Verify Only

**Rule:** `action_payslip_cancel()` sets state to `cancel` from `draft` or `verify` states only.
**Implementation:** Checks `state in ('draft', 'verify')`. Raises `UserError` otherwise.

### BR-PAY-044: Payslip Reset Requires Done State, Manager, and Reason

**Rule:** `action_reset_to_draft(reason)` requires `state == 'done'`, the calling user must belong to `hr.group_hr_manager`, and `reason` must be non-empty.
**Implementation:** Checks all three conditions. Raises `UserError` with appropriate message for each violation.

### BR-PAY-045: Batch Verify Requires Draft State

**Rule:** `hb.payslip.run.action_verify()` only accepts `state == 'draft'`.
**Implementation:** Raises `UserError` if batch is not in draft state.

### BR-PAY-046: Batch Close Finalizes All Child Payslips

**Rule:** `hb.payslip.run.action_close()` iterates all child payslips in `draft` or `verify` state and calls `action_payslip_done()` on each, then transitions the batch to `close`.
**Implementation:** Filters `slip_ids` by `state in ('draft', 'verify')`, calls `slip.action_payslip_done()` per payslip. If any payslip fails finalization (e.g., not computed), the entire operation raises `UserError`.

### BR-PAY-047: Close-by-Period Requires All Employees Confirmed

**Rule:** API `POST /batch/close-by-period` blocks closing if any payslip in the period has `x_employee_confirm != 'confirmed'`.
**Implementation:** Searches all non-cancelled payslips in the month/year. If any are unconfirmed, returns `{ "success": false, "error": "Con X nhan vien chua xac nhan: [names up to 5]..." }` with HTTP 400.

### BR-PAY-048: SPA Save History Button Conditional Enable

**Rule:** FE `BatchList.jsx` disables the "Luu lich su" button unless all employees with payslips in the period have `employee_confirm === 'confirmed'`.
**Implementation:** Computes `allConfirmed` by checking every employee row. Button renders green `#16a34a` when enabled, gray `#9ca3af` when disabled. Title attribute shows reason when disabled.

### BR-PAY-049: Payslip Cascade Delete with Batch

**Rule:** When a batch (`hb.payslip.run`) is deleted, all child payslips are cascade-deleted via `ondelete='cascade'` on the `payslip_run_id` field. Similarly, payslip lines, worked days, and inputs are cascade-deleted with their parent payslip.

---

## 6. STANDARD vs CUSTOM MATRIX

| # | Component | Type | Standard / Custom | Notes |
| --- | --- | --- | --- | --- |
| 1 | `hb.payslip` | Model | Custom (new model) | Standalone payroll payslip. Does not inherit `hr_payroll.payslip`. Inherits `mail.thread`. |
| 2 | `hb.payslip.run` | Model | Custom (new model) | Standalone batch model. Inherits `mail.thread`. |
| 3 | `hb.payslip.line` | Model | Custom (new model) | Computed salary line per rule. |
| 4 | `hb.payslip.worked_days` | Model | Custom (new model) | Work-entry data consumed by rules. |
| 5 | `hb.payslip.input` | Model | Custom (new model) | Ad-hoc monetary inputs consumed by rules. |
| 6 | `hb_payslip_form` / `hb_payslip_tree` | Odoo Views | Custom | Payslip lifecycle UI. |
| 7 | `hb_payslip_run_form` / `hb_payslip_run_tree` | Odoo Views | Custom | Batch lifecycle UI. |
| 8 | `action_hb_payslip` / `action_hb_payslip_run` | Odoo Actions | Custom | Navigation actions. |
| 9 | `/hocba-hrm/api/payroll/batch*` | REST API | Custom | Batch create/list/detail/generate/close/close-by-period. |
| 10 | `/hocba-hrm/api/payroll/payslip*` | REST API | Custom | Payslip list/detail/compute/confirm/reset. |
| 11 | `/hocba-hrm/api/payroll/employee-payroll` | REST API | Custom | FE summary endpoint with dynamic columns. |
| 12 | `BatchList.jsx` | React component | Custom | Payroll period table with employee summary, send mail, save history. |
| 13 | `BatchDrawer.jsx` | React component | Custom | Batch detail with generate/compute-all/close actions. |
| 14 | `BatchForm.jsx` | React component | Custom | Modal form for batch creation. |
| 15 | `PayslipDrawer.jsx` | React component | Custom | Payslip detail with salary lines, worked days, inputs, and action buttons. |
| 16 | `hr.group_hr_manager` | Security Group | Standard Odoo | Used for payslip reset guard. |
| 17 | `hr.group_hr_user` | Security Group | Standard Odoo | Used for read-only access. |
| 18 | `hocba_payroll` module | Module | Custom | Standalone payroll module; depends on `hr`, `mail`, `hocba_employees`. No dependency on `hr_payroll` (Enterprise). |

---

### Appendix A: Security Access Control List

| ACL ID | Model | Group | Read | Write | Create | Delete |
| --- | --- | --- | --- | --- | --- | --- |
| `access_hb_payslip_run_user` | `hb.payslip.run` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_payslip_run_manager` | `hb.payslip.run` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_payslip_user` | `hb.payslip` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_payslip_manager` | `hb.payslip` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_payslip_line_user` | `hb.payslip.line` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_payslip_line_manager` | `hb.payslip.line` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_payslip_worked_days_user` | `hb.payslip.worked_days` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_payslip_worked_days_manager` | `hb.payslip.worked_days` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_payslip_input_user` | `hb.payslip.input` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_payslip_input_manager` | `hb.payslip.input` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |

Note: REST API endpoints use `sudo()` for most operations, bypassing ACL checks. State machine guards and manager-only checks are enforced at the method level.

### Appendix B: Frontend API Functions (`payroll.js`)

| Function | HTTP | Endpoint | Parameters |
| --- | --- | --- | --- |
| `fetchBatches` | GET | `/hocba-hrm/api/payroll/batch` | -- |
| `fetchBatch(id)` | GET | `/hocba-hrm/api/payroll/batch/{id}` | -- |
| `createBatch(payload)` | POST | `/hocba-hrm/api/payroll/batch` | `{ name, date_start, date_end }` |
| `generatePayslips(batchId)` | POST | `/hocba-hrm/api/payroll/batch/{id}/generate` | -- |
| `closeBatch(batchId)` | POST | `/hocba-hrm/api/payroll/batch/{id}/close` | -- |
| `closeBatchByPeriod(month, year)` | POST | `/hocba-hrm/api/payroll/batch/close-by-period` | `{ month, year }` |
| `fetchPayslips(params)` | GET | `/hocba-hrm/api/payroll/payslip` | query params |
| `fetchEmployeePayroll(params)` | GET | `/hocba-hrm/api/payroll/employee-payroll` | `{ month, year }` |
| `fetchPayslip(id)` | GET | `/hocba-hrm/api/payroll/payslip/{id}` | -- |
| `computePayslip(id)` | POST | `/hocba-hrm/api/payroll/payslip/{id}/compute` | -- |
| `confirmPayslip(id)` | POST | `/hocba-hrm/api/payroll/payslip/{id}/confirm` | -- |
| `resetPayslip(id, reason)` | POST | `/hocba-hrm/api/payroll/payslip/{id}/reset` | `{ reason }` |
