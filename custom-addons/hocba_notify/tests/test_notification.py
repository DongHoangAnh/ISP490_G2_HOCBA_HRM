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
