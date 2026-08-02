# ============================================================
# P6 — màn Cấu hình loại yêu cầu + 2 ngưỡng ir.config_parameter (SPEC SVC §10,
# dòng P6). Owner: Nhật Anh.
#
# Ba nhóm kiểm:
#  - Quyền: chỉ HR Manager / Admin. HR User (hr.group_hr_user) và NV thường KHÔNG
#    được sửa danh mục — họ chỉ đọc qua /meta.
#  - Nghiệp vụ danh mục: mã trùng/sai định dạng, SLA > 0, BR-SVC-09 (ẩn danh +
#    đính kèm), BR-SVC-01 (force_hr_only phải mặc định HR), không tắt loại cuối.
#  - Tác động lên đơn ĐANG CHẠY: tắt loại không được làm đơn cũ biến mất khỏi
#    hộp thư; hạ SLA không được đẩy đơn cũ thành quá hạn (đơn chốt SLA lúc gửi).
# ============================================================
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.hocba_service.controllers.main import (
    _config_payload, _inbox_payload, _meta_payload,
)
from odoo.addons.hocba_service.models.hocba_hr_request import (
    DEFAULT_ANON_DAILY, DEFAULT_MIN_ANON_DEPT,
    PARAM_ANON_DAILY, PARAM_MIN_ANON_DEPT, _param_int,
)

from .common import ServiceCase


