# ============================================================
# Phase 12 — Đơn lỡ hạn duyệt (qua ngày bắt đầu nghỉ mà vẫn chờ duyệt).
# Cờ lỡ hạn + đối chiếu chấm công TÍNH SỐNG trong controller (không lưu DB)
# — xem _lapsed_info ở controllers/main.py. DB chỉ giữ 1 field chống báo
# chuông lặp cho cron CRON-TO-002. Owner: Nhật Anh.
# ============================================================
from odoo import fields, models


class HrLeaveLapsed(models.Model):
    _inherit = 'hr.leave'

    x_lapsed_notified = fields.Boolean(
        string='Đã báo lỡ hạn duyệt', default=False,
        help='Cron đã bắn chuông "đơn lỡ hạn" cho người duyệt (chỉ báo 1 lần).',
    )


class HbLeaveNotification(models.Model):
    """Mở rộng selection 'kind' của chuông cho sự kiện đơn lỡ hạn duyệt."""
    _inherit = 'hb.leave.notification'

    kind = fields.Selection(
        selection_add=[('lapsed', 'Lỡ hạn duyệt')],
        ondelete={'lapsed': 'cascade'},
    )
