"""19.0.2.5.0 — hb.interview.slot: 1 ứng viên → NHIỀU ứng viên / slot.

`applicant_id` (many2one) đổi thành `applicant_ids` (many2many, bảng
`hb_interview_slot_applicant_rel`). Odoo tạo bảng quan hệ mới nhưng KHÔNG tự
chuyển dữ liệu cũ, và cột `applicant_id` cũng không tự biến mất ⇒ ở đây chép
các slot đã đặt sang bảng quan hệ rồi mới bỏ cột cũ.

Idempotent: chạy lại không nhân đôi (INSERT ... ON CONFLICT DO NOTHING và các
lệnh IF EXISTS).
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'hb_interview_slot' AND column_name = 'applicant_id'
    """)
    if not cr.fetchone():
        return  # đã chuyển ở lần chạy trước

    # Bảng quan hệ do ORM tạo trước khi post-migrate chạy; thủ sẵn cho chắc.
    cr.execute("""
        CREATE TABLE IF NOT EXISTS hb_interview_slot_applicant_rel (
            slot_id      integer NOT NULL REFERENCES hb_interview_slot(id) ON DELETE CASCADE,
            applicant_id integer NOT NULL REFERENCES hr_applicant(id) ON DELETE CASCADE,
            PRIMARY KEY (slot_id, applicant_id)
        )
    """)
    cr.execute("""
        INSERT INTO hb_interview_slot_applicant_rel (slot_id, applicant_id)
        SELECT s.id, s.applicant_id
          FROM hb_interview_slot s
          JOIN hr_applicant a ON a.id = s.applicant_id
         WHERE s.applicant_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    moved = cr.rowcount

    cr.execute("ALTER TABLE hb_interview_slot DROP COLUMN IF EXISTS applicant_id")

    # state giờ là compute-store theo applicant_ids — đồng bộ lại ngay bằng SQL
    # (rẻ hơn recompute ORM, và bảo đảm slot cũ 'booked' mà không còn ứng viên
    # nào thì trở về 'available').
    cr.execute("""
        UPDATE hb_interview_slot s
           SET state = CASE WHEN EXISTS (
                   SELECT 1 FROM hb_interview_slot_applicant_rel r
                    WHERE r.slot_id = s.id)
               THEN 'booked' ELSE 'available' END
    """)
    cr.execute("""
        UPDATE hb_interview_slot s
           SET applicant_count = (
               SELECT count(*) FROM hb_interview_slot_applicant_rel r
                WHERE r.slot_id = s.id)
    """)

    cr.execute("SELECT count(*) FROM hb_interview_slot WHERE state = 'booked'")
    booked = cr.fetchone()[0]
    _logger.info('hocba_recruitments 2.5.0: chuyển %s lượt đặt sang many2many, '
                 '%s slot đang ở trạng thái Đã đặt', moved, booked)
