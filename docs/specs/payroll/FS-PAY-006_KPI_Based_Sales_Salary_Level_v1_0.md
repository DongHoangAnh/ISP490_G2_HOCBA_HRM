# FS-PAY-006: KPI-Based Sales Salary Level Configuration v1.0

## 1. FUNCTION OVERVIEW
### Business Requirement & Scope
Hoc Ba Education applies KPI-based sales salary level tiers (`hb.sale.salary.level`) to evaluate Sales and Tele-sales performance. Depending on achieved monthly KPI revenue (min_kpi to max_kpi), sales employees receive a dedicated role allowance amount (`allowance_amount`) and commission bonus percentage rate (`bonus_rate`).

This module defines the CRUD operations, data validation, REST API endpoints, and salary rule lookup integration (`lookup_source = 'sale_level'`) for sales salary levels inside Odoo 19 `hocba_payroll`.

---

## 2. FUNCTION FLOW
### Main Flow 1: Sales Level Tier Management
- Operator accesses Sales Salary Level Configuration UI in SPA/Odoo.
- System presents existing level tiers sorted by `min_kpi` ascending.
- Operator creates or updates tier parameters: `Name`, `Code`, `Min KPI`, `Max KPI`, `Allowance Amount`, `Bonus Rate (%)`, `Note`.
- System validates non-overlapping KPI boundaries and positive allowance/bonus values.

### Main Flow 2: Salary Computation Integration
- During payslip computation (`_evaluate_rule_amount`), if a rule specifies `amount_select = 'lookup'` and `lookup_source = 'sale_level'`:
- Engine looks up the employee contract `sales_kpi_tier` or computes achieved KPI against `hb.sale.salary.level`.
- Returns `allowance_amount` or calculates `commission = base * bonus_rate / 100.0`.

---

## 3. REST API ENDPOINTS
| Method | Endpoint | Description | Access Role |
|---|---|---|---|
| `GET` | `/hocba/payroll/api/sale-salary-levels` | List all sales salary levels | HR Manager, Payroll Admin |
| `POST` | `/hocba/payroll/api/sale-salary-levels` | Create new sales salary level | HR Manager, Payroll Admin |
| `PUT` | `/hocba/payroll/api/sale-salary-levels/<id>` | Update sales salary level tier | HR Manager, Payroll Admin |
| `DELETE` | `/hocba/payroll/api/sale-salary-levels/<id>` | Delete sales salary level tier | HR Manager, Payroll Admin |

---

## 4. FIELD SPECIFICATION (`hb.sale.salary.level`)
| Field Name | Technical Name | Type | Constraint / Default | Description |
|---|---|---|---|---|
| Level Name | `name` | Char | Required | Tier label (e.g. Bậc 1 - Tập sự, Bậc 2 - Chuyên nghiệp) |
| Code | `code` | Char | Required, Unique | Unique tier code (e.g. SALE_L1, SALE_L2) |
| Min KPI | `min_kpi` | Float | Required, >= 0 | Minimum revenue threshold (VND) |
| Max KPI | `max_kpi` | Float | Required, > min_kpi | Maximum revenue threshold (VND) |
| Allowance Amount | `allowance_amount` | Float | Default: 0.0 | Fixed monthly allowance amount (VND) |
| Bonus Rate | `bonus_rate` | Float | Default: 0.0 | Commission percentage rate (%) |
| Note | `note` | Text | Optional | Additional notes or description |

---

## 5. BUSINESS RULES & EARS SPECIFICATION
- **BR-PAY-061 (Unique Code Constraint)**: THE system SHALL enforce unique `code` for each sales salary level tier.
- **BR-PAY-062 (Non-overlapping KPI Range)**: WHEN creating or updating a sales salary level, THE system SHALL ensure `min_kpi < max_kpi` and warn if ranges overlap across tiers.
- **BR-PAY-063 (Lookup Integration)**: WHERE salary rule `lookup_source = 'sale_level'`, THE computation engine SHALL fetch matching tier allowance and bonus rate dynamically during payslip computation.

---

## 6. SEED DATA & INITIALIZATION
Module initialization executes `init_default_sale_levels()` to create 4 standard tiers:
1. `SALE_L1`: Bậc 1 (KPI: 0 - 50,000,000 VND, Allowance: 1,000,000 VND, Bonus Rate: 2.0%)
2. `SALE_L2`: Bậc 2 (KPI: 50,000,001 - 100,000,000 VND, Allowance: 2,000,000 VND, Bonus Rate: 3.5%)
3. `SALE_L3`: Bậc 3 (KPI: 100,000,001 - 200,000,000 VND, Allowance: 3,500,000 VND, Bonus Rate: 5.0%)
4. `SALE_L4`: Bậc 4 (KPI: > 200,000,000 VND, Allowance: 5,000,000 VND, Bonus Rate: 7.0%)
