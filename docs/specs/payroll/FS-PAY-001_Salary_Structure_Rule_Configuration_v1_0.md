# FUNCTIONAL SPECIFICATION

## HRM ODOO - HOC BA EDUCATION

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-001 |
| **Function Name** | Salary Structure & Rule Configuration |
| **Created Date** | 21/06/2026 |
| **Last Update Date** | 21/06/2026 |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP (Community / Enterprise) |
| **Reference** | `hb.salary.structure`, `hb.salary.rule`, `hb.salary.rule.category` (new models) - module `hocba_payroll` |

| **Approver** | **Reviewer** | **Creator** |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

---

## CHANGE HISTORY

| No | Version | Change Description | Affected Sections | Date | Author |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial creation | All | 21/06/2026 | Group G2 |
| 2 | 1.1 | Added React SPA component documentation (ConfigView, SalaryRuleForm, FormulaSection). Clarified SPA supports only 2 of 4 amount types (fixed, formula). Documented unused SalaryRuleCategoryForm. | 1, 2, 3, 5 | 21/06/2026 | Group G2 |
| 3 | 1.2 | Standardized UI terminology according to enterprise C&B best practices: "Quy tắc tính lương" -> "Thành phần lương", "Bảng lương" -> "Kỳ tính lương", "Chuyển khoản" -> "File chi lương Bank", "Xác nhận lương" -> "Quy trình chốt & Phản hồi phiếu lương" (Keeping "Lịch sử lương" as requested). | All | 06/08/2026 | Group G2 |

---

## 1. FUNCTION OVERVIEW

| Item | Detail |
| --- | --- |
| **Function ID** | FS-PAY-001 |
| **Function Name** | Salary Structure & Rule Configuration |
| **Created Date** | 21/06/2026 |
| **Last Modified Date** | 21/06/2026 |

| Attribute | Value |
| --- | --- |
| **Processing Time** | On-demand |
| **Processing Type** | Interactive (Form/List view) |
| **Function Type** | Master Data |
| **Multilingual** | Yes (field-level `translate=True` on `name` fields) |

### Business Requirement & Function Overview

**Overview:**
This function manages salary structures (logical groupings of ordered rules) and salary rules (individual computation steps) that define how employee payslips are calculated. It replaces the previous manual Excel-based salary formula configuration with a fully database-driven, auditable system inside Odoo 19.

**Business Context:**
Hoc Ba Education operates two salary models:
- **STRUCT_OFFLINE** (`struct_offline`): For full-time offline staff, comprising 19 active rules. Covers base salary pro-rated by actual working days, allowances (meals, fuel, phone), bonuses, social/health/unemployment insurance (employee and employer portions), personal income tax (PIT) with progressive brackets, and net pay calculation.
- **STRUCT_ONLINE** (`struct_online`): For simplified online staff/teachers, comprising 5 rules. Covers wage, bonus, gross income, advances/deductions, and net pay.

Rules support 4 computation types in the Odoo backend: fixed amount, percentage of a base expression, Excel-like formula (transpiled to Python at runtime), and raw Python code. The React SPA exposes only 2 types: `fixed` and `formula`.

**Functional Scope:**
- CRUD operations on salary structures (`hb.salary.structure`).
- CRUD operations on salary rules (`hb.salary.rule`) with 4 amount types in Odoo backend (`fixed`, `percentage`, `formula`, `code`) and 2 types in the React SPA (`fixed`, `formula`).
- CRUD operations on salary rule categories (`hb.salary.rule.category`) for logical grouping and accumulation.
- Formula engine supporting `IF`, `SUM`, `ROUND`, `MAX`, `MIN`, `ABS` functions, with a transpiler that converts Excel-like syntax to executable Python.
- Drag-and-drop reorder of rules via sequence handle widget and REST API reorder endpoint.
- Formula help wizard (`hb.formula.help.wizard`) in Odoo backend displaying available functions and syntax.
- Quick-insert formula buttons on the rule form — both in Odoo backend (server action buttons) and React SPA (inline snippet insert buttons): IF, SUM, MAX, MIN, ABS, ROUND.
- Inline formula help table in the React SPA (`FormulaSection` component) with collapsible function reference and supported operators.
- Seed data: 8 rule categories, 2 structures, 24 rules (19 active in STRUCT_OFFLINE, 5 active in STRUCT_ONLINE).

**Users:**
- **HR Manager** (`hr.group_hr_manager`): Full CRUD access on all 3 models and the formula help wizard. Access to the Payroll > Cau hinh > Cau truc luong menu.
- **HR User** (`hr.group_hr_user`): Read-only access on `hb.salary.structure`, `hb.salary.rule`, and `hb.salary.rule.category`. No access to the formula help wizard. No access to the configuration menu.

---

## 2. FUNCTION FLOW

### Main Flow 1 -- Structure Management

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Navigates to Payroll > Cau hinh > Cau truc luong | System displays the salary structure list view (`view_salary_structure_list`) showing columns: name, code, rule_count, active. |
| 2 | HR Manager | Clicks "New" button | System opens the salary structure form view (`view_salary_structure_form`) with an empty record. |
| 3 | HR Manager | Fills in name (h1 title field), code, active toggle, and optional note | Fields are validated: `name` and `code` are required. The `code` field has a UNIQUE SQL constraint (`_code_uniq`). |
| 4 | HR Manager | Saves the record | System creates the `hb.salary.structure` record. `rule_count` is computed as 0 (no rules yet). |
| 5 | HR Manager | Opens the "Quy tac luong" notebook tab | System displays an inline editable list of `rule_ids` with columns: sequence (handle widget), code, name, category_id, amount_type, appears_on_payslip, active. |
| 6 | HR Manager | Adds rules inline or navigates to standalone rule form | See Main Flow 2. |
| 7 | HR Manager | Optionally archives the structure by toggling `active` to False | System sets `active=False`. The structure is hidden from default list views but retains all associated rules. |

**REST API (SPA):**
- `GET /hocba-hrm/api/payroll/salary-structure` returns active structures ordered by code, including `id`, `name`, `code`, `rule_count`.

**React SPA Note:** The SPA does not have a dedicated structure management UI. Structures are managed exclusively via the Odoo backend. The SPA `ConfigView` displays all salary rules in a flat list without structure grouping (passes `structureId={null}` to `SalaryRuleForm`).

