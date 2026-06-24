# ============================================================
# Thông báo in-app cho chuông Nghỉ phép (Phase 5). Owner: Nhật Anh.
#
# Vì sao KHÔNG dùng mail.message needaction của hr.leave làm nguồn chuông:
# trong Odoo 19 res.users.notification_type là field computed/stored, mặc định
# 'email' (chỉ user thuộc group mail.group_mail_notification_type_inbox mới là
# 'inbox'). Đa số tài khoản SPA không ở group đó → inbox needaction rỗng, chuông
# sẽ trống. Nên ta dùng 1 model thông báo riêng (giống hb.leave.adjustment) để
# chủ động, robust, không phụ thuộc tuỳ chọn nhận thông báo của user.
# Audit/lịch sử thao tác đơn vẫn dùng message_post (chatter) của hr.leave.
# ============================================================
from odoo import models, fields


class HbLeaveNotification(models.Model):
    """Một thông báo gửi tới 1 người dùng về 1 đơn nghỉ (cho chuông góc phải SPA).

    Sinh khi: tạo đơn → báo người duyệt phạm vi (kind='pending'); duyệt/từ chối
    → báo chủ đơn (kind='approved'/'refused'). Mỗi người đọc/đánh dấu đã đọc
    thông báo CỦA MÌNH (lọc theo recipient_id = uid). Mọi thao tác qua controller
    chạy sudo sau khi đã pin recipient = người đăng nhập."""
    _name = 'hb.leave.notification'
    _description = 'Thông báo nghỉ phép (chuông in-app)'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    recipient_id = fields.Many2one(
        'res.users', string='Người nhận',
        required=True, ondelete='cascade', index=True,
    )
    leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ',
        required=True, ondelete='cascade', index=True,
    )
    kind = fields.Selection(
        [('pending', 'Chờ duyệt'),
         ('approved', 'Đã duyệt'),
         ('refused', 'Từ chối')],
        string='Loại', required=True,
    )
    title = fields.Char(string='Tiêu đề', required=True)
    body = fields.Char(string='Nội dung')
    is_read = fields.Boolean(string='Đã đọc', default=False, index=True)
