# Task 1 — Tích hợp Nghỉ phép ↔ Chấm công. Mở rộng hocba.attendance:
#   - phân loại nguồn bản ghi (chấm công thật / sinh từ đơn nghỉ)
#   - chặn check-in ngày nghỉ cả ngày, sinh/gỡ bản ghi theo vòng đời đơn
#   - ép công + trạng thái cho ngày nghỉ (có/không lương)
from odoo import fields, models


class HocbaAttendanceLeave(models.Model):
    _inherit = 'hocba.attendance'

    source = fields.Selection(
        [('checkin', 'Chấm công'), ('leave', 'Nghỉ phép')],
        string='Nguồn', default='checkin', required=True, index=True,
        help='checkin = NV chấm công thật; leave = bản ghi sinh từ đơn nghỉ cả ngày.')
    leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ', ondelete='set null', index=True)
    leave_half = fields.Selection(
        [('am', 'Sáng'), ('pm', 'Chiều')], string='Buổi nghỉ')
    leave_is_paid = fields.Boolean(
        string='Nghỉ có lương', help='Snapshot loại nghỉ có lương lúc sinh bản ghi.')
