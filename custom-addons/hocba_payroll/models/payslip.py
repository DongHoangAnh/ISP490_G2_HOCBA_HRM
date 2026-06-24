"""
Payslip — standalone payroll engine with data-driven salary rules.

Design:
    - Rule Engine: action_compute_sheet() sorts rules in topological dependency
      order, then evaluates each with a safe AST tree-walking evaluator.
    - No eval() / exec() for formula-type rules — pure AST tree-walking.
    - Proxy classes provide convenient attribute access in rule code.
    - Backward compatible: teaching work-entry methods kept for teacher structures.
"""
import ast as _ast
import logging
import re as _re
import uuid
from collections import deque

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval  # still used for 'code' and condition_python types

_logger = logging.getLogger(__name__)

# ── Vietnam PIT 7-bracket progressive table (2026) ─────────────────────────────
PIT_BRACKETS = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (float('inf'), 0.35),
]


# ── Lookup source registry (whitelist) ─────────────────────────────────────────
# Each entry maps a source key to model, date/employee fields, and aggregatable
# fields.  Only sources listed here can be queried by "lookup" salary rules —
# this is the security boundary.
LOOKUP_SOURCES = {
    'attendance': {
        'model': 'hocba.attendance',
        'label': 'Chấm công',
        'employee_field': 'employee_id',
        'date_field': 'date',
        'fields': {
            'work_credit':         {'label': 'Số công (0/0.5/1.0)', 'agg': 'sum'},
            'working_hours':       {'label': 'Giờ làm việc',        'agg': 'sum'},
            'late_minutes':        {'label': 'Phút đi trễ',         'agg': 'sum'},
            'early_leave_minutes': {'label': 'Phút về sớm',         'agg': 'sum'},
            'morning_credit':      {'label': 'Công sáng',           'agg': 'sum'},
            'afternoon_credit':    {'label': 'Công chiều',          'agg': 'sum'},
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — Safe AST formula evaluator
#
# Replaces the _transpile_formula + safe_eval chain for the 'formula' rule type.
# No eval() / exec() is invoked at runtime — pure AST tree-walking.
# ══════════════════════════════════════════════════════════════════════════════

def _eval_ast_node(node, localdict):
    """
    Recursively evaluate an AST expression node against *localdict*.

    localdict is the full evaluation namespace produced by _build_localdict().
    Rule codes are resolved from localdict['rules'] (accumulated amounts);
    other identifiers (employee, contract, max, min, …) fall through to the
    top-level localdict.

    Supported constructs
    ────────────────────
    Constant             — numeric / string / bool literals
    Name                 — rule-code lookup, localdict lookup, True / False
    Attribute            — getattr(obj, attr) for Odoo records in localdict
    UnaryOp              — -  +  not
    BinOp                — +  -  *  /  //  %  **
    BoolOp               — and / or  (short-circuit)
    Compare              — ==  !=  <  <=  >  >=
    IfExp                — value  if  cond  else  other
    Call (special)       — IF()  SUM()  MAX()  MIN()  ABS()  ROUND()  INT()  FLOAT()
    Call (localdict)     — any callable present in localdict (e.g. _range_sum)
    Call (method)        — obj.method(args)  on objects in localdict
    Subscript            — obj[key]
    """
    # ── Literal constant ──────────────────────────────────────────────────────
    if isinstance(node, _ast.Constant):
        return node.value

    # ── Identifier lookup ─────────────────────────────────────────────────────
    if isinstance(node, _ast.Name):
        n = node.id
        if n == 'True':  return True
        if n == 'False': return False
        # Rule codes take priority (accumulated amounts dict)
        rules_amounts = localdict.get('rules')
        if rules_amounts is not None and n in rules_amounts:
            return rules_amounts[n]
        # Fall through to full localdict (employee, contract, max, min, …)
        if n in localdict:
            return localdict[n]
        # Unknown identifier → 0 (rule not yet evaluated or doesn't exist)
        return 0

    # ── Attribute access: employee.x_field, contract.wage, … ─────────────────
    if isinstance(node, _ast.Attribute):
        obj = _eval_ast_node(node.value, localdict)
        return getattr(obj, node.attr, 0)

    # ── Unary operators ───────────────────────────────────────────────────────
    if isinstance(node, _ast.UnaryOp):
        operand = _eval_ast_node(node.operand, localdict)
        op = type(node.op)
        if op is _ast.USub:   return -operand
        if op is _ast.UAdd:   return +operand
        if op is _ast.Not:    return not operand
        if op is _ast.Invert: return ~int(operand)
        raise ValueError(f'Unsupported unary operator: {op.__name__}')

    # ── Binary operators ──────────────────────────────────────────────────────
    if isinstance(node, _ast.BinOp):
        left  = _eval_ast_node(node.left,  localdict)
        right = _eval_ast_node(node.right, localdict)
        op = type(node.op)
        if op is _ast.Add:      return left + right
        if op is _ast.Sub:      return left - right
        if op is _ast.Mult:     return left * right
        if op is _ast.Div:      return (left / right) if right else 0
        if op is _ast.FloorDiv: return (left // right) if right else 0
        if op is _ast.Mod:      return (left % right)  if right else 0
        if op is _ast.Pow:      return left ** right
        raise ValueError(f'Unsupported binary operator: {op.__name__}')

    # ── Boolean operators (short-circuit) ─────────────────────────────────────
    if isinstance(node, _ast.BoolOp):
        if isinstance(node.op, _ast.And):
            result = True
            for v in node.values:
                result = result and _eval_ast_node(v, localdict)
                if not result:
                    return result
            return result
        if isinstance(node.op, _ast.Or):
            result = False
            for v in node.values:
                result = result or _eval_ast_node(v, localdict)
                if result:
                    return result
            return result

    # ── Comparisons ───────────────────────────────────────────────────────────
    if isinstance(node, _ast.Compare):
        left = _eval_ast_node(node.left, localdict)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval_ast_node(comp, localdict)
            op_t = type(op)
            if op_t is _ast.Eq:    ok = (left == right)
            elif op_t is _ast.NotEq: ok = (left != right)
            elif op_t is _ast.Lt:  ok = (left <  right)
            elif op_t is _ast.LtE: ok = (left <= right)
            elif op_t is _ast.Gt:  ok = (left >  right)
            elif op_t is _ast.GtE: ok = (left >= right)
            else: raise ValueError(f'Unsupported compare op: {type(op).__name__}')
            if not ok:
                return False
            left = right
        return True

    # ── Ternary (Python if-expression) ────────────────────────────────────────
    if isinstance(node, _ast.IfExp):
        test = _eval_ast_node(node.test, localdict)
        return _eval_ast_node(node.body if test else node.orelse, localdict)

    # ── Function / method calls ───────────────────────────────────────────────
    if isinstance(node, _ast.Call):
        if node.keywords:
            raise ValueError('Keyword arguments are not supported in formula expressions')

        # ── Method call: obj.method(args) ─────────────────────────────────
        if isinstance(node.func, _ast.Attribute):
            obj    = _eval_ast_node(node.func.value, localdict)
            method = getattr(obj, node.func.attr, None)
            if not callable(method):
                raise ValueError(f'Attribute {node.func.attr!r} is not callable')
            evaled = [_eval_ast_node(a, localdict) for a in node.args]
            return method(*evaled)

        # ── Named function call ────────────────────────────────────────────
        if not isinstance(node.func, _ast.Name):
            raise ValueError('Only simple function calls are supported in formulas')
        fname_orig  = node.func.id
        fname_upper = fname_orig.upper()
        args = node.args

        # IF(cond, true_val, false_val) — short-circuit evaluation
        if fname_upper == 'IF':
            if len(args) != 3:
                raise ValueError('IF(cond, true_val, false_val) requires exactly 3 arguments')
            cond = _eval_ast_node(args[0], localdict)
            return _eval_ast_node(args[1] if cond else args[2], localdict)

        # SUM(start_code, end_code) — range sum via _range_sum helper
        # Args are rule-code identifiers (Name nodes), NOT numeric lookups.
        # Extract .id directly so 'an_ca' stays as the string "an_ca".
        if fname_upper == 'SUM':
            if len(args) != 2:
                raise ValueError('SUM(start_code, end_code) requires exactly 2 arguments')
            def _code_str(a):
                if isinstance(a, _ast.Name):     return a.id
                if isinstance(a, _ast.Constant): return str(a.value)
                return str(_eval_ast_node(a, localdict))
            fn = localdict.get('_range_sum')
            return fn(_code_str(args[0]), _code_str(args[1])) if fn else 0

        # MAX / MIN — variadic
        if fname_upper in ('MAX', 'MIN'):
            if not args:
                raise ValueError(f'{fname_upper}() requires at least 1 argument')
            vals = [_eval_ast_node(a, localdict) for a in args]
            return max(vals) if fname_upper == 'MAX' else min(vals)

        # ABS
        if fname_upper == 'ABS':
            if len(args) != 1:
                raise ValueError('ABS() requires exactly 1 argument')
            return abs(_eval_ast_node(args[0], localdict))

        # ROUND(value[, direction])  direction: 1=ceil, 0=floor
        if fname_upper == 'ROUND':
            if len(args) not in (1, 2):
                raise ValueError('ROUND(value[, direction]) requires 1 or 2 arguments')
            val       = _eval_ast_node(args[0], localdict)
            direction = _eval_ast_node(args[1], localdict) if len(args) == 2 else 0
            fn = localdict.get('_round_dir')
            return fn(val, direction) if fn else int(round(val))

        # INT / FLOAT casts
        if fname_upper == 'INT':
            if len(args) != 1:
                raise ValueError('INT() requires exactly 1 argument')
            return int(_eval_ast_node(args[0], localdict))
        if fname_upper == 'FLOAT':
            if len(args) != 1:
                raise ValueError('FLOAT() requires exactly 1 argument')
            return float(_eval_ast_node(args[0], localdict))

        # Fall through: call any callable in localdict (e.g. _range_sum directly)
        fn = localdict.get(fname_orig)
        if callable(fn):
            evaled = [_eval_ast_node(a, localdict) for a in args]
            return fn(*evaled)

        raise ValueError(f'Unknown function in formula: {fname_orig!r}')

    # ── Subscript: dict['key'] or list[idx] ──────────────────────────────────
    if isinstance(node, _ast.Subscript):
        obj        = _eval_ast_node(node.value, localdict)
        slice_node = node.slice
        # Python 3.8 wraps the slice in an Index node
        if isinstance(slice_node, _ast.Index):
            slice_node = slice_node.value  # type: ignore[attr-defined]
        key = _eval_ast_node(slice_node, localdict)
        try:
            return obj[key]
        except (KeyError, IndexError, TypeError):
            return 0

    raise ValueError(f'Unsupported expression node: {type(node).__name__}')


def _eval_formula_expr(formula, localdict):
    """
    Parse *formula* as a Python expression and evaluate it via AST tree-walking.

    No eval() / exec() is invoked — completely safe for admin-authored formulas.

    Formula syntax (Excel-like, also valid Python):
        luong_thoi_gian * 0.08
        IF(an_ca > 20, 100_000, 50_000)
        SUM(luong_co_ban, phu_cap)          ← sums all rules between the two codes
        MAX(luong_co_ban, 3_000_000)
        ROUND(value, 1)                     ← 1 = ceil, 0 = floor
        employee.x_base_salary * 0.1        ← attribute access on Odoo records

    Returns a numeric value (int or float).
    Raises ValueError on syntax error or unsupported construct.
    """
    src = (formula or '').strip()
    if not src:
        return 0
    try:
        tree = _ast.parse(src, mode='eval')
    except SyntaxError as exc:
        raise ValueError(f'Formula syntax error in {src!r}: {exc}') from exc
    return _eval_ast_node(tree.body, localdict)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — Dependency extraction + topological sort for salary rules
#
# Rules are sorted so that if rule B's formula references rule A's code,
# A is always evaluated before B — regardless of sequence numbers.
# ══════════════════════════════════════════════════════════════════════════════

def _extract_rule_deps(rule, all_codes):
    """
    Return the set of rule codes that *rule* depends on.

    Scans the rule's formula/code/condition text for identifiers that match
    known rule codes (all_codes).  Only codes other than the rule's own code
    are returned as dependencies.
    """
    deps  = set()
    texts = []
    if rule.amount_type == 'formula' and rule.amount_formula:
        texts.append(rule.amount_formula)
    elif rule.amount_type == 'code' and rule.amount_python_compute:
        texts.append(rule.amount_python_compute)
    elif rule.amount_type == 'percentage' and rule.amount_percentage_base:
        texts.append(rule.amount_percentage_base)
    if rule.condition_type == 'python' and rule.condition_python:
        texts.append(rule.condition_python)
    for text in texts:
        for m in _re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', text):
            token = m.group(1)
            if token in all_codes and token != rule.code:
                deps.add(token)
    return deps


def _topo_sort_rules(rules):
    """
    Sort salary rules in dependency evaluation order using Kahn's algorithm.

    If rule B's formula references rule A, A will appear before B in the
    returned list — regardless of sequence numbers.  Within the same
    dependency "level", sequence number is used as a tiebreaker (ascending).

    Raises UserError if a circular dependency is detected (cycle in the DAG).
    Returns a Python list of rule records in safe evaluation order.
    """
    rules_list = list(rules)
    if not rules_list:
        return rules_list

    all_codes = {r.code for r in rules_list}
    by_code   = {r.code: r for r in rules_list}

    # Build forward and reverse adjacency maps
    deps  = {r.code: _extract_rule_deps(r, all_codes) for r in rules_list}
    rdeps = {r.code: set() for r in rules_list}          # who depends on me?
    for code, dep_set in deps.items():
        for dep_code in dep_set:
            if dep_code in rdeps:
                rdeps[dep_code].add(code)

    in_deg = {r.code: len(deps[r.code]) for r in rules_list}

    # Start with all rules that have no dependencies, sorted by sequence
    queue = deque(sorted(
        (code for code, deg in in_deg.items() if deg == 0),
        key=lambda c: by_code[c].sequence,
    ))

    result = []
    while queue:
        code = queue.popleft()
        result.append(by_code[code])
        # Decrease in-degree for all rules that depend on this one
        for rdep_code in sorted(rdeps.get(code, set()), key=lambda c: by_code[c].sequence):
            in_deg[rdep_code] -= 1
            if in_deg[rdep_code] == 0:
                queue.append(rdep_code)

    if len(result) != len(rules_list):
        # Not all nodes processed → cycle exists
        cycle = sorted(c for c, d in in_deg.items() if d > 0)
        raise UserError(_(
            'Phát hiện phụ thuộc vòng tròn trong quy tắc lương: %(codes)s. '
            'Vui lòng kiểm tra lại công thức của các quy tắc này.',
            codes=', '.join(cycle),
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Proxy classes for rule evaluation
# ═══════════════════════════════════════════════════════════════════════════════

class _EmptyRecord:
    """Fallback when a code is not found."""
    number_of_days = 0.0
    number_of_hours = 0.0
    amount = 0.0

    def __bool__(self):
        return False


class WorkedDaysProxy:
    """Allow ``worked_days.WORK100.number_of_days`` syntax."""

    def __init__(self, records):
        self._data = {}
        for rec in records:
            self._data[rec.code] = rec

    def __getattr__(self, code):
        if code.startswith('_'):
            raise AttributeError(code)
        return self._data.get(code, _EmptyRecord())

    def __contains__(self, code):
        return code in self._data


class InputsProxy:
    """Allow ``inputs.ADVANCE.amount`` syntax."""

    def __init__(self, records):
        self._data = {}
        for rec in records:
            self._data[rec.code] = rec

    def __getattr__(self, code):
        if code.startswith('_'):
            raise AttributeError(code)
        return self._data.get(code, _EmptyRecord())

    def __contains__(self, code):
        return code in self._data


class CategoryTotals:
    """Accumulates category running totals during rule evaluation."""

    def __init__(self):
        self._totals = {}

    def __getattr__(self, code):
        if code.startswith('_'):
            raise AttributeError(code)
        return self._totals.get(code, 0.0)

    def accumulate(self, code, amount):
        self._totals[code] = self._totals.get(code, 0.0) + amount


# ═══════════════════════════════════════════════════════════════════════════════
# Model
# ═══════════════════════════════════════════════════════════════════════════════

class HbPayslip(models.Model):
    _name = 'hb.payslip'
    _description = 'Phiếu lương'
    _order = 'number desc'
    _inherit = ['mail.thread']

    # ── Core fields ─────────────────────────────────────────────────────────
    name = fields.Char(string='Tên', compute='_compute_name', store=True)
    number = fields.Char(
        string='Mã phiếu', readonly=True, copy=False,
        default=lambda self: _('Mới'),
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        index=True, ondelete='restrict',
    )
    contract_id = fields.Many2one(
        'hb.contract', string='Hợp đồng',
    )
    structure_id = fields.Many2one(
        'hb.salary.structure', string='Cấu trúc lương',
    )
    payslip_run_id = fields.Many2one(
        'hb.payslip.run', string='Batch', index=True, ondelete='cascade',
    )
    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('verify', 'Chờ xác nhận'),
        ('done', 'Hoàn tất'),
        ('cancel', 'Đã hủy'),
    ], string='Trạng thái', default='draft', tracking=True, index=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company,
    )

    # ── Payslip details ──────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'hb.payslip.line', 'payslip_id', string='Chi tiết lương',
    )
    worked_days_ids = fields.One2many(
        'hb.payslip.worked_days', 'payslip_id', string='Công',
    )
    input_ids = fields.One2many(
        'hb.payslip.input', 'payslip_id', string='Đầu vào',
    )

    # ── Computed status fields ───────────────────────────────────────────────
    x_compute_warnings = fields.Text(
        string='Cảnh báo tính lương', readonly=True,
    )
    x_teaching_computed = fields.Boolean(
        string='Đã tính', default=False, readonly=True,
    )

    # ── Employee confirmation ────────────────────────────────────────────────
    x_access_token = fields.Char(
        string='Access Token', copy=False, index=True,
        default=lambda self: str(uuid.uuid4()),
    )
    x_employee_confirm = fields.Selection([
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('rejected', 'Từ chối'),
    ], string='NV xác nhận', default='pending', tracking=True)
    x_employee_feedback = fields.Text(string='Phản hồi nhân viên')
    x_email_sent = fields.Boolean(string='Đã gửi mail', default=False)
    x_email_sent_date = fields.Datetime(string='Ngày gửi mail')
    x_confirmed_date = fields.Datetime(string='Ngày xác nhận')

    # ── Aggregated amounts ───────────────────────────────────────────────────
    gross_amount = fields.Float(
        string='Gross', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )
    net_amount = fields.Float(
        string='Net (Thực lĩnh)', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )

    # ── Computed & lifecycle ─────────────────────────────────────────────────
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_name(self):
        for rec in self:
            emp    = rec.employee_id.name or ''
            period = rec.date_from.strftime('%m/%Y') if rec.date_from else ''
            rec.name = f'Lương {emp} — {period}' if emp else 'Phiếu lương mới'

    @api.depends('line_ids.amount', 'line_ids.code')
    def _compute_amounts(self):
        for rec in self:
            # Single pass — avoid 2× filtered() O(2V)
            amounts = {
                l.code: l.amount for l in rec.line_ids
                if l.code in ('tong_thu_nhap', 'thuc_lanh')
            }
            rec.gross_amount = amounts.get('tong_thu_nhap', 0)
            rec.net_amount   = amounts.get('thuc_lanh', 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('Mới')) == _('Mới'):
                vals['number'] = self.env['ir.sequence'].next_by_code('hb.payslip') or '/'
            if not vals.get('x_access_token'):
                vals['x_access_token'] = str(uuid.uuid4())
        return super().create(vals_list)

    # ═════════════════════════════════════════════════════════════════════════
    # RULE-BASED SALARY ENGINE
    # ═════════════════════════════════════════════════════════════════════════

    def action_compute_sheet(self, prefetched_rules=None):
        """Main entry — compute salary using data-driven rules.

        prefetched_rules: recordset hb.salary.rule already loaded (optional).
            When supplied, skip per-slip structure/rules resolution — used when
            all employees share one rule set (batch compute).
            If None: resolve per-slip as before (single slip or multi-structure).

        Phase 2: rules are topologically sorted (dependency order) once per
        call for batch mode, or per-slip for single mode.
        """
        # ── Pre-sort rules once when in batch mode ────────────────────────
        # _presorted_rules is reused for every slip in the recordset.
        _presorted_rules = None
        if prefetched_rules is not None:
            try:
                _presorted_rules = _topo_sort_rules(prefetched_rules)
            except UserError:
                _logger.warning(
                    'Topo sort detected cycle in salary rules — '
                    'falling back to sequence order for batch.',
                )
                _presorted_rules = list(prefetched_rules)

        for slip in self:
            slip._ensure_draft_state()
            contract = slip._resolve_contract()

            # Clear old lines
            slip.line_ids.unlink()

            # Build evaluation namespace
            localdict   = slip._build_localdict(contract)
            _rules_order = localdict['_rules_order']
            _rules_pos   = localdict['_rules_pos']

            # ── Resolve & topo-sort rules ─────────────────────────────────
            warnings = []
            if _presorted_rules is not None:
                rules     = _presorted_rules
                structure = False
            else:
                structure = slip._resolve_structure(contract)
                if structure:
                    raw_rules = structure.rule_ids.filtered('active').sorted('sequence')
                else:
                    raw_rules = self.env['hb.salary.rule']
                if not raw_rules:
                    raw_rules = self.env['hb.salary.rule'].search(
                        [('active', '=', True)], order='sequence, id',
                    )
                try:
                    rules = _topo_sort_rules(raw_rules)
                except UserError as cycle_err:
                    warnings.append(str(cycle_err))
                    rules = list(raw_rules)  # fallback: original order

            lines_to_create = []  # bulk INSERT once instead of N+1 INSERTs

            for rule in rules:
                try:
                    if not slip._evaluate_rule_condition(rule, localdict):
                        continue
                    amount, qty, rate = slip._evaluate_rule_amount(rule, localdict)
                except Exception as e:
                    _logger.warning(
                        'Payslip %s: rule %s error — %s', slip.number, rule.code, e,
                    )
                    warnings.append(_('Rule %(code)s lỗi: %(err)s', code=rule.code, err=str(e)))
                    amount, qty, rate = 0.0, 1.0, 0.0

                # Update accumulated rules dict + O(1) index for _range_sum
                localdict['rules'][rule.code] = amount
                _rules_pos[rule.code] = len(_rules_order)
                _rules_order.append(rule.code)
                localdict['categories'].accumulate(rule.category_id.code, amount)

                # Collect line for bulk INSERT
                if rule.appears_on_payslip:
                    lines_to_create.append({
                        'payslip_id':  slip.id,
                        'rule_id':     rule.id,
                        'category_id': rule.category_id.id,
                        'code':        rule.code,
                        'name':        rule.name,
                        'sequence':    rule.sequence,
                        'quantity':    qty,
                        'rate':        rate,
                        # Phase 3: VND stored as integer (no floating-point noise)
                        'amount':      int(round(amount)),
                    })

            # Bulk INSERT all lines — 1 DB trip instead of V trips
            if lines_to_create:
                self.env['hb.payslip.line'].create(lines_to_create)

            # Finalize slip
            write_vals = {
                'x_teaching_computed': True,
                'x_compute_warnings': '\n'.join(warnings) if warnings else False,
            }
            if structure:
                write_vals['structure_id'] = structure.id
            slip.write(write_vals)

        return True

    # Backward-compat alias
    def action_compute_teaching_salary(self):
        return self.action_compute_sheet()

    # ── Resolve helpers ──────────────────────────────────────────────────────
    def _ensure_draft_state(self):
        self.ensure_one()
        if self.state not in ('draft', 'verify'):
            raise UserError(
                _('Chỉ tính lương khi phiếu ở trạng thái Nháp hoặc Chờ xác nhận.')
            )

    def _resolve_contract(self):
        self.ensure_one()
        contract = self.contract_id
        if not contract:
            contract = self.env['hb.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open'),
                ('date_start', '<=', self.date_to),
                '|', ('date_end', '=', False), ('date_end', '>=', self.date_from),
            ], limit=1)
            if contract:
                self.contract_id = contract
        # Contract is optional — return empty recordset if none found
        return contract or self.env['hb.contract']

    def _resolve_structure(self, contract):
        """Determine salary structure: explicit > contract > auto-detect > None (use all rules)."""
        self.ensure_one()
        structure = self.structure_id or (contract and contract.x_structure_id)
        if not structure:
            # Auto-detect from employee work_form
            work_form = getattr(self.employee_id, 'x_work_form', 'offline')
            code = 'STRUCT_ONLINE' if work_form == 'online' else 'STRUCT_OFFLINE'
            structure = self.env['hb.salary.structure'].search(
                [('code', '=', code), ('active', '=', True)], limit=1,
            )
        # Return structure or False — caller handles missing/empty-rule case
        return structure or False

    # ── Build evaluation namespace ───────────────────────────────────────────
    def _build_localdict(self, contract):
        self.ensure_one()
        employee = self.employee_id

        # rules dict — accumulates amounts as rules are evaluated (insertion order = eval order)
        rules_amounts = {}
        # rules_order + rules_pos: O(1) index for _range_sum (avoids list scan)
        rules_order: list = []
        rules_pos:   dict = {}

        def _range_sum(start_code, end_code):
            """Sum all rule amounts from start_code to end_code (inclusive) by eval order."""
            i_s = rules_pos.get(start_code)
            i_e = rules_pos.get(end_code)
            if i_s is None or i_e is None:
                return 0.0
            if i_s > i_e:
                i_s, i_e = i_e, i_s
            return sum(rules_amounts[c] for c in rules_order[i_s:i_e + 1])

        import math
        def _round_dir(value, direction=0):
            """Round with direction: 1 = ceil (làm tròn lên), 0 = floor (làm tròn xuống)."""
            if direction:
                return math.ceil(value)
            return math.floor(value)

        return {
            # Core objects
            'payslip':      self,
            'employee':     employee,
            'contract':     contract,
            # Proxies
            'worked_days':  WorkedDaysProxy(self.worked_days_ids),
            'inputs':       InputsProxy(self.input_ids),
            'categories':   CategoryTotals(),
            'rules':        rules_amounts,
            # Range sum helper + index structures (updated by action_compute_sheet)
            '_range_sum':   _range_sum,
            '_rules_order': rules_order,
            '_rules_pos':   rules_pos,
            # Result placeholders (used by 'code' type rules)
            'result':       0.0,
            'result_qty':   1.0,
            'result_rate':  0.0,
            # Safe builtins
            'round':  round,
            'max':    max,
            'min':    min,
            'abs':    abs,
            'float':  float,
            'int':    int,
            # ROUND(x, y): y=1 → ceil, y=0 → floor
            '_round_dir': _round_dir,
        }

    # ── Rule evaluation ──────────────────────────────────────────────────────
    @staticmethod
    def _evaluate_rule_condition(rule, localdict):
        if rule.condition_type != 'python' or not rule.condition_python:
            return True
        # Keep safe_eval for conditions — they may be complex multi-expression Python
        return bool(safe_eval(rule.condition_python, localdict))

    def _evaluate_rule_amount(self, rule, localdict):
        amount = 0.0
        qty    = 1.0
        rate   = 0.0

        if rule.amount_type == 'code' and rule.amount_python_compute:
            # 'code' type: full Python exec — keep safe_eval (exec mode)
            localdict['result']      = 0.0
            localdict['result_qty']  = 1.0
            localdict['result_rate'] = 0.0
            safe_eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
            amount = float(localdict.get('result', 0.0))
            qty    = float(localdict.get('result_qty', 1.0))
            rate   = float(localdict.get('result_rate', 0.0))

        elif rule.amount_type == 'fixed':
            amount = rule.amount_fixed

        elif rule.amount_type == 'percentage':
            # Phase 1: use AST evaluator for percentage base expression
            base   = _eval_formula_expr(rule.amount_percentage_base or '0', localdict)
            amount = int(round(float(base) * rule.amount_percentage / 100.0))

        elif rule.amount_type == 'formula' and rule.amount_formula:
            # Phase 1: AST evaluator — no eval/exec, no transpile step
            amount = float(_eval_formula_expr(rule.amount_formula, localdict))

        elif rule.amount_type == 'lookup':
            amount = self._compute_lookup(rule)

        return amount, qty, rate

    def _compute_lookup(self, rule):
        """Aggregate a field from a whitelisted source for the current
        employee within the payslip date range."""
        self.ensure_one()
        source_key = rule.lookup_source
        field_name = rule.lookup_field

        if not source_key or source_key not in LOOKUP_SOURCES:
            _logger.warning(
                'Payslip %s: lookup rule %s — invalid source "%s"',
                self.number, rule.code, source_key,
            )
            return 0.0

        src_def = LOOKUP_SOURCES[source_key]
        if not field_name or field_name not in src_def['fields']:
            _logger.warning(
                'Payslip %s: lookup rule %s — invalid field "%s" for source "%s"',
                self.number, rule.code, field_name, source_key,
            )
            return 0.0

        Model  = self.env[src_def['model']].sudo()
        domain = [
            (src_def['employee_field'], '=', self.employee_id.id),
            (src_def['date_field'], '>=', self.date_from),
            (src_def['date_field'], '<=', self.date_to),
        ]
        agg     = src_def['fields'][field_name].get('agg', 'sum')
        records = Model.search(domain)
        if not records:
            return 0.0

        vals = records.mapped(field_name)
        if agg == 'sum':   return sum(vals)
        if agg == 'avg':   return sum(vals) / len(vals) if vals else 0.0
        if agg == 'count': return float(len(records))
        if agg == 'max':   return max(vals)
        if agg == 'min':   return min(vals)

        _logger.warning(
            'Payslip %s: lookup rule %s — unknown agg "%s"',
            self.number, rule.code, agg,
        )
        return 0.0

    # ── PIT helper (called from 'code' type rules via payslip._hocba_pit) ────
    def _hocba_pit(self, taxable_income):
        """7-bracket progressive PIT calculation (2026 values)."""
        if taxable_income <= 0:
            return 0
        tax       = 0.0
        remaining = taxable_income
        prev      = 0
        for limit, rate in PIT_BRACKETS:
            size = limit - prev
            if remaining <= 0:
                break
            t    = min(remaining, size)
            tax += t * rate
            remaining -= t
            prev = limit
        # Phase 3: VND as integer
        return int(round(tax))

    # ── Dependent count helper (exposed to rule code) ─────────────────────────
    def _get_dependent_count(self):
        self.ensure_one()
        dep_ids = getattr(self.employee_id, 'x_dependent_ids', None)
        if dep_ids:
            today = fields.Date.today()
            return len(dep_ids.filtered(
                lambda d: (
                    getattr(d, 'date_start', False) and d.date_start <= today
                    and (not getattr(d, 'date_end', False) or d.date_end >= today)
                )
            ))
        return 0

    # ═════════════════════════════════════════════════════════════════════════
    # State transitions
    # ═════════════════════════════════════════════════════════════════════════
    def action_payslip_verify(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ xác nhận phiếu ở trạng thái Nháp.'))
            rec.state = 'verify'

    def action_payslip_done(self):
        for rec in self:
            if rec.state not in ('draft', 'verify'):
                raise UserError(_('Chỉ hoàn tất phiếu ở trạng thái Nháp hoặc Chờ xác nhận.'))
            if not rec.x_teaching_computed:
                raise UserError(_('Vui lòng tính lương trước khi hoàn tất phiếu.'))
            rec.state = 'done'

    def action_payslip_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_to_draft(self, reason=None):
        for rec in self:
            if rec.state != 'done':
                raise UserError(_('Chỉ reset phiếu ở trạng thái Hoàn tất.'))
            if not self.env.user.has_group('hr.group_hr_manager'):
                raise UserError(_('Chỉ HR Manager được phép reset phiếu lương.'))
            if not reason:
                raise UserError(_('Bắt buộc nhập lý do reset.'))
            rec.write({'state': 'draft', 'x_teaching_computed': False})
            rec.message_post(body=_(
                'Phiếu lương đã reset về Nháp.\nLý do: %(reason)s\nBởi: %(user)s',
                reason=reason, user=self.env.user.name,
            ))

    # ═════════════════════════════════════════════════════════════════════════
    # EMAIL — send payslip to employee
    # ═════════════════════════════════════════════════════════════════════════
    def action_send_payslip_mail(self):
        """Send payslip email to employee with public view link."""
        ICP      = self.env['ir.config_parameter'].sudo()
        base_url = ICP.get_param('web.base.url')
        subject_tpl = ICP.get_param('hocba_payroll.mail_subject', default=False)
        body_tpl    = ICP.get_param('hocba_payroll.mail_body',    default=False)

        for slip in self:
            employee = slip.employee_id
            email_to = employee.work_email or getattr(employee, 'email', False)
            if not email_to:
                continue
            if not slip.x_access_token:
                slip.x_access_token = str(uuid.uuid4())

            view_url = f'{base_url}/payslip/view/{slip.x_access_token}'
            month    = slip.date_from.strftime('%m') if slip.date_from else ''
            year     = slip.date_from.strftime('%Y') if slip.date_from else ''

            tpl_vars = {
                'employee_name': employee.name,
                'month':         month,
                'year':          year,
                'gross':         f'{slip.gross_amount:,.0f}',
                'net':           f'{slip.net_amount:,.0f}',
                'view_url':      view_url,
            }

            subject   = self._render_mail_tpl(
                subject_tpl or 'Bảng lương tháng {month}/{year} — {employee_name}',
                tpl_vars,
            )
            body_html = self._render_mail_tpl(
                body_tpl or slip._default_mail_body(),
                tpl_vars,
            )

            mail_vals = {
                'subject':     subject,
                'email_to':    email_to,
                'body_html':   body_html,
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].sudo().create(mail_vals)
            mail.send()

            slip.write({
                'x_email_sent':      True,
                'x_email_sent_date': fields.Datetime.now(),
            })

            # Log to chatter for audit trail
            slip.message_post(
                body=_(
                    'Đã gửi phiếu lương tháng %(m)s/%(y)s tới <b>%(email)s</b>.',
                    m=month, y=year, email=email_to,
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    @staticmethod
    def _render_mail_tpl(tpl, variables):
        """Safely render template with {key} placeholders."""
        try:
            return tpl.format(**variables)
        except (KeyError, IndexError, ValueError):
            return tpl

    @staticmethod
    def _default_mail_body():
        return (
            '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">'
            '<h2 style="color:#1f2937;">Bảng lương tháng {month}/{year}</h2>'
            '<p>Xin chào <strong>{employee_name}</strong>,</p>'
            '<p>Phiếu lương tháng {month}/{year} của bạn đã sẵn sàng.</p>'
            '<table style="width:100%;border-collapse:collapse;margin:16px 0;">'
            '<tr style="background:#f3f4f6;">'
            '<td style="padding:8px 12px;font-weight:600;">Tổng thu nhập</td>'
            '<td style="padding:8px 12px;text-align:right;">{gross} ₫</td>'
            '</tr>'
            '<tr style="background:#ecfdf5;">'
            '<td style="padding:8px 12px;font-weight:600;color:#065f46;">Thực lĩnh</td>'
            '<td style="padding:8px 12px;text-align:right;font-weight:700;color:#065f46;">{net} ₫</td>'
            '</tr>'
            '</table>'
            '<p>Vui lòng nhấn nút bên dưới để xem chi tiết và xác nhận:</p>'
            '<a href="{view_url}" '
            'style="display:inline-block;padding:12px 24px;background:#2563eb;'
            'color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">'
            'Xem phiếu lương</a>'
            '<hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;"/>'
            '<p style="font-size:12px;color:#9ca3af;">Email này được gửi tự động. Vui lòng không reply.</p>'
            '</div>'
        )

    # ═════════════════════════════════════════════════════════════════════════
    # API serialization
    # ═════════════════════════════════════════════════════════════════════════
    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id':               self.id,
            'name':             self.name,
            'number':           self.number,
            'employee_id':      self.employee_id.id,
            'employee_name':    self.employee_id.name,
            'contract_id':      self.contract_id.id if self.contract_id else None,
            'structure_id':     self.structure_id.id if self.structure_id else None,
            'structure_code':   self.structure_id.code if self.structure_id else None,
            'date_from':        str(self.date_from),
            'date_to':          str(self.date_to),
            'state':            self.state,
            'teaching_computed': self.x_teaching_computed,
            'compute_warnings': self.x_compute_warnings,
            'gross_amount':     self.gross_amount,
            'net_amount':       self.net_amount,
            'employee_confirm': self.x_employee_confirm,
            'employee_feedback': self.x_employee_feedback or '',
            'email_sent':       self.x_email_sent,
            'worked_days': [{
                'code':            wd.code,
                'name':            wd.name,
                'number_of_days':  wd.number_of_days,
                'number_of_hours': wd.number_of_hours,
            } for wd in self.worked_days_ids],
            'inputs': [{
                'code':   inp.code,
                'name':   inp.name,
                'amount': inp.amount,
            } for inp in self.input_ids],
            'lines': [{
                'id':            l.id,
                'code':          l.code,
                'name':          l.name,
                'sequence':      l.sequence,
                'quantity':      l.quantity,
                'rate':          l.rate,
                'amount':        l.amount,
                'category_code': l.category_id.code if l.category_id else '',
            } for l in self.line_ids.sorted('sequence')],
        }
