from odoo import models, fields, api


class ShiftAttendance(models.Model):
    """Chấm công theo CA (ctv/ot) — 1 bản ghi/ca. Tách khỏi hocba.attendance
    (chỉ dùng cho official ngày thường). Giờ công lấy từ check_in/check_out thực tế."""
    _name = 'hocba.shift.attendance'
    _description = 'Chấm công theo ca'
    _order = 'check_in desc'

    shift_id = fields.Many2one(
        'hocba.work_shift', string='Ca', required=True,
        ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        related='shift_id.employee_id', store=True, index=True)
    check_in = fields.Datetime(string='Giờ vào')
    check_out = fields.Datetime(string='Giờ ra')
    check_in_photo = fields.Text(string='Ảnh vào')
    check_out_photo = fields.Text(string='Ảnh ra')
    check_in_lat = fields.Float(string='Lat vào', digits=(10, 7))
    check_in_lng = fields.Float(string='Lng vào', digits=(10, 7))
    check_out_lat = fields.Float(string='Lat ra', digits=(10, 7))
    check_out_lng = fields.Float(string='Lng ra', digits=(10, 7))
    check_in_face_score = fields.Float(string='Điểm khuôn mặt vào')
    check_out_face_score = fields.Float(string='Điểm khuôn mặt ra')
    face_suspect = fields.Boolean(string='Nghi ngờ khuôn mặt')
    out_of_zone = fields.Boolean(string='Ngoài vùng')
    out_of_window = fields.Boolean(string='Ngoài cửa sổ ca')
    worked_hours = fields.Float(
        string='Số giờ chấm', compute='_compute_worked_hours', store=True,
        help='check_out - check_in (giờ); 0 nếu thiếu mốc.')

    _shift_uniq = models.Constraint(
        'unique(shift_id)',
        'Mỗi ca chỉ có một bản ghi chấm công.',
    )

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.worked_hours = (rec.check_out - rec.check_in).total_seconds() / 3600.0
            else:
                rec.worked_hours = 0.0
