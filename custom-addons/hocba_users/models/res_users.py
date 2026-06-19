from odoo import models, api

# Múi giờ mặc định cho hệ thống (Việt Nam). Đặt cho user mới không truyền tz
# để tránh lệch giờ khi tạo ca & cửa sổ check-in chấm công (xem _to_utc trong
# hocba_hrm: giờ wall-clock nhập vào được localize theo env.user.tz).
DEFAULT_TZ = 'Asia/Ho_Chi_Minh'


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('tz'):
                vals['tz'] = DEFAULT_TZ
        return super().create(vals_list)
