import re
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


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
    x_health_insurance_no = fields.Char(string='Số thẻ BHYT')
    x_health_care_place = fields.Char(string='Nơi KCB ban đầu')
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
        selection=[('draft', 'Chưa đánh giá'), ('pass', 'Đạt'), ('fail', 'Không đạt')],
        string='Kết quả tuần-2', default='draft', tracking=True)
    x_eval_2w_date = fields.Date(string='Ngày đánh giá tuần-2')
    x_eval_2w_evaluator_id = fields.Many2one('res.users', string='Người đánh giá tuần-2')
    x_eval_2w_note = fields.Text(string='Ghi chú tuần-2')
    x_equip_grant_date = fields.Date(
        string='Ngày cấp thiết bị', readonly=True,
        help='Tự set khi cổng tuần-2 Đạt (AUT-001).')
    x_eval_2m_due = fields.Date(
        string='Hạn đánh giá tháng-2',
        compute='_compute_eval_dues', store=True, readonly=False,
        help='Mặc định = ngày thử việc + 60 (GĐ-04, đã xác nhận từ dữ liệu Lark); '
             'được sửa trong khoảng [+30, +120] ngày.')
    x_eval_2m_result = fields.Selection(
        selection=[('draft', 'Chưa đánh giá'), ('pass', 'Đạt'), ('fail', 'Không đạt')],
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

    _sql_constraints = [
        ('x_employee_code_uniq', 'unique(x_employee_code)',
         'Mã nhân sự phải là duy nhất!'),
    ]

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
        # BR-010: nhân viên chính thức bắt buộc khai MST + BHXH
        for emp in self.sudo():
            if emp.x_employment_status == 'official':
                missing = []
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
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # F-004: Dòng thời gian thử việc — compute & constraints
    # ------------------------------------------------------------------
    GATE_RESULT_FIELDS = ('x_eval_2w_result', 'x_eval_2m_result')
    GATE_EDIT_FIELDS = GATE_RESULT_FIELDS + (
        'x_eval_2w_date', 'x_eval_2w_note', 'x_eval_2w_evaluator_id',
        'x_eval_2m_date', 'x_eval_2m_note', 'x_eval_2m_evaluator_id')

    @api.depends('x_probation_start')
    def _compute_eval_dues(self):
        for emp in self:
            if emp.x_probation_start:
                emp.x_eval_2w_due = emp.x_probation_start + timedelta(days=14)
                emp.x_eval_2m_due = emp.x_probation_start + timedelta(days=60)
            else:
                emp.x_eval_2w_due = False
                emp.x_eval_2m_due = False

    @api.constrains('x_probation_start', 'x_eval_2w_due', 'x_eval_2m_due')
    def _check_eval_due_ranges(self):
        for emp in self:
            start = emp.x_probation_start
            if not start:
                continue
            if emp.x_eval_2w_due and not (
                    start + timedelta(days=7) <= emp.x_eval_2w_due <= start + timedelta(days=21)):
                raise ValidationError(_(
                    'Hạn đánh giá tuần-2 phải trong khoảng 7–21 ngày kể từ ngày thử việc.'))
            if emp.x_eval_2m_due and not (
                    start + timedelta(days=30) <= emp.x_eval_2m_due <= start + timedelta(days=120)):
                raise ValidationError(_(
                    'Hạn đánh giá tháng-2 phải trong khoảng 30–120 ngày kể từ ngày thử việc.'))

    @api.constrains('x_eval_2w_result', 'x_eval_2m_result', 'x_probation_start',
                    'x_eval_2w_date', 'x_eval_2m_date')
    def _check_gate_rules(self):
        today = fields.Date.context_today(self)
        for emp in self:
            has_result = emp.x_eval_2w_result != 'draft' or emp.x_eval_2m_result != 'draft'
            if has_result and not emp.x_probation_start:
                raise ValidationError(_(
                    'Cần nhập Ngày bắt đầu thử việc trước khi ghi kết quả đánh giá.'))
            # Không điền cổng tháng-2 nếu tuần-2 chưa Đạt
            if emp.x_eval_2m_result != 'draft' and emp.x_eval_2w_result != 'pass':
                raise ValidationError(_(
                    'Chỉ đánh giá cổng tháng-2 sau khi cổng tuần-2 đã Đạt.'))
            for d in (emp.x_eval_2w_date, emp.x_eval_2m_date):
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
        # Quyền điền kết quả: HR Manager hoặc quản lý trực tiếp (spec F-004)
        if any(f in vals for f in self.GATE_EDIT_FIELDS) and not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            for emp in self:
                if emp.parent_id.user_id != self.env.user:
                    raise AccessError(_(
                        'Chỉ HR Manager hoặc quản lý trực tiếp được điền kết quả thử việc.'))
        # F-001: không sửa tay probation→official ngoài automation (trừ HR Manager)
        if vals.get('x_employment_status') == 'official' \
                and not self.env.context.get('hocba_gate_automation') \
                and not self.env.su \
                and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                'Chuyển Chính thức được thực hiện qua cổng tháng-2 (AUT-002) '
                'hoặc bởi HR Manager.'))

        track_gates = any(f in vals for f in self.GATE_RESULT_FIELDS)
        pre = {e.id: (e.x_eval_2w_result, e.x_eval_2m_result) for e in self} if track_gates else {}
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
                old_2w, old_2m = pre[emp.id]
                if emp.sudo().x_skip_auto_trigger:
                    if emp.x_eval_2w_result != old_2w or emp.x_eval_2m_result != old_2m:
                        emp.message_post(body=_(
                            'Auto trigger bị bỏ qua bởi %s.') % self.env.user.name)
                    continue
                if emp.x_eval_2w_result != old_2w and emp.x_eval_2w_result != 'draft':
                    emp._hocba_aut_001()
                if emp.x_eval_2m_result != old_2m and emp.x_eval_2m_result != 'draft':
                    emp._hocba_aut_002()
        return res

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

    def _hocba_aut_001(self):
        """Cổng tuần-2: Đạt → cấp thiết bị + hẹn cổng tháng-2; Không đạt → offboarding."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        tbp_user = self.parent_id.user_id or self.env.user
        if self.x_eval_2w_result == 'pass':
            self.sudo().with_context(hocba_gate_automation=True).write(
                {'x_equip_grant_date': today})
            self._hocba_gate_activity(
                _('Cấp thiết bị văn phòng cho %s') % self.name,
                today + timedelta(days=1))
            self._hocba_gate_activity(
                _('Đánh giá thử việc tháng-2: %s') % self.name,
                self.x_eval_2m_due or today + timedelta(days=46), tbp_user)
            self.message_post(body=_(
                '✅ Cổng tuần-2 ĐẠT — đã khởi động cấp thiết bị và hẹn đánh giá tháng-2.'))
        elif self.x_eval_2w_result == 'fail':
            self.sudo().with_context(hocba_gate_automation=True).write(
                {'x_employment_status': 'exiting'})
            self._hocba_gate_activity(
                _('Offboarding nghỉ thử việc: %s') % self.name,
                today + timedelta(days=1))
            self.message_post(body=_(
                '❌ Cổng tuần-2 KHÔNG ĐẠT — khởi động nghỉ thử việc '
                '(GĐ-03: không gia hạn).'))

    def _hocba_aut_002(self):
        """Cổng tháng-2: Đạt → Chính thức; Không đạt → offboarding."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.x_eval_2m_result == 'pass':
            self.sudo().with_context(hocba_gate_automation=True).write({
                'x_employment_status': 'official',
                'x_official_date': today,
            })
            # Odoo 19: hợp đồng nằm trên hr.version → giao HR tạo bản ghi
            self._hocba_gate_activity(
                _('Tạo hợp đồng chính thức cho %s') % self.name,
                today + timedelta(days=3))
            self.message_post(body=_(
                '🎉 Cổng tháng-2 ĐẠT — chuyển Chính thức từ %s. '
                'Vui lòng tạo hợp đồng chính thức.') % fields.Date.to_string(today))
        elif self.x_eval_2m_result == 'fail':
            self.sudo().with_context(hocba_gate_automation=True).write(
                {'x_employment_status': 'exiting'})
            self._hocba_gate_activity(
                _('Offboarding nghỉ thử việc: %s') % self.name,
                today + timedelta(days=1))
            self.message_post(body=_(
                '❌ Cổng tháng-2 KHÔNG ĐẠT — khởi động nghỉ thử việc.'))

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
        for emp in self.search(base + [('x_eval_2w_result', '=', 'pass'),
                                       ('x_eval_2m_result', '=', 'draft'),
                                       ('x_eval_2m_due', '<=', soon)]):
            emp._hocba_gate_activity(
                _('Sắp đến hạn đánh giá tháng-2: %s') % emp.name,
                emp.x_eval_2m_due, emp.parent_id.user_id or None)

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
        # Đã hết hạn → ưu tiên cao
        expired = Skill.search(common + [('x_cert_expiry', '<', today)])
        for emp in expired.employee_id:
            skills = expired.filtered(lambda s: s.employee_id == emp)
            emp._hocba_gate_activity(
                _('Chứng chỉ ĐÃ HẾT HẠN: %s') % ', '.join(
                    skills.mapped('skill_id.name')), today)
