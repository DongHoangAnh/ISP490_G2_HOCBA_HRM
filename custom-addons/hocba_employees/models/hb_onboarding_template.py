from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Khớp selection x_position_type trên hr.employee
POSITION_TYPES = ('manager', 'staff', 'ctv', 'freelancer', 'advisor')


class HbOnboardingTemplate(models.Model):
    """Template quy trình nhận việc/thử việc — admin (HR Manager) cấu hình
    danh sách bước động thay cho 3 cổng + thử giảng hard-code.
    Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md"""
    _name = 'hb.onboarding.template'
    _description = 'Template quy trình nhận việc / thử việc'
    _order = 'sequence, id'

    name = fields.Char(string='Tên quy trình', required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        string='Ưu tiên', default=10,
        help='NV khớp nhiều template → lấy template sequence nhỏ nhất.')
    apply_position_types = fields.Char(
        string='Loại vị trí áp dụng',
        help='CSV các giá trị x_position_type (vd "staff,manager"). '
             'Rỗng = mọi loại vị trí.')
    apply_work_form = fields.Selection(
        [('offline', 'Offline'), ('online', 'Online'), ('any', 'Tất cả')],
        string='Hình thức làm việc', default='any', required=True)
    apply_employee_type_ids = fields.Many2many(
        'hocba.employee.type', string='Loại nhân viên áp dụng',
        help='Rỗng = mọi loại nhân viên.')
    step_ids = fields.One2many(
        'hb.onboarding.template.step', 'template_id', string='Các bước')

    @api.model_create_multi
    def create(self, vals_list):
        """Template mới không truyền sequence → vào CUỐI danh sách (max+10)
        — mặc định an toàn: không cướp quyền quy trình cũ, muốn thắng thì
        kéo lên (spec 2026-07-20-onboarding-priority-reorder)."""
        bottom = None
        for vals in vals_list:
            if 'sequence' not in vals:
                if bottom is None:
                    cur = self.sudo().with_context(
                        active_test=False).search([]).mapped('sequence')
                    bottom = max(cur) if cur else 0
                bottom += 10
                vals['sequence'] = bottom
        return super().create(vals_list)

    @api.constrains('step_ids')
    def _check_has_steps(self):
        for tpl in self:
            if not tpl.step_ids:
                raise ValidationError(_(
                    'Quy trình "%s" phải có ít nhất 1 bước.') % tpl.name)

    @api.constrains('apply_position_types')
    def _check_position_types(self):
        for tpl in self:
            if not tpl.apply_position_types:
                continue
            vals = [p.strip() for p in tpl.apply_position_types.split(',')
                    if p.strip()]
            bad = [v for v in vals if v not in POSITION_TYPES]
            if bad:
                raise ValidationError(_(
                    'Loại vị trí không hợp lệ: %(bad)s (chấp nhận: %(ok)s).')
                    % {'bad': ', '.join(bad), 'ok': ', '.join(POSITION_TYPES)})

    # ------------------------------------------------------------------
    # Matching — gán tự động theo 3 tiêu chí (AND, tiêu chí rỗng = khớp)
    # ------------------------------------------------------------------
    def _matches(self, emp):
        """Template có áp dụng cho NV emp không."""
        self.ensure_one()
        if self.apply_position_types:
            allowed = {p.strip() for p in self.apply_position_types.split(',')
                       if p.strip()}
            if (emp.x_position_type or '') not in allowed:
                return False
        if self.apply_work_form != 'any' \
                and emp.x_work_form != self.apply_work_form:
            return False
        if self.apply_employee_type_ids \
                and emp.x_employee_type_id not in self.apply_employee_type_ids:
            return False
        return True

    @api.model
    def _match_for_employee(self, emp):
        """Template active khớp emp, ưu tiên sequence nhỏ nhất; rỗng nếu không."""
        for tpl in self.search([]):
            if tpl._matches(emp):
                return tpl
        return self.browse()

    @api.model
    def action_reorder(self, ordered_ids):
        """Ghi lại sequence theo thứ tự danh sách người dùng kéo-thả
        (trên → dưới = 10, 20, 30…). Thứ tự này quyết định quy trình nào
        giành quyền khi 1 NV khớp nhiều quy trình."""
        templates = self.browse(ordered_ids)
        missing = set(ordered_ids) - set(templates.exists().ids)
        if missing:
            raise ValidationError(_(
                'Quy trình không tồn tại: %s') % ', '.join(map(str, missing)))
        for pos, tpl_id in enumerate(ordered_ids):
            self.browse(tpl_id).write({'sequence': (pos + 1) * 10})
        return True

    @api.model
    def action_assign_pending(self):
        """Gán quy trình cho mọi NV thử việc CHƯA có bước (tạo trước khi
        template phù hợp tồn tại). Trả bộ đếm cho FE báo kết quả:
        assigned / noMatch (không khớp template nào) / noStart (thiếu ngày
        bắt đầu thử việc — không tính được hạn)."""
        pending = self.env['hr.employee'].sudo().search([
            ('x_employment_status', '=', 'probation'),
            ('x_onboarding_step_ids', '=', False)])
        assigned = no_match = no_start = 0
        for emp in pending:
            if not emp.x_probation_start:
                no_start += 1
                continue
            if emp._hocba_assign_onboarding():
                assigned += 1
            else:
                no_match += 1
        return {'assigned': assigned, 'noMatch': no_match,
                'noStart': no_start}


