# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-005 |
| **Function Name** | Employee Payslip Confirmation & Email |
| **Created Date** | 21/06/2026 |
| **Last Update Date** | 21/06/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP (Community / Enterprise) |
| **Reference** | `hb.payslip` (inherited `mail.thread`), `payroll_public.py`, `payslip_public_templates.xml`, `payroll_api.py`, `BatchList.jsx`, `ConfigView.jsx` -- module `hocba_payroll` |

| **Approver** | **Reviewer** | **Creator** |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

---

## CHANGE HISTORY

| No | Version | Change Description | Affected Sections | Date | Author |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial creation from confirmation/email BE/FE implementation | All | 21/06/2026 | Group G2 |
| 2 | 1.1 | Full rewrite with correct Function ID (FS-PAY-005), FS-PAY-001 format, detailed field specs, public controller routes, QWeb template documentation, email template system, and SPA component details derived from actual source code | All | 21/06/2026 | Group G2 |
| 3 | 1.2 | Standardization of Vietnamese C&B Terminology | All | 06/08/2026 | Group G2 |
| 4 | 1.3 | Updated business logic: HR manual mail issuance (removed auto-send on compute), Confirmation Date Window (Start to Deadline), multi-response allowance during open window, auto-confirmation on deadline expiration, and bank file generation flow | All | 06/08/2026 | Group G2 |
| 5 | 1.4 | Added individual employee payslip recalculation, single-employee email resend & deadline extension, confirmation reset API, and dedicated "Thao tác" action column in SPA `BatchList.jsx` & `PayslipDrawer.jsx` | All | 06/08/2026 | Group G2 |
| 6 | 1.6 | Security Enhancement: Mandatory Odoo user authentication (`auth='user'`) and email account ownership verification. Email links force login and redirect directly to the real SPA app (`http://localhost:8069/hocba-hrm`) with self-service `MyPayslipsView` component | All | 06/08/2026 | Group G2 |
| 7 | 1.7 | Start & End Date Confirmation Window: Added configurable Start Day & End Day parameters. Enforced send-mail window validation (`start_day <= today <= end_day`), auto-confirmation of all pending slips past end date, and mail/recalculate lock past deadline unless extended in Config. | All | 07/08/2026 | Group G2 |
| 8 | 1.8 | Pre-Send Confirmation Dialog: Implemented confirmation dialog listing employees missing work_email before sending mail, allowing HR to confirm sending to valid-email employees while skipping no-email employees. | Frontend SPA | 07/08/2026 | Group G2 |
| 8 | 1.6 | UI/UX Redesign: Overhauled `MyPayslipsView` into a Senior-level categorized layout (Thu nhập, Các khoản trừ, Bảo hiểm công ty đóng tài trợ, Căn cứ tính thuế TNCN). Removed raw truncated code column ("Mã"), added feedback presets & enhanced confirmation action footer. | Frontend SPA | 06/08/2026 | Group G2 |

---

## 1. FUNCTION OVERVIEW

| Item | Detail |
| --- | --- |
| **Function ID** | FS-PAY-005 |
| **Function Name** | Employee Payslip Confirmation & Email |
| **Created Date** | 21/06/2026 |
| **Last Modified Date** | 06/08/2026 |

| Attribute | Value |
| --- | --- |
| **Processing Time** | On-demand |
| **Processing Type** | Interactive + REST API + Authenticated Web SPA |
| **Function Type** | Communication / Workflow / Security |
| **Multilingual** | No |

### Business Requirement & Function Overview

**Overview:**
This function provides the secure employee payslip confirmation workflow, email notification mechanism, and account-level security enforcement. It covers: manual email issuance by HR; a configurable confirmation date window (Start Date to End Date / Deadline); mandatory Odoo user authentication (`auth='user'`) and account ownership verification when accessing email links; direct redirection to the main Học Bá HRM SPA application (`http://localhost:8069/hocba-hrm`) rendering the authenticated `MyPayslipsView` component; multi-response allowance within the open window; automatic silent confirmation (`auto_confirmed`) when deadline expires without response; individual employee exception handling; REST API endpoints; and SPA frontend integration.

