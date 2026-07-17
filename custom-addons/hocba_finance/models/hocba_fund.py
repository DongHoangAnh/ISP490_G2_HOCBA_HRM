from odoo import api, fields, models


class HocbaFund(models.Model):
    _name = 'hocba.fund'
    _description = 'Quỹ tiền (cash fund) — theo phòng ban'
    _order = 'department_id, name'

    name = fields.Char(string='Tên quỹ', required=True)
    code = fields.Char(string='Mã quỹ', required=True, index=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban', index=True,
        help='Để trống = quỹ tổng công ty (do Ban giám đốc quản lý).')
    fund_type = fields.Selection(
        [('cash', 'Tiền mặt'), ('bank', 'Ngân hàng')],
        string='Loại quỹ', default='cash', required=True)
    opening_balance = fields.Monetary(string='Số dư đầu', default=0.0)
    current_balance = fields.Monetary(
        string='Số dư hiện tại', compute='_compute_current_balance',
        store=True, readonly=True,
        help='Số dư đầu + tổng thu đã ghi sổ − tổng chi đã ghi sổ.')
    voucher_ids = fields.One2many('hocba.fin.voucher', 'fund_id', string='Phiếu')
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint('unique(code)', 'Mã quỹ phải là duy nhất.')

    @api.depends('opening_balance', 'voucher_ids.state',
                 'voucher_ids.amount', 'voucher_ids.voucher_type')
    def _compute_current_balance(self):
        for fund in self:
            posted = fund.voucher_ids.filtered(lambda v: v.state == 'posted')
            income = sum(posted.filtered(
                lambda v: v.voucher_type == 'income').mapped('amount'))
            expense = sum(posted.filtered(
                lambda v: v.voucher_type == 'expense').mapped('amount'))
            fund.current_balance = fund.opening_balance + income - expense
