# Hợp nhất luồng duyệt: đổi mọi loại nghỉ Học Bá về 1 cấp ('hr') để HR Manager
# duyệt được mọi đơn qua SPA (controller chạy sudo dưới user_root).
#
# Lý do: trước đây Phép Năm / Không Lương / Thai Sản đặt 'both' → cần cấp 2 do
# Time Off Manager (hr_holidays.group_hr_holidays_manager) thực hiện; tài khoản
# HR Manager mặc định KHÔNG thuộc group đó trong Odoo 19, gây lỗi
# "You don't have the rights to apply second approval...". Loại 'manager' cũng
# gom về 'hr' để mọi loại duyệt đồng nhất qua tab "Chờ duyệt" của SPA.
#
# Block <data noupdate="1"> trong hr_leave_type_data.xml → Odoo KHÔNG tự update
# record cũ; migration này ghi đè thủ công các loại đang khác 'hr'.
from odoo import SUPERUSER_ID, api

HB_LEAVE_TYPE_XMLIDS = (
    'hocba_timeoff.hb_leave_type_annual',
    'hocba_timeoff.hb_leave_type_sick',
    'hocba_timeoff.hb_leave_type_unpaid',
    'hocba_timeoff.hb_leave_type_maternity',
    'hocba_timeoff.hb_leave_type_compensatory',
    'hocba_timeoff.hb_leave_type_personal',
    'hocba_timeoff.hb_leave_type_emergency',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in HB_LEAVE_TYPE_XMLIDS:
        lt = env.ref(xmlid, raise_if_not_found=False)
        if lt and lt.leave_validation_type != 'hr':
            lt.leave_validation_type = 'hr'
