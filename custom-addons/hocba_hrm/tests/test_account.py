from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _account_payload


@tagged('post_install', '-at_install')
class TestAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_acct',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng Test'})
        self.emp = self.env['hr.employee'].create({
            'name': 'Nguyen Van A', 'x_employee_code': 'EMP-ACCT-1',
            'department_id': self.dept.id})

    def _env(self, user):
        return self.env(user=user)

    def test_payload_empty(self):
        self.assertEqual(_account_payload(self.emp), {'hasAccount': False})
