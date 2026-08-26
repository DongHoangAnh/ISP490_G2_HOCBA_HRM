
## Change History (v1.1 Update)
- **Version 1.1 (2026-08-13)**:
  - Added `_prefetch_lookups_bulk` for high-performance bulk contract rates, sale levels, and role allowance prefetching.
  - Documented AST-safe Python calculation engine (`_evaluate_rule_condition`, `_evaluate_rule_amount`).
  - Formalized Vietnam Personal Income Tax progressive brackets calculation helper `_hocba_pit(taxable_income, dependent_count)` (11M self deduction, 4.4M per dependent, 7 tax brackets: 5% to 35%).
  - Added Teaching Salary Computation (`action_compute_teaching_salary`) with contract fields (`hourly_rate`, `hsk_extra_rate`, `hsk_teaching_hours`, `sales_kpi_tier`, `sales_kpi_amount`, `custom_role_allowance`, `teaching_hours_threshold`).

| Field        | Value                                                            |
|------------- |----------------------------------------------------------------- |
| **Code**     | FS-PAY-002                                                       |
| **Title**    | Payslip Computation Engine                                       |
| **Module**   | hocba_payroll                                                    |
| **Model**    | hb.payslip (inherited mail.thread)                               |
| **Version**  | 1.2                                                              |
| **Date**     | 2026-08-09                                                       |
| **Status**   | Approved                                                         |
| **Platform** | Odoo 19 Community                                                |

---

## 1. OVERVIEW

The Payslip Computation Engine is the core salary calculation subsystem of the `hocba_payroll` module. It evaluates a set of data-driven salary rules against a payslip, producing payslip lines that represent every element of an employee's pay -- allowances, gross income, insurance deductions, personal income tax, and net pay.

The engine is invoked through `action_compute_sheet()` for individual payslips or `action_compute_batch()` for multi-employee batch calculations. In batch mode, the engine utilizes **High-Performance In-Memory Optimizations**:
1. **$O(1)$ Bulk Lookup Caching (`_prefetch_lookups_bulk`)**: Fetches all attendance/work-entry/lookup data across ALL employees in 1 single pass per model before looping, eliminating $O(N \times R)$ database queries.
2. **Process-Level AST Caching (`_AST_CACHE`)**: Caches compiled Abstract Syntax Trees (AST) for formula expressions in CPython memory, eliminating `ast.parse` overhead across repeated calculations.
3. **Single Topological Rule Pre-Sorting (`_topo_sort_rules`)**: Sorts rules once using Kahn's algorithm per batch execution pass instead of per-slip.
4. **Safe Pure AST Tree-Walking Evaluator (`_eval_formula_expr`)**: Evaluates formulas without executing arbitrary Python string `eval()` or `exec()`.

| Concept               | Description                                                                                  |
|----------------------- |--------------------------------------------------------------------------------------------- |
| Entry point            | `hb.payslip.action_compute_sheet()` -- button on payslip form and batch action               |
| Batch Entry point      | `hb.payslip.action_compute_batch()` -- optimized batch calculation pass                       |
| Salary structure       | `hb.salary.structure` -- groups a set of ordered salary rules                                |
| Salary rule            | `hb.salary.rule` -- defines one computation step (allowance, deduction, tax, net, etc.)      |
| Payslip line           | `hb.payslip.line` -- stores computed result of one rule with `int(round(amount))` for VND |
| Worked days            | `hb.payslip.worked_days` -- attendance/work-entry data consumed by rules                     |
| Payslip input          | `hb.payslip.input` -- ad-hoc monetary inputs (advances, bonuses) consumed by rules           |
| Proxy classes          | Module-level Python classes (`WorkedDaysProxy`, `InputsProxy`, `CategoryTotals`)             |
| AST Cache              | Process-level `_AST_CACHE` dict caching parsed formula ASTs to avoid recompilation overhead  |
| Bulk Lookup Prefetch   | `_prefetch_lookups_bulk()` pre-calculates lookup values for $N$ employees in 1 query pass    |
| PIT calculator         | `_hocba_pit()` implements the 7-bracket Vietnam progressive personal income tax               |

---

## 2. FUNCTION FLOW

### 2.1 Main Entry Point -- action_compute_sheet()

