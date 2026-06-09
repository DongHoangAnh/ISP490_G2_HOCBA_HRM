from odoo import models, fields


class UserRole(models.Model):
    _name = 'hocba.user.role'
    _description = 'User Role'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Role Name', required=True, unique=True)
    code = fields.Char(
        string='Role Code',
        required=True,
        unique=True,
        help='Internal code: admin, hr_manager, employee, contractor'
    )
    description = fields.Text(string='Description')
    group_ids = fields.Many2many(
        'res.groups',
        string='ODOO Groups',
        help='Associated ODOO security groups'
    )
    permissions = fields.Text(string='Permissions')
    active = fields.Boolean(default=True)
    color_code = fields.Char(default='#808080')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Role Code must be unique!'),
    ]
