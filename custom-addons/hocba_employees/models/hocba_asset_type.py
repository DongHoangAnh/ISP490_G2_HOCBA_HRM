from odoo import models, fields


class HocbaAssetType(models.Model):
    _name = 'hocba.asset.type'
    _description = 'Loại tài sản'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên loại tài sản', required=True)
    code = fields.Char(string='Mã loại', required=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã loại tài sản phải là duy nhất!',
    )
