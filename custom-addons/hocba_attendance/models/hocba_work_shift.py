from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class WorkShift(models.Model):
    """Ca làm việc cho CTV/OT (Gói 4A). user đăng ký (state=pending) → manager
    duyệt (chỉnh giờ/loại/hệ số được) hoặc từ chối; manager có thể thêm ca hộ
    NV trong phạm vi (vào thẳng approved). Lịch hiển thị theo tuần."""
    _name = 'hocba.work_shift'
    _description = 'Ca làm việc'
    _order = 'start desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    start = fields.Datetime(string='Bắt đầu', required=True)
    end = fields.Datetime(string='Kết thúc', required=True)
    shift_type = fields.Selection(
        [('ctv', 'CTV'), ('ot', 'Tăng ca (OT)')],
        string='Loại ca', required=True)
    ot_level = fields.Selection(
        [('100', '100%'), ('150', '150%'), ('300', '300%')],
        string='Mức hệ số', default='100', required=True,
        help='Mức quy đổi công OT do người dùng chọn; manager đổi được.')
    rate = fields.Float(
        string='Hệ số', compute='_compute_rate', store=True,
        help='Suy từ mức: 100%→1.0, 150%→1.5, 300%→3.0.')
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reason = fields.Text(string='Lý do')
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    deadline = fields.Datetime(
        string='Hạn thao tác', compute='_compute_deadline', store=True,
        help='Hạn cuối duyệt/sửa/từ chối = giờ bắt đầu trừ 1 phút.')
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True, readonly=True)
    attendance_id = fields.One2many(
        'hocba.shift.attendance', 'shift_id', string='Bản ghi chấm công')

    _OT_RATE = {'100': 1.0, '150': 1.5, '300': 3.0}

    @api.depends('ot_level')
    def _compute_rate(self):
        for rec in self:
            rec.rate = self._OT_RATE.get(rec.ot_level, 1.0)

    @api.depends('start')
    def _compute_deadline(self):
        for rec in self:
            rec.deadline = (rec.start - timedelta(minutes=1)) if rec.start else False

    def _auto_reject_expired(self, domain=None):
        """Tự động từ chối mọi ca pending đã quá hạn (deadline < now).
        domain: lọc thêm (AND). Trả recordset đã từ chối."""
        now = fields.Datetime.now()
        base = [('state', '=', 'pending'), ('deadline', '<', now)]
        expired = self.sudo().search(base + (domain or []))
        if expired:
            expired.write({
                'state': 'rejected',
                'review_note': 'Tự động từ chối: quá hạn duyệt',
                'decision_date': now,
            })
        return expired

    def _assert_actionable(self):
        """Raise nếu đã quá hạn thao tác với ca (now >= deadline)."""
        self.ensure_one()
        if self.deadline and fields.Datetime.now() >= self.deadline:
            raise UserError('Đã quá hạn thao tác với ca này (trước giờ bắt đầu 1 phút).')

    @api.constrains('start', 'end')
    def _check_times(self):
        for rec in self:
            if rec.start and rec.end and rec.end <= rec.start:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu.')

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if rec.state == 'pending':
                rec._notify_managers()
        return recs

    def write(self, vals):
        old_states = {r.id: r.state for r in self}
        res = super().write(vals)
        if 'state' in vals:
            for rec in self:
                if old_states[rec.id] == 'pending' and vals['state'] != 'pending':
                    rec._notify_employee_decision()
        return res

    def _notify_managers(self):
        """Thông báo cho quản lý trực tiếp + trưởng phòng + HR khi có ca mới."""
        self.ensure_one()
        if 'hb.notification' not in self.env:
            return

        recipients = self.env['res.users']
        if self.employee_id.parent_id.user_id:
            recipients |= self.employee_id.parent_id.user_id
        if self.employee_id.department_id.manager_id.user_id:
            recipients |= self.employee_id.department_id.manager_id.user_id

        hr_mgr_grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if hr_mgr_grp:
            recipients |= self.env['res.users'].sudo().search([
                ('all_group_ids', 'in', hr_mgr_grp.id), ('active', '=', True)])

        recipients -= self.env.user

        type_lbl = 'CTV' if self.shift_type == 'ctv' else 'OT'
        title = 'Đăng ký ca %s mới: %s' % (type_lbl, self.employee_id.name)

        emp_tz = self.employee_id.user_id.tz or 'UTC'
        local_start = fields.Datetime.context_timestamp(self.with_context(tz=emp_tz), self.start)
        local_end = fields.Datetime.context_timestamp(self.with_context(tz=emp_tz), self.end)

        body = '%s đăng ký ca %s ngày %s (%s–%s). Lý do: "%s"' % (
            self.employee_id.name, type_lbl, local_start.strftime('%d/%m/%Y'),
            local_start.strftime('%H:%M'), local_end.strftime('%H:%M'),
            self.reason or '')

        self.env['hb.notification'].sudo()._notify(
            recipients, category='attendance', kind='shift_pending', level='warning',
            title=title, body=body, target_view='attendance', target_tab='ot',
            target_ref=self.id)

    def _notify_employee_decision(self):
        """Thông báo cho nhân viên khi ca được duyệt/từ chối."""
        self.ensure_one()
        if 'hb.notification' not in self.env or not self.employee_id.user_id:
            return

        type_lbl = 'CTV' if self.shift_type == 'ctv' else 'OT'
        state_lbl = 'được DUYỆT' if self.state == 'approved' else 'bị TỪ CHỐI'
        level = 'success' if self.state == 'approved' else 'danger'

        emp_tz = self.employee_id.user_id.tz or 'UTC'
        local_start = fields.Datetime.context_timestamp(self.with_context(tz=emp_tz), self.start)

        title = 'Ca %s ngày %s đã %s' % (
            type_lbl, local_start.strftime('%d/%m/%Y'), state_lbl)
        body = 'Người duyệt: %s. %s' % (
            self.reviewer_id.name or 'Hệ thống',
            ('Ghi chú: "%s"' % self.review_note) if self.review_note else '')

        self.env['hb.notification'].sudo()._notify(
            self.employee_id.user_id, category='attendance', kind='shift_decision',
            level=level, title=title, body=body, target_view='attendance',
            target_tab='ot', target_ref=self.id)
