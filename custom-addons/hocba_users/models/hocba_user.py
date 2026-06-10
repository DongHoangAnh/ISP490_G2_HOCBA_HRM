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
        ondelete='cascade'
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
        related='employee_id.x_employee_type_id',
        store=True,
        readonly=False,
        help='Single source: lấy từ hồ sơ hr.employee (module hocba_employees)'
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

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _user_id_unique = models.Constraint(
        'unique (user_id)',
        'Each ODOO user can have only one HOCBA user!',
    )

    def _sync_role_groups(self, old_roles=None):
        """Áp nhóm quyền Odoo của role lên res.users (role = quyền thật).

        Khi đổi role: gỡ các nhóm của role cũ rồi thêm nhóm của role mới
        (các nhóm implied được Odoo tự tính lại).
        """
        for rec in self:
            if not rec.user_id:
                continue
            commands = []
            old_role = (old_roles or {}).get(rec.id)
            if old_role and old_role != rec.role_id:
                commands += [(3, gid) for gid in old_role.group_ids.ids]
            commands += [(4, gid) for gid in rec.role_id.group_ids.ids]
            if commands:
                rec.user_id.sudo().write({'group_ids': commands})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('user_id'):
                user = self.env['res.users'].browse(vals['user_id'])
                vals['name'] = user.name
        records = super().create(vals_list)
        records._sync_role_groups()
        return records

    def write(self, vals):
        if 'name' not in vals and 'user_id' in vals:
            user = self.env['res.users'].browse(vals['user_id'])
            vals['name'] = user.name
        # Gộp updated_at vào vals (gán trong vòng lặp sau super sẽ gọi lại
        # write -> đệ quy vô hạn)
        if 'updated_at' not in vals:
            vals = dict(vals, updated_at=fields.Datetime.now())

        old_roles = {rec.id: rec.role_id for rec in self} \
            if ('role_id' in vals or 'user_id' in vals) else None
        result = super().write(vals)
        if old_roles is not None:
            self._sync_role_groups(old_roles)
        # Khóa/mở tài khoản thật trên res.users (chặn cả /web/login chuẩn)
        if 'is_active' in vals:
            self.sudo().user_id.write({'active': vals['is_active']})

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
