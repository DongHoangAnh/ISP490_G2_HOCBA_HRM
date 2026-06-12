"""
Payslip Run (Batch) — standalone replacement for hr.payslip.run (Enterprise).
Groups payslips for a salary period.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HbPayslipRun(models.Model):
    _name = 'hb.payslip.run'
    _description = 'Payslip Batch'
    _order = 'date_start desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Tên batch', required=True, tracking=True)
    date_start = fields.Date(string='Từ ngày', required=True)
    date_end = fields.Date(string='Đến ngày', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('verify', 'Đang xác nhận'),
        ('close', 'Hoàn tất'),
    ], string='Trạng thái', default='draft', tracking=True, index=True)
    slip_ids = fields.One2many(
        'hb.payslip', 'payslip_run_id', string='Payslips',
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company,
    )
    payslip_count = fields.Integer(
        string='Số phiếu lương', compute='_compute_payslip_count',
    )

    @api.depends('slip_ids')
    def _compute_payslip_count(self):
        for rec in self:
            rec.payslip_count = len(rec.slip_ids)

    def action_verify(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ xác nhận batch ở trạng thái Nháp.'))
            rec.state = 'verify'

    def action_close(self):
        """Close batch — mark all payslips as done first."""
        for rec in self:
            if rec.state not in ('draft', 'verify'):
                raise UserError(_('Batch đã được đóng.'))
            # Confirm all draft/verify payslips
            for slip in rec.slip_ids.filtered(lambda s: s.state in ('draft', 'verify')):
                slip.action_payslip_done()
            rec.state = 'close'
            rec.message_post(body=_('Batch đã được đóng. %(n)s payslips hoàn tất.', n=len(rec.slip_ids)))

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_open_payslips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phiếu lương — %s') % self.name,
            'res_model': 'hb.payslip',
            'view_mode': 'list,form',
            'domain': [('payslip_run_id', '=', self.id)],
            'context': {'default_payslip_run_id': self.id},
        }

    def action_open_bank_file_wizard(self):
        """Open the bank file generation wizard for this batch."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tạo file Ngân hàng'),
            'res_model': 'hb.bank.file.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payslip_batch_id': self.id},
        }
