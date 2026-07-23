from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    x_is_emergency_type = fields.Boolean(
        string='Loại nghỉ khẩn cấp',
        default=False,
        help='Khi bật, đơn nghỉ loại này sẽ kích hoạt quy trình fast-track: '
             'thông báo tức thời đến HR và Manager trực tiếp.',
    )

    x_hb_managed = fields.Boolean(
        string='Do Học Bá quản lý',
        default=False,
        help='Bật = loại nghỉ này hiển thị & cấu hình được trong SPA Học Bá. '
             'Các loại nghỉ demo/bản địa hoá của Odoo để False để ẩn khỏi SPA.',
    )