### Main Flow 2 -- Rule Configuration

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Opens a salary structure form and clicks "Add a line" in the rules list, or opens the standalone salary rule form (`view_salary_rule_form`) | System displays the rule form with two main groups: "Thong tin" and "Tinh toan". |
| 2 | HR Manager | Fills in required fields: name, code, sequence, structure_id, category_id | Validation enforced: `name`, `code`, `sequence`, `structure_id`, `category_id` are all required. |
| 3 | HR Manager | Selects `amount_type` | System conditionally shows/hides fields: `amount_fixed` visible only when `amount_type='fixed'`; `amount_percentage` and `amount_percentage_base` visible only when `amount_type='percentage'`; formula section visible only when `amount_type='formula'`; Python code section visible only when `amount_type='code'`. |
| 4a | HR Manager | For `amount_type='fixed'`: enters `amount_fixed` | Value stored as Float(16,0). |
| 4b | HR Manager | For `amount_type='percentage'`: enters `amount_percentage` and `amount_percentage_base` | Percentage stored as Float(8,4). Base expression is a Char field evaluated at payslip computation time via `safe_eval`. |
| 4c | HR Manager | For `amount_type='formula'`: enters formula using Excel-like syntax | System provides quick-insert buttons (IF, SUM, MAX, MIN, ABS, ROUND) and a "Huong dan ham" help button. The formula is transpiled at payslip computation time by `_transpile_formula()`. |
| 4d | HR Manager | For `amount_type='code'`: enters Python code in the code widget | Python code is executed via `safe_eval` with `mode='exec'`. The code must assign the result to the `result` variable. |
| 5 | HR Manager | Optionally sets `condition_type` to `'python'` and enters `condition_python` | The condition is evaluated before the amount computation. If the condition returns falsy, the rule is skipped (amount = 0). |
| 6 | HR Manager | Toggles `appears_on_payslip` | Controls whether this rule line appears on the rendered payslip output. |
| 7 | HR Manager | Saves the record | System creates/updates the `hb.salary.rule` record. The parent structure's `rule_count` is recomputed via `_compute_rule_count`. |

**REST API (SPA):**
- `GET /hocba-hrm/api/payroll/salary-rule` lists active rules, optionally filtered by `structure_id`. Returns all field values.
- `POST /hocba-hrm/api/payroll/salary-rule` creates a new rule. Required body fields: `name`, `code`, `structure_id`, `category_id`.
- `POST /hocba-hrm/api/payroll/salary-rule/<id>` updates an existing rule.
- `POST /hocba-hrm/api/payroll/salary-rule/<id>/delete` archives the rule (`active=False`).
- `POST /hocba-hrm/api/payroll/salary-rule/reorder` batch-updates sequence values. Body: `{ "order": [id1, id2, ...] }`. Sets `sequence = (index + 1) * 10` for each rule.

**React SPA — SalaryRuleForm Component:**
The SPA rule form (`SalaryRuleForm.jsx`) only exposes 2 amount types: `fixed` (Số cố định) and `formula` (Công thức). The `percentage` and `code` types are only available in the Odoo backend form view.

SPA form fields: `name` (auto-generates `code` slug via `toSlug()` on create), `code` (read-only), `sequence`, `amount_type` (select: fixed/formula), `amount_fixed` (visible when fixed), `amount_formula` (visible when formula, with `FormulaSection`), `note`.

The `FormulaSection` component provides:
- A monospace `<textarea>` for formula input with placeholder example.
- Quick-insert buttons (IF, SUM, MAX, MIN, ABS, ROUND) that insert snippets at cursor position via `insertSnippet()`.
- A collapsible inline help table (toggle button "Hướng dẫn hàm") documenting all 7 formula functions and supported operators — equivalent to the Odoo `hb.formula.help.wizard` but rendered inline.

### Main Flow 3 -- Formula Engine

| Step | Actor | Action | System Response |
| --- | --- | --- | --- |
| 1 | HR Manager | Selects `amount_type='formula'` on a salary rule | The formula input section becomes visible with a text field, quick-insert buttons, and the "Huong dan ham" button. |
| 2 | HR Manager | Clicks a quick-insert button (e.g., "SUM( , )") | System calls `action_insert_formula_func()` which reads `formula_snippet` from the button's context and appends it to the current `amount_formula` value. The form reloads via `ir.actions.client` tag `reload`. |
| 3 | HR Manager | Clicks "Huong dan ham" button | System calls `action_show_formula_help()` which opens the `hb.formula.help.wizard` transient model in a dialog (`target='new'`). |
| 4 | System | The wizard's `default_get()` method calls `_build_help_html()` | Generates an HTML table documenting 7 supported functions: rule code reference, IF, SUM, MAX, MIN, ABS, ROUND. Also lists supported operators: `+ - * / > < >= <= == !=`. |
| 5 | HR Manager | Enters a formula, e.g., `SUM(luong_thoi_gian, thuong_khac)` | Formula is stored as-is in `amount_formula`. |
| 6 | System | At payslip computation time | `_transpile_formula(formula, known_codes)` is called. It converts: `IF(c,a,b)` to `((a) if (c) else (b))`; `SUM(a,b)` to `_range_sum('a','b')`; `ROUND(x,y)` to `_round_dir(x,y)`; known rule codes to `rules.get('code',0)`. The resulting Python expression is executed via `safe_eval`. |

### Error/Exception Flow

| Error Scenario | System Behavior |
| --- | --- |
| Duplicate structure code | SQL UNIQUE constraint (`_code_uniq`) raises `IntegrityError`. User sees message: "Ma cau truc luong phai la duy nhat!" |
| Duplicate category code | SQL UNIQUE constraint (`_code_uniq`) raises `IntegrityError`. User sees message: "Ma danh muc phai la duy nhat!" |
| Missing required fields on rule creation (API) | REST endpoint returns `{ "success": false, "error": "Missing required field: <field>" }` with HTTP 400. |
| Delete category with linked rules | PostgreSQL `ondelete='restrict'` prevents deletion. System raises an error indicating the category is referenced by existing rules. |
| Delete structure with linked rules | PostgreSQL `ondelete='cascade'` deletes all associated rules when the structure is deleted. |
| Invalid formula syntax at transpile time | `_transpile_formula` produces an invalid Python expression. `safe_eval` raises an exception during payslip computation. |
| Rule condition evaluates to falsy | Rule amount is set to 0. The rule line may still appear on the payslip if `appears_on_payslip=True`. |
| API reorder with invalid IDs | Non-existent rule IDs are silently skipped (`if rec.exists()`). |
| API salary rule not found (update/delete) | Returns `{ "success": false, "error": "Salary rule not found." }` with HTTP 404. |
| API category not found (update/delete) | Returns `{ "success": false, "error": "Category not found." }` with HTTP 404. |

