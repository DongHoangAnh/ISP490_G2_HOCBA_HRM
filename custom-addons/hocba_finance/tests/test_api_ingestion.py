# ============================================================
# Test nạp phiếu qua API (_ingest_from_api): tạo, idempotent, cô lập lỗi.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestApiIngestion(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Voucher = self.env['hocba.fin.voucher']
        self.dept = self.env['hr.department'].create({'name': 'Sale (test)'})
        self.fund = self.env['hocba.fund'].create({
            'name': 'Quỹ Sale (test)', 'code': 'SALE_CASH_T',
            'department_id': self.dept.id,
        })
        # auto_post gọi approve/post → cần nhóm Kế toán.
        self.env.user.group_ids = [
            (4, self.env.ref('hocba_finance.group_finance_user').id)]

    def _item(self, ref='ORD-1', amount=10_000_000.0, **kw):
        base = {
            'external_ref': ref, 'voucher_type': 'income',
            'amount': amount, 'date': '2026-07-11',
            'fund_code': 'SALE_CASH_T', 'category_code': 'DT_BANHANG',
            'partner_name': 'Nguyen Van A', 'memo': 'Học phí',
        }
        base.update(kw)
        return base

    def test_ingest_creates_draft_voucher(self):
        res = self.Voucher._ingest_from_api([self._item('ORD-1')])
        self.assertEqual(res['created'], 1)
        self.assertEqual(res['skipped'], 0)
        v = self.Voucher.search([('external_ref', '=', 'ORD-1')])
        self.assertEqual(len(v), 1)
        self.assertEqual(v.state, 'draft')
        self.assertEqual(v.source, 'api')
        self.assertEqual(v.fund_id, self.fund)
        self.assertTrue(v.payload_raw)

    def test_ingest_is_idempotent(self):
        item = self._item('ORD-DUP')
        r1 = self.Voucher._ingest_from_api([item])
        r2 = self.Voucher._ingest_from_api([item])
        self.assertEqual(r1['created'], 1)
        self.assertEqual(r2['created'], 0)
        self.assertEqual(r2['skipped'], 1)
        self.assertEqual(
            self.Voucher.search_count([('external_ref', '=', 'ORD-DUP')]), 1)

    def test_bad_item_does_not_poison_batch(self):
        good = self._item('ORD-OK')
        bad = self._item('ORD-BAD', fund_code='NOPE')
        res = self.Voucher._ingest_from_api([good, bad])
        self.assertEqual(res['created'], 1)
        self.assertEqual(len(res['errors']), 1)
        self.assertEqual(res['errors'][0]['external_ref'], 'ORD-BAD')
        self.assertTrue(
            self.Voucher.search([('external_ref', '=', 'ORD-OK')]))
        self.assertFalse(
            self.Voucher.search([('external_ref', '=', 'ORD-BAD')]))

    def test_auto_post_updates_balance(self):
        res = self.Voucher._ingest_from_api(
            [self._item('ORD-AP', amount=5_000_000.0)], auto_post=True)
        self.assertEqual(res['created'], 1)
        v = self.Voucher.search([('external_ref', '=', 'ORD-AP')])
        self.assertEqual(v.state, 'posted')
        self.assertEqual(self.fund.current_balance, 5_000_000.0)
