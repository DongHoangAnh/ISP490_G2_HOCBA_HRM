# ============================================================
# Duyệt đơn nghỉ của giáo viên — gắn xử lý buổi dạy vào vòng đời hr.leave.
#
#  - Chặn DUYỆT khi còn buổi "đổi GV dạy thay" chưa được GV thay đồng ý.
#  - Khi duyệt xong (state='validate'): ghi thay đổi lịch dạy vào Neon
#       class_off  → buổi 'cancelled'
#       substitute → buổi đổi sang GV thay, 'substituted'
#  - Khi từ chối/rút đơn đã duyệt (action_refuse): revert buổi về GV gốc/'planned'.
# Lịch dạy chỉ đổi tại bước duyệt → đơn bị từ chối/hủy không làm hỏng lịch thật.
# Owner: Nhật Anh. Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict §5.
# ============================================================
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    teaching_resolution_ids = fields.One2many(
        'hocba.leave.session.resolution', 'leave_id',
        string='Xử lý buổi dạy', copy=False,
    )

    def action_approve(self, check_state=True):
        # Gate: không duyệt khi còn dạy thay chưa được GV thay đồng ý (BR).
        for leave in self:
            pending = leave.teaching_resolution_ids.filtered(
                lambda r: r.resolution == 'substitute' and r.state != 'accepted')
            if pending:
                raise ValidationError(_(
                    'Đơn của %(name)s còn %(n)d buổi đổi giáo viên dạy thay '
                    'chưa được giáo viên thay đồng ý — chưa thể duyệt.',
                    name=leave.employee_id.name, n=len(pending)))
        res = super().action_approve(check_state=check_state)
        # Áp thay đổi lịch dạy cho đơn đã duyệt cuối cùng (state='validate').
        for leave in self.filtered(lambda l: l.state == 'validate'):
            leave._apply_teaching_changes()
        return res

    def action_refuse(self):
        # Chụp trước tập đơn ĐÃ ÁP lịch (state validate) — super() sẽ đổi state.
        applied = self.filtered(lambda l: l.state == 'validate')
        res = super().action_refuse()
        for leave in self:
            leave._revert_teaching_changes(was_applied=leave in applied)
        return res

    def _apply_teaching_changes(self):
        """Ghi thay đổi lịch dạy vào Neon khi đơn được duyệt."""
        self.ensure_one()
        for r in self.teaching_resolution_ids:
            session = r.session_id
            if r.resolution == 'class_off':
                session.sudo().write({
                    'state': 'cancelled', 'source_leave_id': self.id})
            elif r.resolution == 'substitute' and r.state == 'accepted':
                session.sudo().write({
                    'employee_id': r.substitute_id.id,
                    'state': 'substituted', 'source_leave_id': self.id})

    def _revert_teaching_changes(self, was_applied=True):
        """Đơn đã duyệt bị từ chối/rút → trả lịch dạy về chủ liền trước.
        Đơn chờ duyệt (chưa áp lịch) → bỏ qua. Chặn nếu buổi đã được giao tiếp
        xuống dưới (phải gỡ chuỗi sau trước)."""
        self.ensure_one()
        if not was_applied:
            return
        for r in self.teaching_resolution_ids:
            # Resolution đã ở trạng thái cuối (đã trả / GV thay từ chối) thì buổi
            # đã được pop/đổi chủ từ trước — bỏ qua để không chặn nhầm khi đơn
            # bị từ chối lúc trả buổi (buổi có thể đã gắn source sang đơn dưới).
            if r.state in ('returned', 'declined'):
                continue
            session = r.session_id
            if session.source_leave_id and session.source_leave_id.id != self.id:
                raise ValidationError(_(
                    'Không thể hủy/từ chối: buổi %s đã được giao tiếp cho giáo '
                    'viên khác. Cần gỡ các thay đổi phía sau trước.',
                    session.display_name))
            if session.source_leave_id.id == self.id:
                session.sudo()._pop_handover(r)
                if r.resolution == 'substitute' and r.state == 'accepted':
                    self._notify_sub_cancelled(r)

    def _notify_sub_cancelled(self, resolution):
        """Báo GV thay khi đơn (đã/đang nhờ dạy thay) bị hủy/rút."""
        sub_user = resolution.substitute_id.sudo().user_id
        if not sub_user:
            return
        self.env['hb.leave.notification'].sudo().create({
            'recipient_id': sub_user.id,
            'leave_id': self.id,
            'kind': 'sub_cancelled',
            'title': 'Yêu cầu dạy thay đã hủy',
            'body': '%s đã hủy/rút đơn — bạn không cần dạy thay buổi %s nữa.' % (
                self.employee_id.sudo().name,
                resolution.session_id.display_name),
        })


class HbLeaveNotification(models.Model):
    """Mở rộng 'kind' chuông cho 3 sự kiện dạy thay."""
    _inherit = 'hb.leave.notification'

    kind = fields.Selection(
        selection_add=[
            ('sub_request', 'Yêu cầu dạy thay'),
            ('sub_accepted', 'GV thay đồng ý'),
            ('sub_declined', 'GV thay từ chối'),
            ('sub_cancelled', 'Yêu cầu dạy thay đã hủy'),
            ('sub_returned', 'GV thay đã trả lại buổi'),
        ],
        ondelete={
            'sub_request': 'cascade',
            'sub_accepted': 'cascade',
            'sub_declined': 'cascade',
            'sub_cancelled': 'cascade',
            'sub_returned': 'cascade',
        },
    )