---

## 3. SCREEN LAYOUT

### Screen 1: Salary Structure List (`view_salary_structure_list`)

**View type:** List
**XML ID:** `hocba_payroll.view_salary_structure_list`
**Model:** `hb.salary.structure`

| Column | Field | Widget | Notes |
| --- | --- | --- | --- |
| Ten cau truc | `name` | (default Char) | Translated field |
| Ma | `code` | (default Char) | |
| So quy tac | `rule_count` | (default Integer) | Computed field |
| Active | `active` | (default Boolean) | |

**Action:** `action_salary_structure` (xml_id: `hocba_payroll.action_salary_structure`)
- `res_model`: `hb.salary.structure`
- `view_mode`: `list,form`

### Screen 2: Salary Structure Form (`view_salary_structure_form`)

**View type:** Form
**XML ID:** `hocba_payroll.view_salary_structure_form`
**Model:** `hb.salary.structure`

**Layout:**

```
<sheet>
  <div class="oe_title">
    <h1> name (placeholder: "Ten cau truc") </h1>
  </div>
  <group>
    <group>
      code
      active
    </group>
    <group>
      rule_count
    </group>
  </group>
  note (placeholder: "Mo ta...")
  <notebook>
    <page string="Quy tac luong" name="rules">
      rule_ids → inline editable list (editable="bottom"):
        sequence (widget="handle")
        code
        name
        category_id
        amount_type
        appears_on_payslip
        active
    </page>
  </notebook>
</sheet>
```

| Field | Widget | Decoration/Attribute | Notes |
| --- | --- | --- | --- |
| `name` | (default Char) | h1 title, placeholder="Ten cau truc" | Required, translated |
| `code` | (default Char) | | Required |
| `active` | (default Boolean) | | Default True |
| `rule_count` | (default Integer) | | Computed, read-only |
| `note` | (default Text) | placeholder="Mo ta..." | Optional |
| `rule_ids` | One2many inline list | editable="bottom" | See inline list columns below |

**Inline rule_ids list columns:**

| Column | Field | Widget | Notes |
| --- | --- | --- | --- |
| (drag handle) | `sequence` | `handle` | Allows drag-reorder |
| Ma | `code` | (default Char) | |
| Ten | `name` | (default Char) | |
| Danh muc | `category_id` | (default Many2one) | |
| Loai tinh | `amount_type` | (default Selection) | |
| Hien thi tren phieu luong | `appears_on_payslip` | (default Boolean) | |
| Active | `active` | (default Boolean) | |

### Screen 3: Salary Rule Form (`view_salary_rule_form`)

**View type:** Form
**XML ID:** `hocba_payroll.view_salary_rule_form`
**Model:** `hb.salary.rule`

**Layout:**

```
<sheet>
  <group>
    <group string="Thong tin">
      name, code, sequence, structure_id, category_id, active, appears_on_payslip
    </group>
    <group string="Tinh toan">
      amount_type
      amount_fixed          (invisible when amount_type != 'fixed')
      amount_percentage     (invisible when amount_type != 'percentage')
      amount_percentage_base(invisible when amount_type != 'percentage')
    </group>
  </group>

  <!-- Formula section (invisible when amount_type != 'formula') -->
  <div invisible="amount_type != 'formula'" class="mt-3">
    <label for="amount_formula" string="Cong thuc"/>
    <field name="amount_formula" widget="text"
           placeholder="VD: SUM(luong_thoi_gian, thuong_khac) hoac luong_thoi_gian * 0.08"/>
    <div class="text-muted small mt-1 mb-2">
      Dung ma rule (slug) de tham chieu gia tri rule khac.
      VD: IF(tong_thu_nhap > 0, tong_thu_nhap - SUM(bhxh_8_nv, bhtn_1_nv), 0)
    </div>
    <!-- Quick-insert function buttons -->
    <div class="d-flex flex-wrap gap-1 mb-2">
      <button name="action_insert_formula_func" string="IF( , , )"
              context="{'formula_snippet': 'IF( , , )'}"/>
      <button name="action_insert_formula_func" string="SUM( , )"
              context="{'formula_snippet': 'SUM( , )'}"/>
      <button name="action_insert_formula_func" string="MAX( , )"
              context="{'formula_snippet': 'MAX( , )'}"/>
      <button name="action_insert_formula_func" string="MIN( , )"
              context="{'formula_snippet': 'MIN( , )'}"/>
      <button name="action_insert_formula_func" string="ABS( )"
              context="{'formula_snippet': 'ABS( )'}"/>
      <button name="action_insert_formula_func" string="ROUND( )"
              context="{'formula_snippet': 'ROUND( )'}"/>
    </div>
    <!-- Help reference button -->
    <button name="action_show_formula_help" string="Huong dan ham"
            class="btn btn-link btn-sm" icon="fa-question-circle"/>
  </div>

  <!-- Python Code section (invisible when amount_type != 'code') -->
  <group string="Python Code" invisible="amount_type != 'code'">
    amount_python_compute (widget="code", nolabel="1")
  </group>

  <group string="Dieu kien">
    condition_type
    condition_python (widget="code", invisible when condition_type != 'python')
  </group>
  note (placeholder: "Mo ta...")
</sheet>
```

