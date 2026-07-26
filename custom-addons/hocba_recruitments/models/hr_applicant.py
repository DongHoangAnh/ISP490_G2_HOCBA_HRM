from markupsafe import Markup

from odoo import api, fields, models


class HrApplicantHocBaExt(models.Model):
    _inherit = 'hr.applicant'

    # ── Sheet 7.4 — Danh sách CV ─────────────────────────────────────────────
    date_received = fields.Date(string='Thời gian nhận CV', index=True,
                                default=fields.Date.context_today)
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

    # ── SLA theo bước (cấu hình sla_days trên hr.recruitment.stage) ──────────

    def _hb_sla_state(self):
        """(số ngày ở bước hiện tại, sla_days của bước, có trễ SLA không).
        Mốc vào bước = date_last_stage_update (core cập nhật mỗi lần đổi stage),
        fallback create_date. Bước hired / sla_days=0 → không tính trễ."""
        self.ensure_one()
        anchor = self.date_last_stage_update or self.create_date
        days = (fields.Datetime.now() - anchor).days if anchor else 0
        sla = self.stage_id.sla_days or 0
        overdue = bool(sla and not self.stage_id.hired_stage and days > sla)
        return days, sla, overdue

    # ── Tự động ngừng đăng khi tuyển đủ chỉ tiêu ─────────────────────────────
    # Ứng viên vào stage "Đã tuyển" (hired_stage) qua bất kỳ đường nào (kéo
    # kanban SPA, backend Odoo, import) đều đi qua write/create → kiểm chỉ tiêu.
    # Hành vi cấu hình được qua ir.config_parameter hocba_recruitments.auto_close_mode:
    #   full (mặc định) = ngừng đăng + đóng phiếu · stop = chỉ ngừng đăng ·
    #   warn = chỉ cảnh báo trên chatter · off = không làm gì.

    AUTO_CLOSE_MODES = ('full', 'stop', 'warn', 'off')

    @api.model
    def _hb_auto_close_mode(self):
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'hocba_recruitments.auto_close_mode', 'full')
        return mode if mode in self.AUTO_CLOSE_MODES else 'full'

    def write(self, vals):
        res = super().write(vals)
        if vals.get('stage_id'):
            stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
            if stage.hired_stage:
                self._hb_auto_close_if_filled()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        hired = recs.filtered(lambda a: a.stage_id.hired_stage)
        if hired:
            hired._hb_auto_close_if_filled()
        return recs

    def _hb_auto_close_if_filled(self):
        """Job đã tuyển đủ → tự Ngừng đăng + đóng phiếu đang tuyển.

        Core Odoo 19 coi no_of_recruitment là số CÒN THIẾU: tự trừ 1 khi
        applicant vào stage hired, cộng lại khi kéo ra (hr_recruitment,
        hr_applicant.write). Vì hook này chạy SAU super().write() nên
        no_of_recruitment đã được core trừ → đủ chỉ tiêu ⇔ còn thiếu <= 0."""
        mode = self._hb_auto_close_mode()
        if mode == 'off':
            return
        Applicant = self.env['hr.applicant'].sudo().with_context(active_test=False)
        Request = self.env['hb.recruitment.request'].sudo()
        for job in self.sudo().mapped('job_id'):
            if not job or job.no_of_recruitment > 0:
                continue
            if job.recruitment_status == 'stopped':
                continue
            hired = Applicant.search_count([
                ('job_id', '=', job.id),
                ('stage_id.hired_stage', '=', True),
            ])
            if mode == 'warn':
                job.sudo().message_post(body=Markup(
                    '<p>Đã tuyển đủ chỉ tiêu (<b>%s</b> ứng viên nhận việc). '
                    'Tin vẫn đang đăng — cân nhắc Ngừng đăng tuyển (chế độ tự '
                    'đóng đang đặt "Chỉ cảnh báo").</p>') % hired)
                continue
            vals = {'recruitment_status': 'stopped', 'x_published': False}
            # website_hr_recruitment có thể không cài (vd DB test local)
            if 'is_published' in job._fields:
                vals['is_published'] = False
            job.sudo().write(vals)
            reqs = Request.browse()
            if mode == 'full':
                reqs = Request.search([
                    ('job_id', '=', job.id), ('state', '=', 'recruiting')])
                if reqs:
                    reqs.write({'state': 'closed'})
            job.sudo().message_post(body=Markup(
                '<p>Đã tuyển đủ chỉ tiêu (<b>%s</b> ứng viên nhận việc) — hệ thống '
                'tự <b>Ngừng đăng tuyển</b>%s.</p>') % (
                    hired,
                    (' và đóng %s phiếu yêu cầu' % len(reqs)) if reqs else ''))

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
                'active_id': self.id,
                'active_ids': self.ids,
                'active_model': self._name,
            },
        }

    def action_send_interview_invite(self):
        return self._open_mail_compose_with_template(
            'hocba_recruitments.email_template_interview_invite'
        )

    def action_send_interview_result(self):
        return self._open_mail_compose_with_template(
            'hocba_recruitments.email_template_interview_result'
        )

    def action_send_job_offer(self):
        return self._open_mail_compose_with_template(
            'hocba_recruitments.email_template_job_offer'
        )

    def action_send_welcome(self):
        return self._open_mail_compose_with_template(
            'hocba_recruitments.email_template_welcome'
        )
