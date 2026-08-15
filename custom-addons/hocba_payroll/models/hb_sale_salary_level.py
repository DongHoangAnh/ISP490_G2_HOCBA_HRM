from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HbSaleSalaryLevel(models.Model):
    """Bảng ngạch Lương Sale theo Level KPI."""
    _name = 'hb.sale.salary.level'
    _description = 'Sale Salary Level KPI Configuration'
    _order = 'sequence, id'

    level_code = fields.Char(string='Mã Level', required=True, index=True)
    name = fields.Char(string='Tên Level', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    kpi_target = fields.Float(string='Chỉ số KPI tối thiểu', default=1.0, required=True, digits=(8, 2),
                              help='Ngưỡng KPI tối thiểu để đạt Level này (VD: 1.0, 1.5, 2.0...)')
    base_wage = fields.Float(string='Lương cơ bản theo Level (VND)', required=True, digits=(16, 0),
                             help='Mức lương cơ bản của nhân viên Sale khi đạt Level này')
    active = fields.Boolean(string='Hoạt động', default=True)

    _sql_constraints = [
        ('level_code_uniq', 'unique(level_code)', 'Mã Level sale phải là duy nhất!'),
    ]

    @api.model
    def init_default_sale_levels(self):
        """Khởi tạo 6 Level mặc định nếu chưa có dữ liệu."""
        if not self.search_count([]):
            defaults = [
                {'level_code': 'LEVEL_1', 'name': 'Level 1 - Thử thách', 'sequence': 10, 'kpi_target': 1.0, 'base_wage': 7000000.0},
                {'level_code': 'LEVEL_2', 'name': 'Level 2 - Tăng trưởng', 'sequence': 20, 'kpi_target': 1.5, 'base_wage': 9000000.0},
                {'level_code': 'LEVEL_3', 'name': 'Level 3 - Tiên phong', 'sequence': 30, 'kpi_target': 2.0, 'base_wage': 12000000.0},
                {'level_code': 'LEVEL_4', 'name': 'Level 4 - Chuyên nghiệp', 'sequence': 40, 'kpi_target': 2.5, 'base_wage': 16000000.0},
                {'level_code': 'LEVEL_5', 'name': 'Level 5 - Bứt phá', 'sequence': 50, 'kpi_target': 3.0, 'base_wage': 22000000.0},
                {'level_code': 'LEVEL_6', 'name': 'Level 6 - Huyền thoại', 'sequence': 60, 'kpi_target': 4.0, 'base_wage': 30000000.0},
            ]
            for d in defaults:
                self.create(d)
