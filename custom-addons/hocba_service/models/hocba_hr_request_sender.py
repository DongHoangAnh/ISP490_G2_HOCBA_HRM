from odoo import fields, models


class HocbaHrRequestSender(models.Model):
    """Danh tính người gửi — TÁCH KHỎI đơn để ẩn danh có hiệu lực thật.

    ⚠️ QUAN TRỌNG (SPEC SVC §3.2, §4.2 lớp L1):
    - Model này **không có một dòng nào** trong ir.model.access.csv ⇒ KHÔNG group
      nào đọc được, kể cả hr.group_hr_manager và kể cả khi mở /odoo backend hay
      gọi XML-RPC. Chỉ .sudo() trong code truy cập được.
    - KHÔNG khai ir.ui.view / ir.actions.act_window cho model này.
    - KHÔNG khai One2many ngược từ hocba.hr.request sang đây: một field trên đơn
      là đủ để HR biết có bảng danh tính và mò ra id.
    Thêm ACL cho bất kỳ group nào = phá vỡ toàn bộ tính ẩn danh của module.
    """
    _name = 'hocba.hr.request.sender'
    _description = 'Danh tính người gửi đơn dịch vụ (không cấp ACL cho group nào)'
    _rec_name = 'request_id'

    request_id = fields.Many2one(
        'hocba.hr.request', string='Đơn', required=True,
        ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    user_id = fields.Many2one(
        'res.users', string='Tài khoản', required=True,
        ondelete='cascade', index=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban lúc gửi',
        help='Phòng thực tế của NV lúc gửi — chỉ dùng cho thống kê tổng hợp, '
             'không bao giờ trả ra API.')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _request_uniq = models.Constraint(
        'unique (request_id)',
        'Mỗi đơn chỉ có một người gửi!',
    )
