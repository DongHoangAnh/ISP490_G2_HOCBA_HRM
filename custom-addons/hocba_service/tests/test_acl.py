# ============================================================
# SPEC SVC §9.2 — phạm vi đọc hộp thư. Gọi thẳng helper cấp module
# (_svc_scope / _inbox_domain) theo quy ước test của repo.
#
# Lưu ý bản chất: Trưởng phòng KHÔNG có group riêng và KHÔNG có ACL trên
# hocba.hr.request ⇒ phạm vi của TP do _inbox_domain quyết định, không do ACL.
# ============================================================
from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.hocba_service.models.hocba_hr_request import (
    _inbox_domain, _svc_scope,
)

from .common import ServiceCase


@tagged('post_install', '-at_install')
class TestServiceAcl(ServiceCase):

    def _inbox_ids(self, user):
        scope = _svc_scope(self.env(user=user))
        return self.Request.sudo().search(_inbox_domain(scope)).ids

    # ----------------------------------------------------------- vai trò

    def test_scope_flags(self):
        self.assertTrue(_svc_scope(self.env(user=self.user_hr))['isHr'])
        self.assertFalse(_svc_scope(self.env(user=self.user_hr))['isHrManager'])
        self.assertTrue(_svc_scope(self.env(user=self.user_hr_mgr))['isHrManager'])
        mgr = _svc_scope(self.env(user=self.user_mgr_big))
        self.assertTrue(mgr['isDeptManager'])
        self.assertFalse(mgr['isHr'])
        self.assertIn(self.dept_big.id, mgr['deptIds'])
        nv = _svc_scope(self.env(user=self.user_sender))
        self.assertFalse(nv['canHandle'])

    # --- case 10/11: NV thường không có hộp thư và không có ACL ---
    def test_plain_employee_has_empty_inbox(self):
        self._send(self.user_sender, type_id=self.type_confirm_work.id)
        self.assertEqual(self._inbox_ids(self.user_sender), [])

    def test_plain_employee_has_no_acl_on_request(self):
        self._send(self.user_sender, type_id=self.type_confirm_work.id)
        with self.assertRaises(AccessError):
            self.Request.with_user(self.user_sender).search([])

    # --- case 8: TP không đọc được đơn phòng khác ---
    def test_manager_cannot_see_other_department(self):
        req = self._send(
            self.user_sender, type_id=self.type_proposal.id,
            recipient_scope='manager')
        self.assertIn(req.id, self._inbox_ids(self.user_mgr_big))
        self.assertNotIn(req.id, self._inbox_ids(self.user_mgr_other))
        self.assertFalse(req.with_user(self.user_mgr_other)._can_handle())
        with self.assertRaises(AccessError):
            req.with_user(self.user_mgr_other).action_claim()

    # --- case 9: BR-SVC-01/10 — đơn khiếu nại quản lý ---
    def test_complaint_invisible_to_own_manager(self):
        req = self._send(
            self.user_sender, type_id=self.type_complaint.id,
            is_anonymous=True)
        # force_hr_only ⇒ luôn về HR bất kể người gửi chọn gì.
        self.assertEqual(req.sudo().recipient_scope, 'hr')
        self.assertNotIn(req.id, self._inbox_ids(self.user_mgr_big))
        self.assertIn(req.id, self._inbox_ids(self.user_hr))
        self.assertFalse(req.with_user(self.user_mgr_big)._can_handle())

    def test_complaint_forced_hr_even_if_manager_requested(self):
        req = self._send(
            self.user_sender, type_id=self.type_complaint.id,
            recipient_scope='manager')
        self.assertEqual(req.sudo().recipient_scope, 'hr')
        self.assertFalse(req.sudo().target_department_id)

    # --- case 12: TP thấy đơn 'both' của phòng mình ---
    def test_manager_sees_both_scope_of_own_dept(self):
        req = self._send(
            self.user_sender, type_id=self.type_proposal.id,
            recipient_scope='both')
        self.assertIn(req.id, self._inbox_ids(self.user_mgr_big))
        self.assertIn(req.id, self._inbox_ids(self.user_hr))

    # --- case 12b/12c: BR-SVC-13 — HR không giám sát TP ---
    def test_hr_manager_does_not_see_manager_only_requests(self):
        req = self._send(
            self.user_sender, type_id=self.type_proposal.id,
            recipient_scope='manager')
        self.assertNotIn(
            req.id, self._inbox_ids(self.user_hr_mgr),
            'BR-SVC-13: HR Manager không giám sát đơn gửi riêng Trưởng phòng')
        self.assertNotIn(req.id, self._inbox_ids(self.user_hr))

    def test_hr_who_is_also_manager_sees_own_dept_manager_requests(self):
        # HR Manager đồng thời là TP dept_other → đọc với tư cách TP.
        self.emp_mgr_other.user_id = self.user_hr_mgr.id
        emp_in_other = self._mk_emp(
            'NV Khác svc', '139000000001', self.dept_other)
        user_other = self._mk_user('svc_other_nv', emp_in_other)
        req = self._send(
            user_other, type_id=self.type_proposal.id,
            recipient_scope='manager')
        self.assertIn(req.id, self._inbox_ids(self.user_hr_mgr))
