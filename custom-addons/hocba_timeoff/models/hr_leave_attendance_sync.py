# Task 1 — Nối vòng đời đơn nghỉ với bảng chấm công:
#   duyệt (state -> validate) sinh bản ghi; từ chối/rút gỡ bản ghi (Task 6).
from odoo import models


class HrLeaveAttendanceSync(models.Model):
    _inherit = 'hr.leave'

    def _action_validate(self, check_state=True):
        res = super()._action_validate(check_state=check_state)
        Att = self.env['hocba.attendance']
        for leave in self.filtered(lambda l: l.state == 'validate'):
            Att._generate_leave_attendance(leave)
        return res
