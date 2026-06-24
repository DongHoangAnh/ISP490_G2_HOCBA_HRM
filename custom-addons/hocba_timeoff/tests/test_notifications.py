# ============================================================
# Test Phase 5 — Thông báo in-app (chuông) + nhật ký thao tác đơn (audit).
# Gọi thẳng hàm cấp module như quy ước test của repo. Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _notify_request_created, _notify_decision,
    _list_notifications, _mark_notification_read, _mark_all_notifications_read,
    _request_history,
)


@tagged('post_install', '-at_install')
class TestTimeoffNotifications(TransactionCase):

    def setUp(self):
        super().setUp()
        Dept = self.env['hr.department']
        # Khối A (cha) → Tổ A1 (con) · Khối B (độc lập, có trưởng phòng riêng)
        self.dept_parent = Dept.create({'name': 'Khối A (notif)'})
        self.dept_child = Dept.create(
            {'name': 'Tổ A1 (notif)', 'parent_id': self.dept_parent.id})
        self.dept_other = Dept.create({'name': 'Khối B (notif)'})

        self.emp_mgr = self._mk_emp('TP A notif', '130000000001', self.dept_parent)
        self.emp_a = self._mk_emp('NV A notif', '130000000002', self.dept_parent)
        self.emp_other_mgr = self._mk_emp('TP B notif', '130000000003', self.dept_other)
        self.emp_b = self._mk_emp('NV B notif', '130000000004', self.dept_other)
        self.dept_parent.manager_id = self.emp_mgr.id
        self.dept_other.manager_id = self.emp_other_mgr.id

        self.mgr_user = self._mk_user('notif_mgr', self.emp_mgr)
        self.owner_user = self._mk_user('notif_owner', self.emp_a)
        self.other_mgr_user = self._mk_user('notif_other_mgr', self.emp_other_mgr)
        self.normal_user = self._mk_user('notif_normal', self.emp_b)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR notif user', 'login': 'notif_hr',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self._allocate(self.emp_a, 12)

    # ----- Helpers -----
    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10],
        })

    def _mk_user(self, login, emp):
        user = self.env['res.users'].create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        emp.user_id = user
        return user

    def _allocate(self, emp, days):
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ notif %s' % emp.name,
            'holiday_status_id': self.annual.id, 'employee_id': emp.id,
            'number_of_days': days, 'allocation_type': 'regular',
            'date_from': '2026-01-01', 'date_to': '2026-12-31',
        })
        if alloc.state != 'validate':
            alloc._action_validate()
        return alloc

    def _mk_leave(self, emp, d_from='2026-07-02', d_to='2026-07-03'):
        return self.env['hr.leave'].create({
            'name': 'Nghỉ notif', 'holiday_status_id': self.annual.id,
            'employee_id': emp.id,
            'request_date_from': d_from, 'request_date_to': d_to,
        })

    def _notifs_of(self, user, only_unread=False):
        domain = [('recipient_id', '=', user.id)]
        if only_unread:
            domain.append(('is_read', '=', False))
        return self.env['hb.leave.notification'].sudo().search(domain)

    # ----- Tests -----
    def test_create_notifies_scoped_approver_only(self):
        """Đơn mới → báo trưởng phòng của NV + HR; KHÔNG lọt sang trưởng phòng khác."""
        leave = self._mk_leave(self.emp_a)
        _notify_request_created(self.env, leave)

        mgr_notifs = self._notifs_of(self.mgr_user)
        self.assertEqual(len(mgr_notifs), 1)
        self.assertEqual(mgr_notifs.kind, 'pending')
        self.assertEqual(mgr_notifs.leave_id.id, leave.id)
        # HR Manager cũng được báo
        self.assertTrue(self._notifs_of(self.hr_user))
        # Trưởng phòng Khối B KHÔNG liên quan → không nhận
        self.assertFalse(self._notifs_of(self.other_mgr_user))
        # Chủ đơn không tự báo cho mình
        self.assertFalse(self._notifs_of(self.owner_user))

    def test_decision_notifies_owner(self):
        """Duyệt/từ chối → báo chủ đơn với kind tương ứng."""
        leave = self._mk_leave(self.emp_a)
        _notify_decision(self.env, leave, 'approve')
        notifs = self._notifs_of(self.owner_user)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs.kind, 'approved')

        leave2 = self._mk_leave(self.emp_a, '2026-08-04', '2026-08-05')
        _notify_decision(self.env, leave2, 'refuse')
        refused = self._notifs_of(self.owner_user).filtered(
            lambda n: n.leave_id.id == leave2.id)
        self.assertEqual(refused.kind, 'refused')

    def test_list_unread_and_mark_read(self):
        """list trả đúng số chưa đọc; /read giảm 1; /read-all về 0."""
        _notify_request_created(self.env, self._mk_leave(self.emp_a))
        _notify_request_created(self.env, self._mk_leave(self.emp_a, '2026-09-01', '2026-09-02'))

        env_mgr = self.env(user=self.mgr_user)
        data = _list_notifications(env_mgr)
        self.assertEqual(data['unread'], 2)
        self.assertEqual(len(data['items']), 2)

        first_id = data['items'][0]['id']
        self.assertTrue(_mark_notification_read(env_mgr, first_id))
        self.assertEqual(_list_notifications(env_mgr)['unread'], 1)

        self.assertEqual(_mark_all_notifications_read(env_mgr), 1)
        self.assertEqual(_list_notifications(env_mgr)['unread'], 0)

    def test_only_unread_filter(self):
        _notify_request_created(self.env, self._mk_leave(self.emp_a))
        env_mgr = self.env(user=self.mgr_user)
        all_notif = self._notifs_of(self.mgr_user)
        all_notif.write({'is_read': True})
        _notify_request_created(self.env, self._mk_leave(self.emp_a, '2026-10-01', '2026-10-02'))
        only = _list_notifications(env_mgr, only_unread=True)
        self.assertEqual(only['unread'], 1)
        self.assertEqual(len(only['items']), 1)

    def test_cannot_read_other_users_notification(self):
        """Đánh dấu đã đọc thông báo của người khác → từ chối, không đổi gì."""
        _notify_decision(self.env, self._mk_leave(self.emp_a), 'approve')
        owner_notif = self._notifs_of(self.owner_user)
        self.assertTrue(owner_notif)

        env_mgr = self.env(user=self.mgr_user)
        self.assertFalse(_mark_notification_read(env_mgr, owner_notif.id))
        self.assertFalse(owner_notif.is_read)  # vẫn chưa đọc

    def test_history_sequence_and_scope(self):
        """history trả đúng trình tự create → quyết định; chặn ngoài phạm vi."""
        leave = self._mk_leave(self.emp_a)
        _notify_request_created(self.env, leave)
        _notify_decision(self.env, leave, 'approve')

        scope_hr = _scope_for(self.env(user=self.hr_user))
        rows = _request_history(self.env(user=self.hr_user), scope_hr, leave.id)
        self.assertIsInstance(rows, list)
        bodies = [r['body'] for r in rows]
        idx_create = next(i for i, b in enumerate(bodies) if 'chờ duyệt' in b)
        idx_decide = next(i for i, b in enumerate(bodies) if 'được duyệt' in b)
        self.assertLess(idx_create, idx_decide)

        # Chủ đơn xem được lịch sử đơn của mình
        scope_owner = _scope_for(self.env(user=self.owner_user))
        self.assertIsInstance(
            _request_history(self.env(user=self.owner_user), scope_owner, leave.id), list)

        # Trưởng phòng phòng KHÁC (ngoài phạm vi) → False (403)
        scope_other = _scope_for(self.env(user=self.other_mgr_user))
        self.assertIs(
            _request_history(self.env(user=self.other_mgr_user), scope_other, leave.id), False)

        # NV thường không phải chủ đơn → False (403)
        scope_normal = _scope_for(self.env(user=self.normal_user))
        self.assertIs(
            _request_history(self.env(user=self.normal_user), scope_normal, leave.id), False)

        # Đơn không tồn tại → None (404)
        self.assertIsNone(_request_history(self.env, scope_hr, 999999999))
