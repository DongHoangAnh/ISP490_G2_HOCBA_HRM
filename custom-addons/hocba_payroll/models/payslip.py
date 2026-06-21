"""
Payslip — standalone payroll engine with data-driven salary rules.

Design:
    - Rule Engine: action_compute_sheet() iterates salary rules via safe_eval.
    - Proxy classes provide convenient attribute access in rule code.
    - Backward compatible: teaching work-entry methods kept for teacher structures.
"""
import logging
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

# ── Vietnam PIT 7-bracket progressive table (2026) ───────────
PIT_BRACKETS = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (float('inf'), 0.35),
]


# ═══════════════════════════════════════════════════════════════
# Proxy classes for rule evaluation
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# Model
# ═══════════════════════════════════════════════════════════════

class HbPayslip(models.Model):
    _name = 'hb.payslip'
    _description = 'Phiếu lương'
    _order = 'number desc'
    _inherit = ['mail.thread']

    # ── Core fields ──────────────────────────────────────────
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

    # ── Payslip details ─────────────────────────────────────
    line_ids = fields.One2many(
        'hb.payslip.line', 'payslip_id', string='Chi tiết lương',
    )
    worked_days_ids = fields.One2many(
        'hb.payslip.worked_days', 'payslip_id', string='Công',
    )
    input_ids = fields.One2many(
        'hb.payslip.input', 'payslip_id', string='Đầu vào',
    )

    # ── Computed status fields ──────────────────────────────
    x_compute_warnings = fields.Text(
        string='Cảnh báo tính lương', readonly=True,
    )
    x_teaching_computed = fields.Boolean(
        string='Đã tính', default=False, readonly=True,
    )

    # ── Employee confirmation ────────────────────────────────
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

    # ── Aggregated amounts ──────────────────────────────────
    gross_amount = fields.Float(
        string='Gross', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )
    net_amount = fields.Float(
        string='Net (Thực lĩnh)', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )

    # ── Computed & lifecycle ────────────────────────────────
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_name(self):
        for rec in self:
            emp = rec.employee_id.name or ''
            period = rec.date_from.strftime('%m/%Y') if rec.date_from else ''
            rec.name = f'Lương {emp} — {period}' if emp else 'Phiếu lương mới'

    @api.depends('line_ids.amount', 'line_ids.code')
    def _compute_amounts(self):
        for rec in self:
            gross_line = rec.line_ids.filtered(lambda l: l.code == 'tong_thu_nhap')
            net_line = rec.line_ids.filtered(lambda l: l.code == 'thuc_lanh')
            rec.gross_amount = gross_line[0].amount if gross_line else 0
            rec.net_amount = net_line[0].amount if net_line else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('Mới')) == _('Mới'):
                vals['number'] = self.env['ir.sequence'].next_by_code('hb.payslip') or '/'
            if not vals.get('x_access_token'):
                vals['x_access_token'] = str(uuid.uuid4())
        return super().create(vals_list)

    # ═════════════════════════════════════════════════════════
    # RULE-BASED SALARY ENGINE
    # ═════════════════════════════════════════════════════════

    def action_compute_sheet(self):
        """Main entry — compute salary using data-driven rules."""
        for slip in self:
            slip._ensure_draft_state()
            contract = slip._resolve_contract()
            structure = slip._resolve_structure(contract)

            # Clear old lines
            slip.line_ids.unlink()

            # Build evaluation namespace
            localdict = slip._build_localdict(contract)

            # Execute rules in sequence order
            warnings = []
            rules = structure.rule_ids.filtered('active').sorted('sequence')
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

                # Store result for subsequent rules
                localdict['rules'][rule.code] = amount
                localdict['categories'].accumulate(rule.category_id.code, amount)

                # Create payslip line
                if rule.appears_on_payslip:
                    self.env['hb.payslip.line'].create({
                        'payslip_id': slip.id,
                        'rule_id': rule.id,
                        'category_id': rule.category_id.id,
                        'code': rule.code,
                        'name': rule.name,
                        'sequence': rule.sequence,
                        'quantity': qty,
                        'rate': rate,
                        'amount': round(amount),
                    })

            # Finalize
            slip.write({
                'structure_id': structure.id,
                'x_teaching_computed': True,
                'x_compute_warnings': '\n'.join(warnings) if warnings else False,
            })

        return True

    # Backward-compat alias
    def action_compute_teaching_salary(self):
        return self.action_compute_sheet()

    # ── Resolve helpers ─────────────────────────────────────
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
        if not contract:
            raise ValidationError(
                _('Nhân viên %(emp)s không có hợp đồng active trong kỳ %(fr)s – %(to)s.',
                  emp=self.employee_id.name, fr=self.date_from, to=self.date_to)
            )
        return contract

    def _resolve_structure(self, contract):
        """Determine salary structure: explicit > contract > auto-detect."""
        self.ensure_one()
        structure = self.structure_id or contract.x_structure_id
        if not structure:
            # Auto-detect from employee work_form
            work_form = getattr(self.employee_id, 'x_work_form', 'offline')
            code = 'STRUCT_ONLINE' if work_form == 'online' else 'STRUCT_OFFLINE'
            structure = self.env['hb.salary.structure'].search(
                [('code', '=', code), ('active', '=', True)], limit=1,
            )
        if not structure:
            raise ValidationError(
                _('Không tìm thấy cấu trúc lương phù hợp cho %(emp)s.',
                  emp=self.employee_id.name)
            )
        return structure

    # ── Build evaluation namespace ──────────────────────────
    def _build_localdict(self, contract):
        self.ensure_one()
        employee = self.employee_id

        # rules dict — preserves insertion order (= sequence order)
        rules = {}

        def _range_sum(start_code, end_code):
            """Sum all rule amounts from start_code to end_code (inclusive) by sequence order."""
            codes = list(rules.keys())
            try:
                i_start = codes.index(start_code)
            except ValueError:
                return 0.0
            try:
                i_end = codes.index(end_code)
            except ValueError:
                return 0.0
            if i_start > i_end:
                i_start, i_end = i_end, i_start
            return sum(rules[c] for c in codes[i_start:i_end + 1])

        import math
        def _round_dir(value, direction=0):
            """Round with direction: 1 = ceil (làm tròn lên), 0 = floor (làm tròn xuống)."""
            if direction:
                return math.ceil(value)
            return math.floor(value)

        return {
            # Core objects
            'payslip': self,
            'employee': employee,
            'contract': contract,
            # Proxies
            'worked_days': WorkedDaysProxy(self.worked_days_ids),
            'inputs': InputsProxy(self.input_ids),
            'categories': CategoryTotals(),
            'rules': rules,
            # Range sum helper
            '_range_sum': _range_sum,
            # Result placeholders
            'result': 0.0,
            'result_qty': 1.0,
            'result_rate': 0.0,
            # Safe builtins
            'round': round,
            'max': max,
            'min': min,
            'abs': abs,
            'float': float,
            'int': int,
            # ROUND(x, y): y=1 → ceil, y=0 → floor
            '_round_dir': _round_dir,
        }

    # ── Formula transpiler ─────────────────────────────────
    @staticmethod
    def _transpile_formula(formula, known_codes):
        """Transpile Excel-like formula → Python expression.

        Supported syntax:
            Rule codes (slug)  → rules.get('slug_code', 0)
            IF(c, a, b)        → (a if c else b)
            SUM(a, b)          → _range_sum('a', 'b')  (cộng tất cả rule từ a đến b theo sequence)
            MAX / MIN / ABS          → Python builtins (already in eval context)
            ROUND(x, y)             → _round_dir(x, y)  (y=1: ceil, y=0: floor)
            + - * / ( ) > < >= <= == !=  → kept as-is

        VD: luong_thoi_gian * 0.08
            SUM(luong_thoi_gian, thuong_khac)  → cộng tất cả rule từ seq 10 đến seq 36
        """
        import re

        if not formula or not formula.strip():
            return '0'

        src = formula.strip()

        # ── 1. Replace IF(cond, true_val, false_val) ──
        #    Handles nested parens via manual depth tracking
        def _replace_if(text):
            while True:
                m = re.search(r'\bIF\s*\(', text, re.IGNORECASE)
                if not m:
                    break
                start = m.end()  # position right after 'IF('
                depth = 1
                parts = []
                cur = []
                i = start
                while i < len(text) and depth > 0:
                    ch = text[i]
                    if ch == '(':
                        depth += 1
                        cur.append(ch)
                    elif ch == ')':
                        depth -= 1
                        if depth == 0:
                            parts.append(''.join(cur))
                        else:
                            cur.append(ch)
                    elif ch == ',' and depth == 1:
                        parts.append(''.join(cur))
                        cur = []
                    else:
                        cur.append(ch)
                    i += 1
                if len(parts) == 3:
                    cond, tv, fv = [p.strip() for p in parts]
                    replacement = f'(({tv}) if ({cond}) else ({fv}))'
                else:
                    replacement = '0'
                text = text[:m.start()] + replacement + text[i:]
            return text

        src = _replace_if(src)

        # ── 2. Replace SUM(a, b) → _range_sum('a', 'b') ──
        # SUM nhận 2 tham số: mã bắt đầu và mã kết thúc,
        # cộng tất cả rule từ mã a đến mã b theo thứ tự sequence.
        def _replace_sum(text):
            while True:
                m = re.search(r'\bSUM\s*\(', text, re.IGNORECASE)
                if not m:
                    break
                start = m.end()
                depth = 1
                i = start
                while i < len(text) and depth > 0:
                    if text[i] == '(':
                        depth += 1
                    elif text[i] == ')':
                        depth -= 1
                    i += 1
                inner = text[m.end():i - 1]
                args = [a.strip() for a in inner.split(',') if a.strip()]
                if len(args) == 2:
                    replacement = f"_range_sum('{args[0]}', '{args[1]}')"
                else:
                    replacement = '0'
                text = text[:m.start()] + replacement + text[i:]
            return text

        src = _replace_sum(src)

        # ── 2b. Replace ROUND(x, y) → _round_dir(x, y) ──
        # y=1: làm tròn lên (ceil), y=0: làm tròn xuống (floor)
        src = re.sub(r'\bROUND\b', '_round_dir', src, flags=re.IGNORECASE)

        # ── 3. Replace rule codes → rules.get('CODE', 0) ──
        # Match identifiers (letters/underscores/digits, 2+ chars)
        # Exclude Python/math builtins
        builtins_skip = {
            'IF', 'SUM', 'MAX', 'MIN', 'ABS', 'ROUND', 'True', 'False',
            'if', 'else', 'and', 'or', 'not', 'in', 'is',
            'max', 'min', 'abs', 'round', 'sum', 'float', 'int',
            'true', 'false', '_range_sum', '_round_dir',
        }

        def _code_replacer(match):
            token = match.group(0)
            if token in builtins_skip:
                return token
            if token in known_codes:
                return f"rules.get('{token}', 0)"
            return token

        src = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]+)\b', _code_replacer, src)

        return src

    # ── Rule evaluation ─────────────────────────────────────
    @staticmethod
    def _evaluate_rule_condition(rule, localdict):
        if rule.condition_type != 'python' or not rule.condition_python:
            return True
        return bool(safe_eval(rule.condition_python, localdict))

    @staticmethod
    def _evaluate_rule_amount(rule, localdict):
        amount = 0.0
        qty = 1.0
        rate = 0.0

        if rule.amount_type == 'code' and rule.amount_python_compute:
            localdict['result'] = 0.0
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 0.0
            safe_eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
            amount = float(localdict.get('result', 0.0))
            qty = float(localdict.get('result_qty', 1.0))
            rate = float(localdict.get('result_rate', 0.0))
        elif rule.amount_type == 'fixed':
            amount = rule.amount_fixed
        elif rule.amount_type == 'percentage':
            base = safe_eval(rule.amount_percentage_base or '0', localdict)
            amount = round(float(base) * rule.amount_percentage / 100.0)
        elif rule.amount_type == 'formula' and rule.amount_formula:
            known = set(localdict.get('rules', {}).keys())
            expr = HbPayslip._transpile_formula(rule.amount_formula, known)
            localdict['result'] = 0.0
            safe_eval(f"result = {expr}", localdict, mode='exec', nocopy=True)
            amount = float(localdict.get('result', 0.0))

        return amount, qty, rate

    # ── PIT helper (exposed to rule code via payslip._hocba_pit) ──
    def _hocba_pit(self, taxable_income):
        """7-bracket progressive PIT calculation (2026 values)."""
        if taxable_income <= 0:
            return 0.0
        tax = 0.0
        remaining = taxable_income
        prev = 0
        for limit, rate in PIT_BRACKETS:
            size = limit - prev
            if remaining <= 0:
                break
            t = min(remaining, size)
            tax += t * rate
            remaining -= t
            prev = limit
        return round(tax)

    # ── Dependent count helper (exposed to rule code) ────────
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

    # ═════════════════════════════════════════════════════════
    # State transitions
    # ═════════════════════════════════════════════════════════
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

    # ═════════════════════════════════════════════════════════
    # EMAIL — send payslip to employee
    # ═════════════════════════════════════════════════════════
    def action_send_payslip_mail(self):
        """Send payslip email to employee with public view link."""
        ICP = self.env['ir.config_parameter'].sudo()
        base_url = ICP.get_param('web.base.url')
        subject_tpl = ICP.get_param('hocba_payroll.mail_subject', default=False)
        body_tpl = ICP.get_param('hocba_payroll.mail_body', default=False)

        for slip in self:
            employee = slip.employee_id
            email_to = employee.work_email or getattr(employee, 'email', False)
            if not email_to:
                continue
            if not slip.x_access_token:
                slip.x_access_token = str(uuid.uuid4())

            view_url = f'{base_url}/payslip/view/{slip.x_access_token}'
            month = slip.date_from.strftime('%m') if slip.date_from else ''
            year = slip.date_from.strftime('%Y') if slip.date_from else ''

            tpl_vars = {
                'employee_name': employee.name,
                'month': month,
                'year': year,
                'gross': f'{slip.gross_amount:,.0f}',
                'net': f'{slip.net_amount:,.0f}',
                'view_url': view_url,
            }

            subject = self._render_mail_tpl(
                subject_tpl or 'Bảng lương tháng {month}/{year} — {employee_name}',
                tpl_vars,
            )
            body_html = self._render_mail_tpl(
                body_tpl or slip._default_mail_body(),
                tpl_vars,
            )

            mail_vals = {
                'subject': subject,
                'email_to': email_to,
                'body_html': body_html,
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].sudo().create(mail_vals)
            mail.send()

            slip.write({
                'x_email_sent': True,
                'x_email_sent_date': fields.Datetime.now(),
            })

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

    # ═════════════════════════════════════════════════════════
    # API serialization
    # ═════════════════════════════════════════════════════════
    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'number': self.number,
            'employee_id': self.employee_id.id,
            'employee_name': self.employee_id.name,
            'contract_id': self.contract_id.id if self.contract_id else None,
            'structure_id': self.structure_id.id if self.structure_id else None,
            'structure_code': self.structure_id.code if self.structure_id else None,
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
            'state': self.state,
            'teaching_computed': self.x_teaching_computed,
            'compute_warnings': self.x_compute_warnings,
            'gross_amount': self.gross_amount,
            'net_amount': self.net_amount,
            'employee_confirm': self.x_employee_confirm,
            'employee_feedback': self.x_employee_feedback or '',
            'email_sent': self.x_email_sent,
            'worked_days': [{
                'code': wd.code,
                'name': wd.name,
                'number_of_days': wd.number_of_days,
                'number_of_hours': wd.number_of_hours,
            } for wd in self.worked_days_ids],
            'inputs': [{
                'code': inp.code,
                'name': inp.name,
                'amount': inp.amount,
            } for inp in self.input_ids],
            'lines': [{
                'id': l.id,
                'code': l.code,
                'name': l.name,
                'sequence': l.sequence,
                'quantity': l.quantity,
                'rate': l.rate,
                'amount': l.amount,
                'category_code': l.category_id.code if l.category_id else '',
            } for l in self.line_ids.sorted('sequence')],
        }
