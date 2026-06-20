from odoo import models, fields, api


class HocbaSaleRevenue(models.Model):
    _name = 'hocba.sale.revenue'
    _description = 'Doanh thu sale theo tháng'
    _order = 'period_year desc, period_month desc, id'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='restrict', index=True,
    )
    period_month = fields.Integer(string='Tháng', required=True)
    period_year = fields.Integer(string='Năm', required=True)
    revenue = fields.Float(
        string='Doanh thu', digits=(16, 0), required=True,
    )
    level_id = fields.Many2one(
        'hocba.sale.level', string='Bậc đạt được',
        compute='_compute_level', store=True,
    )
    commission = fields.Float(
        string='Hoa hồng', digits=(16, 0),
        compute='_compute_commission', store=True,
    )
    sale_wage = fields.Float(
        string='Lương sale (LC + COM)', digits=(16, 0),
        compute='_compute_commission', store=True,
    )

    _employee_period_uniq = models.Constraint(
        'UNIQUE(employee_id, period_month, period_year)',
        'Mỗi nhân viên chỉ có 1 bản ghi doanh thu/tháng!',
    )

    @api.depends('revenue')
    def _compute_level(self):
        levels = self.env['hocba.sale.level'].search(
            [('active', '=', True)], order='kpi_threshold desc',
        )
        for rec in self:
            matched = False
            for lvl in levels:
                if rec.revenue >= lvl.kpi_threshold:
                    rec.level_id = lvl.id
                    matched = True
                    break
            if not matched:
                rec.level_id = False

    @api.depends('revenue', 'level_id')
    def _compute_commission(self):
        for rec in self:
            if rec.level_id:
                rec.commission = round(rec.revenue * rec.level_id.commission_rate)
                rec.sale_wage = rec.level_id.base_sale_wage + rec.commission
            else:
                rec.commission = 0.0
                rec.sale_wage = 0.0