| Field | Widget | Visibility Condition | Notes |
| --- | --- | --- | --- |
| `name` | (default Char) | Always | Required, translated |
| `code` | (default Char) | Always | Required, indexed |
| `sequence` | (default Integer) | Always | Required, default=10 |
| `structure_id` | (default Many2one) | Always | Required, ondelete=cascade |
| `category_id` | (default Many2one) | Always | Required, ondelete=restrict |
| `active` | (default Boolean) | Always | Default True |
| `appears_on_payslip` | (default Boolean) | Always | Default True |
| `amount_type` | (default Selection) | Always | Required, default='fixed' |
| `amount_fixed` | (default Float) | `amount_type != 'fixed'` hides | digits=(16,0) |
| `amount_percentage` | (default Float) | `amount_type != 'percentage'` hides | digits=(8,4) |
| `amount_percentage_base` | (default Char) | `amount_type != 'percentage'` hides | Expression string |
| `amount_formula` | `text` | `amount_type != 'formula'` hides | Placeholder provided |
| `amount_python_compute` | `code` | `amount_type != 'code'` hides | nolabel=1 |
| `condition_type` | (default Selection) | Always | default='none' |
| `condition_python` | `code` | `condition_type != 'python'` hides | |
| `note` | (default Text) | Always | placeholder="Mo ta..." |

**Buttons:**

