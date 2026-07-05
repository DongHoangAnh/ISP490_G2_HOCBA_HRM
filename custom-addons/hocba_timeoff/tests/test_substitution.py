# ============================================================
# Test Step 5 — Workflow GV dạy thay: liệt kê yêu cầu, đồng ý/từ chối,
# chuông thông báo (sub_request / sub_accepted / sub_declined). Owner: Nhật Anh.
# Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict-design §6.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _apply_resolutions, _substitution_rows, _decide_substitution,
)


@tagged('post_install', '-at_install')
class TestSubstitution(TransactionCase):

    def setUp(self):
        super().setUp()
        self.req_user = self.env['res.users'].create({
            'name': 'Req GV', 'login': 'req_gv_sub_test'})
        self.sub_user = self.env['res.users'].create({
            'name': 'Sub GV', 'login': 'sub_gv_sub_test'})
        self.teacher = self.env['hr.employee'].create({
            'name': 'GV Req', 'x_cms_user_id': 'CMS_S1',
            'user_id': self.req_user.id})
        self.sub = self.env['hr.employee'].create({
            'name': 'GV Sub', 'x_cms_user_id': 'CMS_S2',
            'user_id': self.sub_user.id})
        self.session = self.env['hocba.teaching.session'].create({
            'cms_session_id': 'S-1', 'employee_id': self.teacher.id,
            'class_name': 'LK', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00'})
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        self.leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.teacher.id,
            'request_date_from': '2026-07-06', 'request_date_to': '2026-07-06'})
        self.Notif = self.env['hb.notification']

    def _make_sub_resolution(self):
        rows = _apply_resolutions(self.env, self.leave, self.session, [
            {'sessionId': self.session.id, 'type': 'substitute',
             'substituteId': self.sub.id}])
        return rows

    # ---------- Tạo dòng dạy thay → báo chuông cho GV thay ----------
    def test_apply_notifies_substitute(self):
        self._make_sub_resolution()
        n = self.Notif.search([
            ('recipient_id', '=', self.sub_user.id), ('kind', '=', 'sub_request')])
        self.assertEqual(len(n), 1)
        self.assertEqual(n.target_ref, self.leave.id)

    # ---------- Liệt kê yêu cầu dạy thay gửi tới mình ----------
    def test_substitution_rows_lists_pending(self):
        self._make_sub_resolution()
        rows = _substitution_rows(self.env, self.sub)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['state'], 'pending')
        self.assertEqual(rows[0]['requester'], 'GV Req')
        self.assertEqual(rows[0]['className'], 'LK')

    # ---------- Đồng ý dạy thay ----------
    def test_decide_accept(self):
        r = self._make_sub_resolution()
        out = _decide_substitution(self.env, r.id, self.sub, True)
        self.assertEqual(out.state, 'accepted')
        self.assertTrue(out.decided_at)
        n = self.Notif.search([
            ('recipient_id', '=', self.req_user.id), ('kind', '=', 'sub_accepted')])
        self.assertEqual(len(n), 1)

    # ---------- Từ chối dạy thay + lý do ----------
    def test_decide_decline_with_reason(self):
        r = self._make_sub_resolution()
        out = _decide_substitution(self.env, r.id, self.sub, False, 'Bận lịch')
        self.assertEqual(out.state, 'declined')
        self.assertEqual(out.decline_reason, 'Bận lịch')
        n = self.Notif.search([
            ('recipient_id', '=', self.req_user.id), ('kind', '=', 'sub_declined')])
        self.assertEqual(len(n), 1)

    # ---------- Không phải GV thay của mình → từ chối thao tác ----------
    def test_decide_wrong_employee(self):
        r = self._make_sub_resolution()
        out = _decide_substitution(self.env, r.id, self.teacher, True)
        self.assertFalse(out)
        self.assertEqual(r.state, 'pending')

    # ---------- Đã xử lý rồi → không cho quyết lại ----------
    def test_decide_non_pending(self):
        r = self._make_sub_resolution()
        _decide_substitution(self.env, r.id, self.sub, True)
        out = _decide_substitution(self.env, r.id, self.sub, False)
        self.assertFalse(out)
        self.assertEqual(r.state, 'accepted')
