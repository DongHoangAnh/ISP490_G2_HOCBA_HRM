from datetime import date, datetime, time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

from .hb_review_criteria import ROLE_GROUP_SEL

PERIOD_TYPE_SEL = [
    ('quarter', 'Quý'),
    ('half', 'Nửa năm'),
    ('year', 'Năm'),
]
GRADE_SEL = [
    ('a', 'A — Xuất sắc'),
    ('b', 'B — Tốt'),
    ('c', 'C — Đạt'),
    ('d', 'D — Cần cải thiện'),
]
STATE_SEL = [
    ('draft', 'Nháp'),
    ('confirmed', 'Đã chốt'),
    ('published', 'Đã công bố'),
]
# Số tháng mỗi loại kỳ + số kỳ hợp lệ trong năm.
PERIOD_MONTHS = {'quarter': 3, 'half': 6, 'year': 12}
PERIOD_COUNT = {'quarter': 4, 'half': 2, 'year': 1}


def _bucket(value, table):
    """Quy đổi chỉ số -> điểm theo bảng ngưỡng [(min, score), ...] giảm dần.
    Trả về điểm của ngưỡng đầu tiên mà value >= min (docs/CONG_THUC_DANH_GIA.md §4)."""
    for threshold, score in table:
        if value >= threshold:
            return score
    return table[-1][1]


