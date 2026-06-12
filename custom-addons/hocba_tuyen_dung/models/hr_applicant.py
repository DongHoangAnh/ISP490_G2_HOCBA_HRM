from odoo import fields, models


class HrApplicantHocBaExt(models.Model):
    _inherit = 'hr.applicant'

    # ── Sheet 7.4 — Danh sách CV ─────────────────────────────────────────────
    date_received = fields.Date(string='Thời gian nhận CV', index=True)
    ctv_tuyen_dung = fields.Char(string='CTV tuyển dụng')
    cv_link = fields.Char(string='Link CV / Tên file')
    cv_filter_result = fields.Selection([
        ('pass',          'Pass'),
        ('fail',          'Fail'),
        ('potential',     'Tiềm năng'),
        ('contact_later', 'Liên hệ sau'),
    ], string='Lọc CV', tracking=True)
    cv_note = fields.Text(string='Ghi chú CV')
    call_status = fields.Selection([
        ('agree',          'Đồng ý PV'),
        ('refuse',         'Từ chối PV'),
        ('potential',      'Tiềm năng'),
        ('contact_later',  'Liên hệ sau'),
    ], string='Trạng thái gọi điện', tracking=True)
    interview_date = fields.Date(string='Ngày hẹn PV')
    interview_time = fields.Char(string='Giờ hẹn PV', help='VD: 10h, 10h30, 14h00')
    interviewer_name = fields.Char(string='Người PV')

    # ── Sheet 7.5 — Danh sách phỏng vấn ─────────────────────────────────────
    attendance_status = fields.Selection([
        ('present', 'Đã đến'),
        ('absent',  'Không đến'),
    ], string='Tham gia PV', tracking=True)
    interview_result = fields.Selection([
        ('pass',      'Pass'),
        ('fail',      'Fail'),
        ('potential', 'Tiềm năng'),
    ], string='Kết quả PV', tracking=True)
    offer_content = fields.Text(string='Offer')
    start_date = fields.Date(string='Ngày nhận việc')
    offer_note = fields.Text(string='Ghi chú offer')
    candidate_confirmed = fields.Char(string='UV xác nhận mail', help='VD: Đã xác nhận, Đã phản hồi')

    # ── Sheet 7.7 — Mail mẫu ─────────────────────────────────────────────────
    def _open_mail_compose_with_template(self, template_xmlid):
        self.ensure_one()
        template = self.env.ref(template_xmlid)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_model': self._name,
                'default_res_ids': self.ids,
                'default_use_template': True,
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'default_email_to': self.email_from,
            },
        }

    def action_send_interview_invite(self):
        return self._open_mail_compose_with_template(
            'hocba_tuyen_dung.email_template_interview_invite'
        )

    def action_send_interview_result(self):
        return self._open_mail_compose_with_template(
            'hocba_tuyen_dung.email_template_interview_result'
        )

    def action_send_job_offer(self):
        return self._open_mail_compose_with_template(
            'hocba_tuyen_dung.email_template_job_offer'
        )

    def action_send_welcome(self):
        return self._open_mail_compose_with_template(
            'hocba_tuyen_dung.email_template_welcome'
        )
