# ============================================================
# Dòng xử lý buổi dạy bị ảnh hưởng bởi đơn nghỉ của giáo viên.
#
# Mỗi buổi dạy trùng khoảng nghỉ = 1 dòng gắn vào hr.leave, với 2 cách xử lý:
#   - class_off  : cả lớp cùng nghỉ (hủy buổi) — chốt ngay (state='accepted').
#   - substitute : đổi GV dạy thay — chờ GV thay đồng ý (state='pending').
# Lịch dạy thật chỉ bị thay đổi khi đơn được DUYỆT (xem step 4).
# Owner: Nhật Anh. Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict §3.2.
# ============================================================
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HocbaLeaveSessionResolution(models.Model):
    _name = 'hocba.leave.session.resolution'
    _description = 'Xử lý buổi dạy khi giáo viên nghỉ'
    _order = 'leave_id, id'

    leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ',
        required=True, ondelete='cascade', index=True,
    )
    session_id = fields.Many2one(
        'hocba.teaching.session', string='Buổi dạy',
        required=True, ondelete='cascade',
    )
    resolution = fields.Selection(
        [('class_off', 'Cả lớp cùng nghỉ'),
         ('substitute', 'Đổi giáo viên dạy thay')],
        string='Cách xử lý', required=True,
    )
    substitute_id = fields.Many2one(
        'hr.employee', string='Giáo viên dạy thay', ondelete='restrict',
        help='Bắt buộc khi chọn "Đổi giáo viên dạy thay".',
    )
    state = fields.Selection(
        [('pending', 'Chờ GV thay đồng ý'),
         ('accepted', 'Đã chốt'),
         ('declined', 'GV thay từ chối')],
        string='Trạng thái', required=True, index=True,
        help="'class_off' chốt ngay; 'substitute' chờ GV thay đồng ý. "
             "GV thay bận sau khi đã nhận thì tự xử lý tiến (hủy lớp / nhờ GV "
             "khác), KHÔNG trả lại buổi cho GV cũ.",
    )
    decided_at = fields.Datetime(string='Thời điểm phản hồi', copy=False)
    decline_reason = fields.Char(string='Lý do từ chối', copy=False)

    _leave_session_uniq = models.Constraint(
        'unique (leave_id, session_id)',
        'Mỗi buổi dạy chỉ có một cách xử lý trong một đơn nghỉ.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('state'):
                vals['state'] = ('accepted'
                                 if vals.get('resolution') == 'class_off'
                                 else 'pending')
        return super().create(vals_list)

    @api.constrains('resolution', 'substitute_id', 'leave_id')
    def _check_substitute(self):
        for rec in self:
            if rec.resolution != 'substitute':
                continue
            if not rec.substitute_id:
                raise ValidationError(_(
                    'Phải chọn giáo viên dạy thay cho buổi "%s".',
                    rec.session_id.display_name))
            if rec.substitute_id == rec.leave_id.employee_id:
                raise ValidationError(_(
                    'Giáo viên dạy thay phải khác người xin nghỉ.'))
