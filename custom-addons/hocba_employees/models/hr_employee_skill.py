from datetime import timedelta

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
    x_cert_status = fields.Selection(
        selection=[
            ('none', 'Không hạn'),
            ('valid', 'Còn hạn'),
            ('expiring', 'Sắp hết hạn'),
            ('expired', 'Hết hạn'),
        ],
        string='Tình trạng chứng chỉ', compute='_compute_cert_status')

    @api.depends('x_cert_expiry')
    def _compute_cert_status(self):
        today = fields.Date.context_today(self)
        days = int(self.env['ir.config_parameter'].sudo().get_param(
            'hoc_ba.cert_alert_days', '60'))
        for rec in self:
            if not rec.x_cert_expiry:
                rec.x_cert_status = 'none'
            elif rec.x_cert_expiry < today:
                rec.x_cert_status = 'expired'
            elif rec.x_cert_expiry <= today + timedelta(days=days):
                rec.x_cert_status = 'expiring'
            else:
                rec.x_cert_status = 'valid'

    @api.constrains('x_cert_date', 'x_cert_expiry')
    def _check_cert_dates(self):
        for rec in self:
            if rec.x_cert_date and rec.x_cert_expiry \
                    and rec.x_cert_expiry <= rec.x_cert_date:
                raise ValidationError(_(
                    'Ngày hết hạn chứng chỉ phải sau ngày cấp.'))
