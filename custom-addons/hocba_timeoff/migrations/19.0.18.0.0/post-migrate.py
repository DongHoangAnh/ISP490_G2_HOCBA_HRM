# Seed cờ x_hb_managed cho 8 loại nghỉ chuẩn Học Bá trên DB ĐÃ CÀI.
# Block hr_leave_type_data.xml là noupdate="1" → Odoo KHÔNG tự set field mới
# vào record cũ; migration này ghi thủ công. Các loại nghỉ demo/khác giữ mặc
# định False (khi thêm cột) nên tự động bị ẩn khỏi SPA.
from odoo import SUPERUSER_ID, api

HB_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
    'hb_leave_type_teaching_off',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ids = []
    for xmlid in HB_XMLIDS:
        lt = env.ref('hocba_timeoff.%s' % xmlid, raise_if_not_found=False)
        if lt:
            ids.append(lt.id)
    if ids:
        cr.execute(
            "UPDATE hr_leave_type SET x_hb_managed = TRUE WHERE id IN %s",
            (tuple(ids),))
        env.invalidate_all()
