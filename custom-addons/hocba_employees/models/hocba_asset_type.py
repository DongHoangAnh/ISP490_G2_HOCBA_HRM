from odoo import models, fields


class HocbaAssetType(models.Model):
    _name = 'hocba.asset.type'
    _description = 'Loại tài sản'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên loại tài sản', required=True)
    code = fields.Char(string='Mã loại', required=True)
    # Khách họp #2: tách "mặc định" (tự cấp khi onboarding) vs "tự thêm" (HR thêm sau)
    x_is_default = fields.Boolean(
        string='Cấp mặc định',
        help='Loại tài sản tự cấp cho nhân viên khi qua cổng tuần-2; '
             'loại không bật là loại HR tự cấp phát khi cần.')
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã loại tài sản phải là duy nhất!',
    )
