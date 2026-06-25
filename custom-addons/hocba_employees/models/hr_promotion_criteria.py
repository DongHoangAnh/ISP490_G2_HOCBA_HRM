from odoo import models, fields


class HrPromotionCriteria(models.Model):
    _name = 'hr.promotion.criteria'
    _description = 'Tiêu chí đánh giá thăng tiến (cấu hình)'
    _order = 'sequence, id'

    name = fields.Char(string='Tiêu chí', required=True, translate=True)
    code = fields.Char(string='Mã', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    weight = fields.Float(string='Trọng số', required=True, default=1.0)
    max_score = fields.Integer(string='Điểm tối đa', default=5)
    guideline = fields.Text(string='Hướng dẫn chấm')
    active = fields.Boolean(string='Hiệu lực', default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã tiêu chí phải duy nhất.',
    )
