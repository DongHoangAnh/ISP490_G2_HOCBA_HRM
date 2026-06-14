from odoo import models, fields


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    x_from_policy = fields.Boolean(
        string='Từ chính sách tự động',
        default=False,
        copy=False,
        help='Đánh dấu allocation được tạo bởi chính sách nghỉ phép tự động. '
             'Hệ thống sẽ expire allocation này khi chính sách thay đổi.',
    )
