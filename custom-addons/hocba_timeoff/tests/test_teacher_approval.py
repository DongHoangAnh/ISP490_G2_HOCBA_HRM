# ============================================================
# Test Step 4 — Duyệt đơn nghỉ giáo viên: chặn khi dạy thay chưa đồng ý,
# áp ghi lịch dạy lúc duyệt, revert khi hủy/từ chối. Owner: Nhật Anh.
# Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict-design §5.
# ============================================================
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestTeacherApproval(TransactionCase):

    def setUp(self):
        super().setUp()
        self.teacher = self.env['hr.employee'].create({
            'name': 'GV A1', 'x_cms_user_id': 'CMS_A1'})
        self.sub = self.env['hr.employee'].create({
            'name': 'GV A2', 'x_cms_user_id': 'CMS_A2'})
        Session = self.env['hocba.teaching.session']
        self.s_off = Session.create({
            'cms_session_id': 'A-OFF', 'employee_id': self.teacher.id,
            'class_name': 'LO', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00'})
        self.s_sub = Session.create({
            'cms_session_id': 'A-SUB', 'employee_id': self.teacher.id,
            'class_name': 'LS', 'session_date': '2026-07-06',
            'start_time': '13:00', 'end_time': '15:00'})
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        self.Res = self.env['hocba.leave.session.resolution']

    def _confirmed_leave(self):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ GV', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.teacher.id,
            'request_date_from': '2026-07-06', 'request_date_to': '2026-07-06'})
        if leave.state == 'draft':
            leave.action_confirm()
        return leave

    def _add_resolutions(self, leave, sub_state='pending'):
        off = self.Res.create({
            'leave_id': leave.id, 'session_id': self.s_off.id,
            'resolution': 'class_off'})
        sub = self.Res.create({
            'leave_id': leave.id, 'session_id': self.s_sub.id,
            'resolution': 'substitute', 'substitute_id': self.sub.id})
        if sub_state != 'pending':
            sub.state = sub_state
        return off, sub

    # ---------- Chặn duyệt khi dạy thay chưa đồng ý ----------
    def test_approve_blocked_when_substitute_pending(self):
        leave = self._confirmed_leave()
        self._add_resolutions(leave, sub_state='pending')
        with self.assertRaises(ValidationError):
            leave.action_approve()
        self.assertNotEqual(leave.state, 'validate')

    # ---------- Duyệt được khi dạy thay đã đồng ý + áp ghi lịch ----------
    def test_approve_applies_schedule_changes(self):
        leave = self._confirmed_leave()
        self._add_resolutions(leave, sub_state='accepted')
        leave.action_approve()
        self.assertEqual(leave.state, 'validate')
        # class_off → buổi bị hủy
        self.assertEqual(self.s_off.state, 'cancelled')
        self.assertEqual(self.s_off.source_leave_id, leave)
        # substitute → buổi đổi sang GV thay
        self.assertEqual(self.s_sub.state, 'substituted')
        self.assertEqual(self.s_sub.employee_id, self.sub)
        self.assertEqual(self.s_sub.source_leave_id, leave)

    # ---------- Revert khi hủy/từ chối đơn đã duyệt ----------
    def test_refuse_reverts_schedule_changes(self):
        leave = self._confirmed_leave()
        self._add_resolutions(leave, sub_state='accepted')
        leave.action_approve()
        leave.action_refuse()
        # Buổi hủy → về planned
        self.assertEqual(self.s_off.state, 'planned')
        self.assertFalse(self.s_off.source_leave_id)
        # Buổi dạy thay → trả GV gốc
        self.assertEqual(self.s_sub.state, 'planned')
        self.assertEqual(self.s_sub.employee_id, self.teacher)
        self.assertFalse(self.s_sub.source_leave_id)

    # ---------- Đơn thường (không có buổi dạy) duyệt bình thường ----------
    def test_normal_leave_approves_without_resolutions(self):
        leave = self._confirmed_leave()
        leave.action_approve()
        self.assertEqual(leave.state, 'validate')
