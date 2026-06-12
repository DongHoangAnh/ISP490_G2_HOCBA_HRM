"""
Bank File history model.
FUNC-PR-003: Log mỗi lần sinh file thanh toán ngân hàng.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BankFile(models.Model):
    _name = 'hb.bank.file'
    _description = 'Bank Payment File'
    _order = 'generated_at desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Tên file',
        required=True,
        readonly=True,
    )
    batch_id = fields.Many2one(
        'hb.payslip.run',
        string='Payslip Batch',
        required=True,
        ondelete='restrict',
        readonly=True,
    )
    bank_format_id = fields.Many2one(
        'hb.bank.format',
        string='Ngân hàng',
        required=True,
        ondelete='restrict',
        readonly=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='File đính kèm',
        ondelete='set null',
        readonly=True,
    )
    payment_date = fields.Date(
        string='Ngày chi',
        required=True,
        readonly=True,
    )
    total_amount = fields.Float(
        string='Tổng số tiền',
        digits=(16, 0),
        readonly=True,
    )
    record_count = fields.Integer(
        string='Số dòng',
        readonly=True,
    )
    generated_by = fields.Many2one(
        'res.users',
        string='Người tạo',
        required=True,
        readonly=True,
        default=lambda self: self.env.uid,
    )
    generated_at = fields.Datetime(
        string='Thời gian tạo',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )
    state = fields.Selection([
        ('generated', 'Đã tạo'),
        ('uploaded', 'Đã upload'),
        ('confirmed', 'Ngân hàng xác nhận'),
    ], string='Trạng thái', default='generated', tracking=True)

    def action_mark_uploaded(self):
        for rec in self:
            if rec.state != 'generated':
                raise UserError(_('Chỉ đánh dấu uploaded khi state = generated.'))
            rec.state = 'uploaded'

    def action_mark_confirmed(self):
        for rec in self:
            if rec.state != 'uploaded':
                raise UserError(_('Chỉ xác nhận khi state = uploaded.'))
            rec.state = 'confirmed'

    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'batch_id': self.batch_id.id,
            'batch_name': self.batch_id.name,
            'bank_code': self.bank_format_id.code,
            'bank_name': self.bank_format_id.name,
            'payment_date': str(self.payment_date),
            'total_amount': self.total_amount,
            'record_count': self.record_count,
            'state': self.state,
            'generated_by': self.generated_by.name,
            'generated_at': str(self.generated_at),
            'download_url': f'/web/content/{self.attachment_id.id}' if self.attachment_id else None,
        }
