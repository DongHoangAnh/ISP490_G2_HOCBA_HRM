from odoo import fields, models


class HrPromotionHistory(models.Model):
    """Nối bản ghi thăng tiến với phiếu đánh giá làm căn cứ.

    Trường này KHÔNG đặt được trên model gốc trong hocba_employees:
    hocba_reviews đã depends vào hocba_employees, nên trỏ ngược lại sẽ tạo
    vòng phụ thuộc. Đặt ở hocba_hrm (depends cả hai) là chỗ duy nhất hợp lệ
    mà không phải sửa module của Việt.
    Spec: docs/superpowers/specs/
    2026-08-12-gop-danh-gia-thang-tien-vao-reviews-design.md §2
    """
    _inherit = 'hr.promotion.history'

    review_id = fields.Many2one(
        'hb.performance.review', string='Phiếu đánh giá căn cứ',
        ondelete='set null', index=True,
        help='Đợt đánh giá định kỳ dẫn tới quyết định thăng tiến này.')
