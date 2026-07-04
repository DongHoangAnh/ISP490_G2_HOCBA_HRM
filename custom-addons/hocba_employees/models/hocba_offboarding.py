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
