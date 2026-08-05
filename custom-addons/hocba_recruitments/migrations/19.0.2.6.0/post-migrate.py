"""19.0.2.6.0 — hr.job.x_teaching_level: Selection → Char (nhập tự do).

Ô "Trình độ giảng dạy" cũ chỉ có 4 lựa chọn cứng (hsk2/hsk3/tocfl/na). Nay đổi
thành Char để (1) liệt kê đủ các cấp HSK/HSKK/TOCFL trên thị trường dưới dạng
GỢI Ý và (2) cho phép gõ trình độ ngoài danh sách.

Cột trong Postgres vẫn là varchar nên không cần đổi kiểu — chỉ ghi lại giá trị:
mã cũ → nhãn hiển thị, riêng 'na' (N/A = không yêu cầu) → rỗng.

Idempotent: chỉ đụng đúng các mã cũ, chạy lại lần hai không còn dòng nào khớp.
"""
import logging

_logger = logging.getLogger(__name__)

# mã Selection cũ -> giá trị Char mới
RENAMES = {
    'hsk2': 'HSK2',
    'hsk3': 'HSK3',
    'tocfl': 'TOCFL',
}


def migrate(cr, version):
    if not version:
        return

    total = 0
    for old, new in RENAMES.items():
        cr.execute("""
            UPDATE hr_job SET x_teaching_level = %s
             WHERE x_teaching_level = %s
        """, (new, old))
        total += cr.rowcount

    # 'na' = không yêu cầu trình độ ⇒ để trống cho đúng nghĩa field mới.
    cr.execute("""
        UPDATE hr_job SET x_teaching_level = NULL
         WHERE x_teaching_level IN ('na', 'N/A')
    """)
    cleared = cr.rowcount

    _logger.info('hocba_recruitments 2.6.0: đổi %s vị trí sang nhãn trình độ mới, '
                 'xoá trống %s vị trí vốn để N/A', total, cleared)
