# ============================================================
# Migration 19.0.4.0.0 — chuẩn hoá cấu hình loại nghỉ theo phân quyền mới.
#
# Bối cảnh: hr_leave_type_data.xml dùng noupdate="1" nên thay đổi cấu hình
# của các record ĐÃ tồn tại không tự áp khi nâng cấp. Ngoài ra Odoo chặn
# đổi requires_allocation qua ORM khi loại nghỉ đã phát sinh đơn/allocation
# (check_allocation_requirement_edit_validity) → buộc dùng SQL.
#
# Quy ước cuối: CHỈ "Nghỉ Phép Năm" trừ vào quỹ 12 ngày (requires_allocation),
# CHỈ "Nghỉ Không Lương" unpaid=True; mọi loại Học Bá khác = nghỉ tự do, có lương.
# ============================================================
from odoo import SUPERUSER_ID, api

# Các loại nghỉ thuộc module (theo xml_id).
HB_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def _ref_id(xmlid):
        rec = env.ref('hocba_timeoff.%s' % xmlid, raise_if_not_found=False)
        return rec.id if rec else None

    ids = {x: _ref_id(x) for x in HB_XMLIDS}
    owned = tuple(i for i in ids.values() if i)
    if not owned:
        return

    annual_id = ids['hb_leave_type_annual']
    unpaid_id = ids['hb_leave_type_unpaid']

    # SQL trực tiếp (né constraint ORM): chỉ Nghỉ Phép Năm cần allocation,
    # chỉ Nghỉ Không Lương unpaid; các loại còn lại nghỉ tự do, có lương.
    cr.execute(
        "UPDATE hr_leave_type "
        "SET requires_allocation = (id = %s), unpaid = (id = %s) "
        "WHERE id IN %s",
        (annual_id, unpaid_id, owned),
    )
