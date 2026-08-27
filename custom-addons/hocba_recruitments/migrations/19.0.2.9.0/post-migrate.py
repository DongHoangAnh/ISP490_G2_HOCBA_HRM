"""19.0.2.9.0 — gỡ hẳn CRON-REC-002 ("Qua giờ PV → bước Kết quả phỏng vấn").

Yêu cầu 2026-08-26: không cần cron quét slot phỏng vấn nữa. Bước Phỏng vấn →
Kết quả phỏng vấn nay chỉ chạy khi HR điền Kết quả PV (hr_applicant.write).

Vì sao phải xoá bằng migration thay vì chỉ bỏ record khỏi ir_cron_data.xml:
`_process_end` của Odoo chỉ dọn bản ghi mồ côi khi `COALESCE(noupdate,false)`
là false — cron này khai trong khối `noupdate="1"` (để admin đổi giờ chạy không
bị upgrade ghi đè), nên nâng cấp module KHÔNG đụng tới nó. Bỏ XML mà không chạy
đoạn này thì cron vẫn nằm lại trong DB cũ và 30 phút một lần lại gọi
`model._cron_advance_past_interviews()` — method đã bị xoá ⇒ cron nổ lỗi nền,
Odoo tự tắt sau vài lần và để lại log đỏ.

Idempotent: DB nào không có cron (cài mới sau bản này) thì không làm gì.
"""
import logging

_logger = logging.getLogger(__name__)

XMLID = 'cron_recruitment_interview_passed'


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'hocba_recruitments' AND name = %s AND model = 'ir.cron'
    """, (XMLID,))
    row = cr.fetchone()
    if not row:
        _logger.info('hocba_recruitments 2.9.0: không có CRON-REC-002 để gỡ.')
        return

    cron_id = row[0]
    # ir.cron nằm trên ir.actions.server (delegation inherits) — xoá dòng cha
    # cùng lúc, không thì còn lại một action server mồ côi.
    cr.execute("SELECT ir_actions_server_id FROM ir_cron WHERE id = %s", (cron_id,))
    server_action = cr.fetchone()
    cr.execute("DELETE FROM ir_cron WHERE id = %s", (cron_id,))
    if server_action and server_action[0]:
        cr.execute("DELETE FROM ir_act_server WHERE id = %s", (server_action[0],))
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'hocba_recruitments' AND name = %s AND model = 'ir.cron'
    """, (XMLID,))

    _logger.info('hocba_recruitments 2.9.0: đã gỡ CRON-REC-002 (ir.cron id=%s).',
                 cron_id)
