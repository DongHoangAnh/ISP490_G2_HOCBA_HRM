from odoo import models, fields


class EmployeeType(models.Model):
    _name = 'hocba.employee.type'
    _description = 'Employee Type'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Type Name', required=True)
    code = fields.Char(
        string='Type Code',
        required=True,
        help='Internal code for system use'
    )
    description = fields.Text(string='Description')
    color_code = fields.Char(
        string='Color Code',
        default='#0066CC',
        help='Hex color for UI display'
    )
    benefits = fields.Text(string='Benefits')
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Employee Type Code must be unique!',
    )
