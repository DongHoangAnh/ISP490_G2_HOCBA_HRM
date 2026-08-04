"""Thông báo chuông cho vòng duyệt phiếu yêu cầu tuyển dụng.

Vai theo sheet quy trình 7.1: TBP order → HR duyệt.
  TBP bấm Gửi duyệt   → HR / BP tuyển dụng nhận chuông
  HR bấm Duyệt        → người tạo phiếu (TBP) nhận chuông
  HR bấm Từ chối      → người tạo phiếu nhận chuông, kèm lý do
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRequestNotify(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        grp_rec = cls.env.ref('hr_recruitment.group_hr_recruitment_user')
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR duyệt phiếu (test)', 'login': 'test_hr_duyet_phieu',
            'group_ids': [(4, grp_rec.id)],
        })
        # HR Manager KHÔNG thuộc nhóm Tuyển dụng nhưng vẫn duyệt được phiếu
        # (_is_hr) ⇒ phải nhận chuông. Ca thật: test_hrmanager@hocba.vn.
        cls.user_hrm = cls.env['res.users'].create({
            'name': 'HR Manager (test)', 'login': 'test_hrm_duyet_phieu',
            'group_ids': [(4, cls.env.ref('hr.group_hr_manager').id)],
        })
        cls.user_tbp = cls.env['res.users'].create({
            'name': 'TBP order (test)', 'login': 'test_tbp_order_phieu',
        })
        cls.dept = cls.env['hr.department'].create({'name': 'Phòng test phiếu'})

    def _request(self, user=None, **vals):
        """Phiếu do TBP tạo — dùng .sudo() đúng như controller (TBP không có ACL
        ghi trên model, route ghi qua sudo sau khi kiểm vai; sudo giữ env.uid)."""
        env = self.env['hb.recruitment.request'].with_user(user or self.user_tbp).sudo()
        return env.create(dict({
            'job_title': 'Vị trí test thông báo',
            'department_id': self.dept.id,
            'qty_expected': 2,
        }, **vals))

    def _notifs(self, req, event, user=None):
        dom = [('dedup_key', '=', 'rec_request_%s_%s' % (req.id, event))]
        if user:
            dom.append(('recipient_id', '=', user.id))
        return self.env['hb.notification'].sudo().search(dom)

    # ── Gửi duyệt → HR ───────────────────────────────────────────────────────

    def test_01_submit_notifies_hr(self):
        r = self._request()
        self.assertFalse(self._notifs(r, 'submitted'), 'Chưa gửi duyệt thì chưa báo')
        r.with_user(self.user_tbp).sudo().action_submit()
        n = self._notifs(r, 'submitted', self.user_hr)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.kind, 'request_submitted')
        self.assertEqual(n.category, 'recruitment')
        self.assertEqual(n.target_tab, 'requests')
        self.assertEqual(n.target_ref, r.id)
        self.assertIn(r.name, n.body)

    def test_01b_submit_also_notifies_hr_manager(self):
        """HR Manager duyệt được phiếu nên cũng phải được báo, dù không thuộc
        nhóm Tuyển dụng — trước đây bị bỏ sót."""
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        self.assertEqual(len(self._notifs(r, 'submitted', self.user_hrm)), 1)

    def test_02_submitter_not_notified_of_own_request(self):
        """HR tự order tự gửi duyệt thì không tự rung chuông mình."""
        r = self._request(user=self.user_hr)
        r.with_user(self.user_hr).sudo().action_submit()
        self.assertFalse(self._notifs(r, 'submitted', self.user_hr))

    def test_03_dedup_until_read(self):
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        r.action_reset_draft()
        r.with_user(self.user_tbp).sudo().action_submit()
        self.assertEqual(len(self._notifs(r, 'submitted', self.user_hr)), 1)

    # ── Duyệt / từ chối → người tạo phiếu ────────────────────────────────────

    def test_04_approve_notifies_requester(self):
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        r.with_user(self.user_hr).sudo().action_approve()
        n = self._notifs(r, 'approved', self.user_tbp)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'success')
        self.assertIn(self.user_hr.name, n.body)

    def test_05_refuse_notifies_requester_with_reason(self):
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        r.write({'refuse_reason': 'Chưa đủ ngân sách quý này'})
        r.with_user(self.user_hr).sudo().action_refuse()
        n = self._notifs(r, 'refused', self.user_tbp)
        self.assertEqual(len(n), 1)
        self.assertEqual(n.level, 'danger')
        self.assertIn('Chưa đủ ngân sách quý này', n.body,
                      'Bị từ chối mà không nói lý do thì TBP không biết sửa gì')

    def test_06_refuse_without_reason_still_notifies(self):
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        r.with_user(self.user_hr).sudo().action_refuse()
        self.assertEqual(len(self._notifs(r, 'refused', self.user_tbp)), 1)

    def test_07_approver_not_notified_of_own_approval(self):
        """HR order rồi tự duyệt ⇒ không tự báo mình."""
        r = self._request(user=self.user_hr)
        r.with_user(self.user_hr).sudo().action_submit()
        r.with_user(self.user_hr).sudo().action_approve()
        self.assertFalse(self._notifs(r, 'approved', self.user_hr))

    def test_08_close_does_not_notify(self):
        r = self._request()
        r.with_user(self.user_tbp).sudo().action_submit()
        r.with_user(self.user_hr).sudo().action_approve()
        r.with_user(self.user_hr).sudo().action_close()
        self.assertFalse(self._notifs(r, 'closed'),
                         'Đóng phiếu chưa báo ai (ngoài phạm vi đợt này)')
