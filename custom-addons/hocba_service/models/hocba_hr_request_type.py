import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

# Người nhận đơn — dùng chung cho type.default_recipient và request.recipient_scope.
RECIPIENT_SEL = [
    ('hr', 'HR'),
    ('manager', 'Trưởng phòng'),
    ('both', 'HR và Trưởng phòng'),
]

# Mã loại: định danh ổn định cho tích hợp/log ⇒ chỉ chữ thường, số, gạch dưới.
CODE_RE = re.compile(r'^[a-z0-9_]+$')

# Trần của 2 ngưỡng cấu hình — chặn gõ nhầm ("50" thành "500") biến cả hệ thống
# thành không ai gửi ẩn danh được / hạn mức vô hạn.
PARAM_MAX = 999

# camelCase của SPA → field. Whitelist: KHÔNG cho client ghi field ngoài danh
# sách này (vd active — phải đi qua config_toggle_active để chặn tắt loại cuối).
CONFIG_FIELD_MAP = {
    'name': 'name',
    'code': 'code',
    'sequence': 'sequence',
    'defaultRecipient': 'default_recipient',
    'forceHrOnly': 'force_hr_only',
    'allowAnonymous': 'allow_anonymous',
    'allowAttachment': 'allow_attachment',
    'hasRating': 'has_rating',
    'slaDays': 'sla_days',
    'description': 'description',
}


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

    # ==================================================================
    # P6 — màn Cấu hình (Admin / HR Manager). SPEC SVC §10 dòng P6.
    #
    # Nghiệp vụ đặt ở model chứ không ở controller, đúng §10.1(a): test gọi
    # thẳng config_save/config_toggle_active/config_set_params, controller chỉ
    # parse JSON. `payload` là camelCase y như SPA gửi lên.
    # ==================================================================

    def _config_guard(self):
        """Chỉ HR Manager / Admin được sửa danh mục.

        HR User xử lý đơn nhưng không được đổi luật (SLA, ẩn danh, người nhận
        mặc định) — ACL đã cho họ read-only, guard này để trả 403 kèm thông điệp
        thay vì AccessError thô của ORM khi ghi.
        """
        from .hocba_hr_request import _svc_scope
        if not _svc_scope(self.env)['isHrManager']:
            raise AccessError(_(
                'Chỉ HR Manager hoặc Quản trị hệ thống được sửa cấu hình '
                'yêu cầu dịch vụ.'))

    def _config_clean_vals(self, payload, rec=None):
        """payload camelCase → vals ODOO, chỉ những key CÓ trong payload.

        Patch từng phần (không phải ghi đè cả bản ghi) để màn Cấu hình gửi 1
        field cũng được, và để quên field không vô tình reset về mặc định.
        """
        from .hocba_hr_request import SvcError
        vals = {}
        for key, field in CONFIG_FIELD_MAP.items():
            if key in payload:
                vals[field] = payload[key]

        if 'name' in vals:
            vals['name'] = (vals['name'] or '').strip()
            if not vals['name']:
                raise SvcError('name_required', _('Tên loại không được để trống.'))

        if 'code' in vals:
            code = (vals['code'] or '').strip().lower()
            if not code:
                raise SvcError('code_required', _('Mã loại không được để trống.'))
            if not CODE_RE.match(code):
                raise SvcError('code_invalid', _(
                    'Mã loại chỉ gồm chữ thường không dấu, số và gạch dưới '
                    '(vd: xin_nghi_viec).'))
            # active_test=False: loại đã tắt vẫn giữ chỗ mã (unique index không
            # lọc theo active) — không kiểm thì đụng IntegrityError lúc commit.
            dup = self.with_context(active_test=False).search(
                [('code', '=', code)], limit=1)
            if dup and dup.id != (rec.id if rec else 0):
                raise SvcError('code_duplicate', _(
                    'Mã "%(code)s" đã dùng cho loại "%(name)s".',
                    code=code, name=dup.name))
            vals['code'] = code

        if 'default_recipient' in vals \
                and vals['default_recipient'] not in dict(RECIPIENT_SEL):
            raise SvcError('scope_invalid', _('Người nhận mặc định không hợp lệ.'))

        if 'sla_days' in vals:
            try:
                sla = int(vals['sla_days'])
            except (TypeError, ValueError):
                raise SvcError('sla_invalid', _('SLA phải là số ngày.'))
            if sla <= 0:
                raise SvcError('sla_invalid', _('SLA phải lớn hơn 0 ngày.'))
            vals['sla_days'] = sla

        if 'sequence' in vals:
            try:
                vals['sequence'] = int(vals['sequence'])
            except (TypeError, ValueError):
                raise SvcError('sequence_invalid', _('Thứ tự phải là số.'))

        for key in ('force_hr_only', 'allow_anonymous', 'allow_attachment',
                    'has_rating'):
            if key in vals:
                vals[key] = bool(vals[key])
        if 'description' in vals:
            vals['description'] = (vals['description'] or '').strip()
        return vals

    @api.model
    def config_save(self, payload):
        """Thêm mới (không có `id`) hoặc sửa (có `id`) một loại yêu cầu."""
        from .hocba_hr_request import SvcError
        self._config_guard()
        payload = payload or {}

        rec = None
        if payload.get('id'):
            rec = self.with_context(active_test=False).browse(int(payload['id']))
            if not rec.exists():
                raise SvcError('type_invalid', _('Loại yêu cầu không tồn tại.'))
        vals = self._config_clean_vals(payload, rec=rec)

        # Savepoint riêng: @api.constrains (BR-SVC-09, BR-SVC-01) chỉ nổ lúc
        # flush — tức SAU khi INSERT/UPDATE đã chạy. Không có savepoint thì một
        # lần lưu sai để lại bản ghi dở trong transaction (và nếu người gọi
        # không phải controller thì không ai rollback hộ).
        with self.env.cr.savepoint():
            if rec:
                if vals:
                    rec.write(vals)
            else:
                if not vals.get('name'):
                    raise SvcError('name_required',
                                   _('Tên loại không được để trống.'))
                if not vals.get('code'):
                    raise SvcError('code_required',
                                   _('Mã loại không được để trống.'))
                rec = self.create(vals)
            rec.flush_recordset()
        return rec

    @api.model
    def config_toggle_active(self, type_id, active):
        """Bật/tắt một loại. Tắt = ẩn khỏi form gửi, KHÔNG đụng đơn đang chạy."""
        from .hocba_hr_request import SvcError
        self._config_guard()
        rec = self.with_context(active_test=False).browse(int(type_id or 0))
        if not rec.exists():
            raise SvcError('type_invalid', _('Loại yêu cầu không tồn tại.'))
        active = bool(active)
        if not active and rec.active:
            # search() mặc định active_test=True ⇒ chỉ đếm loại đang bật.
            if not self.search([('id', '!=', rec.id)], limit=1):
                raise SvcError('last_active_type', _(
                    'Đây là loại yêu cầu duy nhất còn bật — tắt nốt thì không '
                    'ai gửi được yêu cầu nào nữa.'))
        rec.write({'active': active})
        return rec

    @api.model
    def config_set_params(self, payload):
        """Sửa 2 ngưỡng ir.config_parameter của module (BR-SVC-03, BR-SVC-12).

        set_param đòi base.group_system mà HR Manager không có ⇒ .sudo() SAU khi
        _config_guard() đã chốt vai trò (đúng gotcha "Self-service" CLAUDE.md).
        """
        from .hocba_hr_request import (
            PARAM_ANON_DAILY, PARAM_MIN_ANON_DEPT, SvcError,
        )
        self._config_guard()
        payload = payload or {}
        # Nhãn tiếng Việt cho thông điệp lỗi — người dùng màn Cấu hình không
        # cần biết tên key camelCase của API.
        mapping = {
            'minAnonDeptSize': (PARAM_MIN_ANON_DEPT,
                                _('Số NV tối thiểu của phòng')),
            'anonDailyLimit': (PARAM_ANON_DAILY,
                               _('Số đơn ẩn danh mỗi người mỗi ngày')),
        }
        clean = {}
        for key, (param, label) in mapping.items():
            if key not in payload:
                continue
            try:
                value = int(payload[key])
            except (TypeError, ValueError):
                raise SvcError('param_invalid', _(
                    '"%s" phải là số nguyên.', label))
            if value < 1 or value > PARAM_MAX:
                raise SvcError('param_invalid', _(
                    '"%(label)s" phải trong khoảng 1..%(max)s.',
                    label=label, max=PARAM_MAX))
            clean[param] = value
        # Ghi SAU khi kiểm xong CẢ HAI: một key sai không được để key kia đã ghi.
        icp = self.env['ir.config_parameter'].sudo()
        for param, value in clean.items():
            icp.set_param(param, str(value))
        return clean
