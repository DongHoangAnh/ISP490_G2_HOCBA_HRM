# Task 1 — Tích hợp Nghỉ phép ↔ Chấm công. Mở rộng hocba.attendance:
#   - phân loại nguồn bản ghi (chấm công thật / sinh từ đơn nghỉ)
#   - chặn check-in ngày nghỉ cả ngày, sinh/gỡ bản ghi theo vòng đời đơn
#   - ép công + trạng thái cho ngày nghỉ (có/không lương)
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
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

    def _leave_blocks_attendance(self, leave):
        """Đơn nghỉ 'chiếm' cả ngày làm việc (chặn/ sinh chấm công).
        Loại 'Nghỉ Buổi Dạy' (session-leave) KHÔNG tính: GV chỉ nghỉ buổi dạy,
        vẫn đi làm — không chặn, không sinh bản ghi."""
        teaching_off = self.env.ref(
            'hocba_timeoff.hb_leave_type_teaching_off', raise_if_not_found=False)
        if teaching_off and leave.holiday_status_id == teaching_off:
            return False
        return not self._leave_is_half_day(leave)

    def _approved_full_day_leave(self, employee, day):
        """Đơn nghỉ CẢ NGÀY đã duyệt phủ `day` (hoặc False)."""
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'validate')])
        for lv in leaves:
            d0, d1 = self._leave_day_bounds(lv)
            if d0 and d1 and d0 <= day <= d1 and self._leave_blocks_attendance(lv):
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

    # ---- Sinh bản ghi cho nghỉ cả ngày ------------------------------------
    def _is_working_day(self, day, policy):
        return policy.is_workday(datetime.combine(day, time(0)))

    def _leave_checkin_utc(self, employee, day, policy):
        """check_in quy ước = day tại morning_start (giờ local NV) -> UTC naive."""
        # phải KHỚP _compute_date (base) để 'date' bản ghi ổn định
        tz = pytz.timezone(employee.user_id.tz or 'UTC')
        hours = policy.morning_start or 8.0
        local = tz.localize(datetime.combine(day, time(0)) + timedelta(hours=hours))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _generate_leave_attendance(self, leave):
        if not self._leave_blocks_attendance(leave):
            return  # nửa ngày + "Nghỉ Buổi Dạy": không sinh bản ghi
        d0, d1 = self._leave_day_bounds(leave)
        if not d0 or not d1:
            return
        Att = self.env['hocba.attendance'].sudo()
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        is_paid = not leave.holiday_status_id.unpaid
        emp = leave.employee_id
        cur = d0
        while cur <= d1:
            if self._is_working_day(cur, policy):
                exist = Att.search([('employee_id', '=', emp.id), ('date', '=', cur)], limit=1)
                if exist:
                    if exist.source == 'checkin' and 'rà soát' not in (exist.notes or ''):
                        exist.write({'notes': (exist.notes or '')
                            + '\n[Cảnh báo] Có đơn nghỉ cả ngày đã duyệt trùng ngày đã chấm công — cần HR rà soát.'})
                else:
                    Att.create({
                        'employee_id': emp.id,
                        'check_in': self._leave_checkin_utc(emp, cur, policy),
                        'source': 'leave', 'leave_id': leave.id,
                        'leave_is_paid': is_paid,
                        'notes': leave.holiday_status_id.name,
                    })
            cur += timedelta(days=1)

    # ---- Ép công + trạng thái cho bản ghi nghỉ ----------------------------
    @api.depends('check_in', 'check_out',
                 'source', 'leave_id', 'leave_is_paid', 'leave_half')
    def _compute_work_metrics(self):
        super()._compute_work_metrics()
        for rec in self:
            if rec.source == 'leave':
                rec.late_minutes = 0
                rec.early_leave_minutes = 0
                rec.missing_minutes = 0
                rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.afternoon_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.work_credit = rec.morning_credit + rec.afternoon_credit
            elif rec.leave_id and rec.leave_half:      # nửa ngày, có chấm công thật (Task 5)
                if rec.leave_half == 'am':
                    rec.late_minutes = 0
                    rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                else:
                    rec.early_leave_minutes = 0
                    rec.missing_minutes = 0
                    rec.afternoon_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.work_credit = rec.morning_credit + rec.afternoon_credit

    @api.depends('check_in', 'source', 'leave_is_paid')
    def _compute_status(self):
        super()._compute_status()
        Status = self.env['hocba.attendance.status']
        paid = Status.search([('code', '=', 'on_leave_paid')], limit=1)
        unpaid = Status.search([('code', '=', 'on_leave_unpaid')], limit=1)
        for rec in self:
            if rec.source == 'leave':
                rec.status_id = paid if rec.leave_is_paid else unpaid
