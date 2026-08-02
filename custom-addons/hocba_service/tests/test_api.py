# ============================================================
# SPEC SVC §6 — lớp API. Repo KHÔNG dùng HttpCase ở đâu cả (18 file test của
# hocba_timeoff đều gọi thẳng helper cấp module của controllers.main), nên test
# ở đây cũng gọi helper cấp module với self.env(user=...). Đổi lại, phải có 1
# test soi bảng route để lỗi đánh máy đường dẫn / thiếu csrf=False không lọt.
# ============================================================
import base64

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.hocba_service.controllers.main import (
    HocBaService, MAX_FILES, MAX_SIZE_BYTES, _attachment_owner,
    _create_from_payload, _detail_payload, _inbox_payload, _meta_payload,
    _my_requests_payload, _stats_payload, _visible_request,
)

from .common import ServiceCase

PDF_B64 = base64.b64encode(b'%PDF-1.4 noi dung test').decode()


@tagged('post_install', '-at_install')
class TestServiceApi(ServiceCase):

    def _assert_code(self, ctx, code):
        self.assertEqual(getattr(ctx.exception, 'code', None), code)

    def _env(self, user):
        return self.env(user=user)

    # ------------------------------------------------------------- /meta

    def test_meta_for_plain_employee(self):
        data = _meta_payload(self._env(self.user_sender))
        self.assertFalse(data['canHandle'])
        self.assertTrue(data['canSend'])
        self.assertGreaterEqual(len(data['types']), 9)
        self.assertEqual(data['minAnonDeptSize'], 5)
        self.assertEqual(data['anonDailyLimit'], 3)
        self.assertEqual(data['anonUsedToday'], 0)
        self.assertEqual(data['myDepartment']['id'], self.dept_big.id)
        self.assertEqual(data['myDepartment']['headcount'], 6)
        self.assertFalse(data['myDepartment']['iAmManager'])

    def test_meta_type_payload_carries_form_rules(self):
        types = {t['code']: t for t in
                 _meta_payload(self._env(self.user_sender))['types']}
        self.assertTrue(types['feedback']['allowAnonymous'])
        self.assertFalse(types['feedback']['allowAttachment'])
        self.assertTrue(types['feedback']['hasRating'])
        self.assertTrue(types['complaint_mgr']['forceHrOnly'])
        self.assertFalse(types['confirm_work']['allowAnonymous'])
        self.assertEqual(types['confirm_work']['slaDays'],
                         self.type_confirm_work.sla_days)

    def test_meta_flags_for_hr_and_manager(self):
        hr = _meta_payload(self._env(self.user_hr))
        self.assertTrue(hr['isHr'])
        self.assertTrue(hr['canHandle'])
        mgr = _meta_payload(self._env(self.user_mgr_big))
        self.assertTrue(mgr['isDeptManager'])
        self.assertTrue(mgr['canHandle'])
        self.assertTrue(mgr['myDepartment']['iAmManager'])

    def test_meta_anon_used_today_reflects_quota(self):
        self._send_feedback_anon()
        self._send_feedback_anon()
        data = _meta_payload(self._env(self.user_sender))
        self.assertEqual(data['anonUsedToday'], 2)

    def test_meta_small_dept_lets_form_block_locally(self):
        """§7.3: form phải chặn ẩn danh-gửi-TP tại chỗ, nên meta phải đủ dữ
        liệu để so sánh (headcount < minAnonDeptSize)."""
        data = _meta_payload(self._env(self.user_small))
        self.assertLess(data['myDepartment']['headcount'],
                        data['minAnonDeptSize'])

    # ---------------------------------------------------------- POST /request

    def test_create_maps_camel_case_payload(self):
        req = _create_from_payload(self._env(self.user_sender), {
            'typeId': self.type_confirm_work.id,
            'subject': 'Xin giấy xác nhận công tác',
            'body': 'Em cần 2 bản.',
            'recipientScope': 'hr',
            'priority': 'urgent',
        })
        rec = req.sudo()
        self.assertEqual(rec.type_id, self.type_confirm_work)
        self.assertEqual(rec.recipient_scope, 'hr')
        self.assertEqual(rec.priority, 'urgent')
        self.assertEqual(rec.state, 'new')

    def test_create_maps_rating_and_anonymous(self):
        req = _create_from_payload(self._env(self.user_sender), {
            'typeId': self.type_feedback.id,
            'subject': 'Góp ý', 'body': 'Nội dung góp ý',
            'recipientScope': 'hr', 'isAnonymous': True, 'rating': 4,
        })
        self.assertEqual(req.sudo().rating, '4')
        self.assertTrue(req.sudo().is_anonymous)

    def test_create_propagates_business_error_code(self):
        """Mã lỗi của model phải tới được lớp HTTP nguyên vẹn — _guarded()
        map e.code sang body {'error': code}."""
        with self.assertRaises(ValidationError) as ctx:
            _create_from_payload(self._env(self.user_sender), {
                'typeId': self.type_confirm_work.id,
                'subject': 'x', 'body': 'y', 'isAnonymous': True,
            })
        self._assert_code(ctx, 'anon_not_allowed')

    def test_create_ignores_client_supplied_attachment_ids(self):
        """Không nhận `attachmentIds`: cho client tự chọn id là lỗ hổng (gắn
        attachment của người khác rồi tải về qua /service/attachment/<id>)."""
        other = self.env['ir.attachment'].sudo().create({
            'name': 'cua-nguoi-khac.pdf', 'datas': PDF_B64,
            'mimetype': 'application/pdf'})
        req = _create_from_payload(self._env(self.user_sender), {
            'typeId': self.type_confirm_work.id,
            'subject': 'x', 'body': 'y',
            'attachmentIds': [other.id],
        })
        self.assertFalse(req.sudo().attachment_ids)

    # ------------------------------------------------------------ đính kèm

    def test_create_with_attachment(self):
        req = _create_from_payload(self._env(self.user_sender), {
            'typeId': self.type_confirm_work.id,
            'subject': 'Xin sao y', 'body': 'kèm đơn',
            'attachments': [{'name': 'don.pdf',
                             'mimetype': 'application/pdf', 'data': PDF_B64}],
        })
        atts = req.sudo().attachment_ids
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts.res_model, 'hocba.hr.request')
        self.assertEqual(atts.res_id, req.id)
        payload = req.serialize(viewer_is_sender=True)
        self.assertEqual(payload['attachments'][0]['url'],
                         '/hocba-hrm/api/service/attachment/%d' % atts.id)

    def test_attachment_bad_mimetype_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            _create_from_payload(self._env(self.user_sender), {
                'typeId': self.type_confirm_work.id,
                'subject': 'x', 'body': 'y',
                'attachments': [{'name': 'virus.exe',
                                 'mimetype': 'application/x-msdownload',
                                 'data': PDF_B64}],
            })
        self._assert_code(ctx, 'bad_mimetype')

    def test_attachment_undecodable_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            _create_from_payload(self._env(self.user_sender), {
                'typeId': self.type_confirm_work.id,
                'subject': 'x', 'body': 'y',
                'attachments': [{'name': 'a.pdf',
                                 'mimetype': 'application/pdf',
                                 'data': 'khong-phai-base64!!!'}],
            })
        self._assert_code(ctx, 'bad_attachment')

    def test_attachment_too_large_rejected(self):
        big = base64.b64encode(b'\0' * (MAX_SIZE_BYTES + 1)).decode()
        with self.assertRaises(ValidationError) as ctx:
            _create_from_payload(self._env(self.user_sender), {
                'typeId': self.type_confirm_work.id,
                'subject': 'x', 'body': 'y',
                'attachments': [{'name': 'to.pdf',
                                 'mimetype': 'application/pdf', 'data': big}],
            })
        self._assert_code(ctx, 'file_too_large')

    def test_too_many_files_rejected(self):
        files = [{'name': 'f%d.pdf' % i, 'mimetype': 'application/pdf',
                  'data': PDF_B64} for i in range(MAX_FILES + 1)]
        with self.assertRaises(ValidationError) as ctx:
            _create_from_payload(self._env(self.user_sender), {
                'typeId': self.type_confirm_work.id,
                'subject': 'x', 'body': 'y', 'attachments': files,
            })
        self._assert_code(ctx, 'too_many_files')

    def test_attachment_rolled_back_when_request_refused(self):
        """Hợp đồng mà _guarded() dựa vào: controller BẮT lỗi và trả 400 ⇒ Odoo
        vẫn commit transaction, không savepoint thì ir.attachment vừa tạo bị
        commit mồ côi. Test chính cái savepoint đó."""
        Att = self.env['ir.attachment'].sudo()
        before = Att.search_count([])
        env = self._env(self.user_sender)
        with self.assertRaises(ValidationError):
            with env.cr.savepoint():
                _create_from_payload(env, {
                    'typeId': self.type_feedback.id,   # loại này cấm đính kèm
                    'subject': 'x', 'body': 'y',
                    'attachments': [{'name': 'don.pdf',
                                     'mimetype': 'application/pdf',
                                     'data': PDF_B64}],
                })
        self.assertEqual(Att.search_count([]), before)

    def test_attachment_owner_lookup(self):
        req = _create_from_payload(self._env(self.user_sender), {
            'typeId': self.type_confirm_work.id,
            'subject': 'x', 'body': 'y',
            'attachments': [{'name': 'don.pdf',
                             'mimetype': 'application/pdf', 'data': PDF_B64}],
        })
        att = req.sudo().attachment_ids
        self.assertEqual(_attachment_owner(self.env, att).id, req.id)

    # ------------------------------------------------------- /my-requests

    def test_my_requests_scoped_and_filtered(self):
        r1 = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        r2 = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        r2.with_user(self.user_sender).action_cancel()
        self._send(self.user_small, type_id=self.type_confirm_work.id)

        mine = _my_requests_payload(self._env(self.user_sender))
        ids = [r['id'] for r in mine['requests']]
        self.assertCountEqual(ids, [r1.id, r2.id])

        opened = _my_requests_payload(self._env(self.user_sender), state='open')
        self.assertEqual([r['id'] for r in opened['requests']], [r1.id])

        cancelled = _my_requests_payload(
            self._env(self.user_sender), state='cancelled')
        self.assertEqual([r['id'] for r in cancelled['requests']], [r2.id])

    def test_my_requests_year_filter_and_years_list(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        year = req.sudo().create_date.year
        data = _my_requests_payload(self._env(self.user_sender), year=year)
        self.assertIn(req.id, [r['id'] for r in data['requests']])
        self.assertEqual(data['years'], [year])
        other = _my_requests_payload(self._env(self.user_sender), year=year - 5)
        self.assertEqual(other['requests'], [])

    def test_my_requests_empty_for_user_without_requests(self):
        data = _my_requests_payload(self._env(self.user_mgr_other))
        self.assertEqual(data, {'requests': [], 'years': []})

    def test_my_requests_anon_payload_keeps_identity_hidden(self):
        """Ngay cả payload của CHÍNH người gửi cũng không mang tên/phòng ra —
        để payload 2 phía không lệch nhau (BR-SVC-08)."""
        self._send_feedback_anon()
        data = _my_requests_payload(self._env(self.user_sender))
        row = data['requests'][0]
        self.assertIsNone(row['departmentName'])
        self.assertNotIn(self.emp_sender.name, str(row))
        self.assertNotIn(self.dept_big.name, str(row))

    # -------------------------------------------------------------- /inbox

    def test_inbox_forbidden_for_plain_employee(self):
        with self.assertRaises(AccessError):
            _inbox_payload(self._env(self.user_sender))

    def test_inbox_hr_sees_hr_scope_only(self):
        to_hr = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        to_mgr = self._send(self.user_sender, type_id=self.type_proposal.id,
                            recipient_scope='manager')
        data = _inbox_payload(self._env(self.user_hr))
        ids = [r['id'] for r in data['requests']]
        self.assertIn(to_hr.id, ids)
        self.assertNotIn(to_mgr.id, ids)     # BR-SVC-13
        mgr_ids = [r['id'] for r in
                   _inbox_payload(self._env(self.user_mgr_big))['requests']]
        self.assertIn(to_mgr.id, mgr_ids)

    def test_inbox_state_filter(self):
        r1 = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        r2 = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        r2.with_user(self.user_hr).action_claim()
        new_ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr), state='new')['requests']]
        self.assertIn(r1.id, new_ids)
        self.assertNotIn(r2.id, new_ids)
        open_ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr), state='open')['requests']]
        self.assertIn(r1.id, open_ids)
        self.assertIn(r2.id, open_ids)

    def test_inbox_overdue_filter(self):
        fresh = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        late = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        late.sudo().write({'deadline': '2020-01-01 00:00:00'})
        ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr), overdue=True)['requests']]
        self.assertIn(late.id, ids)
        self.assertNotIn(fresh.id, ids)

    def test_inbox_type_filter(self):
        a = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        b = self._send_feedback_anon()
        ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr),
            type_id=self.type_feedback.id)['requests']]
        self.assertIn(b.id, ids)
        self.assertNotIn(a.id, ids)

    def test_inbox_keyword_search(self):
        # Từ khoá ASCII: ilike của Postgres phụ thuộc collation với ký tự
        # nhiều byte, không muốn test xanh/đỏ theo locale của máy chạy.
        hit = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         subject='Xin giay di DAI SU QUAN')
        miss = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                          subject='Hoi bang luong')
        ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr), q='dai su quan')['requests']]
        self.assertIn(hit.id, ids)
        self.assertNotIn(miss.id, ids)

    def test_inbox_keyword_search_keeps_scope(self):
        """Filter tìm kiếm phải AND với domain phạm vi, không được nong nó ra."""
        to_mgr = self._send(self.user_sender, type_id=self.type_proposal.id,
                            recipient_scope='manager',
                            subject='De xuat TU KHOA RIENG')
        ids = [r['id'] for r in _inbox_payload(
            self._env(self.user_hr), q='tu khoa rieng')['requests']]
        self.assertNotIn(to_mgr.id, ids)

    def test_inbox_anon_rows_have_no_identity(self):
        self._send_feedback_anon()
        data = _inbox_payload(self._env(self.user_hr))
        row = next(r for r in data['requests'] if r['isAnonymous'])
        self.assertIsNone(row['departmentName'])
        self.assertNotIn(self.emp_sender.name, str(row))

    # ----------------------------------------------------- /request/<id>

    def test_detail_for_sender_hides_internal_note(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req.with_user(self.user_hr).action_claim()
        req.with_user(self.user_hr).post_message('nội bộ', is_internal=True)
        req.with_user(self.user_hr).post_message('trả lời NV')
        data = _detail_payload(self._env(self.user_sender), req.id)
        bodies = [m['body'] for m in data['messages']]
        self.assertEqual(bodies, ['trả lời NV'])
        hr_bodies = [m['body'] for m in
                     _detail_payload(self._env(self.user_hr),
                                     req.id)['messages']]
        self.assertIn('nội bộ', hr_bodies)

    def test_detail_forbidden_for_outsider(self):
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        with self.assertRaises(AccessError):
            _detail_payload(self._env(self.user_mgr_other), req.id)

    def test_detail_missing_returns_none(self):
        self.assertIsNone(
            _detail_payload(self._env(self.user_hr), 999999999))

    def test_detail_anon_payload_has_no_identity(self):
        req = self._send_feedback_anon()
        data = _detail_payload(self._env(self.user_hr), req.id)
        self.assertIsNone(data['departmentName'])
        self.assertNotIn(self.emp_sender.name, str(data))
        self.assertNotIn(self.dept_big.name, str(data))

    def test_visible_request_role_detection(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        _rec, is_sender = _visible_request(self._env(self.user_sender), req.id)
        self.assertTrue(is_sender)
        _rec, is_sender = _visible_request(self._env(self.user_hr), req.id)
        self.assertFalse(is_sender)
        rec, _s = _visible_request(self._env(self.user_hr), 999999999)
        self.assertIsNone(rec)

    # -------------------------------------------------------------- /stats

    def test_stats_forbidden_for_plain_employee(self):
        with self.assertRaises(AccessError):
            _stats_payload(self._env(self.user_sender))

    # Đo BIẾN THIÊN, không đo số tuyệt đối: hộp thư HR trong DB thật (và DB
    # local sau khi seed demo) luôn có đơn tồn đọng, số tuyệt đối sẽ đỏ theo
    # môi trường — đúng thứ common.py đã cảnh báo với 2 ir.config_parameter.
    def test_stats_counts_and_averages(self):
        before = _stats_payload(self._env(self.user_hr))
        done = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        done.with_user(self.user_hr).action_claim()
        done.with_user(self.user_hr).post_message('xong rồi')
        done.with_user(self.user_hr).action_answer()
        late = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        late.sudo().write({'deadline': '2020-01-01 00:00:00'})
        anon = self._send_feedback_anon(rating='5')

        data = _stats_payload(self._env(self.user_hr))
        self.assertEqual(data['total'] - before['total'], 3)
        self.assertEqual(data['open'] - before['open'], 2)
        self.assertEqual(data['overdue'] - before['overdue'], 1)
        self.assertEqual(data['anonymous'] - before['anonymous'], 1)
        self.assertEqual(data['ratedCount'] - before['ratedCount'], 1)
        self.assertIsNotNone(data['avgHandleHours'])
        # Trung bình cộng cũng kiểm được chính xác: suy ra kỳ vọng từ 'before'.
        old_n, old_avg = before['ratedCount'], before['avgRating'] or 0
        self.assertAlmostEqual(
            data['avgRating'], (old_avg * old_n + 5) / (old_n + 1), places=2)
        by_type = {r['typeId']: r['count'] for r in data['byType']}
        old_by_type = {r['typeId']: r['count'] for r in before['byType']}
        for type_id, delta in ((self.type_confirm_work.id, 2),
                               (self.type_feedback.id, 1)):
            self.assertEqual(
                by_type.get(type_id, 0) - old_by_type.get(type_id, 0), delta)
        self.assertIn(anon.id, [r['id'] for r in _inbox_payload(
            self._env(self.user_hr))['requests']])

    def test_stats_respects_br_svc_13(self):
        """Đơn gửi Trưởng phòng không được tính vào KPI của HR Manager."""
        before = _stats_payload(self._env(self.user_hr_mgr))['total']
        self._send(self.user_sender, type_id=self.type_proposal.id,
                   recipient_scope='manager')
        self.assertEqual(
            _stats_payload(self._env(self.user_hr_mgr))['total'], before)
        # dept_big do setUp tạo nên chỉ có đúng đơn của test này.
        self.assertEqual(_stats_payload(self._env(self.user_mgr_big))['total'], 1)

    def test_stats_empty_inbox_has_no_division_by_zero(self):
        """Dùng TP của phòng setUp tự tạo — hộp thư chắc chắn rỗng ở MỌI DB
        (hộp thư HR thì không, vì DB thật luôn có đơn tồn đọng)."""
        data = _stats_payload(self._env(self.user_mgr_other))
        self.assertEqual(data['total'], 0)
        self.assertIsNone(data['avgHandleHours'])
        self.assertIsNone(data['avgRating'])

    # -------------------------------------------------- bảng route đã khai

    def test_all_spec_routes_registered(self):
        declared = {}
        for name in dir(HocBaService):
            routing = getattr(
                getattr(HocBaService, name), 'original_routing', None)
            if not routing:
                continue
            for path in routing.get('routes', []):
                declared[path] = routing
        base = '/hocba-hrm/api/service'
        expected_get = [
            '%s/meta' % base,
            '%s/my-requests' % base,
            '%s/inbox' % base,
            '%s/request/<int:rid>' % base,
            '%s/stats' % base,
            '%s/attachment/<int:att_id>' % base,
            '%s/config/types' % base,
        ]
        expected_post = [
            '%s/request' % base,
            '%s/config/types/save' % base,
            '%s/config/types/toggle-active' % base,
            '%s/config/params' % base,
            '%s/request/<int:rid>/reply' % base,
            '%s/request/<int:rid>/claim' % base,
            '%s/request/<int:rid>/answer' % base,
            '%s/request/<int:rid>/close' % base,
            '%s/request/<int:rid>/cancel' % base,
        ]
        for path in expected_get + expected_post:
            self.assertIn(path, declared, 'thiếu route %s' % path)
            self.assertEqual(declared[path].get('auth'), 'user', path)
            self.assertEqual(declared[path].get('type'), 'http', path)
        for path in expected_get:
            self.assertEqual(declared[path].get('methods'), ['GET'], path)
        for path in expected_post:
            self.assertEqual(declared[path].get('methods'), ['POST'], path)
            # SPA gọi bằng fetch JSON, không có token CSRF của Odoo.
            self.assertFalse(declared[path].get('csrf'), path)
