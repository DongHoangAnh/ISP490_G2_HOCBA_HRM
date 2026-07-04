from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOffboardingModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Off Target',
            'identification_id': '012345678901',
        })

    def _make(self, **kw):
        vals = {
            'employee_id': self.emp.id,
            'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hocba.offboarding'].create(vals)

    def test_create_generates_code_and_draft(self):
        rec = self._make()
        self.assertNotIn(rec.name, ('/', False))
        self.assertTrue(rec.name.startswith('OFF/'))
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(rec.source, 'self')

    def test_happy_path_states(self):
        rec = self._make()
        rec.action_submit()
        self.assertEqual(rec.state, 'submitted')
        rec.sudo().action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        self.assertTrue(rec.mgr_approved_by)
        rec.sudo().action_hr_approve()
        self.assertEqual(rec.state, 'hr_approved')
        self.assertTrue(rec.hr_approved_by)

    def test_submit_only_from_draft(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        with self.assertRaises(ValidationError):
            rec.action_submit()

    def test_direct_manager_can_approve(self):
        mgr_user = self.env['res.users'].create({
            'name': 'DirectMgr', 'login': 'off_direct_mgr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        mgr_emp = self.env['hr.employee'].create({
            'name': 'DirectMgr Emp', 'identification_id': '015555555501',
            'user_id': mgr_user.id})
        self.emp.parent_id = mgr_emp
        rec = self._make()
        rec.action_submit()
        rec.with_user(mgr_user).action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')

    def _advance_to_hr_approved(self, rec):
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        rec.sudo().action_hr_approve()

    def test_done_closes_profile_and_locks_user(self):
        user = self.env['res.users'].create({
            'name': 'Leaver', 'login': 'off_leaver_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp.user_id = user
        rec = self._make()
        self._advance_to_hr_approved(rec)
        rec.sudo().action_done()
        self.assertEqual(rec.state, 'done')
        self.assertEqual(self.emp.x_employment_status, 'resigned')
        self.assertFalse(self.emp.active)
        self.assertFalse(user.active)
        self.assertEqual(rec.actual_leave_date, fields.Date.today())

    def test_done_blocked_when_asset_assigned(self):
        from odoo.exceptions import ValidationError
        atype = self.env['hocba.asset.type'].create({
            'name': 'Laptop Off', 'code': 'LAPOFF'})
        self.env['hr.employee.asset'].create({
            'employee_id': self.emp.id,
            'asset_type_id': atype.id,
            'asset_code': 'LAPOFF-1',
            'grant_date': fields.Date.today(),
            'condition_in': 'new',
        })
        rec = self._make()
        self._advance_to_hr_approved(rec)
        with self.assertRaises(ValidationError):
            rec.sudo().action_done()
        self.assertEqual(rec.state, 'hr_approved')

    def test_refuse_after_mgr_restores_status(self):
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        rec.sudo().action_refuse()
        self.assertEqual(rec.state, 'refused')
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_cancel_only_before_approval(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        with self.assertRaises(ValidationError):
            rec.sudo().action_cancel()
