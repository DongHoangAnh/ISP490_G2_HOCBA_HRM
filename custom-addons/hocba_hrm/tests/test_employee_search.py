from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _employee_search


@tagged('post_install', '-at_install')
class TestEmployeeSearch(TransactionCase):

    def setUp(self):
        super().setUp()
        self.target = self.env['hr.employee'].create({
            'name': 'Nguyen Van Tim', 'x_employee_code': 'EMP-TIM-001'})
        self.mgr = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_search',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_search',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

    def test_manager_finds_by_code(self):
        rows = _employee_search(self.env(user=self.mgr), 'EMP-TIM')
        self.assertTrue(any(r['code'] == 'EMP-TIM-001' for r in rows))

    def test_manager_finds_by_name(self):
        rows = _employee_search(self.env(user=self.mgr), 'Van Tim')
        self.assertTrue(any(r['id'] == self.target.id for r in rows))

    def test_non_manager_gets_empty(self):
        self.assertEqual(_employee_search(self.env(user=self.plain), 'EMP-TIM'), [])

    def test_empty_query_gets_empty(self):
        self.assertEqual(_employee_search(self.env(user=self.mgr), '  '), [])
