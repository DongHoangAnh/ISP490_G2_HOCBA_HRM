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
