from odoo import models, fields


class HbPayslipInput(models.Model):
    _name = 'hb.payslip.input'
    _description = 'Payslip Input'
    _order = 'sequence, id'

    payslip_id = fields.Many2one(
        'hb.payslip', string='Phiếu lương',
        required=True, ondelete='cascade', index=True,
    )
    name = fields.Char(string='Mô tả', required=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    amount = fields.Float(string='Giá trị', digits=(16, 0))