@tagged('post_install', '-at_install')
class TestServiceConfig(ServiceCase):

    def setUp(self):
        super().setUp()
        self.Type = self.env['hocba.hr.request.type']

    # ----------------------------------------------------------- helpers

    def _as(self, user):
        return self.Type.with_user(user)

    def _env(self, user):
        return self.env(user=user)

    def _assert_code(self, ctx, code):
        self.assertEqual(getattr(ctx.exception, 'code', None), code)

    def _new_type_vals(self, **over):
        vals = {
            'name': 'Loại mới P6',
            'code': 'p6_new',
            'sequence': 90,
            'defaultRecipient': 'hr',
            'slaDays': 4,
            'description': 'Mô tả loại mới',
        }
        vals.update(over)
        return vals

    def _codes(self, payload):
        return {t['code']: t for t in payload['types']}

    # -------------------------------------------------------------- quyền

    def test_hr_manager_reads_config(self):
        data = _config_payload(self._env(self.user_hr_mgr))
        self.assertTrue(data['canConfig'])
        self.assertGreaterEqual(len(data['types']), 9)
        self.assertEqual(data['params']['minAnonDeptSize'], 5)
        self.assertEqual(data['params']['anonDailyLimit'], 3)

    def test_hr_user_cannot_read_config(self):
        """HR User xử lý đơn nhưng KHÔNG được đổi luật của danh mục."""
        with self.assertRaises(AccessError):
            _config_payload(self._env(self.user_hr))

    def test_employee_and_manager_cannot_read_config(self):
        with self.assertRaises(AccessError):
            _config_payload(self._env(self.user_sender))
        with self.assertRaises(AccessError):
            _config_payload(self._env(self.user_mgr_big))

    def test_hr_user_cannot_save_toggle_or_set_params(self):
        with self.assertRaises(AccessError):
            self._as(self.user_hr).config_save(self._new_type_vals())
        with self.assertRaises(AccessError):
            self._as(self.user_hr).config_toggle_active(
                self.type_confirm_work.id, False)
        with self.assertRaises(AccessError):
            self._as(self.user_hr).config_set_params({'anonDailyLimit': 9})

    def test_meta_exposes_can_config_flag(self):
        self.assertTrue(_meta_payload(self._env(self.user_hr_mgr))['canConfig'])
        self.assertFalse(_meta_payload(self._env(self.user_hr))['canConfig'])
        self.assertFalse(_meta_payload(self._env(self.user_sender))['canConfig'])

    # ------------------------------------------------------ thêm / sửa loại

    def test_create_type_appears_in_meta_and_is_sendable(self):
        rt = self._as(self.user_hr_mgr).config_save(self._new_type_vals())
        self.assertTrue(rt.active)
        self.assertIn('p6_new', self._codes(
            {'types': _meta_payload(self._env(self.user_sender))['types']}))
        req = self._send(self.user_sender, type_id=rt.id)
        self.assertEqual(req.type_id, rt)
        self.assertEqual(req.sla_days, 4)

    def test_edit_type_patches_only_given_keys(self):
        self._as(self.user_hr_mgr).config_save({
            'id': self.type_confirm_work.id, 'slaDays': 7})
        self.assertEqual(self.type_confirm_work.sla_days, 7)
        self.assertEqual(self.type_confirm_work.code, 'confirm_work')
        self.assertEqual(self.type_confirm_work.default_recipient, 'hr')

    def test_config_payload_counts_usage(self):
        self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req2 = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        req2.with_user(self.user_hr).action_claim()
        req2.with_user(self.user_hr).post_message('xong')
        req2.with_user(self.user_hr).action_answer()
        row = self._codes(_config_payload(self._env(self.user_hr_mgr)))['confirm_work']
        self.assertGreaterEqual(row['usageCount'], 2)
        # openCount đếm đơn còn phải xử lý — cảnh báo trước khi Admin tắt loại.
        self.assertGreaterEqual(row['openCount'], 1)
        self.assertLess(row['openCount'], row['usageCount'])

    def test_duplicate_code_refused(self):
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(
                self._new_type_vals(code='confirm_work'))
        self._assert_code(ctx, 'code_duplicate')

    def test_duplicate_code_refused_against_inactive_type(self):
        """Mã của loại ĐÃ TẮT vẫn chiếm chỗ (unique index không lọc active)."""
        rt = self._as(self.user_hr_mgr).config_save(self._new_type_vals())
        self._as(self.user_hr_mgr).config_toggle_active(rt.id, False)
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(
                self._new_type_vals(name='Trùng mã'))
        self._assert_code(ctx, 'code_duplicate')

    def test_keeping_own_code_is_not_duplicate(self):
        self._as(self.user_hr_mgr).config_save({
            'id': self.type_confirm_work.id, 'code': 'confirm_work',
            'name': 'Xin giấy xác nhận công tác (sửa)'})
        self.assertEqual(self.type_confirm_work.name,
                         'Xin giấy xác nhận công tác (sửa)')

    def test_code_normalized_and_validated(self):
        rt = self._as(self.user_hr_mgr).config_save(
            self._new_type_vals(code='  P6_Xin_Nghi  '))
        self.assertEqual(rt.code, 'p6_xin_nghi')
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(
                self._new_type_vals(code='mã có dấu!'))
        self._assert_code(ctx, 'code_invalid')

    def test_name_and_code_required(self):
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(name='  '))
        self._assert_code(ctx, 'name_required')
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(code=''))
        self._assert_code(ctx, 'code_required')

    def test_sla_must_be_positive(self):
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(slaDays=0))
        self._assert_code(ctx, 'sla_invalid')
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(slaDays=-3))
        self._assert_code(ctx, 'sla_invalid')

    def test_recipient_must_be_valid(self):
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save(
                self._new_type_vals(defaultRecipient='sếp tổng'))
        self._assert_code(ctx, 'scope_invalid')

    def test_anonymous_plus_attachment_refused(self):
        """BR-SVC-09 — tiêu chí hoàn thành P6. Đính kèm ghi create_uid nên bật
        cả hai là mở đường lộ người gửi ẩn danh."""
        with self.assertRaises(ValidationError):
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(
                allowAnonymous=True, allowAttachment=True))
        self.assertFalse(self.Type.with_context(active_test=False).search(
            [('code', '=', 'p6_new')]))

    def test_turning_on_anonymous_for_existing_type_refused_if_attachment_on(self):
        with self.assertRaises(ValidationError):
            self._as(self.user_hr_mgr).config_save({
                'id': self.type_confirm_work.id, 'allowAnonymous': True})
        self.type_confirm_work.invalidate_recordset(['allow_anonymous'])
        self.assertFalse(self.type_confirm_work.allow_anonymous)

    def test_force_hr_only_requires_hr_default(self):
        """BR-SVC-01: loại 'khiếu nại về quản lý' mà mặc định gửi TP là vô nghĩa."""
        with self.assertRaises(ValidationError):
            self._as(self.user_hr_mgr).config_save(self._new_type_vals(
                forceHrOnly=True, defaultRecipient='manager'))

    def test_unknown_type_id_refused(self):
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_save({'id': 987654321, 'slaDays': 2})
        self._assert_code(ctx, 'type_invalid')

    # ---------------------------------------------------------- bật / tắt

    def test_toggle_off_hides_type_from_form_and_blocks_new_requests(self):
        self._as(self.user_hr_mgr).config_toggle_active(
            self.type_confirm_work.id, False)
        codes = {t['code'] for t in
                 _meta_payload(self._env(self.user_sender))['types']}
        self.assertNotIn('confirm_work', codes)
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self._assert_code(ctx, 'type_invalid')

    def test_toggle_back_on(self):
        self._as(self.user_hr_mgr).config_toggle_active(
            self.type_confirm_work.id, False)
        self._as(self.user_hr_mgr).config_toggle_active(
            self.type_confirm_work.id, True)
        self.assertTrue(self.type_confirm_work.active)
        self.assertIn('confirm_work', {
            t['code'] for t in _meta_payload(self._env(self.user_sender))['types']})

    def test_toggle_off_keeps_existing_requests_in_manager_inbox(self):
        """Tắt loại là ẩn khỏi FORM GỬI, không phải xoá đơn đang chạy: TP vẫn
        phải thấy đơn cũ, nếu không đơn thành mồ côi giữa vòng đời."""
        req = self._send(self.user_sender, type_id=self.type_proposal.id,
                         recipient_scope='manager')
        self._as(self.user_hr_mgr).config_toggle_active(self.type_proposal.id, False)
        ids = [r['id'] for r in
               _inbox_payload(self._env(self.user_mgr_big))['requests']]
        self.assertIn(req.id, ids)

    def test_toggle_off_keeps_existing_requests_in_hr_inbox(self):
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id,
                         recipient_scope='hr')
        self._as(self.user_hr_mgr).config_toggle_active(
            self.type_confirm_work.id, False)
        ids = [r['id'] for r in _inbox_payload(self._env(self.user_hr))['requests']]
        self.assertIn(req.id, ids)

    def test_cannot_turn_off_last_active_type(self):
        """Tắt hết loại thì không ai gửi được đơn nữa — chặn ở nước cuối cùng."""
        others = self.Type.search([('id', '!=', self.type_confirm_work.id)])
        for rt in others:
            self._as(self.user_hr_mgr).config_toggle_active(rt.id, False)
        with self.assertRaises(ValidationError) as ctx:
            self._as(self.user_hr_mgr).config_toggle_active(
                self.type_confirm_work.id, False)
        self._assert_code(ctx, 'last_active_type')
        self.assertTrue(self.type_confirm_work.active)

    # ------------------------------------------------------- 2 ngưỡng config

    def test_set_params_persists_and_takes_effect(self):
        self._as(self.user_hr_mgr).config_set_params(
            {'minAnonDeptSize': 3, 'anonDailyLimit': 1})
        self.assertEqual(
            _param_int(self.env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT), 3)
        self.assertEqual(
            _param_int(self.env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY), 1)
        data = _meta_payload(self._env(self.user_sender))
        self.assertEqual(data['minAnonDeptSize'], 3)
        self.assertEqual(data['anonDailyLimit'], 1)

    def test_lowering_min_dept_size_unblocks_small_department(self):
        """Đúng kịch bản demo (§2.2): phòng 3 NV bị chặn ẩn danh, Admin hạ
        ngưỡng ở màn Cấu hình là gửi được — không sửa code, không sửa test."""
        with self.assertRaises(ValidationError) as ctx:
            self._send(self.user_small, type_id=self.type_feedback.id,
                       is_anonymous=True, recipient_scope='manager')
        self._assert_code(ctx, 'anon_dept_too_small')
        self._as(self.user_hr_mgr).config_set_params({'minAnonDeptSize': 3})
        req = self._send(self.user_small, type_id=self.type_feedback.id,
                         is_anonymous=True, recipient_scope='manager')
        self.assertTrue(req.is_anonymous)

    def test_set_params_rejects_bad_values(self):
        for bad in ({'minAnonDeptSize': 0}, {'anonDailyLimit': 0},
                    {'minAnonDeptSize': -2}, {'anonDailyLimit': 'nhiều'},
                    {'minAnonDeptSize': 10000}):
            with self.assertRaises(ValidationError) as ctx:
                self._as(self.user_hr_mgr).config_set_params(bad)
            self._assert_code(ctx, 'param_invalid')
        # Không có giá trị nào bị ghi nửa vời.
        self.assertEqual(
            _param_int(self.env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT), 5)
        self.assertEqual(
            _param_int(self.env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY), 3)

    def test_set_params_patches_only_given_key(self):
        self._as(self.user_hr_mgr).config_set_params({'anonDailyLimit': 7})
        self.assertEqual(
            _param_int(self.env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT), 5)
        self.assertEqual(
            _param_int(self.env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY), 7)

    # --------------------------------------------- SLA chốt lúc gửi (§10.6)

    def test_changing_type_sla_does_not_move_deadline_of_existing_requests(self):
        """deadline cũ là CAM KẾT với người gửi. Nếu deadline bám sát
        type_id.sla_days thì Admin hạ SLA sẽ đẩy hàng loạt đơn đang chạy thành
        quá hạn và cron bắn thông báo oan."""
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        before = req.deadline
        self.assertEqual(req.sla_days, self.type_confirm_work.sla_days)
        self._as(self.user_hr_mgr).config_save({
            'id': self.type_confirm_work.id, 'slaDays': 1})
        req.invalidate_recordset(['deadline', 'sla_days', 'is_overdue'])
        self.assertEqual(req.deadline, before)
        self.assertFalse(req.is_overdue)

    def test_new_request_uses_new_sla(self):
        self._as(self.user_hr_mgr).config_save({
            'id': self.type_confirm_work.id, 'slaDays': 9})
        req = self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self.assertEqual(req.sla_days, 9)
        self.assertEqual((req.deadline - req.create_date).days, 9)
