from odoo import models, fields, api


class HbSalaryStructure(models.Model):
    _name = 'hb.salary.structure'
    _description = 'Salary Structure'
    _order = 'name'

    name = fields.Char(string='Tên cấu trúc', required=True, translate=True)
    code = fields.Char(string='Mã', required=True, index=True)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Mô tả')
    rule_ids = fields.One2many(
        'hb.salary.rule', 'structure_id', string='Quy tắc lương',
    )
    rule_count = fields.Integer(
        string='Số quy tắc', compute='_compute_rule_count',
    )

    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        'Mã cấu trúc lương phải là duy nhất!',
    )

    @api.depends('rule_ids')
    def _compute_rule_count(self):
        for rec in self:
            rec.rule_count = len(rec.rule_ids)
