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

    # ── Tạo mã phiếu tự động ─────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hb.recruitment.request')
                    or 'Mới'
                )
        return super().create(vals_list)

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

    # ── State transitions ─────────────────────────────────────────────────────
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Chỉ có thể gửi duyệt phiếu đang ở trạng thái Nháp.')
            rec.state = 'submitted'

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
            # Job từng tự Ngừng tuyển (đủ chỉ tiêu) nay có phiếu mới được duyệt
            # → mở lại trạng thái Đang tuyển; KHÔNG tự publish (HR chủ động đăng).
            if rec.job_id and rec.job_id.recruitment_status != 'recruiting':
                rec.job_id.recruitment_status = 'recruiting'

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

    def action_reset_draft(self):
        for rec in self:
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
