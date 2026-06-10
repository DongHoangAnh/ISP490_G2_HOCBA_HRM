from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployeeSkill(models.Model):
    # F-008/F-009: theo dõi chứng chỉ (HSK/HSKK/Sư phạm...) kèm hạn hiệu lực
    _inherit = 'hr.employee.skill'

    x_cert_date = fields.Date(string='Ngày cấp chứng chỉ')
    x_cert_expiry = fields.Date(string='Ngày hết hạn chứng chỉ')
    x_cert_verified = fields.Boolean(
        string='Đã xác minh', default=False,
        help='HR bật sau khi kiểm tra bản gốc. Chỉ chứng chỉ đã xác minh '
             'mới được CRON cảnh báo hết hạn (GĐ-09).')

    @api.constrains('x_cert_date', 'x_cert_expiry')
    def _check_cert_dates(self):
        for rec in self:
            if rec.x_cert_date and rec.x_cert_expiry \
                    and rec.x_cert_expiry <= rec.x_cert_date:
                raise ValidationError(_(
                    'Ngày hết hạn chứng chỉ phải sau ngày cấp.'))
