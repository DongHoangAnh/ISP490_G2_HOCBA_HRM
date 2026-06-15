import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# x_hb_leave_emp_type values defined in hb_timeoff_policy
INSTRUCTOR_TYPES = frozenset({'teacher', 'ta', 'visiting'})


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    x_schedule_conflict = fields.Boolean(
        string='Có xung đột lịch dạy',
        default=False,
        copy=False,
        help='Tự động đặt True khi hệ thống phát hiện buổi dạy trùng với thời gian nghỉ.',
    )
    x_academic_review_required = fields.Boolean(
        string='Cần phê duyệt Academic Manager',
        default=False,
        copy=False,
    )
    x_replacement_note = fields.Text(
        string='Ghi chú bố trí thay thế',
        copy=False,
        help='Mô tả cách bố trí giảng viên thay thế cho các buổi dạy bị ảnh hưởng.',
    )
    x_conflict_info = fields.Text(
        string='Buổi dạy xung đột',
        readonly=True,
        copy=False,
        help='Danh sách buổi dạy xung đột (tự động điền bởi hệ thống).',
    )
    # BR-030: cờ đánh dấu đơn nghỉ đang chờ kiểm tra xung đột bất đồng bộ.
    # Việc dò xung đột chạy qua ir.cron (kích hoạt ngay bằng _trigger) để
    # KHÔNG block giao diện khi nhân viên gửi đơn.
    x_conflict_check_pending = fields.Boolean(
        string='Chờ kiểm tra xung đột lịch dạy',
        default=False,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        instructor_leaves = leaves.filtered(
            lambda l: getattr(l.employee_id, 'x_hb_leave_emp_type', False) in INSTRUCTOR_TYPES
        )
        if instructor_leaves:
            instructor_leaves._schedule_conflict_check_async()
        return leaves

    def write(self, vals):
        result = super().write(vals)
        if 'date_from' in vals or 'date_to' in vals:
            instructor_leaves = self.filtered(
                lambda l: getattr(l.employee_id, 'x_hb_leave_emp_type', False) in INSTRUCTOR_TYPES
            )
            if instructor_leaves:
                instructor_leaves._schedule_conflict_check_async()
        return result

    def _schedule_conflict_check_async(self):
        """BR-030: Lên lịch dò xung đột bất đồng bộ, không block UI.

        Đặt cờ pending rồi kích hoạt ir.cron chạy ngay (_trigger). Cron sẽ
        xử lý trong transaction riêng và post kết quả vào chatter trong vài giây.
        """
        self.filtered(lambda l: not l.x_conflict_check_pending).write(
            {'x_conflict_check_pending': True}
        )
        cron = self.env.ref(
            'hocba_timeoff.ir_cron_schedule_conflict_check',
            raise_if_not_found=False,
        )
        if cron:
            cron.sudo()._trigger()

    @api.model
    def _cron_process_pending_conflict_checks(self, batch_limit=200):
        """BR-030: Xử lý các đơn nghỉ đang chờ dò xung đột (chạy bởi ir.cron)."""
        pending = self.search(
            [('x_conflict_check_pending', '=', True)], limit=batch_limit
        )
        if not pending:
            return
        # Xóa cờ trước để write() bên trong _check_schedule_conflict không
        # vô tình kích hoạt lại vòng lặp async.
        pending.write({'x_conflict_check_pending': False})
        pending._check_schedule_conflict()
        # Nếu còn đơn chờ (vượt batch_limit), kích hoạt cron chạy tiếp.
        if self.search_count([('x_conflict_check_pending', '=', True)]):
            cron = self.env.ref(
                'hocba_timeoff.ir_cron_schedule_conflict_check',
                raise_if_not_found=False,
            )
            if cron:
                cron.sudo()._trigger()

    def action_approve(self, check_state=True):
        # BR-031: x_replacement_note required at final approval when conflict found
        for leave in self:
            is_final = leave.validation_type != 'both' or leave.state == 'validate1'
            is_emergency = getattr(leave, 'x_is_emergency', False)
            if (is_final
                    and leave.x_schedule_conflict
                    and not leave.x_replacement_note
                    and not is_emergency):
                raise ValidationError(_(
                    'Đơn nghỉ của %(name)s có xung đột lịch dạy. '
                    'Vui lòng điền trường "Ghi chú bố trí thay thế" '
                    'trước khi phê duyệt (BR-031).',
                    name=leave.employee_id.name,
                ))
        return super().action_approve(check_state=check_state)

    def _check_schedule_conflict(self):
        """Kiểm tra xung đột giữa đơn nghỉ và lịch dạy đã xác nhận.

        Bỏ qua nếu model teaching.session chưa được cài đặt.
        """
        TeachingSession = self.env.get('teaching.session')
        if TeachingSession is None:
            _logger.warning(
                'hb_timeoff_schedule_conflict: Schedule conflict check skipped: '
                'teaching.session model not found.'
            )
            return

        academic_group = self.env.ref(
            'hocba_timeoff.group_academic_manager',
            raise_if_not_found=False,
        )
        hr_manager_group = self.env.ref(
            'hr_holidays.group_hr_holidays_manager',
            raise_if_not_found=False,
        )
        # BR-033: chỉ bỏ qua trial lessons nếu field tồn tại trên model
        has_trial_field = 'x_is_trial' in TeachingSession._fields

        for leave in self:
            if not leave.date_from or not leave.date_to:
                continue

            domain = [
                ('instructor_id', '=', leave.employee_id.id),
                ('session_date', '>=', leave.date_from.date()),
                ('session_date', '<=', leave.date_to.date()),
                ('status', 'in', ['confirmed', 'in_progress']),
            ]
            if has_trial_field:
                domain.append(('x_is_trial', '!=', True))

            sessions = TeachingSession.search(domain)

            if sessions:
                lines = []
                for s in sessions:
                    date_val = s.session_date
                    date_str = date_val.strftime('%d/%m/%Y') if date_val else '?'
                    lines.append('• %s — %s' % (date_str, s.display_name or str(s.id)))
                conflict_info = '\n'.join(lines)

                is_emergency = getattr(leave, 'x_is_emergency', False)

                leave.write({
                    'x_schedule_conflict': True,
                    'x_conflict_info': conflict_info,
                    'x_academic_review_required': not is_emergency,
                })

                # Tìm recipients: Academic Manager group, fallback HR Manager
                recipients = self.env['res.partner']
                if academic_group:
                    academic_users = self.env['res.users'].search([
                        ('all_group_ids', 'in', academic_group.id),
                        ('active', '=', True),
                    ])
                    recipients = academic_users.mapped('partner_id')

                if not recipients and hr_manager_group:
                    hr_managers = self.env['res.users'].search([
                        ('all_group_ids', 'in', hr_manager_group.id),
                        ('active', '=', True),
                    ])
                    recipients = hr_managers.mapped('partner_id')

                if recipients:
                    leave.sudo().message_subscribe(partner_ids=recipients.ids)

                # Activity cho Academic Manager (không áp dụng cho đơn khẩn cấp)
                if leave.x_academic_review_required and recipients:
                    leave.sudo().activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Xử lý lịch dạy thay thế'),
                        note=_(
                            '<b>%(employee)s</b> xin nghỉ có %(count)d buổi dạy xung đột:<br/>'
                            '%(sessions)s<br/>'
                            'Vui lòng bố trí giảng viên thay thế và điền ghi chú '
                            'trước khi phê duyệt.',
                            employee=leave.employee_id.name,
                            count=len(sessions),
                            sessions=conflict_info.replace('\n', '<br/>'),
                        ),
                        user_id=(
                            recipients[0].user_ids[:1].id
                            if recipients[0].user_ids
                            else self.env.user.id
                        ),
                    )

                leave.sudo().message_post(
                    body=_(
                        'Phát hiện <b>%(count)d</b> buổi dạy xung đột:<br/>'
                        '%(sessions)s<br/><br/>%(extra)s',
                        count=len(sessions),
                        sessions=conflict_info.replace('\n', '<br/>'),
                        extra=(
                            'Đã yêu cầu phê duyệt từ <b>Academic Manager</b>.'
                            if leave.x_academic_review_required
                            else 'Đơn nghỉ khẩn cấp — xung đột được ghi nhận '
                                 'nhưng không chặn luồng duyệt.'
                        ),
                    ),
                    subtype_xmlid='mail.mt_note',
                )

            else:
                # Không có xung đột — reset flags nếu trước đó đã set
                if leave.x_schedule_conflict:
                    leave.write({
                        'x_schedule_conflict': False,
                        'x_conflict_info': False,
                        'x_academic_review_required': False,
                    })
