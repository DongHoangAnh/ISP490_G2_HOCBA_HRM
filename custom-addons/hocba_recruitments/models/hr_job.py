from odoo import api, fields, models
from odoo.exceptions import ValidationError

_TEACHING_DEPTS = frozenset(['Giảng viên', 'Trợ giảng'])


class HrJobHocBaExt(models.Model):
    _inherit = 'hr.job'

    x_published = fields.Boolean(
        string='Đăng tuyển',
        default=False,
        tracking=True,
        help='Đánh dấu vị trí đang được đăng tuyển. Hiển thị badge PUBLISHED xanh trên Kanban.',
    )
    recruitment_status = fields.Selection(
        selection=[
            ('recruiting', 'Đang tuyển'),
            ('stopped', 'Dừng tuyển'),
        ],
        string='Trạng thái tuyển',
        default='recruiting',
        tracking=True,
    )
    jd_google_link = fields.Char(
        string='Link JD',
        help='Google Docs / Drive link chứa Job Description.',
    )
    x_teaching_level = fields.Selection(
        selection=[
            ('hsk2', 'HSK2'),
            ('hsk3', 'HSK3'),
            ('tocfl', 'TOCFL'),
            ('na', 'N/A'),
        ],
        string='Trình độ giảng dạy',
        default='na',
        help='Yêu cầu trình độ tiếng Trung với vị trí Giảng viên / Trợ giảng.',
    )
    x_required_sessions_per_week = fields.Integer(
        string='Số buổi/tuần tối thiểu',
        default=0,
    )
    x_requires_teaching_level = fields.Boolean(
        compute='_compute_x_requires_teaching_level',
        store=False,
    )

    @api.depends('department_id', 'department_id.name')
    def _compute_x_requires_teaching_level(self):
        for rec in self:
            rec.x_requires_teaching_level = bool(
                rec.department_id and rec.department_id.name in _TEACHING_DEPTS
            )

    def action_toggle_published(self):
        for rec in self:
            rec.x_published = not rec.x_published

    # ── Đồng bộ publish ↔ trạng thái tuyển (mọi cửa ghi) ─────────────────────
    # Đổi cờ publish từ BẤT KỲ đâu (SPA, backend, công tắc Publish trên
    # website) → gương 2 cờ is_published/x_published với nhau và khớp
    # trạng thái: đăng → Đang tuyển, ngừng đăng → Dừng tuyển.
    # Trạng thái truyền tường minh trong cùng write vẫn được tôn trọng.
    def write(self, vals):
        pub = None
        if 'is_published' in vals:
            pub = bool(vals['is_published'])
        elif 'x_published' in vals:
            pub = bool(vals['x_published'])
        if pub is not None:
            vals = dict(vals, x_published=pub)
            if 'is_published' in self._fields:
                vals['is_published'] = pub
            vals.setdefault('recruitment_status',
                            'recruiting' if pub else 'stopped')
        return super().write(vals)

    # ── Logic 2: Kiểm tra trùng lặp tên vị trí trong cùng phòng ban ──────────
    @api.constrains('name', 'department_id', 'active')
    def _check_duplicate_position(self):
        for rec in self:
            if not rec.active:
                continue
            domain = [
                ('name', '=', rec.name),
                ('department_id', '=', rec.department_id.id),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    'Vị trí "%s" đã tồn tại trong phòng ban "%s". Vui lòng kiểm tra lại.' % (
                        rec.name, rec.department_id.name or '',
                    )
                )

    # ── Logic 3: Phòng Giảng viên / Trợ giảng bắt buộc chọn trình độ ─────────
    @api.constrains('x_teaching_level', 'department_id')
    def _check_teaching_level_required(self):
        for rec in self:
            if (rec.department_id
                    and rec.department_id.name in _TEACHING_DEPTS
                    and rec.x_teaching_level == 'na'):
                raise ValidationError(
                    'Phòng ban "%s" yêu cầu chọn Trình độ giảng dạy cụ thể (HSK2 / HSK3 / TOCFL).' % rec.department_id.name
                )
