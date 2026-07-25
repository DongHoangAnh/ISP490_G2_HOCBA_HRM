# Task 1 — Chấm công nhận thêm "ngày công ty đi làm bù" (hb.work.day) mà HR
# khai bên Nghỉ phép, ngoài 7 cờ workday_mon..sun sẵn có.
from odoo import models


class HocbaAttendancePolicy(models.Model):
    _inherit = 'hocba.attendance.policy'

    def is_workday(self, dt_local):
        if super().is_workday(dt_local):
            return True
        # Hàm gốc chỉ dùng .weekday() nên nhận CẢ date lẫn datetime — giữ đúng
        # hợp đồng đó, đừng thu hẹp về datetime (hocba_hrm truyền date thuần).
        day = dt_local.date() if hasattr(dt_local, 'date') else dt_local
        return bool(self.env['hb.work.day'].sudo().search_count(
            [('date', '=', day)]))
