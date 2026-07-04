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
