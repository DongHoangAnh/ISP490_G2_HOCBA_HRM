from odoo import models, fields


class AccessControl(models.Model):
    _name = 'hocba.access.control'
    _description = 'Access Control'
    _order = 'user_id, module_name'

    user_id = fields.Many2one(
        'hocba.user',
        string='User',
        required=True,
        ondelete='cascade'
    )
    module_name = fields.Selection(
        [
            ('attendance', 'Attendance'),
            ('leaves', 'Leaves'),
            ('reports', 'Reports'),
            ('admin', 'Admin'),
            ('hr_management', 'HR Management'),
        ],
        string='Module',
        required=True
    )
    action = fields.Selection(
        [
            ('read', 'Read'),
            ('write', 'Write'),
            ('create', 'Create'),
            ('delete', 'Delete'),
            ('all', 'All'),
        ],
        string='Action',
        required=True
    )
    allowed = fields.Boolean(
        string='Allowed',
        default=True
    )
    notes = fields.Text(string='Notes')

    _unique_user_module_action = models.Constraint(
        'unique (user_id, module_name, action)',
        'Access control rule must be unique per user, module, and action!',
    )
