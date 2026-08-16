# FS-PAY-007: Role-Based Allowances and Bulk Bonus/Penalty v1.0

## 1. FUNCTION OVERVIEW
### Business Requirement & Scope
Hoc Ba Education requires a flexible mechanism to manage role-based job position allowances (`hb.role.allowance.config`) and to process bulk monthly adjustments (bonus/penalty amounts) across employee payslips (`apply_bulk_bonus_penalty`).

This module provides:
1. Management of standard position allowances linked to `hr.job`.
2. Dynamic lookup integration (`lookup_source = 'role_allowance'`) in salary computation.
3. Bulk bonus and penalty input mechanism for active payslip batches.

---

## 2. FUNCTION FLOW
### Main Flow 1: Role Allowance Configuration
- Operator configures role allowances by selecting Job Position (`job_id`) and setting monthly allowance amount (`allowance_amount`).
- Salary rule engine queries `hb.role.allowance.config` during payslip computation when `lookup_source = 'role_allowance'`.

### Main Flow 2: Bulk Bonus / Penalty Application
- Operator posts JSON payload to `/hocba/payroll/api/bulk-bonus-penalty` containing batch ID or employee IDs and amounts.
- System creates or updates `hb.payslip.input` lines:
  - Positive amounts create/update `BONUS` input code lines.
  - Negative amounts create/update `PENALTY` input code lines.
- System automatically triggers `action_compute_sheet()` for affected draft payslips.

---

## 3. REST API ENDPOINTS
| Method | Endpoint | Description | Access Role |
|---|---|---|---|
| `GET` | `/hocba/payroll/api/role-allowance-configs` | List role allowance configs | HR Manager, Payroll Admin |
| `POST` | `/hocba/payroll/api/role-allowance-configs` | Create role allowance config | HR Manager, Payroll Admin |
| `DELETE` | `/hocba/payroll/api/role-allowance-configs/<id>` | Delete role allowance config | HR Manager, Payroll Admin |
| `POST` | `/hocba/payroll/api/bulk-bonus-penalty` | Apply bulk bonus/penalty adjustments | HR Manager, Payroll Admin |

---

## 4. FIELD SPECIFICATION (`hb.role.allowance.config`)
| Field Name | Technical Name | Type | Constraint / Default | Description |
|---|---|---|---|---|
| Job Position | `job_id` | Many2one (`hr.job`) | Required | Target job position |
| Job Title | `job_name` | Char | Related | Read-only job title string |
| Allowance Amount | `allowance_amount` | Float | Required, >= 0 | Monthly role allowance amount (VND) |
| Description | `description` | Text | Optional | Additional details |

---

## 5. BUSINESS RULES & EARS SPECIFICATION
- **BR-PAY-071 (Single Allowance per Job)**: THE system SHALL prevent duplicate active allowance configs for the same `job_id`.
- **BR-PAY-072 (Bulk Input Creation)**: WHEN `bulk-bonus-penalty` API is invoked, THE system SHALL create `hb.payslip.input` entries linked to target payslips and recalculate net pay immediately.
- **BR-PAY-073 (Draft State Constraint)**: WHERE payslip state is `done` or `close`, THE system SHALL reject bulk bonus/penalty mutations unless payslip is reset to `draft`.
