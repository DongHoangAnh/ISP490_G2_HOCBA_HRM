"""
Work Entry — standalone replacement for hr.work.entry (Enterprise).
Records actual teaching hours logged by teachers.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HbWorkEntry(models.Model):
    _name = 'hb.work.entry'
    _description = 'Work Entry (Giờ dạy)'
    _order = 'date_start desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Mô tả', compute='_compute_name', store=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        index=True, ondelete='cascade',
    )
    work_entry_type_id = fields.Many2one(
        'hb.work.entry.type', string='Loại', required=True,
        index=True,
    )
    date_start = fields.Datetime(string='Bắt đầu', required=True)
    date_stop = fields.Datetime(string='Kết thúc', required=True)
    duration = fields.Float(
        string='Số giờ', digits=(8, 2),
        compute='_compute_duration', store=True, readonly=False,
    )
    x_class_level = fields.Selection([
        ('basic', 'Cơ bản'),
        ('intermediate', 'Trung cấp'),
        ('hsk4', 'HSK4'),
        ('hsk5', 'HSK5'),
        ('hsk6', 'HSK6'),
    ], string='Cấp lớp', default='basic',
       help='Cấp HSK của lớp — dùng để tính premium.',
    )
    x_class_code = fields.Char(string='Mã lớp')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('validated', 'Đã xác thực'),
        ('conflict', 'Xung đột'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', tracking=True, index=True)

    @api.depends('employee_id', 'work_entry_type_id', 'date_start')
    def _compute_name(self):
        for rec in self:
            emp = rec.employee_id.name or ''
            we_type = rec.work_entry_type_id.code or ''
            date = rec.date_start.strftime('%d/%m/%Y') if rec.date_start else ''
            rec.name = f'{emp} — {we_type} — {date}'

    @api.depends('date_start', 'date_stop')
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_stop:
                delta = rec.date_stop - rec.date_start
                rec.duration = delta.total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_stop and rec.date_stop < rec.date_start:
                raise ValidationError(_('Thời gian kết thúc phải sau thời gian bắt đầu.'))

    def action_validate(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'validated'

    def action_reset_draft(self):
        for rec in self:
            if rec.state in ('validated', 'conflict'):
                rec.state = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
