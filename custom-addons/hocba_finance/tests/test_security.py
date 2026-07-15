# ============================================================
# Test phân quyền: nhân viên thường không duyệt/ghi sổ được; chỉ thấy phiếu mình.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestFinanceSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Voucher = self.env['hocba.fin.voucher']
        self.fund = self.env['hocba.fund'].create({
            'name': 'Quỹ chung (test)', 'code': 'GEN_CASH_T'})
        self.cat_in = self.env.ref('hocba_finance.cat_income_sales')

        grp_user = self.env.ref('base.group_user')
        self.acct_group = self.env.ref('hocba_finance.group_finance_user')

        self.normal = self.env['res.users'].create({
            'name': 'NV thường', 'login': 'fin_normal_t',
            'group_ids': [(6, 0, [grp_user.id])]})
        self.acct = self.env['res.users'].create({
            'name': 'Kế toán', 'login': 'fin_acct_t',
            'group_ids': [(6, 0, [grp_user.id, self.acct_group.id])]})

    def _mk_as(self, user):
        return self.Voucher.with_user(user).create({
            'voucher_type': 'income', 'amount': 100_000.0,
            'fund_id': self.fund.id, 'category_id': self.cat_in.id,
        })

    def test_normal_user_can_create_draft(self):
        v = self._mk_as(self.normal)
        self.assertEqual(v.state, 'draft')

    def test_normal_user_cannot_approve(self):
        v = self._mk_as(self.normal)
        with self.assertRaises(AccessError):
            v.with_user(self.normal).action_approve()

    def test_normal_user_sees_only_own(self):
        mine = self._mk_as(self.normal)
        others = self._mk_as(self.acct)
        visible = self.Voucher.with_user(self.normal).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(others, visible)

    def test_accountant_sees_all_and_can_post(self):
        by_normal = self._mk_as(self.normal)
        visible = self.Voucher.with_user(self.acct).search([])
        self.assertIn(by_normal, visible)
        v = by_normal.with_user(self.acct)
        v.action_approve()
        v.action_post()
        self.assertEqual(v.state, 'posted')
