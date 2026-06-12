"""
Bank File Generation Wizard.
FUNC-PR-003: Wizard sinh file thanh toán ngân hàng.
"""
import base64
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

from ..models.bank_formatter import BankFormatterRegistry

_logger = logging.getLogger(__name__)


class BankFileWizard(models.TransientModel):
    _name = 'hb.bank.file.wizard'
    _description = 'Tạo file thanh toán ngân hàng'

    payslip_batch_id = fields.Many2one(
        'hb.payslip.run', string='Payslip Batch',
        required=True, readonly=True,
    )
    bank_format_id = fields.Many2one(
        'hb.bank.format', string='Ngân hàng',
        required=True,
        domain=[('active', '=', True)],
    )
    company_bank_id = fields.Many2one(
        'res.partner.bank', string='Tài khoản công ty',
        required=True,
        help='TK ngân hàng của công ty để chuyển khoản.',
    )
    payment_date = fields.Date(
        string='Ngày chi', required=True,
        default=lambda self: fields.Date.add(fields.Date.today(), days=1),
    )
    description = fields.Char(
        string='Mô tả giao dịch',
        default='Luong T{month}/{year}',
        required=True,
    )

    # Read-only display
    payslip_count = fields.Integer(
        string='Số payslip',
        compute='_compute_summary',
    )
    total_net = fields.Float(
        string='Tổng số tiền', digits=(16, 0),
        compute='_compute_summary',
    )

    @api.depends('payslip_batch_id')
    def _compute_summary(self):
        for wiz in self:
            slips = wiz.payslip_batch_id.slip_ids.filtered(lambda s: s.state == 'done')
            wiz.payslip_count = len(slips)
            wiz.total_net = sum(
                self._get_net(s) for s in slips
            )

    @staticmethod
    def _get_net(payslip):
        net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
        return net_line[0].amount if net_line else 0.0

    @staticmethod
    def _get_employee_bank(employee):
        """Get employee bank account — compatible with Community (no bank_account_id)."""
        if hasattr(employee, 'bank_account_id') and employee.bank_account_id:
            return employee.bank_account_id
        # Community fallback: partner bank accounts
        partner = employee.address_home_id or employee.work_contact_id
        if partner and partner.bank_ids:
            return partner.bank_ids[0]
        return None

    # ─────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────
    def _validate(self):
        self.ensure_one()
        batch = self.payslip_batch_id

        # VR-001: Batch must be done
        if batch.state != 'close':
            raise UserError(_('Payslip Batch phải ở trạng thái Done/Close.'))

        # VR-005: payment_date >= today
        if self.payment_date < fields.Date.today():
            raise ValidationError(_('Ngày chi phải lớn hơn hoặc bằng hôm nay.'))

        # VR-002 & VR-003: All employees must have valid bank account
        regex = self.bank_format_id.account_format_regex
        missing = []
        invalid_format = []

        for slip in batch.slip_ids.filtered(lambda s: s.state == 'done'):
            emp = slip.employee_id
            bank_acc = self._get_employee_bank(emp)
            if not bank_acc or not bank_acc.acc_number:
                missing.append(f'{emp.name} ({getattr(emp, "x_employee_code", "N/A")})')
                continue
            if regex and not re.match(regex, bank_acc.acc_number.strip()):
                invalid_format.append(
                    f'{emp.name} — STK: {bank_acc.acc_number}'
                )

        errors = []
        if missing:
            errors.append(_(
                'Có %(n)s nhân viên thiếu tài khoản ngân hàng:\n%(list)s',
                n=len(missing), list='\n'.join(f'• {m}' for m in missing),
            ))
        if invalid_format:
            errors.append(_(
                'Có %(n)s nhân viên STK không đúng format:\n%(list)s',
                n=len(invalid_format), list='\n'.join(f'• {i}' for i in invalid_format),
            ))
        if errors:
            raise ValidationError('\n\n'.join(errors))

    # ─────────────────────────────────────────────────────────
    # Main action
    # ─────────────────────────────────────────────────────────
    def action_generate(self):
        """Generate bank file and return download action."""
        self.ensure_one()
        self._validate()

        batch = self.payslip_batch_id
        bank_fmt = self.bank_format_id

        # Load formatter (Strategy)
        formatter = BankFormatterRegistry.get(bank_fmt.code)

        # Build rows
        done_slips = batch.slip_ids.filtered(lambda s: s.state == 'done')
        rows, warnings = formatter.build_rows(
            done_slips,
            self.description,
            account_regex=bank_fmt.account_format_regex,
        )

        if not rows:
            raise UserError(_('Không có dữ liệu để tạo file (tất cả payslip có NET = 0).'))

        # Generate XLSX
        file_bytes = formatter.export_xlsx(rows)
        period = f'T{self.payslip_batch_id.date_start.strftime("%m_%Y")}' if self.payslip_batch_id.date_start else 'N-A'
        filename = f'{bank_fmt.code}_{period}.xlsx'

        # Save attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(file_bytes),
            'res_model': 'hb.payslip.run',
            'res_id': batch.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Create bank file record
        total_amount = sum(r.get('amount', 0) for r in rows)
        self.env['hb.bank.file'].create({
            'name': filename,
            'batch_id': batch.id,
            'bank_format_id': bank_fmt.id,
            'attachment_id': attachment.id,
            'payment_date': self.payment_date,
            'total_amount': total_amount,
            'record_count': len(rows),
            'generated_by': self.env.uid,
            'generated_at': fields.Datetime.now(),
        })

        # Chatter log
        warning_text = '\n'.join(warnings) if warnings else ''
        batch.message_post(body=_(
            'Đã sinh file %(filename)s: %(count)s dòng, tổng %(amount)s VND%(warn)s',
            filename=filename,
            count=len(rows),
            amount='{:,.0f}'.format(total_amount),
            warn=f'\n⚠ Cảnh báo:\n{warning_text}' if warning_text else '',
        ))

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
