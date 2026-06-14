from odoo import models, fields, api, _


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    x_is_emergency = fields.Boolean(
        string='Nghỉ khẩn cấp',
        related='holiday_status_id.x_is_emergency_type',
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        emergency = leaves.filtered(lambda l: l.x_is_emergency)
        if emergency:
            emergency._notify_emergency_fast_track()
        return leaves

    def _notify_emergency_fast_track(self):
        model_description = self.env['ir.model']._get('hr.leave').name
        for leave in self:
            recipients = self.env['res.partner']

            # Direct manager của nhân viên
            if leave.employee_id.leave_manager_id:
                recipients |= leave.employee_id.leave_manager_id.partner_id

            # HR responsible được chỉ định trên loại nghỉ
            if leave.holiday_status_id.responsible_ids:
                recipients |= leave.holiday_status_id.responsible_ids.mapped('partner_id')
            else:
                # Fallback: tất cả HR Officer trong hệ thống
                hr_group = self.env.ref(
                    'hr_holidays.group_hr_holidays_user', raise_if_not_found=False
                )
                if hr_group:
                    hr_users = self.env['res.users'].search([
                        ('all_group_ids', 'in', hr_group.id),
                        ('active', '=', True),
                    ])
                    recipients |= hr_users.mapped('partner_id')

            # Đăng ký theo dõi để nhận cập nhật tiếp theo
            if recipients:
                leave.sudo().message_subscribe(partner_ids=recipients.ids)

            # Thông báo inbox + email tức thời
            if recipients:
                date_from_str = (
                    leave.date_from.strftime('%d/%m/%Y') if leave.date_from else '?'
                )
                date_to_str = (
                    leave.date_to.strftime('%d/%m/%Y') if leave.date_to else '?'
                )
                leave.sudo().message_notify(
                    partner_ids=recipients.ids,
                    model_description=model_description,
                    subject=_('[KHAN CAP] Don nghi khan cap — %s', leave.employee_id.name),
                    body=_(
                        '<b>%(employee)s</b> vừa gửi đơn <b>Nghỉ Khẩn Cấp</b> '
                        'từ %(date_from)s đến %(date_to)s.<br/>'
                        'Vui lòng xử lý <b>ưu tiên</b> — chỉ cần 1 bước phê duyệt.',
                        employee=leave.employee_id.name,
                        date_from=date_from_str,
                        date_to=date_to_str,
                    ),
                    email_layout_xmlid='mail.mail_notification_layout',
                    subtitles=[leave.display_name],
                )

            # Ghi chú vào chatter của đơn nghỉ
            leave.sudo().message_post(
                body=_(
                    'Đơn nghỉ khẩn cấp đã được ghi nhận. '
                    'HR và Manager trực tiếp đã được thông báo để xử lý ưu tiên. '
                    'Quy trình 1 bước phê duyệt được áp dụng.'
                ),
                subtype_xmlid='mail.mt_note',
            )