**Security Context & Ownership Verification:**
To prevent unauthorized access or token leakage where unauthenticated individuals could view or confirm another person's income statement, all payslip links require user authentication (`auth='user'`). When an employee clicks an email link (`/payslip/view/<token>`):
1. If the user is unauthenticated, Odoo automatically redirects to `/web/login?redirect=/hocba-hrm`.
2. The user must authenticate using the official Odoo user account corresponding to their employee work email.
3. Upon login, the controller verifies account ownership: `slip.employee_id.user_id.id == user.id` or `user.partner_id.email == slip.employee_id.work_email` (or HR Admin).
4. If unauthorized, access is denied with an explicit security alert template (`payslip_unauthorized`).
5. If verified, the user is redirected into the official SPA app (`/hocba-hrm`) rendering `MyPayslipsView` (Image 3) to view their breakdown and submit confirmation or feedback.s.

**Functional Scope:**
- HR manual mail dispatch (disabling `auto_send_mail` on calculation).
- Unique access token (`x_access_token`, UUID v4) generated on email send.
- Confirmation Date Window: Start date (`x_email_sent_date`) to End date/deadline (`x_confirm_deadline`).
- Multi-response allowance: Employees can confirm or submit feedback multiple times while `now <= x_confirm_deadline`.
- Auto-confirmation on deadline expiration (`x_confirm_deadline <= now`) for un-actioned slips.
- Individual Employee Exception Handling:
  - Single-employee payslip recalculation (`POST /hocba-hrm/api/payroll/payslip/<id>/compute`).
  - Single-employee email resend & deadline extension (`POST /hocba-hrm/api/payroll/payslip/send-mail`).
  - Single-employee confirmation reset (`POST /hocba-hrm/api/payroll/payslip/<id>/reset-confirm`).
- Public web controller (`PayrollPublicController`) with token-based view and confirmation window banners.
- SPA integration: "Thao tác" action column in `BatchList.jsx` table (🧮 Compute, ✉️ Resend Mail, 🔄 Reset Confirm) and action bar in `PayslipDrawer.jsx`.
- Close-by-period & Bank File creation integration.

**Users:**
- **HR Manager** (`hr.group_hr_manager`): Sends payslip emails, views confirmation status, configures email templates, closes payroll periods.
- **HR User** (`hr.group_hr_user`): Views confirmation status (read-only).
- **Employee** (public, no login): Receives email, views payslip, confirms or rejects via public link.

---

## 2. FUNCTION FLOW

### Main Flow 1 -- Send Payslip Emails

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In `BatchList.jsx`, selects payslips via checkboxes and clicks "Gui mail (N)" | FE calls `POST /payslip/send-mail` with `{ payslip_ids: [id1, id2, ...] }`. |
| 2 | Backend | Iterates each payslip | For each: reads employee `work_email` (falling back to `email`). If no email, adds to `skipped` list with reason "Khong co email". |
| 3 | Backend | For each payslip with email | Calls `action_send_payslip_mail()`: reads email templates from `ir.config_parameter`, builds template variables (`employee_name`, `month`, `year`, `gross`, `net`, `view_url`), renders subject and body via `_render_mail_tpl()`, creates `mail.mail` record with `auto_delete=True`, sends mail. |
| 4 | Backend | Token generation | If `x_access_token` is empty at send time, generates a new UUID and saves it. Constructs public URL: `{web.base.url}/payslip/view/{x_access_token}`. |
| 5 | Backend | Post-send | Writes `x_email_sent=True` and `x_email_sent_date=Datetime.now()` on the payslip. |
| 6 | Backend | Returns summary | `{ sent: N, skipped: [{employee_name, reason}, ...] }`. FE shows alert with counts. |

**REST API:**
- `POST /hocba-hrm/api/payroll/payslip/send-mail` -- Required: `{ payslip_ids }`. Returns `{ sent, skipped }`.

### Main Flow 2 -- Employee Views Payslip (Public)

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | Employee | Clicks link in email: `/payslip/view/{token}` | Public controller `view_payslip(token)` searches `hb.payslip` by `x_access_token` with `sudo()`. |
| 2 | System | Token valid | Renders `hocba_payroll.payslip_public_view` QWeb template with: `slip`, `employee`, `lines` (sorted by sequence), `month`, `year`, `gross`, `net`, `token`. |
| 3 | System | Token invalid or not found | Renders `hocba_payroll.payslip_public_not_found` (404-style page). |
| 4 | Employee | Views payslip details | Page shows: header with month/year and employee name, info bar with ID/department/status badge, salary lines table, net total bar, and action buttons (if `pending`). |

