from odoo import models, fields


class AttendanceStatus(models.Model):
    _name = 'hocba.attendance.status'
    _description = 'Attendance Status'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Status Name', required=True)
    code = fields.Char(string='Status Code', required=True)
    description = fields.Text(string='Description')
    color_code = fields.Char(
        string='Color Code',
        help='Hex color code for UI display',
        default='#808080'
    )
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Status code must be unique!',
    )
