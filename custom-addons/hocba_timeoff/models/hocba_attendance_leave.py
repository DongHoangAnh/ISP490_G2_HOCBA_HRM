# Task 1 — Tích hợp Nghỉ phép ↔ Chấm công. Mở rộng hocba.attendance:
#   - phân loại nguồn bản ghi (chấm công thật / sinh từ đơn nghỉ)
#   - chặn check-in ngày nghỉ cả ngày, sinh/gỡ bản ghi theo vòng đời đơn
#   - ép công + trạng thái cho ngày nghỉ (có/không lương)
from odoo import fields, models
from odoo.exceptions import UserError


class HocbaAttendanceLeave(models.Model):
    _inherit = 'hocba.attendance'

    source = fields.Selection(
        [('checkin', 'Chấm công'), ('leave', 'Nghỉ phép')],
        string='Nguồn', default='checkin', required=True, index=True,
        help='checkin = NV chấm công thật; leave = bản ghi sinh từ đơn nghỉ cả ngày.')
    leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ', ondelete='set null', index=True)
    leave_half = fields.Selection(
        [('am', 'Sáng'), ('pm', 'Chiều')], string='Buổi nghỉ')
    leave_is_paid = fields.Boolean(
        string='Nghỉ có lương', help='Snapshot loại nghỉ có lương lúc sinh bản ghi.')

    # ---- Tra đơn nghỉ ------------------------------------------------------
    def _leave_day_bounds(self, leave):
        d0 = leave.request_date_from or (leave.date_from and leave.date_from.date())
        d1 = leave.request_date_to or (leave.date_to and leave.date_to.date())
        return d0, d1

    def _leave_is_half_day(self, leave):
        """Nửa ngày = đơn 1 ngày, cùng buổi sáng/chiều. Đơn nhiều ngày -> cả ngày."""
        return bool(leave.request_unit_half
                    and leave.request_date_from_period
                    and leave.request_date_from_period == leave.request_date_to_period)

    def _approved_full_day_leave(self, employee, day):
        """Đơn nghỉ CẢ NGÀY đã duyệt phủ `day` (hoặc False)."""
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'validate')])
        for lv in leaves:
            d0, d1 = self._leave_day_bounds(lv)
            if d0 and d1 and d0 <= day <= d1 and not self._leave_is_half_day(lv):
                return lv
        return False

    def _assert_not_on_full_day_leave(self, employee):
        tz = employee.user_id.tz or self.env.user.tz or 'UTC'
        today = fields.Datetime.context_timestamp(
            self.with_context(tz=tz), fields.Datetime.now()).date()
        if self._approved_full_day_leave(employee, today):
            raise UserError('on_approved_leave')

    def _assert_check_allowed(self, employee, kind):
        self._assert_not_on_full_day_leave(employee)   # nghỉ trước, rồi luật cũ
        return super()._assert_check_allowed(employee, kind)

    def _assert_shift_check_allowed(self, employee, kind):
        self._assert_not_on_full_day_leave(employee)
        return super()._assert_shift_check_allowed(employee, kind)