class HbOnboardingTemplateStep(models.Model):
    _name = 'hb.onboarding.template.step'
    _description = 'Bước mẫu trong template nhận việc'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'hb.onboarding.template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên bước', required=True)
    step_type = fields.Selection(
        [('task', 'Việc cần làm'), ('evaluation', 'Đánh giá')],
        string='Loại bước', default='task', required=True)
    due_days = fields.Integer(
        string='Hạn (+N ngày)', default=0,
        help='Hạn = ngày bắt đầu thử việc + N ngày. 0 = không hạn.')
    pass_completes = fields.Boolean(
        string='Đạt → lên chính thức',
        help='Chỉ bước Đánh giá: Đạt sẽ chuyển NV lên Chính thức, '
             'bỏ qua các bước sau.')
    is_extension = fields.Boolean(
        string='Bước gia hạn',
        help='Chỉ bước Đánh giá: chỉ kích hoạt khi bước đánh giá liền '
             'trước chọn "Gia hạn".')
    is_independent = fields.Boolean(
        string='Không ràng buộc thứ tự',
        help='Chỉ bước Việc cần làm: bước mở ngay từ lúc gán quy trình, làm '
             'lúc nào cũng được, không chặn và không bị chặn bởi chuỗi.')
    auto_action = fields.Selection(
        [('none', 'Không'), ('grant_assets', 'Tự cấp tài sản mặc định')],
        string='Automation', default='none', required=True,
        help='Chỉ bước Việc cần làm: bước mở → chạy automation rồi tự '
             'hoàn thành.')
    note = fields.Text(string='Hướng dẫn')

    @api.constrains('step_type', 'pass_completes', 'is_extension',
                    'is_independent', 'auto_action', 'due_days', 'sequence')
    def _check_step_flags(self):
        for step in self:
            if step.due_days < 0:
                raise ValidationError(_('Hạn (+N ngày) không được âm.'))
            if step.is_independent and step.step_type != 'task':
                raise ValidationError(_(
                    'Cờ "Không ràng buộc thứ tự" chỉ dùng cho bước Việc '
                    'cần làm — các bước Đánh giá phải chạy tuần tự.'))
            if step.is_independent and step.auto_action != 'none':
                raise ValidationError(_(
                    'Bước "không ràng buộc thứ tự" mở ngay từ đầu nên không '
                    'được đặt Automation — nếu không nó sẽ tự chạy ngày đầu.'))
            if step.step_type != 'evaluation' \
                    and (step.pass_completes or step.is_extension):
                raise ValidationError(_(
                    'Cờ "Đạt → lên chính thức" / "Bước gia hạn" chỉ dùng '
                    'cho bước Đánh giá.'))
            if step.step_type != 'task' and step.auto_action != 'none':
                raise ValidationError(_(
                    'Automation chỉ dùng cho bước Việc cần làm.'))
            if step.is_extension:
                sibs = step.template_id.step_ids.sorted(
                    lambda s: (s.sequence, s.id))
                idx = list(sibs).index(step)
                if idx == 0 or sibs[idx - 1].step_type != 'evaluation':
                    raise ValidationError(_(
                        'Bước gia hạn "%s" phải đứng ngay sau một bước '
                        'Đánh giá.') % step.name)
