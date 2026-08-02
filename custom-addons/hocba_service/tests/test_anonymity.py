# ============================================================
# SPEC SVC §9.1 — nhóm test QUAN TRỌNG NHẤT: ẩn danh mức 2.
# Mỗi test ở đây tương ứng một đường rò danh tính đã lường trước (§4.2).
# ============================================================
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import ServiceCase


@tagged('post_install', '-at_install')
class TestServiceAnonymity(ServiceCase):

    # --- case 1: payload API không chứa danh tính ---
    def test_anon_payload_hides_identity_from_hr(self):
        req = self._send_feedback_anon()
        data = req.with_user(self.user_hr).serialize(
            viewer_is_sender=False, with_messages=True)
        self.assertTrue(data['isAnonymous'])
        self.assertEqual(data['senderName'], 'Người gửi (ẩn danh)')
        self.assertIsNone(data['departmentName'])
        self.assertNotIn(self.emp_sender.name, str(data))

    # --- case 2: đơn KHÔNG có field người gửi ---
    def test_request_model_has_no_sender_field(self):
        fields_ = self.Request.fields_get()
        for fname in ('employee_id', 'user_id', 'sender_id', 'sender_ids'):
            self.assertNotIn(
                fname, fields_,
                'hocba.hr.request không được có field %s — danh tính phải nằm '
                'ở bảng tách rời (SPEC §3.1)' % fname)
        # Không field nào trỏ tới bảng danh tính.
        for fname, meta in fields_.items():
            self.assertNotEqual(
                meta.get('relation'), 'hocba.hr.request.sender',
                'Field %s làm lộ đường tới bảng danh tính' % fname)

    # --- case 3: bảng danh tính không cấp ACL cho group nào ---
    def test_sender_table_unreadable_even_for_hr_manager(self):
        self._send_feedback_anon()
        with self.assertRaises(AccessError):
            self.Sender.with_user(self.user_hr_mgr).search([])
        with self.assertRaises(AccessError):
            self.Sender.with_user(self.user_hr).search([])
        with self.assertRaises(AccessError):
            self.Sender.with_user(self.user_mgr_big).search([])

    def test_no_acl_row_grants_sender_table(self):
        """Chặn hồi quy: ai đó thêm 1 dòng ACL cho bảng danh tính là phá toàn bộ
        cơ chế ẩn danh."""
        acls = self.env['ir.model.access'].sudo().search(
            [('model_id.model', '=', 'hocba.hr.request.sender')])
        self.assertFalse(
            acls, 'hocba.hr.request.sender phải KHÔNG có dòng ACL nào — thêm '
                  'ACL cho bất kỳ group nào là phá vỡ ẩn danh mức 2')

    # --- case 4: create_uid / write_uid không phải nhân viên ---
    def test_anon_create_uid_is_odoobot(self):
        req = self._send_feedback_anon()
        self.assertEqual(
            req.sudo().create_uid.id, 1,
            '.sudo() giữ nguyên env.uid nên phải tạo bằng with_user('
            'SUPERUSER_ID) — nếu không create_uid chỉ thẳng người gửi')
        row = self.Sender.sudo().search([('request_id', '=', req.id)])
        self.assertEqual(row.create_uid.id, 1)

    def test_anon_sender_cancel_does_not_leak_write_uid(self):
        req = self._send_feedback_anon()
        req.with_user(self.user_sender).action_cancel()
        self.assertEqual(req.sudo().state, 'cancelled')
        self.assertEqual(
            req.sudo().write_uid.id, 1,
            'Người gửi rút đơn ẩn danh mà write_uid = NV thì lộ ngay ai gửi')

    def test_anon_sender_message_create_uid_is_odoobot(self):
        req = self._send_feedback_anon()
        msg = req.with_user(self.user_sender).post_message('bổ sung thêm ý')
        self.assertEqual(msg.sudo().create_uid.id, 1)

    # --- case 6: tên người viết trong hội thoại ---
    def test_anon_thread_author_masked_for_handler(self):
        req = self._send_feedback_anon()
        req.with_user(self.user_sender).post_message('ý kiến của em')
        data = req.with_user(self.user_hr).serialize(
            viewer_is_sender=False, with_messages=True)
        sender_msgs = [m for m in data['messages'] if m['authorRole'] == 'sender']
        self.assertTrue(sender_msgs)
        for m in sender_msgs:
            self.assertEqual(m['authorName'], 'Người gửi (ẩn danh)')
            self.assertNotIn(self.emp_sender.name, m['authorName'])

    def test_handler_name_visible_to_sender(self):
        """Ẩn danh là một chiều: người XỬ LÝ không ẩn danh, để NV biết ai đang
        trả lời mình."""
        req = self._send_feedback_anon()
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('HR đã tiếp nhận')
        data = req.with_user(self.user_sender).serialize(with_messages=True)
        handler_msgs = [m for m in data['messages'] if m['authorRole'] == 'handler']
        self.assertEqual(handler_msgs[0]['authorName'], self.user_hr.name)
        self.assertEqual(data['handlerName'], self.user_hr.name)

    # --- case 7: người gửi thấy đúng đơn của mình ---
    def test_my_requests_scoped_to_sender(self):
        from odoo.addons.hocba_service.models.hocba_hr_request import (
            _my_request_ids,
        )
        mine = self._send_feedback_anon()
        other = self._send_feedback_anon(user=self.user_small)
        ids_sender = _my_request_ids(self.env(user=self.user_sender))
        self.assertIn(mine.id, ids_sender)
        self.assertNotIn(other.id, ids_sender)
        ids_other = _my_request_ids(self.env(user=self.user_small))
        self.assertIn(other.id, ids_other)
        self.assertNotIn(mine.id, ids_other)

    # --- không ẩn danh thì phải hiện tên (đối chứng) ---
    def test_non_anon_shows_identity(self):
        req = self._send(
            self.user_sender, type_id=self.type_confirm_work.id,
            recipient_scope='hr')
        data = req.with_user(self.user_hr).serialize(viewer_is_sender=False)
        self.assertFalse(data['isAnonymous'])
        self.assertEqual(data['senderName'], self.emp_sender.name)
        self.assertEqual(data['departmentName'], self.dept_big.name)
