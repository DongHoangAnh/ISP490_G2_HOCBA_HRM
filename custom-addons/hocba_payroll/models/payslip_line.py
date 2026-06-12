"""
Payslip Line — one line per salary rule result.
"""
from odoo import fields, models


class HbPayslipLine(models.Model):
    _name = 'hb.payslip.line'
    _description = 'Chi tiết phiếu lương'
    _order = 'sequence, id'

    payslip_id = fields.Many2one(
        'hb.payslip', string='Phiếu lương', required=True, ondelete='cascade',
    )
    code = fields.Char(string='Mã', required=True, index=True)
    name = fields.Char(string='Tên', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    quantity = fields.Float(string='Số lượng', digits=(10, 2), default=1.0)
    rate = fields.Float(string='Đơn giá', digits=(16, 0))
    amount = fields.Float(string='Thành tiền', digits=(16, 0))
