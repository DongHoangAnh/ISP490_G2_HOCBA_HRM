from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestUserDefaultTz(TransactionCase):
    """User mới không truyền tz → mặc định Asia/Ho_Chi_Minh (tránh lệch giờ
    chấm công ca: xem _to_utc / cửa sổ check-in trong hocba_hrm)."""

    def test_new_user_gets_default_tz(self):
        u = self.env['res.users'].create({
            'name': 'TZ Default', 'login': 'tz_default_user'})
        self.assertEqual(u.tz, 'Asia/Ho_Chi_Minh')

    def test_explicit_tz_is_preserved(self):
        u = self.env['res.users'].create({
            'name': 'TZ Explicit', 'login': 'tz_explicit_user', 'tz': 'UTC'})
        self.assertEqual(u.tz, 'UTC')
