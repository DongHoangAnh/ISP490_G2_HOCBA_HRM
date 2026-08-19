import json
import logging
import re
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

# Kết quả cổng đánh giá — khách họp #2 yêu cầu thêm "Gia hạn"
GATE_RESULT_SEL = [
    ('draft', 'Chưa đánh giá'),
    ('pass', 'Đạt'),
    ('fail', 'Không đạt'),
    ('extend', 'Gia hạn'),
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # --- F-001: Định danh & 4 trục phân loại Học Bá (đặc tả v2.1) ---
    x_employee_code = fields.Char(
        string='Mã nhân sự',
        copy=False,
        index=True,
        help='Mã định danh nội bộ, định dạng HB.xx — tự sinh, HR có thể sửa trước khi lưu lần đầu.',
    )
    # Trục 1 — Hình thức làm việc
    x_work_form = fields.Selection(
        selection=[
            ('offline', 'Offline'),
            ('online', 'Online'),
        ],
        string='Hình thức làm việc',
    )
    # Trục 2 — Tình trạng / Loại hợp đồng
    x_employment_status = fields.Selection(
        selection=[
            ('probation', 'Thử việc'),
            ('official', 'Chính thức'),
            ('intern', 'TTS'),
            ('parttime', 'Part-time'),
            ('ctv', 'CTV'),
            ('advisor', 'Cố vấn'),
            ('exiting', 'Đang offboarding'),
            ('resigned', 'Nghỉ việc'),
        ],
        string='Tình trạng',
        default='probation',
        tracking=True,
    )
    # Trục 3 — Loại vị trí
    x_position_type = fields.Selection(
        selection=[
            ('manager', 'Quản lý'),
            ('staff', 'Nhân viên'),
            ('ctv', 'CTV'),
            ('freelancer', 'Freelancer'),
            ('advisor', 'Cố vấn'),
        ],
        string='Loại vị trí',
    )
    # Loại nhân viên (danh mục hocba.employee.type — single source tại đây)
    x_employee_type_id = fields.Many2one(
        'hocba.employee.type', string='Loại nhân viên',
        help='Nhân viên văn phòng / Giáo viên / Cộng tác viên — '
             'hocba.user đọc related từ field này.')
    # Phân cấp năng lực (khách họp #2): áp dụng cho cả nhân viên lẫn giáo viên.
    # Với giáo viên dùng để lọc xếp lớp (sơ/trung/cao cấp).
    x_seniority_level = fields.Selection(
        selection=[
            ('junior', 'Sơ cấp / Junior'),
            ('middle', 'Trung cấp / Middle'),
            ('senior', 'Cao cấp / Senior'),
        ],
        string='Phân cấp', tracking=True,
        help='Phân loại trình độ — giáo viên dùng để lọc khi xếp lớp.')
    # Mốc lên chính thức (automation thử việc sẽ set ở Pha 3 — F-004/F-005)
    x_official_date = fields.Date(
        string='Ngày chính thức',
        tracking=True,
    )
    x_official_months = fields.Float(
        string='Số tháng chính thức',
        compute='_compute_official_months',
        help='(Hôm nay - Ngày chính thức) / 30 ngày.',
    )

    # --- F-002: Hồ sơ pháp lý Việt Nam ---
    x_id_date_issue = fields.Date(string='Ngày cấp CCCD')
    x_id_place_issue = fields.Char(string='Nơi cấp CCCD')
    x_pit_code = fields.Char(
        string='MST TNCN', groups='hr.group_hr_manager',
        help='Mã số thuế thu nhập cá nhân (10 hoặc 13 chữ số).')
    x_social_insurance_no = fields.Char(
        string='Số sổ BHXH', groups='hr.group_hr_manager',
        help='Số sổ Bảo hiểm xã hội (10 chữ số).')
    x_bank_account_no = fields.Char(
        string='Số tài khoản nhận lương', groups='hr.group_hr_manager',
        help='Số tài khoản nhân viên nhận lương.')
    x_bank_code = fields.Char(
        string='Ngân hàng nhận lương', groups='hr.group_hr_manager',
        help='Mã ngân hàng chuẩn hoá (vd VCB), đồng bộ với danh sách cấu hình payroll (hb.bank.format).')
    x_health_insurance_no = fields.Char(string='Số thẻ BHYT')
    x_health_care_place = fields.Char(string='Nơi KCB ban đầu')

    # --- Liên kết CMS (lịch dạy giáo viên) ---
    x_cms_user_id = fields.Char(
        string='CMS User ID',
        copy=False,
        index=True,
        help='ID người dùng trong hệ thống CMS (erp_database.user.id). '
             'Dùng để lấy lịch dạy của giáo viên từ CMS MySQL.',
    )

    # --- Face enrollment (for hocba_attendance face check-in) ---
    x_face_image = fields.Binary(string='Ảnh khuôn mặt mẫu', attachment=True)
    x_face_descriptor = fields.Text(
        string='Face descriptor (JSON)',
        help='128-d face descriptor as JSON list, computed by face-api.js.',
        copy=False,
    )
    x_face_enrolled = fields.Boolean(
        string='Đã đăng ký khuôn mặt',
        compute='_compute_x_face_enrolled',
        store=True,
    )
    # Địa chỉ thường trú
    x_permanent_state_id = fields.Many2one(
        'res.country.state', string='Tỉnh/Thành (thường trú)',
        domain="[('country_id.code', '=', 'VN')]")
    x_permanent_ward = fields.Char(string='Phường/Xã (thường trú)')
    x_permanent_street = fields.Char(string='Số nhà/Đường (thường trú)')
    # Địa chỉ tạm trú
    x_current_same_as_permanent = fields.Boolean(
        string='Tạm trú giống thường trú', default=True)
    x_current_state_id = fields.Many2one(
        'res.country.state', string='Tỉnh/Thành (tạm trú)',
        domain="[('country_id.code', '=', 'VN')]")
    x_current_ward = fields.Char(string='Phường/Xã (tạm trú)')
    x_current_street = fields.Char(string='Số nhà/Đường (tạm trú)')

    # --- F-004: Dòng thời gian thử việc & 2 cổng đánh giá (Nhóm B) ---
    x_probation_start = fields.Date(string='Ngày bắt đầu thử việc', tracking=True)
    # Quy trình nhận việc bước động (thay dần các field cổng cứng bên dưới —
    # spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md)
    x_onboarding_template_id = fields.Many2one(
        'hb.onboarding.template', string='Quy trình nhận việc', tracking=True)
    x_onboarding_step_ids = fields.One2many(
        'hb.onboarding.step', 'employee_id', string='Các bước nhận việc')
    x_eval_2w_due = fields.Date(
        string='Hạn đánh giá tuần-2',
        compute='_compute_eval_dues', store=True, readonly=False,
        help='Mặc định = ngày thử việc + 14; được sửa trong khoảng [+7, +21] ngày.')
    x_eval_2w_result = fields.Selection(
        selection=GATE_RESULT_SEL,
        string='Kết quả tuần-2', default='draft', tracking=True)
    x_eval_2w_date = fields.Date(string='Ngày đánh giá tuần-2')
    x_eval_2w_evaluator_id = fields.Many2one('res.users', string='Người đánh giá tuần-2')
    x_eval_2w_note = fields.Text(string='Ghi chú tuần-2')
    x_equip_grant_date = fields.Date(
        string='Ngày cấp thiết bị', readonly=True,
        help='Tự set khi cổng tuần-2 Đạt (AUT-001).')
    # --- Cổng tháng-1 (khách họp #2: có bạn hết thử việc sau 1 tháng) ---
    x_eval_1m_due = fields.Date(
        string='Hạn đánh giá tháng-1',
        compute='_compute_eval_dues', store=True, readonly=False,
        help='Mặc định = ngày thử việc + 30; được sửa trong khoảng [+21, +45] ngày.')
    x_eval_1m_result = fields.Selection(
        selection=GATE_RESULT_SEL,
        string='Kết quả tháng-1', default='draft', tracking=True,
        help='Đạt → lên chính thức sớm; Gia hạn → tiếp tục tới cổng tháng-2; '
             'Không đạt → kết thúc thử việc.')
    x_eval_1m_date = fields.Date(string='Ngày đánh giá tháng-1')
    x_eval_1m_evaluator_id = fields.Many2one('res.users', string='Người đánh giá tháng-1')
    x_eval_1m_note = fields.Text(string='Ghi chú tháng-1')
    x_eval_2m_due = fields.Date(
        string='Hạn đánh giá tháng-2',
        compute='_compute_eval_dues', store=True, readonly=False,
        help='Mặc định = ngày thử việc + 60 (GĐ-04, đã xác nhận từ dữ liệu Lark); '
             'được sửa trong khoảng [+30, +120] ngày.')
    x_eval_2m_result = fields.Selection(
        selection=GATE_RESULT_SEL,
        string='Kết quả tháng-2', default='draft', tracking=True)
    x_eval_2m_date = fields.Date(string='Ngày đánh giá tháng-2')
    x_eval_2m_evaluator_id = fields.Many2one('res.users', string='Người đánh giá tháng-2')
    x_eval_2m_note = fields.Text(string='Ghi chú tháng-2')
    x_skip_auto_trigger = fields.Boolean(
        string='Bỏ qua tự động hóa cổng', groups='hr.group_hr_manager',
        help='Bật để nhập liệu lịch sử mà không kích hoạt AUT-001/002.')

    # --- F-003: Người phụ thuộc (giảm trừ gia cảnh) ---
    x_dependent_ids = fields.One2many(
        'hr.employee.dependent', 'employee_id', string='Người phụ thuộc')
    x_active_dependent_count = fields.Integer(
        string='Số NPT đang hiệu lực',
        compute='_compute_active_dependent_count',
        help='Số người phụ thuộc đang trong thời gian được tính giảm trừ.')

    # --- F-008: Đánh giá thử giảng (Nhóm A — giảng viên) ---
    x_trial_lesson_date = fields.Date(string='Ngày thử giảng')
    x_trial_lesson_class = fields.Char(string='Lớp thử giảng')
    x_trial_score_method = fields.Float(
        string='Điểm phương pháp', digits=(3, 1),
        help='Thang điểm 1–10.')
    x_trial_score_content = fields.Float(
        string='Điểm chuyên môn', digits=(3, 1),
        help='Thang điểm 1–10.')
    x_trial_lesson_note = fields.Text(string='Nhận xét thử giảng')
    x_trial_lesson_result = fields.Selection(
        selection=[('draft', 'Chưa đánh giá'), ('pass', 'Đạt'), ('fail', 'Không đạt')],
        string='Kết quả thử giảng', default='draft', tracking=True)

    # --- F-006 / F-007: tài sản & thăng tiến ---
    x_asset_ids = fields.One2many(
        'hr.employee.asset', 'employee_id', string='Tài sản')
    x_asset_count = fields.Integer(
        string='Tài sản đang giữ', compute='_compute_asset_count')
    x_promotion_ids = fields.One2many(
        'hr.promotion.history', 'employee_id', string='Lịch sử thăng tiến')
    x_promotion_count = fields.Integer(
        string='Số lần thăng tiến', compute='_compute_promotion_count')
    x_evaluation_ids = fields.One2many(
        'hr.promotion.evaluation', 'employee_id', string='Đợt đánh giá thăng tiến')

    # --- F-001: Hồ sơ tổng quan — mini-timeline & cảnh báo chứng chỉ ---
    x_probation_timeline_html = fields.Html(
        string='Dòng thời gian thử việc',
        compute='_compute_probation_timeline_html', sanitize=False)
    x_cert_alert_count = fields.Integer(
        string='Chứng chỉ sắp hết hạn', compute='_compute_cert_alert_count')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _x_employee_code_uniq = models.Constraint(
        'unique (x_employee_code)',
        'Mã nhân sự phải là duy nhất!',
    )

    @api.depends('x_asset_ids')
    def _compute_asset_count(self):
        # F-006 rút gọn: mọi dòng tài sản đều là "đang giữ".
        for emp in self:
            emp.x_asset_count = len(emp.x_asset_ids)

    @api.depends('x_promotion_ids')
    def _compute_promotion_count(self):
        for emp in self:
            emp.x_promotion_count = len(emp.x_promotion_ids)

    def _promo_auto_metrics(self):
        """Chỉ số tự động cho dashboard đánh giá thăng tiến (read-only).
        Chấm công lấy best-effort: thiếu model/khoá → trả None, không vỡ."""
        self.ensure_one()
        today = fields.Date.context_today(self)

        def _months(d):
            if not d:
                return 0.0
            return round((today - d).days / 30.44, 1)

        last_promo = self.env['hr.promotion.history'].search(
            [('employee_id', '=', self.id)], order='date_effective desc', limit=1)
        metrics = {
            'tenureMonths': (_months(self.x_probation_start) if self.x_probation_start
                             else _months(self.create_date and self.create_date.date())),
            'officialMonths': round(self.x_official_months or 0, 1),
            'monthsSincePromo': _months(last_promo.date_effective)
            if last_promo else None,
            'currentJob': self.job_id.name or '',
            'attendance': self._promo_attendance_summary(),
        }
        return metrics

    def _promo_attendance_summary(self):
        """Tổng hợp chấm công ~3 tháng. Best-effort: module owner khác."""
        self.ensure_one()
        if 'hr.attendance' not in self.env:
            return None
        try:
            since = fields.Datetime.now() - timedelta(days=90)
            recs = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', self.id),
                ('check_in', '>=', since),
            ])
            return {'days': len(recs)}
        except Exception:
            _logger.exception(
                'Tổng hợp chấm công thất bại cho NV %s', self.id)
            return None

    def action_view_hocba_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tài sản: %s') % self.name,
            'res_model': 'hr.employee.asset',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_view_hocba_promotions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Thăng tiến: %s') % self.name,
            'res_model': 'hr.promotion.history',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_view_hocba_certs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Chứng chỉ: %s') % self.name,
            'res_model': 'hr.employee.skill',
            'view_mode': 'list',
            'view_id': self.env.ref(
                'hocba_employees.hr_employee_skill_cert_list').id,
            'domain': [('employee_id', '=', self.id),
                       ('x_cert_expiry', '!=', False)],
        }

    @api.depends('employee_skill_ids.x_cert_expiry',
                 'employee_skill_ids.x_cert_verified')
    def _compute_cert_alert_count(self):
        days = int(self.env['ir.config_parameter'].sudo().get_param(
            'hoc_ba.cert_alert_days', '60'))
        limit = fields.Date.context_today(self) + timedelta(days=days)
        for emp in self:
            emp.x_cert_alert_count = len(emp.employee_skill_ids.filtered(
                lambda s: s.x_cert_verified and s.x_cert_expiry
                and s.x_cert_expiry <= limit))

    TIMELINE_COLORS = {'done': '#28a745', 'fail': '#C8102E',
                       'extend': '#E8A33D', 'pending': '#ced4da'}

    @api.depends('x_probation_start', 'x_official_date',
                 'x_onboarding_step_ids.state', 'x_onboarding_step_ids.result',
                 'x_onboarding_step_ids.done_date', 'x_onboarding_step_ids.due_date')
    def _compute_probation_timeline_html(self):
        # F-001: mini-timeline (server-rendered, không JS) — render từ các
        # bước động hb.onboarding.step; bước skipped ẩn khỏi timeline.
        def fmt(d):
            return d.strftime('%d/%m/%Y') if d else ''

        for emp in self:
            marks = {'pass': 'done', 'fail': 'fail', 'extend': 'extend'}
            steps = [(_('Thử việc'),
                      'done' if emp.x_probation_start else 'pending',
                      fmt(emp.x_probation_start))]
            for s in emp.x_onboarding_step_ids.sorted(
                    lambda x: (x.sequence, x.id)):
                if s.state == 'skipped':
                    continue
                if s.state == 'done':
                    st = marks.get(s.result, 'done')
                elif s.extend_count:
                    st = 'extend'    # đang open nhưng đã gia hạn tại chỗ
                else:
                    st = 'pending'
                sub = fmt(s.done_date) or (
                    s.due_date and _('hạn %s') % fmt(s.due_date) or '')
                steps.append((s.name, st, sub))
            steps.append((_('Chính thức'),
                          'done' if emp.x_official_date else 'pending',
                          fmt(emp.x_official_date)))
            parts = []
            for i, (label, state, sub) in enumerate(steps):
                if i:
                    parts.append(
                        '<div style="flex:1 1 24px;border-top:2px solid #dee2e6;'
                        'margin-top:11px;min-width:12px;"></div>')
                mark = {'done': '✓', 'fail': '✗', 'extend': '↻'}.get(state, str(i + 1))
                color = self.TIMELINE_COLORS[state]
                txt = '#fff' if state != 'pending' else '#495057'
                parts.append(
                    '<div style="text-align:center;min-width:78px;">'
                    '<div style="width:24px;height:24px;border-radius:50%%;'
                    'background:%(color)s;color:%(txt)s;line-height:24px;'
                    'margin:0 auto;font-size:12px;font-weight:bold;">%(mark)s</div>'
                    '<div style="font-size:11px;font-weight:600;margin-top:4px;">'
                    '%(label)s</div>'
                    '<div style="font-size:10px;color:#6c757d;">%(sub)s</div>'
                    '</div>' % {
                        'color': color, 'txt': txt, 'mark': mark,
                        'label': label, 'sub': sub})
            emp.x_probation_timeline_html = (
                '<div style="display:flex;align-items:flex-start;'
                'padding:4px 0;">%s</div>' % ''.join(parts))

    @api.depends('x_face_descriptor')
    def _compute_x_face_enrolled(self):
        for emp in self:
            emp.x_face_enrolled = bool(emp.x_face_descriptor)

    @api.depends('x_official_date')
    def _compute_official_months(self):
        today = fields.Date.context_today(self)
        for emp in self:
            if emp.x_official_date:
                emp.x_official_months = (today - emp.x_official_date).days / 30.0
            else:
                emp.x_official_months = 0.0

    @api.depends('x_dependent_ids.date_start', 'x_dependent_ids.date_end')
    def _compute_active_dependent_count(self):
        today = fields.Date.context_today(self)
        for emp in self:
            emp.x_active_dependent_count = len(emp.x_dependent_ids.filtered(
                lambda d: d.date_start and d.date_start <= today
                and (not d.date_end or d.date_end >= today)
            ))

    @api.onchange('x_current_same_as_permanent', 'x_permanent_state_id',
                  'x_permanent_ward', 'x_permanent_street')
    def _onchange_current_same_as_permanent(self):
        # BR-012: khi "giống thường trú" → tạm trú mirror & lock
        for emp in self:
            if emp.x_current_same_as_permanent:
                emp.x_current_state_id = emp.x_permanent_state_id
                emp.x_current_ward = emp.x_permanent_ward
                emp.x_current_street = emp.x_permanent_street

    @api.constrains('x_pit_code')
    def _check_pit_code(self):
        for emp in self.sudo():
            if emp.x_pit_code and not re.fullmatch(r'\d{10}(\d{3})?', emp.x_pit_code):
                raise ValidationError(_('MST TNCN phải gồm 10 hoặc 13 chữ số.'))

    @api.constrains('x_social_insurance_no')
    def _check_social_insurance_no(self):
        for emp in self.sudo():
            if emp.x_social_insurance_no and not re.fullmatch(r'\d{10}', emp.x_social_insurance_no):
                raise ValidationError(_('Số sổ BHXH phải gồm đúng 10 chữ số.'))

    @api.constrains('x_id_date_issue', 'birthday')
    def _check_id_date_issue(self):
        today = fields.Date.context_today(self)
        for emp in self:
            if emp.x_id_date_issue:
                if emp.x_id_date_issue > today:
                    raise ValidationError(_('Ngày cấp CCCD không được sau hôm nay.'))
                if emp.birthday and emp.x_id_date_issue < emp.birthday + relativedelta(years=14):
                    raise ValidationError(_('Ngày cấp CCCD phải sau sinh nhật 14 tuổi.'))

    def _hocba_missing_official_fields(self):
        """Các mục BR-010 còn thiếu để lên chính thức — [] là đã đủ.

        Tách khỏi constrains để chỗ khác dùng lại được mà không phải chép luật:
        hiện dùng ở thông báo "cần hoàn thiện hồ sơ" lúc Onboard tạo hồ sơ từ
        ứng viên (tuyển dụng không nắm CCCD/MST/BHXH nên hồ sơ mới luôn thiếu).
        """
        self.ensure_one()
        emp = self.sudo()
        missing = []
        if not emp.identification_id:
            missing.append('CCCD')
        if not emp.x_pit_code:
            missing.append('MST TNCN')
        if not emp.x_social_insurance_no:
            missing.append('Số sổ BHXH')
        return missing

    @api.constrains('x_employment_status', 'x_pit_code', 'x_social_insurance_no')
    def _check_official_required_fields(self):
        # BR-010 (mở rộng họp #2): chính thức bắt buộc CCCD + MST + BHXH
        for emp in self.sudo():
            if emp.x_employment_status == 'official':
                missing = emp._hocba_missing_official_fields()
                if missing:
                    raise ValidationError(_(
                        'Nhân viên chính thức cần khai: %s (BR-010).') % ', '.join(missing))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_employee_code'):
                vals['x_employee_code'] = self.env['ir.sequence'].next_by_code(
                    'hocba.employee.code') or '/'
        employees = super().create(vals_list)
        # Snapshot "nhận việc" cho lịch sử thăng tiến (khách họp #2)
        if not self.env.context.get('hocba_no_join_log'):
            today = fields.Date.context_today(self)
            for emp in employees:
                emp._hocba_log_promotion('join', today, _('Nhận việc'))
        # NV thử việc có ngày bắt đầu → gán quy trình nhận việc bước động
        employees._hocba_maybe_assign_onboarding()
        return employees

    # ------------------------------------------------------------------
    # Face attendance helpers (kiosk client action — hocba_attendance)
    # ------------------------------------------------------------------
    @api.model
    def get_self_attendance_info(self):
        """Return current user's employee name + enrollment state for kiosk."""
        emp = self.env.user.employee_id
        return {
            'employee_id': emp.id,
            'name': emp.name,
            'enrolled': bool(emp.x_face_descriptor),
            'is_official': emp.x_employment_status == 'official',
        }

    @api.model
    def enroll_self_face(self, payload):
        """Save the current user's face sample (image + descriptor)."""
        emp = self.env.user.employee_id
        if not emp:
            raise UserError('Tài khoản chưa gắn với hồ sơ nhân viên.')
        emp.write({
            'x_face_image': payload.get('photo'),
            'x_face_descriptor': json.dumps(payload.get('descriptor') or []),
        })
        return True

    # ------------------------------------------------------------------
    # F-004 (legacy): field cổng cứng x_eval_* chỉ còn là cột lịch sử —
    # constraint/automation đã chuyển sang hb.onboarding.step (bước động).
    # Compute due giữ lại vô hại cho dữ liệu cũ.
    # ------------------------------------------------------------------
    @api.depends('x_probation_start')
    def _compute_eval_dues(self):
        for emp in self:
            if emp.x_probation_start:
                emp.x_eval_2w_due = emp.x_probation_start + timedelta(days=14)
                emp.x_eval_1m_due = emp.x_probation_start + timedelta(days=30)
                emp.x_eval_2m_due = emp.x_probation_start + timedelta(days=60)
            else:
                emp.x_eval_2w_due = False
                emp.x_eval_1m_due = False
                emp.x_eval_2m_due = False

    @api.constrains('x_trial_score_method', 'x_trial_score_content',
                    'x_trial_lesson_date', 'x_trial_lesson_result',
                    'x_trial_lesson_note')
    def _check_trial_lesson(self):
        today = fields.Date.context_today(self)
        for emp in self:
            for score in (emp.x_trial_score_method, emp.x_trial_score_content):
                if score and not (1 <= score <= 10):
                    raise ValidationError(_('Điểm thử giảng phải trong thang 1–10.'))
            if emp.x_trial_lesson_date and emp.x_trial_lesson_date > today:
                raise ValidationError(_('Ngày thử giảng không được sau hôm nay.'))
            if emp.x_trial_lesson_result == 'fail' and not emp.x_trial_lesson_note:
                raise ValidationError(_(
                    'Cần nhập Nhận xét thử giảng khi kết quả Không đạt.'))

    # ------------------------------------------------------------------
    # F-005: Tự động hóa cổng (AUT-001 / AUT-002) — chạy khi result đổi
    # ------------------------------------------------------------------
    def write(self, vals):
        # F-001: không sửa tay probation→official ngoài automation (trừ HR Manager)
        if vals.get('x_employment_status') == 'official' \
                and not self.env.context.get('hocba_gate_automation') \
                and not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                'Chuyển Chính thức được thực hiện qua bước đánh giá đạt '
                'chuẩn (quy trình nhận việc) hoặc bởi HR Manager.'))

        res = super().write(vals)
        # NV chuyển sang thử việc / có ngày bắt đầu → gán quy trình bước động
        if not self.env.context.get('hocba_onb_assigning') and any(
                f in vals for f in ('x_employment_status',
                                    'x_probation_start')):
            self._hocba_maybe_assign_onboarding()
        return res

    def _hocba_user_manages_dept(self, user):
        """True nếu user là trưởng phòng ban của NV (hoặc phòng ban cha)."""
        self.ensure_one()
        dept = self.department_id
        seen = set()
        while dept and dept.id not in seen:
            seen.add(dept.id)
            if dept.manager_id and dept.manager_id.user_id == user:
                return True
            dept = dept.parent_id
        return False

    def _hocba_gate_activity(self, summary, date_deadline, user=None):
        """Tạo Activity nếu chưa có activity cùng summary đang mở (BR-041)."""
        self.ensure_one()
        if any(a.summary == summary for a in self.activity_ids):
            return
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=summary,
            date_deadline=date_deadline,
            user_id=(user or self.env.user).id,
        )

    def _hocba_start_offboarding(self, gate_label):
        """Không đạt cổng → khởi động nghỉ thử việc (tạo đơn offboarding).

        Idempotent: nếu đã có đơn offboarding đang mở cho NV thì bỏ qua,
        tránh tạo trùng khi cổng bị đánh giá lại (re-fire 'fail')."""
        self.ensure_one()
        Offboarding = self.env['hocba.offboarding'].sudo()
        if Offboarding.search_count([
                ('employee_id', '=', self.id),
                ('state', 'in',
                 ('draft', 'submitted', 'mgr_approved', 'hr_approved'))]):
            return
        today = fields.Date.context_today(self)
        Offboarding.create({
            'employee_id': self.id,
            'source': 'probation',
            'reason_type': 'performance',
            'reason': _('Không đạt cổng thử việc %s') % gate_label,
            'request_date': today,
            'expected_leave_date': today,
            'prev_employment_status': self.x_employment_status,
            'state': 'hr_approved',
        })
        self.sudo().with_context(hocba_gate_automation=True).write(
            {'x_employment_status': 'exiting'})
        self._hocba_gate_activity(
            _('Offboarding nghỉ thử việc: %s') % self.name,
            today + timedelta(days=1))
        self.message_post(body=_(
            '❌ Cổng %s KHÔNG ĐẠT — khởi động nghỉ thử việc.') % gate_label)
        self._hocba_notify_probation(
            'probation_fail', 'danger',
            _('Không đạt thử việc: %s') % self.name,
            body=_('Cổng %s không đạt — khởi động nghỉ thử việc.') % gate_label,
            include_employee=True)

    def _hocba_grant_default_assets(self):
        """F-006: tự cấp các loại tài sản 'mặc định' khi qua cổng tuần-2."""
        self.ensure_one()
        Asset = self.env['hr.employee.asset'].sudo()
        today = fields.Date.context_today(self)
        defaults = self.env['hocba.asset.type'].sudo().search(
            [('x_is_default', '=', True)])
        granted = []
        for atype in defaults:
            has = Asset.search_count([
                ('employee_id', '=', self.id),
                ('asset_type_id', '=', atype.id)])
            if has:
                continue
            code = '%s-%s' % (atype.code, self.x_employee_code or self.id)
            if Asset.search_count([('asset_code', '=', code)]):
                continue
            Asset.create({
                'employee_id': self.id,
                'asset_type_id': atype.id,
                'asset_code': code,
                'grant_date': today,
                'condition_in': 'new',
            })
            granted.append(atype.name)
        if granted:
            self.message_post(body=_(
                '🧰 Tự cấp tài sản mặc định: %s.') % ', '.join(granted))

    def _hocba_make_official(self, gate_label):
        """Chuyển Chính thức + lưu snapshot thăng tiến + nhắc tạo hợp đồng."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        self.sudo().with_context(hocba_gate_automation=True).write({
            'x_employment_status': 'official',
            'x_official_date': today,
        })
        self._hocba_log_promotion(
            'probation', today,
            _('Lên chính thức sau cổng %s') % gate_label)
        # Odoo 19: hợp đồng nằm trên hr.version → giao HR tạo bản ghi
        self._hocba_gate_activity(
            _('Tạo hợp đồng chính thức cho %s') % self.name,
            today + timedelta(days=3))
        self.message_post(body=_(
            '🎉 Cổng %(gate)s ĐẠT — chuyển Chính thức từ %(date)s. '
            'Vui lòng tạo hợp đồng chính thức.') % {
                'gate': gate_label, 'date': fields.Date.to_string(today)})
        self._hocba_notify_probation(
            'probation_pass', 'success',
            _('Đạt thử việc — lên chính thức: %s') % self.name,
            body=_('Qua cổng %s.') % gate_label, include_employee=True)

    def _hocba_onboarding_can_finalize(self):
        """(ok, lý do từ chối) cho nút "Chuyển chính thức".

        Chuỗi chạy hết mà không bước nào mang cờ pass_completes thì
        `_advance` chỉ bắn chuông rồi dừng — không có đường nào lên official
        (vd quy trình Giáo viên: thử giảng → ký hợp đồng). Đây là cửa để HR
        Manager tự chốt, nên nó phải chặt đúng bằng quy trình: chỉ mở khi
        mọi bước đã xong và không bước nào Không đạt."""
        self.ensure_one()
        if self.x_employment_status != 'probation':
            return False, _('Nhân viên không ở trạng thái Thử việc.')
        steps = self.sudo().x_onboarding_step_ids
        if not steps:
            return False, _('Nhân viên chưa được gán quy trình nhận việc.')
        pending = steps.filtered(lambda s: s.state not in ('done', 'skipped'))
        if pending:
            return False, _('Còn %(n)s bước chưa xong: %(names)s.') % {
                'n': len(pending),
                'names': ', '.join(pending.mapped('name'))}
        failed = steps.filtered(lambda s: s.result == 'fail')
        if failed:
            return False, _('Có bước Không đạt: %s.') % ', '.join(
                failed.mapped('name'))
        return True, ''

    def action_hocba_finalize_onboarding(self):
        """HR Manager chốt hoàn tất nhận việc → Chính thức từ HÔM NAY.

        Chỉ HR Manager: khớp đúng guard của `write()` — ngoài automation cổng
        đánh giá, không ai khác đặt được x_employment_status='official'."""
        self.ensure_one()
        if not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                'Chỉ HR Manager được chuyển nhân viên lên Chính thức.'))
        ok, reason = self._hocba_onboarding_can_finalize()
        if not ok:
            raise ValidationError(_(
                'Chưa thể chuyển Chính thức: %s') % reason)
        self._hocba_make_official(_('nhận việc (HR xác nhận hoàn tất)'))
        return True

    def _hocba_log_promotion(self, change_type, date_effective, reason):
        """Tạo snapshot lịch sử thăng tiến tự động (nhận việc / lên chính thức)."""
        self.ensure_one()
        self.env['hr.promotion.history'].sudo().with_context(
            hocba_snapshot_only=True).create({
                'employee_id': self.id,
                'x_change_type': change_type,
                'date_effective': date_effective,
                'from_job_id': self.job_id.id or False,
                'to_job_id': self.job_id.id or False,
                'to_department_id': self.department_id.id or False,
                'x_work_form': self.x_work_form or False,
                'x_employment_status': self.x_employment_status or False,
                'reason': reason,
                'approved_by': self.env.user.id,
            })

    def _hocba_notify_probation(self, kind, level, title, body=None,
                                dedup_key=None, include_employee=False):
        """Chuông onboarding/thử việc (hb.notification) → QL trực tiếp + HR
        (trỏ view quản lý 'employees'). Nếu include_employee: gửi thêm bản
        RIÊNG cho chính NV trỏ view self-service 'profile' — NV thường không mở
        được 'employees' nên bấm sẽ trơ. dedup_key để cron không nhân bản."""
        self.ensure_one()
        Notif = self.env['hb.notification'].sudo()
        staff = self.env['res.users']
        if self.parent_id.user_id:
            staff |= self.parent_id.user_id
        grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if grp:
            staff |= self.env['res.users'].sudo().search(
                [('all_group_ids', 'in', grp.id), ('active', '=', True)])
        if include_employee and self.user_id:
            staff -= self.user_id  # NV nhận bản 'profile' riêng, tránh trùng
            Notif._notify(
                self.user_id, category='onboarding', kind=kind, level=level,
                title=title, body=body, target_view='profile',
                target_ref=self.id, dedup_key=dedup_key)
        Notif._notify(
            staff, category='onboarding', kind=kind, level=level,
            title=title, body=body, target_view='employees',
            target_ref=self.id, dedup_key=dedup_key)

    # ------------------------------------------------------------------
    # Onboarding bước động — gán template (snapshot)
    # Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
    # ------------------------------------------------------------------
    def _hocba_assign_onboarding(self, template=None):
        """Sinh instance bước từ template (tự match nếu không truyền).
        Không match → chuông cảnh báo HR, KHÔNG chặn lưu NV.
        Đổi template giữa chừng: bỏ bước chưa chạy, giữ bước done/skipped
        làm lịch sử, bước mới nối tiếp sau (offset sequence)."""
        self.ensure_one()
        tpl = template or self.env['hb.onboarding.template'].sudo(
            )._match_for_employee(self)
        if not tpl:
            self._hocba_notify_probation(
                'onboarding_no_template', 'warning',
                _('Chưa có quy trình nhận việc phù hợp: %s') % self.name,
                body=_('Tạo template khớp hoặc gán tay trong màn Cấu hình '
                       'nhận việc.'),
                dedup_key='onb_no_tpl:%s' % self.id)
            return self.env['hb.onboarding.step']
        Step = self.env['hb.onboarding.step'].sudo()
        self.x_onboarding_step_ids.filtered(
            lambda s: s.state in ('waiting', 'open')).sudo().unlink()
        kept = self.x_onboarding_step_ids
        base_seq = max(kept.mapped('sequence') or [0])
        start = self.x_probation_start
        steps = Step.create([{
            'employee_id': self.id,
            'template_id': tpl.id,
            'sequence': base_seq + ts.sequence,
            'name': ts.name,
            'step_type': ts.step_type,
            'pass_completes': ts.pass_completes,
            'is_extension': ts.is_extension,
            'is_independent': ts.is_independent,
            'auto_action': ts.auto_action,
            'note': ts.note,
            'due_date': (start + timedelta(days=ts.due_days)
                         if start and ts.due_days else False),
        } for ts in tpl.step_ids.sorted(lambda s: (s.sequence, s.id))])
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})
        # Bước độc lập nằm ngoài chuỗi → mở hết ngay. Chuỗi tuần tự vẫn
        # chỉ mở bước KHÔNG độc lập đầu tiên.
        ordered = steps.sorted(lambda s: (s.sequence, s.id))
        for step in ordered.filtered('is_independent'):
            step._open()
        chain = ordered.filtered(lambda s: not s.is_independent)
        if chain:
            chain[0]._open()
        return steps

    def _hocba_maybe_assign_onboarding(self):
        """Gán tự động khi NV thử việc có ngày bắt đầu mà chưa có bước."""
        if self.env.context.get('hocba_no_onb_assign'):
            return
        for emp in self:
            if (emp.x_employment_status == 'probation'
                    and emp.x_probation_start
                    and not emp.x_onboarding_step_ids):
                emp._hocba_assign_onboarding()

    # ------------------------------------------------------------------
    # Migration một lần: field cổng cứng cũ → hb.onboarding.step
    # (gọi từ migrations/19.0.2.0.0/post-migrate.py; idempotent)
    # ------------------------------------------------------------------
    @api.model
    def _hocba_migrate_legacy_gates(self):
        """Map dữ liệu cổng cũ (2w/1m/2m, thử giảng, thiết bị) sang instance
        bước động. Bỏ qua NV đã có bước. NV chưa có dữ liệu cổng → gán mới."""
        Step = self.env['hb.onboarding.step'].sudo()
        tpl_vp = self.env.ref('hocba_employees.onb_template_office',
                              raise_if_not_found=False)
        tpl_gv = self.env.ref('hocba_employees.onb_template_teacher',
                              raise_if_not_found=False)
        emps = self.sudo().with_context(active_test=False).search([
            ('x_probation_start', '!=', False),
            ('x_onboarding_step_ids', '=', False)])
        for emp in emps:
            is_b = (emp.x_position_type in ('staff', 'manager')
                    and emp.x_work_form == 'offline')
            has_trial = (emp.x_trial_lesson_result
                         and emp.x_trial_lesson_result != 'draft')
            if is_b and tpl_vp:
                emp._hocba_migrate_legacy_group_b(Step, tpl_vp)
            elif not is_b and has_trial and tpl_gv:
                emp._hocba_migrate_legacy_teacher(Step, tpl_gv)
            else:
                # chưa có dữ liệu cổng → đi luồng gán mới bình thường
                emp._hocba_maybe_assign_onboarding()

    def _hocba_migrate_legacy_group_b(self, Step, tpl):
        """Nhóm B cũ: tuần-2 → thiết bị → tháng-1 → tháng-2."""
        self.ensure_one()
        closed = self.x_official_date or self.x_employment_status in (
            'official', 'exiting', 'inactive')
        gates = [
            # (tên, kết quả cũ, ngày, note, due, pass_completes, is_extension)
            ('Đánh giá tuần-2', self.x_eval_2w_result, self.x_eval_2w_date,
             self.x_eval_2w_note, self.x_eval_2w_due, False, False),
            ('Cấp thiết bị làm việc', None, self.x_equip_grant_date,
             False, False, False, False),
            ('Đánh giá tháng-1', self.x_eval_1m_result, self.x_eval_1m_date,
             self.x_eval_1m_note, self.x_eval_1m_due, True, False),
            ('Đánh giá tháng-2', self.x_eval_2m_result, self.x_eval_2m_date,
             self.x_eval_2m_note, self.x_eval_2m_due, True, True),
        ]
        opened = False
        seq = 0
        for name, res, date, note, due, pc, ext in gates:
            seq += 1
            vals = {
                'employee_id': self.id, 'template_id': tpl.id,
                'sequence': seq, 'name': name,
                'step_type': 'task' if res is None else 'evaluation',
                'pass_completes': pc, 'is_extension': ext,
                'auto_action': 'grant_assets' if res is None else 'none',
                'due_date': due or False, 'result_note': note or False,
            }
            if res is None:                     # bước thiết bị (task)
                if date:
                    vals.update(state='done', done_date=date)
                elif closed or opened:
                    vals['state'] = 'skipped'
                else:
                    vals['state'] = 'open'
                    opened = True
            elif res in ('pass', 'fail', 'extend'):
                vals.update(state='done', result=res,
                            done_date=date or False)
                # extend cũ ở tuần-2 = tái đánh giá tại chỗ → nếu chưa có
                # dữ liệu phía sau thì để open + extend_count
                if (res == 'extend' and not ext
                        and name == 'Đánh giá tuần-2'
                        and self.x_eval_1m_result == 'draft' and not closed):
                    vals.update(state='open', result=False, extend_count=1)
                    opened = True
            else:                               # draft
                if closed or opened:
                    vals['state'] = 'skipped'
                elif ext and self.x_eval_1m_result != 'extend':
                    # tháng-2 chỉ mở nếu tháng-1 = Gia hạn
                    vals['state'] = 'skipped'
                else:
                    vals['state'] = 'open'
                    opened = True
            Step.create(vals)
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})

    def _hocba_migrate_legacy_teacher(self, Step, tpl):
        """Nhóm A cũ: thử giảng (điểm cũ gộp vào nhận xét) + task ký HĐ."""
        self.ensure_one()
        res = self.x_trial_lesson_result
        note_parts = []
        if self.x_trial_score_method:
            note_parts.append('PP %.1f/10' % self.x_trial_score_method)
        if self.x_trial_score_content:
            note_parts.append('CM %.1f/10' % self.x_trial_score_content)
        if self.x_trial_lesson_note:
            note_parts.append(self.x_trial_lesson_note)
        Step.create({
            'employee_id': self.id, 'template_id': tpl.id, 'sequence': 1,
            'name': 'Thử giảng', 'step_type': 'evaluation',
            'state': 'done', 'result': res,
            'done_date': self.x_trial_lesson_date or False,
            'result_note': '; '.join(note_parts) or False})
        Step.create({
            'employee_id': self.id, 'template_id': tpl.id, 'sequence': 2,
            'name': 'Ký hợp đồng thỉnh giảng', 'step_type': 'task',
            'state': 'open' if res == 'pass' else 'skipped'})
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})

    def _hocba_notify_reminder(self, kind, level, title, body=None,
                               dedup_key=None, include_employee=True):
        """Chuông nhắc hạn hồ sơ (hr_reminder) → HR (view 'employees'). Nếu
        include_employee: bản RIÊNG cho NV trỏ 'profile' (NV thường không mở
        được 'employees'). dedup_key để cron hằng ngày không nhân bản."""
        self.ensure_one()
        Notif = self.env['hb.notification'].sudo()
        staff = self.env['res.users']
        grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if grp:
            staff |= self.env['res.users'].sudo().search(
                [('all_group_ids', 'in', grp.id), ('active', '=', True)])
        if include_employee and self.user_id:
            staff -= self.user_id  # NV nhận bản 'profile' riêng, tránh trùng
            Notif._notify(
                self.user_id, category='hr_reminder', kind=kind, level=level,
                title=title, body=body, target_view='profile',
                target_ref=self.id, dedup_key=dedup_key)
        Notif._notify(
            staff, category='hr_reminder', kind=kind, level=level,
            title=title, body=body, target_view='employees',
            target_ref=self.id, dedup_key=dedup_key)

    @api.model
    def _cron_probation_eval_reminders(self):
        """CRON 7:00 SA (Asia/Ho_Chi_Minh): nhắc bước nhận việc đang mở
        sắp đến hạn trong 2 ngày (quét hb.onboarding.step thay 3 cổng cũ)."""
        soon = fields.Date.today() + timedelta(days=2)
        steps = self.env['hb.onboarding.step'].sudo().search([
            ('state', '=', 'open'),
            ('due_date', '!=', False),
            ('due_date', '<=', soon),
            ('employee_id.x_employment_status', '=', 'probation'),
        ])
        for step in steps:
            emp = step.employee_id
            emp._hocba_gate_activity(
                _('Sắp đến hạn bước "%(step)s": %(emp)s') % {
                    'step': step.name, 'emp': emp.name},
                step.due_date, emp.parent_id.user_id or None)
            emp._hocba_notify_probation(
                'probation_eval', 'warning',
                _('Sắp đến hạn bước "%(step)s": %(emp)s') % {
                    'step': step.name, 'emp': emp.name},
                body=_('Hạn: %s') % step.due_date,
                dedup_key='onb_step:%s:%s' % (step.id, step.due_date))

    @api.model
    def _cron_cert_expiry_alerts(self):
        """F-009 — CRON 7:00 SA: cảnh báo chứng chỉ sắp/đã hết hạn.

        Ngưỡng cấu hình qua ir.config_parameter `hoc_ba.cert_alert_days`
        (mặc định 60 — GĐ-08); chỉ xét chứng chỉ đã xác minh (GĐ-09).
        """
        Skill = self.env['hr.employee.skill']
        days = int(self.env['ir.config_parameter'].sudo().get_param(
            'hoc_ba.cert_alert_days', '60'))
        today = fields.Date.today()
        common = [('x_cert_verified', '=', True),
                  ('employee_id.active', '=', True)]
        # Sắp hết hạn trong <days> ngày
        expiring = Skill.search(common + [
            ('x_cert_expiry', '>=', today),
            ('x_cert_expiry', '<=', today + timedelta(days=days))])
        for emp in expiring.employee_id:
            skills = expiring.filtered(lambda s: s.employee_id == emp)
            deadline = max(min(skills.mapped('x_cert_expiry')) - timedelta(days=30), today)
            emp._hocba_gate_activity(
                _('Chứng chỉ sắp hết hạn: %s') % ', '.join(
                    skills.mapped('skill_id.name')), deadline)
            nearest = min(skills.mapped('x_cert_expiry'))
            emp._hocba_notify_reminder(
                'cert_expiry', 'warning',
                _('Chứng chỉ sắp hết hạn: %s') % ', '.join(
                    skills.mapped('skill_id.name')),
                body=_('Hạn gần nhất: %s') % nearest,
                dedup_key='cert_expiry:%s:%s' % (emp.id, nearest))
        # Đã hết hạn → ưu tiên cao
        expired = Skill.search(common + [('x_cert_expiry', '<', today)])
        for emp in expired.employee_id:
            skills = expired.filtered(lambda s: s.employee_id == emp)
            emp._hocba_gate_activity(
                _('Chứng chỉ ĐÃ HẾT HẠN: %s') % ', '.join(
                    skills.mapped('skill_id.name')), today)
            emp._hocba_notify_reminder(
                'cert_expired', 'danger',
                _('Chứng chỉ ĐÃ HẾT HẠN: %s') % ', '.join(
                    skills.mapped('skill_id.name')),
                dedup_key='cert_expired:%s:%s' % (emp.id, today.strftime('%Y-%m')))

    @api.model
    def _cron_contract_end_alerts(self, days=30):
        """CRON: nhắc HR khi hợp đồng NV sắp hết hạn trong <days> ngày.
        Odoo 19: ngày hết hạn HĐ nằm ở hr.version.contract_date_end (bản version
        hiện hành của NV = employee.version_id). Chỉ báo HR (không báo NV)."""
        today = fields.Date.today()
        limit = today + timedelta(days=days)
        for emp in self.search([
                ('active', '=', True),
                ('version_id.contract_date_end', '>=', today),
                ('version_id.contract_date_end', '<=', limit)]):
            end = emp.version_id.contract_date_end
            emp._hocba_notify_reminder(
                'contract_end', 'warning',
                _('Hợp đồng sắp hết hạn: %s') % emp.name,
                body=_('Ngày hết hạn: %s') % end,
                dedup_key='contract_end:%s:%s' % (emp.id, end),
                include_employee=False)
