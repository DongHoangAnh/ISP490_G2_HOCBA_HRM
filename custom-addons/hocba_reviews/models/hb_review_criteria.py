from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

ROLE_GROUP_SEL = [
    ('teacher', 'Giảng viên'),
    ('office', 'Nhân viên văn phòng'),
]

# Nguồn dữ liệu tự chấm. Công thức từng nguồn: docs/CONG_THUC_DANH_GIA.md §4.
AUTO_SOURCE_SEL = [
    ('none', 'Chấm tay'),
    ('punctuality', 'Tự động — chuyên cần & đúng giờ'),
    ('workload', 'Tự động — khối lượng giảng dạy'),
    ('cert', 'Tự động — chuẩn chứng chỉ'),
]


class HbReviewCriteria(models.Model):
    """Tiêu chí đánh giá định kỳ, tách theo nhóm nhân sự.
    Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md"""
    _name = 'hb.review.criteria'
    _description = 'Tiêu chí đánh giá định kỳ'
    _order = 'role_group, sequence, id'

    name = fields.Char(string='Tiêu chí', required=True, translate=True)
    code = fields.Char(string='Mã', required=True)
    role_group = fields.Selection(
        ROLE_GROUP_SEL, string='Nhóm áp dụng', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    weight = fields.Float(
        string='Trọng số (%)', required=True, default=10.0,
        help='Tổng trọng số của mỗi nhóm nên bằng 100.')
    max_score = fields.Integer(string='Điểm tối đa', default=5, required=True)
    auto_source = fields.Selection(
        AUTO_SOURCE_SEL, string='Nguồn chấm', default='none', required=True,
        help='Khác "Chấm tay" = hệ thống tính sẵn điểm đề xuất từ dữ liệu vận '
             'hành; quản lý vẫn sửa đè được.')
    guideline = fields.Text(string='Hướng dẫn chấm')
    active = fields.Boolean(string='Hiệu lực', default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã tiêu chí phải duy nhất.',
    )

    @api.constrains('weight', 'max_score')
    def _check_ranges(self):
        for rec in self:
            if rec.weight < 0:
                raise ValidationError(_('Trọng số không được âm.'))
            if rec.max_score < 1:
                raise ValidationError(_('Điểm tối đa phải từ 1 trở lên.'))
