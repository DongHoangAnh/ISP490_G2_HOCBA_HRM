from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestNotifyHelper(TransactionCase):
    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.u1 = self.env['res.users'].create({
            'name': 'Notif U1', 'login': 'notif_u1', 'group_ids': gu})
        self.u2 = self.env['res.users'].create({
            'name': 'Notif U2', 'login': 'notif_u2', 'group_ids': gu})
        self.Notif = self.env['hb.notification']

    def test_notify_creates_row_with_fields(self):
        recs = self.Notif._notify(
            self.u1, category='offboarding', kind='pending', level='warning',
            title='Đơn mới', body='ND', target_view='offboarding', target_ref=42)
        self.assertEqual(len(recs), 1)
        r = recs
        self.assertEqual(r.recipient_id, self.u1)
        self.assertEqual(r.category, 'offboarding')
        self.assertEqual(r.kind, 'pending')
        self.assertEqual(r.level, 'warning')
        self.assertEqual(r.target_view, 'offboarding')
        self.assertEqual(r.target_ref, 42)
        self.assertFalse(r.is_read)

    def test_notify_multiple_recipients(self):
        recs = self.Notif._notify(
            self.u1 | self.u2, category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 2)

    def test_notify_skips_inactive_recipient(self):
        self.u2.active = False
        recs = self.Notif._notify(
            self.u1 | self.u2, category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(recs.recipient_id, self.u1)

    def test_notify_skips_falsy_recipient(self):
        recs = self.Notif._notify(
            self.env['res.users'], category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 0)

    def test_notify_accepts_single_int_id(self):
        recs = self.Notif._notify(
            self.u1.id, category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs.recipient_id, self.u1)

    def test_notify_accepts_list_of_ids(self):
        recs = self.Notif._notify(
            [self.u1.id, self.u2.id], category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs.recipient_id, self.u1 | self.u2)

    def test_notify_dedup_when_unread(self):
        kw = dict(category='hr_reminder', kind='cert_expiry', level='warning',
                  title='Chứng chỉ', dedup_key='cert:1:2026-08')
        first = self.Notif._notify(self.u1, **kw)
        second = self.Notif._notify(self.u1, **kw)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)

    def test_notify_dedup_allows_after_read(self):
        kw = dict(category='hr_reminder', kind='cert_expiry', level='warning',
                  title='Chứng chỉ', dedup_key='cert:1:2026-09')
        first = self.Notif._notify(self.u1, **kw)
        first.is_read = True
        second = self.Notif._notify(self.u1, **kw)
        self.assertEqual(len(second), 1)


@tagged('post_install', '-at_install')
class TestNotifyApiHelpers(TransactionCase):
    def setUp(self):
        super().setUp()
        from odoo.addons.hocba_notify.controllers.main import (
            _list_notifications, _mark_read, _mark_all)
        self._list = _list_notifications
        self._mark = _mark_read
        self._mark_all = _mark_all
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.u1 = self.env['res.users'].create({
            'name': 'AU1', 'login': 'napi_u1', 'group_ids': gu})
        self.u2 = self.env['res.users'].create({
            'name': 'AU2', 'login': 'napi_u2', 'group_ids': gu})
        N = self.env['hb.notification']
        N._notify(self.u1, category='timeoff', kind='pending', level='info', title='A')
        N._notify(self.u1, category='timeoff', kind='approved', level='success', title='B')
        N._notify(self.u2, category='timeoff', kind='pending', level='info', title='C')

    def test_list_only_own(self):
        env1 = self.env(user=self.u1)
        res = self._list(env1, limit=20)
        self.assertEqual(res['unread'], 2)
        self.assertEqual({i['title'] for i in res['items']}, {'A', 'B'})
        self.assertIn('targetView', res['items'][0])
        self.assertIn('createdAt', res['items'][0])
        # createdAt phải là ISO-8601 UTC kèm 'Z' để FE không hiểu nhầm là giờ
        # local (bug "vừa xong" → "7 giờ trước" theo offset VN).
        self.assertTrue(res['items'][0]['createdAt'].endswith('Z'))

    def test_mark_read_own(self):
        env1 = self.env(user=self.u1)
        first = self._list(env1)['items'][0]
        ok = self._mark(env1, first['id'])
        self.assertTrue(ok)
        self.assertEqual(self._list(env1)['unread'], 1)

    def test_mark_read_rejects_other_user(self):
        env1 = self.env(user=self.u1)
        other = self.env['hb.notification'].sudo().search(
            [('recipient_id', '=', self.u2.id)], limit=1)
        ok = self._mark(env1, other.id)
        self.assertFalse(ok)
        self.assertFalse(other.is_read)

    def test_mark_all_own(self):
        env1 = self.env(user=self.u1)
        n = self._mark_all(env1)
        self.assertEqual(n, 2)
        self.assertEqual(self._list(env1)['unread'], 0)

    def test_list_bad_limit_falls_back(self):
        env1 = self.env(user=self.u1)
        res = self._list(env1, limit='abc')  # malformed → không lỗi, dùng mặc định
        self.assertEqual(res['unread'], 2)
        self.assertEqual(len(res['items']), 2)

    def test_mark_read_bad_id_returns_false(self):
        env1 = self.env(user=self.u1)
        self.assertFalse(self._mark(env1, 'abc'))
