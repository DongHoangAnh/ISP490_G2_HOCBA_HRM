# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-007 |
| **Function Name** | Role-Based Allowances & Monthly Bulk Bonus/Penalty Management |
| **Created Date** | 11/08/2026 |
| **Last Update Date** | 11/08/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP & React SPA |
| **Reference** | `hb.role.allowance.config`, `hb.payslip` - module `hocba_payroll` |

---

## EARS REQUIREMENTS SPECIFICATION

### 1. Ubiquitous Requirements
- **FS-PAY-007-REQ-001:** THE system SHALL maintain a role allowance configuration table `hb.role.allowance.config` mapping Job Positions (`hr.job`) or Departments (`hr.department`) to fixed recurring allowances or holiday bonuses.
- **FS-PAY-007-REQ-002:** THE system SHALL provide a bulk bonus and penalty wizard API `POST /hocba-hrm/api/payroll/batch/<id>/bulk-bonus-penalty` allowing HR to apply bonus or penalty amounts with reasons to filtered subsets of employees.

### 2. Event-Driven Requirements
- **FS-PAY-007-REQ-003:** WHEN a payslip is computed, THE system SHALL automatically match the employee's Job Position and Department against active `hb.role.allowance.config` rules and aggregate the corresponding allowance amount.
- **FS-PAY-007-REQ-004:** WHEN HR applies a bulk bonus or penalty, THE system SHALL update `x_bonus_extra`, `x_bonus_reason`, `x_penalty_amount`, and `x_penalty_reason` on all target payslips and recalculate their net amounts.

### 3. State-Driven Requirements
- **FS-PAY-007-REQ-005:** WHILE a new payslip batch is created for a new month, THE system SHALL reset individual monthly bonus/penalty amounts to zero (`0.0`), requiring HR to re-enter monthly dynamic adjustments.

### 4. Unwanted Behaviors (Error Handling & Edge Cases)
- **FS-PAY-007-REQ-006:** WHERE an input bonus or penalty amount is negative or invalid, THE system SHALL raise a validation error or clamp negative values appropriately.
