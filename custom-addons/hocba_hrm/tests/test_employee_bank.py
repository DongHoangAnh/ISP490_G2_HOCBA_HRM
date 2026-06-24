from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM


@tagged('post_install', '-at_install')
class TestEmployeeBankField(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()

    def test_model_stores_bank_fields(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Bank', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        self.assertEqual(emp.x_bank_code, 'VCB')
        self.assertEqual(emp.x_bank_account_no, '0123456789')
