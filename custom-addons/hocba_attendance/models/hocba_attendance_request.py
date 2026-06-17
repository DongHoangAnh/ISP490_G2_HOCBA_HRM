from odoo import models, fields


class AttendanceRequest(models.Model):
    """Đơn xin sửa/tạo bản ghi chấm công cho 1 ngày (Gói 3).
    user gửi (state=pending) → manager duyệt (chỉnh giờ được) hoặc từ chối.
    Duyệt thì áp vào hocba.attendance (sửa bản ghi có sẵn / tạo nếu ngày thiếu)."""
    _name = 'hocba.attendance.request'
    _description = 'Đơn chấm công'
    _order = 'create_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    request_date = fields.Date(string='Ngày công', required=True)
    attendance_id = fields.Many2one(
        'hocba.attendance', string='Bản ghi', ondelete='set null',
        help='Bản ghi cần sửa; rỗng = ngày thiếu (duyệt thì tạo mới).')
    proposed_check_in = fields.Datetime(string='Giờ vào đề xuất')
    proposed_check_out = fields.Datetime(string='Giờ ra đề xuất')
    reason = fields.Text(string='Lý do', required=True)
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True)
