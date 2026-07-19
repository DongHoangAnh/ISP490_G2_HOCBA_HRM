# ============================================================
# Test luồng phiếu thu/chi: state machine, số dư quỹ, khoá phiếu posted.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install')
class TestVoucherFlow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Voucher = self.env['hocba.fin.voucher']
        self.dept = self.env['hr.department'].create({'name': 'MKT (test)'})
        self.fund = self.env['hocba.fund'].create({
            'name': 'Quỹ MKT (test)', 'code': 'MKT_CASH_T',
            'department_id': self.dept.id, 'opening_balance': 1_000_000.0,
        })
        self.cat_in = self.env.ref('hocba_finance.cat_income_sales')
        self.cat_out = self.env.ref('hocba_finance.cat_expense_ads')
        # User test phải thuộc nhóm Kế toán để được duyệt/ghi sổ.
        self.env.user.group_ids = [
            (4, self.env.ref('hocba_finance.group_finance_user').id)]

    def _mk(self, vtype='income', amount=500_000.0, cat=None):
        return self.Voucher.create({
            'voucher_type': vtype,
            'amount': amount,
            'fund_id': self.fund.id,
            'category_id': (cat or (self.cat_in if vtype == 'income'
                                    else self.cat_out)).id,
        })

    # ── Sequence & department auto-fill ──────────────────────────────────
    def test_sequence_and_department(self):
        v_in = self._mk('income')
        v_out = self._mk('expense')
        self.assertTrue(v_in.name.startswith('PT/'), v_in.name)
        self.assertTrue(v_out.name.startswith('PC/'), v_out.name)
        # department tự điền từ quỹ
        self.assertEqual(v_in.department_id, self.dept)

    # ── State machine ────────────────────────────────────────────────────
    def test_state_machine_happy_path(self):
        v = self._mk('income', 500_000.0)
        self.assertEqual(v.state, 'draft')
        v.action_approve()
        self.assertEqual(v.state, 'approved')
        self.assertTrue(v.approved_by and v.approved_date)
        v.action_post()
        self.assertEqual(v.state, 'posted')
        self.assertTrue(v.posted_by and v.posted_date)

    def test_cannot_post_before_approve(self):
        v = self._mk('income')
        with self.assertRaises(UserError):
            v.action_post()

    def test_cannot_approve_twice(self):
        v = self._mk('income')
        v.action_approve()
        with self.assertRaises(UserError):
            v.action_approve()

    def test_cannot_reset_posted(self):
        v = self._mk('income')
        v.action_approve()
        v.action_post()
        with self.assertRaises(UserError):
            v.action_reset_draft()

    # ── Số dư quỹ ────────────────────────────────────────────────────────
    def test_balance_only_counts_posted(self):
        self.assertEqual(self.fund.current_balance, 1_000_000.0)
        v = self._mk('income', 500_000.0)
        # chưa post → số dư không đổi
        self.assertEqual(self.fund.current_balance, 1_000_000.0)
        v.action_approve()
        v.action_post()
        self.assertEqual(self.fund.current_balance, 1_500_000.0)

    def test_balance_income_minus_expense(self):
        vi = self._mk('income', 800_000.0)
        vi.action_approve(); vi.action_post()
        ve = self._mk('expense', 300_000.0)
        ve.action_approve(); ve.action_post()
        # 1,000,000 + 800,000 - 300,000
        self.assertEqual(self.fund.current_balance, 1_500_000.0)

    def test_post_is_idempotent(self):
        v = self._mk('income', 500_000.0)
        v.action_approve(); v.action_post()
        # gọi post lần nữa phải lỗi (không cộng dồn số dư)
        with self.assertRaises(UserError):
            v.action_post()
        self.assertEqual(self.fund.current_balance, 1_500_000.0)

    def test_cancel_posted_restores_balance(self):
        v = self._mk('income', 500_000.0)
        v.action_approve(); v.action_post()
        self.assertEqual(self.fund.current_balance, 1_500_000.0)
        v.action_cancel()
        self.assertEqual(v.state, 'cancel')
        self.assertEqual(self.fund.current_balance, 1_000_000.0)

    # ── Khoá phiếu posted ────────────────────────────────────────────────
    def test_locked_after_post(self):
        v = self._mk('income', 500_000.0)
        v.action_approve(); v.action_post()
        with self.assertRaises(UserError):
            v.amount = 999_000.0
        with self.assertRaises(UserError):
            v.unlink()

    # ── Constraints ──────────────────────────────────────────────────────
    def test_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._mk('income', 0.0)
        with self.assertRaises(ValidationError):
            self._mk('income', -100.0)

    def test_category_type_must_match(self):
        # phiếu thu nhưng gán mục chi → lỗi
        with self.assertRaises(ValidationError):
            self._mk('income', 500_000.0, cat=self.cat_out)

    def test_external_ref_unique(self):
        self.Voucher.create({
            'voucher_type': 'income', 'amount': 100_000.0,
            'fund_id': self.fund.id, 'category_id': self.cat_in.id,
            'external_ref': 'REF-DUP',
        })
        with self.assertRaises(ValidationError):
            self.Voucher.create({
                'voucher_type': 'income', 'amount': 200_000.0,
                'fund_id': self.fund.id, 'category_id': self.cat_in.id,
                'external_ref': 'REF-DUP',
            })
