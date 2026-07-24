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

    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin', 'login': 'cfg_admin',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})
        self.hr_mgr_user = self.env['res.users'].create({
            'name': 'Cfg HRM', 'login': 'cfg_hrm',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

    def _admin_env(self):
        return self.env(user=self.admin_user)

    def test_is_admin_gate(self):
        from odoo.addons.hocba_timeoff.controllers.config import _is_admin
        self.assertTrue(_is_admin(self._admin_env()))
        self.assertFalse(_is_admin(self.env(user=self.hr_mgr_user)))

    def test_list_returns_eight_managed(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_leave_types
        rows = _config_list_leave_types(self._admin_env())
        self.assertEqual(len(rows), len(HB_XMLIDS))
        annual = next(r for r in rows
                      if r['id'] == self.env.ref('hocba_timeoff.hb_leave_type_annual').id)
        self.assertTrue(annual['requiresAllocation'])
        self.assertEqual(annual['requestUnit'], 'half_day')

    def test_create_leave_type_appears(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        env = self._admin_env()
        row = _config_save_leave_type(env, {
            'name': 'Nghỉ Thử Nghiệm', 'requiresAllocation': False,
            'unpaid': False, 'validationType': 'hr', 'requestUnit': 'day',
            'supportDocument': False, 'isEmergency': False, 'color': 5})
        self.assertTrue(row['id'])
        lt = self.env['hr.leave.type'].browse(row['id'])
        self.assertTrue(lt.x_hb_managed)
        self.assertIn(row['id'], _hb_leave_type_ids(self.env))

    def test_update_leave_type_writes(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        env = self._admin_env()
        annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        row = _config_save_leave_type(env, {
            'id': annual.id, 'name': 'Phép Năm (đã sửa)',
            'requiresAllocation': True, 'unpaid': False,
            'validationType': 'both', 'requestUnit': 'half_day',
            'supportDocument': False, 'isEmergency': False, 'color': 10})
        self.assertEqual(row['name'], 'Phép Năm (đã sửa)')
        self.assertEqual(row['validationType'], 'both')
        self.assertEqual(annual.leave_validation_type, 'both')

    def test_toggle_archives_and_hides(self):
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_leave_type, _config_toggle_leave_type)
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        env = self._admin_env()
        row = _config_save_leave_type(env, {
            'name': 'Nghỉ Tạm', 'requiresAllocation': False, 'unpaid': False,
            'validationType': 'hr', 'requestUnit': 'day',
            'supportDocument': False, 'isEmergency': False, 'color': 3})
        _config_toggle_leave_type(env, row['id'], False)
        self.assertNotIn(row['id'], _hb_leave_type_ids(self.env))

    def test_save_empty_name_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        with self.assertRaises(ValidationError):
            _config_save_leave_type(self._admin_env(), {'name': '   '})

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

    def test_second_allocation_type_rejected(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        # Nghỉ Phép Năm (seed) đã có requires_allocation=True và đang active.
        with self.assertRaises(ValidationError):
            _config_save_leave_type(self._admin_env(), {
                'name': 'Quỹ Phép Thứ Hai', 'requiresAllocation': True,
                'unpaid': False, 'validationType': 'hr', 'requestUnit': 'day',
                'supportDocument': False, 'isEmergency': False, 'color': 1})

    def test_second_unpaid_type_rejected(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        # Nghỉ Không Lương (seed) đã có unpaid=True và đang active.
        with self.assertRaises(ValidationError):
            _config_save_leave_type(self._admin_env(), {
                'name': 'Không Lương Thứ Hai', 'requiresAllocation': False,
                'unpaid': True, 'validationType': 'hr', 'requestUnit': 'day',
                'supportDocument': False, 'isEmergency': False, 'color': 1})

    def test_edit_allocation_type_keeps_itself(self):
        # Sửa chính loại Phép Năm mà vẫn giữ requires_allocation=True phải OK
        # (không tự xung đột với chính nó).
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        row = _config_save_leave_type(self._admin_env(), {
            'id': annual.id, 'name': 'Nghỉ Phép Năm', 'requiresAllocation': True,
            'unpaid': False, 'validationType': 'hr', 'requestUnit': 'half_day',
            'supportDocument': False, 'isEmergency': False, 'color': 10})
        self.assertTrue(row['requiresAllocation'])

    def test_allocation_flag_ok_when_existing_archived(self):
        # Nếu loại giữ cờ đang TẮT thì được phép tạo loại allocation mới đang bật.
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_leave_type, _config_toggle_leave_type)
        annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        _config_toggle_leave_type(self._admin_env(), annual.id, False)  # archive Annual
        row = _config_save_leave_type(self._admin_env(), {
            'name': 'Quỹ Phép Mới', 'requiresAllocation': True, 'unpaid': False,
            'validationType': 'hr', 'requestUnit': 'day',
            'supportDocument': False, 'isEmergency': False, 'color': 2})
        self.assertTrue(row['requiresAllocation'])
        # Bật lại Annual bây giờ phải bị chặn (sẽ thành 2 loại allocation active).
        with self.assertRaises(ValidationError):
            _config_toggle_leave_type(self._admin_env(), annual.id, True)
