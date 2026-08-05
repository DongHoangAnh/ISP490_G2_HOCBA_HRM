from odoo import api, fields, models
from odoo.exceptions import ValidationError

_TEACHING_DEPTS = frozenset(['Giảng viên', 'Trợ giảng'])

# Gợi ý trình độ cho ô "Trình độ" của vị trí tuyển dụng. Đây chỉ là DANH SÁCH
# GỢI Ý (field là Char, không phải Selection) — trung tâm gặp chứng chỉ lạ thì
# gõ thẳng, không phải chờ sửa code. Gồm đủ các cấp đang lưu hành trên thị
# trường: HSK 2.0 (1–6), HSK 3.0 cấp cao (7–9), HSKK khẩu ngữ và TOCFL.
HB_TEACHING_LEVELS = [
    'HSK1', 'HSK2', 'HSK3', 'HSK4', 'HSK5', 'HSK6',
    'HSK7', 'HSK8', 'HSK9', 'HSK7-9',
    'HSKK Sơ cấp', 'HSKK Trung cấp', 'HSKK Cao cấp',
    'TOCFL Band A', 'TOCFL Band B', 'TOCFL Band C', 'TOCFL',
]


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
    x_teaching_level = fields.Char(
        string='Trình độ',
        help='Yêu cầu trình độ tiếng Trung với vị trí Giảng viên / Trợ giảng. '
             'Chọn trong danh sách gợi ý hoặc gõ trình độ khác nếu cần. '
             'Để trống = không yêu cầu.',
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

    # ── Logic 3: Phòng Giảng viên / Trợ giảng bắt buộc điền trình độ ─────────
    # Field là Char nên "chưa điền" = rỗng, hoặc người dùng gõ N/A cho có lệ.
    @api.constrains('x_teaching_level', 'department_id')
    def _check_teaching_level_required(self):
        for rec in self:
            level = (rec.x_teaching_level or '').strip()
            if (rec.department_id
                    and rec.department_id.name in _TEACHING_DEPTS
                    and level.lower() in ('', 'na', 'n/a')):
                raise ValidationError(
                    'Phòng ban "%s" yêu cầu điền Trình độ cụ thể '
                    '(VD: HSK4, HSK7-9, TOCFL Band B…).' % rec.department_id.name
                )
