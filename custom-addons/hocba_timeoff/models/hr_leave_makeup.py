# ============================================================
# Đơn "xin nghỉ bù" — nhân viên nghỉ hôm đó nhưng quên nộp đơn, nay nộp bù
# cho ngày đã qua. Cờ này tách khỏi "quá hạn duyệt" (hr_leave_lapsed):
#   - Quá hạn duyệt = đơn nộp trước, người duyệt để qua ngày nghỉ mới xử lý.
#   - Xin nghỉ bù   = nhân viên chủ động nộp muộn → KHÔNG phải người duyệt trễ.
# Vì vậy đơn nghỉ bù không vào bảng "Kiểm duyệt phát sinh", không lên chuông
# CRON-TO-002 và không hiện tag "Quá hạn" ở tab Chờ duyệt.
# Owner: Nhật Anh.
# ============================================================
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrLeaveMakeup(models.Model):
    _inherit = 'hr.leave'

    x_is_makeup = fields.Boolean(
        string='Xin nghỉ bù', default=False,
        help='Nhân viên tự khai đơn nộp bù cho ngày nghỉ đã qua. '
             'Đơn nghỉ bù không bị tính là "quá hạn duyệt".',
    )

    @api.constrains('x_is_makeup', 'request_date_from')
    def _check_makeup_only_for_past(self):
        """Chỉ ngày nghỉ ĐÃ QUA mới nộp bù được — nếu không, cờ này thành lối
        thoát khỏi thống kê quá hạn cho mọi đơn."""
        for leave in self:
            if not leave.x_is_makeup or not leave.request_date_from:
                continue
            if leave.request_date_from >= fields.Date.context_today(leave):
                raise ValidationError(_(
                    'Chỉ đơn có ngày nghỉ trong quá khứ mới được đánh dấu '
                    '"xin nghỉ bù".'))
