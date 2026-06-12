from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    x_is_emergency_type = fields.Boolean(
        string='Loại nghỉ khẩn cấp',
        default=False,
        help='Khi bật, đơn nghỉ loại này sẽ kích hoạt quy trình fast-track: '
             'thông báo tức thời đến HR và Manager trực tiếp.',
    )
