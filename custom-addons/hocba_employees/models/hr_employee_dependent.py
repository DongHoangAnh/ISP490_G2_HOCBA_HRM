from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Người phụ thuộc (giảm trừ gia cảnh)'
    _order = 'employee_id, date_start'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Họ tên NPT', required=True)
    relationship = fields.Selection(
        selection=[
            ('spouse', 'Vợ/Chồng'),
            ('child', 'Con'),
            ('parent', 'Cha/Mẹ'),
            ('sibling', 'Anh/Chị/Em'),
            ('other', 'Khác'),
        ],
        string='Quan hệ', required=True)
    birthday = fields.Date(string='Ngày sinh', required=True)
    national_id = fields.Char(string='Số CCCD/Hộ chiếu')
    date_start = fields.Date(string='Ngày bắt đầu giảm trừ', required=True)
    date_end = fields.Date(string='Ngày kết thúc')
    notes = fields.Text(string='Ghi chú')

    @api.constrains('birthday', 'date_start', 'date_end')
    def _check_dates(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.birthday and rec.birthday > today:
                raise ValidationError(_('Ngày sinh NPT không được sau hôm nay.'))
            if rec.date_start and rec.date_start > today:
                raise ValidationError(_('Ngày bắt đầu giảm trừ không được sau hôm nay.'))
            if rec.date_end and rec.date_start and rec.date_end <= rec.date_start:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu.'))
