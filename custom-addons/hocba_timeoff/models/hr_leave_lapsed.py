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
    # Chuông đã hợp nhất sang hb.notification (module hocba_notify): 'kind' là
    # Char tự do nên KHÔNG cần selection_add cho 'lapsed'. Level map ở
    # _KIND_LEVEL (controllers/main.py).
