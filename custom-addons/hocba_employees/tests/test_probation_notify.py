from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProbationNotify(TransactionCase):
    """Cron nhắc đánh giá + kết quả cổng thử việc phát chuông onboarding."""

    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.mgr_user = self.env['res.users'].create({
            'name': 'PMgr', 'login': 'pn_mgr', 'group_ids': gu})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'PMgr Emp', 'identification_id': '017777770001',
            'user_id': self.mgr_user.id})
        self.emp_user = self.env['res.users'].create({
            'name': 'PEmp', 'login': 'pn_emp', 'group_ids': gu})
        # BR-010: chính thức cần CCCD 12 số + MST + BHXH — khai sẵn để cổng
        # pass lên 'official' không vướng ValidationError.
        self.emp = self.env['hr.employee'].create({
            'name': 'Probation Emp', 'identification_id': '017777770002',
            'parent_id': self.mgr_emp.id, 'user_id': self.emp_user.id,
            'x_employment_status': 'probation',
            'x_pit_code': '8017777702', 'x_social_insurance_no': '0117777702',
            'x_probation_start': fields.Date.today() - timedelta(days=13)})

    def _notifs(self, kind):
        return self.env['hb.notification'].sudo().search([
            ('category', '=', 'onboarding'), ('kind', '=', kind),
            ('target_ref', '=', self.emp.id)])

    def test_cron_reminder_notifies_manager_with_dedup(self):
        # due 2w = start + 14 ngày → nằm trong cửa sổ nhắc (<= today+2)
        Emp = self.env['hr.employee']
        Emp._cron_probation_eval_reminders()
        first = self._notifs('probation_eval').filtered(
            lambda n: n.recipient_id == self.mgr_user)
        self.assertEqual(len(first), 1)
        self.assertEqual(first.level, 'warning')
        self.assertEqual(first.target_view, 'employees')
        # Chạy lần 2 → dedup theo (recipient, dedup_key), không nhân bản
        Emp._cron_probation_eval_reminders()
        again = self._notifs('probation_eval').filtered(
            lambda n: n.recipient_id == self.mgr_user)
        self.assertEqual(len(again), 1)

    def test_gate_fail_notifies(self):
        # Cổng tuần-2 KHÔNG ĐẠT → offboarding + chuông danger cho QL + NV
        self.emp.sudo().write({'x_eval_2w_result': 'fail'})
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        notifs = self._notifs('probation_fail')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'danger' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)
        # Re-fire cổng khác khi đã exiting → offboarding idempotent, không
        # bắn thêm chuông fail
        before = len(notifs)
        self.emp._hocba_start_offboarding('tháng-1')
        self.assertEqual(len(self._notifs('probation_fail')), before)

    def test_gate_pass_notifies(self):
        # Tuần-2 Đạt rồi tháng-1 Đạt → Chính thức sớm + chuông success
        self.emp.sudo().write({'x_eval_2w_result': 'pass'})
        self.emp.sudo().write({'x_eval_1m_result': 'pass'})
        self.assertEqual(self.emp.x_employment_status, 'official')
        notifs = self._notifs('probation_pass')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'success' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)

    def test_gate_extend_notifies(self):
        # Tuần-2 Đạt rồi tháng-1 Gia hạn → chuông warning cho QL + NV
        self.emp.sudo().write({'x_eval_2w_result': 'pass'})
        self.emp.sudo().write({'x_eval_1m_result': 'extend'})
        notifs = self._notifs('probation_extend')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'warning' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)
