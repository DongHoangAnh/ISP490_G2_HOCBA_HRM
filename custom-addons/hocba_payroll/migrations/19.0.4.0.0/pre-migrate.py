# -*- coding: utf-8 -*-
"""Bỏ ràng buộc unique(code) đã lỗi thời trên hb.bank.format.

Từ 19.0.3.0.0 (commit c3813cd), model hb.bank.format gộp thêm "danh sách ngân
hàng tham chiếu" (trước đây là model riêng hb.mb.bank.entry). Danh sách này ở
mức CHI NHÁNH nên nhiều bản ghi dùng chung một `code` (SHBVN, VID, Woori...),
và 3 ngân hàng VCB/TCB/MB vừa có bản ghi cấu hình format vừa có bản ghi tham
chiếu. Vì vậy `code` KHÔNG còn là khoá duy nhất và ràng buộc
`_code_unique = models.Constraint('unique (code)', ...)` đã bị bỏ khỏi model.

Tuy nhiên các DB cài trước đó (vd `hocba_hrm` dùng chung) vẫn còn ràng buộc vật
lý `hb_bank_format_code_unique` trong Postgres. Khi upgrade, Odoo nạp data file
TRƯỚC khi dọn constraint lỗi thời, nên INSERT bản ghi tham chiếu trùng code sẽ
báo "duplicate key value violates unique constraint hb_bank_format_code_unique"
và làm hỏng toàn bộ quá trình load/upgrade.

Pre-migration chạy trước khi nạp data → xoá ràng buộc để data nạp được. Lệnh
idempotent (IF EXISTS) nên an toàn nếu chạy lại hoặc trên DB đã sạch constraint.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # version là False khi cài mới (khi đó không có gì để dọn); chỉ chạy khi upgrade.
    if not version:
        return

    cr.execute(
        "ALTER TABLE hb_bank_format "
        "DROP CONSTRAINT IF EXISTS hb_bank_format_code_unique"
    )

    # Xoá luôn bản ghi theo dõi trong ir_model_constraint (nếu còn) để Odoo không
    # thử thao tác lại một ràng buộc đã không còn khai báo trong model.
    cr.execute(
        "DELETE FROM ir_model_constraint "
        "WHERE name = 'hb_bank_format_code_unique'"
    )

    _logger.info(
        "hocba_payroll: da bo rang buoc loi thoi hb_bank_format_code_unique "
        "tren hb.bank.format (code khong con la khoa duy nhat)."
    )
