from odoo import models, fields, api


class HbSalaryRuleCategory(models.Model):
    _name = 'hb.salary.rule.category'
    _description = 'Salary Rule Category'
    _order = 'sequence, id'

    name = fields.Char(string='Tên', required=True, translate=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    note = fields.Text(string='Ghi chú')

    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        'Mã danh mục phải là duy nhất!',
    )