| Button Label | Type | Method / Action | Context | Visibility |
| --- | --- | --- | --- | --- |
| IF( , , ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'IF( , , )'}` | `amount_type='formula'` |
| SUM( , ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'SUM( , )'}` | `amount_type='formula'` |
| MAX( , ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'MAX( , )'}` | `amount_type='formula'` |
| MIN( , ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'MIN( , )'}` | `amount_type='formula'` |
| ABS( ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'ABS( )'}` | `amount_type='formula'` |
| ROUND( ) | `object` | `action_insert_formula_func` | `{'formula_snippet': 'ROUND( )'}` | `amount_type='formula'` |
| Huong dan ham | `object` | `action_show_formula_help` | (none) | `amount_type='formula'` |

### Screen 4: Formula Help Wizard (`view_formula_help_wizard_form`)

**View type:** Form (dialog, `target='new'`)
**XML ID:** `hocba_payroll.view_formula_help_wizard_form`
**Model:** `hb.formula.help.wizard` (TransientModel)

| Field | Widget | Notes |
| --- | --- | --- |
| `info` | (default Html) | `nolabel="1"`, `readonly="1"`. Populated by `default_get()` calling `_build_help_html()`. |

**Footer:** A single "Dong" (Close) button with `special="cancel"`, class `btn-primary`.

**Help content table generated by `_build_help_html()`:**

| Function | Description | Example |
| --- | --- | --- |
| Ma rule | Write the rule slug code directly to reference its computed value. | `luong_thoi_gian * 0.08` |
| IF(dieu_kien, dung, sai) | Returns the true-value if condition is truthy, otherwise false-value. | `IF(tong_thu_nhap > 0, tong_thu_nhap - khau_tru_nv, 0)` |
| SUM(a, b) | Sums all rule amounts from code `a` to code `b` in sequence order (inclusive). | `SUM(luong_thoi_gian, thuong_khac)` |
| MAX(a, b) | Returns the maximum of the parameters. | `MAX(tong_thu_nhap - khau_tru_nv, 0)` |
| MIN(a, b) | Returns the minimum of the parameters. | `MIN(luong_thoi_gian, 5000000)` |
| ABS(x) | Returns the absolute value (removes negative sign). | `ABS(bhxh_8_nv)` |
| ROUND(x, y) | Rounds a number. y=1: round up (ceil), y=0: round down (floor). | `ROUND(luong_thoi_gian * 0.08, 1)` |

Supported operators: `+ - * / > < >= <= == !=`

### Screen 5: REST API Endpoints for SPA

**Base path:** `/hocba-hrm/api/payroll/`

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| GET | `/salary-structure` | `user` | List active salary structures ordered by code. Returns: `id`, `name`, `code`, `rule_count`. |
| GET | `/salary-rule` | `user` | List active salary rules. Optional query param `structure_id` to filter. Returns all rule fields. |
| POST | `/salary-rule` | `user` | Create a new salary rule. Required body: `name`, `code`, `structure_id`, `category_id`. |
| POST | `/salary-rule/<id>` | `user` | Update an existing salary rule. Accepts any writable field in body. |
| POST | `/salary-rule/<id>/delete` | `user` | Archive a salary rule (sets `active=False`). |
| POST | `/salary-rule/reorder` | `user` | Batch reorder rules. Body: `{ "order": [id1, id2, ...] }`. Sets `sequence=(index+1)*10`. |
| GET | `/salary-rule-category` | `user` | List all salary rule categories ordered by sequence, id. Returns: `id`, `name`, `code`, `sequence`, `note`. |
| POST | `/salary-rule-category` | `user` | Create a new salary rule category. |
| POST | `/salary-rule-category/<id>` | `user` | Update an existing salary rule category. |
| POST | `/salary-rule-category/<id>/delete` | `user` | Delete (unlink) a salary rule category. |

All endpoints use `csrf=False` and return JSON with the envelope: `{ "success": true/false, "data": ..., "message": ..., "error": ... }`.

### Screen 6: React SPA — SalaryRuleForm (`SalaryRuleForm.jsx`)

**File:** `frontend/src/features/payroll/SalaryRuleForm.jsx`
**Component:** `SalaryRuleForm` (default export)
**Used by:** Config view for adding/editing salary rules within a selected structure.

**Props:**

| Prop | Type | Description |
| --- | --- | --- |
| `item` | Object \| null | Existing rule to edit, or null for create mode |
| `structureId` | Number | ID of the parent salary structure |
| `nextSequence` | Number | Default sequence for new rules (default: 10) |
| `onClose` | Function | Callback to close the modal |
| `onSaved` | Function | Callback after successful save |

**AMOUNT_TYPES constant (line 7-10):**

```js
const AMOUNT_TYPES = [
  ['fixed', 'Số cố định'],
  ['formula', 'Công thức'],
];
```

Note: The Odoo backend supports 4 types (`fixed`, `percentage`, `formula`, `code`). The SPA only exposes `fixed` and `formula`.

**Form state fields:**

| Field | Type | Notes |
| --- | --- | --- |
| `code` | string | Auto-generated slug from `name` via `toSlug()` on create; read-only input |
| `name` | string | Required |
| `sequence` | number | Default from `nextSequence` prop |
| `amount_type` | string | `'fixed'` or `'formula'` |
| `amount_fixed` | number | Visible when `amount_type='fixed'` |
| `amount_formula` | string | Visible when `amount_type='formula'` (renders `FormulaSection`) |
| `note` | string | Optional description |

**`toSlug(str)` utility (line 13-38):** Converts Vietnamese diacritics to ASCII, lowercases, replaces spaces with underscores, strips non-alphanumeric characters. Used to auto-generate rule `code` from `name` on new rule creation.

**`FormulaSection` sub-component:**
- `FUNC_BUTTONS` array: 6 buttons — `IF( , , )`, `SUM( , )`, `MAX( , )`, `MIN( , )`, `ABS( )`, `ROUND( , )`.
- `insertSnippet(snippet)`: Inserts formula snippet at textarea cursor position (uses `selectionStart`/`selectionEnd`).
- `FUNC_HELP` array: 7 entries documenting formula functions (mã rule, IF, SUM, MAX, MIN, ABS, ROUND) with Vietnamese descriptions and examples.
- Collapsible help table toggled by "Hướng dẫn hàm" / "Ẩn hướng dẫn" button.
- Footer shows supported operators: `+ - * / > < >= <= == !=`.

**Submit behavior:** Calls `createSalaryRule(payload)` or `updateSalaryRule(id, payload)` from `api/payroll.js`. Payload includes `structure_id` from props.

### Screen 7: React SPA — ConfigView Rules Tab (`ConfigView.jsx`)

**File:** `frontend/src/features/payroll/ConfigView.jsx`
**Component:** `ConfigView` (default export)
**Used by:** `Payroll.jsx` main module when the "Cấu hình" tab is active.

**Sub-tabs (segmented control):**

| Tab ID | Label | FS-PAY Spec |
| --- | --- | --- |
| `rules` | Quy tắc lương | FS-PAY-001 |
| `banks` | Ngân hàng | FS-PAY-006 |
| `mail` | Mẫu email | FS-PAY-007 |

**Rules tab behavior:**
- Fetches all salary rules via `fetchSalaryRules({})` on mount (no structure filter — flat list).
- Displays a table with columns: Thứ tự (order arrows + index), Mã, Tên, Loại tính (type badge), Giá trị / Công thức, Thao tác (edit/delete).
- `TYPE_LABEL` constant: `{ fixed: 'Số cố định', formula: 'Công thức' }` — used for type badge display.
- **Drag-and-drop reorder:** Each `<tr>` is `draggable`. On drop, reorders the array and calls `reorderSalaryRules(order)` with the new ID sequence.
- **Arrow button reorder:** Up/down arrow buttons (`move(idx, dir)`) swap adjacent rules and call `reorderSalaryRules()`.
- **Add rule:** "Thêm rule" button opens `SalaryRuleForm` modal with `item=null`, `structureId=null`, `nextSequence` = max existing sequence + 10.
- **Edit rule:** Edit icon opens `SalaryRuleForm` modal with `item=ruleObject`.
- **Delete rule:** Delete icon calls `deleteSalaryRule(id)` after `confirm()` dialog.

**Note:** The SPA does not manage salary structures or salary rule categories in ConfigView. Structure management is Odoo-backend-only. Category management has a form component (`SalaryRuleCategoryForm.jsx`) but it is not currently imported or rendered by any view — it is unused dead code.

### Screen 8: React SPA — SalaryRuleCategoryForm (`SalaryRuleCategoryForm.jsx`) (UNUSED)

**File:** `frontend/src/features/payroll/SalaryRuleCategoryForm.jsx`
**Component:** `SalaryRuleCategoryForm` (default export)
**Status:** This component exists in the codebase but is NOT imported or used by any parent component. It is dead code.

**Props:** `item` (Object|null), `onClose` (Function), `onSaved` (Function).

**Form fields:** `code` (text, required), `name` (text, required), `sequence` (number, default 10), `note` (text, optional).

**Submit behavior:** Calls `createRuleCategory(payload)` or `updateRuleCategory(id, payload)` from `api/payroll.js`.

**Note:** The backend API endpoints for category CRUD exist and are functional (`GET/POST /salary-rule-category`, `POST /salary-rule-category/<id>`, `POST /salary-rule-category/<id>/delete`). The SPA form component is ready but has no parent view that renders it.

---

## 4. FIELD SPECIFICATION

### 4.1 Model: `hb.salary.structure`

**Python class:** `HbSalaryStructure`
**`_name`:** `hb.salary.structure`
**`_description`:** `Salary Structure`
**`_order`:** `name`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | -- | Ten cau truc | Name of the salary structure. `translate=True`. |
| 2 | `code` | `Char` | Yes | Yes | -- | SQL UNIQUE (`_code_uniq`: `UNIQUE(code)`, message: "Ma cau truc luong phai la duy nhat!") | Ma | Unique code identifier for the structure. |
| 3 | `active` | `Boolean` | No | No | `True` | -- | (default) | Archive toggle. When False the structure is hidden from default searches. |
| 4 | `note` | `Text` | No | No | -- | -- | Mo ta | Free-text description of the structure. |
| 5 | `rule_ids` | `One2many` | No | No | -- | Comodel: `hb.salary.rule`, inverse: `structure_id` | Quy tac luong | All salary rules belonging to this structure. |
| 6 | `rule_count` | `Integer` | No | No | -- | Computed by `_compute_rule_count`, depends on `rule_ids` | So quy tac | Count of rules in the structure. Read-only. |

### 4.2 Model: `hb.salary.rule`

**Python class:** `HbSalaryRule`
**`_name`:** `hb.salary.rule`
**`_description`:** `Salary Rule`
**`_order`:** `sequence, id`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | -- | Ten | Name of the salary rule. `translate=True`. |
| 2 | `code` | `Char` | Yes | Yes | -- | -- | Ma | Code slug used to reference this rule in formulas (e.g., `luong_thoi_gian`). |
| 3 | `sequence` | `Integer` | Yes | No | `10` | -- | Thu tu | Determines execution order. Lower sequence runs first. |
| 4 | `structure_id` | `Many2one` | Yes | Yes | -- | Comodel: `hb.salary.structure`, `ondelete='cascade'` | Cau truc luong | Parent salary structure. Cascade-deletes rules when structure is deleted. |
| 5 | `category_id` | `Many2one` | Yes | No | -- | Comodel: `hb.salary.rule.category`, `ondelete='restrict'` | Danh muc | Category for grouping and accumulation. Cannot delete category while rules reference it. |
| 6 | `active` | `Boolean` | No | No | `True` | -- | (default) | Archive toggle. Deactivated rules are excluded from payslip computation. |
| 7 | `amount_type` | `Selection` | Yes | No | `'fixed'` | Options: `('fixed','So tien co dinh')`, `('percentage','Ti le %')`, `('formula','Cong thuc')`, `('code','Python Code')` | Loai tinh | Determines which amount field is used for computation. |
| 8 | `amount_python_compute` | `Text` | No | No | -- | -- | Python Code | Python code executed via `safe_eval(mode='exec')`. Must assign result to `result` variable. Help text: "Python code gan ket qua vao bien `result`." |
| 9 | `amount_formula` | `Text` | No | No | -- | -- | Cong thuc | Excel-like formula transpiled to Python at runtime by `_transpile_formula()`. Help text describes SUM range syntax. |
| 10 | `amount_fixed` | `Float` | No | No | -- | `digits=(16, 0)` | So tien co dinh | Fixed monetary amount. Used when `amount_type='fixed'`. |
| 11 | `amount_percentage` | `Float` | No | No | -- | `digits=(8, 4)` | Ti le % | Percentage value (e.g., 8.0000 for 8%). Used when `amount_type='percentage'`. |
| 12 | `amount_percentage_base` | `Char` | No | No | -- | -- | Bieu thuc base cho % | Python expression evaluated via `safe_eval` to obtain the base amount for percentage calculation. |
| 13 | `condition_type` | `Selection` | No | No | `'none'` | Options: `('none','Luon dung')`, `('python','Bieu thuc Python')` | Dieu kien | Whether a condition is evaluated before computing the rule amount. |
| 14 | `condition_python` | `Text` | No | No | -- | -- | Dieu kien Python | Python expression evaluated via `safe_eval`. If falsy, the rule is skipped. |
| 15 | `appears_on_payslip` | `Boolean` | No | No | `True` | -- | Hien thi tren phieu luong | Controls visibility of this rule line on the payslip output. |
| 16 | `note` | `Text` | No | No | -- | -- | Mo ta | Free-text description of the rule. |

### 4.3 Model: `hb.salary.rule.category`

**Python class:** `HbSalaryRuleCategory`
**`_name`:** `hb.salary.rule.category`
**`_description`:** `Salary Rule Category`
**`_order`:** `sequence, id`

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `name` | `Char` | Yes | No | -- | -- | Ten | Category name. `translate=True`. |
| 2 | `code` | `Char` | Yes | Yes | -- | SQL UNIQUE (`_code_uniq`: `UNIQUE(code)`, message: "Ma danh muc phai la duy nhat!") | Ma | Unique code identifier for the category. Used in `categories.<code>` accumulation in payslip context. |
| 3 | `sequence` | `Integer` | No | No | `10` | -- | Thu tu | Display/sort order. |
| 4 | `note` | `Text` | No | No | -- | -- | Ghi chu | Free-text note. |

### 4.4 Model: `hb.formula.help.wizard`

**Python class:** `HbFormulaHelpWizard`
**`_name`:** `hb.formula.help.wizard`
**`_description`:** `Huong dan ham cong thuc`
**Type:** TransientModel

| # | Field Name | Type | Required | Index | Default | Constraints | String (Label) | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `info` | `Html` | No | No | `''` | `readonly=True` | Thong tin | HTML content displaying available formula functions. Populated by `default_get()` via `_build_help_html()`. |

**Methods:**
- `default_get(fields_list)`: Overrides parent to call `_build_help_html()` and set the `info` field.
- `_build_help_html()`: Static method that generates an HTML `<table>` documenting 7 formula functions plus supported operators.

---

## 5. BUSINESS RULES

### BR-PAY-001: Unique Code Constraint on Structure

**Rule:** The `code` field on `hb.salary.structure` has a SQL UNIQUE constraint (`_code_uniq`).
**Implementation:** `_code_uniq = models.Constraint('UNIQUE(code)', 'Ma cau truc luong phai la duy nhat!')`
**Behavior:** Attempting to create or update a structure with a duplicate code raises a database integrity error. The constraint message is displayed to the user.

### BR-PAY-002: Unique Code Constraint on Category

**Rule:** The `code` field on `hb.salary.rule.category` has a SQL UNIQUE constraint (`_code_uniq`).
**Implementation:** `_code_uniq = models.Constraint('UNIQUE(code)', 'Ma danh muc phai la duy nhat!')`
**Behavior:** Attempting to create or update a category with a duplicate code raises a database integrity error.

### BR-PAY-003: Amount Type Determines Visible and Used Fields

**Rule:** The `amount_type` selection determines which computation fields are visible on the form and which are used during payslip computation.
**Implementation (Odoo backend — 4 types):**
- `amount_type='fixed'`: Only `amount_fixed` is visible. The rule amount equals `rule.amount_fixed`.
- `amount_type='percentage'`: Only `amount_percentage` and `amount_percentage_base` are visible. The rule amount equals `round(safe_eval(amount_percentage_base) * amount_percentage / 100.0)`.
- `amount_type='formula'`: Only the formula section (with `amount_formula`, quick-insert buttons, and help button) is visible. The formula is transpiled to Python by `_transpile_formula()` and executed via `safe_eval`.
- `amount_type='code'`: Only the Python code group with `amount_python_compute` (widget=code) is visible. The code is executed via `safe_eval(mode='exec')` and must assign the result to the `result` variable.

**Implementation (React SPA — 2 types):**
The SPA `SalaryRuleForm` component only exposes `fixed` and `formula` in its `AMOUNT_TYPES` constant. Rules with `percentage` or `code` types can be created/edited via the Odoo backend form only. The SPA displays `amount_fixed` input for `fixed` and renders the `FormulaSection` component for `formula`.

### BR-PAY-004: Formula Transpiler Converts Excel-like Syntax to Python

**Rule:** The `_transpile_formula(formula, known_codes)` static method on `HbPayslip` converts user-entered Excel-like formulas into valid Python expressions.
**Implementation in:** `custom-addons/hocba_payroll/models/payslip.py`
**Transpilation rules (applied in order):**
1. `IF(condition, true_value, false_value)` is converted to `((true_value) if (condition) else (false_value))`. Supports nested parentheses via manual depth tracking. Case-insensitive. If not exactly 3 arguments, defaults to `0`.
2. `SUM(a, b)` is converted to `_range_sum('a', 'b')`. Case-insensitive. If not exactly 2 arguments, defaults to `0`.
3. `ROUND(x, y)` is converted to `_round_dir(x, y)` via regex substitution. Case-insensitive.
4. Known rule codes (identifiers matching `[a-zA-Z_][a-zA-Z0-9_]+` that exist in `known_codes` and are not in the builtins skip list) are converted to `rules.get('code', 0)`.
5. `MAX`, `MIN`, `ABS` are left as-is (they are Python builtins available in the eval context).
6. Operators `+ - * / > < >= <= == !=` and parentheses are kept as-is.
7. Empty or whitespace-only formulas return `'0'`.

**Builtins skip list:** `IF`, `SUM`, `MAX`, `MIN`, `ABS`, `ROUND`, `True`, `False`, `if`, `else`, `and`, `or`, `not`, `in`, `is`, `max`, `min`, `abs`, `round`, `sum`, `float`, `int`, `true`, `false`, `_range_sum`, `_round_dir`.

### BR-PAY-005: Rule Execution Order by Sequence

**Rule:** Salary rules are evaluated in `sequence, id` order (`_order = 'sequence, id'`).
**Behavior:** During payslip computation, rules within a structure are processed sequentially. Each rule's computed amount is stored in the `rules` dict (keyed by rule code), making it available to subsequent rules that reference it via code slug or `SUM()`.

### BR-PAY-006: SUM Range Sums Rules Between Two Codes

**Rule:** The `SUM(start_code, end_code)` formula function sums all computed rule amounts from `start_code` to `end_code` (inclusive) in sequence order.
**Implementation:** `_range_sum(start_code, end_code)` function in the payslip eval context. It looks up the positions of `start_code` and `end_code` in the ordered `rules` dict, swaps if start > end, and sums all values in the range `rules[codes[i_start:i_end+1]]`. Returns `0.0` if either code is not found.

### BR-PAY-007: Condition Evaluation Before Amount Computation

**Rule:** If a rule's `condition_type` is `'python'` and `condition_python` is non-empty, the condition expression is evaluated via `safe_eval` before computing the rule's amount.
**Implementation:** `_evaluate_rule_condition(rule, localdict)` returns `True` if `condition_type != 'python'` or `condition_python` is empty. Otherwise, returns `bool(safe_eval(rule.condition_python, localdict))`.
**Behavior:** If the condition returns a falsy value, the rule's amount is treated as 0.

### BR-PAY-008: Appears on Payslip Visibility Toggle

**Rule:** The `appears_on_payslip` boolean field controls whether a rule's computed line is displayed on the payslip output.
**Default:** `True`.
**Behavior:** Rules with `appears_on_payslip=False` are excluded from the visible payslip lines but may still participate in intermediate calculations. The REST API `employee-payroll` endpoint filters rules by `active=True` and `appears_on_payslip=True` to generate dynamic columns.

### BR-PAY-009: Reorder Sets Sequence = (index + 1) * 10

**Rule:** The REST API reorder endpoint (`POST /hocba-hrm/api/payroll/salary-rule/reorder`) accepts an ordered array of rule IDs and sets each rule's `sequence` to `(index + 1) * 10`.
**Implementation:** For each `(idx, rule_id)` in the `order` array: `rec.write({'sequence': (idx + 1) * 10})`. Non-existent IDs are silently skipped.
**Example:** For `order: [5, 3, 7]`, rule 5 gets `sequence=10`, rule 3 gets `sequence=20`, rule 7 gets `sequence=30`.

---

## 6. STANDARD vs CUSTOM MATRIX

| # | Component | Type | Standard / Custom | Notes |
| --- | --- | --- | --- | --- |
| 1 | `hb.salary.structure` model | Model | Custom (new model) | Standalone; does not inherit or extend any standard Odoo model. |
| 2 | `hb.salary.rule` model | Model | Custom (new model) | Standalone; does not use `hr_payroll.salary.rule`. |
| 3 | `hb.salary.rule.category` model | Model | Custom (new model) | Standalone; does not use `hr_payroll.salary.rule.category`. |
| 4 | `hb.formula.help.wizard` model | TransientModel | Custom (new model) | Wizard for displaying formula help in a dialog. |
| 5 | `view_salary_structure_form` | View (form) | Custom | Form view for `hb.salary.structure`. |
| 6 | `view_salary_structure_list` | View (list) | Custom | List view for `hb.salary.structure`. |
| 7 | `view_salary_rule_form` | View (form) | Custom | Form view for `hb.salary.rule` with conditional sections and formula buttons. |
| 8 | `view_formula_help_wizard_form` | View (form) | Custom | Dialog form for `hb.formula.help.wizard`. |
| 9 | `action_salary_structure` | Action (`ir.actions.act_window`) | Custom | Window action for salary structure list/form. |
| 10 | `menu_hb_payroll_config` | Menu item | Custom | "Cau hinh" sub-menu under Payroll, restricted to `hr.group_hr_manager`. |
| 11 | `menu_salary_structure_config` | Menu item | Custom | "Cau truc luong" menu item under Cau hinh, linked to `action_salary_structure`. |
| 12 | `salary_rule_category_data.xml` | Seed data | Custom | 8 categories with `noupdate="0"`. |
| 13 | `salary_structure_data.xml` | Seed data | Custom | 2 structures, 19 active rules (STRUCT_OFFLINE), 5 active rules (STRUCT_ONLINE), all with `noupdate="0"`. |
| 14 | Security ACL (ir.model.access.csv) | Access rules | Custom | HR User: read-only on structure, rule, category. HR Manager: full CRUD on structure, rule, category, wizard. |
| 15 | REST API (`PayrollAPI` controller) | Controller | Custom | Endpoints for salary-structure (GET), salary-rule (GET/POST/POST-update/POST-delete/POST-reorder), salary-rule-category (GET/POST/POST-update/POST-delete). |
| 16 | `_transpile_formula()` method | Business logic | Custom | Static method on `HbPayslip` that converts Excel-like formulas to Python. |
| 17 | `_range_sum()` helper | Business logic | Custom | Closure function in payslip eval context for SUM(a,b) range accumulation. |
| 18 | `_round_dir()` helper | Business logic | Custom | Closure function in payslip eval context for ROUND(x,y) with direction (ceil/floor). |
| 19 | `action_insert_formula_func()` method | Business logic | Custom | Appends formula snippet to `amount_formula` from button context. |
| 20 | `action_show_formula_help()` method | Business logic | Custom | Opens the formula help wizard dialog. |
| 21 | `_compute_rule_count()` method | Computed field | Custom | Counts `rule_ids` on the structure. |
| 22 | `hr.group_hr_user` | Security group | Standard Odoo | Standard HR User group from `hr` module. |
| 23 | `hr.group_hr_manager` | Security group | Standard Odoo | Standard HR Manager group from `hr` module. |
| 24 | `models.Constraint` (SQL) | Constraint mechanism | Standard Odoo 19 | Odoo 19 declarative SQL constraint API. |
| 25 | `safe_eval` | Utility | Standard Odoo | Standard Odoo safe evaluation utility used for formula/code execution. |
| 26 | `hocba_payroll` module | Module | Custom | Standalone payroll module; depends on `hr`, `mail`, `hocba_employees`. No dependency on `hr_payroll` (Enterprise). |

---

### Appendix A: Seed Data -- Rule Categories

| XML ID | Name | Code | Sequence |
| --- | --- | --- | --- |
| `rule_categ_alw` | Phu cap | `phu_cap` | 10 |
| `rule_categ_bonus` | Thuong | `thuong` | 20 |
| `rule_categ_gross` | Tong thu nhap | `tong_thu_nhap` | 30 |
| `rule_categ_deduct` | Giam tru | `giam_tru` | 40 |
| `rule_categ_ded` | BH nhan vien | `khau_tru_nv` | 50 |
| `rule_categ_tax` | Thue TNCN | `thue_tncn` | 60 |
| `rule_categ_net` | Thuc linh | `thuc_lanh` | 70 |
| `rule_categ_comp` | BH phan cong ty | `bh_phan_cong_ty` | 80 |

### Appendix B: Seed Data -- STRUCT_OFFLINE Rules (19 Active)

| # | XML ID | Name | Code | Seq | Category | Amount Type | Active |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `rule_off_an_ca` | An ca | `an_ca` | 10 | `phu_cap` | code | Yes |
| 2 | `rule_off_xang_xe` | Xang xe | `xang_xe` | 11 | `phu_cap` | code | Yes |
| 3 | `rule_off_dien_thoai` | Dien thoai | `dien_thoai` | 12 | `phu_cap` | code | Yes |
| 4 | `rule_off_thuong_khac` | Thuong khac | `thuong_khac` | 13 | `thuong` | code | Yes |
| 5 | `rule_off_ho_tro_nuoi_con` | Ho tro nuoi con nho | `ho_tro_nuoi_con` | 14 | `phu_cap` | code | Yes |
| 6 | `rule_off_gross` | Tong thu nhap | `tong_thu_nhap` | 20 | `tong_thu_nhap` | code | Yes |
| 7 | `rule_off_tn_mien_thue` | Thu nhap mien thue TNCN | `tn_mien_thue` | 21 | `tong_thu_nhap` | code | Yes |
| 8 | `rule_off_tn_truoc_thue` | Tong TN truoc thue | `tn_truoc_thue` | 22 | `tong_thu_nhap` | code | Yes |
| 9 | `rule_off_npt` | NPT | `npt` | 30 | `giam_tru` | code | Yes |
| 10 | `rule_off_giam_tru` | So tien giam tru | `giam_tru` | 31 | `giam_tru` | code | Yes |
| 11 | `rule_off_bhxh_nv` | BHXH (8%) | `bhxh_8_nv` | 40 | `khau_tru_nv` | code | Yes |
| 12 | `rule_off_bhyt_nv` | BHYT (1.5%) | `bhyt_1_5_nv` | 41 | `khau_tru_nv` | code | Yes |
| 13 | `rule_off_bhtn_nv` | BHTN (1%) | `bhtn_1_nv` | 42 | `khau_tru_nv` | code | Yes |
| 14 | `rule_off_tn_tinh_thue` | Tong TN tinh thue | `tn_tinh_thue` | 50 | `thue_tncn` | code | Yes |
| 15 | `rule_off_tncn` | Thue TNCN | `thue_tncn` | 60 | `thue_tncn` | code | Yes |
| 16 | `rule_off_net` | Tong luong thuc linh | `thuc_lanh` | 70 | `thuc_lanh` | code | Yes |
| 17 | `rule_off_bhxh_ct` | BHXH (17.5%) CT | `bhxh_17_5_ct` | 80 | `bh_phan_cong_ty` | code | Yes |
| 18 | `rule_off_bhyt_ct` | BHYT (3%) CT | `bhyt_3_ct` | 81 | `bh_phan_cong_ty` | code | Yes |
| 19 | `rule_off_bhtn_ct` | BHTN (1%) CT | `bhtn_1_ct` | 82 | `bh_phan_cong_ty` | code | Yes |

### Appendix C: Seed Data -- STRUCT_ONLINE Rules (5 Active)

| # | XML ID | Name | Code | Seq | Category | Amount Type |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `rule_on_wage` | Luong | `luong` | 10 | `phu_cap` | code |
| 2 | `rule_on_thuong` | Thuong | `thuong` | 40 | `thuong` | code |
| 3 | `rule_on_gross` | TONG THU NHAP | `tong_thu_nhap` | 50 | `tong_thu_nhap` | code |
| 4 | `rule_on_tam_ung` | Tam ung, tru khac | `tam_ung_tru_khac` | 90 | `giam_tru` | code |
| 5 | `rule_on_net` | THUC LINH | `thuc_lanh` | 99 | `thuc_lanh` | code |

### Appendix D: Security Access Control List

| ACL ID | Model | Group | Read | Write | Create | Delete |
| --- | --- | --- | --- | --- | --- | --- |
| `access_hb_salary_structure_user` | `hb.salary.structure` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_salary_structure_manager` | `hb.salary.structure` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_salary_rule_user` | `hb.salary.rule` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_salary_rule_manager` | `hb.salary.rule` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_salary_rule_category_user` | `hb.salary.rule.category` | `hr.group_hr_user` | 1 | 0 | 0 | 0 |
| `access_hb_salary_rule_category_manager` | `hb.salary.rule.category` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |
| `access_hb_formula_help_wizard_manager` | `hb.formula.help.wizard` | `hr.group_hr_manager` | 1 | 1 | 1 | 1 |

Note: The formula help wizard has no access rule for `hr.group_hr_user`. Only HR Managers can open the wizard.
