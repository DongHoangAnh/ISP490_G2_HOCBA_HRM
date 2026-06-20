from odoo import models, fields


class HocbaSaleLevel(models.Model):
    _name = 'hocba.sale.level'
    _description = 'Bậc hoa hồng Sale'
    _order = 'level'

    name = fields.Char(string='Tên', required=True)
    level = fields.Integer(string='Bậc', required=True)
    kpi_threshold = fields.Float(
        string='Ngưỡng doanh thu (KPI)', digits=(16, 0), required=True,
    )
    commission_rate = fields.Float(
        string='% Hoa hồng', digits=(8, 4), required=True,
    )
    base_sale_wage = fields.Float(
        string='Lương cứng sale (LC sale)', digits=(12, 0), required=True,
    )
    active = fields.Boolean(default=True)

    _level_uniq = models.Constraint(
        'UNIQUE(level)',
        'Bậc phải là duy nhất!',
    )
