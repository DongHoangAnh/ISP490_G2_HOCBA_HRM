# Gỡ cơ chế "xung đột lịch dạy" cũ (BR-030/031/033 + Academic Manager), đã được
# luồng dạy thay mới (hocba.teaching.session + hocba.leave.session.resolution)
# thay thế. Cơ chế cũ dò model ảo teaching.session (không tồn tại) nên luôn no-op.
#
# Phải chạy PRE-migrate: khi gỡ file model, field x_schedule_conflict biến mất khỏi
# hr.leave; nhưng view cũ (vẫn còn trong DB từ lần cài trước) còn tham chiếu field
# này → validate combined arch của form hr.leave VỠ trước khi Odoo kịp dọn record
# mồ côi. Xoá sẵn các record cũ theo xml_id để arch hợp nhất không còn tham chiếu.
from odoo import SUPERUSER_ID, api

STALE_XMLIDS = (
    'hocba_timeoff.view_hr_leave_form_hb_schedule_conflict',  # view tham chiếu field cũ
    'hocba_timeoff.ir_cron_schedule_conflict_check',          # cron gọi method đã gỡ
    'hocba_timeoff.group_academic_manager',                   # nhóm chỉ cơ chế cũ dùng
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in STALE_XMLIDS:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.unlink()
