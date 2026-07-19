# Task 1 — Chấm công nhận thêm "ngày công ty đi làm bù" (hb.work.day) mà HR
# khai bên Nghỉ phép, ngoài 7 cờ workday_mon..sun sẵn có.
from odoo import models


class HocbaAttendancePolicy(models.Model):
    _inherit = 'hocba.attendance.policy'

    def is_workday(self, dt_local):
        if super().is_workday(dt_local):
            return True
        return bool(self.env['hb.work.day'].sudo().search_count(
            [('date', '=', dt_local.date())]))
