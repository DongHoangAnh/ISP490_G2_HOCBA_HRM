from odoo import fields, models

AUTHOR_ROLE_SEL = [
    ('sender', 'Người gửi'),
    ('handler', 'Người xử lý'),
    ('system', 'Hệ thống'),
]


class HocbaHrRequestMessage(models.Model):
    """Hội thoại 2 chiều trên đơn (SPEC SVC §3.3).

    Không dùng mail.thread/chatter vì mail.message.author_id không ẩn được
    (ACL mail.message mở cho base.group_user, chatter render ở backend) ⇒ đơn
    ẩn danh sẽ lộ người gửi ngay dòng đầu tiên.
    """
    _name = 'hocba.hr.request.message'
    _description = 'Tin nhắn trên đơn dịch vụ nhân sự'
    _order = 'create_date asc, id asc'

    request_id = fields.Many2one(
        'hocba.hr.request', string='Đơn', required=True,
        ondelete='cascade', index=True)
    author_role = fields.Selection(
        AUTHOR_ROLE_SEL, string='Vai trò người viết', required=True)
    author_id = fields.Many2one(
        'res.users', string='Người viết',
        help='Luôn ghi để phục vụ điều tra chính thức. Serializer CHỈ trả tên '
             'ra ngoài khi author_role != "sender" hoặc đơn không ẩn danh '
             '(BR-SVC-08).')
    body = fields.Text(string='Nội dung', required=True)
    is_internal = fields.Boolean(
        string='Ghi chú nội bộ', default=False,
        help='BR-SVC-07: chỉ người xử lý/HR thấy, người gửi không thấy.')
