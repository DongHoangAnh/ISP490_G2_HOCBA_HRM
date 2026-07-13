from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOffboardingNotify(TransactionCase):
    """Mỗi transition offboarding phát đúng chuông tới đúng người."""

    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Notify', 'login': 'offn_hr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.mgr_user = self.env['res.users'].create({
            'name': 'Mgr Notify', 'login': 'offn_mgr', 'group_ids': gu})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'Mgr Notify Emp', 'identification_id': '016666660001',
            'user_id': self.mgr_user.id})
        self.staff_user = self.env['res.users'].create({
            'name': 'Staff Notify', 'login': 'offn_staff', 'group_ids': gu})
        self.staff = self.env['hr.employee'].create({
            'name': 'Staff Notify Emp', 'identification_id': '016666660002',
            'parent_id': self.mgr_emp.id, 'user_id': self.staff_user.id})
        self.rec = self.env['hocba.offboarding'].with_user(self.staff_user).create({
            'employee_id': self.staff.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})

    def _notifs(self, kind=None, recipient=None):
        dom = [('category', '=', 'offboarding'), ('target_ref', '=', self.rec.id)]
        if kind:
            dom.append(('kind', '=', kind))
        if recipient:
            dom.append(('recipient_id', '=', recipient.id))
        return self.env['hb.notification'].sudo().search(dom)

    def test_submit_notifies_manager(self):
        self.rec.action_submit()
        n = self._notifs('pending', self.mgr_user)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'warning')
        self.assertEqual(n.target_view, 'offboarding')
        # Chính chủ không tự nhận thông báo
        self.assertFalse(self._notifs('pending', self.staff_user))

    def test_mgr_approve_notifies_hr(self):
        self.rec.action_submit()
        self.rec.with_user(self.mgr_user).action_mgr_approve()
        self.assertTrue(self._notifs('pending', self.hr_user))

    def test_hr_approve_notifies_employee(self):
        self.rec.action_submit()
        self.rec.sudo().action_mgr_approve()
        self.rec.with_user(self.hr_user).action_hr_approve()
        n = self._notifs('approved', self.staff_user)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'info')

    def test_refuse_notifies_employee(self):
        self.rec.action_submit()
        self.rec.with_user(self.mgr_user).action_refuse()
        n = self._notifs('refused', self.staff_user)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'danger')

    def test_done_notifies_manager(self):
        self.rec.action_submit()
        self.rec.sudo().action_mgr_approve()
        self.rec.with_user(self.hr_user).action_hr_approve()
        self.rec.with_user(self.hr_user).action_done()
        n = self._notifs('done', self.mgr_user)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'success')

    def test_cancel_no_notification(self):
        self.rec.action_submit()
        before = len(self._notifs())
        self.rec.with_user(self.staff_user).action_cancel()
        self.assertEqual(len(self._notifs()), before)