### Main Flow 3 -- Employee Confirms Payslip

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | Employee | On the public payslip page (status `pending`), clicks "Xac nhan" button | Form POSTs to `/payslip/view/{token}/confirm`. |
| 2 | System | Validates token and state | Checks `x_employee_confirm == 'pending'`. If already actioned, redirects with `?msg=already_actioned`. |
| 3 | System | Updates payslip | Writes `x_employee_confirm='confirmed'` and `x_confirmed_date=Datetime.now()`. |
| 4 | System | Redirects | `?msg=confirmed`. Page reloads showing green success message and confirmed status badge. |

### Main Flow 4 -- Employee Rejects Payslip

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | Employee | On the public payslip page (status `pending`), clicks "Tu choi" button | JavaScript toggles the rejection feedback form visible. |
| 2 | Employee | Enters rejection reason in textarea and clicks "Gui phan hoi" | Form POSTs to `/payslip/view/{token}/reject` with `feedback` parameter. |
| 3 | System | Validates feedback | If `feedback` is empty or whitespace-only, redirects with `?msg=feedback_required`. |
| 4 | System | Validates token and state | Checks `x_employee_confirm == 'pending'`. If already actioned, redirects with `?msg=already_actioned`. |
| 5 | System | Updates payslip | Writes `x_employee_confirm='rejected'`, `x_employee_feedback=feedback`, `x_confirmed_date=Datetime.now()`. |
| 6 | System | Redirects | `?msg=rejected`. Page reloads showing red status with the stored feedback text. |

### Main Flow 5 -- Email Template Configuration

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In `ConfigView.jsx`, selects the "Mau email" tab | FE calls `GET /mail-template`. Loads current subject and body from `ir.config_parameter`. Falls back to defaults if not configured. |
| 2 | HR Manager | Edits subject and/or body text, optionally clicks "Xem truoc" | Preview modal substitutes placeholders with sample values: `employee_name="Nguyen Van A"`, `month="06"`, `year="2026"`, `gross="15,000,000"`, `net="12,500,000"`, `view_url="#"`. |
| 3 | HR Manager | Clicks "Luu mau email" | FE calls `POST /mail-template` with `{ subject, body }`. Backend saves to `ir.config_parameter`. |

**REST API:**
- `GET /hocba-hrm/api/payroll/mail-template` -- Returns `{ subject, body }`.
- `POST /hocba-hrm/api/payroll/mail-template` -- Saves `{ subject?, body? }` to `ir.config_parameter`.

### Main Flow 6 -- Close-by-Period Guard

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | In `BatchList.jsx`, clicks "Luu lich su" | FE first checks that all employees have `employee_confirm === 'confirmed'`. Button is disabled (gray) if any are not confirmed. |
| 2 | HR Manager | Confirms browser dialog | FE calls `POST /batch/close-by-period` with `{ month, year }`. |
| 3 | Backend | Validates | Searches all non-cancelled payslips in month/year. If any have `x_employee_confirm != 'confirmed'`, returns error with up to 5 names. |
| 4 | Backend | If all confirmed | Closes all related batches. Returns `{ closed_batches, payslip_count }`. |

**REST API:**
- `POST /hocba-hrm/api/payroll/batch/close-by-period` -- See FS-PAY-003.

### Error/Exception Flow

| Error Scenario | System Behavior |
| --- | --- |
| Invalid/non-existent token | Public controller returns 404 page: "Phieu luong khong ton tai hoac duong link da het han." |
| Confirm already actioned payslip | Redirects with `?msg=already_actioned`. Yellow warning: "Phieu luong nay da duoc xu ly truoc do." |
| Reject without feedback | Redirects with `?msg=feedback_required`. Red error: "Vui long nhap ly do tu choi." |
| Send mail -- no employee email | Skipped with reason "Khong co email" |
| Send mail -- mail send error | Skipped with exception message as reason |
| Missing `payslip_ids` in send-mail | 400 error |
| Empty `payslip_ids` array | 404 error: no valid payslips |
| Close period with unconfirmed employees | 400 error listing up to 5 names |
| Template render error (bad placeholder) | `_render_mail_tpl()` catches `KeyError`/`IndexError`/`ValueError` and returns raw template unchanged |

