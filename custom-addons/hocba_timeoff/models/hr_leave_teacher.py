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
        res = super().action_refuse()
        for leave in self:
            leave._revert_teaching_changes()
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

    def _revert_teaching_changes(self):
        """Trả lịch dạy về GV gốc / 'planned' khi đơn đã duyệt bị hủy/từ chối."""
        self.ensure_one()
        for r in self.teaching_resolution_ids:
            session = r.session_id
            if session.source_leave_id.id != self.id:
                continue  # buổi không bị đơn này đổi → bỏ qua
            session.sudo().write({
                'employee_id': (session.original_employee_id.id
                                or session.employee_id.id),
                'state': 'planned', 'source_leave_id': False})


class HbLeaveNotification(models.Model):
    """Mở rộng 'kind' chuông cho 3 sự kiện dạy thay."""
    _inherit = 'hb.leave.notification'

    kind = fields.Selection(
        selection_add=[
            ('sub_request', 'Yêu cầu dạy thay'),
            ('sub_accepted', 'GV thay đồng ý'),
            ('sub_declined', 'GV thay từ chối'),
        ],
        ondelete={
            'sub_request': 'cascade',
            'sub_accepted': 'cascade',
            'sub_declined': 'cascade',
        },
    )
