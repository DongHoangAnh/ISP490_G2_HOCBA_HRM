"""19.0.2.0.0 — thang mô tả hành vi (BARS) cho các tiêu chí chấm tay.

Trước bản này người chấm chỉ có một dòng "hướng dẫn chấm" nói tiêu chí đo cái
gì, nhưng không nói hành vi thế nào thì 5, thế nào thì 3 — mỗi quản lý tự hiểu
một kiểu nên điểm giữa các phòng không so sánh được với nhau.

Ba cột mới (anchor_top/mid/low) chứa mốc hành vi quan sát được. Bản ghi tiêu chí
nằm trong file data noupdate=1 (để giữ trọng số HR đã chỉnh), nên thêm giá trị
vào XML sẽ KHÔNG áp dụng cho DB đang chạy — phải backfill ở đây.

Idempotent: chỉ ghi vào ô đang rỗng, chạy lại không đè nội dung HR đã sửa.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.hocba_reviews.models.hb_review_criteria import (
    seed_default_anchors,
)

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    filled = seed_default_anchors(env)
    _logger.info('hocba_reviews 2.0.0: điền thang mô tả hành vi cho %s tiêu chí.',
                 filled)
