from odoo import models, fields, api


class AttendanceRequest(models.Model):
    """Đơn xin sửa/tạo bản ghi chấm công cho 1 ngày (Gói 3).
    user gửi (state=pending) → manager duyệt (chỉnh giờ được) hoặc từ chối.
    Duyệt thì áp vào hocba.attendance (sửa bản ghi có sẵn / tạo nếu ngày thiếu)."""
    _name = 'hocba.attendance.request'
    _description = 'Đơn chấm công'
    _order = 'create_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    request_date = fields.Date(string='Ngày công', required=True)
    attendance_id = fields.Many2one(
        'hocba.attendance', string='Bản ghi', ondelete='set null',
        help='Bản ghi cần sửa; rỗng = ngày thiếu (duyệt thì tạo mới).')
    proposed_check_in = fields.Datetime(string='Giờ vào đề xuất')
    proposed_check_out = fields.Datetime(string='Giờ ra đề xuất')
    reason = fields.Text(string='Lý do', required=True)
    state = fields.Selection(
        [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
         ('rejected', 'Từ chối')],
        string='Trạng thái', default='pending', index=True, required=True)
    reviewer_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    review_note = fields.Text(string='Ghi chú duyệt')
    decision_date = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if rec.state == 'pending':
                rec._notify_managers()
        return recs

    def write(self, vals):
        old_states = {r.id: r.state for r in self}
        res = super().write(vals)
        if 'state' in vals:
            for rec in self:
                if old_states[rec.id] == 'pending' and vals['state'] != 'pending':
                    rec._notify_employee_decision()
        return res

    def _notify_managers(self):
        """Thông báo cho quản lý trực tiếp + trưởng phòng + HR khi có đơn mới."""
        self.ensure_one()
        if 'hb.notification' not in self.env:
            return

        recipients = self.env['res.users']
        # 1. Quản lý trực tiếp
        if self.employee_id.parent_id.user_id:
            recipients |= self.employee_id.parent_id.user_id
        # 2. Trưởng phòng
        if self.employee_id.department_id.manager_id.user_id:
            recipients |= self.employee_id.department_id.manager_id.user_id
        # 3. HR Manager
        hr_mgr_grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if hr_mgr_grp:
            recipients |= self.env['res.users'].sudo().search([
                ('all_group_ids', 'in', hr_mgr_grp.id), ('active', '=', True)])

        recipients -= self.env.user

        title = 'Đơn chấm công chờ duyệt: %s' % self.employee_id.name
        body = '%s xin sửa chấm công ngày %s. Lý do: "%s"' % (
            self.employee_id.name, self.request_date.strftime('%d/%m/%Y'), self.reason)

        self.env['hb.notification'].sudo()._notify(
            recipients, category='attendance', kind='request_pending', level='warning',
            title=title, body=body, target_view='attendance', target_tab='requests',
            target_ref=self.id)

    def _notify_employee_decision(self):
        """Thông báo cho nhân viên khi đơn được duyệt/từ chối."""
        self.ensure_one()
        if 'hb.notification' not in self.env or not self.employee_id.user_id:
            return

        state_lbl = 'được DUYỆT' if self.state == 'approved' else 'bị TỪ CHỐI'
        level = 'success' if self.state == 'approved' else 'danger'
        title = 'Đơn chấm công ngày %s đã %s' % (
            self.request_date.strftime('%d/%m/%Y'), state_lbl)
        body = 'Người duyệt: %s. %s' % (
            self.reviewer_id.name or 'Hệ thống',
            ('Ghi chú: "%s"' % self.review_note) if self.review_note else '')

        self.env['hb.notification'].sudo()._notify(
            self.employee_id.user_id, category='attendance', kind='request_decision',
            level=level, title=title, body=body, target_view='attendance',
            target_tab='requests', target_ref=self.id)
