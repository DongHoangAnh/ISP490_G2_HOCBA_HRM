"""
Social Insurance (BHXH) Report model.
FUNC-PR-004: Báo cáo BHXH hàng tháng theo schema iBHXH.

Design: Template Method — _generate_lines() is the skeleton,
        sub-steps compute insurance amounts per employee.
"""
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# ── Vietnam social insurance rates (employee portion) ────────
BHXH_RATE_EE = 0.08       # 8%
BHYT_RATE_EE = 0.015      # 1.5%
BHTN_RATE_EE = 0.01       # 1%
# Employer portion
BHXH_RATE_ER = 0.175       # 17.5%
BHYT_RATE_ER = 0.03        # 3%
BHTN_RATE_ER = 0.01        # 1%
# Base salary cap multiplier (20× base salary)
INSURANCE_CAP_MULTIPLIER = 20


class BhxhReport(models.Model):
    _name = 'hb.bhxh.report'
    _description = 'Báo cáo BHXH hàng tháng'
    _order = 'period_year desc, period_month desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Tên báo cáo', compute='_compute_name', store=True)
    period_month = fields.Selection(
        [(str(m), f'Tháng {m}') for m in range(1, 13)],
        string='Tháng', required=True,
    )
    period_year = fields.Char(string='Năm', required=True, default=lambda self: str(fields.Date.today().year))
    batch_id = fields.Many2one(
        'hb.payslip.run',
        string='Payslip Batch',
        help='Batch payslip liên kết (state=close).',
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'hb.bhxh.report.line', 'report_id',
        string='Chi tiết BHXH',
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('computed', 'Đã tính'),
        ('submitted', 'Đã nộp'),
    ], default='draft', tracking=True)
    total_bhxh_ee = fields.Float(string='Tổng BHXH (NV)', digits=(16, 0), compute='_compute_totals', store=True)
    total_bhyt_ee = fields.Float(string='Tổng BHYT (NV)', digits=(16, 0), compute='_compute_totals', store=True)
    total_bhtn_ee = fields.Float(string='Tổng BHTN (NV)', digits=(16, 0), compute='_compute_totals', store=True)
    total_bhxh_er = fields.Float(string='Tổng BHXH (DN)', digits=(16, 0), compute='_compute_totals', store=True)
    total_bhyt_er = fields.Float(string='Tổng BHYT (DN)', digits=(16, 0), compute='_compute_totals', store=True)
    total_bhtn_er = fields.Float(string='Tổng BHTN (DN)', digits=(16, 0), compute='_compute_totals', store=True)
    employee_count = fields.Integer(string='Số NV', compute='_compute_totals', store=True)

    @api.depends('period_month', 'period_year')
    def _compute_name(self):
        for rec in self:
            rec.name = f'BHXH T{rec.period_month}/{rec.period_year}'

    @api.depends('line_ids.bhxh_ee', 'line_ids.bhyt_ee', 'line_ids.bhtn_ee',
                 'line_ids.bhxh_er', 'line_ids.bhyt_er', 'line_ids.bhtn_er')
    def _compute_totals(self):
        for rec in self:
            lines = rec.line_ids
            rec.total_bhxh_ee = sum(lines.mapped('bhxh_ee'))
            rec.total_bhyt_ee = sum(lines.mapped('bhyt_ee'))
            rec.total_bhtn_ee = sum(lines.mapped('bhtn_ee'))
            rec.total_bhxh_er = sum(lines.mapped('bhxh_er'))
            rec.total_bhyt_er = sum(lines.mapped('bhyt_er'))
            rec.total_bhtn_er = sum(lines.mapped('bhtn_er'))
            rec.employee_count = len(lines)

    # ─────────────────────────────────────────────────────────
    # Template Method: generate report lines from payslip batch
    # ─────────────────────────────────────────────────────────
    def action_compute(self):
        """Generate BHXH report lines from linked payslip batch."""
        for report in self:
            if report.state != 'draft':
                raise UserError(_('Chỉ tính báo cáo ở trạng thái Nháp.'))
            report._validate_batch()
            report.line_ids.unlink()
            report._generate_lines()
            report.state = 'computed'
            report.message_post(body=_(
                'Đã tính BHXH: %(n)s nhân viên.', n=report.employee_count,
            ))

    def _validate_batch(self):
        self.ensure_one()
        if not self.batch_id:
            raise ValidationError(_('Vui lòng chọn Payslip Batch trước khi tính.'))
        if self.batch_id.state != 'close':
            raise ValidationError(_('Payslip Batch phải ở trạng thái Done/Close.'))

    def _generate_lines(self):
        """Build one line per employee in the batch."""
        self.ensure_one()
        base_salary = self._get_regional_min_salary()
        cap = base_salary * INSURANCE_CAP_MULTIPLIER

        vals_list = []
        for slip in self.batch_id.slip_ids.filtered(lambda s: s.state == 'done'):
            emp = slip.employee_id
            insurance_base = self._get_insurance_base(slip, cap)
            vals_list.append({
                'report_id': self.id,
                'employee_id': emp.id,
                'employee_code': getattr(emp, 'x_employee_code', '') or '',
                'social_insurance_no': getattr(emp, 'x_social_insurance_no', '') or '',
                'insurance_base': insurance_base,
                'bhxh_ee': insurance_base * BHXH_RATE_EE,
                'bhyt_ee': insurance_base * BHYT_RATE_EE,
                'bhtn_ee': insurance_base * BHTN_RATE_EE,
                'bhxh_er': insurance_base * BHXH_RATE_ER,
                'bhyt_er': insurance_base * BHYT_RATE_ER,
                'bhtn_er': insurance_base * BHTN_RATE_ER,
            })
        if vals_list:
            self.env['hb.bhxh.report.line'].create(vals_list)

    def _get_insurance_base(self, payslip, cap):
        """Determine insurance base from contract, respecting policy."""
        contract = payslip.contract_id
        policy = getattr(contract, 'x_insurance_policy', 'standard') or 'standard'
        if policy == 'none':
            return 0.0
        base = getattr(contract, 'x_insurance_base', 0) or contract.wage or 0
        return min(base, cap)

    def _get_regional_min_salary(self):
        """Return regional minimum salary for insurance cap calculation."""
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'hocba_payroll.regional_min_salary', '2340000'
        ))

    def action_mark_submitted(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('Chỉ nộp báo cáo ở trạng thái Đã tính.'))
            rec.state = 'submitted'
            rec.message_post(body=_('Báo cáo BHXH đã được đánh dấu Đã nộp.'))

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
            'total_bhxh_ee': self.total_bhxh_ee,
            'total_bhyt_ee': self.total_bhyt_ee,
            'total_bhtn_ee': self.total_bhtn_ee,
            'total_bhxh_er': self.total_bhxh_er,
            'total_bhyt_er': self.total_bhyt_er,
            'total_bhtn_er': self.total_bhtn_er,
            'lines': [l._to_api_dict() for l in self.line_ids],
        }
