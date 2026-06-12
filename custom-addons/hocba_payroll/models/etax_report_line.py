"""
eTax Report Line — per-employee PIT detail.
FUNC-PR-005
"""
from odoo import api, fields, models


class EtaxReportLine(models.Model):
    _name = 'hb.etax.report.line'
    _description = 'Chi tiết thuế TNCN theo nhân viên'
    _order = 'employee_code'

    report_id = fields.Many2one(
        'hb.etax.report', string='Báo cáo', required=True, ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True, ondelete='restrict',
    )
    employee_code = fields.Char(string='Mã NV')
    pit_code = fields.Char(string='Mã số thuế TNCN')
    residence_status = fields.Selection([
        ('resident', 'Cư trú'),
        ('non_resident', 'Không cư trú'),
    ], string='Tình trạng cư trú', default='resident')
    gross_income = fields.Float(string='Thu nhập Gross', digits=(16, 0))
    insurance_deduction = fields.Float(string='Trừ BH bắt buộc', digits=(16, 0))
    personal_deduction = fields.Float(string='Giảm trừ bản thân', digits=(16, 0))
    dependent_count = fields.Integer(string='Số NPT')
    dependent_deduction = fields.Float(string='Giảm trừ NPT', digits=(16, 0))
    taxable_income = fields.Float(string='Thu nhập chịu thuế', digits=(16, 0))
    pit_amount = fields.Float(string='Thuế TNCN', digits=(16, 0))

    net_income = fields.Float(
        string='Thu nhập sau thuế',
        compute='_compute_net', store=True, digits=(16, 0),
    )

    @api.depends('gross_income', 'insurance_deduction', 'pit_amount')
    def _compute_net(self):
        for rec in self:
            rec.net_income = rec.gross_income - rec.insurance_deduction - rec.pit_amount

    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'employee_id': self.employee_id.id,
            'employee_name': self.employee_id.name,
            'employee_code': self.employee_code,
            'pit_code': self.pit_code,
            'residence_status': self.residence_status,
            'gross_income': self.gross_income,
            'insurance_deduction': self.insurance_deduction,
            'personal_deduction': self.personal_deduction,
            'dependent_count': self.dependent_count,
            'dependent_deduction': self.dependent_deduction,
            'taxable_income': self.taxable_income,
            'pit_amount': self.pit_amount,
            'net_income': self.net_income,
        }
