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

    def test_hb_leave_type_ids_matches_seeded(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        expected = set()
        for xmlid in HB_XMLIDS:
            expected.add(self.env.ref('hocba_timeoff.%s' % xmlid).id)
        self.assertEqual(set(_hb_leave_type_ids(self.env)), expected)

    def test_hb_leave_type_ids_excludes_unmanaged(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        other = self.env['hr.leave.type'].create({
            'name': 'Loại demo không thuộc HB', 'x_hb_managed': False})
        self.assertNotIn(other.id, _hb_leave_type_ids(self.env))

    def test_hb_leave_type_ids_includes_new_managed(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        new_managed = self.env['hr.leave.type'].create({
            'name': 'Loại HB tạo mới', 'x_hb_managed': True})
        self.assertIn(new_managed.id, _hb_leave_type_ids(self.env))

    def test_hb_leave_type_ids_excludes_archived(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self.assertIn(annual.id, _hb_leave_type_ids(self.env))
        annual.active = False
        self.assertNotIn(annual.id, _hb_leave_type_ids(self.env))
