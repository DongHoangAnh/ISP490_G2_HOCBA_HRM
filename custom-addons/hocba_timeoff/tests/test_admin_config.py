# ============================================================
# Test — Trung tâm Cấu hình Time Off (Admin), Phase 1: Loại nghỉ.
# Theo quy ước repo: TransactionCase gọi thẳng hàm cấp module của controller
# với self.env(user=...). Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError

HB_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
    'hb_leave_type_teaching_off',
)


@tagged('post_install', '-at_install')
class TestAdminConfigLeaveTypes(TransactionCase):

    def test_seeded_types_are_managed(self):
        for xmlid in HB_XMLIDS:
            lt = self.env.ref('hocba_timeoff.%s' % xmlid)
            self.assertTrue(
                lt.x_hb_managed,
                'Loại nghỉ %s phải có x_hb_managed=True' % xmlid)
