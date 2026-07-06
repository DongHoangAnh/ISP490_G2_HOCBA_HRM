from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestReminderNotify(TransactionCase):
    """Cron nhắc hạn hồ sơ: chứng chỉ (cert) + hợp đồng (contract) phát chuông
    category='hr_reminder'."""

    def setUp(self):
        super().setUp()
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Rem', 'login': 'rem_hr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.emp_user = self.env['res.users'].create({
            'name': 'Rem Emp User', 'login': 'rem_emp',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp = self.env['hr.employee'].create({
            'name': 'Rem Emp', 'identification_id': '018888880001',
            'user_id': self.emp_user.id})
        self.skill_type = self.env['hr.skill.type'].create({'name': 'Cert Type'})
        self.skill = self.env['hr.skill'].create({
            'name': 'HSK5', 'skill_type_id': self.skill_type.id})
        self.level = self.env['hr.skill.level'].create({
            'name': 'L1', 'skill_type_id': self.skill_type.id,
            'level_progress': 50})
        self.Emp = self.env['hr.employee']

    def _add_cert(self, expiry):
        return self.env['hr.employee.skill'].create({
            'employee_id': self.emp.id, 'skill_type_id': self.skill_type.id,
            'skill_id': self.skill.id, 'skill_level_id': self.level.id,
            'x_cert_expiry': expiry, 'x_cert_verified': True})

    def _notifs(self, kind):
        return self.env['hb.notification'].sudo().search([
            ('category', '=', 'hr_reminder'), ('kind', '=', kind),
            ('target_ref', '=', self.emp.id)])

    def test_cert_expiring_notifies_hr_and_employee_with_dedup(self):
        self._add_cert(fields.Date.today() + timedelta(days=10))
        self.Emp._cron_cert_expiry_alerts()
        n = self._notifs('cert_expiry')
        self.assertTrue(n)
        self.assertTrue(all(x.level == 'warning' for x in n))
        recips = n.mapped('recipient_id')
        self.assertIn(self.hr_user, recips)
        self.assertIn(self.emp_user, recips)  # cert: báo cả HR lẫn NV
        # NV trỏ 'profile' (mở được), HR trỏ 'employees'
        self.assertEqual(
            n.filtered(lambda x: x.recipient_id == self.emp_user).target_view,
            'profile')
        self.assertEqual(
            n.filtered(lambda x: x.recipient_id == self.hr_user).target_view,
            'employees')
        hr_before = len(n.filtered(lambda x: x.recipient_id == self.hr_user))
        # dedup: chạy lần 2 không nhân bản
        self.Emp._cron_cert_expiry_alerts()
        hr_after = len(self._notifs('cert_expiry').filtered(
            lambda x: x.recipient_id == self.hr_user))
        self.assertEqual(hr_after, hr_before)

    def test_cert_expired_notifies_danger(self):
        self._add_cert(fields.Date.today() - timedelta(days=5))
        self.Emp._cron_cert_expiry_alerts()
        n = self._notifs('cert_expired')
        self.assertTrue(n)
        self.assertTrue(all(x.level == 'danger' for x in n))

    def test_contract_end_notifies_hr_only_with_dedup(self):
        self.emp.version_id.sudo().write({
            'contract_date_start': fields.Date.today() - timedelta(days=180),
            'contract_date_end': fields.Date.today() + timedelta(days=15)})
        self.Emp._cron_contract_end_alerts()
        n = self._notifs('contract_end')
        self.assertTrue(n)
        self.assertTrue(all(x.level == 'warning' for x in n))
        recips = n.mapped('recipient_id')
        self.assertIn(self.hr_user, recips)
        self.assertNotIn(self.emp_user, recips)  # HĐ chỉ báo HR
        before = len(n)
        self.Emp._cron_contract_end_alerts()
        self.assertEqual(len(self._notifs('contract_end')), before)

    def test_contract_end_ignores_far_future(self):
        self.emp.version_id.sudo().write({
            'contract_date_start': fields.Date.today() - timedelta(days=180),
            'contract_date_end': fields.Date.today() + timedelta(days=90)})
        self.Emp._cron_contract_end_alerts()
        self.assertFalse(self._notifs('contract_end'))