| Step | Action                              | Detail                                                                                                                                                         |
|----- |------------------------------------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Iterate payslips                    | The method operates on `self` (one or more `hb.payslip` records). Each payslip is processed independently within a `for slip in self` loop.                    |
| 2    | Call `_ensure_draft_state()`        | Raises `UserError` if `slip.state` is not in `('draft', 'verify')`. Prevents recomputation of confirmed or cancelled payslips.                                |
| 3    | Call `_resolve_contract()`          | Resolves the employee's active contract for the payslip date range. See section 2.2.                                                                           |
| 4    | Call `_resolve_structure(contract)` | Determines the salary structure to use for this payslip. See section 2.3.                                                                                      |
| 5    | Clear existing lines                | Calls `slip.line_ids.unlink()` to remove all previously computed payslip lines before recomputation.                                                           |
| 6    | Build evaluation namespace          | Calls `slip._build_localdict(contract)` to construct the Python namespace. See section 2.4.                                                                     |
| 7    | Collect active rules & Topo-Sort    | Retrieves structure rules and applies Kahn's algorithm (`_topo_sort_rules`). Falls back to `sequence` order if a dependency cycle is detected.                 |
| 8    | Initialize warnings list            | Creates an empty `warnings = []` list to capture non-fatal rule evaluation errors.                                                                             |
| 9    | Iterate rules in topological order  | For each rule, performs steps 9a through 9d.                                                                                                                   |
| 9a   | Evaluate condition                  | Calls `_evaluate_rule_condition(rule, localdict)`. If condition returns `False`, rule is skipped (`continue`).                                                |
| 9b   | Evaluate amount                     | Calls `_evaluate_rule_amount(rule, localdict, prefetched_lookups)`. Returns a tuple `(amount, qty, rate)`.                                                     |
| 9c   | Store result in namespace           | Sets `localdict['rules'][rule.code] = amount` and calls `localdict['categories'].accumulate(rule.category_id.code, amount)`.                                   |
| 9d   | Create payslip line                 | If `rule.appears_on_payslip` is True, collects line dict with `amount = int(round(amount))` for bulk insert into `hb.payslip.line`.                            |
| 9e   | Error handling (per rule)           | If any exception occurs during 9a/9b, error is logged, a warning is appended, and rule produces `(0.0, 1.0, 0.0)`.                                             |
| 10   | Finalize payslip                    | Bulk-inserts lines in 1 DB trip, sets `x_teaching_computed = True`, and stores `x_compute_warnings`.                                                          |
| 11   | Return                              | Returns `True`.                                                                                                                                                |

### 2.2 Contract Resolution -- _resolve_contract()

| Step | Action                                       | Detail                                                                                                                                 |
|----- |--------------------------------------------- |--------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Check explicit contract                       | If `self.contract_id` is already set on the payslip, use it directly.                                                                  |
| 2    | Search for active contract                    | Searches `hb.contract` with domain: `employee_id` matches, `state = 'open'`, `date_start <= payslip.date_to`, and (`date_end` unset OR `date_end >= payslip.date_from`). Limit 1. |
| 3    | Assign if found                               | Sets `self.contract_id = contract` on the payslip record.                                                                              |
| 4    | Raise if none                                 | Raises `ValidationError` with a message naming the employee and the date range if no contract is found.                                |

### 2.3 Structure Resolution -- _resolve_structure(contract)

| Step | Priority | Source                                 | Detail                                                                                                                        |
|----- |--------- |--------------------------------------- |------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Highest  | `self.structure_id`                    | Explicit structure set directly on the payslip record.                                                                        |
| 2    | Medium   | `contract.x_structure_id`              | Structure linked on the employee's contract.                                                                                  |
| 3    | Lowest   | Auto-detect by `employee.x_work_form`  | Reads `employee.x_work_form` (default `'offline'`). If `'online'` selects `STRUCT_ONLINE`; otherwise selects `STRUCT_OFFLINE`. Searches `hb.salary.structure` by code. |
| 4    | --       | Raise if none                          | Raises `ValidationError` if no structure is found at any priority level.                                                      |

### 2.4 Namespace Construction -- _build_localdict(contract)

