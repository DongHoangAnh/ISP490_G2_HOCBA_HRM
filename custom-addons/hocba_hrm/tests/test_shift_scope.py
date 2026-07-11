from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _shift_scope_domain


@tagged('post_install', '-at_install')
class TestShiftScope(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctv = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.reg = self.env['hr.employee'].create({
            'name': 'NV B', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789'})

    def _user_for(self, emp, manager=False):
        groups = [self.env.ref('base.group_user').id]
        if manager:
            groups.append(self.env.ref('hr.group_hr_manager').id)
        user = self.env['res.users'].create({
            'name': emp.name, 'login': 'u_%s' % emp.id,
            'group_ids': [(6, 0, groups)]})
        emp.user_id = user
        return user

    def test_regular_employee_sees_only_ot(self):
        env = self.env(user=self._user_for(self.reg))
        dom = _shift_scope_domain(env)
        self.assertIn(('shift_type', '=', 'ot'), dom)

    def test_ctv_sees_only_ctv(self):
        env = self.env(user=self._user_for(self.ctv))
        dom = _shift_scope_domain(env)
        self.assertIn(('shift_type', '=', 'ctv'), dom)

    def test_manager_no_type_restriction_by_default(self):
        env = self.env(user=self._user_for(self.reg, manager=True))
        dom = _shift_scope_domain(env)
        self.assertFalse([t for t in dom if t[0] == 'shift_type'])

    def test_manager_type_filter_applies(self):
        env = self.env(user=self._user_for(self.reg, manager=True))
        dom = _shift_scope_domain(env, 'ctv')
        self.assertIn(('shift_type', '=', 'ctv'), dom)
