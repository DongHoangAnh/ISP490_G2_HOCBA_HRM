from odoo import models, fields, api


class WorkAssignment(models.Model):
    _name = 'hocba.work_assignment'
    _description = 'Work Assignment'
    _order = 'assigned_date desc, name'

    name = fields.Char(string='Assignment Name', required=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade'
    )
    job_title = fields.Char(string='Job Title')
    project_name = fields.Char(string='Project Name')
    description = fields.Text(string='Description')
    assigned_date = fields.Date(
        string='Assigned Date',
        required=True,
        default=fields.Date.context_today
    )
    end_date = fields.Date(string='End Date')
    active = fields.Boolean(default=True)
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        readonly=True,
        store=True
    )
    attendance_count = fields.Integer(
        string='Attendance Records',
        compute='_compute_attendance_count'
    )

    @api.depends('employee_id')
    def _compute_attendance_count(self):
        for assignment in self:
            assignment.attendance_count = self.env['hocba.attendance'].search_count(
                [('work_assignment_id', '=', assignment.id)]
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                vals['name'] = f"{employee.name} - {vals.get('project_name', 'Assignment')}"
        return super().create(vals_list)
