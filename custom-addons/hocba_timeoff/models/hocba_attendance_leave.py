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

    # ---- Nghỉ nửa ngày: gắn vào chấm công thật (Task 5) --------------------
    _HALF_LABEL = {'am': 'Nghỉ phép nửa buổi sáng', 'pm': 'Nghỉ phép nửa buổi chiều'}

    def _approved_half_day_leave(self, employee, day):
        """Đơn nghỉ NỬA NGÀY đã duyệt phủ `day` (hoặc False)."""
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'validate')])
        for lv in leaves:
            d0, d1 = self._leave_day_bounds(lv)
            if d0 and d1 and d0 <= day <= d1 and self._leave_is_half_day(lv):
                return lv
        return False

    def _stamp_half_day_leave(self):
        """Gắn thông tin nghỉ nửa ngày vào bản ghi chấm công thật (idempotent).
        Nhánh leave_half trong _compute_work_metrics sẽ miễn phạt + bù công
        đúng buổi nghỉ (0.5 nếu có lương)."""
        for record in self:
            if not record.date or record.source == 'leave':
                continue
            lv = self._approved_half_day_leave(record.employee_id, record.date)
            if not lv:
                continue
            half = lv.request_date_from_period
            note = self._HALF_LABEL.get(half, '')
            vals = {'leave_id': lv.id, 'leave_half': half,
                    'leave_is_paid': not lv.holiday_status_id.unpaid}
            if note and note not in (record.notes or ''):
                vals['notes'] = ((record.notes + '\n') if record.notes else '') + note
            record.write(vals)

    def _do_check(self, payload, kind):
        res = super()._do_check(payload, kind)
        rec = self.browse(res['record_id'])
        rec._stamp_half_day_leave()
        return res

    # ---- Sinh bản ghi cho nghỉ cả ngày ------------------------------------
    _CONFLICT_NOTE = ('[Cảnh báo] Có đơn nghỉ cả ngày đã duyệt trùng ngày '
                      'đã chấm công — cần HR rà soát.')

    def _is_working_day(self, day, policy):
        return policy.is_workday(datetime.combine(day, time(0)))

    def _leave_checkin_utc(self, employee, day, policy):
        """check_in quy ước = day tại morning_start (giờ local NV) -> UTC naive."""
        # phải KHỚP _compute_date (base) để 'date' bản ghi ổn định
        tz = pytz.timezone(employee.user_id.tz or 'UTC')
        hours = policy.morning_start or 8.0
        local = tz.localize(datetime.combine(day, time(0)) + timedelta(hours=hours))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _stamp_existing_for_half_day(self, leave):
        """Đơn nửa ngày duyệt MUỘN (NV đã chấm công trước trong khoảng nghỉ):
        stamp lại các bản ghi chấm công thật để miễn phạt/bù công."""
        d0, d1 = self._leave_day_bounds(leave)
        if not d0 or not d1:
            return
        recs = self.env['hocba.attendance'].sudo().search([
            ('employee_id', '=', leave.employee_id.id),
            ('date', '>=', d0), ('date', '<=', d1),
            ('source', '=', 'checkin')])
        recs._stamp_half_day_leave()

    def _generate_leave_attendance(self, leave):
        teaching_off = self.env.ref(
            'hocba_timeoff.hb_leave_type_teaching_off', raise_if_not_found=False)
        if teaching_off and leave.holiday_status_id == teaching_off:
            return  # nghỉ buổi dạy: GV vẫn đi làm, không đụng chấm công
        if self._leave_is_half_day(leave):
            self._stamp_existing_for_half_day(leave)
            return  # nửa ngày: không sinh bản ghi, chỉ stamp bản ghi có sẵn
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
                            + '\n' + self._CONFLICT_NOTE})
                else:
                    Att.create({
                        'employee_id': emp.id,
                        'check_in': self._leave_checkin_utc(emp, cur, policy),
                        'source': 'leave', 'leave_id': leave.id,
                        'leave_is_paid': is_paid,
                        'notes': leave.holiday_status_id.name,
                    })
            cur += timedelta(days=1)

    def _remove_leave_attendance(self, leave):
        """Gỡ dấu vết chấm công của một đơn nghỉ (khi từ chối/rút):
        bản ghi tự sinh -> xoá; bản ghi chấm công thật -> chỉ gỡ stamp."""
        recs = self.env['hocba.attendance'].sudo().search([('leave_id', '=', leave.id)])
        gen = recs.filtered(lambda r: r.source == 'leave')
        real = recs - gen
        gen.unlink()
        for r in real:
            notes = r.notes or ''
            for lab in self._HALF_LABEL.values():
                notes = notes.replace(lab, '')
            r.write({'leave_id': False, 'leave_half': False,
                     'leave_is_paid': False,
                     'notes': notes.strip('\n') or False})
        # Note cảnh báo trùng (đơn CẢ ngày duyệt sau khi đã chấm công) được
        # append vào bản ghi thật mà KHÔNG set leave_id -> gỡ theo khoảng ngày.
        # An toàn: Odoo chặn đơn nghỉ duyệt chồng ngày cùng NV, nên note trong
        # khoảng này chỉ có thể thuộc về CHÍNH đơn đang gỡ.
        d0, d1 = self._leave_day_bounds(leave)
        if d0 and d1:
            warned = self.env['hocba.attendance'].sudo().search([
                ('employee_id', '=', leave.employee_id.id),
                ('date', '>=', d0), ('date', '<=', d1),
                ('source', '=', 'checkin'),
                ('notes', 'like', self._CONFLICT_NOTE)])
            for r in warned:
                notes = (r.notes or '').replace(self._CONFLICT_NOTE, '')
                r.write({'notes': notes.strip('\n') or False})

    # ---- Ép công + trạng thái cho bản ghi nghỉ ----------------------------
    @api.depends('check_in', 'check_out',
                 'source', 'leave_id', 'leave_is_paid', 'leave_half')
    def _compute_work_metrics(self):
        super()._compute_work_metrics()
        policy = self.env['hocba.attendance.policy'].get_policy()
        std = policy.std_work_hours or 8.0
        aft_margin = policy.afternoon_margin_hours or 2.0
        for rec in self:
            if rec.source == 'leave':
                rec.late_minutes = 0
                rec.early_leave_minutes = 0
                rec.missing_minutes = 0
                rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.afternoon_credit = 0.5 if rec.leave_is_paid else 0.0
                rec.work_credit = rec.morning_credit + rec.afternoon_credit
            elif rec.leave_id and rec.leave_half:      # nửa ngày, có chấm công thật (Task 5)
                ci, co = rec.check_in, rec.check_out
                if rec.leave_half == 'am':
                    # Nghỉ SÁNG: miễn phạt trễ, buổi sáng tính theo đơn;
                    # buổi CHIỀU (buổi làm) chấm theo chuẩn NỬA ngày thay vì
                    # công thức cả ngày của base (ngưỡng 6h là bất khả thi
                    # với một buổi chiều ~4h).
                    rec.late_minutes = 0
                    rec.morning_credit = 0.5 if rec.leave_is_paid else 0.0
                    if ci:
                        rec.expected_check_out = ci + timedelta(hours=std / 2.0)
                    if ci and co:
                        worked_min = (co - ci).total_seconds() / 60.0
                        rec.afternoon_credit = 0.5 if (co - ci) >= timedelta(
                            hours=std / 2.0 - aft_margin / 2.0) else 0.0
                        rec.early_leave_minutes = max(0, int(round(
                            (rec.expected_check_out - co).total_seconds() / 60.0)))
                        rec.missing_minutes = max(0, min(240, int(round(
                            std / 2.0 * 60 - worked_min))))
                    else:
                        rec.afternoon_credit = 0.0
                        rec.early_leave_minutes = 0
                        rec.missing_minutes = 0
                else:
                    # Nghỉ CHIỀU: buổi sáng (buổi làm) đã đúng theo luật base
                    # (đến trước cutoff là đủ 0.5); buổi chiều tính theo ĐƠN
                    # (kể cả khi NV thực tế ở lại — HR đối soát nếu lệch).
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
