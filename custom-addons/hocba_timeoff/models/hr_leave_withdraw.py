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
from odoo import _, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError

# Trạng thái đơn còn "chờ duyệt" — đồng bộ với controllers.main.PENDING_STATES.
_SELF_CANCEL_STATES = ('confirm', 'validate1')


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

    def action_timeoff_self_cancel(self, employee):
        """Chủ đơn tự rút đơn CHỜ DUYỆT (self-service SPA).

        Kiểm đúng chủ đơn (`employee`) + đơn còn chờ duyệt, rồi xoá.

        Xoá phải chạy với env.user = SUPERUSER (OdooBot, đã thuộc
        group_hr_holidays_user) để vượt chặn core `_unlink_if_correct_states`
        ("không xoá được đơn nghỉ trong quá khứ") — NV vẫn phải rút được đơn ĐÃ
        QUÁ HẠN mà chưa được duyệt. LƯU Ý: `.sudo()` KHÔNG đủ — trong Odoo 19
        sudo chỉ bật cờ su (bỏ ACL/record-rule) nhưng GIỮ NGUYÊN env.user, nên
        `has_group()` trong chặn core vẫn đọc quyền của NV thường → vẫn bị chặn.
        `with_user(SUPERUSER_ID)` mới đổi thật env.user. An toàn vì phạm vi
        (đúng chủ đơn + đúng trạng thái) đã kiểm ngay tại đây.

        Gọi với recordset đã .sudo() (từ controller) để đọc field/quan hệ
        không vướng ACL; quyền thực tế do `employee` truyền vào quyết định.
        """
        self.ensure_one()
        if not employee or self.employee_id.id != employee.id:
            raise AccessError(_("Bạn không phải chủ đơn nghỉ này."))
        if self.state not in _SELF_CANCEL_STATES:
            raise UserError(_("Chỉ rút được đơn đang chờ duyệt."))
        # Báo GV thay (đơn chờ duyệt: lịch chưa đổi nên chỉ cần báo hủy).
        for r in self.teaching_resolution_ids.filtered(
                lambda x: x.resolution == 'substitute'
                and x.state in ('pending', 'accepted')):
            self._notify_sub_cancelled(r)
        self.with_user(SUPERUSER_ID).unlink()
