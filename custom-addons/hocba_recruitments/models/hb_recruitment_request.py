from odoo import api, fields, models
from odoo.exceptions import UserError


class HbRecruitmentRequest(models.Model):
    _name = 'hb.recruitment.request'
    _description = 'Phiếu Yêu Cầu Tuyển Dụng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ── Thông tin chung ───────────────────────────────────────────────────────
    name = fields.Char(
        string='Mã phiếu', readonly=True, default='Mới', copy=False, tracking=True,
    )
    date_request = fields.Date(
        string='Ngày order', default=fields.Date.context_today,
    )
    requester_id = fields.Many2one(
        'res.users', string='Người tạo',
        default=lambda self: self.env.user, readonly=True, tracking=True,
    )
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban', required=True, tracking=True,
    )

    # ── Vị trí cần tuyển ─────────────────────────────────────────────────────
    job_id = fields.Many2one(
        'hr.job', string='Vị trí (theo JD)',
        domain="[('department_id', '=', department_id)]",
    )
    job_title = fields.Char(string='Tên vị trí', required=True, tracking=True)
    jd_link = fields.Char(string='Link JD / Google Drive')
    qty_expected = fields.Integer(string='Số lượng cần tuyển', default=1, required=True)
    reason = fields.Selection([
        ('new', 'Tuyển mới'),
        ('replacement', 'Thay thế nhân viên'),
        ('expansion', 'Mở rộng quy mô'),
    ], string='Lý do tuyển', default='new', required=True, tracking=True)
    level = fields.Selection([
        ('intern', 'Thực tập sinh'),
        ('fresher', 'Fresher (dưới 1 năm)'),
        ('junior', 'Junior (1–3 năm)'),
        ('mid', 'Middle (3–5 năm)'),
        ('senior', 'Senior (5+ năm)'),
        ('lead', 'Lead / Trưởng nhóm'),
        ('manager', 'Manager / Trưởng phòng'),
    ], string='Cấp bậc', tracking=True)

    # ── Yêu cầu ứng viên ─────────────────────────────────────────────────────
    education = fields.Selection([
        ('none', 'Không yêu cầu cụ thể'),
        ('intermediate', 'Trung cấp'),
        ('college', 'Cao đẳng'),
        ('bachelor', 'Đại học'),
        ('master', 'Thạc sĩ'),
        ('doctor', 'Tiến sĩ'),
    ], string='Bằng cấp tối thiểu', default='none')
    experience_years = fields.Float(
        string='Kinh nghiệm tối thiểu (năm)', digits=(5, 1), default=0.0,
    )
    skill_description = fields.Text(string='Kỹ năng yêu cầu')
    language_requirement = fields.Char(string='Yêu cầu ngoại ngữ')

    # ── Điều kiện ─────────────────────────────────────────────────────────────
    expected_start_date = fields.Date(string='Ngày cần onboard', tracking=True)
    salary_range = fields.Char(string='Mức lương dự kiến', tracking=True)
    salary_from = fields.Float(string='Lương từ (VNĐ)', digits=(15, 0))
    salary_to = fields.Float(string='Lương đến (VNĐ)', digits=(15, 0))
    work_type = fields.Selection([
        ('onsite', 'Tại văn phòng'),
        ('remote', 'Remote / Từ xa'),
        ('hybrid', 'Hybrid'),
    ], string='Hình thức làm việc', default='onsite')

    # ── Phê duyệt ─────────────────────────────────────────────────────────────
    manager_id = fields.Many2one(
        'res.users', string='Trưởng phòng phê duyệt', tracking=True,
    )
    hr_manager_id = fields.Many2one(
        'res.users', string='HR Manager phê duyệt', tracking=True,
    )
    director_id = fields.Many2one(
        'res.users', string='Ban giám đốc phê duyệt', tracking=True,
    )
    refuse_reason = fields.Text(string='Lý do từ chối / trả về')

    # ── Ghi chú ───────────────────────────────────────────────────────────────
    note = fields.Html(string='Ghi chú nội bộ', sanitize=True)

    # Cờ chống cộng trùng chỉ tiêu vào vị trí (đã cộng khi duyệt → recruiting)
    headcount_synced = fields.Boolean(
        string='Đã cộng chỉ tiêu vào vị trí', default=False, copy=False,
    )

    # ── Trạng thái ────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Chờ BP duyệt'),
        ('recruiting', 'Đang tuyển'),
        ('closed', 'Đã đóng'),
        ('refused', 'Từ chối'),
    ], string='Trạng thái', default='draft', tracking=True, copy=False, index=True)

    # Phiếu "còn mở" = chưa chốt. Dùng cho luật trạng thái của vị trí: còn ít
    # nhất một phiếu ở đây thì Kho JD giữ "Đang tuyển", hết thì hạ về Dừng
    # tuyển. Cố ý gồm cả draft/submitted vì tạo phiếu (còn Nháp) đã mở lại
    # vị trí — xem _resume_job_recruiting / _stop_jobs_without_open_request.
    OPEN_STATES = ('draft', 'submitted', 'recruiting')

    # ── Tạo mã phiếu tự động ─────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hb.recruitment.request')
                    or 'Mới'
                )
        recs = super().create(vals_list)
        recs._resume_job_recruiting()
        return recs

    def _resume_job_recruiting(self):
        """Chọn JD đang Dừng tuyển vào phiếu ⇒ mở lại Đang tuyển ngay.

        Kho JD là kho DÙNG LẠI: đợt trước tuyển đủ thì vị trí về Dừng tuyển
        nhưng JD vẫn nằm đó cho đợt sau. Trước đây chỉ `action_approve()` mới
        mở lại trạng thái, nên từ lúc TBP tạo phiếu tới lúc HR duyệt thì Kho JD
        vẫn hiện "Dừng tuyển" trong khi đợt mới đã mở — người xem tưởng chọn
        nhầm JD chết. Chiều ngược: `_stop_jobs_without_open_request()`.

        KHÔNG tự đăng tin: đăng tuyển vẫn là quyết định của HR (cùng luật với
        `action_approve`, xem SPEC §3.3).
        """
        for rec in self:
            if not rec.job_id:
                continue
            if rec.job_id.sudo()._hb_resume_recruiting():
                rec.job_id.sudo().message_post(body=(
                    'Phiếu %s dùng lại vị trí này nên hệ thống chuyển trạng '
                    'thái tuyển về "Đang tuyển". Tin đăng giữ nguyên — bật đăng '
                    'tuyển ở tab Theo dõi tuyển dụng khi cần.' % (rec.name or '')))

    # ── Onchange: lọc & tự điền vị trí theo phòng ban ──────────────────────────
    @api.onchange('department_id')
    def _onchange_department_id(self):
        """Đổi phòng ban → bỏ chọn vị trí cũ nếu không thuộc phòng ban mới."""
        if self.job_id and self.job_id.department_id != self.department_id:
            self.job_id = False

    @api.onchange('job_id')
    def _onchange_job_id(self):
        """Chọn vị trí theo JD → tự điền tên vị trí + link JD nếu còn trống."""
        if self.job_id:
            self.job_title = self.job_id.name
            if not self.jd_link and self.job_id.jd_google_link:
                self.jd_link = self.job_id.jd_google_link

    # ── Thông báo chuông ──────────────────────────────────────────────────────
    # Vai theo sheet quy trình 7.1: TBP order → HR duyệt.
    #   gửi duyệt   → báo HR / BP tuyển dụng (người sẽ duyệt)
    #   duyệt / từ chối → báo ngược lại người tạo phiếu (TBP)

    def _hr_approver_users(self):
        """Người có quyền duyệt phiếu — phải khớp với _is_hr() bên controller.

        _is_hr() = base.group_system | hr.group_hr_manager | nhóm Tuyển dụng.
        Nếu chỉ báo cho nhóm Tuyển dụng thì HR Manager duyệt được mà không được
        báo — đúng ca đã gặp với tài khoản test_hrmanager@hocba.vn.

        Tìm theo all_group_ids nên bắt luôn group_hr_recruitment_manager kế thừa.
        Lệch có chủ ý (giống hocba_service): user CHỈ có base.group_system thì
        không nhận chuông — sysadmin không phải người xử lý nghiệp vụ.
        """
        Users = self.env['res.users'].sudo()
        gids = [g.id for g in (
            self.env.ref('hr_recruitment.group_hr_recruitment_user',
                         raise_if_not_found=False),
            self.env.ref('hr.group_hr_manager', raise_if_not_found=False),
        ) if g]
        if not gids:
            return Users.browse()
        return Users.search([('all_group_ids', 'in', gids),
                             ('active', '=', True)])

    def _req_notify(self, users, event, level, title, body):
        """Bắn chuông, tự loại người vừa bấm nút — không ai cần tự báo mình."""
        self.ensure_one()
        targets = users.filtered(lambda u: u.id != self.env.uid)
        if not targets:
            return self.env['hb.notification']
        return self.env['hb.notification'].sudo()._notify(
            targets, category='recruitment', kind='request_%s' % event,
            level=level, title=title, body=body,
            target_view='recruitment', target_tab='requests', target_ref=self.id,
            dedup_key='rec_request_%s_%s' % (self.id, event))

    def _label(self):
        self.ensure_one()
        return '%s · %s · %s người' % (
            self.name, self.job_title or 'Chưa rõ vị trí', self.qty_expected)

    # ── State transitions ─────────────────────────────────────────────────────
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Chỉ có thể gửi duyệt phiếu đang ở trạng thái Nháp.')
            rec.state = 'submitted'
            rec._req_notify(
                rec._hr_approver_users(), 'submitted', 'warning',
                'Phiếu yêu cầu tuyển dụng chờ duyệt',
                '%s · do %s gửi' % (rec._label(), rec.env.user.name))

    def action_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError('Phiếu chưa ở trạng thái chờ bộ phận duyệt.')
            rec.state = 'recruiting'
            # Cộng dồn số lượng cần tuyển vào chỉ tiêu của vị trí (1 lần / phiếu)
            if rec.job_id and not rec.headcount_synced:
                rec.job_id.no_of_recruitment = (
                    (rec.job_id.no_of_recruitment or 0) + rec.qty_expected
                )
                rec.headcount_synced = True
            # Job từng tự Ngừng tuyển (đủ chỉ tiêu) nay có phiếu được duyệt →
            # mở lại Đang tuyển; KHÔNG tự publish (HR chủ động đăng). Thường đã
            # mở sẵn từ lúc tạo phiếu (_resume_job_recruiting), giữ ở đây cho
            # phiếu cũ / phiếu tạo trước khi có luật đó.
            if rec.job_id:
                rec.job_id.sudo()._hb_resume_recruiting()
            rec._req_notify(
                rec.requester_id, 'approved', 'success',
                'Phiếu yêu cầu tuyển dụng đã được duyệt',
                '%s · duyệt bởi %s' % (rec._label(), rec.env.user.name))

    def _hired_count(self):
        """Số ứng viên của phiếu này đã vào bước Bàn giao nhân sự.

        active_test=False vì hồ sơ ứng viên hay bị lưu trữ sau khi nhận việc —
        bỏ đi thì "đã tuyển" tụt số và phiếu trả lại chỉ tiêu nhiều hơn thực tế.
        """
        self.ensure_one()
        return self.env['hr.applicant'].sudo().with_context(
            active_test=False).search_count([
                ('hb_request_id', '=', self.id),
                ('stage_id.hired_stage', '=', True)])

    def _release_headcount(self):
        """Đóng phiếu ⇒ trả lại phần CHƯA tuyển vào chỉ tiêu của vị trí.

        `no_of_recruitment` của core là "còn cần tuyển bao nhiêu": duyệt phiếu
        cộng `qty_expected`, mỗi ứng viên vào bước hired thì core tự trừ 1. Đóng
        phiếu mà không trả phần còn thiếu thì chỉ tiêu ma nằm lại vĩnh viễn —
        vừa sai số, vừa làm `_hb_auto_close_if_filled` (chặn ở `> 0`) không bao
        giờ kích hoạt lại cho vị trí đó.

        Chỉ trừ đúng phần của phiếu này, kẹp ở 0: vị trí có thể đang gánh chỉ
        tiêu của phiếu khác, và có thể đã tuyển vượt số phiếu ghi.
        """
        self.ensure_one()
        if not self.job_id or not self.headcount_synced:
            return 0
        remaining = max(0, (self.qty_expected or 0) - self._hired_count())
        if remaining:
            self.job_id.sudo().no_of_recruitment = max(
                0, (self.job_id.no_of_recruitment or 0) - remaining)
        self.headcount_synced = False
        return remaining

    def write(self, vals):
        # Bắt ở write() chứ không chỉ trong action_close(): phiếu còn bị đóng
        # TỰ ĐỘNG khi vị trí tuyển đủ chỉ tiêu (hr_applicant._hb_auto_close_if_
        # filled ghi thẳng state), và HR có thể đóng từ form backend.
        closing = (self.filtered(lambda r: r.state != 'closed')
                   if vals.get('state') == 'closed' else self.browse())
        res = super().write(vals)
        # Gắn phiếu sang vị trí khác cũng là "dùng lại JD" — xử như lúc tạo.
        if vals.get('job_id'):
            self._resume_job_recruiting()
        for rec in closing:
            released = rec._release_headcount()
            if released:
                rec.message_post(body=(
                    'Đóng phiếu khi còn %s chỉ tiêu chưa tuyển — đã trả lại '
                    'chỉ tiêu cho vị trí "%s".' % (released, rec.job_id.name)))
            rec._stop_jobs_without_open_request(
                rec.job_id, vi='phiếu %s đã đóng' % (rec.name or ''))
        return res

    def _stop_jobs_without_open_request(self, jobs, bo_qua_ids=(), vi=''):
        """Vị trí hết đợt tuyển đang mở ⇒ về Dừng tuyển + gỡ tin đăng.

        "Đang tuyển" trên Kho JD phải có nghĩa là CÒN ĐỢT TUYỂN ĐANG MỞ. Trước
        đây chỉ hạ trạng thái khi chỉ tiêu TỔNG của vị trí về 0, nên vị trí mang
        chỉ tiêu dư (JD cũ nhập tay, hoặc default 1 của core) thì phiếu chốt rồi
        mà tin vẫn treo "Đang tuyển" và vẫn nằm trên trang tuyển dụng.

        "Đợt còn mở" = phiếu ở `OPEN_STATES` (nháp / chờ duyệt / đang tuyển) —
        KHÔNG chỉ mỗi `recruiting`. Phải khớp với `_resume_job_recruiting()`:
        phiếu vừa tạo còn Nháp đã mở lại vị trí, nên nếu ở đây chỉ đếm phiếu
        `recruiting` thì chốt đợt cũ sẽ dập tắt luôn đợt mới đang chờ duyệt.

        Gọi ở cả 3 cửa chốt phiếu: đóng (tự động lẫn tay), từ chối, xoá phiếu.
        `bo_qua_ids` cho ca phiếu đã bị xoá.
        """
        Req = self.sudo()
        for job in jobs:
            if not job:
                continue
            domain = [('job_id', '=', job.id), ('state', 'in', self.OPEN_STATES)]
            if bo_qua_ids:
                domain.append(('id', 'not in', list(bo_qua_ids)))
            if Req.search_count(domain):
                continue
            if job.sudo()._hb_stop_recruiting():
                job.sudo().message_post(body=(
                    'Vị trí không còn phiếu yêu cầu tuyển dụng nào đang mở%s — '
                    'hệ thống tự chuyển sang Dừng tuyển và ngừng đăng tin.'
                    % (' (%s)' % vi if vi else '')))

    def unlink(self):
        """Xoá phiếu cũng là một cửa chốt đợt — vị trí phải theo kịp."""
        jobs = self.mapped('job_id')
        ids = self.ids
        res = super().unlink()
        self._stop_jobs_without_open_request(jobs, bo_qua_ids=ids,
                                             vi='phiếu vừa bị xoá')
        return res

    def action_close(self):
        for rec in self:
            if rec.state != 'recruiting':
                raise UserError('Chỉ đóng phiếu khi đang tuyển.')
            rec.state = 'closed'

    def action_refuse(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError('Chỉ từ chối phiếu đang chờ bộ phận duyệt.')
            rec.state = 'refused'
            rec._req_notify(
                rec.requester_id, 'refused', 'danger',
                'Phiếu yêu cầu tuyển dụng bị từ chối',
                '%s · từ chối bởi %s%s' % (
                    rec._label(), rec.env.user.name,
                    ' · Lý do: %s' % rec.refuse_reason if rec.refuse_reason else ''))
            # Phiếu bị từ chối cũng là hết đợt: lúc tạo, phiếu đã mở vị trí sang
            # Đang tuyển (_resume_job_recruiting); từ chối mà không hạ lại thì
            # vị trí treo "Đang tuyển" trong khi chẳng còn đợt nào.
            rec._stop_jobs_without_open_request(
                rec.job_id, vi='phiếu %s bị từ chối' % (rec.name or ''))

    def action_reset_draft(self):
        """Mở lại nháp — CHỈ từ trạng thái Từ chối (quyết định 2026-08-26).

        Phiếu đang tuyển đã cộng chỉ tiêu vào vị trí; cho kéo thẳng về Nháp thì
        chỉ tiêu treo lại mà phiếu trông như chưa duyệt, sửa `qty_expected` rồi
        duyệt lại cũng không cộng thêm (đã có `headcount_synced`). Muốn sửa
        phiếu đang tuyển thì Đóng trước — lúc đó chỉ tiêu được trả lại đàng
        hoàng. Phiếu đã đóng là chốt đợt, mở lại thì tạo phiếu mới.
        """
        for rec in self:
            if rec.state != 'refused':
                raise UserError(
                    'Chỉ mở lại nháp được với phiếu đang ở trạng thái Từ chối. '
                    'Phiếu "%s" đang ở "%s" — nếu cần dừng đợt tuyển này thì '
                    'dùng nút Đóng phiếu.'
                    % (rec.name, dict(rec._fields['state'].selection).get(
                        rec.state, rec.state)))
            rec.state = 'draft'

    def action_create_job_position(self):
        self.ensure_one()
        if self.job_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.job',
                'res_id': self.job_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        job = self.env['hr.job'].create({
            'name': self.job_title,
            'department_id': self.department_id.id,
        })
        self.job_id = job
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.job',
            'res_id': job.id,
            'view_mode': 'form',
            'target': 'current',
        }