| Key              | Type / Class           | Description                                                                                                      |
|----------------- |----------------------- |----------------------------------------------------------------------------------------------------------------- |
| `payslip`        | `hb.payslip`           | The current payslip record (`self`).                                                                             |
| `employee`       | `hr.employee`          | The payslip's employee record (`self.employee_id`).                                                              |
| `contract`       | `hb.contract`          | The resolved contract passed as argument.                                                                        |
| `worked_days`    | `WorkedDaysProxy`      | Proxy wrapping `self.worked_days_ids`. Access via `worked_days.WORK100.number_of_days`.                          |
| `inputs`         | `InputsProxy`          | Proxy wrapping `self.input_ids`. Access via `inputs.ADVANCE.amount`.                                             |
| `categories`     | `CategoryTotals`       | Running totals by category code. Access via `categories.BASIC`. Mutated via `accumulate(code, amount)`.          |
| `rules`          | `dict`                 | Ordered dict of computed rule results keyed by rule code. Access via `rules.get('an_ca', 0)`.                    |
| `_range_sum`     | `function`             | Closure: `_range_sum(start_code, end_code)` sums all rule amounts between two codes (inclusive) by insertion order.|
| `_round_dir`     | `function`             | Closure: `_round_dir(value, direction)`. Direction `1` returns `math.ceil(value)`, direction `0` returns `math.floor(value)`. |
| `result`         | `float`                | Placeholder initialized to `0.0`. Rules write their computed amount here.                                        |
| `result_qty`     | `float`                | Placeholder initialized to `1.0`. Rules may override quantity.                                                   |
| `result_rate`    | `float`                | Placeholder initialized to `0.0`. Rules may override rate.                                                       |
| `round`          | built-in               | Python `round()`.                                                                                                |
| `max`            | built-in               | Python `max()`.                                                                                                  |
| `min`            | built-in               | Python `min()`.                                                                                                  |
| `abs`            | built-in               | Python `abs()`.                                                                                                  |
| `float`          | built-in               | Python `float()`.                                                                                                |
| `int`            | built-in               | Python `int()`.                                                                                                  |

### 2.5 Condition Evaluation -- _evaluate_rule_condition(rule, localdict)

| Scenario                                           | Return Value                                         |
|--------------------------------------------------- |----------------------------------------------------- |
| `rule.condition_type != 'python'`                  | `True` (rule always executes)                        |
| `rule.condition_python` is empty/falsy             | `True` (rule always executes)                        |
| `rule.condition_type == 'python'` and code present | `bool(safe_eval(rule.condition_python, localdict))`  |

### 2.6 Amount Evaluation -- _evaluate_rule_amount(rule, localdict, prefetched_lookups=None)

Returns a tuple `(amount, qty, rate)`.

| amount_type    | Evaluation Logic                                                                                                                                                                  |
|--------------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `code`         | Resets `result`, `result_qty`, `result_rate` in `localdict`. Executes `safe_eval(rule.amount_python_compute, localdict, mode='exec')`. Reads back updated result values.          |
| `fixed`        | Returns `(rule.amount_fixed, 1.0, 0.0)`.                                                                                                                                         |
| `percentage`   | Evaluates `rule.amount_percentage_base` via `_eval_formula_expr()`. Computes `int(round(base * rule.amount_percentage / 100.0))`. Returns `(amount, 1.0, 0.0)`.                   |
| `formula`      | Evaluates `rule.amount_formula` safely via `_eval_formula_expr(formula, localdict)`. Returns `(amount, 1.0, 0.0)`.                                                               |
| `lookup`       | Checks `prefetched_lookups` dict cache for `(employee_id, lookup_source, lookup_field)`. If missed, calls `_compute_lookup(rule)` to query database via `LOOKUP_CATALOG`.        |

### 2.7 Pure AST Tree-Walking Evaluator -- _eval_formula_expr(expr, localdict)

Safe AST expression walker replacing string transpiling and code execution:

| Expression / Syntax      | AST Handling                                                                                         |
|------------------------- |----------------------------------------------------------------------------------------------------- |
| `IF(cond, true, false)`  | AST call evaluated as Python `if/else` expression: `true_val if cond_val else false_val`.            |
| `SUM(a, b)`              | Evaluates closure `_range_sum(a, b)` summing all computed rules between sequence range `a` to `b`.    |
| `MAX(...)`, `MIN(...)`   | Evaluates `max()` or `min()` built-in over list of arguments.                                        |
| `ROUND(x, y)`            | Evaluates `_round_dir(x, y)` where `y=1` (ceil) or `y=0` (floor) or standard Python `round(x, y)`.   |
| Rule codes               | Looked up in `localdict['rules'].get(code, 0.0)`.                                                    |
| Operators                | AST support for `+`, `-`, `*`, `/`, `%`, `>`, `<`, `>=`, `<=`, `==`, `!=`, `and`, `or`, `not`.       |

