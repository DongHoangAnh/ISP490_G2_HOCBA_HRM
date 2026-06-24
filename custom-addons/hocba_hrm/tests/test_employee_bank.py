from odoo import http
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM, _bank_options


class _FakeRequest:
    """Stand-in tối giản cho odoo.http.request — chỉ đủ để
    _employee_detail/_can_eval_emp đọc được request.env.user
    khi gọi trực tiếp ngoài context HTTP (unit test)."""

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestEmployeeBankField(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()
        http._request_stack.push(_FakeRequest(self.env))
        self.addCleanup(http._request_stack.pop)

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

    _LABELS = {'status': {}, 'work_form': {}, 'position': {},
               'asset_state': {}, 'relationship': {}}

    def test_detail_includes_bank_for_mgr(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Detail', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        data = self.ctrl._employee_detail(emp, self._LABELS, is_hr=True, is_mgr=True)
        self.assertEqual(data.get('bankCode'), 'VCB')
        self.assertEqual(data.get('bankAccountNo'), '0123456789')

    def test_detail_hides_bank_for_non_mgr(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Detail2', 'x_bank_code': 'VCB',
            'x_bank_account_no': '0123456789'})
        data = self.ctrl._employee_detail(emp, self._LABELS, is_hr=True, is_mgr=False)
        self.assertNotIn('bankCode', data)
        self.assertNotIn('bankAccountNo', data)
