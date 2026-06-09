import re

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # --- F-001: Định danh & 4 trục phân loại Học Bá (đặc tả v2.1) ---
    x_employee_code = fields.Char(
        string='Mã nhân sự',
        copy=False,
        index=True,
        help='Mã định danh nội bộ, định dạng HB.xx — tự sinh, HR có thể sửa trước khi lưu lần đầu.',
    )
    # Trục 1 — Hình thức làm việc
    x_work_form = fields.Selection(
        selection=[
            ('offline', 'Offline'),
            ('online', 'Online'),
        ],
        string='Hình thức làm việc',
    )
    # Trục 2 — Tình trạng / Loại hợp đồng
    x_employment_status = fields.Selection(
        selection=[
            ('probation', 'Thử việc'),
            ('official', 'Chính thức'),
            ('intern', 'TTS'),
            ('parttime', 'Part-time'),
            ('ctv', 'CTV'),
            ('advisor', 'Cố vấn'),
            ('resigned', 'Nghỉ việc'),
        ],
        string='Tình trạng',
        default='probation',
        tracking=True,
    )
    # Trục 3 — Loại vị trí
    x_position_type = fields.Selection(
        selection=[
            ('manager', 'Quản lý'),
            ('staff', 'Nhân viên'),
            ('ctv', 'CTV'),
            ('freelancer', 'Freelancer'),
            ('advisor', 'Cố vấn'),
        ],
        string='Loại vị trí',
    )
    # Mốc lên chính thức (automation thử việc sẽ set ở Pha 3 — F-004/F-005)
    x_official_date = fields.Date(
        string='Ngày chính thức',
        tracking=True,
    )
    x_official_months = fields.Float(
        string='Số tháng chính thức',
        compute='_compute_official_months',
        help='(Hôm nay - Ngày chính thức) / 30 ngày.',
    )

    # --- F-002: Hồ sơ pháp lý Việt Nam ---
    x_id_date_issue = fields.Date(string='Ngày cấp CCCD')
    x_id_place_issue = fields.Char(string='Nơi cấp CCCD')
    x_pit_code = fields.Char(
        string='MST TNCN', groups='hr.group_hr_manager',
        help='Mã số thuế thu nhập cá nhân (10 hoặc 13 chữ số).')
    x_social_insurance_no = fields.Char(
        string='Số sổ BHXH', groups='hr.group_hr_manager',
        help='Số sổ Bảo hiểm xã hội (10 chữ số).')
    x_health_insurance_no = fields.Char(string='Số thẻ BHYT')
    x_health_care_place = fields.Char(string='Nơi KCB ban đầu')
    # Địa chỉ thường trú
    x_permanent_state_id = fields.Many2one(
        'res.country.state', string='Tỉnh/Thành (thường trú)',
        domain="[('country_id.code', '=', 'VN')]")
    x_permanent_ward = fields.Char(string='Phường/Xã (thường trú)')
    x_permanent_street = fields.Char(string='Số nhà/Đường (thường trú)')
    # Địa chỉ tạm trú
    x_current_same_as_permanent = fields.Boolean(
        string='Tạm trú giống thường trú', default=True)
    x_current_state_id = fields.Many2one(
        'res.country.state', string='Tỉnh/Thành (tạm trú)',
        domain="[('country_id.code', '=', 'VN')]")
    x_current_ward = fields.Char(string='Phường/Xã (tạm trú)')
    x_current_street = fields.Char(string='Số nhà/Đường (tạm trú)')

    # --- F-003: Người phụ thuộc (giảm trừ gia cảnh) ---
    x_dependent_ids = fields.One2many(
        'hr.employee.dependent', 'employee_id', string='Người phụ thuộc')
    x_active_dependent_count = fields.Integer(
        string='Số NPT đang hiệu lực',
        compute='_compute_active_dependent_count',
        help='Số người phụ thuộc đang trong thời gian được tính giảm trừ.')

    _sql_constraints = [
        ('x_employee_code_uniq', 'unique(x_employee_code)',
         'Mã nhân sự phải là duy nhất!'),
    ]

    @api.depends('x_official_date')
    def _compute_official_months(self):
        today = fields.Date.context_today(self)
        for emp in self:
            if emp.x_official_date:
                emp.x_official_months = (today - emp.x_official_date).days / 30.0
            else:
                emp.x_official_months = 0.0

    @api.depends('x_dependent_ids.date_start', 'x_dependent_ids.date_end')
    def _compute_active_dependent_count(self):
        today = fields.Date.context_today(self)
        for emp in self:
            emp.x_active_dependent_count = len(emp.x_dependent_ids.filtered(
                lambda d: d.date_start and d.date_start <= today
                and (not d.date_end or d.date_end >= today)
            ))

    @api.onchange('x_current_same_as_permanent', 'x_permanent_state_id',
                  'x_permanent_ward', 'x_permanent_street')
    def _onchange_current_same_as_permanent(self):
        # BR-012: khi "giống thường trú" → tạm trú mirror & lock
        for emp in self:
            if emp.x_current_same_as_permanent:
                emp.x_current_state_id = emp.x_permanent_state_id
                emp.x_current_ward = emp.x_permanent_ward
                emp.x_current_street = emp.x_permanent_street

    @api.constrains('x_pit_code')
    def _check_pit_code(self):
        for emp in self.sudo():
            if emp.x_pit_code and not re.fullmatch(r'\d{10}(\d{3})?', emp.x_pit_code):
                raise ValidationError(_('MST TNCN phải gồm 10 hoặc 13 chữ số.'))

    @api.constrains('x_social_insurance_no')
    def _check_social_insurance_no(self):
        for emp in self.sudo():
            if emp.x_social_insurance_no and not re.fullmatch(r'\d{10}', emp.x_social_insurance_no):
                raise ValidationError(_('Số sổ BHXH phải gồm đúng 10 chữ số.'))

    @api.constrains('x_id_date_issue', 'birthday')
    def _check_id_date_issue(self):
        today = fields.Date.context_today(self)
        for emp in self:
            if emp.x_id_date_issue:
                if emp.x_id_date_issue > today:
                    raise ValidationError(_('Ngày cấp CCCD không được sau hôm nay.'))
                if emp.birthday and emp.x_id_date_issue < emp.birthday + relativedelta(years=14):
                    raise ValidationError(_('Ngày cấp CCCD phải sau sinh nhật 14 tuổi.'))

    @api.constrains('x_employment_status', 'x_pit_code', 'x_social_insurance_no')
    def _check_official_required_fields(self):
        # BR-010: nhân viên chính thức bắt buộc khai MST + BHXH
        for emp in self.sudo():
            if emp.x_employment_status == 'official':
                missing = []
                if not emp.x_pit_code:
                    missing.append('MST TNCN')
                if not emp.x_social_insurance_no:
                    missing.append('Số sổ BHXH')
                if missing:
                    raise ValidationError(_(
                        'Nhân viên chính thức cần khai: %s (BR-010).') % ', '.join(missing))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_employee_code'):
                vals['x_employee_code'] = self.env['ir.sequence'].next_by_code(
                    'hocba.employee.code') or '/'
        return super().create(vals_list)
