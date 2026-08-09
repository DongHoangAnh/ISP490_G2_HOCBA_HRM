import logging

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrApplicantHocBaExt(models.Model):
    _inherit = 'hr.applicant'

    # ── Đợt tuyển (phiếu yêu cầu) mà CV này thuộc về ─────────────────────────
    # Trước đây số liệu theo dõi phải bắc cầu qua JD (job_id) vì ứng viên không
    # biết mình thuộc phiếu nào ⇒ hai đợt tuyển cùng một vị trí thấy CÙNG bộ số.
    # Gắn thẳng vào phiếu để mỗi đợt có sổ riêng.
    hb_request_id = fields.Many2one(
        'hb.recruitment.request', string='Phiếu yêu cầu tuyển dụng',
        index=True, ondelete='set null', tracking=True,
        help='Đợt tuyển mà CV này thuộc về. Tự điền theo phiếu đang tuyển của '
             'vị trí lúc nhận CV; sửa tay được khi cần gán sang đợt khác.')

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
    # Cột "Kết quả nhận việc" của sheet 7.6. Bỏ trống = CHƯA XÁC ĐỊNH (đã gửi thư
    # mời, đang chờ tới ngày hẹn) — đó là trạng thái mặc định nên không cần giá
    # trị riêng. Thiếu ô này thì ứng viên bùng nằm lẫn với người đang chờ, và
    # không đo được tỷ lệ nhận offer rồi bùng.
    onboard_result = fields.Selection([
        ('arrived', 'Đã đến'),
        ('no_show', 'Không nhận việc'),
    ], string='Kết quả nhận việc', tracking=True)

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

    # ── Tự chuyển bước theo hành động của HR ─────────────────────────────────
    # Bám xmlid chứ KHÔNG bám tên bước: admin đổi tên bước trên màn Cấu hình là
    # chuyện bình thường, bám tên thì tự động hoá chết ngay lúc đó.

    def _hb_stage(self, ref):
        return self.env.ref('hocba_recruitments.' + ref, raise_if_not_found=False)

    def _hb_advance_stage(self, from_ref, to_ref, reason):
        """Chuyển các bản ghi ĐANG ở một trong các bước `from_ref` sang `to_ref`.

        `from_ref` nhận 1 mã hoặc list mã — vd Kết quả PV có thể được điền lúc
        ứng viên còn ở bước "Phỏng vấn" hoặc đã sang "Kết quả phỏng vấn".

        Chỉ đẩy tới, không kéo lùi: ứng viên đã đi xa hơn thì bỏ qua. Bước bị
        admin xoá/ẩn ⇒ không làm gì (im lặng, không chặn thao tác của HR).
        Ghi chatter để còn lần được ai/khi nào bị máy đổi bước.
        """
        refs = [from_ref] if isinstance(from_ref, str) else list(from_ref)
        src_ids = [s.id for s in (self._hb_stage(r) for r in refs) if s]
        dst = self._hb_stage(to_ref)
        if not src_ids or not dst or not dst.active:
            return
        todo = self.filtered(lambda a: a.stage_id.id in src_ids)
        if not todo:
            return
        for a in todo:
            src_name = a.stage_id.name
            a.write({'stage_id': dst.id})
            a.message_post(body=Markup(
                '<p>⚙ Tự chuyển bước <b>%s</b> → <b>%s</b><br/>%s</p>'
            ) % (src_name, dst.name, reason))

    # ── Nhắc CV quá hạn xử lý (CRON-REC-001) ─────────────────────────────────
    # Spec: docs/superpowers/specs/2026-08-03-recruitment-overdue-notification-design.md

    # Ai nhận nhắc quá hạn — cấu hình trên màn Cấu hình tuyển dụng, tab Thông báo.
    # both (mặc định) = HR + Trưởng phòng · hr_only · manager_only · off = tắt.
    OVERDUE_NOTIFY_MODES = ('both', 'hr_only', 'manager_only', 'off')

    @api.model
    def _hb_overdue_notify_mode(self):
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'hocba_recruitments.overdue_notify_mode', 'both')
        return mode if mode in self.OVERDUE_NOTIFY_MODES else 'both'

    def _hb_overdue_recipients(self):
        """HR nhóm tuyển dụng + Trưởng phòng của phòng ban vị trí này.

        Phạm vi cắt theo _hb_overdue_notify_mode(): phòng Giảng viên có 169 NV,
        ngày gán Trưởng phòng cho phòng đó thì người này nhận chuông cho MỌI CV
        giáo viên quá hạn — phải tắt được mà không cần sửa code.

        Ghi nhận lệch có chủ ý (giống hocba_service._notif_handlers): user chỉ
        có base.group_system mà không thuộc nhóm tuyển dụng thì KHÔNG nhận
        chuông — sysadmin không phải người xử lý nghiệp vụ.
        """
        self.ensure_one()
        mode = self._hb_overdue_notify_mode()
        Users = self.env['res.users'].sudo()
        users = Users.browse()
        if mode == 'off':
            return users
        if mode in ('both', 'hr_only'):
            # group_hr_recruitment_manager kế thừa group user ⇒ all_group_ids bắt cả hai.
            grp = self.env.ref('hr_recruitment.group_hr_recruitment_user',
                               raise_if_not_found=False)
            if grp:
                users |= Users.search([('all_group_ids', 'in', grp.id),
                                       ('active', '=', True)])
        if mode in ('both', 'manager_only'):
            mgr_user = self.sudo().department_id.manager_id.user_id
            if mgr_user:
                users |= mgr_user.sudo()
        return users

    @api.model
    def _cron_overdue_reminder(self):
        """Nhắc ứng viên đứng ở một bước lâu hơn hạn xử lý của bước đó.

        4 điều kiện loại trừ khớp 1-1 với quy tắc hiện badge trên card kanban
        (SPA CvList) — cố ý, để "có badge" ⇔ "có thông báo".

        interview_result != 'fail' KHÔNG loại mất ứng viên chưa PV: ORM quy về
        `not in ['fail']` và tự sinh `... OR interview_result IS NULL`
        (odoo/orm/fields.py). Test BR-4b khoá hành vi này.

        dedup_key='rec_overdue_<id>': _notify bỏ qua khi người nhận còn một
        dòng CHƯA ĐỌC cùng khoá ⇒ chạy 30 ngày liền vẫn 1 dòng, đọc rồi mà
        chưa xử lý thì hôm sau nhắc lại.
        """
        if self._hb_overdue_notify_mode() == 'off':
            _logger.info('CRON-REC-001: đang tắt (overdue_notify_mode=off).')
            return True
        candidates = self.sudo().search([
            ('active', '=', True),
            ('stage_id.sla_days', '>', 0),
            ('stage_id.hired_stage', '=', False),
            ('interview_result', '!=', 'fail'),
        ])
        Notification = self.env['hb.notification'].sudo()
        sent = 0
        overdue_count = 0
        for app in candidates:
            days, sla, overdue = app._hb_sla_state()
            if not overdue:
                continue
            overdue_count += 1
            sent += len(Notification._notify(
                app._hb_overdue_recipients(),
                category='recruitment', kind='recruitment_overdue',
                level='warning', title='CV quá hạn xử lý',
                body='%s · %s · bước "%s" · quá hạn %s ngày' % (
                    app.partner_name or app.display_name,
                    app.job_id.name or 'Chưa gán vị trí',
                    app.stage_id.name, days - sla),
                target_view='recruitment', target_tab='cv', target_ref=app.id,
                dedup_key='rec_overdue_%s' % app.id))
        _logger.info('CRON-REC-001: %d CV quá hạn, gửi %d thông báo.',
                     overdue_count, sent)
        return True

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

    # ── Gắn CV vào đợt tuyển ─────────────────────────────────────────────────

    def _hb_open_request(self):
        """Phiếu ĐANG TUYỂN mới nhất của vị trí này, không có thì trả rỗng.

        Cố ý KHÔNG lùi về phiếu đã đóng/nháp/từ chối: CV nộp lúc vị trí không mở
        đợt nào thì nó thật sự không thuộc đợt nào — gắn bừa vào phiếu cũ làm
        hỏng số liệu của đợt đã chốt.
        """
        self.ensure_one()
        if not self.job_id:
            return self.env['hb.recruitment.request']
        return self.env['hb.recruitment.request'].sudo().search(
            [('job_id', '=', self.job_id.id), ('state', '=', 'recruiting')],
            order='id desc', limit=1)

    def _hb_fill_request(self):
        """Điền phiếu cho các CV còn trống ô này. KHÔNG bao giờ ghi đè.

        HR gán tay là quyết định của người, máy không được đạp lên — kể cả khi
        sau đó đổi vị trí ứng tuyển.
        """
        for a in self.filtered(lambda x: not x.hb_request_id and x.job_id):
            req = a._hb_open_request()
            if req:
                a.hb_request_id = req.id

    @api.constrains('onboard_result', 'stage_id')
    def _check_onboard_result_vs_stage(self):
        """Đã bàn giao nhân sự thì không thể "không nhận việc".

        Vừa là mâu thuẫn dữ liệu, vừa phá bất biến của phễu theo dõi: ô "Nhận
        việc" loại người bùng ra, nên nếu để trạng thái này tồn tại thì
        "Đã tuyển" sẽ lớn hơn "Nhận việc" — người xem tưởng số liệu sai.
        """
        for a in self:
            if a.onboard_result == 'no_show' and a.stage_id.hired_stage:
                raise ValidationError(
                    'Ứng viên "%s" đã ở bước "%s" (đã bàn giao nhân sự) nên '
                    'không đánh "Không nhận việc" được. Nếu người này thực sự '
                    'không đi làm, hãy kéo hồ sơ về bước trước rồi đánh lại.'
                    % (a.partner_name or a.display_name, a.stage_id.name))

    def write(self, vals):
        res = super().write(vals)
        # Đổi vị trí ứng tuyển mà chưa có đợt ⇒ thử gắn theo vị trí mới.
        if 'job_id' in vals and 'hb_request_id' not in vals:
            self._hb_fill_request()
        if vals.get('stage_id'):
            stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
            if stage.hired_stage:
                self._hb_auto_close_if_filled()
        # ── Tự chuyển bước theo kết quả HR vừa nhập ──────────────────────────
        # Đều chỉ xét khi GÁN giá trị; xoá trắng không kéo ngược bước.
        if vals.get('cv_filter_result') == 'pass':
            self._hb_advance_stage(
                'hb_stage_screening', 'hb_stage_schedule',
                'Do kết quả lọc CV là Pass.')
        if vals.get('interview_date'):
            self._hb_advance_stage(
                'hb_stage_schedule', 'hb_stage_invite',
                'Do đã đặt Ngày hẹn phỏng vấn.')
        # Có kết quả PV (Pass / Fail / Tiềm năng) = phỏng vấn đã xong ⇒ về bước
        # "Kết quả phỏng vấn" để HR chốt bước kế. KHÔNG tự nhảy tiếp sang Gửi
        # Offer kể cả khi Pass: quyết định offer là của HR, không phải của máy.
        if vals.get('interview_result'):
            labels = dict(self._fields['interview_result'].selection)
            self._hb_advance_stage(
                'hb_stage_interview', 'hb_stage_result',
                'Do đã có Kết quả phỏng vấn: %s.'
                % labels.get(vals['interview_result'], vals['interview_result']))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._hb_fill_request()
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
