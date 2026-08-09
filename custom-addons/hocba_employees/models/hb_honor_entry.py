from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

CATEGORY_SEL = [
    ('promotion', 'Bổ nhiệm / Thăng chức'),
    ('achievement', 'Thành tích'),
    ('tenure', 'Kỷ niệm gắn bó'),
    ('other', 'Khác'),
]


class HbHonorEntry(models.Model):
    """Một mục trên bảng vinh danh chung của công ty.

    Khách (họp 2026-08-07, 09:56): "bảng leadership của những người được vinh
    danh, hiển thị lên trang dashboard chung của tất cả mọi người".
    Spec: docs/superpowers/specs/2026-08-09-career-dashboard-honor-board-design.md
    """
    _name = 'hb.honor.entry'
    _description = 'Mục vinh danh trên dashboard chung'
    # rank KHÔNG nằm trong _order: rank=0 nghĩa là "không xếp hạng" nên nếu sắp
    # tăng dần nó sẽ leo lên trên cả hạng 1. Việc xếp hạng làm ở tầng payload.
    _order = 'date_awarded desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    category = fields.Selection(
        CATEGORY_SEL, string='Nhóm', default='achievement', required=True)
    title = fields.Char(string='Danh hiệu', required=True)
    description = fields.Text(string='Mô tả')
    date_awarded = fields.Date(
        string='Ngày vinh danh', required=True,
        default=fields.Date.context_today, index=True)
    # Kỳ vinh danh = tháng dương lịch. Khách hỏi "hiển thị bao lâu" → "đến lần
    # bầu tiếp theo"; hệ thống chưa có khái niệm "lần bầu" nên lấy tháng làm
    # chu kỳ, HR không phải mở/đóng kỳ bằng tay.
    period_key = fields.Char(
        string='Kỳ', compute='_compute_period_key', store=True, index=True)
    rank = fields.Integer(string='Hạng', default=0)
    source = fields.Selection(
        [('auto', 'Tự động'), ('manual', 'HR nhập')],
        string='Nguồn', default='manual', required=True)
    promotion_id = fields.Many2one(
        'hr.promotion.history', string='Mốc thăng tiến', ondelete='set null')
    active = fields.Boolean(default=True)

    # Một mốc thăng tiến chỉ được vinh danh một lần — chống trùng khi migration
    # backfill chạy lại. NULL không bị chặn (nhiều bản HR nhập tay vẫn tạo
    # được). Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _promotion_uniq = models.Constraint(
        'unique (promotion_id)',
        'Mốc thăng tiến này đã có trên bảng vinh danh.',
    )

    @api.depends('date_awarded')
    def _compute_period_key(self):
        for rec in self:
            d = rec.date_awarded
            rec.period_key = '%04d-%02d' % (d.year, d.month) if d else False

    @api.constrains('rank', 'title')
    def _check_rank_title(self):
        for rec in self:
            if rec.rank < 0:
                raise ValidationError(_('Hạng không được âm.'))
            if not (rec.title or '').strip():
                raise ValidationError(_('Danh hiệu không được để trống.'))
