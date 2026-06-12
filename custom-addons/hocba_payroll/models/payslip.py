"""
Payslip — standalone replacement for hr.payslip (Enterprise).
FUNC-PR-001: Tính lương giáo viên theo giờ dạy (TEACH_HOURS).

Design:
    - Template Method: action_compute_teaching_salary orchestrates the pipeline.
    - Each step is a separate method for testability & overriding.
"""
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
WORK_ENTRY_TEACHING = 'WORK200'
WORK_ENTRY_HOLIDAY_OT = 'WORK110_OT_HOLIDAY'
HOLIDAY_OT_MULTIPLIER = 3.0
MAX_SINGLE_ENTRY_HOURS = 24.0
WARN_MONTHLY_HOURS = 200.0

# ── Vietnam PIT 7-bracket progressive table ─────────────────
PIT_BRACKETS = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (float('inf'), 0.35),
]
PERSONAL_DEDUCTION = 11_000_000
DEPENDENT_DEDUCTION = 4_400_000
BHXH_EE_RATE = 0.08
BHYT_EE_RATE = 0.015
BHTN_EE_RATE = 0.01


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

    # ── Payslip lines ────────────────────────────────────────
    line_ids = fields.One2many(
        'hb.payslip.line', 'payslip_id', string='Chi tiết lương',
    )

    # ── Teaching computed fields ─────────────────────────────
    x_teaching_total_hours = fields.Float(
        string='Tổng giờ dạy', digits=(8, 2), readonly=True,
    )
    x_holiday_ot_hours = fields.Float(
        string='Giờ OT ngày lễ', digits=(8, 2), readonly=True,
    )
    x_compute_warnings = fields.Text(
        string='Cảnh báo tính lương', readonly=True,
    )
    x_teaching_computed = fields.Boolean(
        string='Đã tính', default=False, readonly=True,
    )

    # ── Aggregated amounts ───────────────────────────────────
    gross_amount = fields.Float(
        string='Gross', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )
    net_amount = fields.Float(
        string='Net (Thực lĩnh)', digits=(16, 0),
        compute='_compute_amounts', store=True,
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_name(self):
        for rec in self:
            emp = rec.employee_id.name or ''
            period = ''
            if rec.date_from and rec.date_to:
                period = f'{rec.date_from.strftime("%m/%Y")}'
            rec.name = f'Lương {emp} — {period}' if emp else 'Phiếu lương mới'

    @api.depends('line_ids.amount', 'line_ids.code')
    def _compute_amounts(self):
        for rec in self:
            gross_line = rec.line_ids.filtered(lambda l: l.code == 'GROSS')
            net_line = rec.line_ids.filtered(lambda l: l.code == 'NET')
            rec.gross_amount = gross_line[0].amount if gross_line else 0
            rec.net_amount = net_line[0].amount if net_line else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('Mới')) == _('Mới'):
                vals['number'] = self.env['ir.sequence'].next_by_code('hb.payslip') or '/'
        return super().create(vals_list)

    # ═════════════════════════════════════════════════════════
    # TEMPLATE METHOD: Compute teaching salary
    # ═════════════════════════════════════════════════════════
    def action_compute_teaching_salary(self):
        """Main entry — compute full salary pipeline for each payslip."""
        for slip in self:
            slip._ensure_draft_state()
            contract = slip._resolve_contract()
            slip._validate_work_entries()
            result = slip._build_teaching_salary(contract)
            slip._write_salary_lines(result, contract)
            slip._finalize_compute(result)
        return True

    # ── Step 1: Guards ───────────────────────────────────────
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
            # Auto-find active contract
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
        if not contract.x_teaching_hourly_rate or contract.x_teaching_hourly_rate <= 0:
            raise ValidationError(
                _('Hợp đồng %(ref)s của %(emp)s chưa cấu hình đơn giá giờ dạy.',
                  ref=contract.name, emp=self.employee_id.name)
            )
        return contract

    # ── Step 2: Validation Gate (VR-004) ─────────────────────
    def _validate_work_entries(self):
        self.ensure_one()
        pending = self.env['hb.work.entry'].search_count([
            ('employee_id', '=', self.employee_id.id),
            ('date_start', '>=', self.date_from),
            ('date_stop', '<=', self.date_to),
            ('work_entry_type_id.code', '=', WORK_ENTRY_TEACHING),
            ('state', 'in', ('draft', 'conflict')),
        ])
        if pending:
            raise ValidationError(
                _('Còn %(n)s Work Entry chưa được xác thực trong kỳ. '
                  'Vui lòng xử lý trước khi tính lương.', n=pending)
            )

    # ── Step 3: Build salary breakdown ───────────────────────
    def _build_teaching_salary(self, contract):
        self.ensure_one()
        warnings = []

        # Teaching hours (WORK200)
        teaching_entries = self._get_work_entries(WORK_ENTRY_TEACHING)
        total_hours, skipped = self._sum_hours(teaching_entries)
        if skipped:
            warnings.append(_('Bỏ qua %(n)s Work Entry không hợp lệ.', n=skipped))

        teach_amount = total_hours * contract.x_teaching_hourly_rate

        # HSK Premium
        hsk_premium = self._calc_hsk_premium(teaching_entries, contract)

        # Extra hours bonus
        extra_bonus = self._calc_extra_bonus(total_hours, contract)

        # Holiday OT
        holiday_entries = self._get_work_entries(WORK_ENTRY_HOLIDAY_OT)
        holiday_hours, _ = self._sum_hours(holiday_entries)
        holiday_amount = holiday_hours * contract.x_teaching_hourly_rate * HOLIDAY_OT_MULTIPLIER

        # Fixed base (pro-rated)
        fixed_base = self._calc_fixed_base(contract)

        # Gross
        gross = teach_amount + hsk_premium + extra_bonus + holiday_amount + fixed_base

        # Insurance deductions (employee portion)
        wage = contract.wage or 0
        bhxh_ee = wage * BHXH_EE_RATE
        bhyt_ee = wage * BHYT_EE_RATE
        bhtn_ee = wage * BHTN_EE_RATE
        total_insurance_ee = bhxh_ee + bhyt_ee + bhtn_ee

        # PIT
        dep_count = self._get_dependent_count()
        taxable = max(gross - total_insurance_ee - PERSONAL_DEDUCTION - dep_count * DEPENDENT_DEDUCTION, 0)
        pit = self._calc_pit(taxable)

        # Net
        net = gross - total_insurance_ee - pit

        if total_hours > WARN_MONTHLY_HOURS:
            warnings.append(_('Tổng giờ dạy vượt %(h)sh — cần review.', h=WARN_MONTHLY_HOURS))

        return {
            'total_hours': total_hours,
            'holiday_hours': holiday_hours,
            'teach_amount': teach_amount,
            'hsk_premium': hsk_premium,
            'extra_bonus': extra_bonus,
            'holiday_amount': holiday_amount,
            'fixed_base': fixed_base,
            'gross': gross,
            'bhxh_ee': bhxh_ee,
            'bhyt_ee': bhyt_ee,
            'bhtn_ee': bhtn_ee,
            'pit': pit,
            'taxable': taxable,
            'dep_count': dep_count,
            'net': net,
            'warnings': warnings,
        }

    # ── Sub-calculations ─────────────────────────────────────
    def _get_work_entries(self, type_code):
        self.ensure_one()
        return self.env['hb.work.entry'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_start', '>=', self.date_from),
            ('date_stop', '<=', self.date_to),
            ('work_entry_type_id.code', '=', type_code),
            ('state', '=', 'validated'),
        ])

    @staticmethod
    def _sum_hours(entries):
        total = 0.0
        skipped = 0
        for entry in entries:
            if entry.duration < 0 or entry.duration > MAX_SINGLE_ENTRY_HOURS:
                skipped += 1
                continue
            total += entry.duration
        return total, skipped

    def _calc_hsk_premium(self, entries, contract):
        if not contract.x_rate_hsk_class:
            return 0.0
        rate_diff = contract.x_rate_hsk_class - contract.x_teaching_hourly_rate
        if rate_diff <= 0:
            return 0.0
        hsk_hours = 0.0
        for entry in entries:
            if entry.x_class_level in ('hsk4', 'hsk5', 'hsk6'):
                if 0 < entry.duration <= MAX_SINGLE_ENTRY_HOURS:
                    hsk_hours += entry.duration
        return hsk_hours * rate_diff

    @staticmethod
    def _calc_extra_bonus(total_hours, contract):
        threshold = contract.x_standard_threshold or 60.0
        if total_hours <= threshold:
            return 0.0
        excess = total_hours - threshold
        extra_rate = contract.x_effective_extra_rate
        return excess * extra_rate

    def _calc_fixed_base(self, contract):
        self.ensure_one()
        if not contract.x_has_fixed_base or not contract.x_fixed_base or contract.x_fixed_base <= 0:
            return 0.0
        period_start = self.date_from
        period_end = self.date_to
        c_start = max(contract.date_start, period_start) if contract.date_start else period_start
        c_end = min(contract.date_end, period_end) if contract.date_end else period_end
        total_days = (period_end - period_start).days + 1
        worked_days = max((c_end - c_start).days + 1, 0)
        if total_days <= 0:
            return 0.0
        return contract.x_fixed_base * (worked_days / total_days)

    def _get_dependent_count(self):
        self.ensure_one()
        dep_ids = getattr(self.employee_id, 'x_dependent_ids', None)
        if dep_ids:
            return len(dep_ids.filtered(lambda d: getattr(d, 'active', True)))
        return 0

    @staticmethod
    def _calc_pit(taxable_income):
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
        return tax

    # ── Step 4: Write lines ──────────────────────────────────
    def _write_salary_lines(self, result, contract):
        """Clear old lines and write new salary breakdown."""
        self.ensure_one()
        self.line_ids.unlink()

        lines = [
            ('FIXED_BASE', 'Lương cố định base', result['fixed_base'], 5),
            ('TEACH_HOURS', 'Lương theo giờ dạy', result['teach_amount'], 10),
            ('HSK_PREMIUM', 'Premium giờ HSK4+', result['hsk_premium'], 11),
            ('EXTRA_BONUS', 'Bonus giờ vượt ngưỡng', result['extra_bonus'], 12),
            ('HOLIDAY_OT', 'OT ngày lễ (300%)', result['holiday_amount'], 13),
            ('GROSS', 'Tổng lương Gross', result['gross'], 20),
            ('BHXH_EE', 'BHXH NV đóng (8%)', -result['bhxh_ee'], 30),
            ('BHYT_EE', 'BHYT NV đóng (1.5%)', -result['bhyt_ee'], 31),
            ('BHTN_EE', 'BHTN NV đóng (1%)', -result['bhtn_ee'], 32),
            ('PIT', 'Thuế TNCN', -result['pit'], 40),
            ('NET', 'Thực lĩnh', result['net'], 99),
        ]

        vals_list = []
        for code, name, amount, seq in lines:
            # Derive quantity/rate for display
            qty = 1.0
            rate = amount
            if code == 'TEACH_HOURS':
                qty = result['total_hours']
                rate = contract.x_teaching_hourly_rate
            elif code == 'HOLIDAY_OT':
                qty = result['holiday_hours']
                rate = contract.x_teaching_hourly_rate * HOLIDAY_OT_MULTIPLIER

            vals_list.append({
                'payslip_id': self.id,
                'code': code,
                'name': name,
                'sequence': seq,
                'quantity': qty,
                'rate': rate,
                'amount': amount,
            })

        self.env['hb.payslip.line'].create(vals_list)

    # ── Step 5: Finalize ─────────────────────────────────────
    def _finalize_compute(self, result):
        self.ensure_one()
        self.write({
            'x_teaching_total_hours': result['total_hours'],
            'x_holiday_ot_hours': result['holiday_hours'],
            'x_compute_warnings': '\n'.join(result['warnings']) if result['warnings'] else False,
            'x_teaching_computed': True,
        })
        self.message_post(body=_(
            'Tính lương thành công:\n'
            '• Giờ dạy: %(hours).1fh | Gross: %(gross)s | Net: %(net)s\n'
            '• Chi tiết: Base=%(base)s | HSK+=%(hsk)s | Extra=%(extra)s | Holiday=%(hol)s | Fixed=%(fix)s\n'
            '• BHXH=%(bhxh)s | BHYT=%(bhyt)s | BHTN=%(bhtn)s | PIT=%(pit)s',
            hours=result['total_hours'],
            gross='{:,.0f}'.format(result['gross']),
            net='{:,.0f}'.format(result['net']),
            base='{:,.0f}'.format(result['teach_amount']),
            hsk='{:,.0f}'.format(result['hsk_premium']),
            extra='{:,.0f}'.format(result['extra_bonus']),
            hol='{:,.0f}'.format(result['holiday_amount']),
            fix='{:,.0f}'.format(result['fixed_base']),
            bhxh='{:,.0f}'.format(result['bhxh_ee']),
            bhyt='{:,.0f}'.format(result['bhyt_ee']),
            bhtn='{:,.0f}'.format(result['bhtn_ee']),
            pit='{:,.0f}'.format(result['pit']),
        ))

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
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
            'state': self.state,
            'teaching_total_hours': self.x_teaching_total_hours,
            'holiday_ot_hours': self.x_holiday_ot_hours,
            'teaching_computed': self.x_teaching_computed,
            'compute_warnings': self.x_compute_warnings,
            'gross_amount': self.gross_amount,
            'net_amount': self.net_amount,
            'lines': [{
                'id': l.id,
                'code': l.code,
                'name': l.name,
                'sequence': l.sequence,
                'quantity': l.quantity,
                'rate': l.rate,
                'amount': l.amount,
            } for l in self.line_ids.sorted('sequence')],
        }
