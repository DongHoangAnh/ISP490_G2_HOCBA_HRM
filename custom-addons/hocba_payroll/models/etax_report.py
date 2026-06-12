"""
eTax Monthly PIT Report.
FUNC-PR-005: Báo cáo thuế TNCN tháng theo Mẫu 05/KK-TNCN.

Design: Template Method — same skeleton as BHXH report.
"""
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# ── Vietnam PIT 7-bracket progressive table (resident) ──────
PIT_BRACKETS = [
    (5_000_000,   0.05),
    (10_000_000,  0.10),
    (18_000_000,  0.15),
    (32_000_000,  0.20),
    (52_000_000,  0.25),
    (80_000_000,  0.30),
    (float('inf'), 0.35),
]
PERSONAL_DEDUCTION = 11_000_000       # 11M/month
DEPENDENT_DEDUCTION = 4_400_000       # 4.4M per dependent
NON_RESIDENT_RATE = 0.20             # flat 20%


def compute_pit_resident(taxable_income):
    """Compute PIT for resident using 7-bracket progressive table."""
    if taxable_income <= 0:
        return 0.0
    tax = 0.0
    remaining = taxable_income
    prev_limit = 0
    for bracket_limit, rate in PIT_BRACKETS:
        bracket_size = bracket_limit - prev_limit
        if remaining <= 0:
            break
        taxable_in_bracket = min(remaining, bracket_size)
        tax += taxable_in_bracket * rate
        remaining -= taxable_in_bracket
        prev_limit = bracket_limit
    return tax


class EtaxReport(models.Model):
    _name = 'hb.etax.report'
    _description = 'Báo cáo thuế TNCN tháng (eTax 05/KK)'
    _order = 'period_year desc, period_month desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Tên báo cáo', compute='_compute_name', store=True)
    period_month = fields.Selection(
        [(str(m), f'Tháng {m}') for m in range(1, 13)],
        string='Tháng', required=True,
    )
    period_year = fields.Char(string='Năm', required=True, default=lambda self: str(fields.Date.today().year))
    batch_id = fields.Many2one(
        'hb.payslip.run', string='Payslip Batch',
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'hb.etax.report.line', 'report_id',
        string='Chi tiết thuế TNCN',
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('computed', 'Đã tính'),
        ('submitted', 'Đã nộp'),
    ], default='draft', tracking=True)

    total_gross = fields.Float(string='Tổng thu nhập Gross', digits=(16, 0),
                               compute='_compute_totals', store=True)
    total_pit = fields.Float(string='Tổng thuế TNCN', digits=(16, 0),
                              compute='_compute_totals', store=True)
    employee_count = fields.Integer(string='Số NV', compute='_compute_totals', store=True)

    @api.depends('period_month', 'period_year')
    def _compute_name(self):
        for rec in self:
            rec.name = f'eTax 05/KK T{rec.period_month}/{rec.period_year}'

    @api.depends('line_ids.gross_income', 'line_ids.pit_amount')
    def _compute_totals(self):
        for rec in self:
            lines = rec.line_ids
            rec.total_gross = sum(lines.mapped('gross_income'))
            rec.total_pit = sum(lines.mapped('pit_amount'))
            rec.employee_count = len(lines)

    # ─────────────────────────────────────────────────────────
    # Template Method: compute eTax lines
    # ─────────────────────────────────────────────────────────
    def action_compute(self):
        for report in self:
            if report.state != 'draft':
                raise UserError(_('Chỉ tính báo cáo ở trạng thái Nháp.'))
            report._validate_batch()
            report.line_ids.unlink()
            report._generate_lines()
            report.state = 'computed'
            report.message_post(body=_(
                'Đã tính eTax: %(n)s nhân viên, tổng thuế = %(pit)s VND.',
                n=report.employee_count,
                pit='{:,.0f}'.format(report.total_pit),
            ))

    def _validate_batch(self):
        self.ensure_one()
        if not self.batch_id:
            raise ValidationError(_('Vui lòng chọn Payslip Batch.'))
        if self.batch_id.state != 'close':
            raise ValidationError(_('Payslip Batch phải ở trạng thái Done/Close.'))

    def _generate_lines(self):
        """Build one eTax line per employee."""
        self.ensure_one()
        vals_list = []
        for slip in self.batch_id.slip_ids.filtered(lambda s: s.state == 'done'):
            emp = slip.employee_id
            gross = self._get_gross(slip)
            insurance_ee = self._get_insurance_deduction(slip)
            dependent_count = self._get_dependent_count(emp)
            residence = getattr(emp, 'x_tax_residence_status', 'resident') or 'resident'

            personal_ded = PERSONAL_DEDUCTION
            dependent_ded = dependent_count * DEPENDENT_DEDUCTION
            taxable = max(gross - insurance_ee - personal_ded - dependent_ded, 0)

            if residence == 'non_resident':
                pit = gross * NON_RESIDENT_RATE
            else:
                pit = compute_pit_resident(taxable)

            vals_list.append({
                'report_id': self.id,
                'employee_id': emp.id,
                'employee_code': getattr(emp, 'x_employee_code', '') or '',
                'pit_code': getattr(emp, 'x_pit_code', '') or '',
                'residence_status': residence,
                'gross_income': gross,
                'insurance_deduction': insurance_ee,
                'personal_deduction': personal_ded,
                'dependent_count': dependent_count,
                'dependent_deduction': dependent_ded,
                'taxable_income': taxable,
                'pit_amount': pit,
            })
        if vals_list:
            self.env['hb.etax.report.line'].create(vals_list)

    def _get_gross(self, payslip):
        gross_line = payslip.line_ids.filtered(lambda l: l.code == 'GROSS')
        return gross_line[0].total if gross_line else 0.0

    def _get_insurance_deduction(self, payslip):
        """Sum BHXH + BHYT + BHTN employee portions from payslip lines."""
        codes = ('BHXH_EE', 'BHYT_EE', 'BHTN_EE')
        total = 0.0
        for line in payslip.line_ids:
            if line.code in codes:
                total += abs(line.total)
        return total

    def _get_dependent_count(self, employee):
        """Get registered dependent count for PIT deduction."""
        dep_ids = getattr(employee, 'x_dependent_ids', None)
        if dep_ids:
            return len(dep_ids.filtered(lambda d: getattr(d, 'active', True)))
        return 0

    def action_mark_submitted(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('Chỉ nộp báo cáo ở trạng thái Đã tính.'))
            rec.state = 'submitted'
            rec.message_post(body=_('Báo cáo eTax đã được đánh dấu Đã nộp.'))

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'batch_id': self.batch_id.id if self.batch_id else None,
            'state': self.state,
            'employee_count': self.employee_count,
            'total_gross': self.total_gross,
            'total_pit': self.total_pit,
            'lines': [l._to_api_dict() for l in self.line_ids],
        }