### 2.8 PIT Calculation -- _hocba_pit(taxable_income)

Implements the 7-bracket Vietnam progressive Personal Income Tax (PIT) schedule.

| Bracket | Taxable Income Range (VND) | Rate |
|-------- |--------------------------- |----- |
| 1       | 0 -- 5,000,000             | 5%   |
| 2       | 5,000,001 -- 10,000,000    | 10%  |
| 3       | 10,000,001 -- 18,000,000   | 15%  |
| 4       | 18,000,001 -- 32,000,000   | 20%  |
| 5       | 32,000,001 -- 52,000,000   | 25%  |
| 6       | 52,000,001 -- 80,000,000   | 30%  |
| 7       | 80,000,001+                | 35%  |

Returns `0.0` if `taxable_income <= 0`. Result is rounded via `round()`. The bracket table is defined in the module-level constant `PIT_BRACKETS`.

### 2.9 Dependent Count -- _get_dependent_count()

Counts active dependents from `employee.x_dependent_ids` where `date_start <= today` and (`date_end` is unset OR `date_end >= today`). Returns `0` if the field is not present on the employee model.

---

## 3. FIELD SPECIFICATIONS

### 3.1 hb.payslip -- Fields Relevant to Computation

| Field                   | Type                     | Required | Default           | Description                                                  |
|------------------------ |------------------------- |--------- |------------------ |------------------------------------------------------------- |
| employee_id             | Many2one(hr.employee)    | Yes      | --                | The employee whose salary is being computed.                 |
| contract_id             | Many2one(hb.contract)    | No       | --                | Resolved contract; set automatically if empty.               |
| structure_id            | Many2one(hb.salary.structure) | No  | --                | Resolved salary structure; set during computation.           |
| date_from               | Date                     | Yes      | --                | Start date of the pay period.                                |
| date_to                 | Date                     | Yes      | --                | End date of the pay period.                                  |
| state                   | Selection                | Yes      | `'draft'`         | Values: draft, verify, done, cancel.                         |
| line_ids                | One2many(hb.payslip.line)| --       | --                | Computed payslip lines (cleared and rebuilt on each compute). |
| worked_days_ids         | One2many(hb.payslip.worked_days) | -- | --             | Work-entry data consumed by rules.                           |
| input_ids               | One2many(hb.payslip.input) | --     | --                | Ad-hoc inputs consumed by rules.                             |
| gross_amount            | Float(16,0)              | --       | computed/stored   | Stored compute: reads `tong_thu_nhap` line amount.           |
| net_amount              | Float(16,0)              | --       | computed/stored   | Stored compute: reads `thuc_lanh` line amount.               |
| x_teaching_computed     | Boolean                  | --       | False             | Set to True after successful computation.                    |
| x_compute_warnings      | Text                     | --       | --                | Newline-joined warning messages from rule errors.            |

### 3.2 hb.salary.rule -- Rule Definition Fields

| Field                    | Type         | Required | Default   | Description                                                           |
|------------------------- |------------- |--------- |---------- |---------------------------------------------------------------------- |
| name                     | Char         | Yes      | --        | Human-readable rule name.                                             |
| code                     | Char         | Yes      | --        | Unique slug code used as key in `rules` dict.                         |
| sequence                 | Integer      | Yes      | 10        | Execution order. Lower runs first.                                    |
| structure_id             | Many2one     | Yes      | --        | Parent salary structure.                                              |
| category_id              | Many2one     | Yes      | --        | Salary rule category for grouping and `categories` accumulator.       |
| active                   | Boolean      | --       | True      | Inactive rules are excluded from computation.                         |
| amount_type              | Selection    | Yes      | `'fixed'` | One of: `fixed`, `percentage`, `formula`, `code`.                     |
| amount_python_compute    | Text         | No       | --        | Python code for `code` type. Must assign to `result`.                 |
| amount_formula           | Text         | No       | --        | Excel-like formula for `formula` type. Transpiled by `_transpile_formula`. |
| amount_fixed             | Float(16,0)  | No       | --        | Fixed monetary amount for `fixed` type.                               |
| amount_percentage        | Float(8,4)   | No       | --        | Percentage value for `percentage` type.                               |
| amount_percentage_base   | Char         | No       | --        | Python expression returning the base value for percentage computation.|
| condition_type           | Selection    | --       | `'none'`  | Values: `none` (always true), `python` (evaluate expression).         |
| condition_python         | Text         | No       | --        | Python boolean expression for `python` condition type.                |
| appears_on_payslip       | Boolean      | --       | True      | If False, the rule computes but does not create a payslip line.       |

