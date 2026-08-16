# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-006 |
| **Function Name** | KPI-Based Sales Salary Level Configuration & Computation |
| **Created Date** | 11/08/2026 |
| **Last Update Date** | 11/08/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP & React SPA |
| **Reference** | `hb.sale.salary.level`, `hb.payslip` - module `hocba_payroll` |

---

## EARS REQUIREMENTS SPECIFICATION

### 1. Ubiquitous Requirements
- **FS-PAY-006-REQ-001:** THE system SHALL maintain a master data table `hb.sale.salary.level` storing sales salary tiers with `level_code`, `name`, `sequence`, `kpi_target`, and `base_wage`.
- **FS-PAY-006-REQ-002:** THE system SHALL pre-seed 6 default sales salary levels (Level 1 to Level 6) upon module installation.

### 2. Event-Driven Requirements
- **FS-PAY-006-REQ-003:** WHEN HR calculates a payslip for an employee, THE system SHALL evaluate whether the employee is an official sales staff member (`x_employment_status == 'official'` AND position/job IS sales).
- **FS-PAY-006-REQ-004:** WHEN an employee is identified as official sales staff, THE system SHALL look up the highest sales salary level where `kpi_target <= x_kpi_score` and apply its configured `base_wage` as the employee's monthly basic salary.

### 3. State-Driven Requirements
- **FS-PAY-006-REQ-005:** WHILE an employee is a probationary sales staff (`x_employment_status == 'probation'`) or a non-sales employee, THE system SHALL use the contract's standard `wage_base` instead of the sales level grid.

### 4. Unwanted Behaviors (Error Handling & Edge Cases)
- **FS-PAY-006-REQ-006:** WHERE an official sales staff member's KPI score is below Level 1 threshold (`x_kpi_score < 1.0`), THE system SHALL default to Level 1 base wage to prevent zero-wage calculation errors.
- **FS-PAY-006-REQ-007:** WHERE no active sales salary levels exist in configuration, THE system SHALL fallback gracefully to contract `wage_base`.
