from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM, _bank_options


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

    def test_form_payload_mgr_includes_bank(self):
        emp_vals, _ver = self.ctrl._split_form_payload(
            {'name': 'X', 'bankCode': 'VCB', 'bankAccountNo': '0123456789'},
            is_hr=True, is_mgr=True)
        self.assertEqual(emp_vals.get('x_bank_code'), 'VCB')
        self.assertEqual(emp_vals.get('x_bank_account_no'), '0123456789')

    def test_form_payload_non_mgr_excludes_bank(self):
        emp_vals, _ver = self.ctrl._split_form_payload(
            {'name': 'X', 'bankCode': 'VCB', 'bankAccountNo': '0123456789'},
            is_hr=True, is_mgr=False)
        self.assertNotIn('x_bank_code', emp_vals)
        self.assertNotIn('x_bank_account_no', emp_vals)

    def test_bank_options_lists_active_formats(self):
        if 'hb.bank.format' not in self.env:
            self.skipTest('hocba_payroll chưa cài')
        self.env['hb.bank.format'].create({
            'name': 'Test Bank', 'code': 'TSTBANK',
            'formatter_class': 'VCBFormatter'})
        opts = _bank_options(self.env)
        self.assertIn(
            {'code': 'TSTBANK', 'name': 'Test Bank'},
            [{'code': o['code'], 'name': o['name']} for o in opts])
