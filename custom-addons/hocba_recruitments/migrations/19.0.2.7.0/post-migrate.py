"""19.0.2.7.0 — gán ngược CV cũ vào đợt tuyển (hr_applicant.hb_request_id).

Trước bản này ứng viên chỉ biết mình ứng tuyển VỊ TRÍ nào (job_id), không biết
thuộc ĐỢT TUYỂN nào; số liệu theo dõi phải bắc cầu qua JD nên hai phiếu cùng một
vị trí thấy chung một bộ số. Cột mới gắn thẳng CV vào phiếu, còn dữ liệu cũ phải
đoán lại ở đây.

Luật đoán — "phiếu mở gần nhất TRƯỚC khi nhận CV":
  1. Trong các phiếu cùng job_id có date_request <= ngày nhận CV, lấy phiếu có
     date_request muộn nhất (hoà thì id lớn hơn = phiếu tạo sau).
  2. Không có phiếu nào mở trước đó (CV đến trước cả phiếu đầu tiên — dữ liệu
     nhập bù, chuyện thường) ⇒ lấy phiếu SỚM NHẤT của vị trí đó.
  3. Vị trí chưa từng có phiếu ⇒ để NULL.

Ngày nhận CV: date_received, thiếu thì create_date. Cả hai đều rỗng ⇒ chỉ còn
nhánh (2) áp dụng, vẫn ra kết quả hợp lý.

Idempotent: chỉ đụng dòng đang NULL, chạy lại lần hai không còn dòng nào khớp.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Subquery TƯƠNG QUAN chứ không phải FROM LATERAL: trong UPDATE, mệnh đề
    # FROM (kể cả LATERAL) không được tham chiếu ngược bảng đích — Postgres báo
    # "invalid reference to FROM-clause entry".
    cr.execute("""
        UPDATE hr_applicant a
           SET hb_request_id = (
                SELECT r.id
                  FROM hb_recruitment_request r
                 WHERE r.job_id = a.job_id
              ORDER BY -- (1) ưu tiên phiếu đã mở trước khi nhận CV, muộn nhất trước
                       (r.date_request IS NOT NULL
                        AND r.date_request <= COALESCE(
                            a.date_received, a.create_date::date)) DESC,
                       CASE WHEN r.date_request <= COALESCE(
                                 a.date_received, a.create_date::date)
                            THEN r.date_request END DESC NULLS LAST,
                       CASE WHEN r.date_request <= COALESCE(
                                 a.date_received, a.create_date::date)
                            THEN r.id END DESC NULLS LAST,
                       -- (2) không có phiếu nào mở trước ⇒ phiếu sớm nhất
                       r.date_request ASC NULLS LAST,
                       r.id ASC
                 LIMIT 1)
         WHERE a.hb_request_id IS NULL
           AND a.job_id IS NOT NULL
           AND EXISTS (SELECT 1 FROM hb_recruitment_request r
                        WHERE r.job_id = a.job_id)
    """)
    filled = cr.rowcount

    cr.execute("""
        SELECT COUNT(*) FROM hr_applicant
         WHERE hb_request_id IS NULL
    """)
    left = cr.fetchone()[0]

    _logger.info('hocba_recruitments 2.7.0: gán đợt tuyển cho %s CV cũ, '
                 'còn %s CV không quy được về phiếu nào (vị trí trống hoặc '
                 'vị trí chưa từng có phiếu yêu cầu).', filled, left)
