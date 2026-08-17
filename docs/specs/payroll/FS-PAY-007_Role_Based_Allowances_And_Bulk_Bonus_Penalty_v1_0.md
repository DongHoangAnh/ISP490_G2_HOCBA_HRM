# FS-PAY-007: Role-Based Allowances and Bulk Bonus/Penalty v1.1

## 1. FUNCTION OVERVIEW
### Business Requirement & Scope
Hoc Ba Education requires a flexible mechanism to manage role-based job position allowances (`hb.role.allowance.config`) and to process bulk monthly adjustments (bonus/penalty amounts) across employee payslips (`apply_bulk_bonus_penalty`).

This module provides:
1. Management of standard position allowances linked to `hr.job`.
2. Dynamic lookup integration (`lookup_source = 'role_allowance'`) in salary computation.
3. Bulk bonus and penalty input mechanism for active payslip batches (`x_bonus_extra`, `x_penalty_amount`).

---

## 2. FUNCTION FLOW
### Main Flow 1: Role Allowance Configuration
- Operator configures role allowances by selecting Job Position (`job_id`) and setting monthly allowance amount (`allowance_amount`).
- Salary rule engine queries `hb.role.allowance.config` during payslip computation when `lookup_source = 'role_allowance'`.

### Main Flow 2: Bulk Bonus / Penalty Application
- Operator posts JSON payload to `/hocba-hrm/api/payroll/bulk-bonus-penalty` containing month, year, target payslip/employee IDs and amounts (`bonusAmount`, `penaltyAmount`).
- System updates `x_bonus_extra` and `x_penalty_amount` on target `hb.payslip` records.
- System automatically triggers `action_compute_batch()` for affected draft payslips so that rule `bonus_extra` and rule `penalty_amount` generate payslip lines (`code: bonus_extra`, `code: penalty_amount`) and recalculate net pay (`net_amount`) immediately without requiring manual re-computation.

---

## 3. REST API ENDPOINTS
| Method | Endpoint | Description | Access Role |
|---|---|---|---|
| `GET` | `/hocba-hrm/api/payroll/role-allowance-configs` | List role allowance configs | HR Manager, Payroll Admin |
| `POST` | `/hocba-hrm/api/payroll/role-allowance-configs` | Create role allowance config | HR Manager, Payroll Admin |
| `DELETE` | `/hocba-hrm/api/payroll/role-allowance-configs/<id>` | Delete role allowance config | HR Manager, Payroll Admin |
| `POST` | `/hocba-hrm/api/payroll/bulk-bonus-penalty` | Apply bulk bonus/penalty adjustments | HR Manager, Payroll Admin |

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
- **BR-PAY-072 (Bulk Input & Auto Recomputation)**: WHEN `bulk-bonus-penalty` API is invoked, THE system SHALL update `x_bonus_extra` and `x_penalty_amount` on target payslips, generate `bonus_extra` and `penalty_amount` lines, and recalculate net pay immediately.
- **BR-PAY-073 (Draft State Constraint)**: WHERE payslip state is `done` or `close`, THE system SHALL reject bulk bonus/penalty mutations unless payslip is reset to `draft`.

