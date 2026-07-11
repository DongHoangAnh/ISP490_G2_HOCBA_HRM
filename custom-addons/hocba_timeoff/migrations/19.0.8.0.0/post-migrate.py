# Phase 6 — ép loại nghỉ phù hợp sang nửa ngày (half_day) trên các DB đã cài.
#
# Các record loại nghỉ được tạo lần đầu từ block <data noupdate="1">, nên Odoo
# lưu cờ noupdate=True và sẽ KHÔNG cập nhật request_unit khi nâng cấp dù file
# data đã đổi sang half_day. Migration này ghi thẳng để DB hiện hữu đồng bộ với
# cấu hình mới (bản cài mới lấy giá trị trực tiếp từ hr_leave_type_data.xml).
#
# CHẶN ĐÃ BIẾT: đổi `request_unit` làm Odoo recompute chuỗi
#   leave_type_request_unit → request_unit_half → _compute_date_from_to (date_from/
#   date_to) trên MỌI đơn `hr.leave` của loại đó, kể cả đơn lịch sử đang `validate`.
#   Constraint `_check_date_state` chặn ghi date_from/date_to khi đơn ở
#   validate1/validate → upgrade vỡ với "This modification is not allowed in the
#   current state." Hai constraint này đều bỏ qua khi context có
#   `leave_skip_state_check` / `leave_skip_date_check` (xem hr_leave.py), nên ta đặt
#   context đó RỒI flush ngay trong migration để recompute đơn cũ diễn ra an toàn,
#   trước khi flush "trần" ở cuối quá trình load module (nơi đã nổ lỗi).
from odoo import api, SUPERUSER_ID

HALF_DAY_TYPES = (
    'hocba_timeoff.hb_leave_type_annual',
    'hocba_timeoff.hb_leave_type_sick',
    'hocba_timeoff.hb_leave_type_compensatory',
    'hocba_timeoff.hb_leave_type_personal',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {
        'leave_skip_state_check': True,
        'leave_skip_date_check': True,
    })
    changed = False
    for xmlid in HALF_DAY_TYPES:
        lt = env.ref(xmlid, raise_if_not_found=False)
        if lt and lt.request_unit != 'half_day':
            lt.request_unit = 'half_day'
            changed = True
    if changed:
        # Recompute (date_from/date_to/duration của đơn cũ) ngay tại đây, dưới context
        # bỏ qua state-check, để flush cuối load module không còn gì dirty → không vỡ.
        env.flush_all()
