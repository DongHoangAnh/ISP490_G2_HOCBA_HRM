# Task 1 — Nối vòng đời đơn nghỉ với bảng chấm công:
#   - duyệt (state -> validate): sinh bản ghi / stamp bản ghi có sẵn;
#   - từ chối/rút (action_refuse — kể cả rút đơn Phase 7 gọi action_refuse):
#     xoá bản ghi tự sinh, gỡ stamp khỏi bản ghi chấm công thật.
from odoo import models


class HrLeaveAttendanceSync(models.Model):
    _inherit = 'hr.leave'

    def _action_validate(self, check_state=True):
        res = super()._action_validate(check_state=check_state)
        Att = self.env['hocba.attendance']
        for leave in self.filtered(lambda l: l.state == 'validate'):
            Att._generate_leave_attendance(leave)
        return res

    def action_refuse(self):
        res = super().action_refuse()
        Att = self.env['hocba.attendance']
        for leave in self:
            Att._remove_leave_attendance(leave)
        return res