class HbPerformanceReview(models.Model):
    """Phiếu đánh giá định kỳ của MỘT nhân viên trong MỘT kỳ.
    Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
    Công thức: docs/CONG_THUC_DANH_GIA.md"""
    _name = 'hb.performance.review'
    _description = 'Phiếu đánh giá nhân viên định kỳ'
    _order = 'period_year desc, period_index desc, id desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        related='employee_id.department_id', store=True, readonly=True)
    role_group = fields.Selection(
        ROLE_GROUP_SEL, string='Nhóm', required=True, index=True,
        help='Chốt tại thời điểm tạo phiếu — nhân viên đổi loại sau không làm '
             'lệch phiếu cũ.')

    period_type = fields.Selection(
        PERIOD_TYPE_SEL, string='Loại kỳ', default='quarter', required=True)
    period_year = fields.Integer(
        string='Năm', required=True,
        default=lambda self: fields.Date.context_today(self).year)
    period_index = fields.Integer(string='Kỳ thứ', default=1, required=True)
    date_from = fields.Date(
        string='Từ ngày', compute='_compute_period_range', store=True)
    date_to = fields.Date(
        string='Đến ngày', compute='_compute_period_range', store=True)
    period_label = fields.Char(
        string='Kỳ', compute='_compute_period_label', store=True)

    line_ids = fields.One2many(
        'hb.performance.review.line', 'review_id', string='Dòng chấm')
    total_score = fields.Float(
        string='Tổng điểm (thang 100)', compute='_compute_total', store=True)
    grade = fields.Selection(
        GRADE_SEL, string='Xếp loại', compute='_compute_total', store=True)

    state = fields.Selection(
        STATE_SEL, string='Trạng thái', default='draft', required=True, index=True)
    evaluator_id = fields.Many2one(
        'res.users', string='Người đánh giá',
        default=lambda self: self.env.user)
    confirmed_on = fields.Datetime(string='Ngày chốt')
    published_on = fields.Datetime(string='Ngày công bố')

    self_note = fields.Text(string='Nhân viên tự đánh giá')
    manager_note = fields.Text(string='Nhận xét của quản lý')
    hr_note = fields.Text(string='Ý kiến HR')

    # --- Chỉ số snapshot (đóng băng khi chốt; chỉ tính lại lúc Nháp) ---
    metric_total_units = fields.Integer(
        string='Tổng buổi dạy / ngày công')
    metric_ok_units = fields.Integer(string='Số buổi / ngày đạt')
    metric_punctual_pct = fields.Float(string='Tỷ lệ đúng giờ (%)')
    metric_late_count = fields.Integer(string='Số lần trễ')
    metric_leave_days = fields.Float(string='Ngày nghỉ phép trong kỳ')
    metric_cert_valid = fields.Integer(string='Chứng chỉ còn hạn')
    metric_cert_expiring = fields.Integer(string='Chứng chỉ sắp hết hạn')
    metric_cert_expired = fields.Integer(string='Chứng chỉ hết hạn')
    metrics_computed_on = fields.Datetime(string='Tính chỉ số lúc')

    _uniq_period = models.Constraint(
        'unique (employee_id, period_type, period_year, period_index)',
        'Mỗi nhân viên chỉ có một phiếu đánh giá cho mỗi kỳ.',
    )

    # ------------------------------------------------------------------
    # Kỳ đánh giá
    # ------------------------------------------------------------------
    @api.model
    def period_range(self, period_type, year, index):
        """(date_from, date_to) của kỳ — docs/CONG_THUC_DANH_GIA.md §3."""
        months = PERIOD_MONTHS.get(period_type, 3)
        idx = max(1, min(int(index or 1), PERIOD_COUNT.get(period_type, 4)))
        start_month = (idx - 1) * months + 1
        end_month = start_month + months - 1
        first = date(year, start_month, 1)
        if end_month >= 12:
            last = date(year, 12, 31)
        else:
            last = date(year, end_month + 1, 1) - timedelta(days=1)
        return first, last

    @api.depends('period_type', 'period_year', 'period_index')
    def _compute_period_range(self):
        for rec in self:
            if not rec.period_year:
                rec.date_from = rec.date_to = False
                continue
            rec.date_from, rec.date_to = self.period_range(
                rec.period_type, rec.period_year, rec.period_index)

    @api.depends('period_type', 'period_year', 'period_index')
    def _compute_period_label(self):
        for rec in self:
            if rec.period_type == 'year':
                rec.period_label = _('Năm %s') % rec.period_year
            elif rec.period_type == 'half':
                rec.period_label = _('Nửa năm %s/%s') % (
                    rec.period_index, rec.period_year)
            else:
                rec.period_label = _('Quý %s/%s') % (
                    rec.period_index, rec.period_year)

    @api.constrains('period_type', 'period_index', 'period_year')
    def _check_period(self):
        for rec in self:
            limit = PERIOD_COUNT.get(rec.period_type, 4)
            if not 1 <= rec.period_index <= limit:
                raise ValidationError(_(
                    'Kỳ thứ phải trong khoảng 1..%(n)s với loại kỳ "%(t)s".') % {
                        'n': limit,
                        't': dict(PERIOD_TYPE_SEL).get(rec.period_type, ''),
                    })
            if not 2000 <= rec.period_year <= 2100:
                raise ValidationError(_('Năm đánh giá không hợp lệ.'))

    # ------------------------------------------------------------------
    # Điểm & xếp loại
    # ------------------------------------------------------------------
    @api.depends('line_ids.score', 'line_ids.weight', 'line_ids.max_score')
    def _compute_total(self):
        ICP = self.env['ir.config_parameter'].sudo()
        ga = float(ICP.get_param('hocba_reviews.grade_a', 85))
        gb = float(ICP.get_param('hocba_reviews.grade_b', 70))
        gc = float(ICP.get_param('hocba_reviews.grade_c', 55))
        for rec in self:
            scored = rec.line_ids.filtered(lambda l: l.max_score > 0)
            wsum = sum(scored.mapped('weight'))
            if wsum:
                acc = sum((l.score / l.max_score) * l.weight for l in scored)
                rec.total_score = acc / wsum * 100
            else:
                rec.total_score = 0.0
            if rec.total_score >= ga:
                rec.grade = 'a'
            elif rec.total_score >= gb:
                rec.grade = 'b'
            elif rec.total_score >= gc:
                rec.grade = 'c'
            else:
                rec.grade = 'd'

    # ------------------------------------------------------------------
    # Cấu hình chấm điểm — màn Cấu hình đánh giá
    # Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md
    # ------------------------------------------------------------------
    @api.model
    def grading_config(self):
        """Ngưỡng xếp loại + tham số đang chạy (nguồn: ir.config_parameter)."""
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'grade_a': float(ICP.get_param('hocba_reviews.grade_a', 85)),
            'grade_b': float(ICP.get_param('hocba_reviews.grade_b', 70)),
            'grade_c': float(ICP.get_param('hocba_reviews.grade_c', 55)),
            'sessions_target': float(ICP.get_param(
                'hocba_reviews.teacher_sessions_target', 60)),
        }

    @api.model
    def set_grading(self, vals):
        """Lưu ngưỡng A/B/C + chỉ tiêu buổi dạy.

        Ngưỡng đọc lúc tính điểm (không snapshot vào phiếu), nên phiếu Nháp
        được tính lại ngay để bảng xếp loại không hiển thị số cũ; phiếu đã
        chốt/công bố giữ nguyên kết quả đã đóng băng.
        """
        cur = self.grading_config()
        try:
            ga = float(vals.get('grade_a', cur['grade_a']))
            gb = float(vals.get('grade_b', cur['grade_b']))
            gc = float(vals.get('grade_c', cur['grade_c']))
            target = float(vals.get('sessions_target', cur['sessions_target']))
        except (TypeError, ValueError):
            raise ValidationError(_('Ngưỡng xếp loại phải là số.'))
        if not 0 < gc < gb < ga <= 100:
            raise ValidationError(_(
                'Ngưỡng phải giảm dần và nằm trong 0–100: A (%(a)s) > B (%(b)s)'
                ' > C (%(c)s) > 0.') % {'a': ga, 'b': gb, 'c': gc})
        if target <= 0:
            raise ValidationError(_('Chỉ tiêu buổi dạy phải lớn hơn 0.'))
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('hocba_reviews.grade_a', str(ga))
        ICP.set_param('hocba_reviews.grade_b', str(gb))
        ICP.set_param('hocba_reviews.grade_c', str(gc))
        ICP.set_param('hocba_reviews.teacher_sessions_target', str(target))
        drafts = self.sudo().search([('state', '=', 'draft')])
        if drafts:
            drafts._compute_total()
        return self.grading_config()

    # ------------------------------------------------------------------
    # Tạo phiếu — sinh dòng chấm theo bộ tiêu chí của nhóm
    # ------------------------------------------------------------------
    @api.model
    def _role_group_of(self, employee):
        return 'teacher' if employee.x_employee_type_id.code == 'teacher' \
            else 'office'

    @api.model
    def role_group_domain(self, role_group):
        """Domain lọc nhân viên theo nhóm.
        Nhóm 'office' phải BẮT buộc gộp NV chưa gán loại: domain '!=' trên field
        related đi qua JOIN nên bỏ sót bản ghi NULL (21 NV trên Neon từng bị
        thiếu vì lý do này)."""
        if role_group == 'teacher':
            return [('x_employee_type_id.code', '=', 'teacher')]
        return ['|', ('x_employee_type_id', '=', False),
                ('x_employee_type_id.code', '!=', 'teacher')]

    @api.model_create_multi
    def create(self, vals_list):
        Criteria = self.env['hb.review.criteria'].sudo()
        for vals in vals_list:
            if not vals.get('role_group') and vals.get('employee_id'):
                emp = self.env['hr.employee'].sudo().browse(vals['employee_id'])
                vals['role_group'] = self._role_group_of(emp)
            if not vals.get('line_ids'):
                crits = Criteria.search(
                    [('role_group', '=', vals.get('role_group', 'office'))])
                vals['line_ids'] = [(0, 0, {
                    'criteria_id': c.id,
                    'weight': c.weight,
                    'max_score': c.max_score,
                    'is_auto': c.auto_source != 'none',
                }) for c in crits]
        reviews = super().create(vals_list)
        reviews.compute_metrics()
        return reviews

    def write(self, vals):
        # Phiếu đã chốt/công bố: khoá nội dung chấm, chỉ HR Manager mới sửa được
        # (mở lại phiếu là đường chính thức — action_reset_draft).
        locked_fields = {
            'line_ids', 'self_note', 'manager_note', 'period_type',
            'period_year', 'period_index', 'employee_id', 'role_group',
        }
        if locked_fields & set(vals) and not self.env.su:
            is_hr = self.env.user.has_group('hr.group_hr_manager')
            for rec in self:
                if rec.state != 'draft' and not is_hr:
                    raise AccessError(_(
                        'Phiếu đã chốt — cần HR mở lại trước khi sửa.'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    'Không xoá được phiếu đã chốt/công bố (lưu vết đánh giá).'))
        return super().unlink()

    # ------------------------------------------------------------------
    # Chỉ số tự động — docs/CONG_THUC_DANH_GIA.md §4
    # ------------------------------------------------------------------
    PCT_TABLE = [(98, 5), (95, 4), (90, 3), (80, 2), (0, 1)]
    WORKLOAD_TABLE = [(100, 5), (85, 4), (70, 3), (50, 2), (0, 1)]

    def compute_metrics(self):
        """Tính lại chỉ số + điền điểm đề xuất cho dòng tự động (chỉ khi Nháp)."""
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec._collect_metrics()
            rec._apply_auto_scores()
        return True

    def _collect_metrics(self):
        self.ensure_one()
        if self.role_group == 'teacher':
            total, ok, late = self._teaching_units()
        else:
            total, ok, late = self._office_units()
        self.metric_total_units = total
        self.metric_ok_units = ok
        self.metric_late_count = late
        self.metric_punctual_pct = (ok / total * 100.0) if total else 0.0
        self.metric_leave_days = self._leave_days()
        valid, expiring, expired = self._cert_counts()
        self.metric_cert_valid = valid
        self.metric_cert_expiring = expiring
        self.metric_cert_expired = expired
        self.metrics_computed_on = fields.Datetime.now()

    def _teaching_units(self):
        """(tổng buổi dạy, buổi đạt, buổi trễ) — hocba.teaching.attendance."""
        self.ensure_one()
        recs = self.env['hocba.teaching.attendance'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('session_date', '>=', self.date_from),
            ('session_date', '<=', self.date_to),
            ('check_in', '!=', False),
        ])
        violated = recs.filtered(
            lambda r: r.out_of_window or r.out_of_zone or r.face_suspect)
        late = len(recs.filtered(lambda r: r.out_of_window))
        return len(recs), len(recs) - len(violated), late

    def _office_units(self):
        """(tổng ngày công, ngày đạt, ngày trễ) — hocba.attendance."""
        self.ensure_one()
        recs = self.env['hocba.attendance'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        ok = recs.filtered(
            lambda r: not r.late_minutes and not r.early_leave_minutes)
        late = len(recs.filtered(lambda r: r.late_minutes > 0))
        return len(recs), len(ok), late

    def _leave_days(self):
        """Ngày nghỉ phép đã duyệt giao với kỳ (chỉ hiển thị, không tính điểm)."""
        self.ensure_one()
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', datetime.combine(self.date_to, time.max)),
            ('date_to', '>=', datetime.combine(self.date_from, time.min)),
        ])
        return sum(leaves.mapped('number_of_days'))

    def _cert_counts(self):
        """(còn hạn, sắp hết hạn, hết hạn) trên chứng chỉ ĐÃ XÁC MINH."""
        self.ensure_one()
        skills = self.env['hr.employee.skill'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('x_cert_verified', '=', True),
        ])
        valid = expiring = expired = 0
        for s in skills:
            if s.x_cert_status == 'expired':
                expired += 1
            elif s.x_cert_status == 'expiring':
                expiring += 1
            else:
                valid += 1
        return valid, expiring, expired

    def _auto_score_for(self, source, max_score):
        """Điểm đề xuất cho một nguồn tự động; 0 = không đủ dữ liệu, để chấm tay."""
        self.ensure_one()
        if source == 'punctuality':
            if not self.metric_total_units:
                return 0
            return _bucket(self.metric_punctual_pct, self.PCT_TABLE)
        if source == 'workload':
            if self.role_group != 'teacher':
                return 0
            target = self._session_target()
            if not target:
                return 0
            pct = self.metric_total_units / target * 100.0
            return _bucket(pct, self.WORKLOAD_TABLE)
        if source == 'cert':
            total = (self.metric_cert_valid + self.metric_cert_expiring
                     + self.metric_cert_expired)
            if not total:
                return 1
            if self.metric_cert_expired:
                return 2
            if self.metric_cert_expiring:
                return 3
            return 5 if self.metric_cert_valid >= 2 else 4
        return 0

    def _session_target(self):
        """Chỉ tiêu buổi dạy quy đổi theo độ dài kỳ (mặc định 60 buổi/quý)."""
        self.ensure_one()
        base = float(self.env['ir.config_parameter'].sudo().get_param(
            'hocba_reviews.teacher_sessions_target', 60))
        return base * (PERIOD_MONTHS.get(self.period_type, 3) / 3.0)

    def _apply_auto_scores(self):
        """Ghi auto_score cho dòng tự động; dòng chưa bị sửa tay thì đồng bộ score."""
        self.ensure_one()
        for line in self.line_ids:
            if not line.is_auto:
                continue
            auto = self._auto_score_for(
                line.criteria_id.auto_source, line.max_score)
            line.auto_score = auto
            if not line.manual_override:
                line.score = auto

    # ------------------------------------------------------------------
    # Luồng trạng thái
    # ------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ chốt được phiếu đang ở trạng thái Nháp.'))
            if not rec.line_ids:
                raise UserError(_('Phiếu chưa có tiêu chí nào để chấm.'))
            if not any(l.score > 0 for l in rec.line_ids):
                raise UserError(_('Cần chấm điểm trước khi chốt phiếu.'))
            if not (rec.manager_note or '').strip():
                raise UserError(_(
                    'Cần nhập "Nhận xét của quản lý" trước khi chốt.'))
            rec.write({
                'state': 'confirmed',
                'confirmed_on': fields.Datetime.now(),
                'evaluator_id': rec.evaluator_id.id or self.env.user.id,
            })
            rec.employee_id.sudo().message_post(body=_(
                '📊 Đánh giá %(p)s: %(s).1f điểm — loại %(g)s.') % {
                    'p': rec.period_label,
                    's': rec.total_score,
                    'g': (rec.grade or '').upper(),
                })
        return True

    def action_publish(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Chỉ công bố được phiếu đã chốt.'))
            rec.write({
                'state': 'published',
                'published_on': fields.Datetime.now(),
            })
            rec._notify_employee()
        return True

    def action_reset_draft(self):
        if not self.env.su and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_('Chỉ HR Manager được mở lại phiếu đã chốt.'))
        for rec in self:
            rec.sudo().write({
                'state': 'draft', 'confirmed_on': False, 'published_on': False,
            })
        return True

    def _notify_employee(self):
        """Bắn thông báo in-app cho nhân viên khi kết quả được công bố."""
        self.ensure_one()
        user = self.employee_id.sudo().user_id
        if not user:
            return
        self.env['hb.notification'].sudo()._notify(
            user, 'review', 'review_published', 'info',
            _('Kết quả đánh giá %s') % self.period_label,
            _('Bạn được %(s).1f điểm — xếp loại %(g)s.') % {
                's': self.total_score, 'g': (self.grade or '').upper()},
            target_view='reviews', target_ref=self.id,
            dedup_key='review_published_%s' % self.id)

    # ------------------------------------------------------------------
    # Mở đợt hàng loạt
    # ------------------------------------------------------------------
    @api.model
    def open_period(self, role_group, period_type, year, index, employee_ids=None):
        """Tạo phiếu Nháp cho mọi NV đang làm việc thuộc nhóm (idempotent).
        Trả về {'created': n, 'skipped': n} — NV đã có phiếu kỳ đó bị bỏ qua."""
        Employee = self.env['hr.employee'].sudo()
        dom = [('active', '=', True)] + self.role_group_domain(role_group)
        if employee_ids is not None:
            dom.append(('id', 'in', list(employee_ids)))
        employees = Employee.search(dom)
        existing = set(self.sudo().search([
            ('employee_id', 'in', employees.ids),
            ('period_type', '=', period_type),
            ('period_year', '=', year),
            ('period_index', '=', index),
        ]).mapped('employee_id').ids)
        todo = [e for e in employees if e.id not in existing]
        if todo:
            self.sudo().create([{
                'employee_id': e.id,
                'role_group': role_group,
                'period_type': period_type,
                'period_year': year,
                'period_index': index,
            } for e in todo])
        return {'created': len(todo), 'skipped': len(existing)}