---

## 4. SUPPORTING MODELS AND PROXY CLASSES

### 4.1 hb.payslip.line (ORM Model)

| Field         | Type                            | Required | Default | Description                                             |
|-------------- |-------------------------------- |--------- |-------- |-------------------------------------------------------- |
| payslip_id    | Many2one(hb.payslip)            | Yes      | --      | Parent payslip. Cascade delete.                         |
| rule_id       | Many2one(hb.salary.rule)        | No       | --      | Source salary rule. Set null on rule deletion.           |
| category_id   | Many2one(hb.salary.rule.category)| No      | --      | Category from the source rule. Set null on deletion.    |
| code          | Char                            | Yes      | --      | Rule code copied at creation time.                      |
| name          | Char                            | Yes      | --      | Rule name copied at creation time.                      |
| sequence      | Integer                         | --       | 10      | Display/sort order copied from the rule.                |
| quantity      | Float(10,2)                     | --       | 1.0     | Quantity component from rule evaluation.                 |
| rate          | Float(16,0)                     | --       | --      | Rate component from rule evaluation.                    |
| amount        | Float(16,0)                     | --       | --      | `round(amount)` -- the primary computed monetary value. |

**Order**: `sequence, id`.

### 4.2 hb.payslip.worked_days (ORM Model)

| Field           | Type                 | Required | Default | Description                                 |
|---------------- |--------------------- |--------- |-------- |-------------------------------------------- |
| payslip_id      | Many2one(hb.payslip) | Yes      | --      | Parent payslip. Cascade delete.             |
| name            | Char                 | Yes      | --      | Descriptive label (e.g., "Normal Working Days"). |
| code            | Char                 | Yes      | --      | Lookup code (e.g., `WORK100`).              |
| sequence        | Integer              | --       | 10      | Display order.                              |
| number_of_days  | Float(8,2)           | --       | --      | Number of worked days in the period.        |
| number_of_hours | Float(8,2)           | --       | --      | Number of worked hours in the period.       |

**Order**: `sequence, id`.

### 4.3 hb.payslip.input (ORM Model)

| Field        | Type                 | Required | Default | Description                                       |
|------------- |--------------------- |--------- |-------- |-------------------------------------------------- |
| payslip_id   | Many2one(hb.payslip) | Yes      | --      | Parent payslip. Cascade delete.                   |
| name         | Char                 | Yes      | --      | Descriptive label (e.g., "Advance Payment").      |
| code         | Char                 | Yes      | --      | Lookup code (e.g., `ADVANCE`, `XANG_XE`).         |
| sequence     | Integer              | --       | 10      | Display order.                                    |
| amount       | Float(16,0)          | --       | --      | Monetary value of the input.                      |

**Order**: `sequence, id`.

### 4.4 _EmptyRecord (Python Class -- Module Level)

| Aspect        | Detail                                                                                       |
|-------------- |--------------------------------------------------------------------------------------------- |
| Type          | Plain Python class (not ORM model)                                                           |
| Purpose       | Fallback object returned by `WorkedDaysProxy` and `InputsProxy` when a code is not found.    |
| Attributes    | `number_of_days = 0.0`, `number_of_hours = 0.0`, `amount = 0.0`                             |
| Boolean       | `__bool__` returns `False`. Allows `if inputs.ADVANCE:` guard patterns in rule code.         |
| Instantiation | Created on-the-fly via `_EmptyRecord()` inside proxy `__getattr__`.                          |

### 4.5 WorkedDaysProxy (Python Class -- Module Level)

