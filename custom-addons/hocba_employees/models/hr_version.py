import re

from odoo import models, api, _
from odoo.exceptions import ValidationError


class HrVersion(models.Model):
    # Odoo 19: dữ liệu định danh nằm ở hr.version (hr.employee.identification_id
    # là field related, không lưu) → đặt constraint CCCD tại đây cho cùng bản ghi.
    _inherit = 'hr.version'

    @api.constrains('identification_id')
    def _check_identification_id_format(self):
        # G-01: CCCD Việt Nam gồm đúng 12 chữ số.
        # Hộ chiếu nước ngoài (có ký tự chữ) được tự động bỏ qua kiểm tra.
        for ver in self:
            v = (ver.identification_id or '').strip()
            if v and v.isdigit() and len(v) != 12:
                raise ValidationError(_(
                    'Số CCCD phải gồm đúng 12 chữ số '
                    '(hộ chiếu nước ngoài dùng mã có ký tự chữ).'))
