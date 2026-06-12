from odoo import models, fields, api

EMPLOYMENT_TYPE_SELECTION = [
    ('fulltime', 'Nhân viên Toàn thời gian'),
    ('teacher', 'Giảng viên (Chính thức)'),
    ('ta', 'Trợ giảng'),
    ('parttime', 'Nhân viên Bán thời gian'),
    ('visiting', 'Giảng viên Thỉnh giảng'),
    ('ctv', 'Cộng tác viên'),
]


class HbTimeoffPolicyRule(models.Model):
    _name = 'hb.timeoff.policy.rule'
    _description = 'Quy tắc Chính sách Nghỉ phép'
    _rec_name = 'name'
    _order = 'employment_type'

    name = fields.Char(string='Tên chính sách', required=True)
    employment_type = fields.Selection(
        EMPLOYMENT_TYPE_SELECTION,
        string='Loại nhân viên',
        required=True,
        index=True,
    )
    leave_type_ids = fields.Many2many(
        'hr.leave.type',
        'hb_policy_rule_leave_type_rel',
        'rule_id',
        'leave_type_id',
        string='Loại nghỉ phép được phép',
    )
    accrual_plan_id = fields.Many2one(
        'hr.leave.accrual.plan',
        string='Kế hoạch tích lũy phép năm',
    )
    allocation_mode = fields.Selection([
        ('accrual', 'Tích lũy tự động (Accrual)'),
        ('fixed', 'Phân bổ cố định hàng năm'),
        ('none', 'Không phân bổ'),
    ], string='Chế độ phân bổ phép năm', default='none', required=True)
    annual_days = fields.Float(
        string='Số ngày phép năm',
        default=0,
        help='Chỉ dùng khi chế độ phân bổ = Phân bổ cố định',
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Ghi chú chính sách')
    employee_count = fields.Integer(
        string='Nhân viên áp dụng',
        compute='_compute_employee_count',
    )

    _unique_employment_type = models.Constraint(
        'UNIQUE(employment_type)',
        'Mỗi loại nhân viên chỉ được có một chính sách nghỉ phép duy nhất.',
    )

    def _compute_employee_count(self):
        for rule in self:
            rule.employee_count = self.env['hr.employee'].search_count([
                ('x_hb_leave_emp_type', '=', rule.employment_type),
            ])

    def action_view_employees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nhân viên áp dụng chính sách',
            'res_model': 'hr.employee',
            'domain': [('x_hb_leave_emp_type', '=', self.employment_type)],
            'view_mode': 'list,form',
        }
