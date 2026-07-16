# Cho phép nghỉ NỬA NGÀY với "Nghỉ Không Lương" và "Nghỉ Khẩn Cấp".
#
# Hai loại này trước đây đặt request_unit='day' (chỉ nghỉ cả ngày). Đổi sang
# 'half_day' để NV chọn được buổi Sáng/Chiều (SPA tự hiện toggle theo
# requestUnit; logic chấm công nửa ngày đã hỗ trợ paid/unpaid am/pm).
#
# Block <data noupdate="1"> trong hr_leave_type_data.xml → Odoo KHÔNG tự update
# record cũ đã seed; migration này ghi đè thủ công.
#
# PHẢI dùng SQL trực tiếp (không qua ORM write): đổi request_unit qua ORM sẽ
# đánh dấu recompute number_of_days/request_unit_half cho MỌI đơn cũ của loại
# này; đơn đã duyệt/từ chối vướng _check_date_state ("không được sửa đơn ở
# trạng thái này") → vỡ upgrade trên DB đã có dữ liệu. SQL chỉ đổi cấu hình
# loại nghỉ, giữ nguyên giá trị lịch sử của đơn cũ (đúng nghiệp vụ: đơn cũ vẫn
# là đơn cả ngày); chỉ đơn tạo MỚI mới tính nửa ngày.
from odoo import SUPERUSER_ID, api

HALF_DAY_XMLIDS = (
    'hocba_timeoff.hb_leave_type_unpaid',
    'hocba_timeoff.hb_leave_type_emergency',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ids = []
    for xmlid in HALF_DAY_XMLIDS:
        lt = env.ref(xmlid, raise_if_not_found=False)
        if lt:
            ids.append(lt.id)
    if ids:
        cr.execute(
            "UPDATE hr_leave_type SET request_unit = 'half_day' "
            "WHERE id IN %s AND request_unit != 'half_day'",
            (tuple(ids),))
        env.invalidate_all()
