"""
Contract — standalone replacement for hr.contract (Enterprise).
Covers teaching hourly-rate config, allowances, and insurance.
"""
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
HOURLY_RATE_WARN_THRESHOLD = 1_000_000   # VND/h  (VR-009)
THRESHOLD_MIN = 0.0
THRESHOLD_MAX = 200.0                     # VR-003


class HbContract(models.Model):
    _name = 'hb.contract'
    _description = 'Hợp đồng lao động'
    _order = 'date_start desc'
    _inherit = ['mail.thread']

    # ── Core ─────────────────────────────────────────────────
    name = fields.Char(string='Tên hợp đồng', required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        index=True, ondelete='restrict',
    )
    date_start = fields.Date(string='Ngày bắt đầu', required=True)
    date_end = fields.Date(string='Ngày kết thúc')
    wage = fields.Float(
        string='Lương cơ bản',
        digits=(12, 0),
        help='Mức lương ghi trên hợp đồng.',
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('open', 'Đang hiệu lực'),
        ('close', 'Hết hạn'),
        ('cancel', 'Đã hủy'),
    ], string='Trạng thái', default='draft', tracking=True, index=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company,
    )

    # ── Insurance ────────────────────────────────────────────
    x_insurance_base = fields.Float(
        string='Lương đóng BH', digits=(12, 0),
        help='Cơ sở tính BHXH/BHYT/BHTN. Có thể KHÁC lương cơ bản.',
    )
    x_insurance_policy = fields.Selection([
        ('standard', 'BH theo định mức'),
        ('tnld_0_5', 'Đóng 0.5% BH TNLĐ'),
        ('none', 'Không đóng'),
    ], string='Chính sách BH', default='standard')
    x_dependent_count = fields.Integer(
        string='Số NPT (override)',
        help='Số người phụ thuộc giảm trừ. Để 0 sẽ lấy từ hồ sơ nhân viên.',
    )

    # ── Allowances (Phụ cấp) ─────────────────────────────────
    x_pc_seniority = fields.Float(
        string='PC thâm niên', digits=(12, 0),
    )
    x_pc_parking = fields.Float(
        string='PC gửi xe', digits=(12, 0),
    )
    x_pc_fuel = fields.Float(
        string='PC xăng xe', digits=(12, 0),
    )
    x_pc_position = fields.Float(
        string='PC chức vụ', digits=(12, 0),
    )
    x_sp_transport = fields.Float(
        string='HT đi lại', digits=(12, 0),
    )
    x_sp_phone = fields.Float(
        string='HT điện thoại', digits=(12, 0),
    )
    x_sp_meal = fields.Float(
        string='HT ăn ca', digits=(12, 0),
    )
    x_sp_uniform = fields.Float(
        string='HT trang phục', digits=(12, 0),
    )

    x_structure_id = fields.Many2one(
        'hb.salary.structure', string='Cấu trúc lương',
        help='STRUCT_OFFLINE hoặc STRUCT_ONLINE. Nếu trống sẽ tự xác định.',
    )

    # ── Teaching hourly-rate fields (PR-001) ─────────────────
    x_teaching_hourly_rate = fields.Float(
        string='Đơn giá giờ cơ bản', digits=(12, 0),
        help='Đơn giá 1 giờ dạy cơ bản (VND/h).',
    )
    x_rate_hsk_class = fields.Float(
        string='Đơn giá giờ HSK4+', digits=(12, 0),
        help='Đơn giá giờ cho lớp HSK cấp 4 trở lên (VND/h).',
    )
    x_rate_advanced_class = fields.Float(
        string='Đơn giá giờ lớp đặc biệt', digits=(12, 0),
    )
    x_standard_threshold = fields.Float(
        string='Ngưỡng giờ chuẩn/tháng', digits=(6, 2), default=60.0,
        help='Số giờ chuẩn mỗi tháng. Vượt ngưỡng sẽ tính bonus.',
    )
    x_extra_rate = fields.Float(
        string='Đơn giá giờ vượt ngưỡng', digits=(12, 0),
        help='Để trống → = đơn giá cơ bản × 1.25.',
    )
    x_has_fixed_base = fields.Boolean(
        string='Có lương cố định base', default=False,
    )
    x_fixed_base = fields.Float(
        string='Lương cố định', digits=(12, 0),
    )

    # ── Computed helper ──────────────────────────────────────
    x_effective_extra_rate = fields.Float(
        string='Đơn giá vượt ngưỡng (thực tế)',
        compute='_compute_effective_extra_rate', digits=(12, 0),
    )

    @api.depends('x_teaching_hourly_rate', 'x_extra_rate')
    def _compute_effective_extra_rate(self):
        for rec in self:
            if rec.x_extra_rate and rec.x_extra_rate > 0:
                rec.x_effective_extra_rate = rec.x_extra_rate
            else:
                rec.x_effective_extra_rate = rec.x_teaching_hourly_rate * 1.25

    # ── State transitions ────────────────────────────────────
    def action_open(self):
        for rec in self:
            rec.state = 'open'

    def action_close(self):
        for rec in self:
            rec.state = 'close'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    # ── Constraints (VR-001 .. VR-009) ───────────────────────
    @api.constrains('x_teaching_hourly_rate')
    def _check_hourly_rate_positive(self):
        for rec in self:
            if rec.x_teaching_hourly_rate and rec.x_teaching_hourly_rate < 0:
                raise ValidationError(
                    _('Đơn giá giờ phải lớn hơn 0.')
                )

    @api.constrains('x_rate_hsk_class', 'x_teaching_hourly_rate')
    def _check_hsk_rate_higher(self):
        for rec in self:
            if (rec.x_rate_hsk_class
                    and rec.x_teaching_hourly_rate
                    and rec.x_rate_hsk_class < rec.x_teaching_hourly_rate):
                _logger.warning(
                    'Contract %s: Đơn giá HSK (%.0f) < đơn giá cơ bản (%.0f)',
                    rec.name, rec.x_rate_hsk_class, rec.x_teaching_hourly_rate,
                )

    @api.constrains('x_standard_threshold')
    def _check_threshold_range(self):
        for rec in self:
            if rec.x_standard_threshold < THRESHOLD_MIN or rec.x_standard_threshold > THRESHOLD_MAX:
                raise ValidationError(
                    _('Ngưỡng giờ chuẩn phải trong khoảng %(min)s – %(max)s giờ/tháng.',
                      min=THRESHOLD_MIN, max=THRESHOLD_MAX)
                )

    @api.constrains('x_has_fixed_base', 'x_fixed_base')
    def _check_fixed_base_consistent(self):
        for rec in self:
            if rec.x_has_fixed_base and (not rec.x_fixed_base or rec.x_fixed_base <= 0):
                raise ValidationError(
                    _('Bật "Có lương cố định base" nhưng chưa nhập số tiền lương cố định.')
                )

    @api.constrains('x_teaching_hourly_rate')
    def _warn_high_hourly_rate(self):
        for rec in self:
            if rec.x_teaching_hourly_rate and rec.x_teaching_hourly_rate > HOURLY_RATE_WARN_THRESHOLD:
                _logger.warning(
                    'Contract %s: Đơn giá giờ %.0f vượt ngưỡng cảnh báo %s — cần HR Manager review.',
                    rec.name, rec.x_teaching_hourly_rate, HOURLY_RATE_WARN_THRESHOLD,
                )

    # ── API serialization ────────────────────────────────────
    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'employee_id': self.employee_id.id,
            'employee_name': self.employee_id.name,
            'date_start': str(self.date_start) if self.date_start else None,
            'date_end': str(self.date_end) if self.date_end else None,
            'wage': self.wage,
            'state': self.state,
            # Insurance
            'x_insurance_base': self.x_insurance_base,
            'x_insurance_policy': self.x_insurance_policy,
            'x_dependent_count': self.x_dependent_count,
            # Allowances
            'x_pc_seniority': self.x_pc_seniority,
            'x_pc_parking': self.x_pc_parking,
            'x_pc_fuel': self.x_pc_fuel,
            'x_pc_position': self.x_pc_position,
            'x_sp_transport': self.x_sp_transport,
            'x_sp_phone': self.x_sp_phone,
            'x_sp_meal': self.x_sp_meal,
            'x_sp_uniform': self.x_sp_uniform,
            'x_structure_id': self.x_structure_id.id if self.x_structure_id else None,
            'x_structure_code': self.x_structure_id.code if self.x_structure_id else None,
            # Teaching
            'x_teaching_hourly_rate': self.x_teaching_hourly_rate,
            'x_rate_hsk_class': self.x_rate_hsk_class,
            'x_rate_advanced_class': self.x_rate_advanced_class,
            'x_standard_threshold': self.x_standard_threshold,
            'x_extra_rate': self.x_extra_rate,
            'x_effective_extra_rate': self.x_effective_extra_rate,
            'x_has_fixed_base': self.x_has_fixed_base,
            'x_fixed_base': self.x_fixed_base,
        }
