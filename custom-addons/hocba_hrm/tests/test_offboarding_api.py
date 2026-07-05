from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.hocba_hrm.controllers.main import _emp_scope_domain


@tagged('post_install', '-at_install')
class TestOffboardingScope(TransactionCase):
    def setUp(self):
        super().setUp()
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Off', 'login': 'off_api_hr',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_manager').id])]})
        self.emp = self.env['hr.employee'].create({
            'name': 'API Off Emp', 'identification_id': '014444444401'})

    def test_hr_scope_sees_offboarding(self):
        rec = self.env['hocba.offboarding'].create({
            'employee_id': self.emp.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        env = self.env(user=self.hr_user)
        # HR Manager: _emp_scope_domain trả [] → thấy mọi nhân viên
        self.assertEqual(_emp_scope_domain(env), [])
        scope_emp_ids = env['hr.employee'].sudo().search(
            _emp_scope_domain(env)).ids
        found = env['hocba.offboarding'].sudo().search(
            [('employee_id', 'in', scope_emp_ids)])
        self.assertIn(rec.id, found.ids)


@tagged('post_install', '-at_install')
class TestOffboardingApiJson(TransactionCase):
    """Enrichment JSON + scope managed (gồm parent_id) cho SPA."""
    def setUp(self):
        super().setUp()
        from odoo.addons.hocba_hrm.controllers.main import HocBaHRM
        self.ctrl = HocBaHRM()
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Json', 'login': 'offj_hr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.mgr_user = self.env['res.users'].create({
            'name': 'ParentMgr', 'login': 'offj_pmgr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'ParentMgr Emp', 'identification_id': '015555550001',
            'user_id': self.mgr_user.id})
        self.staff_user = self.env['res.users'].create({
            'name': 'StaffJson', 'login': 'offj_staff',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.staff = self.env['hr.employee'].create({
            'name': 'StaffJson Emp', 'identification_id': '015555550002',
            'parent_id': self.mgr_emp.id, 'user_id': self.staff_user.id})
        self.rec = self.env['hocba.offboarding'].with_user(self.staff_user).create({
            'employee_id': self.staff.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        self.rec.action_submit()

    def _json(self, user):
        return self.ctrl._offb_json(
            self.env(user=user)['hocba.offboarding'].browse(self.rec.id))

    def test_json_state_label_and_flags_parent_mgr(self):
        d = self._json(self.mgr_user)
        self.assertEqual(d['stateLabel'], 'Chờ quản lý duyệt')
        self.assertEqual(d['stateKind'], 'amber')
        self.assertTrue(d['canMgrApprove'])
        self.assertFalse(d['canHrApprove'])
        self.assertTrue(d['canRefuse'])
        self.assertFalse(d['canCancel'])

    def test_json_flags_staff_own(self):
        d = self._json(self.staff_user)
        self.assertFalse(d['canMgrApprove'])
        self.assertTrue(d['canCancel'])  # submitted + đơn của mình

    def test_json_flags_hr(self):
        self.rec.sudo().action_mgr_approve()
        d = self._json(self.hr_user)
        self.assertEqual(d['stateKind'], 'blue')
        self.assertTrue(d['canHrApprove'])
        self.assertTrue(d['canRefuse'])
        self.assertFalse(d['canMgrApprove'])

    def test_managed_scope_includes_parent_reports(self):
        ids = self.ctrl._offb_managed_employee_ids(
            self.env(user=self.mgr_user))
        self.assertIn(self.staff.id, ids)
        self.assertNotIn(self.mgr_emp.id, ids)
