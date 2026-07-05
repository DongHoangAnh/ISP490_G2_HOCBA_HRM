# ============================================================
# Test — Đổi lịch dạy chuyền tiếp (A→B→C), trả buổi, hủy/rút có chặn chuỗi.
# Owner: Nhật Anh. Spec: 2026-06-26-timeoff-teaching-handover-chain-cancel §9.
# ============================================================
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _upcoming_teaching_sessions, _find_teaching_conflicts, _return_substitution,
)


@tagged('post_install', '-at_install')
class TestHandoverChain(TransactionCase):

    def setUp(self):
        super().setUp()
        # Ngày tương lai cố định để _upcoming_teaching_sessions (hôm nay→+28) ổn định.
        self.sdate = date.today() + timedelta(days=7)
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
        self.Notif = self.env['hb.leave.notification']

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

    # ---------- §9.3: C trả buổi → về B, báo B, đơn B bị từ chối ----------
    def test_return_top_reverts_to_previous(self):
        l_a, _ = self._handover(self.A, self.B)
        l_b, res_c = self._handover(self.B, self.C)
        out = _return_substitution(self.env, res_c.id, self.C)
        self.assertTrue(out)
        self.assertEqual(self.session.employee_id, self.B)
        self.assertEqual(self.session.state, 'substituted')
        self.assertEqual(self.session.source_leave_id, l_a)
        self.assertEqual(res_c.state, 'returned')
        # Đơn của B (chỉ buổi này) không còn buổi hiệu lực → tự từ chối, không lỗi.
        self.assertEqual(l_b.state, 'refuse')
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_returned')])
        self.assertEqual(len(n), 1)

    # ---------- §9.4: trả buổi giữa chuỗi bị chặn ----------
    def test_return_middle_blocked(self):
        _, res_b = self._handover(self.A, self.B)
        self._handover(self.B, self.C)  # C đang giữ buổi
        out = _return_substitution(self.env, res_b.id, self.B)
        self.assertFalse(out)
        self.assertEqual(self.session.employee_id, self.C)
        self.assertEqual(res_b.state, 'accepted')

    # ---------- §9.5: pop về gốc → planned ----------
    def test_return_to_original_planned(self):
        _, res_b = self._handover(self.A, self.B)
        out = _return_substitution(self.env, res_b.id, self.B)
        self.assertTrue(out)
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        self.assertFalse(self.session.source_leave_id)

    # ---------- B trả buổi cho A → đơn A bị từ chối + A xin nghỉ lại được ----------
    def test_return_refuses_origin_leave_and_frees_session(self):
        l_a, res_b = self._handover(self.A, self.B)
        self.assertEqual(l_a.state, 'validate')
        out = _return_substitution(self.env, res_b.id, self.B)
        self.assertTrue(out)
        # Đơn của A chuyển 'Từ chối'.
        self.assertEqual(l_a.state, 'refuse')
        self.assertEqual(res_b.state, 'returned')
        # Buổi về A, planned → A xin nghỉ lại được (guard chặn-trùng trả rỗng).
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        dup = self.Res.search([
            ('session_id', '=', self.session.id),
            ('leave_id.state', 'in', ['confirm', 'validate1', 'validate']),
            ('state', 'in', ['pending', 'accepted']),
        ])
        self.assertFalse(dup)

    # ---------- Đơn nhiều buổi: trả 1 buổi → giữ đơn, chỉ buổi đó được giải phóng ----------
    def test_multisession_return_keeps_leave_other_sessions(self):
        session2 = self.env['hocba.teaching.session'].create({
            'cms_session_id': 'HC-2', 'employee_id': self.A.id,
            'class_name': 'LY', 'session_date': self.sdate,
            'start_time': '14:00', 'end_time': '16:00'})
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ 2 buổi', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.A.id,
            'request_date_from': self.sdate, 'request_date_to': self.sdate})
        if leave.state == 'draft':
            leave.action_confirm()
        r1 = self.Res.create({'leave_id': leave.id, 'session_id': self.session.id,
                              'resolution': 'substitute', 'substitute_id': self.B.id})
        r2 = self.Res.create({'leave_id': leave.id, 'session_id': session2.id,
                              'resolution': 'substitute', 'substitute_id': self.B.id})
        r1.state = 'accepted'
        r2.state = 'accepted'
        leave.action_approve()
        self.assertEqual(self.session.employee_id, self.B)
        self.assertEqual(session2.employee_id, self.B)

        # B trả buổi 1 → đơn còn buổi 2 hiệu lực → đơn GIỮ 'validate'.
        out = _return_substitution(self.env, r1.id, self.B)
        self.assertTrue(out)
        self.assertEqual(leave.state, 'validate')
        self.assertEqual(r1.state, 'returned')
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        # Buổi 2 vẫn do B giữ.
        self.assertEqual(session2.employee_id, self.B)
        self.assertEqual(r2.state, 'accepted')
        # Buổi 1 đã giải phóng (xin nghỉ lại được) dù đơn vẫn validate.
        dup = self.Res.search([
            ('session_id', '=', self.session.id),
            ('leave_id.state', 'in', ['confirm', 'validate1', 'validate']),
            ('state', 'in', ['pending', 'accepted']),
        ])
        self.assertFalse(dup)

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
