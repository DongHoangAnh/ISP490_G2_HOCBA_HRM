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


@tagged('post_install', '-at_install')
class TestAdminConfigPolicies(TransactionCase):

    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin P2', 'login': 'cfg_admin_p2',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})

    def _env(self):
        return self.env(user=self.admin_user)

    def test_list_returns_six_policies_with_choices(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_policies
        data = _config_list_policies(self._env())
        self.assertEqual(len(data['policies']), 6)
        ft = next(p for p in data['policies'] if p['employmentType'] == 'fulltime')
        self.assertEqual(ft['annualDays'], 12)
        self.assertEqual(ft['employmentLabel'], 'Nhân viên Toàn thời gian')
        self.assertTrue(data['leaveTypeChoices'])
        annual_id = self.env.ref('hocba_timeoff.hb_leave_type_annual').id
        self.assertIn(annual_id, [c['id'] for c in data['leaveTypeChoices']])
        ft_plan = self.env.ref('hocba_timeoff.hb_accrual_plan_annual_fulltime').id
        self.assertIn(ft_plan, [c['id'] for c in data['accrualPlanChoices']])

    def test_update_policy_writes(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        env = self._env()
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        sick_id = self.env.ref('hocba_timeoff.hb_leave_type_sick').id
        row = _config_save_policy(env, {
            'id': rule.id, 'name': 'CS Toàn thời gian (sửa)',
            'allocationMode': 'fixed', 'annualDays': 15,
            'accrualPlanId': False, 'notes': 'ghi chú mới',
            'leaveTypeIds': [sick_id]})
        self.assertEqual(row['annualDays'], 15)
        self.assertEqual(row['allocationMode'], 'fixed')
        self.assertEqual(rule.name, 'CS Toàn thời gian (sửa)')
        self.assertEqual(rule.leave_type_ids.ids, [sick_id])

    def test_employment_type_immutable(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        env = self._env()
        rule = self.env.ref('hocba_timeoff.hb_policy_ta')
        _config_save_policy(env, {
            'id': rule.id, 'name': rule.name, 'employmentType': 'fulltime',
            'allocationMode': rule.allocation_mode, 'annualDays': rule.annual_days,
            'leaveTypeIds': rule.leave_type_ids.ids})
        self.assertEqual(rule.employment_type, 'ta')

    def test_negative_annual_days_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': rule.id, 'name': 'x', 'allocationMode': 'none',
                'annualDays': -1, 'leaveTypeIds': []})

    def test_save_without_id_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'name': 'mới', 'allocationMode': 'none', 'annualDays': 0})

    def test_bad_allocation_mode_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': rule.id, 'name': 'x', 'allocationMode': 'weird',
                'annualDays': 0, 'leaveTypeIds': []})

    def test_bad_id_type_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': 'abc', 'name': 'x', 'allocationMode': 'none',
                'annualDays': 0, 'leaveTypeIds': []})

    def test_bad_accrual_plan_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        rule = self.env.ref('hocba_timeoff.hb_policy_fulltime')
        with self.assertRaises(ValidationError):
            _config_save_policy(self._env(), {
                'id': rule.id, 'name': 'x', 'allocationMode': 'accrual',
                'annualDays': 0, 'accrualPlanId': 99999999, 'leaveTypeIds': []})

    def test_nonmanaged_leave_type_dropped(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_policy
        env = self._env()
        rule = self.env.ref('hocba_timeoff.hb_policy_ta')
        managed_id = self.env.ref('hocba_timeoff.hb_leave_type_annual').id
        bad = self.env['hr.leave.type'].search(
            [('x_hb_managed', '=', False)], limit=1)
        self.assertTrue(bad, 'cần ít nhất 1 loại nghỉ non-managed để test')
        row = _config_save_policy(env, {
            'id': rule.id, 'name': rule.name, 'allocationMode': 'none',
            'annualDays': 0, 'leaveTypeIds': [managed_id, bad.id]})
        self.assertEqual(row['leaveTypeIds'], [managed_id])  # bad id bị loại
