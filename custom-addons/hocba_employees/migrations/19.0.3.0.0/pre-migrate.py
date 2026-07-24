# Migration 19.0.3.0.0 — F-006 rút gọn: bỏ vòng đời tài sản.
# Phải xoá các dòng lịch sử (đã thu hồi / đã chuyển giao) TRƯỚC khi ORM bỏ
# cột state; nếu để lại chúng sẽ được hiểu là "đang giữ" và đụng ràng buộc
# unique asset_code mới.
# Spec: docs/superpowers/specs/2026-07-24-asset-simplify-design.md
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'hr_employee_asset'
           AND column_name = 'state'
           AND table_schema = current_schema()
    """)
    if not cr.fetchone():
        return
    cr.execute("""
        DELETE FROM hr_employee_asset
         WHERE state IN ('returned', 'transferred')
    """)
    _logger.info('F-006: xoá %s dòng tài sản lịch sử.', cr.rowcount)
    # Khử trùng mã còn sót (dữ liệu bẩn) — giữ dòng cấp gần nhất, tức người
    # đang thực sự giữ. Liệt kê trước khi xoá: dữ liệu không khôi phục được.
    cr.execute("""
        SELECT a.asset_code, a.employee_id
          FROM hr_employee_asset a, hr_employee_asset b
         WHERE a.asset_code = b.asset_code
           AND (a.grant_date, a.id) < (b.grant_date, b.id)
    """)
    dups = cr.fetchall()
    if dups:
        _logger.warning(
            'F-006: xoá %s dòng trùng mã tài sản (mã → NV): %s',
            len(dups), ', '.join('%s → NV#%s' % d for d in dups))
        cr.execute("""
            DELETE FROM hr_employee_asset a
             USING hr_employee_asset b
             WHERE a.asset_code = b.asset_code
               AND (a.grant_date, a.id) < (b.grant_date, b.id)
        """)