---

## 3. SCREEN LAYOUT

### Screen 1: Public Payslip View (`payslip_public_view`)

**Template ID:** `hocba_payroll.payslip_public_view`
**Type:** QWeb HTML template (standalone, no Odoo chrome)
**Route:** `GET /payslip/view/<string:token>` with `auth='public'`
**Responsive:** Yes (mobile-optimized via media query at 480px)

| Section | Description |
| --- | --- |
| **Flash messages** | Rendered at top based on `request.params.get('msg')`: `confirmed` -> green `.msg-ok` with checkmark, `rejected` -> red `.msg-err`, `already_actioned` -> yellow `.msg-warn`, `feedback_required` -> red `.msg-err`. |
| **Header** | Blue gradient (`.header`, `linear-gradient(135deg, #1e40af, #2563eb)`). Displays "Phieu luong thang {month}/{year}", employee name, and job title. |
| **Info bar** | Flex row with employee ID/barcode, department name, and confirmation status badge: `badge-pending` (yellow `#fef3c7`), `badge-confirmed` (green `#d1fae5`), `badge-rejected` (red `#fee2e2`). |
| **Salary lines** | Each `hb.payslip.line` rendered as `.line` div with label and formatted amount (`{:,.0f}` VND). Lines with `thuc_lanh` in code receive `.line-net` (green background `#ecfdf5`). |
| **Total bar** | Green gradient bar (`.total-bar`, `linear-gradient(135deg, #065f46, #047857)`) showing "Thuc linh" label and net amount in white bold text. |
| **Actions (pending)** | Visible only when `x_employee_confirm == 'pending'`. Contains: confirm form (POST to `/payslip/view/{token}/confirm`, green button), reject button (toggles form), hidden reject form with textarea + red submit button. |
| **Actions (confirmed)** | Green `.msg-ok` div: "Ban da xac nhan phieu luong thanh cong. Cam on!" |
| **Actions (rejected)** | Red `.msg-err` div displaying stored `x_employee_feedback`. |
| **Footer** | "Hoc Ba Education -- He thong quan ly luong". |

### Screen 2: Public Not Found Page (`payslip_public_not_found`)

**Template ID:** `hocba_payroll.payslip_public_not_found`
**Type:** QWeb HTML template (standalone, no Odoo chrome)

| Section | Description |
| --- | --- |
| 404 page | Centered white card with large "404" heading and message: "Phieu luong khong ton tai hoac duong link da het han." |

### Screen 3: REST API Endpoints

**Base path:** `/hocba-hrm/api/payroll/`

All endpoints use `type='http'`, `auth='user'`, `csrf=False`.

| Method | Endpoint | Description | Request Body | Response (`data`) |
| --- | --- | --- | --- | --- |
| POST | `/payslip/send-mail` | Send payslip emails | `{ payslip_ids: [int, ...] }` | `{ sent: int, skipped: [{employee_name, reason}] }` |
| GET | `/mail-template` | Get email template | -- | `{ subject, body }` |
| POST | `/mail-template` | Save email template | `{ subject?, body? }` | `{ saved: true }` |

**Public Controller Endpoints (no auth):**

| Method | Route | Auth | CSRF | Description |
| --- | --- | --- | --- | --- |
| GET | `/payslip/view/<token>` | `public` | False | View payslip page. Renders QWeb template. |
| POST | `/payslip/view/<token>/confirm` | `public` | False | Confirm payslip. Redirects with flash message. |
| POST | `/payslip/view/<token>/reject` | `public` | False | Reject payslip. Requires `feedback` POST parameter. Redirects with flash message. |

### Screen 4: React SPA -- BatchList.jsx (Confirmation UI)

**File:** `frontend/src/features/payroll/BatchList.jsx`

**Confirmation-Related Elements:**

