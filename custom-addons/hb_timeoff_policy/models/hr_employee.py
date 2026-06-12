from odoo import models, fields, api, _

EMPLOYMENT_TYPE_SELECTION = [
    ('fulltime', 'Nhân viên Toàn thời gian'),
    ('teacher', 'Giảng viên (Chính thức)'),
    ('ta', 'Trợ giảng'),
    ('parttime', 'Nhân viên Bán thời gian'),
    ('visiting', 'Giảng viên Thỉnh giảng'),
    ('ctv', 'Cộng tác viên'),
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_employment_status = fields.Selection(
        EMPLOYMENT_TYPE_SELECTION,
        string='Loại nhân viên',
        tracking=True,
        index=True,
    )
    x_policy_override = fields.Boolean(
        string='Khóa chính sách thủ công',
        default=False,
        help='Nếu bật, hệ thống sẽ không tự động cập nhật chính sách '
             'nghỉ phép khi loại nhân viên thay đổi.',
    )
    x_current_policy_id = fields.Many2one(
        'hb.timeoff.policy.rule',
        string='Chính sách nghỉ phép hiện tại',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    x_policy_log_ids = fields.One2many(
        'hb.leave.policy.log',
        'employee_id',
        string='Lịch sử chính sách',
    )
    x_policy_log_count = fields.Integer(
        compute='_compute_policy_log_count',
        string='Lần thay đổi',
    )

    def _compute_policy_log_count(self):
        for emp in self:
            emp.x_policy_log_count = len(emp.x_policy_log_ids)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for emp in employees:
            if emp.x_employment_status and not emp.x_policy_override:
                emp.sudo()._apply_leave_policy(triggered_by='auto')
        return employees

    def write(self, vals):
        old_statuses = {emp.id: emp.x_employment_status for emp in self}
        result = super().write(vals)
        if 'x_employment_status' in vals:
            for emp in self:
                if (old_statuses[emp.id] != emp.x_employment_status
                        and not emp.x_policy_override):
                    emp.sudo()._apply_leave_policy(triggered_by='auto')
        return result

    def action_reapply_leave_policy(self):
        """Nút HR thủ công áp dụng lại chính sách."""
        for emp in self:
            emp.sudo()._apply_leave_policy(triggered_by='manual')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Chính sách nghỉ phép'),
                'message': _('Đã áp dụng lại chính sách nghỉ phép thành công.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_policy_log(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lịch sử chính sách — %s') % self.name,
            'res_model': 'hb.leave.policy.log',
            'domain': [('employee_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'default_employee_id': self.id},
        }

    # ------------------------------------------------------------------ #
    #  Core policy engine                                                  #
    # ------------------------------------------------------------------ #

    def _apply_leave_policy(self, triggered_by='auto'):
        """Áp dụng chính sách nghỉ phép theo loại nhân viên.

        - Expire allocation cũ do chính sách tạo ra (x_from_policy=True).
        - Tạo allocation mới theo policy rule.
        - Ghi log (hb.leave.policy.log) và chatter.
        """
        self.ensure_one()

        old_policy = self.x_current_policy_id

        # BR-021: Cộng tác viên — tắt toàn bộ policy allocation
        if self.x_employment_status == 'ctv':
            self._expire_policy_allocations()
            self.x_current_policy_id = False
            self.env['hb.leave.policy.log'].create({
                'employee_id': self.id,
                'old_policy_id': old_policy.id if old_policy else False,
                'new_policy_id': False,
                'triggered_by': triggered_by,
                'notes': 'Cộng tác viên — không có allocation nghỉ phép.',
            })
            self.message_post(
                body=_(
                    'Chính sách nghỉ phép đã được cập nhật: '
                    '<strong>Cộng tác viên</strong> — Không có allocation.'
                )
            )
            return

        # Tìm policy rule theo loại nhân viên
        policy_rule = self.env['hb.timeoff.policy.rule'].search([
            ('employment_type', '=', self.x_employment_status),
            ('active', '=', True),
        ], limit=1)

        if not policy_rule:
            # Gửi activity cảnh báo cho HR Admin
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Chưa có chính sách nghỉ phép'),
                note=_(
                    'Loại nhân viên [%(type)s] của nhân viên %(name)s chưa có '
                    'chính sách nghỉ phép. Vui lòng cấu hình trong '
                    'Time Off > Cấu hình > Chính sách Nghỉ phép.'
                ) % {
                    'type': self.x_employment_status or '',
                    'name': self.name,
                },
            )
            return

        # Expire allocation cũ từ chính sách
        self._expire_policy_allocations()

        # BR-020: Tính prorated days cho nhân viên vào giữa năm
        today = fields.Date.today()
        months_remaining = 13 - today.month
        proration_factor = min(months_remaining / 12.0, 1.0)

        new_allocations = self.env['hr.leave.allocation']

        if policy_rule.allocation_mode == 'accrual' and policy_rule.accrual_plan_id:
            # Tạo accrual allocation cho các leave type cần allocation
            for leave_type in policy_rule.leave_type_ids.filtered('requires_allocation'):
                alloc = self.env['hr.leave.allocation'].create({
                    'name': '%s — %s (%s)' % (leave_type.name, self.name, today.year),
                    'employee_id': self.id,
                    'holiday_status_id': leave_type.id,
                    'allocation_type': 'accrual',
                    'accrual_plan_id': policy_rule.accrual_plan_id.id,
                    'date_from': today,
                    'number_of_days': 0,
                    'x_from_policy': True,
                })
                alloc._action_validate()
                new_allocations |= alloc

        elif policy_rule.allocation_mode == 'fixed' and policy_rule.annual_days > 0:
            prorated_days = round(policy_rule.annual_days * proration_factor, 1)
            for leave_type in policy_rule.leave_type_ids.filtered('requires_allocation'):
                alloc = self.env['hr.leave.allocation'].create({
                    'name': '%s — %s (%s)' % (leave_type.name, self.name, today.year),
                    'employee_id': self.id,
                    'holiday_status_id': leave_type.id,
                    'allocation_type': 'regular',
                    'number_of_days': prorated_days,
                    'date_from': today,
                    'date_to': today.replace(month=12, day=31),
                    'x_from_policy': True,
                })
                alloc._action_validate()
                new_allocations |= alloc

        # Cập nhật chính sách hiện tại trên employee
        self.x_current_policy_id = policy_rule

        # BR-023: Ghi log thay đổi chính sách
        self.env['hb.leave.policy.log'].create({
            'employee_id': self.id,
            'old_policy_id': old_policy.id if old_policy else False,
            'new_policy_id': policy_rule.id,
            'triggered_by': triggered_by,
            'allocation_ids': [(6, 0, new_allocations.ids)],
        })

        # Ghi vào chatter
        self.message_post(
            body=_(
                'Chính sách nghỉ phép đã được cập nhật: '
                '<strong>%(policy)s</strong>'
            ) % {'policy': policy_rule.name}
        )

    def _expire_policy_allocations(self):
        """Expire các allocation được đánh dấu x_from_policy=True."""
        today = fields.Date.today()
        policy_allocs = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.id),
            ('x_from_policy', '=', True),
            ('state', '=', 'validate'),
        ])
        if policy_allocs:
            policy_allocs.write({'date_to': today})
