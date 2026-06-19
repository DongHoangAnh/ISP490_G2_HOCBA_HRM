from odoo import models, fields


class HbPayslipWorkedDays(models.Model):
    _name = 'hb.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _order = 'sequence, id'

    payslip_id = fields.Many2one(
        'hb.payslip', string='Phiếu lương',
        required=True, ondelete='cascade', index=True,
    )
    name = fields.Char(string='Mô tả', required=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    number_of_days = fields.Float(string='Số ngày', digits=(8, 2))
    number_of_hours = fields.Float(string='Số giờ', digits=(8, 2))