class HbPerformanceReviewLine(models.Model):
    _name = 'hb.performance.review.line'
    _description = 'Dòng chấm tiêu chí đánh giá'
    _order = 'sequence, id'

    review_id = fields.Many2one(
        'hb.performance.review', string='Phiếu đánh giá',
        required=True, ondelete='cascade', index=True)
    criteria_id = fields.Many2one(
        'hb.review.criteria', string='Tiêu chí', required=True,
        ondelete='restrict')
    sequence = fields.Integer(related='criteria_id.sequence', store=True)
    # weight/max_score SNAPSHOT lúc tạo phiếu — sửa cấu hình tiêu chí sau
    # không làm đổi phiếu đã chấm.
    weight = fields.Float(string='Trọng số')
    max_score = fields.Integer(string='Điểm tối đa')
    score = fields.Float(string='Điểm', default=0.0)
    auto_score = fields.Float(string='Điểm hệ thống đề xuất')
    is_auto = fields.Boolean(string='Chấm tự động')
    manual_override = fields.Boolean(
        string='Quản lý đã sửa đè',
        help='Bật khi người chấm sửa điểm khác đề xuất — lần tính lại chỉ số '
             'sau đó sẽ không ghi đè.')
    note = fields.Text(string='Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        """Thiếu weight/max_score/is_auto thì lấy snapshot từ tiêu chí."""
        for vals in vals_list:
            crit = self.env['hb.review.criteria'].sudo().browse(
                vals.get('criteria_id'))
            if not crit:
                continue
            vals.setdefault('weight', crit.weight)
            vals.setdefault('max_score', crit.max_score)
            vals.setdefault('is_auto', crit.auto_source != 'none')
        return super().create(vals_list)

    @api.constrains('score', 'max_score')
    def _check_score_range(self):
        for line in self:
            if line.score < 0 or (line.max_score and line.score > line.max_score):
                raise ValidationError(_(
                    'Điểm phải trong khoảng 0..%s.') % line.max_score)
