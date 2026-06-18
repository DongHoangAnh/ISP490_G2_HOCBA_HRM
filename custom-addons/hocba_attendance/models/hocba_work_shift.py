from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    rate = fields.Float(string='Hệ số', default=1.0)
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reason = fields.Text(string='Lý do')
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True, readonly=True)

    @api.constrains('start', 'end')
    def _check_times(self):
        for rec in self:
            if rec.start and rec.end and rec.end <= rec.start:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu.')

    @api.constrains('start', 'end', 'employee_id', 'state')
    def _check_overlap(self):
        for rec in self:
            if rec.state not in ('pending', 'approved') or not (rec.start and rec.end):
                continue
            clash = self.search_count([
                ('id', '!=', rec.id),
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ('pending', 'approved')),
                ('start', '<', rec.end),
                ('end', '>', rec.start),
            ])
            if clash:
                raise ValidationError('Ca bị trùng giờ với ca khác.')

    @api.model
    def _default_rate(self, start_dt):
        """Hệ số gợi ý theo thứ trong tuần (local): T2–T6 = 1.5; T7/CN = 2.0.
        (Lễ/đêm + 30% để Gói 4C.) start_dt là Datetime UTC naive."""
        if not start_dt:
            return 1.0
        local = fields.Datetime.context_timestamp(self.env.user, start_dt)
        return 2.0 if local.weekday() >= 5 else 1.5
