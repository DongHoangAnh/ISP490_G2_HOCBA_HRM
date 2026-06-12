from odoo import models, fields


class HbLeavePolicyLog(models.Model):
    _name = 'hb.leave.policy.log'
    _description = 'Lịch sử thay đổi Chính sách Nghỉ phép'
    _order = 'applied_date desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên',
        required=True,
        ondelete='cascade',
        index=True,
    )
    old_policy_id = fields.Many2one(
        'hb.timeoff.policy.rule',
        string='Chính sách cũ',
        ondelete='set null',
    )
    new_policy_id = fields.Many2one(
        'hb.timeoff.policy.rule',
        string='Chính sách mới',
        ondelete='set null',
    )
    applied_date = fields.Datetime(
        string='Ngày áp dụng',
        default=fields.Datetime.now,
        required=True,
    )
    triggered_by = fields.Selection([
        ('auto', 'Tự động (thay đổi loại NV)'),
        ('manual', 'HR thủ công'),
        ('probation', 'Kết thúc thử việc'),
    ], string='Kích hoạt bởi', default='auto', required=True)
    notes = fields.Text(string='Ghi chú')
    allocation_ids = fields.Many2many(
        'hr.leave.allocation',
        'hb_policy_log_allocation_rel',
        'log_id',
        'allocation_id',
        string='Allocations đã tạo',
    )
