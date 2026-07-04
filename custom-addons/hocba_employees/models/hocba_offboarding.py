from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class HocbaOffboarding(models.Model):
    _name = 'hocba.offboarding'
    _description = 'Đơn / Quy trình thôi việc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    SOURCE_SEL = [
        ('self', 'NV tự nộp'),
        ('hr', 'HR khởi tạo'),
        ('probation', 'Rớt thử việc'),
    ]
    REASON_SEL = [
        ('voluntary', 'Tự nguyện'),
        ('performance', 'Không đạt'),
        ('contract_end', 'Hết hạn HĐ'),
        ('other', 'Khác'),
    ]
    STATE_SEL = [
        ('draft', 'Nháp'),
        ('submitted', 'Chờ quản lý duyệt'),
        ('mgr_approved', 'Chờ HR duyệt'),
        ('hr_approved', 'Chờ hoàn tất'),
        ('done', 'Đã nghỉ'),
        ('refused', 'Từ chối'),
        ('cancelled', 'Đã huỷ'),
    ]

    name = fields.Char(string='Mã đơn', readonly=True, copy=False, default='/')
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True, tracking=True)
    source = fields.Selection(
        SOURCE_SEL, string='Nguồn', default='self', required=True)
    reason_type = fields.Selection(
        REASON_SEL, string='Loại lý do', required=True, default='voluntary')
    reason = fields.Text(string='Lý do chi tiết')
    request_date = fields.Date(
        string='Ngày nộp đơn', default=fields.Date.context_today)
    expected_leave_date = fields.Date(string='Ngày nghỉ dự kiến', required=True)
    actual_leave_date = fields.Date(string='Ngày nghỉ thực tế', readonly=True)
    mgr_approved_by = fields.Many2one('res.users', string='Quản lý duyệt', readonly=True)
    mgr_approved_date = fields.Datetime(string='Ngày QL duyệt', readonly=True)
    hr_approved_by = fields.Many2one('res.users', string='HR duyệt', readonly=True)
    hr_approved_date = fields.Datetime(string='Ngày HR duyệt', readonly=True)
    chk_handover = fields.Boolean(string='Đã bàn giao công việc')
    chk_payroll = fields.Boolean(string='Đã chốt lương/công nợ')
    chk_documents = fields.Boolean(string='Đã lưu hồ sơ')
    asset_pending_count = fields.Integer(
        string='Tài sản chưa thu hồi', compute='_compute_asset_pending_count')
    state = fields.Selection(
        STATE_SEL, string='Trạng thái', default='draft',
        required=True, tracking=True, copy=False)
    prev_employment_status = fields.Char(readonly=True, copy=False)
    note = fields.Text(string='Ghi chú')

    @api.depends('employee_id.x_asset_ids.state')
    def _compute_asset_pending_count(self):
        for rec in self:
            rec.asset_pending_count = len(rec.employee_id.x_asset_ids.filtered(
                lambda a: a.state == 'assigned'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hocba.offboarding') or '/'
        return super().create(vals_list)

    def _ensure_manages(self):
        """Raise nếu user hiện tại không quản lý phạm vi của NV (và không HR/su)."""
        self.ensure_one()
        user = self.env.user
        if self.env.su or user.has_group('hr.group_hr_manager'):
            return
        emp = self.employee_id.sudo()
        if emp._hocba_user_manages_dept(user):
            return
        if emp.parent_id and emp.parent_id.user_id == user:
            return
        if user.has_group('hocba_employees.group_hocba_giaovu') \
                and emp.x_employee_type_id.code == 'teacher':
            return
        raise AccessError(_(
            'Bạn không có quyền duyệt đơn nghỉ của nhân viên này.'))

    def _is_hr_manager(self):
        return self.env.su or self.env.user.has_group('hr.group_hr_manager')

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Chỉ đơn nháp mới được nộp.'))
            user = rec.env.user
            if not rec._is_hr_manager() and rec.employee_id != user.employee_id:
                raise AccessError(_('Chỉ được nộp đơn nghỉ của chính mình.'))
            rec.state = 'submitted'
            rec.message_post(body=_('📤 Đã nộp đơn nghỉ việc.'))

    def action_mgr_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(_('Đơn không ở trạng thái chờ quản lý duyệt.'))
            rec._ensure_manages()
            rec.mgr_approved_by = rec.env.user
            rec.mgr_approved_date = fields.Datetime.now()
            rec.prev_employment_status = rec.employee_id.x_employment_status
            rec.employee_id.sudo().with_context(
                hocba_gate_automation=True).write({'x_employment_status': 'exiting'})
            rec.state = 'mgr_approved'
            rec.message_post(body=_('✅ Quản lý đã duyệt đơn nghỉ.'))

    def action_hr_approve(self):
        for rec in self:
            if rec.state != 'mgr_approved':
                raise ValidationError(_('Đơn chưa được quản lý duyệt.'))
            if not rec._is_hr_manager():
                raise AccessError(_('Chỉ HR Manager được duyệt bước này.'))
            rec.hr_approved_by = rec.env.user
            rec.hr_approved_date = fields.Datetime.now()
            rec.state = 'hr_approved'
            rec.message_post(body=_(
                '✅ HR đã duyệt — chờ thu hồi tài sản & hoàn tất.'))
