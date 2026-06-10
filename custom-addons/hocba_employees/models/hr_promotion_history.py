from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HrPromotionHistory(models.Model):
    _name = 'hr.promotion.history'
    _description = 'Lịch sử thăng tiến & lương (snapshot)'
    _order = 'date_effective desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='restrict', index=True)
    date_effective = fields.Date(
        string='Ngày có hiệu lực', required=True,
        default=fields.Date.context_today)
    from_job_id = fields.Many2one('hr.job', string='Chức vụ trước')
    to_job_id = fields.Many2one('hr.job', string='Chức vụ mới', required=True)
    to_department_id = fields.Many2one('hr.department', string='Phòng ban mới')
    from_wage = fields.Float(string='Lương cũ')
    to_wage = fields.Float(string='Lương mới', required=True)
    allowance_note = fields.Text(string='Phụ cấp (tóm tắt)')
    reason = fields.Text(string='Lý do / Căn cứ')
    decision_ref = fields.Char(string='Số quyết định')
    approved_by = fields.Many2one(
        'res.users', string='Người phê duyệt', required=True,
        default=lambda self: self.env.user)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.from_job_id = rec.employee_id.job_id

    @api.constrains('date_effective', 'to_wage', 'from_job_id', 'to_job_id',
                    'from_wage', 'reason')
    def _check_rules(self):
        limit = fields.Date.context_today(self) + timedelta(days=30)
        for rec in self:
            if rec.date_effective > limit:
                raise ValidationError(_(
                    'Ngày hiệu lực không được quá 30 ngày trong tương lai.'))
            if rec.to_wage <= 0:
                raise ValidationError(_('Lương mới phải lớn hơn 0.'))
            if rec.to_job_id == rec.from_job_id and rec.to_wage == rec.from_wage:
                raise ValidationError(_(
                    'Phải thay đổi ít nhất một trong: chức vụ hoặc mức lương.'))
            if rec.to_wage != rec.from_wage and not rec.reason:
                raise ValidationError(_(
                    'Cần nhập Lý do / Căn cứ khi thay đổi mức lương.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            emp = rec.employee_id
            if not rec.from_job_id and emp.job_id:
                rec.from_job_id = emp.job_id
            emp_vals = {'job_id': rec.to_job_id.id}
            if rec.to_department_id:
                emp_vals['department_id'] = rec.to_department_id.id
            emp.sudo().write(emp_vals)
            emp.message_post(body=_(
                '📈 Cập nhật chức vụ: %(old)s → %(new)s từ %(date)s '
                '(QĐ: %(ref)s, duyệt bởi %(by)s).') % {
                    'old': rec.from_job_id.name or '—',
                    'new': rec.to_job_id.name,
                    'date': rec.date_effective,
                    'ref': rec.decision_ref or '—',
                    'by': rec.approved_by.name,
                })
        return records

    def write(self, vals):
        # BR-060: sau 24h chỉ HR Manager được sửa
        if not self.env.su and not self.env.user.has_group('hr.group_hr_manager'):
            cutoff = fields.Datetime.now() - timedelta(hours=24)
            for rec in self:
                if rec.create_date and rec.create_date < cutoff:
                    raise AccessError(_(
                        'Bản ghi thăng tiến quá 24h — chỉ HR Manager được sửa.'))
        return super().write(vals)

    def unlink(self):
        # BR-060: audit trail — không xóa
        raise UserError(_('Không được xóa lịch sử thăng tiến (audit trail).'))
