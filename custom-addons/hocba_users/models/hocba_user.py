from odoo import models, fields, api
from datetime import datetime


class HocbaUser(models.Model):
    _name = 'hocba.user'
    _description = 'HOCBA User'
    _order = 'name'

    name = fields.Char(string='Full Name', required=True)
    user_id = fields.Many2one(
        'res.users',
        string='ODOO User',
        required=True,
        ondelete='cascade',
        unique=True
    )
    email = fields.Char(
        string='Email',
        related='user_id.email',
        readonly=True,
        store=True
    )
    role_id = fields.Many2one(
        'hocba.user.role',
        string='Role',
        required=True,
        ondelete='restrict'
    )
    role_code = fields.Char(
        string='Role Code',
        related='role_id.code',
        readonly=True,
        store=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        ondelete='set null'
    )
    employee_type_id = fields.Many2one(
        'hocba.employee.type',
        string='Employee Type',
        ondelete='set null',
        help='office_staff, teacher, or contractor'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        readonly=True,
        store=True
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Disable user without deleting'
    )
    last_login = fields.Datetime(
        string='Last Login',
        readonly=True
    )
    created_at = fields.Datetime(
        string='Created',
        default=fields.Datetime.now,
        readonly=True
    )
    updated_at = fields.Datetime(
        string='Updated',
        default=fields.Datetime.now,
        readonly=True
    )
    access_control_ids = fields.One2many(
        'hocba.access.control',
        'user_id',
        string='Access Control'
    )
    department_manager_ids = fields.One2many(
        'hocba.department.manager',
        'user_id',
        string='Managed Departments'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('user_id'):
                user = self.env['res.users'].browse(vals['user_id'])
                vals['name'] = user.name
        return super().create(vals_list)

    def write(self, vals):
        if 'name' not in vals and 'user_id' in vals:
            user = self.env['res.users'].browse(vals['user_id'])
            vals['name'] = user.name
        
        result = super().write(vals)
        
        for record in self:
            record.updated_at = datetime.now()
        
        return result

    def action_update_last_login(self):
        self.write({'last_login': datetime.now()})

    def action_deactivate(self):
        self.write({'is_active': False})

    def action_activate(self):
        self.write({'is_active': True})

    @api.depends('role_id')
    def _compute_role_code(self):
        for record in self:
            record.role_code = record.role_id.code if record.role_id else ''