| Element | Description |
| --- | --- |
| **Checkbox column** | Leftmost sticky column (40px). Header checkbox toggles all employees with a `payslip_id`. Per-row checkbox for individual selection. |
| **"Gui mail" button** | Blue (`#2563eb`) with mail icon. Shows `"Gui mail (N)"` where N = checked count. Disabled when `checkedCount === 0` or `sending === true`. Calls `sendPayslipMail(checkedIds)`. Shows alert with sent/skipped counts. |
| **"Luu lich su" button** | Green (`#16a34a`) when `allConfirmed`, gray (`#9ca3af`) otherwise. Disabled unless every employee has `employee_confirm === 'confirmed'`. Title: "Tat ca nhan vien phai xac nhan truoc khi luu". Calls `closeBatchByPeriod(month, year)`. |
| **"NV xac nhan" column** | Rightmost column (100px). Colored badge per `CONFIRM_MAP`: `pending` -> "Cho" (yellow `#fef3c7`/`#92400e`), `confirmed` -> "Da XN" (green `#d1fae5`/`#065f46`), `rejected` -> "Tu choi" (red `#fee2e2`/`#991b1b`). Envelope icon (&#x2709;) appended if `email_sent`. Badge title shows `employee_feedback`. |
| **Row background** | Tinted by confirmation: `confirmed` -> `#f0fdf4`, `rejected` -> `#fef2f2`, `pending` -> `#fff`. Hover: `#dcfce7`, `#fee2e2`, `#f8fafc` respectively. |

### Screen 5: React SPA -- ConfigView.jsx (Email Template Editor)

**File:** `frontend/src/features/payroll/ConfigView.jsx`
**Sub-tab:** "Mau email" (third segmented tab, after "Quy tac luong" and "Ngan hang")

| Element | Description |
| --- | --- |
| **Placeholder guide** | Blue info box (`#eff6ff` bg, `#bfdbfe` border) listing variables: `{employee_name}` (Ten nhan vien), `{month}` (Thang), `{year}` (Nam), `{gross}` (Tong thu nhap), `{net}` (Thuc linh), `{view_url}` (Link xem phieu luong). |
| **Subject input** | Text input for email subject. Placeholder: `"Bang luong thang {month}/{year} -- {employee_name}"`. |
| **Body textarea** | Monospace `<textarea>` (14 rows) for HTML email body. Placeholder: `"<div>Noi dung email HTML...</div>"`. |
| **"Xem truoc" button** | Opens modal with `lg` flag. Substitutes placeholders with sample values. Subject in gray info bar; body rendered via `dangerouslySetInnerHTML`. |
| **"Luu mau email" button** | Primary button. Calls `saveMailTemplate({ subject, body })`. Disabled while `mailSaving`. Shows success/error message inline. |

---

## 4. FIELD SPECIFICATION

### 4.1 Model: `hb.payslip` -- Employee Confirmation Fields

These fields are defined on the existing `hb.payslip` model (`_name = 'hb.payslip'`, `_inherit = ['mail.thread']`). See FS-PAY-003 for the full payslip model specification.

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `x_access_token` | `Char` | No | Yes | `str(uuid.uuid4())` | `copy=False`. Auto-generated on `create()`. | Token truy cap | Unique UUID v4 public access token. Used in public URL path. Indexed for fast lookup. |
| 2 | `x_employee_confirm` | `Selection` | No | No | `'pending'` | Options: `('pending','Cho xac nhan')`, `('confirmed','Da xac nhan')`, `('rejected','Tu choi')`. `tracking=True` | NV xac nhan | Employee confirmation status. Irreversible once set to `confirmed` or `rejected`. |
| 3 | `x_employee_feedback` | `Text` | No | No | -- | -- | Phan hoi NV | Free-text rejection reason from employee. Stored when employee rejects via public page. |
| 4 | `x_email_sent` | `Boolean` | No | No | `False` | -- | Da gui email | Set `True` after `action_send_payslip_mail()` succeeds. |
| 5 | `x_email_sent_date` | `Datetime` | No | No | -- | -- | Ngay gui email | Timestamp of last email dispatch. Set to `Datetime.now()` after successful send. |
| 6 | `x_confirmed_date` | `Datetime` | No | No | -- | -- | Ngay xac nhan | Timestamp when employee confirmed or rejected via public page. |

### 4.2 `ir.config_parameter` Keys

| Key | Default Value | Description |
| --- | --- | --- |
| `hocba_payroll.mail_subject` | `Bang luong thang {month}/{year} -- {employee_name}` | Email subject template. Supports `{employee_name}`, `{month}`, `{year}` placeholders. |
| `hocba_payroll.mail_body` | Styled HTML (see default below) | Email body HTML template. Supports all 6 placeholders. |

**Default Email Body (`_default_mail_body()`):**

```html
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <h2 style="color:#1f2937;">Bang luong thang {month}/{year}</h2>
  <p>Xin chao <strong>{employee_name}</strong>,</p>
  <p>Phieu luong thang {month}/{year} cua ban da san sang.</p>
  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    <tr style="background:#f3f4f6;">
      <td style="padding:8px 12px;font-weight:600;">Tong thu nhap</td>
      <td style="padding:8px 12px;text-align:right;">{gross} dong</td>
    </tr>
    <tr style="background:#ecfdf5;">
      <td style="padding:8px 12px;font-weight:600;color:#065f46;">Thuc linh</td>
      <td style="padding:8px 12px;text-align:right;font-weight:700;color:#065f46;">{net} dong</td>
    </tr>
  </table>
  <p>Vui long nhan nut ben duoi de xem chi tiet va xac nhan:</p>
  <a href="{view_url}" style="display:inline-block;padding:12px 24px;
     background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;
     font-weight:600;">Xem phieu luong</a>
  <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;"/>
  <p style="font-size:12px;color:#9ca3af;">Email nay duoc gui tu dong.
     Vui long khong reply.</p>
</div>
```

### 4.3 Methods on `hb.payslip`

| Method | Decorator | Signature | Description |
| --- | --- | --- | --- |
| `action_send_payslip_mail` | -- | `action_send_payslip_mail(self)` | Iterates `self`. For each payslip: reads `ir.config_parameter` for subject/body templates (falling back to `_MAIL_TPL_DEFAULTS`), ensures `x_access_token` exists, builds `tpl_vars` dict with `{employee_name, month, year, gross, net, view_url}`, renders templates via `_render_mail_tpl()`, creates `mail.mail` record (with `auto_delete=True`), sends mail, writes `x_email_sent=True` and `x_email_sent_date=now`. |
| `_render_mail_tpl` | `@staticmethod` | `_render_mail_tpl(tpl, variables)` | Calls `tpl.format(**variables)`. Catches `KeyError`, `IndexError`, `ValueError` and returns raw `tpl` unchanged on error. |
| `_default_mail_body` | `@staticmethod` | `_default_mail_body()` | Returns the styled HTML string shown in section 4.2. |

### 4.4 Public Controller: `PayrollPublicController`

**File:** `controllers/payroll_public.py`
**Class:** `PayrollPublicController(http.Controller)`

| Method | Route | HTTP | Auth | CSRF | Description |
| --- | --- | --- | --- | --- | --- |
| `_get_payslip_by_token(token)` | (helper) | -- | -- | -- | Searches `hb.payslip` with `sudo()` by `x_access_token == token`, limit 1. Returns record or `None`. |
| `view_payslip(token)` | `/payslip/view/<string:token>` | GET | `public` | False | If not found: renders `payslip_public_not_found`. Otherwise: renders `payslip_public_view` with context `{slip, employee, lines, month, year, gross, net, token}`. |
| `confirm_payslip_public(token)` | `/payslip/view/<string:token>/confirm` | POST | `public` | False | Checks `pending` state. Writes `confirmed` + `x_confirmed_date`. Redirects with `?msg=confirmed`. Returns 404 Response if token not found. |
| `reject_payslip_public(token)` | `/payslip/view/<string:token>/reject` | POST | `public` | False | Checks `pending` state. Validates non-empty `feedback`. Writes `rejected` + `x_employee_feedback` + `x_confirmed_date`. Redirects with `?msg=rejected`. |

---

## 5. BUSINESS RULES

### BR-PAY-060: Access Token Generation on Create

**Rule:** Each payslip receives a unique `x_access_token` (UUID v4) on creation.
**Implementation:** The `create()` method generates the token via `str(uuid.uuid4())` if not already supplied. The field has `copy=False` (not copied on duplication) and `index=True` (database index for fast lookup).

### BR-PAY-061: Irreversible Confirmation State

**Rule:** `x_employee_confirm` defaults to `pending`. Valid transitions are: `pending -> confirmed` and `pending -> rejected`. Once set, the value is final.
**Implementation:** Public controller checks `slip.x_employee_confirm == 'pending'` before any update. If already actioned, redirects with `?msg=already_actioned` without modifying the record.

### BR-PAY-062: Rejection Requires Feedback

**Rule:** Rejection requires non-empty feedback text.
**Implementation:** Public controller reads `feedback` POST parameter, strips whitespace. If empty, redirects with `?msg=feedback_required` without updating the payslip. The feedback is stored in `x_employee_feedback`.

### BR-PAY-063: Email Skip for Missing Address

**Rule:** `action_send_payslip_mail()` reads `work_email` (falling back to `email`) for each employee. If no email address is found, the payslip is silently skipped.
**Implementation:** REST API collects skipped payslips in a list with `employee_name` and `reason: "Khong co email"`.

### BR-PAY-064: Configurable Email Templates

**Rule:** Email subject and body templates are stored in `ir.config_parameter` under keys `hocba_payroll.mail_subject` and `hocba_payroll.mail_body`.
**Implementation:** If no custom value exists, the method falls back to `_MAIL_TPL_DEFAULTS` which contains a hardcoded default subject and the styled HTML from `_default_mail_body()`.

### BR-PAY-065: Template Rendering with Error Suppression

**Rule:** `_render_mail_tpl(tpl, variables)` calls `tpl.format(**variables)` with error suppression.
**Implementation:** Catches `KeyError`, `IndexError`, `ValueError` and returns the raw template string unchanged on error. This prevents bad placeholders from crashing the email send process.
**Supported placeholders:** `{employee_name}`, `{month}`, `{year}`, `{gross}`, `{net}`, `{view_url}`.

### BR-PAY-066: Post-Send Email Tracking

**Rule:** After successful mail dispatch, the payslip is updated with `x_email_sent=True` and `x_email_sent_date=fields.Datetime.now()`.
**Implementation:** The `mail.mail` record is created with `auto_delete=True` (automatically deleted after sending to reduce database bloat).

### BR-PAY-067: Public View URL Construction

**Rule:** The public view URL format is `{web.base.url}/payslip/view/{x_access_token}`.
**Implementation:** At mail-send time, if `x_access_token` is empty, a new UUID is generated and saved before constructing the URL. `web.base.url` is read from `ir.config_parameter`.

### BR-PAY-068: Salary Line Display Rules

**Rule:** The public payslip page renders salary lines sorted by `sequence`. Lines whose `code` contains `thuc_lanh` receive the CSS class `line-net` (green highlight `#ecfdf5`). A total bar at the bottom displays the net amount with green gradient background.
**Implementation:** QWeb template iterates `lines` (sorted by sequence), applies conditional CSS class `line-net` based on code match, and shows `net` amount in the total bar.

### BR-PAY-069: Save History Guard

**Rule:** The "Luu lich su" action in the SPA frontend is only enabled when all employees with payslips in the period have `employee_confirm == 'confirmed'`. The backend endpoint `close-by-period` enforces this check.
**Implementation:** Backend searches non-cancelled payslips in month/year, verifies all have `x_employee_confirm == 'confirmed'`. Returns error listing up to 5 unconfirmed employee names if condition is not met. See FS-PAY-003 for close-by-period flow details.

---

## 6. STANDARD vs CUSTOM MATRIX

| # | Component | Type | Standard / Custom | Notes |
| --- | --- | --- | --- | --- |
| 1 | `x_access_token` field on `hb.payslip` | Field | Custom | UUID v4 token for public page access. |
| 2 | `x_employee_confirm` field on `hb.payslip` | Field | Custom | Selection field with tracking for confirmation state. |
| 3 | `x_employee_feedback` field on `hb.payslip` | Field | Custom | Free-text rejection reason. |
| 4 | `x_email_sent` / `x_email_sent_date` fields | Fields | Custom | Email dispatch tracking. |
| 5 | `x_confirmed_date` field | Field | Custom | Confirmation/rejection timestamp. |
| 6 | `action_send_payslip_mail()` method | Business logic | Custom | Email dispatch with template rendering. |
| 7 | `_render_mail_tpl()` method | Business logic | Custom | Template rendering with error suppression. |
| 8 | `_default_mail_body()` method | Business logic | Custom | Default styled HTML email body. |
| 9 | `PayrollPublicController` | Controller | Custom | Public routes for payslip view/confirm/reject. |
| 10 | `payslip_public_view` template | QWeb template | Custom | Public payslip page with confirmation UI. |
| 11 | `payslip_public_not_found` template | QWeb template | Custom | 404 page for invalid tokens. |
| 12 | `POST /payslip/send-mail` endpoint | REST API | Custom | Bulk email dispatch. |
| 13 | `GET/POST /mail-template` endpoints | REST API | Custom | Template configuration CRUD. |
| 14 | `BatchList.jsx` confirmation UI | React component | Custom | Checkbox, send-mail, confirmation badges. |
| 15 | `ConfigView.jsx` email tab | React component | Custom | Template editor with preview. |
| 16 | `ir.config_parameter` | Model | Standard Odoo | Used to store email template strings. |
| 17 | `mail.mail` | Model | Standard Odoo | Transactional email record with `auto_delete`. |
| 18 | `mail.thread` | Mixin | Standard Odoo | Inherited by `hb.payslip` for chatter and tracking. |
| 19 | `http.Controller` | Base class | Standard Odoo | Base class for public controller. |
| 20 | `uuid.uuid4()` | Python stdlib | Standard | Used for token generation. |
| 21 | `hr.group_hr_manager` / `hr.group_hr_user` | Security Groups | Standard Odoo | Access control groups. |

---

### Appendix A: Template Variables

| Variable | Type | Description | Example Value |
| --- | --- | --- | --- |
| `{employee_name}` | String | Employee full name | "Nguyen Van A" |
| `{month}` | String | Month (MM format) | "06" |
| `{year}` | String | Year (YYYY format) | "2026" |
| `{gross}` | String | Gross amount (formatted, no decimals, comma separators) | "15,000,000" |
| `{net}` | String | Net amount (formatted, no decimals, comma separators) | "12,500,000" |
| `{view_url}` | String | Full public URL to payslip | "https://example.com/payslip/view/abc-123-..." |

### Appendix B: Flash Message Types

| `msg` Parameter | CSS Class | Color | Message Text |
| --- | --- | --- | --- |
| `confirmed` | `.msg-ok` | Green | "Ban da xac nhan phieu luong thanh cong. Cam on!" |
| `rejected` | `.msg-err` | Red | "Ban da tu choi phieu luong. Phan hoi da duoc ghi nhan." |
| `already_actioned` | `.msg-warn` | Yellow | "Phieu luong nay da duoc xu ly truoc do." |
| `feedback_required` | `.msg-err` | Red | "Vui long nhap ly do tu choi." |

### Appendix C: Confirmation Badge Color Map (SPA)

```javascript
const CONFIRM_MAP = {
  pending:   { label: 'Cho',     bg: '#fef3c7', color: '#92400e' },
  confirmed: { label: 'Da XN',   bg: '#d1fae5', color: '#065f46' },
  rejected:  { label: 'Tu choi', bg: '#fee2e2', color: '#991b1b' },
};
```

### Appendix D: Frontend API Functions (`payroll.js`)

| Function | HTTP | Endpoint | Parameters |
| --- | --- | --- | --- |
| `sendPayslipMail(payslipIds)` | POST | `/hocba-hrm/api/payroll/payslip/send-mail` | `{ payslip_ids: payslipIds }` |
| `fetchMailTemplate()` | GET | `/hocba-hrm/api/payroll/mail-template` | -- |
| `saveMailTemplate(payload)` | POST | `/hocba-hrm/api/payroll/mail-template` | `{ subject, body }` |
| `closeBatchByPeriod(month, year)` | POST | `/hocba-hrm/api/payroll/batch/close-by-period` | `{ month, year }` |

### Appendix E: Source Files

| File | Purpose |
| --- | --- |
| `models/payslip.py` | `hb.payslip` model with confirmation fields and email methods |
| `controllers/payroll_public.py` | Public controller for token-based payslip view/confirm/reject |
| `controllers/payroll_api.py` | REST API endpoints for send-mail, mail-template |
| `views/payslip_public_templates.xml` | QWeb templates for public payslip page and 404 page |
| `frontend/src/api/payroll.js` | Frontend API client methods |
| `frontend/src/features/payroll/BatchList.jsx` | Payroll dashboard with confirmation UI |
| `frontend/src/features/payroll/ConfigView.jsx` | Email template editor (Mau email tab) |
