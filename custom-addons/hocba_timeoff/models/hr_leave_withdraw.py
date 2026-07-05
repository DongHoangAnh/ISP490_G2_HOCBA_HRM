# Phase 7 — Rút đơn nghỉ đã duyệt (có phê duyệt lại).
#
# Chủ đơn yêu cầu rút đơn validate → đơn vào trạng thái "chờ duyệt rút" (lưu ở
# x_withdraw_state='pending'). Người duyệt phạm vi (HR/Admin/Trưởng phòng):
#   - approve  → leave.action_refuse() → virtual_remaining_leaves tự khôi phục
#                (refused không vào leaves_taken). x_withdraw_state giữ 'pending'
#                để FE phân biệt "hủy do rút" với "từ chối ban đầu" (đối chiếu
#                chatter audit).
#   - reject   → x_withdraw_state về 'none', đơn giữ nguyên 'validate'.
#
# Không lưu trạng thái trung gian bằng state mới (sẽ vỡ workflow Odoo); dùng
# field bổ sung x_withdraw_state là an toàn nhất.
from odoo import fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    x_withdraw_state = fields.Selection(
        [('none', 'Không có'),
         ('pending', 'Chờ duyệt rút')],
        string='Trạng thái rút đơn',
        default='none', required=True, index=True,
    )
    x_withdraw_reason = fields.Text(
        string='Lý do rút đơn',
    )


class HbLeaveNotification(models.Model):
    """Mở rộng selection 'kind' của thông báo cho 3 sự kiện rút đơn."""
    _inherit = 'hb.leave.notification'

    kind = fields.Selection(
        selection_add=[
            ('withdraw_pending', 'Chờ duyệt rút'),
            ('withdraw_approved', 'Đã duyệt rút'),
            ('withdraw_refused', 'Từ chối rút'),
        ],
        ondelete={
            'withdraw_pending': 'cascade',
            'withdraw_approved': 'cascade',
            'withdraw_refused': 'cascade',
        },
    )
