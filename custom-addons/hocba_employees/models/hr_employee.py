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

    @api.depends('x_asset_ids.state')
    def _compute_asset_count(self):
        # BR-052: chỉ đếm tài sản đang giữ
        for emp in self:
            emp.x_asset_count = len(emp.x_asset_ids.filtered(
                lambda a: a.state == 'assigned'))

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

    @api.depends('x_probation_start', 'x_eval_2w_result', 'x_eval_2w_date',
                 'x_eval_2w_due', 'x_equip_grant_date', 'x_eval_1m_result',
                 'x_eval_1m_date', 'x_eval_1m_due', 'x_eval_2m_result',
                 'x_eval_2m_date', 'x_eval_2m_due', 'x_official_date')
    def _compute_probation_timeline_html(self):
        # F-001: mini-timeline theo wireframe (server-rendered, không JS)
        def fmt(d):
            return d.strftime('%d/%m/%Y') if d else ''

        for emp in self:
            def gate_state(result):
                return {'pass': 'done', 'fail': 'fail',
                        'extend': 'extend'}.get(result, 'pending')

            steps = [
                (_('Thử việc'), 'done' if emp.x_probation_start else 'pending',
                 fmt(emp.x_probation_start)),
                (_('ĐG tuần-2'), gate_state(emp.x_eval_2w_result),
                 fmt(emp.x_eval_2w_date) or (
                     emp.x_eval_2w_due and _('hạn %s') % fmt(emp.x_eval_2w_due) or '')),
                (_('Cấp thiết bị'), 'done' if emp.x_equip_grant_date else 'pending',
                 fmt(emp.x_equip_grant_date)),
                (_('ĐG tháng-1'), gate_state(emp.x_eval_1m_result),
                 fmt(emp.x_eval_1m_date) or (
                     emp.x_eval_1m_due and _('hạn %s') % fmt(emp.x_eval_1m_due) or '')),
                (_('ĐG tháng-2'), gate_state(emp.x_eval_2m_result),
                 fmt(emp.x_eval_2m_date) or (
                     emp.x_eval_2m_due and _('hạn %s') % fmt(emp.x_eval_2m_due) or '')),
                (_('Chính thức'), 'done' if emp.x_official_date else 'pending',
                 fmt(emp.x_official_date)),
            ]
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

    @api.constrains('x_employment_status', 'x_pit_code', 'x_social_insurance_no')
    def _check_official_required_fields(self):
        # BR-010 (mở rộng họp #2): chính thức bắt buộc CCCD + MST + BHXH
        for emp in self.sudo():
            if emp.x_employment_status == 'official':
                missing = []
                if not emp.identification_id:
                    missing.append('CCCD')
                if not emp.x_pit_code:
                    missing.append('MST TNCN')
                if not emp.x_social_insurance_no:
                    missing.append('Số sổ BHXH')
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
    # F-004: Dòng thời gian thử việc — compute & constraints
    # ------------------------------------------------------------------
    GATE_RESULT_FIELDS = ('x_eval_2w_result', 'x_eval_1m_result', 'x_eval_2m_result')
    GATE_EDIT_FIELDS = GATE_RESULT_FIELDS + (
        'x_eval_2w_date', 'x_eval_2w_note', 'x_eval_2w_evaluator_id',
        'x_eval_1m_date', 'x_eval_1m_note', 'x_eval_1m_evaluator_id',
        'x_eval_2m_date', 'x_eval_2m_note', 'x_eval_2m_evaluator_id')

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

    @api.constrains('x_probation_start', 'x_eval_2w_due', 'x_eval_1m_due', 'x_eval_2m_due')
    def _check_eval_due_ranges(self):
        for emp in self:
            start = emp.x_probation_start
            if not start:
                continue
            if emp.x_eval_2w_due and not (
                    start + timedelta(days=7) <= emp.x_eval_2w_due <= start + timedelta(days=21)):
                raise ValidationError(_(
                    'Hạn đánh giá tuần-2 phải trong khoảng 7–21 ngày kể từ ngày thử việc.'))
            if emp.x_eval_1m_due and not (
                    start + timedelta(days=21) <= emp.x_eval_1m_due <= start + timedelta(days=45)):
                raise ValidationError(_(
                    'Hạn đánh giá tháng-1 phải trong khoảng 21–45 ngày kể từ ngày thử việc.'))
            if emp.x_eval_2m_due and not (
                    start + timedelta(days=30) <= emp.x_eval_2m_due <= start + timedelta(days=120)):
                raise ValidationError(_(
                    'Hạn đánh giá tháng-2 phải trong khoảng 30–120 ngày kể từ ngày thử việc.'))

    @api.constrains('x_eval_2w_result', 'x_eval_1m_result', 'x_eval_2m_result',
                    'x_probation_start', 'x_eval_2w_date', 'x_eval_1m_date',
                    'x_eval_2m_date')
    def _check_gate_rules(self):
        today = fields.Date.context_today(self)
        for emp in self:
            has_result = (emp.x_eval_2w_result != 'draft'
                          or emp.x_eval_1m_result != 'draft'
                          or emp.x_eval_2m_result != 'draft')
            if has_result and not emp.x_probation_start:
                raise ValidationError(_(
                    'Cần nhập Ngày bắt đầu thử việc trước khi ghi kết quả đánh giá.'))
            # Cổng tháng-1 chỉ mở sau khi tuần-2 đã Đạt
            if emp.x_eval_1m_result != 'draft' and emp.x_eval_2w_result != 'pass':
                raise ValidationError(_(
                    'Chỉ đánh giá cổng tháng-1 sau khi cổng tuần-2 đã Đạt.'))
            # Cổng tháng-2 chỉ mở khi tháng-1 = Gia hạn (chưa chốt ở mốc 1 tháng)
            if emp.x_eval_2m_result != 'draft' and emp.x_eval_1m_result != 'extend':
                raise ValidationError(_(
                    'Chỉ đánh giá cổng tháng-2 khi cổng tháng-1 đã "Gia hạn".'))
            for d in (emp.x_eval_2w_date, emp.x_eval_1m_date, emp.x_eval_2m_date):
                if d and emp.x_probation_start and (d < emp.x_probation_start or d > today):
                    raise ValidationError(_(
                        'Ngày đánh giá phải từ ngày bắt đầu thử việc đến hôm nay.'))

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
        # F-006: chặn Archive khi còn tài sản chưa thu hồi/chuyển giao
        if vals.get('active') is False:
            for emp in self:
                pending = emp.x_asset_ids.filtered(lambda a: a.state == 'assigned')
                if pending:
                    raise ValidationError(_(
                        'Không thể lưu trữ "%(emp)s" — còn %(n)d tài sản chưa thu hồi: '
                        '%(codes)s') % {
                            'emp': emp.name, 'n': len(pending),
                            'codes': ', '.join(pending.mapped('asset_code'))})
        # Quyền điền kết quả: HR Manager, quản lý trực tiếp, hoặc trưởng phòng
        # ban của nhân viên (phân theo phòng ban — họp #2).
        if any(f in vals for f in self.GATE_EDIT_FIELDS) and not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            user = self.env.user
            for emp in self:
                if emp.parent_id.user_id == user:
                    continue
                if emp._hocba_user_manages_dept(user):
                    continue
                raise AccessError(_(
                    'Chỉ HR Manager, quản lý trực tiếp hoặc trưởng phòng ban '
                    'được điền kết quả thử việc.'))
        # F-001: không sửa tay probation→official ngoài automation (trừ HR Manager)
        if vals.get('x_employment_status') == 'official' \
                and not self.env.context.get('hocba_gate_automation') \
                and not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                'Chuyển Chính thức được thực hiện qua cổng tháng-2 (AUT-002) '
                'hoặc bởi HR Manager.'))

        track_gates = any(f in vals for f in self.GATE_RESULT_FIELDS)
        pre = {e.id: (e.x_eval_2w_result, e.x_eval_1m_result, e.x_eval_2m_result)
               for e in self} if track_gates else {}
        track_trial = 'x_trial_lesson_result' in vals
        pre_trial = {e.id: e.x_trial_lesson_result for e in self} if track_trial else {}
        res = super().write(vals)
        # F-008: kết quả thử giảng → activity cho HR
        if track_trial:
            today = fields.Date.context_today(self)
            for emp in self:
                if emp.x_trial_lesson_result == pre_trial[emp.id] \
                        or emp.x_trial_lesson_result == 'draft':
                    continue
                if emp.x_trial_lesson_result == 'pass':
                    emp._hocba_gate_activity(
                        _('Ký HĐ thỉnh giảng cho %s') % emp.name,
                        today + timedelta(days=3))
                    emp.message_post(body=_(
                        '✅ Thử giảng ĐẠT (PP %(m).1f / CM %(c).1f) — nhắc HR ký HĐ.') % {
                            'm': emp.x_trial_score_method, 'c': emp.x_trial_score_content})
                else:
                    emp._hocba_gate_activity(
                        _('Thông báo kết quả thử giảng cho %s') % emp.name,
                        today + timedelta(days=1))
                    emp.message_post(body=_('❌ Thử giảng KHÔNG ĐẠT — nhắc HR thông báo.'))
        if track_gates:
            for emp in self:
                old_2w, old_1m, old_2m = pre[emp.id]
                if emp.sudo().x_skip_auto_trigger:
                    if (emp.x_eval_2w_result != old_2w
                            or emp.x_eval_1m_result != old_1m
                            or emp.x_eval_2m_result != old_2m):
                        emp.message_post(body=_(
                            'Auto trigger bị bỏ qua bởi %s.') % self.env.user.name)
                    continue
                if emp.x_eval_2w_result != old_2w and emp.x_eval_2w_result != 'draft':
                    emp._hocba_aut_001()
                if emp.x_eval_1m_result != old_1m and emp.x_eval_1m_result != 'draft':
                    emp._hocba_aut_001m()
                if emp.x_eval_2m_result != old_2m and emp.x_eval_2m_result != 'draft':
                    emp._hocba_aut_002()
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
                ('asset_type_id', '=', atype.id),
                ('state', '=', 'assigned')])
            if has:
                continue
            code = '%s-%s' % (atype.code, self.x_employee_code or self.id)
            if Asset.search_count([('asset_code', '=', code),
                                   ('state', '=', 'assigned')]):
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

    def _hocba_aut_001(self):
        """Cổng tuần-2: Đạt → cấp thiết bị + tài sản + hẹn tháng-1;
        Gia hạn → tái đánh giá; Không đạt → offboarding."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        tbp_user = self.parent_id.user_id or self.env.user
        if self.x_eval_2w_result == 'pass':
            self.sudo().with_context(hocba_gate_automation=True).write(
                {'x_equip_grant_date': today})
            self._hocba_grant_default_assets()
            self._hocba_gate_activity(
                _('Cấp thiết bị văn phòng cho %s') % self.name,
                today + timedelta(days=1))
            self._hocba_gate_activity(
                _('Đánh giá thử việc tháng-1: %s') % self.name,
                self.x_eval_1m_due or today + timedelta(days=16), tbp_user)
            self.message_post(body=_(
                '✅ Cổng tuần-2 ĐẠT — đã cấp thiết bị/tài sản và hẹn đánh giá tháng-1.'))
        elif self.x_eval_2w_result == 'extend':
            self._hocba_gate_activity(
                _('Tái đánh giá thử việc (gia hạn): %s') % self.name,
                today + timedelta(days=7), tbp_user)
            self.message_post(body=_(
                '⏳ Cổng tuần-2 GIA HẠN — tiếp tục thử việc, hẹn tái đánh giá.'))
            self._hocba_notify_probation(
                'probation_extend', 'warning',
                _('Gia hạn thử việc: %s') % self.name,
                body=_('Cổng tuần-2 gia hạn.'), include_employee=True)
        elif self.x_eval_2w_result == 'fail':
            self._hocba_start_offboarding(_('tuần-2'))

    def _hocba_aut_001m(self):
        """Cổng tháng-1: Đạt → Chính thức sớm; Gia hạn → hẹn tháng-2;
        Không đạt → offboarding."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        tbp_user = self.parent_id.user_id or self.env.user
        if self.x_eval_1m_result == 'pass':
            self._hocba_make_official(_('tháng-1'))
        elif self.x_eval_1m_result == 'extend':
            self._hocba_gate_activity(
                _('Đánh giá thử việc tháng-2: %s') % self.name,
                self.x_eval_2m_due or today + timedelta(days=30), tbp_user)
            self.message_post(body=_(
                '⏳ Cổng tháng-1 GIA HẠN — tiếp tục đến cổng tháng-2.'))
            self._hocba_notify_probation(
                'probation_extend', 'warning',
                _('Gia hạn thử việc: %s') % self.name,
                body=_('Cổng tháng-1 gia hạn.'), include_employee=True)
        elif self.x_eval_1m_result == 'fail':
            self._hocba_start_offboarding(_('tháng-1'))

    def _hocba_aut_002(self):
        """Cổng tháng-2: Đạt → Chính thức; Gia hạn → tái đánh giá;
        Không đạt → offboarding."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        tbp_user = self.parent_id.user_id or self.env.user
        if self.x_eval_2m_result == 'pass':
            self._hocba_make_official(_('tháng-2'))
        elif self.x_eval_2m_result == 'extend':
            self._hocba_gate_activity(
                _('Tái đánh giá thử việc (gia hạn tháng-2): %s') % self.name,
                today + timedelta(days=14), tbp_user)
            self.message_post(body=_(
                '⏳ Cổng tháng-2 GIA HẠN — kéo dài thử việc, hẹn tái đánh giá.'))
            self._hocba_notify_probation(
                'probation_extend', 'warning',
                _('Gia hạn thử việc: %s') % self.name,
                body=_('Cổng tháng-2 gia hạn.'), include_employee=True)
        elif self.x_eval_2m_result == 'fail':
            self._hocba_start_offboarding(_('tháng-2'))

    @api.model
    def _cron_probation_eval_reminders(self):
        """CRON 7:00 SA (Asia/Ho_Chi_Minh): nhắc đánh giá đến hạn trong 2 ngày."""
        soon = fields.Date.today() + timedelta(days=2)
        base = [('x_employment_status', '=', 'probation'),
                ('x_probation_start', '!=', False)]
        for emp in self.search(base + [('x_eval_2w_result', '=', 'draft'),
                                       ('x_eval_2w_due', '<=', soon)]):
            emp._hocba_gate_activity(
                _('Sắp đến hạn đánh giá tuần-2: %s') % emp.name,
                emp.x_eval_2w_due, emp.parent_id.user_id or None)
            emp._hocba_notify_probation(
                'probation_eval', 'warning',
                _('Sắp đến hạn đánh giá tuần-2: %s') % emp.name,
                body=_('Hạn: %s') % emp.x_eval_2w_due,
                dedup_key='probation_eval:%s:2w:%s' % (emp.id, emp.x_eval_2w_due))
        for emp in self.search(base + [('x_eval_2w_result', '=', 'pass'),
                                       ('x_eval_1m_result', '=', 'draft'),
                                       ('x_eval_1m_due', '<=', soon)]):
            emp._hocba_gate_activity(
                _('Sắp đến hạn đánh giá tháng-1: %s') % emp.name,
                emp.x_eval_1m_due, emp.parent_id.user_id or None)
            emp._hocba_notify_probation(
                'probation_eval', 'warning',
                _('Sắp đến hạn đánh giá tháng-1: %s') % emp.name,
                body=_('Hạn: %s') % emp.x_eval_1m_due,
                dedup_key='probation_eval:%s:1m:%s' % (emp.id, emp.x_eval_1m_due))
        for emp in self.search(base + [('x_eval_1m_result', '=', 'extend'),
                                       ('x_eval_2m_result', '=', 'draft'),
                                       ('x_eval_2m_due', '<=', soon)]):
            emp._hocba_gate_activity(
                _('Sắp đến hạn đánh giá tháng-2: %s') % emp.name,
                emp.x_eval_2m_due, emp.parent_id.user_id or None)
            emp._hocba_notify_probation(
                'probation_eval', 'warning',
                _('Sắp đến hạn đánh giá tháng-2: %s') % emp.name,
                body=_('Hạn: %s') % emp.x_eval_2m_due,
                dedup_key='probation_eval:%s:2m:%s' % (emp.id, emp.x_eval_2m_due))

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
