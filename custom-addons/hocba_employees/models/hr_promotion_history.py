from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HrPromotionHistory(models.Model):
    _name = 'hr.promotion.history'
    _description = 'Lịch sử thăng tiến & lương (snapshot)'
    _order = 'date_effective desc, id desc'

    # Mirror các selection của hr.employee để snapshot "trạng thái lúc đấy"
    WORK_FORM_SEL = [('offline', 'Offline'), ('online', 'Online')]
    STATUS_SEL = [
        ('probation', 'Thử việc'), ('official', 'Chính thức'),
        ('intern', 'TTS'), ('parttime', 'Part-time'), ('ctv', 'CTV'),
        ('advisor', 'Cố vấn'), ('exiting', 'Đang offboarding'),
        ('resigned', 'Nghỉ việc'),
    ]

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='restrict', index=True)
    # Loại biến động — khách: "lúc vào làm" và "lên chính thức" cũng là thăng tiến
    x_change_type = fields.Selection(
        selection=[
            ('join', 'Nhận việc'),
            ('probation', 'Lên chính thức'),
            ('promotion', 'Thăng chức'),
            ('salary', 'Điều chỉnh lương'),
            ('other', 'Khác'),
        ],
        string='Loại biến động', required=True, default='promotion', index=True)
    date_effective = fields.Date(
        string='Ngày có hiệu lực', required=True,
        default=fields.Date.context_today)
    from_job_id = fields.Many2one('hr.job', string='Chức vụ trước')
    to_job_id = fields.Many2one('hr.job', string='Chức vụ / Chức danh')
    to_department_id = fields.Many2one('hr.department', string='Phòng ban')
    # Snapshot trạng thái tại thời điểm (khách yêu cầu lưu đầy đủ)
    x_work_form = fields.Selection(
        WORK_FORM_SEL, string='Hình thức (tại thời điểm)')
    x_employment_status = fields.Selection(
        STATUS_SEL, string='Trạng thái (tại thời điểm)')
    from_wage = fields.Float(string='Lương cũ', groups='hr.group_hr_manager')
    to_wage = fields.Float(string='Lương', groups='hr.group_hr_manager')
    allowance_note = fields.Text(string='Phụ cấp (tóm tắt)')
    reason = fields.Text(string='Lý do / Căn cứ')
    # Bằng chứng đổi lương — khách yêu cầu đính link đánh giá/KPI/kết quả
    x_evidence_url = fields.Char(
        string='Link bằng chứng (đánh giá/KPI)',
        help='Bắt buộc khi thay đổi mức lương — đính link kết quả đánh giá, '
             'bản KPI hoặc minh chứng tương ứng.')
    decision_ref = fields.Char(string='Số quyết định')
    approved_by = fields.Many2one(
        'res.users', string='Người phê duyệt', required=True,
        default=lambda self: self.env.user)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.from_job_id = rec.employee_id.job_id
                rec.to_job_id = rec.employee_id.job_id
                rec.to_department_id = rec.employee_id.department_id
                rec.x_work_form = rec.employee_id.x_work_form
                rec.x_employment_status = rec.employee_id.x_employment_status

    @api.constrains('date_effective', 'to_wage', 'from_job_id', 'to_job_id',
                    'from_wage', 'reason', 'x_change_type', 'x_evidence_url')
    def _check_rules(self):
        limit = fields.Date.context_today(self) + timedelta(days=30)
        for rec in self.sudo():
            if rec.date_effective > limit:
                raise ValidationError(_(
                    'Ngày hiệu lực không được quá 30 ngày trong tương lai.'))
            wage_changed = rec.to_wage and rec.from_wage != rec.to_wage
            if rec.to_wage and rec.to_wage < 0:
                raise ValidationError(_('Mức lương không được âm.'))
            # Bản ghi tự sinh (nhận việc / lên chính thức) không cần "phải đổi"
            if rec.x_change_type in ('promotion', 'salary'):
                if rec.to_job_id == rec.from_job_id and not wage_changed:
                    raise ValidationError(_(
                        'Phải thay đổi ít nhất một trong: chức vụ hoặc mức lương.'))
            # Đổi lương: bắt buộc lý do + link bằng chứng (yêu cầu khách họp #2)
            if wage_changed:
                if not rec.reason:
                    raise ValidationError(_(
                        'Cần nhập Lý do / Căn cứ khi thay đổi mức lương.'))
                if not rec.x_evidence_url:
                    raise ValidationError(_(
                        'Cần đính Link bằng chứng (đánh giá/KPI) khi đổi lương.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            emp = rec.employee_id
            if not rec.from_job_id and emp.job_id:
                rec.sudo().from_job_id = emp.job_id
            # Chỉ áp chức vụ/phòng ban ngược vào hồ sơ khi là biến động thật;
            # snapshot tự sinh (nhận việc/lên chính thức) chỉ để lưu vết.
            if rec.x_change_type in ('promotion', 'salary', 'other') \
                    and not self.env.context.get('hocba_snapshot_only'):
                emp_vals = {}
                if rec.to_job_id:
                    emp_vals['job_id'] = rec.to_job_id.id
                if rec.to_department_id:
                    emp_vals['department_id'] = rec.to_department_id.id
                if emp_vals:
                    emp.sudo().write(emp_vals)
            rec._hocba_award_honor()
            emp.message_post(body=_(
                '📈 %(kind)s: %(old)s → %(new)s từ %(date)s '
                '(QĐ: %(ref)s, duyệt bởi %(by)s).') % {
                    'kind': dict(self._fields['x_change_type'].selection).get(
                        rec.x_change_type, rec.x_change_type),
                    'old': rec.from_job_id.name or '—',
                    'new': rec.to_job_id.name or '—',
                    'date': rec.date_effective,
                    'ref': rec.decision_ref or '—',
                    'by': rec.approved_by.name,
                })
        return records

    def _hocba_award_honor(self):
        """Bổ nhiệm chức danh mới → lên bảng vinh danh chung (spec §5.2).

        Chỉ 'promotion' có ĐỔI chức vụ mới được vinh danh: 'join'/'probation'
        là snapshot vòng đời, còn 'salary' (và promotion chỉ tăng lương) không
        có chức danh mới để công bố trước toàn công ty."""
        self.ensure_one()
        if self.x_change_type != 'promotion':
            return
        if not self.to_job_id or self.to_job_id == self.from_job_id:
            return
        self.env['hb.honor.entry'].sudo().create({
            'employee_id': self.employee_id.id,
            'category': 'promotion',
            'source': 'auto',
            'title': _('Bổ nhiệm %s') % self.to_job_id.name,
            'description': self.reason or False,
            'date_awarded': self.date_effective,
            'promotion_id': self.id,
        })

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
