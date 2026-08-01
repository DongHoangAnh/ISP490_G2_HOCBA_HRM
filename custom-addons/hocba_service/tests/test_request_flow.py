# ============================================================
# SPEC SVC §9.3 — nghiệp vụ gửi đơn + vòng đời + SLA.
# ============================================================
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.hocba_service.models.hocba_hr_request import (
    PARAM_MIN_ANON_DEPT, _inbox_domain, _svc_scope,
)

from .common import ServiceCase


@tagged('post_install', '-at_install')
class TestServiceRequestFlow(ServiceCase):

    def _assert_code(self, ctx, code):
        self.assertEqual(getattr(ctx.exception, 'code', None), code)

    # ------------------------------------------------- luật gửi đơn

    # case 13
    def test_anonymous_rejected_when_type_disallows(self):
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_sender, type_id=self.type_confirm_work.id,
                       is_anonymous=True)
        self._assert_code(ctx, 'anon_not_allowed')

    # case 14
    def test_attachment_rejected_on_anonymous(self):
        att = self.env['ir.attachment'].sudo().create({
            'name': 'bangchung.txt', 'datas': b'aGVsbG8='})
        with self.assertRaises(ValidationError) as ctx:
            self._send_feedback_anon(attachment_ids=[att.id])
        self._assert_code(ctx, 'attachment_not_allowed')

    # case 15
    def test_anon_to_manager_blocked_when_dept_too_small(self):
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_small, type_id=self.type_feedback.id,
                       is_anonymous=True, recipient_scope='manager')
        self._assert_code(ctx, 'anon_dept_too_small')

    # case 15b — chứng minh tham số cấu hình có tác dụng thật
    def test_anon_to_manager_allowed_after_lowering_threshold(self):
        self.Param.set_param(PARAM_MIN_ANON_DEPT, '3')
        req = self._send(self.user_small, type_id=self.type_feedback.id,
                         is_anonymous=True, recipient_scope='manager')
        self.assertEqual(req.sudo().recipient_scope, 'manager')
        self.assertEqual(req.sudo().target_department_id, self.dept_small)

    # case 15c / 15d — BR-SVC-12
    def test_anon_daily_limit(self):
        for _i in range(3):
            self._send_feedback_anon()
        with self.assertRaises(ValidationError) as ctx:
            self._send_feedback_anon()
        self._assert_code(ctx, 'anon_daily_limit')

    def test_daily_limit_does_not_apply_to_named_requests(self):
        for _i in range(3):
            self._send_feedback_anon()
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self.assertTrue(req.id)

    # case 15e — BR-SVC-03 sửa (§2.2.1)
    def test_anon_scope_both_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_sender, type_id=self.type_feedback.id,
                       is_anonymous=True, recipient_scope='both')
        self._assert_code(ctx, 'anon_scope_both')

    # case 15f — định tuyến vẫn sống sau khi sửa BR-SVC-03
    def test_anon_to_manager_reaches_that_manager(self):
        req = self._send(self.user_sender, type_id=self.type_feedback.id,
                         is_anonymous=True, recipient_scope='manager')
        scope = _svc_scope(self.env(user=self.user_mgr_big))
        found = self.Request.sudo().search(_inbox_domain(scope))
        self.assertIn(req.id, found.ids,
                      'Đơn ẩn danh gửi TP phải tới được hộp thư của TP đó')
        self.assertNotIn(req.id, self.Request.sudo().search(
            _inbox_domain(_svc_scope(self.env(user=self.user_hr)))).ids)

    # case 15g
    def test_anon_to_manager_hides_department_in_payload(self):
        req = self._send(self.user_sender, type_id=self.type_feedback.id,
                         is_anonymous=True, recipient_scope='manager')
        data = req.with_user(self.user_mgr_big).serialize(viewer_is_sender=False)
        self.assertIsNone(data['departmentName'])
        self.assertNotIn(self.dept_big.name, str(data))

    # case 16 — BR-SVC-04
    def test_manager_sending_to_own_dept_is_routed_to_hr(self):
        req = self._send(self.user_mgr_big, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        self.assertEqual(req.sudo().recipient_scope, 'hr')
        self.assertFalse(req.sudo().target_department_id)

    # Phòng chưa có trưởng phòng → đơn sẽ không có ai trong hộp thư nào
    # (_inbox_domain lọc theo target_department_id của TP). Form P3 đã chặn,
    # nhưng gọi API trực tiếp thì vẫn tạo được đơn mồ côi ⇒ chốt ở model.
    def test_send_to_manager_rejected_when_dept_has_no_manager(self):
        self.dept_small.manager_id = False
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_small, type_id=self.type_proposal.id,
                       recipient_scope='manager')
        self._assert_code(ctx, 'dept_no_manager')

    def test_send_to_both_rejected_when_dept_has_no_manager(self):
        """'both' cũng bị chặn: im lặng hạ về HR = đổi người đọc đơn mà người
        gửi không biết, tệ hơn là báo lỗi rõ ràng."""
        self.dept_small.manager_id = False
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_small, type_id=self.type_proposal.id,
                       recipient_scope='both')
        self._assert_code(ctx, 'dept_no_manager')

    def test_send_to_hr_still_ok_when_dept_has_no_manager(self):
        self.dept_small.manager_id = False
        req = self._send(self.user_small, type_id=self.type_proposal.id,
                         recipient_scope='hr')
        self.assertEqual(req.sudo().recipient_scope, 'hr')

    def test_rating_rejected_when_type_has_none(self):
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_sender, type_id=self.type_confirm_work.id,
                       rating='5')
        self._assert_code(ctx, 'rating_not_allowed')

    def test_empty_content_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_sender, type_id=self.type_confirm_work.id,
                       subject='   ', body='')
        self._assert_code(ctx, 'content_required')

    # case 23
    def test_sequence_code(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self.assertTrue(req.sudo().name.startswith('YCDV/'))
        self.assertNotEqual(req.sudo().name, '/')

    # ------------------------------------------------- vòng đời

    def test_full_happy_path(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self.assertEqual(req.sudo().state, 'new')
        req.with_user(self.user_hr).action_claim()
        self.assertEqual(req.sudo().state, 'in_progress')
        self.assertEqual(req.sudo().handler_id, self.user_hr)
        req.with_user(self.user_hr).post_message('Giấy sẽ có sau 2 ngày')
        req.with_user(self.user_hr).action_answer()
        self.assertEqual(req.sudo().state, 'answered')
        req.with_user(self.user_hr).action_close('đã giao giấy')
        self.assertEqual(req.sudo().state, 'closed')
        self.assertEqual(req.sudo().closed_reason, 'đã giao giấy')

    # case 17
    def test_answer_requires_handler_reply(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        with self.assertRaises(ValidationError) as ctx:
            req.with_user(self.user_hr).action_answer()
        self._assert_code(ctx, 'no_handler_reply')

    def test_internal_note_does_not_count_as_reply(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('chờ ký', is_internal=True)
        with self.assertRaises(ValidationError) as ctx:
            req.with_user(self.user_hr).action_answer()
        self._assert_code(ctx, 'no_handler_reply')

    # case 18 — BR-SVC-05
    def test_second_handler_cannot_answer_claimed_request(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('đang làm')
        emp_hr2 = self._mk_emp('HR2 svc', '138000000001', self.dept_other)
        user_hr2 = self._mk_user(
            'svc_hr2', emp_hr2, groups=['hr.group_hr_user'])
        with self.assertRaises(AccessError):
            req.with_user(user_hr2).action_answer()
        # HR Manager thì được (điều phối khi người xử lý nghỉ).
        req.with_user(self.user_hr_mgr).action_answer()
        self.assertEqual(req.sudo().state, 'answered')

    # case 19 — BR-SVC-06
    def test_sender_reply_reopens_answered_request(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('đã xử lý')
        req.with_user(self.user_hr).action_answer()
        req.with_user(self.user_sender).post_message('em cần thêm 1 bản nữa')
        self.assertEqual(req.sudo().state, 'in_progress')

    # case 20
    def test_cancel_only_from_new(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        with self.assertRaises(ValidationError) as ctx:
            req.with_user(self.user_sender).action_cancel()
        self._assert_code(ctx, 'bad_state')

    def test_cancel_by_non_sender_refused(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        with self.assertRaises(AccessError):
            req.with_user(self.user_hr).action_cancel()

    def test_no_message_after_closed(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_sender).action_cancel()
        with self.assertRaises(ValidationError) as ctx:
            req.with_user(self.user_sender).post_message('thêm ý')
        self._assert_code(ctx, 'bad_state')

    def test_outsider_cannot_post_message(self):
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        with self.assertRaises(AccessError):
            req.with_user(self.user_mgr_other).post_message('xen vào')

    # case 21 — BR-SVC-07
    def test_internal_note_hidden_from_sender(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('ghi chú nội bộ', is_internal=True)
        req.with_user(self.user_hr).post_message('trả lời NV')
        sender_view = req.with_user(self.user_sender).serialize(with_messages=True)
        bodies = [m['body'] for m in sender_view['messages']]
        self.assertIn('trả lời NV', bodies)
        self.assertNotIn('ghi chú nội bộ', bodies)
        hr_view = req.with_user(self.user_hr).serialize(
            viewer_is_sender=False, with_messages=True)
        self.assertIn('ghi chú nội bộ', [m['body'] for m in hr_view['messages']])

    def test_sender_cannot_write_internal_note(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        msg = req.with_user(self.user_sender).post_message('thử', is_internal=True)
        self.assertFalse(msg.sudo().is_internal)
        self.assertEqual(msg.sudo().author_role, 'sender')

    # ------------------------------------------------- SLA (case 22)

    def test_deadline_follows_sla_days(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        rec = req.sudo()
        expected = rec.create_date + timedelta(days=self.type_confirm_work.sla_days)
        self.assertEqual(rec.deadline, expected)
        self.assertFalse(rec.is_overdue)

    def test_is_overdue_and_search(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        rec = req.sudo()
        rec.write({'deadline': fields.Datetime.now() - timedelta(days=1)})
        rec.invalidate_recordset(['is_overdue'])
        self.assertTrue(rec.is_overdue)
        self.assertIn(rec.id, self.Request.sudo().search(
            [('is_overdue', '=', True)]).ids)
        rec.write({'state': 'closed'})
        rec.invalidate_recordset(['is_overdue'])
        self.assertFalse(rec.is_overdue)
        self.assertNotIn(rec.id, self.Request.sudo().search(
            [('is_overdue', '=', True)]).ids)

    # ------------------------------------------------- danh mục (case 24)

    def test_type_anonymous_forbids_attachment(self):
        with self.assertRaises(ValidationError):
            self.env['hocba.hr.request.type'].sudo().create({
                'name': 'Loại sai svc', 'code': 'bad_svc_type',
                'allow_anonymous': True, 'allow_attachment': True})

    def test_type_sla_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.env['hocba.hr.request.type'].sudo().create({
                'name': 'Loại SLA 0', 'code': 'bad_sla_svc', 'sla_days': 0})

    def test_seed_types_installed(self):
        types = self.env['hocba.hr.request.type'].sudo().search([])
        self.assertGreaterEqual(len(types), 9)
        self.assertTrue(self.type_complaint.force_hr_only)
        self.assertTrue(self.type_feedback.allow_anonymous)
        self.assertFalse(self.type_feedback.allow_attachment)
