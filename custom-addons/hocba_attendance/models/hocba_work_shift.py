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

    # NOTE: Ràng buộc chống trùng giờ đã được gỡ theo yêu cầu nghiệp vụ — cho
    # phép mỗi ngày nhiều người & một người nhiều ca OT, kể cả khi giờ chồng nhau.
