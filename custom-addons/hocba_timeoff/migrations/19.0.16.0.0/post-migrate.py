# Cho phép nghỉ NỬA NGÀY với "Nghỉ Không Lương" và "Nghỉ Khẩn Cấp".
#
# Hai loại này trước đây đặt request_unit='day' (chỉ nghỉ cả ngày). Đổi sang
# 'half_day' để NV chọn được buổi Sáng/Chiều (SPA tự hiện toggle theo
# requestUnit; logic chấm công nửa ngày đã hỗ trợ paid/unpaid am/pm).
#
# Block <data noupdate="1"> trong hr_leave_type_data.xml → Odoo KHÔNG tự update
# record cũ đã seed; migration này ghi đè thủ công.
from odoo import SUPERUSER_ID, api

HALF_DAY_XMLIDS = (
    'hocba_timeoff.hb_leave_type_unpaid',
    'hocba_timeoff.hb_leave_type_emergency',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in HALF_DAY_XMLIDS:
        lt = env.ref(xmlid, raise_if_not_found=False)
        if lt and lt.request_unit != 'half_day':
            lt.request_unit = 'half_day'
