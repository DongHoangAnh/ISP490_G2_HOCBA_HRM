import logging
import calendar
from datetime import date

from odoo import models, api, _

_logger = logging.getLogger(__name__)


class HbTimeoffCron(models.AbstractModel):
    _name = 'hb.timeoff.cron'
    _description = 'HB Time Off — Scheduled Jobs'

    # Ngưỡng ngày bắt đầu nhắc nhở (cuối tháng): từ ngày 25 trở đi.
    _REMIND_FROM_DAY = 25

    @api.model
    def _is_month_end_window(self, today):
        """Trả về True nếu hôm nay nằm trong cửa sổ cuối tháng.

        Logic: từ ngày 25 đến ngày làm việc cuối cùng của tháng.
        Dùng calendar để biết ngày cuối tháng thực tế (28/29/30/31).
        """
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.day >= min(self._REMIND_FROM_DAY, last_day)

    @api.model
    def _cron_leave_balance_reminder(self):
        """CRON-TO-001: Nhắc nhở số dư nghỉ phép vào ngày cuối tháng.

        Chạy hằng ngày lúc 07:00 (Asia/Ho_Chi_Minh = 00:00 UTC). Chỉ thực sự
        gửi nhắc nhở trong cửa sổ cuối tháng (từ ngày 25). Với mỗi nhân viên
        còn số dư phép > 0, tạo một activity nhắc nhở.
        """
        today = date.today()

        if not self._is_month_end_window(today):
            _logger.info(
                'CRON-TO-001: %s chưa tới cửa sổ cuối tháng — bỏ qua.', today
            )
            return

        employees = self.env['hr.employee'].search([('active', '=', True)])
        notified = 0

        for emp in employees:
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.requires_allocation', '=', True),
            ])
            # Số dư còn lại = tổng available (virtual_remaining_leaves)
            remaining = sum(allocations.mapped('virtual_remaining_leaves'))

            if remaining > 0:
                emp.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Nhắc nhở: Bạn còn %.1f ngày nghỉ phép chưa sử dụng')
                    % remaining,
                    note=_(
                        'Bạn còn <b>%.1f ngày</b> nghỉ phép chưa sử dụng trong tháng này. '
                        'Vui lòng lên kế hoạch nghỉ phép hoặc chuyển sang tháng sau '
                        'theo chính sách công ty.'
                    ) % remaining,
                    user_id=emp.user_id.id or self.env.uid,
                )
                notified += 1

        _logger.info(
            'CRON-TO-001: Đã nhắc nhở %d nhân viên về số dư nghỉ phép.', notified
        )

        # Ghi vào ir.logging để audit lịch sử chạy cron
        self.env['ir.logging'].sudo().create({
            'name': 'CRON-TO-001',
            'type': 'server',
            'level': 'INFO',
            'dbname': self.env.cr.dbname,
            'message': 'Leave Balance Reminder: %d employees notified on %s'
            % (notified, today),
            'path': 'hb_timeoff_cron',
            'func': '_cron_leave_balance_reminder',
            'line': '0',
        })
        return notified