| Aspect          | Detail                                                                                                          |
|---------------- |---------------------------------------------------------------------------------------------------------------- |
| Type            | Plain Python class (not ORM model)                                                                              |
| Constructor     | `WorkedDaysProxy(records)` -- takes `hb.payslip.worked_days` recordset, builds internal `_data` dict keyed by `code`. |
| Attribute access| `__getattr__(code)` returns the `hb.payslip.worked_days` record matching `code`, or `_EmptyRecord()` if missing.|
| Membership test | `__contains__(code)` returns `True` if `code` exists in `_data`.                                               |
| Usage in rules  | `worked_days.WORK100.number_of_days` returns the number of worked days for code `WORK100`.                      |

### 4.6 InputsProxy (Python Class -- Module Level)

| Aspect          | Detail                                                                                                           |
|---------------- |----------------------------------------------------------------------------------------------------------------- |
| Type            | Plain Python class (not ORM model)                                                                               |
| Constructor     | `InputsProxy(records)` -- takes `hb.payslip.input` recordset, builds internal `_data` dict keyed by `code`.      |
| Attribute access| `__getattr__(code)` returns the `hb.payslip.input` record matching `code`, or `_EmptyRecord()` if missing.       |
| Membership test | `__contains__(code)` returns `True` if `code` exists in `_data`.                                                |
| Usage in rules  | `inputs.ADVANCE.amount` returns the amount for input code `ADVANCE`. `inputs.XANG_XE.amount` for fuel allowance. |

### 4.7 CategoryTotals (Python Class -- Module Level)

| Aspect          | Detail                                                                                                       |
|---------------- |------------------------------------------------------------------------------------------------------------- |
| Type            | Plain Python class (not ORM model)                                                                           |
| Constructor     | `CategoryTotals()` -- initializes empty `_totals` dict.                                                      |
| accumulate()    | `accumulate(code, amount)` adds `amount` to the running total for category `code`.                           |
| Attribute access| `__getattr__(code)` returns the current total for category `code`, or `0.0` if not yet accumulated.          |
| Usage in rules  | `categories.phu_cap` returns sum of all rule amounts in category `phu_cap`. Called after each rule evaluation.|

---

## 5. BUSINESS RULES

| ID         | Rule                                                                                                                                                                  |
|----------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BR-PAY-030 | The system must reject computation if the payslip state is not `draft` or `verify`. `_ensure_draft_state()` raises `UserError` for states `done` and `cancel`.        |
| BR-PAY-031 | The system must resolve exactly one active contract (`state = 'open'`) overlapping the payslip date range `[date_from, date_to]`. `_resolve_contract()` raises `ValidationError` if none is found. |
| BR-PAY-031A | Batch computation SHALL resolve salary rules per payslip structure; it SHALL NOT combine rules from `STRUCT_OFFLINE` and `STRUCT_ONLINE` in one evaluation. |
| BR-PAY-032 | Structure resolution follows a strict priority: (1) explicit `payslip.structure_id`, (2) `contract.x_structure_id`, (3) auto-detect from `employee.x_work_form` (`'online'` maps to `STRUCT_ONLINE`, all others map to `STRUCT_OFFLINE`). `_resolve_structure()` raises `ValidationError` if no structure is resolved. |
| BR-PAY-033 | All existing payslip lines (`line_ids`) must be deleted (`unlink()`) before recomputation. The engine always produces a fresh, complete set of lines.                  |
| BR-PAY-034 | Salary rules are evaluated strictly in ascending `sequence` order. A rule may reference any previously computed rule's result via `rules.get('code', 0)` or the `categories` accumulator. Forward references are not supported. |
| BR-PAY-035 | A rule with `condition_type = 'none'` or empty `condition_python` always evaluates. A rule with `condition_type = 'python'` evaluates only if `safe_eval(condition_python, localdict)` returns a truthy value. |
| BR-PAY-036 | The four amount computation modes must behave as follows: (a) `code` -- executes `amount_python_compute` via `safe_eval` in `exec` mode; reads `result`, `result_qty`, `result_rate` from the namespace. (b) `fixed` -- returns `amount_fixed` directly. (c) `percentage` -- evaluates `amount_percentage_base` to get a base, multiplies by `amount_percentage / 100`, rounds the result. (d) `formula` -- transpiles via `_transpile_formula()` then evaluates the resulting Python expression. |
| BR-PAY-037 | If a rule evaluation raises any exception, the engine must not abort. It logs a warning, appends a user-visible message to `x_compute_warnings`, and defaults the failed rule to `(amount=0.0, qty=1.0, rate=0.0)`. Subsequent rules continue to execute. |
| BR-PAY-038 | A payslip line is created only when `rule.appears_on_payslip` is `True`. Rules with `appears_on_payslip = False` still compute and store their result in `localdict['rules']` and `categories`, but produce no visible line. |
| BR-PAY-039 | The `_hocba_pit(taxable_income)` method must implement the 7-bracket Vietnam progressive PIT table exactly as defined in `PIT_BRACKETS`. The result must be rounded to the nearest integer. If `taxable_income <= 0`, the method returns `0.0`. |
| BR-PAY-040 | WHEN HR selects a payroll month, THE payroll list SHALL include only employees whose open contract overlaps that calendar month. Contract boundaries SHALL be evaluated against the inclusive last day of the selected month; an employee whose contract starts on the first day of the following month SHALL NOT appear. |
| BR-PAY-041 | WHEN HR starts batch computation for a selected month, THE system SHALL compute only draft/verify payslips belonging to the same valid-contract employee set returned by the payroll list for that month. Stale payslips for employees outside that set SHALL NOT be recomputed. |

