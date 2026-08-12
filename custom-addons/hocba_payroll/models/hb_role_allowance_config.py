from odoo import models, fields, api, _


class HbRoleAllowanceConfig(models.Model):
    """Cấu hình Thưởng & Phụ cấp cố định theo Chức vụ / Phòng ban (Role-based)."""
    _name = 'hb.role.allowance.config'
    _description = 'Role & Position Allowance Configuration'
    _order = 'id desc'

    name = fields.Char(string='Tên khoản Thưởng / Phụ cấp', required=True)
    job_id = fields.Many2one('hr.job', string='Chức vụ / Vị trí áp dụng (Đơn lẻ)', ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='Phòng ban áp dụng (Đơn lẻ)', ondelete='cascade')
    job_ids = fields.Many2many('hr.job', 'hb_role_allowance_job_rel', 'cfg_id', 'job_id', string='Các Chức vụ áp dụng')
    department_ids = fields.Many2many('hr.department', 'hb_role_allowance_dept_rel', 'cfg_id', 'dept_id', string='Các Phòng ban áp dụng')
    allowance_type = fields.Selection([
        ('responsibility', 'Phụ cấp Trách nhiệm'),
        ('holiday_bonus', 'Thưởng Lễ / Tết'),
        ('position_allowance', 'Phụ cấp Chức vụ'),
        ('other', 'Thưởng / Trợ cấp khác'),
    ], string='Loại khoản thưởng / phụ cấp', default='position_allowance', required=True)
    amount = fields.Float(string='Số tiền (VND)', required=True, digits=(16, 0), default=0.0)
    active = fields.Boolean(string='Hoạt động', default=True)
    notes = fields.Text(string='Ghi chú')
