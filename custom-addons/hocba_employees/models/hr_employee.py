from odoo import models, fields, api


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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_employee_code'):
                vals['x_employee_code'] = self.env['ir.sequence'].next_by_code(
                    'hocba.employee.code') or '/'
        return super().create(vals_list)