---

## 6. SEED DATA -- SALARY RULES

### 6.1 Salary Rule Categories

| XML ID            | Code              | Name            | Sequence |
|------------------ |------------------ |---------------- |--------- |
| rule_categ_alw    | phu_cap           | Phu cap         | 10       |
| rule_categ_bonus  | thuong            | Thuong          | 20       |
| rule_categ_gross  | tong_thu_nhap     | Tong thu nhap   | 30       |
| rule_categ_deduct | giam_tru          | Giam tru        | 40       |
| rule_categ_ded    | khau_tru_nv       | BH nhan vien    | 50       |
| rule_categ_tax    | thue_tncn         | Thue TNCN       | 60       |
| rule_categ_net    | thuc_lanh         | Thuc lanh       | 70       |
| rule_categ_comp   | bh_phan_cong_ty   | BH phan cong ty | 80       |

### 6.2 STRUCT_OFFLINE Rules (19 active rules)

| Seq | Code            | Name                    | amount_type | Category        | Computation Summary                                                              |
|---- |---------------- |------------------------ |------------ |---------------- |--------------------------------------------------------------------------------- |
| 10  | an_ca           | An ca                   | code        | phu_cap         | `round(50000 * NCTT)` where NCTT = `worked_days.WORK100.number_of_days`          |
| 11  | xang_xe         | Xang xe                 | code        | phu_cap         | `inputs.XANG_XE.amount` or `contract.x_pc_fuel`                                 |
| 12  | dien_thoai      | Dien thoai              | code        | phu_cap         | `inputs.DIEN_THOAI.amount` or `contract.x_sp_phone`                             |
| 13  | thuong_khac     | Thuong khac             | code        | thuong          | `inputs.THUONG_KHAC.amount or 0.0`                                               |
| 14  | ho_tro_nuoi_con | Ho tro nuoi con nho     | code        | phu_cap         | `inputs.HO_TRO_NUOI_CON.amount or 0.0`                                          |
| 20  | tong_thu_nhap   | Tong thu nhap           | code        | tong_thu_nhap   | `round((an_ca + xang_xe + dien_thoai + wage) / 25 * NCTT)`                      |
| 21  | tn_mien_thue    | Thu nhap mien thue TNCN | code        | tong_thu_nhap   | `inputs.TN_MIEN_THUE.amount` or default `730000`                                |
| 22  | tn_truoc_thue   | Tong TN truoc thue      | code        | tong_thu_nhap   | `tong_thu_nhap - tn_mien_thue`                                                  |
| 30  | npt             | NPT                     | code        | giam_tru        | `inputs.NPT.amount` or `contract.x_dependent_count`                             |
| 31  | giam_tru        | So tien giam tru        | code        | giam_tru        | `15,500,000 + int(npt) * 6,200,000`                                             |
| 40  | bhxh_8_nv       | BHXH (8%)               | code        | khau_tru_nv     | `round(wage * 0.08)`                                                             |
| 41  | bhyt_1_5_nv     | BHYT (1.5%)             | code        | khau_tru_nv     | `round(wage * 0.015)`                                                            |
| 42  | bhtn_1_nv       | BHTN (1%)               | code        | khau_tru_nv     | `round(wage * 0.01)`                                                             |
| 50  | tn_tinh_thue    | Tong TN tinh thue       | code        | thue_tncn       | `max(0, tn_truoc_thue - giam_tru - bhxh_8_nv - bhyt_1_5_nv - bhtn_1_nv)`       |
| 60  | thue_tncn       | Thue TNCN               | code        | thue_tncn       | 5-bracket progressive PIT on `tn_tinh_thue`                                     |
| 70  | thuc_lanh       | Tong luong thuc linh    | code        | thuc_lanh       | `round(tong_thu_nhap - bhxh_8_nv - bhyt_1_5_nv - bhtn_1_nv - thue_tncn)`       |
| 80  | bhxh_17_5_ct    | BHXH (17.5%) CT         | code        | bh_phan_cong_ty | `round(wage * 0.175)` -- company portion                                        |
| 81  | bhyt_3_ct       | BHYT (3%) CT            | code        | bh_phan_cong_ty | `round(wage * 0.03)` -- company portion                                         |
| 82  | bhtn_1_ct       | BHTN (1%) CT            | code        | bh_phan_cong_ty | `round(wage * 0.01)` -- company portion                                         |

