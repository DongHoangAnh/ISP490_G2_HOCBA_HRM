from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    x_function_desc = fields.Char(
        string='Chức năng phòng ban',
        help='Mô tả ngắn chức năng nghiệp vụ của phòng ban (theo Lookup 8.4 Lark).',
    )
