from odoo import models, fields


class DepartmentManager(models.Model):
    _name = 'hocba.department.manager'
    _description = 'Department Manager'
    _order = 'department_id, user_id'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        'hocba.user',
        string='Manager',
        required=True,
        ondelete='cascade'
    )
    can_manage_attendance = fields.Boolean(
        string='Can Manage Attendance',
        default=True
    )
    can_manage_leaves = fields.Boolean(
        string='Can Manage Leaves',
        default=True
    )
    can_manage_employees = fields.Boolean(
        string='Can Manage Employees',
        default=False
    )
    can_approve_reports = fields.Boolean(
        string='Can Approve Reports',
        default=False
    )

    _sql_constraints = [
        ('unique_department_manager',
         'UNIQUE(department_id, user_id)',
         'User can only manage each department once!'),
    ]
