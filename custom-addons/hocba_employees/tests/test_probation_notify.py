from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProbationNotify(TransactionCase):
    """Cron nhắc hạn + kết quả bước nhận việc động phát chuông onboarding."""

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
        # BR-010: chính thức cần CCCD 12 số + MST + BHXH — khai sẵn để bước
        # pass_completes lên 'official' không vướng ValidationError.
        # staff + offline → khớp seed 'Thử việc Nhân viên văn phòng'
        # (ĐG tuần-2 due +14 → start hôm nay-13 → hạn ngày mai, trong cửa sổ nhắc).
        self.emp = self.env['hr.employee'].create({
            'name': 'Probation Emp', 'identification_id': '017777770002',
            'parent_id': self.mgr_emp.id, 'user_id': self.emp_user.id,
            'x_position_type': 'staff', 'x_work_form': 'offline',
            'x_employment_status': 'probation',
            'x_pit_code': '8017777702', 'x_social_insurance_no': '0117777702',
            'x_probation_start': fields.Date.today() - timedelta(days=13)})

    def _steps(self):
        return self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def _notifs(self, kind):
        return self.env['hb.notification'].sudo().search([
            ('category', '=', 'onboarding'), ('kind', '=', kind),
            ('target_ref', '=', self.emp.id)])

    def test_seed_template_assigned(self):
        self.assertEqual(
            self.emp.x_onboarding_template_id,
            self.env.ref('hocba_employees.onb_template_office'))
        self.assertEqual(len(self._steps()), 4)

    def test_cron_reminder_notifies_manager_with_dedup(self):
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

    def test_step_fail_notifies(self):
        # Bước tuần-2 KHÔNG ĐẠT → offboarding + chuông danger cho QL + NV
        self._steps()[0].action_evaluate('fail', note='Không đạt')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        notifs = self._notifs('probation_fail')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'danger' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)
        # Re-fire khi đã exiting → offboarding idempotent, không thêm chuông
        before = len(notifs)
        self.emp._hocba_start_offboarding('tháng-1')
        self.assertEqual(len(self._notifs('probation_fail')), before)

    def test_step_pass_notifies(self):
        # Tuần-2 Đạt (thiết bị auto) rồi tháng-1 Đạt → Chính thức + success
        self._steps()[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('pass')
        self.assertEqual(self.emp.x_employment_status, 'official')
        notifs = self._notifs('probation_pass')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'success' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)
        # NV nhận bản trỏ 'profile' (mở được), QL trỏ 'employees'
        emp_n = notifs.filtered(lambda n: n.recipient_id == self.emp_user)
        mgr_n = notifs.filtered(lambda n: n.recipient_id == self.mgr_user)
        self.assertEqual(emp_n.target_view, 'profile')
        self.assertEqual(mgr_n.target_view, 'employees')

    def test_step_extend_notifies(self):
        # Tuần-2 Đạt rồi tháng-1 Gia hạn (→ mở tháng-2) → warning QL + NV
        self._steps()[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('extend', extend_days=14)
        self.assertEqual(self._steps()[3].state, 'open')
        notifs = self._notifs('probation_extend')
        self.assertTrue(notifs)
        self.assertTrue(all(n.level == 'warning' for n in notifs))
        recipients = notifs.mapped('recipient_id')
        self.assertIn(self.mgr_user, recipients)
        self.assertIn(self.emp_user, recipients)
