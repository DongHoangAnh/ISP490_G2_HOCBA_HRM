from odoo import fields, models


class HbNotification(models.Model):
    """Thêm nhóm 'Đánh giá' vào chuông thông báo dùng chung (hocba_notify)."""
    _inherit = 'hb.notification'

    category = fields.Selection(
        selection_add=[('review', 'Đánh giá')],
        ondelete={'review': 'cascade'})
