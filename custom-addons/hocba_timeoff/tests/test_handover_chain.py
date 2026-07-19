# ============================================================
# Test — Đổi lịch dạy chuyền tiếp (A→B→C), hủy/rút có chặn chuỗi.
# Mô hình "không trả lại" (spec §12, sửa 2026-07-17): GV thay bận thì tự xử lý
# tiến (hủy lớp / nhờ GV khác), KHÔNG trả buổi cho GV cũ. Buổi chỉ quay ngược khi
# chính chủ đơn rút/từ chối đơn của mình.
# Owner: Nhật Anh. Spec: 2026-06-26-timeoff-teaching-handover-chain-cancel §9,§12.
# ============================================================
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _upcoming_teaching_sessions, _find_teaching_conflicts,
    _sessions_requestable_error,
)


@tagged('post_install', '-at_install')
class TestHandoverChain(TransactionCase):

    def setUp(self):
        super().setUp()
        # Ngày tương lai cố định để _upcoming_teaching_sessions (hôm nay→+28) ổn định.
        # Né T7/CN: lịch làm việc chuẩn không có ca cuối tuần → hr_holidays chặn
        # duyệt đơn ("not supposed to work during that period") nếu rơi cuối tuần.
        self.sdate = date.today() + timedelta(days=7)
        while self.sdate.weekday() >= 5:
            self.sdate += timedelta(days=1)
        U = self.env['res.users']
        self.uA = U.create({'name': 'UA', 'login': 'hc_ua'})
        self.uB = U.create({'name': 'UB', 'login': 'hc_ub'})
        self.uC = U.create({'name': 'UC', 'login': 'hc_uc'})
        E = self.env['hr.employee']
        self.A = E.create({'name': 'GV A', 'x_cms_user_id': 'HC_A', 'user_id': self.uA.id})
        self.B = E.create({'name': 'GV B', 'x_cms_user_id': 'HC_B', 'user_id': self.uB.id})
        self.C = E.create({'name': 'GV C', 'x_cms_user_id': 'HC_C', 'user_id': self.uC.id})
        self.session = self.env['hocba.teaching.session'].create({
            'cms_session_id': 'HC-1', 'employee_id': self.A.id,
            'class_name': 'LX', 'session_date': self.sdate,
            'start_time': '08:00', 'end_time': '10:00'})
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        self.Res = self.env['hocba.leave.session.resolution']
        self.Notif = self.env['hb.notification']

    def _leave_for(self, emp, resolution='substitute', sub=None, state='accepted'):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': emp.id,
            'request_date_from': self.sdate, 'request_date_to': self.sdate})
        if leave.state == 'draft':
            leave.action_confirm()
        vals = {'leave_id': leave.id, 'session_id': self.session.id,
                'resolution': resolution}
        if resolution == 'substitute':
            vals['substitute_id'] = sub.id
        r = self.Res.create(vals)
        if resolution == 'substitute' and state != 'pending':
            r.state = state
        return leave, r

    def _handover(self, frm, to):
        """Tạo đơn của `frm`, gắn substitute `to` (accepted), duyệt → áp lịch."""
        leave, r = self._leave_for(frm, sub=to, state='accepted')
        leave.action_approve()
        return leave, r

    # ---------- §9.2: chuỗi A→B→C ----------
    def test_chain_apply(self):
        self._handover(self.A, self.B)
        self.assertEqual(self.session.employee_id, self.B)
        l_b, _ = self._handover(self.B, self.C)
        self.assertEqual(self.session.employee_id, self.C)
        self.assertEqual(self.session.state, 'substituted')
        self.assertEqual(self.session.source_leave_id, l_b)

    # ---------- §9.1: chủ mới thấy buổi; chủ cũ không còn thấy ----------
    def test_visibility_follows_owner(self):
        self._handover(self.A, self.B)
        self.assertIn(self.session, _upcoming_teaching_sessions(self.env, self.B))
        self.assertNotIn(self.session, _upcoming_teaching_sessions(self.env, self.A))
        conf_b = _find_teaching_conflicts(self.env, self.B, self.sdate, self.sdate)
        self.assertIn(self.session, conf_b)

    # ---------- §10 (MỚI): chủ hiện tại buổi substituted tự xử lý tiến ----------
    def test_owner_can_self_handle_substituted_session(self):
        # A→B (apply): B là chủ buổi 'substituted'. B được đưa chính buổi đó vào
        # đơn nghỉ-theo-buổi MỚI (hủy lớp / nhờ GV khác) — không cần trả về A.
        self._handover(self.A, self.B)
        self.assertEqual(self.session.state, 'substituted')
        sessions, err = _sessions_requestable_error(
            self.env, self.B, [self.session.id])
        self.assertIsNone(err)
        self.assertEqual(sessions, self.session)

    # ---------- §11 (MỚI): chủ cũ không đưa được buổi đã giao vào đơn mới ----------
    def test_previous_owner_cannot_request_handed_session(self):
        # A→B: A không còn là chủ hiện tại → buổi không hợp lệ cho đơn mới của A.
        self._handover(self.A, self.B)
        sessions, err = _sessions_requestable_error(
            self.env, self.A, [self.session.id])
        self.assertIsNone(sessions)
        self.assertEqual(err[0], 'invalid_session')

    # ---------- Chặn-trùng bỏ qua mắt xích đang sở hữu, chặn mắt xích tiến khác ----------
    def test_self_handle_dup_check_ignores_ownership_link(self):
        # A→B: buổi 'substituted', source_leave = đơn A (mắt xích đưa buổi cho B).
        # Lần đầu B tạo đơn tiến: hợp lệ (bỏ qua đơn A). Sau khi B đã có 1 đơn
        # tiến pending cho buổi này → lần tạo tiếp bị chặn 'session_already_requested'.
        l_a, _ = self._handover(self.A, self.B)
        # B tạo mắt xích tiến B→C (pending, chưa duyệt).
        l_b = self.env['hr.leave'].create({
            'name': 'B bận', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.B.id,
            'request_date_from': self.sdate, 'request_date_to': self.sdate})
        if l_b.state == 'draft':
            l_b.action_confirm()
        self.Res.create({'leave_id': l_b.id, 'session_id': self.session.id,
                         'resolution': 'substitute', 'substitute_id': self.C.id})
        # Đơn A (mắt xích đang sở hữu) không tính trùng; nhưng đơn B tiến đang
        # pending thì chặn đơn tiến thứ hai của B cho cùng buổi.
        sessions, err = _sessions_requestable_error(
            self.env, self.B, [self.session.id])
        self.assertIsNone(sessions)
        self.assertEqual(err[0], 'session_already_requested')

    # ---------- §9.7: rút đơn đã duyệt → revert + báo GV thay ----------
    def test_refuse_reverts_and_notifies_substitute(self):
        l_a, _ = self._handover(self.A, self.B)
        l_a.action_refuse()
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_cancelled')])
        self.assertEqual(len(n), 1)

    # ---------- §9.8: chặn rút khi buổi đã giao tiếp xuống dưới ----------
    def test_refuse_blocked_when_downstream_exists(self):
        l_a, _ = self._handover(self.A, self.B)
        self._handover(self.B, self.C)  # buổi giờ do C giữ
        with self.assertRaises(ValidationError):
            l_a.action_refuse()
        self.assertEqual(self.session.employee_id, self.C)

    # ---------- §9.9: class_off → refuse trả về planned ----------
    def test_class_off_refuse_reverts_planned(self):
        leave, _ = self._leave_for(self.A, resolution='class_off')
        leave.action_approve()
        self.assertEqual(self.session.state, 'cancelled')
        leave.action_refuse()
        self.assertEqual(self.session.state, 'planned')

    # ---------- §9.6: refuse đơn pending (chưa áp) → không revert/không lỗi ----------
    def test_refuse_pending_leave_no_revert(self):
        leave, _ = self._leave_for(self.A, sub=self.B, state='accepted')
        # KHÔNG approve → đơn chưa áp lịch.
        leave.action_refuse()
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')

    # ---------- Helper báo hủy đơn pending ----------
    def test_notify_sub_cancelled_helper(self):
        leave, r = self._leave_for(self.A, sub=self.B, state='pending')
        leave._notify_sub_cancelled(r)
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_cancelled')])
        self.assertEqual(len(n), 1)