### 6.3 STRUCT_ONLINE Rules (5 active rules)

| Seq | Code             | Name                | amount_type | Category        | Computation Summary                                          |
|---- |----------------- |-------------------- |------------ |---------------- |------------------------------------------------------------- |
| 10  | luong            | Luong               | code        | phu_cap         | `inputs.WAGE_ONLINE.amount or contract.wage`                 |
| 40  | thuong           | Thuong              | code        | thuong          | `inputs.BONUS_OTHER.amount or 0.0`                           |
| 50  | tong_thu_nhap    | TONG THU NHAP       | code        | tong_thu_nhap   | `categories.phu_cap + categories.thuong`                     |
| 90  | tam_ung_tru_khac | Tam ung, tru khac   | code        | khau_tru_nv     | `-(inputs.ADVANCE.amount or 0.0)`                            |
| 99  | thuc_lanh        | THUC LINH           | code        | thuc_lanh       | `categories.tong_thu_nhap + categories.khau_tru_nv`          |

---

---

## 7. HIGH-SCALE ASYNC BATCH ENGINE & PROGRESS POLLING (1,000+ EMPLOYEES)

| Requirement | Detail |
|------------ |--------------------------------------------------------------------------------------------------------- |
| **Async Execution** | `POST /hocba-hrm/api/payroll/compute-all` MUST launch a daemon background worker thread and return HTTP 200 in **< 100ms** to prevent socket/Gunicorn timeouts. |
| **Chunked DB Transactions** | Background worker MUST process payslips in chunks of 50-100 records and execute `cr.commit()` per chunk to prevent long locks and cloud DB (`cursor already closed`) errors. |
| **Progress Polling** | `GET /hocba-hrm/api/payroll/compute-status` MUST provide real-time progress updates (`computed`, `total`, `percent`, `status`). |
| **UI Progress Bar** | Frontend SPA MUST poll status every 1.5s and display an animated real-time progress bar when `status === 'processing'`. |
| **High Scalability** | Supports 1,000 to 50,000+ employees without browser timeout, socket disconnect, or `Failed to fetch` errors. |

---

- **v2.1 (2026-08-07)**: Refactored batch salary engine (`action_compute_batch` and `compute-all`) to iteratively invoke the single-employee computation engine (`action_compute_sheet`), eliminating ThreadPoolExecutor thread-safety issues and bulk prefetch cache divergence for 100% calculation consistency.
- **v2.2 (2026-08-25)**: Aligned payroll-list and batch-compute employee scope. Month boundaries now exclude contracts starting on the first day of the following month, and stale out-of-period payslips are excluded from batch computation.
- **v2.0 (2026-08-06)**: Upgraded to Async Job Queue & Chunked DB Transaction Architecture with real-time progress polling for 1,000+ employee scalability.
- **v1.1 (2026-08-06)**: Integrated `action_compute_batch` high-performance engine for batch salary computation (`/hocba-hrm/api/payroll/compute-all`), eliminated N+1 queries in summary endpoints, and added confirmation reset logic.

*End of FS-PAY-002 v2.1*

