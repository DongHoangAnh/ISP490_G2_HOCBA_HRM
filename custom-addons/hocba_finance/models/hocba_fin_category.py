from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HocbaFinCategory(models.Model):
    _name = 'hocba.fin.category'
    _description = 'Mục thu/chi (income/expense category)'
    _order = 'category_type, name'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(string='Tên mục', required=True, translate=True)
    code = fields.Char(string='Mã mục', required=True, index=True)
    category_type = fields.Selection(
        [('income', 'Thu'), ('expense', 'Chi')],
        string='Loại', required=True, index=True)
    parent_id = fields.Many2one(
        'hocba.fin.category', string='Mục cha', ondelete='restrict', index=True)
    parent_path = fields.Char(index=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint('unique(code)', 'Mã mục phải là duy nhất.')

    @api.constrains('parent_id', 'category_type')
    def _check_parent_type(self):
        for rec in self:
            if rec.parent_id and rec.parent_id.category_type != rec.category_type:
                raise ValidationError(_('Mục con phải cùng loại Thu/Chi với mục cha.'))

    @api.constrains('parent_id')
    def _check_no_cycle(self):
        if self._has_cycle():
            raise ValidationError(_('Không được tạo phân cấp mục vòng lặp.'))

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for rec in self:
            if rec.parent_id:
                rec.display_name = f'{rec.parent_id.name} / {rec.name}'
            else:
                rec.display_name = rec.name
