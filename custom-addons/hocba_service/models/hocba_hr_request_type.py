from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Người nhận đơn — dùng chung cho type.default_recipient và request.recipient_scope.
RECIPIENT_SEL = [
    ('hr', 'HR'),
    ('manager', 'Trưởng phòng'),
    ('both', 'HR và Trưởng phòng'),
]


class HocbaHrRequestType(models.Model):
    """Danh mục loại yêu cầu dịch vụ (SPEC SVC §3.4).

    Mỗi loại tự khai luật của mình (ẩn danh / đính kèm / SLA / người nhận) để
    thêm loại mới không phải sửa code — màn Cấu hình P6 chỉnh trực tiếp bảng này.
    """
    _name = 'hocba.hr.request.type'
    _description = 'Loại yêu cầu dịch vụ nhân sự'
    _order = 'sequence, id'

    name = fields.Char(string='Tên loại', required=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    default_recipient = fields.Selection(
        RECIPIENT_SEL, string='Người nhận mặc định',
        default='hr', required=True)
    force_hr_only = fields.Boolean(
        string='Bắt buộc chỉ HR',
        help='BR-SVC-01: loại khiếu nại về quản lý — luôn route về HR, '
             'Trưởng phòng không bao giờ đọc được.')
    allow_anonymous = fields.Boolean(string='Cho ẩn danh', default=False)
    allow_attachment = fields.Boolean(string='Cho đính kèm', default=True)
    has_rating = fields.Boolean(
        string='Có chấm điểm', default=False,
        help='Loại đánh giá — form hiện thang 1..5 sao.')
    sla_days = fields.Integer(
        string='SLA (ngày)', default=5, required=True,
        help='Số ngày DƯƠNG LỊCH kể từ lúc gửi tới hạn xử lý.')
    active = fields.Boolean(string='Đang dùng', default=True)
    description = fields.Text(
        string='Hướng dẫn',
        help='Hiện trên form SPA khi người gửi chọn loại này.')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _code_uniq = models.Constraint(
        'unique (code)',
        'Mã loại yêu cầu phải là duy nhất!',
    )

    @api.constrains('allow_anonymous', 'allow_attachment')
    def _check_anonymous_attachment(self):
        """BR-SVC-09: ẩn danh + đính kèm là không tương thích.

        ir.attachment.create_uid ghi người tạo và ACL ir.attachment mở cho
        base.group_user ⇒ một file đính kèm là đủ để lộ người gửi ẩn danh.
        """
        for rec in self:
            if rec.allow_anonymous and rec.allow_attachment:
                raise ValidationError(_(
                    'Loại "%s": cho ẩn danh thì không được cho đính kèm — '
                    'file đính kèm ghi lại người tạo nên sẽ lộ danh tính.',
                    rec.name))

    @api.constrains('sla_days')
    def _check_sla_days(self):
        for rec in self:
            if rec.sla_days <= 0:
                raise ValidationError(_('SLA phải lớn hơn 0 ngày.'))

    @api.constrains('force_hr_only', 'default_recipient')
    def _check_force_hr_only(self):
        """BR-SVC-01: loại HR-only không được mặc định gửi Trưởng phòng."""
        for rec in self:
            if rec.force_hr_only and rec.default_recipient != 'hr':
                raise ValidationError(_(
                    'Loại "%s" bắt buộc chỉ HR nên người nhận mặc định '
                    'phải là HR.', rec.name))
