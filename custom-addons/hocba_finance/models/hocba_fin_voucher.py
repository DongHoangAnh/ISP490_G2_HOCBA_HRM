import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, AccessError

_logger = logging.getLogger(__name__)

# Các field nội dung bị khoá sau khi phiếu đã ghi sổ (chỉ được Huỷ).
_LOCKED_FIELDS = {
    'voucher_type', 'amount', 'voucher_date', 'fund_id', 'category_id',
    'department_id', 'partner_name', 'partner_address', 'memo',
    'external_ref', 'attachment_count',
}


class HocbaFinVoucher(models.Model):
    _name = 'hocba.fin.voucher'
    _description = 'Phiếu thu / Phiếu chi (cash voucher)'
    _inherit = ['mail.thread']
    _order = 'voucher_date desc, id desc'

    name = fields.Char(
        string='Số phiếu', required=True, copy=False, readonly=True,
        default=lambda self: _('New'), index=True)
    voucher_type = fields.Selection(
        [('income', 'Phiếu thu'), ('expense', 'Phiếu chi')],
        string='Loại', required=True, default='income', tracking=True)
    amount = fields.Monetary(string='Số tiền', required=True, tracking=True)
    voucher_date = fields.Date(
        string='Ngày', required=True, tracking=True,
        default=fields.Date.context_today,
        help='Ngày tiền thực chạy — mốc dựng báo cáo dòng tiền.')
    fund_id = fields.Many2one(
        'hocba.fund', string='Quỹ', required=True, tracking=True,
        ondelete='restrict')
    category_id = fields.Many2one(
        'hocba.fin.category', string='Mục', required=True, tracking=True,
        ondelete='restrict')
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        compute='_compute_department_id', store=True, readonly=False, index=True)
    partner_name = fields.Char(string='Người nộp/nhận')
    partner_address = fields.Char(
        string='Địa chỉ',
        help='Địa chỉ người nộp/nhận tiền — theo Mẫu 01-TT/02-TT TT200.')
    memo = fields.Text(
        string='Lý do nộp/chi',
        help='Lý do nộp tiền (phiếu thu) hoặc lý do chi (phiếu chi) — '
             'theo chuẩn Mẫu 01-TT/02-TT Thông tư 200/2014/TT-BTC.')
    attachment_count = fields.Integer(
        string='Kèm theo chứng từ gốc', default=0,
        help='Số lượng chứng từ gốc đính kèm (hóa đơn, quyết định, bảng kê…).')

    source = fields.Selection(
        [('manual', 'Nhập tay'), ('api', 'API')],
        string='Nguồn', default='manual', readonly=True, required=True)
    external_ref = fields.Char(
        string='Mã tham chiếu', index=True, copy=False,
        help='Mã chứng từ từ hệ thống ngoài — chống tạo trùng khi nạp qua API.')
    payload_raw = fields.Text(string='Payload gốc', readonly=True, copy=False)

    state = fields.Selection(
        [('draft', 'Nháp'), ('approved', 'Đã duyệt'),
         ('posted', 'Đã ghi sổ'), ('cancel', 'Huỷ')],
        string='Trạng thái', default='draft', required=True,
        tracking=True, index=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Người duyệt',
                                  readonly=True, copy=False)
    approved_date = fields.Datetime(string='Ngày duyệt', readonly=True, copy=False)
    posted_by = fields.Many2one('res.users', string='Người ghi sổ',
                                readonly=True, copy=False)
    posted_date = fields.Datetime(string='Ngày ghi sổ', readonly=True, copy=False)

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='fund_id.currency_id',
        store=True, readonly=True)

    # ── Compute ────────────────────────────────────────────────────────────
    @api.depends('fund_id')
    def _compute_department_id(self):
        for rec in self:
            if rec.fund_id.department_id:
                rec.department_id = rec.fund_id.department_id
            elif not rec.department_id:
                rec.department_id = False

    # ── Constraints ────────────────────────────────────────────────────────
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Số tiền phải lớn hơn 0.'))

    @api.constrains('category_id', 'voucher_type')
    def _check_category_type(self):
        for rec in self:
            if rec.category_id and rec.category_id.category_type != rec.voucher_type:
                raise ValidationError(_(
                    'Mục "%s" (%s) không khớp loại phiếu.',
                    rec.category_id.name, rec.category_id.category_type))

    @api.constrains('external_ref')
    def _check_external_ref_unique(self):
        for rec in self:
            if rec.external_ref:
                dup = self.search_count([
                    ('external_ref', '=', rec.external_ref),
                    ('id', '!=', rec.id)])
                if dup:
                    raise ValidationError(_(
                        'Mã tham chiếu "%s" đã tồn tại.', rec.external_ref))

    # ── CRUD overrides ─────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                seq = ('hocba.fin.voucher.income'
                       if vals.get('voucher_type', 'income') == 'income'
                       else 'hocba.fin.voucher.expense')
                vals['name'] = self.env['ir.sequence'].next_by_code(seq) or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if _LOCKED_FIELDS & set(vals):
            for rec in self:
                if rec.state == 'posted':
                    raise UserError(_(
                        'Không thể sửa phiếu đã ghi sổ (%s). Hãy Huỷ trước.',
                        rec.name))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_(
                    'Không thể xoá phiếu đã ghi sổ (%s). Hãy Huỷ.', rec.name))
        return super().unlink()

    # ── Workflow actions ───────────────────────────────────────────────────
    def _check_finance_user(self):
        """Chỉ Kế toán/BGĐ được duyệt & ghi sổ (nút UI ẩn theo group nhưng
        method vẫn phải tự chặn — nhân viên có quyền write phiếu của mình)."""
        if not self.env.user.has_group('hocba_finance.group_finance_user'):
            raise AccessError(_(
                'Chỉ Kế toán / Ban giám đốc được duyệt hoặc ghi sổ phiếu.'))

    def action_approve(self):
        self._check_finance_user()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ duyệt được phiếu ở trạng thái Nháp.'))
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })

    def action_post(self):
        self._check_finance_user()
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Chỉ ghi sổ phiếu đã duyệt.'))
        # Số dư quỹ tự cập nhật qua compute (depends voucher_ids.state) — idempotent.
        self.write({
            'state': 'posted',
            'posted_by': self.env.user.id,
            'posted_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        # Huỷ được ở mọi trạng thái; nếu đang posted, số dư quỹ tự trừ lại.
        self.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_(
                    'Không thể reset phiếu đã ghi sổ. Hãy Huỷ.'))
        self.write({
            'state': 'draft',
            'approved_by': False,
            'approved_date': False,
        })

    # ── API ingestion ──────────────────────────────────────────────────────
    @api.model
    def _ingest_from_api(self, vouchers, source='api', auto_post=False):
        """Tạo phiếu từ payload API. Idempotent theo external_ref, cô lập lỗi
        từng item bằng savepoint. Trả về {created, skipped, errors}."""
        Fund = self.env['hocba.fund']
        Cat = self.env['hocba.fin.category']
        Dept = self.env['hr.department']
        created = skipped = 0
        errors = []
        for idx, item in enumerate(vouchers or []):
            ref = (item.get('external_ref') or '').strip()
            if ref and self.search_count([('external_ref', '=', ref)]):
                skipped += 1
                continue
            try:
                with self.env.cr.savepoint():
                    fund = Fund.search(
                        [('code', '=', item.get('fund_code'))], limit=1)
                    if not fund:
                        raise ValueError(
                            'fund_code không hợp lệ: %s' % item.get('fund_code'))
                    cat = Cat.search(
                        [('code', '=', item.get('category_code'))], limit=1)
                    if not cat:
                        raise ValueError(
                            'category_code không hợp lệ: %s'
                            % item.get('category_code'))
                    vals = {
                        'voucher_type': item.get('voucher_type') or 'income',
                        'amount': item.get('amount'),
                        'voucher_date': (item.get('date')
                                         or fields.Date.context_today(self)),
                        'fund_id': fund.id,
                        'category_id': cat.id,
                        'partner_name': item.get('partner_name') or False,
                        'memo': item.get('memo') or False,
                        'external_ref': ref or False,
                        'source': source,
                        'payload_raw': json.dumps(item, ensure_ascii=False),
                    }
                    dept_name = item.get('department_code') or item.get('department')
                    if dept_name and not fund.department_id:
                        dept = Dept.search([('name', '=', dept_name)], limit=1)
                        if dept:
                            vals['department_id'] = dept.id
                    rec = self.create(vals)
                    if auto_post:
                        rec.action_approve()
                        rec.action_post()
                    created += 1
            except Exception as e:  # noqa: BLE001 - cô lập lỗi từng item
                _logger.warning('Finance API ingest item %s failed: %s', idx, e)
                errors.append({
                    'index': idx,
                    'external_ref': item.get('external_ref'),
                    'error': str(e),
                })
        return {'created': created, 'skipped': skipped, 'errors': errors}
