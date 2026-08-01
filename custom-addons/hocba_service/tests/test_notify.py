# ============================================================
# P5 — hb.notification producers + cron quá hạn (SPEC SVC §8).
# Owner: Nhật Anh.
#
# Hai nhóm kiểm khác nhau:
#  - Định tuyến: ai nhận kind nào, tab nào (chuông bấm vào phải nhảy đúng chỗ).
#  - Ẩn danh: §9.1 case 5 — NỘI DUNG thông báo không lộ tên/phòng, và
#    create_uid của chính dòng hb.notification cũng không lộ (người nhận đọc
#    được dòng thông báo của mình ⇒ đọc luôn được create_uid của nó).
# ============================================================
from odoo import SUPERUSER_ID
from odoo.tests.common import tagged

from .common import ServiceCase


@tagged('post_install', '-at_install')
class TestServiceNotify(ServiceCase):

    def setUp(self):
        super().setUp()
        self.Notif = self.env['hb.notification'].sudo()

    # ----------------------------------------------------------- helpers

    def _notifs(self, user, kind=None, req=None):
        dom = [('recipient_id', '=', user.id), ('category', '=', 'service')]
        if kind:
            dom.append(('kind', '=', kind))
        if req is not None:
            dom.append(('target_ref', '=', req.id))
        return self.Notif.search(dom)

    def _text(self, notif):
        return '%s %s' % (notif.title or '', notif.body or '')

    # ------------------------------------------------- định tuyến người nhận

    def test_new_request_to_hr_notifies_hr_not_manager(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        hit = self._notifs(self.user_hr, 'service_new', req)
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit.target_view, 'service')
        self.assertEqual(hit.target_tab, 'inbox')
        self.assertEqual(hit.target_ref, req.id)
        # TP của phòng người gửi KHÔNG nhận — đơn không vào hộp thư họ.
        self.assertFalse(self._notifs(self.user_mgr_big, req=req))

    def test_new_request_to_manager_notifies_manager_not_hr(self):
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        self.assertEqual(len(self._notifs(self.user_mgr_big, 'service_new', req)), 1)
        # BR-SVC-13: HR không giám sát đơn gửi TP ⇒ cũng không nhận chuông.
        self.assertFalse(self._notifs(self.user_hr, req=req))
        self.assertFalse(self._notifs(self.user_hr_mgr, req=req))

    def test_new_request_both_notifies_both_sides(self):
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='both')
        self.assertTrue(self._notifs(self.user_hr, 'service_new', req))
        self.assertTrue(self._notifs(self.user_mgr_big, 'service_new', req))

    def test_force_hr_only_never_pings_manager(self):
        """BR-SVC-01/10: khiếu nại về quản lý ép về HR — TP tuyệt đối không
        được biết là có đơn (chuông là đường rò rõ nhất)."""
        req = self._send(self.user_sender, type_id=self.type_complaint.id,
                         recipient_scope='manager')
        self.assertTrue(self._notifs(self.user_hr, 'service_new', req))
        self.assertFalse(self._notifs(self.user_mgr_big, req=req))

    def test_sender_does_not_notify_himself(self):
        """HR tự gửi đơn cho HR thì không tự rung chuông của mình."""
        self.emp_big_3.user_id = self.user_hr.id
        req = self._send(self.user_hr, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        self.assertFalse(self._notifs(self.user_hr, 'service_new', req))
        self.assertTrue(self._notifs(self.user_hr_mgr, 'service_new', req))

    # ------------------------------------------------------------ vòng đời

    def test_claim_notifies_sender(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        hit = self._notifs(self.user_sender, 'service_claimed', req)
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit.target_tab, 'mine')

    def test_handler_reply_notifies_sender(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('Đã nhận, em chờ nhé.')
        hit = self._notifs(self.user_sender, 'service_reply', req)
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit.target_tab, 'mine')

    def test_internal_note_does_not_notify_sender(self):
        """BR-SVC-07: ghi chú nội bộ người gửi không đọc được ⇒ càng không
        được rung chuông họ (tiêu đề thông báo cũng là nội dung rò)."""
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('Nội bộ: hỏi kế toán', is_internal=True)
        self.assertFalse(self._notifs(self.user_sender, 'service_reply', req))

    def test_sender_reply_notifies_handler_only(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_sender).post_message('Em bổ sung thêm ạ.')
        hit = self._notifs(self.user_hr, 'service_reply', req)
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit.target_tab, 'inbox')
        # Đơn đã có người nhận ⇒ HR còn lại không bị làm phiền.
        self.assertFalse(self._notifs(self.user_hr_mgr, 'service_reply', req))

    def test_sender_reply_on_unclaimed_notifies_all_recipients(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_sender).post_message('Em bổ sung thêm ạ.')
        self.assertTrue(self._notifs(self.user_hr, 'service_reply', req))
        self.assertTrue(self._notifs(self.user_hr_mgr, 'service_reply', req))

    def test_answer_notifies_sender(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('Giấy đã ký, mời anh nhận.')
        req.with_user(self.user_hr).action_answer()
        self.assertEqual(
            len(self._notifs(self.user_sender, 'service_answered', req)), 1)

    def test_close_by_handler_notifies_sender(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).action_close('Đã bàn giao trực tiếp.')
        self.assertEqual(
            len(self._notifs(self.user_sender, 'service_closed', req)), 1)

    def test_close_by_sender_notifies_handler_not_sender(self):
        """Người gửi tự đóng thì đừng báo lại chính họ — báo người đang xử lý
        để họ khỏi làm tiếp việc đã thừa."""
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_sender).action_close('Em tự giải quyết được rồi.')
        self.assertTrue(self._notifs(self.user_hr, 'service_closed', req))
        self.assertFalse(self._notifs(self.user_sender, 'service_closed', req))

    # ---------------------------------------------------- ẩn danh (§9.1 c.5)

    def test_anon_notification_body_hides_identity(self):
        req = self._send_feedback_anon(self.user_sender, subject='Góp ý bãi xe')
        hit = self._notifs(self.user_hr, 'service_new', req)
        self.assertTrue(hit)
        text = self._text(hit)
        self.assertNotIn(self.emp_sender.name, text)
        self.assertNotIn(self.dept_big.name, text)
        self.assertNotIn(self.user_sender.name, text)
        # Vẫn đủ dùng: mã đơn + tiêu đề để bấm vào đúng đơn.
        self.assertIn(req.name, text)
        self.assertIn('Góp ý bãi xe', text)

    def test_anon_sender_reply_notification_hides_identity(self):
        req = self._send_feedback_anon(self.user_sender)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_sender).post_message('Em nói rõ thêm ạ.')
        hit = self._notifs(self.user_hr, 'service_reply', req)
        self.assertTrue(hit)
        text = self._text(hit)
        self.assertNotIn(self.emp_sender.name, text)
        self.assertNotIn(self.dept_big.name, text)

    def test_anon_notification_create_uid_is_odoobot(self):
        """Dòng hb.notification do người gửi ẩn danh kích hoạt phải mang
        create_uid = OdooBot. ir.rule của hb.notification cho người nhận đọc
        dòng của chính mình ⇒ HR đọc được create_uid; để nguyên uid của NV là
        lộ danh tính y hệt lớp L2 trên đơn."""
        req = self._send_feedback_anon(self.user_sender)
        hit = self._notifs(self.user_hr, 'service_new', req)
        self.assertTrue(hit)
        self.assertEqual(hit.create_uid.id, SUPERUSER_ID)

    # ------------------------------------------------------------- cron

    def _make_overdue(self, req):
        """Đẩy hạn về quá khứ. deadline là compute-store nên ghi thẳng được
        (đúng cách seed dữ liệu demo ở §10.4); invalidate vì is_overdue không
        store."""
        req.sudo().write({'deadline': '2020-01-01 00:00:00'})
        req.invalidate_recordset(['is_overdue'])
        return req

    def test_cron_notifies_handler_of_overdue(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        self._make_overdue(req)
        self.Request._cron_overdue_reminder()
        hit = self._notifs(self.user_hr, 'service_overdue', req)
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit.target_tab, 'inbox')

    def test_cron_notifies_all_recipients_when_unclaimed(self):
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        self._make_overdue(req)
        self.Request._cron_overdue_reminder()
        self.assertTrue(self._notifs(self.user_mgr_big, 'service_overdue', req))
        self.assertFalse(self._notifs(self.user_hr, 'service_overdue', req))

    def test_cron_does_not_duplicate_unread_reminder(self):
        """dedup_key: chạy 3 ngày liền vẫn chỉ 1 dòng chưa đọc, không dồn đống."""
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        self._make_overdue(req)
        for _i in range(3):
            self.Request._cron_overdue_reminder()
        self.assertEqual(
            len(self._notifs(self.user_hr, 'service_overdue', req)), 1)

    def test_cron_skips_answered_and_closed(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('Đã xử lý xong.')
        req.with_user(self.user_hr).action_answer()
        self._make_overdue(req)
        self.Request._cron_overdue_reminder()
        self.assertFalse(self._notifs(self.user_hr, 'service_overdue', req))

    def test_cron_anon_reminder_hides_identity(self):
        req = self._send_feedback_anon(self.user_sender)
        self._make_overdue(req)
        self.Request._cron_overdue_reminder()
        text = self._text(self._notifs(self.user_hr, 'service_overdue', req))
        self.assertTrue(text.strip())
        self.assertNotIn(self.emp_sender.name, text)
        self.assertNotIn(self.dept_big.name, text)
